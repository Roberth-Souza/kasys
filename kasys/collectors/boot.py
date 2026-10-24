"""Collects boot timings from systemd"""

import os
import string
import subprocess
import warnings
from dataclasses import dataclass

MESSAGE_ID_HASH = "b07a249cd024414a82dd00cd181378ff"
UNIT_SECONDS = {"us": 1e-6, "ms": 1e-3, "s": 1, "min": 60, "h": 3600}


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
    print(get_boot_info())
    print(get_recent_boots())
    print(get_critical_chain())
