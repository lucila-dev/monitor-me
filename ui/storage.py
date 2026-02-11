"""Storage page: per-partition disk usage."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models import DiskMetrics, SystemSnapshot
from ui.theme import COLORS
from utils import format_bytes


class StoragePage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Storage")
        title.setObjectName("titleLabel")
        outer.addWidget(title)

        self.summary = QLabel("")
        self.summary.setObjectName("metricCaption")
        outer.addWidget(self.summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        scroll.setWidget(self.container)
        outer.addWidget(scroll)

    def update_snapshot(self, snapshot: SystemSnapshot) -> None:
        disk = snapshot.disk
        self.summary.setText(
            f"Root volume: {disk.percent:.0f}% used — "
            f"{format_bytes(disk.used)} of {format_bytes(disk.total)} "
            f"({format_bytes(disk.free)} free)"
        )
        self._rebuild(disk)

    def _rebuild(self, disk: DiskMetrics) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        partitions = disk.partitions or []
        if not partitions:
            # Fallback single root card
            self.list_layout.insertWidget(0, self._card("/", "root", disk.percent, disk.total, disk.used, disk.free))
            return

        for i, part in enumerate(partitions):
            card = self._card(
                part.mountpoint,
                f"{part.device} · {part.fstype}",
                part.percent,
                part.total,
                part.used,
                part.free,
            )
            self.list_layout.insertWidget(i, card)

    def _card(
        self,
        mount: str,
        subtitle: str,
        percent: float,
        total: int,
        used: int,
        free: int,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)

        top = QHBoxLayout()
        name = QLabel(mount)
        name.setStyleSheet("font-weight: 600; font-size: 15px;")
        top.addWidget(name)
        top.addStretch()
        pct = QLabel(f"{percent:.0f}%")
        pct.setStyleSheet("font-weight: 700; font-size: 16px;")
        top.addWidget(pct)
        layout.addLayout(top)

        sub = QLabel(subtitle)
        sub.setObjectName("metricCaption")
        layout.addWidget(sub)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(percent))
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        color = COLORS["accent"]
        if percent >= 90:
            color = COLORS["critical"]
        elif percent >= 80:
            color = COLORS["warning"]
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {COLORS['bar_track']};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
            """
        )
        layout.addWidget(bar)

        detail = QLabel(
            f"{format_bytes(used)} used · {format_bytes(free)} free · {format_bytes(total)} total"
        )
        detail.setObjectName("metricCaption")
        layout.addWidget(detail)
        return frame
