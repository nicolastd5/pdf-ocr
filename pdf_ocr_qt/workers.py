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
    entities = pyqtSignal(list)   # list[Entity], emitido após finished

    def __init__(self, files, outdir, lang, highlight_names,
                 poppler_path, use_ner=False, use_openai=False,
                 openai_key="", ner_engine="spacy", parent=None):
        super().__init__(parent)
        self.files           = files
        self.outdir          = outdir
        self.lang            = lang
        self.highlight_names = highlight_names
        self.poppler_path    = poppler_path
        self.use_ner         = use_ner
        self.use_openai      = use_openai
        self.openai_key      = openai_key
        self.ner_engine      = ner_engine

    def run(self):
        from pdf_ocr_qt.ner import NERPipeline
        pipeline = None
        if self.use_ner:
            pipeline = NERPipeline(
                use_openai=self.use_openai,
                openai_key=self.openai_key,
                engine=self.ner_engine,
            )

        total = len(self.files)
        ok_files, errors = [], []
        all_entities = []

        for fi, input_pdf in enumerate(self.files, 1):
            base     = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = self.outdir if self.outdir else os.path.dirname(input_pdf)
            output_pdf = os.path.join(dest_dir, base + "_pesquisavel.pdf")
            try:
                page_entities = self._process_single(
                    input_pdf, output_pdf, fi, total, pipeline)
                ok_files.append(output_pdf)
                all_entities.extend(page_entities)
            except Exception as e:
                errors.append(f"{os.path.basename(input_pdf)}: {e}")

        self.finished.emit(ok_files, errors)
        if self.use_ner:
            self.entities.emit(all_entities)

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

    def _process_single(self, input_pdf, output_pdf, fi, total_files, pipeline=None):
        tess_config = "--oem 3 --psm 3"
        basename = os.path.basename(input_pdf)
        page_entities = []

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

                # ── Destaque de entidades ─────────────────────────
                if pipeline is not None:
                    from pdf_ocr_qt.ner import ENTITY_TYPES
                    ner_result = pipeline.extract(ocr_data, pi)
                    _COLORS = {
                        "PER":  (1.0, 0.85, 0.0, 0.35),
                        "ORG":  (0.2, 0.6,  1.0, 0.30),
                        "LOC":  (0.2, 0.85, 0.4, 0.30),
                        "MISC": (0.6, 0.6,  0.6, 0.25),
                    }
                    boxes_by_type: dict[str, list] = {k: [] for k in ENTITY_TYPES}
                    for ent in ner_result.entities:
                        bx, by, bw, bh = ent.bbox
                        if bw > 0 and bh > 0:
                            boxes_by_type[ent.type].append((bx, by, bw, bh))
                    c.saveState()
                    for etype, boxes in boxes_by_type.items():
                        r, g, b, a = _COLORS.get(etype, (1.0, 0.85, 0.0, 0.35))
                        c.setFillColorRGB(r, g, b, alpha=a)
                        for nx, ny, nw, nh in boxes:
                            pad = 2
                            c.rect(nx - pad, img_h - ny - nh - pad,
                                   nw + pad * 2, nh + pad * 2,
                                   fill=1, stroke=0)
                    c.restoreState()
                    page_entities.extend(ner_result.entities)
                elif self.highlight_names:
                    # Fallback: regex original
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
        return page_entities


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
