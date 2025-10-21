"""Overview page: live metrics, CPU chart, top processes, alerts."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models import Alert, MetricSample, SystemSnapshot
from ui.widgets import HistoryChart, MetricCard
from utils import format_bytes


class OverviewPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.cpu_card = MetricCard("CPU")
        self.mem_card = MetricCard("Memory")
        self.disk_card = MetricCard("Disk")
        cards.addWidget(self.cpu_card)
        cards.addWidget(self.mem_card)
        cards.addWidget(self.disk_card)
        root.addLayout(cards)

        self.cpu_chart = HistoryChart(title="CPU usage — last 60 seconds")
        root.addWidget(self.cpu_chart, stretch=2)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # Top processes
        proc_frame = QFrame()
        proc_frame.setObjectName("metricCard")
        proc_layout = QVBoxLayout(proc_frame)
        proc_title = QLabel("TOP PROCESSES")
        proc_title.setObjectName("sectionLabel")
        proc_layout.addWidget(proc_title)
        self.proc_table = QTableWidget(0, 3)
        self.proc_table.setHorizontalHeaderLabels(["Process", "CPU", "RAM"])
        self.proc_table.horizontalHeader().setStretchLastSection(True)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.proc_table.setSelectionMode(QTableWidget.NoSelection)
        self.proc_table.setShowGrid(False)
        proc_layout.addWidget(self.proc_table)
        bottom.addWidget(proc_frame, stretch=3)

        # Alerts
        alert_frame = QFrame()
        alert_frame.setObjectName("metricCard")
        alert_layout = QVBoxLayout(alert_frame)
        alert_title = QLabel("ALERTS")
        alert_title.setObjectName("sectionLabel")
        alert_layout.addWidget(alert_title)
        self.alert_list = QLabel("No active alerts.")
        self.alert_list.setWordWrap(True)
        self.alert_list.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.alert_list.setObjectName("metricCaption")
        alert_layout.addWidget(self.alert_list, stretch=1)
        bottom.addWidget(alert_frame, stretch=2)

        root.addLayout(bottom, stretch=2)

    def update_snapshot(self, snapshot: SystemSnapshot, history: List[MetricSample]) -> None:
        mem = snapshot.memory
        disk = snapshot.disk
        self.cpu_card.set_value(
            snapshot.cpu.percent,
            f"{snapshot.cpu.cores_logical} cores",
        )
        self.mem_card.set_value(
            mem.percent,
            f"{format_bytes(mem.used)} / {format_bytes(mem.total)}",
        )
        self.disk_card.set_value(
            disk.percent,
            f"{format_bytes(disk.free)} free",
        )
        self.cpu_chart.set_values([s.cpu for s in history])

        tops = snapshot.top_processes[:8]
        self.proc_table.setRowCount(len(tops))
        for row, proc in enumerate(tops):
            self.proc_table.setItem(row, 0, QTableWidgetItem(proc.name))
            self.proc_table.setItem(row, 1, QTableWidgetItem(f"{proc.cpu_percent:.0f}%"))
            self.proc_table.setItem(row, 2, QTableWidgetItem(format_bytes(proc.memory_rss)))
        self.proc_table.resizeColumnsToContents()

    def update_alerts(self, alerts: List[Alert]) -> None:
        active = [a for a in alerts if a.active][:5]
        if not active:
            self.alert_list.setText("No active alerts.")
            return
        lines = []
        for a in active:
            icon = "🔴" if a.severity.value == "critical" else "🟠"
            lines.append(f"{icon} <b>{a.title}</b><br/>{a.message}")
        self.alert_list.setText("<br/><br/>".join(lines))
