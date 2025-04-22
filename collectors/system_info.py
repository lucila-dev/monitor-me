"""Static / diagnostic system information."""

from __future__ import annotations

import platform
import socket
from datetime import datetime
from typing import Optional

import psutil

from models import SystemInfo
from utils import format_bytes, format_uptime


def collect_system_info() -> SystemInfo:
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = (datetime.now() - boot).total_seconds()

    processor = platform.processor() or platform.machine()
    if not processor.strip():
        processor = platform.machine()

    mac_ver = platform.mac_ver()[0]
    system = platform.system()
    if system == "Darwin" and mac_ver:
        os_name = "macOS"
        os_version = mac_ver
    else:
        os_name = system
        os_version = platform.release()

    return SystemInfo(
        hostname=socket.gethostname(),
        os_name=os_name,
        os_version=os_version,
        architecture=platform.machine(),
        processor=processor,
        cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
        cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
        memory_total=int(psutil.virtual_memory().total),
        boot_time=boot,
        uptime_seconds=uptime,
    )


def format_system_report(
    info: SystemInfo,
    memory_available: Optional[int] = None,
    disk_free: Optional[int] = None,
) -> str:
    lines = [
        "System Diagnostic Report",
        f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        f"Hostname: {info.hostname}",
        f"OS: {info.os_name} {info.os_version}",
        f"Architecture: {info.architecture}",
        f"Processor: {info.processor}",
        f"CPU cores (logical): {info.cpu_cores_logical}",
        f"CPU cores (physical): {info.cpu_cores_physical}",
        f"Memory: {format_bytes(info.memory_total)}",
    ]
    if memory_available is not None:
        lines.append(f"Available Memory: {format_bytes(memory_available)}")
    if disk_free is not None:
        lines.append(f"Disk Available: {format_bytes(disk_free)}")
    lines.extend(
        [
            f"Boot time: {info.boot_time.strftime('%H:%M')}",
            f"Uptime: {format_uptime(info.uptime_seconds)}",
        ]
    )
    return "\n".join(lines)
