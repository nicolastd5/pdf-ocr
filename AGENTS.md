# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## Commands

```bash
# Run the app directly (requires Tesseract + Poppler installed locally)
python -m pdf_ocr_qt.main

# Install Python dependencies
pip install -r requirements.txt

# Build EXE (requires deps/tesseract/ and deps/poppler/bin/ populated first)
pyinstaller pdf_ocr.spec

# Trigger a GitHub Actions release build manually
gh workflow run build.yml --field tag=vX.Y.Z
```

There are no automated tests. Validation is done by running the app and exercising the UI manually.

## Architecture

The application is a PyQt6 desktop app in the `pdf_ocr_qt/` package. Entry point is `pdf_ocr_qt/main.py`.

**File structure:**

```
pdf_ocr_qt/
  main.py       — MainWindow, helpers (check_tesseract, find_poppler, fetch_latest_release), entry point
  styles.py     — QSS stylesheet, color dict C, nav_btn() factory
  ner.py        — NERPipeline (spaCy + OpenAI), Entity dataclass, SpacyNotInstalledError
  workers.py    — QThread subclasses: OcrWorker, CompressWorker, WordWorker, SplitWorker, MergeWorker
  pages/
    ocr.py      — OCR page (file list, language selector, NER toggle, output dir)
    compress.py — PDF compression page
    word.py     — PDF → Word conversion page
    split.py    — PDF split page
    merge.py    — PDF merge page (drag-and-drop reorder)
    about.py    — About/changelog page
  widgets/
    spinner.py       — AnimatedSpinner widget
    progress.py      — CanvasProgressBar widget
    spacy_install.py — SpacyInstallDialog (install spaCy in-app)
```

**Class structure:**

- `MainWindow(QMainWindow)` — main window, sidebar nav, QStackedWidget page container
  - `_build_ui()`: creates sidebar with nav buttons and stacks all page widgets
  - `_navigate(key)`: switches active page and highlights nav button
  - `_load_prefs()` / `_save_prefs()`: JSON prefs at `pdf_ocr_prefs.json`

- Each page is a `QWidget` subclass imported from `pdf_ocr_qt/pages/`
- Long operations run in `QThread` workers from `pdf_ocr_qt/workers.py`, emitting signals back to the UI

**Six pages:**

| Key | File | Worker class |
|---|---|---|
| `ocr` | `pages/ocr.py` | `OcrWorker` |
| `compress` | `pages/compress.py` | `CompressWorker` |
| `word` | `pages/word.py` | `WordWorker` |
| `split` | `pages/split.py` | `SplitWorker` |
| `merge` | `pages/merge.py` | `MergeWorker` |
| `about` | `pages/about.py` | — |

## Key Patterns

**Threading:** All long operations run in `QThread` workers. Workers emit `progress(current, total, status)` and `finished(ok_files, errors)` signals. Never update widgets directly from a worker thread — use signals.

**NER (AI name detection):** `NERPipeline` in `ner.py` supports two engines:
- `"spacy"` — uses `pt_core_news_lg` model (bundled in EXE via `_MEIPASS`)
- `"openai"` — uses OpenAI API with user-provided key

**File handles:** Always use `with open(path, "rb") as fh: PyPDF2.PdfReader(fh)` — Windows locks open file handles.

**Color palette:** All colors come from the `C` dict in `styles.py`. Never hardcode color values. Primary accent is `C["accent"]` (#2dd4bf teal).

**Preferences:** Stored as JSON at `pdf_ocr_prefs.json` (same dir as executable or script dir in dev). Keys: `auto_update`, `highlight_names`, `compress_quality`, `compress_format`, `use_ner`, `use_openai`, `openai_key`, `ner_engine`.

**Bundled binaries (EXE only):** `_bundled_bin(name)` in `main.py` resolves paths inside `sys._MEIPASS`. Tesseract at `_MEIPASS/tesseract.exe`, Poppler at `_MEIPASS/poppler/bin/`, spaCy model at `_MEIPASS/pt_core_news_lg`.

## CI/CD

`.github/workflows/build.yml` triggers on `v*` tag pushes and manually via `workflow_dispatch` (with a `tag` input field). It:
1. Installs Python deps including `spacy`
2. Downloads `pt_core_news_lg` spaCy model
3. Installs Tesseract and Poppler via Chocolatey
4. Copies binaries to `deps/tesseract/` and `deps/poppler/bin/`
5. Runs `pyinstaller pdf_ocr.spec` → produces `dist/PDF_Tools.exe`
6. Creates a GitHub Release with the EXE (only when `tag` input is provided or push is a `v*` tag)

**To publish a release via tag push:** commit all changes → `git tag vX.Y.Z` → `git push origin master && git push origin vX.Y.Z`

**To publish manually (without a tag):** `gh workflow run build.yml --field tag=vX.Y.Z`
