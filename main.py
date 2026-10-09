"""Entry point: the QML overlay plus the Monitor object behind it."""

from __future__ import annotations

import argparse
import signal
import socket
import sys
from pathlib import Path

from PySide6.QtCore import QSocketNotifier
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from kasys.bridge import Monitor, Overlay
from kasys.single_instance import SingleInstance

ROOT = Path(__file__).resolve().parent
APP_ID = "kasys"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=APP_ID)
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="start hidden and stay resident; launching again shows/hides the window",
    )
    return parser.parse_args()


def _handle_signals(app: QGuiApplication, overlay: Overlay) -> tuple[socket.socket, socket.socket, QSocketNotifier]:
    """SIGUSR1 (a second launch) toggles the window; SIGTERM / SIGINT quit.

    Qt's C++ loop does not yield to Python, so a plain handler would only run
    on the next event. The signal writes its number as a byte to a socket the
    loop watches instead. The returned objects must stay referenced while the
    app runs.
    """
    reader, writer = socket.socketpair()
    reader.setblocking(False)
    writer.setblocking(False)
    signal.set_wakeup_fd(writer.fileno())

    notifier = QSocketNotifier(reader.fileno(), QSocketNotifier.Type.Read)

    def dispatch() -> None:
        try:
            received = reader.recv(64)
        except OSError:
            return
        for number in received:
            if number == signal.SIGUSR1:
                overlay.toggle()
            else:
                app.quit()

    notifier.activated.connect(dispatch)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        signal.signal(sig, lambda *_: None)
    return reader, writer, notifier


def main() -> int:
    args = _parse_args()
    # A second launch toggles the instance that is already up, and opens nothing.
    instance = SingleInstance()
    if not instance.acquire():
        return 0

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_ID)
    app.setDesktopFileName(APP_ID)
    # A daemon hides its only window; that must not end the process.
    app.setQuitOnLastWindowClosed(not args.daemon)
    overlay = Overlay(daemon=args.daemon)
    signal_guard = _handle_signals(app, overlay)

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "qml"))
    monitor = Monitor()

    def reread_on_show() -> None:
        if overlay.shown:
            monitor.read_system_info()

    overlay.shownChanged.connect(reread_on_show)
    engine.rootContext().setContextProperty("monitor", monitor)
    engine.rootContext().setContextProperty("overlay", overlay)
    engine.load(ROOT / "qml" / "Main.qml")
    if not engine.rootObjects():
        print(
            "kasys: the window failed to load. It is a wlr-layer-shell overlay: "
            "install layer-shell-qt and run it on a compositor that supports it.",
            file=sys.stderr,
        )
        return 1

    try:
        return app.exec()
    finally:
        del signal_guard
        instance.release()


if __name__ == "__main__":
    sys.exit(main())
