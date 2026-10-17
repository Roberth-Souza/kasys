"""Collects Ram memory data :)"""

from dataclasses import dataclass

PROC_MEMINFO = "/proc/meminfo"
BYTES_PER_KB = 1024


@dataclass(frozen=True)
class MemInfo:
    total: int
    available: int
    used: int


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


if __name__ == "__main__":
    print(get_mem_info())
