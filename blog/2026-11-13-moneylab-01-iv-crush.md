---
title: "The stock went up. Why did your call lose money?"
date: "2026-11-13"
slug: "moneylab-01-iv-crush"
description: "A stock trades at $100 the day before earnings. A $105 call with 7 days to expiry is priced with implied volatility of 80%. Using the Black-Scholes model wit..."
tags: ["AugasterMoneyLab", "Options", "ImpliedVolatility", "IVCrush", "Earnings", "OptionsTrading"]
series: "Augaster Money Lab"
video: "https://www.instagram.com/reel/DfsgLVXkqu7/"
---
**The setup.** A stock trades at $100 the day before earnings. A $105 call with 7 days to expiry is priced with implied volatility of 80%. Using the Black-Scholes model with a 4% interest rate, that call is worth about $2.48.

**What happens.** Earnings come out and the stock rises to $104. Implied volatility collapses to 30%, typical once the uncertainty is gone, and one day of time value is gone. The same call is now worth about $1.18, a 52% loss.

**Why.** Option prices include the size of the move the market expects. Before earnings that expectation is large, so the call is expensive. When the actual move is smaller than what was priced in, the extra value drains away. After the crush, the stock needs to be about $106.50 for the call to be worth what you paid.

**What it means for you.** Being right on direction is not enough with options. Check implied volatility and the expected move before buying calls or puts into an event.

**Our take.** Treat implied volatility as part of the price tag. This is education, not financial advice.

**How we checked.** Every number comes from a script you can run yourself: https://github.com/ypratap11/augaster-reels/blob/main/moneylab/episodes.py
