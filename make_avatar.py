"""Render the Augaster profile picture (1080x1080 PNG, circle-crop safe).

Usage: python make_avatar.py [out.png]
Design: custom "A" whose crossbar is the amber brand bar from the reels, with
"AUGASTER" underneath, inside a thin sky-blue ring. Uses render_reel.py's palette.
Also writes <out>_preview.png showing the circle crop at 110 px and 32 px.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

S = 1080
BG_TOP, BG_BOT = (8, 14, 30), (18, 30, 58)
AMBER, SKY, WHITE = (245, 166, 35), (56, 189, 248), (245, 247, 250)

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "C:/Windows/Fonts/seguibl.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
]

def heavy_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("No heavy font found; install Inter (see setup.sh).")

def a_mark(d, cx, top, h, w):
    """White legs meeting at a flat apex; the crossbar is the amber brand bar."""
    stroke = w * 0.24
    apex_l, apex_r = (cx - stroke * 0.55, top), (cx + stroke * 0.55, top)
    d.polygon([apex_l, apex_r, (cx + w / 2, top + h), (cx + w / 2 - stroke, top + h)], fill=WHITE)
    d.polygon([apex_l, apex_r, (cx - w / 2 + stroke, top + h), (cx - w / 2, top + h)], fill=WHITE)
    by = top + h * 0.62
    d.rounded_rectangle([cx - w * 0.36, by, cx + w * 0.36, by + stroke * 0.62], radius=10, fill=AMBER)

def render():
    img = Image.new("RGB", (S, S)); d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        d.line([(0, y), (S, y)], fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3)))
    d.ellipse([30, 30, S - 30, S - 30], outline=SKY, width=14)  # sits just inside Instagram's circle crop
    a_mark(d, S / 2, 220, 430, 440)
    font = heavy_font(118)
    l, t, r, b = d.textbbox((0, 0), "AUGASTER", font=font)
    d.text(((S - (r - l)) / 2 - l, 720 - t), "AUGASTER", font=font, fill=WHITE)
    return img

def circle(img, size):
    p = img.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size)); ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    c = Image.new("RGB", (size, size), (255, 255, 255)); c.paste(p, (0, 0), m)
    return c

def main(out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img = render()
    img.save(out)
    prev = Image.new("RGB", (170, 120), (255, 255, 255))
    prev.paste(circle(img, 110), (5, 5)); prev.paste(circle(img, 32), (130, 44))
    prev.save(os.path.splitext(out)[0] + "_preview.png")
    print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "brand/profile_picture.png")
