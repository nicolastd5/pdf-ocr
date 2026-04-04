# pdf_ocr_qt/ner.py
from __future__ import annotations
import json
import re
import sys
import subprocess
from dataclasses import dataclass, field

ENTITY_TYPES: dict[str, str] = {
    "PER":  "Pessoa",
    "ORG":  "Organização",
    "LOC":  "Local",
    "MISC": "Outro",
}

# Mapeamento de labels spaCy → tipos internos
_SPACY_LABEL_MAP: dict[str, str] = {
    "PER":  "PER",
    "PERSON": "PER",
    "ORG":  "ORG",
    "GPE":  "LOC",
    "LOC":  "LOC",
    "MISC": "MISC",
}


@dataclass
class Entity:
    text: str
    type: str        # "PER", "ORG", "LOC", "MISC"
    page: int        # 1-based
    bbox: tuple      # (x, y, w, h) em pixels — pode ser (0,0,0,0) se sem match


@dataclass
class NERResult:
    entities: list[Entity] = field(default_factory=list)


class SpacyNotInstalledError(RuntimeError):
    pass


class NERPipeline:
    def __init__(self, use_openai: bool = False, openai_key: str = "",
                 engine: str = "spacy"):
        self.use_openai  = use_openai
        self.openai_key  = openai_key
        self.engine      = engine
        self._nlp        = None   # lazy-loaded

    @staticmethod
    def _find_model_path() -> str | None:
        """Localiza o diretório do modelo pt_core_news_lg dentro do _MEIPASS.

        collect_data_files("pt_core_news_lg") produz:
          _MEIPASS/pt_core_news_lg/meta.json          <- meta do pacote Python
          _MEIPASS/pt_core_news_lg/pt_core_news_lg-X.Y.Z/meta.json  <- modelo real
          _MEIPASS/pt_core_news_lg/pt_core_news_lg-X.Y.Z/config.cfg
          ...

        spacy.load() precisa do diretório que contém config.cfg (modelo real),
        não do diretório raiz do pacote.
        """
        import os
        base = sys._MEIPASS
        pkg_dir = os.path.join(base, "pt_core_news_lg")
        if os.path.isdir(pkg_dir):
            # Procura subdiretório que contém config.cfg (é o modelo real)
            for entry in os.scandir(pkg_dir):
                if entry.is_dir() and entry.name.startswith("pt_core_news_lg"):
                    if os.path.isfile(os.path.join(entry.path, "config.cfg")):
                        return entry.path
            # Fallback: qualquer subdiretório com meta.json e config.cfg
            for entry in os.scandir(pkg_dir):
                if entry.is_dir():
                    if (os.path.isfile(os.path.join(entry.path, "config.cfg")) and
                            os.path.isfile(os.path.join(entry.path, "meta.json"))):
                        return entry.path
        # Último recurso: busca recursiva pelo config.cfg
        for root, dirs, files in os.walk(base):
            if "config.cfg" in files and "meta.json" in files:
                if os.path.basename(root).startswith("pt_core_news_lg"):
                    return root
        return None

    @staticmethod
    def is_spacy_installed() -> bool:
        try:
            import spacy
            if getattr(sys, "frozen", False):
                return NERPipeline._find_model_path() is not None
            return spacy.util.is_package("pt_core_news_lg")
        except Exception:
            return False

    @staticmethod
    def install_spacy():
        """Gerador: yields linhas de output durante a instalação."""
        pip = [sys.executable, "-m", "pip", "install", "spacy>=3.7"]
        proc = subprocess.Popen(pip, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            yield line.rstrip()
        proc.wait()
        if proc.returncode != 0:
            yield "ERRO: falha ao instalar spaCy."
            return
        dl = [sys.executable, "-m", "spacy", "download", "pt_core_news_lg"]
        proc2 = subprocess.Popen(dl, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True)
        for line in proc2.stdout:
            yield line.rstrip()
        proc2.wait()
        if proc2.returncode == 0:
            yield "OK"
        else:
            yield "ERRO: falha ao baixar pt_core_news_lg."

    @staticmethod
    def _filter_tokens(ocr_data: dict) -> tuple[list[str], list[tuple]]:
        """Return (words, token_bboxes) after filtering low-confidence tokens."""
        texts   = ocr_data.get("text", [])
        confs   = ocr_data.get("conf", [])
        lefts   = ocr_data.get("left", [])
        tops    = ocr_data.get("top", [])
        widths  = ocr_data.get("width", [])
        heights = ocr_data.get("height", [])

        words: list[str] = []
        token_bboxes: list[tuple] = []
        for i, word in enumerate(texts):
            if not word or not word.strip():
                continue
            try:
                conf = int(confs[i])
            except (TypeError, ValueError):
                continue
            if conf < 30:
                continue
            words.append(word)
            token_bboxes.append((lefts[i], tops[i], widths[i], heights[i]))

        return words, token_bboxes

    def extract(self, ocr_data: dict, page_num: int) -> NERResult:
        """Extrai entidades. Se OpenAI falhar, guarda o erro em self.last_openai_error
        e retorna o resultado spaCy sem interromper o processamento."""
        words, token_bboxes = self._filter_tokens(ocr_data)
        self.last_openai_error: str = ""

        if self.engine == "spacy":
            result = self._extract_spacy(ocr_data, page_num, words, token_bboxes)
        else:
            result = NERResult()

        if self.use_openai and self.openai_key:
            try:
                result = self._enrich_openai(ocr_data, page_num, result, words, token_bboxes)
            except Exception as e:
                self.last_openai_error = str(e)

        return result

    def _extract_spacy(self, ocr_data: dict, page_num: int,
                       words: list[str], token_bboxes: list[tuple]) -> NERResult:
        try:
            import spacy
        except ImportError:
            raise SpacyNotInstalledError(
                "spaCy não está instalado. Use NERPipeline.install_spacy().")

        if self._nlp is None:
            try:
                if getattr(sys, "frozen", False):
                    model_path = NERPipeline._find_model_path()
                    if model_path is None:
                        raise OSError("Modelo não encontrado em _MEIPASS")
                    self._nlp = spacy.load(model_path)
                else:
                    self._nlp = spacy.load("pt_core_news_lg")
            except OSError:
                raise SpacyNotInstalledError(
                    "Modelo pt_core_news_lg não encontrado. "
                    "Execute: python -m spacy download pt_core_news_lg")

        full_text = " ".join(words)
        doc = self._nlp(full_text)

        entities: list[Entity] = []
        char_offset = 0
        word_char_starts = []
        for w in words:
            word_char_starts.append(char_offset)
            char_offset += len(w) + 1

        for ent in doc.ents:
            ent_type = _SPACY_LABEL_MAP.get(ent.label_, "MISC")
            bbox = NERPipeline._static_find_bbox(
                ent.text, words, token_bboxes, word_char_starts,
                ent.start_char, ent.end_char)
            entities.append(Entity(
                text=ent.text,
                type=ent_type,
                page=page_num,
                bbox=bbox,
            ))

        return NERResult(entities=entities)

    def _enrich_openai(self, ocr_data: dict, page_num: int,
                       base: NERResult, words: list[str],
                       token_bboxes: list[tuple]) -> NERResult:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError(
                "Pacote 'openai' não instalado. Execute: pip install openai")

        page_text = " ".join(words)
        if not page_text.strip():
            return base

        client = OpenAI(api_key=self.openai_key)
        prompt = (
            "Extraia entidades nomeadas do texto abaixo. "
            "Responda SOMENTE com JSON array: "
            '[{"text":"...","type":"PER|ORG|LOC|MISC"}]\n\n'
            + page_text
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        items = json.loads(raw)

        char_starts: list[int] = []
        off = 0
        for w in words:
            char_starts.append(off)
            off += len(w) + 1

        existing_texts = {e.text.lower() for e in base.entities}

        new_entities = list(base.entities)
        for item in items:
            ent_text = item.get("text", "").strip()
            ent_type = item.get("type", "MISC")
            if not ent_text or ent_text.lower() in existing_texts:
                continue
            if ent_type not in ENTITY_TYPES:
                ent_type = "MISC"
            idx = next((i for i, w in enumerate(words)
                        if ent_text.lower().startswith(w.lower())), -1)
            if idx >= 0:
                cs = char_starts[idx]
                ce = cs + len(ent_text)
                bbox = NERPipeline._static_find_bbox(
                    ent_text, words, token_bboxes, char_starts, cs, ce)
            else:
                bbox = (0, 0, 0, 0)
            new_entities.append(Entity(
                text=ent_text, type=ent_type, page=page_num, bbox=bbox))
            existing_texts.add(ent_text.lower())

        return NERResult(entities=new_entities)

    @staticmethod
    def _static_find_bbox(ent_text, words, token_bboxes, word_char_starts,
                          start_char, end_char):
        matched = []
        for i, (w, cs) in enumerate(zip(words, word_char_starts)):
            ce = cs + len(w)
            if cs >= start_char and ce <= end_char:
                matched.append(token_bboxes[i])
        if not matched:
            return (0, 0, 0, 0)
        x  = min(b[0] for b in matched)
        y  = min(b[1] for b in matched)
        x2 = max(b[0] + b[2] for b in matched)
        y2 = max(b[1] + b[3] for b in matched)
        return (x, y, x2 - x, y2 - y)
