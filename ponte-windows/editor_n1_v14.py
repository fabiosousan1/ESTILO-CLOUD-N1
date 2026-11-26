from editor_n1_v12 import edit, stamp, safe
from diretor_criativo_n1 import direction
from plano_n1 import plan
from pathlib import Path
import argparse,json,tempfile,subprocess,shutil

def main():
    p=argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("saida")
    a=p.parse_args()
    source,target=Path(a.video).resolve(),Path(a.saida).resolve()
    if target.exists() or source==target: raise ValueError("Escolha uma nova saida")
    report=target.with_suffix(".direcao.json")
    if report.exists(): raise ValueError("Relatorio ja existe")
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp,"base.mp4")
        edit(source,base,False)
        data=plan(str(base))
        creative=direction(data)
        events=[]
        fontdir=Path(tmp,"fonts")
        fontdir.mkdir()
        font="Arial"
        from fontTools.ttLib import TTFont
        for f in (Path.home()/"Downloads"/"ESTILO_N1_Referencias"/"Fontes").rglob("*.ttf"):
            try:
                with TTFont(f,lazy=True) as ft:
                    name=ft["name"].getDebugName(1)
                if name=="Montserrat":
                    shutil.copy2(f,fontdir/f.name)
                    font=name
                    break
            except Exception:
                continue
        last_graph=-10
        for s,d in zip(data["cenas"],creative["cenas"]):
            words=s["palavras"]
            highlights={str(w["texto"]) for w in d["legenda"]["palavras_destaque"]}
            for i in range(0,len(words),2):
                group=words[i:i+2]
                start=float(group[0]["inicio"])
                end=float(group[-1]["fim"])
                if end<=start: continue
                parts=[]
                if any(str(w["texto"]) in highlights for w in group) and start-last_graph>=3:
                    last_graph=start
                    events.append(f"Dialogue: 0,{stamp(start)},{stamp(min(end,start+.7))},Caption,,0,0,0,,"+r"{\an7\pos(90,1500)\bord0\shad0\c&H6BE6B5&\p1}m 0 0 l 180 0 180 10 0 10")
                size=min(120,int(1450/max(1,sum(len(str(w["texto"]))+1 for w in group))))
                for w in group:
                    hot=str(w["texto"]) in highlights
                    color="6BE6B5" if hot else "FFFFFF"
                    parts.append(r"{\c&H"+color+r"&\fs"+str(size)+"}"+safe(w["texto"]).upper())
                motion=r"\fscx94\fscy94\t(0,120,\fscx100\fscy100)" if d["legenda"]["movimento"]=="pop" else ""
                events.append(f"Dialogue: 0,{stamp(start)},{stamp(end)},Caption,,0,0,0,,"+r"{\an2\pos(540,1450)"+motion+"}"+" ".join(parts))
        header="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,120,&H00FFFFFF,&H00FFFFFF,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,420,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        Path(tmp,"captions.ass").write_text(header.replace("Caption,Arial,","Caption,"+font+",")+"\n".join(events),encoding="utf-8")
        subprocess.run(["ffmpeg","-nostdin","-n","-i",str(base),"-vf","ass=captions.ass:fontsdir=fonts","-c:v","libx264","-preset","fast","-crf","20","-af","aresample=async=1:first_pts=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000","-c:a","aac","-b:a","192k","-movflags","+faststart",str(target)],cwd=tmp,check=True)
        report.write_text(json.dumps(creative,ensure_ascii=False,indent=2),encoding="utf-8")
    print("V14 OK:",target,report)
if __name__=="__main__": main()
