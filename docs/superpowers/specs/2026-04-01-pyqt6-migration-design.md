# PDF Tools — PyQt6 Migration Design

**Goal:** Migrar a UI do PDF Tools de Tkinter para PyQt6, mantendo toda a lógica de OCR/PDF intacta.

**Approach:** Migração direta (Abordagem A) — reescrever só a UI, copiar a lógica dos `_run_*` para QThread workers com mínimas alterações.

---

## Estrutura de Arquivos

```
pdf_ocr_qt/
  main.py          ← QApplication, splash screen, MainWindow com sidebar
  styles.py        ← paleta C{} + QSS global (Ocean/Teal)
  workers.py       ← QThread subclasses para cada operação
  pages/
    ocr.py         ← OcrPage (QWidget)
    compress.py    ← CompressPage (QWidget)
    word.py        ← WordPage (QWidget)
    split.py       ← SplitPage (QWidget)
    merge.py       ← MergePage (QWidget)
    about.py       ← AboutPage (QWidget)
  widgets/
    spinner.py     ← SpinnerDialog (QDialog modal animado)
    progress.py    ← GradientProgressBar (QProgressBar estilizado)
```

---

## Workers (workers.py)

Cada operação vira uma subclasse de `QThread` com signals padronizados:

```python
class OcrWorker(QThread):
    progress = pyqtSignal(int, int, str)  # current, total, status
    finished = pyqtSignal()
    error    = pyqtSignal(str)

class CompressWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error    = pyqtSignal(str)

class WordWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error    = pyqtSignal(str)

class SplitWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error    = pyqtSignal(str)

class MergeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error    = pyqtSignal(str)
```

O corpo do `run()` de cada worker é o código dos métodos `_run_*_batch` do `pdf_ocr.py` original, com as únicas mudanças:
- `self.after(0, lambda: ...)` → `self.progress.emit(current, total, status)`
- Remoção de referências a widgets Tkinter

---

## MainWindow (main.py)

- Sidebar fixa (180px) com `QPushButton` para cada aba
- `QStackedWidget` para troca de páginas
- Navegação por `setCurrentWidget()` + highlight do botão ativo
- Janela: 1200x850, mínimo 1000x700

---

## Tema (styles.py)

Paleta Ocean/Teal centralizada no dict `C{}` — igual ao app atual.
QSS global aplicado via `app.setStyleSheet(QSS)` no startup.
Funções helper: `flat_btn(text)`, `accent_btn(text)` retornam `QPushButton` já estilizado.

---

## Drag & Drop

Nativo PyQt6 via `dragEnterEvent` + `dropEvent` em cada página.
Sem dependência externa (elimina `tkinterdnd2`).
Aceita `text/uri-list` com filtro `.pdf`.

---

## Spinner (widgets/spinner.py)

`SpinnerDialog(QDialog)` modal, sem bordas, fundo semitransparente.
Dois círculos orbitais animados via `QTimer` + `QPainter`.
Métodos: `show(status)`, `hide()`, `set_status(msg)`, `set_page(current, total)`.

---

## Progresso (widgets/progress.py)

`GradientProgressBar(QProgressBar)` com gradiente teal→sky via QSS.
Altura fixa 6px, sem texto visível.

---

## Splash Screen

`QSplashScreen` simples mostrado enquanto imports pesados carregam em background thread.
Substituí o `SplashScreen(tk.Tk)` atual.

---

## Preferências

Mantém o mesmo `pdf_ocr_prefs.json` no mesmo local.
Mesmas chaves: `auto_update`, `highlight_names`, `compress_quality`, `compress_format`.

---

## CI/CD

Sem alterações. PyInstaller + GitHub Actions existente continua funcionando.
Adicionar `PyQt6` no `requirements.txt` e no `pip install` do workflow.
Remover `tkinterdnd2`.

---

## O que NÃO muda

- Toda a lógica de OCR (`pytesseract`, `pdf2image`, name detection)
- Toda a lógica de compress, split, merge, word (`PyPDF2`, `pdf2docx`, `reportlab`, `Pillow`)
- `check_tesseract()`, `find_poppler()`, `_bundled_bin()`
- `fetch_latest_release()` e `UpdateDialog` (reescrito em PyQt6)
- `APP_VERSION`, `GITHUB_RELEASES_PAGE`
- Lógica de preferências (`_load_prefs`, `_save_prefs`)
