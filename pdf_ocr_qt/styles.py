from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont

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


def _make_icon(draw_fn, size: int = 20) -> QIcon:
    """Cria um QIcon 20×20 usando uma função de desenho QPainter."""
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(p, size)
    p.end()
    return QIcon(pix)


def icon_split() -> QIcon:
    """✂ Ícone de dividir: uma folha com linha tracejada horizontal no meio."""
    def draw(p: QPainter, s: int):
        fg = QColor(C["fg_dim"])
        acc = QColor(C["accent"])
        pen = QPen(fg, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(QColor(C["input"]))
        # Folha PDF
        margin = 3
        fold = 5
        path = QPainterPath()
        path.moveTo(margin, margin)
        path.lineTo(s - margin - fold, margin)
        path.lineTo(s - margin, margin + fold)
        path.lineTo(s - margin, s - margin)
        path.lineTo(margin, s - margin)
        path.closeSubpath()
        p.drawPath(path)
        # Linha tracejada central
        dash_pen = QPen(acc, 1.5)
        dash_pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(dash_pen)
        mid = s // 2
        p.drawLine(margin + 1, mid, s - margin - 1, mid)
        # Setas apontando para fora (cima e baixo)
        arr = QPen(acc, 1.5)
        arr.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arr)
        cx = s // 2
        # seta cima
        p.drawLine(cx, mid - 2, cx, margin + 1)
        p.drawLine(cx - 2, margin + 3, cx, margin + 1)
        p.drawLine(cx + 2, margin + 3, cx, margin + 1)
        # seta baixo
        p.drawLine(cx, mid + 2, cx, s - margin - 1)
        p.drawLine(cx - 2, s - margin - 3, cx, s - margin - 1)
        p.drawLine(cx + 2, s - margin - 3, cx, s - margin - 1)
    return _make_icon(draw)


def icon_merge() -> QIcon:
    """⊞ Ícone de juntar: duas folhas pequenas convergindo para uma maior."""
    def draw(p: QPainter, s: int):
        fg = QColor(C["fg_dim"])
        acc = QColor(C["accent"])
        pen = QPen(fg, 1.2)
        p.setPen(pen)
        p.setBrush(QColor(C["input"]))
        # Folha esquerda (menor, atrás)
        p.drawRoundedRect(QRectF(2, 4, 7, 9), 1, 1)
        # Folha direita (menor, atrás)
        p.drawRoundedRect(QRectF(11, 4, 7, 9), 1, 1)
        # Setas convergindo
        arr = QPen(acc, 1.5)
        arr.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arr)
        mid = s // 2
        # seta esquerda →
        p.drawLine(9, mid, 11, mid)
        p.drawLine(9, mid, 9 - 2, mid - 2)
        p.drawLine(9, mid, 9 - 2, mid + 2)
        # seta direita ←
        p.drawLine(11, mid, 9, mid)
        p.drawLine(11, mid, 11 + 2, mid - 2)
        p.drawLine(11, mid, 11 + 2, mid + 2)
        # Folha resultado (maior, frente)
        p.setPen(QPen(acc, 1.5))
        p.setBrush(QColor(0, 0, 0, 0))
        p.drawRoundedRect(QRectF(6, 6, 8, 10), 1.5, 1.5)
    return _make_icon(draw)


def icon_about() -> QIcon:
    """ℹ Ícone de informação: círculo com 'i'."""
    def draw(p: QPainter, s: int):
        acc = QColor(C["accent"])
        # Círculo
        pen = QPen(acc, 1.8)
        p.setPen(pen)
        p.setBrush(QColor(0, 0, 0, 0))
        p.drawEllipse(QRectF(2, 2, s - 4, s - 4))
        # Letra i
        p.setBrush(acc)
        p.setPen(Qt.PenStyle.NoPen)
        cx = s / 2
        # ponto do i
        p.drawEllipse(QRectF(cx - 1.2, 5, 2.4, 2.4))
        # haste do i
        p.setBrush(acc)
        p.drawRoundedRect(QRectF(cx - 1.2, 9, 2.4, 7), 1, 1)
    return _make_icon(draw)
