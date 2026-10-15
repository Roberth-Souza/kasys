"""
Collects data about running processes
"""

import os
import time
from dataclasses import dataclass

from kasys.collectors import cpu

PROC_FOLDER = "/proc"
RSS_POSITION = 21
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
CPU_UTIME_POSITION = 11
CPU_STIME_POSITION = 12


@dataclass(frozen=True)
class Process:
    pid: int
    name: str
    mem_bytes: int
    cpu_percent: float


class ProcessSample:
    def __init__(self) -> None:
        self.previous_ticks: dict[int, int] = read_all_ticks()
        self.previous_tick_total: int = calculates_total_tick()

    def calculates_total_tick_delta(self) -> int:
        current_tick_total: int = calculates_total_tick()
        total_tick_delta = current_tick_total - self.previous_tick_total
        self.previous_tick_total = current_tick_total
        return total_tick_delta

    @staticmethod
    def calculates_tick_delta(pid: int, current_tick: int, previous_ticks: dict[int, int]) -> int:
        if pid not in previous_ticks:
            delta = 0
        else:
            delta = current_tick - previous_ticks[pid]
        return delta

    @staticmethod
    def calculates_process_tick_percentage(process_delta: int, total_tick_delta: int) -> float:
        if total_tick_delta == 0:
            return 0.0
        process_tick_percentage = process_delta / total_tick_delta * 100
        return process_tick_percentage

    def returns_process(self) -> list[Process]:
        pids_list = list_pids()
        parsed_pid_list = parse_pid_list(pids_list)
        total_tick_delta = self.calculates_total_tick_delta()
        processes: list[Process] = []
        current_ticks: dict[int, int] = {}
        for pid in parsed_pid_list:
            try:
                stat = read_parsed_pid(pid)
                split_stats = split_stat_fields(stat)
                name = parse_process_name(stat)
                pages = parse_rss(split_stats)
                rss_bytes = page_to_bytes(pages)
                cpu_tick = parse_cpu_ticks(split_stats)
                current_ticks[pid] = cpu_tick
                process_delta = self.calculates_tick_delta(pid, cpu_tick, self.previous_ticks)
                process_tick_percentage = self.calculates_process_tick_percentage(process_delta, total_tick_delta)
                process = Process(pid=pid, name=name, mem_bytes=rss_bytes, cpu_percent=process_tick_percentage)
                processes.append(process)

            except FileNotFoundError, ProcessLookupError:
                continue

        self.previous_ticks = current_ticks
        return processes


def calculates_total_tick() -> int:
    raw_proc = cpu.read_cpu_proc()
    parsed_proc = cpu.parse_stat(raw_proc)
    proc_sum = cpu.calc_proc_sum(parsed_proc).total
    return proc_sum


def read_all_ticks() -> dict[int, int]:
    """This runs only once on startup"""
    pids_list = list_pids()
    parsed_pid_list = parse_pid_list(pids_list)
    pid_tick: dict[int, int] = {}
    for pid in parsed_pid_list:
        try:
            stat = read_parsed_pid(pid)
            split_stats = split_stat_fields(stat)
            cpu_tick = parse_cpu_ticks(split_stats)
            pid_tick[pid] = cpu_tick
        except FileNotFoundError, ProcessLookupError:
            continue
    return pid_tick


def list_pids() -> list[str]:
    raw_pids = os.listdir(PROC_FOLDER)
    return raw_pids


def parse_pid_list(raw_pids: list[str]) -> list[int]:
    return [int(pid) for pid in raw_pids if pid.isdigit()]


def read_parsed_pid(pid: int) -> str:
    with open(f"{PROC_FOLDER}/{pid}/stat", "r") as raw_process:
        process = raw_process.read()
    return process


def split_stat_fields(process: str) -> list[str]:
    start = process.rfind(")")
    return process[start + 1 :].split()


def parse_process_name(process: str) -> str:
    start = process.find("(")
    finish = process.rfind(")")
    return process[start + 1 : finish]


def parse_rss(parsed_stat_field: list[str]) -> int:
    return int(parsed_stat_field[RSS_POSITION])


def page_to_bytes(pages: int) -> int:
    return pages * PAGE_SIZE


def parse_cpu_ticks(split_stats: list[str]) -> int:
    return int(split_stats[CPU_STIME_POSITION]) + int(split_stats[CPU_UTIME_POSITION])


if __name__ == "__main__":
    previous_sample = ProcessSample()
    while True:
        print(previous_sample.returns_process())
        time.sleep(1)
