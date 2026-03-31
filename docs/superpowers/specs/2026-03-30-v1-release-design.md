---
name: v1.0.0 Release
description: Design spec for publishing PDF Tools v1.0.0 — version bump, EXE rename, changelog in app and GitHub Release
type: project
---

# v1.0.0 Release — Design Spec

**Date:** 2026-03-30
**Status:** Approved

---

## Changes to `pdf_ocr.py`

1. `APP_VERSION = "1.0.0"`
2. Aba Sobre — grade de funcionalidades: remover "Em breve." das descrições de Dividir e Juntar, substituir por descrição funcional
3. Aba Sobre — adicionar card "O que há de novo" com changelog da v1.0.0 (texto fixo, abaixo do card de atualização)

## Changes to `pdf_ocr.spec`

- `name='PDF_OCR'` → `name='PDF_Tools'`

## Changelog Text (app + GitHub Release)

```
v1.0.0 — Lançamento oficial

✦ Dividir PDF
  Separe um PDF em partes: intervalo único, múltiplos intervalos
  (campo de texto ou visual) ou todas as páginas individualmente.

✦ Juntar PDF
  Una múltiplos PDFs em um único arquivo. Reordene arrastando
  com o mouse ou usando os botões ↑↓. Suporte a drag & drop
  de arquivos do Explorer.

✦ Melhorias gerais
  Correções de layout, melhor gerenciamento de recursos e
  tratamento de erros aprimorado.
```

## Publication Steps

1. Commit all changes
2. `git tag v1.0.0`
3. `git push origin master --tags`
4. GitHub Actions builds `PDF_Tools.exe` and publishes the Release automatically
