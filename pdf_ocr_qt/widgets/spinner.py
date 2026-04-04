import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from pdf_ocr_qt.styles import C


class _OrbitCanvas(QWidget):
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


class SpinnerDialog(QWidget):
    """Overlay de progresso — widget filho flutuante, sem QDialog fantasma."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Janela sem decoração, transparente, sempre visível sobre o pai
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.hide()

        # Painel central com fundo sólido arredondado
        panel = QWidget(self)
        panel.setObjectName("spinner_panel")
        panel.setStyleSheet(f"""
            QWidget#spinner_panel {{
                background-color: {C["panel"]};
                border-radius: 14px;
                border: 1px solid {C["border"]};
            }}
        """)

        inner = QVBoxLayout(panel)
        inner.setContentsMargins(36, 32, 36, 32)
        inner.setSpacing(14)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._orbit = _OrbitCanvas()
        inner.addWidget(self._orbit, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status_lbl = QLabel("Processando...")
        self._status_lbl.setStyleSheet(
            f"color: {C['fg']}; font-size: 14px; background: transparent;")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self._status_lbl)

        self._page_lbl = QLabel("")
        self._page_lbl.setStyleSheet(
            f"color: {C['fg_dim']}; font-size: 12px; background: transparent;")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self._page_lbl)

        # Layout externo só para dimensionar o widget raiz igual ao panel
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(panel)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._orbit.step)

    def paintEvent(self, event):
        # Não pinta nada no widget raiz — o fundo deve ser completamente
        # transparente para que só o panel arredondado apareça.
        pass

    def show_spinner(self, status: str = "Processando..."):
        self._status_lbl.setText(status)
        self._page_lbl.setText("")
        self._timer.start(40)
        self._center_on_parent()
        self.show()
        self.raise_()

    def hide_spinner(self):
        self._timer.stop()
        self.hide()

    def set_status(self, msg: str):
        self._status_lbl.setText(msg)

    def set_page(self, current: int, total: int):
        self._page_lbl.setText(f"{current} / {total}")

    def _center_on_parent(self):
        p = self.parent()
        if p is None:
            return
        self.adjustSize()
        parent_center = p.mapToGlobal(p.rect().center())
        self.move(parent_center - self.rect().center())
