import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QMessageBox, QButtonGroup, QRadioButton, QLineEdit,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from pdf_ocr_qt.styles import flat_btn, accent_btn
from pdf_ocr_qt.workers import SplitWorker
from pdf_ocr_qt.widgets.spinner import SpinnerDialog
from pdf_ocr_qt.widgets.progress import GradientProgressBar


class SplitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._file: str = ""
        self._total_pages: int = 0
        self._worker: SplitWorker | None = None
        self._spinner = SpinnerDialog(self)
        self._preview_page = 1
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Seleção de arquivo
        file_row = QHBoxLayout()
        btn_sel = flat_btn("+ Selecionar PDF")
        btn_sel.clicked.connect(self._select_file)
        self._file_lbl = QLabel("Nenhum arquivo selecionado")
        self._file_lbl.setObjectName("dim_lbl")
        file_row.addWidget(btn_sel)
        file_row.addWidget(self._file_lbl)
        file_row.addStretch()
        layout.addLayout(file_row)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1e3a4f;")
        layout.addWidget(sep)

        # Modo de divisão
        mode_row = QHBoxLayout()
        lbl_mode = QLabel("Modo:")
        lbl_mode.setObjectName("section_lbl")
        mode_row.addWidget(lbl_mode)
        self._mode_grp = QButtonGroup(self)
        for val, label in [("single", "Intervalo único"),
                           ("multi",  "Múltiplos intervalos"),
                           ("all",    "Todas individualmente")]:
            rb = QRadioButton(label)
            rb.setProperty("mode_val", val)
            self._mode_grp.addButton(rb)
            mode_row.addWidget(rb)
            if val == "single":
                rb.setChecked(True)
        # Campos De/Até inline
        self._from_edit = QLineEdit("1")
        self._from_edit.setFixedWidth(50)
        self._to_edit = QLineEdit("1")
        self._to_edit.setFixedWidth(50)
        mode_row.addWidget(QLabel("De:"))
        mode_row.addWidget(self._from_edit)
        mode_row.addWidget(QLabel("Até:"))
        mode_row.addWidget(self._to_edit)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Intervalo texto livre (modo multi)
        self._multi_row = QHBoxLayout()
        self._multi_row_widget = QWidget()
        self._multi_row_widget.setLayout(self._multi_row)
        self._multi_row_widget.hide()
        lbl_iv = QLabel("Intervalos (ex: 1-3, 5-8, 10):")
        lbl_iv.setObjectName("dim_lbl")
        self._intervals_edit = QLineEdit()
        self._intervals_edit.setPlaceholderText("1-3, 5-8, 10")
        self._multi_row.addWidget(lbl_iv)
        self._multi_row.addWidget(self._intervals_edit)
        layout.addWidget(self._multi_row_widget)

        self._mode_grp.buttonClicked.connect(self._on_mode_change)

        # Preview
        preview_frame = QFrame()
        preview_frame.setObjectName("preview_frame")
        preview_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pv_layout = QVBoxLayout(preview_frame)
        self._preview_lbl = QLabel("Pré-visualização")
        self._preview_lbl.setObjectName("dim_lbl")
        self._preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pv_layout.addWidget(self._preview_lbl, stretch=1)

        # Nav ◀ ▶
        nav_row = QHBoxLayout()
        btn_prev = flat_btn("◀")
        btn_prev.clicked.connect(self._prev_page)
        self._page_lbl = QLabel("")
        self._page_lbl.setObjectName("dim_lbl")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_next = flat_btn("▶")
        btn_next.clicked.connect(self._next_page)
        nav_row.addStretch()
        nav_row.addWidget(btn_prev)
        nav_row.addWidget(self._page_lbl)
        nav_row.addWidget(btn_next)
        nav_row.addStretch()
        pv_layout.addLayout(nav_row)
        layout.addWidget(preview_frame, stretch=1)

        # Destino
        from PyQt6.QtWidgets import QCheckBox
        self._same_dir = QCheckBox("Salvar na mesma pasta do arquivo original")
        self._same_dir.setChecked(True)
        layout.addWidget(self._same_dir)

        # Status + progress
        self._status = QLabel("Selecione um PDF para dividir.")
        self._status.setObjectName("status_lbl")
        layout.addWidget(self._status)
        self._pb = GradientProgressBar()
        layout.addWidget(self._pb)

        # Botão
        btn_row = QHBoxLayout()
        self._btn_split = accent_btn("  ⊟  Dividir PDF  ")
        self._btn_split.clicked.connect(self._start_split)
        btn_row.addWidget(self._btn_split)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_mode_change(self, btn):
        mode = btn.property("mode_val")
        self._multi_row_widget.setVisible(mode == "multi")

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar PDF", "", "PDF (*.pdf)")
        if not path:
            return
        self._file = path
        self._file_lbl.setText(os.path.basename(path))
        import PyPDF2
        with open(path, "rb") as fh:
            self._total_pages = len(PyPDF2.PdfReader(fh).pages)
        self._to_edit.setText(str(self._total_pages))
        self._preview_page = 1
        self._load_preview()

    def _load_preview(self):
        if not self._file:
            return
        try:
            from pdf2image import convert_from_path
            from pdf_ocr_qt.main import find_poppler
            imgs = convert_from_path(self._file, dpi=72,
                                     poppler_path=find_poppler(),
                                     first_page=self._preview_page,
                                     last_page=self._preview_page)
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
                self._page_lbl.setText(
                    f"{self._preview_page} / {self._total_pages}")
        except Exception:
            self._preview_lbl.setText("Erro ao carregar preview")

    def _prev_page(self):
        if self._preview_page > 1:
            self._preview_page -= 1
            self._load_preview()

    def _next_page(self):
        if self._preview_page < self._total_pages:
            self._preview_page += 1
            self._load_preview()

    def _parse_intervals(self) -> list[tuple[int, int]]:
        mode = next(
            b.property("mode_val") for b in self._mode_grp.buttons()
            if b.isChecked())
        if mode == "all":
            return [(i, i) for i in range(self._total_pages)]
        if mode == "single":
            f = int(self._from_edit.text() or "1") - 1
            t = int(self._to_edit.text() or "1") - 1
            return [(max(0, f), min(t, self._total_pages - 1))]
        # multi
        intervals = []
        for part in self._intervals_edit.text().split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                intervals.append((int(a) - 1, int(b) - 1))
            elif part.isdigit():
                p = int(part) - 1
                intervals.append((p, p))
        return intervals

    def _start_split(self):
        if not self._file:
            self._status.setText("Selecione um PDF primeiro.")
            return
        intervals = self._parse_intervals()
        if not intervals:
            self._status.setText("Nenhum intervalo válido.")
            return
        out_dir = (os.path.dirname(self._file)
                   if self._same_dir.isChecked()
                   else QFileDialog.getExistingDirectory(
                       self, "Pasta de destino"))
        if not out_dir:
            return

        self._btn_split.setEnabled(False)
        self._pb.set(0)
        self._spinner.show_spinner("Dividindo PDF...")

        self._worker = SplitWorker(
            self._file, intervals, out_dir, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, status: str):
        self._spinner.set_status(status)
        self._spinner.set_page(current, total)
        self._pb.set(current / total * 100)
        self._status.setText(status)

    def _on_finished(self, generated: list):
        self._spinner.hide_spinner()
        self._btn_split.setEnabled(True)
        self._pb.set(100)
        self._status.setText(
            f"{len(generated)} arquivo(s) gerado(s) em: "
            f"{os.path.dirname(generated[0]) if generated else ''}")
        QMessageBox.information(self, "Concluído",
            f"{len(generated)} parte(s) gerada(s)!\n"
            + "\n".join(os.path.basename(p) for p in generated))

    def _on_error(self, msg: str):
        self._spinner.hide_spinner()
        self._btn_split.setEnabled(True)
        self._status.setText(f"Erro: {msg}")
        QMessageBox.critical(self, "Erro ao dividir", msg)
