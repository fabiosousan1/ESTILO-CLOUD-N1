import argparse
import json
import subprocess
import tempfile
from pathlib import Path

def stamp(t):
    n = max(0, round(t*100))
    return f"{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}"

def safe(s):
    return str(s).replace("\\", "").replace("{", "").replace("}", "").replace("\n", " ")

def render(video, plan, output):
    video, plan, output = map(lambda p: Path(p).resolve(), (video, plan, output))
    if output in (video, plan) or output.exists():
        raise ValueError("Escolha um novo arquivo de saída.")
    data = json.loads(plan.read_text(encoding="utf-8"))
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,60,&H00FFFFFF,&H006BE6B5,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,100,100,420,1
Style: Title,Arial,65,&H00288CF2,&H00FFFFFF,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,8,90,90,220,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    def add(a,b,style,text):
        if b-a >= .01:
            events.append(f"Dialogue: 0,{stamp(a)},{stamp(b)},{style},,0,0,0,,{text}")
    keywords = {"instagram","carreira","resultado","jornada","tendência","anunciar","sucesso","importante"}
    for scene in data["cenas"]:
        words = scene["palavras"]
        for offset in range(0,len(words),3):
            group = words[offset:offset+3]
            for i,w in enumerate(group):
                a = float(w["inicio"])
                b = float(group[i+1]["inicio"]) if i+1<len(group) else float(w["fim"])
                if b <= a:
                    continue
                parts = []
                for j,x in enumerate(group):
                    color = r"{\c&H6BE6B5&}" if j==i else r"{\c&HFFFFFF&}"
                    parts.append(color+safe(x["texto"]))
                add(a,b,"Caption"," ".join(parts))
        hits = [w for w in words if w["texto"].lower().strip(".,?!") in keywords]
        if hits:
            w=hits[0]
            add(float(w["inicio"]),min(float(scene["fim"])+.4,float(w["inicio"])+1.6),"Title",r"{\fad(120,180)\fscx85\fscy85\t(0,180,\fscx100\fscy100)}"+safe(w["texto"].strip(".,?!").upper()))
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp,"captions.ass").write_text(header+"\n".join(events),encoding="utf-8")
        vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x171717,setsar=1,ass=captions.ass"
        subprocess.run(["ffmpeg","-nostdin","-n","-i",str(video),"-vf",vf,"-c:v","libx264","-preset","fast","-crf","20","-c:a","aac","-b:a","192k","-movflags","+faststart",str(output)],cwd=tmp,check=True)
    print("RENDER N1 V4 OK:",output)

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("plano")
    p.add_argument("saida")
    a=p.parse_args()
    render(a.video,a.plano,a.saida)
