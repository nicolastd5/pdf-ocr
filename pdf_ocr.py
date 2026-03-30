"""
PDF OCR v0.1
Converte PDFs escaneados em PDFs pesquisáveis com OCR.
Repositório: https://github.com/nicol/pdf-ocr
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import json
import webbrowser

try:
    import urllib.request
    import urllib.error
    URLLIB_OK = True
except ImportError:
    URLLIB_OK = False

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

APP_VERSION = "0.1"
GITHUB_USER = "nicolastd5"
GITHUB_REPO = "pdf-ocr"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"


# ─────────────────────────────────────────────────────────────
#  Tesseract / Poppler helpers
# ─────────────────────────────────────────────────────────────

def check_tesseract():
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
    import shutil
    if shutil.which("pdftoppm"):
        return None
    common = [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler-24\Library\bin",
        r"C:\poppler\bin",
        r"C:\poppler\Library\bin",
    ]
    for p in common:
        if os.path.isdir(p):
            return p
    return None


# ─────────────────────────────────────────────────────────────
#  Update checker
# ─────────────────────────────────────────────────────────────

def fetch_latest_release():
    """Retorna (tag_str, url_release) ou lança exceção."""
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"pdf-ocr/{APP_VERSION}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    tag = data.get("tag_name", "").lstrip("v")
    url = data.get("html_url", GITHUB_RELEASES_PAGE)
    return tag, url


def version_tuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0,)


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

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.lang = tk.StringVar(value="por")
        self.status = tk.StringVar(value="Aguardando arquivo...")
        self.progress_var = tk.DoubleVar(value=0)
        self._running = False

        self._build_ui()

        if not DEPS_OK:
            self._show_dep_error()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_ocr = tk.Frame(nb, bg="#f5f5f5")
        self.tab_about = tk.Frame(nb, bg="#f5f5f5")

        nb.add(self.tab_ocr, text="  OCR  ")
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

        # Entrada
        frame_in = tk.Frame(f, bg="#f5f5f5")
        frame_in.pack(fill="x", **pad)
        tk.Label(frame_in, text="PDF de entrada:", width=14, anchor="w",
                 bg="#f5f5f5").pack(side="left")
        tk.Entry(frame_in, textvariable=self.input_path, width=44,
                 state="readonly").pack(side="left", padx=(0, 6))
        tk.Button(frame_in, text="Abrir", command=self._browse_input,
                  width=8).pack(side="left")

        # Saída
        frame_out = tk.Frame(f, bg="#f5f5f5")
        frame_out.pack(fill="x", **pad)
        tk.Label(frame_out, text="PDF de saída:", width=14, anchor="w",
                 bg="#f5f5f5").pack(side="left")
        tk.Entry(frame_out, textvariable=self.output_path, width=44,
                 state="readonly").pack(side="left", padx=(0, 6))
        tk.Button(frame_out, text="Salvar", command=self._browse_output,
                  width=8).pack(side="left")

        # Idioma
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

        # Status / Progress
        tk.Label(f, textvariable=self.status, font=("Segoe UI", 9),
                 bg="#f5f5f5", fg="#444").pack(pady=(14, 2))
        self.pb = ttk.Progressbar(f, variable=self.progress_var,
                                  maximum=100, length=580)
        self.pb.pack(padx=16)

        # Botões
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

        # Auto-update toggle
        self.auto_update_var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            f,
            text="Verificar atualizações automaticamente ao iniciar",
            variable=self.auto_update_var,
            bg="#f5f5f5", font=("Segoe UI", 9),
            command=self._save_prefs
        )
        chk.pack()

        # Status update
        self.update_status = tk.StringVar(value="")
        tk.Label(f, textvariable=self.update_status,
                 font=("Segoe UI", 9), bg="#f5f5f5", fg="#555").pack(pady=(6, 0))

        # Botão Update
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
                 text=f"© 2025 {GITHUB_USER}  •  MIT License",
                 font=("Segoe UI", 8), bg="#f5f5f5", fg="#aaa").pack(
            side="bottom", pady=12)

        # Verificação automática ao iniciar
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
            latest, url = fetch_latest_release()
            current = version_tuple(APP_VERSION)
            remote = version_tuple(latest)

            if remote > current:
                msg = f"Nova versão disponível: v{latest}"
                self.after(0, lambda: self.update_status.set(msg))
                if manual:
                    self.after(0, lambda: self._prompt_update(latest, url))
                else:
                    self.after(0, lambda: self._notify_update(latest, url))
            else:
                msg = f"Você está na versão mais recente (v{APP_VERSION})"
                if manual:
                    self.after(0, lambda: self.update_status.set(msg))
                    self.after(0, lambda: messagebox.showinfo(
                        "Atualização", msg))
                else:
                    self.after(0, lambda: self.update_status.set(msg))
        except Exception as e:
            msg = f"Não foi possível verificar: {e}"
            if manual:
                self.after(0, lambda: self.update_status.set(msg))
                self.after(0, lambda: messagebox.showwarning(
                    "Verificação de atualização", msg))
            else:
                self.after(0, lambda: self.update_status.set(msg))
        finally:
            self.after(0, lambda: self.btn_update.config(state="normal"))

    def _prompt_update(self, latest, url):
        if messagebox.askyesno(
            "Atualização disponível",
            f"Nova versão v{latest} disponível!\n\n"
            "Deseja abrir a página de download?"
        ):
            webbrowser.open(url)

    def _notify_update(self, latest, url):
        self.update_status.set(
            f"⬆ Nova versão v{latest} disponível! Acesse a aba Sobre.")

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
            stem = os.path.splitext(path)[0]
            self.output_path.set(stem + "_pesquisavel.pdf")

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
                "https://github.com/UB-Mannheim/tesseract/wiki\n\n"
                "Após instalar, reinicie o programa."
            )
            return
        if self._running:
            return
        self._running = True
        self.btn_run.config(state="disabled")
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
            self._set_status("Convertendo páginas para imagem...")
            poppler_path = find_poppler()
            pages = convert_from_path(input_pdf, dpi=300,
                                      poppler_path=poppler_path)
            total = len(pages)
            page_buffers = []

            for i, pil_img in enumerate(pages, 1):
                self._set_status(f"OCR página {i} / {total}...")
                ocr_data = pytesseract.image_to_data(
                    pil_img, lang=lang,
                    output_type=pytesseract.Output.DICT
                )
                img_w, img_h = pil_img.size
                buf = io.BytesIO()
                c = rl_canvas.Canvas(buf, pagesize=(img_w, img_h))
                img_reader = ImageReader(pil_img)
                c.drawImage(img_reader, 0, 0, width=img_w, height=img_h)
                c.setFillColorRGB(0, 0, 0, alpha=0)
                for j in range(len(ocr_data["text"])):
                    word = ocr_data["text"][j]
                    conf = int(ocr_data["conf"][j])
                    if not word.strip() or conf < 0:
                        continue
                    x = ocr_data["left"][j]
                    y = ocr_data["top"][j]
                    w = ocr_data["width"][j]
                    h = ocr_data["height"][j]
                    if h <= 0 or w <= 0:
                        continue
                    pdf_y = img_h - y - h
                    font_size = max(h * 0.85, 1)
                    try:
                        c.setFont("Helvetica", font_size)
                        text_w = c.stringWidth(word, "Helvetica", font_size)
                        scale_x = w / text_w if text_w > 0 else 1
                        c.saveState()
                        c.transform(scale_x, 0, 0, 1, x, pdf_y)
                        c.drawString(0, 0, word)
                        c.restoreState()
                    except Exception:
                        pass
                c.save()
                page_buffers.append(buf.getvalue())
                self.progress_var.set(i / total * 95)

            self._set_status("Gerando PDF final...")
            merger = PyPDF2.PdfWriter()
            for pb in page_buffers:
                reader = PyPDF2.PdfReader(io.BytesIO(pb))
                merger.add_page(reader.pages[0])
            with open(output_pdf, "wb") as f:
                merger.write(f)

            self.progress_var.set(100)
            self._set_status(
                f"Concluído! Salvo em: {os.path.basename(output_pdf)}")
            self.after(0, lambda: messagebox.showinfo(
                "Sucesso",
                f"PDF pesquisável gerado com sucesso!\n\n{output_pdf}\n\n"
                "Use CTRL+F no seu leitor de PDF para pesquisar."
            ))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Erro durante OCR", str(e)))
            self._set_status(f"Erro: {e}")
        finally:
            self._running = False
            self.after(0, lambda: self.btn_run.config(state="normal"))

    def _set_status(self, msg):
        self.after(0, lambda: self.status.set(msg))

    def _show_dep_error(self):
        messagebox.showerror(
            "Dependências faltando",
            f"Biblioteca não instalada: {MISSING_DEP}\n\n"
            "Execute:\n"
            "pip install pytesseract pillow pdf2image reportlab PyPDF2\n\n"
            "Também instale:\n"
            "• Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "• Poppler: https://github.com/oschwartz10612/poppler-windows/releases"
        )


if __name__ == "__main__":
    app = PDFOcrApp()
    app.mainloop()
