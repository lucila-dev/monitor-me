"""Battery metrics collector."""

from __future__ import annotations

from typing import Optional

import psutil

from models import BatteryMetrics


def collect_battery() -> BatteryMetrics:
    try:
        bat = psutil.sensors_battery()
    except (AttributeError, NotImplementedError, OSError):
        return BatteryMetrics(percent=None, plugged_in=None, secs_left=None, available=False)

    if bat is None:
        return BatteryMetrics(percent=None, plugged_in=None, secs_left=None, available=False)

    secs: Optional[int]
    if bat.secsleft in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
        secs = None
    else:
        secs = int(bat.secsleft)

    return BatteryMetrics(
        percent=float(bat.percent),
        plugged_in=bool(bat.power_plugged),
        secs_left=secs,
        available=True,
    )
