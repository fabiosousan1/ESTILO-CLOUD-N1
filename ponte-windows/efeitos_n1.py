from pathlib import Path
import json

ROOT = Path.home() / "Downloads" / "ESTILO_N1_Referencias"
# ASS/libass override tags, usable with FFmpeg's ass filter.
MOTIONS = {
"pop": r"\fscx75\fscy75\t(0,150,\fscx100\fscy100)",
"pulse": r"\t(0,120,\fscx115\fscy115)\t(120,240,\fscx100\fscy100)",
"slide_up": r"\move(540,1530,540,1460,0,180)",
"slide_down": r"\move(540,1390,540,1460,0,180)",
"slide_left": r"\move(420,1460,540,1460,0,180)",
"slide_right": r"\move(660,1460,540,1460,0,180)",
"fade": r"\fad(120,100)",
"rotate": r"\frz-12\t(0,180,\frz0)",
"bounce": r"\fscx80\fscy80\t(0,100,\fscx115\fscy115)\t(100,220,\fscx100\fscy100)",
"stretch": r"\fscx65\fscy120\t(0,180,\fscx100\fscy100)",
"blur_reveal": r"\blur8\t(0,200,\blur0)",
"perspective": r"\fry45\t(0,200,\fry0)",
"tracking": r"\fsp15\t(0,200,\fsp0)",
"shrink": r"\fscx125\fscy125\t(0,180,\fscx100\fscy100)",
"flip": r"\frx75\t(0,220,\frx0)",
"clean": ""
}
LOOKS = {
"clean": r"\bord3\shad1",
"bold_outline": r"\bord7\shad0",
"neon_green": r"\bord7\3c&H45FF39&\blur3\shad0",
"neon_pink": r"\bord7\3c&HA800FF&\blur3\shad0",
"gold": r"\c&H37AFD4&\3c&H17394F&\bord4\shad3",
"deep_shadow": r"\bord3\xshad6\yshad8",
"outline_only": r"\1a&HFF&\bord4\shad0",
"soft_shadow": r"\bord2\shad5\blur1",
"wide": r"\fsp5\bord3",
"red_impact": r"\c&H3131FF&\bord5\shad2"
}
def save(path, data):
    if not path.exists():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
def main():
    for folder in ("Animacoes","Efeitos_Tipograficos","Legendas_Profissionais"):
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    for name,tags in MOTIONS.items():
        save(ROOT/"Animacoes"/("motion_"+name+".json"),{"id":name,"engine":"libass","tags":tags,"minimum_duration_ms":250})
    for name,tags in LOOKS.items():
        save(ROOT/"Efeitos_Tipograficos"/("look_"+name+".json"),{"id":name,"engine":"libass","tags":tags})
    for motion,mt in MOTIONS.items():
        for look,lt in LOOKS.items():
            key="fx_"+motion+"_"+look
            save(ROOT/"Legendas_Profissionais"/(key+".json"),{"id":key,"engine":"libass","motion":motion,"look":look,"ass_tags":lt+mt,"font":"Arial","size":96,"position":[540,1460],"minimum_duration_ms":250})
    print("16 movimentos, 10 efeitos visuais, 160 combinacoes ASS.")
    print("Biblioteca:",ROOT)
    print("Presets originais. Integracao e teste visual pendentes.")
if __name__=="__main__":
    main()
