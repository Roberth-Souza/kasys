"""Collects temperatures from devices"""

import glob
import os
import re
import warnings
from dataclasses import dataclass

SYS_HWMON_CHIPS = "/sys/class/hwmon/hwmon*"
SYS_HWMON_PREFIX = "/sys/block/"
SYS_HWMON_SUFFIX = "/device/hwmon"


@dataclass(frozen=True)
class Sensor:
    label: str
    celsius: float


def find_disk_hwmon(disk_name: str) -> list[str]:
    nvme_folders: list[str] = glob.glob(f"{SYS_HWMON_PREFIX}{disk_name}{SYS_HWMON_SUFFIX}[0-9]*")
    sata_folders: list[str] = glob.glob(f"{SYS_HWMON_PREFIX}{disk_name}{SYS_HWMON_SUFFIX}/hwmon[0-9]*")
    return sata_folders + nvme_folders


def parse_path_number(path: str) -> int:
    name = os.path.basename(path)
    match = re.search(r"\d+", name)
    if match is None:
        raise ValueError(f"Could not find number in {path}")
    return int(match.group())


def sort_paths(paths: list[str]) -> list[str]:
    return sorted(paths, key=parse_path_number)


def read_hwmon_path() -> list[str]:
    paths = sort_paths(glob.glob(SYS_HWMON_CHIPS))
    return paths


def read_sensors(folder: str) -> list[Sensor]:
    sensor_paths = sort_paths(glob.glob(f"{folder}/temp*_input"))
    result: list[Sensor] = []
    for input_path in sensor_paths:
        prefix = input_path.removesuffix("_input")
        try:
            with open(prefix + "_label", "r") as raw:
                label = raw.read().strip()
        except FileNotFoundError:
            label = os.path.basename(prefix)

        try:
            with open(input_path, "r") as raw:
                result.append(Sensor(label, parse_temperature(raw.read())))
        except ValueError, OSError:
            continue

    return result


def parse_temperature(temperature: str) -> float:
    return int(temperature) / 1000


def read_chip_name(path: str) -> str:
    location = path + "/name"
    with open(location, "r") as raw:
        return raw.read().strip()


def make_unique_name(name: str, result: dict[str, list[Sensor]]) -> str:
    candidate = name
    counter = 1
    while candidate in result:
        counter += 1
        candidate = name + str(counter)

    return candidate


def get_sensors_info() -> dict[str, list[Sensor]]:
    collected_paths = read_hwmon_path()
    result: dict[str, list[Sensor]] = {}
    for path in collected_paths:
        try:
            raw_name = read_chip_name(path)
            sensors = read_sensors(path)
        except FileNotFoundError:
            continue
        if sensors:
            name = make_unique_name(raw_name, result)
            result[name] = sensors

    return result


def get_disk_temperature(disk_name: str) -> float | None:
    disk_folders = find_disk_hwmon(disk_name)
    if not disk_folders:
        return None

    sensor_list = read_sensors(disk_folders[0])
    if not sensor_list:
        warnings.warn(f"Could not find any sensors in {disk_folders[0]}")
        return None

    for sensor in sensor_list:
        if sensor.label == "Composite":
            return sensor.celsius

    return sensor_list[0].celsius


if __name__ == "__main__":
    print(get_sensors_info())
    print(get_disk_temperature("nvme0n1"))
    print(get_disk_temperature("sda"))
