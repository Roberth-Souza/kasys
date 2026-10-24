"""Collects session and system info: desktop, display server, OS, uptime, shell"""

import os
import pwd
from dataclasses import dataclass

OS_NAME_PATH = ("/etc/os-release", "/usr/lib/os-release")
PROC_HOSTNAME = "/proc/sys/kernel/hostname"
PROC_UPTIME = "/proc/uptime"


@dataclass(frozen=True)
class SessionInfo:
    desktop: str | None
    display_server: str | None


@dataclass(frozen=True)
class SysInfo:
    hostname: str
    os_name: str
    uptime: float
    shell_name: str


def read_desktop() -> str | None:
    return os.environ.get("XDG_CURRENT_DESKTOP")


def read_display_server() -> str | None:
    wayland_socket = os.environ.get("WAYLAND_DISPLAY")
    if wayland_socket is None:
        if os.environ.get("DISPLAY") is None:
            return None
        return "x11"
    return "wayland"


def read_hostname_proc() -> str:
    with open(PROC_HOSTNAME, "r") as info:
        hostname_info = info.read()
        return hostname_info.strip()


def read_uptime_proc() -> str:
    with open(PROC_UPTIME, "r") as info:
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
        if line.startswith("PRETTY_NAME="):
            parsed_line = line.split("=", 1)
            pretty_name = parsed_line[1].strip("\"'")
            if not pretty_name:
                return "Linux"
            return pretty_name
    return "Linux"  # os_name not found


def read_shell_name() -> str:
    user_uid = os.getuid()
    user_passwd = pwd.getpwuid(user_uid)
    return os.path.basename(user_passwd.pw_shell)


def get_session_info() -> SessionInfo:
    desktop = read_desktop()
    display_server = read_display_server()
    return SessionInfo(desktop, display_server)


def get_sys_info() -> SysInfo:
    hostname = read_hostname_proc()
    unparsed_os_name = read_os_name()
    os_name = parse_os_name(unparsed_os_name)
    unparsed_uptime = read_uptime_proc()
    uptime = parse_uptime_proc(unparsed_uptime)
    shell_name = read_shell_name()
    return SysInfo(hostname, os_name, uptime, shell_name)


if __name__ == "__main__":
    print(get_session_info())
    print(get_sys_info())
