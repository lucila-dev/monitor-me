"""Network metrics collector."""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

import psutil

from models import NetworkInterface, NetworkMetrics


class NetworkRateTracker:
    """Compute send/recv rates from successive counter samples."""

    def __init__(self) -> None:
        self._prev: Optional[Tuple[int, int, float]] = None

    def update(self, bytes_sent: int, bytes_recv: int) -> Tuple[float, float]:
        now = time.monotonic()
        if self._prev is None:
            self._prev = (bytes_sent, bytes_recv, now)
            return 0.0, 0.0

        prev_sent, prev_recv, prev_t = self._prev
        dt = max(now - prev_t, 1e-6)
        send_rate = max(0.0, (bytes_sent - prev_sent) / dt)
        recv_rate = max(0.0, (bytes_recv - prev_recv) / dt)
        self._prev = (bytes_sent, bytes_recv, now)
        return send_rate, recv_rate


def collect_network(rate_tracker: Optional[NetworkRateTracker] = None) -> NetworkMetrics:
    io = psutil.net_io_counters()
    send_rate = 0.0
    recv_rate = 0.0
    if rate_tracker is not None:
        send_rate, recv_rate = rate_tracker.update(int(io.bytes_sent), int(io.bytes_recv))

    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    per_nic = psutil.net_io_counters(pernic=True)

    interfaces: List[NetworkInterface] = []
    for name, st in stats.items():
        addr_list: List[str] = []
        for snic in addrs.get(name, []):
            # AF_LINK / MAC often not useful; keep IPv4/IPv6 strings
            if snic.family.name in ("AF_INET", "AF_INET6") or getattr(snic.family, "name", "") in (
                "AF_INET",
                "AF_INET6",
            ):
                addr_list.append(snic.address)
            elif str(snic.family) in ("AddressFamily.AF_INET", "AddressFamily.AF_INET6"):
                addr_list.append(snic.address)

        nic_io = per_nic.get(name)
        interfaces.append(
            NetworkInterface(
                name=name,
                is_up=bool(st.isup),
                addresses=addr_list,
                bytes_sent=int(nic_io.bytes_sent) if nic_io else 0,
                bytes_recv=int(nic_io.bytes_recv) if nic_io else 0,
            )
        )

    interfaces.sort(key=lambda i: (not i.is_up, i.name.lower()))

    return NetworkMetrics(
        bytes_sent=int(io.bytes_sent),
        bytes_recv=int(io.bytes_recv),
        packets_sent=int(io.packets_sent),
        packets_recv=int(io.packets_recv),
        send_rate=send_rate,
        recv_rate=recv_rate,
        interfaces=interfaces,
    )
