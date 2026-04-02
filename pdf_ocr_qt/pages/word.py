import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QCheckBox, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from pdf_ocr_qt.styles import flat_btn, accent_btn
from pdf_ocr_qt.workers import WordWorker
from pdf_ocr_qt.widgets.spinner import SpinnerDialog
from pdf_ocr_qt.widgets.progress import GradientProgressBar


class WordPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[str] = []
        self._worker: WordWorker | None = None
        self._spinner = SpinnerDialog(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("PDFs para converter em Word")
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

        self._list = QListWidget()
        self._list.setFixedHeight(150)
        layout.addWidget(self._list)

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

        self._same_dir = QCheckBox("Salvar na mesma pasta do arquivo original")
        self._same_dir.setChecked(True)
        layout.addWidget(self._same_dir)

        layout.addStretch()

        self._status = QLabel("Adicione PDFs para converter.")
        self._status.setObjectName("status_lbl")
        layout.addWidget(self._status)
        self._pb = GradientProgressBar()
        layout.addWidget(self._pb)

        btn_row = QHBoxLayout()
        self._btn = accent_btn("  📄  Converter para Word  ")
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
        out_dir = (None if self._same_dir.isChecked()
                   else QFileDialog.getExistingDirectory(
                       self, "Pasta de destino"))
        if not self._same_dir.isChecked() and not out_dir:
            return

        self._btn.setEnabled(False)
        self._pb.set(0)
        self._spinner.show_spinner("Convertendo para Word...")

        self._worker = WordWorker(list(self._files), out_dir or "", self)
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
            QMessageBox.warning(self, "Erros", "\n".join(errors))
        else:
            self._status.setText(
                f"Concluído! {len(ok_files)} arquivo(s) convertido(s).")
            QMessageBox.information(self, "Conversão concluída",
                f"{len(ok_files)} arquivo(s) Word gerado(s)!\n\n"
                + "\n".join(os.path.basename(p) for p in ok_files))

    def _on_error(self, msg: str):
        self._spinner.hide_spinner()
        self._btn.setEnabled(True)
        self._status.setText(f"Erro: {msg}")
        QMessageBox.critical(self, "Erro", msg)
