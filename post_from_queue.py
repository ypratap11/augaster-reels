#!/usr/bin/env python3
"""Post the next ready episode from queue/ and file it under episodes/.

Usage:
  python3 post_from_queue.py                 # next episode in queue (alphabetical)
  python3 post_from_queue.py --prefix moneylab-
  python3 post_from_queue.py --count         # print how many episodes are ready

An episode is ready when its folder has reel.mp4, posts.md, script.json and
verification.json and passes publish_instagram.py's gate. After posting, the
folder moves to episodes/<Pacific date>-<name> and its blog post is exported.
Prints the new episode folder on the last line (for the workflow).
"""
import argparse, datetime, os, shutil, subprocess, sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, "queue")
NEEDED = ("reel.mp4", "posts.md", "script.json", "verification.json")


def ready(prefix=""):
    if not os.path.isdir(QUEUE):
        return []
    return sorted(d for d in os.listdir(QUEUE)
                  if d.startswith(prefix) and all(os.path.exists(os.path.join(QUEUE, d, f)) for f in NEEDED))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    items = ready(a.prefix)
    if a.count:
        print(len(ready()))
        return
    if not items:
        raise SystemExit(f"::error::queue has no ready episodes{' with prefix ' + a.prefix if a.prefix else ''}")
    name = items[0]
    src = os.path.join("queue", name)
    args = [sys.executable, os.path.join(ROOT, "publish_instagram.py"), src] + (["--dry-run"] if a.dry_run else [])
    if subprocess.run(args, cwd=ROOT).returncode != 0:
        raise SystemExit(f"::error::publishing {src} failed")
    if a.dry_run:
        print(src)
        return
    date = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    dest = os.path.join("episodes", f"{date}-{name}")
    shutil.move(os.path.join(ROOT, src), os.path.join(ROOT, dest))
    subprocess.run([sys.executable, os.path.join(ROOT, "export_blog.py"), dest], cwd=ROOT, check=True)
    print(dest)


if __name__ == "__main__":
    main()
