#!/usr/bin/env python3
"""Turn an episode's website article into a blog post file.

Usage:
  python3 export_blog.py episodes/<date-slug>      # writes blog/<date-slug>.md
  python3 export_blog.py --all                     # every episode that has posts.md

Output is Markdown with YAML front matter (title, date, slug, description,
tags, video), which Next.js/Astro/Hugo/Jekyll and most CMS importers read.
Wire the blog/ folder into augaster.com once we know what the site runs on.
"""
import argparse, glob, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))


def export(epdir):
    epdir = epdir.rstrip("/")
    name = os.path.basename(epdir)
    md = open(os.path.join(epdir, "posts.md"), encoding="utf-8").read()
    m = re.search(r"## Website article[^\n]*\n\n### ([^\n]+)\n\n(.*)\Z", md, re.S)
    if not m:
        raise SystemExit(f"{epdir}: no website article in posts.md")
    title, body = m.group(1).strip(), m.group(2).strip()
    first = re.sub(r"\*\*[^*]+\*\*\s*", "", body.split("\n\n")[0]).strip()
    desc = (first[:157] + "...") if len(first) > 160 else first
    cap = re.search(r"## Instagram[^\n]*\n(.*?)\n---", md, re.S)
    tags = re.findall(r"#(\w+)", cap.group(1)) if cap else []
    front = {
        "title": title,
        "date": name[:10],
        "slug": name[11:] or name,
        "description": desc,
        "tags": [t for t in tags if t != "AugasterAIDigest"][:6],
        "series": json.load(open(os.path.join(epdir, "script.json"))).get("series", "Augaster AI Digest") if os.path.exists(os.path.join(epdir, "script.json")) else "Augaster AI Digest",
    }
    pub = os.path.join(epdir, "published.json")
    if os.path.exists(pub):
        link = json.load(open(pub)).get("permalink")
        if link and "/reel/" in link:
            front["video"] = link
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()] + ["---", ""]
    os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)
    out = os.path.join(ROOT, "blog", f"{name}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + body + "\n")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir", nargs="?")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    dirs = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "episodes", "*", "posts.md"))) \
        if a.all else [a.episode_dir]
    for d in dirs:
        if d:
            print(export(d))


if __name__ == "__main__":
    main()
