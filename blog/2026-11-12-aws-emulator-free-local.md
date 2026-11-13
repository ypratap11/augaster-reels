---
title: "AWS releases a free, AI-built emulator that runs 200+ cloud services locally"
date: "2026-11-12"
slug: "aws-emulator-free-local"
description: "AWS has released the AWS Emulator, a local copy of more than 200 AWS services. All of its code was written and tested by AI agents. The idea and project came..."
tags: ["AWS", "AI", "AIAgents", "CloudComputing", "SmallBusiness", "Developers"]
series: "Augaster AI Digest"
---
**What happened.** AWS has released the AWS Emulator, a local copy of more than 200 AWS services. All of its code was written and tested by AI agents. The idea and project came from Matt Goldberg, a Senior Principal Engineer on the AWS Developer Tools team.

**How it works.** The emulator is built from more than 400 public API models. The agents work from fidelity tests, which are customer scenarios devised from those models. The tests are checked against real AWS, and the emulator is built until it passes them. Human-defined guardrails apply: every change goes through a merge gate of automated checks, including multiple security agents doing adversarial reviews. The code is released under CC0, a Creative Commons public-domain dedication. The repository does not accept pull requests but takes bug reports through GitHub Issues. The full commit history and the agent-filed issues are public in the GitHub repo aws/aws-emulator.

**Availability and price.** The emulator is free and runs offline on your own machine.

**What it means for small businesses.** If your business relies on software built on AWS, your developer may be able to test it locally and offline instead of testing only in the cloud. The catch is that an emulator is a simulation of AWS, not AWS itself, so important behavior should still be verified on the real service.

**Our take.** This is a tool for your developer or agency, not something you need to install yourself. Ask them whether it fits your setup, and have them try it on a test project before relying on it.

**Sources**
- RIO Rundown (Substack) daily digest, Nov 12, 2026, Nov 12, 2026: https://riorundown.substack.com/p/ai-news-nov-12-2026-ai-agents-infrastructure
- All Things Distributed (Werner Vogels blog, guest post by Swami Sivasubramian), November 11, 2026: https://www.allthingsdistributed.com/2026/11/aws-emulator-and-the-engineers-job-when-agents-write-the-code.html
