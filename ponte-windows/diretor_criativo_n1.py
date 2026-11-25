from pathlib import Path
import json, argparse, re

KEYWORDS={"vendas","vender","clientes","dinheiro","resultado","resultados","conteúdo","instagram","marketing","sucesso","crescer","estratégia","negócio"}
def direction(data):
    scenes=[]
    for i,s in enumerate(data["cenas"]):
        words=s.get("palavras",[])
        text=" ".join(str(w["texto"]) for w in words)
        hits=[w for w in words if re.sub(r"[^\w]","",str(w["texto"]).lower()) in KEYWORDS or any(ch.isdigit() for ch in str(w["texto"]))]
        role="gancho" if i==0 else "convite" if re.search(r"\b(siga|comente|salve|clique)\b",text.lower()) else "enfase" if hits else "explicacao"
        scenes.append({"inicio":s["inicio"],"fim":s["fim"],"texto":text,"funcao":role,"legenda":{"layout":"horizontal","fontes":["Montserrat","Anton"],"paleta":["#FFFFFF","#B5E66B","#F28C28"],"palavras_destaque":hits,"movimento":"pop" if hits else "clean"},"camera":{"motion":"stable","zoom_max":1.012},"audio_candidato": {"tipo":"pop","inicio":hits[0]["inicio"]} if hits and role!="convite" else None,"overlay_candidato":str(hits[0]["texto"]) if hits else None})
    return {"version":1,"method":"heuristic","cenas":scenes,"pending":["semantic headline","reference analysis","segmentation","audio and overlay rendering"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("plano")
    p.add_argument("saida")
    a=p.parse_args()
    source,target=Path(a.plano).resolve(),Path(a.saida).resolve()
    if source==target or target.exists(): raise ValueError("Escolha nova saida")
    result=direction(json.loads(source.read_text(encoding="utf-8")))
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Direcao N1:",target,len(result["cenas"]),"cenas")
if __name__=="__main__": main()
