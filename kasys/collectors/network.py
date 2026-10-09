"""Collects network data lol :)"""

import time
from dataclasses import dataclass


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

    def calculates_net_sample(self) -> NetSpeed:
        current_sample = parse_network_proc(read_net_proc())
        current_collect_time = time.monotonic()
        time_delta = current_collect_time - self.previous_collect_time
        if time_delta == 0:
            raise RuntimeError(
                "0 seconds since last sample, not enough time to measure speed"
            )
        download_difference = (
            current_sample.download - self.previous_sample.download
        ) / time_delta
        upload_difference = (
            current_sample.upload - self.previous_sample.upload
        ) / time_delta

        self.previous_collect_time = current_collect_time
        self.previous_sample = current_sample
        return NetSpeed(max(download_difference, 0.0), max(upload_difference, 0.0))


def read_net_proc() -> str:
    with open("/proc/net/dev", "r") as proc:
        raw_proc = proc.read()
        return raw_proc


def parse_network_proc(raw_proc: str) -> NetInfo:
    download, upload = 0, 0
    splitted_lines = raw_proc.splitlines()
    for line in splitted_lines[2:]:
        name, rest = line.split(":", 1)
        if name.strip() == "lo":
            continue
        fields = rest.split()
        download += int(fields[0])
        upload += int(fields[8])
    return NetInfo(download, upload)


if __name__ == "__main__":
    previous_sample = NetSample()
    while True:
        time.sleep(1)
        net_speed = previous_sample.calculates_net_sample()
        print(net_speed)
