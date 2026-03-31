# -*- mode: python ; coding: utf-8 -*-
#
# O GitHub Actions baixa Tesseract e Poppler antes do build e os coloca em:
#   deps/tesseract/   → binários do Tesseract (incluindo tessdata/)
#   deps/poppler/bin/ → binários do Poppler (pdftoppm, etc.)
#
# O PyInstaller os embute no EXE via 'binaries' e 'datas' abaixo.

import os, glob

block_cipher = None

# ── Tesseract binários + tessdata ─────────────────────────────────────────────
tess_root = os.path.join(os.getcwd(), "deps", "tesseract")
tess_binaries = []
tess_datas    = []

if os.path.isdir(tess_root):
    for f in glob.glob(os.path.join(tess_root, "*.exe")):
        tess_binaries.append((f, "."))
    for f in glob.glob(os.path.join(tess_root, "*.dll")):
        tess_binaries.append((f, "."))
    tessdata_dir = os.path.join(tess_root, "tessdata")
    if os.path.isdir(tessdata_dir):
        tess_datas.append((tessdata_dir, "tessdata"))

# ── Poppler binários ───────────────────────────────────────────────────────────
poppler_bin = os.path.join(os.getcwd(), "deps", "poppler", "bin")
poppler_binaries = []

if os.path.isdir(poppler_bin):
    for f in glob.glob(os.path.join(poppler_bin, "*.exe")):
        poppler_binaries.append((f, os.path.join("poppler", "bin")))
    for f in glob.glob(os.path.join(poppler_bin, "*.dll")):
        poppler_binaries.append((f, os.path.join("poppler", "bin")))

# ─────────────────────────────────────────────────────────────────────────────

a = Analysis(
    ['pdf_ocr.py'],
    pathex=[],
    binaries=tess_binaries + poppler_binaries,
    datas=tess_datas,
    hiddenimports=[
        'pytesseract',
        'PIL',
        'PIL.Image',
        'pdf2image',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.lib.pagesizes',
        'reportlab.lib.utils',
        'PyPDF2',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF_Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
)
