# Augaster AI Digest — reel pipeline (handoff notes for Claude Code)

Owner: Pratap Yeragudipati, Augaster Technologies. Remote: https://github.com/ypratap11/augaster-reels (public, currently empty).

## What exists
- `render_reel.py` — script.json → narrated, captioned, branded 1080×1920 MP4 (30–35 sec). Offline Piper voice (`voices/en-us-lessac-medium.onnx`, downloaded by `setup.sh`), or `--voiceover my.wav`. Writes `reel.mp4`, `captions.srt`, `thumbnail.png`, `render_report.json` into the episode folder.
- `episodes/2026-11-09-perplexity-teammates/` — first episode (script, reel, posts.md with caption / LinkedIn / article).
- `offers/upwork-short-video-offer.md` — service offer copy.
- Reel tracker (claude.ai artifact, not in this repo): https://claude.ai/artifact/VMznDCb5UTVovuLP4wQKXM — collection `reels`, one doc per episode id with `date, title, story, source_url, status (draft|approved|posted), cta (follow|service), views{youtube,instagram,linkedin}, clicks`.

## Tasks, in order
1. **Push:** `git remote add origin https://github.com/ypratap11/augaster-reels.git && git push -u origin main`.
2. **Verify locally:** run `./setup.sh`, then re-render the existing episode and confirm a ~32 sec MP4. Needs ffmpeg and Python 3.10+.
3. **Episode generator** (`make_episode.py`): given a story (title + source URLs), call the Anthropic API (`ANTHROPIC_API_KEY`) to verify claims against the sources, then write `script.json` in the existing schema plus `posts.md`. Rules:
   - One story per reel; ~75 words of narration total (30–35 sec at `LENGTH_SCALE = 0.95`).
   - Six segments: hook, news, news, analysis (what it means for a small business), our take, CTA ("Full breakdown and sources on augaster dot com…").
   - Every factual claim must appear in at least two sources; if not, drop the claim. Never invent numbers or dates.
   - Spell out numbers and "dot com" in `narration` so the voice reads them correctly; on-screen `title`/`point` use normal formatting.
   - Every third episode uses a service CTA ("Want this set up for your business? Link in bio.").
4. **Story picker:** pick the single most useful AI story for small-business owners from the past 3 days (web search via the API's web search tool, or the user's existing 8 AM AI Digest output if he points you to it — ask him where it runs).
5. **Schedule:** GitHub Actions workflow on Mon/Wed/Fri 8:30 AM Pacific (cron in UTC, e.g. `30 16 * * 1,3,5` during PST) that runs picker → generator → renderer, commits the episode folder, and uploads `reel.mp4` as a workflow artifact. Secrets: `ANTHROPIC_API_KEY` only. Cache the Piper voice.
6. **Approval stays human:** never auto-publish. `render_report.json` keeps `"approved": false` until Pratap approves.

## Constraints
- Content must not involve Oracle, Wipro, or any Wipro client — Pratap can't do Oracle-related side work.
- No API keys or secrets in the repo.
- Commit messages end with a `Co-Authored-By: Claude` line.
