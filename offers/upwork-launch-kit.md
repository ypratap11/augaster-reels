# Upwork launch kit (Nov 20, 2026) — drafts for Pratap's approval

Nothing here has been posted or sent. Pratap reviews, edits and submits each item himself.

## 0. Blocker: Connects
The account has **0 Connects**. Each proposal below costs 8–16 Connects (the MCP job shows 16).
Buy a small pack (enough for 5–6 proposals) in Upwork → Find work → Connects. Check the
current price on that page before buying.

## 1. Profile

**Title**
AI Agent Engineer | Claude & MCP Integrations, Document Automation, AI Video

**Hourly rate:** $75/hr (fixed-price projects below are the main offer)

**Overview**
I build AI agents that do real work inside a business: connecting Claude or ChatGPT to your CRM, accounting or ad accounts, turning invoices and checks into clean data, and producing branded short videos automatically.

What I've shipped:
• JiraIQ: an MCP server that gives Claude Desktop live access to Jira, with delivery-risk scoring (github.com/ypratap11/jiraiq-mcp)
• Augaster AI Digest: a fully automated pipeline that finds AI news, checks every claim against two sources with the Claude API, renders a narrated video and posts it to Instagram behind a safety gate, three times a day (github.com/ypratap11/augaster-reels)
• FinLedger: Stripe webhooks into a double-entry ledger with ASC 606 revenue schedules, reconciled to the source (github.com/ypratap11/finledger)
• Rhapto and Dokimo: AI products built so every output can be traced to its source (augaster.com)

How I work:
• Safe by default: read-only first, mocks and sample data for development, reversible writes, logs you can audit
• Fixed scope and a written plan before I build; you approve each milestone
• Plain-English handover docs, and all accounts and keys stay in your name

Background: 20+ years in finance systems and program delivery, now focused on practical AI. Bay Area, US.

**Skills (pick 15):** Model Context Protocol (MCP), MCP servers, Claude API, AI Agent Development, LLM API Integration, Python, API Integration, OAuth, Automation, QuickBooks Online API, Stripe API, Data Extraction, OCR, Google Ads API, n8n

**Portfolio items**
1. JiraIQ MCP server — screenshot of Claude answering a Jira question + repo link
2. Augaster AI Digest pipeline — one reel + architecture diagram (story picker → two-source check → render → safety gate → Instagram)
3. FinLedger — ledger output + reconciliation report
4. Crumb & Kettle demo — client-branded reel (samples/crumb-and-kettle), labelled as a demo

## 2. Project catalog (three listings)
1. **I will build a custom MCP server that connects Claude to your system** — $1,200 intro (first 3 clients), then $1,800 · 2–3 weeks · one API or SaaS tool, auth, up to 6 tools, logging, tests, README
2. **I will build AI document extraction for invoices, receipts or checks** — $1,500 · 2–3 weeks · to CSV/database, confidence scores, review screen
3. **I will turn your content into 4 branded, narrated short videos** — $79 / $149 / $399 per month (see upwork-short-video-offer.md)

## 3. Proposals for live job posts (found Nov 20)

Ranked by fit and competition. Send in this order.

---
### A. Claude AI agent system for a children's puzzle digital-products business
https://www.upwork.com/jobs/~022123764757127750086 · Hourly $25–48 · posted 1 hour ago when found (early, few proposals)

Hi Alicja,

I read your blueprint idea: eight agents, a Google Sheets/Drive data layer, and Etsy, beehiiv, Buffer, Meta Ads and Gemini images. You asked to be challenged on it, so here's my honest take: I'd start with three agents, not eight.

1. Product maker: turns a book chapter into a puzzle/maze bundle, with your approval before anything is listed.
2. Listing and launch: writes the Etsy listing and the beehiiv email from the same product record.
3. Weekly social: drafts a week of posts for Buffer from the product tracker.

One shared Google Sheet as the product tracker covers what most of the other agents would do. That's fewer subscriptions and fewer things to break. The Meta Ads and analytics agents can wait until you have sales data worth acting on.

I build this way already: my own AI Digest runs Claude agents on a schedule that research, write, render videos and post to Instagram, with a check step that stops anything I haven't approved (github.com/ypratap11/augaster-reels).

Deliverables as you listed: working agents, documentation per agent, a recorded walkthrough, 30 days of support, everything in your accounts.

Could you share the Master Product Tracker output that failed? I'll tell you why it failed before we start.

Pratap

---
### B. AI agent engineer: consult on and build a Claude MCP data pipeline (CRE brokerage)
https://www.upwork.com/jobs/~022123404877281550791 · Hourly $40–80 · 50+ proposals, 20 interviewing (competitive; answer every question)

Hi,

The most similar thing I've built is JiraIQ, an MCP server that gives Claude live access to a company's Jira, plus an automated pipeline where several Claude calls research, fact-check and publish content on a schedule. Your four questions:

**1. Safe, auditable, reversible CRM writes.** Agents never write directly. Every write goes through one MCP tool that (a) validates against your business rules, (b) logs the before-and-after record with the agent's reasoning, and (c) writes to a "proposed changes" queue. High-confidence, low-risk changes apply automatically; the rest wait for you. Reversal is replaying the logged "before" record.

**2. What broke after launch.** In my publishing pipeline, Instagram's byte upload started failing intermittently; I added a fallback where Meta fetches the file by URL, and a gate that refuses to publish anything unverified. Separately, a background job that was reported killed kept running and overwrote an approved output; now every test runs on a copy, never the live folder.

**3. Reducing LLM cost.** Route simple steps to a smaller model, cache stable instructions, stop agents re-reading the same records (fetch once, pass IDs), and cap tool calls per run. I'd measure cost per run first so we fix the real driver.

**4. Building without live access.** A mock CRM that replays recorded, anonymised responses, contract tests on the MCP tools, and a dry-run mode that prints the writes it would make. You run the PR against live.

First milestone as you described: review, written top improvements, implement the first. NDA fine.

Pratap

---
### C. Connect Google Ads, Merchant Center and GA4 to Claude (Google's official MCP servers, read-only)
https://www.upwork.com/jobs/~022123114367255861918 · Fixed $500 · 50+ proposals

Hi,

I can set this up as specified: Google's official Google Ads MCP, Merchant API access and the Analytics MCP, all authenticating with your dedicated read-only Google account, connected to Claude and tested with a real query on each.

How I'll keep it read-only: least-privilege roles on the read-only user, read-only OAuth scopes where Google offers them, and no write tools exposed in the MCP config. I'll show you a failed write attempt as proof.

One thing to plan for: the Google Ads API developer token needs Google's approval, which can take a few days. I'll file it on day one with you so it doesn't hold up the rest.

Handover: a short doc covering what's installed, where each credential lives, and how to revoke or reconnect.

I've built MCP servers for Claude before (github.com/ypratap11/jiraiq-mcp).

Pratap

---
### D. Claude AI + QuickBooks Online for ~90 clients, with check OCR
https://www.upwork.com/jobs/~022122865978145096745 · Fixed · 50+ proposals

Hi,

The hard part of this job is your point 2, strict client isolation, so here's how I'd do it: one OAuth token and one rules file per Realm ID, stored separately, and an MCP server where every tool call must name the client and can only load that client's chart of accounts, vendors and history. A test suite tries cross-client reads on purpose and must fail.

For bank-feed categorisation: suggest a category with a confidence score; anything below your threshold goes to a review list instead of being posted.

For checks: extract payee, amount, date and check number from the image, then match against the bank feed before anything is entered. Mismatches go to review.

I'd start with a pilot on 3 clients, measure accuracy against your bookkeepers' choices, then roll out.

Background: 20+ years in finance systems (GL/AP/AR), and I built FinLedger, a Stripe-to-ledger reconciliation engine (github.com/ypratap11/finledger).

Pratap

---
### E. MCP server and cloud architecture for an AI content creation tool (real estate, pilot MVP)
https://www.upwork.com/jobs/~022123030380504670662 · Hourly · 50+ proposals

Hi,

Your design (creators work inside Claude, your backend behind a remote MCP server, instructions served by the server) is the right call for a pilot. It skips a frontend and lets you change workflows without users reinstalling anything.

For the pilot I'd build: a remote MCP server with OAuth and creator/admin roles; server-side instructions loaded per session; per-user logs of every tool call (inputs, outputs, files) in Postgres plus object storage; property and room data as structured records; and your rendering behind one tool call.

The logs are what make your "turn usage into templates" goal possible, so I'd design them for that from day one.

I've built an MCP server for Claude (github.com/ypratap11/jiraiq-mcp) and an automated video rendering pipeline (github.com/ypratap11/augaster-reels).

Happy to sketch the architecture on a call.

Pratap

## 4. Skipped
- YouTube Shorts growth specialist (B2B automation channel): good topic match, but we don't yet have a track record of channel growth to show. Revisit once our own Shorts have numbers.
- Sales-only or commission roles, recruiter posts, and anything Oracle/Wipro.
