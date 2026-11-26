"""AUTOPILOT N1 v1: fila local, serial, sem APIs pagas."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "Downloads" / "AUTOPILOT_N1"
ENGINE = Path(__file__).resolve().with_name("editor_n1_v14.py")
EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

def save(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                        "-of", "json", str(path)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    if not any(s["codec_type"] == "audio" for s in d["streams"]):
        raise ValueError("Sem audio")
    if (v["width"], v["height"]) != (1080, 1920):
        raise ValueError("Resolucao inesperada")
    if float(d["format"]["duration"]) <= 0:
        raise ValueError("Duracao invalida")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(path),
                    "-f", "null", "-"], check=True)
    return {"duracao": float(d["format"]["duration"]), "largura": v["width"], "altura": v["height"]}

def run_job(source, key, root):
    status = root / "Relatorios" / (key + ".json")
    out = root / "Prontos" / (key + ".mp4")
    work = root / "Processando" / key
    work.mkdir(exist_ok=True)
    candidate = work / "video.mp4"
    log = root / "Relatorios" / (key + ".log")
    if status.exists():
        return
    state = {"arquivo": str(source), "estado": "processando", "inicio": time.time(),
             "motor": "V14", "referencia_aplicada": False}
    save(status, state)
    try:
        if out.exists() or candidate.exists():
            raise ValueError("Saida anterior encontrada; preserve os arquivos para revisao")
        with log.open("w", encoding="utf-8") as f:
            subprocess.run([sys.executable, str(ENGINE), str(source), str(candidate)],
                           stdout=f, stderr=subprocess.STDOUT, check=True)
        state["validacao"] = probe(candidate)
        os.replace(candidate, out)
        report = candidate.with_suffix(".direcao.json")
        if report.exists():
            shutil.copy2(report, root / "Relatorios" / (key + ".direcao.json"))
        state.update(estado="pronto", saida=str(out))
        print("PRONTO:", out, flush=True)
        try:
            import winsound
            winsound.MessageBeep()
        except Exception:
            pass
    except Exception as e:
        state.update(estado="erro", erro=str(e))
        print("ERRO:", source.name, str(e), flush=True)
    finally:
        state["fim"] = time.time()
        save(status, state)

def main():
    import hashlib
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args()
    root = a.root.resolve()
    for name in ("Entrada", "Prontos", "Processando", "Relatorios", "Referencias"):
        (root / name).mkdir(parents=True, exist_ok=True)
    if not ENGINE.exists() or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("Motor V14, ffmpeg ou ffprobe ausente.")
    lock = (root / "autopilot.lock").open("a+b")
    if os.name == "nt":
        import msvcrt
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit("Outra instancia ja esta ativa.")
    else:
        import fcntl
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print("AUTOPILOT N1:", root, flush=True)
    print("Copie videos para Entrada. Originais preservados. Ctrl+C encerra.", flush=True)
    print("V1 usa V14; pasta Referencias reservada, ainda nao aplicada.", flush=True)
    seen = {}
    try:
        while True:
            now = time.monotonic()
            for f in sorted((root / "Entrada").iterdir()):
                if not f.is_file() or f.suffix.lower() not in EXT:
                    continue
                try:
                    s = f.stat()
                    sig = (s.st_size, s.st_mtime_ns)
                    old = seen.get(f)
                    if old is None or old[0] != sig:
                        seen[f] = (sig, now)
                        continue
                    if now - old[1] < 15 or not s.st_size:
                        continue
                    key = f.stem[:65] + "_" + hashlib.sha256(
                        (f.name + str(sig)).encode()).hexdigest()[:12]
                    run_job(f, key, root)
                except OSError as e:
                    print("Arquivo indisponivel:", f.name, e, flush=True)
            if a.once and seen and all(time.monotonic()-v[1]>=15 for v in seen.values()):
                break
            if a.once and not seen:
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print("Encerrado.")
    finally:
        lock.close()

if __name__ == "__main__":
    main()
