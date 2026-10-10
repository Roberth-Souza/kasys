"""Collects disk data"""

import glob
import os
import time
import warnings
from dataclasses import dataclass

DISK_NAME_IN_SYS = 3
DISK_NAME_IN_PROC = 2
IO_TICKS_POSITION = 12


@dataclass(frozen=True)
class DiskInfo:
    total: int
    used: int
    available: int


class DiskSample:
    def __init__(self) -> None:
        self.previous_sample: dict[str, int] = get_disk_io_ticks()
        self.previous_time: float = time.monotonic()

    def get_disk_activity(self) -> dict[str, float]:
        current_sample = get_disk_io_ticks()
        current_time = time.monotonic()
        delta_time = current_time - self.previous_time
        if delta_time == 0:
            raise RuntimeError("0 seconds since last sample, not enough time to measure disk activity")
        activity: dict[str, float] = {}
        for name, io_tick in current_sample.items():
            if name not in self.previous_sample:
                continue
            # io_ticks is in milliseconds, delta_time in seconds
            active_percentage = (io_tick - self.previous_sample[name]) / (delta_time * 1000) * 100
            activity[name] = min(active_percentage, 100)
        self.previous_sample = current_sample
        self.previous_time = current_time
        return activity


def read_disk_names() -> list[str]:
    disk_names = glob.glob("/sys/block/*/device")
    return disk_names


def parse_disk_names(disk_names: list[str]) -> list[str]:
    disk_list = [name.split("/")[DISK_NAME_IN_SYS] for name in disk_names]
    return disk_list


def read_disk_stats() -> str:
    with open("/proc/diskstats", "r") as raw:
        disk_stats = raw.read()
    return disk_stats


def parse_disk_stats(disk_names: list[str], disk_stats: str) -> dict[str, int]:
    disk_io_tick: dict[str, int] = {}
    split_lines = [line.split() for line in disk_stats.splitlines()]
    for line in split_lines:
        disk_name = line[DISK_NAME_IN_PROC]
        if disk_name in disk_names:
            io_tick = line[IO_TICKS_POSITION]
            disk_io_tick[disk_name] = int(io_tick)
            if len(disk_io_tick) == len(disk_names):
                break
    return disk_io_tick


def check_missing_disks(disk_names: list[str], disk_io_tick: dict[str, int]) -> None:
    if not disk_io_tick:
        raise RuntimeError("Could not find disk names in /proc/diskstats")

    if len(disk_io_tick) < len(disk_names):
        expected_disks = set(disk_names)
        found_disks = set(disk_io_tick)
        not_found_disks = expected_disks - found_disks
        warnings.warn(f"Could not find {', '.join(not_found_disks)} in /proc/diskstats")


def get_disk_info() -> DiskInfo:
    disk = os.statvfs("/")
    total = disk.f_frsize * disk.f_blocks
    used = (disk.f_blocks - disk.f_bfree) * disk.f_frsize
    available = disk.f_bavail * disk.f_frsize
    return DiskInfo(total, used, available)


def get_disk_io_ticks() -> dict[str, int]:
    raw_disk_names = read_disk_names()
    parsed_disk_names = parse_disk_names(raw_disk_names)
    raw_disk_stats = read_disk_stats()
    parsed_disk_stats = parse_disk_stats(parsed_disk_names, raw_disk_stats)
    check_missing_disks(parsed_disk_names, parsed_disk_stats)
    return parsed_disk_stats


if __name__ == "__main__":
    print(get_disk_info())
    disk_sample = DiskSample()
    while True:
        time.sleep(1)
        print(disk_sample.get_disk_activity())
