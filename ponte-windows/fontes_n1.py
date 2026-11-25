from pathlib import Path
import urllib.request
import zipfile
import tempfile
import shutil
import json

ROOT = Path.home() / "Downloads" / "ESTILO_N1_Referencias" / "Fontes"
NAMES = """montserrat poppins anton bebasneue inter oswald archivo archivoblack robotocondensed roboto playfairdisplay pacifico raleway lato opensans nunito nunitosans rubik ubuntu mukta barlow barlowcondensed barlowsemicondensed teko rajdhani orbitron exo2 audiowide bangers luckiestguy permanentmarker caveat dancingScript satisfy greatvibes lobster lobsterTwo righteous abrilfatface alfaSlabOne blackopsone russoone titilliumweb workSans dmSans manrope outfit spacegrotesk syne sora urbanist lexend plusjakartasans figtree karla cabin assistant oxygen quicksand comfortaa josefinsans josefinslab merriweather lora cormorantgaramond cinzel cinzeldecorative bodonimoda libreBaskerville libreCaslonText bitter arvo zillaSlab crimsontext cardo spectral vollkorn alegreya alegreyaSans kanit prompt sarabun chakraPetch baiJamjuree ibmplexsans ibmplexmono spacemono jetbrainsmono inconsolata firaSans firaCode redhatdisplay redhattext epilogue publicSans mulish hind heebo notoSans notoSerif""".lower().split()
def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    report = []
    for name in NAMES:
        try:
            url = "https://api.github.com/repos/google/fonts/contents/ofl/" + name
            req = urllib.request.Request(url,headers={"User-Agent":"Editor-N1"})
            # Public API is rate limited; raw metadata avoids that limit.
            base = "https://raw.githubusercontent.com/google/fonts/main/ofl/"+name+"/"
            import re
            with urllib.request.urlopen(base+"METADATA.pb",timeout=30) as r:
                metadata = r.read()
            names = list(dict.fromkeys(re.findall(r'filename:\s*"([^"]+)"',metadata.decode("utf-8"))))
            if not names:
                raise ValueError("Sem fontes no metadata")
            with urllib.request.urlopen(base+"OFL.txt",timeout=30) as r:
                license_data = r.read()
            folder = ROOT/name
            folder.mkdir(exist_ok=True)
            (folder/"OFL.txt").write_bytes(license_data)
            (folder/"METADATA.pb").write_bytes(metadata)
            for filename in names:
                from urllib.parse import quote
                if Path(filename).name != filename:
                    raise ValueError("Nome invalido")
                dest = folder/filename
                if not dest.exists():
                    with urllib.request.urlopen(base+quote(filename),timeout=60) as r:
                        data = r.read()
                    dest.write_bytes(data)
            report.append({"family":name,"status":"downloaded","files":len(names)})
            print("OK",name,flush=True)
        except Exception as e:
            report.append({"family":name,"status":"failed","error":str(e)})
            print("PENDENTE",name,str(e),flush=True)
        (ROOT/"catalogo_fontes.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("Familias disponiveis:",sum(r["status"]=="downloaded" for r in report),"de",len(NAMES))
if __name__ == "__main__":
    main()
