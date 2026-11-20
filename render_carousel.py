#!/usr/bin/env python3
"""Render an Augaster carousel (1080x1350 PNG slides) from carousel.json.

Usage: python3 render_carousel.py carousels/<slug>/carousel.json

carousel.json:
  {"cover": {"kicker": "...", "title": "5 AI prompts **every** shop owner should save", "sub": "..."},
   "slides": [{"title": "...", "use": "when to use it", "prompt": "the prompt text", "tip": "..."}],
   "cta": {"title": "...", "body": "..."},
   "caption": "Instagram caption"}
Words wrapped in **double asterisks** get a gold highlighter. Writes slide-01.png ...
next to the JSON, plus caption.txt. Brand: augaster-brand-kit (night, gold, amber, starlight).
"""
import json, os, random, re, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
NIGHT, NIGHT2 = (13, 16, 48), (20, 25, 56)
GOLD, AMBER, TEXT, MUTED = (227, 178, 92), (226, 136, 90), (242, 238, 227), (154, 160, 200)
CARD = (255, 255, 255, 14)
M = 84  # side margin

FONTS = {
    "serif": ["/usr/share/fonts/truetype/cormorant/CormorantGaramond-SemiBold.ttf",
              "C:/Windows/Fonts/georgiab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "sans": ["/usr/share/fonts/opentype/inter/Inter-Medium.otf", "C:/Windows/Fonts/segoeui.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "C:/Windows/Fonts/segoeuib.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf"],
}
_cache = {}


def font(kind, size):
    key = (kind, size)
    if key not in _cache:
        path = next((p for p in FONTS[kind] if os.path.exists(p)), None)
        if not path:
            raise SystemExit(f"no {kind} font found; install fonts-inter / fonts-dejavu")
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def star(cx, cy, s):
    """The Augaster dawn star (augaster-mark.svg), as a polygon of size ~s."""
    def quad(p0, p1, p2, n=16):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]
    k = s / 52
    P = lambda x, y: (cx + (x - 40) * k, cy + (y - 34) * k)
    segs = [((40, 8), (41.6, 31.4), (66, 34)), ((66, 34), (41.6, 36.6), (40, 60)),
            ((40, 60), (38.4, 36.6), (14, 34)), ((14, 34), (38.4, 31.4), (40, 8))]
    return [pt for seg in segs for pt in quad(*[P(*p) for p in seg])]


def background(seed):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NIGHT[i] * (1 - t) + NIGHT2[i] * t) for i in range(3)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for _ in range(70):
        x, y, depth = rnd.uniform(0, W), rnd.uniform(0, H), rnd.random()
        r, a = 1.5 + 2.5 * depth ** 2, int(50 + 90 * depth)
        col = GOLD if rnd.random() < 0.2 else TEXT
        ld.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
    img.alpha_composite(layer)
    return img


def header(img, idx, total):
    d = ImageDraw.Draw(img)
    d.polygon(star(M + 18, 86, 40), fill=GOLD)
    d.text((M + 50, 86), "AUGASTER", font=font("bold", 30), fill=TEXT, anchor="lm")
    d.text((M + 50 + d.textlength("AUGASTER", font=font("bold", 30)) + 16, 87), "AI FOR SMALL BUSINESS",
           font=font("sans", 22), fill=MUTED, anchor="lm")
    if total > 1:
        tag = f"{idx}/{total}"
        f = font("sans", 24)
        tw = d.textlength(tag, font=f)
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([W - M - tw - 32, 66, W - M, 106], radius=20, fill=(255, 255, 255, 34))
        img.alpha_composite(pill)
        d = ImageDraw.Draw(img)
        d.text((W - M - tw / 2 - 16, 86), tag, font=f, fill=TEXT, anchor="mm")


def tokens(text):
    """Split into (word, highlighted) pairs; **a b** highlights each word."""
    out = []
    for i, part in enumerate(re.split(r"\*\*", text)):
        out += [(w, i % 2 == 1) for w in part.split()]
    return out


def rich(img, text, x, y, f, maxw, fill=TEXT, lh=1.25, hl=GOLD):
    """Draw wrapped text with gold highlighter on **marked** words. Returns the y after the block."""
    d = ImageDraw.Draw(img)
    space = d.textlength(" ", font=f)
    lines, cur, cw = [], [], 0
    for w, h in tokens(text):
        ww = d.textlength(w, font=f)
        if cur and cw + space + ww > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append((w, h, ww)); cw += (space if cw else 0) + ww
    if cur:
        lines.append(cur)
    asc, desc = f.getmetrics()
    step = int((asc + desc) * lh)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    yy = y
    for line in lines:
        cx = x
        for i, (w, h, ww) in enumerate(line):
            if h:
                nxt_h = i + 1 < len(line) and line[i + 1][1]
                ld.rounded_rectangle([cx - 8, yy + asc * 0.22, cx + ww + (space if nxt_h else 8), yy + asc + desc * 0.5],
                                     radius=10, fill=hl + (150,))
            cx += ww + space
        yy += step
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    for line in lines:
        cx = x
        for w, h, ww in line:
            d.text((cx, y), w, font=f, fill=fill)
            cx += ww + space
        y += step
    return y


def wrap_mono(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw:
                cur = t
            else:
                lines.append(cur); cur = w
        lines.append(cur)
    return lines


def cover(c, total, seed):
    img = background(seed)
    header(img, 1, total)
    d = ImageDraw.Draw(img)
    y = 300
    if c.get("kicker"):
        d.text((M, y), c["kicker"].upper(), font=font("bold", 30), fill=AMBER)
        y += 70
    y = rich(img, c["title"], M, y, font("serif", 96), W - 2 * M, lh=1.12)
    if c.get("sub"):
        y = rich(img, c["sub"], M, y + 40, font("sans", 40), W - 2 * M, fill=MUTED, lh=1.35)
    d.text((W - M, H - 110), "Swipe  →", font=font("bold", 36), fill=GOLD, anchor="rm")
    return img


def prompt_slide(s, n, idx, total, seed, y0=170):
    img = background(seed)
    header(img, idx, total)
    d = ImageDraw.Draw(img)
    y = y0
    d.ellipse([M, y, M + 76, y + 76], fill=GOLD)
    d.text((M + 38, y + 39), str(n), font=font("bold", 42), fill=NIGHT, anchor="mm")
    y = rich(img, s["title"], M + 100, y + 4, font("serif", 64), W - 2 * M - 100, lh=1.08)
    y = max(y, y0 + 100) + 24
    if s.get("use"):
        y = rich(img, "**Use it:** " + s["use"], M, y, font("sans", 36), W - 2 * M, fill=MUTED, lh=1.3) + 26
    # prompt card
    f = font("mono", 33)
    lines = wrap_mono(d, s["prompt"], f, W - 2 * M - 70)
    asc, desc = f.getmetrics()
    step = int((asc + desc) * 1.32)
    top = y
    card_h = 70 + 50 + step * len(lines) + 20
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([M, top, W - M, top + card_h], radius=24, fill=CARD,
                                           outline=(227, 178, 92, 90), width=2)
    img.alpha_composite(card)
    d = ImageDraw.Draw(img)
    d.rectangle([M, top + 24, M + 6, top + card_h - 24], fill=GOLD)
    d.text((M + 35, top + 32), "PROMPT  ·  copy it, fill the [brackets]", font=font("bold", 26), fill=GOLD)
    yy = top + 90
    for ln in lines:
        d.text((M + 35, yy), ln, font=f, fill=TEXT)
        yy += step
    y = top + card_h + 30
    if s.get("tip"):
        y = rich(img, "**Tip:** " + s["tip"], M, y + 10, font("sans", 36), W - 2 * M, fill=TEXT, lh=1.3, hl=AMBER)
    return img, y


def cta_slide(c, idx, total, seed):
    img = background(seed)
    header(img, idx, total)
    d = ImageDraw.Draw(img)
    d.polygon(star(W / 2, 400, 170), fill=GOLD)
    y = rich_center(img, c["title"], 560, font("serif", 80))
    y = rich_center(img, c["body"], y + 30, font("sans", 38), fill=MUTED)
    d.text((W / 2, H - 120), "augaster.com", font=font("bold", 34), fill=GOLD, anchor="mm")
    return img


def rich_center(img, text, y, f, fill=TEXT):
    d = ImageDraw.Draw(img)
    words, lines, cur = text.replace("**", "").split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= W - 2 * M:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    asc, desc = f.getmetrics()
    for ln in lines:
        d.text((W / 2, y), ln, font=f, fill=fill, anchor="ma")
        y += int((asc + desc) * 1.2)
    return y


def main(path):
    c = json.load(open(path, encoding="utf-8"))
    out = os.path.dirname(os.path.abspath(path))
    total = len(c["slides"]) + 2
    imgs = [cover(c["cover"], total, 1)]
    for i, s in enumerate(c["slides"]):
        img, bottom = prompt_slide(s, i + 1, i + 2, total, i + 2)
        spare = H - 90 - bottom
        if spare > 0:  # centre the block vertically below the header
            img, bottom = prompt_slide(s, i + 1, i + 2, total, i + 2, y0=170 + spare // 2)
        if bottom > H - 60:
            raise SystemExit(f"slide {i + 2} prompt is too long ({bottom}px); shorten it")
        imgs.append(img)
    imgs.append(cta_slide(c["cta"], total, total, 99))
    for i, img in enumerate(imgs, 1):
        img.convert("RGB").save(os.path.join(out, f"slide-{i:02d}.png"))
    if c.get("caption"):
        open(os.path.join(out, "caption.txt"), "w", encoding="utf-8").write(c["caption"].strip() + "\n")
    print(f"wrote {len(imgs)} slides to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
