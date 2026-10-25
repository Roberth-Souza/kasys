"""Guess? ... Yes , it collect's display data"""

import glob
import os
import warnings

DISPLAY_CARD_PREFIX = "/sys/class/drm/card*-"
EDID_BLOCK_SIZE = 128
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def read_display_edid(connector: str) -> bytes:
    display_edid_path = glob.glob(os.path.join(DISPLAY_CARD_PREFIX + connector, "edid"))
    if not display_edid_path:
        raise FileNotFoundError(f"no EDID file found for connector {connector}")
    with open(display_edid_path[0], "rb") as raw:
        return raw.read()


def parse_edid_size(edid: bytes) -> tuple[int, int] | None:
    if len(edid) < EDID_BLOCK_SIZE:
        warnings.warn(f"{len(edid)} is less than the minimum edid block size: {EDID_BLOCK_SIZE}")
        return None

    if edid[:8] != EDID_HEADER:
        warnings.warn(f"{edid[:8]} is not a valid edid header")
        return None
    edid_sizes: tuple[int, int] = edid[21], edid[22]
    if all(size > 0 for size in edid_sizes):
        return edid_sizes
    return None


def get_monitor_size(connector: str) -> tuple[int, int] | None:
    try:
        edid = read_display_edid(connector)
    except FileNotFoundError as error:
        warnings.warn(f"{error}")
        return None
    except OSError as error:
        warnings.warn(f"could not read EDID for {connector}: {error}")
        return None

    return parse_edid_size(edid)


if __name__ == "__main__":
    print(get_monitor_size("DP-2"))
