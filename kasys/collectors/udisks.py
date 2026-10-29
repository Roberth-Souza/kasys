"""Collects udisk data"""

import json
import os
import subprocess
import warnings
from dataclasses import dataclass
from subprocess import CompletedProcess
from typing import cast

UDISKS = "org.freedesktop.UDisks2"
UDISKS_BLOCK_PREFIX = "/org/freedesktop/UDisks2/block_devices/"
BLOCK_INTERFACE = "org.freedesktop.UDisks2.Block"
NVME_INTERFACE = "org.freedesktop.UDisks2.NVMe.Controller"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


@dataclass(frozen=True)
class NvmeSmart:
    critical_warnings: list[str] | None
    power_on_hours: int | None
    percent_used: int | None
    media_errors: int | None
    bytes_written: int | None


def read_busctl(*args: str) -> CompletedProcess[str]:
    env = {**os.environ, "LC_ALL": "C"}
    output = subprocess.run(
        ["busctl", "--json=short", *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    return output


def try_read_udisk(*args: str) -> str | None:
    try:
        udisk = read_busctl(*args)
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read udisk")
        return None

    if udisk.returncode != 0:
        warnings.warn(f"{udisk.stderr.strip()}")
        return None

    return udisk.stdout


def parse_udisk(udisk_stdout: str) -> str | None:
    try:
        parsed_udisk = cast(object, json.loads(udisk_stdout))
    except json.JSONDecodeError:
        warnings.warn(f"{udisk_stdout} is not a valid Json format")
        return None

    if not isinstance(parsed_udisk, dict):
        warnings.warn("parsed udisk is not a valid dictionary format")
        return None

    data = cast(dict[str, object], parsed_udisk).get("data")
    if isinstance(data, str):
        return data
    warnings.warn(f"{data} is not a valid string")
    return None


def parse_busctl(busctl_stdout: str) -> dict[str, object] | None:
    try:
        parsed_busctl = cast(object, json.loads(busctl_stdout))
    except json.JSONDecodeError:
        warnings.warn(f"{busctl_stdout} is not a valid Json format")
        return None

    if not isinstance(parsed_busctl, dict):
        warnings.warn("parsed busctl is not a valid dictionary format")
        return None

    outer_data = cast(dict[str, object], parsed_busctl).get("data")
    if not isinstance(outer_data, list):
        warnings.warn(f"{outer_data} is not a list")
        return None

    outer_list = cast(list[object], outer_data)
    if len(outer_list) != 1:
        warnings.warn(f"{outer_list} is not a one-item list")
        return None

    properties = outer_list[0]
    if not isinstance(properties, dict):
        warnings.warn(f"{properties} is not a valid dictionary format")
        return None

    unwrapped: dict[str, object] = {}
    for name, wrapped in cast(dict[str, object], properties).items():
        if not isinstance(wrapped, dict):
            warnings.warn(f"{name}: {wrapped} is not a valid dictionary format")
            continue
        unwrapped[name] = cast(dict[str, object], wrapped).get("data")

    return unwrapped


def get_int_field(values: dict[str, object], key: str) -> int | None:
    value = values.get(key)
    if isinstance(value, int):
        return value
    warnings.warn(f"{key}: {value} is not an int")
    return None


def get_str_list_field(values: dict[str, object], key: str) -> list[str] | None:
    value = values.get(key)
    if not isinstance(value, list):
        warnings.warn(f"{key}: {value} is not a list")
        return None

    strings: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            warnings.warn(f"{key}: {item} is not a string")
            return None
        strings.append(item)

    return strings


def get_nvme_smart(disk_name: str) -> NvmeSmart | None:
    drive_stdout = try_read_udisk("get-property", UDISKS, f"{UDISKS_BLOCK_PREFIX}{disk_name}", BLOCK_INTERFACE, "Drive")
    if drive_stdout is None:
        return None
    drive = parse_udisk(drive_stdout)
    if drive is None:
        return None

    properties_stdout = try_read_udisk("call", UDISKS, drive, PROPERTIES_INTERFACE, "GetAll", "s", NVME_INTERFACE)
    if properties_stdout is None:
        return None
    properties = parse_busctl(properties_stdout)
    if properties is None:
        return None

    attributes_stdout = try_read_udisk("call", UDISKS, drive, NVME_INTERFACE, "SmartGetAttributes", "a{sv}", "0")
    if attributes_stdout is None:
        return None
    attributes = parse_busctl(attributes_stdout)
    if attributes is None:
        return None

    smart = NvmeSmart(
        critical_warnings=get_str_list_field(properties, "SmartCriticalWarning"),
        power_on_hours=get_int_field(properties, "SmartPowerOnHours"),
        percent_used=get_int_field(attributes, "percent_used"),
        media_errors=get_int_field(attributes, "media_errors"),
        bytes_written=get_int_field(attributes, "total_data_written"),
    )
    return smart


if __name__ == "__main__":
    print(get_nvme_smart("nvme0n1"))
