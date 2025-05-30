"""Monitoring engine: poll collectors, ring buffer, optional SQLite + alerts."""

from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime
from typing import Callable, Deque, List, Optional

from collectors import (
    NetworkRateTracker,
    collect_battery,
    collect_cpu,
    collect_disk,
    collect_memory,
    collect_network,
    collect_processes,
    top_processes,
)
from models import MetricSample, SystemSnapshot
from services.alerts import AlertService
from services.database import MetricsDatabase


class MonitoringEngine:
    """Background poller that builds SystemSnapshot objects every interval."""

    def __init__(
        self,
        interval: float = 1.0,
        history_size: int = 60,
        database: Optional[MetricsDatabase] = None,
        alert_service: Optional[AlertService] = None,
        persist_every: int = 1,
    ) -> None:
        self.interval = interval
        self.history: Deque[MetricSample] = deque(maxlen=history_size)
        self.database = database
        self.alerts = alert_service or AlertService()
        self.persist_every = persist_every

        self._rate_tracker = NetworkRateTracker()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest: Optional[SystemSnapshot] = None
        self._tick = 0
        self._listeners: List[Callable[[SystemSnapshot], None]] = []
        self._cpu_primed = False

    def add_listener(self, callback: Callable[[SystemSnapshot], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[SystemSnapshot], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    @property
    def latest(self) -> Optional[SystemSnapshot]:
        with self._lock:
            return self._latest

    def history_list(self) -> List[MetricSample]:
        with self._lock:
            return list(self.history)

    def collect_snapshot(self, include_processes: bool = True) -> SystemSnapshot:
        # First call to cpu_percent(None) is always 0; prime then wait.
        if not self._cpu_primed:
            collect_cpu(interval=None)
            if include_processes:
                collect_processes()
            time.sleep(0.2)
            self._cpu_primed = True

        cpu = collect_cpu(interval=None)
        memory = collect_memory()
        disk = collect_disk()
        network = collect_network(self._rate_tracker)
        battery = collect_battery()

        processes = collect_processes() if include_processes else []
        tops = top_processes(processes, limit=10, sort_by="cpu") if processes else []

        snapshot = SystemSnapshot(
            timestamp=datetime.now(),
            cpu=cpu,
            memory=memory,
            disk=disk,
            network=network,
            battery=battery,
            processes=processes,
            top_processes=tops,
        )
        return snapshot

    def _record(self, snapshot: SystemSnapshot) -> None:
        sample = MetricSample(
            timestamp=snapshot.timestamp,
            cpu=snapshot.cpu.percent,
            memory=snapshot.memory.percent,
            disk=snapshot.disk.percent,
            net_sent_rate=snapshot.network.send_rate,
            net_recv_rate=snapshot.network.recv_rate,
        )
        with self._lock:
            self.history.append(sample)
            self._latest = snapshot
            self._tick += 1
            tick = self._tick

        if self.database is not None and tick % self.persist_every == 0:
            try:
                self.database.insert_sample(sample)
                if tick % 300 == 0:
                    self.database.prune()
            except Exception:
                pass  # don't crash monitoring on DB errors

        new_alerts = self.alerts.evaluate(snapshot)
        if self.database is not None:
            for alert in new_alerts:
                try:
                    self.database.save_alert(
                        alert.id,
                        alert.title,
                        alert.message,
                        alert.severity.value,
                        alert.created_at,
                        alert.active,
                        alert.rule_key,
                    )
                except Exception:
                    pass

        for listener in list(self._listeners):
            try:
                listener(snapshot)
            except Exception:
                pass

    def poll_once(self, include_processes: bool = True) -> SystemSnapshot:
        snapshot = self.collect_snapshot(include_processes=include_processes)
        self._record(snapshot)
        return snapshot

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="MonitoringEngine", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                self.poll_once(include_processes=True)
            except Exception:
                pass
            elapsed = time.monotonic() - started
            wait = max(0.05, self.interval - elapsed)
            self._stop.wait(wait)
