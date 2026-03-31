# Split & Merge PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar as abas "Dividir PDF" e "Juntar PDF" em `pdf_ocr.py`, substituindo os placeholders "Em breve".

**Architecture:** Toda a lógica fica em `pdf_ocr.py` seguindo o padrão existente (métodos `_build_*_page` para UI e `_run_*` executados em thread separada). PyPDF2 já está importado. Sem novos arquivos.

**Tech Stack:** Python, Tkinter, PyPDF2, threading

---

## Arquivo Modificado

- Modify: `pdf_ocr.py` — substituir chamadas `_build_coming_soon_page("split")` e `_build_coming_soon_page("merge")` pelos novos métodos; adicionar lógica de split e merge.

---

## Task 1: Substituir placeholder split por página funcional

**Files:**
- Modify: `pdf_ocr.py` (linha ~744 e região após linha ~1202)

### Subtask 1a — Trocar chamada no `__init__`

- [ ] **Step 1: Substituir a chamada do coming soon para split**

Em `pdf_ocr.py` linha ~744, substituir:
```python
self._build_coming_soon_page("split")
```
por:
```python
self._build_split_page()
```

- [ ] **Step 2: Verificar que o app ainda abre sem erro**

```bash
python pdf_ocr.py
```
Esperado: app abre, aba Dividir mostra tela vazia (sem crash).

---

### Subtask 1b — Construir `_build_split_page`

Adicionar após `_build_coming_soon_page` (linha ~1258), o método abaixo. Ele cria toda a UI da aba Dividir:

- [ ] **Step 3: Adicionar variáveis de estado no `__init__` da classe `App`**

Localizar onde as outras variáveis de estado são inicializadas (procurar por `self.compress_files` ou `self.ocr_outdir`) e adicionar junto:

```python
# Split
self._split_pdf_path = ""
self._split_total_pages = 0
self._split_running = False
self._split_intervals = []   # lista de (tk.StringVar, tk.StringVar) para modo múltiplos intervalos
```

- [ ] **Step 4: Adicionar o método `_build_split_page`**

```python
def _build_split_page(self):
    page = tk.Frame(self._pages, bg=C["bg"])
    self._page_frames["split"] = page
    page.columnconfigure(0, weight=1)
    page.rowconfigure(0, weight=1)

    card = tk.Frame(page, bg=C["panel"],
                    highlightthickness=1,
                    highlightbackground=C["border"])
    card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
    card.columnconfigure(0, weight=1)

    inner = tk.Frame(card, bg=C["panel"], padx=20, pady=16)
    inner.pack(fill="both", expand=True)
    inner.columnconfigure(0, weight=1)

    # ── Seleção de arquivo ──────────────────────────────────
    file_f = tk.Frame(inner, bg=C["panel"])
    file_f.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    _flat_btn(file_f, "+ Selecionar PDF", self._split_select_file,
              padx=10, pady=3).pack(side="left")
    self._split_file_lbl = tk.Label(
        file_f, text="Nenhum arquivo selecionado",
        font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"])
    self._split_file_lbl.pack(side="left", padx=(10, 0))

    tk.Frame(inner, bg=C["border"], height=1).grid(row=1, column=0, sticky="ew", pady=(0, 12))

    # ── Modo de divisão ──────────────────────────────────────
    tk.Label(inner, text="Modo de divisão",
             font=("Segoe UI", 9, "bold"), bg=C["panel"],
             fg=C["fg"]).grid(row=2, column=0, sticky="w", pady=(0, 8))

    self._split_mode = tk.StringVar(value="single")
    modes_f = tk.Frame(inner, bg=C["panel"])
    modes_f.grid(row=3, column=0, sticky="ew", pady=(0, 12))

    for val, label in [("single", "Intervalo único"),
                       ("multi",  "Múltiplos intervalos"),
                       ("all",    "Todas as páginas individualmente")]:
        tk.Radiobutton(
            modes_f, text=label, variable=self._split_mode,
            value=val, command=self._split_update_mode_ui,
            bg=C["panel"], fg=C["fg"],
            selectcolor=C["input"],
            activebackground=C["panel"], activeforeground=C["accent"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 20))

    # ── Painel modo único ────────────────────────────────────
    self._split_single_f = tk.Frame(inner, bg=C["panel"])
    self._split_single_f.grid(row=4, column=0, sticky="ew", pady=(0, 8))
    tk.Label(self._split_single_f, text="De:", font=("Segoe UI", 9),
             bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
    self._split_from = tk.StringVar(value="1")
    e_from = tk.Entry(self._split_single_f, textvariable=self._split_from,
                      width=5, font=("Segoe UI", 9))
    _style_entry(e_from)
    e_from.pack(side="left", ipady=3, padx=(4, 12))
    tk.Label(self._split_single_f, text="Até:", font=("Segoe UI", 9),
             bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
    self._split_to = tk.StringVar(value="1")
    e_to = tk.Entry(self._split_single_f, textvariable=self._split_to,
                    width=5, font=("Segoe UI", 9))
    _style_entry(e_to)
    e_to.pack(side="left", ipady=3, padx=(4, 0))

    # ── Painel múltiplos intervalos ──────────────────────────
    self._split_multi_f = tk.Frame(inner, bg=C["panel"])
    self._split_multi_f.grid(row=4, column=0, sticky="ew", pady=(0, 8))
    self._split_multi_f.grid_remove()  # oculto inicialmente

    # campo de texto livre
    text_f = tk.Frame(self._split_multi_f, bg=C["panel"])
    text_f.pack(fill="x", pady=(0, 6))
    tk.Label(text_f, text="Intervalos (ex: 1-3, 5-8, 10):",
             font=("Segoe UI", 9), bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
    self._split_text_intervals = tk.StringVar()
    e_text = tk.Entry(text_f, textvariable=self._split_text_intervals,
                      width=30, font=("Segoe UI", 9))
    _style_entry(e_text)
    e_text.pack(side="left", ipady=3, padx=(8, 0))

    # lista visual de intervalos
    self._split_rows_f = tk.Frame(self._split_multi_f, bg=C["panel"])
    self._split_rows_f.pack(fill="x", pady=(0, 6))

    _flat_btn(self._split_multi_f, "+ Adicionar intervalo",
              self._split_add_interval_row, padx=8, pady=2).pack(anchor="w")

    # ── Destino ──────────────────────────────────────────────
    tk.Frame(inner, bg=C["border"], height=1).grid(row=5, column=0, sticky="ew", pady=(4, 10))

    dest_f = tk.Frame(inner, bg=C["panel"])
    dest_f.grid(row=6, column=0, sticky="ew", pady=(0, 12))
    self._split_same_dir = tk.BooleanVar(value=True)
    tk.Checkbutton(
        dest_f, text="Salvar na mesma pasta do arquivo original",
        variable=self._split_same_dir,
        bg=C["panel"], fg=C["fg"],
        selectcolor=C["input"],
        activebackground=C["panel"], activeforeground=C["accent"],
        font=("Segoe UI", 9),
    ).pack(side="left")

    # ── Progresso e botão ────────────────────────────────────
    self._split_status = tk.StringVar(value="Selecione um PDF para dividir.")
    tk.Label(inner, textvariable=self._split_status,
             font=("Segoe UI", 9), bg=C["panel"],
             fg=C["fg_dim"], anchor="w").grid(row=7, column=0, sticky="ew", pady=(0, 4))

    self._split_pb = CanvasProgressBar(inner, height=6)
    self._split_pb.grid(row=8, column=0, sticky="ew", pady=(0, 10))

    btn_f = tk.Frame(inner, bg=C["panel"])
    btn_f.grid(row=9, column=0, sticky="w")
    self.btn_split = _accent_btn(
        btn_f, text="  ⊟  Dividir PDF  ",
        command=self._start_split,
        font=("Segoe UI", 10, "bold"),
        padx=18, pady=9,
    )
    self.btn_split.pack(side="left")
```

- [ ] **Step 5: Verificar que a aba Dividir renderiza corretamente**

```bash
python pdf_ocr.py
```
Esperado: aba Dividir mostra UI com botão de seleção, radio buttons de modo, checkbox de destino, barra de progresso e botão Dividir.

---

## Task 2: Lógica de eventos da aba Dividir

**Files:**
- Modify: `pdf_ocr.py`

- [ ] **Step 1: Adicionar métodos de evento do Split**

Adicionar após `_build_split_page`:

```python
def _split_select_file(self):
    path = filedialog.askopenfilename(
        title="Selecionar PDF para dividir",
        filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
    )
    if not path:
        return
    try:
        reader = PyPDF2.PdfReader(path)
        self._split_total_pages = len(reader.pages)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o PDF:\n{e}")
        return
    self._split_pdf_path = path
    name = os.path.basename(path)
    self._split_file_lbl.config(
        text=f"{name}  ({self._split_total_pages} páginas)",
        fg=C["fg"])
    self._split_to.set(str(self._split_total_pages))
    self._split_status.set("Configure o modo de divisão e clique em Dividir.")

def _split_update_mode_ui(self):
    mode = self._split_mode.get()
    if mode == "single":
        self._split_single_f.grid()
        self._split_multi_f.grid_remove()
    elif mode == "multi":
        self._split_single_f.grid_remove()
        self._split_multi_f.grid()
    else:  # all
        self._split_single_f.grid_remove()
        self._split_multi_f.grid_remove()

def _split_add_interval_row(self):
    row_f = tk.Frame(self._split_rows_f, bg=C["panel"])
    row_f.pack(fill="x", pady=2)
    v_from = tk.StringVar(value="1")
    v_to   = tk.StringVar(value="1")
    tk.Label(row_f, text="De:", font=("Segoe UI", 9),
             bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
    e_f = tk.Entry(row_f, textvariable=v_from, width=5, font=("Segoe UI", 9))
    _style_entry(e_f)
    e_f.pack(side="left", ipady=3, padx=(4, 8))
    tk.Label(row_f, text="Até:", font=("Segoe UI", 9),
             bg=C["panel"], fg=C["fg_dim"]).pack(side="left")
    e_t = tk.Entry(row_f, textvariable=v_to, width=5, font=("Segoe UI", 9))
    _style_entry(e_t)
    e_t.pack(side="left", ipady=3, padx=(4, 8))
    _flat_btn(row_f, "×", lambda f=row_f, vs=(v_from, v_to): self._split_remove_interval_row(f, vs),
              padx=6, pady=1).pack(side="left")
    self._split_intervals.append((v_from, v_to))

def _split_remove_interval_row(self, frame, vars_tuple):
    if vars_tuple in self._split_intervals:
        self._split_intervals.remove(vars_tuple)
    frame.destroy()

def _parse_split_intervals(self):
    """Retorna lista de (from_page, to_page) com índice 0-based, ou None em caso de erro."""
    mode = self._split_mode.get()
    total = self._split_total_pages
    intervals = []

    if mode == "single":
        try:
            f = int(self._split_from.get())
            t = int(self._split_to.get())
        except ValueError:
            messagebox.showerror("Erro", "Digite números válidos para De e Até.")
            return None
        if not (1 <= f <= t <= total):
            messagebox.showerror("Erro", f"Páginas devem estar entre 1 e {total}, com De ≤ Até.")
            return None
        intervals = [(f - 1, t - 1)]

    elif mode == "multi":
        # Tenta linhas visuais primeiro
        for v_from, v_to in self._split_intervals:
            try:
                f = int(v_from.get())
                t = int(v_to.get())
            except ValueError:
                messagebox.showerror("Erro", "Preencha todos os campos De/Até com números.")
                return None
            if not (1 <= f <= t <= total):
                messagebox.showerror("Erro", f"Intervalo {f}-{t} inválido. Páginas de 1 a {total}.")
                return None
            intervals.append((f - 1, t - 1))

        # Se não há linhas visuais, parseia campo de texto
        if not intervals:
            text = self._split_text_intervals.get().strip()
            if not text:
                messagebox.showerror("Erro", "Adicione intervalos ou preencha o campo de texto.")
                return None
            import re
            for part in text.split(","):
                part = part.strip()
                m = re.match(r'^(\d+)-(\d+)$', part)
                if m:
                    f, t = int(m.group(1)), int(m.group(2))
                elif re.match(r'^\d+$', part):
                    f = t = int(part)
                else:
                    messagebox.showerror("Erro", f"Formato inválido: '{part}'. Use '1-3' ou '5'.")
                    return None
                if not (1 <= f <= t <= total):
                    messagebox.showerror("Erro", f"Intervalo {f}-{t} inválido. Páginas de 1 a {total}.")
                    return None
                intervals.append((f - 1, t - 1))

    else:  # all
        intervals = [(i, i) for i in range(total)]

    return intervals
```

- [ ] **Step 2: Adicionar `_start_split` e `_run_split`**

```python
def _start_split(self):
    if not self._split_pdf_path:
        messagebox.showwarning("Aviso", "Selecione um PDF primeiro.")
        return
    if self._split_running:
        return
    intervals = self._parse_split_intervals()
    if intervals is None:
        return

    out_dir = ""
    if not self._split_same_dir.get():
        out_dir = filedialog.askdirectory(title="Pasta para salvar os PDFs divididos")
        if not out_dir:
            return

    self._split_running = True
    self.btn_split.config(state="disabled")
    self._split_pb.set(0)
    threading.Thread(
        target=self._run_split,
        args=(self._split_pdf_path, intervals, out_dir),
        daemon=True,
    ).start()

def _run_split(self, input_pdf, intervals, out_dir):
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        base = os.path.splitext(os.path.basename(input_pdf))[0]
        dest = out_dir if out_dir else os.path.dirname(input_pdf)
        total = len(intervals)
        generated = []

        for i, (f, t) in enumerate(intervals):
            writer = PyPDF2.PdfWriter()
            for p in range(f, t + 1):
                writer.add_page(reader.pages[p])
            if f == t:
                out_name = f"{base}_p{f + 1}.pdf"
            else:
                out_name = f"{base}_p{f + 1}-{t + 1}.pdf"
            out_path = os.path.join(dest, out_name)
            with open(out_path, "wb") as fh:
                writer.write(fh)
            generated.append(out_path)
            progress = (i + 1) / total
            self.after(0, lambda v=progress: self._split_pb.set(v))
            self.after(0, lambda n=i+1, tot=total: self._split_status.set(
                f"Processando... {n}/{tot}"))

        self.after(0, lambda: self._split_status.set(
            f"{len(generated)} arquivo(s) gerado(s) em: {dest}"))
        self.after(0, lambda: self._split_pb.set(1.0))
    except Exception as e:
        self.after(0, lambda: messagebox.showerror("Erro ao dividir", str(e)))
        self.after(0, lambda: self._split_status.set("Erro ao dividir o PDF."))
    finally:
        self._split_running = False
        self.after(0, lambda: self.btn_split.config(state="normal"))
```

- [ ] **Step 3: Testar manualmente**

```bash
python pdf_ocr.py
```
1. Aba Dividir → Selecionar PDF → conferir nome e nº de páginas
2. Modo "Intervalo único" → De: 1, Até: 2 → Dividir → verificar arquivo gerado
3. Modo "Todas individualmente" → Dividir → verificar N arquivos gerados
4. Modo "Múltiplos intervalos" → adicionar 2 linhas → Dividir → verificar 2 arquivos
5. Testar campo de texto livre "1-2, 3" → Dividir → verificar 2 arquivos

- [ ] **Step 4: Commit**

```bash
git add pdf_ocr.py
git commit -m "feat: implement split PDF page"
```

---

## Task 3: Substituir placeholder merge por página funcional

**Files:**
- Modify: `pdf_ocr.py`

- [ ] **Step 1: Trocar chamada no `__init__`**

Em `pdf_ocr.py` linha ~745, substituir:
```python
self._build_coming_soon_page("merge")
```
por:
```python
self._build_merge_page()
```

- [ ] **Step 2: Adicionar variáveis de estado para merge no `__init__`**

Junto às outras variáveis de estado, adicionar:
```python
# Merge
self._merge_files = []   # lista de caminhos completos
self._merge_running = False
self._merge_drag_start_idx = None
```

- [ ] **Step 3: Adicionar `_build_merge_page`**

```python
def _build_merge_page(self):
    page = tk.Frame(self._pages, bg=C["bg"])
    self._page_frames["merge"] = page
    page.columnconfigure(0, weight=1)
    page.rowconfigure(0, weight=1)

    card = tk.Frame(page, bg=C["panel"],
                    highlightthickness=1,
                    highlightbackground=C["border"])
    card.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 8))
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    inner = tk.Frame(card, bg=C["panel"], padx=20, pady=16)
    inner.pack(fill="both", expand=True)
    inner.columnconfigure(0, weight=1)
    inner.rowconfigure(1, weight=1)

    # ── Cabeçalho / botões ───────────────────────────────────
    hdr = tk.Frame(inner, bg=C["panel"])
    hdr.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    tk.Label(hdr, text="PDFs para juntar",
             font=("Segoe UI", 9), bg=C["panel"],
             fg=C["fg_dim"]).pack(side="left")
    self._merge_count_lbl = tk.Label(
        hdr, text="(0 arquivos)", font=("Segoe UI", 9),
        bg=C["panel"], fg=C["fg_dim"])
    self._merge_count_lbl.pack(side="left", padx=(6, 0))
    _flat_btn(hdr, "✕ Remover", self._merge_remove_selected,
              padx=8, pady=2).pack(side="right")
    _flat_btn(hdr, "+ Adicionar PDFs", self._merge_add_files,
              padx=8, pady=2).pack(side="right", padx=(0, 4))

    # ── Listbox ──────────────────────────────────────────────
    list_f = tk.Frame(inner, bg=C["panel"])
    list_f.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
    list_f.columnconfigure(0, weight=1)
    list_f.rowconfigure(0, weight=1)

    sb = ttk.Scrollbar(list_f, orient="vertical",
                       style="Dark.Vertical.TScrollbar")
    self._merge_listbox = tk.Listbox(
        list_f,
        bg=C["input"], fg=C["fg"],
        selectbackground=C["sel"], selectforeground=C["fg_bright"],
        relief="flat", highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
        font=("Segoe UI", 9), activestyle="none",
        yscrollcommand=sb.set,
    )
    sb.config(command=self._merge_listbox.yview)
    self._merge_listbox.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")

    # Drag & drop interno (reordenação com mouse)
    self._merge_listbox.bind("<Button-1>",       self._merge_drag_start)
    self._merge_listbox.bind("<B1-Motion>",       self._merge_drag_motion)
    self._merge_listbox.bind("<ButtonRelease-1>", self._merge_drag_release)

    # Drag & drop externo (arrastar arquivos do explorer)
    try:
        self._merge_listbox.drop_target_register("DND_Files")
        self._merge_listbox.dnd_bind("<<Drop>>", self._merge_drop_files)
    except Exception:
        pass  # tkinterdnd2 não disponível

    # ── Botões ↑ ↓ ──────────────────────────────────────────
    ord_f = tk.Frame(inner, bg=C["panel"])
    ord_f.grid(row=1, column=1, sticky="ns", padx=(8, 0), pady=(0, 8))
    _flat_btn(ord_f, "↑", self._merge_move_up,
              padx=10, pady=6).pack(pady=(0, 4))
    _flat_btn(ord_f, "↓", self._merge_move_down,
              padx=10, pady=6).pack()

    # ── Área de drop visual ──────────────────────────────────
    drop_f = tk.Frame(inner, bg=C["input"],
                      highlightthickness=1,
                      highlightbackground=C["border"])
    drop_f.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    drop_lbl = tk.Label(drop_f,
                        text="⊞  Arraste PDFs aqui  ou  clique em + Adicionar PDFs",
                        font=("Segoe UI", 9), bg=C["input"],
                        fg=C["fg_dim"], pady=10)
    drop_lbl.pack()
    try:
        drop_f.drop_target_register("DND_Files")
        drop_f.dnd_bind("<<Drop>>", self._merge_drop_files)
        drop_lbl.drop_target_register("DND_Files")
        drop_lbl.dnd_bind("<<Drop>>", self._merge_drop_files)
    except Exception:
        pass

    # ── Destino ──────────────────────────────────────────────
    tk.Frame(inner, bg=C["border"], height=1).grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    dest_f = tk.Frame(inner, bg=C["panel"])
    dest_f.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    self._merge_same_dir = tk.BooleanVar(value=True)
    tk.Checkbutton(
        dest_f, text="Salvar na mesma pasta do primeiro PDF",
        variable=self._merge_same_dir,
        bg=C["panel"], fg=C["fg"],
        selectcolor=C["input"],
        activebackground=C["panel"], activeforeground=C["accent"],
        font=("Segoe UI", 9),
    ).pack(side="left")

    # ── Progresso e botão ────────────────────────────────────
    self._merge_status = tk.StringVar(value="Adicione PDFs para juntar.")
    tk.Label(inner, textvariable=self._merge_status,
             font=("Segoe UI", 9), bg=C["panel"],
             fg=C["fg_dim"], anchor="w").grid(
        row=5, column=0, columnspan=2, sticky="ew", pady=(0, 4))

    self._merge_pb = CanvasProgressBar(inner, height=6)
    self._merge_pb.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    btn_f = tk.Frame(inner, bg=C["panel"])
    btn_f.grid(row=7, column=0, columnspan=2, sticky="w")
    self.btn_merge = _accent_btn(
        btn_f, text="  ⊞  Juntar PDFs  ",
        command=self._start_merge,
        font=("Segoe UI", 10, "bold"),
        padx=18, pady=9,
    )
    self.btn_merge.pack(side="left", padx=(0, 10))
    _flat_btn(btn_f, "Limpar lista", self._merge_clear,
              padx=14, pady=9).pack(side="left")
```

- [ ] **Step 4: Verificar que a aba Juntar renderiza**

```bash
python pdf_ocr.py
```
Esperado: aba Juntar mostra lista, botões ↑↓, área de drop, checkbox e botão Juntar.

---

## Task 4: Lógica de eventos da aba Juntar

**Files:**
- Modify: `pdf_ocr.py`

- [ ] **Step 1: Adicionar métodos de evento do Merge**

```python
def _merge_add_files(self):
    paths = filedialog.askopenfilenames(
        title="Selecionar PDFs para juntar",
        filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
    )
    self._merge_insert_paths(paths)

def _merge_drop_files(self, event):
    raw = event.data
    # tkinterdnd2 retorna paths separados por espaço; paths com espaço ficam entre {}
    import re
    paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
    flat = [p[0] or p[1] for p in paths]
    pdf_paths = [p for p in flat if p.lower().endswith(".pdf")]
    self._merge_insert_paths(pdf_paths)

def _merge_insert_paths(self, paths):
    for p in paths:
        if p not in self._merge_files:
            try:
                reader = PyPDF2.PdfReader(p)
                n_pages = len(reader.pages)
            except Exception:
                n_pages = "?"
            self._merge_files.append(p)
            self._merge_listbox.insert(
                tk.END, f"{os.path.basename(p)}  ({n_pages} pág.)")
    self._merge_update_count()

def _merge_remove_selected(self):
    sel = list(self._merge_listbox.curselection())
    for idx in reversed(sel):
        self._merge_listbox.delete(idx)
        del self._merge_files[idx]
    self._merge_update_count()

def _merge_clear(self):
    self._merge_files.clear()
    self._merge_listbox.delete(0, tk.END)
    self._merge_pb.set(0)
    self._merge_status.set("Adicione PDFs para juntar.")
    self._merge_update_count()

def _merge_update_count(self):
    n = len(self._merge_files)
    self._merge_count_lbl.config(
        text=f"({n} arquivo{'s' if n != 1 else ''})")

def _merge_move_up(self):
    sel = self._merge_listbox.curselection()
    if not sel or sel[0] == 0:
        return
    idx = sel[0]
    self._merge_files[idx], self._merge_files[idx - 1] = \
        self._merge_files[idx - 1], self._merge_files[idx]
    text = self._merge_listbox.get(idx)
    self._merge_listbox.delete(idx)
    self._merge_listbox.insert(idx - 1, text)
    self._merge_listbox.selection_set(idx - 1)

def _merge_move_down(self):
    sel = self._merge_listbox.curselection()
    if not sel or sel[0] >= self._merge_listbox.size() - 1:
        return
    idx = sel[0]
    self._merge_files[idx], self._merge_files[idx + 1] = \
        self._merge_files[idx + 1], self._merge_files[idx]
    text = self._merge_listbox.get(idx)
    self._merge_listbox.delete(idx)
    self._merge_listbox.insert(idx + 1, text)
    self._merge_listbox.selection_set(idx + 1)

def _merge_drag_start(self, event):
    self._merge_drag_start_idx = self._merge_listbox.nearest(event.y)

def _merge_drag_motion(self, event):
    if self._merge_drag_start_idx is None:
        return
    idx = self._merge_listbox.nearest(event.y)
    if idx != self._merge_drag_start_idx:
        self._merge_files[idx], self._merge_files[self._merge_drag_start_idx] = \
            self._merge_files[self._merge_drag_start_idx], self._merge_files[idx]
        text_from = self._merge_listbox.get(self._merge_drag_start_idx)
        text_to   = self._merge_listbox.get(idx)
        self._merge_listbox.delete(self._merge_drag_start_idx)
        self._merge_listbox.insert(self._merge_drag_start_idx, text_to)
        self._merge_listbox.delete(idx)
        self._merge_listbox.insert(idx, text_from)
        self._merge_drag_start_idx = idx
        self._merge_listbox.selection_clear(0, tk.END)
        self._merge_listbox.selection_set(idx)

def _merge_drag_release(self, event):
    self._merge_drag_start_idx = None
```

- [ ] **Step 2: Adicionar `_start_merge` e `_run_merge`**

```python
def _start_merge(self):
    if len(self._merge_files) < 2:
        messagebox.showwarning("Aviso", "Adicione ao menos 2 PDFs para juntar.")
        return
    if self._merge_running:
        return

    if self._merge_same_dir.get():
        out_dir = os.path.dirname(self._merge_files[0])
        out_path = os.path.join(out_dir, "merged.pdf")
    else:
        out_path = filedialog.asksaveasfilename(
            title="Salvar PDF juntado como",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile="merged.pdf",
        )
        if not out_path:
            return

    self._merge_running = True
    self.btn_merge.config(state="disabled")
    self._merge_pb.set(0)
    threading.Thread(
        target=self._run_merge,
        args=(list(self._merge_files), out_path),
        daemon=True,
    ).start()

def _run_merge(self, files, out_path):
    try:
        merger = PyPDF2.PdfMerger()
        total = len(files)
        for i, f in enumerate(files):
            merger.append(f)
            progress = (i + 1) / total
            self.after(0, lambda v=progress: self._merge_pb.set(v))
            self.after(0, lambda n=i+1, tot=total: self._merge_status.set(
                f"Processando... {n}/{tot}"))

        with open(out_path, "wb") as fh:
            merger.write(fh)
        merger.close()

        reader = PyPDF2.PdfReader(out_path)
        n_pages = len(reader.pages)
        self.after(0, lambda: self._merge_status.set(
            f"PDF gerado: {os.path.basename(out_path)}  ({n_pages} páginas)  →  {os.path.dirname(out_path)}"))
        self.after(0, lambda: self._merge_pb.set(1.0))
    except Exception as e:
        self.after(0, lambda: messagebox.showerror("Erro ao juntar", str(e)))
        self.after(0, lambda: self._merge_status.set("Erro ao juntar os PDFs."))
    finally:
        self._merge_running = False
        self.after(0, lambda: self.btn_merge.config(state="normal"))
```

- [ ] **Step 3: Testar manualmente**

```bash
python pdf_ocr.py
```
1. Aba Juntar → "Adicionar PDFs" → selecionar 2+ PDFs → verificar lista com nome e páginas
2. Testar ↑ e ↓ para reordenar
3. Testar arrastar item na lista com o mouse para reordenar
4. Testar "Remover" e "Limpar lista"
5. Checkbox marcada → Juntar → verificar `merged.pdf` na pasta do primeiro PDF
6. Checkbox desmarcada → Juntar → escolher destino → verificar arquivo salvo corretamente
7. Tentar juntar com menos de 2 PDFs → verificar aviso

- [ ] **Step 4: Commit**

```bash
git add pdf_ocr.py
git commit -m "feat: implement merge PDF page"
```

---

## Task 5: Remover `_build_coming_soon_page` se não usado em mais nada

**Files:**
- Modify: `pdf_ocr.py`

- [ ] **Step 1: Verificar se `_build_coming_soon_page` ainda é chamado em algum lugar**

```bash
grep -n "_build_coming_soon_page" pdf_ocr.py
```
Esperado: 0 ocorrências. Se houver, não remover.

- [ ] **Step 2: Se 0 ocorrências, remover o método**

Deletar o bloco do método `_build_coming_soon_page` (linhas ~1203–1257).

- [ ] **Step 3: Verificar que o app abre corretamente**

```bash
python pdf_ocr.py
```
Esperado: todas as 5 abas funcionam, sem erro.

- [ ] **Step 4: Commit final**

```bash
git add pdf_ocr.py
git commit -m "chore: remove coming soon placeholder after split/merge implementation"
```

---

## Self-Review

**Spec coverage:**
- [x] Dividir: seleção de arquivo com total de páginas
- [x] Dividir: 3 modos (intervalo único, múltiplos, todas individualmente)
- [x] Dividir: campo de texto livre + linhas visuais para múltiplos intervalos
- [x] Dividir: checkbox "salvar na mesma pasta"
- [x] Juntar: botão "Adicionar PDFs" (múltipla seleção)
- [x] Juntar: drag & drop externo via tkinterdnd2 (com fallback gracioso)
- [x] Juntar: lista com nome e nº de páginas
- [x] Juntar: reordenação com ↑↓ e drag interno com mouse
- [x] Juntar: checkbox "salvar na mesma pasta do primeiro PDF"
- [x] Ambas: barra de progresso, execução em thread, tratamento de erro

**Placeholder scan:** Nenhum TBD ou TODO — todos os steps têm código completo.

**Type consistency:** `_merge_listbox`, `_merge_files`, `_split_pb`, `_merge_pb`, `btn_split`, `btn_merge` — nomes consistentes em todos os tasks.
