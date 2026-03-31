# License Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a license key system to PDF OCR, with server-side validation on Render (free tier), a local admin script to generate keys, and a license activation screen in the app.

**Architecture:** A FastAPI server on Render stores license keys in a SQLite database (persisted via Render disk or simple file). The app sends `{key, hardware_id}` to the API on every startup; the server validates and responds OK/denied. Keys are generated locally by the owner via a CLI script using HMAC-SHA256 so they can be pre-validated offline if needed, but the server is the authority.

**Tech Stack:** FastAPI + SQLite (server), `requests` (client in app), `hashlib`/`hmac`/`uuid` (key generation), Render free tier (hosting), Tkinter (activation UI).

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `license_server/main.py` | Create | FastAPI app — validate/activate/revoke endpoints |
| `license_server/db.py` | Create | SQLite schema + CRUD helpers |
| `license_server/keygen.py` | Create | CLI script to generate + print license keys |
| `license_server/requirements.txt` | Create | fastapi, uvicorn, python-multipart |
| `license_server/render.yaml` | Create | Render deployment config |
| `pdf_ocr.py` | Modify | Add license check on startup, activation dialog, hw_id helper |

---

## Task 1: License server — database layer

**Files:**
- Create: `license_server/db.py`
- Create: `license_server/requirements.txt`

- [ ] **Step 1: Create the requirements file**

```
# license_server/requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
```

- [ ] **Step 2: Create db.py**

```python
# license_server/db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "licenses.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key         TEXT PRIMARY KEY,
                hw_id       TEXT,
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL,
                activated_at TEXT,
                note        TEXT
            )
        """)
        c.commit()


def insert_key(key: str, note: str = ""):
    with _conn() as c:
        c.execute(
            "INSERT INTO licenses (key, active, created_at, note) VALUES (?,1,?,?)",
            (key, datetime.utcnow().isoformat(), note)
        )
        c.commit()


def get_key(key: str):
    with _conn() as c:
        row = c.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()
        return dict(row) if row else None


def activate_key(key: str, hw_id: str):
    with _conn() as c:
        c.execute(
            "UPDATE licenses SET hw_id=?, activated_at=? WHERE key=?",
            (hw_id, datetime.utcnow().isoformat(), key)
        )
        c.commit()


def revoke_key(key: str):
    with _conn() as c:
        c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
        c.commit()


def list_keys():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM licenses ORDER BY created_at DESC").fetchall()]
```

- [ ] **Step 3: Commit**

```bash
git add license_server/
git commit -m "feat: license server db layer"
```

---

## Task 2: License server — FastAPI app

**Files:**
- Create: `license_server/main.py`

- [ ] **Step 1: Create main.py**

```python
# license_server/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import init_db, get_key, activate_key, insert_key, revoke_key, list_keys

app = FastAPI()
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]  # set in Render env vars

@app.on_event("startup")
def startup():
    init_db()


# ── Public endpoint ──────────────────────────────────────────────

class ValidateRequest(BaseModel):
    key: str
    hw_id: str

@app.post("/validate")
def validate(req: ValidateRequest):
    row = get_key(req.key)
    if not row:
        raise HTTPException(status_code=404, detail="Chave não encontrada.")
    if not row["active"]:
        raise HTTPException(status_code=403, detail="Chave revogada.")
    # If already bound to a different machine, deny
    if row["hw_id"] and row["hw_id"] != req.hw_id:
        raise HTTPException(status_code=403, detail="Chave vinculada a outro computador.")
    # First activation: bind hw_id
    if not row["hw_id"]:
        activate_key(req.key, req.hw_id)
    return {"ok": True, "message": "Licença válida."}


# ── Admin endpoints (protected by token) ─────────────────────────

def _check_token(token: str):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido.")

class AdminRequest(BaseModel):
    token: str

class GenerateRequest(AdminRequest):
    key: str
    note: str = ""

class RevokeRequest(AdminRequest):
    key: str

@app.post("/admin/generate")
def admin_generate(req: GenerateRequest):
    _check_token(req.token)
    if get_key(req.key):
        raise HTTPException(status_code=409, detail="Chave já existe.")
    insert_key(req.key, req.note)
    return {"ok": True, "key": req.key}

@app.post("/admin/revoke")
def admin_revoke(req: RevokeRequest):
    _check_token(req.token)
    revoke_key(req.key)
    return {"ok": True}

@app.get("/admin/list")
def admin_list(token: str):
    _check_token(token)
    return list_keys()

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add license_server/main.py
git commit -m "feat: license server FastAPI endpoints"
```

---

## Task 3: Key generator CLI script

**Files:**
- Create: `license_server/keygen.py`

- [ ] **Step 1: Create keygen.py**

```python
# license_server/keygen.py
"""
Gera chaves de licença e as registra no servidor.

Uso:
  python keygen.py --url https://seu-app.onrender.com --token SEU_TOKEN --note "Cliente X" --count 1
"""
import argparse
import secrets
import string
import urllib.request
import urllib.error
import json

def gen_key(length=29):
    """Gera uma chave no formato XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"""
    chars = string.ascii_uppercase + string.digits
    raw = "".join(secrets.choice(chars) for _ in range(25))
    return "-".join(raw[i:i+5] for i in range(0, 25, 5))

def register_key(url: str, token: str, key: str, note: str):
    payload = json.dumps({"token": token, "key": key, "note": note}).encode()
    req = urllib.request.Request(
        f"{url}/admin/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",   required=True,  help="URL do servidor, ex: https://pdf-ocr-license.onrender.com")
    parser.add_argument("--token", required=True,  help="ADMIN_TOKEN configurado no Render")
    parser.add_argument("--note",  default="",     help="Observação (ex: nome do cliente)")
    parser.add_argument("--count", type=int, default=1, help="Quantas chaves gerar")
    args = parser.parse_args()

    for i in range(args.count):
        key = gen_key()
        result = register_key(args.url, args.token, key, args.note)
        if "error" in result:
            print(f"ERRO: {result['error']}")
        else:
            print(f"Chave gerada: {key}  |  nota: {args.note}")
```

- [ ] **Step 2: Commit**

```bash
git add license_server/keygen.py
git commit -m "feat: license key generator CLI"
```

---

## Task 4: Render deployment config

**Files:**
- Create: `license_server/render.yaml`

- [ ] **Step 1: Create render.yaml**

```yaml
# license_server/render.yaml
services:
  - type: web
    name: pdf-ocr-license
    runtime: python
    rootDir: license_server
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ADMIN_TOKEN
        generateValue: true
      - key: DB_PATH
        value: /data/licenses.db
    disk:
      name: licenses-data
      mountPath: /data
      sizeGB: 1
```

- [ ] **Step 2: Commit**

```bash
git add license_server/render.yaml
git commit -m "feat: render deployment config for license server"
```

---

## Task 5: Deploy no Render

- [ ] **Step 1: Acessar render.com e criar conta gratuita** (se não tiver)

- [ ] **Step 2: Criar novo Web Service**
  - Dashboard → "New" → "Web Service"
  - Conectar repositório GitHub: `nicolastd5/pdf-ocr`
  - Root Directory: `license_server`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

- [ ] **Step 3: Configurar variável de ambiente**
  - Em "Environment" adicionar:
    - `ADMIN_TOKEN` = uma senha forte (ex: gerada em https://passwordsgenerator.net/)
    - `DB_PATH` = `/data/licenses.db`

- [ ] **Step 4: Adicionar disco persistente**
  - Em "Disks" → Add Disk
  - Name: `licenses-data`, Mount Path: `/data`, Size: 1 GB

- [ ] **Step 5: Deploy e anotar a URL**
  - Clicar "Deploy"
  - Após ~2 minutos, anotar a URL: `https://pdf-ocr-license.onrender.com`

- [ ] **Step 6: Testar health check**
  ```
  curl https://pdf-ocr-license.onrender.com/health
  # Esperado: {"status":"ok"}
  ```

---

## Task 6: Modificar pdf_ocr.py — hardware ID e verificação de licença

**Files:**
- Modify: `pdf_ocr.py`

- [ ] **Step 1: Adicionar constantes e helper de hardware ID** (após linha com `GITHUB_RELEASES_PAGE`)

```python
LICENSE_SERVER = "https://pdf-ocr-license.onrender.com"
LICENSE_FILE_NAME = "pdf_ocr_license.json"


def _get_hw_id():
    """Gera um ID estável baseado no nome do computador + username."""
    import hashlib
    raw = f"{os.environ.get('COMPUTERNAME','')}-{os.environ.get('USERNAME','')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _license_path():
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                           else os.path.abspath(__file__))
    return os.path.join(base, LICENSE_FILE_NAME)


def _load_license():
    """Retorna {'key': ..., 'hw_id': ...} ou None."""
    try:
        with open(_license_path()) as f:
            return json.load(f)
    except Exception:
        return None


def _save_license(key: str, hw_id: str):
    with open(_license_path(), "w") as f:
        json.dump({"key": key, "hw_id": hw_id}, f)


def validate_license_online(key: str, hw_id: str):
    """
    Retorna (True, mensagem) ou (False, mensagem_de_erro).
    """
    import urllib.request, urllib.error, json as _json
    payload = _json.dumps({"key": key, "hw_id": hw_id}).encode()
    req = urllib.request.Request(
        f"{LICENSE_SERVER}/validate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            return True, data.get("message", "OK")
    except urllib.error.HTTPError as e:
        try:
            detail = _json.loads(e.read()).get("detail", str(e))
        except Exception:
            detail = str(e)
        return False, detail
    except Exception as e:
        return False, f"Sem conexão com servidor de licenças: {e}"
```

- [ ] **Step 2: Commit**

```bash
git add pdf_ocr.py
git commit -m "feat: add hardware ID and license validation helpers"
```

---

## Task 7: Diálogo de ativação de licença

**Files:**
- Modify: `pdf_ocr.py` — adicionar classe `LicenseDialog` antes de `PDFOcrApp`

- [ ] **Step 1: Adicionar classe LicenseDialog**

```python
class LicenseDialog(tk.Toplevel):
    """Tela de ativação de licença mostrada quando não há licença válida."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ativar PDF OCR")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.result = False  # True se ativação ok

        hw_id = _get_hw_id()

        # ── Layout ──────────────────────────────────────────────
        wrap = tk.Frame(self, bg=C["bg"], padx=32, pady=24)
        wrap.pack()

        tk.Label(wrap, text="PDF OCR", font=("Segoe UI", 18, "bold"),
                 bg=C["bg"], fg=C["accent"]).pack(pady=(0, 4))
        tk.Label(wrap, text="Ativação de Licença",
                 font=("Segoe UI", 11), bg=C["bg"], fg=C["fg"]).pack(pady=(0, 20))

        # Hardware ID (somente leitura, para o usuário enviar ao admin)
        hw_frame = tk.Frame(wrap, bg=C["panel"], bd=0, highlightthickness=1,
                            highlightbackground=C["border"])
        hw_frame.pack(fill="x", pady=(0, 16))
        tk.Label(hw_frame, text="Seu ID de computador:",
                 bg=C["panel"], fg=C["fg_dim"],
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=10, pady=(8, 0))
        hw_entry = tk.Entry(hw_frame, font=("Consolas", 9))
        _style_entry(hw_entry)
        hw_entry.configure(state="normal")
        hw_entry.insert(0, hw_id)
        hw_entry.configure(state="readonly")
        hw_entry.pack(fill="x", padx=10, pady=(2, 8))

        # Botão copiar ID
        def _copy_hw():
            self.clipboard_clear()
            self.clipboard_append(hw_id)
            copy_btn.configure(text="Copiado!")
            self.after(2000, lambda: copy_btn.configure(text="Copiar ID"))
        copy_btn = _flat_btn(hw_frame, "Copiar ID", _copy_hw,
                             font=("Segoe UI", 8))
        copy_btn.configure(bg=C["input"])
        copy_btn.pack(anchor="e", padx=10, pady=(0, 8))

        # Campo de chave
        tk.Label(wrap, text="Chave de licença:",
                 bg=C["bg"], fg=C["fg"], font=("Segoe UI", 10), anchor="w").pack(fill="x")
        self.key_entry = tk.Entry(wrap, font=("Consolas", 11), width=36)
        _style_entry(self.key_entry)
        self.key_entry.pack(fill="x", pady=(4, 4))
        self.key_entry.bind("<Return>", lambda _: self._activate())

        # Exemplo de formato
        tk.Label(wrap, text="Formato: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
                 bg=C["bg"], fg=C["fg_dim"], font=("Segoe UI", 8)).pack(anchor="w")

        # Status
        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(wrap, textvariable=self.status_var,
                                   bg=C["bg"], fg=C["error"],
                                   font=("Segoe UI", 9), wraplength=320)
        self.status_lbl.pack(pady=(8, 0))

        # Botão ativar
        self.activate_btn = _accent_btn(wrap, "Ativar", self._activate,
                                        font=("Segoe UI", 11, "bold"))
        self.activate_btn.pack(fill="x", pady=(16, 0), ipady=6)

        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _activate(self):
        key = self.key_entry.get().strip().upper()
        if not key:
            self.status_var.set("Digite a chave de licença.")
            return
        self.activate_btn.configure(state="disabled", text="Verificando...")
        self.status_var.set("")
        hw_id = _get_hw_id()

        def _check():
            ok, msg = validate_license_online(key, hw_id)
            def _done():
                self.activate_btn.configure(state="normal", text="Ativar")
                if ok:
                    _save_license(key, hw_id)
                    self.result = True
                    self.destroy()
                else:
                    self.status_lbl.configure(fg=C["error"])
                    self.status_var.set(f"Erro: {msg}")
            self.after(0, _done)

        threading.Thread(target=_check, daemon=True).start()

    def _on_close(self):
        self.result = False
        self.destroy()
```

- [ ] **Step 2: Adicionar `_flat_btn` helper** (antes de `LicenseDialog`, junto com `_accent_btn`)

```python
def _flat_btn(parent, text, command, font=None, **kw):
    font = font or ("Segoe UI", 10)
    btn = tk.Button(
        parent, text=text, command=command,
        bg=C["input"], fg=C["fg"],
        activebackground=C["hover"], activeforeground=C["fg_bright"],
        relief="flat", bd=0, cursor="hand2",
        font=font, **kw
    )
    return btn
```

- [ ] **Step 3: Commit**

```bash
git add pdf_ocr.py
git commit -m "feat: license activation dialog"
```

---

## Task 8: Integrar verificação de licença na inicialização do app

**Files:**
- Modify: `pdf_ocr.py` — método `__init__` de `PDFOcrApp` e bloco `if __name__ == "__main__"`

- [ ] **Step 1: Substituir o bloco principal**

Localizar o bloco final do arquivo:
```python
if __name__ == "__main__":
    app = PDFOcrApp()
    app.mainloop()
```

Substituir por:
```python
if __name__ == "__main__":
    # Verificação de licença antes de abrir o app principal
    _root = tk.Tk()
    _root.withdraw()  # Esconde janela vazia

    license_ok = False
    saved = _load_license()
    if saved:
        ok, _ = validate_license_online(saved["key"], saved["hw_id"])
        if ok:
            license_ok = True
        else:
            # Licença salva inválida/revogada — pede reativação
            dlg = LicenseDialog(_root)
            _root.wait_window(dlg)
            license_ok = dlg.result
    else:
        dlg = LicenseDialog(_root)
        _root.wait_window(dlg)
        license_ok = dlg.result

    _root.destroy()

    if not license_ok:
        sys.exit(0)

    app = PDFOcrApp()
    app.mainloop()
```

- [ ] **Step 2: Bump versão para 0.9**

Alterar:
```python
APP_VERSION = "0.8.1"
```
Para:
```python
APP_VERSION = "0.9"
```
E no docstring:
```python
PDF OCR v0.9
```

- [ ] **Step 3: Adicionar `pdf_ocr_license.json` ao .gitignore**

Abrir `.gitignore` e adicionar:
```
pdf_ocr_license.json
```

- [ ] **Step 4: Commit e tag**

```bash
git add pdf_ocr.py .gitignore
git commit -m "feat: license check on startup — v0.9"
git tag v0.9
git push origin master --tags
```

---

## Self-Review

**Spec coverage:**
- ✅ Servidor FastAPI com endpoints validate/generate/revoke/list
- ✅ Banco SQLite persistente no Render
- ✅ Script CLI para gerar chaves
- ✅ Vinculação por hardware ID (1 máquina por chave)
- ✅ Diálogo de ativação no app
- ✅ Verificação online a cada inicialização
- ✅ Deploy config para Render (free tier)

**Notas importantes:**
- O Render free tier hiberna após 15 min de inatividade — a primeira validação do dia pode demorar ~30s para "acordar" o servidor. Isso é aceitável para um produto pequeno.
- O `_get_hw_id()` usa `COMPUTERNAME + USERNAME` — simples e suficiente. Não usa MAC address (pode mudar com VMs/adapters).
- A licença fica salva em `pdf_ocr_license.json` ao lado do `.exe` — se o usuário mover o `.exe` para outra pasta, o arquivo vai junto.
