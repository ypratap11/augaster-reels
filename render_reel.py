#!/usr/bin/env python3
"""Augaster AI Digest reel renderer.

script.json -> narrated, captioned, branded 1080x1920 MP4.

Usage:
  python3 render_reel.py episodes/<episode>/script.json --voice path/to/voice.onnx
  python3 render_reel.py episodes/<episode>/script.json --voiceover my_recording.wav

Voice options:
  --voice      offline Piper voice model (.onnx); narrates each segment.
  --voiceover  your own recording for the whole reel; captions are spread
               across it in proportion to the script text.
"""
import argparse, json, math, os, subprocess, sys, wave, textwrap, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
LENGTH_SCALE = 0.95  # <1 speaks faster
BRAND = {
    "bg_top": (8, 14, 30), "bg_bottom": (18, 30, 58),
    "accent": (245, 166, 35), "accent2": (56, 189, 248),
    "text": (245, 247, 250), "muted": (160, 172, 194),
    "card": (255, 255, 255, 18),
}
FONT_DIR = "/usr/share/fonts/opentype/inter"
def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Inter-{weight}.otf"), size)

F_LABEL = font("Bold", 34)
F_TITLE = font("ExtraBold", 92)
F_POINT = font("SemiBold", 46)
F_CAP = font("ExtraBold", 64)
F_SMALL = font("Medium", 30)
F_BRAND = font("Black", 40)
F_CTA_URL = font("Black", 110)

PAD_START, PAD_END = 0.1, 0.2  # silence around each narrated segment

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode(errors="ignore"))
        raise SystemExit(f"command failed: {cmd[0]}")
    return r

def wav_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()

def tts(text, voice, out):
    run([sys.executable, "-m", "piper", "-m", voice, "--length-scale", str(LENGTH_SCALE), "-f", out], input=text.encode())

def pad_wav(src, dst, start, end):
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af",
         f"adelay={int(start*1000)}:all=1,apad=pad_dur={end}", "-ar", "22050", "-ac", "1", dst])

def chunk_words(text, n=4):
    words = text.split()
    return [" ".join(words[i:i+n]) for i in range(0, len(words), n)]

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = wd
    if cur: lines.append(cur)
    return lines

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def make_background():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        f = y / H
        c = tuple(int(BRAND["bg_top"][i] * (1 - f) + BRAND["bg_bottom"][i] * f) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return bg

def glow(radius, color, alpha):
    size = radius * 4  # extra margin so the blur fades to zero instead of clipping
    g = Image.new("RGBA", (size, size), color + (0,))
    ImageDraw.Draw(g).ellipse([radius, radius, radius * 3, radius * 3], fill=color + (alpha,))
    return g.filter(ImageFilter.GaussianBlur(radius // 1.5))

def build_timeline(script, voice, voiceover, workdir):
    segs = script["segments"]
    timeline, t = [], 0.0
    if voiceover:
        total = wav_duration(voiceover)
        weights = [len(s["narration"]) for s in segs]
        tot_w = sum(weights)
        for s, wgt in zip(segs, weights):
            dur = total * wgt / tot_w
            timeline.append({**s, "start": t, "dur": dur, "speech_start": t, "speech_dur": dur})
            t += dur
        return timeline, voiceover
    parts = []
    for i, s in enumerate(segs):
        raw = os.path.join(workdir, f"seg{i}_raw.wav")
        padded = os.path.join(workdir, f"seg{i}.wav")
        tts(s["narration"], voice, raw)
        speech = wav_duration(raw)
        pad_wav(raw, padded, PAD_START, PAD_END)
        dur = wav_duration(padded)
        timeline.append({**s, "start": t, "dur": dur,
                         "speech_start": t + PAD_START, "speech_dur": speech})
        parts.append(padded)
        t += dur
    lst = os.path.join(workdir, "parts.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
    narration = os.path.join(workdir, "narration.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", narration])
    return timeline, narration

def caption_cues(timeline):
    cues = []
    for seg in timeline:
        chunks = chunk_words(seg["narration"], 4)
        weights = [len(c) + 3 for c in chunks]
        tot = sum(weights)
        t = seg["speech_start"]
        for c, wgt in zip(chunks, weights):
            d = seg["speech_dur"] * wgt / tot
            cues.append({"start": t, "end": t + d, "text": c})
            t += d
    return cues

def srt_time(s):
    ms = int(round(s * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def draw_frame(base, glows, seg, local_t, global_t, total, cue, script):
    img = base.copy().convert("RGBA")
    # drifting glows
    g1, g2 = glows
    x1 = int(-600 + 120 * math.sin(global_t * 0.35)); y1 = int(-140 + 80 * math.cos(global_t * 0.3))
    x2 = int(W - 1000 + 100 * math.cos(global_t * 0.28)); y2 = int(H - 1500 + 120 * math.sin(global_t * 0.32))
    img.alpha_composite(g1, (x1, y1)); img.alpha_composite(g2, (x2, y2))
    d = ImageDraw.Draw(img)
    M = 80

    # header
    d.rounded_rectangle([M, 110, M + 22, 132], radius=4, fill=BRAND["accent"])
    d.text((M + 40, 100), "AUGASTER", font=F_BRAND, fill=BRAND["text"])
    d.text((M + 40 + d.textlength("AUGASTER ", font=F_BRAND), 100), "AI DIGEST", font=F_BRAND, fill=BRAND["accent"])
    d.text((W - M - d.textlength(script["episode"], font=F_SMALL), 108), script["episode"], font=F_SMALL, fill=BRAND["muted"])

    a_in = ease(local_t / 0.45)
    shift = int((1 - a_in) * 60)
    alpha = int(255 * a_in)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    if seg["kind"] == "cta":
        ld.text((M, 560 + shift), seg["label"], font=F_LABEL, fill=BRAND["accent"] + (alpha,))
        y = 630 + shift
        for line in wrap(ld, seg["title"], F_TITLE, W - 2 * M):
            ld.text((M, y), line, font=F_TITLE, fill=BRAND["text"] + (alpha,)); y += 108
        y += 50
        url = seg["point"]
        tw = ld.textlength(url, font=F_CTA_URL)
        box = [M, y, M + tw + 80, y + 170]
        ld.rounded_rectangle(box, radius=28, fill=BRAND["accent"] + (alpha,))
        ld.text((M + 40, y + 22), url, font=F_CTA_URL, fill=BRAND["bg_top"] + (alpha,))
        ld.text((M, y + 220), "Link in bio · Follow for weekly practical AI", font=F_POINT, fill=BRAND["muted"] + (alpha,))
    else:
        # label chip
        lw = ld.textlength(seg["label"], font=F_LABEL)
        ld.rounded_rectangle([M, 470 + shift, M + lw + 48, 530 + shift], radius=30,
                             fill=(BRAND["accent2"] if seg["kind"] != "analysis" else BRAND["accent"]) + (int(alpha * 0.18),),
                             outline=(BRAND["accent2"] if seg["kind"] != "analysis" else BRAND["accent"]) + (alpha,), width=3)
        ld.text((M + 24, 481 + shift), seg["label"], font=F_LABEL,
                fill=(BRAND["accent2"] if seg["kind"] != "analysis" else BRAND["accent"]) + (alpha,))
        y = 580 + shift
        for line in wrap(ld, seg["title"], F_TITLE, W - 2 * M):
            ld.text((M, y), line, font=F_TITLE, fill=BRAND["text"] + (alpha,)); y += 108
        if seg["point"]:
            pa = int(255 * ease((local_t - 0.35) / 0.45))
            y += 40
            ld.rectangle([M, y + 8, M + 8, y + 8 + 56 * len(wrap(ld, seg["point"], F_POINT, W - 2 * M - 40))], fill=BRAND["accent"] + (pa,))
            for line in wrap(ld, seg["point"], F_POINT, W - 2 * M - 40):
                ld.text((M + 36, y), line, font=F_POINT, fill=BRAND["muted"] + (pa,)); y += 60
    img.alpha_composite(layer)

    # caption box
    if cue:
        cw = d.textlength(cue["text"], font=F_CAP)
        cw = min(cw, W - 2 * M)
        lines = wrap(d, cue["text"], F_CAP, W - 2 * M - 60)
        bh = 80 * len(lines) + 50
        top = 1430
        d.rounded_rectangle([M, top, W - M, top + bh], radius=24, fill=(0, 0, 0, 150))
        yy = top + 25
        for line in lines:
            lw = d.textlength(line, font=F_CAP)
            d.text(((W - lw) / 2, yy), line, font=F_CAP, fill=BRAND["accent"] if seg["kind"] == "hook" else BRAND["text"])
            yy += 80

    # footer: source + progress
    d.text((M, H - 170), script.get("source_line", ""), font=F_SMALL, fill=BRAND["muted"])
    d.rounded_rectangle([M, H - 110, W - M, H - 100], radius=5, fill=(255, 255, 255, 40))
    d.rounded_rectangle([M, H - 110, M + int((W - 2 * M) * min(1, global_t / total)), H - 100], radius=5, fill=BRAND["accent"])
    return img.convert("RGB")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--voice", help="Piper .onnx voice model")
    ap.add_argument("--voiceover", help="your own narration .wav/.m4a for the whole reel")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if not (args.voice or args.voiceover):
        raise SystemExit("pass --voice or --voiceover")

    script = json.load(open(args.script))
    epdir = os.path.dirname(os.path.abspath(args.script))
    work = os.path.join(epdir, "_work"); os.makedirs(work, exist_ok=True)

    vo = None
    if args.voiceover:
        vo = os.path.join(work, "voiceover.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", args.voiceover, "-ar", "22050", "-ac", "1", vo])

    timeline, narration = build_timeline(script, args.voice, vo, work)
    total = timeline[-1]["start"] + timeline[-1]["dur"]
    cues = caption_cues(timeline)

    with open(os.path.join(epdir, "captions.srt"), "w") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n")

    base = make_background()
    glows = (glow(420, BRAND["accent2"], 55), glow(380, BRAND["accent"], 45))
    silent = os.path.join(work, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent],
                           stdin=subprocess.PIPE)
    nframes = int(math.ceil(total * FPS))
    seg_i, cue_i = 0, 0
    thumb = None
    for fno in range(nframes):
        t = fno / FPS
        while seg_i < len(timeline) - 1 and t >= timeline[seg_i + 1]["start"]: seg_i += 1
        seg = timeline[seg_i]
        while cue_i < len(cues) - 1 and t >= cues[cue_i]["end"]: cue_i += 1
        cue = cues[cue_i] if cues[cue_i]["start"] <= t < cues[cue_i]["end"] + 0.25 else None
        frame = draw_frame(base, glows, seg, t - seg["start"], t, total, cue, script)
        if seg_i == 0 and thumb is None and t - seg["start"] > 1.0:
            thumb = frame
        enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait()

    out = args.out or os.path.join(epdir, "reel.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", narration,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-ar", "44100", "-shortest", "-movflags", "+faststart", out])
    if thumb: thumb.save(os.path.join(epdir, "thumbnail.png"))
    report = {"duration_sec": round(total, 2), "segments": len(timeline), "captions": len(cues),
              "resolution": f"{W}x{H}", "fps": FPS, "output": out,
              "voice": os.path.basename(args.voice) if args.voice else "user voiceover",
              "sources": script.get("sources", []), "approved": False}
    json.dump(report, open(os.path.join(epdir, "render_report.json"), "w"), indent=2)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
