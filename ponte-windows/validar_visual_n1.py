from pathlib import Path
import json, subprocess, tempfile, shutil, html
ROOT=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
OUT=ROOT/"Previews"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for p in sorted((ROOT/"Legendas_Profissionais").glob("*.json")):
        try:
            d=json.loads(p.read_text(encoding="utf-8"))
            tags=d.get("ass_tags")
            if tags is None:
                rows.append({"id":p.stem,"status":"pending_renderer"})
                continue
            target=OUT/(p.stem+".mp4")
            header="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,80,80,460,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            if not target.exists():
                with tempfile.TemporaryDirectory() as tmp:
                    Path(tmp,"test.ass").write_text(header+"Dialogue: 0,0:00:00.00,0:00:01.50,Default,,0,0,0,,{"+tags+"}CRIE CONTEÚDO\n",encoding="utf-8")
                    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=0x303030:s=360x640:r=24:d=1.5","-vf","ass=test.ass","-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",str(target)],cwd=tmp,check=True)
            subprocess.run(["ffmpeg","-v","error","-i",str(target),"-f","null","-"],check=True)
            rows.append({"id":p.stem,"status":"rendered_pending_visual_review","file":target.name})
        except Exception as e:
            rows.append({"id":p.stem,"status":"error","error":str(e)})
        print(p.stem,rows[-1]["status"],flush=True)
    (OUT/"relatorio.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    cards=[]
    for r in rows:
        if "file" in r:
            cards.append('<article><video controls preload="none" src="'+html.escape(r["file"],quote=True)+'"></video><p>'+html.escape(r["id"])+'</p></article>')
    (OUT/"catalogo.html").write_text('<meta charset="utf-8"><title>N1 Previews</title><style>body{background:#171717;color:white;font:16px Arial}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}video{width:100%}</style><h1>Previews N1</h1><main>'+''.join(cards)+'</main>',encoding="utf-8")
    print("Catalogo:",OUT/"catalogo.html")
if __name__=="__main__": main()
