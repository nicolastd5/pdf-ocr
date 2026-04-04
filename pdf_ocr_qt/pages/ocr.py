import csv
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame,
    QLineEdit, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtGui import QColor, QIcon, QPixmap
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
        self._entities: list = []
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

        # ── Opções de IA ──────────────────────────────────────────
        self._chk_ner = QCheckBox("Usar IA para detectar nomes (spaCy)")
        self._chk_ner.toggled.connect(self._on_ner_toggled)
        layout.addWidget(self._chk_ner)

        ai_indent = QHBoxLayout()
        ai_indent.setContentsMargins(24, 0, 0, 0)
        ai_col = QVBoxLayout()

        self._chk_openai = QCheckBox("Usar OpenAI para NER avançado")
        self._chk_openai.setEnabled(False)
        self._chk_openai.toggled.connect(self._on_openai_toggled)
        ai_col.addWidget(self._chk_openai)

        key_row = QHBoxLayout()
        key_lbl = QLabel("Chave API OpenAI:")
        key_lbl.setObjectName("dim_lbl")
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setPlaceholderText("sk-…")
        self._key_edit.setEnabled(False)
        self._key_edit.setFixedWidth(260)
        key_row.addWidget(key_lbl)
        key_row.addWidget(self._key_edit)
        key_row.addStretch()
        ai_col.addLayout(key_row)

        ai_indent.addLayout(ai_col)
        layout.addLayout(ai_indent)

        layout.addStretch()

        # ── Painel de entidades (oculto até OCR com IA) ──────────
        self._ner_panel = QFrame()
        self._ner_panel.setObjectName("drop_area")
        self._ner_panel.setVisible(False)
        ner_layout = QVBoxLayout(self._ner_panel)
        ner_layout.setContentsMargins(8, 8, 8, 8)
        ner_layout.setSpacing(6)

        ner_hdr = QHBoxLayout()
        ner_title = QLabel("Entidades encontradas")
        ner_title.setObjectName("section_lbl")
        ner_hdr.addWidget(ner_title)
        ner_hdr.addStretch()
        self._btn_export = flat_btn("📄 Exportar CSV")
        self._btn_export.clicked.connect(self._export_csv)
        ner_hdr.addWidget(self._btn_export)
        ner_layout.addLayout(ner_hdr)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Nome", "Tipo", "Páginas"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setColumnWidth(1, 100)
        self._tree.setColumnWidth(2, 80)
        self._tree.setFixedHeight(160)
        ner_layout.addWidget(self._tree)

        layout.addWidget(self._ner_panel)

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

        use_ner    = self._chk_ner.isChecked()
        use_openai = self._chk_openai.isChecked()
        openai_key = self._key_edit.text().strip()

        self._worker = OcrWorker(
            list(self._files), out_dir or "",
            lang, highlight, find_poppler(),
            use_ner=use_ner,
            use_openai=use_openai,
            openai_key=openai_key,
            parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.entities.connect(self._on_entities)
        self._worker.start()

    # ── Controles de IA ──────────────────────────────────────────
    def _on_ner_toggled(self, checked: bool):
        if checked:
            from pdf_ocr_qt.ner import NERPipeline
            if not NERPipeline.is_spacy_installed():
                from pdf_ocr_qt.widgets.spacy_install import SpacyInstallDialog
                dlg = SpacyInstallDialog(self)
                dlg.exec()
                if not dlg.install_succeeded:
                    self._chk_ner.blockSignals(True)
                    self._chk_ner.setChecked(False)
                    self._chk_ner.blockSignals(False)
                    return
        self._chk_openai.setEnabled(checked)
        if not checked:
            self._chk_openai.setChecked(False)
            self._key_edit.setEnabled(False)

    def _on_openai_toggled(self, checked: bool):
        self._key_edit.setEnabled(checked)

    def _color_icon(self, etype: str) -> QIcon:
        _COLORS = {
            "PER":  "#f59e0b",
            "ORG":  "#38bdf8",
            "LOC":  "#34d399",
            "MISC": "#94a3b8",
        }
        color = _COLORS.get(etype, "#94a3b8")
        pix = QPixmap(12, 12)
        pix.fill(QColor(color))
        return QIcon(pix)

    def _populate_tree(self, entities: list):
        from pdf_ocr_qt.ner import ENTITY_TYPES
        self._tree.clear()
        seen: dict = {}
        for ent in entities:
            key = (ent.text.lower(), ent.type)
            if key not in seen:
                seen[key] = {"text": ent.text, "type": ent.type, "pages": set()}
            seen[key]["pages"].add(ent.page)

        for data in seen.values():
            pages_str = ", ".join(str(p) for p in sorted(data["pages"]))
            item = QTreeWidgetItem([
                data["text"],
                ENTITY_TYPES.get(data["type"], data["type"]),
                pages_str,
            ])
            item.setIcon(0, self._color_icon(data["type"]))
            self._tree.addTopLevelItem(item)

    def _export_csv(self):
        if not self._entities:
            return
        from pdf_ocr_qt.ner import ENTITY_TYPES

        default_dir = ""
        if self._files:
            base = os.path.splitext(os.path.basename(self._files[0]))[0]
            default_dir = os.path.join(
                os.path.dirname(self._files[0]),
                f"{base}_entidades.csv")

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar entidades", default_dir, "CSV (*.csv)")
        if not path:
            return

        seen: dict = {}
        for ent in self._entities:
            key = (ent.text.lower(), ent.type)
            if key not in seen:
                seen[key] = {
                    "text":  ent.text,
                    "type":  ENTITY_TYPES.get(ent.type, ent.type),
                    "pages": set(),
                    "file":  (os.path.basename(self._files[0])
                              if self._files else ""),
                }
            seen[key]["pages"].add(ent.page)

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Nome", "Tipo", "Páginas", "Arquivo"])
                for data in seen.values():
                    pages_str = ", ".join(str(p) for p in sorted(data["pages"]))
                    writer.writerow([
                        data["text"], data["type"],
                        pages_str, data["file"]])
            QMessageBox.information(self, "CSV exportado",
                f"Entidades salvas em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao exportar", str(e))

    def _on_entities(self, entities: list):
        self._entities = entities
        if entities:
            self._populate_tree(entities)
            self._ner_panel.setVisible(True)

    def load_prefs(self, prefs: dict):
        self._chk_ner.setChecked(prefs.get("use_ner", False))
        self._chk_openai.setChecked(prefs.get("use_openai", False))
        self._key_edit.setText(prefs.get("openai_key", ""))

    def save_prefs(self, prefs: dict):
        prefs["use_ner"]    = self._chk_ner.isChecked()
        prefs["use_openai"] = self._chk_openai.isChecked()
        prefs["openai_key"] = self._key_edit.text().strip()

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
