from pathlib import Path
import json
import itertools

ROOT = Path.home() / "Downloads" / "ESTILO_N1_Referencias"
FOLDERS = ["Fontes","Paletas","Legendas_Profissionais","Efeitos_Tipograficos","Animacoes","Efeitos_Sonoros","Transicoes","Elementos_3D","Elementos_Graficos","Filtros","Texturas","Movimentos_Camera","Modelos_Edicao","pinterest"]
PALETTES = {"autoridade":["#FFFFFF","#B5E66B","#171717"],"vendas":["#FFFFFF","#FF9234","#171717"],"viral":["#FFFFFF","#FFDE00","#171717"],"cinema":["#FFFFFF","#D4AF37","#171717"],"alerta":["#FFFFFF","#FF3131","#171717"],"minimal":["#FFFFFF","#CCCCCC","#171717"]}
FONTS = ["Arial","Impact","Georgia","Verdana","Montserrat","Poppins","Anton","Bebas Neue","Inter","Oswald"]
MOTIONS = ["pop","pulse","slide","fade","glow","clean"]
def save(path, data):
    if not path.exists():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
def main():
    for name in FOLDERS:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    for name, colors in PALETTES.items():
        save(ROOT / "Paletas" / (name+".json"), {"id":name,"colors":colors})
    for i,(font,palette,motion) in enumerate(itertools.product(FONTS, PALETTES, MOTIONS),1):
        save(ROOT / "Legendas_Profissionais" / ("n1_%03d.json"%i), {"id":"n1_%03d"%i,"font":font,"fallback":"Arial","palette":palette,"motion":motion,"size":96,"active_size":108,"words":3,"position":[540,1460],"status":"preset_config_only"})
    save(ROOT / "catalogo.json", {"version":1,"folders":FOLDERS,"caption_configurations":360,"palettes":6,"font_candidates":FONTS,"note":"Configuracoes originais; fontes externas e midias nao incluidas. Integracao com renderizador pendente."})
    print("Biblioteca N1:",ROOT)
    print("360 configuracoes de legenda, 6 paletas. Arquivos existentes preservados.")
if __name__ == "__main__":
    main()
