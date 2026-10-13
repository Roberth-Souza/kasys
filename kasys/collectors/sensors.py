"""Collects temperatures from devices"""

import glob
import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Sensor:
    label: str
    celsius: float


def path_number(path: str) -> int:
    name = os.path.basename(path)
    match = re.search(r"\d+", name)
    if match is None:
        raise ValueError(f"Could not find number in {path}")
    return int(match.group())


def sort_paths(paths: list[str]) -> list[str]:
    return sorted(paths, key=path_number)


def collect_hwmon_path() -> list[str]:
    paths = sort_paths(glob.glob("/sys/class/hwmon/hwmon*"))
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

        with open(input_path, "r") as raw:
            result.append(Sensor(label, parse_temperature(raw.read())))

    return result


def parse_temperature(temperature: str) -> float:
    return int(temperature) / 1000


def extract_chip_name(path: str) -> str:
    location = path + "/name"
    with open(location, "r") as raw:
        return raw.read().strip()


def unique_name(name: str, result: dict[str, list[Sensor]]) -> str:
    candidate = name
    counter = 1
    while candidate in result:
        counter += 1
        candidate = name + str(counter)

    return candidate


def get_sensors_info() -> dict[str, list[Sensor]]:
    collected_paths = collect_hwmon_path()
    result: dict[str, list[Sensor]] = {}
    for path in collected_paths:
        raw_name = extract_chip_name(path)
        sensors = read_sensors(path)
        if sensors:
            name = unique_name(raw_name, result)
            result[name] = sensors

    return result


if __name__ == "__main__":
    print(get_sensors_info())
