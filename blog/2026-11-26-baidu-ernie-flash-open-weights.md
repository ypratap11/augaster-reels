---
title: "Baidu releases ERNIE 5.5 Flash Preview as a free open-weights model with a commercial license"
date: "2026-11-26"
slug: "baidu-ernie-flash-open-weights"
description: "Baidu has released the model weights for ERNIE 5.5 Flash Preview under the Apache License 2.0. The Apache 2.0 licence allows commercial use, modification and..."
tags: ["AI", "OpenSource", "ERNIE", "Baidu", "SmallBusiness", "Automation"]
series: "Augaster AI Digest"
video: "https://www.instagram.com/reel/DgOMJC8hQmm/"
---
**What happened.** Baidu has released the model weights for ERNIE 5.5 Flash Preview under the Apache License 2.0. The Apache 2.0 licence allows commercial use, modification and redistribution, and developers do not pay Baidu per interaction. The announcement came first: Baidu introduced the Preview through its cloud platform roughly two weeks before the open weights were published.

**How it works.** ERNIE 5.5 Flash Preview is a Mixture-of-Experts model with 280B total parameters and 14B active per token. Its context window is 1M tokens. Most of the weights are compressed to 4-bit precision, and the model uses speculative decoding with a DSpark draft head. It is text in, text out and cannot process images natively. As a demo, Baidu says the model wrote a third-person wuxia/martial-arts game on Unreal Engine 5.8 in a single 11-hour coding task. The model card describes the Preview as an intermediate checkpoint from post-training. Some capabilities may fall short because training is not finished, and an official release will follow.

Baidu also published benchmark results. On Terminal-Bench 4.0, ERNIE 5.5 Flash Preview scored 46.5, against 42.3 for DeepSeek-V4.1-Flash, 35.8 for GLM-5.3-Flash and 56.1 for GPT-6.1 Sol. On AutomationBench it scored 61.9, against 49.3 for GPT-6.1 Sol and 58.0 for Claude Opus 5.5. These are Baidu's own, manufacturer-reported evaluations.

**Availability and price.** Baidu's international API pricing is $0.28 per million input tokens and $1.13 per million output tokens. Decrypt links this figure to a third-party blog, and the Hugging Face model card gives no pricing. The model is also available through a free tier on OpenRouter.

**What it means for small businesses.** A commercial licence with no per-interaction fee to Baidu gives you another option to weigh against paid AI services. There are catches. This is a preview, so some capabilities may fall short. The benchmark scores come from Baidu itself rather than independent testers. And because the model handles text only, it won't help with tasks that depend on reading images.

**Our take.** Treat this as something to try, not something to bet on yet. Have a developer test it on one small, low-risk task and compare the result with the tools you already use before you build anything around it.

**Sources**
- Baidu ERNIE-5.5-Flash-Preview Hugging Face model card: https://huggingface.co/baidu/ERNIE-5.5-Flash-Preview
- Decrypt, Nov 25, 2026: https://decrypt.co/384015/china-google-released-fast-new-ai-model-free-baidu-ernie
- The Machine Herald, 2026-11-26: https://machineherald.io/article/2026-11/26-baidu-opens-ernie-55-flash-preview-weights-under-apache-20-as-benchmark-claims-remain-self-reported/
