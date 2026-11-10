#!/usr/bin/env python3
"""Augaster AI Digest episode generator.

story (title + source URLs) -> verified facts -> episodes/<date-slug>/script.json + posts.md

Usage:
  python3 make_episode.py --title "Perplexity launches Teammates" \
      --url https://www.perplexity.ai/hub/products/teammate \
      --url https://letsdatascience.com/news/... [--date 2026-11-09] [--slug perplexity-teammates]

Needs ANTHROPIC_API_KEY (or another credential the Anthropic SDK can find).

Two model calls:
  1. verify: Claude fetches every source and lists the factual claims each one supports.
     Claims supported by fewer than two sources are dropped here, in code.
  2. write:  Claude writes the six-segment script and posts.md using only the surviving claims.
     The result is checked in code (segment order, word count, spelled-out numbers,
     CTA) and sent back for a fix if it fails.
"""
import argparse, datetime, json, os, re, sys

import anthropic

MODEL = "claude-sonnet-5-5"  # $2/$10 per MTok; switch back to "claude-opus-5-5" for higher quality
BETAS = ["server-side-fallback-2026-07-01"]
ROOT = os.path.dirname(os.path.abspath(__file__))
EPISODES = os.path.join(ROOT, "episodes")

# Measured: the first episode is 91 words -> 31.7 sec at LENGTH_SCALE 0.95 (~3 words/sec plus
# 0.3 sec padding per segment). 82-98 words lands in the 30-35 sec target.
WORDS_MIN, WORDS_MAX = 82, 98
KINDS = ["hook", "news", "news", "analysis", "analysis", "cta"]
LABELS = {1: "WHAT HAPPENED", 3: "WHAT IT MEANS FOR YOU", 4: "OUR TAKE"}
BLOCKED = re.compile(r"\b(oracle|wipro)\b", re.I)  # also screened by the model for Wipro clients

CTA = {
    "follow": {
        "label": "AUGASTER AI DIGEST",
        "title": "Full breakdown + sources",
        "point": "augaster.com",
        "narration": "Full breakdown and sources on augaster dot com. Follow for weekly practical AI.",
    },
    "service": {
        "label": "AUGASTER TECHNOLOGIES",
        "title": "Want this set up for your business?",
        "point": "augaster.com",
        "narration": "Full breakdown and sources on augaster dot com. Want this set up for your business? Link in bio.",
    },
}

# ---------------------------------------------------------------- schemas

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "sources": {
            "type": "array",
            "description": "One entry per source URL, in the order given.",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "name": {"type": "string", "description": "Short publisher name, e.g. 'Perplexity product page'"},
                    "fetched": {"type": "boolean", "description": "false if the page could not be read"},
                    "published": {"type": "string", "description": "Publication date as printed on the page, or ''"},
                    "kind": {
                        "type": "string",
                        "enum": ["primary", "original_reporting", "roundup"],
                        "description": "primary = the company's own announcement/docs/changelog; "
                                       "original_reporting = a journalist's own article; "
                                       "roundup = daily news digest, aggregator or list that summarizes others",
                    },
                },
                "required": ["index", "name", "fetched", "published", "kind"],
                "additionalProperties": False,
            },
        },
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "supported_by": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Indexes of sources that state this claim explicitly",
                    },
                    "evidence": {"type": "string", "description": "Short quote or paraphrase from each supporting source"},
                },
                "required": ["claim", "supported_by", "evidence"],
                "additionalProperties": False,
            },
        },
        "off_limits": {
            "type": "boolean",
            "description": "true if the story involves Oracle, Wipro, or a Wipro client",
        },
        "off_limits_reason": {"type": "string"},
    },
    "required": ["sources", "claims", "off_limits", "off_limits_reason"],
    "additionalProperties": False,
}

SEGMENT = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["hook", "news", "analysis", "cta"]},
        "label": {"type": "string"},
        "title": {"type": "string"},
        "point": {"type": "string"},
        "narration": {"type": "string"},
    },
    "required": ["kind", "label", "title", "point", "narration"],
    "additionalProperties": False,
}

WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "story": {"type": "string", "description": "One-line story summary"},
        "source_line": {"type": "string", "description": "e.g. 'Sources: Perplexity, Digital Trends'"},
        "segments": {"type": "array", "items": SEGMENT},
        "instagram_caption": {"type": "string"},
        "linkedin_post": {"type": "string"},
        "article_title": {"type": "string"},
        "article_body": {"type": "string", "description": "Markdown, bold run-in headings, no Sources section"},
    },
    "required": ["story", "source_line", "segments", "instagram_caption",
                 "linkedin_post", "article_title", "article_body"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------- prompts

VERIFY_SYSTEM = """You fact-check AI news for the Augaster AI Digest, a short video series for small-business owners.

Fetch every source URL with the web_fetch tool, then list the factual claims about the story that the sources state.
- A claim is one checkable fact: what launched, who made it, when, price, availability, how it works, limits.
- For each claim, list every source index that states it explicitly. Do not count a source that only implies it.
- Copy numbers, prices and dates exactly as the sources print them. Where sources disagree, record each version as a separate claim.
- If a page cannot be fetched, mark it fetched=false and give it no claims.
- Classify each source: primary (the company's own announcement, docs, changelog), original_reporting, or roundup (daily digests and aggregators such as AIToolsRecap, AI Weekly, Ground News). If a roundup links to the underlying announcement, fetch that too and attribute claims to it only if it actually states them.
- Numbers: say exactly what a figure measures. A cumulative or rolling total (total downloads, all-time stars) is not a daily or weekly figure; write it as the sources define it.
- Dates: record when the thing was actually announced or released, from the primary source if available, not when a roundup mentioned it. If the announcement is older than the sources imply, include that as a claim.
- Set off_limits=true if the story involves Oracle, Wipro, or any Wipro client company."""

WRITE_SYSTEM = """You write the Augaster AI Digest: 30-35 second vertical news reels for small-business owners, plus matching posts.

Use only the verified claims you are given. Do not add any other fact, number, date, price or name. Opinion and advice are fine in the analysis and "our take" segments, but phrase them as advice, not as fact.

Reel script: exactly six segments, in this order:
1. hook: names a specific benefit or surprise. label "THIS WEEK IN AI".
2. news: what happened. label "WHAT HAPPENED".
3. news: how it works or a key detail. label is a short caps phrase such as "HOW IT WORKS".
4. analysis: what it means for a small business, including the catch. label "WHAT IT MEANS FOR YOU".
5. analysis: our practical take, starting the narration with "Our take:". label "OUR TAKE".
6. cta: copy exactly the CTA segment you are given.

Narration rules (the narration is read by a text-to-speech voice):
- 85 to 95 words across all six segments, CTA included (the reel must run 30-35 seconds). Short, spoken sentences.
- Spell out every number, price and year in words ("two hundred dollars a month", "twenty twenty-six"). No digits, no "$" or "%".
- Say "dot com", never ".com".
On-screen title and point use normal written formatting ("$200 a month"). Keep titles under about 60 characters and points under about 50. A point may be "" if nothing useful fits.

Posts:
- instagram_caption: hook line, three lines starting with ✅ or ⚠️, "Our take:" line, "Full breakdown + sources: augaster.com (link in bio)", then 5-8 hashtags including #AugasterAIDigest.
- linkedin_post: first-person from Pratap, short paragraphs and bullets, "What it means for a small business" section, ends with a "Sources:" line naming the publishers, then 3 hashtags.
- article_body: sections with bold run-in headings: **What happened.** **How it works.** **Availability and price.** (only if verified) **What it means for small businesses.** **Our take.** Do not include a sources list; it is added separately."""

# ---------------------------------------------------------------- API

def call(client, system, content, schema, tools=None, effort="high"):
    """One structured-output request, resuming server-tool pauses. Returns parsed JSON."""
    messages = [{"role": "user", "content": content}]
    kw = dict(model=MODEL, max_tokens=64000, system=system,
              output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
              betas=BETAS, fallbacks="default")
    if tools:
        kw["tools"] = tools
    for _ in range(8):
        with client.beta.messages.stream(messages=messages, **kw) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": msg.content})
            continue
        break
    if msg.stop_reason == "refusal":
        raise SystemExit(f"model declined: {getattr(msg.stop_details, 'category', None)} (request {msg._request_id})")
    if msg.stop_reason == "max_tokens":
        raise SystemExit(f"response truncated at max_tokens (request {msg._request_id})")
    if msg.stop_reason == "pause_turn":
        raise SystemExit(f"server tools still paused after retries (request {msg._request_id})")
    text = "".join(b.text for b in msg.content if b.type == "text")
    return json.loads(text)


def verify(client, title, urls):
    listing = "\n".join(f"[{i}] {u}" for i, u in enumerate(urls))
    content = f"Story: {title}\n\nSources:\n{listing}\n\nFetch each source and list the claims."
    tools = [{"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": len(urls) + 3}]
    return call(client, VERIFY_SYSTEM, content, VERIFY_SCHEMA, tools=tools)


def write(client, title, claims, sources, cta, feedback=None, previous=None):
    facts = "\n".join(f"- {c['claim']}  (sources: {', '.join(sources[i]['name'] for i in c['supported_by'])})"
                      for c in claims)
    content = (f"Story: {title}\n\nVerified claims (each confirmed by at least two sources):\n{facts}\n\n"
               f"CTA segment to copy exactly:\n{json.dumps({'kind': 'cta', **cta}, ensure_ascii=False)}")
    if feedback:
        content += (f"\n\nYour previous draft:\n{json.dumps(previous, ensure_ascii=False)}\n\n"
                    "It failed these checks. Fix them and return the full corrected draft:\n- " + "\n- ".join(feedback))
    return call(client, WRITE_SYSTEM, content, WRITE_SCHEMA)

# ---------------------------------------------------------------- checks (no API needed)

def keep_corroborated(verified, n_sources):
    """Keep claims confirmed by two distinct fetched sources, at least one of them primary or
    original reporting (roundups alone don't count). Returns (kept, dropped)."""
    fetched = {s["index"] for s in verified["sources"] if s["fetched"]}
    solid = {s["index"] for s in verified["sources"] if s["fetched"] and s["kind"] != "roundup"}
    kept, dropped = [], []
    for c in verified["claims"]:
        srcs = sorted({i for i in c["supported_by"] if i in fetched and 0 <= i < n_sources})
        ok = len(srcs) >= 2 and any(i in solid for i in srcs)
        (kept if ok else dropped).append({**c, "supported_by": srcs})
    return kept, dropped


def narration_words(segments):
    return sum(len(s["narration"].split()) for s in segments)


def check_draft(draft, cta):
    problems = []
    segs = draft["segments"]
    kinds = [s["kind"] for s in segs]
    if kinds != KINDS:
        problems.append(f"segment kinds must be {KINDS}, got {kinds}")
    else:
        if segs[0]["label"] != "THIS WEEK IN AI":
            problems.append('hook label must be "THIS WEEK IN AI"')
        for i, lab in LABELS.items():
            if segs[i]["label"] != lab:
                problems.append(f'segment {i + 1} label must be "{lab}"')
        if not segs[4]["narration"].startswith("Our take"):
            problems.append('segment 5 narration must start with "Our take:"')
        if {k: segs[5][k] for k in cta} != cta:
            problems.append("CTA segment must match the given CTA exactly")
    words = narration_words(segs)
    if not WORDS_MIN <= words <= WORDS_MAX:
        problems.append(f"narration is {words} words; it must be {WORDS_MIN}-{WORDS_MAX} (aim for 90)")
    for i, s in enumerate(segs):
        if re.search(r"[0-9$%]", s["narration"]):
            problems.append(f"segment {i + 1} narration has digits or symbols; spell them out: {s['narration']!r}")
        if re.search(r"\.com\b", s["narration"], re.I):
            problems.append(f'segment {i + 1} narration must say "dot com", not ".com"')
    blob = json.dumps(draft, ensure_ascii=False)
    if BLOCKED.search(blob):
        problems.append("draft mentions Oracle or Wipro, which is off-limits")
    return problems


def episode_number(slug_dir):
    """1-based number of this episode among all episodes (existing + this one)."""
    existing = sorted(d for d in os.listdir(EPISODES)
                      if os.path.isfile(os.path.join(EPISODES, d, "script.json")))
    if slug_dir in existing:
        return existing.index(slug_dir) + 1
    return len(existing) + 1


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")

# ---------------------------------------------------------------- output

def build_script(date, draft, sources_used):
    return {
        "episode": date,
        "series": "Augaster AI Digest",
        "story": draft["story"],
        "sources": [{"name": s["name"], "url": s["url"]} for s in sources_used],
        "source_line": draft["source_line"],
        "segments": draft["segments"],
    }


def build_posts(date, title, draft, sources_used):
    d = datetime.date.fromisoformat(date)
    heading = f"{d.day} {d.strftime('%b %Y')}"
    srcs = "\n".join(f"- {s['name']}{', ' + s['published'] if s.get('published') else ''}: {s['url']}"
                     for s in sources_used)
    return (f"# Augaster AI Digest — {heading}: {title}\n\n"
            f"## Instagram / YouTube Shorts caption\n\n{draft['instagram_caption'].strip()}\n\n---\n\n"
            f"## LinkedIn post\n\n{draft['linkedin_post'].strip()}\n\n---\n\n"
            f"## Website article (augaster.com/digest)\n\n### {draft['article_title'].strip()}\n\n"
            f"{draft['article_body'].strip()}\n\n**Sources**\n{srcs}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", help="story.json from pick_story.py (title, slug, urls)")
    ap.add_argument("--title", help="story headline")
    ap.add_argument("--url", action="append", default=[], help="source URL (repeat; at least two)")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--slug", help="folder slug (default: from title)")
    ap.add_argument("--cta", choices=["auto", "follow", "service"], default="auto",
                    help="auto = service CTA on every third episode")
    ap.add_argument("--force", action="store_true", help="overwrite an existing episode folder")
    ap.add_argument("--print-dir", action="store_true", help="print only the episode folder path on success")
    args = ap.parse_args()

    if args.story:
        with open(args.story, encoding="utf-8") as f:
            picked = json.load(f)
        args.title = args.title or picked["title"]
        args.url = args.url or picked["urls"]
        args.slug = args.slug or picked.get("slug")
    if not args.title:
        raise SystemExit("pass --title or --story")
    if len(args.url) < 2:
        raise SystemExit("need at least two source URLs: every claim must appear in two sources")
    if BLOCKED.search(args.title):
        raise SystemExit("story involves Oracle or Wipro; off-limits")

    folder = f"{args.date}-{args.slug or slugify(args.title)}"
    epdir = os.path.join(EPISODES, folder)
    if os.path.exists(os.path.join(epdir, "script.json")) and not args.force:
        raise SystemExit(f"{folder} already exists (use --force to overwrite)")
    n = episode_number(folder)
    cta_kind = args.cta if args.cta != "auto" else ("service" if n % 3 == 0 else "follow")
    cta = CTA[cta_kind]

    client = anthropic.Anthropic()

    print(f"[1/2] verifying {len(args.url)} sources…", file=sys.stderr)
    verified = verify(client, args.title, args.url)
    if verified["off_limits"]:
        raise SystemExit(f"off-limits story: {verified['off_limits_reason']}")
    sources = {s["index"]: {**s, "url": args.url[s["index"]]}
               for s in verified["sources"] if 0 <= s["index"] < len(args.url)}
    kept, dropped = keep_corroborated(verified, len(args.url))
    print(f"      {len(kept)} claims confirmed by 2+ sources (1+ non-roundup), {len(dropped)} dropped", file=sys.stderr)
    for s in verified["sources"]:
        print(f"      source [{s['index']}] fetched={s['fetched']} kind={s['kind']} {s['name']} {s['published']}", file=sys.stderr)
    for c in verified["claims"]:
        mark = "keep" if any(k["claim"] == c["claim"] for k in kept) else "drop"
        print(f"      {mark} {c['supported_by']} {c['claim']}", file=sys.stderr)
    if len(kept) < 3:
        raise SystemExit("fewer than three claims are confirmed by two sources; pick a better-covered story")

    print(f"[2/2] writing episode #{n} ({cta_kind} CTA)…", file=sys.stderr)
    draft, problems = None, None
    for attempt in range(3):
        draft = write(client, args.title, kept, sources, cta, feedback=problems, previous=draft)
        problems = check_draft(draft, cta)
        if not problems:
            break
        print(f"      draft {attempt + 1} failed checks: {problems}", file=sys.stderr)
    if problems:
        raise SystemExit("draft still fails checks after 3 attempts:\n- " + "\n- ".join(problems))

    used = sorted({i for c in kept for i in c["supported_by"]})
    sources_used = [sources[i] for i in used]
    os.makedirs(epdir, exist_ok=True)
    with open(os.path.join(epdir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(build_script(args.date, draft, sources_used), f, indent=2, ensure_ascii=False)
    with open(os.path.join(epdir, "posts.md"), "w", encoding="utf-8") as f:
        f.write(build_posts(args.date, args.title, draft, sources_used))
    with open(os.path.join(epdir, "verification.json"), "w", encoding="utf-8") as f:
        json.dump({"title": args.title, "episode_number": n, "cta": cta_kind,
                   "sources": list(sources.values()), "kept": kept, "dropped": dropped},
                  f, indent=2, ensure_ascii=False)
    if args.print_dir:
        print(epdir)
        return
    print(json.dumps({"episode": folder, "dir": epdir, "words": narration_words(draft["segments"]),
                      "cta": cta_kind, "claims_kept": len(kept), "claims_dropped": len(dropped)}, indent=2))


if __name__ == "__main__":
    main()
