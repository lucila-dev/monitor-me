"""Network monitor page."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from models import MetricSample, SystemSnapshot
from ui.widgets import DualHistoryChart, MetricCard
from utils import format_bytes, format_rate


class NetworkPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel("Network")
        title.setObjectName("titleLabel")
        root.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.down_card = MetricCard("Download")
        self.up_card = MetricCard("Upload")
        self.recv_card = MetricCard("Total received")
        self.sent_card = MetricCard("Total sent")
        # MetricCard expects percent bars — override for rates/totals display
        for card in (self.down_card, self.up_card, self.recv_card, self.sent_card):
            card.bar.hide()
        cards.addWidget(self.down_card)
        cards.addWidget(self.up_card)
        cards.addWidget(self.recv_card)
        cards.addWidget(self.sent_card)
        root.addLayout(cards)

        self.chart = DualHistoryChart(title="Transfer rate — last 60 seconds")
        root.addWidget(self.chart, stretch=2)

        if_title = QLabel("INTERFACES")
        if_title.setObjectName("sectionLabel")
        root.addWidget(if_title)

        self.if_frame = QFrame()
        self.if_frame.setObjectName("metricCard")
        self.if_layout = QVBoxLayout(self.if_frame)
        self.if_layout.setContentsMargins(16, 12, 16, 12)
        root.addWidget(self.if_frame, stretch=1)

    def update_snapshot(self, snapshot: SystemSnapshot, history: List[MetricSample]) -> None:
        net = snapshot.network
        self.down_card.value_label.setText(format_rate(net.recv_rate))
        self.down_card.sub.setText("↓ inbound")
        self.up_card.value_label.setText(format_rate(net.send_rate))
        self.up_card.sub.setText("↑ outbound")
        self.recv_card.value_label.setText(format_bytes(net.bytes_recv))
        self.recv_card.sub.setText("since boot")
        self.sent_card.value_label.setText(format_bytes(net.bytes_sent))
        self.sent_card.sub.setText("since boot")

        # Shrink font slightly for large totals
        for card in (self.recv_card, self.sent_card, self.down_card, self.up_card):
            card.value_label.setStyleSheet("font-size: 22px; font-weight: 700;")

        self.chart.set_series(
            [s.net_recv_rate for s in history],
            [s.net_sent_rate for s in history],
        )

        while self.if_layout.count():
            item = self.if_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for iface in net.interfaces:
            # Skip loopback noise unless it's the only one
            if iface.name.startswith("lo") and len(net.interfaces) > 1:
                continue
            row = QHBoxLayout()
            status = "● Connected" if iface.is_up else "○ Disconnected"
            color = "#3fb950" if iface.is_up else "#8b949e"
            name = QLabel(iface.name)
            name.setStyleSheet("font-weight: 600;")
            st = QLabel(status)
            st.setStyleSheet(f"color: {color};")
            row.addWidget(name)
            row.addStretch()
            row.addWidget(st)
            wrap = QWidget()
            wrap.setLayout(row)
            self.if_layout.addWidget(wrap)

        self.if_layout.addStretch()
