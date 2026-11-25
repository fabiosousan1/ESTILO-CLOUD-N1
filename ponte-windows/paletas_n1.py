from pathlib import Path
import colorsys
import json

ROOT = Path.home() / "Downloads" / "ESTILO_N1_Referencias" / "Paletas"
THEMES = ["autoridade","vendas","viral","cinema","luxo","educacao","tecnologia","storytelling","minimalista","neon"]
HUES = [0.0,0.045,0.085,0.13,0.22,0.32,0.43,0.68,0.78,0.92]
def color(h,s,l):
    return "#" + "".join(f"{round(v*255):02X}" for v in colorsys.hls_to_rgb(h%1,l,s))
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    for i,theme in enumerate(THEMES):
        for j in range(20):
            h = (HUES[j%10]+i*0.017)%1
            s = 0.45+0.045*i
            accent = color(h,s,0.65 if j<10 else 0.78)
            secondary = color(h+0.12,s,0.72)
            dark = color(h,0.22,0.09)
            data = {"id":f"{theme}_{j+1:02}","theme":theme,"primary":"#FFFFFF","accent":accent,"secondary":secondary,"outline":dark,"shadow":"#000000","background":dark,"gradient":[accent,secondary]}
            path = ROOT / (data["id"]+".json")
            if not path.exists():
                path.write_text(json.dumps(data,indent=2),encoding="utf-8")
    print("200 novas paletas N1 geradas; arquivos existentes preservados.")
if __name__ == "__main__":
    main()
