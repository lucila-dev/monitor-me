"""Processes page: searchable, sortable table with terminate action."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from collectors.processes import terminate_process
from models import ProcessInfo
from utils import format_bytes


class ProcessesPage(QWidget):
    status_message = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._all: List[ProcessInfo] = []
        self._sort_col = 2  # CPU
        self._sort_desc = True

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Processes")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search processes…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self._apply_filter)
        header.addWidget(self.search)

        self.kill_btn = QPushButton("End Process")
        self.kill_btn.setObjectName("dangerButton")
        self.kill_btn.clicked.connect(self._end_selected)
        header.addWidget(self.kill_btn)
        root.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Process", "PID", "CPU", "Memory", "User"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        root.addWidget(self.table)

        self.count_label = QLabel("")
        self.count_label.setObjectName("metricCaption")
        root.addWidget(self.count_label)

    def update_processes(self, processes: List[ProcessInfo]) -> None:
        self._all = processes
        self._apply_filter()

    def _on_header_clicked(self, index: int) -> None:
        if self._sort_col == index:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = index
            self._sort_desc = True
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search.text().strip().lower()
        rows = self._all
        if query:
            rows = [p for p in rows if query in p.name.lower() or query in str(p.pid)]

        def sort_key(p: ProcessInfo):
            return (
                p.name.lower(),
                p.pid,
                p.cpu_percent,
                p.memory_rss,
                p.username.lower(),
            )[self._sort_col]

        rows = sorted(rows, key=sort_key, reverse=self._sort_desc)

        self.table.setRowCount(len(rows))
        for i, proc in enumerate(rows):
            name_item = QTableWidgetItem(proc.name)
            name_item.setData(Qt.UserRole, proc.pid)
            self.table.setItem(i, 0, name_item)

            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.DisplayRole, proc.pid)
            self.table.setItem(i, 1, pid_item)

            cpu_item = QTableWidgetItem()
            cpu_item.setData(Qt.DisplayRole, round(proc.cpu_percent, 1))
            self.table.setItem(i, 2, cpu_item)

            mem_item = QTableWidgetItem(format_bytes(proc.memory_rss))
            mem_item.setData(Qt.UserRole, proc.memory_rss)
            self.table.setItem(i, 3, mem_item)

            self.table.setItem(i, 4, QTableWidgetItem(proc.username))

        arrow = "↓" if self._sort_desc else "↑"
        headers = ["Process", "PID", "CPU", "Memory", "User"]
        for i, h in enumerate(headers):
            label = f"{h} {arrow}" if i == self._sort_col else h
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(label))

        self.count_label.setText(f"{len(rows)} processes")

    def _end_selected(self) -> None:
        items = self.table.selectedItems()
        if not items:
            QMessageBox.information(self, "End Process", "Select a process first.")
            return
        row = self.table.currentRow()
        name_item = self.table.item(row, 0)
        pid_item = self.table.item(row, 1)
        if not name_item or not pid_item:
            return
        pid = int(pid_item.data(Qt.DisplayRole))
        name = name_item.text()

        reply = QMessageBox.warning(
            self,
            "Confirm End Process",
            f"Terminate “{name}” (PID {pid})?\n\n"
            "Unsaved work in that application may be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ok, message = terminate_process(pid)
        if ok:
            self.status_message.emit(message)
            self._all = [p for p in self._all if p.pid != pid]
            self._apply_filter()
        else:
            QMessageBox.critical(self, "Could not end process", message)
