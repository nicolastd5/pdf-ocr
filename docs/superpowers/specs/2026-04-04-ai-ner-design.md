# PDF Tools — AI NER (Named Entity Recognition) Design

**Goal:** Substituir a detecção de nomes por regex do OCR por um pipeline NER de dois níveis (spaCy local + OpenAI opcional), exibir os resultados em painel na UI e permitir exportar CSV. Abordagem BERT/transformers documentada como extensão futura.

**Scope:** Apenas a página OCR (`OcrPage`). Nenhuma outra página é alterada.

---

## Arquivos Afetados

| Arquivo | Mudança |
|---|---|
| `pdf_ocr_qt/ner.py` | **novo** — NERPipeline, NERResult, Entity, instalação lazy |
| `pdf_ocr_qt/workers.py` | OcrWorker: chama NERPipeline, emite sinal `entities` |
| `pdf_ocr_qt/pages/ocr.py` | Opções de IA + painel de resultados + exportar CSV |
| `pdf_ocr_qt/main.py` | `_load_prefs`/`_save_prefs` com 4 novas chaves |
| `requirements.txt` | Adiciona `spacy`, `openai` como opcionais (comentados) |

---

## NER Pipeline (`ner.py`)

### Tipos de entidade

```python
ENTITY_TYPES = {
    "PER":  "Pessoa",        # destaque amarelo
    "ORG":  "Organização",   # destaque azul claro
    "LOC":  "Local",         # destaque verde
    "MISC": "Outro",         # destaque cinza
}
```

### Estrutura de dados

```python
@dataclass
class Entity:
    text:     str        # texto da entidade
    type:     str        # "PER", "ORG", "LOC", "MISC"
    page:     int        # número da página (1-based)
    bbox:     tuple      # (x, y, w, h) em pixels da imagem OCR

@dataclass
class NERResult:
    entities: list[Entity]
```

### NERPipeline

```python
class NERPipeline:
    def __init__(self, use_openai: bool = False, openai_key: str = "",
                 engine: str = "spacy"):
        ...

    def extract(self, ocr_data: dict, page_num: int,
                img_w: int, img_h: int) -> NERResult:
        """
        Recebe o dict do pytesseract.image_to_data e retorna NERResult.
        Nível 1: spaCy — sempre executado se engine == "spacy".
        Nível 2: OpenAI — enriquece/corrige se use_openai e openai_key.
        """
```

**Lazy load do spaCy:** `import spacy` e `spacy.load("pt_core_news_lg")` só ocorrem na primeira chamada a `extract()`. Se o pacote não estiver instalado, levanta `SpacyNotInstalledError` — capturado pelo caller, que abre diálogo de instalação.

**Instalação automática:** `NERPipeline.install_spacy()` — método estático que executa `pip install spacy` e `python -m spacy download pt_core_news_lg` em `subprocess.Popen`, retornando um gerador de linhas de output para exibir progresso.

**Nível 2 — OpenAI:** Constrói um prompt com o texto completo da página e pede JSON `[{"text": "...", "type": "PER|ORG|LOC|MISC"}]`. Merge com resultado do spaCy: entidades do OpenAI que coincidem com tokens do `ocr_data` herdam o `bbox`; entidades sem match de bbox são incluídas sem destaque no PDF (apenas na lista).

**Engine BERT (futuro):** Quando `engine == "bert"`, `NERPipeline` carrega `BERTNEREngine` (não implementado nesta versão). A chave `ner_engine` no prefs já suporta o valor `"bert"` para não exigir mudança de schema no futuro.

---

## OcrWorker (`workers.py`)

Novo sinal:
```python
entities = pyqtSignal(list)  # list[Entity], emitido após finished
```

Mudanças no `run()`:
1. Se `self.use_ner` for `True`, instancia `NERPipeline(use_openai, openai_key, engine)`.
2. Em `_process_single`, após cada página, chama `pipeline.extract(ocr_data, pi, img_w, img_h)` e acumula entidades.
3. Ao final, emite `self.entities.emit(all_entities)`.
4. O destaque no PDF usa `entity.type` para escolher a cor (em vez de fixo amarelo).

Cores de destaque por tipo (RGBA):
- `PER` → amarelo `(1.0, 0.85, 0.0, 0.35)` — igual ao comportamento atual
- `ORG` → azul `(0.2, 0.6, 1.0, 0.30)`
- `LOC` → verde `(0.2, 0.85, 0.4, 0.30)`
- `MISC` → cinza `(0.6, 0.6, 0.6, 0.25)`

Compatibilidade retroativa: se `use_ner` for `False`, o worker usa o `_detect_names` com regex atual — nenhum comportamento existente muda.

---

## OcrPage (`pages/ocr.py`)

### Opções de IA

Adicionadas abaixo do checkbox "Destacar nomes detectados":

```
[ ] Usar IA para detectar nomes (spaCy)
      [ ] Usar OpenAI para NER avançado
          Chave API OpenAI: [_________________________]
```

- Checkbox filho e campo de chave ficam `setEnabled(False)` quando o pai está desmarcado.
- Campo de chave usa `setEchoMode(QLineEdit.EchoMode.Password)`.
- Ao marcar "Usar IA" pela primeira vez, verificar se spaCy está instalado:
  - Se não: abrir `SpacyInstallDialog` (QDialog com log de progresso).
  - Se sim: habilitar normalmente.

### Painel de resultados

`QTreeWidget` com 3 colunas: **Nome**, **Tipo**, **Páginas**.

- Oculto por padrão (`setVisible(False)`).
- Torna-se visível após OCR com IA concluído.
- Cada linha tem um ícone colorido (quadrado 12×12 px) conforme o tipo.
- Linhas agrupáveis por tipo (opcional — não obrigatório nesta versão).
- Botão "📄 Exportar CSV" no rodapé do painel.

### Exportar CSV

Formato:
```csv
Nome,Tipo,Páginas,Arquivo
João Silva,Pessoa,"1, 3",documento_escaneado.pdf
Ministério da Saúde,Organização,"2",documento_escaneado.pdf
```

Salvo em `<mesmo_dir_do_pdf>/<nome_base>_entidades.csv` por padrão, com `QFileDialog` de confirmação.

---

## Preferências (`main.py`)

4 novas chaves no `pdf_ocr_prefs.json`:

```json
{
  "use_ner":    false,
  "use_openai": false,
  "openai_key": "",
  "ner_engine": "spacy"
}
```

- `use_ner`: ativa o pipeline NER na OcrPage.
- `use_openai`: ativa o nível 2 (OpenAI).
- `openai_key`: chave da API, salva em texto simples (usuário é avisado na UI).
- `ner_engine`: `"spacy"` (padrão) ou `"bert"` (futuro). A UI exibe um `QComboBox` "Motor de IA" com apenas "spaCy" nesta versão; o item "BERT (local, ~400 MB)" será adicionado na implementação da Abordagem C.

---

## SpacyInstallDialog (`widgets/spacy_install.py`)

`QDialog` modal com:
- Texto: *"O spaCy não está instalado. Deseja instalar agora? (~50 MB)"*
- Botão "Instalar" → executa `NERPipeline.install_spacy()` em QThread, exibe output em `QPlainTextEdit`.
- Botão "Cancelar" → fecha sem instalar, desmarca checkbox "Usar IA".
- Ao concluir com sucesso: fecha automaticamente, OcrPage prossegue.

---

## Dependências

`requirements.txt` — adicionar (comentado, com instrução):

```
# IA / NER (opcional) — descomentar para ativar:
# spacy>=3.7
# openai>=1.0
# Após instalar spacy: python -m spacy download pt_core_news_lg
```

O app funciona sem essas dependências — todas as importações são lazy.

---

## O que NÃO muda

- Lógica de OCR (Tesseract, pdf2image, pré-processamento de imagem)
- Todas as outras páginas (Compress, Word, Split, Merge, About)
- CI/CD e PyInstaller spec
- Preferências existentes (`auto_update`, `highlight_names`, `compress_quality`, `compress_format`)
- Comportamento do OCR quando "Usar IA" está desativado

---

## Extensão Futura — Abordagem C (BERT)

Quando implementada:
1. Adicionar `BERTNEREngine` em `ner.py` usando `transformers` + `neuralmind/bert-base-portuguese-cased`.
2. Adicionar item "BERT (local, ~400 MB)" no `QComboBox` "Motor de IA".
3. Diálogo de download do modelo (~400 MB) antes do primeiro uso.
4. `NERPipeline` roteia para `BERTNEREngine` quando `engine == "bert"`.
5. OpenAI continua disponível como enriquecedor opcional sobre o BERT.

Nenhuma mudança de schema de prefs ou de interface é necessária — a infraestrutura já está preparada.
