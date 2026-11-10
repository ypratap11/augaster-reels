# Augaster AI Digest — reel pipeline

Turns one verified AI news story into a narrated, captioned, branded 1080×1920 reel (30–35 sec), plus caption, LinkedIn post and website article.

## Setup
```bash
./setup.sh
```
Installs the Python packages and downloads the offline narrator voice (Piper, en-US "lessac").

## Generate an episode (script + posts)
```bash
export ANTHROPIC_API_KEY=...
python3 make_episode.py --title "Story headline" --url https://source-one --url https://source-two
```
Claude fetches every source; claims not confirmed by two sources are dropped (see `verification.json`). The script is checked for segment order, 82–98 words, spelled-out numbers and the CTA (service CTA on every third episode). Then render it as below.

## Make a reel
1. Create `episodes/YYYY-MM-DD-slug/script.json` (copy an existing episode). Keep total narration to ~90 words for 30–35 sec (the first episode is 91 words → 31.7 sec).
2. Render:
   ```bash
   python3 render_reel.py episodes/YYYY-MM-DD-slug/script.json --voice voices/en-us-lessac-medium.onnx
   ```
   Or narrate it yourself: `--voiceover my_recording.m4a`
3. Outputs in the episode folder: `reel.mp4`, `captions.srt`, `thumbnail.png`, `render_report.json`.
4. Write `posts.md` (caption, LinkedIn, article) alongside.

## script.json
| field | meaning |
|---|---|
| `segments[].kind` | `hook`, `news`, `analysis`, `cta` |
| `label` | small chip above the headline |
| `title` | big on-screen headline |
| `point` | supporting line (CTA: the URL) |
| `narration` | what the voice says |
| `sources` | URLs every claim was checked against |

## Rules
- Every claim must be confirmed in at least two sources, one primary where possible.
- One story per reel. Hook names a specific benefit or surprise.
- `render_report.json` starts with `"approved": false`; nothing is published until Pratap approves.

Tuning: `LENGTH_SCALE` in `render_reel.py` (<1 = faster speech); brand colors in `BRAND`.
