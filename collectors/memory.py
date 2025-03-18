"""Memory metrics collector."""

from __future__ import annotations

import psutil

from models import MemoryMetrics


def collect_memory() -> MemoryMetrics:
    mem = psutil.virtual_memory()
    return MemoryMetrics(
        percent=float(mem.percent),
        total=int(mem.total),
        available=int(mem.available),
        used=int(mem.used),
    )
