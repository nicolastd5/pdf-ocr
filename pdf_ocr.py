"""
PDF OCR v0.9
Converte PDFs escaneados em PDFs pesquisáveis com OCR.
Repositório: https://github.com/nicolastd5/pdf-ocr
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import json
import webbrowser
import urllib.request
import urllib.error
import tempfile
import subprocess
import shutil

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    import reportlab.pdfgen.canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    import PyPDF2
    import io
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    MISSING_DEP = str(e)

APP_VERSION = "0.9.1"
GITHUB_USER = "nicolastd5"
GITHUB_REPO = "pdf-ocr"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"


# ─────────────────────────────────────────────────────────────
#  Paleta VS Code Dark
# ─────────────────────────────────────────────────────────────
C = {
    "bg":        "#1e1e1e",
    "panel":     "#252526",
    "sidebar":   "#333333",
    "input":     "#3c3c3c",
    "hover":     "#2a2d2e",
    "border":    "#454545",
    "accent":    "#4fc3f7",
    "accent_dk": "#0288d1",
    "fg":        "#d4d4d4",
    "fg_dim":    "#858585",
    "fg_bright": "#ffffff",
    "success":   "#4ec9b0",
    "warn":      "#dcdcaa",
    "error":     "#f44747",
    "sel":       "#094771",
}


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


def fetch_latest_release():
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"pdf-ocr/{APP_VERSION}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
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
    """Aplica estilo dark num tk.Entry."""
    e.configure(
        bg=C["input"], fg=C["fg"],
        insertbackground=C["fg"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
        readonlybackground=C["input"],
        disabledbackground=C["input"],
        disabledforeground=C["fg_dim"],
    )


def _flat_btn(parent, text, command, fg=None, bg=None, font=None, **kw):
    fg   = fg   or C["fg"]
    bg   = bg   or C["hover"]
    font = font or ("Segoe UI", 9)
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=C["sel"],
        activeforeground=C["fg_bright"],
        relief="flat", bd=0, cursor="hand2",
        font=font, **kw
    )
    btn.bind("<Enter>", lambda _: btn.config(bg=C["sel"] if bg == C["hover"] else C["accent_dk"]))
    btn.bind("<Leave>", lambda _: btn.config(bg=bg))
    return btn


def _accent_btn(parent, text, command, font=None, **kw):
    font = font or ("Segoe UI", 10, "bold")
    btn = tk.Button(
        parent, text=text, command=command,
        bg=C["accent"], fg=C["bg"],
        activebackground=C["accent_dk"], activeforeground=C["fg_bright"],
        relief="flat", bd=0, cursor="hand2",
        font=font, **kw
    )
    btn.bind("<Enter>", lambda _: btn.config(bg=C["accent_dk"]) if str(btn.cget("state")) != "disabled" else None)
    btn.bind("<Leave>", lambda _: btn.config(bg=C["accent"]) if str(btn.cget("state")) != "disabled" else None)
    return btn


class CanvasProgressBar(tk.Canvas):
    """Barra de progresso customizada desenhada em Canvas."""

    def __init__(self, parent, **kw):
        kw.setdefault("height", 6)
        kw.setdefault("bg", C["panel"])
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, **kw)
        self._value = 0
        self.bind("<Configure>", self._redraw)

    def set(self, value):
        self._value = max(0.0, min(100.0, value))
        self._redraw()

    def _redraw(self, *_):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        self.delete("all")
        r = min(3, h // 2)
        # track
        self._rounded_rect(0, 0, w, h, r, fill=C["input"], outline="")
        # fill
        fill_w = int(w * self._value / 100)
        if fill_w > r:
            self._rounded_rect(0, 0, fill_w, h, r, fill=C["accent"], outline="")

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
    _ARC_SPAN  = 280
    _SPEED     = 6
    _INTERVAL  = 16
    _RADIUS    = 44
    _THICKNESS = 8

    def __init__(self, parent):
        super().__init__(parent)
        self.title("")
        self.resizable(False, False)
        self.configure(bg=C["panel"])
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._angle    = 0
        self._running  = False
        self._after_id = None
        self.status_var = tk.StringVar(value="Iniciando OCR...")
        self.page_var   = tk.StringVar(value="")
        self._build()
        self._center(parent)
        self.grab_set()

    def _build(self):
        # borda sutil
        outer = tk.Frame(self, bg=C["border"], padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=C["panel"], padx=36, pady=32)
        inner.pack()

        tk.Label(inner, text="Processando OCR",
                 font=("Segoe UI", 12, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(pady=(0, 16))

        size = self._RADIUS * 2 + self._THICKNESS * 2 + 4
        self._canvas = tk.Canvas(inner, width=size, height=size,
                                 bg=C["panel"], highlightthickness=0)
        self._canvas.pack()
        cx = cy = size // 2
        r, t = self._RADIUS, self._THICKNESS
        self._canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                 outline=C["input"], width=t)
        self._arc = self._canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=90, extent=-self._ARC_SPAN,
            outline=C["accent"], width=t, style="arc"
        )

        tk.Label(inner, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=C["panel"], fg=C["fg"],
                 wraplength=260, justify="center").pack(pady=(14, 2))
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
        self._angle = (self._angle + self._SPEED) % 360
        self._canvas.itemconfigure(self._arc, start=90 - self._angle)
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

        # progresso
        self._prog_frame = tk.Frame(root, bg=C["panel"], padx=24, pady=8)
        self._prog_frame.pack(fill="x")
        self._prog_label = tk.Label(self._prog_frame, text="",
                                    font=("Segoe UI", 8),
                                    bg=C["panel"], fg=C["fg_dim"])
        self._prog_label.pack(anchor="w")
        self._prog_bar = CanvasProgressBar(self._prog_frame, width=420)
        self._prog_bar.pack(fill="x", pady=(4, 0))
        self._prog_frame.pack_forget()

        # botões
        self._btn_row = tk.Frame(root, bg=C["panel"], padx=24, pady=16)
        self._btn_row.pack(fill="x")
        self._btn_update = _accent_btn(
            self._btn_row,
            text="  Atualizar agora  ",
            command=self._start_download,
            padx=16, pady=8
        )
        self._btn_update.pack(side="left", padx=(0, 10))
        _flat_btn(
            self._btn_row, text="Agora não",
            command=self._dismiss,
            padx=12, pady=8
        ).pack(side="left")

        self._center(self._parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_reqwidth())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    def _dismiss(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _start_download(self):
        exe_url = self._info.get("exe_url")
        if not exe_url:
            messagebox.showwarning(
                "Sem executável",
                "Esta release não possui um .exe para download.\n\n"
                "Acesse manualmente:\n" + self._info.get("html_url", GITHUB_RELEASES_PAGE),
                parent=self
            )
            return
        self._btn_update.config(state="disabled", text="  Baixando...  ")
        self._prog_frame.pack(fill="x", before=self._btn_row, padx=0, pady=(0, 4))
        threading.Thread(target=self._download_and_apply,
                         args=(exe_url,), daemon=True).start()

    def _download_and_apply(self, url):
        try:
            tmp_dir = tempfile.mkdtemp(prefix="pdfocr_update_")
            tmp_exe = os.path.join(tmp_dir, "PDF_OCR_new.exe")
            req = urllib.request.Request(url, headers={"User-Agent": f"pdf-ocr/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=300) as resp:
                total      = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk      = 65536
                with open(tmp_exe, "wb") as f:
                    while True:
                        data = resp.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)
                        if total > 0:
                            pct      = downloaded / total * 100
                            mb_done  = downloaded / 1_048_576
                            mb_total = total      / 1_048_576
                            self.after(0, lambda p=pct, d=mb_done, t=mb_total:
                                       self._update_progress(p, d, t))
            self.after(0, lambda: self._apply_update(tmp_exe))
        except Exception as e:
            self.after(0, lambda: self._download_failed(str(e)))

    def _update_progress(self, pct, mb_done, mb_total):
        self._prog_bar.set(pct)
        self._prog_label.config(
            text=f"Baixando...  {mb_done:.1f} MB / {mb_total:.1f} MB  ({pct:.0f}%)"
        )

    def _apply_update(self, new_exe):
        current_exe = sys.executable if getattr(sys, "frozen", False) else None
        if current_exe and os.path.isfile(current_exe):
            pid     = os.getpid()
            bat_path = os.path.join(tempfile.gettempdir(), "pdfocr_update.bat")
            old_exe  = current_exe + ".old"
            with open(bat_path, "w") as f:
                f.write(f"""@echo off
:wait
tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul
if not errorlevel 1 (
    ping 127.0.0.1 -n 2 > nul
    goto wait
)
ping 127.0.0.1 -n 3 > nul
if exist "{old_exe}" del /F /Q "{old_exe}"
rename "{current_exe}" "{os.path.basename(old_exe)}"
if errorlevel 1 (
    msg * "PDF OCR: falha ao renomear executável. Copie manualmente: {new_exe}"
    goto :eof
)
move /Y "{new_exe}" "{current_exe}"
if errorlevel 1 (
    rename "{old_exe}" "{os.path.basename(current_exe)}"
    msg * "PDF OCR: falha ao instalar atualização. Copie manualmente: {new_exe}"
    goto :eof
)
del /F /Q "{old_exe}" 2>nul
start "" "{current_exe}"
del "%~f0"
""")
            self._prog_label.config(text="Instalando atualização...")
            self.after(400, lambda: self._launch_bat_and_quit(bat_path))
        else:
            self._prog_label.config(text="Download concluído!")
            self.after(0, lambda: messagebox.showinfo(
                "Download concluído",
                f"Novo executável salvo em:\n{new_exe}\n\nSubstitua manualmente o arquivo atual.",
                parent=self
            ))

    def _launch_bat_and_quit(self, bat_path):
        subprocess.Popen(["cmd", "/c", bat_path],
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         close_fds=True)
        self._parent.quit()

    def _download_failed(self, msg):
        self._btn_update.config(state="normal", text="  Atualizar agora  ")
        self._prog_label.config(text=f"Erro: {msg}")
        messagebox.showerror("Falha no download", msg, parent=self)


# ─────────────────────────────────────────────────────────────
#  Main App
# ─────────────────────────────────────────────────────────────

class PDFOcrApp(tk.Tk):

    # ícones unicode para a sidebar
    _NAV = [
        ("ocr",   "⬡", "OCR"),
        ("about", "ℹ", "Sobre"),
    ]

    def __init__(self):
        super().__init__()
        self.title(f"PDF OCR  v{APP_VERSION}")
        self.geometry("740x520")
        self.minsize(740, 520)
        self.resizable(True, False)
        self.configure(bg=C["bg"])

        self.input_path         = tk.StringVar()
        self.output_path        = tk.StringVar()
        self.lang               = tk.StringVar(value="por")
        self.status             = tk.StringVar(value="Aguardando arquivo...")
        self.progress_var       = tk.DoubleVar(value=0)
        self.auto_update_var    = tk.BooleanVar(value=True)
        self.update_status      = tk.StringVar(value="")
        self.highlight_names_var = tk.BooleanVar(value=True)
        self.compress_var       = tk.BooleanVar(value=False)
        self._running        = False
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
                     arrowcolor=C["fg_dim"],
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
                     arrowcolor=C["fg_dim"])
        s.configure("TCheckbutton",
                     background=C["panel"],
                     foreground=C["fg"],
                     focuscolor=C["panel"])
        s.map("TCheckbutton",
              background=[("active", C["panel"])],
              foreground=[("active", C["fg_bright"])])

    # ── Layout principal ──────────────────────────────────────

    def _build_ui(self):
        # sidebar
        self._sidebar = tk.Frame(self, bg=C["sidebar"], width=56)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # cabeçalho da sidebar
        tk.Label(self._sidebar, text="⬡",
                 font=("Segoe UI", 18), bg=C["sidebar"],
                 fg=C["accent"]).pack(pady=(18, 2))
        tk.Frame(self._sidebar, bg=C["border"], height=1).pack(fill="x", padx=8, pady=6)

        # botões de navegação
        self._nav_btns = {}
        self._nav_active_key = None
        for key, icon, label in self._NAV:
            f = tk.Frame(self._sidebar, bg=C["sidebar"])
            f.pack(fill="x")
            btn = tk.Button(
                f, text=icon,
                font=("Segoe UI", 16),
                bg=C["sidebar"], fg=C["fg_dim"],
                activebackground=C["hover"],
                activeforeground=C["accent"],
                relief="flat", bd=0, cursor="hand2",
                width=3, pady=10,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn, k=key: b.config(fg=C["fg"]) if k != self._nav_active_key else None)
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(fg=C["fg_dim"]) if k != self._nav_active_key else None)
            self._nav_btns[key] = btn

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
        self._build_about_page()

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
            if k == key:
                btn.config(fg=C["accent"], bg=C["hover"])
            else:
                btn.config(fg=C["fg_dim"], bg=C["sidebar"])

        titles = {
            "ocr":   ("OCR",   "Converta PDFs escaneados em PDFs pesquisáveis"),
            "about": ("Sobre", f"PDF OCR  v{APP_VERSION}"),
        }
        t, s = titles[key]
        self._page_title.config(text=t)
        self._page_sub.config(text=s)

    # ── Página OCR ────────────────────────────────────────────

    def _build_ocr_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["ocr"] = page

        # card principal
        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.pack(fill="x", padx=24, pady=20)

        def row(label, var, browse_cmd, btn_text):
            f = tk.Frame(card, bg=C["panel"])
            f.pack(fill="x", padx=16, pady=(12, 0))
            tk.Label(f, text=label, width=13, anchor="w",
                     font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
            e = tk.Entry(f, textvariable=var, state="readonly",
                         font=("Segoe UI", 9), width=46)
            _style_entry(e)
            e.pack(side="left", ipady=5, padx=(0, 8))
            _flat_btn(f, text=btn_text, command=browse_cmd,
                      padx=10, pady=4).pack(side="left")

        row("PDF de entrada", self.input_path,  self._browse_input,  "Abrir")
        row("PDF de saída",   self.output_path, self._browse_output, "Salvar")

        # idioma
        lang_f = tk.Frame(card, bg=C["panel"])
        lang_f.pack(fill="x", padx=16, pady=(12, 16))
        tk.Label(lang_f, text="Idioma OCR", width=13, anchor="w",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
        lang_combo = ttk.Combobox(lang_f, textvariable=self.lang,
                                  width=30, state="readonly",
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
        lang_combo.pack(side="left", ipady=4)
        lang_combo.bind("<<ComboboxSelected>>", self._on_lang_select)

        # opções extras
        opts_f = tk.Frame(card, bg=C["panel"])
        opts_f.pack(fill="x", padx=16, pady=(4, 16))
        ttk.Checkbutton(
            opts_f,
            text="Destacar nomes de pessoas no PDF",
            variable=self.highlight_names_var,
            style="TCheckbutton",
            command=self._save_prefs
        ).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(
            opts_f,
            text="Comprimir PDF",
            variable=self.compress_var,
            style="TCheckbutton",
            command=self._save_prefs
        ).pack(side="left")

        # status + barra de progresso
        status_f = tk.Frame(page, bg=C["bg"])
        status_f.pack(fill="x", padx=24, pady=(4, 6))
        tk.Label(status_f, textvariable=self.status,
                 font=("Segoe UI", 9), bg=C["bg"], fg=C["fg_dim"],
                 anchor="w").pack(fill="x")

        self.pb = CanvasProgressBar(page, height=6)
        self.pb.pack(fill="x", padx=24, pady=(0, 16))

        # botões de ação
        btn_f = tk.Frame(page, bg=C["bg"])
        btn_f.pack(fill="x", padx=24)
        self.btn_run = _accent_btn(
            btn_f, text="  ▶  Iniciar OCR  ",
            command=self._start,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9
        )
        self.btn_run.pack(side="left", padx=(0, 10))
        _flat_btn(btn_f, text="Limpar",
                  command=self._clear,
                  padx=14, pady=9).pack(side="left")

    # ── Página Sobre ──────────────────────────────────────────

    def _build_about_page(self):
        page = tk.Frame(self._pages, bg=C["bg"])
        self._page_frames["about"] = page

        # card info
        card = tk.Frame(page, bg=C["panel"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.pack(fill="x", padx=24, pady=20)

        inner = tk.Frame(card, bg=C["panel"], padx=20, pady=18)
        inner.pack(fill="x")

        tk.Label(inner, text=f"PDF OCR",
                 font=("Segoe UI", 18, "bold"),
                 bg=C["panel"], fg=C["fg_bright"]).pack(anchor="w")

        badge_f = tk.Frame(inner, bg=C["panel"])
        badge_f.pack(anchor="w", pady=(4, 0))
        tk.Label(badge_f, text=f"v{APP_VERSION}",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["accent_dk"], fg=C["fg_bright"],
                 padx=8, pady=2).pack(side="left")
        tk.Label(badge_f, text="  MIT License",
                 font=("Segoe UI", 9),
                 bg=C["panel"], fg=C["fg_dim"]).pack(side="left")

        tk.Label(inner,
                 text="Converte PDFs escaneados em PDFs pesquisáveis usando OCR.\n"
                      "Desenvolvido com Python, Tesseract e Tkinter.",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg"],
                 justify="left").pack(anchor="w", pady=(10, 8))

        link = tk.Label(inner,
                        text=f"github.com/{GITHUB_USER}/{GITHUB_REPO}",
                        font=("Segoe UI", 9, "underline"),
                        bg=C["panel"], fg=C["accent"], cursor="hand2")
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda _: webbrowser.open(
            f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"))

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(14, 0))

        tk.Label(inner,
                 text="Autor: Nicolas Almeida Hader Dias",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(anchor="w", pady=(10, 0))

        # card atualização
        upd_card = tk.Frame(page, bg=C["panel"],
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
            self.compress_var.set(data.get("compress_pdf", False))
        except Exception:
            pass

    def _save_prefs(self):
        try:
            with open(self._prefs_path(), "w") as f:
                json.dump({
                    "auto_update": self.auto_update_var.get(),
                    "highlight_names": self.highlight_names_var.get(),
                    "compress_pdf": self.compress_var.get(),
                }, f)
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

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        if path:
            self.input_path.set(path)
            self.output_path.set(os.path.splitext(path)[0] + "_pesquisavel.pdf")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Salvar PDF pesquisável",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if path:
            self.output_path.set(path)

    def _clear(self):
        self.input_path.set("")
        self.output_path.set("")
        self.progress_var.set(0)
        self.pb.set(0)
        self.status.set("Aguardando arquivo...")

    def _start(self):
        if not DEPS_OK:
            self._show_dep_error()
            return
        if not self.input_path.get():
            messagebox.showwarning("Aviso", "Selecione um PDF de entrada.")
            return
        if not self.output_path.get():
            messagebox.showwarning("Aviso", "Defina o caminho do PDF de saída.")
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
            target=self._run_ocr,
            args=(self.input_path.get(), self.output_path.get(), lang,
                  self.highlight_names_var.get(), self.compress_var.get()),
            daemon=True
        ).start()

    # ── OCR core ──────────────────────────────────────────────

    def _detect_names(self, ocr_data):
        """
        Retorna lista de (x, y, w, h) para sequências de nomes de pessoas detectadas.
        Heurística: 2+ palavras consecutivas na mesma linha começando com maiúscula,
        com comprimento mínimo de 2 caracteres e apenas letras/hífen.
        Conectores comuns em nomes (de, da, do, etc.) são permitidos no meio.
        """
        _CONNECTORS = {"de", "da", "do", "das", "dos", "e", "von", "van", "del", "di"}
        _SKIP = {"Rua", "Av", "Avenida", "Dr", "Prof", "Sr", "Sra", "Mês", "Janeiro",
                 "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
                 "Setembro", "Outubro", "Novembro", "Dezembro"}

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

    def _run_ocr(self, input_pdf, output_pdf, lang,
                 highlight_names=True, compress=False):
        try:
            self._spinner_status("Convertendo páginas para imagem...")
            poppler_path = find_poppler()
            pages = convert_from_path(input_pdf, dpi=300, poppler_path=poppler_path)
            total = len(pages)
            page_buffers = []

            for i, pil_img in enumerate(pages, 1):
                self._spinner_status("Aplicando OCR...")
                self._spinner_page(i, total)
                self._set_status(f"OCR página {i} / {total}...")

                ocr_data = pytesseract.image_to_data(
                    pil_img, lang=lang, output_type=pytesseract.Output.DICT)
                img_w, img_h = pil_img.size

                # Compressão: converte imagem para JPEG antes de embutir no PDF
                if compress:
                    _cbuf = io.BytesIO()
                    pil_img.convert("RGB").save(_cbuf, format="JPEG",
                                                quality=60, optimize=True)
                    _cbuf.seek(0)
                    img_to_draw = Image.open(_cbuf)
                else:
                    img_to_draw = pil_img

                buf = io.BytesIO()
                c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
                c.drawImage(ImageReader(img_to_draw), 0, 0, width=img_w, height=img_h)

                # Destaque de nomes de pessoas (retângulo âmbar semi-transparente)
                if highlight_names:
                    self._spinner_status("Detectando nomes de pessoas...")
                    name_boxes = self._detect_names(ocr_data)
                    if name_boxes:
                        c.saveState()
                        c.setFillColorRGB(1.0, 0.85, 0.0, alpha=0.35)
                        for nx, ny, nw, nh in name_boxes:
                            pad = 2
                            c.rect(nx - pad,
                                   img_h - ny - nh - pad,
                                   nw + pad * 2,
                                   nh + pad * 2,
                                   fill=1, stroke=0)
                        c.restoreState()

                # Camada de texto invisível (pesquisável)
                c.setFillColorRGB(0, 0, 0, alpha=0)
                for j in range(len(ocr_data["text"])):
                    word = ocr_data["text"][j]
                    try:
                        conf = int(ocr_data["conf"][j])
                    except (TypeError, ValueError):
                        conf = -1
                    if not word or not word.strip() or conf <= 0:
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
                page_buffers.append(buf.getvalue())
                pct = i / total * 95
                self.after(0, lambda p=pct: (self.progress_var.set(p), self.pb.set(p)))

            self._spinner_status("Gerando PDF final...")
            self._set_status("Gerando PDF final...")
            merger = PyPDF2.PdfWriter()
            for pb in page_buffers:
                merger.add_page(PyPDF2.PdfReader(io.BytesIO(pb)).pages[0])
            with open(output_pdf, "wb") as f:
                merger.write(f)

            self.after(0, lambda: (self.progress_var.set(100), self.pb.set(100)))
            self._set_status(f"Concluído! {os.path.basename(output_pdf)}")
            self.after(0, self._close_spinner)
            extras = []
            if highlight_names:
                extras.append("nomes destacados em amarelo")
            if compress:
                extras.append("PDF comprimido")
            extra_msg = f"\n({', '.join(extras)})" if extras else ""
            self.after(0, lambda: messagebox.showinfo(
                "Sucesso",
                f"PDF pesquisável gerado!\n\n{output_pdf}{extra_msg}\n\n"
                "Use CTRL+F no seu leitor de PDF para pesquisar."
            ))
        except Exception as e:
            self.after(0, self._close_spinner)
            self.after(0, lambda: messagebox.showerror("Erro durante OCR", str(e)))
            self._set_status(f"Erro: {e}")
        finally:
            self._running = False
            self.after(0, lambda: self.btn_run.config(state="normal"))

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
    app = PDFOcrApp()
    app.mainloop()
