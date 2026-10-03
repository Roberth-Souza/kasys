"""
Collects data from the CPU
"""

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class CpuTimes:
    total: int
    idle: int


class Sample:
    def __init__(self) -> None:
        self.previous_sample: CpuTimes = calc_proc_sum(parse_stat(read_cpu_proc()))

    def calculates_sample(self) -> float:
        current_sample: CpuTimes = calc_proc_sum(parse_stat(read_cpu_proc()))
        delta = calculates_delta(self.previous_sample, current_sample)
        self.previous_sample = current_sample
        return delta


def calculates_delta(previous_sample: CpuTimes, current_sample: CpuTimes) -> float:
    delta_idle = current_sample.idle - previous_sample.idle
    delta_total = current_sample.total - previous_sample.total
    delta = 100 * (delta_total - delta_idle) / delta_total
    return delta


def parse_stat(cpu_stats: str) -> list[int]:
    """Since the proc/stat returns a string, we need to convert
    only the useful information to integers"""
    first_line = cpu_stats.splitlines()[0]
    splitted_first_line = first_line.split()
    integer_stats = [int(stat) for stat in splitted_first_line[1:9]]
    return integer_stats


def calc_proc_sum(integer_stats: list[int]) -> CpuTimes:
    """calculates the total cpu stats for both idle
    and total"""
    total = sum(integer_stats)
    idle = integer_stats[3] + integer_stats[4]
    return CpuTimes(total=total, idle=idle)


def read_cpu_proc() -> str:
    with open("/proc/stat", "r") as proc:
        cpu_stats = proc.read()
        return cpu_stats


if __name__ == "__main__":
    previous_sample = Sample()
    while True:
        time.sleep(1)
        delta_percentage = previous_sample.calculates_sample()
        print(f"{delta_percentage:.0f}%")
