"""Qt glue: polls the collectors on a timer and hands their readings to QML.

The bridge adapts to the collectors, never the other way round: it converts
units (memory comes in kB, everything else in bytes) and keeps the graph
histories. Formatting for display is the QML side's job.

Errors: a collector raises when the world is broken (a missing /proc file, a
parse failure). The bridge catches it, reports it once on stderr and shows
the fallback value, so one broken source never takes the whole window down.
"""

from __future__ import annotations

import re
import sys
from collections import deque
from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import Property, QCoreApplication, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from kasys.collectors import avatar, boot, cpu, disk, gpu, host, mem, network, pacman, processes, sensors, session

TICK_MS = 1000
# One minute of samples at one per second: what every graph spans.
HISTORY_LENGTH = 60
# Rows in the Overview's "Top by memory" card.
TOP_PROCESSES = 12
# Rows under "TOP BY CPU" in the CPU card.
TOP_CPU_PROCESSES = 3
# What a property reads when its source failed; QML draws it as "--".
MISSING = -1
# How often to ask systemd again while the boot is still running.
BOOT_RETRY_MS = 5000

# Chips the Temperatures card knows, in the order it lists them: display
# name, glyph kind for QML, and the one sensor shown. Any other chip shows up
# under its raw name with its first sensor.
KNOWN_CHIPS: dict[str, tuple[str, str, str]] = {
    "k10temp": ("CPU", "cpu", "Tctl"),
    "coretemp": ("CPU", "cpu", "Package id 0"),
    "amdgpu": ("GPU", "gpu", "edge"),
    "nvme": ("NVMe", "disk", "Composite"),
}

COLLECTOR_ERRORS = (OSError, ValueError, RuntimeError, IndexError, KeyError)

_reported: set[str] = set()


def _read[T](label: str, read: Callable[[], T], fallback: T) -> T:
    """Call one collector; on failure log it once and return the fallback."""
    try:
        return read()
    except COLLECTOR_ERRORS as error:
        if label not in _reported:
            _reported.add(label)
            print(f"kasys: {label} unavailable: {error}", file=sys.stderr)
        return fallback


def _percent(part: float, whole: float) -> float:
    return 100 * part / whole if whole > 0 else 0.0


def _known_chip(key: str) -> tuple[str, str]:
    """Split a sensors key into a KNOWN_CHIPS name and its repeat counter.

    `nvme2` -> ("nvme", "2"). Unknown chips come back as (key, ""), so a raw
    name ending in digits (`nct6775`) is never cut.
    """
    if key in KNOWN_CHIPS:
        return key, ""
    match = re.fullmatch(r"(.+?)(\d+)", key)
    if match and match.group(1) in KNOWN_CHIPS:
        return match.group(1), match.group(2)
    return key, ""


def _temperature_rows(chips: dict[str, list[sensors.Sensor]]) -> list[dict[str, object]]:
    """One row per chip: known chips first in KNOWN_CHIPS order, then the rest."""
    order = list(KNOWN_CHIPS)
    rows: list[tuple[int, dict[str, object]]] = []
    for key, chip_sensors in chips.items():
        chip, counter = _known_chip(key)
        if chip in KNOWN_CHIPS:
            name, kind, wanted = KNOWN_CHIPS[chip]
            if counter:
                name = f"{name} {counter}"
            rank = order.index(chip)
        else:
            name, kind, wanted, rank = key, "", "", len(order)
        sensor = next((s for s in chip_sensors if s.label == wanted), chip_sensors[0])
        rows.append((rank, {"name": name, "kind": kind, "celsius": sensor.celsius}))
    # sorted() is stable: same-rank chips keep the collector's hwmon order.
    return [row for _, row in sorted(rows, key=lambda pair: pair[0])]


class Overlay(QObject):
    """Whether the window is on screen, and what closing it means.

    A plain run is open from launch and quits on close. A daemon (`--daemon`,
    started once by the session) starts hidden and only hides on close, so the
    graphs keep filling while nobody is looking.
    """

    shownChanged = Signal()

    def __init__(self, daemon: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._daemon = daemon
        self._shown = not daemon

    @Slot()
    def toggle(self) -> None:
        self._set_shown(not self._shown)

    @Slot()
    def close(self) -> None:
        self._set_shown(False)

    def _set_shown(self, shown: bool) -> None:
        if shown == self._shown:
            return
        if not shown and not self._daemon:
            QCoreApplication.quit()
            return
        self._shown = shown
        self.shownChanged.emit()

    def _get_shown(self) -> bool:
        return self._shown

    shown = Property(bool, _get_shown, notify=shownChanged)


class Monitor(QObject):
    """Every reading the window shows. Live values change on `tick`."""

    tick = Signal()
    systemInfoChanged = Signal()
    bootInfoChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cpu_sample: cpu.CpuSample | None = _read("cpu usage", cpu.CpuSample, None)
        self._net_sample: network.NetSample | None = _read("network", network.NetSample, None)
        self._disk_sample: disk.DiskSample | None = _read("disk activity", disk.DiskSample, None)
        self._process_sample: processes.ProcessSample | None = _read("processes", processes.ProcessSample, None)

        self._cpu_usage = 0.0
        self._cpu_freq = MISSING
        self._mem: mem.MemInfo | None = None
        # Free space of the largest mounted partition per disk. Only disks with
        # something mounted have a key, and only those reach the Disk card.
        self._disk_space: dict[str, disk.DiskInfo] = {}
        self._net = network.NetSpeed(download=0.0, upload=0.0)
        # Active time % per physical disk, mounted or not.
        self._disk_activity: dict[str, float] = {}
        self._sensors: dict[str, list[sensors.Sensor]] = {}
        self._top_processes: list[processes.Process] = []
        self._top_cpu_processes: list[processes.Process] = []
        self._gpu: gpu.GpuStats | None = None

        self._cpu_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._mem_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._disk_activity_history: dict[str, deque[float]] = {}
        self._down_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._up_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._gpu_history: deque[float] = deque(maxlen=HISTORY_LENGTH)

        # System info is read once per opening: at launch, and again by
        # main.py each time a daemon's window is shown.
        self._sys: session.SysInfo | None = None
        self._install_date: datetime | None = None
        self._last_update: datetime | None = None
        self._recent_boots: list[float] = []
        self.read_system_info()

        # Model and core counts never change while running: read once.
        self._cpu_info: cpu.CpuInfo | None = _read("cpu info", cpu.get_cpu_info, None)

        # Kernel, boot mode and package count: read once, like the CPU model.
        self._host: host.HostInfo | None = _read("host info", host.get_host_info, None)
        # The desktop session outlives the app: read once.
        self._session: session.SessionInfo | None = _read("session info", session.get_session_info, None)

        # The boot times are fixed once systemd is done booting. Started early
        # (autostart), it is not done yet: ask again until it is.
        self._boot: boot.BootInfo | None = None
        # Units on systemd's critical chain, slowest first.
        self._critical_chain: list[boot.ChainUnit] = []
        self._boot_timer = QTimer(self)
        self._boot_timer.setInterval(BOOT_RETRY_MS)
        self._boot_timer.timeout.connect(self._read_boot_info)
        if not self._read_boot_info():
            self._boot_timer.start()

        # The card is found once: a GPU is never hot-plugged.
        self._gpu_dir: str | None = _read("gpu", gpu.find_gpu_dir, None)
        self._gpu_hwmon: str | None = None
        self._gpu_name = ""
        if self._gpu_dir is not None:
            gpu_dir = self._gpu_dir
            self._gpu_hwmon = gpu.find_hwmon_path(gpu_dir)
            name = _read("gpu name", lambda: gpu.get_gpu_name(gpu_dir), None)
            # The card header already says GPU; the vendor is noise next to it.
            self._gpu_name = name.removeprefix("AMD ") if name else ""

        # The avatar is resolved once at startup: changing it means a restart.
        avatar_path = _read("avatar", avatar.get_avatar_path, None)
        self._avatar_url = QUrl.fromLocalFile(avatar_path).toString() if avatar_path else ""

        # Memory, disk space, sensors and the GPU need no previous reading, so the first
        # frame already has them. CPU and network are deltas and wait for the
        # first tick.
        self._read_levels()

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._sample)
        self._timer.start()

    def read_system_info(self) -> None:
        self._sys = _read("system info", session.get_sys_info, None)
        self._install_date = _read("install date", pacman.get_install_date, None)
        self._last_update = _read("last update", pacman.get_last_update, None)
        # The journal only gains this boot once systemd is done: an opening
        # after that picks it up.
        self._recent_boots = _read("recent boots", boot.get_recent_boots, None) or []
        self.systemInfoChanged.emit()

    @Slot(result=bool)
    def _read_boot_info(self) -> bool:
        """Read the boot times; False while systemd is still booting."""
        try:
            self._boot = _read("boot info", boot.get_boot_info, None)
            chain = _read("critical chain", boot.get_critical_chain, None) or []
        except boot.BootNotFinishedError:
            return False
        self._critical_chain = sorted(chain, key=lambda unit: unit.seconds, reverse=True)
        # Read, or failed for good: either way there is nothing to retry.
        self._boot_timer.stop()
        self.bootInfoChanged.emit()
        return True

    def _read_levels(self) -> None:
        self._mem = _read("memory", mem.get_mem_info, self._mem)
        self._disk_space = _read("disk space", disk.get_disk_space, self._disk_space)
        self._sensors = _read("sensors", sensors.get_sensors_info, self._sensors)
        self._read_gpu()

    def _read_gpu(self) -> None:
        if self._gpu_dir is None:
            return
        gpu_dir, hwmon = self._gpu_dir, self._gpu_hwmon
        self._gpu = _read("gpu stats", lambda: gpu.get_gpu_stats(gpu_dir, hwmon), None)

    @Slot()
    def _sample(self) -> None:
        if self._cpu_sample is not None:
            self._cpu_usage = _read("cpu usage", self._cpu_sample.get_cpu_usage, 0.0)
        self._cpu_freq = _read("cpu frequency", cpu.get_cpu_freq, MISSING)
        if self._net_sample is not None:
            self._net = _read("network", self._net_sample.get_net_speed, network.NetSpeed(0.0, 0.0))
        self._read_levels()
        self._sample_disk_activity()
        self._sample_processes()

        self._cpu_history.append(self._cpu_usage)
        self._mem_history.append(self._mem_percent())
        self._down_history.append(self._net.download)
        self._up_history.append(self._net.upload)
        if self._gpu_dir is not None:
            self._gpu_history.append(self._gpu.busy_percentage if self._gpu else 0.0)
        self.tick.emit()

    def _sample_disk_activity(self) -> None:
        if self._disk_sample is None:
            return
        activity = _read("disk activity", self._disk_sample.get_disk_activity, {})
        self._disk_activity = dict(sorted(activity.items()))
        # Rebuilt each tick: an unplugged disk loses its graph, a new one starts empty.
        history: dict[str, deque[float]] = {}
        for name, percent in self._disk_activity.items():
            history[name] = self._disk_activity_history.get(name, deque(maxlen=HISTORY_LENGTH))
            history[name].append(percent)
        self._disk_activity_history = history

    def _sample_processes(self) -> None:
        if self._process_sample is None:
            return
        found = _read("processes", self._process_sample.get_processes, None)
        if found is None:
            return
        # Ties break on the other column, then PID, so equal rows keep their place.
        by_cpu = sorted(found, key=lambda p: (-p.cpu_percent, -p.mem_bytes, p.pid))
        self._top_cpu_processes = by_cpu[:TOP_CPU_PROCESSES]
        found.sort(key=lambda p: (-p.mem_bytes, -p.cpu_percent, p.pid))
        self._top_processes = found[:TOP_PROCESSES]

    def _gpu_celsius(self, label: str) -> float:
        """One sensor of the amdgpu hwmon chip (edge, junction, mem), or MISSING."""
        for key, chip_sensors in self._sensors.items():
            if _known_chip(key)[0] == "amdgpu":
                return next((s.celsius for s in chip_sensors if s.label == label), MISSING)
        return MISSING

    def _mem_percent(self) -> float:
        if self._mem is None:
            return 0.0
        return _percent(self._mem.used, self._mem.total)

    # -- CPU ---------------------------------------------------------------
    def _get_cpu_usage(self) -> float:
        return self._cpu_usage

    def _get_cpu_freq(self) -> int:
        return self._cpu_freq

    def _get_cpu_history(self) -> list[float]:
        return list(self._cpu_history)

    def _get_cpu_peak(self) -> float:
        return max(self._cpu_history) if self._cpu_history else MISSING

    def _get_cpu_model(self) -> str:
        info = self._cpu_info
        return info.model if info and info.model is not None else ""

    def _get_cpu_cores(self) -> int:
        info = self._cpu_info
        return info.cores if info and info.cores is not None else MISSING

    def _get_cpu_threads(self) -> int:
        info = self._cpu_info
        return info.threads if info and info.threads is not None else MISSING

    def _get_top_cpu_processes(self) -> list[dict[str, object]]:
        return [{"name": process.name, "cpu": process.cpu_percent} for process in self._top_cpu_processes]

    cpuUsage = Property(float, _get_cpu_usage, notify=tick)
    # kHz, or MISSING when cpufreq is not exposed.
    cpuFreq = Property(int, _get_cpu_freq, notify=tick)
    cpuHistory = Property(list, _get_cpu_history, notify=tick)
    # Max of cpuHistory, or MISSING before the first tick.
    cpuPeak = Property(float, _get_cpu_peak, notify=tick)
    # From /proc/cpuinfo at startup: "" / MISSING when the field is absent.
    cpuModel = Property(str, _get_cpu_model, constant=True)
    cpuCores = Property(int, _get_cpu_cores, constant=True)
    cpuThreads = Property(int, _get_cpu_threads, constant=True)
    # Up to TOP_CPU_PROCESSES dicts, busiest first: name and cpu (0..100).
    topCpuProcesses = Property(list, _get_top_cpu_processes, notify=tick)

    # -- GPU ---------------------------------------------------------------
    def _get_gpu_name(self) -> str:
        return self._gpu_name

    def _get_gpu_usage(self) -> float:
        return self._gpu.busy_percentage if self._gpu else MISSING

    def _get_gpu_history(self) -> list[float]:
        return list(self._gpu_history)

    def _get_gpu_vram_used(self) -> float:
        return float(self._gpu.vram_used) if self._gpu else MISSING

    def _get_gpu_vram_total(self) -> float:
        return float(self._gpu.vram_total) if self._gpu else MISSING

    def _get_gpu_temp(self) -> float:
        return self._gpu_celsius("edge")

    def _get_gpu_clock(self) -> float:
        clock = self._gpu.clock if self._gpu else None
        return float(clock) if clock is not None else MISSING

    def _get_gpu_fan(self) -> int:
        fan = self._gpu.fan_rpm if self._gpu else None
        return fan if fan is not None else MISSING

    # From amdgpu.ids at startup, "AMD " dropped; "" when unknown or no GPU.
    gpuName = Property(str, _get_gpu_name, constant=True)
    # 0..100, or MISSING without an amdgpu card.
    gpuUsage = Property(float, _get_gpu_usage, notify=tick)
    gpuHistory = Property(list, _get_gpu_history, notify=tick)
    # Bytes, floats because Qt's int is 32-bit.
    gpuVramUsed = Property(float, _get_gpu_vram_used, notify=tick)
    gpuVramTotal = Property(float, _get_gpu_vram_total, notify=tick)
    # °C of the edge sensor.
    gpuTemp = Property(float, _get_gpu_temp, notify=tick)
    # Hz (shader clock): float, since 2.5 GHz overflows a 32-bit int.
    gpuClock = Property(float, _get_gpu_clock, notify=tick)
    # RPM, or MISSING when the card has no fan reading.
    gpuFan = Property(int, _get_gpu_fan, notify=tick)

    # -- memory (bytes; floats because Qt's int is 32-bit) -------------------
    def _get_mem_total(self) -> float:
        return float(self._mem.total) if self._mem else MISSING

    def _get_mem_used(self) -> float:
        return float(self._mem.used) if self._mem else MISSING

    def _get_mem_available(self) -> float:
        return float(self._mem.available) if self._mem else MISSING

    def _get_mem_percent(self) -> float:
        return self._mem_percent()

    def _get_mem_history(self) -> list[float]:
        return list(self._mem_history)

    memTotal = Property(float, _get_mem_total, notify=tick)
    memUsed = Property(float, _get_mem_used, notify=tick)
    memAvailable = Property(float, _get_mem_available, notify=tick)
    memPercent = Property(float, _get_mem_percent, notify=tick)
    memHistory = Property(list, _get_mem_history, notify=tick)

    # -- disk (space in bytes, activity in %) ---------------------------------
    def _get_disks(self) -> list[dict[str, object]]:
        return [
            {
                "name": name,
                "total": float(space.total),
                "used": float(space.used),
                "available": float(space.available),
                # Same ratio `df` prints: the root-reserved blocks count as neither.
                "percent": _percent(space.used, space.used + space.available),
                "history": list(self._disk_activity_history.get(name, ())),
            }
            for name, space in sorted(self._disk_space.items())
        ]

    # One dict per disk with something mounted, sorted by name: space of its
    # largest mounted partition (bytes, percent = fill) and the active time
    # history (0..100) for the graph.
    disks = Property(list, _get_disks, notify=tick)

    # -- temperatures (°C) ---------------------------------------------------
    def _get_temperatures(self) -> list[dict[str, object]]:
        return _temperature_rows(self._sensors)

    # One dict per hwmon chip with temperatures: display name, glyph kind
    # ("cpu", "gpu", "disk" or "" for an unknown chip) and celsius.
    temperatures = Property(list, _get_temperatures, notify=tick)

    # -- processes -----------------------------------------------------------
    def _get_top_processes(self) -> list[dict[str, object]]:
        return [
            {
                "pid": process.pid,
                "name": process.name,
                "cpu": process.cpu_percent,
                "mem": float(process.mem_bytes),
            }
            for process in self._top_processes
        ]

    # Up to TOP_PROCESSES dicts, largest memory first: pid, name (comm, up to 15
    # chars), cpu (0..100 of the whole machine) and mem (RSS bytes).
    topProcesses = Property(list, _get_top_processes, notify=tick)

    # -- network (bytes/s) ---------------------------------------------------
    def _get_net_down(self) -> float:
        return self._net.download

    def _get_net_up(self) -> float:
        return self._net.upload

    def _get_down_history(self) -> list[float]:
        return list(self._down_history)

    def _get_up_history(self) -> list[float]:
        return list(self._up_history)

    netDown = Property(float, _get_net_down, notify=tick)
    netUp = Property(float, _get_net_up, notify=tick)
    netDownHistory = Property(list, _get_down_history, notify=tick)
    netUpHistory = Property(list, _get_up_history, notify=tick)

    # -- system info (read once per opening) ---------------------------------
    def _get_hostname(self) -> str:
        return self._sys.hostname if self._sys else ""

    def _get_os_name(self) -> str:
        return self._sys.os_name if self._sys else ""

    def _get_shell_name(self) -> str:
        return self._sys.shell_name if self._sys else ""

    def _get_uptime(self) -> float:
        return self._sys.uptime if self._sys else MISSING

    def _get_os_age_days(self) -> int:
        # Calendar days in local time: installed yesterday at 23:00 is 1 day.
        if self._install_date is None:
            return MISSING
        today = datetime.now().astimezone().date()
        return (today - self._install_date.astimezone().date()).days

    def _get_install_date(self) -> float:
        # Milliseconds since the epoch: what a JS Date takes.
        return self._install_date.timestamp() * 1000 if self._install_date else MISSING

    def _get_last_update(self) -> float:
        return self._last_update.timestamp() * 1000 if self._last_update else MISSING

    def _get_last_update_age(self) -> float:
        if self._last_update is None:
            return MISSING
        return (datetime.now().astimezone() - self._last_update).total_seconds()

    hostname = Property(str, _get_hostname, notify=systemInfoChanged)
    osName = Property(str, _get_os_name, notify=systemInfoChanged)
    shellName = Property(str, _get_shell_name, notify=systemInfoChanged)
    # Seconds.
    uptime = Property(float, _get_uptime, notify=systemInfoChanged)
    # First line of pacman.log, in ms since the epoch; MISSING if unreadable.
    installDate = Property(float, _get_install_date, notify=systemInfoChanged)
    # Days since install; notified every tick so it turns over at midnight.
    osAgeDays = Property(int, _get_os_age_days, notify=tick)
    # Last `pacman -Syu`, in ms since the epoch; MISSING if none found.
    lastUpdate = Property(float, _get_last_update, notify=systemInfoChanged)
    # Seconds since the last update; notified every tick so "3h ago" moves.
    lastUpdateAge = Property(float, _get_last_update_age, notify=tick)

    def _get_recent_boots(self) -> list[float]:
        return list(self._recent_boots)

    # Total seconds of the last startups, oldest first; [] when unknown.
    recentBoots = Property(list, _get_recent_boots, notify=systemInfoChanged)

    # -- host info (read once at startup) -------------------------------------
    def _get_kernel(self) -> str:
        return self._host.kernel if self._host else ""

    def _get_architecture(self) -> str:
        return self._host.arch if self._host else ""

    def _get_uefi(self) -> int:
        return int(self._host.uefi) if self._host else MISSING

    def _get_secure_boot(self) -> int:
        host = self._host
        return int(host.secure_boot) if host and host.secure_boot is not None else MISSING

    def _get_bootloader(self) -> str:
        host = self._host
        return host.boot_loader if host and host.boot_loader is not None else ""

    def _get_packages(self) -> int:
        host = self._host
        return host.packages if host and host.packages is not None else MISSING

    # "" / MISSING when the field is unknown.
    kernel = Property(str, _get_kernel, constant=True)
    architecture = Property(str, _get_architecture, constant=True)
    # Flags as 1 / 0, or MISSING: a QML bool has no "unknown".
    uefi = Property(int, _get_uefi, constant=True)
    secureBoot = Property(int, _get_secure_boot, constant=True)
    bootloader = Property(str, _get_bootloader, constant=True)
    # Installed pacman packages.
    packages = Property(int, _get_packages, constant=True)

    # -- session info (read once at startup) ----------------------------------
    def _get_desktop(self) -> str:
        session = self._session
        return session.desktop if session and session.desktop is not None else ""

    def _get_display_server(self) -> str:
        session = self._session
        return session.display_server if session and session.display_server is not None else ""

    # "" when unknown; display server is raw ("wayland" / "x11"), QML formats.
    desktop = Property(str, _get_desktop, constant=True)
    displayServer = Property(str, _get_display_server, constant=True)

    # -- boot info (read once systemd has finished booting) --------------------
    def _get_boot_total(self) -> float:
        return self._boot.total if self._boot else MISSING

    def _get_boot_phases(self) -> list[dict[str, object]]:
        if self._boot is None:
            return []
        return [{"name": name, "seconds": seconds} for name, seconds in self._boot.phases.items()]

    # Seconds from the first phase to startup finished, or MISSING.
    bootTotal = Property(float, _get_boot_total, notify=bootInfoChanged)
    # One dict per phase in systemd's order: name (raw, "firmware") and seconds.
    bootPhases = Property(list, _get_boot_phases, notify=bootInfoChanged)

    def _get_startup_services(self) -> list[dict[str, object]]:
        return [{"name": unit.name, "seconds": unit.seconds} for unit in self._critical_chain]

    # Every unit that held up the boot, slowest first: name (raw,
    # "proton.VPN.service") and seconds. QML picks how many rows to show.
    startupServices = Property(list, _get_startup_services, notify=bootInfoChanged)

    @Slot(str, result=float)
    def refreshRate(self, screen_name: str) -> float:
        """Hz of the named screen: QML's Screen knows the name but not the rate."""
        for screen in QGuiApplication.screens():
            if screen.name() == screen_name:
                return screen.refreshRate()
        return MISSING

    def _get_avatar_url(self) -> str:
        return self._avatar_url

    # file:// URL, or "" when no avatar is configured.
    avatarUrl = Property(str, _get_avatar_url, constant=True)
