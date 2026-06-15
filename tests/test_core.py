"""Tests for formatting helpers and alert rules."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from models import (
    BatteryMetrics,
    CpuMetrics,
    DiskMetrics,
    HealthStatus,
    MemoryMetrics,
    NetworkMetrics,
    ProcessInfo,
    SystemSnapshot,
)
from services.alerts import AlertRule, AlertService
from utils import format_bytes, format_uptime


def test_format_bytes():
    assert format_bytes(512) == "512 B"
    assert "KB" in format_bytes(2048)
    assert "GB" in format_bytes(5 * 1024**3)


def test_format_uptime():
    assert "1h" in format_uptime(3661)
    assert "2m" in format_uptime(120)


def _snapshot(
    cpu: float = 10.0,
    memory: float = 50.0,
    disk: float = 40.0,
    battery: Optional[float] = None,
    plugged: bool = True,
    ts: Optional[datetime] = None,
) -> SystemSnapshot:
    ts = ts or datetime.now()
    bat = BatteryMetrics(
        percent=battery,
        plugged_in=plugged if battery is not None else None,
        secs_left=None,
        available=battery is not None,
    )
    return SystemSnapshot(
        timestamp=ts,
        cpu=CpuMetrics(percent=cpu, cores_logical=8, cores_physical=4),
        memory=MemoryMetrics(percent=memory, total=16_000_000_000, available=8_000_000_000, used=8_000_000_000),
        disk=DiskMetrics(percent=disk, total=500_000_000_000, used=200_000_000_000, free=300_000_000_000),
        network=NetworkMetrics(0, 0, 0, 0),
        battery=bat,
        processes=[],
        top_processes=[
            ProcessInfo(pid=1, name="Chrome", cpu_percent=12.0, memory_rss=2_000_000_000, memory_percent=10.0)
        ],
    )


def test_alert_cpu_requires_duration():
    service = AlertService(
        rules=[
            AlertRule(
                key="high_cpu",
                title="High CPU usage",
                severity=HealthStatus.CRITICAL,
                threshold=90.0,
                duration_seconds=5.0,
                metric="cpu",
                above=True,
            )
        ]
    )
    t0 = datetime(2026, 8, 7, 12, 0, 0)
    # First breaches — not long enough
    created = service.evaluate(_snapshot(cpu=95, ts=t0))
    assert created == []
    created = service.evaluate(_snapshot(cpu=96, ts=t0 + timedelta(seconds=3)))
    assert created == []
    # Past duration
    created = service.evaluate(_snapshot(cpu=97, ts=t0 + timedelta(seconds=6)))
    assert len(created) == 1
    assert created[0].title == "High CPU usage"
    assert "Chrome" in created[0].message


def test_alert_resolves_when_metric_drops():
    service = AlertService(
        rules=[
            AlertRule(
                key="high_cpu",
                title="High CPU usage",
                severity=HealthStatus.CRITICAL,
                threshold=90.0,
                duration_seconds=1.0,
                metric="cpu",
                above=True,
            )
        ]
    )
    t0 = datetime(2026, 8, 7, 12, 0, 0)
    service.evaluate(_snapshot(cpu=95, ts=t0))
    service.evaluate(_snapshot(cpu=95, ts=t0 + timedelta(seconds=2)))
    assert len(service.active_alerts()) == 1
    service.evaluate(_snapshot(cpu=20, ts=t0 + timedelta(seconds=3)))
    assert service.active_alerts() == []


def test_soft_status_critical_on_high_cpu():
    service = AlertService(rules=[])
    status = service.soft_status(_snapshot(cpu=95))
    assert status == HealthStatus.CRITICAL


def test_database_roundtrip(tmp_path):
    from models import MetricSample
    from services.database import MetricsDatabase

    db = MetricsDatabase(path=tmp_path / "test.db", retention_days=7)
    now = datetime.now()
    for i in range(5):
        db.insert_sample(
            MetricSample(
                timestamp=now.replace(microsecond=0) - timedelta(seconds=5 - i),
                cpu=10.0 + i,
                memory=50.0,
                disk=40.0,
                net_sent_rate=100.0,
                net_recv_rate=200.0,
            )
        )
    samples = db.query_range(now - timedelta(minutes=1))
    assert len(samples) == 5
    stats = db.stats_for_range(now - timedelta(minutes=1))
    assert stats.sample_count == 5
    assert stats.cpu_peak == 14.0
