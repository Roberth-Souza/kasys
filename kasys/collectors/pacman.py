"""Collects pacman data: installed packages, last update, install date"""

import os
import warnings
from datetime import datetime

PACKAGE_LIST_PATH = "/var/lib/pacman/local"
PACMAN_LOG = "/var/log/pacman.log"
SYSTEM_UPGRADE_LOG = "starting full system upgrade"
TRANSACTION_COMPLETED_LOG = "transaction completed"
PACMAN_RUNNING_LOG = "[PACMAN] Running"


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


if __name__ == "__main__":
    print(try_read_total_packages())
    print(get_install_date())
    print(get_last_update())
