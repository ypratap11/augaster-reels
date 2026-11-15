"""Render the Augaster profile picture (1080x1080 PNG, circle-crop safe).

Usage: python make_avatar.py [out.png]
Uses the existing Augaster brand (augaster/augaster-brand-kit.html): the gold
dawn-star mark from augaster-mark.svg over the night background, with the
"Augaster" wordmark. Also writes <out>_preview.png (circle crop at 110 and 32 px).
"""
import os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S, SS = 1080, 2                      # output size, supersampling factor
NIGHT, NIGHT2 = (13, 16, 48), (20, 25, 56)          # --night, --night-2
GOLD, STARLIGHT = (227, 178, 92), (242, 238, 227)   # --gold, --starlight

# Brand wordmark is Cormorant Garamond 600; the logo SVG itself falls back to Georgia.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/CormorantGaramond-SemiBold.ttf",
    os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/CormorantGaramond-SemiBold.ttf"),
    "/usr/share/fonts/truetype/cormorant/CormorantGaramond-SemiBold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
]

def wordmark_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("No serif font found; install Cormorant Garamond.")

def quad(p0, p1, p2, n=60):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / n for i in range(n + 1))]

# augaster-mark.svg star path, in its 80x80 viewBox.
STAR = [((40, 8), (41.6, 31.4), (66, 34)), ((66, 34), (41.6, 36.6), (40, 60)),
        ((40, 60), (38.4, 36.6), (14, 34)), ((14, 34), (38.4, 31.4), (40, 8))]

def render():
    W = S * SS
    img = Image.new("RGB", (W, W)); d = ImageDraw.Draw(img)
    for y in range(W):
        t = y / W
        d.line([(0, y), (W, y)], fill=tuple(int(NIGHT[i] * (1 - t) + NIGHT2[i] * t) for i in range(3)))

    k = 8.5 * SS                     # viewBox unit -> pixels
    ox, oy = W / 2 - 40 * k, 120 * SS  # place mark centred horizontally
    P = lambda x, y: (ox + x * k, oy + y * k)

    glow = Image.new("RGB", (W, W)); gd = ImageDraw.Draw(glow)
    cx, cy = P(40, 34); r = 26 * k
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * 0.30) for c in GOLD))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(r * 0.45)))
    d = ImageDraw.Draw(img)

    pts = []
    for seg in STAR:
        pts += quad(*[P(*p) for p in seg])
    d.polygon(pts, fill=GOLD)
    dx, dy = P(58, 18); dr = 1.7 * k
    d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=GOLD)
    d.line(quad(P(12, 69), P(40, 75), P(68, 69)), fill=GOLD, width=int(1.6 * k), joint="curve")
    for end in (P(12, 69), P(68, 69)):   # round caps
        e = 0.8 * k; d.ellipse([end[0] - e, end[1] - e, end[0] + e, end[1] + e], fill=GOLD)

    font = wordmark_font(150 * SS)
    l, t, r_, b = d.textbbox((0, 0), "Augaster", font=font)
    d.text(((W - (r_ - l)) / 2 - l, 790 * SS - t), "Augaster", font=font, fill=STARLIGHT)
    return img.resize((S, S), Image.LANCZOS)

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
