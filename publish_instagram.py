#!/usr/bin/env python3
"""Publish a rendered episode to Instagram as a Reel.

Usage:
  python3 publish_instagram.py episodes/<date-slug>            # gate + publish
  python3 publish_instagram.py episodes/<date-slug> --dry-run  # gate + print caption only

Env (GitHub Actions secrets):
  IG_ACCESS_TOKEN   long-lived Instagram User access token (Instagram API with
                    Instagram Login, permission instagram_business_content_publish)
  IG_USER_ID        the augaster.ai Instagram professional account id
  PUBLIC_BASE_URL   where episode files are publicly readable, e.g.
                    https://raw.githubusercontent.com/ypratap11/augaster-reels/main
  LINK_IN_BIO=1     keep "(link in bio)" in the caption (set once the profile has
                    the augaster.com link)

Safety gate (nothing is posted unless all pass):
  - every kept claim in verification.json is supported by at least two sources,
    and at least three claims were kept
  - reel.mp4 is 25-40 sec, 1080x1920
  - the episode was not already published (published.json absent)
  - the caption has no Oracle/Wipro mention
Writes published.json (media id, permalink, time) and sets approved=true in
render_report.json on success.
"""
import argparse, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

GRAPH = os.environ.get("IG_GRAPH_BASE", "https://graph.instagram.com/v23.0")
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


def caption_from(posts_md, link_in_bio):
    m = re.search(r"## Instagram[^\n]*\n(.*?)\n---", posts_md, re.S)
    if not m:
        fail("posts.md has no '## Instagram' caption section")
    cap = m.group(1).strip()
    if not link_in_bio:
        cap = cap.replace(" (link in bio)", "").replace("Link in bio.", "Visit augaster.com.")
    return cap


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
    weak = [k["claim"] for k in kept if len(set(k.get("supported_by", []))) < 2]
    if weak:
        fail("claims without two sources: " + "; ".join(weak))
    dur, w, h = probe(os.path.join(epdir, "reel.mp4"))
    if not 25 <= dur <= 40:
        fail(f"reel is {dur:.1f} sec; allowed 25-40")
    if (w, h) != (1080, 1920):
        fail(f"reel is {w}x{h}; expected 1080x1920")
    return dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    epdir = a.episode_dir.rstrip("/")

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
    base = (os.environ.get("PUBLIC_BASE_URL") or fail("PUBLIC_BASE_URL not set")).rstrip("/")
    rel = urllib.parse.quote(epdir.strip("./"))
    video_url, cover_url = f"{base}/{rel}/reel.mp4", f"{base}/{rel}/thumbnail.png"

    c = api("POST", f"{user}/media", {"media_type": "REELS", "video_url": video_url,
                                       "cover_url": cover_url, "caption": cap,
                                       "share_to_feed": "true", "access_token": token})
    cid = c["id"]
    print(f"container {cid}; waiting for Instagram to process the video")
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
