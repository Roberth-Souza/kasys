"""
Collects data from the CPU
"""

import glob
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class CpuTimes:
    total: int
    idle: int


IDLE_POSITION = 3
IOWAIT_POSITION = 4
VALID_CPU_STATS = slice(1, 9)


class CpuSample:
    def __init__(self) -> None:
        self.previous_sample: CpuTimes = calc_proc_sum(parse_stat(read_cpu_proc()))

    def get_cpu_usage(self) -> float:
        current_sample: CpuTimes = calc_proc_sum(parse_stat(read_cpu_proc()))
        delta = calculates_delta(self.previous_sample, current_sample)
        self.previous_sample = current_sample
        return delta


def read_cpu_proc() -> str:
    with open("/proc/stat", "r") as proc:
        cpu_stats = proc.read()
        return cpu_stats


def read_cpu_frequencies() -> list[int]:
    cpu_files = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")
    if not cpu_files:
        raise RuntimeError(
            "Could not find any cpu file to read in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"
        )
    cpu_frequencies: list[int] = []
    for freq_file in cpu_files:
        with open(freq_file, "r") as freq:
            cpu_frequencies.append(int(freq.read().strip()))
    return cpu_frequencies


def calculates_frequency(cpu_frequencies: list[int]) -> int:
    return sum(cpu_frequencies) // len(cpu_frequencies)


def parse_stat(cpu_stats: str) -> list[int]:
    first_line = cpu_stats.splitlines()[0]
    splitted_first_line = first_line.split()
    integer_stats = [int(stat) for stat in splitted_first_line[VALID_CPU_STATS]]
    return integer_stats


def calc_proc_sum(integer_stats: list[int]) -> CpuTimes:
    total = sum(integer_stats)
    idle = integer_stats[IDLE_POSITION] + integer_stats[IOWAIT_POSITION]
    return CpuTimes(total=total, idle=idle)


def calculates_delta(previous_sample: CpuTimes, current_sample: CpuTimes) -> float:
    delta_idle = current_sample.idle - previous_sample.idle
    delta_total = current_sample.total - previous_sample.total
    if delta_total == 0:
        return 0.0
    delta = 100 * (delta_total - delta_idle) / delta_total
    return delta


def get_cpu_freq() -> int:
    cpu_frequencies = read_cpu_frequencies()
    frequency = calculates_frequency(cpu_frequencies)
    return frequency


if __name__ == "__main__":
    previous_sample = CpuSample()
    while True:
        print(f"frequencia da CPU: {get_cpu_freq()}")
        time.sleep(1)
        delta_percentage = previous_sample.get_cpu_usage()
        print(f"{delta_percentage:.0f}%")
