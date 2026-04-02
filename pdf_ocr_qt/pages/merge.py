import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QCheckBox, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap
from pdf_ocr_qt.styles import flat_btn, accent_btn, C
from pdf_ocr_qt.workers import MergeWorker
from pdf_ocr_qt.widgets.spinner import SpinnerDialog
from pdf_ocr_qt.widgets.progress import GradientProgressBar


class MergePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[str] = []
        self._worker: MergeWorker | None = None
        self._spinner = SpinnerDialog(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        lbl = QLabel("PDFs para juntar")
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

        # Lista + botões ↑↓
        list_row = QHBoxLayout()
        self._list = QListWidget()
        self._list.setFixedHeight(130)
        self._list.setAcceptDrops(True)
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.currentRowChanged.connect(self._on_select)
        list_row.addWidget(self._list)
        ord_v = QVBoxLayout()
        btn_up = flat_btn("↑")
        btn_up.clicked.connect(self._move_up)
        btn_dn = flat_btn("↓")
        btn_dn.clicked.connect(self._move_down)
        ord_v.addWidget(btn_up)
        ord_v.addWidget(btn_dn)
        ord_v.addStretch()
        list_row.addLayout(ord_v)
        layout.addLayout(list_row)

        # Drop area
        from PyQt6.QtWidgets import QFrame
        drop = QFrame()
        drop.setObjectName("drop_area")
        drop.setAcceptDrops(True)
        drop.dragEnterEvent  = self._drag_enter
        drop.dropEvent       = self._drop_event
        drop_lbl = QLabel("⊞  Arraste PDFs aqui  ou  clique em + Adicionar PDFs")
        drop_lbl.setObjectName("dim_lbl")
        drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_lbl.setContentsMargins(0, 10, 0, 10)
        drop_layout = QVBoxLayout(drop)
        drop_layout.setContentsMargins(0, 0, 0, 0)
        drop_layout.addWidget(drop_lbl)
        layout.addWidget(drop)

        # Preview
        from PyQt6.QtWidgets import QFrame
        preview_frame = QFrame()
        preview_frame.setObjectName("preview_frame")
        preview_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout = QVBoxLayout(preview_frame)
        self._preview_lbl = QLabel("Selecione um PDF para pré-visualizar")
        self._preview_lbl.setObjectName("dim_lbl")
        self._preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_name = QLabel("")
        self._preview_name.setObjectName("dim_lbl")
        self._preview_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self._preview_lbl, stretch=1)
        preview_layout.addWidget(self._preview_name)
        layout.addWidget(preview_frame, stretch=1)

        # Destino
        self._same_dir = QCheckBox("Salvar na mesma pasta do primeiro PDF")
        self._same_dir.setChecked(True)
        layout.addWidget(self._same_dir)

        # Status + progress
        self._status = QLabel("Adicione PDFs para juntar.")
        self._status.setObjectName("status_lbl")
        layout.addWidget(self._status)
        self._pb = GradientProgressBar()
        layout.addWidget(self._pb)

        # Botões ação
        btn_row = QHBoxLayout()
        self._btn_merge = accent_btn("  ⊞  Juntar PDFs  ")
        self._btn_merge.clicked.connect(self._start_merge)
        btn_clear = flat_btn("Limpar lista")
        btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(self._btn_merge)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ── Drag & drop ──────────────────────────────────────────────
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

    def _drag_enter(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def _drop_event(self, e):
        self.dropEvent(e)

    # ── Ações ────────────────────────────────────────────────────
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

    def _move_up(self):
        row = self._list.currentRow()
        if row > 0:
            item = self._list.takeItem(row)
            self._list.insertItem(row - 1, item)
            self._list.setCurrentRow(row - 1)
            self._files.insert(row - 1, self._files.pop(row))

    def _move_down(self):
        row = self._list.currentRow()
        if 0 <= row < self._list.count() - 1:
            item = self._list.takeItem(row)
            self._list.insertItem(row + 1, item)
            self._list.setCurrentRow(row + 1)
            self._files.insert(row + 1, self._files.pop(row))

    def _clear(self):
        self._files.clear()
        self._list.clear()
        self._update_count()
        self._preview_lbl.setText("Selecione um PDF para pré-visualizar")
        self._preview_lbl.setPixmap(QPixmap())
        self._preview_name.setText("")

    def _on_select(self, row: int):
        if row < 0 or row >= len(self._files):
            return
        path = self._files[row]
        self._preview_name.setText(os.path.basename(path))
        self._load_preview(path)

    def _load_preview(self, path: str):
        try:
            from pdf2image import convert_from_path
            from pdf_ocr_qt.main import find_poppler
            imgs = convert_from_path(path, dpi=72,
                                     poppler_path=find_poppler(),
                                     first_page=1, last_page=1)
            if imgs:
                import io
                buf = io.BytesIO()
                imgs[0].save(buf, format="PNG")
                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                h = self._preview_lbl.height() or 300
                pix = pix.scaledToHeight(h,
                    Qt.TransformationMode.SmoothTransformation)
                self._preview_lbl.setPixmap(pix)
                self._preview_lbl.setText("")
        except Exception:
            self._preview_lbl.setText("Erro ao carregar preview")

    def _update_count(self):
        n = self._list.count()
        self._count_lbl.setText(f"({n} arquivo{'s' if n != 1 else ''})")

    def _start_merge(self):
        if self._list.count() < 2:
            self._status.setText("Adicione ao menos 2 PDFs.")
            return
        if self._same_dir.isChecked():
            out_dir = os.path.dirname(self._files[0])
        else:
            out_dir = QFileDialog.getExistingDirectory(
                self, "Pasta de destino")
            if not out_dir:
                return
        out_path = os.path.join(out_dir, "merged.pdf")

        self._btn_merge.setEnabled(False)
        self._pb.set(0)
        self._spinner.show_spinner("Juntando PDFs...")

        self._worker = MergeWorker(list(self._files), out_path, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, status: str):
        self._spinner.set_status(status)
        self._spinner.set_page(current, total)
        self._pb.set(current / total * 100)
        self._status.setText(status)

    def _on_finished(self, out_path: str):
        self._spinner.hide_spinner()
        self._btn_merge.setEnabled(True)
        self._pb.set(100)
        with open(out_path, "rb") as fh:
            import PyPDF2
            n = len(PyPDF2.PdfReader(fh).pages)
        self._status.setText(
            f"PDF gerado: {os.path.basename(out_path)}  ({n} páginas)")
        QMessageBox.information(self, "Concluído",
            f"PDFs juntados com sucesso!\n{out_path}")

    def _on_error(self, msg: str):
        self._spinner.hide_spinner()
        self._btn_merge.setEnabled(True)
        self._status.setText(f"Erro: {msg}")
        QMessageBox.critical(self, "Erro ao juntar", msg)
