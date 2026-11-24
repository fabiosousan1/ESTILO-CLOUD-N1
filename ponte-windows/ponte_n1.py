"""ESTILO CLOUD N1: ponte local para baixar Pins autorizados."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json, subprocess, threading, webbrowser, shutil, re, os

HOST="127.0.0.1"
PORT=8765
ORIGIN="https://fabiosousan1.github.io"
FOLDER=Path.home()/"Downloads"/"ESTILO_N1_Referencias"
FOLDER.mkdir(parents=True,exist_ok=True)
lock=threading.Lock()
state={"running":False,"done":0,"total":0,"errors":[],"current":"","finished":False}
PIN=re.compile(r"^/pin/(\d+)/?$")
def normalize(url):
    try:
        p=urlparse(url)
        if p.scheme!="https" or p.hostname not in ("pinterest.com","www.pinterest.com","br.pinterest.com"):
            return None
        m=PIN.fullmatch(p.path)
        return "https://www.pinterest.com/pin/"+m.group(1)+"/" if m else None
    except Exception:
        return None
def worker(urls):
    for url in urls:
        with lock: state["current"]=url
        try:
            proc=subprocess.run(["py","-3","-m","gallery_dl","-d",str(FOLDER),"--download-archive",str(FOLDER/".pinterest-downloads.sqlite3"),"-o","skip=true",url],capture_output=True,text=True,timeout=240)
            if proc.returncode!=0:
                with lock: state["errors"].append(url+": "+(proc.stderr or proc.stdout)[-220:])
        except Exception as e:
            with lock: state["errors"].append(url+": "+str(e))
        with lock: state["done"]+=1
    with lock: state["running"]=False;state["finished"]=True;state["current"]=""
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def headers_cors(self):
        self.send_header("Access-Control-Allow-Origin",ORIGIN)
        self.send_header("Vary","Origin")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type, X-Video-Name")
        self.send_header("Access-Control-Allow-Private-Network","true")
        self.send_header("Cache-Control","no-store")
    def reply(self,code,obj):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code);self.headers_cors()
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers();self.wfile.write(data)
    def allowed(self):
        return self.headers.get("Origin")==ORIGIN
    def do_OPTIONS(self):
        if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
        self.send_response(204);self.headers_cors();self.end_headers()
    def do_GET(self):
        if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
        if self.path=="/status":
            with lock: snapshot=dict(state)
            return self.reply(200,{"ok":True,"folder":str(FOLDER),**snapshot})
        return self.reply(404,{"error":"Não encontrado"})
    def do_POST(self):
        if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
        if self.path!="/download":return self.reply(404,{"error":"Não encontrado"})
        if not self.headers.get("Content-Type","").startswith("application/json"):
            return self.reply(415,{"error":"Use JSON"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length<1 or length>20000:return self.reply(413,{"error":"Lista muito grande"})
            payload=json.loads(self.rfile.read(length))
            incoming=payload.get("urls",[])
            if not isinstance(incoming,list) or len(incoming)>30:return self.reply(400,{"error":"Máximo de 30 Pins por lote"})
            urls=list(dict.fromkeys(x for raw in incoming if isinstance(raw,str) if (x:=normalize(raw))))
            if not urls:return self.reply(400,{"error":"Nenhum Pin válido"})
            with lock:
                if state["running"]:return self.reply(409,{"error":"Já existe um lote em andamento"})
                state.update(running=True,done=0,total=len(urls),errors=[],current="",finished=False)
            threading.Thread(target=worker,args=(urls,),daemon=True).start()
            return self.reply(202,{"ok":True,"accepted":len(urls),"folder":str(FOLDER)})
        except Exception as e:return self.reply(400,{"error":str(e)})

# Editor local: upload somente a partir da origem autorizada e do próprio computador.
EDIT_FOLDER=Path.home()/"Downloads"/"ESTILO_N1_Editados"
EDIT_FOLDER.mkdir(parents=True,exist_ok=True)
edit_state={"running":False,"finished":False,"error":"","output":"","clips":0}
edit_lock=threading.Lock()
def edit_worker(source):
    try:
        from editor_n1 import edit
        target=EDIT_FOLDER/("editado_"+str(int(__import__("time").time()))+".mp4")
        result=edit(source,target,subtitle=True)
        with edit_lock: edit_state.update(running=False,finished=True,error="",output=str(target),clips=result["clips"])
    except Exception as exc:
        with edit_lock: edit_state.update(running=False,finished=True,error=str(exc),output="")
    finally:
        try: source.unlink(missing_ok=True)
        except OSError: pass

class EditorHandler(Handler):
    def do_GET(self):
        if self.path=="/edit-status":
            if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
            with edit_lock: snapshot=dict(edit_state)
            return self.reply(200,{"ok":True,**snapshot})
        if self.path=="/edit-result":
            if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
            with edit_lock: path=Path(edit_state["output"]) if edit_state["output"] else None
            if not path or not path.is_file():return self.reply(404,{"error":"Vídeo ainda não disponível"})
            self.send_response(200);self.headers_cors()
            self.send_header("Content-Type","video/mp4")
            self.send_header("Content-Disposition",'attachment; filename="ESTILO_N1_editado.mp4"')
            self.send_header("Content-Length",str(path.stat().st_size))
            self.end_headers()
            with path.open("rb") as video:
                shutil.copyfileobj(video,self.wfile)
            return
        return super().do_GET()
    def do_POST(self):
        if self.path=="/drive-save":
            if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
            from urllib.parse import unquote, parse_qs
            try:
                length=int(self.headers.get("Content-Length","0"))
                if length<1 or length>1024*1024*1024:return self.reply(413,{"error":"Máximo de 1 GB"})
                name=unquote(self.headers.get("X-Video-Name",""))
                if not name or name in (".","..") or any(c in name for c in '/\\:*?"<>|') or any(ord(c)<32 for c in name) or name.endswith((" ",".")):
                    return self.reply(400,{"error":"Nome inválido"})
                folder=FOLDER/"Google Drive"
                folder.mkdir(exist_ok=True)
                target=folder/name
                import tempfile
                with tempfile.NamedTemporaryFile(dir=folder,delete=False) as out:
                    temp=Path(out.name)
                    try:
                        remaining=length
                        while remaining:
                            chunk=self.rfile.read(min(1024*1024,remaining))
                            if not chunk:raise ValueError("Upload incompleto")
                            out.write(chunk);remaining-=len(chunk)
                    except Exception:
                        out.close();temp.unlink(missing_ok=True);raise
                try:
                    with lock:
                        if target.exists():
                            return self.reply(200,{"ok":True,"skipped":True,"file":str(target)})
                        temp.replace(target)
                    return self.reply(200,{"ok":True,"file":str(target)})
                finally:temp.unlink(missing_ok=True)
            except Exception as exc:return self.reply(400,{"error":str(exc)})
        if self.path!="/edit":return super().do_POST()
        if not self.allowed():return self.reply(403,{"error":"Origem não autorizada"})
        if self.headers.get("Content-Type","").split(";")[0]!="video/mp4":
            return self.reply(415,{"error":"Envie um vídeo MP4"})
        try: length=int(self.headers.get("Content-Length","0"))
        except ValueError:return self.reply(400,{"error":"Tamanho inválido"})
        if length<1 or length>250*1024*1024:return self.reply(413,{"error":"Máximo de 250 MB"})
        with edit_lock:
            if edit_state["running"]:return self.reply(409,{"error":"Já existe uma edição em andamento"})
            edit_state.update(running=True,finished=False,error="",output="",clips=0)
        source=EDIT_FOLDER/("entrada_"+str(threading.get_ident())+".mp4")
        try:
            remaining=length
            with source.open("wb") as out:
                while remaining:
                    chunk=self.rfile.read(min(1024*1024,remaining))
                    if not chunk:raise ValueError("Upload incompleto")
                    out.write(chunk);remaining-=len(chunk)
            threading.Thread(target=edit_worker,args=(source,),daemon=True).start()
            return self.reply(202,{"ok":True,"message":"Edição iniciada"})
        except Exception as exc:
            source.unlink(missing_ok=True)
            with edit_lock: edit_state.update(running=False,finished=True,error=str(exc))
            return self.reply(400,{"error":str(exc)})

if __name__=="__main__":
    print("ESTILO CLOUD N1 | Ponte local")
    print("Pasta:",FOLDER)
    print("Abra https://fabiosousan1.github.io/ESTILO-CLOUD-N1/")
    print("Mantenha esta janela aberta durante os downloads.")
    ThreadingHTTPServer((HOST,PORT),EditorHandler).serve_forever()
