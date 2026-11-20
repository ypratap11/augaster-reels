#!/usr/bin/env python3
"""Augaster AI Digest reel renderer.

script.json -> narrated, captioned, branded 1080x1920 MP4.

Usage:
  python3 render_reel.py episodes/<episode>/script.json --voice kokoro:af_heart
  python3 render_reel.py episodes/<episode>/script.json --voice path/to/piper_voice.onnx
  python3 render_reel.py episodes/<episode>/script.json --voiceover my_recording.wav

Voice options:
  --voice      kokoro:<voice> (default house voice: kokoro:af_heart) or an
               offline Piper voice model (.onnx); narrates each segment.
  --voiceover  your own recording for the whole reel; captions are spread
               across it in proportion to the script text.
"""
import argparse, json, math, os, random, subprocess, sys, wave, textwrap, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
LENGTH_SCALE = 0.95  # <1 speaks faster
# Augaster brand kit (augaster-brand-kit.html): night, gold, amber, starlight, slate.
BRAND = {
    "bg_top": (13, 16, 48), "bg_bottom": (20, 25, 56),
    "accent": (227, 178, 92), "accent2": (226, 136, 90),
    "text": (242, 238, 227), "muted": (154, 160, 200),
    "card": (255, 255, 255, 18),
}
# Header text, CTA footer and optional logo; overridden per client with --brand.
IDENTITY = {"name": "AUGASTER", "tagline": "AI DIGEST", "cta_footer": None, "logo": None, "starfield": True}

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def load_brand(path):
    """Apply a client brand.json: {"name", "tagline", "cta_footer", "logo", "colors": {key: "#hex"}}.

    colors keys: bg_top, bg_bottom, accent, accent2, text, muted (any subset).
    logo: image path relative to brand.json, drawn in the header instead of the star.
    starfield: false turns off the animated star background (on by default; it is Augaster's look).
    """
    b = json.load(open(path, encoding="utf-8"))
    for k, v in b.get("colors", {}).items():
        if k not in BRAND or k == "card":
            raise SystemExit(f"brand.json: unknown color '{k}'")
        BRAND[k] = hex_rgb(v)
    for k in ("name", "tagline", "cta_footer", "starfield"):
        if k in b: IDENTITY[k] = b[k]
    if b.get("logo"):
        logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(path)), b["logo"])).convert("RGBA")
        logo.thumbnail((400, 64), Image.LANCZOS)
        IDENTITY["logo"] = logo
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

KOKORO_DIR = os.environ.get("KOKORO_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices"))
KOKORO_SPEED = 1.05  # >1 speaks faster
_kokoro = None

def tts(text, voice, out):
    """voice = 'kokoro:<name>' (e.g. kokoro:af_heart) or a Piper .onnx path."""
    global _kokoro
    if voice.startswith("kokoro:"):
        import soundfile as sf
        from kokoro_onnx import Kokoro
        if _kokoro is None:
            _kokoro = Kokoro(os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx"),
                             os.path.join(KOKORO_DIR, "voices-v1.0.bin"))
        audio, sr = _kokoro.create(text, voice=voice.split(":", 1)[1], speed=KOKORO_SPEED, lang="en-us")
        sf.write(out, audio, sr, subtype="PCM_16")
        return
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

def star_points(cx, cy, size):
    """Polygon for the four-point star in augaster-mark.svg (52 viewBox units wide), centred at cx, cy."""
    k = size / 52
    segs = [((40, 8), (41.6, 31.4), (66, 34)), ((66, 34), (41.6, 36.6), (40, 60)),
            ((40, 60), (38.4, 36.6), (14, 34)), ((14, 34), (38.4, 31.4), (40, 8))]
    pts = []
    for p0, p1, p2 in segs:
        for i in range(25):
            t = i / 24
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((cx + (x - 40) * k, cy + (y - 34) * k))
    return pts

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

CHART_COLORS = {"accent": BRAND["accent"], "accent2": BRAND["accent2"], "bad": (244, 114, 114), "muted": BRAND["muted"]}
F_AXIS = font("Medium", 28)

def fmt_num(v, unit):
    if unit == "$":
        return ("-$" if v < 0 else "$") + f"{abs(v):,.0f}"
    if unit == "%":
        return f"{v:,.0f}%"
    return f"{v:,.0f}"

def draw_chart(ld, chart, box, progress, alpha):
    """Line chart drawn left to right as progress goes 0 -> 1. Values come from the script, never invented here."""
    x0, y0, x1, y1 = box
    series = chart["series"]
    allv = [v for s in series for v in s["values"]] + ([0] if chart.get("zero", True) else [])
    lo, hi = min(allv), max(allv)
    pad = (hi - lo) * 0.08 or 1
    lo, hi = lo - pad, hi + pad
    unit = chart.get("unit", "")
    span0 = hi - lo - 2 * pad
    step0 = 10 ** max(0, len(str(int(abs(span0) / 2))) - 1) if span0 >= 10 else 1
    widest = max(ld.textlength(fmt_num(round((lo + pad + span0 * f) / step0) * step0, unit), font=F_AXIS) for f in (0, 0.5, 1))
    left = x0 + max(150, int(widest) + 30)
    Y = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)
    y0 += 80  # room for the legend above the plot
    ld.rounded_rectangle([x0 - 20, y0 - 110, x1 + 20, y1 + 70], radius=24, fill=(255, 255, 255, int(alpha * 0.05)))
    span = hi - lo - 2 * pad
    step = 10 ** max(0, len(str(int(abs(span) / 2))) - 1) if span >= 10 else 1
    for frac in (0, 0.5, 1):
        v = round((lo + pad + span * frac) / step) * step
        ld.line([left, Y(v), x1, Y(v)], fill=(255, 255, 255, int(alpha * 0.12)), width=2)
        ld.text((x0, Y(v) - 16), fmt_num(v, unit), font=F_AXIS, fill=BRAND["muted"] + (alpha,))
    if lo < 0 < hi:
        ld.line([left, Y(0), x1, Y(0)], fill=(255, 255, 255, int(alpha * 0.45)), width=3)
    if chart.get("x_label"):
        ld.text((left, y1 + 18), chart["x_label"], font=F_AXIS, fill=BRAND["muted"] + (alpha,))
    ly, lx = y0 - 10, left
    for s in series:
        col = CHART_COLORS.get(s.get("color", "accent"), BRAND["accent"])
        n = len(s["values"])
        upto = max(2, int(round(n * progress)))
        pts = [(left + (x1 - left) * i / (n - 1), Y(v)) for i, v in enumerate(s["values"][:upto])]
        ld.line(pts, fill=col + (alpha,), width=7, joint="curve")
        ex, ey = pts[-1]
        ld.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=col + (alpha,))
        tag = s["name"] + (f"  {fmt_num(s['values'][upto - 1], unit)}" if progress >= 0.999 else "")
        ld.text((lx, ly), tag, font=F_AXIS, fill=col + (alpha,))
        ly += 40

def make_stars(seed=7):
    """Fixed starfield: same stars every render, so episodes look consistent."""
    rnd = random.Random(seed)
    dots = []
    for _ in range(130):
        depth = rnd.random()  # nearer stars are bigger, brighter and drift faster (parallax)
        dots.append({"x": rnd.uniform(0, W), "y": rnd.uniform(0, H), "r": 2.0 + 3.5 * depth ** 2,
                     "a": 90 + 140 * depth, "f": rnd.uniform(0.6, 1.8), "p": rnd.uniform(0, 6.28),
                     "v": 8 + 30 * depth, "gold": rnd.random() < 0.2})
    sparkles = [{"x": x, "y": y, "s": s, "p": p} for x, y, s, p in
                [(900, 330, 54, 0.0), (140, 1260, 40, 2.1), (970, 1170, 32, 4.0), (330, 390, 24, 1.2), (560, 1340, 20, 3.1)]]
    return dots, sparkles

STARS = make_stars()

def draw_starfield(img, t):
    """Slow upward-drifting, twinkling stars plus a few pulsing dawn-star sparkles (brand mark)."""
    dots, sparkles = STARS
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for s in dots:
        y = (s["y"] - s["v"] * t) % H
        a = s["a"] * (0.55 + 0.45 * math.sin(t * s["f"] + s["p"]))
        if 430 < y < 1000 or y < 180 or y > H - 210:  # keep headline, header and footer text calm
            a *= 0.4
        col = BRAND["accent"] if s["gold"] else BRAND["text"]
        r = s["r"]
        ld.ellipse([s["x"] - r, y - r, s["x"] + r, y + r], fill=col + (int(a),))
    for s in sparkles:
        pulse = 0.5 + 0.5 * math.sin(t * 0.9 + s["p"])
        size = s["s"] * (0.75 + 0.25 * pulse)
        ld.polygon(star_points(s["x"], s["y"], size), fill=BRAND["accent"] + (int(90 + 140 * pulse),))
    img.alpha_composite(layer)

def draw_frame(base, glows, seg, local_t, global_t, total, cue, script):
    img = base.copy().convert("RGBA")
    # drifting glows
    g1, g2 = glows
    x1 = int(-600 + 120 * math.sin(global_t * 0.35)); y1 = int(-140 + 80 * math.cos(global_t * 0.3))
    x2 = int(W - 1000 + 100 * math.cos(global_t * 0.28)); y2 = int(H - 1500 + 120 * math.sin(global_t * 0.32))
    img.alpha_composite(g1, (x1, y1)); img.alpha_composite(g2, (x2, y2))
    if IDENTITY["starfield"]:
        draw_starfield(img, global_t)
    d = ImageDraw.Draw(img)
    M = 80

    # header: brand mark (client logo, or the Augaster dawn-star) + name + tag
    if IDENTITY["logo"]:
        lg = IDENTITY["logo"]
        img.alpha_composite(lg, (M, 124 - lg.height // 2))
        x = M + lg.width + 18
    else:
        d.polygon(star_points(M + 26, 124, 52), fill=BRAND["accent"])
        x = M + 70
    if IDENTITY["name"]:
        d.text((x, 100), IDENTITY["name"], font=F_BRAND, fill=BRAND["text"])
        x += d.textlength(IDENTITY["name"] + " ", font=F_BRAND)
    tag = script.get("brand_tag", IDENTITY["tagline"])  # per-episode tag (e.g. Money Lab) wins
    if tag:
        d.text((x, 100), tag, font=F_BRAND, fill=BRAND["accent"])
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
        f_url = F_CTA_URL
        tw = ld.textlength(url, font=f_url)
        if tw + 80 > W - 2 * M:  # longer CTAs (client sites, "link in bio") shrink to fit
            f_url = font("Black", int(110 * (W - 2 * M - 80) / tw))
            tw = ld.textlength(url, font=f_url)
        box = [M, y, M + tw + 80, y + 170]
        ld.rounded_rectangle(box, radius=28, fill=BRAND["accent"] + (alpha,))
        _, t_, _, b_ = ld.textbbox((0, 0), url, font=f_url)
        ld.text((M + 40, y + (170 - (b_ - t_)) / 2 - t_), url, font=f_url, fill=BRAND["bg_top"] + (alpha,))
        footer = IDENTITY["cta_footer"] or ("Link in bio · Follow for weekly practical AI" if "Follow" in seg["narration"] else "Link in bio")
        ld.text((M, y + 220), footer, font=F_POINT, fill=BRAND["muted"] + (alpha,))
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
        if seg.get("chart"):
            span = max(1.0, seg.get("speech_dur", seg["dur"]) * 0.85)
            prog = ease((local_t - 0.3) / span)
            top = max(y + 90, 900)
            draw_chart(ld, seg["chart"], (M + 20, top, W - M - 20, 1330), max(prog, 0.02), alpha)
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
    if script.get("disclaimer"):
        d.text((M, H - 215), script["disclaimer"], font=F_SMALL, fill=BRAND["muted"])
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
    ap.add_argument("--brand", help="client brand.json (colors, name, logo); default is Augaster")
    args = ap.parse_args()
    if not (args.voice or args.voiceover):
        raise SystemExit("pass --voice or --voiceover")
    if args.brand:
        load_brand(args.brand)

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
    glows = (glow(420, BRAND["muted"], 40), glow(380, BRAND["accent"], 40))
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
