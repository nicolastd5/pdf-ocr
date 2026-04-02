from PyQt6.QtWidgets import QProgressBar


class GradientProgressBar(QProgressBar):
    """QProgressBar estilizado com gradiente teal→sky. Altura fixa 6px."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)

    def set(self, value: float):
        """Aceita float 0-100, igual à API do CanvasProgressBar do Tkinter."""
        self.setValue(int(value))
