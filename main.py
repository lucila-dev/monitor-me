#!/usr/bin/env python3
"""Monitor Me — desktop system monitor (CLI + PySide6 GUI)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path when run as a script
if getattr(sys, "frozen", False):
    # PyInstaller .app: resources live in _MEIPASS; writable data beside the .app or in Application Support
    ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors import (  # noqa: E402
    collect_battery,
    collect_cpu,
    collect_disk,
    collect_memory,
)
from collectors.system_info import collect_system_info  # noqa: E402
from services.alerts import AlertService  # noqa: E402
from services.database import MetricsDatabase  # noqa: E402
from services.monitor import MonitoringEngine  # noqa: E402
from utils import format_bytes  # noqa: E402

APP_NAME = "Monitor Me"
ICON_PATH = ROOT / "assets" / "app_icon.png"


def print_once() -> None:
    """V1 — one-shot system information to the terminal."""
    cpu = collect_cpu(interval=0.3)
    mem = collect_memory()
    disk = collect_disk()
    bat = collect_battery()
    info = collect_system_info()

    print(f"CPU: {cpu.percent:.0f}%")
    print(f"RAM: {mem.percent:.0f}%")
    print(f"Disk: {disk.percent:.0f}%")
    if bat.available and bat.percent is not None:
        print(f"Battery: {bat.percent:.0f}%")
    else:
        print("Battery: n/a")
    print()
    print(f"CPU cores: {cpu.cores_logical}")
    print(f"Total RAM: {format_bytes(mem.total)}")
    print(f"Available RAM: {format_bytes(mem.available)}")
    print(f"Hostname: {info.hostname}")
    print(f"OS: {info.os_name} {info.os_version}")


def run_live(duration: float = 0.0) -> None:
    """V2 — live monitoring to the terminal."""
    engine = MonitoringEngine(interval=1.0, history_size=60, database=None)
    print("Live monitoring (Ctrl+C to stop)")
    print("-" * 48)
    start = time.time()
    try:
        while True:
            snap = engine.poll_once(include_processes=False)
            ts = snap.timestamp.strftime("%H:%M:%S")
            print(
                f"{ts}   CPU {snap.cpu.percent:5.1f}%   "
                f"RAM {snap.memory.percent:5.1f}%   "
                f"Disk {snap.disk.percent:5.1f}%"
            )
            if duration > 0 and (time.time() - start) >= duration:
                break
            time.sleep(max(0.0, 1.0 - 0.05))
    except KeyboardInterrupt:
        print("\nStopped.")


def _load_app_icon():
    from PySide6.QtGui import QIcon

    if ICON_PATH.exists():
        return QIcon(str(ICON_PATH))
    return QIcon()


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    db = MetricsDatabase()
    alerts = AlertService()
    engine = MonitoringEngine(
        interval=1.0,
        history_size=60,
        database=db,
        alert_service=alerts,
        persist_every=1,
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow(engine=engine, database=db)
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    return app.exec()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} — desktop system monitor")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Print a one-shot system summary to the terminal (no GUI)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Live terminal monitoring (1s refresh)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="With --live, stop after N seconds (0 = until Ctrl+C)",
    )
    args = parser.parse_args(argv)

    if args.cli:
        print_once()
        return 0
    if args.live:
        run_live(duration=args.duration)
        return 0
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
