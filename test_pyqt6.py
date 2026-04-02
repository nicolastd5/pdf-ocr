"""
Protótipo visual PyQt6 — PDF Tools
Teste de layout e tema Ocean/Teal
"""
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QListWidget, QStackedWidget,
    QFileDialog, QProgressBar, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush
import sys

# ── Paleta ────────────────────────────────────────────────────────
C = {
    "bg":        "#1e1e1e",
    "panel":     "#252526",
    "input":     "#2d2d2d",
    "border":    "#3a3a3a",
    "fg":        "#d4d4d4",
    "fg_dim":    "#888888",
    "fg_bright": "#ffffff",
    "accent":    "#2dd4bf",
    "accent2":   "#38bdf8",
    "sel":       "#264f78",
}

GLOBAL_STYLE = f"""
QWidget {{
    background-color: {C["bg"]};
    color: {C["fg"]};
    font-family: 'Segoe UI';
    font-size: 13px;
}}
QFrame#sidebar {{
    background-color: {C["panel"]};
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
    border: none;
    border-radius: 4px;
    padding: 5px 12px;
}}
QPushButton#flat_btn:hover {{
    background-color: {C["border"]};
}}
QPushButton#accent_btn {{
    background-color: {C["accent"]};
    color: #0f172a;
    border: none;
    border-radius: 5px;
    padding: 9px 18px;
    font-weight: bold;
    font-size: 13px;
}}
QPushButton#accent_btn:hover {{
    background-color: #26b8a6;
}}
QPushButton#accent_btn:disabled {{
    opacity: 0.4;
    background-color: {C["border"]};
    color: {C["fg_dim"]};
}}
QListWidget {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    color: {C["fg"]};
    font-size: 13px;
}}
QListWidget::item:selected {{
    background-color: {C["sel"]};
    color: {C["fg_bright"]};
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
QLabel#title {{
    color: {C["accent"]};
    font-size: 18px;
    font-weight: bold;
}}
QLabel#version {{
    color: {C["fg_dim"]};
    font-size: 11px;
}}
QLabel#section {{
    color: {C["fg"]};
    font-size: 13px;
    font-weight: bold;
}}
QLabel#dim {{
    color: {C["fg_dim"]};
    font-size: 12px;
}}
QFrame#card {{
    background-color: {C["panel"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
}}
QFrame#preview {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
QFrame#drop_area {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
"""

def nav_btn(text):
    b = QPushButton(text)
    b.setObjectName("nav_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def flat_btn(text):
    b = QPushButton(text)
    b.setObjectName("flat_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def accent_btn(text):
    b = QPushButton(text)
    b.setObjectName("accent_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class MergePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        lbl = QLabel("PDFs para juntar")
        lbl.setObjectName("section")
        self.count_lbl = QLabel("(0 arquivos)")
        self.count_lbl.setObjectName("dim")
        hdr.addWidget(lbl)
        hdr.addWidget(self.count_lbl)
        hdr.addStretch()
        hdr.addWidget(flat_btn("+ Adicionar PDFs"))
        hdr.addWidget(flat_btn("✕ Remover"))
        layout.addLayout(hdr)

        # Lista + botões ordem
        list_row = QHBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(130)
        self.file_list.addItems([
            "relatorio_2024.pdf",
            "anexo_contrato.pdf",
            "paginas_extras.pdf",
        ])
        list_row.addWidget(self.file_list)
        ord_v = QVBoxLayout()
        ord_v.addWidget(flat_btn("↑"))
        ord_v.addWidget(flat_btn("↓"))
        ord_v.addStretch()
        list_row.addLayout(ord_v)
        layout.addLayout(list_row)

        # Drop area
        drop = QFrame()
        drop.setObjectName("drop_area")
        drop_lbl = QLabel("⊞  Arraste PDFs aqui  ou  clique em + Adicionar PDFs")
        drop_lbl.setObjectName("dim")
        drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_lbl.setContentsMargins(0, 10, 0, 10)
        drop_layout = QVBoxLayout(drop)
        drop_layout.setContentsMargins(0, 0, 0, 0)
        drop_layout.addWidget(drop_lbl)
        layout.addWidget(drop)

        # Preview
        preview = QFrame()
        preview.setObjectName("preview")
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        prev_layout = QVBoxLayout(preview)
        prev_lbl = QLabel("Selecione um PDF para pré-visualizar")
        prev_lbl.setObjectName("dim")
        prev_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prev_layout.addWidget(prev_lbl)
        layout.addWidget(preview, stretch=1)

        # Destino
        self.same_dir = QCheckBox("Salvar na mesma pasta do primeiro PDF")
        self.same_dir.setChecked(True)
        layout.addWidget(self.same_dir)

        # Status + progress
        self.status_lbl = QLabel("Adicione PDFs para juntar.")
        self.status_lbl.setObjectName("dim")
        layout.addWidget(self.status_lbl)
        pb = QProgressBar()
        pb.setValue(45)
        pb.setFixedHeight(6)
        pb.setTextVisible(False)
        layout.addWidget(pb)

        # Botões
        btn_row = QHBoxLayout()
        btn_row.addWidget(accent_btn("  ⊞  Juntar PDFs  "))
        btn_row.addWidget(flat_btn("Limpar lista"))
        btn_row.addStretch()
        layout.addLayout(btn_row)


class OcrPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Arquivos para OCR")
        lbl.setObjectName("section")
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(flat_btn("+ Adicionar PDFs"))
        hdr.addWidget(flat_btn("✕ Remover"))
        layout.addLayout(hdr)

        file_list = QListWidget()
        file_list.setFixedHeight(150)
        file_list.addItems(["documento_escaneado.pdf", "contrato_assinado.pdf"])
        layout.addWidget(file_list)

        drop = QFrame()
        drop.setObjectName("drop_area")
        drop_lbl = QLabel("⊞  Arraste PDFs aqui")
        drop_lbl.setObjectName("dim")
        drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_lbl.setContentsMargins(0, 10, 0, 10)
        drop_layout = QVBoxLayout(drop)
        drop_layout.setContentsMargins(0, 0, 0, 0)
        drop_layout.addWidget(drop_lbl)
        layout.addWidget(drop)

        opts = QHBoxLayout()
        opts.addWidget(QCheckBox("Destacar nomes detectados"))
        opts.addStretch()
        layout.addLayout(opts)

        layout.addStretch()

        status = QLabel("Selecione arquivos para iniciar o OCR.")
        status.setObjectName("dim")
        layout.addWidget(status)

        pb = QProgressBar()
        pb.setValue(0)
        pb.setFixedHeight(6)
        pb.setTextVisible(False)
        layout.addWidget(pb)

        btn_row = QHBoxLayout()
        btn_row.addWidget(accent_btn("  🔍  Aplicar OCR  "))
        btn_row.addStretch()
        layout.addLayout(btn_row)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tools  v1.0.5")
        self.resize(1200, 850)
        self.setMinimumSize(1000, 700)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        logo = QLabel("PDF Tools")
        logo.setObjectName("title")
        logo.setContentsMargins(16, 20, 16, 4)
        ver = QLabel("v1.0.5")
        ver.setObjectName("version")
        ver.setContentsMargins(16, 0, 16, 20)
        side_layout.addWidget(logo)
        side_layout.addWidget(ver)

        self.nav_buttons = {}
        pages_map = [
            ("ocr",      "🔍  OCR"),
            ("compress", "🗜  Comprimir"),
            ("word",     "📄  PDF → Word"),
            ("split",    "✂  Dividir"),
            ("merge",    "⊞  Juntar"),
            ("about",    "ℹ  Sobre"),
        ]
        for key, label in pages_map:
            btn = nav_btn(label)
            btn.clicked.connect(lambda _, k=key: self.navigate(k))
            side_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        side_layout.addStretch()
        main_layout.addWidget(sidebar)

        # ── Content ───────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.pages = {
            "ocr":      OcrPage(),
            "compress": self._placeholder("Comprimir — em breve"),
            "word":     self._placeholder("PDF → Word — em breve"),
            "split":    self._placeholder("Dividir — em breve"),
            "merge":    MergePage(),
            "about":    self._placeholder("Sobre"),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        main_layout.addWidget(self.stack)

        self._active = None
        self.navigate("ocr")

    def _placeholder(self, text):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel(text)
        lbl.setObjectName("dim")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)
        return w

    def navigate(self, key):
        if self._active:
            self.nav_buttons[self._active].setProperty("active", False)
            self.nav_buttons[self._active].style().unpolish(self.nav_buttons[self._active])
            self.nav_buttons[self._active].style().polish(self.nav_buttons[self._active])
        self._active = key
        self.nav_buttons[key].setProperty("active", True)
        self.nav_buttons[key].style().unpolish(self.nav_buttons[key])
        self.nav_buttons[key].style().polish(self.nav_buttons[key])
        self.stack.setCurrentWidget(self.pages[key])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
