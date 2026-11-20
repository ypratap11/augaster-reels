#!/usr/bin/env python3
"""Augaster AI Digest story picker.

Searches the web for the single most useful AI story for small-business owners from
the past three days and writes it as story.json for make_episode.py:

  python3 pick_story.py --out story.json
  python3 make_episode.py --story story.json
  python3 pick_story.py --beat security   # force a beat (see BEATS)

Topics rotate through BEATS (one beat per news episode, in order) so the feed
covers the whole AI world, always through a small-business lens. If nothing in
the beat qualifies, it falls back to the best story on any beat.

Needs ANTHROPIC_API_KEY. Skips stories already covered in episodes/ and anything
involving Oracle, Wipro or a Wipro client.
"""
import argparse, datetime, json, os, re, sys

import anthropic

from make_episode import BLOCKED, EPISODES, call, slugify

# Rotating topic beats. Every story still has to matter to a small-business owner.
BEATS = {
    "tools": "a new AI tool, feature, price change or free tier a small business can use now",
    "big-tech": "a move by OpenAI, Google, Microsoft, Apple, Meta, Anthropic or Amazon that changes what businesses or their customers can do",
    "industry": "AI arriving in one specific industry: retail, restaurants, real estate, healthcare clinics, legal, home services/trades, fitness, salons, or marketing agencies",
    "security": "AI scams, deepfakes, voice-cloning fraud, phishing or data-leak risks that hit businesses, with what to do about them",
    "rules": "a new AI law, regulation, court ruling, copyright or privacy rule that affects how businesses may use AI (no election or party politics)",
    "creative": "AI for marketing content: image, video, voice, music or design tools and platform changes for creators",
    "open-source": "open or local AI models and cheap self-hosted options that cut a small business's AI costs",
}


def next_beat():
    """Rotate by the number of news episodes made so far (Money Lab episodes don't count)."""
    n = sum(1 for d in os.listdir(EPISODES) if "moneylab" not in d and os.path.isdir(os.path.join(EPISODES, d)))
    return list(BEATS)[n % len(BEATS)]


SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Plain headline, e.g. 'Perplexity launches Teammates, always-on AI agents'"},
        "slug": {"type": "string", "description": "2-4 lowercase words joined by hyphens"},
        "announced": {"type": "string", "description": "Date of the announcement, YYYY-MM-DD"},
        "why": {"type": "string", "description": "One sentence: why a small-business owner should care"},
        "urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-4 source URLs: the primary source (company announcement) first, then independent coverage",
        },
        "runners_up": {"type": "array", "items": {"type": "string"}, "description": "Other candidates considered"},
    },
    "required": ["title", "slug", "announced", "why", "urls", "runners_up"],
    "additionalProperties": False,
}

SYSTEM = """You pick the story for the Augaster AI Digest, a 30-second video for small-business owners (local services, shops, consultants, small SaaS teams).

Search the web and pick the single most useful AI story announced in the given date window. Prefer:
- something a small business can use or should react to now (a new tool, feature, price change, free tier, policy or rule that affects them);
- concrete, checkable facts (what launched, who, price, availability);
- stories with a primary source (the company's own announcement or docs) and at least one independent report.
- this episode's beat, given in the request, when a qualifying story exists in it.
Avoid: funding rounds, research benchmarks, rumors, opinion pieces, stories already covered (listed below), and anything involving Oracle, Wipro, or any Wipro client company.
Good places to find leads: aitoolsrecap.com/ai-news-today, aiweekly.co/ai-news-today, ground.news, the OpenAI API changelog, Anthropic and Google announcements, Hugging Face trending, TechFundingNews, Crunchbase News.
Roundups and aggregators are leads only: always follow them to the underlying announcement, and check its date there. A story that a roundup presents as new but that was announced before the window is not eligible. Do not treat cumulative figures (total downloads, all-time stars) as daily or weekly numbers.
Return 2-4 source URLs you actually found: the primary announcement first, then at least one independent original report. Use a roundup URL only as a last extra source. Every URL must be a specific article or product page, not a home page.
Set "announced" to the date in the primary source.
Before returning, open each URL with web_fetch and keep only pages whose article text you could actually read; some sites block fetching. If fewer than two readable sources remain (one of them primary or original reporting), find replacements or pick a different story."""


def covered_stories():
    out = []
    for d in sorted(os.listdir(EPISODES)):
        p = os.path.join(EPISODES, d, "script.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                out.append(f"{d}: {json.load(f).get('story', '')}")
    return out


def pick(client, today, since, covered, beat):
    focus = (f"This episode's beat: {beat}: {BEATS[beat]}.\n" if beat else
             "Any beat is fine; pick the single most useful story.\n")
    content = (f"Today is {today}. Pick the best story announced between {since} and {today}.\n{focus}\n"
               "Already covered (do not repeat):\n" + ("\n".join(f"- {c}" for c in covered) or "- none"))
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 12},
             {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8}]
    print(f"searching AI news {since}..{today} (beat: {beat or 'any'})…", file=sys.stderr)
    story = call(client, SYSTEM, content, SCHEMA, tools=tools)

    urls = [u for u in dict.fromkeys(story["urls"]) if re.match(r"https?://", u)]
    if len(urls) < 2:
        raise ValueError(f"picker returned fewer than two usable sources: {story['urls']}")
    if BLOCKED.search(story["title"]) or any(BLOCKED.search(u) for u in urls):
        raise ValueError(f"picked an off-limits story: {story['title']}")
    story["urls"] = urls
    story["beat"] = beat or "any"
    return story


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="story.json")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    ap.add_argument("--beat", choices=list(BEATS), help="force a beat (default: rotate)")
    args = ap.parse_args()

    today = datetime.date.fromisoformat(args.today)
    since = today - datetime.timedelta(days=args.days)
    covered = covered_stories()
    client = anthropic.Anthropic()
    beat = args.beat or next_beat()
    try:
        story = pick(client, today, since, covered, beat)
    except (ValueError, SystemExit) as e:
        print(f"warning: beat '{beat}' gave no usable story ({e}); trying any beat", file=sys.stderr)
        try:
            story = pick(client, today, since, covered, None)
        except ValueError as e2:
            raise SystemExit(str(e2))

    try:
        announced = datetime.date.fromisoformat(story["announced"])
        if not since <= announced <= today:
            print(f"warning: announced {announced} is outside {since}..{today}", file=sys.stderr)
    except ValueError:
        print(f"warning: unparseable announced date {story['announced']!r}", file=sys.stderr)

    story["slug"] = slugify(story["slug"]) or slugify(story["title"])
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    print(json.dumps(story, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
