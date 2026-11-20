#!/usr/bin/env python3
"""Build a manual YouTube Studio upload pack from every published episode.

Usage: python export_youtube_pack.py <out_dir>

Copies each published reel (oldest first) as NN-<slug>.mp4 with a matching
NN-<slug>.txt holding the title and description (same text publish_youtube.py
would use), plus UPLOAD-GUIDE.txt. Skips episodes already on YouTube (youtube.json).
"""
import os, shutil, sys

from publish_youtube import metadata

ROOT = os.path.dirname(os.path.abspath(__file__))
GUIDE = """YouTube Shorts upload pack for Augaster AI ({n} reels, oldest first)

1. studio.youtube.com -> Create -> Upload videos -> select up to 15 .mp4 files at once.
2. For each video, open its draft and paste from the matching .txt file:
     Title       -> the TITLE line
     Description -> everything under DESCRIPTION
3. Audience: "No, it's not made for kids".
4. Altered or synthetic content: the narration is an AI voice that doesn't imitate a
   real person, and every description says so. "Yes" is the cautious choice.
5. Visibility: Public. Optional: schedule them a few hours apart instead of all at once,
   so the channel doesn't post 14 at the same minute.
6. Category (under Show more): Science & Technology.
7. When done, tell Claude which ones went up so it can mark them as on YouTube.
"""


def main(out):
    eps = sorted(d for d in os.listdir(os.path.join(ROOT, "episodes"))
                 if os.path.exists(os.path.join(ROOT, "episodes", d, "published.json"))
                 and not os.path.exists(os.path.join(ROOT, "episodes", d, "youtube.json")))
    os.makedirs(out, exist_ok=True)
    for i, d in enumerate(eps, 1):
        ep = os.path.join(ROOT, "episodes", d)
        title, desc, _ = metadata(ep)
        base = f"{i:02d}-{d}"
        shutil.copyfile(os.path.join(ep, "reel.mp4"), os.path.join(out, base + ".mp4"))
        with open(os.path.join(out, base + ".txt"), "w", encoding="utf-8") as f:
            f.write(f"TITLE\n{title}\n\nDESCRIPTION\n{desc}\n")
        print(f"{base}  ({len(title)} chars) {title}")
    with open(os.path.join(out, "UPLOAD-GUIDE.txt"), "w", encoding="utf-8") as f:
        f.write(GUIDE.format(n=len(eps)))
    print(f"wrote {len(eps)} reels to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "youtube-upload-pack")
