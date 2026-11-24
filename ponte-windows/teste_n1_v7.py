import argparse
import subprocess
from pathlib import Path
import cv2
import statistics

p=argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("saida")
a=p.parse_args()
src,dst=Path(a.video).resolve(),Path(a.saida).resolve()
if src==dst or dst.exists():
    raise ValueError("Escolha uma nova saida.")
cap=cv2.VideoCapture(str(src))
det=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
faces=[]
w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
try:
    for t in range(10):
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000)
        ok,f=cap.read()
        if not ok: continue
        h,w=f.shape[:2]
        gray=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        found=det.detectMultiScale(gray,1.1,5)
        if len(found):
            x,y,fw,fh=max(found,key=lambda r:r[2]*r[3])
            faces.append((x+fw/2,y+fh/2,fw,fh))
finally:
    cap.release()
if min(w,h)<16: raise ValueError("Video invalido")
cw=int(min(w,h*9/16)//2)*2
ch=int(min(h,w*16/9)//2)*2
cx=statistics.median(f[0] for f in faces) if faces else w/2
cy=statistics.median(f[1] for f in faces) if faces else h/2
x=int(max(0,min(w-cw,cx-cw/2))//2)*2
y=int(max(0,min(h-ch,cy-ch*.35))//2)*2
print("Faces detectadas:",len(faces),flush=True)
subprocess.run(["ffmpeg","-nostdin","-n","-i",str(src),"-t","10","-vf",f"crop={cw}:{ch}:{x}:{y},scale=1080:1920,setsar=1","-r","30","-c:v","libx264","-preset","fast","-crf","19","-c:a","aac","-movflags","+faststart",str(dst)],check=True)
print("TESTE N1 V7 OK:",dst)
