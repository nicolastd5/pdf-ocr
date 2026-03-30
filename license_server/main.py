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
