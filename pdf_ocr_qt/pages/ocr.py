import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from pdf_ocr_qt.styles import flat_btn, accent_btn
from pdf_ocr_qt.workers import OcrWorker
from pdf_ocr_qt.widgets.spinner import SpinnerDialog
from pdf_ocr_qt.widgets.progress import GradientProgressBar


LANGUAGES = [
    ("Português",           "por"),
    ("Inglês",              "eng"),
    ("Português + Inglês",  "por+eng"),
    ("Espanhol",            "spa"),
    ("Francês",             "fra"),
    ("Alemão",              "deu"),
]


class OcrPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[str] = []
        self._worker: OcrWorker | None = None
        self._spinner = SpinnerDialog(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        lbl = QLabel("Arquivos para OCR")
        lbl.setObjectName("section_lbl")
        self._count_lbl = QLabel("(0 arquivos)")
        self._count_lbl.setObjectName("dim_lbl")
        hdr.addWidget(lbl)
        hdr.addWidget(self._count_lbl)
        hdr.addStretch()
        btn_add = flat_btn("+ Adicionar PDFs")
        btn_add.clicked.connect(self._add_files)
        btn_rem = flat_btn("✕ Remover")
        btn_rem.clicked.connect(self._remove_selected)
        hdr.addWidget(btn_add)
        hdr.addWidget(btn_rem)
        layout.addLayout(hdr)

        # Lista
        self._list = QListWidget()
        self._list.setFixedHeight(150)
        layout.addWidget(self._list)

        # Drop area
        drop = QFrame()
        drop.setObjectName("drop_area")
        drop.setAcceptDrops(True)
        drop.dragEnterEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else None
        drop.dropEvent = self.dropEvent
        drop_lbl = QLabel("⊞  Arraste PDFs aqui  ou  clique em + Adicionar PDFs")
        drop_lbl.setObjectName("dim_lbl")
        drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_lbl.setContentsMargins(0, 10, 0, 10)
        dl = QVBoxLayout(drop)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.addWidget(drop_lbl)
        layout.addWidget(drop)

        # Opções
        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("Idioma:"))
        self._lang_combo = QComboBox()
        for label, _ in LANGUAGES:
            self._lang_combo.addItem(label)
        opts_row.addWidget(self._lang_combo)
        opts_row.addSpacing(20)
        self._highlight = QCheckBox("Destacar nomes detectados")
        self._highlight.setChecked(True)
        opts_row.addWidget(self._highlight)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        # Destino
        self._same_dir = QCheckBox("Salvar na mesma pasta do arquivo original")
        self._same_dir.setChecked(True)
        layout.addWidget(self._same_dir)

        layout.addStretch()

        # Status + progress
        self._status = QLabel("Selecione arquivos para iniciar o OCR.")
        self._status.setObjectName("status_lbl")
        layout.addWidget(self._status)
        self._pb = GradientProgressBar()
        layout.addWidget(self._pb)

        # Botão
        btn_row = QHBoxLayout()
        self._btn = accent_btn("  🔍  Aplicar OCR  ")
        self._btn.clicked.connect(self._start)
        btn_row.addWidget(self._btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._files.append(path)
                self._list.addItem(os.path.basename(path))
        self._update_count()

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar PDFs", "", "PDF (*.pdf)")
        for p in paths:
            self._files.append(p)
            self._list.addItem(os.path.basename(p))
        self._update_count()

    def _remove_selected(self):
        row = self._list.currentRow()
        if row >= 0:
            self._list.takeItem(row)
            self._files.pop(row)
            self._update_count()

    def _update_count(self):
        n = self._list.count()
        self._count_lbl.setText(f"({n} arquivo{'s' if n != 1 else ''})")

    def _start(self):
        if not self._files:
            self._status.setText("Adicione PDFs primeiro.")
            return
        lang = LANGUAGES[self._lang_combo.currentIndex()][1]
        highlight = self._highlight.isChecked()
        out_dir = (None if self._same_dir.isChecked()
                   else QFileDialog.getExistingDirectory(
                       self, "Pasta de destino"))
        if not self._same_dir.isChecked() and not out_dir:
            return

        from pdf_ocr_qt.main import find_poppler, check_tesseract
        if not check_tesseract():
            QMessageBox.critical(self, "Tesseract não encontrado",
                "Instale o Tesseract OCR e tente novamente.")
            return

        self._btn.setEnabled(False)
        self._pb.set(0)
        self._spinner.show_spinner("Aplicando OCR...")

        self._worker = OcrWorker(
            list(self._files), out_dir or "",
            lang, highlight, find_poppler(),
            parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, status: str):
        self._spinner.set_status(status)
        self._spinner.set_page(current, total)
        self._pb.set(current / total * 100)
        self._status.setText(status)

    def _on_finished(self, ok_files: list, errors: list):
        self._spinner.hide_spinner()
        self._btn.setEnabled(True)
        self._pb.set(100)
        if errors:
            self._status.setText(f"Concluído com {len(errors)} erro(s).")
            QMessageBox.warning(self, "OCR com erros", "\n".join(errors))
        else:
            extra = " · nomes destacados" if self._highlight.isChecked() else ""
            self._status.setText(
                f"Concluído! {len(ok_files)} arquivo(s) processado(s).{extra}")
            QMessageBox.information(self, "OCR concluído",
                f"{len(ok_files)} PDF(s) pesquisável(is) gerado(s)!\n\n"
                + "\n".join(os.path.basename(p) for p in ok_files)
                + "\n\nUse CTRL+F no leitor de PDF para pesquisar.")

    def _on_error(self, msg: str):
        self._spinner.hide_spinner()
        self._btn.setEnabled(True)
        self._status.setText(f"Erro: {msg}")
        QMessageBox.critical(self, "Erro no OCR", msg)
