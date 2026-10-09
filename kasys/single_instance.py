"""One overlay at a time, and the launcher key toggles it.

The window holds the keyboard exclusively, so two of them would fight over it.
The first launch takes an advisory `flock` on a lock file for its whole life
and writes its PID there; a second launch cannot take the lock, sends that PID
SIGUSR1 - the toggle: a daemon shows or hides its window, a plain run quits -
and exits. The kernel drops the lock with its owner, so a crash never leaves a
stale one behind. Linux only (`fcntl`).
"""

from __future__ import annotations

import fcntl
import os
import signal
from pathlib import Path


def _lock_path() -> Path:
    """Per-user runtime path: tmpfs when `XDG_RUNTIME_DIR` is set."""
    base = os.environ.get("XDG_RUNTIME_DIR") or str(Path.home() / ".cache")
    return Path(base) / "kasys.lock"


class SingleInstance:
    """Owns the run lock for this process, or closes the process that does."""

    def __init__(self) -> None:
        self._path = _lock_path()
        self._fd: int | None = None

    def acquire(self) -> bool:
        """True when this process is now the only instance.

        False when another one holds the lock; it has been told to quit, and
        the caller should exit without opening a window.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self._path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            _signal_owner(fd)
            os.close(fd)
            return False
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        self._fd = fd
        return True

    def release(self) -> None:
        """Drop the lock early; exiting drops it anyway."""
        if self._fd is None:
            return
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
        finally:
            self._fd = None


def _signal_owner(fd: int) -> None:
    """SIGUSR1 the PID written in the lock file, if there is a live one."""
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        pid = int(os.read(fd, 32).decode().strip() or 0)
    except (ValueError, OSError):
        return
    if pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGUSR1)
    except ProcessLookupError:
        pass
