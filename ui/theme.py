"""Shared dark theme stylesheet and colors."""

COLORS = {
    "bg": "#0f1419",
    "panel": "#161b22",
    "sidebar": "#0d1117",
    "border": "#30363d",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#3fb950",
    "warning": "#d29922",
    "critical": "#f85149",
    "chart": "#58a6ff",
    "chart2": "#3fb950",
    "bar_track": "#21262d",
}

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f1419;
    color: #e6edf3;
    font-family: -apple-system, "Helvetica Neue", "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #0d1117;
    border-right: 1px solid #30363d;
}
QPushButton#navButton {
    background: transparent;
    border: none;
    text-align: left;
    padding: 12px 18px;
    color: #8b949e;
    border-radius: 6px;
    font-size: 14px;
}
QPushButton#navButton:hover {
    background-color: #161b22;
    color: #e6edf3;
}
QPushButton#navButton[active="true"] {
    background-color: #21262d;
    color: #e6edf3;
    font-weight: 600;
}
QFrame#metricCard {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
}
QLabel#titleLabel {
    font-size: 20px;
    font-weight: 700;
    color: #e6edf3;
}
QLabel#sectionLabel {
    font-size: 12px;
    font-weight: 600;
    color: #8b949e;
    letter-spacing: 0.6px;
}
QLabel#metricValue {
    font-size: 28px;
    font-weight: 700;
    color: #e6edf3;
}
QLabel#metricCaption {
    color: #8b949e;
    font-size: 12px;
}
QLineEdit, QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 10px;
    color: #e6edf3;
    selection-background-color: #388bfd;
}
QTableWidget {
    background-color: #161b22;
    alternate-background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
}
QHeaderView::section {
    background-color: #0d1117;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item:selected {
    background-color: #1f6feb;
}
QPushButton#primaryButton {
    background-color: #238636;
    color: white;
    border: 1px solid #2ea043;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #2ea043;
}
QPushButton#dangerButton {
    background-color: #da3633;
    color: white;
    border: 1px solid #f85149;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton#dangerButton:hover {
    background-color: #f85149;
}
QPushButton#rangeButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #8b949e;
}
QPushButton#rangeButton[active="true"] {
    background-color: #1f6feb;
    border-color: #388bfd;
    color: white;
}
QScrollArea {
    border: none;
}
QStatusBar {
    background-color: #0d1117;
    color: #8b949e;
    border-top: 1px solid #30363d;
}
"""
