# PyQt6 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar o PDF Tools de Tkinter para PyQt6, mantendo toda a lógica de OCR/PDF intacta e melhorando o visual com o tema Ocean/Teal.

**Architecture:** Estrutura multi-arquivo em `pdf_ocr_qt/`. Lógica de processamento extraída para `workers.py` como subclasses de `QThread` com signals. UI reescrita em PyQt6 com QStackedWidget + sidebar de navegação.

**Tech Stack:** PyQt6, pytesseract, pdf2image, PyPDF2, reportlab, pdf2docx, Pillow, PyInstaller

---

## Estrutura de Arquivos

```
pdf_ocr_qt/
  __init__.py
  main.py            ← QApplication, SplashScreen, MainWindow, UpdateDialog
  styles.py          ← paleta C{} + QSS global + flat_btn() / accent_btn()
  workers.py         ← OcrWorker, CompressWorker, WordWorker, SplitWorker, MergeWorker
  pages/
    __init__.py
    ocr.py
    compress.py
    word.py
    split.py
    merge.py
    about.py
  widgets/
    __init__.py
    spinner.py       ← SpinnerDialog
    progress.py      ← GradientProgressBar
```

---

## Task 1: Estrutura base + styles.py

**Files:**
- Create: `pdf_ocr_qt/__init__.py`
- Create: `pdf_ocr_qt/pages/__init__.py`
- Create: `pdf_ocr_qt/widgets/__init__.py`
- Create: `pdf_ocr_qt/styles.py`

- [ ] **Step 1: Criar diretórios e `__init__.py` vazios**

```bash
cd "c:\Users\nicol\Downloads\pdf_ocr"
mkdir pdf_ocr_qt
mkdir pdf_ocr_qt\pages
mkdir pdf_ocr_qt\widgets
type nul > pdf_ocr_qt\__init__.py
type nul > pdf_ocr_qt\pages\__init__.py
type nul > pdf_ocr_qt\widgets\__init__.py
```

- [ ] **Step 2: Criar `pdf_ocr_qt/styles.py`**

```python
from PyQt6.QtWidgets import QPushButton

C = {
    "bg":        "#1e1e1e",
    "panel":     "#1a2332",
    "sidebar":   "#141c27",
    "input":     "#1e293b",
    "hover":     "#0f2a3d",
    "border":    "#1e3a4f",
    "accent":    "#2dd4bf",
    "accent2":   "#38bdf8",
    "accent_dk": "#0d9488",
    "fg":        "#e2e8f0",
    "fg_dim":    "#64748b",
    "fg_bright": "#f8fafc",
    "success":   "#34d399",
    "warn":      "#fbbf24",
    "error":     "#f87171",
    "sel":       "#164e63",
}

QSS = f"""
QWidget {{
    background-color: {C["bg"]};
    color: {C["fg"]};
    font-family: 'Segoe UI';
    font-size: 13px;
}}
QFrame#sidebar {{
    background-color: {C["sidebar"]};
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
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 5px 12px;
}}
QPushButton#flat_btn:hover {{
    background-color: {C["hover"]};
}}
QPushButton#flat_btn:disabled {{
    color: {C["fg_dim"]};
    opacity: 0.5;
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
    background-color: {C["accent_dk"]};
}}
QPushButton#accent_btn:disabled {{
    background-color: {C["border"]};
    color: {C["fg_dim"]};
}}
QListWidget {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    color: {C["fg"]};
}}
QListWidget::item:selected {{
    background-color: {C["sel"]};
    color: {C["fg_bright"]};
}}
QListWidget::item:hover {{
    background-color: {C["hover"]};
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
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {C["border"]};
    border-radius: 3px;
    background: {C["input"]};
}}
QCheckBox::indicator:checked {{
    background: {C["accent"]};
    border-color: {C["accent"]};
}}
QRadioButton {{
    color: {C["fg"]};
    spacing: 6px;
}}
QComboBox {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {C["input"]};
    color: {C["fg"]};
    selection-background-color: {C["sel"]};
}}
QTextEdit {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
QLineEdit {{
    background-color: {C["input"]};
    color: {C["fg"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}
QScrollBar:vertical {{
    background: {C["panel"]};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C["border"]};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QLabel#title_lbl {{
    color: {C["accent"]};
    font-size: 18px;
    font-weight: bold;
}}
QLabel#version_lbl {{
    color: {C["fg_dim"]};
    font-size: 11px;
}}
QLabel#section_lbl {{
    color: {C["fg"]};
    font-weight: bold;
}}
QLabel#dim_lbl {{
    color: {C["fg_dim"]};
    font-size: 12px;
}}
QLabel#status_lbl {{
    color: {C["fg_dim"]};
    font-size: 12px;
}}
QFrame#drop_area {{
    background-color: {C["input"]};
    border: 1px dashed {C["border"]};
    border-radius: 4px;
}}
QFrame#preview_frame {{
    background-color: {C["input"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
}}
QFrame#card {{
    background-color: {C["panel"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
}}
"""


def flat_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("flat_btn")
    from PyQt6.QtCore import Qt
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def accent_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("accent_btn")
    from PyQt6.QtCore import Qt
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def nav_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("nav_btn")
    from PyQt6.QtCore import Qt
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setCheckable(False)
    return b
```

- [ ] **Step 3: Verificar syntax**

```bash
cd "c:\Users\nicol\Downloads\pdf_ocr"
python -c "from pdf_ocr_qt.styles import C, QSS, flat_btn; print('OK')"
```
Esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add pdf_ocr_qt/
git commit -m "feat: create pdf_ocr_qt package with styles"
```

---

## Task 2: widgets/progress.py + widgets/spinner.py

**Files:**
- Create: `pdf_ocr_qt/widgets/progress.py`
- Create: `pdf_ocr_qt/widgets/spinner.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/widgets/progress.py`**

```python
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
```

- [ ] **Step 2: Criar `pdf_ocr_qt/widgets/spinner.py`**

```python
import math
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from pdf_ocr_qt.styles import C


class _OrbitCanvas(QWidget):
    """Canvas que desenha dois círculos orbitais animados."""

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


class SpinnerDialog(QDialog):
    """Modal animado de progresso — equivalente ao SpinnerWindow do Tkinter."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Fundo escuro arredondado
        inner = QWidget(self)
        inner.setStyleSheet(f"""
            background-color: {C["panel"]};
            border-radius: 12px;
            border: 1px solid {C["border"]};
        """)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(32, 28, 32, 28)
        inner_layout.setSpacing(12)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._orbit = _OrbitCanvas()
        inner_layout.addWidget(self._orbit, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status_lbl = QLabel("Processando...")
        self._status_lbl.setStyleSheet(f"color: {C['fg']}; font-size: 14px; background: transparent;")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self._status_lbl)

        self._page_lbl = QLabel("")
        self._page_lbl.setStyleSheet(f"color: {C['fg_dim']}; font-size: 12px; background: transparent;")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self._page_lbl)

        layout.addWidget(inner)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._orbit.step)

    def show_spinner(self, status: str = "Processando..."):
        self._status_lbl.setText(status)
        self._page_lbl.setText("")
        self._timer.start(40)  # ~25 fps
        if self.parent():
            p = self.parent()
            self.move(
                p.mapToGlobal(p.rect().center()) -
                self.rect().center()
            )
        self.show()

    def hide_spinner(self):
        self._timer.stop()
        self.hide()

    def set_status(self, msg: str):
        self._status_lbl.setText(msg)

    def set_page(self, current: int, total: int):
        self._page_lbl.setText(f"{current} / {total}")
```

- [ ] **Step 3: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.widgets.progress import GradientProgressBar; from pdf_ocr_qt.widgets.spinner import SpinnerDialog; print('OK')"
```
Esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add pdf_ocr_qt/widgets/
git commit -m "feat: add GradientProgressBar and SpinnerDialog widgets"
```

---

## Task 3: workers.py

**Files:**
- Create: `pdf_ocr_qt/workers.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/workers.py`**

O código dos métodos `_run_*` é copiado do `pdf_ocr.py` original. As únicas mudanças são:
- `self.after(0, lambda: ...)` → `self.progress.emit(...)`
- Remoção de referências a widgets Tkinter (`self.btn_*`, `self.*_status`, etc.)
- `self._spinner_status(msg)` → `self.progress.emit(current, total, msg)`

```python
import os
import io

from PyQt6.QtCore import QThread, pyqtSignal


# ── Lazy-loaded heavy deps (mesmos do pdf_ocr.py) ──────────────
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from pdf2image import convert_from_path
import reportlab.pdfgen.canvas as rl_canvas
from reportlab.lib.utils import ImageReader
import PyPDF2
from pdf2docx import Converter


class OcrWorker(QThread):
    progress = pyqtSignal(int, int, str)   # current_page, total_pages, status
    finished = pyqtSignal(list, list)       # ok_files, errors
    error    = pyqtSignal(str)

    def __init__(self, files, outdir, lang, highlight_names,
                 poppler_path, parent=None):
        super().__init__(parent)
        self.files           = files
        self.outdir          = outdir
        self.lang            = lang
        self.highlight_names = highlight_names
        self.poppler_path    = poppler_path

    def run(self):
        total = len(self.files)
        ok_files, errors = [], []
        for fi, input_pdf in enumerate(self.files, 1):
            base     = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = self.outdir if self.outdir else os.path.dirname(input_pdf)
            output_pdf = os.path.join(dest_dir, base + "_pesquisavel.pdf")
            try:
                self._process_single(input_pdf, output_pdf, fi, total)
                ok_files.append(output_pdf)
            except Exception as e:
                errors.append(f"{os.path.basename(input_pdf)}: {e}")
        self.finished.emit(ok_files, errors)

    def _preprocess_for_ocr(self, img):
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0)
        return img

    def _detect_names(self, ocr_data):
        """Detecta caixas delimitadoras de possíveis nomes próprios."""
        import re
        boxes = []
        texts  = ocr_data["text"]
        confs  = ocr_data["conf"]
        lefts  = ocr_data["left"]
        tops   = ocr_data["top"]
        widths = ocr_data["width"]
        heights= ocr_data["height"]
        i = 0
        while i < len(texts):
            word = texts[i]
            if not word or not word.strip():
                i += 1
                continue
            try:
                conf = int(confs[i])
            except (TypeError, ValueError):
                i += 1
                continue
            if conf < 40:
                i += 1
                continue
            if re.match(r'^[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç]{2,}$', word):
                x, y, w, h = lefts[i], tops[i], widths[i], heights[i]
                # Verifica se próxima palavra também é nome próprio
                j = i + 1
                while j < len(texts) and (not texts[j] or not texts[j].strip()):
                    j += 1
                if (j < len(texts) and
                        re.match(r'^[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç]{2,}$',
                                 texts[j]) and
                        abs(tops[j] - tops[i]) < heights[i]):
                    w = lefts[j] + widths[j] - x
                    i = j
                boxes.append((x, y, w, h))
            i += 1
        return boxes

    def _process_single(self, input_pdf, output_pdf, fi, total_files):
        tess_config = "--oem 3 --psm 3"
        basename = os.path.basename(input_pdf)

        with open(input_pdf, "rb") as fh:
            total_pages = len(PyPDF2.PdfReader(fh).pages)

        merger = PyPDF2.PdfWriter()
        try:
            for pi in range(1, total_pages + 1):
                self.progress.emit(pi, total_pages,
                    f"[{fi}/{total_files}] OCR — {basename} — página {pi}/{total_pages}")

                page_imgs = convert_from_path(
                    input_pdf, dpi=300,
                    poppler_path=self.poppler_path,
                    first_page=pi, last_page=pi)
                pil_img = page_imgs[0]
                img_w, img_h = pil_img.size

                ocr_img  = self._preprocess_for_ocr(pil_img)
                ocr_data = pytesseract.image_to_data(
                    ocr_img, lang=self.lang,
                    config=tess_config,
                    output_type=pytesseract.Output.DICT)
                del ocr_img

                buf = io.BytesIO()
                c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
                c.drawImage(ImageReader(pil_img), 0, 0,
                            width=img_w, height=img_h)
                del pil_img, page_imgs

                if self.highlight_names:
                    name_boxes = self._detect_names(ocr_data)
                    if name_boxes:
                        c.saveState()
                        c.setFillColorRGB(1.0, 0.85, 0.0, alpha=0.35)
                        for nx, ny, nw, nh in name_boxes:
                            pad = 2
                            c.rect(nx - pad, img_h - ny - nh - pad,
                                   nw + pad * 2, nh + pad * 2,
                                   fill=1, stroke=0)
                        c.restoreState()

                c.setFillColorRGB(0, 0, 0, alpha=0)
                texts   = ocr_data["text"]
                confs   = ocr_data["conf"]
                lefts   = ocr_data["left"]
                tops    = ocr_data["top"]
                widths  = ocr_data["width"]
                heights = ocr_data["height"]
                for j in range(len(texts)):
                    word = texts[j]
                    if not word or not word.strip():
                        continue
                    try:
                        conf = int(confs[j])
                    except (TypeError, ValueError):
                        continue
                    if conf < 30:
                        continue
                    x, y = lefts[j], tops[j]
                    w, h = widths[j], heights[j]
                    if h <= 0 or w <= 0:
                        continue
                    font_size = max(h * 0.85, 1)
                    try:
                        c.setFont("Helvetica", font_size)
                        tw = c.stringWidth(word, "Helvetica", font_size)
                        sx = w / tw if tw > 0 else 1
                        c.saveState()
                        c.transform(sx, 0, 0, 1, x, img_h - y - h)
                        c.drawString(0, 0, word)
                        c.restoreState()
                    except Exception:
                        pass

                c.save()
                page_data = buf.getvalue()
                buf.close()
                merger.add_page(
                    PyPDF2.PdfReader(io.BytesIO(page_data)).pages[0])

            with open(output_pdf, "wb") as f:
                merger.write(f)
        finally:
            merger.close()


class CompressWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list, list)   # results, errors
    error    = pyqtSignal(str)

    def __init__(self, files, outdir, dpi, jpeg_q, img_fmt,
                 poppler_path, parent=None):
        super().__init__(parent)
        self.files        = files
        self.outdir       = outdir
        self.dpi          = dpi
        self.jpeg_q       = jpeg_q
        self.img_fmt      = img_fmt
        self.poppler_path = poppler_path

    def run(self):
        total = len(self.files)
        results, errors = [], []
        tmp_suffix = ".jpg" if self.img_fmt == "JPEG" else ".png"

        for fi, input_pdf in enumerate(self.files, 1):
            base     = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = self.outdir if self.outdir else os.path.dirname(input_pdf)
            output_pdf = os.path.join(dest_dir, base + "_comprimido.pdf")
            try:
                orig_kb, new_kb = self._compress_single(
                    input_pdf, output_pdf, fi, total)
                ratio = (1 - new_kb / orig_kb) * 100 if orig_kb > 0 else 0
                results.append((os.path.basename(input_pdf),
                                 orig_kb, new_kb, ratio))
            except Exception as e:
                errors.append(f"{os.path.basename(input_pdf)}: {e}")

        self.finished.emit(results, errors)

    def _compress_single(self, input_pdf, output_pdf, fi, total_files):
        with open(input_pdf, "rb") as fh:
            total_pages = len(PyPDF2.PdfReader(fh).pages)

        merger = PyPDF2.PdfWriter()
        try:
            for pi in range(1, total_pages + 1):
                self.progress.emit(pi, total_pages,
                    f"[{fi}/{total_files}] {os.path.basename(input_pdf)} — página {pi}/{total_pages}")

                page_imgs = convert_from_path(
                    input_pdf, dpi=self.dpi,
                    poppler_path=self.poppler_path,
                    first_page=pi, last_page=pi)
                pil_img = page_imgs[0]
                img_w, img_h = pil_img.size

                img_buf = io.BytesIO()
                img_rgb = pil_img.convert("RGB")
                if self.img_fmt == "JPEG":
                    img_rgb.save(img_buf, format="JPEG",
                                 quality=self.jpeg_q,
                                 optimize=True, progressive=True)
                else:
                    img_rgb.save(img_buf, format="PNG",
                                 compress_level=9, optimize=True)
                img_buf.seek(0)
                del pil_img, page_imgs, img_rgb

                buf = io.BytesIO()
                c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
                c.drawImage(ImageReader(img_buf), 0, 0,
                            width=img_w, height=img_h)
                c.save()
                img_buf.close()

                page_data = buf.getvalue()
                buf.close()
                merger.add_page(
                    PyPDF2.PdfReader(io.BytesIO(page_data)).pages[0])

            with open(output_pdf, "wb") as f:
                merger.write(f)
        finally:
            merger.close()

        return (os.path.getsize(input_pdf) // 1024,
                os.path.getsize(output_pdf) // 1024)


class WordWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list, list)   # ok_files, errors
    error    = pyqtSignal(str)

    def __init__(self, files, outdir, parent=None):
        super().__init__(parent)
        self.files  = files
        self.outdir = outdir

    def run(self):
        total = len(self.files)
        ok_files, errors = [], []

        for fi, input_pdf in enumerate(self.files, 1):
            base     = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = self.outdir if self.outdir else os.path.dirname(input_pdf)
            output_docx = os.path.join(dest_dir, base + ".docx")
            basename = os.path.basename(input_pdf)
            try:
                self.progress.emit(fi, total,
                    f"[{fi}/{total}] Convertendo {basename}...")
                cv = Converter(input_pdf)
                try:
                    cv.convert(output_docx)
                finally:
                    cv.close()
                ok_files.append(output_docx)
            except Exception as e:
                errors.append(f"{basename}: {e}")

        self.finished.emit(ok_files, errors)


class SplitWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)   # generated files
    error    = pyqtSignal(str)

    def __init__(self, input_pdf, intervals, out_dir, parent=None):
        super().__init__(parent)
        self.input_pdf = input_pdf
        self.intervals = intervals
        self.out_dir   = out_dir

    def run(self):
        try:
            base  = os.path.splitext(os.path.basename(self.input_pdf))[0]
            dest  = self.out_dir if self.out_dir else os.path.dirname(self.input_pdf)
            total = len(self.intervals)
            generated = []

            with open(self.input_pdf, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for i, (f, t) in enumerate(self.intervals):
                    writer = PyPDF2.PdfWriter()
                    for p in range(f, t + 1):
                        writer.add_page(reader.pages[p])
                    out_name = (f"{base}_p{f+1}.pdf" if f == t
                                else f"{base}_p{f+1}-{t+1}.pdf")
                    out_path = os.path.join(dest, out_name)
                    with open(out_path, "wb") as out_fh:
                        writer.write(out_fh)
                    generated.append(out_path)
                    self.progress.emit(i + 1, total,
                        f"Dividindo parte {i+1} de {total}")

            self.finished.emit(generated)
        except Exception as e:
            self.error.emit(str(e))


class MergeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(str)   # output path
    error    = pyqtSignal(str)

    def __init__(self, files, out_path, parent=None):
        super().__init__(parent)
        self.files    = files
        self.out_path = out_path

    def run(self):
        try:
            merger = PyPDF2.PdfMerger()
            total  = len(self.files)
            try:
                for i, f in enumerate(self.files):
                    merger.append(f)
                    self.progress.emit(i + 1, total,
                        os.path.basename(f))
                with open(self.out_path, "wb") as fh:
                    merger.write(fh)
            finally:
                merger.close()
            self.finished.emit(self.out_path)
        except Exception as e:
            self.error.emit(str(e))
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.workers import OcrWorker, CompressWorker, WordWorker, SplitWorker, MergeWorker; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/workers.py
git commit -m "feat: add QThread workers for all PDF operations"
```

---

## Task 4: pages/merge.py

**Files:**
- Create: `pdf_ocr_qt/pages/merge.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/merge.py`**

```python
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
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.merge import MergePage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/merge.py
git commit -m "feat: implement MergePage with PyQt6"
```

---

## Task 5: pages/split.py

**Files:**
- Create: `pdf_ocr_qt/pages/split.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/split.py`**

```python
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
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.split import SplitPage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/split.py
git commit -m "feat: implement SplitPage with PyQt6"
```

---

## Task 6: pages/compress.py

**Files:**
- Create: `pdf_ocr_qt/pages/compress.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/compress.py`**

```python
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from pdf_ocr_qt.styles import flat_btn, accent_btn
from pdf_ocr_qt.workers import CompressWorker
from pdf_ocr_qt.widgets.spinner import SpinnerDialog
from pdf_ocr_qt.widgets.progress import GradientProgressBar


QUALITY_PRESETS = [
    ("Alta qualidade",   150, 88, "JPEG"),
    ("Balanceado",       150, 65, "JPEG"),
    ("Máxima compressão",100, 40, "JPEG"),
    ("PNG sem perda",    150, 95, "PNG"),
]

IMG_FORMATS = [
    ("JPEG — menor tamanho (com perda)",  "JPEG", ".jpg"),
    ("PNG  — sem perda de qualidade",     "PNG",  ".png"),
]


class CompressPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[str] = []
        self._worker: CompressWorker | None = None
        self._spinner = SpinnerDialog(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        lbl = QLabel("Arquivos para comprimir")
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

        # Qualidade
        q_row = QHBoxLayout()
        q_row.addWidget(QLabel("Qualidade:"))
        self._quality_combo = QComboBox()
        for label, *_ in QUALITY_PRESETS:
            self._quality_combo.addItem(label)
        self._quality_combo.setCurrentIndex(1)
        q_row.addWidget(self._quality_combo)
        q_row.addStretch()
        layout.addLayout(q_row)

        # Destino
        self._same_dir = QCheckBox("Salvar na mesma pasta do arquivo original")
        self._same_dir.setChecked(True)
        layout.addWidget(self._same_dir)

        layout.addStretch()

        # Status + progress
        self._status = QLabel("Adicione PDFs para comprimir.")
        self._status.setObjectName("status_lbl")
        layout.addWidget(self._status)
        self._pb = GradientProgressBar()
        layout.addWidget(self._pb)

        # Botão
        btn_row = QHBoxLayout()
        self._btn = accent_btn("  🗜  Comprimir PDFs  ")
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
        idx = self._quality_combo.currentIndex()
        _, dpi, jpeg_q, img_fmt = QUALITY_PRESETS[idx]
        out_dir = (None if self._same_dir.isChecked()
                   else QFileDialog.getExistingDirectory(
                       self, "Pasta de destino"))
        if not self._same_dir.isChecked() and not out_dir:
            return

        from pdf_ocr_qt.main import find_poppler
        self._btn.setEnabled(False)
        self._pb.set(0)
        self._spinner.show_spinner("Comprimindo PDFs...")

        self._worker = CompressWorker(
            list(self._files), out_dir or "",
            dpi, jpeg_q, img_fmt, find_poppler(), self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, status: str):
        self._spinner.set_status(status)
        self._spinner.set_page(current, total)
        self._pb.set(current / total * 100)
        self._status.setText(status)

    def _on_finished(self, results: list, errors: list):
        self._spinner.hide_spinner()
        self._btn.setEnabled(True)
        self._pb.set(100)
        if errors:
            self._status.setText(f"Concluído com {len(errors)} erro(s).")
            QMessageBox.warning(self, "Erros",
                "\n".join(errors))
        else:
            total_orig = sum(r[1] for r in results)
            total_new  = sum(r[2] for r in results)
            ratio = (1 - total_new / total_orig) * 100 if total_orig else 0
            self._status.setText(
                f"Concluído! {total_orig} KB → {total_new} KB  (-{ratio:.0f}%)")
            lines = "\n".join(
                f"  {r[0]}  {r[1]}→{r[2]} KB  (-{r[3]:.0f}%)"
                for r in results)
            QMessageBox.information(self, "Compressão concluída",
                f"{len(results)} arquivo(s) comprimido(s)!\n\n{lines}\n\n"
                f"Total: {total_orig} KB → {total_new} KB  (-{ratio:.0f}%)")

    def _on_error(self, msg: str):
        self._spinner.hide_spinner()
        self._btn.setEnabled(True)
        self._status.setText(f"Erro: {msg}")
        QMessageBox.critical(self, "Erro", msg)
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.compress import CompressPage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/compress.py
git commit -m "feat: implement CompressPage with PyQt6"
```

---

## Task 7: pages/word.py

**Files:**
- Create: `pdf_ocr_qt/pages/word.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/word.py`**

```python
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
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.word import WordPage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/word.py
git commit -m "feat: implement WordPage with PyQt6"
```

---

## Task 8: pages/ocr.py

**Files:**
- Create: `pdf_ocr_qt/pages/ocr.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/ocr.py`**

```python
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame
)
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
            lang, highlight, find_poppler(), self)
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
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.ocr import OcrPage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/ocr.py
git commit -m "feat: implement OcrPage with PyQt6"
```

---

## Task 9: pages/about.py

**Files:**
- Create: `pdf_ocr_qt/pages/about.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/pages/about.py`**

```python
import threading
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from pdf_ocr_qt.styles import flat_btn, accent_btn, C

APP_VERSION      = "1.0.6"
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
            "• Migração para PyQt6 — visual moderno Ocean/Teal\n"
            "• Drag & drop nativo (sem tkinterdnd2)\n"
            "• Workers assíncronos com QThread + signals\n"
            "• SpinnerDialog animado em todas as operações\n"
            "• Estrutura multi-arquivo (pages/, widgets/, workers)"
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
            from PyQt6.QtCore import QMetaObject, Qt
            if tag and tag != APP_VERSION:
                QMetaObject.invokeMethod(self, "_show_update",
                    Qt.ConnectionType.QueuedConnection)
            else:
                from PyQt6.QtCore import QMetaObject
                QMetaObject.invokeMethod(self, "_show_latest",
                    Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(self, "_show_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e)))

    def _show_update(self):
        self._update_lbl.setText("Nova versão disponível!")
        webbrowser.open(GITHUB_RELEASES_PAGE)

    def _show_latest(self):
        self._update_lbl.setText(f"Você está na versão mais recente (v{APP_VERSION})")

    def _show_error(self, msg: str):
        self._update_lbl.setText(f"Erro ao verificar: {msg}")
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.pages.about import AboutPage; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/pages/about.py
git commit -m "feat: implement AboutPage with PyQt6"
```

---

## Task 10: main.py — MainWindow + SplashScreen + entry point

**Files:**
- Create: `pdf_ocr_qt/main.py`

- [ ] **Step 1: Criar `pdf_ocr_qt/main.py`**

```python
import os
import sys
import json
import ssl
import shutil
import threading
import urllib.request
import urllib.error
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QFrame, QStackedWidget,
    QSplashScreen, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

from pdf_ocr_qt.styles import QSS, C, nav_btn

APP_VERSION          = "1.0.6"
GITHUB_USER          = "nicolastd5"
GITHUB_REPO          = "pdf-ocr"
GITHUB_RELEASES_API  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"


# ── Helpers (copiados do pdf_ocr.py) ─────────────────────────────

def _bundled_bin(name: str) -> str | None:
    if getattr(sys, "frozen", False):
        p = os.path.join(sys._MEIPASS, name)
        return p if os.path.isfile(p) else None
    return None


def check_tesseract() -> bool:
    try:
        import pytesseract
    except ImportError:
        return False
    bundled = _bundled_bin("tesseract.exe")
    if bundled:
        pytesseract.pytesseract.tesseract_cmd = bundled
        tessdata = os.path.join(os.path.dirname(bundled), "tessdata")
        os.environ["TESSDATA_PREFIX"] = (
            tessdata if os.path.isdir(tessdata)
            else os.path.dirname(bundled))
        return True
    for path in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
            os.environ.get("USERNAME", "")),
    ]:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def find_poppler() -> str | None:
    if getattr(sys, "frozen", False):
        bundled_dir = os.path.join(sys._MEIPASS, "poppler", "bin")
        if os.path.isdir(bundled_dir):
            return bundled_dir
    if shutil.which("pdftoppm"):
        return None
    for p in [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler-24\Library\bin",
        r"C:\poppler\bin",
        r"C:\poppler\Library\bin",
    ]:
        if os.path.isdir(p):
            return p
    return None


def _urlopen_ssl(req, timeout=15):
    ctx = ssl.create_default_context()
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def fetch_latest_release() -> dict:
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"pdf-tools/{APP_VERSION}"})
    with _urlopen_ssl(req, timeout=15) as resp:
        import json as _json
        data = _json.loads(resp.read().decode())
    tag      = data.get("tag_name", "").lstrip("v")
    body     = data.get("body", "Sem notas de versão.").strip()
    html_url = data.get("html_url", GITHUB_RELEASES_PAGE)
    return {"tag": tag, "body": body, "html_url": html_url}


def _prefs_path() -> str:
    base = (os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "pdf_ocr_prefs.json")


# ── MainWindow ────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"PDF Tools  v{APP_VERSION}")
        self.resize(1200, 850)
        self.setMinimumSize(1000, 700)

        self._active_nav: QPushButton | None = None
        self._prefs: dict = {}
        self._load_prefs()
        self._build_ui()
        self._navigate("ocr")

        # Verificar atualização em background
        if self._prefs.get("auto_update", True):
            threading.Thread(
                target=self._check_update_bg, daemon=True).start()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        logo = QLabel("PDF Tools")
        logo.setStyleSheet(
            f"color: {C['accent']}; font-size: 18px; font-weight: bold;"
            f" padding: 20px 16px 4px 16px; background: transparent;")
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet(
            f"color: {C['fg_dim']}; font-size: 11px;"
            f" padding: 0 16px 20px 16px; background: transparent;")
        side_layout.addWidget(logo)
        side_layout.addWidget(ver_lbl)

        self._nav_btns: dict[str, QPushButton] = {}
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
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            side_layout.addWidget(btn)
            self._nav_btns[key] = btn

        side_layout.addStretch()
        main_layout.addWidget(sidebar)

        # Stack
        self._stack = QStackedWidget()
        self._pages: dict[str, QWidget] = {}

        from pdf_ocr_qt.pages.ocr      import OcrPage
        from pdf_ocr_qt.pages.compress import CompressPage
        from pdf_ocr_qt.pages.word     import WordPage
        from pdf_ocr_qt.pages.split    import SplitPage
        from pdf_ocr_qt.pages.merge    import MergePage
        from pdf_ocr_qt.pages.about    import AboutPage

        for key, PageClass in [
            ("ocr",      OcrPage),
            ("compress", CompressPage),
            ("word",     WordPage),
            ("split",    SplitPage),
            ("merge",    MergePage),
            ("about",    AboutPage),
        ]:
            page = PageClass(self)
            self._pages[key] = page
            self._stack.addWidget(page)

        main_layout.addWidget(self._stack)

    def _navigate(self, key: str):
        if self._active_nav:
            self._active_nav.setProperty("active", False)
            self._active_nav.style().unpolish(self._active_nav)
            self._active_nav.style().polish(self._active_nav)

        self._active_nav = self._nav_btns[key]
        self._active_nav.setProperty("active", True)
        self._active_nav.style().unpolish(self._active_nav)
        self._active_nav.style().polish(self._active_nav)

        self._stack.setCurrentWidget(self._pages[key])

    # ── Preferências ─────────────────────────────────────────────
    def _load_prefs(self):
        try:
            with open(_prefs_path()) as f:
                self._prefs = json.load(f)
        except Exception:
            self._prefs = {}

    def _save_prefs(self):
        try:
            with open(_prefs_path(), "w") as f:
                json.dump(self._prefs, f)
        except Exception:
            pass

    def closeEvent(self, event):
        self._save_prefs()
        super().closeEvent(event)

    # ── Auto-update ──────────────────────────────────────────────
    def _check_update_bg(self):
        try:
            info = fetch_latest_release()
            tag = info.get("tag", "")
            if tag and tag != APP_VERSION:
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self, "_show_update_dialog",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, tag),
                    Q_ARG(str, info.get("html_url", GITHUB_RELEASES_PAGE)))
        except Exception:
            pass

    def _show_update_dialog(self, tag: str, url: str):
        dlg = QDialog(self)
        dlg.setWindowTitle("Atualização disponível")
        dlg.setStyleSheet(f"background: {C['panel']}; color: {C['fg']};")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(f"Nova versão disponível: v{tag}"))
        layout.addWidget(QLabel(f"Versão atual: v{APP_VERSION}"))
        btns = QDialogButtonBox()
        btn_dl = btns.addButton(
            "Baixar atualização", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_dl.clicked.connect(lambda: webbrowser.open(url))
        btn_cl = btns.addButton("Fechar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_cl.clicked.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()


# ── Entry point ───────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)

    # Splash simples
    splash_pix = QPixmap(400, 200)
    splash_pix.fill(QColor(C["panel"]))
    painter = QPainter(splash_pix)
    painter.setPen(QColor(C["accent"]))
    painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter,
                     "PDF Tools")
    painter.setPen(QColor(C["fg_dim"]))
    painter.setFont(QFont("Segoe UI", 11))
    painter.drawText(0, 150, 400, 30, Qt.AlignmentFlag.AlignCenter,
                     f"v{APP_VERSION} — carregando...")
    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents()

    win = MainWindow()
    QTimer.singleShot(1200, lambda: (splash.finish(win), win.show()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar syntax**

```bash
python -c "from pdf_ocr_qt.main import main, check_tesseract, find_poppler; print('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr_qt/main.py
git commit -m "feat: implement MainWindow, SplashScreen and entry point"
```

---

## Task 11: Teste de smoke + ajuste do requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Atualizar requirements.txt**

```text
PyQt6
pytesseract
Pillow
pdf2image
reportlab
PyPDF2
pdf2docx
```
(Remover `tkinterdnd2` se presente)

- [ ] **Step 2: Rodar o app**

```bash
cd "c:\Users\nicol\Downloads\pdf_ocr"
python -m pdf_ocr_qt.main
```
Esperado: splash screen aparece por ~1.2s, depois a janela principal abre com sidebar e aba OCR ativa.

- [ ] **Step 3: Testar navegação entre abas**

Clicar em cada botão da sidebar e verificar que a aba correta aparece sem erros no terminal.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: update requirements.txt for PyQt6 migration"
```

---

## Task 12: Atualizar pdf_ocr.spec para PyQt6

**Files:**
- Modify: `pdf_ocr.spec`

- [ ] **Step 1: Ler o spec atual**

```bash
cat pdf_ocr.spec
```

- [ ] **Step 2: Atualizar o spec**

Alterar a linha `Analysis` para apontar para `pdf_ocr_qt/main.py`:
- `scripts=['pdf_ocr_qt/main.py']` (ou `pdf_ocr_qt\\main.py` no Windows)
- Em `hiddenimports`, substituir `'tkinterdnd2'` por `'PyQt6'`
- Em `datas`, manter `deps/tesseract` e `deps/poppler/bin`
- `name='PDF_Tools'` permanece igual

- [ ] **Step 3: Build de teste**

```bash
pyinstaller pdf_ocr.spec
```
Esperado: `dist/PDF_Tools.exe` gerado sem erros.

- [ ] **Step 4: Commit**

```bash
git add pdf_ocr.spec
git commit -m "chore: update PyInstaller spec for PyQt6"
```

---

## Task 13: Push + GitHub Actions

- [ ] **Step 1: Push**

```bash
git push origin master
```

- [ ] **Step 2: Rodar Actions manualmente**

```bash
gh workflow run build.yml --field tag=v1.0.7
```

- [ ] **Step 3: Acompanhar o build**

```bash
gh run watch
```
Esperado: build passa, release v1.0.7 criado com `PDF_Tools.exe`.
