"""
PDF Tools
Ferramenta completa para PDF: OCR, compressão, divisão e união.
Repositório: https://github.com/nicolastd5/pdf-ocr
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    import tkinterdnd2 as TkinterDnD
    _HAS_DND = True
except ImportError:
    TkinterDnD = None
    _HAS_DND = False
import threading
import os
import sys
import json
import re
import ssl
import webbrowser
import urllib.request
import urllib.error
import shutil
import io

# ── Lazy-loaded heavy deps (loaded in background at startup) ──
pytesseract = None
Image = ImageFilter = ImageEnhance = ImageOps = ImageTk = None
convert_from_path = None
rl_canvas = None
ImageReader = None
PyPDF2 = None
DEPS_OK = None          # None = not yet loaded; True/False = result
MISSING_DEP = ""

APP_VERSION = "1.0.4"
GITHUB_USER = "nicolastd5"
GITHUB_REPO = "pdf-ocr"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"


# ─────────────────────────────────────────────────────────────
#  Paleta Ocean / Teal
# ─────────────────────────────────────────────────────────────
C = {
    "bg":        "#1e1e1e",
    "panel":     "#1a2332",
    "sidebar":   "#141c27",
    "sidebar_x": "#1a2536",      # sidebar expandida
    "input":     "#1e293b",
    "hover":     "#0f2a3d",
    "border":    "#1e3a4f",
    "accent":    "#2dd4bf",
    "accent2":   "#38bdf8",
    "accent_dk": "#0d9488",
    "grad_start":"#2dd4bf",
    "grad_end":  "#38bdf8",
    "fg":        "#e2e8f0",
    "fg_dim":    "#64748b",
    "fg_bright": "#f8fafc",
    "success":   "#34d399",
    "warn":      "#fbbf24",
    "error":     "#f87171",
    "sel":       "#164e63",
    "glass":     "#1a233280",    # for reference only (tkinter can't do alpha)
    "glow":      "#2dd4bf",
}


# ─────────────────────────────────────────────────────────────
#  Carregamento lazy de dependências pesadas
# ─────────────────────────────────────────────────────────────

def _load_heavy_deps():
    """Importa bibliotecas pesadas. Chamado em background thread."""
    global pytesseract, Image, ImageFilter, ImageEnhance, ImageOps, ImageTk
    global convert_from_path, rl_canvas, ImageReader, PyPDF2
    global DEPS_OK, MISSING_DEP
    try:
        import pytesseract as _pytesseract
        from PIL import (Image as _Image, ImageFilter as _ImageFilter,
                         ImageEnhance as _ImageEnhance, ImageOps as _ImageOps,
                         ImageTk as _ImageTk)
        from pdf2image import convert_from_path as _convert_from_path
        import reportlab.pdfgen.canvas as _rl_canvas
        from reportlab.lib.utils import ImageReader as _ImageReader
        import PyPDF2 as _PyPDF2

        pytesseract = _pytesseract
        Image = _Image
        ImageFilter = _ImageFilter
        ImageEnhance = _ImageEnhance
        ImageOps = _ImageOps
        ImageTk = _ImageTk
        convert_from_path = _convert_from_path
        rl_canvas = _rl_canvas
        ImageReader = _ImageReader
        PyPDF2 = _PyPDF2
        DEPS_OK = True
    except ImportError as e:
        DEPS_OK = False
        MISSING_DEP = str(e)


# ─────────────────────────────────────────────────────────────
#  Splash Screen
# ─────────────────────────────────────────────────────────────

class SplashScreen(tk.Tk):
    """Janela de splash exibida enquanto as dependências carregam."""

    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.configure(bg="#1e1e1e")
        self.attributes("-topmost", True)

        w, h = 360, 200
        sx = self.winfo_screenwidth()  // 2 - w // 2
        sy = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{sx}+{sy}")

        # Borda sutil
        border = tk.Frame(self, bg="#454545", padx=1, pady=1)
        border.pack(fill="both", expand=True)
        inner = tk.Frame(border, bg="#1e1e1e")
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="⬡",
                 font=("Segoe UI", 32), bg="#1e1e1e",
                 fg="#4fc3f7").pack(pady=(24, 4))
        tk.Label(inner, text="PDF Tools",
                 font=("Segoe UI", 16, "bold"), bg="#1e1e1e",
                 fg="#ffffff").pack()
        tk.Label(inner, text=f"v{APP_VERSION}",
                 font=("Segoe UI", 9), bg="#1e1e1e",
                 fg="#858585").pack(pady=(2, 0))

        self._dots = 0
        self._load_lbl = tk.Label(inner, text="Carregando",
                                  font=("Segoe UI", 9), bg="#1e1e1e",
                                  fg="#858585")
        self._load_lbl.pack(pady=(16, 0))

        # Barra de progresso simples
        self._bar = tk.Canvas(inner, height=3, bg="#3c3c3c",
                              highlightthickness=0)
        self._bar.pack(fill="x", padx=40, pady=(8, 0))
        self._bar_fill = self._bar.create_rectangle(0, 0, 0, 3, fill="#4fc3f7", outline="")

        self._ready = False
        self._animate()
        self._start_loading()

    def _animate(self):
        if self._ready:
            return
        self._dots = (self._dots + 1) % 4
        self._load_lbl.config(text="Carregando" + "." * self._dots)
        # Pulse the progress bar
        self.update_idletasks()
        bar_w = self._bar.winfo_width()
        if bar_w > 10:
            fill_w = int(bar_w * 0.4)
            cycle = (self._dots * bar_w // 3) % max(bar_w - fill_w, 1)
            self._bar.coords(self._bar_fill, cycle, 0, cycle + fill_w, 3)
        self.after(350, self._animate)

    def _start_loading(self):
        def _worker():
            _load_heavy_deps()
            self.after(0, self._on_loaded)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self):
        self._ready = True
        self.destroy()


# ─────────────────────────────────────────────────────────────
#  Helpers de dependências
# ─────────────────────────────────────────────────────────────

def _bundled_bin(name):
    if not getattr(sys, "frozen", False):
        return None
    path = os.path.join(sys._MEIPASS, name)
    return path if os.path.isfile(path) else None


def check_tesseract():
    bundled = _bundled_bin("tesseract.exe")
    if bundled:
        pytesseract.pytesseract.tesseract_cmd = bundled
        tessdata = os.path.join(os.path.dirname(bundled), "tessdata")
        if os.path.isdir(tessdata):
            os.environ["TESSDATA_PREFIX"] = tessdata
        else:
            os.environ["TESSDATA_PREFIX"] = os.path.dirname(bundled)
        return True
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
            os.environ.get("USERNAME", "")
        ),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def find_poppler():
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


# ─────────────────────────────────────────────────────────────
#  Update helpers
# ─────────────────────────────────────────────────────────────

def version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def _urlopen_ssl(req, timeout=15):
    """
    Tenta urlopen com verificação SSL; se falhar por certificado,
    refaz sem verificação (comum em Windows sem bundle de CAs atualizado).
    """
    try:
        ctx = ssl.create_default_context()
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except ssl.SSLError:
        ctx = ssl._create_unverified_context()
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError):
            ctx = ssl._create_unverified_context()
            return urllib.request.urlopen(req, timeout=timeout, context=ctx)
        raise


def fetch_latest_release():
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"pdf-tools/{APP_VERSION}"}
    )
    with _urlopen_ssl(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    tag  = data.get("tag_name", "").lstrip("v")
    body = data.get("body", "Sem notas de versão.").strip()
    html_url = data.get("html_url", GITHUB_RELEASES_PAGE)

    exe_url = None
    for asset in data.get("assets", []):
        if asset["name"].lower().endswith(".exe"):
            exe_url = asset["browser_download_url"]
            break

    return {"tag": tag, "body": body, "exe_url": exe_url, "html_url": html_url}


# ─────────────────────────────────────────────────────────────
#  Widget helpers
# ─────────────────────────────────────────────────────────────

def _style_entry(e):
    """Aplica estilo dark com glow teal no focus."""
    e.configure(
        bg=C["input"], fg=C["fg"],
        insertbackground=C["accent"],
        relief="flat",
        highlightthickness=2,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
        readonlybackground=C["input"],
        disabledbackground=C["input"],
        disabledforeground=C["fg_dim"],
    )


def _flat_btn(parent, text, command, fg=None, bg=None, font=None, **kw):
    fg   = fg   or C["fg"]
    bg   = bg   or C["input"]
    font = font or ("Segoe UI", 9)
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=C["sel"],
        activeforeground=C["fg_bright"],
        relief="flat", bd=0, cursor="hand2",
        font=font,
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
        **kw
    )
    _hover_bg = C["sel"] if bg == C["input"] else C["accent_dk"]
    btn.bind("<Enter>", lambda _: btn.config(bg=_hover_bg) if str(btn.cget("state")) != "disabled" else None)
    btn.bind("<Leave>", lambda _: btn.config(bg=bg) if str(btn.cget("state")) != "disabled" else None)
    return btn


def _accent_btn(parent, text, command, font=None, **kw):
    font = font or ("Segoe UI", 10, "bold")
    btn = tk.Button(
        parent, text=text, command=command,
        bg=C["accent"], fg="#0f172a",
        activebackground=C["accent2"], activeforeground="#0f172a",
        relief="flat", bd=0, cursor="hand2",
        font=font, **kw
    )
    btn.bind("<Enter>", lambda _: btn.config(bg=C["accent2"]) if str(btn.cget("state")) != "disabled" else None)
    btn.bind("<Leave>", lambda _: btn.config(bg=C["accent"]) if str(btn.cget("state")) != "disabled" else None)
    return btn


class CanvasProgressBar(tk.Canvas):
    """Barra de progresso com gradiente teal→blue animado."""

    _GRAD_STEPS = 20       # segmentos do gradiente
    _SHIMMER_SPEED = 2     # pixels por frame
    _SHIMMER_MS = 40       # intervalo de animação

    def __init__(self, parent, **kw):
        kw.setdefault("height", 8)
        kw.setdefault("bg", C["panel"])
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, **kw)
        self._value = 0
        self._shimmer_offset = 0
        self._animating = False
        self._after_id = None
        self.bind("<Configure>", self._redraw)

    def set(self, value):
        self._value = max(0.0, min(100.0, value))
        self._redraw()
        if 0 < self._value < 100 and not self._animating:
            self._animating = True
            self._animate_shimmer()
        elif self._value >= 100 or self._value <= 0:
            self._animating = False
            if self._after_id:
                self.after_cancel(self._after_id)
                self._after_id = None

    @staticmethod
    def _lerp_color(c1, c2, t):
        """Interpola entre duas cores hex."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _animate_shimmer(self):
        if not self._animating:
            return
        self._shimmer_offset = (self._shimmer_offset + self._SHIMMER_SPEED) % 60
        self._redraw()
        self._after_id = self.after(self._SHIMMER_MS, self._animate_shimmer)

    def _redraw(self, *_):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        self.delete("all")
        r = min(4, h // 2)
        # track
        self._rounded_rect(0, 0, w, h, r, fill=C["input"], outline="")
        # gradient fill
        fill_w = int(w * self._value / 100)
        if fill_w > r:
            for i in range(self._GRAD_STEPS):
                x1 = int(i * fill_w / self._GRAD_STEPS)
                x2 = int((i + 1) * fill_w / self._GRAD_STEPS)
                if x2 > fill_w:
                    x2 = fill_w
                t = ((i / self._GRAD_STEPS) + self._shimmer_offset / 60) % 1.0
                color = self._lerp_color(C["grad_start"], C["grad_end"], t)
                if i == 0:
                    self._rounded_rect(x1, 0, x2, h, r, fill=color, outline="")
                elif i == self._GRAD_STEPS - 1:
                    self._rounded_rect(x1, 0, x2, h, r, fill=color, outline="")
                else:
                    self.create_rectangle(x1, 0, x2, h, fill=color, outline="")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        """Draws a rounded rectangle using a smooth polygon (no pieslice artifacts)."""
        points = [
            x1+r, y1,
            x2-r, y1,
            x2,   y1,
            x2,   y1+r,
            x2,   y2-r,
            x2,   y2,
            x2-r, y2,
            x1+r, y2,
            x1,   y2,
            x1,   y2-r,
            x1,   y1+r,
            x1,   y1,
        ]
        self.create_polygon(points, smooth=True, **kw)


# ─────────────────────────────────────────────────────────────
#  Spinner
# ─────────────────────────────────────────────────────────────

class SpinnerWindow(tk.Toplevel):
    _ARC1_SPAN = 120
    _ARC2_SPAN = 80
    _SPEED1    = 5          # arco teal — mais lento
    _SPEED2    = 8          # arco blue — mais rápido
    _INTERVAL  = 16
    _RADIUS    = 44
    _THICKNESS = 6

    def __init__(self, parent):
        super().__init__(parent)
        self.title("")
        self.resizable(False, False)
        self.configure(bg=C["panel"])
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._angle1   = 0
        self._angle2   = 180
        self._running  = False
        self._after_id = None
        self.status_var = tk.StringVar(value="Iniciando...")
        self.page_var   = tk.StringVar(value="")
        self._build()
        self._center(parent)
        self.grab_set()

    def _build(self):
        # borda glassmorphism
        outer = tk.Frame(self, bg=C["border"], padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=C["panel"], padx=40, pady=36)
        inner.pack()

        tk.Label(inner, text="Processando",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(pady=(0, 18))

        size = self._RADIUS * 2 + self._THICKNESS * 2 + 8
        self._canvas = tk.Canvas(inner, width=size, height=size,
                                 bg=C["panel"], highlightthickness=0)
        self._canvas.pack()
        cx = cy = size // 2
        r, t = self._RADIUS, self._THICKNESS

        # track sutil
        self._canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                 outline=C["input"], width=t)
        # arco 1 — teal
        self._arc1 = self._canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=90, extent=-self._ARC1_SPAN,
            outline=C["accent"], width=t, style="arc"
        )
        # arco 2 — blue (mais rápido)
        self._arc2 = self._canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=270, extent=-self._ARC2_SPAN,
            outline=C["accent2"], width=t, style="arc"
        )

        tk.Label(inner, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=C["panel"], fg=C["fg"],
                 wraplength=280, justify="center").pack(pady=(16, 2))
        tk.Label(inner, textvariable=self.page_var,
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_reqwidth())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def set_status(self, msg):
        self.status_var.set(msg)

    def set_page(self, current, total):
        self.page_var.set(f"Página {current} de {total}")

    def _animate(self):
        if not self._running:
            return
        self._angle1 = (self._angle1 + self._SPEED1) % 360
        self._angle2 = (self._angle2 + self._SPEED2) % 360
        self._canvas.itemconfigure(self._arc1, start=90 - self._angle1)
        self._canvas.itemconfigure(self._arc2, start=90 - self._angle2)
        self._after_id = self.after(self._INTERVAL, self._animate)


# ─────────────────────────────────────────────────────────────
#  Update Dialog
# ─────────────────────────────────────────────────────────────

class UpdateDialog(tk.Toplevel):

    def __init__(self, parent, release_info):
        super().__init__(parent)
        self._info   = release_info
        self._parent = parent
        self.title("Atualização disponível")
        self.resizable(False, False)
        self.configure(bg=C["panel"])
        self.attributes("-topmost", True)
        self._build()
        self._center(parent)
        self.grab_set()

    def _build(self):
        tag  = self._info["tag"]
        body = self._info["body"]

        # borda
        wrap = tk.Frame(self, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True)
        root = tk.Frame(wrap, bg=C["panel"])
        root.pack(fill="both", expand=True)

        # cabeçalho
        hdr = tk.Frame(root, bg=C["bg"], padx=24, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Nova versão disponível",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["bg"], fg=C["fg_bright"]).pack(anchor="w")
        tk.Label(hdr, text=f"v{APP_VERSION}  →  v{tag}",
                 font=("Segoe UI", 10), bg=C["bg"], fg=C["accent"]).pack(anchor="w", pady=(3, 0))

        # separador
        tk.Frame(root, bg=C["border"], height=1).pack(fill="x")

        # changelog
        body_frame = tk.Frame(root, bg=C["panel"], padx=20, pady=14)
        body_frame.pack(fill="both", expand=True)
        tk.Label(body_frame, text="O que há de novo:",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["fg_dim"]).pack(anchor="w", pady=(0, 6))

        txt = tk.Text(body_frame, height=10, width=52,
                      bg=C["input"], fg=C["fg"],
                      relief="flat", font=("Consolas", 9),
                      wrap="word", state="normal",
                      highlightthickness=1,
                      highlightbackground=C["border"],
                      bd=0, padx=8, pady=6)
        txt.insert("1.0", body)
        txt.config(state="disabled")

        sb = ttk.Scrollbar(body_frame, orient="vertical",
                           command=txt.yview, style="Dark.Vertical.TScrollbar")
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tk.Frame(root, bg=C["border"], height=1).pack(fill="x")

        # botões
        btn_row = tk.Frame(root, bg=C["panel"], padx=24, pady=16)
        btn_row.pack(fill="x")
        _accent_btn(
            btn_row,
            text="  Baixar atualização  ",
            command=self._open_release,
            padx=16, pady=8
        ).pack(side="left", padx=(0, 10))
        _flat_btn(
            btn_row, text="Agora não",
            command=self._dismiss,
            padx=12, pady=8
        ).pack(side="left")

        self._center(self._parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_reqwidth())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    def _open_release(self):
        webbrowser.open(self._info.get("html_url", GITHUB_RELEASES_PAGE))
        self._dismiss()

    def _dismiss(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        messagebox.showerror("Falha no download", msg, parent=self)


# ─────────────────────────────────────────────────────────────
#  Main App
# ─────────────────────────────────────────────────────────────

class PDFOcrApp(TkinterDnD.Tk if _HAS_DND else tk.Tk):

    # ícones unicode para a sidebar
    _NAV = [
        ("ocr",      "⬡", "OCR"),
        ("compress", "⊜", "Comprimir"),
        ("split",    "⊟", "Dividir"),
        ("merge",    "⊞", "Juntar"),
        ("about",    "ℹ", "Sobre"),
    ]

    # Presets de qualidade: (label_exibição, dpi, jpeg_quality)
    _QUALITY_PRESETS = [
        ("Máxima compressão  —  100 DPI · JPEG 40%",  100, 40),
        ("Baixa              —  120 DPI · JPEG 55%",  120, 55),
        ("Média              —  150 DPI · JPEG 65%",  150, 65),
        ("Alta               —  200 DPI · JPEG 80%",  200, 80),
        ("Muito alta         —  250 DPI · JPEG 88%",  250, 88),
    ]

    # Formatos de imagem embutida: (label_exibição, fmt_PIL, sufixo_tmp)
    _IMG_FORMATS = [
        ("JPEG — menor tamanho (com perda)",  "JPEG", ".jpg"),
        ("PNG  — sem perda de qualidade",     "PNG",  ".png"),
    ]

    def __init__(self):
        super().__init__()
        self.title(f"PDF Tools  v{APP_VERSION}")
        self.geometry("760x640")
        self.minsize(760, 580)
        self.resizable(True, True)
        self.configure(bg=C["bg"])

        # ── OCR ──────────────────────────────────────────────
        self.ocr_files           = []          # lista de caminhos
        self.ocr_outdir          = tk.StringVar()
        self.lang                = tk.StringVar(value="por")
        self.status              = tk.StringVar(value="Adicione PDFs para iniciar.")
        self.progress_var        = tk.DoubleVar(value=0)
        self.highlight_names_var = tk.BooleanVar(value=True)
        self._running            = False

        # ── Comprimir ────────────────────────────────────────
        self.compress_files      = []
        self.compress_outdir     = tk.StringVar()
        self.compress_status     = tk.StringVar(value="Adicione PDFs para comprimir.")
        self._compress_running   = False
        # índice default = Média (posição 2)
        self.compress_quality    = tk.StringVar(
            value=self._QUALITY_PRESETS[2][0])
        self.compress_format     = tk.StringVar(
            value=self._IMG_FORMATS[0][0])

        # ── Split ────────────────────────────────────────────
        self._split_pdf_path = ""
        self._split_total_pages = 0
        self._split_running = False
        self._split_intervals = []

        # Merge
        self._merge_files = []
        self._merge_running = False
        self._merge_drag_start_idx = None

        # ── Geral ────────────────────────────────────────────
        self.auto_update_var = tk.BooleanVar(value=True)
        self.update_status   = tk.StringVar(value="")
        self._spinner        = None
        self._active_page    = None
        self._page_frames    = {}

        self._apply_ttk_style()
        self._build_ui()
        self._load_prefs()
        self._show_page("ocr")

        if not DEPS_OK:
            self._show_dep_error()

    # ── TTK global style ──────────────────────────────────────

    def _apply_ttk_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".",
                     background=C["bg"],
                     foreground=C["fg"],
                     fieldbackground=C["input"],
                     troughcolor=C["input"],
                     selectbackground=C["sel"],
                     selectforeground=C["fg_bright"],
                     bordercolor=C["border"],
                     lightcolor=C["border"],
                     darkcolor=C["border"])
        s.configure("TCombobox",
                     background=C["input"],
                     foreground=C["fg"],
                     fieldbackground=C["input"],
                     arrowcolor=C["accent"],
                     bordercolor=C["border"],
                     relief="flat")
        s.map("TCombobox",
              fieldbackground=[("readonly", C["input"])],
              foreground=[("readonly", C["fg"])],
              selectbackground=[("readonly", C["sel"])],
              selectforeground=[("readonly", C["fg_bright"])])
        s.configure("Dark.Vertical.TScrollbar",
                     background=C["input"],
                     troughcolor=C["panel"],
                     bordercolor=C["panel"],
                     arrowcolor=C["accent"])
        s.configure("TCheckbutton",
                     background=C["panel"],
                     foreground=C["fg"],
                     focuscolor=C["panel"],
                     indicatorcolor=C["input"],
                     indicatorrelief="flat")
        s.map("TCheckbutton",
              background=[("active", C["panel"])],
              foreground=[("active", C["fg_bright"])],
              indicatorcolor=[("selected", C["accent"])])

    # ── Thumbnail helpers ────────────────────────────────────

    def _pdf_thumbnail(self, pdf_path, page_num=1, max_h=220):
        """Gera thumbnail de uma página do PDF. Retorna ImageTk.PhotoImage ou None."""
        try:
            poppler_path = find_poppler()
            imgs = convert_from_path(
                pdf_path, dpi=72, poppler_path=poppler_path,
                first_page=page_num, last_page=page_num)
            img = imgs[0]
            ratio = max_h / img.height
            new_w = int(img.width * ratio)
            img = img.resize((new_w, max_h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _pdf_thumbnail_async(self, pdf_path, page_num, max_h, callback):
        """Gera thumbnail em background thread e chama callback(photo) na UI thread."""
        def _worker():
            photo = self._pdf_thumbnail(pdf_path, page_num, max_h)
            self.after(0, lambda: callback(photo))
        threading.Thread(target=_worker, daemon=True).start()

    # ── Sidebar constants ────────────────────────────────────────
    _SIDEBAR_COLLAPSED = 56
    _SIDEBAR_EXPANDED  = 180
    _SIDEBAR_ANIM_MS   = 15      # intervalo entre frames
    _SIDEBAR_ANIM_STEP = 12      # pixels por frame

    # ── Layout principal ──────────────────────────────────────

    def _build_ui(self):
        # sidebar container — usa place para animar width
        self._sidebar = tk.Frame(self, bg=C["sidebar"], width=self._SIDEBAR_COLLAPSED)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._sidebar_expanded = False
        self._sidebar_anim_id = None
        self._sidebar_target_w = self._SIDEBAR_COLLAPSED

        # cabeçalho da sidebar
        self._sidebar_logo = tk.Label(self._sidebar, text="⬡",
                 font=("Segoe UI", 18), bg=C["sidebar"],
                 fg=C["accent"])
        self._sidebar_logo.pack(pady=(18, 2))
        tk.Frame(self._sidebar, bg=C["border"], height=1).pack(fill="x", padx=8, pady=6)

        # botões de navegação
        self._nav_btns = {}
        self._nav_labels = {}
        self._nav_active_key = None
        for key, icon, label in self._NAV:
            f = tk.Frame(self._sidebar, bg=C["sidebar"])
            f.pack(fill="x")
            # frame interno para ícone + texto lado a lado
            inner = tk.Frame(f, bg=C["sidebar"])
            inner.pack(fill="x", padx=4, pady=2)
            btn = tk.Button(
                inner, text=icon,
                font=("Segoe UI", 16),
                bg=C["sidebar"], fg=C["fg_dim"],
                activebackground=C["hover"],
                activeforeground=C["accent"],
                relief="flat", bd=0, cursor="hand2",
                width=2, pady=8,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(side="left")
            lbl = tk.Label(inner, text=label,
                           font=("Segoe UI", 10),
                           bg=C["sidebar"], fg=C["fg_dim"],
                           cursor="hand2")
            lbl.bind("<Button-1>", lambda _, k=key: self._show_page(k))
            # label starts hidden (collapsed)
            self._nav_btns[key] = btn
            self._nav_labels[key] = lbl

        # hover para expandir / retrair
        self._sidebar.bind("<Enter>", self._sidebar_expand)
        self._sidebar.bind("<Leave>", self._sidebar_collapse)

        # área de conteúdo
        self._content = tk.Frame(self, bg=C["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        # título da página
        self._title_bar = tk.Frame(self._content, bg=C["bg"], padx=24, pady=14)
        self._title_bar.pack(fill="x")
        self._page_title = tk.Label(self._title_bar, text="",
                                    font=("Segoe UI", 14, "bold"),
                                    bg=C["bg"], fg=C["fg_bright"])
        self._page_title.pack(side="left")
        self._page_sub = tk.Label(self._title_bar, text="",
                                  font=("Segoe UI", 9),
                                  bg=C["bg"], fg=C["fg_dim"])
        self._page_sub.pack(side="left", padx=(10, 0), pady=(3, 0))

        tk.Frame(self._content, bg=C["border"], height=1).pack(fill="x")

        # container das páginas
        self._pages = tk.Frame(self._content, bg=C["bg"])
        self._pages.pack(fill="both", expand=True)

        self._build_ocr_page()
        self._build_compress_page()
        self._build_split_page()
        self._build_merge_page()
        self._build_about_page()

    # ── Sidebar animation ─────────────────────────────────────

    def _sidebar_expand(self, _event=None):
        self._sidebar_expanded = True
        self._sidebar_target_w = self._SIDEBAR_EXPANDED
        # mostrar labels
        for key, lbl in self._nav_labels.items():
            lbl.pack(side="left", padx=(4, 0))
        if not self._sidebar_anim_id:
            self._sidebar_animate()

    def _sidebar_collapse(self, _event=None):
        self._sidebar_expanded = False
        self._sidebar_target_w = self._SIDEBAR_COLLAPSED
        # esconder labels
        for key, lbl in self._nav_labels.items():
            lbl.pack_forget()
        if not self._sidebar_anim_id:
            self._sidebar_animate()

    def _sidebar_animate(self):
        current_w = self._sidebar.winfo_width()
        target = self._sidebar_target_w
        if current_w == target:
            self._sidebar_anim_id = None
            return
        if current_w < target:
            new_w = min(current_w + self._SIDEBAR_ANIM_STEP, target)
        else:
            new_w = max(current_w - self._SIDEBAR_ANIM_STEP, target)
        self._sidebar.config(width=new_w)
        self._sidebar_anim_id = self.after(self._SIDEBAR_ANIM_MS, self._sidebar_animate)

    def _show_page(self, key):
        if self._active_page == key:
            return
        self._active_page = key
        self._nav_active_key = key
        for k, frame in self._page_frames.items():
            frame.pack_forget()
        self._page_frames[key].pack(fill="both", expand=True, padx=0, pady=0)

        # atualiza destaque da sidebar
        for k, btn in self._nav_btns.items():
            lbl = self._nav_labels[k]
            if k == key:
                btn.config(fg=C["accent"], bg=C["hover"])
                lbl.config(fg=C["accent"], bg=C["hover"])
            else:
                btn.config(fg=C["fg_dim"], bg=C["sidebar"])
                lbl.config(fg=C["fg_dim"], bg=C["sidebar"])

        titles = {
            "ocr":      ("OCR",        "Converta PDFs escaneados em PDFs pesquisáveis"),
            "compress": ("Comprimir",  "Reduza o tamanho de PDFs existentes"),
            "split":    ("Dividir PDF","Separe um PDF em partes individuais"),
            "merge":    ("Juntar PDF", "Una múltiplos PDFs em um único arquivo"),
            "about":    ("Sobre",      f"PDF Tools  v{APP_VERSION}"),
        }
        t, s = titles[key]
        self._page_title.config(text=t)
        self._page_sub.config(text=s)

    # ── Página OCR ────────────────────────────────────────────

    def _build_ocr_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["ocr"] = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        # card principal — glassmorphism style
        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)   # row da listbox expande

        # ── Cabeçalho da lista ────────────────────────────────
        hdr = tk.Frame(card, bg=C["panel"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        tk.Label(hdr, text="Arquivos PDF para OCR",
                 font=("Segoe UI", 9, "bold"), bg=C["panel"],
                 fg=C["fg"]).pack(side="left")
        self._ocr_count_lbl = tk.Label(
            hdr, text="(0 arquivo)", font=("Segoe UI", 9),
            bg=C["panel"], fg=C["fg_dim"])
        self._ocr_count_lbl.pack(side="left", padx=(6, 0))
        _flat_btn(hdr, "✕ Remover", self._ocr_remove_selected,
                  padx=8, pady=2).pack(side="right")
        _flat_btn(hdr, "+ Adicionar", self._ocr_add_files,
                  padx=8, pady=2).pack(side="right", padx=(0, 4))

        # ── Listbox ───────────────────────────────────────────
        list_f = tk.Frame(card, bg=C["panel"])
        list_f.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        list_f.columnconfigure(0, weight=1)
        list_f.rowconfigure(0, weight=1)

        sb_ocr = ttk.Scrollbar(list_f, orient="vertical",
                               style="Dark.Vertical.TScrollbar")
        self.ocr_listbox = tk.Listbox(
            list_f,
            bg=C["input"], fg=C["fg"],
            selectbackground=C["sel"], selectforeground=C["fg_bright"],
            relief="flat", highlightthickness=2,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            font=("Segoe UI", 10), activestyle="none",
            selectmode="extended",
            yscrollcommand=sb_ocr.set,
        )
        sb_ocr.config(command=self.ocr_listbox.yview)
        self.ocr_listbox.grid(row=0, column=0, sticky="nsew")
        sb_ocr.grid(row=0, column=1, sticky="ns")
        # Drag-and-drop (double-click to remove individual)
        self.ocr_listbox.bind("<Double-Button-1>", lambda _: self._ocr_remove_selected())

        # ── Pasta de saída (opcional) ─────────────────────────
        outdir_f = tk.Frame(card, bg=C["panel"])
        outdir_f.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        tk.Label(outdir_f, text="Pasta de saída", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")
        e_outdir = tk.Entry(outdir_f, textvariable=self.ocr_outdir,
                            state="readonly", font=("Segoe UI", 9), width=42)
        _style_entry(e_outdir)
        e_outdir.pack(side="left", ipady=4, padx=(0, 8))
        _flat_btn(outdir_f, "Pasta", self._browse_ocr_outdir,
                  padx=10, pady=3).pack(side="left")
        tk.Label(outdir_f, text="(vazio = mesma pasta do PDF)",
                 font=("Segoe UI", 8), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left", padx=(8, 0))

        # ── Idioma + opções ───────────────────────────────────
        cfg_f = tk.Frame(card, bg=C["panel"])
        cfg_f.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

        tk.Label(cfg_f, text="Idioma OCR", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")
        lang_combo = ttk.Combobox(cfg_f, textvariable=self.lang,
                                  width=26, state="readonly",
                                  font=("Segoe UI", 9))
        lang_combo["values"] = [
            "por — Português",
            "eng — Inglês",
            "por+eng — Português + Inglês",
            "spa — Espanhol",
            "fra — Francês",
            "deu — Alemão",
        ]
        lang_combo.current(0)
        lang_combo.pack(side="left", ipady=4, padx=(0, 20))
        lang_combo.bind("<<ComboboxSelected>>", self._on_lang_select)

        ttk.Checkbutton(
            cfg_f,
            text="Destacar nomes de pessoas no PDF",
            variable=self.highlight_names_var,
            style="TCheckbutton",
            command=self._save_prefs,
        ).pack(side="left")

        # ── Status + barra + botões (fixos na base) ───────────
        bottom = tk.Frame(page, bg=C["bg"])
        bottom.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        bottom.columnconfigure(0, weight=1)

        tk.Label(bottom, textvariable=self.status,
                 font=("Segoe UI", 9), bg=C["bg"], fg=C["fg_dim"],
                 anchor="w").grid(row=0, column=0, sticky="ew", pady=(4, 4))

        self.pb = CanvasProgressBar(bottom, height=6)
        self.pb.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        btn_f = tk.Frame(bottom, bg=C["bg"])
        btn_f.grid(row=2, column=0, sticky="w")
        self.btn_run = _accent_btn(
            btn_f, text="  ▶  Iniciar OCR  ",
            command=self._start,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9,
        )
        self.btn_run.pack(side="left", padx=(0, 10))
        _flat_btn(btn_f, text="Limpar lista",
                  command=self._clear,
                  padx=14, pady=9).pack(side="left")

    # ── Página Comprimir ─────────────────────────────────────

    def _build_compress_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["compress"] = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        # ── Cabeçalho ─────────────────────────────────────────
        hdr = tk.Frame(card, bg=C["panel"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        tk.Label(hdr, text="Arquivos PDF para comprimir",
                 font=("Segoe UI", 9, "bold"), bg=C["panel"],
                 fg=C["fg"]).pack(side="left")
        self._cmp_count_lbl = tk.Label(
            hdr, text="(0 arquivo)", font=("Segoe UI", 9),
            bg=C["panel"], fg=C["fg_dim"])
        self._cmp_count_lbl.pack(side="left", padx=(6, 0))
        _flat_btn(hdr, "✕ Remover", self._compress_remove_selected,
                  padx=8, pady=2).pack(side="right")
        _flat_btn(hdr, "+ Adicionar", self._compress_add_files,
                  padx=8, pady=2).pack(side="right", padx=(0, 4))

        # ── Listbox ───────────────────────────────────────────
        list_f = tk.Frame(card, bg=C["panel"])
        list_f.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        list_f.columnconfigure(0, weight=1)
        list_f.rowconfigure(0, weight=1)

        sb_cmp = ttk.Scrollbar(list_f, orient="vertical",
                               style="Dark.Vertical.TScrollbar")
        self.compress_listbox = tk.Listbox(
            list_f,
            bg=C["input"], fg=C["fg"],
            selectbackground=C["sel"], selectforeground=C["fg_bright"],
            relief="flat", highlightthickness=2,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            font=("Segoe UI", 10), activestyle="none",
            selectmode="extended",
            yscrollcommand=sb_cmp.set,
        )
        sb_cmp.config(command=self.compress_listbox.yview)
        self.compress_listbox.grid(row=0, column=0, sticky="nsew")
        sb_cmp.grid(row=0, column=1, sticky="ns")
        self.compress_listbox.bind(
            "<Double-Button-1>", lambda _: self._compress_remove_selected())

        # ── Pasta de saída ────────────────────────────────────
        outdir_f = tk.Frame(card, bg=C["panel"])
        outdir_f.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        tk.Label(outdir_f, text="Pasta de saída", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")
        e_cout = tk.Entry(outdir_f, textvariable=self.compress_outdir,
                          state="readonly", font=("Segoe UI", 9), width=42)
        _style_entry(e_cout)
        e_cout.pack(side="left", ipady=4, padx=(0, 8))
        _flat_btn(outdir_f, "Pasta", self._browse_compress_outdir,
                  padx=10, pady=3).pack(side="left")
        tk.Label(outdir_f, text="(vazio = mesma pasta do PDF)",
                 font=("Segoe UI", 8), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left", padx=(8, 0))

        # ── Qualidade + Formato ───────────────────────────────
        qf_f = tk.Frame(card, bg=C["panel"])
        qf_f.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 6))

        tk.Label(qf_f, text="Qualidade", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")
        quality_combo = ttk.Combobox(
            qf_f, textvariable=self.compress_quality,
            values=[p[0] for p in self._QUALITY_PRESETS],
            state="readonly", width=38, font=("Segoe UI", 9))
        quality_combo.pack(side="left", ipady=4)

        fmt_f = tk.Frame(card, bg=C["panel"])
        fmt_f.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 14))

        tk.Label(fmt_f, text="Formato", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")
        fmt_combo = ttk.Combobox(
            fmt_f, textvariable=self.compress_format,
            values=[f[0] for f in self._IMG_FORMATS],
            state="readonly", width=38, font=("Segoe UI", 9))
        fmt_combo.pack(side="left", ipady=4)

        # ── Status + barra + botões ───────────────────────────
        bottom = tk.Frame(page, bg=C["bg"])
        bottom.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        bottom.columnconfigure(0, weight=1)

        tk.Label(bottom, textvariable=self.compress_status,
                 font=("Segoe UI", 9), bg=C["bg"], fg=C["fg_dim"],
                 anchor="w").grid(row=0, column=0, sticky="ew", pady=(4, 4))

        self.compress_pb = CanvasProgressBar(bottom, height=6)
        self.compress_pb.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        btn_f = tk.Frame(bottom, bg=C["bg"])
        btn_f.grid(row=2, column=0, sticky="w")
        self.btn_compress = _accent_btn(
            btn_f, text="  ⊜  Comprimir PDFs  ",
            command=self._start_compress,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9,
        )
        self.btn_compress.pack(side="left", padx=(0, 10))
        _flat_btn(btn_f, text="Limpar lista",
                  command=self._clear_compress,
                  padx=14, pady=9).pack(side="left")

    # ── Comprimir eventos ─────────────────────────────────────

    def _compress_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar PDFs para comprimir",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        for p in paths:
            if p not in self.compress_files:
                self.compress_files.append(p)
                self.compress_listbox.insert(tk.END, os.path.basename(p))
        self._update_compress_count()

    def _compress_remove_selected(self):
        sel = list(self.compress_listbox.curselection())
        for idx in reversed(sel):
            self.compress_listbox.delete(idx)
            del self.compress_files[idx]
        self._update_compress_count()

    def _browse_compress_outdir(self):
        d = filedialog.askdirectory(title="Pasta de saída para PDFs comprimidos")
        if d:
            self.compress_outdir.set(d)

    def _update_compress_count(self):
        n = len(self.compress_files)
        self._cmp_count_lbl.config(
            text=f"({n} arquivo{'s' if n != 1 else ''})")

    def _clear_compress(self):
        self.compress_files.clear()
        self.compress_listbox.delete(0, tk.END)
        self.compress_pb.set(0)
        self.compress_outdir.set("")
        self.compress_status.set("Adicione PDFs para comprimir.")
        self._update_compress_count()

    def _start_compress(self):
        if not DEPS_OK:
            self._show_dep_error()
            return
        if not self.compress_files:
            messagebox.showwarning("Aviso", "Adicione ao menos um PDF.")
            return
        if self._compress_running:
            return

        # Resolve preset de qualidade
        q_label = self.compress_quality.get()
        dpi, jpeg_q = next(
            ((p[1], p[2]) for p in self._QUALITY_PRESETS if p[0] == q_label),
            (150, 65))

        # Resolve formato
        f_label = self.compress_format.get()
        img_fmt, tmp_suffix = next(
            ((f[1], f[2]) for f in self._IMG_FORMATS if f[0] == f_label),
            ("JPEG", ".jpg"))

        self._compress_running = True
        self.btn_compress.config(state="disabled")
        self.compress_pb.set(0)
        self._spinner = SpinnerWindow(self)
        self._spinner.start()
        threading.Thread(
            target=self._run_compress_batch,
            args=(list(self.compress_files), self.compress_outdir.get(),
                  dpi, jpeg_q, img_fmt, tmp_suffix),
            daemon=True,
        ).start()

    def _run_compress_single(self, input_pdf, output_pdf,
                             fi, total_files,
                             dpi=150, jpeg_q=65,
                             img_fmt="JPEG", tmp_suffix=".jpg"):
        """Comprime um único arquivo. Retorna (orig_kb, new_kb) ou levanta exceção."""
        poppler_path = find_poppler()

        # Count pages first (lightweight)
        with open(input_pdf, "rb") as fh:
            total_pages = len(PyPDF2.PdfReader(fh).pages)

        merger = PyPDF2.PdfWriter()

        for pi in range(1, total_pages + 1):
            base_pct = (fi - 1) / total_files * 100
            page_pct = pi / total_pages * (100 / total_files)
            msg = (f"[{fi}/{total_files}] "
                   f"{os.path.basename(input_pdf)} "
                   f"— página {pi}/{total_pages}")
            self.after(0, lambda m=msg: self.compress_status.set(m))
            self._spinner_status(f"{os.path.basename(input_pdf)}")
            self._spinner_page(pi, total_pages)

            # Convert one page at a time to save memory
            page_imgs = convert_from_path(
                input_pdf, dpi=dpi, poppler_path=poppler_path,
                first_page=pi, last_page=pi)
            pil_img = page_imgs[0]
            img_w, img_h = pil_img.size

            # Compress image directly to BytesIO (no temp files)
            img_buf = io.BytesIO()
            img_rgb = pil_img.convert("RGB")
            if img_fmt == "JPEG":
                img_rgb.save(img_buf, format="JPEG", quality=jpeg_q,
                             optimize=True, progressive=True)
            else:  # PNG
                img_rgb.save(img_buf, format="PNG",
                             compress_level=9, optimize=True)
            img_buf.seek(0)
            del pil_img, page_imgs, img_rgb  # free memory

            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
            c.drawImage(ImageReader(img_buf), 0, 0, width=img_w, height=img_h)
            c.save()

            merger.add_page(PyPDF2.PdfReader(io.BytesIO(buf.getvalue())).pages[0])

            pct = base_pct + page_pct * 0.95
            self.after(0, lambda p=pct: self.compress_pb.set(p))

        with open(output_pdf, "wb") as f:
            merger.write(f)

        return os.path.getsize(input_pdf) // 1024, \
               os.path.getsize(output_pdf) // 1024

    def _run_compress_batch(self, files, outdir,
                            dpi=150, jpeg_q=65,
                            img_fmt="JPEG", tmp_suffix=".jpg"):
        total = len(files)
        results, errors = [], []

        for fi, input_pdf in enumerate(files, 1):
            base = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = outdir if outdir else os.path.dirname(input_pdf)
            output_pdf = os.path.join(dest_dir, base + "_comprimido.pdf")
            try:
                orig_kb, new_kb = self._run_compress_single(
                    input_pdf, output_pdf, fi, total,
                    dpi, jpeg_q, img_fmt, tmp_suffix)
                ratio = (1 - new_kb / orig_kb) * 100 if orig_kb > 0 else 0
                results.append((os.path.basename(input_pdf),
                                 orig_kb, new_kb, ratio))
            except Exception as e:
                errors.append(f"{os.path.basename(input_pdf)}: {e}")

        self.after(0, lambda: self.compress_pb.set(100))
        self.after(0, self._close_spinner)

        if errors:
            err_list = "\n".join(errors)
            self.after(0, lambda: self.compress_status.set(
                f"Concluído com {len(errors)} erro(s)."))
            self.after(0, lambda: messagebox.showwarning(
                "Compressão concluída com erros",
                f"{len(results)} arquivo(s) comprimido(s) com sucesso.\n\n"
                f"Erros:\n{err_list}"
            ))
        else:
            lines = "\n".join(
                f"  {name}  {ok}→{nk} KB  (-{r:.0f}%)"
                for name, ok, nk, r in results
            )
            total_orig = sum(r[1] for r in results)
            total_new  = sum(r[2] for r in results)
            total_ratio = (1 - total_new / total_orig) * 100 if total_orig > 0 else 0
            self.after(0, lambda: self.compress_status.set(
                f"Concluído! {total_orig} KB → {total_new} KB  "
                f"(-{total_ratio:.0f}%)"))
            self.after(0, lambda: messagebox.showinfo(
                "Compressão concluída",
                f"{total} arquivo(s) comprimido(s)!\n\n{lines}\n\n"
                f"Total: {total_orig} KB → {total_new} KB  (-{total_ratio:.0f}%)"
            ))

        self._compress_running = False
        self.after(0, lambda: self.btn_compress.config(state="normal"))

    # ── Em breve ──────────────────────────────────────────────

    def _build_split_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["split"] = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
        card.columnconfigure(0, weight=1)

        inner = tk.Frame(card, bg=C["panel"], padx=20, pady=16)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(0, weight=1)

        # ── Seleção de arquivo ──────────────────────────────────
        file_f = tk.Frame(inner, bg=C["panel"])
        file_f.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        _flat_btn(file_f, "+ Selecionar PDF", self._split_select_file,
                  padx=10, pady=3).pack(side="left")
        self._split_file_lbl = tk.Label(
            file_f, text="Nenhum arquivo selecionado",
            font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"])
        self._split_file_lbl.pack(side="left", padx=(10, 0))

        tk.Frame(inner, bg=C["border"], height=1).grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # ── Preview + controles lado a lado ──────────────────────
        content_f = tk.Frame(inner, bg=C["panel"])
        content_f.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        content_f.columnconfigure(0, weight=1)

        # Coluna esquerda: controles
        controls_f = tk.Frame(content_f, bg=C["panel"])
        controls_f.pack(side="left", fill="both", expand=True)

        # ── Modo de divisão ──────────────────────────────────────
        tk.Label(controls_f, text="Modo de divisão",
                 font=("Segoe UI", 9, "bold"), bg=C["panel"],
                 fg=C["fg"]).pack(anchor="w", pady=(0, 8))

        self._split_mode = tk.StringVar(value="single")
        modes_f = tk.Frame(controls_f, bg=C["panel"])
        modes_f.pack(anchor="w", pady=(0, 12))

        for val, label in [("single", "Intervalo único"),
                           ("multi",  "Múltiplos intervalos"),
                           ("all",    "Todas as páginas individualmente")]:
            tk.Radiobutton(
                modes_f, text=label, variable=self._split_mode,
                value=val, command=self._split_update_mode_ui,
                bg=C["panel"], fg=C["fg"],
                selectcolor=C["input"],
                activebackground=C["panel"], activeforeground=C["accent"],
                font=("Segoe UI", 9),
                highlightthickness=0,
            ).pack(side="left", padx=(0, 20))

        # ── Painel modo único ────────────────────────────────────
        self._split_single_f = tk.Frame(controls_f, bg=C["panel"])
        self._split_single_f.pack(anchor="w", pady=(0, 8))
        tk.Label(self._split_single_f, text="De:", font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        self._split_from = tk.StringVar(value="1")
        e_from = tk.Entry(self._split_single_f, textvariable=self._split_from,
                          width=5, font=("Segoe UI", 9))
        _style_entry(e_from)
        e_from.pack(side="left", ipady=3, padx=(4, 12))
        tk.Label(self._split_single_f, text="Até:", font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        self._split_to = tk.StringVar(value="1")
        e_to = tk.Entry(self._split_single_f, textvariable=self._split_to,
                        width=5, font=("Segoe UI", 9))
        _style_entry(e_to)
        e_to.pack(side="left", ipady=3, padx=(4, 0))

        # ── Painel múltiplos intervalos ──────────────────────────
        self._split_multi_f = tk.Frame(controls_f, bg=C["panel"])
        # Starts hidden; shown via _split_update_mode_ui

        # campo de texto livre
        text_f = tk.Frame(self._split_multi_f, bg=C["panel"])
        text_f.pack(fill="x", pady=(0, 6))
        tk.Label(text_f, text="Intervalos (ex: 1-3, 5-8, 10):",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        self._split_text_intervals = tk.StringVar()
        e_text = tk.Entry(text_f, textvariable=self._split_text_intervals,
                          width=30, font=("Segoe UI", 9))
        _style_entry(e_text)
        e_text.pack(side="left", ipady=3, padx=(8, 0))

        # lista visual de intervalos
        self._split_rows_f = tk.Frame(self._split_multi_f, bg=C["panel"])
        self._split_rows_f.pack(fill="x", pady=(0, 6))

        _flat_btn(self._split_multi_f, "+ Adicionar intervalo",
                  self._split_add_interval_row, padx=8, pady=2).pack(anchor="w")

        # Coluna direita: preview
        preview_f = tk.Frame(content_f, bg=C["input"],
                             highlightthickness=1,
                             highlightbackground=C["border"])
        preview_f.pack(side="right", padx=(16, 0))

        self._split_preview_lbl = tk.Label(
            preview_f, text="Pré-visualização",
            font=("Segoe UI", 8), bg=C["input"], fg=C["fg_dim"],
            anchor="center")
        self._split_preview_lbl.pack(padx=8, pady=8)
        self._split_preview_photo = None  # keep reference

        # Navegação de páginas no preview
        nav_f = tk.Frame(preview_f, bg=C["input"])
        nav_f.pack(pady=(0, 8))
        _flat_btn(nav_f, "◀", self._split_preview_prev,
                  padx=6, pady=2).pack(side="left", padx=(0, 4))
        self._split_preview_page_var = tk.StringVar(value="")
        tk.Label(nav_f, textvariable=self._split_preview_page_var,
                 font=("Segoe UI", 8), bg=C["input"],
                 fg=C["fg_dim"]).pack(side="left", padx=4)
        _flat_btn(nav_f, "▶", self._split_preview_next,
                  padx=6, pady=2).pack(side="left", padx=(4, 0))

        self._split_preview_current = 1

        # ── Destino ──────────────────────────────────────────────
        tk.Frame(inner, bg=C["border"], height=1).grid(row=3, column=0, sticky="ew", pady=(4, 10))

        dest_f = tk.Frame(inner, bg=C["panel"])
        dest_f.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self._split_same_dir = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dest_f, text="Salvar na mesma pasta do arquivo original",
            variable=self._split_same_dir,
            bg=C["panel"], fg=C["fg"],
            selectcolor=C["input"],
            activebackground=C["panel"], activeforeground=C["accent"],
            font=("Segoe UI", 9),
            highlightthickness=0,
        ).pack(side="left")

        # ── Progresso e botão ────────────────────────────────────
        self._split_status = tk.StringVar(value="Selecione um PDF para dividir.")
        tk.Label(inner, textvariable=self._split_status,
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"], anchor="w").grid(row=5, column=0, sticky="ew", pady=(0, 4))

        self._split_pb = CanvasProgressBar(inner, height=6)
        self._split_pb.grid(row=6, column=0, sticky="ew", pady=(0, 10))

        btn_f = tk.Frame(inner, bg=C["panel"])
        btn_f.grid(row=7, column=0, sticky="w")
        self.btn_split = _accent_btn(
            btn_f, text="  \u229f  Dividir PDF  ",
            command=self._start_split,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9,
        )
        self.btn_split.pack(side="left")

    def _split_select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar PDF para dividir",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                self._split_total_pages = len(reader.pages)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o PDF:\n{e}")
            return
        self._split_pdf_path = path
        name = os.path.basename(path)
        self._split_file_lbl.config(
            text=f"{name}  ({self._split_total_pages} páginas)",
            fg=C["fg"])
        self._split_to.set(str(self._split_total_pages))
        self._split_status.set("Configure o modo de divisão e clique em Dividir.")
        # Load preview of first page
        self._split_preview_current = 1
        self._split_load_preview(1)

    def _split_load_preview(self, page_num):
        """Carrega thumbnail da página no preview."""
        if not self._split_pdf_path:
            return
        self._split_preview_page_var.set(f"{page_num} / {self._split_total_pages}")
        self._split_preview_lbl.config(text="Carregando...", image="")
        self._pdf_thumbnail_async(
            self._split_pdf_path, page_num, 300,
            self._split_set_preview)

    def _split_set_preview(self, photo):
        if photo:
            self._split_preview_photo = photo  # prevent GC
            self._split_preview_lbl.config(image=photo, text="")
        else:
            self._split_preview_lbl.config(text="Erro ao carregar", image="")

    def _split_preview_prev(self):
        if not self._split_pdf_path or self._split_preview_current <= 1:
            return
        self._split_preview_current -= 1
        self._split_load_preview(self._split_preview_current)

    def _split_preview_next(self):
        if not self._split_pdf_path or self._split_preview_current >= self._split_total_pages:
            return
        self._split_preview_current += 1
        self._split_load_preview(self._split_preview_current)

    def _split_update_mode_ui(self):
        mode = self._split_mode.get()
        if mode == "single":
            self._split_single_f.pack(anchor="w", pady=(0, 8))
            self._split_multi_f.pack_forget()
        elif mode == "multi":
            self._split_single_f.pack_forget()
            self._split_multi_f.pack(anchor="w", fill="x", pady=(0, 8))
        else:  # all
            self._split_single_f.pack_forget()
            self._split_multi_f.pack_forget()

    def _split_add_interval_row(self):
        row_f = tk.Frame(self._split_rows_f, bg=C["panel"])
        row_f.pack(fill="x", pady=2)
        v_from = tk.StringVar(value="1")
        v_to   = tk.StringVar(value="1")
        tk.Label(row_f, text="De:", font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        e_f = tk.Entry(row_f, textvariable=v_from, width=5, font=("Segoe UI", 9))
        _style_entry(e_f)
        e_f.pack(side="left", ipady=3, padx=(4, 8))
        tk.Label(row_f, text="Até:", font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        e_t = tk.Entry(row_f, textvariable=v_to, width=5, font=("Segoe UI", 9))
        _style_entry(e_t)
        e_t.pack(side="left", ipady=3, padx=(4, 8))
        _flat_btn(row_f, "×", lambda f=row_f, vs=(v_from, v_to): self._split_remove_interval_row(f, vs),
                  padx=6, pady=1).pack(side="left")
        self._split_intervals.append((v_from, v_to))

    def _split_remove_interval_row(self, frame, vars_tuple):
        if vars_tuple in self._split_intervals:
            self._split_intervals.remove(vars_tuple)
        frame.destroy()

    def _parse_split_intervals(self):
        """Retorna lista de (from_page, to_page) com índice 0-based, ou None em caso de erro."""
        mode = self._split_mode.get()
        total = self._split_total_pages
        intervals = []

        if mode == "single":
            try:
                f = int(self._split_from.get())
                t = int(self._split_to.get())
            except ValueError:
                messagebox.showerror("Erro", "Digite números válidos para De e Até.")
                return None
            if not (1 <= f <= t <= total):
                messagebox.showerror("Erro", f"Páginas devem estar entre 1 e {total}, com De ≤ Até.")
                return None
            intervals = [(f - 1, t - 1)]

        elif mode == "multi":
            # Tenta linhas visuais primeiro
            for v_from, v_to in self._split_intervals:
                try:
                    f = int(v_from.get())
                    t = int(v_to.get())
                except ValueError:
                    messagebox.showerror("Erro", "Preencha todos os campos De/Até com números.")
                    return None
                if not (1 <= f <= t <= total):
                    messagebox.showerror("Erro", f"Intervalo {f}-{t} inválido. Páginas de 1 a {total}.")
                    return None
                intervals.append((f - 1, t - 1))

            # Se não há linhas visuais, parseia campo de texto
            if not intervals:
                text = self._split_text_intervals.get().strip()
                if not text:
                    messagebox.showerror("Erro", "Adicione intervalos ou preencha o campo de texto.")
                    return None
                for part in text.split(","):
                    part = part.strip()
                    m = re.match(r'^(\d+)-(\d+)$', part)
                    if m:
                        f, t = int(m.group(1)), int(m.group(2))
                    elif re.match(r'^\d+$', part):
                        f = t = int(part)
                    else:
                        messagebox.showerror("Erro", f"Formato inválido: '{part}'. Use '1-3' ou '5'.")
                        return None
                    if not (1 <= f <= t <= total):
                        messagebox.showerror("Erro", f"Intervalo {f}-{t} inválido. Páginas de 1 a {total}.")
                        return None
                    intervals.append((f - 1, t - 1))

        else:  # all
            intervals = [(i, i) for i in range(total)]

        return intervals

    def _start_split(self):
        if not self._split_pdf_path:
            messagebox.showwarning("Aviso", "Selecione um PDF primeiro.")
            return
        if self._split_running:
            return
        intervals = self._parse_split_intervals()
        if intervals is None:
            return

        out_dir = ""
        if not self._split_same_dir.get():
            out_dir = filedialog.askdirectory(title="Pasta para salvar os PDFs divididos")
            if not out_dir:
                return

        self._split_running = True
        self.btn_split.config(state="disabled")
        self._split_pb.set(0)
        self._spinner = SpinnerWindow(self)
        self._spinner.start()
        threading.Thread(
            target=self._run_split,
            args=(self._split_pdf_path, intervals, out_dir),
            daemon=True,
        ).start()

    def _run_split(self, input_pdf, intervals, out_dir):
        try:
            base = os.path.splitext(os.path.basename(input_pdf))[0]
            dest = out_dir if out_dir else os.path.dirname(input_pdf)
            total = len(intervals)
            generated = []

            with open(input_pdf, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for i, (f, t) in enumerate(intervals):
                    writer = PyPDF2.PdfWriter()
                    for p in range(f, t + 1):
                        writer.add_page(reader.pages[p])
                    if f == t:
                        out_name = f"{base}_p{f + 1}.pdf"
                    else:
                        out_name = f"{base}_p{f + 1}-{t + 1}.pdf"
                    out_path = os.path.join(dest, out_name)
                    with open(out_path, "wb") as out_fh:
                        writer.write(out_fh)
                    generated.append(out_path)
                    pct = (i + 1) / total * 100
                    self.after(0, lambda v=pct: self._split_pb.set(v))
                    self.after(0, lambda n=i+1, tot=total: self._split_status.set(
                        f"Processando... {n}/{tot}"))
                    self._spinner_status(f"Dividindo parte {i+1} de {total}")

            self.after(0, lambda: self._split_status.set(
                f"{len(generated)} arquivo(s) gerado(s) em: {dest}"))
            self.after(0, lambda: self._split_pb.set(100))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro ao dividir", str(e)))
            self.after(0, lambda: self._split_status.set("Erro ao dividir o PDF."))
        finally:
            self._split_running = False
            self.after(0, self._close_spinner)
            self.after(0, lambda: self.btn_split.config(state="normal"))

    # ── Página Merge ─────────────────────────────────────────

    def _build_merge_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["merge"] = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        inner = tk.Frame(card, bg=C["panel"], padx=20, pady=16)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(0, weight=1)
        inner.rowconfigure(1, weight=1)

        # ── Cabeçalho / botões ───────────────────────────────────
        hdr = tk.Frame(inner, bg=C["panel"])
        hdr.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        tk.Label(hdr, text="PDFs para juntar",
                 font=("Segoe UI", 9, "bold"), bg=C["panel"],
                 fg=C["fg"]).pack(side="left")
        self._merge_count_lbl = tk.Label(
            hdr, text="(0 arquivos)", font=("Segoe UI", 9),
            bg=C["panel"], fg=C["fg_dim"])
        self._merge_count_lbl.pack(side="left", padx=(6, 0))
        _flat_btn(hdr, "✕ Remover", self._merge_remove_selected,
                  padx=8, pady=2).pack(side="right")
        _flat_btn(hdr, "+ Adicionar PDFs", self._merge_add_files,
                  padx=8, pady=2).pack(side="right", padx=(0, 4))

        # ── Listbox ──────────────────────────────────────────────
        list_f = tk.Frame(inner, bg=C["panel"])
        list_f.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        list_f.columnconfigure(0, weight=1)
        list_f.rowconfigure(0, weight=1)

        sb = ttk.Scrollbar(list_f, orient="vertical",
                           style="Dark.Vertical.TScrollbar")
        self._merge_listbox = tk.Listbox(
            list_f,
            bg=C["input"], fg=C["fg"],
            selectbackground=C["sel"], selectforeground=C["fg_bright"],
            relief="flat", highlightthickness=2,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            font=("Segoe UI", 10), activestyle="none",
            yscrollcommand=sb.set,
        )
        sb.config(command=self._merge_listbox.yview)
        self._merge_listbox.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        # Drag & drop interno (reordenação com mouse)
        self._merge_listbox.bind("<Button-1>",       self._merge_drag_start)
        self._merge_listbox.bind("<B1-Motion>",       self._merge_drag_motion)
        self._merge_listbox.bind("<ButtonRelease-1>", self._merge_drag_release)
        # Preview on selection change
        self._merge_listbox.bind("<<ListboxSelect>>", self._merge_on_select)

        # Drag & drop externo (arrastar arquivos do explorer)
        if _HAS_DND:
            self._merge_listbox.drop_target_register(TkinterDnD.DND_FILES)
            self._merge_listbox.dnd_bind("<<Drop>>", self._merge_drop_files)

        # ── Botões ↑ ↓ ──────────────────────────────────────────
        ord_f = tk.Frame(inner, bg=C["panel"])
        ord_f.grid(row=1, column=1, sticky="ns", padx=(8, 0), pady=(0, 8))
        _flat_btn(ord_f, "↑", self._merge_move_up,
                  padx=10, pady=6).pack(pady=(0, 4))
        _flat_btn(ord_f, "↓", self._merge_move_down,
                  padx=10, pady=6).pack()

        # ── Preview panel (right side) ───────────────────────────
        preview_f = tk.Frame(inner, bg=C["input"],
                             highlightthickness=1,
                             highlightbackground=C["border"])
        preview_f.grid(row=1, column=2, sticky="ns", padx=(8, 0), pady=(0, 8))

        self._merge_preview_lbl = tk.Label(
            preview_f, text="Selecione um PDF\npara pré-visualizar",
            font=("Segoe UI", 8), bg=C["input"], fg=C["fg_dim"],
            anchor="center")
        self._merge_preview_lbl.pack(padx=8, pady=8, expand=True)
        self._merge_preview_photo = None  # keep reference

        self._merge_preview_name = tk.Label(
            preview_f, text="",
            font=("Segoe UI", 8), bg=C["input"], fg=C["fg_dim"],
            wraplength=160)
        self._merge_preview_name.pack(padx=8, pady=(0, 8))

        # ── Área de drop visual ──────────────────────────────────
        drop_f = tk.Frame(inner, bg=C["input"],
                          highlightthickness=1,
                          highlightbackground=C["border"])
        drop_f.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        drop_lbl = tk.Label(drop_f,
                            text="⊞  Arraste PDFs aqui  ou  clique em + Adicionar PDFs",
                            font=("Segoe UI", 9), bg=C["input"],
                            fg=C["fg_dim"], pady=10)
        drop_lbl.pack()
        if _HAS_DND:
            drop_f.drop_target_register(TkinterDnD.DND_FILES)
            drop_f.dnd_bind("<<Drop>>", self._merge_drop_files)
            drop_lbl.drop_target_register(TkinterDnD.DND_FILES)
            drop_lbl.dnd_bind("<<Drop>>", self._merge_drop_files)

        # ── Destino ──────────────────────────────────────────────
        tk.Frame(inner, bg=C["border"], height=1).grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        dest_f = tk.Frame(inner, bg=C["panel"])
        dest_f.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        self._merge_same_dir = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dest_f, text="Salvar na mesma pasta do primeiro PDF",
            variable=self._merge_same_dir,
            bg=C["panel"], fg=C["fg"],
            selectcolor=C["input"],
            activebackground=C["panel"], activeforeground=C["accent"],
            font=("Segoe UI", 9),
            highlightthickness=0,
        ).pack(side="left")

        # ── Progresso e botão ────────────────────────────────────
        self._merge_status = tk.StringVar(value="Adicione PDFs para juntar.")
        tk.Label(inner, textvariable=self._merge_status,
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"], anchor="w").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=(0, 4))

        self._merge_pb = CanvasProgressBar(inner, height=6)
        self._merge_pb.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        btn_f = tk.Frame(inner, bg=C["panel"])
        btn_f.grid(row=7, column=0, columnspan=3, sticky="w")
        self.btn_merge = _accent_btn(
            btn_f, text="  ⊞  Juntar PDFs  ",
            command=self._start_merge,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9,
        )
        self.btn_merge.pack(side="left", padx=(0, 10))
        _flat_btn(btn_f, "Limpar lista", self._merge_clear,
                  padx=14, pady=9).pack(side="left")

    def _merge_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar PDFs para juntar",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        self._merge_insert_paths(paths)

    def _merge_drop_files(self, event):
        raw = event.data
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        flat = [p[0] or p[1] for p in paths]
        pdf_paths = [p for p in flat if p.lower().endswith(".pdf")]
        self._merge_insert_paths(pdf_paths)

    def _merge_insert_paths(self, paths):
        for p in paths:
            if p not in self._merge_files:
                try:
                    with open(p, "rb") as fh:
                        reader = PyPDF2.PdfReader(fh)
                        n_pages = len(reader.pages)
                except Exception:
                    n_pages = "?"
                self._merge_files.append(p)
                self._merge_listbox.insert(
                    tk.END, f"{os.path.basename(p)}  ({n_pages} pág.)")
        self._merge_update_count()

    def _merge_on_select(self, _event=None):
        """Carrega preview do PDF selecionado na listbox."""
        sel = self._merge_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._merge_files):
            return
        pdf_path = self._merge_files[idx]
        name = os.path.basename(pdf_path)
        self._merge_preview_name.config(text=name)
        self._merge_preview_lbl.config(text="Carregando...", image="")
        self._pdf_thumbnail_async(
            pdf_path, 1, 300,
            self._merge_set_preview)

    def _merge_set_preview(self, photo):
        if photo:
            self._merge_preview_photo = photo  # prevent GC
            self._merge_preview_lbl.config(image=photo, text="")
        else:
            self._merge_preview_lbl.config(text="Erro ao carregar", image="")

    def _merge_reset_preview(self):
        self._merge_preview_photo = None
        self._merge_preview_lbl.config(
            text="Selecione um PDF\npara pré-visualizar", image="")
        self._merge_preview_name.config(text="")

    def _merge_remove_selected(self):
        sel = list(self._merge_listbox.curselection())
        for idx in reversed(sel):
            self._merge_listbox.delete(idx)
            del self._merge_files[idx]
        self._merge_update_count()
        self._merge_reset_preview()

    def _merge_clear(self):
        self._merge_files.clear()
        self._merge_listbox.delete(0, tk.END)
        self._merge_pb.set(0)
        self._merge_status.set("Adicione PDFs para juntar.")
        self._merge_update_count()
        self._merge_reset_preview()

    def _merge_update_count(self):
        n = len(self._merge_files)
        self._merge_count_lbl.config(
            text=f"({n} arquivo{'s' if n != 1 else ''})")

    def _merge_move_up(self):
        sel = self._merge_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self._merge_files[idx], self._merge_files[idx - 1] = \
            self._merge_files[idx - 1], self._merge_files[idx]
        text = self._merge_listbox.get(idx)
        self._merge_listbox.delete(idx)
        self._merge_listbox.insert(idx - 1, text)
        self._merge_listbox.selection_set(idx - 1)

    def _merge_move_down(self):
        sel = self._merge_listbox.curselection()
        if not sel or sel[0] >= self._merge_listbox.size() - 1:
            return
        idx = sel[0]
        self._merge_files[idx], self._merge_files[idx + 1] = \
            self._merge_files[idx + 1], self._merge_files[idx]
        text = self._merge_listbox.get(idx)
        self._merge_listbox.delete(idx)
        self._merge_listbox.insert(idx + 1, text)
        self._merge_listbox.selection_set(idx + 1)

    def _merge_drag_start(self, event):
        self._merge_drag_start_idx = self._merge_listbox.nearest(event.y)

    def _merge_drag_motion(self, event):
        if self._merge_drag_start_idx is None:
            return
        idx = self._merge_listbox.nearest(event.y)
        if idx != self._merge_drag_start_idx:
            self._merge_files[idx], self._merge_files[self._merge_drag_start_idx] = \
                self._merge_files[self._merge_drag_start_idx], self._merge_files[idx]
            text_from = self._merge_listbox.get(self._merge_drag_start_idx)
            text_to   = self._merge_listbox.get(idx)
            self._merge_listbox.delete(self._merge_drag_start_idx)
            self._merge_listbox.insert(self._merge_drag_start_idx, text_to)
            self._merge_listbox.delete(idx)
            self._merge_listbox.insert(idx, text_from)
            self._merge_drag_start_idx = idx
            self._merge_listbox.selection_clear(0, tk.END)
            self._merge_listbox.selection_set(idx)

    def _merge_drag_release(self, event):
        self._merge_drag_start_idx = None

    def _start_merge(self):
        if len(self._merge_files) < 2:
            messagebox.showwarning("Aviso", "Adicione ao menos 2 PDFs para juntar.")
            return
        if self._merge_running:
            return

        if self._merge_same_dir.get():
            out_dir = os.path.dirname(self._merge_files[0])
            out_path = os.path.join(out_dir, "merged.pdf")
        else:
            out_path = filedialog.asksaveasfilename(
                title="Salvar PDF juntado como",
                defaultextension=".pdf",
                filetypes=[("Arquivo PDF", "*.pdf")],
                initialfile="merged.pdf",
            )
            if not out_path:
                return

        self._merge_running = True
        self.btn_merge.config(state="disabled")
        self._merge_pb.set(0)
        self._spinner = SpinnerWindow(self)
        self._spinner.start()
        threading.Thread(
            target=self._run_merge,
            args=(list(self._merge_files), out_path),
            daemon=True,
        ).start()

    def _run_merge(self, files, out_path):
        try:
            merger = PyPDF2.PdfMerger()
            try:
                total = len(files)
                for i, f in enumerate(files):
                    merger.append(f)
                    pct = (i + 1) / total * 100
                    self.after(0, lambda v=pct: self._merge_pb.set(v))
                    self.after(0, lambda n=i+1, tot=total: self._merge_status.set(
                        f"Processando... {n}/{tot}"))
                    self._spinner_status(os.path.basename(f))
                    self._spinner_page(i + 1, total)

                with open(out_path, "wb") as fh:
                    merger.write(fh)

                with open(out_path, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    n_pages = len(reader.pages)
                self.after(0, lambda: self._merge_status.set(
                    f"PDF gerado: {os.path.basename(out_path)}  ({n_pages} páginas)  →  {os.path.dirname(out_path)}"))
                self.after(0, lambda: self._merge_pb.set(100))
            finally:
                merger.close()
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro ao juntar", str(e)))
            self.after(0, lambda: self._merge_status.set("Erro ao juntar os PDFs."))
        finally:
            self._merge_running = False
            self.after(0, self._close_spinner)
            self.after(0, lambda: self.btn_merge.config(state="normal"))

    # ── Página Sobre ──────────────────────────────────────────

    def _build_about_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["about"] = page

        # ── Scrollable wrapper ────────────────────────────────────
        canvas = tk.Canvas(page, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        scroll_frame = tk.Frame(canvas, bg=C["bg"])

        scroll_frame.bind("<Configure>",
                          lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_win = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make inner frame follow canvas width
        def _resize_scroll(event):
            canvas.itemconfigure(canvas_win, width=event.width)
        canvas.bind("<Configure>", _resize_scroll)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-3, "units")
        def _on_linux_scroll_down(event):
            canvas.yview_scroll(3, "units")

        def _bind_wheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_linux_scroll_up)
            canvas.bind_all("<Button-5>", _on_linux_scroll_down)
        def _unbind_wheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # card info
        card = tk.Frame(scroll_frame, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.pack(fill="x", padx=24, pady=20)

        inner = tk.Frame(card, bg=C["panel"], padx=20, pady=18)
        inner.pack(fill="x")

        tk.Label(inner, text="PDF Tools",
                 font=("Segoe UI", 18, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")

        badge_f = tk.Frame(inner, bg=C["panel"])
        badge_f.pack(anchor="w", pady=(4, 0))
        tk.Label(badge_f, text=f"v{APP_VERSION}",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["accent"], fg="#0f172a",
                 padx=8, pady=2).pack(side="left")
        tk.Label(badge_f, text="  MIT License",
                 font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")

        tk.Label(inner,
                 text="Ferramenta completa para manipulação de PDFs.\n"
                      "Desenvolvido com Python, Tesseract e Tkinter.",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg"],
                 justify="left").pack(anchor="w", pady=(10, 8))

        # Grade de funcionalidades
        feats_f = tk.Frame(inner, bg=C["panel"])
        feats_f.pack(anchor="w", pady=(0, 10))
        _features = [
            ("⬡", "OCR",          "Converte PDFs escaneados em pesquisáveis,\n"
                                   "com destaque automático de nomes de pessoas."),
            ("⊜", "Comprimir",    "Reduz o tamanho de PDFs com opções de\n"
                                   "qualidade (100–250 DPI) e formato (JPEG/PNG)."),
            ("⊟", "Dividir PDF",  "Separa um PDF por intervalo único, múltiplos\n"
                                   "intervalos ou todas as páginas individualmente."),
            ("⊞", "Juntar PDF",   "Une múltiplos PDFs em ordem personalizável,\n"
                                   "com drag & drop e reordenação por ↑↓."),
        ]
        for icon, title, desc in _features:
            row_f = tk.Frame(feats_f, bg=C["panel"])
            row_f.pack(anchor="w", pady=(0, 8))
            tk.Label(row_f, text=icon,
                     font=("Segoe UI", 14), bg=C["panel"],
                     fg=C["accent"], width=3).pack(side="left", anchor="n")
            txt_f = tk.Frame(row_f, bg=C["panel"])
            txt_f.pack(side="left", anchor="w")
            tk.Label(txt_f, text=title,
                     font=("Segoe UI", 9, "bold"),
                     bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")
            tk.Label(txt_f, text=desc,
                     font=("Segoe UI", 8),
                     bg=C["panel"], fg=C["fg_dim"],
                     justify="left").pack(anchor="w")

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(4, 0))

        link_f = tk.Frame(inner, bg=C["panel"])
        link_f.pack(anchor="w", pady=(10, 0), fill="x")
        link = tk.Label(link_f,
                        text=f"github.com/{GITHUB_USER}/{GITHUB_REPO}",
                        font=("Segoe UI", 9, "underline"),
                        bg=C["panel"], fg=C["accent"], cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _: webbrowser.open(
            f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"))

        tk.Label(link_f, text=" · Autor: Nicolas Almeida Hader Dias",
                 font=("Segoe UI", 9), bg=C["panel"],
                 fg=C["fg_dim"]).pack(side="left")

        # card atualização
        upd_card = tk.Frame(scroll_frame, bg=C["panel"],
                            highlightthickness=1,
                            highlightbackground=C["border"])
        upd_card.pack(fill="x", padx=24)

        upd_inner = tk.Frame(upd_card, bg=C["panel"], padx=20, pady=16)
        upd_inner.pack(fill="x")

        tk.Label(upd_inner, text="Atualizações",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")

        chk_f = tk.Frame(upd_inner, bg=C["panel"])
        chk_f.pack(anchor="w", pady=(8, 0))
        ttk.Checkbutton(
            chk_f,
            text="Verificar atualizações automaticamente ao iniciar",
            variable=self.auto_update_var,
            style="TCheckbutton",
            command=self._save_prefs
        ).pack(side="left")

        status_f = tk.Frame(upd_inner, bg=C["panel"])
        status_f.pack(anchor="w", pady=(8, 0), fill="x")
        tk.Label(status_f, textvariable=self.update_status,
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(side="left")

        self.btn_update = _accent_btn(
            upd_inner, text="  Verificar atualização  ",
            command=self._check_update_manual,
            padx=14, pady=7
        )
        self.btn_update.pack(anchor="w", pady=(12, 0))

        # changelog section
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(12, 0))

        cl_inner = tk.Frame(inner, bg=C["panel"], pady=12)
        cl_inner.pack(fill="x")

        tk.Label(cl_inner, text=f"O que há de novo — v{APP_VERSION}",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")

        _changelog = [
            ("⊟", "Dividir PDF",
             "Separe um PDF em partes: intervalo único, múltiplos\n"
             "intervalos (campo de texto ou visual) ou todas as\n"
             "páginas individualmente."),
            ("⊞", "Juntar PDF",
             "Una múltiplos PDFs em um único arquivo. Reordene\n"
             "arrastando com o mouse ou usando os botões ↑↓.\n"
             "Suporte a drag & drop de arquivos do Explorer."),
            ("⚙", "Melhorias gerais",
             "Correções de layout, melhor gerenciamento de recursos\n"
             "e tratamento de erros aprimorado."),
        ]

        cl_f = tk.Frame(cl_inner, bg=C["panel"])
        cl_f.pack(anchor="w", pady=(10, 0))
        for icon, title, desc in _changelog:
            row_f = tk.Frame(cl_f, bg=C["panel"])
            row_f.pack(anchor="w", pady=(0, 8))
            tk.Label(row_f, text=icon,
                     font=("Segoe UI", 14), bg=C["panel"],
                     fg=C["accent"], width=3).pack(side="left", anchor="n")
            txt_f = tk.Frame(row_f, bg=C["panel"])
            txt_f.pack(side="left", anchor="w")
            tk.Label(txt_f, text=title,
                     font=("Segoe UI", 9, "bold"),
                     bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")
            tk.Label(txt_f, text=desc,
                     font=("Segoe UI", 8),
                     bg=C["panel"], fg=C["fg_dim"],
                     justify="left").pack(anchor="w")

        self.after(1500, self._auto_update_check)

    # ── Prefs ─────────────────────────────────────────────────

    def _prefs_path(self):
        base = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                               else os.path.abspath(__file__))
        return os.path.join(base, "pdf_ocr_prefs.json")

    def _load_prefs(self):
        try:
            with open(self._prefs_path()) as f:
                data = json.load(f)
            self.auto_update_var.set(data.get("auto_update", True))
            self.highlight_names_var.set(data.get("highlight_names", True))
            q = data.get("compress_quality")
            if q and any(p[0] == q for p in self._QUALITY_PRESETS):
                self.compress_quality.set(q)
            f = data.get("compress_format")
            if f and any(x[0] == f for x in self._IMG_FORMATS):
                self.compress_format.set(f)
        except Exception:
            pass

    def _save_prefs(self):
        try:
            with open(self._prefs_path(), "w") as fp:
                json.dump({
                    "auto_update":      self.auto_update_var.get(),
                    "highlight_names":  self.highlight_names_var.get(),
                    "compress_quality": self.compress_quality.get(),
                    "compress_format":  self.compress_format.get(),
                }, fp)
        except Exception:
            pass

    # ── Update ────────────────────────────────────────────────

    def _auto_update_check(self):
        if self.auto_update_var.get():
            threading.Thread(target=self._do_check_update,
                             args=(False,), daemon=True).start()

    def _check_update_manual(self):
        self.update_status.set("Verificando...")
        self.btn_update.config(state="disabled")
        threading.Thread(target=self._do_check_update,
                         args=(True,), daemon=True).start()

    def _do_check_update(self, manual):
        try:
            info    = fetch_latest_release()
            current = version_tuple(APP_VERSION)
            remote  = version_tuple(info["tag"])
            if remote > current:
                self.after(0, lambda: self.update_status.set(f"Nova versão v{info['tag']} disponível!"))
                self.after(0, lambda: UpdateDialog(self, info))
            else:
                msg = f"Você está na versão mais recente (v{APP_VERSION})"
                self.after(0, lambda: self.update_status.set(msg))
                if manual:
                    self.after(0, lambda: messagebox.showinfo("Atualização", msg))
        except Exception as e:
            msg = f"Não foi possível verificar: {e}"
            self.after(0, lambda: self.update_status.set(msg))
            if manual:
                self.after(0, lambda: messagebox.showwarning("Verificação de atualização", msg))
        finally:
            self.after(0, lambda: self.btn_update.config(state="normal"))

    # ── OCR eventos ───────────────────────────────────────────

    def _on_lang_select(self, _event):
        code = self.lang.get().split(" — ")[0]
        self.lang.set(code)

    def _ocr_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar PDFs para OCR",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        for p in paths:
            if p not in self.ocr_files:
                self.ocr_files.append(p)
                self.ocr_listbox.insert(tk.END, os.path.basename(p))
        self._update_ocr_count()

    def _ocr_remove_selected(self):
        sel = list(self.ocr_listbox.curselection())
        for idx in reversed(sel):
            self.ocr_listbox.delete(idx)
            del self.ocr_files[idx]
        self._update_ocr_count()

    def _browse_ocr_outdir(self):
        d = filedialog.askdirectory(title="Pasta de saída para PDFs com OCR")
        if d:
            self.ocr_outdir.set(d)

    def _update_ocr_count(self):
        n = len(self.ocr_files)
        self._ocr_count_lbl.config(
            text=f"({n} arquivo{'s' if n != 1 else ''})")

    def _clear(self):
        self.ocr_files.clear()
        self.ocr_listbox.delete(0, tk.END)
        self.pb.set(0)
        self.ocr_outdir.set("")
        self.status.set("Adicione PDFs para iniciar.")
        self._update_ocr_count()

    def _start(self):
        if not DEPS_OK:
            self._show_dep_error()
            return
        if not self.ocr_files:
            messagebox.showwarning("Aviso", "Adicione ao menos um PDF.")
            return
        if not check_tesseract():
            messagebox.showerror(
                "Tesseract não encontrado",
                "O Tesseract OCR não foi encontrado.\n\n"
                "Baixe e instale em:\nhttps://github.com/UB-Mannheim/tesseract/wiki"
            )
            return
        if self._running:
            return

        self._running = True
        self.btn_run.config(state="disabled")
        self._spinner = SpinnerWindow(self)
        self._spinner.start()

        lang_raw = self.lang.get()
        lang = lang_raw.split(" — ")[0] if " — " in lang_raw else lang_raw
        threading.Thread(
            target=self._run_ocr_batch,
            args=(list(self.ocr_files), self.ocr_outdir.get(),
                  lang, self.highlight_names_var.get()),
            daemon=True,
        ).start()

    # ── OCR core ──────────────────────────────────────────────

    def _run_ocr_batch(self, files, outdir, lang, highlight_names):
        total = len(files)
        ok_files, errors = [], []

        for fi, input_pdf in enumerate(files, 1):
            base = os.path.splitext(os.path.basename(input_pdf))[0]
            dest_dir = outdir if outdir else os.path.dirname(input_pdf)
            output_pdf = os.path.join(dest_dir, base + "_pesquisavel.pdf")
            try:
                self._run_ocr_single(
                    input_pdf, output_pdf, lang,
                    highlight_names, fi, total)
                ok_files.append(output_pdf)
            except Exception as e:
                errors.append(f"{os.path.basename(input_pdf)}: {e}")

        self.after(0, lambda: (self.progress_var.set(100), self.pb.set(100)))
        self.after(0, self._close_spinner)

        if errors:
            err_list = "\n".join(errors)
            self._set_status(f"Concluído com {len(errors)} erro(s).")
            self.after(0, lambda: messagebox.showwarning(
                "OCR concluído com erros",
                f"{len(ok_files)} arquivo(s) processado(s) com sucesso.\n\n"
                f"Erros:\n{err_list}"
            ))
        else:
            extra = " · nomes destacados" if highlight_names else ""
            self._set_status(
                f"Concluído! {total} arquivo(s) processado(s).{extra}")
            names_note = ("\n(nomes de pessoas destacados em amarelo)"
                          if highlight_names else "")
            listing = "\n".join(os.path.basename(p) for p in ok_files)
            self.after(0, lambda: messagebox.showinfo(
                "OCR concluído",
                f"{total} PDF(s) pesquisável(is) gerado(s)!\n\n"
                f"{listing}{names_note}\n\n"
                "Use CTRL+F no leitor de PDF para pesquisar."
            ))

        self._running = False
        self.after(0, lambda: self.btn_run.config(state="normal"))

    @staticmethod
    def _preprocess_for_ocr(pil_img):
        """Preprocessa imagem para melhorar precisão do OCR.

        Pipeline: grayscale → contraste → nitidez → binarização Otsu.
        Retorna imagem processada no mesmo tamanho da original.
        """
        # Converter para escala de cinza
        gray = pil_img.convert("L")

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.8)

        # Nitidez leve para realçar bordas de caracteres
        gray = gray.filter(ImageFilter.SHARPEN)

        # Binarização adaptativa via Otsu (simples com pillow):
        # Calcula threshold pelo histograma
        hist = gray.histogram()
        total = sum(hist)
        current = 0
        threshold = 128
        weight_bg = 0
        sum_bg = 0
        sum_total = sum(i * hist[i] for i in range(256))
        max_variance = 0
        for i in range(256):
            weight_bg += hist[i]
            if weight_bg == 0:
                continue
            weight_fg = total - weight_bg
            if weight_fg == 0:
                break
            sum_bg += i * hist[i]
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg
            variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
            if variance > max_variance:
                max_variance = variance
                threshold = i

        binary = gray.point(lambda p: 255 if p > threshold else 0)
        return binary

    def _run_ocr_single(self, input_pdf, output_pdf, lang,
                        highlight_names, fi, total_files):
        """Processa um único PDF. Levanta exceção em caso de erro."""
        poppler_path = find_poppler()

        # Count pages first (lightweight — no image conversion)
        with open(input_pdf, "rb") as fh:
            total_pages = len(PyPDF2.PdfReader(fh).pages)

        # Tesseract config: OEM 3 (best available), PSM 6 (block of text)
        tess_config = "--oem 3 --psm 6"

        merger = PyPDF2.PdfWriter()

        for pi in range(1, total_pages + 1):
            self._spinner_status(
                f"[{fi}/{total_files}] OCR — "
                f"{os.path.basename(input_pdf)}")
            self._spinner_page(pi, total_pages)
            self._set_status(
                f"[{fi}/{total_files}] {os.path.basename(input_pdf)} "
                f"— página {pi}/{total_pages}")

            # Convert one page at a time to save memory
            page_imgs = convert_from_path(
                input_pdf, dpi=300, poppler_path=poppler_path,
                first_page=pi, last_page=pi)
            pil_img = page_imgs[0]
            img_w, img_h = pil_img.size

            # Preprocessar imagem para melhorar OCR
            ocr_img = self._preprocess_for_ocr(pil_img)

            ocr_data = pytesseract.image_to_data(
                ocr_img, lang=lang,
                config=tess_config,
                output_type=pytesseract.Output.DICT)
            del ocr_img  # free preprocessed image

            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
            # Draw original (non-preprocessed) image for visual fidelity
            c.drawImage(ImageReader(pil_img), 0, 0,
                        width=img_w, height=img_h)
            del pil_img, page_imgs  # free memory immediately

            if highlight_names:
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

            # Invisible text layer — minimum confidence threshold 20
            c.setFillColorRGB(0, 0, 0, alpha=0)
            for j in range(len(ocr_data["text"])):
                word = ocr_data["text"][j]
                try:
                    conf = int(ocr_data["conf"][j])
                except (TypeError, ValueError):
                    conf = -1
                if not word or not word.strip() or conf < 20:
                    continue
                x, y = ocr_data["left"][j], ocr_data["top"][j]
                w, h = ocr_data["width"][j], ocr_data["height"][j]
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
            merger.add_page(PyPDF2.PdfReader(io.BytesIO(buf.getvalue())).pages[0])

            # Progresso global
            base_pct = (fi - 1) / total_files * 95
            page_pct = pi / total_pages * (95 / total_files)
            pct = base_pct + page_pct
            self.after(0, lambda p=pct: (
                self.progress_var.set(p), self.pb.set(p)))

        self._spinner_status(
            f"[{fi}/{total_files}] Gerando PDF...")
        with open(output_pdf, "wb") as f:
            merger.write(f)

    def _detect_names(self, ocr_data):
        """
        Retorna lista de (x, y, w, h) para sequências de nomes de pessoas detectadas.
        Heurística: 2+ palavras consecutivas na mesma linha começando com maiúscula,
        com comprimento mínimo de 2 caracteres e apenas letras/hífen.
        Conectores comuns em nomes (de, da, do, etc.) são permitidos no meio.
        """
        _CONNECTORS = frozenset({"de", "da", "do", "das", "dos", "e", "von", "van", "del", "di"})
        _SKIP = frozenset({"Rua", "Av", "Avenida", "Dr", "Prof", "Sr", "Sra", "Mês", "Janeiro",
                 "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
                 "Setembro", "Outubro", "Novembro", "Dezembro"})

        names = []
        n = len(ocr_data["text"])
        i = 0
        while i < n:
            word = ocr_data["text"][i]
            try:
                conf = int(ocr_data["conf"][i])
            except (TypeError, ValueError):
                conf = -1
            if not word or not word.strip() or conf <= 0:
                i += 1
                continue
            # Palavra candidata a início de nome: começa com maiúscula, só letras/hífen, ≥2 chars
            clean = word.replace("-", "")
            if (word[0].isupper() and len(word) >= 2 and clean.isalpha()
                    and word not in _SKIP):
                group = [i]
                j = i + 1
                while j < n:
                    nw = ocr_data["text"][j]
                    try:
                        nc = int(ocr_data["conf"][j])
                    except (TypeError, ValueError):
                        nc = -1
                    # Mesma linha e mesmo bloco
                    same_line = (
                        ocr_data["line_num"][j] == ocr_data["line_num"][i]
                        and ocr_data["block_num"][j] == ocr_data["block_num"][i]
                    )
                    if not same_line:
                        break
                    if not nw or not nw.strip():
                        j += 1
                        continue
                    nw_clean = nw.replace("-", "")
                    if nw.lower() in _CONNECTORS:
                        group.append(j)
                        j += 1
                        continue
                    if (nw[0].isupper() and len(nw) >= 2
                            and nw_clean.isalpha() and nc > 0
                            and nw not in _SKIP):
                        group.append(j)
                        j += 1
                    else:
                        break
                # Conta palavras reais (sem conectores)
                real = [k for k in group
                        if ocr_data["text"][k].lower() not in _CONNECTORS]
                if len(real) >= 2:
                    xs  = [ocr_data["left"][k] for k in group]
                    ys  = [ocr_data["top"][k]  for k in group]
                    x2s = [ocr_data["left"][k] + ocr_data["width"][k]  for k in group]
                    y2s = [ocr_data["top"][k]  + ocr_data["height"][k] for k in group]
                    names.append((min(xs), min(ys),
                                  max(x2s) - min(xs),
                                  max(y2s) - min(ys)))
                i = j
            else:
                i += 1
        return names

    def _spinner_status(self, msg):
        sp = self._spinner
        if sp:
            self.after(0, lambda: sp.set_status(msg) if sp._running else None)

    def _spinner_page(self, current, total):
        sp = self._spinner
        if sp:
            self.after(0, lambda: sp.set_page(current, total) if sp._running else None)

    def _close_spinner(self):
        if self._spinner:
            try:
                self._spinner.stop()
            except Exception:
                pass
            self._spinner = None

    def _set_status(self, msg):
        self.after(0, lambda: self.status.set(msg))

    def _show_dep_error(self):
        missing = MISSING_DEP if not DEPS_OK else "dependência desconhecida"
        messagebox.showerror(
            "Dependências faltando",
            f"Biblioteca não instalada: {missing}\n\n"
            "Execute:\npip install pytesseract pillow pdf2image reportlab PyPDF2"
        )


if __name__ == "__main__":
    splash = SplashScreen()
    splash.mainloop()
    app = PDFOcrApp()
    app.mainloop()
