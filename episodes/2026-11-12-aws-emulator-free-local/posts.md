# Augaster AI Digest — 12 Nov 2026: AWS releases free AWS Emulator, built entirely by AI agents, to run 200+ cloud services locally

## Instagram / YouTube Shorts caption

AWS just released a free copy of its cloud that runs offline on your own machine, and AI agents wrote all of the code. 🤖

✅ The AWS Emulator simulates more than 200 AWS services
✅ It's free and runs offline on your own machine
⚠️ It's a simulation, so real AWS is still the final check

Our take: ask your developer to try it on a test project first.

Full breakdown + sources: augaster.com (link in bio)

#AugasterAIDigest #AWS #AI #AIAgents #CloudComputing #SmallBusiness #Developers #OpenSource

---

## LinkedIn post

AWS has released a free AWS Emulator, and what stood out to me is how it was built: all of its code was written and tested by AI agents.

What happened:

- It simulates more than 200 AWS services
- It's free and runs offline on your own machine
- It's built from more than 400 public API models
- The code is released under CC0, a public-domain dedication

The project came from Matt Goldberg, a Senior Principal Engineer on the AWS Developer Tools team. The agents work from fidelity tests, which are customer scenarios checked against real AWS, and they build until the tests pass. Every change goes through a merge gate of automated checks, including multiple security agents doing adversarial reviews.

What it means for a small business

If you build or pay for cloud software, your developer may be able to test it locally without running up cloud usage. The catch is that it's a simulation, so I'd still verify anything important on real AWS.

My take: ask your developer to try it on a test project first.

Sources: RIO Rundown, All Things Distributed

#AI #AWS #SmallBusiness

---

## Website article (augaster.com/digest)

### AWS releases a free, AI-built emulator that runs 200+ cloud services locally

**What happened.** AWS has released the AWS Emulator, a local copy of more than 200 AWS services. All of its code was written and tested by AI agents. The idea and project came from Matt Goldberg, a Senior Principal Engineer on the AWS Developer Tools team.

**How it works.** The emulator is built from more than 400 public API models. The agents work from fidelity tests, which are customer scenarios devised from those models. The tests are checked against real AWS, and the emulator is built until it passes them. Human-defined guardrails apply: every change goes through a merge gate of automated checks, including multiple security agents doing adversarial reviews. The code is released under CC0, a Creative Commons public-domain dedication. The repository does not accept pull requests but takes bug reports through GitHub Issues. The full commit history and the agent-filed issues are public in the GitHub repo aws/aws-emulator.

**Availability and price.** The emulator is free and runs offline on your own machine.

**What it means for small businesses.** If your business relies on software built on AWS, your developer may be able to test it locally and offline instead of testing only in the cloud. The catch is that an emulator is a simulation of AWS, not AWS itself, so important behavior should still be verified on the real service.

**Our take.** This is a tool for your developer or agency, not something you need to install yourself. Ask them whether it fits your setup, and have them try it on a test project before relying on it.

**Sources**
- RIO Rundown (Substack) daily digest, Nov 12, 2026, Nov 12, 2026: https://riorundown.substack.com/p/ai-news-nov-12-2026-ai-agents-infrastructure
- All Things Distributed (Werner Vogels blog, guest post by Swami Sivasubramian), November 11, 2026: https://www.allthingsdistributed.com/2026/11/aws-emulator-and-the-engineers-job-when-agents-write-the-code.html
