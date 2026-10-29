"""Qt glue: polls the collectors on a timer and hands their readings to QML.

The bridge adapts to the collectors, never the other way round: it converts
units (memory comes in kB, everything else in bytes) and keeps the graph
histories. Formatting for display is the QML side's job.

Errors: a collector raises when the world is broken (a missing /proc file, a
parse failure). The bridge catches it, reports it once on stderr and shows
the fallback value, so one broken source never takes the whole window down.
"""

from __future__ import annotations

import math
import re
import sys
from collections import deque
from collections.abc import Callable
from datetime import datetime, time

from PySide6.QtCore import Property, QCoreApplication, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from kasys.collectors import (
    avatar,
    boot,
    cpu,
    disk,
    display,
    gpu,
    host,
    mem,
    motherboard,
    network,
    pacman,
    processes,
    sensors,
    session,
    udisks,
)

TICK_MS = 1000
# One minute of samples at one per second: what every graph spans.
HISTORY_LENGTH = 60
# Rows in the Overview's "Top by memory" card.
TOP_PROCESSES = 12
# Rows under "TOP BY CPU" in the CPU card.
TOP_CPU_PROCESSES = 3
# What a property reads when its source failed; QML draws it as "--".
MISSING = -1
CM_PER_INCH = 2.54
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


def _float_or_missing(value: int | None) -> float:
    return float(value) if value is not None else MISSING


def _disk_kind(identity: disk.DiskIdentity) -> str:
    # Not "SATA" for the rest: USB and SAS disks land there too.
    if identity.nvme:
        return "NVMe"
    if identity.rotational is None:
        return ""
    return "HDD" if identity.rotational else "SSD"


def _disk_health(smart: udisks.NvmeSmart | udisks.AtaSmart | None) -> str:
    if smart is None:
        return ""
    # Same rule for both: the drive's own alarm, then damaged blocks.
    if isinstance(smart, udisks.NvmeSmart):
        alarm = None if smart.critical_warnings is None else bool(smart.critical_warnings)
        errors = smart.media_errors
    else:
        alarm = smart.failing
        errors = smart.bad_sectors
    # A known problem is a warning even when the other half is unknown.
    if alarm or (errors or 0) > 0:
        return "Warning"
    if alarm is None or errors is None:
        return ""
    return "Healthy"


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


class NetScale:
    """Top of the network graph in bytes/s, kept steady against short bursts.

    Traffic jumps from KiB/s to MiB/s in one second. Scaling to the peak of
    the window lets a single burst flatten the rest of the minute, so the
    scale only moves after RESCALE_TICKS readings in a row agree: above it
    (grow) or under a tenth of it (shrink). A burst shorter than that is
    clipped at the top instead.
    """

    FLOOR = 10 * 1024
    RESCALE_TICKS = 5
    GROW = 1.3
    SHRINK = 3.0

    def __init__(self) -> None:
        self.top: float = self.FLOOR
        self._over = 0
        self._under = 0
        self._recent: deque[float] = deque(maxlen=self.RESCALE_TICKS)

    def update(self, speed: float) -> None:
        self._recent.append(speed)
        if speed > self.top:
            self._over += 1
            self._under = max(0, self._under - 1)
        elif self.top > self.FLOOR and speed < self.top / 10:
            self._under += 1
            self._over = max(0, self._over - 1)

        if self._over >= self.RESCALE_TICKS:
            self._rescale(self.GROW)
        elif self._under >= self.RESCALE_TICKS:
            self._rescale(self.SHRINK)

    def _rescale(self, headroom: float) -> None:
        average = sum(self._recent) / len(self._recent)
        self.top = max(average * headroom, self.FLOOR)
        self._over = 0
        self._under = 0


class Overlay(QObject):
    """Whether the window is on screen, and what closing it means.

    A plain run is open from launch and quits on close. A daemon (`--daemon`,
    started once by the session) starts hidden and only hides on close, so the
    graphs keep filling while nobody is looking (`Monitor.set_shown` skips
    everything else).
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

    def __init__(self, shown: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Hidden, only the graph sources are read and nothing reaches QML.
        self._shown = shown
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
        # Download and upload share one graph, so one scale fits both.
        self._net_scale = NetScale()
        self._gpu_history: deque[float] = deque(maxlen=HISTORY_LENGTH)

        # System info is read once per opening: at launch, and again by
        # set_shown each time a daemon's window is shown.
        self._sys: session.SysInfo | None = None
        self._install_date: datetime | None = None
        self._last_update: datetime | None = None
        self._recent_boots: list[float] = []
        self._cpu_policy: cpu.CpuPolicy | None = None
        # Disks never change while running. The Storage row lists them all and
        # opens on the one holding /.
        self._disk_identities: dict[str, disk.DiskIdentity] = _read("disk identity", disk.get_disk_identity, {})
        self._root_disk: str = _read("root disk", disk.get_root_disk, None) or ""
        # NVMe and ATA SMART differ: wear fields exist on NVMe only.
        self._smart: dict[str, udisks.NvmeSmart | udisks.AtaSmart | None] = {}
        self._disk_temps: dict[str, float | None] = {}
        self.read_system_info()

        # Model and core counts never change while running: read once.
        self._cpu_info: cpu.CpuInfo | None = _read("cpu info", cpu.get_cpu_info, None)

        # Kernel, boot mode and package count: read once, like the CPU model.
        self._host: host.HostInfo | None = _read("host info", host.get_host_info, None)
        # BIOS and board only change after a flash and a reboot: read once.
        self._board: motherboard.BoardInfo | None = _read("motherboard", motherboard.get_motherboard_info, None)
        # Sticks only change with the machine off: read once.
        self._memory: mem.MemoryLayout | None = _read("memory layout", mem.get_memory_layout, None)
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
        self._gpu_vram_type = ""
        self._gpu_interface: gpu.GpuInterface | None = None
        if self._gpu_dir is not None:
            gpu_dir = self._gpu_dir
            self._gpu_hwmon = gpu.find_hwmon_path(gpu_dir)
            name = _read("gpu name", lambda: gpu.get_gpu_name(gpu_dir), None)
            # The card header already says GPU; the vendor is noise next to it.
            self._gpu_name = name.removeprefix("AMD ") if name else ""
            # From the boot's kernel log, which no later reading changes.
            self._gpu_vram_type = _read("vram type", gpu.get_vram_type, None) or ""
            # Max rates of the slot and the card: hardware limits, fixed until a reboot.
            self._gpu_interface = _read("pcie link", lambda: gpu.get_pcie_links(gpu_dir), None)
        # Userspace driver (radeonsi + RADV); a pacman upgrade shows after a restart.
        self._mesa_version = _read("mesa", lambda: pacman.get_package_version("mesa"), None) or ""

        # The avatar is resolved once at startup: changing it means a restart.
        avatar_path = _read("avatar", avatar.get_avatar_path, None)
        self._avatar_url = QUrl.fromLocalFile(avatar_path).toString() if avatar_path else ""

        # Instant readings need no previous one, so the first frame already
        # has them. CPU, network, disk activity and processes are deltas and
        # wait for the first tick.
        self._read_levels()
        self._read_panel_values()

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
        # Hours and bytes written grow while the daemon runs: re-read per opening.
        for name, identity in self._disk_identities.items():
            if identity.nvme:
                self._smart[name] = _read("nvme smart", lambda name=name: udisks.get_nvme_smart(name), None)
            else:
                self._smart[name] = _read("ata smart", lambda name=name: udisks.get_ata_smart(name), None)
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

    def set_shown(self, shown: bool) -> None:
        """Follow the window: panel-only readings pause while it is hidden."""
        self._shown = shown
        if not shown:
            # Hours old by the next opening: the cards start empty instead.
            self._top_processes = []
            self._top_cpu_processes = []
            return
        self.read_system_info()
        # Process CPU % is a delta: without a fresh baseline the first tick
        # would show the average over the whole time hidden.
        if self._process_sample is not None:
            _read("processes", self._process_sample.get_processes, None)
        # Restarted so that first delta spans a whole tick, not a few ms.
        self._timer.start()
        self._read_panel_values()
        self.tick.emit()

    def _read_levels(self) -> None:
        """Instant readings behind a graph: kept going while hidden."""
        self._mem = _read("memory", mem.get_mem_info, self._mem)
        self._read_gpu()

    def _read_panel_values(self) -> None:
        """Instant readings no graph keeps: only read while the window is shown."""
        self._cpu_freq = _read("cpu frequency", cpu.get_cpu_freq, MISSING)
        self._disk_space = _read("disk space", disk.get_disk_space, self._disk_space)
        self._sensors = _read("sensors", sensors.get_sensors_info, self._sensors)
        for name in self._disk_identities:
            self._disk_temps[name] = _read(
                "disk temperature", lambda name=name: sensors.get_disk_temperature(name), None
            )
        # powerprofilesctl can switch the governor / EPP with the window open.
        self._cpu_policy = _read("cpu policy", cpu.get_cpu_policy, None)

    def _read_gpu(self) -> None:
        if self._gpu_dir is None:
            return
        gpu_dir, hwmon = self._gpu_dir, self._gpu_hwmon
        self._gpu = _read("gpu stats", lambda: gpu.get_gpu_stats(gpu_dir, hwmon), None)

    @Slot()
    def _sample(self) -> None:
        # The graph sources run even while hidden, so an opening finds the
        # last minute already drawn.
        if self._cpu_sample is not None:
            self._cpu_usage = _read("cpu usage", self._cpu_sample.get_cpu_usage, 0.0)
        if self._net_sample is not None:
            self._net = _read("network", self._net_sample.get_net_speed, network.NetSpeed(0.0, 0.0))
        self._read_levels()
        self._sample_disk_activity()

        self._cpu_history.append(self._cpu_usage)
        self._mem_history.append(self._mem_percent())
        self._down_history.append(self._net.download)
        self._up_history.append(self._net.upload)
        self._net_scale.update(max(self._net.download, self._net.upload))
        if self._gpu_dir is not None:
            self._gpu_history.append(self._gpu.busy_percentage if self._gpu else 0.0)

        if not self._shown:
            return
        self._read_panel_values()
        self._sample_processes()
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

    def _chip_celsius(self, chip: str, label: str) -> float:
        """One sensor of the first hwmon chip named `chip` (a KNOWN_CHIPS key), or MISSING."""
        for key, chip_sensors in self._sensors.items():
            if _known_chip(key)[0] == chip:
                return next((s.celsius for s in chip_sensors if s.label == label), MISSING)
        return MISSING

    def _gpu_celsius(self, label: str) -> float:
        """One sensor of the amdgpu hwmon chip (edge, junction, mem), or MISSING."""
        return self._chip_celsius("amdgpu", label)

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

    def _get_cpu_temp(self) -> float:
        # AMD or Intel, whichever chip is there, with the sensor the
        # Temperatures card shows for it.
        for chip in ("k10temp", "coretemp"):
            celsius = self._chip_celsius(chip, KNOWN_CHIPS[chip][2])
            if celsius != MISSING:
                return celsius
        return MISSING

    def _get_top_cpu_processes(self) -> list[dict[str, object]]:
        return [{"name": process.name, "cpu": process.cpu_percent} for process in self._top_cpu_processes]

    def _get_cpu_driver(self) -> str:
        policy = self._cpu_policy
        return policy.driver if policy and policy.driver is not None else ""

    def _get_cpu_governor(self) -> str:
        policy = self._cpu_policy
        return policy.governor if policy and policy.governor is not None else ""

    def _get_cpu_epp(self) -> str:
        policy = self._cpu_policy
        return policy.epp if policy and policy.epp is not None else ""

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
    # °C of the package sensor (Tctl / Package id 0), or MISSING.
    cpuTemp = Property(float, _get_cpu_temp, notify=tick)
    # Up to TOP_CPU_PROCESSES dicts, busiest first: name and cpu (0..100).
    topCpuProcesses = Property(list, _get_top_cpu_processes, notify=tick)
    # cpufreq policy0, re-read every tick: "" when absent (epp: driver
    # without EPP).
    cpuDriver = Property(str, _get_cpu_driver, notify=tick)
    cpuGovernor = Property(str, _get_cpu_governor, notify=tick)
    cpuEpp = Property(str, _get_cpu_epp, notify=tick)

    # -- GPU ---------------------------------------------------------------
    def _get_gpu_name(self) -> str:
        return self._gpu_name

    def _get_gpu_vram_type(self) -> str:
        return self._gpu_vram_type

    def _get_mesa_version(self) -> str:
        return self._mesa_version

    def _get_gpu_link_speed(self) -> float:
        return self._gpu_interface.link.speed if self._gpu_interface else MISSING

    def _get_gpu_link_width(self) -> int:
        return self._gpu_interface.link.width if self._gpu_interface else MISSING

    def _get_gpu_card_speed(self) -> float:
        return self._gpu_interface.card.speed if self._gpu_interface else MISSING

    def _get_gpu_card_width(self) -> int:
        return self._gpu_interface.card.width if self._gpu_interface else MISSING

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

    def _get_gpu_hotspot_temp(self) -> float:
        return self._gpu_celsius("junction")

    def _get_gpu_vram_temp(self) -> float:
        return self._gpu_celsius("mem")

    def _get_gpu_driver(self) -> str:
        # find_gpu_dir only accepts cards bound to amdgpu.
        return "amdgpu" if self._gpu_dir is not None else ""

    def _get_gpu_clock(self) -> float:
        clock = self._gpu.clock if self._gpu else None
        return float(clock) if clock is not None else MISSING

    def _get_gpu_fan(self) -> int:
        fan = self._gpu.fan_rpm if self._gpu else None
        return fan if fan is not None else MISSING

    def _get_gpu_power(self) -> float:
        power = self._gpu.power_average if self._gpu else None
        return float(power) if power is not None else MISSING

    def _get_gpu_power_cap(self) -> float:
        cap = self._gpu.power_cap if self._gpu else None
        return float(cap) if cap is not None else MISSING

    # From amdgpu.ids at startup, "AMD " dropped; "" when unknown or no GPU.
    gpuName = Property(str, _get_gpu_name, constant=True)
    # "GDDR6", "HBM", ... from the kernel log; "" when not found.
    gpuVramType = Property(str, _get_gpu_vram_type, constant=True)
    # "26.2.5", epoch and pkgrel dropped; "" when mesa is not installed.
    mesaVersion = Property(str, _get_mesa_version, constant=True)
    # PCIe link the card runs at (GT/s, lanes): the lower max of card and slot.
    # MISSING when the link could not be read.
    gpuLinkSpeed = Property(float, _get_gpu_link_speed, constant=True)
    gpuLinkWidth = Property(int, _get_gpu_link_width, constant=True)
    # What the card alone supports, above the link when the slot holds it back.
    gpuCardSpeed = Property(float, _get_gpu_card_speed, constant=True)
    gpuCardWidth = Property(int, _get_gpu_card_width, constant=True)
    # 0..100, or MISSING without an amdgpu card.
    gpuUsage = Property(float, _get_gpu_usage, notify=tick)
    gpuHistory = Property(list, _get_gpu_history, notify=tick)
    # Bytes, floats because Qt's int is 32-bit.
    gpuVramUsed = Property(float, _get_gpu_vram_used, notify=tick)
    gpuVramTotal = Property(float, _get_gpu_vram_total, notify=tick)
    # °C of the edge sensor.
    gpuTemp = Property(float, _get_gpu_temp, notify=tick)
    # °C of the junction (hotspot) and memory sensors.
    gpuHotspotTemp = Property(float, _get_gpu_hotspot_temp, notify=tick)
    gpuVramTemp = Property(float, _get_gpu_vram_temp, notify=tick)
    # Kernel driver of the card, "" without one.
    gpuDriver = Property(str, _get_gpu_driver, constant=True)
    # Hz (shader clock): float, since 2.5 GHz overflows a 32-bit int.
    gpuClock = Property(float, _get_gpu_clock, notify=tick)
    # RPM, or MISSING when the card has no fan reading.
    gpuFan = Property(int, _get_gpu_fan, notify=tick)
    # µW of the PPT sensor and its limit, floats like gpuClock.
    gpuPower = Property(float, _get_gpu_power, notify=tick)
    gpuPowerCap = Property(float, _get_gpu_power_cap, notify=tick)

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

    def _get_net_scale(self) -> float:
        return self._net_scale.top

    netDown = Property(float, _get_net_down, notify=tick)
    netUp = Property(float, _get_net_up, notify=tick)
    netDownHistory = Property(list, _get_down_history, notify=tick)
    netUpHistory = Property(list, _get_up_history, notify=tick)
    # Top of the network graph (bytes/s); QML rounds it for the axis labels.
    netScale = Property(float, _get_net_scale, notify=tick)

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

    # -- storage (identity once, SMART per opening, temperature per tick) ------
    def _get_storage_disks(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for name, identity in sorted(self._disk_identities.items()):
            smart = self._smart.get(name)
            nvme_smart = smart if isinstance(smart, udisks.NvmeSmart) else None
            temp = self._disk_temps.get(name)
            space = self._disk_space.get(name)
            rows.append(
                {
                    "name": name,
                    "model": identity.model or "",
                    "size": _float_or_missing(identity.size),
                    "kind": _disk_kind(identity),
                    "temp": temp if temp is not None else MISSING,
                    "health": _disk_health(smart),
                    "lifespanUsed": _float_or_missing(nvme_smart.percent_used if nvme_smart else None),
                    "written": _float_or_missing(nvme_smart.bytes_written if nvme_smart else None),
                    "powerOnHours": _float_or_missing(smart.power_on_hours if smart else None),
                    "fstype": space.fstype if space else "",
                    "used": float(space.used) if space else MISSING,
                    "available": float(space.available) if space else MISSING,
                    "percent": _percent(space.used, space.used + space.available) if space else MISSING,
                }
            )
        return rows

    def _get_root_disk(self) -> str:
        return self._root_disk

    # One dict per disk, sorted by name. model ("" unknown; SATA cut at 16
    # chars), size (bytes), kind ("NVMe", "HDD", "SSD" or ""), temp (°C);
    # SMART: health ("Healthy", "Warning", ""), powerOnHours; NVMe only:
    # lifespanUsed (%, may pass 100), written (bytes). Largest mounted
    # partition, like `disks`: fstype ("" unmounted), used / available
    # (bytes), percent. Numbers are MISSING when unknown.
    storageDisks = Property(list, _get_storage_disks, notify=tick)
    # Name of the disk holding /, the row's default; "" when not found.
    rootDisk = Property(str, _get_root_disk, constant=True)

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

    # -- motherboard (read once at startup) -----------------------------------
    def _get_board_name(self) -> str:
        board = self._board
        return board.name if board and board.name is not None else ""

    def _get_board_vendor(self) -> str:
        board = self._board
        return board.vendor if board and board.vendor is not None else ""

    def _get_bios_version(self) -> str:
        board = self._board
        return board.bios_version if board and board.bios_version is not None else ""

    def _get_bios_date(self) -> float:
        board = self._board
        if board is None or board.bios_date is None:
            return MISSING
        # Local midnight, so a JS Date shows the same calendar day.
        return datetime.combine(board.bios_date, time()).timestamp() * 1000

    # "" when unknown; vendor raw ("ASUSTeK COMPUTER INC.").
    boardName = Property(str, _get_board_name, constant=True)
    boardVendor = Property(str, _get_board_vendor, constant=True)
    biosVersion = Property(str, _get_bios_version, constant=True)
    # ms since the epoch (a date, no time), or MISSING.
    biosDate = Property(float, _get_bios_date, constant=True)

    # -- memory modules (read once at startup) --------------------------------
    def _memory_modules(self) -> list[mem.MemoryModule]:
        """The populated slots, in slot order."""
        if self._memory is None:
            return []
        return [module for module in self._memory.slots if module is not None]

    def _get_memory_installed(self) -> float:
        modules = self._memory_modules()
        return float(sum(module.size for module in modules)) if modules else MISSING

    # Mixed sticks are not handled: the first one speaks for all.
    def _get_memory_type(self) -> str:
        modules = self._memory_modules()
        return modules[0].type if modules and modules[0].type is not None else ""

    def _get_memory_speed(self) -> int:
        modules = self._memory_modules()
        return modules[0].speed if modules and modules[0].speed is not None else MISSING

    def _get_memory_channels(self) -> int:
        channels = [module.channel for module in self._memory_modules()]
        # One stick of unknown channel and the count would be a guess.
        if not channels or None in channels:
            return MISSING
        return len(set(channels))

    def _get_memory_slots(self) -> list[dict[str, object]]:
        if self._memory is None:
            return []
        return [
            {"populated": module is not None, "size": float(module.size) if module else MISSING}
            for module in self._memory.slots
        ]

    # Sum of the sticks in bytes (not MemTotal, which the kernel trims), or MISSING.
    memoryInstalled = Property(float, _get_memory_installed, constant=True)
    # "DDR4", or "" when unknown.
    memoryType = Property(str, _get_memory_type, constant=True)
    # MT/s the sticks run at, or MISSING.
    memorySpeed = Property(int, _get_memory_speed, constant=True)
    # Distinct channels with a stick, or MISSING when any stick's channel is unknown.
    memoryChannels = Property(int, _get_memory_channels, constant=True)
    # One dict per slot in board order: populated and size (bytes, MISSING if empty).
    memorySlots = Property(list, _get_memory_slots, constant=True)

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

    @Slot(str, result=float)
    def monitorDiagonal(self, screen_name: str) -> float:
        """Inches of the named screen from its EDID size (whole cm), or MISSING."""
        size = display.get_monitor_size(screen_name)
        if size is None:
            return MISSING
        return math.hypot(*size) / CM_PER_INCH

    def _get_avatar_url(self) -> str:
        return self._avatar_url

    # file:// URL, or "" when no avatar is configured.
    avatarUrl = Property(str, _get_avatar_url, constant=True)
