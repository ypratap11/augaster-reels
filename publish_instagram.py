#!/usr/bin/env python3
"""Publish a rendered episode to Instagram as a Reel.

Usage:
  python3 publish_instagram.py episodes/<date-slug>            # gate + publish
  python3 publish_instagram.py episodes/<date-slug> --dry-run  # gate + print caption only

Env (GitHub Actions secrets):
  IG_ACCESS_TOKEN   system-user access token from the Meta app "Augaster Reels
                    Publisher" (Instagram API, Unified login; never expires;
                    permission instagram_content_publish)
  IG_USER_ID        the augaster.ai Instagram professional account id
  LINK_IN_BIO=1     keep "(link in bio)" in the caption (set once the profile has
                    the augaster.com link)

The video bytes are sent straight to Meta (resumable upload), so the repo does
not need to be public.

Safety gate (nothing is posted unless all pass):
  - every kept claim in verification.json is supported by at least two sources,
    and at least three claims were kept
  - reel.mp4 is 25-60 sec, 1080x1920
  - the episode was not already published (published.json absent)
  - the caption has no Oracle/Wipro mention
Writes published.json (media id, permalink, time) and sets approved=true in
render_report.json on success.

Carousels (carousels/<slug>, made by render_carousel.py) are evergreen how-to
posts with no news claims. Their gate: approved.json from Pratap, not already
published, 2-10 JPEG slides at 1080x1350, caption.txt within limits and free of
Oracle/Wipro, and every slide publicly reachable (Instagram fetches carousel
images by URL from the public repo).
"""
import argparse, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

GRAPH = os.environ.get("IG_GRAPH_BASE", "https://graph.facebook.com/v23.0")
COVER_MS = 3000  # cover frame: the headline card, 3 sec in
BLOCKED = re.compile(r"\b(oracle|wipro)\b", re.I)


def fail(msg):
    print(f"::error::{msg}")
    raise SystemExit(msg)


def api(method, path, params):
    url = f"{GRAPH}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        body = body.replace(params.get("access_token", "") or "\x00", "***")
        fail(f"Instagram API {method} {path} failed ({e.code}): {body}")


def rupload(uri, token, headers, body):
    req = urllib.request.Request(uri, data=body, method="POST",
                                 headers={"Authorization": f"OAuth {token}", **headers})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            up = json.load(r)
    except urllib.error.HTTPError as e:
        return None, f"{e.code} {e.read().decode(errors='ignore')}"
    if up.get("success") is False:
        return None, f"not accepted: {up}"
    return up, None


def caption_from(posts_md, link_in_bio):
    m = re.search(r"## Instagram[^\n]*\n(.*?)\n---", posts_md, re.S)
    if not m:
        fail("posts.md has no '## Instagram' caption section")
    cap = m.group(1).strip()
    if not link_in_bio:
        cap = cap.replace(" (link in bio)", "").replace("Link in bio.", "Visit augaster.com.")
    return with_ai_voice_note(cap)


AI_VOICE_NOTE = "🎙️ Narrated with an AI voice."


def with_ai_voice_note(caption):
    """Disclose the AI narration on every reel (Digest and Money Lab alike), just above the hashtags."""
    caption = caption.strip()
    if AI_VOICE_NOTE in caption:
        return caption
    lines = caption.split("\n")
    i = len(lines)
    while i > 0 and (lines[i - 1].lstrip().startswith("#") or not lines[i - 1].strip()):
        i -= 1
    body, tags = "\n".join(lines[:i]).rstrip(), "\n".join(lines[i:]).strip()
    return f"{body}\n\n{AI_VOICE_NOTE}" + (f"\n\n{tags}" if tags else "")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return float(j["format"]["duration"]), s["width"], s["height"]


def gate(epdir):
    if os.path.exists(os.path.join(epdir, "published.json")):
        fail(f"{epdir} is already published")
    vpath = os.path.join(epdir, "verification.json")
    if not os.path.exists(vpath):
        fail(f"{epdir} has no verification.json (made before two-source checking); publish it by hand")
    v = json.load(open(vpath))
    kept = v.get("kept", [])
    if len(kept) < 3:
        fail(f"only {len(kept)} verified claims; need 3")
    if v.get("method") == "computed":
        # Money Lab and other evergreen episodes: every claim must come from committed code + results.
        root = os.path.dirname(os.path.abspath(__file__))
        for key in ("code", "results"):
            if not v.get(key) or not os.path.exists(os.path.join(root, v[key])):
                fail(f"computed episode is missing its {key} file")
        unbacked = [k["claim"] for k in kept if "computed" not in k]
        if unbacked:
            fail("claims without a computed value: " + "; ".join(unbacked))
    else:
        weak = [k["claim"] for k in kept if len(set(k.get("supported_by", []))) < 2]
        if weak:
            fail("claims without two sources: " + "; ".join(weak))
    dur, w, h = probe(os.path.join(epdir, "reel.mp4"))
    if not 25 <= dur <= 60:
        fail(f"reel is {dur:.1f} sec; allowed 25-60")
    if (w, h) != (1080, 1920):
        fail(f"reel is {w}x{h}; expected 1080x1920")
    return dur


def carousel_gate(cdir):
    """Carousels are evergreen how-to posts, so instead of the two-source check they need
    Pratap's explicit approval (approved.json, written only on his say-so)."""
    if os.path.exists(os.path.join(cdir, "published.json")):
        fail(f"{cdir} is already published")
    ap = os.path.join(cdir, "approved.json")
    if not os.path.exists(ap) or not json.load(open(ap)).get("approved_by"):
        fail(f"{cdir} has no approved.json; Pratap must approve a carousel before it posts")
    slides = sorted(f for f in os.listdir(cdir) if re.fullmatch(r"slide-\d\d\.jpg", f))
    if not 2 <= len(slides) <= 10:
        fail(f"carousel has {len(slides)} slides; Instagram allows 2-10")
    from PIL import Image
    for f in slides:
        if Image.open(os.path.join(cdir, f)).size != (1080, 1350):
            fail(f"{f} is not 1080x1350")
    cap_path = os.path.join(cdir, "caption.txt")
    if not os.path.exists(cap_path):
        fail("carousel has no caption.txt")
    return slides


def wait_ready(cid, token):
    for _ in range(40):  # up to ~10 min
        st = api("GET", cid, {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code in (None, "FINISHED"):
            return
        if code in ("ERROR", "EXPIRED"):
            fail(f"container {cid} {code}: {st.get('status')}")
        time.sleep(15)
    fail(f"container {cid} still processing after 10 min")


def publish_carousel(cdir, dry_run):
    slides = carousel_gate(cdir)
    cap = open(os.path.join(cdir, "caption.txt"), encoding="utf-8").read().strip()
    if os.environ.get("LINK_IN_BIO") != "1":
        cap = cap.replace(" (link in bio)", "").replace("Link in bio.", "Visit augaster.com.")
    if BLOCKED.search(cap):
        fail("caption mentions Oracle or Wipro")
    if len(cap) > 2200:
        fail(f"caption is {len(cap)} chars; Instagram max is 2200")
    root = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.relpath(os.path.abspath(cdir), root).replace(os.sep, "/")
    repo, ref = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME", "main")
    base = os.environ.get("CAROUSEL_BASE_URL") or (repo and f"https://raw.githubusercontent.com/{repo}/{ref}")
    print(f"gate passed: carousel of {len(slides)} slides, caption {len(cap)} chars")
    if dry_run:
        print(cap)
        return
    if not base:
        fail("set GITHUB_REPOSITORY or CAROUSEL_BASE_URL so Instagram can fetch the slides")
    urls = [f"{base}/{urllib.parse.quote(rel)}/{f}" for f in slides]
    for u in urls:  # Instagram fetches the images itself; make sure they are public first
        try:
            urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=30)
        except Exception as e:
            fail(f"slide not publicly reachable (pushed?): {u} ({e})")

    token = os.environ.get("IG_ACCESS_TOKEN") or fail("IG_ACCESS_TOKEN not set")
    user = os.environ.get("IG_USER_ID") or fail("IG_USER_ID not set")
    children = []
    for u in urls:
        c = api("POST", f"{user}/media", {"image_url": u, "is_carousel_item": "true", "access_token": token})
        children.append(c["id"])
    for cid in children:
        wait_ready(cid, token)
    parent = api("POST", f"{user}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                            "caption": cap, "access_token": token})
    wait_ready(parent["id"], token)
    pub = api("POST", f"{user}/media_publish", {"creation_id": parent["id"], "access_token": token})
    info = api("GET", pub["id"], {"fields": "permalink", "access_token": token})
    rec = {"platform": "instagram", "type": "carousel", "media_id": pub["id"], "permalink": info.get("permalink"),
           "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    json.dump(rec, open(os.path.join(cdir, "published.json"), "w"), indent=2)
    print(f"published: {rec['permalink']}")
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        open(gh, "a").write(f"Published carousel to Instagram: {rec['permalink']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir", help="episodes/<slug> for a reel, or carousels/<slug> for a carousel")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    epdir = a.episode_dir.rstrip("/")
    if os.path.exists(os.path.join(epdir, "carousel.json")):
        return publish_carousel(epdir, a.dry_run)

    dur = gate(epdir)
    cap = caption_from(open(os.path.join(epdir, "posts.md"), encoding="utf-8").read(),
                       os.environ.get("LINK_IN_BIO") == "1")
    if BLOCKED.search(cap):
        fail("caption mentions Oracle or Wipro")
    if len(cap) > 2200:
        fail(f"caption is {len(cap)} chars; Instagram max is 2200")
    print(f"gate passed: {dur:.1f} sec, caption {len(cap)} chars")
    if a.dry_run:
        print(cap)
        return

    token = os.environ.get("IG_ACCESS_TOKEN") or fail("IG_ACCESS_TOKEN not set")
    user = os.environ.get("IG_USER_ID") or fail("IG_USER_ID not set")
    reel = os.path.join(epdir, "reel.mp4")
    size = os.path.getsize(reel)

    c = api("POST", f"{user}/media", {"media_type": "REELS", "upload_type": "resumable",
                                       "caption": cap, "thumb_offset": str(COVER_MS),
                                       "share_to_feed": "true", "access_token": token})
    upload_uri = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{GRAPH.rsplit('/', 1)[-1]}/{c['id']}"
    with open(reel, "rb") as f:
        body = f.read()
    up, err = rupload(upload_uri, token, {"offset": "0", "file_size": str(size),
                                          "Content-Type": "application/octet-stream"}, body)
    if err:
        # Fallback: let Meta fetch the file from the public GitHub copy of the repo.
        repo, ref = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME", "main")
        if not repo:
            fail(f"video upload failed: {err}")
        rel = os.path.relpath(os.path.abspath(epdir), os.path.dirname(os.path.abspath(__file__))).replace(os.sep, "/")
        file_url = f"https://raw.githubusercontent.com/{repo}/{ref}/{urllib.parse.quote(rel)}/reel.mp4"
        print(f"::warning::byte upload failed ({err}); retrying with file_url {file_url}")
        up, err = rupload(upload_uri, token, {"file_url": file_url}, b"")
        if err:
            fail(f"video upload failed both ways: {err}")
    print(f"upload response: {up}")
    cid = c["id"]
    print(f"container {cid} (upload uri from Meta: {bool(c.get('uri'))}); waiting for Instagram to process the video")
    for _ in range(40):  # up to ~10 min
        st = api("GET", cid, {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            fail(f"container {cid} {code}: {st.get('status')}")
        time.sleep(15)
    else:
        fail(f"container {cid} still processing after 10 min")

    pub = api("POST", f"{user}/media_publish", {"creation_id": cid, "access_token": token})
    mid = pub["id"]
    info = api("GET", mid, {"fields": "permalink", "access_token": token})
    rec = {"platform": "instagram", "media_id": mid, "permalink": info.get("permalink"),
           "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    json.dump(rec, open(os.path.join(epdir, "published.json"), "w"), indent=2)
    rp = os.path.join(epdir, "render_report.json")
    r = json.load(open(rp)); r["approved"] = True; r["approved_by"] = "auto-publish gate"
    json.dump(r, open(rp, "w"), indent=2)
    print(f"published: {rec['permalink']}")
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        open(gh, "a").write(f"Published to Instagram: {rec['permalink']}\n")


if __name__ == "__main__":
    main()
