"""Collects disk data"""

import glob
import os
import time
import warnings
from dataclasses import dataclass

SYS_BLOCK_PREFIX = "/sys/block/"
SYS_BLOCK_DEVICES = "/sys/block/*/device"
SYS_CLASS_BLOCK = "/sys/class/block"
PROC_DISKSTATS = "/proc/diskstats"
PROC_MOUNTS = "/proc/self/mounts"
DEV_PREFIX = "/dev/"
BYTES_PER_SECTOR = 512  # /sys/block/*/size unit
DISK_MODEL = "device/model"
DISK_SIZE = "size"
DISK_ROTATIONAL = "queue/rotational"
DISK_NAME_IN_SYS = 3
DISK_NAME_IN_PROC = 2
IO_TICKS_POSITION = 12
DISK_PARTITION_NAME = 0
DISK_PARTITION_FOLDER = 1


@dataclass(frozen=True)
class DiskInfo:
    total: int
    used: int
    available: int


@dataclass(frozen=True)
class DiskIdentity:
    model: str | None
    size: int | None  # bytes
    rotational: bool | None  # True = HD
    nvme: bool


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


def read_disk_paths() -> list[str]:
    disk_paths = glob.glob(SYS_BLOCK_DEVICES)
    return disk_paths


def parse_disk_names(disk_paths: list[str]) -> list[str]:
    disk_list = [path.split("/")[DISK_NAME_IN_SYS] for path in disk_paths]
    return disk_list


def read_disk_stats() -> str:
    with open(PROC_DISKSTATS, "r") as raw:
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
        raise RuntimeError(f"Could not find disk names in {PROC_DISKSTATS}")

    if len(disk_io_tick) < len(disk_names):
        expected_disks = set(disk_names)
        found_disks = set(disk_io_tick)
        not_found_disks = expected_disks - found_disks
        warnings.warn(f"Could not find {', '.join(not_found_disks)} in {PROC_DISKSTATS}")


def read_disk_mounts() -> str:
    with open(PROC_MOUNTS, "r") as raw:
        raw_mount_proc = raw.read()
    return raw_mount_proc


def read_disk_field(disk_name: str, field: str) -> str:
    with open(os.path.join(SYS_BLOCK_PREFIX, disk_name, field), "r") as raw:
        return raw.read().strip()


def try_read_disk_field(disk_name: str, field: str) -> str | None:
    try:
        value = read_disk_field(disk_name, field)
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read {field} of {disk_name}")
        return None

    if not value:
        return None
    return value


def parse_disk_size(raw_size: str | None) -> int | None:
    if raw_size is None:
        return None
    try:
        size = int(raw_size) * BYTES_PER_SECTOR
    except ValueError:
        warnings.warn(f"Could not parse disk size, {raw_size!r} is not a number")
        return None
    return size


def parse_rotational(raw_rotational: str | None) -> bool | None:
    if raw_rotational is None:
        return None
    if raw_rotational == "1":
        rotational = True
    elif raw_rotational == "0":
        rotational = False
    else:
        warnings.warn(f"Could not parse rotational, {raw_rotational!r} is not 0 or 1")
        rotational = None
    return rotational


def decode_mount_path(disk_partition_folder: str) -> str:
    r"""We need to decode the mount path because it is escaped in /proc/self/mounts.
    Spaces are represented as \040, tabs as \011, newlines as \012, and backslashes as \134."""
    return (
        disk_partition_folder.replace(r"\040", " ").replace(r"\011", "\t").replace(r"\012", "\n").replace(r"\134", "\\")
    )


def parse_disk_mounts(raw_mount_proc: str) -> dict[str, str]:
    lines = [line.split() for line in raw_mount_proc.splitlines()]
    raw_partitions: dict[str, str] = {}
    for fields in lines:
        device = fields[DISK_PARTITION_NAME]
        if device.startswith(DEV_PREFIX):
            disk_partition_name = os.path.basename(device)
            disk_partition_folder = fields[DISK_PARTITION_FOLDER]
            decoded_partition_folder = decode_mount_path(disk_partition_folder)
            raw_partitions[disk_partition_name] = decoded_partition_folder
    return raw_partitions


def map_partitions_to_disks(partitions: dict[str, str], disk_names: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for partition in partitions:
        path = os.path.realpath(f"{SYS_CLASS_BLOCK}/{partition}/..")
        disk_name = os.path.basename(path)
        if disk_name in disk_names:
            result[partition] = disk_name
    return result


def calc_partition_space(stats: os.statvfs_result) -> DiskInfo:
    total = stats.f_frsize * stats.f_blocks
    used = (stats.f_blocks - stats.f_bfree) * stats.f_frsize
    available = stats.f_bavail * stats.f_frsize
    return DiskInfo(total, used, available)


def read_partition_space(parsed_disk_mounts: dict[str, str]) -> dict[str, DiskInfo]:
    partition_info: dict[str, DiskInfo] = {}
    for partition, mount_point in parsed_disk_mounts.items():
        try:
            stats = os.statvfs(mount_point)
        except OSError as error:
            warnings.warn(f"os.statvfs failed: {error}")
            continue
        partition_info[partition] = calc_partition_space(stats)
    return partition_info


def pick_largest_partition(
    mapped_partitions: dict[str, str],
    partition_space: dict[str, DiskInfo],
) -> dict[str, DiskInfo]:
    max_partitions: dict[str, DiskInfo] = {}
    for partition, disk in mapped_partitions.items():
        if partition not in partition_space:
            continue
        space = partition_space[partition]
        if disk not in max_partitions or max_partitions[disk].total < space.total:
            max_partitions[disk] = space
    return max_partitions


def get_disk_io_ticks() -> dict[str, int]:
    disk_paths = read_disk_paths()
    parsed_disk_names = parse_disk_names(disk_paths)
    raw_disk_stats = read_disk_stats()
    parsed_disk_stats = parse_disk_stats(parsed_disk_names, raw_disk_stats)
    check_missing_disks(parsed_disk_names, parsed_disk_stats)
    return parsed_disk_stats


def get_disk_space() -> dict[str, DiskInfo]:
    raw_disk_mounts = read_disk_mounts()
    parsed_disk_mounts = parse_disk_mounts(raw_disk_mounts)
    disk_paths = read_disk_paths()
    parsed_disk_names = parse_disk_names(disk_paths)
    mapped_partitions = map_partitions_to_disks(parsed_disk_mounts, parsed_disk_names)
    partition_space = read_partition_space(parsed_disk_mounts)
    largest_partition_disk_space = pick_largest_partition(mapped_partitions, partition_space)
    return largest_partition_disk_space


def get_disk_identity() -> dict[str, DiskIdentity]:
    disks: dict[str, DiskIdentity] = {}
    disk_names = parse_disk_names(read_disk_paths())
    for disk_name in disk_names:
        disk_model = try_read_disk_field(disk_name, DISK_MODEL)
        raw_disk_size = try_read_disk_field(disk_name, DISK_SIZE)
        disk_size = parse_disk_size(raw_disk_size)
        raw_disk_rotational = try_read_disk_field(disk_name, DISK_ROTATIONAL)
        disk_rotational = parse_rotational(raw_disk_rotational)
        disk_is_nvme = disk_name.startswith("nvme")

        disks[disk_name] = DiskIdentity(model=disk_model, size=disk_size, rotational=disk_rotational, nvme=disk_is_nvme)

    return disks


if __name__ == "__main__":
    print(get_disk_space())
    sampler = DiskSample()
    print(get_disk_identity())
    while True:
        time.sleep(1)
        print(sampler.get_disk_activity())
