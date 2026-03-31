# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app directly (requires Tesseract + Poppler installed locally)
python pdf_ocr.py

# Install Python dependencies
pip install -r requirements.txt

# Syntax check (the file uses UTF-8 characters)
python -c "import ast; ast.parse(open('pdf_ocr.py', encoding='utf-8').read()); print('OK')"

# Build EXE (requires deps/tesseract/ and deps/poppler/bin/ populated first)
pyinstaller pdf_ocr.spec
```

There are no automated tests. Validation is done by running the app and exercising the UI manually.

## Architecture

The entire application lives in a single file: `pdf_ocr.py`. There are no modules, no packages, no separate files beyond the PyInstaller spec.

**Class structure:**

- `App(tk.Tk)` — the main window and all application logic (~2300 lines)
  - `__init__`: initialises all state variables for all four tools, then calls `_apply_ttk_style()` → `_build_ui()` → `_load_prefs()` → `_show_page("ocr")`
  - `_build_ui()`: creates the sidebar navigation and a `self._pages` frame container, then calls all four `_build_*_page()` methods
  - `_show_page(key)`: pack/pack_forget pattern — only one page visible at a time, stored in `self._page_frames` dict

- `SpinnerDialog` — modal progress dialog used during long operations
- `UpdateDialog` — modal dialog for auto-update download/apply
- `SmoothProgressBar` — custom canvas-based progress bar widget

**Module-level helpers:** `check_tesseract()`, `find_poppler()`, `_bundled_bin()`, `fetch_latest_release()`, `_flat_btn()`, `_accent_btn()`, `_style_entry()`

**Four pages, each self-contained:**

| Key | Build method | State prefix | Core logic methods |
|---|---|---|---|
| `ocr` | `_build_ocr_page` | `self.ocr_*`, `self._running` | `_run_ocr_batch`, `_run_ocr_single`, `_detect_names` |
| `compress` | `_build_compress_page` | `self.compress_*`, `self._compress_running` | `_run_compress_batch`, `_run_compress_single` |
| `split` | `_build_split_page` | `self._split_*` | `_run_split`, `_parse_split_intervals` |
| `merge` | `_build_merge_page` | `self._merge_*` | `_run_merge`, `_merge_drag_*` |

## Key Patterns

**Threading:** All long operations run in `threading.Thread(daemon=True)`. UI updates from background threads always go through `self.after(0, lambda: ...)`. Never touch widgets directly from a worker thread.

**File handles:** Always use `with open(path, "rb") as fh: PyPDF2.PdfReader(fh)` — Windows locks open file handles, so reader objects must not outlive the `with` block.

**UI layout:** Pages use `grid` with `page.columnconfigure(0, weight=1)` and `page.rowconfigure(0, weight=1)` so the card expands to fill the frame. Inner scrollable areas additionally need `card.rowconfigure(1, weight=1)` for the list to grow.

**Color palette:** All colors come from the `C` dict (VS Code Dark theme). Never hardcode color values — always use `C["key"]`.

**Button factories:** Use `_flat_btn()` for secondary actions and `_accent_btn()` for primary CTAs. Do not use `ttk.Button` directly in page layouts.

**Preferences:** Stored as JSON at `%APPDATA%\PDFTools\prefs.json` via `_load_prefs()` / `_save_prefs()`. Only OCR output dir, compress output dir, language, and auto-update toggle are persisted.

**Bundled binaries (EXE only):** When frozen by PyInstaller, `sys._MEIPASS` is the extraction dir. `_bundled_bin(name)` resolves paths inside it. Tesseract lives at `sys._MEIPASS/tesseract.exe`, Poppler at `sys._MEIPASS/poppler/bin/`.

## CI/CD

`.github/workflows/build.yml` triggers on `v*` tags and `master` pushes. It:
1. Installs Tesseract and Poppler via Chocolatey
2. Copies binaries to `deps/tesseract/` and `deps/poppler/bin/`
3. Runs `pyinstaller pdf_ocr.spec` → produces `dist/PDF_Tools.exe`
4. Creates a GitHub Release (only on tag pushes, not branch pushes)

To publish a release: commit all changes → `git tag vX.Y.Z` → `git push origin master && git push origin vX.Y.Z`.
