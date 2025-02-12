"""Shared data models for collectors, services, and UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CpuMetrics:
    percent: float
    cores_logical: int
    cores_physical: int
    per_cpu: List[float] = field(default_factory=list)
    freq_mhz: Optional[float] = None


@dataclass
class MemoryMetrics:
    percent: float
    total: int
    available: int
    used: int


@dataclass
class DiskPartition:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class DiskMetrics:
    percent: float
    total: int
    used: int
    free: int
    partitions: List[DiskPartition] = field(default_factory=list)


@dataclass
class NetworkInterface:
    name: str
    is_up: bool
    addresses: List[str] = field(default_factory=list)
    bytes_sent: int = 0
    bytes_recv: int = 0


@dataclass
class NetworkMetrics:
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    # Rates in bytes/sec since previous sample (0 on first sample)
    send_rate: float = 0.0
    recv_rate: float = 0.0
    interfaces: List[NetworkInterface] = field(default_factory=list)


@dataclass
class BatteryMetrics:
    percent: Optional[float]
    plugged_in: Optional[bool]
    secs_left: Optional[int]
    available: bool = False


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_rss: int
    memory_percent: float
    status: str = ""
    username: str = ""


@dataclass
class SystemInfo:
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    processor: str
    cpu_cores_logical: int
    cpu_cores_physical: int
    memory_total: int
    boot_time: datetime
    uptime_seconds: float


@dataclass
class MetricSample:
    """One point in the in-memory ring buffer / history charts."""

    timestamp: datetime
    cpu: float
    memory: float
    disk: float
    net_sent_rate: float = 0.0
    net_recv_rate: float = 0.0


@dataclass
class SystemSnapshot:
    """Full system reading at a point in time."""

    timestamp: datetime
    cpu: CpuMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    battery: BatteryMetrics
    processes: List[ProcessInfo] = field(default_factory=list)
    top_processes: List[ProcessInfo] = field(default_factory=list)


@dataclass
class Alert:
    id: str
    title: str
    message: str
    severity: HealthStatus
    created_at: datetime
    active: bool = True
    rule_key: str = ""


@dataclass
class HistoryStats:
    cpu_avg: float
    cpu_peak: float
    memory_avg: float
    memory_peak: float
    disk_avg: float
    disk_peak: float
    sample_count: int
