"""SQLite persistence for historical metrics."""

from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, List, Optional

from models import HistoryStats, MetricSample


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "monitor.db"


def default_db_path() -> Path:
    """Writable DB location (Application Support when frozen as an .app)."""
    if getattr(sys, "frozen", False):
        support = Path.home() / "Library" / "Application Support" / "Monitor Me"
        support.mkdir(parents=True, exist_ok=True)
        return support / "monitor.db"
    return DEFAULT_DB_PATH


class MetricsDatabase:
    def __init__(self, path: Optional[Path] = None, retention_days: int = 30) -> None:
        self.path = Path(path) if path else default_db_path()
        self.retention_days = retention_days
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu REAL NOT NULL,
                    memory REAL NOT NULL,
                    disk REAL NOT NULL,
                    net_sent REAL DEFAULT 0,
                    net_recv REAL DEFAULT 0
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_ts ON system_metrics(timestamp)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    rule_key TEXT DEFAULT ''
                )
                """
            )

    def insert_sample(self, sample: MetricSample) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO system_metrics
                    (timestamp, cpu, memory, disk, net_sent, net_recv)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    sample.timestamp.isoformat(timespec="seconds"),
                    sample.cpu,
                    sample.memory,
                    sample.disk,
                    sample.net_sent_rate,
                    sample.net_recv_rate,
                ),
            )

    def prune(self) -> None:
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat(
            timespec="seconds"
        )
        with self._connect() as conn:
            conn.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff,))

    def query_range(
        self,
        start: datetime,
        end: Optional[datetime] = None,
        max_points: int = 300,
    ) -> List[MetricSample]:
        end = end or datetime.now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, cpu, memory, disk, net_sent, net_recv
                FROM system_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                """,
                (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            ).fetchall()

        samples = [
            MetricSample(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                cpu=float(row["cpu"]),
                memory=float(row["memory"]),
                disk=float(row["disk"]),
                net_sent_rate=float(row["net_sent"] or 0),
                net_recv_rate=float(row["net_recv"] or 0),
            )
            for row in rows
        ]
        return _downsample(samples, max_points)

    def stats_for_range(
        self, start: datetime, end: Optional[datetime] = None
    ) -> HistoryStats:
        end = end or datetime.now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    AVG(cpu) AS cpu_avg,
                    MAX(cpu) AS cpu_peak,
                    AVG(memory) AS memory_avg,
                    MAX(memory) AS memory_peak,
                    AVG(disk) AS disk_avg,
                    MAX(disk) AS disk_peak
                FROM system_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                """,
                (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            ).fetchone()

        n = int(row["n"] or 0)
        if n == 0:
            return HistoryStats(0, 0, 0, 0, 0, 0, 0)
        return HistoryStats(
            cpu_avg=float(row["cpu_avg"] or 0),
            cpu_peak=float(row["cpu_peak"] or 0),
            memory_avg=float(row["memory_avg"] or 0),
            memory_peak=float(row["memory_peak"] or 0),
            disk_avg=float(row["disk_avg"] or 0),
            disk_peak=float(row["disk_peak"] or 0),
            sample_count=n,
        )

    def save_alert(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: str,
        created_at: datetime,
        active: bool,
        rule_key: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO alerts
                    (id, title, message, severity, created_at, active, rule_key)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    title,
                    message,
                    severity,
                    created_at.isoformat(timespec="seconds"),
                    1 if active else 0,
                    rule_key,
                ),
            )

    def recent_alerts(self, limit: int = 20) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT * FROM alerts
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )


def _downsample(samples: List[MetricSample], max_points: int) -> List[MetricSample]:
    if len(samples) <= max_points or max_points <= 0:
        return samples
    step = len(samples) / max_points
    result: List[MetricSample] = []
    i = 0.0
    while len(result) < max_points and int(i) < len(samples):
        result.append(samples[int(i)])
        i += step
    return result
