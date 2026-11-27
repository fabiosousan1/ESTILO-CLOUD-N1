"""Ponte Codex N1: fila de tarefas predefinidas, sem comandos remotos arbitrarios."""
import argparse, json, os, re, shutil, subprocess, time, urllib.request
from pathlib import Path

URL="https://raw.githubusercontent.com/fabiosousan1/ESTILO-CLOUD-N1/main/codex-n1/fila.json"
TASKS={
 "diagnostico":"Inspecione apenas o projeto N1 STUDIO e as ferramentas locais disponiveis. Nao altere arquivos. Resuma dependencias e bloqueios.",
 "integrar_hyperframes":"Integre HyperFrames ao editor N1 STUDIO com processamento local. Preserve os originais, crie testes e execute os testes possiveis. Sem APIs pagas, sem instalar software, sem publicar ou fazer push.",
 "testar_editor":"Execute os testes locais existentes do editor N1. Nao instale dependencias nem publique arquivos. Relate erros."
}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--workspace",required=True,type=Path)
 p.add_argument("--auto",action="store_true",help="Autoriza somente os tipos de tarefa predefinidos")
 a=p.parse_args()
 w=a.workspace.resolve()
 if not (w/"ponte-windows").is_dir(): raise SystemExit("Escolha a raiz do ESTILO-CLOUD-N1.")
 exe=shutil.which("codex")
 if not exe: raise SystemExit("Codex nao encontrado.")
 state=Path.home()/".n1-codex"
 state.mkdir(exist_ok=True)
 lock=(state/"lock").open("a+b")
 if os.name=="nt":
  import msvcrt
  lock.seek(0)
  msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 else:
  import fcntl
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 print("PONTE CODEX N1 ativa. Ctrl+C para parar.",flush=True)
 while True:
  try:
   with urllib.request.urlopen(URL,timeout=20) as r:
    tasks=json.loads(r.read(65536))
   for t in tasks:
    ident=t.get("id","")
    kind=t.get("tipo","")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}",ident) or kind not in TASKS: continue
    result=state/(ident+".json")
    if result.exists(): continue
    if not a.auto and input("Executar "+ident+" ("+kind+")? [s/N] ").lower()!="s": continue
    result.write_text(json.dumps({"id":ident,"estado":"executando"}),encoding="utf-8")
    mode="read-only" if kind=="diagnostico" else "workspace-write"
    args=[exe,"--ask-for-approval","never","exec","--sandbox",mode,"-c","sandbox_workspace_write.network_access=false",TASKS[kind]+" Trabalhe somente neste projeto. Nao leia credenciais, nao envie arquivos ou dados, nao execute comandos destrutivos."]
    try:
     with (state/(ident+".log")).open("wb") as log:
      rc=subprocess.run(args,cwd=w,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=3600).returncode
     status={"id":ident,"estado":"executado" if rc==0 else "erro","codigo":rc}
    except Exception as e:
     status={"id":ident,"estado":"erro","tipo_erro":type(e).__name__}
    result.write_text(json.dumps(status),encoding="utf-8")
    print(status,flush=True)
   time.sleep(30)
  except KeyboardInterrupt: break
  except Exception as e:
   print("Ponte:",type(e).__name__,flush=True)
   time.sleep(30)
if __name__=="__main__": main()
