"""Collects Ram memory data :)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemInfo:
    total_memory: int
    available_memory: int
    memory_usage: int


def read_mem_proc() -> str:
    with open("/proc/meminfo", "r") as data:
        memory_data = data.read()
        return memory_data


def parse_mem_stats(memory_data: str) -> dict[str, int]:
    splitted_lines = memory_data.splitlines()
    removed_spaces = [line.split() for line in splitted_lines]
    integer_stats: dict[str, int] = {}
    for line in removed_spaces:
        if line[0] == "MemTotal:":
            integer_stats["MemTotal"] = int(line[1])
        if line[0] == "MemAvailable:":
            integer_stats["MemAvailable"] = int(line[1])

        if len(integer_stats) == 2:
            break

    return integer_stats


def calculate_usage(total_memory: int, available_memory: int) -> MemInfo:
    memory_usage = total_memory - available_memory
    return MemInfo(total_memory, available_memory, memory_usage)


def get_mem_info() -> MemInfo:
    collected_mem_info = read_mem_proc()
    parsed_mem_info = parse_mem_stats(collected_mem_info)
    mem_data = calculate_usage(
        parsed_mem_info["MemTotal"], parsed_mem_info["MemAvailable"]
    )
    return mem_data


if __name__ == "__main__":
    print(get_mem_info())
