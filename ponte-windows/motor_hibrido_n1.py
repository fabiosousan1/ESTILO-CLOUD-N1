import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

LOCAL = {"edicao", "legendas", "cortes", "referencias"}
CLOUD = {"gerar_video", "gerar_imagem", "gerar_3d"}

def route(task):
    if task in LOCAL:
        return {"task":task,"engine":"local","available":bool(shutil.which("ffmpeg")),"cloud_cost":0}
    if task in CLOUD:
        return {"task":task,"engine":"cloud","available":False,"reason":"Provedor ainda nao configurado"}
    raise ValueError("Tarefa desconhecida")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("task",choices=sorted(LOCAL|CLOUD))
    p.add_argument("--video")
    p.add_argument("--saida")
    a=p.parse_args()
    status=route(a.task)
    print(json.dumps(status,ensure_ascii=False),flush=True)
    if not status["available"]:
        return 2
    root=Path(__file__).resolve().parent
    if a.task=="referencias":
        subprocess.run([sys.executable,str(root/"analisador_referencias_n1.py")],check=True)
    elif a.task=="edicao":
        if not a.video or not a.saida: p.error("Informe --video e --saida")
        subprocess.run([sys.executable,str(root/"editor_n1_v14.py"),a.video,a.saida],check=True)
    else:
        print("Rota reservada; execucao independente ainda nao integrada")
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
