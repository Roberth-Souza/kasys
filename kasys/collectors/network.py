"""Collects network data lol :)"""

import time
from dataclasses import dataclass

VALID_LINES = slice(2, None)
DOWNLOAD_POSITION = 0
UPLOAD_POSITION = 8


@dataclass(frozen=True)
class NetInfo:
    download: int
    upload: int


@dataclass(frozen=True)
class NetSpeed:
    download: float
    upload: float


class NetSample:
    def __init__(self) -> None:
        self.previous_sample: NetInfo = parse_network_proc(read_net_proc())
        self.previous_collect_time: float = time.monotonic()

    def get_net_speed(self) -> NetSpeed:
        current_sample = parse_network_proc(read_net_proc())
        current_collect_time = time.monotonic()
        time_delta = current_collect_time - self.previous_collect_time
        speed = calculates_net_speed(self.previous_sample, current_sample, time_delta)

        self.previous_collect_time = current_collect_time
        self.previous_sample = current_sample
        return speed


def calculates_net_speed(previous_sample: NetInfo, current_sample: NetInfo, time_delta: float) -> NetSpeed:
    if time_delta == 0:
        raise RuntimeError("0 seconds since last sample, not enough time to measure speed")

    download_difference: float = (current_sample.download - previous_sample.download) / time_delta
    upload_difference: float = (current_sample.upload - previous_sample.upload) / time_delta
    return NetSpeed(max(0.0, download_difference), max(0.0, upload_difference))


def read_net_proc() -> str:
    with open("/proc/net/dev", "r") as proc:
        raw_proc = proc.read()
        return raw_proc


def parse_network_proc(raw_proc: str) -> NetInfo:
    download, upload = 0, 0
    splitted_lines = raw_proc.splitlines()
    for line in splitted_lines[VALID_LINES]:
        name, rest = line.split(":", 1)
        if name.strip() == "lo":
            continue
        fields = rest.split()
        download += int(fields[DOWNLOAD_POSITION])
        upload += int(fields[UPLOAD_POSITION])
    return NetInfo(download, upload)


if __name__ == "__main__":
    previous_sample = NetSample()
    while True:
        time.sleep(1)
        net_speed = previous_sample.get_net_speed()
        print(net_speed)
