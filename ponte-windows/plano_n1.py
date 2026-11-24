"""Planejador local experimental: transcrição e sugestões de edição, sem renderizar."""
import argparse
import json
import re
from pathlib import Path
from editor_n1_v3 import transcribe

def plan(video):
    words = transcribe(video, "small")
    scenes = []
    group = []
    for word in words:
        if group and (word[0]-group[-1][1] > .65 or word[1]-group[0][0] > 4 or re.search(r"[.!?]$",group[-1][2])):
            scenes.append(group)
            group = []
        group.append(word)
    if group:
        scenes.append(group)
    result = []
    for i, g in enumerate(scenes):
        phrase = " ".join(w[2] for w in g)
        numeric = bool(re.search(r"\d|\b(?:mil|milhão|milhões|por cento)\b", phrase, re.I))
        question = "?" in phrase
        contrast = bool(re.search(r"\b(?:mas|porém|nunca|atenção|importante|segredo)\b", phrase, re.I))
        effect = "numero_destaque" if numeric else "pergunta" if question else "zoom_sugerido" if contrast or i == 0 else "legenda"
        result.append({"inicio":round(g[0][0],3),"fim":round(g[-1][1],3),"fala":phrase,"efeito_sugerido":effect,"palavras":[{"inicio":round(w[0],3),"fim":round(w[1],3),"texto":w[2]} for w in g]})
    return {"versao":"4.0 experimental","estilo":"Professor Viral N1","paleta":["#FFFFFF","#B5E66B","#F28C28"],"metodo":"regras de texto; sugestões não renderizadas","cenas":result}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("saida")
    a = p.parse_args()
    source, target = Path(a.video).resolve(), Path(a.saida).resolve()
    if source == target or target.suffix.lower() != ".json":
        p.error("Escolha uma saída JSON diferente do vídeo.")
    data = plan(str(source))
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PLANO N1 OK:", len(data["cenas"]), "cenas", str(target))
