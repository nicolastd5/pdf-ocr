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

# Trigger a GitHub Actions release build manually
gh workflow run build.yml --field tag=vX.Y.Z
```

There are no automated tests. Validation is done by running the app and exercising the UI manually.

## Architecture

The entire application lives in a single file: `pdf_ocr.py`. There are no modules, no packages, no separate files beyond the PyInstaller spec.

**Class structure:**

- `PDFOcrApp(TkinterDnD.Tk | tk.Tk)` — the main window and all application logic (~2400 lines)
  - `__init__`: initialises all state variables for all four tools, then calls `_apply_ttk_style()` → `_build_ui()` → `_load_prefs()` → `_show_page("ocr")`
  - `_build_ui()`: creates the expandable sidebar and a `self._pages` frame container, then calls all four `_build_*_page()` methods
  - `_show_page(key)`: pack/pack_forget pattern — only one page visible at a time, stored in `self._page_frames` dict

- `SplashScreen(tk.Tk)` — startup splash shown while heavy deps load in background
- `SpinnerWindow(tk.Toplevel)` — dual-orbital animated modal shown during all long operations
- `UpdateDialog(tk.Toplevel)` — modal that shows new version info and opens the release page in browser
- `CanvasProgressBar(tk.Canvas)` — gradient-animated progress bar widget used on every page

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

**Spinner:** All four processing operations use the same pattern — create `SpinnerWindow`, call `.start()`, update via `self._spinner_status(msg)` and `self._spinner_page(current, total)`, then close via `self._close_spinner()` in the `finally` block.

**File handles:** Always use `with open(path, "rb") as fh: PyPDF2.PdfReader(fh)` — Windows locks open file handles, so reader objects must not outlive the `with` block.

**UI layout:** Pages use `grid` with `page.columnconfigure(0, weight=1)` and `page.rowconfigure(0, weight=1)` so the card expands to fill the frame. Inner scrollable areas additionally need `card.rowconfigure(1, weight=1)` for the list to grow.

**Color palette:** All colors come from the `C` dict (Ocean/Teal theme, `#1e1e1e` background). Never hardcode color values — always use `C["key"]`. Primary accent is `C["accent"]` (#2dd4bf teal), secondary is `C["accent2"]` (#38bdf8 sky blue).

**Button factories:** Use `_flat_btn()` for secondary actions and `_accent_btn()` for primary CTAs. Do not use `ttk.Button` directly in page layouts.

**Drag & drop:** `PDFOcrApp` inherits from `TkinterDnD.Tk` when `tkinterdnd2` is available (checked via `_HAS_DND`), falling back to `tk.Tk`. Always guard drop registrations with `if _HAS_DND:`.

**Preferences:** Stored as JSON at `pdf_ocr_prefs.json` (same dir as the executable, or script dir in dev) via `_load_prefs()` / `_save_prefs()`. Persists: `auto_update`, `highlight_names`, `compress_quality`, `compress_format`.

**Bundled binaries (EXE only):** When frozen by PyInstaller, `sys._MEIPASS` is the extraction dir. `_bundled_bin(name)` resolves paths inside it. Tesseract lives at `sys._MEIPASS/tesseract.exe`, Poppler at `sys._MEIPASS/poppler/bin/`.

## CI/CD

`.github/workflows/build.yml` triggers on `v*` tag pushes and manually via `workflow_dispatch` (with a `tag` input field). It:
1. Installs Python deps including `tkinterdnd2`
2. Installs Tesseract and Poppler via Chocolatey
3. Copies binaries to `deps/tesseract/` and `deps/poppler/bin/`
4. Runs `pyinstaller pdf_ocr.spec` → produces `dist/PDF_Tools.exe`
5. Creates a GitHub Release with the EXE (only when `tag` input is provided or push is a `v*` tag)

**To publish a release via tag push:** commit all changes → `git tag vX.Y.Z` → `git push origin master && git push origin vX.Y.Z`

**To publish manually (without a tag):** `gh workflow run build.yml --field tag=vX.Y.Z`
