"""Collects host info: kernel, architecture, firmware and boot setup"""

import os
import warnings
from dataclasses import dataclass

from kasys.collectors import pacman

UEFI_PATH = "/sys/firmware/efi"
SECURE_BOOT_PATH = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
BOOT_LOADER_PATH = "/sys/firmware/efi/efivars/LoaderInfo-4a67b082-0a4c-41cf-b6c7-440b29bb8c4f"
AFTER_ATRIBUTE_BYTES = slice(4, None)


@dataclass(frozen=True)
class HostInfo:
    kernel: str
    arch: str
    uefi: bool
    secure_boot: bool | None
    boot_loader: str | None
    packages: int | None


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


def get_host_info() -> HostInfo:
    kernel = read_uname_release()
    arch = read_uname_machine()
    uefi = uefi_is_active()
    secure_boot = try_read_secure_boot(uefi)
    boot_loader = try_read_boot_loader(uefi)
    packages = pacman.try_read_total_packages()

    return HostInfo(kernel, arch, uefi, secure_boot, boot_loader, packages)


if __name__ == "__main__":
    print(get_host_info())
