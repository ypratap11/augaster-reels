# Upwork / Fiverr offer — AI short-video packages (Augaster Technologies)

## Profile headline
AI Short-Form Video for Small Businesses | Branded Reels & Shorts from Your News, Tips or Blog

## Profile overview
I run Augaster Technologies, a small AI product studio. We turn your updates, tips, blog posts or industry news into ready-to-post vertical videos for Instagram Reels, YouTube Shorts, TikTok and LinkedIn.

Every video is:
• Scripted for a 30–35 second watch, with a strong first 3 seconds
• Narrated (natural AI voice, or your own recording)
• Captioned word-by-word for silent viewing
• In your brand colors, with your logo
• Fact-checked against the sources you give us
• Delivered as 1080×1920 MP4 plus caption text and hashtags

You approve every script before we render. Typical turnaround is 2 business days.

Good fit for: local service businesses, consultants, coaches, real estate agents, SaaS startups and anyone with a blog or newsletter who wants to be on short video without filming.

## Project catalog offer
**Title:** I will turn your content into 4 branded, narrated short videos

| Package | Starter | Standard | Monthly |
|---|---|---|---|
| Price | $79 | $149 | $399/month |
| Videos | 2 | 4 | 12 (3 per week) |
| Length | up to 35 sec | up to 35 sec | up to 35 sec |
| Script writing | ✓ | ✓ | ✓ |
| AI voiceover | ✓ | ✓ | ✓ |
| Burned-in captions | ✓ | ✓ | ✓ |
| Brand colors + logo | ✓ | ✓ | ✓ |
| Post captions + hashtags | — | ✓ | ✓ |
| LinkedIn post + blog version | — | — | ✓ |
| Revisions | 1 | 2 | 2 per video |
| Delivery | 3 days | 4 days | weekly |

**What I need from you:** links or text for each topic (blog post, product update, tip), your logo, brand colors, and website/CTA.

## Sample-portfolio items
1. Augaster AI Digest: "Apple Intelligence Usage Packs" (34-sec narrated news reel, Augaster brand)
2. Client-brand demo: "Crumb & Kettle" holiday pie pre-orders (fictional bakery, its own colors + logo). `samples/crumb-and-kettle/`. It shows a buyer that the output is in *their* brand, not ours. Label it as a demo.
3. Add 2–3 more Digest reels as they're published

## Making a client's reels
1. Create `clients/<name>/brand.json` (see `samples/crumb-and-kettle/brand.json`): name, tagline, colors, logo path, CTA footer.
2. Write `script.json` in the episode schema (six segments, ~80 words of narration; spell out numbers in `narration`).
3. `python3 render_reel.py clients/<name>/<video>/script.json --voice voices/en-us-lessac-medium.onnx --brand clients/<name>/brand.json`
4. Send the script for approval *before* rendering; send the MP4 + caption text after.

## Fastest path to a first paid order
- Offer one free 30-sec test video in proposals (already in the template). Render it in their brand from their own website or Google Business posts. A buyer seeing their own logo moving is the strongest close.
- Target job posts for "Reels", "YouTube Shorts", "TikTok videos for my business", "faceless video". Skip any Oracle or Wipro-client work.

## Proposal template (for job posts)
Hi [Name],

I can make these for you. I build branded, narrated 30-second reels from your existing content, and you approve each script before I render. Here's a recent sample: [link].

For [their business], I'd start with [2–3 specific topic ideas from their post or website].

I can deliver the first [N] videos in [X] days. Happy to do one short test video first so you can check the style.

Pratap
Augaster Technologies
