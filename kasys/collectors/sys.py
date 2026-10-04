"""Collects System Info"""

from dataclasses import dataclass
from datetime import datetime

OS_NAME_PATH = ("/etc/os-release", "/usr/lib/os-release")


@dataclass(frozen=True)
class SysInfo:
    hostname: str
    os_name: str
    uptime: float


def read_hostname_proc() -> str:
    with open("/proc/sys/kernel/hostname", "r") as info:
        hostname_info = info.read()
        return hostname_info.strip()


def read_os_age() -> str:
    with open("/var/log/pacman.log", "r") as info:
        unparsed_os_age = info.readline()
        return unparsed_os_age


def parse_os_age(unparsed_os_age: str) -> datetime:
    striped_age = unparsed_os_age.split()
    if not striped_age:
        raise ValueError("pacman.log is empty")
    parsed_age = striped_age[0][1:-1]
    date_ = datetime.fromisoformat(parsed_age)
    return date_


def read_uptime_proc() -> str:
    with open("/proc/uptime", "r") as info:
        uptime_info = info.read()
        return uptime_info


def parse_uptime_proc(uptime_info: str) -> float:
    return float(uptime_info.split()[0])


def read_os_name() -> str:
    for path in OS_NAME_PATH:
        try:
            with open(path, "r") as info:
                os_proc = info.read()
                return os_proc
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"os-release not found in {OS_NAME_PATH}")


def parse_os_name(os_proc: str) -> str:
    for line in os_proc.splitlines():
        if "PRETTY_NAME" in line:
            parsed_line = line.split("=", 1)
            return parsed_line[1].strip("\"'")
    return "Linux"  # os_name not found


def get_sys_info() -> SysInfo:
    hostname = read_hostname_proc()
    unparsed_os_name = read_os_name()
    os_name = parse_os_name(unparsed_os_name)
    unparsed_uptime = read_uptime_proc()
    uptime = parse_uptime_proc(unparsed_uptime)
    return SysInfo(hostname, os_name, uptime)


def get_install_date() -> datetime:
    unparsed_os_age = read_os_age()
    os_age = parse_os_age(unparsed_os_age)
    return os_age


if __name__ == "__main__":
    print(get_sys_info())
    print(get_install_date())
