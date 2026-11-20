#!/usr/bin/env python3
"""Upload a published episode to YouTube as a Short.

Usage:
  python3 publish_youtube.py episodes/<date-slug>            # upload
  python3 publish_youtube.py episodes/<date-slug> --dry-run  # print title/description only

Only episodes that already passed the Instagram safety gate (published.json exists)
are uploaded, so the two-source rule applies here too. Writes youtube.json.

Env (GitHub Actions secrets; get the refresh token once with youtube_auth.py):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
  YT_PRIVACY      public (default) | unlisted | private

Note: YouTube locks uploads from an *unaudited* Google Cloud API project as private,
and locked videos cannot be made public later. Keep the repo variable YT_PUBLISH off
until the project passes YouTube's API compliance audit.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

BLOCKED = re.compile(r"\b(oracle|wipro)\b", re.I)
AI_NOTE = "🎙️ Narrated with an AI voice."


def fail(msg):
    print(f"::error::{msg}")
    raise SystemExit(msg)


def metadata(epdir):
    script = json.load(open(os.path.join(epdir, "script.json"), encoding="utf-8"))
    posts = open(os.path.join(epdir, "posts.md"), encoding="utf-8").read()
    m = re.search(r"## Instagram[^\n]*\n(.*?)\n---", posts, re.S)
    caption = m.group(1).strip() if m else ""
    caption = caption.replace(" (link in bio)", "").replace("Link in bio.", "")
    lines = caption.split("\n")
    tags = [w.lstrip("#") for w in re.findall(r"#\w+", caption)]
    body = "\n".join(l for l in lines if not l.strip().startswith("#")
                     and not l.lower().startswith("full breakdown")).strip()
    story = script.get("story") or lines[0]
    hook = re.sub(r"[^\w)\]!?.,'’$%]+$", "", lines[0]).strip() if lines else ""
    fits = [t for t in (story, hook) if t and len(t) <= 85]
    if fits:
        title = min(fits, key=len) if len(story) > 70 else story
    else:  # cut at the last clause break, never mid-phrase
        cut = max(story.rfind(", ", 0, 85), story.rfind(": ", 0, 85))
        title = story[:cut] if cut > 30 else story[:84].rsplit(" ", 1)[0] + "…"
    title = f"{title} #Shorts"
    src = script.get("source_line") or ""
    desc = (f"{body}\n\n{AI_NOTE}\n"
            + (f"{src}\n" if src.lower().startswith("source") else f"Sources: {src}\n" if src else "")
            + "Full breakdown: https://augaster.com\n\n"
            + " ".join(f"#{t}" for t in ["Shorts"] + tags[:8]))
    if BLOCKED.search(title + desc):
        fail("title/description mentions Oracle or Wipro")
    return title[:100], desc[:4900], tags[:15]


def access_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ.get("YT_CLIENT_ID") or fail("YT_CLIENT_ID not set"),
        "client_secret": os.environ.get("YT_CLIENT_SECRET") or fail("YT_CLIENT_SECRET not set"),
        "refresh_token": os.environ.get("YT_REFRESH_TOKEN") or fail("YT_REFRESH_TOKEN not set"),
        "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen("https://oauth2.googleapis.com/token", data, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        fail(f"token refresh failed ({e.code}): {e.read().decode(errors='ignore')[:300]}")


def upload(path, title, desc, tags, token):
    meta = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "28"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"),
                       "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    size = os.path.getsize(path)
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            loc = r.headers["Location"]
        with open(path, "rb") as f:
            put = urllib.request.Request(loc, data=f.read(), method="PUT",
                                         headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"})
        with urllib.request.urlopen(put, timeout=600) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        fail(f"YouTube upload failed ({e.code}): {e.read().decode(errors='ignore')[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    epdir = a.episode_dir.rstrip("/")
    if not os.path.exists(os.path.join(epdir, "published.json")):
        fail(f"{epdir} has not passed the Instagram safety gate (no published.json)")
    if os.path.exists(os.path.join(epdir, "youtube.json")):
        fail(f"{epdir} is already on YouTube")
    title, desc, tags = metadata(epdir)
    print(f"title ({len(title)}): {title}")
    if a.dry_run:
        print(desc)
        return
    v = upload(os.path.join(epdir, "reel.mp4"), title, desc, tags, access_token())
    rec = {"platform": "youtube", "video_id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}",
           "privacy": v.get("status", {}).get("privacyStatus"),
           "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    json.dump(rec, open(os.path.join(epdir, "youtube.json"), "w"), indent=2)
    print(f"uploaded: {rec['url']} ({rec['privacy']})")
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        open(gh, "a").write(f"Uploaded to YouTube: {rec['url']}\n")


if __name__ == "__main__":
    main()
