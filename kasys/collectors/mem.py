"""Collects Ram memory data :)"""

import os
import subprocess
import warnings
from dataclasses import dataclass
from subprocess import CompletedProcess

PROC_MEMINFO = "/proc/meminfo"
BYTES_PER_KB = 1024
MEMORY_SLOTS_FIELD = "MEMORY_ARRAY_NUM_DEVICES"
MEMORY_DEVICE_PREFIX = "MEMORY_DEVICE_"
SIZE_FIELD_SUFFIX = "SIZE"
LOCATOR_FIELD_SUFFIX = "LOCATOR"
BANK_LOCATOR_FIELD_SUFFIX = "BANK_LOCATOR"
TYPE_FIELD_SUFFIX = "TYPE"
SPEED_FIELD_SUFFIX = "CONFIGURED_SPEED_MTS"
UNKNOWN_MEMORY_TYPE = "UNKNOWN"
CHANNEL_MARKER = "CHANNEL"


@dataclass(frozen=True)
class MemInfo:
    total: int
    available: int
    used: int


@dataclass(frozen=True)
class MemoryModule:
    locator: str | None
    channel: str | None
    size: int
    type: str | None
    speed: int | None


@dataclass(frozen=True)
class MemoryLayout:
    total_slots: int | None
    slots: list[MemoryModule | None]


def read_mem_proc() -> str:
    with open(PROC_MEMINFO, "r") as data:
        memory_data = data.read()
        return memory_data


def parse_mem_stats(memory_data: str) -> dict[str, int]:
    split_lines = memory_data.splitlines()
    removed_spaces = [line.split() for line in split_lines]
    integer_stats: dict[str, int] = {}
    for line in removed_spaces:
        if line[0] == "MemTotal:":
            integer_stats["MemTotal"] = int(line[1]) * BYTES_PER_KB
        if line[0] == "MemAvailable:":
            integer_stats["MemAvailable"] = int(line[1]) * BYTES_PER_KB

        if len(integer_stats) == 2:
            break

    return integer_stats


def calc_usage(total_memory: int, available_memory: int) -> MemInfo:
    memory_usage = total_memory - available_memory
    return MemInfo(total_memory, available_memory, memory_usage)


def get_mem_info() -> MemInfo:
    collected_mem_info = read_mem_proc()
    parsed_mem_info = parse_mem_stats(collected_mem_info)
    mem_data = calc_usage(parsed_mem_info["MemTotal"], parsed_mem_info["MemAvailable"])
    return mem_data


def read_udevadm() -> CompletedProcess[str]:
    env = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(
        ["udevadm", "info", "-q", "property", "-p", "/sys/devices/virtual/dmi/id"],
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )


def try_read_udevadm() -> str | None:
    try:
        udevadm = read_udevadm()
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read udevadm")
        return None

    if udevadm.returncode != 0:
        warnings.warn(f"{udevadm.stderr}")
        return None

    return udevadm.stdout


def parse_udevadm_fields(udevadm: str) -> dict[str, str]:
    parsed_udevadm: dict[str, str] = {}
    for line in udevadm.splitlines():
        field, separator, value = line.partition("=")
        if not separator:
            continue
        parsed_udevadm[field] = value

    return parsed_udevadm


def parse_total_slots(parsed_udevadm: dict[str, str]) -> int | None:
    total = parsed_udevadm.get(MEMORY_SLOTS_FIELD)
    if total is None:
        warnings.warn("Could not find total memory slots in udevadm")
        return None

    # TODO: int() raises ValueError on a non-numeric value; None + warning instead.
    return int(total)


def parse_memory_channel(memory_field: str | None) -> str | None:
    if memory_field is not None:
        _, _, channel = memory_field.upper().partition(CHANNEL_MARKER)
        channel = channel.strip()
        if channel:
            return channel[0]

    return None


def parse_slot(parsed_udevadm: dict[str, str], slot_index: int) -> MemoryModule | None:
    memory_size = parsed_udevadm.get(f"{MEMORY_DEVICE_PREFIX}{slot_index}_{SIZE_FIELD_SUFFIX}")
    if memory_size is None:
        return None

    # TODO: int() raises ValueError on a non-numeric SIZE or SPEED; handle like the total.
    memory_size = int(memory_size)
    memory_locator = parsed_udevadm.get(f"{MEMORY_DEVICE_PREFIX}{slot_index}_{LOCATOR_FIELD_SUFFIX}")
    bank_locator = parsed_udevadm.get(f"{MEMORY_DEVICE_PREFIX}{slot_index}_{BANK_LOCATOR_FIELD_SUFFIX}")
    memory_type = parsed_udevadm.get(f"{MEMORY_DEVICE_PREFIX}{slot_index}_{TYPE_FIELD_SUFFIX}")
    memory_speed = parsed_udevadm.get(f"{MEMORY_DEVICE_PREFIX}{slot_index}_{SPEED_FIELD_SUFFIX}")

    if memory_type is not None and memory_type.upper() == UNKNOWN_MEMORY_TYPE:
        memory_type = None

    if memory_speed is not None:
        memory_speed = int(memory_speed)

    memory_channel = parse_memory_channel(bank_locator)
    if memory_channel is None:
        memory_channel = parse_memory_channel(memory_locator)

    return MemoryModule(
        locator=memory_locator,
        channel=memory_channel,
        size=memory_size,
        type=memory_type,
        speed=memory_speed,
    )


def get_memory_layout() -> MemoryLayout | None:
    memory_list: list[MemoryModule | None] = []
    udevadm = try_read_udevadm()
    if udevadm is None:
        return None

    parsed_udevadm = parse_udevadm_fields(udevadm)
    total_slots = parse_total_slots(parsed_udevadm)
    if total_slots:
        for slot in range(total_slots):
            memory_module = parse_slot(parsed_udevadm, slot)
            memory_list.append(memory_module)

    return MemoryLayout(total_slots, memory_list)


if __name__ == "__main__":
    print(get_mem_info())
    print(get_memory_layout())
