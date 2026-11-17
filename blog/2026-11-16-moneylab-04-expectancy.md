---
title: "An 80% win rate can still lose money: why expectancy beats win rate"
date: "2026-11-16"
slug: "moneylab-04-expectancy"
description: "Two simple strategies each make 200 trades from a $10,000 start. Strategy A wins 80% of the time, gaining $100 on a win and losing $500 on a loss. Strategy B..."
tags: ["AugasterMoneyLab", "Trading", "RiskManagement", "Expectancy", "Investing", "PersonalFinance"]
series: "Augaster Money Lab"
video: "https://www.instagram.com/reel/Df03-zvHOYl/"
---
**The setup.** Two simple strategies each make 200 trades from a $10,000 start. Strategy A wins 80% of the time, gaining $100 on a win and losing $500 on a loss. Strategy B wins only 40% of the time, gaining $300 on a win and losing $100 on a loss.

**What happens.** In a typical simulated run, A drifts down to $6,000 while B climbs to $20,400. Across 20,000 simulated runs, A finished below $10,000 88% of the time. B finished below $10,000 in none of them.

**Why: expectancy.** Expectancy is the average result per trade: win rate × average win − loss rate × average loss. For A that is 0.8 × $100 − 0.2 × $500 = −$20 per trade. For B it is 0.4 × $300 − 0.6 × $100 = +$60 per trade. Over many trades, the average wins; the win rate only decides how it feels along the way.

**What it means for you.** A strategy that "almost always works" can hide rare, large losses that erase many small gains. Before trusting a strategy, check its average win, its average loss, and how often each happens, and size positions so one loss cannot wipe out weeks of wins.

**Our take.** Judge any repeated decision by its average outcome, not its hit rate. This is education, not financial advice.

**How we checked.** The numbers come from a simulation script you can run yourself: github.com/ypratap11/augaster-reels/blob/main/moneylab/ep04_expectancy.py
