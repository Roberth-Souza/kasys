"""Collects disk data"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DiskInfo:
    total: int
    usage: int
    available: int


def get_disk_info() -> DiskInfo:

    disk = os.statvfs("/")
    total = disk.f_frsize * disk.f_blocks
    used = (disk.f_blocks - disk.f_bfree) * disk.f_frsize
    available = disk.f_bavail * disk.f_frsize
    return DiskInfo(total, used, available)


if __name__ == "__main__":
    print(get_disk_info())
