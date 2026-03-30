"""
PDF OCR v0.3
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

APP_VERSION = "0.4"
GITHUB_USER = "nicolastd5"
GITHUB_REPO = "pdf-ocr"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"


# ─────────────────────────────────────────────────────────────
#  Tesseract / Poppler helpers
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
    else:
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
    """Retorna dict com tag, body (changelog) e download_url do .exe."""
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"pdf-ocr/{APP_VERSION}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    tag = data.get("tag_name", "").lstrip("v")
    body = data.get("body", "Sem notas de versão.").strip()
    html_url = data.get("html_url", GITHUB_RELEASES_PAGE)

    # Procura o asset .exe
    exe_url = None
    for asset in data.get("assets", []):
        if asset["name"].lower().endswith(".exe"):
            exe_url = asset["browser_download_url"]
            break

    return {"tag": tag, "body": body, "exe_url": exe_url, "html_url": html_url}


# ─────────────────────────────────────────────────────────────
#  Spinner
# ─────────────────────────────────────────────────────────────

class SpinnerWindow(tk.Toplevel):
    _ARC_SPAN = 280
    _SPEED    = 6
    _INTERVAL = 16
    _RADIUS   = 48
    _THICKNESS = 9
    _BG       = "#1a1a2e"
    _FG_ARC   = "#4fc3f7"
    _FG_TRACK = "#2e2e4e"
    _FG_TEXT  = "#ffffff"
    _FG_SUB   = "#aaaacc"

    def __init__(self, parent):
        super().__init__(parent)
        self.title("")
        self.resizable(False, False)
        self.configure(bg=self._BG)
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
        outer = tk.Frame(self, bg=self._BG, padx=32, pady=32)
        outer.pack()
        tk.Label(outer, text="Processando OCR",
                 font=("Segoe UI", 13, "bold"),
                 bg=self._BG, fg=self._FG_TEXT).pack(pady=(0, 18))
        size = self._RADIUS * 2 + self._THICKNESS * 2 + 4
        self._canvas = tk.Canvas(outer, width=size, height=size,
                                 bg=self._BG, highlightthickness=0)
        self._canvas.pack()
        cx = cy = size // 2
        r, t = self._RADIUS, self._THICKNESS
        self._canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                 outline=self._FG_TRACK, width=t)
        self._arc = self._canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=90, extent=-self._ARC_SPAN,
            outline=self._FG_ARC, width=t, style="arc"
        )
        tk.Label(outer, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=self._BG, fg=self._FG_TEXT,
                 wraplength=260, justify="center").pack(pady=(16, 2))
        tk.Label(outer, textvariable=self.page_var,
                 font=("Segoe UI", 9), bg=self._BG, fg=self._FG_SUB).pack()

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
#  Update Dialog  (changelog + download automático)
# ─────────────────────────────────────────────────────────────

class UpdateDialog(tk.Toplevel):
    """Janela que mostra changelog e baixa + aplica o update automaticamente."""

    _BG      = "#1a1a2e"
    _BG2     = "#14142a"
    _FG      = "#ffffff"
    _FG_SUB  = "#aaaacc"
    _ACCENT  = "#4fc3f7"
    _BTN_BG  = "#4fc3f7"
    _BTN_FG  = "#1a1a2e"

    def __init__(self, parent, release_info):
        super().__init__(parent)
        self._info    = release_info
        self._parent  = parent
        self.title("Atualização disponível")
        self.resizable(False, False)
        self.configure(bg=self._BG)
        self.attributes("-topmost", True)
        self._build()
        self._center(parent)
        self.grab_set()

    def _build(self):
        tag  = self._info["tag"]
        body = self._info["body"]

        # Cabeçalho
        hdr = tk.Frame(self, bg=self._BG, padx=28, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Nova versão disponível!",
                 font=("Segoe UI", 14, "bold"),
                 bg=self._BG, fg=self._FG).pack(anchor="w")
        tk.Label(hdr, text=f"v{APP_VERSION}  →  v{tag}",
                 font=("Segoe UI", 10), bg=self._BG, fg=self._ACCENT).pack(anchor="w", pady=(2, 0))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=0)

        # Changelog
        body_frame = tk.Frame(self, bg=self._BG2, padx=20, pady=14)
        body_frame.pack(fill="both", expand=True, padx=0)
        tk.Label(body_frame, text="O que há de novo:",
                 font=("Segoe UI", 9, "bold"),
                 bg=self._BG2, fg=self._FG_SUB).pack(anchor="w", pady=(0, 6))

        txt = tk.Text(body_frame, height=10, width=52,
                      bg=self._BG2, fg=self._FG,
                      relief="flat", font=("Segoe UI", 9),
                      wrap="word", state="normal",
                      highlightthickness=0, bd=0)
        txt.insert("1.0", body)
        txt.config(state="disabled")
        sb = ttk.Scrollbar(body_frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Progresso (oculto até o download iniciar)
        self._prog_frame = tk.Frame(self, bg=self._BG, padx=28, pady=8)
        self._prog_frame.pack(fill="x")
        self._prog_label = tk.Label(self._prog_frame, text="",
                                    font=("Segoe UI", 8),
                                    bg=self._BG, fg=self._FG_SUB)
        self._prog_label.pack(anchor="w")
        self._prog_bar = ttk.Progressbar(self._prog_frame, length=400,
                                         mode="determinate", maximum=100)
        self._prog_bar.pack(fill="x", pady=(2, 0))
        self._prog_frame.pack_forget()   # escondido por padrão

        # Botões
        self._btn_row = tk.Frame(self, bg=self._BG, padx=28, pady=16)
        btn_row = self._btn_row
        btn_row.pack(fill="x")
        self._btn_update = tk.Button(
            btn_row,
            text="Sim, atualizar agora",
            font=("Segoe UI", 10, "bold"),
            bg=self._BTN_BG, fg=self._BTN_FG,
            activebackground="#81d4fa", activeforeground=self._BTN_FG,
            relief="flat", padx=16, pady=8,
            command=self._start_download
        )
        self._btn_update.pack(side="left", padx=(0, 10))
        tk.Button(
            btn_row, text="Agora não",
            font=("Segoe UI", 10), bg=self._BG, fg=self._FG_SUB,
            activebackground="#2e2e4e", activeforeground=self._FG,
            relief="flat", padx=12, pady=8,
            command=self.destroy
        ).pack(side="left")

        self._center(self._parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_reqwidth())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Download + aplicação ──────────────────────────────────

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

        self._btn_update.config(state="disabled", text="Baixando...")
        self._prog_frame.pack(fill="x", before=self._btn_row, padx=28, pady=(0, 4))
        threading.Thread(target=self._download_and_apply,
                         args=(exe_url,), daemon=True).start()

    def _download_and_apply(self, url):
        try:
            # Baixa para temp
            tmp_dir  = tempfile.mkdtemp(prefix="pdfocr_update_")
            tmp_exe  = os.path.join(tmp_dir, "PDF_OCR_new.exe")

            req = urllib.request.Request(url, headers={"User-Agent": f"pdf-ocr/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 65536
                with open(tmp_exe, "wb") as f:
                    while True:
                        data = resp.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)
                        if total > 0:
                            pct = downloaded / total * 100
                            mb_done  = downloaded / 1_048_576
                            mb_total = total      / 1_048_576
                            self.after(0, lambda p=pct, d=mb_done, t=mb_total:
                                       self._update_progress(p, d, t))

            self.after(0, lambda: self._apply_update(tmp_exe))

        except Exception as e:
            self.after(0, lambda: self._download_failed(str(e)))

    def _update_progress(self, pct, mb_done, mb_total):
        self._prog_bar["value"] = pct
        self._prog_label.config(
            text=f"Baixando... {mb_done:.1f} MB / {mb_total:.1f} MB  ({pct:.0f}%)"
        )

    def _apply_update(self, new_exe):
        """Substitui o executável atual e reinicia."""
        current_exe = sys.executable if getattr(sys, "frozen", False) else None

        if current_exe and os.path.isfile(current_exe):
            # Cria script .bat que: espera o processo atual fechar, copia o novo exe e reinicia
            bat_path = os.path.join(tempfile.gettempdir(), "pdfocr_update.bat")
            with open(bat_path, "w") as f:
                f.write(f"""@echo off
ping 127.0.0.1 -n 6 > nul
copy /Y "{new_exe}" "{current_exe}"
if errorlevel 1 (
    echo Falha ao copiar o executavel. Tente manualmente.
    pause
    goto :eof
)
start "" "{current_exe}"
del "%~f0"
""")
            self._prog_label.config(text="Instalando atualização...")
            self.after(400, lambda: self._launch_bat_and_quit(bat_path))
        else:
            # Modo dev: apenas abre a pasta com o novo exe
            self._prog_label.config(text="Download concluído!")
            self.after(0, lambda: messagebox.showinfo(
                "Download concluído",
                f"Novo executável salvo em:\n{new_exe}\n\n"
                "Substitua manualmente o arquivo atual.",
                parent=self
            ))

    def _launch_bat_and_quit(self, bat_path):
        subprocess.Popen(["cmd", "/c", bat_path],
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         close_fds=True)
        self._parent.quit()

    def _download_failed(self, msg):
        self._btn_update.config(state="normal", text="Sim, atualizar agora")
        self._prog_label.config(text=f"Erro: {msg}")
        messagebox.showerror("Falha no download", msg, parent=self)


# ─────────────────────────────────────────────────────────────
#  Main App
# ─────────────────────────────────────────────────────────────

class PDFOcrApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"PDF OCR v{APP_VERSION}")
        self.geometry("640x460")
        self.resizable(False, False)
        self.configure(bg="#f5f5f5")

        self.input_path   = tk.StringVar()
        self.output_path  = tk.StringVar()
        self.lang         = tk.StringVar(value="por")
        self.status       = tk.StringVar(value="Aguardando arquivo...")
        self.progress_var = tk.DoubleVar(value=0)
        self._running     = False
        self._spinner     = None

        self._build_ui()

        if not DEPS_OK:
            self._show_dep_error()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_ocr   = tk.Frame(nb, bg="#f5f5f5")
        self.tab_about = tk.Frame(nb, bg="#f5f5f5")
        nb.add(self.tab_ocr,   text="  OCR  ")
        nb.add(self.tab_about, text="  Sobre  ")
        self._build_ocr_tab()
        self._build_about_tab()

    # ── Aba OCR ───────────────────────────────────────────────

    def _build_ocr_tab(self):
        pad = {"padx": 16, "pady": 6}
        f = self.tab_ocr

        tk.Label(f, text="PDF OCR", font=("Segoe UI", 16, "bold"),
                 bg="#f5f5f5", fg="#1a1a2e").pack(pady=(16, 2))
        tk.Label(f, text="Converte PDF escaneado em PDF com texto pesquisável",
                 font=("Segoe UI", 9), bg="#f5f5f5", fg="#555").pack(pady=(0, 10))

        frame_in = tk.Frame(f, bg="#f5f5f5")
        frame_in.pack(fill="x", **pad)
        tk.Label(frame_in, text="PDF de entrada:", width=14, anchor="w",
                 bg="#f5f5f5").pack(side="left")
        tk.Entry(frame_in, textvariable=self.input_path, width=44,
                 state="readonly").pack(side="left", padx=(0, 6))
        tk.Button(frame_in, text="Abrir", command=self._browse_input,
                  width=8).pack(side="left")

        frame_out = tk.Frame(f, bg="#f5f5f5")
        frame_out.pack(fill="x", **pad)
        tk.Label(frame_out, text="PDF de saída:", width=14, anchor="w",
                 bg="#f5f5f5").pack(side="left")
        tk.Entry(frame_out, textvariable=self.output_path, width=44,
                 state="readonly").pack(side="left", padx=(0, 6))
        tk.Button(frame_out, text="Salvar", command=self._browse_output,
                  width=8).pack(side="left")

        frame_lang = tk.Frame(f, bg="#f5f5f5")
        frame_lang.pack(fill="x", **pad)
        tk.Label(frame_lang, text="Idioma OCR:", width=14, anchor="w",
                 bg="#f5f5f5").pack(side="left")
        lang_combo = ttk.Combobox(frame_lang, textvariable=self.lang,
                                  width=26, state="readonly")
        lang_combo["values"] = [
            "por — Português",
            "eng — Inglês",
            "por+eng — Português + Inglês",
            "spa — Espanhol",
            "fra — Francês",
            "deu — Alemão",
        ]
        lang_combo.current(0)
        lang_combo.pack(side="left")
        lang_combo.bind("<<ComboboxSelected>>", self._on_lang_select)

        tk.Label(f, textvariable=self.status, font=("Segoe UI", 9),
                 bg="#f5f5f5", fg="#444").pack(pady=(14, 2))
        self.pb = ttk.Progressbar(f, variable=self.progress_var,
                                  maximum=100, length=580)
        self.pb.pack(padx=16)

        frame_btn = tk.Frame(f, bg="#f5f5f5")
        frame_btn.pack(pady=14)
        self.btn_run = tk.Button(
            frame_btn, text="▶  Iniciar OCR",
            font=("Segoe UI", 10, "bold"),
            bg="#1a1a2e", fg="white",
            activebackground="#333", activeforeground="white",
            relief="flat", padx=18, pady=8,
            command=self._start
        )
        self.btn_run.pack(side="left", padx=8)
        tk.Button(frame_btn, text="Limpar", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=8,
                  command=self._clear).pack(side="left", padx=8)

    # ── Aba Sobre ─────────────────────────────────────────────

    def _build_about_tab(self):
        f = self.tab_about

        tk.Label(f, text="PDF OCR", font=("Segoe UI", 20, "bold"),
                 bg="#f5f5f5", fg="#1a1a2e").pack(pady=(24, 4))
        tk.Label(f, text=f"Versão {APP_VERSION}",
                 font=("Segoe UI", 11), bg="#f5f5f5", fg="#555").pack()
        tk.Label(f,
                 text="Converte PDFs escaneados em PDFs pesquisáveis usando OCR.\n"
                      "Desenvolvido com Python, Tesseract e Tkinter.",
                 font=("Segoe UI", 9), bg="#f5f5f5", fg="#444",
                 justify="center").pack(pady=(10, 4))

        link = tk.Label(f, text=f"github.com/{GITHUB_USER}/{GITHUB_REPO}",
                        font=("Segoe UI", 9, "underline"),
                        bg="#f5f5f5", fg="#0066cc", cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda _: webbrowser.open(
            f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"))

        ttk.Separator(f, orient="horizontal").pack(fill="x", padx=40, pady=18)

        self.auto_update_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            f,
            text="Verificar atualizações automaticamente ao iniciar",
            variable=self.auto_update_var,
            bg="#f5f5f5", font=("Segoe UI", 9),
            command=self._save_prefs
        ).pack()

        self.update_status = tk.StringVar(value="")
        tk.Label(f, textvariable=self.update_status,
                 font=("Segoe UI", 9), bg="#f5f5f5", fg="#555").pack(pady=(6, 0))

        self.btn_update = tk.Button(
            f, text="🔄  Verificar Atualização",
            font=("Segoe UI", 10),
            bg="#1a1a2e", fg="white",
            activebackground="#333", activeforeground="white",
            relief="flat", padx=16, pady=7,
            command=self._check_update_manual
        )
        self.btn_update.pack(pady=(10, 0))

        tk.Label(f,
                 text="© 2025 Nicolas Almeida Hader Dias  •  MIT License",
                 font=("Segoe UI", 8), bg="#f5f5f5", fg="#aaa").pack(
            side="bottom", pady=12)

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
        except Exception:
            pass

    def _save_prefs(self):
        try:
            with open(self._prefs_path(), "w") as f:
                json.dump({"auto_update": self.auto_update_var.get()}, f)
        except Exception:
            pass

    # ── Update ────────────────────────────────────────────────

    def _auto_update_check(self):
        self._load_prefs()
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
                self.after(0, lambda: self.update_status.set(
                    f"Nova versão v{info['tag']} disponível!"))
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
                self.after(0, lambda: messagebox.showwarning(
                    "Verificação de atualização", msg))
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
                "Baixe e instale em:\n"
                "https://github.com/UB-Mannheim/tesseract/wiki"
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
            args=(self.input_path.get(), self.output_path.get(), lang),
            daemon=True
        ).start()

    # ── OCR core ──────────────────────────────────────────────

    def _run_ocr(self, input_pdf, output_pdf, lang):
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
                buf = io.BytesIO()
                c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
                c.drawImage(ImageReader(pil_img), 0, 0, width=img_w, height=img_h)
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
                self.progress_var.set(i / total * 95)

            self._spinner_status("Gerando PDF final...")
            self._set_status("Gerando PDF final...")
            merger = PyPDF2.PdfWriter()
            for pb in page_buffers:
                merger.add_page(PyPDF2.PdfReader(io.BytesIO(pb)).pages[0])
            with open(output_pdf, "wb") as f:
                merger.write(f)

            self.progress_var.set(100)
            self._set_status(f"Concluído! {os.path.basename(output_pdf)}")
            self.after(0, self._close_spinner)
            self.after(0, lambda: messagebox.showinfo(
                "Sucesso",
                f"PDF pesquisável gerado!\n\n{output_pdf}\n\n"
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
        if self._spinner:
            self.after(0, lambda: self._spinner.set_status(msg))

    def _spinner_page(self, current, total):
        if self._spinner:
            self.after(0, lambda: self._spinner.set_page(current, total))

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
