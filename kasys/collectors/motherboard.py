"""Collects motherboard data :)"""

import os
import warnings
from dataclasses import dataclass
from datetime import date, datetime

MOTHERBOARD_INFO_PATH = "/sys/class/dmi/id/"
TRASH_INFO = {"To Be Filled By O.E.M.", "Default string"}


@dataclass(frozen=True)
class BoardInfo:
    name: str | None
    vendor: str | None
    bios_version: str | None
    bios_date: date | None


def read_dmi_field(name: str) -> str:
    info_path = os.path.join(MOTHERBOARD_INFO_PATH, name)
    with open(info_path, "r") as raw:
        return raw.read().strip()


def try_read_dmi_field(name: str) -> str | None:
    try:
        field = read_dmi_field(name)
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read dmi field")
        return None

    if not field or field in TRASH_INFO:
        return None
    return field


def parse_dmi_date(raw_date: str) -> date:
    return datetime.strptime(raw_date, "%m/%d/%Y").date()


def get_motherboard_info() -> BoardInfo:
    board_name = try_read_dmi_field("board_name")
    board_vendor = try_read_dmi_field("board_vendor")
    bios_version = try_read_dmi_field("bios_version")
    raw_date = try_read_dmi_field("bios_date")
    if raw_date:
        try:
            bios_date = parse_dmi_date(raw_date)
        except ValueError:
            warnings.warn(f"Could not parse date, {raw_date} is an invalid date format")
            bios_date = None
    else:
        bios_date = None

    return BoardInfo(board_name, board_vendor, bios_version, bios_date)


if __name__ == "__main__":
    print(get_motherboard_info())
