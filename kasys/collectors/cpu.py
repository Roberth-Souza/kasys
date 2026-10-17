"""
Collects data from the CPU
"""

import glob
import re
import time
import warnings
from dataclasses import dataclass

PROC_STAT = "/proc/stat"
PROC_CPU_INFO = "/proc/cpuinfo"
CPU_FILES = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"
IDLE_POSITION = 3
IOWAIT_POSITION = 4
MODEL_NAME_KEY = "model name"
CPU_NAME_CUTS = (" @", " w/", " with")
CPU_NAME_JUNK = ("(R)", "(TM)", " CPU")
CORES_COUNT_KEY = "cpu cores"
THREADS_COUNT_KEY = "siblings"
VALID_CPU_STATS = slice(1, 9)


@dataclass(frozen=True)
class CpuTimes:
    total: int
    idle: int


@dataclass(frozen=True)
class CpuInfo:
    model: str | None
    cores: int | None
    threads: int | None


class CpuSample:
    def __init__(self) -> None:
        self.previous_sample: CpuTimes = calc_proc_sum(parse_stat(read_stat_proc()))

    def get_cpu_usage(self) -> float:
        current_sample: CpuTimes = calc_proc_sum(parse_stat(read_stat_proc()))
        usage = calc_usage_percentage(self.previous_sample, current_sample)
        self.previous_sample = current_sample
        return usage


def read_stat_proc() -> str:
    with open(PROC_STAT, "r") as proc:
        cpu_stats = proc.read()
        return cpu_stats


def parse_stat(cpu_stats: str) -> list[int]:
    first_line = cpu_stats.splitlines()[0]
    split_first_line = first_line.split()
    integer_stats = [int(stat) for stat in split_first_line[VALID_CPU_STATS]]
    return integer_stats


def calc_proc_sum(integer_stats: list[int]) -> CpuTimes:
    total = sum(integer_stats)
    idle = integer_stats[IDLE_POSITION] + integer_stats[IOWAIT_POSITION]
    return CpuTimes(total=total, idle=idle)


def calc_usage_percentage(previous_sample: CpuTimes, current_sample: CpuTimes) -> float:
    delta_idle = current_sample.idle - previous_sample.idle
    delta_total = current_sample.total - previous_sample.total
    if delta_total == 0:
        return 0.0
    usage = 100 * (delta_total - delta_idle) / delta_total
    return usage


def read_cpuinfo_proc() -> str:
    with open(PROC_CPU_INFO, "r") as raw_info:
        raw_proc = raw_info.read()
    return raw_proc


def parse_cpu_info(raw_proc: str, key: str) -> str | None:
    split_proc = raw_proc.splitlines()
    for line in split_proc:
        if line.startswith(key):
            return line.split(":", 1)[1].strip()
    warnings.warn(f"Could not find {key} in {PROC_CPU_INFO}")
    return None


def parse_cpu_model_name(raw_cpu_model: str) -> str:
    name = raw_cpu_model
    for cut in CPU_NAME_CUTS:
        name = name.split(cut, 1)[0]
    for junk in CPU_NAME_JUNK:
        name = name.replace(junk, "")
    name = re.sub(r"\s*\d+-Core Processor", "", name)
    name = re.sub(r"\d+th Gen ", "", name)
    return name.strip()


def read_cpu_frequencies() -> list[int]:
    cpu_files = glob.glob(CPU_FILES)
    if not cpu_files:
        raise RuntimeError(f"Could not find any cpu file to read in {CPU_FILES}")
    cpu_frequencies: list[int] = []
    for freq_file in cpu_files:
        with open(freq_file, "r") as freq:
            cpu_frequencies.append(int(freq.read().strip()))
    return cpu_frequencies


def calc_frequency(cpu_frequencies: list[int]) -> int:
    return sum(cpu_frequencies) // len(cpu_frequencies)


def get_cpu_info() -> CpuInfo:
    raw_proc = read_cpuinfo_proc()
    raw_cpu_model = parse_cpu_info(raw_proc, MODEL_NAME_KEY)

    if raw_cpu_model is not None:
        parsed_cpu_model = parse_cpu_model_name(raw_cpu_model)
    else:
        parsed_cpu_model = None

    raw_cpu_cores = parse_cpu_info(raw_proc, CORES_COUNT_KEY)
    raw_cpu_threads = parse_cpu_info(raw_proc, THREADS_COUNT_KEY)
    cpu_cores = int(raw_cpu_cores) if raw_cpu_cores is not None else None
    cpu_threads = int(raw_cpu_threads) if raw_cpu_threads is not None else None

    return CpuInfo(model=parsed_cpu_model, cores=cpu_cores, threads=cpu_threads)


def get_cpu_freq() -> int:
    cpu_frequencies = read_cpu_frequencies()
    frequency = calc_frequency(cpu_frequencies)
    return frequency


if __name__ == "__main__":
    print(get_cpu_info())
    sampler = CpuSample()
    while True:
        print(f"frequencia da CPU: {get_cpu_freq()}")
        time.sleep(1)
        usage = sampler.get_cpu_usage()
        print(f"{usage:.0f}%")
