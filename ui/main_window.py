"""Main application window with sidebar navigation."""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models import SystemSnapshot
from services.database import MetricsDatabase
from services.monitor import MonitoringEngine
from ui.network import NetworkPage
from ui.overview import OverviewPage
from ui.performance import PerformancePage
from ui.processes import ProcessesPage
from ui.storage import StoragePage
from ui.system_page import SystemPage
from ui.theme import STYLESHEET
from ui.widgets import StatusChip


class _SnapshotBridge(QObject):
    """Marshal snapshots from the monitor thread onto the Qt event loop."""

    snapshot_ready = Signal(object)


class MainWindow(QMainWindow):
    def __init__(
        self,
        engine: MonitoringEngine,
        database: Optional[MetricsDatabase] = None,
    ) -> None:
        super().__init__()
        self.engine = engine
        self.database = database
        self.setWindowTitle("Monitor Me")
        self.resize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        self._bridge = _SnapshotBridge()
        self._bridge.snapshot_ready.connect(self._on_snapshot)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 20, 12, 20)
        side_layout.setSpacing(4)

        brand = QLabel("MONITOR\nME")
        brand.setStyleSheet("font-size: 14px; font-weight: 800; letter-spacing: 1px; color: #e6edf3;")
        side_layout.addWidget(brand)
        side_layout.addSpacing(20)

        self._nav_buttons: Dict[str, QPushButton] = {}
        self.stack = QStackedWidget()

        pages = [
            ("Overview", "overview"),
            ("Processes", "processes"),
            ("Performance", "performance"),
            ("Storage", "storage"),
            ("Network", "network"),
            ("System", "system"),
        ]
        for label, key in pages:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCursor(btn.cursor())
            btn.clicked.connect(lambda checked=False, k=key: self._navigate(k))
            side_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        side_layout.addStretch()
        layout.addWidget(sidebar)

        # Content column
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        topbar = QHBoxLayout()
        topbar.setContentsMargins(24, 16, 24, 8)
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("titleLabel")
        topbar.addWidget(self.page_title)
        topbar.addStretch()
        self.status_chip = StatusChip()
        topbar.addWidget(self.status_chip)
        content.addLayout(topbar)
        content.addWidget(self.stack, stretch=1)

        content_wrap = QWidget()
        content_wrap.setLayout(content)
        layout.addWidget(content_wrap, stretch=1)

        # Pages
        self.overview = OverviewPage()
        self.processes_page = ProcessesPage()
        self.performance = PerformancePage(
            database=database,
            live_history_provider=self.engine.history_list,
        )
        self.storage = StoragePage()
        self.network = NetworkPage()
        self.system = SystemPage()

        self._page_index = {
            "overview": 0,
            "processes": 1,
            "performance": 2,
            "storage": 3,
            "network": 4,
            "system": 5,
        }
        for page in (
            self.overview,
            self.processes_page,
            self.performance,
            self.storage,
            self.network,
            self.system,
        ):
            self.stack.addWidget(page)

        self.processes_page.status_message.connect(self.statusBar().showMessage)
        self._navigate("overview")

        # Hook engine
        self.engine.add_listener(self._bridge.snapshot_ready.emit)
        self.engine.start()

        # Refresh performance charts periodically
        self._perf_timer = QTimer(self)
        self._perf_timer.setInterval(5000)
        self._perf_timer.timeout.connect(self.performance.refresh)
        self._perf_timer.start()

        self.statusBar().showMessage("Monitoring started")

    def _navigate(self, key: str) -> None:
        titles = {
            "overview": "Overview",
            "processes": "Processes",
            "performance": "Performance",
            "storage": "Storage",
            "network": "Network",
            "system": "System",
        }
        self.stack.setCurrentIndex(self._page_index[key])
        self.page_title.setText(titles[key])
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if key == "performance":
            self.performance.refresh()

    @Slot(object)
    def _on_snapshot(self, snapshot: object) -> None:
        if not isinstance(snapshot, SystemSnapshot):
            return
        history = self.engine.history_list()
        status = self.engine.alerts.soft_status(snapshot)
        self.status_chip.set_status(status.value)

        self.overview.update_snapshot(snapshot, history)
        self.overview.update_alerts(self.engine.alerts.alerts)
        self.processes_page.update_processes(snapshot.processes)
        self.storage.update_snapshot(snapshot)
        self.network.update_snapshot(snapshot, history)
        self.system.update_snapshot(snapshot)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.engine.stop()
        self.engine.remove_listener(self._bridge.snapshot_ready.emit)
        super().closeEvent(event)
