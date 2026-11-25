from pathlib import Path
import urllib.request, subprocess, sys, json, tempfile, os, wave
ROOT=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
BASE="https://raw.githubusercontent.com/fabiosousan1/ESTILO-CLOUD-N1/main/ponte-windows/"
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    report={}
    for name in ("biblioteca_n1.py","paletas_n1.py","efeitos_n1.py","instalador_recursos_n1.py"):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/name
                with urllib.request.urlopen(BASE+name,timeout=60) as r:
                    data=r.read()
                compile(data,name,"exec")
                p.write_bytes(data)
                # The unified installer fetches its own dependencies into this temporary directory.
                subprocess.run([sys.executable,str(p)],check=True)
            report[name]="ok"
        except Exception as e:
            report[name]=str(e)
    counts={}
    errors=[]
    for folder in ROOT.iterdir():
        if not folder.is_dir(): continue
        count=0
        for p in folder.rglob("*"):
            if not p.is_file(): continue
            try:
                if p.suffix.lower()==".json": json.loads(p.read_text(encoding="utf-8"))
                elif p.suffix.lower()==".wav":
                    with wave.open(str(p)) as w:
                        if w.getnframes()==0: raise ValueError("WAV vazio")
                elif p.suffix.lower() in (".ttf",".otf"):
                    with p.open("rb") as f:
                        if f.read(4) not in (b"\x00\x01\x00\x00",b"OTTO",b"true",b"ttcf"): raise ValueError("Cabecalho de fonte invalido")
                else: continue
                count+=1
            except Exception as e: errors.append({"file":str(p),"error":str(e)})
        counts[folder.name]=count
    result={"stages":report,"validated_files":counts,"errors":errors,"pending":["fontes faltantes","texturas","elementos graficos","3D","validacao visual","integracao editor"]}
    target=ROOT/"relatorio_instalacao.json"
    temp=target.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    os.replace(temp,target)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("Relatorio:",target)
    if errors or any(v!="ok" for v in report.values()): sys.exit(1)
if __name__=="__main__": main()
