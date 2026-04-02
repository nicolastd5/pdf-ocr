import math
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from pdf_ocr_qt.styles import C


class _OrbitCanvas(QWidget):
    """Canvas que desenha dois círculos orbitais animados."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._angle1 = 0.0
        self._angle2 = 180.0

    def step(self):
        self._angle1 = (self._angle1 + 6) % 360
        self._angle2 = (self._angle2 + 9) % 360
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = 32, 32, 22

        def dot(angle, size, color):
            rad = math.radians(angle)
            x = cx + r * math.cos(rad) - size / 2
            y = cy + r * math.sin(rad) - size / 2
            p.setBrush(QColor(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(x, y, size, size))

        dot(self._angle1, 12, C["accent"])
        dot(self._angle2,  8, C["accent2"])
        p.end()


class SpinnerDialog(QDialog):
    """Modal animado de progresso — equivalente ao SpinnerWindow do Tkinter."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Fundo escuro arredondado
        inner = QWidget(self)
        inner.setStyleSheet(f"""
            background-color: {C["panel"]};
            border-radius: 12px;
            border: 1px solid {C["border"]};
        """)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(32, 28, 32, 28)
        inner_layout.setSpacing(12)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._orbit = _OrbitCanvas()
        inner_layout.addWidget(self._orbit, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status_lbl = QLabel("Processando...")
        self._status_lbl.setStyleSheet(f"color: {C['fg']}; font-size: 14px; background: transparent;")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self._status_lbl)

        self._page_lbl = QLabel("")
        self._page_lbl.setStyleSheet(f"color: {C['fg_dim']}; font-size: 12px; background: transparent;")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self._page_lbl)

        layout.addWidget(inner)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._orbit.step)

    def show_spinner(self, status: str = "Processando..."):
        self._status_lbl.setText(status)
        self._page_lbl.setText("")
        self._timer.start(40)  # ~25 fps
        if self.parent():
            p = self.parent()
            self.move(
                p.mapToGlobal(p.rect().center()) -
                self.rect().center()
            )
        self.show()

    def hide_spinner(self):
        self._timer.stop()
        self.hide()

    def set_status(self, msg: str):
        self._status_lbl.setText(msg)

    def set_page(self, current: int, total: int):
        self._page_lbl.setText(f"{current} / {total}")
