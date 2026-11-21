---
title: "Inkling 2 Mini: A free, open-weights AI model that runs on a laptop"
date: "2026-11-21"
slug: "inkling-2-mini-laptop-model"
description: "Thinking Machines Lab, the startup founded by former OpenAI CTO Mira Murati, announced and released Inkling 2 Mini on November 20, 2026. It is an open-weight..."
tags: ["AI", "OpenSourceAI", "LocalAI", "SmallBusiness", "Ollama", "GenerativeAI"]
series: "Augaster AI Digest"
---
**What happened.** Thinking Machines Lab, the startup founded by former OpenAI CTO Mira Murati, announced and released Inkling 2 Mini on November 20, 2026. It is an open-weights model small enough to run on consumer laptops and desktop AI computers. The lab showed it off with an offline demo. Researchers flew with the model, and on a MacBook Pro (M5 Pro, 48GB) in airplane mode it built a playable flight simulator in a few minutes. In a second demo, one offline MacBook ran all 20 villagers of a pixel town the model had built.

**How it works.** Inkling 2 Mini is a looped transformer. It runs the middle layers of the model three times for every token, so it can reason more while writing fewer tokens. It is a Mixture-of-Experts model with 26.4B total parameters and 3.4B active parameters. Counting the loops, it uses 5.4B weight activations per token. Most weights were trained and deployed natively in 4-bit NVFP4, with the last four layers in 8-bit MXFP8, so there is no conversion loss from quantization. Two-thirds of the experts were pruned during training, from 384 down to 128, and the model was then trained on 1T tokens distilled from a larger internal Inkling model. The total memory footprint is about 20GB. Press coverage also reports a 1M-token context window.

Thinking Machines reports that Inkling 2 Mini leads every open-weights model with fewer than 100B total parameters on benchmarks such as DeepSWE v1.1, where it scores 48.2% against 42.2% for Alibaba's Qwen3.8-27B. It also scores 77.9% on SWE-bench Pro v2 Hard and 79.2% on SWE-bench Verified. On the Artificial Analysis Intelligence Index (v5.0) it scores 20.1, tying Qwen3.8-27B. Artificial Analysis, a third-party tester, reportedly found it about six times cheaper and four times faster per task than Qwen3.8-27B: $0.59 and 9 minutes per task, against $3.53 and 38.2 minutes.

**Availability and price.** Full weights are published openly on Hugging Face. Press coverage says the model is released under the Apache 2.0 license, paired with a Model Acceptable Use Policy. At launch it is supported on any Mac (MacBook, Mac Mini) with at least 32GB RAM via Ollama, and it also runs on NVIDIA DGX Spark. Quantized GGUF versions are available via Unsloth and llama.cpp for local inference.

**What it means for small businesses.** A capable model that runs on hardware you already own opens up a few options. You could keep sensitive documents on your own machine, and you would not depend on one vendor's pricing. There are limits, though. Inkling 2 Mini is not the strongest small model for multi-turn chat or instructions with many constraints. It scores 50.0% on MultiChallenge and 33.4% on ComplexConstraints v1.1, behind Qwen3.8-27B on both. It also trails larger models on hard reasoning tests, and looping does not let the weights store more facts. It may suit internal work better than customer-facing chat.

**Our take.** Treat this as a low-risk experiment. If you have a Mac with enough memory, pick one internal task, such as drafting or code help, and run it locally. Compare the results and the effort against the tools you use today. Check the license and usage policy before you build anything into your business. Do not rely on it for customer-facing conversations until you have tested it properly.

**Sources**
- Thinking Machines Lab announcement (Introducing Inkling 2 Mini), Nov 20, 2026: https://thinkingmachines.ai/news/inkling-2-mini/
- The Next Web (Ana Maria Constantin), November 21, 2026 - 3:49 pm GMT: https://thenextweb.com/news/inkling-2-mini-thinking-machines-looped-open-weights-laptop
- VentureBeat (Carl Franzen), 10:29 am, PT, November 21, 2026: https://venturebeat.com/technology/thinking-machines-wows-with-inkling-2-mini-looped-transformer-model-that-runs-locally-on-laptops
