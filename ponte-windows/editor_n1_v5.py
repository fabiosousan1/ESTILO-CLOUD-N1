"""Pipeline experimental N1: reutiliza cortes v3 e render v4."""
import argparse
import tempfile
import json
from pathlib import Path
from editor_n1_v3 import edit
from plano_n1 import plan
from render_n1_v4 import render

def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("saida")
    a = p.parse_args()
    source, target = Path(a.video).resolve(), Path(a.saida).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if target.exists() or source == target:
        raise ValueError("Escolha um novo arquivo de saída.")
    with tempfile.TemporaryDirectory(prefix="n1_v5_") as tmp:
        base = Path(tmp, "base.mp4")
        plano = Path(tmp, "plano.json")
        print("N1 1/3: cortes e enquadramento", flush=True)
        result = edit(source, base, False)
        print("N1 2/3: transcricao apos os cortes", flush=True)
        data = plan(str(base))
        plano.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("N1 3/3: legendas e destaques", flush=True)
        render(base, plano, target)
        print("EDITOR N1 V5 OK:", result["clips"], "trechos;", len(data["cenas"]), "cenas")

if __name__ == "__main__":
    main()
