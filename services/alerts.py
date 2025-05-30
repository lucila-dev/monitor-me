"""Health alert rules and evaluation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from models import Alert, HealthStatus, SystemSnapshot


@dataclass
class AlertRule:
    key: str
    title: str
    severity: HealthStatus
    threshold: float
    duration_seconds: float
    # "cpu" | "memory" | "disk" | "battery"
    metric: str
    # True => alert when value > threshold; False => when value < threshold
    above: bool = True


DEFAULT_RULES: List[AlertRule] = [
    AlertRule(
        key="high_cpu",
        title="High CPU usage",
        severity=HealthStatus.CRITICAL,
        threshold=90.0,
        duration_seconds=120.0,
        metric="cpu",
        above=True,
    ),
    AlertRule(
        key="high_memory",
        title="High memory usage",
        severity=HealthStatus.WARNING,
        threshold=90.0,
        duration_seconds=60.0,
        metric="memory",
        above=True,
    ),
    AlertRule(
        key="low_disk",
        title="Low disk space",
        severity=HealthStatus.WARNING,
        threshold=90.0,  # disk percent used
        duration_seconds=30.0,
        metric="disk",
        above=True,
    ),
    AlertRule(
        key="low_battery",
        title="Low battery",
        severity=HealthStatus.CRITICAL,
        threshold=15.0,
        duration_seconds=10.0,
        metric="battery",
        above=False,
    ),
]


@dataclass
class _RuleState:
    breached_since: Optional[datetime] = None
    active_alert_id: Optional[str] = None


class AlertService:
    def __init__(self, rules: Optional[List[AlertRule]] = None) -> None:
        self.rules = list(rules or DEFAULT_RULES)
        self._states: Dict[str, _RuleState] = {r.key: _RuleState() for r in self.rules}
        self.alerts: List[Alert] = []
        self._max_alerts = 50

    def evaluate(self, snapshot: SystemSnapshot) -> List[Alert]:
        """Evaluate rules against a snapshot. Returns newly created alerts."""
        now = snapshot.timestamp
        new_alerts: List[Alert] = []

        for rule in self.rules:
            value = self._metric_value(snapshot, rule.metric)
            state = self._states[rule.key]

            if value is None:
                state.breached_since = None
                if state.active_alert_id:
                    self._resolve(state.active_alert_id)
                    state.active_alert_id = None
                continue

            breached = value > rule.threshold if rule.above else value < rule.threshold

            if breached:
                if state.breached_since is None:
                    state.breached_since = now
                elapsed = (now - state.breached_since).total_seconds()
                if elapsed >= rule.duration_seconds and state.active_alert_id is None:
                    alert = self._create_alert(rule, snapshot, value, elapsed)
                    state.active_alert_id = alert.id
                    new_alerts.append(alert)
            else:
                state.breached_since = None
                if state.active_alert_id:
                    self._resolve(state.active_alert_id)
                    state.active_alert_id = None

        return new_alerts

    def active_alerts(self) -> List[Alert]:
        return [a for a in self.alerts if a.active]

    def overall_status(self) -> HealthStatus:
        active = self.active_alerts()
        if any(a.severity == HealthStatus.CRITICAL for a in active):
            return HealthStatus.CRITICAL
        if any(a.severity == HealthStatus.WARNING for a in active):
            return HealthStatus.WARNING
        # Soft thresholds without firing duration-based alerts yet
        return HealthStatus.HEALTHY

    def soft_status(self, snapshot: SystemSnapshot) -> HealthStatus:
        """Immediate status for the header chip (no duration wait)."""
        order = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 1,
            HealthStatus.CRITICAL: 2,
        }
        status = self.overall_status()

        cpu = snapshot.cpu.percent
        mem = snapshot.memory.percent
        disk = snapshot.disk.percent
        if cpu >= 90 or mem >= 95 or disk >= 95:
            status = max(status, HealthStatus.CRITICAL, key=lambda s: order[s])
        elif cpu >= 75 or mem >= 85 or disk >= 85:
            status = max(status, HealthStatus.WARNING, key=lambda s: order[s])

        if snapshot.battery.available and snapshot.battery.percent is not None:
            if not snapshot.battery.plugged_in:
                if snapshot.battery.percent < 10:
                    status = max(status, HealthStatus.CRITICAL, key=lambda s: order[s])
                elif snapshot.battery.percent < 20:
                    status = max(status, HealthStatus.WARNING, key=lambda s: order[s])

        return status

    def _metric_value(self, snapshot: SystemSnapshot, metric: str) -> Optional[float]:
        if metric == "cpu":
            return snapshot.cpu.percent
        if metric == "memory":
            return snapshot.memory.percent
        if metric == "disk":
            return snapshot.disk.percent
        if metric == "battery":
            if not snapshot.battery.available or snapshot.battery.percent is None:
                return None
            if snapshot.battery.plugged_in:
                return None  # don't alert on battery when plugged in
            return snapshot.battery.percent
        return None

    def _create_alert(
        self,
        rule: AlertRule,
        snapshot: SystemSnapshot,
        value: float,
        elapsed: float,
    ) -> Alert:
        top = ""
        if snapshot.top_processes:
            p = snapshot.top_processes[0]
            top = f" {p.name} was the highest-consuming process."

        if rule.metric == "cpu":
            message = (
                f"CPU remained above {rule.threshold:.0f}% for "
                f"{int(elapsed)} seconds (now {value:.0f}%).{top}"
            )
        elif rule.metric == "memory":
            message = (
                f"Memory remained above {rule.threshold:.0f}% for "
                f"{int(elapsed)} seconds (now {value:.0f}%).{top}"
            )
        elif rule.metric == "disk":
            message = (
                f"Disk usage is above {rule.threshold:.0f}% "
                f"(now {value:.0f}%). Free space is running low."
            )
        elif rule.metric == "battery":
            message = f"Battery is at {value:.0f}% and not charging."
        else:
            message = f"{rule.title}: value={value:.1f}"

        alert = Alert(
            id=str(uuid.uuid4()),
            title=rule.title,
            message=message,
            severity=rule.severity,
            created_at=snapshot.timestamp,
            active=True,
            rule_key=rule.key,
        )
        self.alerts.insert(0, alert)
        self.alerts = self.alerts[: self._max_alerts]
        return alert

    def _resolve(self, alert_id: str) -> None:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.active = False
                break
