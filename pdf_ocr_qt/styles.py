from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

C = {
    "bg":        "#1e1e1e",
    "panel":     "#1a2332",
    "sidebar":   "#141c27",
    "input":     "#1e293b",
    "hover":     "#0f2a3d",
    "border":    "#1e3a4f",
    "accent":    "#2dd4bf",
    "accent2":   "#38bdf8",
    "accent_dk": "#0d9488",
    "accent_fg": "#0f172a",
    "fg":        "#e2e8f0",
    "fg_dim":    "#64748b",
    "fg_bright": "#f8fafc",
    "success":   "#34d399",
    "warn":      "#fbbf24",
    "error":     "#f87171",
    "sel":       "#164e63",
}

QSS = f"""
QWidget {{
    background-color: {C["bg"]};
    color: {C["fg"]};
    font-family: 'Segoe UI';
    font-size: 13px;
}}
QFrame#sidebar {{
    background-color: {C["sidebar"]};
    border-right: 1px solid {C["border"]};
}}
QPushButton#nav_btn {{
    background: transparent;
    color: {C["fg_dim"]};
    border: none;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
}}
QPushButton#nav_btn:hover {{
    background-color: {C["input"]};
    color: {C["fg"]};
}}
QPushButton#nav_btn[active=true] {{
    color: {C["accent"]};
    background-color: {C["input"]};
}}
QPushButton#flat_btn {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 5px 12px;
}}
QPushButton#flat_btn:hover {{
    background-color: {C["hover"]};
}}
QPushButton#flat_btn:disabled {{
    color: {C["fg_dim"]};
    background-color: {C["bg"]};
}}
QPushButton#accent_btn {{
    background-color: {C["accent"]};
    color: {C["accent_fg"]};
    border: none;
    border-radius: 5px;
    padding: 9px 18px;
    font-weight: bold;
    font-size: 13px;
}}
QPushButton#accent_btn:hover {{
    background-color: {C["accent_dk"]};
}}
QPushButton#accent_btn:disabled {{
    background-color: {C["border"]};
    color: {C["fg_dim"]};
}}
QListWidget {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    color: {C["fg"]};
}}
QListWidget::item:selected {{
    background-color: {C["sel"]};
    color: {C["fg_bright"]};
}}
QListWidget::item:hover {{
    background-color: {C["hover"]};
}}
QProgressBar {{
    background-color: {C["input"]};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C["accent"]}, stop:1 {C["accent2"]});
    border-radius: 3px;
}}
QCheckBox {{
    color: {C["fg"]};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {C["border"]};
    border-radius: 3px;
    background: {C["input"]};
}}
QCheckBox::indicator:checked {{
    background: {C["accent"]};
    border-color: {C["accent"]};
}}
QRadioButton {{
    color: {C["fg"]};
    spacing: 6px;
}}
QComboBox {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {C["input"]};
    color: {C["fg"]};
    selection-background-color: {C["sel"]};
}}
QTextEdit {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
QLineEdit {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}
QScrollBar:vertical {{
    background: {C["panel"]};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C["border"]};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QLabel#title_lbl {{
    color: {C["accent"]};
    font-size: 18px;
    font-weight: bold;
}}
QLabel#version_lbl {{
    color: {C["fg_dim"]};
    font-size: 11px;
}}
QLabel#section_lbl {{
    color: {C["fg"]};
    font-weight: bold;
}}
QLabel#dim_lbl {{
    color: {C["fg_dim"]};
    font-size: 12px;
}}
QLabel#status_lbl {{
    color: {C["fg_dim"]};
    font-size: 12px;
}}
QFrame#drop_area {{
    background-color: {C["input"]};
    border: 1px dashed {C["border"]};
    border-radius: 4px;
}}
QFrame#preview_frame {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
QFrame#card {{
    background-color: {C["panel"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
}}
"""


def flat_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("flat_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def accent_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("accent_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def nav_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("nav_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b
