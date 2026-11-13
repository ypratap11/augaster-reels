# Augaster AI Digest — reel pipeline

Turns one verified AI news story into a narrated, captioned, branded 1080×1920 reel (30–35 sec), plus caption, LinkedIn post and website article.

## Setup
```bash
./setup.sh
```
Installs the Python packages and downloads the narrator voices: Kokoro (house voice `af_heart`, natural-sounding) and Piper "lessac" as a fallback.

## Generate an episode (script + posts)
```bash
export ANTHROPIC_API_KEY=...
python3 make_episode.py --title "Story headline" --url https://source-one --url https://source-two
```
Claude fetches every source; claims not confirmed by two sources are dropped (see `verification.json`). The script is checked for segment order, 82–98 words, spelled-out numbers and the CTA (service CTA on every third episode). Then render it as below.

## Pick a story automatically
```bash
python3 pick_story.py --out story.json          # web search, past 3 days, skips covered stories
python3 make_episode.py --story story.json
```
Roundups (AIToolsRecap, AI Weekly, Ground News…) are used as leads only: the picker follows them to the primary announcement and checks its date, and the generator requires every claim to have two sources, at least one primary or original reporting.

## Scheduled pipeline (GitHub Actions)
`.github/workflows/episode.yml` runs three times a day, 8:30 AM, 12:30 PM and 5:30 PM Pacific (DST-aware): pick → generate → render → commit `episodes/<date-slug>/` → upload artifacts → publish to Instagram when the repo variable `AUTO_PUBLISH` is `true` and the safety gate in `publish_instagram.py` passes.
- One-time: add the repo secret `A_API_KEY` (your Anthropic API key; the workflow passes it to the scripts as `ANTHROPIC_API_KEY`) (Settings → Secrets and variables → Actions).
- Manual run: Actions → Make episode → Run workflow; optionally give a title and space-separated source URLs to skip the picker.

## Make a reel
1. Create `episodes/YYYY-MM-DD-slug/script.json` (copy an existing episode). Keep total narration to ~90 words for 30–35 sec (the first episode is 91 words → 31.7 sec).
2. Render:
   ```bash
   python3 render_reel.py episodes/YYYY-MM-DD-slug/script.json --voice kokoro:af_heart
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

## Auto-publish to Instagram
`publish_instagram.py episodes/<date-slug>` posts the reel through the Instagram API (Instagram Login), but only if its gate passes: at least three claims each confirmed by two sources, a 25–40 sec 1080×1920 reel, no Oracle/Wipro mention, and no `published.json` yet. Use `--dry-run` to check the gate and see the caption without posting.

One-time setup (repo Settings → Secrets and variables → Actions):
- Secrets: `IG_ACCESS_TOKEN` (system-user token from the Meta app "Augaster Reels Publisher", Instagram API with Unified login; never expires), `IG_USER_ID` (the augaster.ai account id).
- Variables: `AUTO_PUBLISH` = `true` to turn posting on (anything else = off); `LINK_IN_BIO` = `1` once the profile has the augaster.com link.
- Keep the repo public: direct byte upload is tried first, but Meta currently rejects it, so posting falls back to Meta fetching `reel.mp4` from raw.githubusercontent.com.
- To retry a failed post: Actions → Publish episode → Run workflow, with the episode folder name.

## Queue and Money Lab (15-day buffer)
- `queue/<name>/` holds finished episodes (reel.mp4, posts.md, script.json, verification.json). `post_from_queue.py` posts the next one and moves it to `episodes/<date>-<name>`.
- The 12:30 PM slot on Tuesdays and Fridays posts Money Lab from the queue. Any other slot that can't make a verified news episode posts from the queue instead of skipping.
- Money Lab episodes are computed, not reported: `moneylab/episodes.py` (and `ep04_expectancy.py`) produce every number; the publish gate checks the code and results files exist and every claim carries a computed value.
- The health step opens a "Reels pipeline needs attention" GitHub issue (GitHub emails the owner) when a slot posts nothing, a publish fails, or fewer than 5 queue episodes remain.
- Add an episode: add a function to `moneylab/episodes.py`, run it, render with `python3 render_reel.py queue/<name>/script.json --voice kokoro:af_heart`, check the frames, commit.
