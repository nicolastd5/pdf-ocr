# pdf_ocr_qt/widgets/spacy_install.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pdf_ocr_qt.styles import accent_btn, flat_btn, C
from pdf_ocr_qt.ner import NERPipeline


class _InstallThread(QThread):
    line   = pyqtSignal(str)
    done   = pyqtSignal(bool)   # True = sucesso

    def run(self):
        success = True
        for output in NERPipeline.install_spacy():
            self.line.emit(output)
            if output.startswith("ERRO"):
                success = False
        self.done.emit(success)


class SpacyInstallDialog(QDialog):
    """Diálogo modal que instala spaCy + pt_core_news_lg com log de progresso."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instalar spaCy")
        self.setMinimumWidth(500)
        self.setStyleSheet(
            f"background: {C['panel']}; color: {C['fg']}; font-size: 13px;")
        self._success = False
        self._thread: _InstallThread | None = None
        self._build_ui()

    @property
    def install_succeeded(self) -> bool:
        return self._success

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._msg = QLabel(
            "O spaCy não está instalado.\n"
            "Deseja instalar agora? (~50 MB)")
        self._msg.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._msg)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(180)
        self._log.setStyleSheet(
            f"background: {C['input']}; color: {C['fg_dim']};"
            f" font-family: Consolas, monospace; font-size: 11px;"
            f" border: 1px solid {C['border']};")
        self._log.setVisible(False)
        layout.addWidget(self._log)

        btn_row = QHBoxLayout()
        self._btn_install = accent_btn("Instalar")
        self._btn_install.clicked.connect(self._start_install)
        self._btn_cancel  = flat_btn("Cancelar")
        self._btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_install)
        btn_row.addWidget(self._btn_cancel)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _start_install(self):
        self._btn_install.setEnabled(False)
        self._btn_cancel.setEnabled(False)
        self._log.setVisible(True)
        self._msg.setText("Instalando spaCy e modelo PT…")

        self._thread = _InstallThread(self)
        self._thread.line.connect(self._log.appendPlainText)
        self._thread.done.connect(self._on_done)
        self._thread.start()

    def _on_done(self, success: bool):
        self._success = success
        self._btn_cancel.setEnabled(True)
        if success:
            self._msg.setText("Instalação concluída com sucesso!")
            self.accept()
        else:
            self._msg.setText("Erro durante a instalação. Veja o log acima.")
            self._btn_install.setEnabled(True)
            self._btn_install.setText("Tentar novamente")
