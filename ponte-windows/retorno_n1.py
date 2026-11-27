"""Publica somente estados de tarefas N1, nunca logs ou dados pessoais."""
import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

REPO = "fabiosousan1/ESTILO-CLOUD-N1"
STATE = Path.home() / ".n1-codex"
VALID = {"executado", "erro", "pendente", "executando"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--publicar", action="store_true")
    p.add_argument("--continuo", action="store_true")
    a = p.parse_args()
    gh = shutil.which("gh")
    if a.publicar and not gh:
        raise SystemExit("GitHub CLI gh ausente. Nenhum dado enviado.")
    if a.publicar:
        subprocess.run([gh, "auth", "status"], check=True)
    sent = set()
    while True:
        for f in sorted(STATE.glob("n1-*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8-sig"))
                ident = d.get("id")
                status = d.get("estado")
                code = d.get("codigo")
                if not isinstance(ident, str) or not re.fullmatch(r"n1-[a-z0-9-]{1,55}", ident):
                    continue
                if f.stem != ident or status not in VALID:
                    continue
                if status not in {"executado", "erro"}:
                    continue
                clean = {"id": ident, "estado": status}
                if type(code) is int:
                    clean["codigo"] = code
                payload = json.dumps(clean, ensure_ascii=True)
                if payload in sent:
                    continue
                print(payload, flush=True)
                if a.publicar:
                    title = "N1 retorno " + ident
                    found = subprocess.run([gh, "issue", "list", "--repo", REPO,
                        "--state", "all", "--search", title + " in:title", "--json", "title"],
                        capture_output=True, text=True, check=True)
                    if not any(x.get("title") == title for x in json.loads(found.stdout)):
                        subprocess.run([gh, "issue", "create", "--repo", REPO,
                            "--title", title, "--body", payload], check=True)
                sent.add(payload)
            except Exception as e:
                print("Retorno:", type(e).__name__, flush=True)
        if not a.continuo:
            break
        time.sleep(30)
if __name__ == "__main__":
    main()
