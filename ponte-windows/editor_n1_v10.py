"""Editor local gratuito do ESTILO CLOUD N1. Requer FFmpeg no PATH; legendas opcionais com faster-whisper."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import tempfile

def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

def duration(video):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
                       capture_output=True, text=True, check=True)
    return float(p.stdout.strip())

def segments(video, length):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af",
                        "silencedetect=noise=-35dB:d=0.45", "-f", "null", "-"],
                       capture_output=True, text=True)
    import re
    events = []
    for line in p.stderr.splitlines():
        start = re.search(r"silence_start: ([\d.]+)", line)
        end = re.search(r"silence_end: ([\d.]+)", line)
        if start:
            events.append(("start", float(start.group(1))))
        if end:
            events.append(("end", float(end.group(1))))
    spans = []
    cursor = 0.0
    for kind, t in events:
        if kind == "start":
            if t - cursor > 0.25:
                spans.append((cursor, min(length, t + 0.08)))
        else:
            cursor = max(0.0, t - 0.08)
    if length - cursor > 0.25:
        spans.append((cursor, length))
    return [(max(0, a), min(length, b)) for a, b in spans if b - a >= 0.25] or [(0, length)]

def transcribe(video, model_name):
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError("Instale as legendas: py -3 -m pip install faster-whisper") from e
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    words = []
    for segment in model.transcribe(str(video), language="pt", beam_size=5, word_timestamps=True, vad_filter=True)[0]:
        for w in segment.words or []:
            words.append((float(w.start), float(w.end), w.word.strip()))
    return words

def srt_time(seconds):
    ms = int(max(0, seconds) * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"

def captions(words, spans, path):
    output = []
    offset = 0.0
    for a, b in spans:
        for start, end, word in words:
            if word and start < b and end > a:
                output.append((offset + max(0, start-a), offset + min(b-a, end-a), word))
        offset += b-a
    lines = []
    for i in range(0, len(output), 4):
        group = output[i:i+4]
        if not group:
            continue
        lines.append(f"{i//4+1}\n{srt_time(group[0][0])} --> {srt_time(group[-1][1])}\n" +
                     " ".join(x[2] for x in group) + "\n")
    path.write_text("\n".join(lines), encoding="utf-8")

def framing(source, a, b):
    # Sample faces per clip; stable crop rather than jittery frame-by-frame zoom.
    import cv2
    import statistics
    cap = cv2.VideoCapture(str(source))
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = []
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    try:
        for i in range(7):
            cap.set(cv2.CAP_PROP_POS_MSEC, (a + (b-a)*(i+0.5)/7)*1000)
            ok, frame = cap.read()
            if not ok:
                continue
            h, w = frame.shape[:2]
            ratio = min(1.0, 640/max(w,h))
            gray = cv2.cvtColor(cv2.resize(frame, None, fx=ratio, fy=ratio), cv2.COLOR_BGR2GRAY)
            found = detector.detectMultiScale(gray, 1.1, 5, minSize=(24,24))
            if len(found):
                x,y,fw,fh = max(found, key=lambda f:f[2]*f[3])
                faces.append(tuple(float(v)/ratio for v in (x,y,fw,fh)))
    finally:
        cap.release()
    if w < 2 or h < 2:
        return "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1"
    cw = min(w, h*9/16)
    cx = statistics.median(f[0]+f[2]/2 for f in faces) if faces else w/2
    cy = statistics.median(f[1]+f[3]/2 for f in faces) if faces else h/2
    ch = min(h,w*16/9)
    cw = int(cw/2)*2
    ch = int(ch/2)*2
    x = int(max(0,min(w-cw,cx-cw/2))/2)*2
    y = int(max(0,min(h-ch,cy-ch*0.35))/2)*2
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920,setsar=1"

def edit(source, target, subtitle=False, model="small"):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("Instale o FFmpeg e adicione ffmpeg/ffprobe ao PATH do Windows.")
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source == target:
        raise ValueError("A saída deve ser diferente do vídeo original.")
    target.parent.mkdir(parents=True, exist_ok=True)
    length = duration(source)
    spans = segments(source, length)
    with tempfile.TemporaryDirectory(prefix="estilo_n1_") as temp:
        folder = Path(temp)
        clips = []
        for i, (a, b) in enumerate(spans):
            clip = folder / f"parte_{i:04}.mp4"
            run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-i", str(source),
                 "-t", str(b-a), "-filter_complex",
                 framing(source, a, b),
                 "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "19", "-c:a", "aac", "-ar", "44100", "-ac", "2",
                 str(clip)])
            clips.append(clip)
        listing = folder / "concat.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
        joined = folder / "unido.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i",
             str(listing), "-c", "copy", str(joined)])
        if subtitle:
            words = transcribe(joined, model)
            subs = folder / "legendas.srt"
            captions(words, [(0, duration(joined))], subs)
            if subs.stat().st_size:
                # Use caminho relativo dentro da pasta temporária para evitar escapes no filtro.
                run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-vf",
                     "subtitles=legendas.srt:force_style='FontName=Arial,FontSize=18,Bold=1,"
                     "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                     "BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=85,MarginL=24,MarginR=24'",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                     "-c:a", "copy", str(target)], cwd=folder)
                return {"output": str(target), "clips": len(clips), "captions": True}
        shutil.copy2(joined, target)
    return {"output": str(target), "clips": len(clips), "captions": False}


def stamp(t):
    n = max(0, round(t*100))
    return f"{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}"

def safe(s):
    return str(s).replace("\\", "").replace("{", "").replace("}", "").replace("\n", " ")

def render(video, plan, output):
    video, plan, output = map(lambda p: Path(p).resolve(), (video, plan, output))
    if output in (video, plan) or output.exists():
        raise ValueError("Escolha um novo arquivo de saída.")
    data = json.loads(plan.read_text(encoding="utf-8"))
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,132,&H00FFFFFF,&H006BE6B5,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,85,85,420,1
Style: Title,Arial,120,&H00288CF2,&H00FFFFFF,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,8,90,90,220,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    def add(a,b,style,text):
        if b-a >= .01:
            events.append(f"Dialogue: 0,{stamp(a)},{stamp(b)},{style},,0,0,0,,{text}")
    # Presets originais, inspirados em motion typography.
    presets = [
        ("Arial", 96, "6BE6B5", "pop"),
        ("Impact", 102, "3492FF", "slide"),
        ("Georgia", 88, "79CFFF", "fade"),
        ("Arial", 96, "00DEFF", "pulse"),
        ("Verdana", 84, "6BE6B5", "clean"),
        ("Impact", 105, "FFFFFF", "glow"),
    ]
    keywords = {"instagram","carreira","resultado","jornada","sucesso","vendas","dinheiro","clientes","crescer","conteúdo"}
    for scene_index, scene in enumerate(data["cenas"]):
        words = scene["palavras"]
        font, size, accent, motion = presets[scene_index % len(presets)]
        for offset in range(0, len(words), 3):
            group = words[offset:offset+3]
            if not group:
                continue
            for i,w in enumerate(group):
                a = float(w["inicio"])
                b = float(group[i+1]["inicio"]) if i+1<len(group) else float(w["fim"])
                if b <= a:
                    continue
                parts = []
                for j,x in enumerate(group):
                    active = j == i
                    important = x["texto"].lower().strip(".,?!") in keywords
                    word = safe(x["texto"])
                    fs = size + (12 if important else 0) if active else size-12
                    tags = rf"\fn{font if active else 'Arial'}\fs{fs}\c&H{accent if active else 'FFFFFF'}&\bord4\shad1"
                    if active and motion == "pop":
                        tags += r"\fscx85\fscy85\t(0,100,\fscx100\fscy100)"
                    elif active and motion == "pulse":
                        tags += r"\fscx100\fscy100\t(0,90,\fscx108\fscy108)\t(90,180,\fscx100\fscy100)"
                    elif active and motion == "glow":
                        tags += r"\bord7\3c&H207050&\blur2"
                    parts.append("{" + tags + "}" + word)
                position = r"{\an2\pos(540,1460)}"
                if motion == "slide":
                    position = r"{\an2\move(540,1500,540,1460,0,120)}"
                elif motion == "fade":
                    position = r"{\an2\pos(540,1460)\fad(70,50)}"
                add(a,b,"Caption",position+" ".join(parts))
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp,"captions.ass").write_text(header+"\n".join(events),encoding="utf-8")
        zooms = []
        for scene in data["cenas"]:
            if scene.get("efeito_sugerido") == "zoom_sugerido":
                a = max(0,float(scene["inicio"]))
                b = min(float(scene["fim"]),a+2.5)
                if b-a > .3:
                    zooms.append(f"if(between(it,{a:.3f},{b:.3f}),0.025*sin(PI*(it-{a:.3f})/{b-a:.3f}),0)")
        z = "1+" + "+".join(zooms) if zooms else "1"
        vf = f"scale=2160:3840,zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,setsar=1,ass=captions.ass"
        subprocess.run(["ffmpeg","-nostdin","-n","-i",str(video),"-vf",vf,"-c:v","libx264","-preset","fast","-crf","20","-af","aresample=async=1:first_pts=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000","-c:a","aac","-b:a","192k","-movflags","+faststart",str(output)],cwd=tmp,check=True)
    print("RENDER N1 V10 OK:",output)


from plano_n1 import plan
def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("saida")
    a = p.parse_args()
    source, target = Path(a.video).resolve(), Path(a.saida).resolve()
    if target.exists() or source == target:
        raise ValueError("Escolha uma nova saida.")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp, "base.mp4")
        plano = Path(tmp, "plano.json")
        print("N1 1/3: cortes e enquadramento", flush=True)
        edit(source, base, False)
        print("N1 2/3: planejamento", flush=True)
        plano.write_text(json.dumps(plan(str(base)), ensure_ascii=False), encoding="utf-8")
        print("N1 3/3: legendas e audio", flush=True)
        render(base, plano, target)
    print("EDITOR N1 V10 OK:", target)
if __name__ == "__main__":
    main()
