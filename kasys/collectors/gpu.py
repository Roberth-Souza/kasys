"""Collects GPU data"""

import glob
import os
import subprocess
import warnings
from dataclasses import dataclass

GPU_DRIVER_DIRECTORY = "/sys/class/drm/card*/device/driver"
HWMON_PREFIX = "hwmon/hwmon*/"
AMD_GPU_IDS_PATH = "/usr/share/libdrm/amdgpu.ids"
AMD_GPU = "amdgpu"
GPU_BUSY_KEY = "gpu_busy_percent"
VRAM_USED_KEY = "mem_info_vram_used"
VRAM_TOTAL_KEY = "mem_info_vram_total"
FAN_KEY = "fan1_input"
CLOCK_KEY = "freq1_input"
POWER_AVERAGE_KEY = "power1_average"
POWER_CAP_KEY = "power1_cap"
GPU_MEMORY_LINE_IN_KERNEL_LOG = "RAM width"
AMD_MEMORY_TYPES = {"DDR", "HBM"}
REVISION_KEY = "revision"
DEVICE_KEY = "device"


@dataclass(frozen=True)
class GpuStats:
    busy_percentage: int
    vram_total: int
    vram_used: int
    fan_rpm: int | None
    clock: int | None
    power_average: int | None
    power_cap: int | None


def read_kernel_log() -> subprocess.CompletedProcess[str]:
    return subprocess.run(["journalctl", "-k", "-b", "-o", "cat"], text=True, check=False, capture_output=True)


def parse_vram_type(kernel_log: str) -> str | None:
    for line in kernel_log.splitlines():
        if GPU_MEMORY_LINE_IN_KERNEL_LOG in line:
            memory_type = line.split()[-1].strip()
            if any(e in memory_type for e in AMD_MEMORY_TYPES):
                return memory_type
            else:
                raise ValueError(f"Unrecognized VRAM type '{memory_type}'")
    return None


def solve_symlink(raw_path: str) -> str:
    real_path = os.readlink(raw_path)
    return os.path.basename(real_path)


def find_gpu_dir() -> str | None:
    for path in glob.glob(GPU_DRIVER_DIRECTORY):
        if solve_symlink(path) == AMD_GPU:
            return os.path.dirname(path)
    warnings.warn(f"Could not find amd_gpu on {GPU_DRIVER_DIRECTORY}, please make sure you have an AMD GPU")
    return None


def read_value(gpu_info_path: str, key: str) -> str:
    with open(os.path.join(gpu_info_path, key), "r") as raw:
        return raw.read().strip()


def find_hwmon_path(gpu_dir: str) -> str | None:
    hwmon_paths = glob.glob(os.path.join(gpu_dir, HWMON_PREFIX))
    if not hwmon_paths:
        warnings.warn(f"Could not find any hwmon_paths in {gpu_dir}")
        return None
    return hwmon_paths[0]


def read_hwmon_info(hwmon_path: str | None, key: str) -> int | None:
    if hwmon_path is None:
        return None
    path = os.path.join(hwmon_path, key)
    try:
        with open(path, "r") as raw_info:
            return int(raw_info.read())
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read hwmon")
        return None


def read_amd_gpu_ids() -> str | None:
    try:
        with open(AMD_GPU_IDS_PATH, "r") as raw:
            return raw.read()
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read {AMD_GPU_IDS_PATH}")
        return None


def parse_amd_gpu_ids(amdgpu_ids: str, device_id: str, revision_id: str) -> str | None:
    for line in amdgpu_ids.splitlines():
        split_line = [e.strip() for e in line.split(",")]
        if split_line[0] == device_id and split_line[1] == revision_id:
            return split_line[2]
    warnings.warn(f"Could not find gpu_name in {AMD_GPU_IDS_PATH}")
    return None


def get_gpu_name(gpu_dir: str) -> str | None:

    device_id = read_value(gpu_dir, DEVICE_KEY).removeprefix("0x").upper()
    revision_id = read_value(gpu_dir, REVISION_KEY).removeprefix("0x").upper()
    amd_gpu_ids = read_amd_gpu_ids()
    if amd_gpu_ids is not None:
        gpu_name = parse_amd_gpu_ids(amd_gpu_ids, device_id, revision_id)
        return gpu_name

    return None


def get_gpu_stats(gpu_dir: str, hwmon_path: str | None) -> GpuStats:

    gpu_busy_percent = int(read_value(gpu_dir, GPU_BUSY_KEY))
    gpu_vram_total = int(read_value(gpu_dir, VRAM_TOTAL_KEY))
    gpu_vram_used = int(read_value(gpu_dir, VRAM_USED_KEY))
    gpu_rpm = read_hwmon_info(hwmon_path, FAN_KEY)
    gpu_clock = read_hwmon_info(hwmon_path, CLOCK_KEY)
    gpu_power_average = read_hwmon_info(hwmon_path, POWER_AVERAGE_KEY)
    gpu_power_cap = read_hwmon_info(hwmon_path, POWER_CAP_KEY)

    return GpuStats(
        busy_percentage=gpu_busy_percent,
        vram_total=gpu_vram_total,
        vram_used=gpu_vram_used,
        fan_rpm=gpu_rpm,
        clock=gpu_clock,
        power_average=gpu_power_average,
        power_cap=gpu_power_cap,
    )


def get_vram_type() -> str | None:
    try:
        kernel_log = read_kernel_log()
    except OSError as error:
        warnings.warn(f"Received {error} while trying to read kernel log")
        return None

    if kernel_log.returncode != 0:
        warnings.warn(f"{kernel_log.stderr}")
        return None

    try:
        vram_type = parse_vram_type(kernel_log.stdout)
    except ValueError as error:
        warnings.warn(f"{error}")
        return None

    if vram_type is None:
        warnings.warn(f"Could not find '{GPU_MEMORY_LINE_IN_KERNEL_LOG}' line in kernel log")

    return vram_type


if __name__ == "__main__":
    gpu_dir = find_gpu_dir()
    if gpu_dir is not None:
        hwmon_path = find_hwmon_path(gpu_dir)
        print(get_gpu_stats(gpu_dir, hwmon_path))
        print(get_gpu_name(gpu_dir))
        print(get_vram_type())
