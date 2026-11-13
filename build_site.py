#!/usr/bin/env python3
"""Build the Augaster AI Digest website from blog/*.md into site/.

Zero dependencies, so Cloudflare Pages can run it as the build command:
  Build command:     python3 build_site.py
  Output directory:  site

Pages: site/index.html (newest first), site/<slug>/index.html per post,
site/feed.xml (RSS), site/sitemap.xml, site/robots.txt, plus About/Privacy/
Contact pages (needed for AdSense). Set ADSENSE_CLIENT (ca-pub-...) as a
Pages environment variable once approved and the ad script is added.
"""
import datetime, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
BASE = os.environ.get("SITE_URL", "https://digest.augaster.com").rstrip("/")
ADSENSE = os.environ.get("ADSENSE_CLIENT", "").strip()
SIGNUP = os.environ.get("NEWSLETTER_URL", "").strip()
NAME = "Augaster AI Digest"
TAGLINE = "One verified AI story, explained for small businesses."

CSS = """
:root{--night:#0D1030;--night2:#141938;--gold:#E3B25C;--star:#F2EEE3;--slate:#9AA0C8;--line:rgba(242,238,227,.12)}
*{box-sizing:border-box}body{margin:0;background:var(--night);color:var(--star);font:17px/1.65 'Hanken Grotesk',system-ui,sans-serif}
a{color:var(--gold)}header,main,footer{max-width:760px;margin:0 auto;padding:0 24px}
header{display:flex;justify-content:space-between;align-items:center;padding-top:24px;padding-bottom:24px;border-bottom:1px solid var(--line)}
header a{color:var(--star);text-decoration:none}.brand{font-family:'Cormorant Garamond',Georgia,serif;font-size:26px}
.brand span{color:var(--gold)}nav a{margin-left:20px;font-size:14px;color:var(--slate)}
h1,h2{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;line-height:1.15}h1{font-size:44px;margin:40px 0 8px}
.lede{color:var(--slate);margin:0 0 32px}.card{display:block;padding:20px 0;border-bottom:1px solid var(--line);text-decoration:none}
.card h2{font-size:26px;margin:4px 0;color:var(--star)}.card p{color:var(--slate);margin:4px 0 0}.meta{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}
article p,article li{color:var(--star)}article strong{color:var(--gold);font-weight:600}.video{margin:24px 0;padding:16px;border:1px solid var(--line);border-radius:8px}
.cta{margin:40px 0;padding:24px;background:var(--night2);border:1px solid var(--line);border-radius:8px}
footer{margin-top:56px;padding-top:24px;padding-bottom:40px;border-top:1px solid var(--line);font-size:14px;color:var(--slate)}footer a{color:var(--slate);margin-right:16px}
"""


def esc(s):
    return html.escape(s, quote=True)


def inline(t):
    t = esc(t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{m.group(2)}" rel="nofollow sponsored noopener">{m.group(1)}</a>'
               if "affiliate" in m.group(0).lower() or "ref=" in m.group(2) else f'<a href="{m.group(2)}" rel="noopener">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\"=>])(https?://[^\s<]+)", r'<a href="\1" rel="noopener">\1</a>', t)
    return t


def md_to_html(md):
    out, items = [], []
    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()
    for block in re.split(r"\n\s*\n", md.strip()):
        lines = block.strip().split("\n")
        if all(l.startswith("- ") for l in lines):
            items.extend(l[2:] for l in lines); continue
        flush()
        if lines[0].startswith("- ") is False and any(l.startswith("- ") for l in lines[1:]):
            out.append(f"<p>{inline(lines[0])}</p>")
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines[1:] if l.startswith('- ')) + "</ul>")
        elif lines[0].startswith("### "):
            out.append(f"<h2>{inline(lines[0][4:])}</h2>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    flush()
    return "\n".join(out)


def page(title, desc, body, path="/"):
    ads = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(ADSENSE)}" '
           f'crossorigin="anonymous"></script>') if ADSENSE else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}{path}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{BASE}/feed.xml">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{BASE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Hanken+Grotesk:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>{ads}</head><body>
<header><a class="brand" href="/">Augaster <span>AI Digest</span></a><nav><a href="/">Latest</a><a href="/about/">About</a><a href="https://augaster.com">augaster.com</a></nav></header>
<main>{body}</main>
<footer><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/feed.xml">RSS</a><br>
© {datetime.date.today().year} Augaster Technologies, Inc. Some links are affiliate links; we may earn a commission at no cost to you.</footer>
</body></html>"""


def load_posts():
    posts = []
    for fn in sorted(os.listdir(os.path.join(ROOT, "blog")), reverse=True):
        if not fn.endswith(".md"):
            continue
        raw = open(os.path.join(ROOT, "blog", fn), encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---\n(.*)\Z", raw, re.S)
        if not m:
            continue
        meta = {k.strip(): json.loads(v) for k, v in (l.split(":", 1) for l in m.group(1).split("\n") if ":" in l)}
        meta["body"] = m.group(2)
        posts.append(meta)
    return posts


def write(path, content):
    full = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith((".xml", ".txt")) else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)


def cta():
    signup = f'<a href="{esc(SIGNUP)}">Get the digest by email</a> · ' if SIGNUP else ""
    return (f'<div class="cta"><strong>Want AI set up for your business?</strong><br>'
            f'Augaster builds AI agents, automations and branded short videos for small businesses. '
            f'{signup}<a href="https://augaster.com/#contact">Start a conversation</a></div>')


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    posts = load_posts()
    cards = "".join(f'<a class="card" href="/{p["slug"]}/"><div class="meta">{esc(p["date"])}</div>'
                    f'<h2>{esc(p["title"])}</h2><p>{esc(p.get("description", ""))}</p></a>' for p in posts)
    write("/", page(f"{NAME} — {TAGLINE}", TAGLINE,
                    f'<h1>{NAME}</h1><p class="lede">{TAGLINE} Every claim checked against two sources.</p>{cards}'))
    for p in posts:
        video = (f'<div class="video">Watch the 30-second version: <a href="{esc(p["video"])}">Instagram reel</a></div>'
                 if p.get("video") else "")
        body = (f'<article><div class="meta" style="margin-top:32px">{esc(p["date"])} · {NAME}</div><h1>{esc(p["title"])}</h1>{video}'
                f'{md_to_html(p["body"])}</article>{cta()}')
        write(f'/{p["slug"]}/', page(f'{p["title"]} — {NAME}', p.get("description", ""), body, f'/{p["slug"]}/'))
    write("/about/", page(f"About — {NAME}", "About the Augaster AI Digest",
        "<h1>About</h1><p>The Augaster AI Digest picks one AI story at a time and explains what it means for small businesses. "
        "Every factual claim is checked against at least two sources, one of them primary where possible. Stories are researched "
        "and drafted with AI assistance and narrated with an AI voice; a human sets the rules and reviews the output.</p>"
        "<p>Published by Augaster Technologies, Inc., an AI engineering studio in the San Francisco Bay Area.</p>", "/about/"))
    write("/contact/", page(f"Contact — {NAME}", "Contact Augaster",
        '<h1>Contact</h1><p>Email <a href="mailto:hello@augaster.com">hello@augaster.com</a>.</p>', "/contact/"))
    write("/privacy/", page(f"Privacy — {NAME}", "Privacy policy",
        "<h1>Privacy policy</h1><p>This site does not require an account and does not sell personal data. Our host (Cloudflare) "
        "keeps standard server logs. If advertising is enabled, Google and its partners use cookies to serve ads based on your "
        "visits to this and other sites; you can opt out of personalised advertising at "
        '<a href="https://www.google.com/settings/ads">Google Ads Settings</a>. Affiliate links may set cookies with the merchant '
        "to credit a referral. Questions: hello@augaster.com.</p>", "/privacy/"))
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{BASE}/{p['slug']}/</link><guid>{BASE}/{p['slug']}/</guid>"
                    f"<pubDate>{datetime.datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y 08:00:00 -0800')}</pubDate>"
                    f"<description>{esc(p.get('description', ''))}</description></item>" for p in posts[:30])
    write("/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title>'
                       f"<link>{BASE}/</link><description>{TAGLINE}</description>{items}</channel></rss>")
    urls = "".join(f"<url><loc>{BASE}/{p['slug']}/</loc><lastmod>{p['date']}</lastmod></url>" for p in posts)
    write("/sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                          f"<url><loc>{BASE}/</loc></url>{urls}</urlset>")
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    print(f"built {len(posts)} posts into {OUT}")


if __name__ == "__main__":
    main()
