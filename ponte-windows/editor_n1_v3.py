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
    # Use a blurred background when a full-screen crop would be too tight.
    cw = min(w, h*9/16)
    if not faces or max(f[2] for f in faces) > cw*0.62:
        return ("split[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:2[back];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];"
                "[back][front]overlay=(W-w)/2:(H-h)/2,setsar=1")
    cx = statistics.median(f[0]+f[2]/2 for f in faces)
    cy = statistics.median(f[1]+f[3]/2 for f in faces)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edição automática gratuita ESTILO CLOUD N1")
    parser.add_argument("video", help="Caminho do MP4 original")
    parser.add_argument("saida", help="Caminho do MP4 editado")
    parser.add_argument("--legendas", action="store_true", help="Legendas automáticas com faster-whisper")
    parser.add_argument("--modelo", default="small", help="Modelo Whisper: tiny, base, small")
    args = parser.parse_args()
    print(json.dumps(edit(args.video, args.saida, args.legendas, args.modelo), ensure_ascii=False))
