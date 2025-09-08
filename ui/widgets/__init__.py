"""Reusable UI widgets."""

from __future__ import annotations

from typing import List, Optional, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class MetricCard(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        self.caption = QLabel(title.upper())
        self.caption.setObjectName("sectionLabel")
        self.value_label = QLabel("—")
        self.value_label.setObjectName("metricValue")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {COLORS['bar_track']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['chart']};
                border-radius: 4px;
            }}
            """
        )
        self.sub = QLabel("")
        self.sub.setObjectName("metricCaption")

        layout.addWidget(self.caption)
        layout.addWidget(self.value_label)
        layout.addWidget(self.bar)
        layout.addWidget(self.sub)

    def set_value(self, percent: float, subtitle: str = "") -> None:
        self.value_label.setText(f"{percent:.0f}%")
        self.bar.setValue(int(max(0, min(100, percent))))
        color = COLORS["accent"]
        if percent >= 90:
            color = COLORS["critical"]
        elif percent >= 75:
            color = COLORS["warning"]
        self.bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {COLORS['bar_track']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
            """
        )
        self.sub.setText(subtitle)


class StatusChip(QLabel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.set_status("healthy")

    def set_status(self, status: str) -> None:
        status = status.lower()
        colors = {
            "healthy": (COLORS["accent"], "Healthy"),
            "warning": (COLORS["warning"], "Warning"),
            "critical": (COLORS["critical"], "Critical"),
        }
        color, label = colors.get(status, colors["healthy"])
        self.setText(f"●  {label}")
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-weight: 600;
                padding: 4px 10px;
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                background-color: {COLORS['panel']};
            }}
            """
        )


class HistoryChart(QWidget):
    """Simple line chart for percentage history (0–100) or arbitrary series."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "",
        color: Optional[str] = None,
        y_max: Optional[float] = 100.0,
        auto_scale: bool = False,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.line_color = QColor(color or COLORS["chart"])
        self.y_max = y_max
        self.auto_scale = auto_scale
        self._values: List[float] = []
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_values(self, values: Sequence[float]) -> None:
        self._values = [float(v) for v in values]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(48, 28, -12, -24)
        painter.fillRect(self.rect(), QColor(COLORS["panel"]))

        # Border
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)

        if self.title:
            painter.setPen(QColor(COLORS["muted"]))
            font = QFont(painter.font())
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(16, 20, self.title.upper())

        if not self._values or rect.width() < 10 or rect.height() < 10:
            painter.end()
            return

        ymax = self.y_max
        if self.auto_scale or ymax is None:
            peak = max(self._values) if self._values else 1.0
            ymax = max(peak * 1.15, 1.0)

        # Grid / labels
        painter.setPen(QColor(COLORS["muted"]))
        font = QFont(painter.font())
        font.setPointSize(9)
        painter.setFont(font)
        for frac, label in ((1.0, f"{ymax:.0f}"), (0.5, f"{ymax/2:.0f}"), (0.0, "0")):
            y = rect.bottom() - frac * rect.height()
            painter.drawText(8, int(y + 4), label)
            painter.setPen(QPen(QColor(COLORS["border"]), 1, Qt.DotLine))
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            painter.setPen(QColor(COLORS["muted"]))

        n = len(self._values)
        if n == 1:
            points = [(rect.left(), rect.bottom() - (self._values[0] / ymax) * rect.height())]
        else:
            points = []
            for i, v in enumerate(self._values):
                x = rect.left() + (i / (n - 1)) * rect.width()
                y = rect.bottom() - (max(0.0, min(v, ymax)) / ymax) * rect.height()
                points.append((x, y))

        pen = QPen(self.line_color, 2)
        painter.setPen(pen)
        for i in range(1, len(points)):
            painter.drawLine(
                int(points[i - 1][0]),
                int(points[i - 1][1]),
                int(points[i][0]),
                int(points[i][1]),
            )

        # Fill under curve lightly
        if len(points) >= 2:
            path = QPainterPath()
            path.moveTo(points[0][0], rect.bottom())
            for x, y in points:
                path.lineTo(x, y)
            path.lineTo(points[-1][0], rect.bottom())
            path.closeSubpath()
            fill = QColor(self.line_color)
            fill.setAlpha(40)
            painter.fillPath(path, fill)

        painter.end()


class DualHistoryChart(QWidget):
    """Two-series chart (e.g. download / upload)."""

    def __init__(self, parent: Optional[QWidget] = None, title: str = "") -> None:
        super().__init__(parent)
        self.title = title
        self._a: List[float] = []
        self._b: List[float] = []
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_series(self, a: Sequence[float], b: Sequence[float]) -> None:
        self._a = [float(x) for x in a]
        self._b = [float(x) for x in b]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(COLORS["panel"]))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)

        if self.title:
            painter.setPen(QColor(COLORS["muted"]))
            font = QFont(painter.font())
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(16, 20, self.title.upper())

        rect = self.rect().adjusted(56, 32, -12, -24)
        values = self._a + self._b
        if not values:
            painter.end()
            return

        ymax = max(max(values), 1.0) * 1.15

        def draw_series(series: List[float], color: str) -> None:
            if not series:
                return
            n = len(series)
            pts = []
            for i, v in enumerate(series):
                x = rect.left() if n == 1 else rect.left() + (i / (n - 1)) * rect.width()
                y = rect.bottom() - (v / ymax) * rect.height()
                pts.append((x, y))
            painter.setPen(QPen(QColor(color), 2))
            for i in range(1, len(pts)):
                painter.drawLine(int(pts[i - 1][0]), int(pts[i - 1][1]), int(pts[i][0]), int(pts[i][1]))

        # Y labels
        from utils import format_bytes

        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(6, int(rect.top() + 4), format_bytes(ymax) + "/s")
        painter.drawText(6, int(rect.bottom()), "0")

        draw_series(self._a, COLORS["chart"])
        draw_series(self._b, COLORS["chart2"])
        painter.end()
