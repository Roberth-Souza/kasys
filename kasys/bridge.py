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
from statistics import fmean

from PySide6.QtCore import Property, QCoreApplication, QObject, QTimer, QUrl, Signal, Slot

from kasys.collectors import avatar, cpu, disk, mem, network, processes, sensors
from kasys.collectors import sys as sysinfo

TICK_MS = 1000
# One minute of samples at one per second: what every graph spans.
HISTORY_LENGTH = 60
# Rows in the Overview's "Top by memory" card.
TOP_PROCESSES = 12
# Rows under "TOP BY CPU" in the CPU card.
TOP_CPU_PROCESSES = 3
# What a property reads when its source failed; QML draws it as "--".
MISSING = -1

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

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cpu_sample = cpu.CpuSample()
        self._net_sample = network.NetSample()
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

        self._cpu_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._mem_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._disk_activity_history: dict[str, deque[float]] = {}
        self._down_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._up_history: deque[float] = deque(maxlen=HISTORY_LENGTH)

        # System info is read once per opening: at launch, and again by
        # main.py each time a daemon's window is shown.
        self._sys: sysinfo.SysInfo | None = None
        self._install_date: datetime | None = None
        self.read_system_info()

        # Model and core counts never change while running: read once.
        self._cpu_info: cpu.CpuInfo | None = _read("cpu info", cpu.get_cpu_info, None)

        # The avatar is resolved once at startup: changing it means a restart.
        avatar_path = _read("avatar", avatar.get_avatar_path, None)
        self._avatar_url = QUrl.fromLocalFile(avatar_path).toString() if avatar_path else ""

        # Memory, disk space and sensors need no previous reading, so the first
        # frame already has them. CPU and network are deltas and wait for the
        # first tick.
        self._read_levels()

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._sample)
        self._timer.start()

    def read_system_info(self) -> None:
        self._sys = _read("system info", sysinfo.get_sys_info, None)
        self._install_date = _read("install date", sysinfo.get_install_date, None)
        self.systemInfoChanged.emit()

    def _read_levels(self) -> None:
        self._mem = _read("memory", mem.get_mem_info, self._mem)
        self._disk_space = _read("disk space", disk.get_disk_space, self._disk_space)
        self._sensors = _read("sensors", sensors.get_sensors_info, self._sensors)

    @Slot()
    def _sample(self) -> None:
        self._cpu_usage = _read("cpu usage", self._cpu_sample.get_cpu_usage, 0.0)
        self._cpu_freq = _read("cpu frequency", cpu.get_cpu_freq, MISSING)
        self._net = _read("network", self._net_sample.get_net_speed, network.NetSpeed(0.0, 0.0))
        self._read_levels()
        self._sample_disk_activity()
        self._sample_processes()

        self._cpu_history.append(self._cpu_usage)
        self._mem_history.append(self._mem_percent())
        self._down_history.append(self._net.download)
        self._up_history.append(self._net.upload)
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

    def _get_cpu_average(self) -> float:
        return fmean(self._cpu_history) if self._cpu_history else MISSING

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
    # Mean and max of cpuHistory, or MISSING before the first tick.
    cpuAverage = Property(float, _get_cpu_average, notify=tick)
    cpuPeak = Property(float, _get_cpu_peak, notify=tick)
    # From /proc/cpuinfo at startup: "" / MISSING when the field is absent.
    cpuModel = Property(str, _get_cpu_model, constant=True)
    cpuCores = Property(int, _get_cpu_cores, constant=True)
    cpuThreads = Property(int, _get_cpu_threads, constant=True)
    # Up to TOP_CPU_PROCESSES dicts, busiest first: name and cpu (0..100).
    topCpuProcesses = Property(list, _get_top_cpu_processes, notify=tick)

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

    hostname = Property(str, _get_hostname, notify=systemInfoChanged)
    osName = Property(str, _get_os_name, notify=systemInfoChanged)
    shellName = Property(str, _get_shell_name, notify=systemInfoChanged)
    # Seconds.
    uptime = Property(float, _get_uptime, notify=systemInfoChanged)
    # Days since install; notified every tick so it turns over at midnight.
    osAgeDays = Property(int, _get_os_age_days, notify=tick)

    def _get_avatar_url(self) -> str:
        return self._avatar_url

    # file:// URL, or "" when no avatar is configured.
    avatarUrl = Property(str, _get_avatar_url, constant=True)
