"""Collects network data lol :)"""

import time
from dataclasses import dataclass

PROC_NET_DEV = "/proc/net/dev"
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
        self.previous_sample: NetInfo = parse_net_proc(read_net_proc())
        self.previous_collect_time: float = time.monotonic()

    def get_net_speed(self) -> NetSpeed:
        current_sample = parse_net_proc(read_net_proc())
        current_collect_time = time.monotonic()
        time_delta = current_collect_time - self.previous_collect_time
        speed = calc_net_speed(self.previous_sample, current_sample, time_delta)

        self.previous_collect_time = current_collect_time
        self.previous_sample = current_sample
        return speed


def read_net_proc() -> str:
    with open(PROC_NET_DEV, "r") as proc:
        raw_proc = proc.read()
        return raw_proc


def parse_net_proc(raw_proc: str) -> NetInfo:
    download, upload = 0, 0
    split_lines = raw_proc.splitlines()
    for line in split_lines[VALID_LINES]:
        name, rest = line.split(":", 1)
        if name.strip() == "lo":
            continue
        fields = rest.split()
        download += int(fields[DOWNLOAD_POSITION])
        upload += int(fields[UPLOAD_POSITION])
    return NetInfo(download, upload)


def calc_net_speed(previous_sample: NetInfo, current_sample: NetInfo, time_delta: float) -> NetSpeed:
    if time_delta == 0:
        raise RuntimeError("0 seconds since last sample, not enough time to measure speed")

    download_speed: float = (current_sample.download - previous_sample.download) / time_delta
    upload_speed: float = (current_sample.upload - previous_sample.upload) / time_delta
    return NetSpeed(max(0.0, download_speed), max(0.0, upload_speed))


if __name__ == "__main__":
    sampler = NetSample()
    while True:
        time.sleep(1)
        net_speed = sampler.get_net_speed()
        print(net_speed)
