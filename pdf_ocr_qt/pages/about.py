import threading
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from pdf_ocr_qt.styles import flat_btn, accent_btn, C

APP_VERSION      = "2.0.2"
GITHUB_RELEASES_PAGE = "https://github.com/nicolastd5/pdf-ocr/releases"


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo + versão
        title = QLabel("PDF Tools")
        title.setStyleSheet(
            f"color: {C['accent']}; font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("dim_lbl")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        desc = QLabel("OCR • Comprimir • Dividir • Juntar • PDF→Word")
        desc.setObjectName("dim_lbl")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Changelog
        cl_title = QLabel(f"O que há de novo — v{APP_VERSION}")
        cl_title.setObjectName("section_lbl")
        layout.addWidget(cl_title)

        changelog = QLabel(
            "• Corrigido: modelo spaCy (IA) agora é carregado corretamente no EXE\n"
            "• Identificado path real do modelo: pt_core_news_lg/pt_core_news_lg-X.Y.Z/\n"
            "• Corrigido: verificação de atualização e auto-update funcionando\n"
            "• Comunicação thread→UI reescrita com QTimer.singleShot"
        )
        changelog.setObjectName("dim_lbl")
        changelog.setWordWrap(True)
        layout.addWidget(changelog)

        layout.addStretch()

        # Botões
        btn_row = QHBoxLayout()
        btn_update = accent_btn("Verificar atualização")
        btn_update.clicked.connect(self._check_update)
        btn_gh = flat_btn("Ver no GitHub")
        btn_gh.clicked.connect(
            lambda: webbrowser.open(GITHUB_RELEASES_PAGE))
        btn_row.addWidget(btn_update)
        btn_row.addWidget(btn_gh)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._update_lbl = QLabel("")
        self._update_lbl.setObjectName("dim_lbl")
        layout.addWidget(self._update_lbl)

    def _check_update(self):
        self._update_lbl.setText("Verificando...")
        threading.Thread(target=self._fetch_update, daemon=True).start()

    def _fetch_update(self):
        try:
            from pdf_ocr_qt.main import fetch_latest_release
            info = fetch_latest_release()
            tag = info.get("tag", "")
            if tag and tag != APP_VERSION:
                QTimer.singleShot(0, self._show_update)
            else:
                QTimer.singleShot(0, self._show_latest)
        except Exception as e:
            msg = str(e)
            QTimer.singleShot(0, lambda: self._show_error(msg))

    def _show_update(self):
        self._update_lbl.setText("Nova versão disponível!")
        webbrowser.open(GITHUB_RELEASES_PAGE)

    def _show_latest(self):
        self._update_lbl.setText(f"Você está na versão mais recente (v{APP_VERSION})")

    def _show_error(self, msg: str):
        self._update_lbl.setText(f"Erro ao verificar: {msg}")
