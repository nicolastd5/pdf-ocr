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

APP_VERSION          = "1.0.8"
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

        # Carregar prefs nas páginas que as suportam
        ocr_page = self._pages["ocr"]
        if hasattr(ocr_page, "load_prefs"):
            ocr_page.load_prefs(self._prefs)

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
        # Garantir chaves NER com defaults
        self._prefs.setdefault("use_ner",    False)
        self._prefs.setdefault("use_openai", False)
        self._prefs.setdefault("openai_key", "")
        self._prefs.setdefault("ner_engine", "spacy")

    def _save_prefs(self):
        try:
            with open(_prefs_path(), "w") as f:
                json.dump(self._prefs, f)
        except Exception:
            pass

    def closeEvent(self, event):
        ocr_page = self._pages.get("ocr")
        if ocr_page and hasattr(ocr_page, "save_prefs"):
            ocr_page.save_prefs(self._prefs)
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
