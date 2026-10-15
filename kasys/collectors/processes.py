"""
Collects data about running processes
"""

import os

PROC_FOLDER = "/proc"
RSS_POSITION = 21
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")


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


if __name__ == "__main__":
    pids_list = list_pids()
    parsed_pid_list = parse_pid_list(pids_list)
    for pid in parsed_pid_list:
        try:
            stat = read_parsed_pid(pid)
            name = parse_process_name(stat)
            raw_rss = parse_rss(split_stat_fields(stat))
            rss_bytes = page_to_bytes(raw_rss)
        except FileNotFoundError:
            continue

        print(pid, name, " ", rss_bytes)
