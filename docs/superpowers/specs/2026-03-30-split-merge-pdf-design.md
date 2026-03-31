---
name: Split and Merge PDF
description: Design spec for Dividir PDF and Juntar PDF features in PDF Tools app
type: project
---

# Split & Merge PDF — Design Spec

**Date:** 2026-03-30
**Status:** Approved
**Approach:** Opção 1 — implementar diretamente em `pdf_ocr.py`, substituindo `_build_coming_soon_page` para split e merge.

---

## Aba Dividir PDF (`_build_split_page`)

### UI

1. **Seleção de arquivo**
   - Botão "Selecionar PDF" → `filedialog.askopenfilename`
   - Label exibe nome do arquivo e total de páginas após seleção

2. **Modo de divisão** (3 radio buttons)
   - **Intervalo único** — dois campos numéricos: "De" e "Até"
   - **Múltiplos intervalos** — lista de linhas, cada uma com campos "De" / "Até" + botão "×" para remover; botão "+" para adicionar nova linha; campo de texto livre abaixo (`1-3, 5-8, 10-12`) como alternativa — ao executar, parseia o campo de texto se as linhas estiverem vazias
   - **Todas individualmente** — sem configuração extra

3. **Destino**
   - Checkbox "Salvar na mesma pasta do arquivo original"
   - Se desmarcada → `filedialog.askdirectory` ao clicar em Dividir

4. **Execução**
   - Botão "Dividir"
   - Barra de progresso (`ttk.Progressbar`)
   - Label de resultado: "X arquivo(s) gerado(s) em /caminho/"

### Lógica

- Usa `PyPDF2.PdfWriter` para cada intervalo
- Parse do campo de texto livre: regex `(\d+)-(\d+)` ou número único
- Validação: páginas dentro do range do PDF, De <= Até
- Nomes de saída: `{nome_original}_p{inicio}-{fim}.pdf` ou `{nome_original}_p{n}.pdf`
- Execução em thread separada (padrão da app)

---

## Aba Juntar PDF (`_build_merge_page`)

### UI

1. **Adição de arquivos**
   - Área de drop com texto "Arraste PDFs aqui" (usa `tkinterdnd2` se disponível, fallback gracioso se não)
   - Botão "Adicionar PDFs" → `filedialog.askopenfilenames` (múltipla seleção)

2. **Lista de arquivos**
   - `tk.Listbox` com scrollbar
   - Cada item exibe: nome do arquivo + nº de páginas
   - Reordenação:
     - Botões ↑ e ↓ na lateral direita
     - Drag & drop interno: eventos `<Button-1>`, `<B1-Motion>`, `<ButtonRelease-1>` no Listbox
   - Botão "Remover" para tirar item selecionado

3. **Destino**
   - Checkbox "Salvar na mesma pasta do primeiro PDF"
   - Se desmarcada → `filedialog.asksaveasfilename` ao clicar em Juntar

4. **Execução**
   - Botão "Juntar"
   - Barra de progresso
   - Label de resultado: "PDF gerado: /caminho/arquivo.pdf (X páginas)"

### Lógica

- Usa `PyPDF2.PdfMerger` para unir na ordem da lista
- Nome de saída padrão: `merged.pdf` (ou nome escolhido pelo usuário)
- Execução em thread separada

---

## Estrutura de Mudanças em `pdf_ocr.py`

| Antes | Depois |
|-------|--------|
| `self._build_coming_soon_page("split")` | `self._build_split_page()` |
| `self._build_coming_soon_page("merge")` | `self._build_merge_page()` |
| `_build_coming_soon_page` mantida para outros usos | Pode ser removida se não usada em mais nada |

Novos métodos a adicionar:
- `_build_split_page()`
- `_run_split()` — lógica em thread
- `_build_merge_page()`
- `_run_merge()` — lógica em thread
- `_merge_list_drag_start()`, `_merge_list_drag_motion()`, `_merge_list_drag_release()` — drag & drop interno

---

## Dependências

- `PyPDF2` — já importado na app
- `tkinterdnd2` — opcional para drag & drop de arquivos externos; se não instalado, apenas o botão "Adicionar" funciona

---

## Fora de Escopo

- Preview de páginas
- Reordenação de páginas individuais dentro de um PDF
- Compressão do output
