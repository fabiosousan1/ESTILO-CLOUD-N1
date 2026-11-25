from pathlib import Path
import urllib.request
import subprocess
import sys
import json
import math
import wave
import struct
import random

ROOT=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
BASE="https://raw.githubusercontent.com/fabiosousan1/ESTILO-CLOUD-N1/main/ponte-windows/"
def save(folder,name,data):
    p=ROOT/folder/(name+".json")
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists(): p.write_text(json.dumps(data,indent=2),encoding="utf-8")
def main():
    for script in ("biblioteca_n1.py","paletas_n1.py","efeitos_n1.py"):
        try:
            p=Path(__file__).resolve().parent/script
            urllib.request.urlretrieve(BASE+script,p)
            subprocess.run([sys.executable,str(p)],check=True)
        except Exception as e: print("PENDENTE",script,e)
    for name in ("fade","wipeleft","wiperight","wipeup","wipedown","slideleft","slideright","slideup","slidedown","circleopen","circleclose","dissolve","pixelize","smoothleft","smoothright"):
        for ms in (200,350,500):
            save("Transicoes",f"{name}_{ms}",{"engine":"ffmpeg_xfade","transition":name,"duration":ms/1000})
    for name,expr in {"warm":"colorbalance=rs=.06:bs=-.05","cool":"colorbalance=rs=-.05:bs=.06","mono":"hue=s=0","contrast":"eq=contrast=1.15","soft":"eq=contrast=.9:saturation=.85","vivid":"eq=saturation=1.25"}.items():
        save("Filtros",name,{"engine":"ffmpeg","filter":expr})
    for name in ("push_in","pull_out","pan_left","pan_right","tilt_up","tilt_down"):
        for strength in (.02,.05,.08):
            save("Movimentos_Camera",f"{name}_{strength}",{"motion":name,"strength":strength,"status":"configuration"})
    folder=ROOT/"Efeitos_Sonoros"
    folder.mkdir(parents=True,exist_ok=True)
    rng=random.Random(42)
    for kind in ("click","pop","whoosh","rise","impact"):
        for variant in range(10):
            p=folder/f"{kind}_{variant+1:02}.wav"
            if p.exists(): continue
            rate=44100
            dur=.12+variant*.025 if kind in ("click","pop") else .35+variant*.045
            samples=[]
            phase=0
            for i in range(int(rate*dur)):
                t=i/rate; u=t/dur
                env=min(1,t/.008)*max(0,1-u)**2
                freq=(800+variant*70)*(1-u)+90 if kind in ("pop","impact") else 200+u*(1200+variant*100)
                phase+=2*math.pi*freq/rate
                noise=rng.uniform(-1,1)
                signal=noise*.65 if kind=="whoosh" else math.sin(phase)*.65+noise*.1
                if kind=="click": signal=noise*.6
                samples.append(int(14000*env*signal))
            with wave.open(str(p),"wb") as w:
                w.setparams((1,2,rate,0,"NONE","not compressed"))
                w.writeframes(struct.pack("<"+"h"*len(samples),*samples))
    print("45 configuracoes de transicao, 6 filtros, 18 movimentos de camera e 50 WAV sinteticos.")
    print("Fontes pendentes, texturas, elementos graficos e 3D externos ainda nao incluidos.")
    print("Biblioteca:",ROOT)
if __name__=="__main__": main()
