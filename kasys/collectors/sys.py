"""Collects System Info"""

import os
import pwd
import string
import subprocess
import warnings
from dataclasses import dataclass
from datetime import datetime

OS_NAME_PATH = ("/etc/os-release", "/usr/lib/os-release")
PACKAGE_LIST_PATH = "/var/lib/pacman/local"
UEFI_PATH = "/sys/firmware/efi"
SECURE_BOOT_PATH = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
BOOT_LOADER_PATH = "/sys/firmware/efi/efivars/LoaderInfo-4a67b082-0a4c-41cf-b6c7-440b29bb8c4f"
AFTER_ATRIBUTE_BYTES = slice(4, None)
PROC_HOSTNAME = "/proc/sys/kernel/hostname"
PROC_UPTIME = "/proc/uptime"
PACMAN_LOG = "/var/log/pacman.log"
SYSTEM_UPGRADE_LOG = "starting full system upgrade"
TRANSACTION_COMPLETED_LOG = "transaction completed"
PACMAN_RUNNING_LOG = "[PACMAN] Running"
MESSAGE_ID_HASH = "b07a249cd024414a82dd00cd181378ff"
UNIT_SECONDS = {"us": 1e-6, "ms": 1e-3, "s": 1, "min": 60, "h": 3600}


@dataclass(frozen=True)
class HostInfo:
    kernel: str
    arch: str
    uefi: bool
    secure_boot: bool | None
    boot_loader: str | None
    packages: int | None


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


@dataclass(frozen=True)
class BootInfo:
    phases: dict[str, float]
    total: float


@dataclass(frozen=True)
class ChainUnit:
    name: str
    seconds: float


class BootNotFinishedError(Exception):
    """systemd has not finished booting yet; try again later"""


def read_systemd_analyze(*subcommand: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(["systemd-analyze", *subcommand], capture_output=True, check=False, text=True, env=env)


def read_recent_boots() -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(
        ["journalctl", "_PID=1", f"MESSAGE_ID={MESSAGE_ID_HASH}", "-o", "cat", "-n", "7"],
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )


def parse_timespan(text: str) -> float:
    total = 0.0
    for token in text.split():  # "1min 4.615s" -> ["1min", "4.615s"]
        number = token.rstrip(string.ascii_lowercase)  # "4.615s" -> "4.615"
        unit = token[len(number) :]  # "4.615s" -> "s"
        if unit not in UNIT_SECONDS:
            raise ValueError(f"unknown time unit in {token!r}")
        total += float(number) * UNIT_SECONDS[unit]
    return total


def parse_critical_chain(critical_chain: str) -> list[ChainUnit]:
    result: list[ChainUnit] = []
    _, critical_chain_tree = critical_chain.split("\n\n", 1)
    makes_boot_slower = [e for e in critical_chain_tree.splitlines() if "+" in e]
    for line in makes_boot_slower:
        name = line.split()[0][2:]
        parsed_time = parse_timespan(line.partition("+")[-1])
        chain_unit = ChainUnit(name, parsed_time)
        result.append(chain_unit)
    return result


def parse_recent_boots(boots: str) -> list[float]:
    total_list: list[float] = []
    for line in boots.splitlines():
        _, total_text = line.removeprefix("Startup finished in").strip().split(" = ")
        total = parse_timespan(total_text.strip().removesuffix("."))
        total_list.append(total)

    return total_list


def parse_systemd_analyze(raw_systemd: str) -> BootInfo:
    phases: dict[str, float] = {}
    first_line = raw_systemd.splitlines()[0]
    phases_text, total_text = first_line.removeprefix("Startup finished in").strip().split(" = ")
    total = parse_timespan(total_text.strip())
    split_phases = phases_text.split("+")
    for phase in split_phases:
        start = phase.find("(")
        end = phase.rfind(")")
        phase_name = phase[start + 1 : end]

        phases[phase_name] = parse_timespan(phase[0:start].strip())

    return BootInfo(phases, total)


def read_desktop() -> str | None:
    return os.environ.get("XDG_CURRENT_DESKTOP")


def read_display_server() -> str | None:
    wayland_socket = os.environ.get("WAYLAND_DISPLAY")
    if wayland_socket is None:
        if os.environ.get("DISPLAY") is None:
            return None
        return "x11"
    return "wayland"


def read_uname_release() -> str:
    return os.uname().release


def read_uname_machine() -> str:
    return os.uname().machine


def uefi_is_active() -> bool:
    return os.path.isdir(UEFI_PATH)


def read_secure_boot() -> bytes:
    with open(SECURE_BOOT_PATH, "rb") as raw:
        return raw.read()


def secure_boot_is_active(raw_secure_boot: bytes) -> bool:
    return raw_secure_boot[-1] == 1


def try_read_secure_boot(uefi: bool) -> bool | None:
    if not uefi:
        return None

    try:
        raw_secure_boot = read_secure_boot()
        secure_boot = secure_boot_is_active(raw_secure_boot)
        return secure_boot
    except (OSError, IndexError) as error:
        warnings.warn(f"{error}")
        return None


def read_boot_loader() -> bytes:
    with open(BOOT_LOADER_PATH, "rb") as raw:
        return raw.read()


def parse_boot_loader(raw_boot_loader: bytes) -> str:
    removed_atributes = raw_boot_loader[AFTER_ATRIBUTE_BYTES]
    decoded_boot_loader = removed_atributes.decode("utf-16-le")
    return decoded_boot_loader.removesuffix("\x00")


def try_read_boot_loader(uefi: bool) -> str | None:
    if not uefi:
        return None
    try:
        raw_boot_loader = read_boot_loader()
        boot_loader = parse_boot_loader(raw_boot_loader)
    except UnicodeDecodeError as error:
        warnings.warn(f"{error}")
        return None

    except FileNotFoundError:
        return None

    if boot_loader == "":
        return None
    return boot_loader


def count_package_list() -> int:
    packages = os.listdir(PACKAGE_LIST_PATH)
    total_packages = 0
    for package in packages:
        package_path = os.path.join(PACKAGE_LIST_PATH, package)
        if os.path.isdir(package_path):
            total_packages += 1
        else:
            continue

    return total_packages


def try_read_total_packages() -> int | None:
    try:
        packages = count_package_list()
    except FileNotFoundError:
        warnings.warn("Can't find packages in a non arch distro")
        packages = None

    return packages


def read_hostname_proc() -> str:
    with open(PROC_HOSTNAME, "r") as info:
        hostname_info = info.read()
        return hostname_info.strip()


def read_pacman_log() -> str:
    with open(PACMAN_LOG, "r") as info:
        return info.read()


def parse_last_update(raw_pacman_log: str) -> datetime | None:
    split_line = raw_pacman_log.splitlines()
    if not split_line:
        raise ValueError("pacman.log is empty")
    reversed_pacman_log_list = list(reversed(split_line))
    transaction_completed = False
    for line in reversed_pacman_log_list:
        if TRANSACTION_COMPLETED_LOG in line:
            transaction_completed = True
            continue
        if SYSTEM_UPGRADE_LOG in line:
            if transaction_completed:
                timestamp = line.split()[0][1:-1]
                return datetime.fromisoformat(timestamp)
            continue
        if PACMAN_RUNNING_LOG in line:
            transaction_completed = False

    warnings.warn("Could not find system update on pacman_log")
    return None


def read_install_date() -> str:
    with open(PACMAN_LOG, "r") as info:
        unparsed_install_date = info.readline()
        return unparsed_install_date


def parse_install_date(unparsed_install_date: str) -> datetime:
    split_line = unparsed_install_date.split()
    if not split_line:
        raise ValueError("pacman.log is empty")
    timestamp = split_line[0][1:-1]
    install_date = datetime.fromisoformat(timestamp)
    return install_date


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


def try_read_systemd_analyze(*subcommand: str) -> str | None:
    try:
        result = read_systemd_analyze(*subcommand)
    except OSError as error:
        warnings.warn(f"could not run systemd-analyze: {error}")
        return None
    stdout = result.stdout
    if result.returncode != 0:
        if "not yet finished" in result.stderr:
            raise BootNotFinishedError("systemd has not finished booting yet; try again later")
        else:
            warnings.warn(f"{result.stderr}")
            return None

    return stdout


def get_boot_info() -> BootInfo | None:
    stdout = try_read_systemd_analyze()
    if stdout is None:
        return None

    try:
        boot_info = parse_systemd_analyze(stdout)
    except (ValueError, IndexError) as error:
        warnings.warn(f"received {error} while trying to parse systemd.stdout")
        return None

    return boot_info


def get_critical_chain() -> list[ChainUnit] | None:
    critical_chain_tree = try_read_systemd_analyze("critical-chain")

    if critical_chain_tree is None:
        return None

    try:
        chain_list = parse_critical_chain(critical_chain_tree)
    except (ValueError, IndexError) as error:
        warnings.warn(f"Received {error} while trying to parse critical-chain")
        return None

    return chain_list


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


def get_host_info() -> HostInfo:
    kernel = read_uname_release()
    arch = read_uname_machine()
    uefi = uefi_is_active()
    secure_boot = try_read_secure_boot(uefi)
    boot_loader = try_read_boot_loader(uefi)
    packages = try_read_total_packages()

    return HostInfo(kernel, arch, uefi, secure_boot, boot_loader, packages)


def get_install_date() -> datetime:
    unparsed_install_date = read_install_date()
    install_date = parse_install_date(unparsed_install_date)
    return install_date


def get_last_update() -> datetime | None:
    try:
        raw_pacman_log = read_pacman_log()
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read pacman log")
        return None

    try:
        last_update_date = parse_last_update(raw_pacman_log)
    except ValueError as error:
        warnings.warn(f"{error}")
        return None

    return last_update_date


def get_recent_boots() -> list[float] | None:
    try:
        recent_boots = read_recent_boots()
        recent_boots_stdout = recent_boots.stdout

    except OSError as error:
        warnings.warn(f"Received {error} while trying to read journalctl")
        return None

    if recent_boots.returncode != 0:
        warnings.warn(f"{recent_boots.stderr.strip()}")
        return None

    try:
        last_boots = parse_recent_boots(recent_boots_stdout)
    except ValueError as error:
        warnings.warn(f"Received {error} while trying to parse journalctl")
        return None

    if not last_boots:
        return None

    return last_boots


if __name__ == "__main__":
    print(get_session_info())
    print(get_sys_info())
    print(get_host_info())
    print(get_install_date())
    print(get_boot_info())
    print(get_recent_boots())
    print(get_last_update())
    print(get_critical_chain())
