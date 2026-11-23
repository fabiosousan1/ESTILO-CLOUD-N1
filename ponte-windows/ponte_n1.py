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
            proc=subprocess.run(["py","-3","-m","gallery_dl","-d",str(FOLDER),url],capture_output=True,text=True,timeout=240)
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
        self.send_header("Access-Control-Allow-Headers","Content-Type")
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
if __name__=="__main__":
    print("ESTILO CLOUD N1 | Ponte local")
    print("Pasta:",FOLDER)
    print("Abra https://fabiosousan1.github.io/ESTILO-CLOUD-N1/")
    print("Mantenha esta janela aberta durante os downloads.")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
