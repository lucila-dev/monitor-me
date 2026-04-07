"""System information / diagnostic report page."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from collectors.system_info import collect_system_info, format_system_report
from models import SystemInfo, SystemSnapshot
from utils import format_bytes, format_uptime


class SystemPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._info: Optional[SystemInfo] = None
        self._last_snapshot: Optional[SystemSnapshot] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("System")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        self.copy_btn = QPushButton("Copy System Report")
        self.copy_btn.setObjectName("primaryButton")
        self.copy_btn.clicked.connect(self.copy_report)
        header.addWidget(self.copy_btn)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("metricCard")
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft)

        self.fields: Dict[str, QLabel] = {}
        for key, label in [
            ("hostname", "Hostname"),
            ("os", "Operating System"),
            ("arch", "Architecture"),
            ("processor", "Processor"),
            ("cores", "CPU cores"),
            ("memory", "Memory"),
            ("boot", "Boot time"),
            ("uptime", "Uptime"),
            ("battery", "Battery"),
        ]:
            value = QLabel("—")
            value.setStyleSheet("font-weight: 600;")
            form.addRow(QLabel(label), value)
            self.fields[key] = value

        root.addWidget(card)
        root.addStretch()
        self.refresh_static()

    def refresh_static(self) -> None:
        self._info = collect_system_info()
        info = self._info
        self.fields["hostname"].setText(info.hostname)
        self.fields["os"].setText(f"{info.os_name} {info.os_version}".strip())
        self.fields["arch"].setText(info.architecture)
        self.fields["processor"].setText(info.processor)
        self.fields["cores"].setText(
            f"{info.cpu_cores_logical} logical / {info.cpu_cores_physical} physical"
        )
        self.fields["memory"].setText(format_bytes(info.memory_total))
        self.fields["boot"].setText(info.boot_time.strftime("%Y-%m-%d %H:%M"))
        self.fields["uptime"].setText(format_uptime(info.uptime_seconds))

    def update_snapshot(self, snapshot: SystemSnapshot) -> None:
        self._last_snapshot = snapshot
        if self._info:
            uptime = (datetime.now() - self._info.boot_time).total_seconds()
            self.fields["uptime"].setText(format_uptime(uptime))

        bat = snapshot.battery
        if bat.available and bat.percent is not None:
            plug = "plugged in" if bat.plugged_in else "on battery"
            self.fields["battery"].setText(f"{bat.percent:.0f}% ({plug})")
        else:
            self.fields["battery"].setText("Not available")

    def copy_report(self) -> None:
        if self._info is None:
            self.refresh_static()
        assert self._info is not None
        mem_avail = self._last_snapshot.memory.available if self._last_snapshot else None
        disk_free = self._last_snapshot.disk.free if self._last_snapshot else None
        report = format_system_report(self._info, mem_avail, disk_free)
        QGuiApplication.clipboard().setText(report)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy System Report"))
