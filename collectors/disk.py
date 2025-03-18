"""Disk metrics collector."""

from __future__ import annotations

import os
from typing import List

import psutil

from models import DiskMetrics, DiskPartition


def _root_path() -> str:
    return os.path.abspath(os.sep)


def collect_disk() -> DiskMetrics:
    root = _root_path()
    usage = psutil.disk_usage(root)

    partitions: List[DiskPartition] = []
    for part in psutil.disk_partitions(all=False):
        # Skip pseudo / network mounts that often fail on macOS/Linux
        if part.fstype in ("", "devfs", "autofs", "proc", "sysfs", "cgroup", "cgroup2"):
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError, FileNotFoundError):
            continue
        partitions.append(
            DiskPartition(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total=int(u.total),
                used=int(u.used),
                free=int(u.free),
                percent=float(u.percent),
            )
        )

    # Prefer root partition percent for overview cards
    return DiskMetrics(
        percent=float(usage.percent),
        total=int(usage.total),
        used=int(usage.used),
        free=int(usage.free),
        partitions=partitions,
    )
