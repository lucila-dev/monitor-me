"""Performance page: historical charts and stats for selectable ranges."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, List, Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models import HistoryStats, MetricSample
from services.database import MetricsDatabase
from ui.widgets import HistoryChart


RANGES = [
    ("1 min", timedelta(minutes=1)),
    ("1 hour", timedelta(hours=1)),
    ("24 hours", timedelta(hours=24)),
    ("7 days", timedelta(days=7)),
]


class PerformancePage(QWidget):
    def __init__(
        self,
        database: Optional[MetricsDatabase] = None,
        live_history_provider: Optional[Callable[[], List[MetricSample]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.live_history_provider = live_history_provider
        self._range_index = 0
        self._range_buttons: List[QPushButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Performance")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        for i, (label, _) in enumerate(RANGES):
            btn = QPushButton(label)
            btn.setObjectName("rangeButton")
            btn.clicked.connect(lambda checked=False, idx=i: self.set_range(idx))
            self._range_buttons.append(btn)
            header.addWidget(btn)
        root.addLayout(header)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("metricCaption")
        root.addWidget(self.stats_label)

        self.cpu_chart = HistoryChart(title="CPU %")
        self.mem_chart = HistoryChart(title="Memory %", color="#3fb950")
        self.disk_chart = HistoryChart(title="Disk %", color="#d29922")
        root.addWidget(self.cpu_chart, stretch=1)
        root.addWidget(self.mem_chart, stretch=1)
        root.addWidget(self.disk_chart, stretch=1)

        self.set_range(0)

    def set_range(self, index: int) -> None:
        self._range_index = index
        for i, btn in enumerate(self._range_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.refresh()

    def refresh(self) -> None:
        label, delta = RANGES[self._range_index]
        start = datetime.now() - delta
        samples: List[MetricSample] = []
        stats = HistoryStats(0, 0, 0, 0, 0, 0, 0)

        if self._range_index == 0 and self.live_history_provider:
            samples = self.live_history_provider()
            if samples:
                cpus = [s.cpu for s in samples]
                mems = [s.memory for s in samples]
                disks = [s.disk for s in samples]
                stats = HistoryStats(
                    cpu_avg=sum(cpus) / len(cpus),
                    cpu_peak=max(cpus),
                    memory_avg=sum(mems) / len(mems),
                    memory_peak=max(mems),
                    disk_avg=sum(disks) / len(disks),
                    disk_peak=max(disks),
                    sample_count=len(samples),
                )
        elif self.database is not None:
            samples = self.database.query_range(start)
            stats = self.database.stats_for_range(start)

        self.cpu_chart.set_values([s.cpu for s in samples])
        self.mem_chart.set_values([s.memory for s in samples])
        self.disk_chart.set_values([s.disk for s in samples])

        if stats.sample_count == 0:
            self.stats_label.setText(f"{label}: no samples yet")
        else:
            self.stats_label.setText(
                f"{label} — CPU avg {stats.cpu_avg:.0f}% · peak {stats.cpu_peak:.0f}%  |  "
                f"Memory avg {stats.memory_avg:.0f}% · peak {stats.memory_peak:.0f}%  |  "
                f"{stats.sample_count} samples"
            )
