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
