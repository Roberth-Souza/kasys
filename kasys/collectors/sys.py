"""Collects System Info"""

import os
import pwd
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


@dataclass(frozen=True)
class HostInfo:
    kernel: str
    arch: str
    uefi: bool
    secure_boot: bool | None
    boot_loader: str | None
    packages: int | None


@dataclass(frozen=True)
class SysInfo:
    hostname: str
    os_name: str
    uptime: float
    shell_name: str


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


if __name__ == "__main__":
    print(get_sys_info())
    print(get_host_info())
    print(get_install_date())
