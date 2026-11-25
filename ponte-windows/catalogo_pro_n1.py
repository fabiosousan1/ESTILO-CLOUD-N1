from pathlib import Path
import json, html, shutil
ROOT=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
OUT=ROOT/"Catalogo_Pro"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fonts=[]
    for p in sorted((ROOT/"Fontes").rglob("*")):
        if p.suffix.lower() in (".ttf",".otf"):
            fonts.append(p)
    palettes=[]
    for p in sorted((ROOT/"Paletas").glob("*.json")):
        try:
            d=json.loads(p.read_text(encoding="utf-8"))
            colors=d.get("colors") or [d["primary"],d["accent"],d["background"]]
            if len(colors)>=3 and all(len(x)==7 and x.startswith("#") and all(y in "0123456789abcdefABCDEF" for y in x[1:]) for x in colors):
                palettes.append((p.stem,colors))
        except Exception: pass
    if not fonts or not palettes: raise RuntimeError("Biblioteca de fontes ou paletas vazia")
    from urllib.parse import quote
    styles=[]
    for i,p in enumerate(fonts):
        url="../"+quote(p.relative_to(ROOT).as_posix())
        styles.append(f"@font-face{{font-family:n{i};src:url('{url}')}}")
    cards=[]
    for i in range(max(len(fonts),len(palettes))):
        fi=i%len(fonts); name,colors=palettes[i%len(palettes)]
        fg,accent,bg=colors[:3]
        motion=["pop","slide","pulse","reveal","glow","clean"][i%6]
        cards.append(f'<article data-search="{html.escape(fonts[fi].parent.name+" "+name+" "+motion,quote=True)}"><div class="preview {motion}" style="background:{bg};color:{fg};font-family:n{fi},Arial"><span>TRANSFORME</span><strong style="color:{accent}">CONTEÚDO</strong><span>EM RESULTADOS</span></div><small>{html.escape(fonts[fi].name)} | {html.escape(name)} | {motion}</small></article>')
    css="""body{background:#171717;color:white;font:16px Arial;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}article{background:#262626;padding:10px;border-radius:8px;overflow:hidden}.preview{aspect-ratio:9/16;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;text-align:center;font-size:18px;overflow:hidden}.preview strong{font-size:30px;max-width:100%;overflow-wrap:anywhere;text-shadow:1px 2px 3px #000}.preview span{font-size:16px}small{display:block;margin-top:8px;overflow-wrap:anywhere}input{padding:12px;width:min(90%,500px);margin-bottom:20px}.pop:hover strong{animation:pop .6s}.slide:hover strong{animation:slide .6s}.pulse:hover strong{animation:pulse .7s}.reveal:hover strong{animation:reveal .7s}.glow:hover strong{animation:glow .7s}@keyframes pop{0%{transform:scale(.6)}60%{transform:scale(1.12)}100%{transform:scale(1)}}@keyframes slide{from{transform:translateY(45px);opacity:0}}@keyframes pulse{50%{transform:scale(1.15)}}@keyframes reveal{from{clip-path:inset(0 100% 0 0)}}@keyframes glow{50%{text-shadow:0 0 15px currentColor}}"""
    page='<!doctype html><meta charset="utf-8"><title>Catalogo N1 Pro</title><style>'+css+''.join(styles)+'</style><h1>Biblioteca N1 Pro</h1><p>Previa HTML: passe o mouse para animar. Nao equivale a renderizacao FFmpeg.</p><input id="q" placeholder="Buscar fonte, paleta ou movimento"><main>'+''.join(cards)+'</main><script>document.getElementById("q").oninput=function(){for(const a of document.querySelectorAll("article"))a.hidden=!a.dataset.search.toLowerCase().includes(this.value.toLowerCase())}</script>'
    (OUT/"index.html").write_text(page,encoding="utf-8")
    print("Arquivos de fontes:",len(fonts),"Paletas:",len(palettes),"Previews HTML:",len(cards))
    print("Catalogo:",OUT/"index.html")
if __name__=="__main__": main()
