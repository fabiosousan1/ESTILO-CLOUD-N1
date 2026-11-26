from pathlib import Path
import cv2
import numpy as np
import json

def analyze(path):
    cap=cv2.VideoCapture(str(path))
    fps=cap.get(cv2.CAP_PROP_FPS)
    count=cap.get(cv2.CAP_PROP_FRAME_COUNT)
    prev=None
    cuts=[]
    changes=[]
    colors=[]
    try:
        if not cap.isOpened() or fps<=0 or count<=0:
            raise ValueError("Video indisponivel")
        duration=count/fps
        for t in np.arange(0,min(duration,180),0.25):
            cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000)
            ok,frame=cap.read()
            if not ok: continue
            frame=cv2.resize(frame,(160,90))
            colors.append(frame.mean(axis=(0,1))[::-1].tolist())
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            if prev is not None:
                diff=float(cv2.absdiff(gray,prev).mean())
                changes.append(diff)
                if diff>35: cuts.append(round(float(t),2))
            prev=gray
        if not colors: raise ValueError("Sem quadros")
        return {"arquivo":path.name,"duracao":duration,"janela_analisada":min(duration,180),"mudancas_visuais_candidatas":cuts,"variacao_visual_media":float(np.mean(changes)) if changes else 0,"rgb_medio":np.mean(colors,axis=0).round().astype(int).tolist()}
    finally:
        cap.release()

def main():
    root=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
    results=[]
    for path in sorted((root/"pinterest").rglob("*.mp4")):
        try: results.append(analyze(path))
        except Exception as e: results.append({"arquivo":path.name,"erro":str(e)})
    out=root/"ANALISE_REFERENCIAS_N1.json"
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Referencias:",len(results),"Relatorio:",out)

if __name__=="__main__":
    main()
