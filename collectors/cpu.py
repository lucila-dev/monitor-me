"""CPU metrics collector."""

from __future__ import annotations

from typing import List, Optional

import psutil

from models import CpuMetrics


def collect_cpu(interval: Optional[float] = None) -> CpuMetrics:
    """Collect CPU usage.

    Pass interval=None for non-blocking (uses last cached value).
    First call with interval=None may return 0.0 until a prior sample exists.
    """
    percent = psutil.cpu_percent(interval=interval)
    per_cpu: List[float] = list(psutil.cpu_percent(interval=None, percpu=True))
    freq_mhz: Optional[float] = None
    try:
        freq = psutil.cpu_freq()
        if freq is not None:
            freq_mhz = float(freq.current)
    except (AttributeError, NotImplementedError, FileNotFoundError, OSError):
        freq_mhz = None

    return CpuMetrics(
        percent=float(percent),
        cores_logical=psutil.cpu_count(logical=True) or 1,
        cores_physical=psutil.cpu_count(logical=False) or 1,
        per_cpu=per_cpu,
        freq_mhz=freq_mhz,
    )
