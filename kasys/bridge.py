"""Qt glue: polls the collectors on a timer and hands their readings to QML.

The bridge adapts to the collectors, never the other way round: it converts
units (memory comes in kB, everything else in bytes) and keeps the graph
histories. Formatting for display is the QML side's job.

Errors: a collector raises when the world is broken (a missing /proc file, a
parse failure). The bridge catches it, reports it once on stderr and shows
the fallback value, so one broken source never takes the whole window down.
"""

from __future__ import annotations

import os
import sys
from collections import deque
from collections.abc import Callable

from PySide6.QtCore import Property, QCoreApplication, QObject, QTimer, Signal, Slot

from kasys.collectors import cpu, disk, mem, network
from kasys.collectors import sys as sysinfo

TICK_MS = 1000
# One minute of samples at one per second: what every graph spans.
HISTORY_LENGTH = 60
BYTES_PER_KB = 1024
# What a property reads when its source failed; QML draws it as "--".
MISSING = -1

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

        self._cpu_usage = 0.0
        self._cpu_freq = MISSING
        self._mem: mem.MemInfo | None = None
        self._disk: disk.DiskInfo | None = None
        self._net = network.NetSpeed(download=0.0, upload=0.0)

        self._cpu_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._mem_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._disk_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._down_history: deque[float] = deque(maxlen=HISTORY_LENGTH)
        self._up_history: deque[float] = deque(maxlen=HISTORY_LENGTH)

        # System info is read once per opening: at launch, and again by
        # main.py each time a daemon's window is shown.
        self._sys: sysinfo.SysInfo | None = None
        self._install_date = ""
        self.read_system_info()

        # Memory and disk need no previous reading, so the first frame already
        # has them. CPU and network are deltas and wait for the first tick.
        self._read_levels()

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._sample)
        self._timer.start()

    def read_system_info(self) -> None:
        self._sys = _read("system info", sysinfo.get_sys_info, None)
        install_date = _read("install date", sysinfo.get_install_date, None)
        self._install_date = install_date.date().isoformat() if install_date else ""
        self.systemInfoChanged.emit()

    def _read_levels(self) -> None:
        self._mem = _read("memory", mem.get_mem_info, self._mem)
        self._disk = _read("disk", disk.get_disk_info, self._disk)

    @Slot()
    def _sample(self) -> None:
        self._cpu_usage = _read("cpu usage", self._cpu_sample.get_cpu_usage, 0.0)
        self._cpu_freq = _read("cpu frequency", cpu.get_cpu_freq, MISSING)
        self._net = _read("network", self._net_sample.get_net_speed, network.NetSpeed(0.0, 0.0))
        self._read_levels()

        self._cpu_history.append(self._cpu_usage)
        self._mem_history.append(self._mem_percent())
        self._disk_history.append(self._disk_percent())
        self._down_history.append(self._net.download)
        self._up_history.append(self._net.upload)
        self.tick.emit()

    def _mem_percent(self) -> float:
        if self._mem is None:
            return 0.0
        return _percent(self._mem.memory_usage, self._mem.total_memory)

    def _disk_percent(self) -> float:
        if self._disk is None:
            return 0.0
        # Same ratio `df` prints: the root-reserved blocks count as neither.
        return _percent(self._disk.usage, self._disk.usage + self._disk.available)

    # -- CPU ---------------------------------------------------------------
    def _get_cpu_usage(self) -> float:
        return self._cpu_usage

    def _get_cpu_freq(self) -> int:
        return self._cpu_freq

    def _get_cpu_history(self) -> list[float]:
        return list(self._cpu_history)

    def _get_core_count(self) -> int:
        return os.cpu_count() or 0

    cpuUsage = Property(float, _get_cpu_usage, notify=tick)
    # kHz, or MISSING when cpufreq is not exposed.
    cpuFreq = Property(int, _get_cpu_freq, notify=tick)
    cpuHistory = Property(list, _get_cpu_history, notify=tick)
    # Only sizes the per-core placeholder rows until a collector fills them.
    coreCount = Property(int, _get_core_count, constant=True)

    # -- memory (bytes; floats because Qt's int is 32-bit) -------------------
    def _get_mem_total(self) -> float:
        return float(self._mem.total_memory * BYTES_PER_KB) if self._mem else MISSING

    def _get_mem_used(self) -> float:
        return float(self._mem.memory_usage * BYTES_PER_KB) if self._mem else MISSING

    def _get_mem_available(self) -> float:
        return float(self._mem.available_memory * BYTES_PER_KB) if self._mem else MISSING

    def _get_mem_percent(self) -> float:
        return self._mem_percent()

    def _get_mem_history(self) -> list[float]:
        return list(self._mem_history)

    memTotal = Property(float, _get_mem_total, notify=tick)
    memUsed = Property(float, _get_mem_used, notify=tick)
    memAvailable = Property(float, _get_mem_available, notify=tick)
    memPercent = Property(float, _get_mem_percent, notify=tick)
    memHistory = Property(list, _get_mem_history, notify=tick)

    # -- disk (bytes) --------------------------------------------------------
    def _get_disk_total(self) -> float:
        return float(self._disk.total) if self._disk else MISSING

    def _get_disk_used(self) -> float:
        return float(self._disk.usage) if self._disk else MISSING

    def _get_disk_percent(self) -> float:
        return self._disk_percent()

    def _get_disk_history(self) -> list[float]:
        return list(self._disk_history)

    diskTotal = Property(float, _get_disk_total, notify=tick)
    diskUsed = Property(float, _get_disk_used, notify=tick)
    diskPercent = Property(float, _get_disk_percent, notify=tick)
    diskHistory = Property(list, _get_disk_history, notify=tick)

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

    def _get_uptime(self) -> float:
        return self._sys.uptime if self._sys else MISSING

    def _get_install_date(self) -> str:
        return self._install_date

    hostname = Property(str, _get_hostname, notify=systemInfoChanged)
    osName = Property(str, _get_os_name, notify=systemInfoChanged)
    # Seconds.
    uptime = Property(float, _get_uptime, notify=systemInfoChanged)
    # ISO date, or "" when pacman.log could not be read.
    installDate = Property(str, _get_install_date, notify=systemInfoChanged)
