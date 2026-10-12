"""Collects temperatures from devices"""

import glob
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Sensor:
    label: str
    celsius: float


def collect_sensors(folder: str) -> list[Sensor]:
    sensor_paths = sorted(glob.glob(f"{folder}/temp*_input"))
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


if __name__ == "__main__":
    print(collect_sensors("/sys/class/hwmon/hwmon1"))
    print(collect_sensors("/sys/class/hwmon/hwmon4"))
