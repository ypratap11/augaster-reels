# Augaster Money Lab 01: The stock went up. Why did your call lose money?

## Instagram / YouTube Shorts caption

The stock rose 4%. The call option fell 52%. 📉

✅ Before earnings: stock $100, $105 call, 7 days left, implied volatility 80% → $2.48
✅ After: stock $104, implied volatility 30% → $1.18
⚠️ After the volatility crush, breakeven is a stock price of about $106.50

Our take: before buying options into earnings, compare the expected move priced in with the move you expect.

Education only, not financial advice. Calculation code and full breakdown: augaster.com (link in bio)

#AugasterMoneyLab #Options #ImpliedVolatility #IVCrush #Earnings #OptionsTrading #LearnToTrade

---

## LinkedIn post

The stock rose 4%. The call option fell 52%. 📉

• Before earnings: stock $100, $105 call, 7 days left, implied volatility 80% → $2.48
• After: stock $104, implied volatility 30% → $1.18
•  After the volatility crush, breakeven is a stock price of about $106.50

Our take: before buying options into earnings, compare the expected move priced in with the move you expect.

Education only, not financial advice. The calculation is public on GitHub (ypratap11/augaster-reels).

---

## Website article (augaster.com/digest)

### The stock went up. Why did your call lose money?

**The setup.** A stock trades at $100 the day before earnings. A $105 call with 7 days to expiry is priced with implied volatility of 80%. Using the Black-Scholes model with a 4% interest rate, that call is worth about $2.48.

**What happens.** Earnings come out and the stock rises to $104. Implied volatility collapses to 30%, typical once the uncertainty is gone, and one day of time value is gone. The same call is now worth about $1.18, a 52% loss.

**Why.** Option prices include the size of the move the market expects. Before earnings that expectation is large, so the call is expensive. When the actual move is smaller than what was priced in, the extra value drains away. After the crush, the stock needs to be about $106.50 for the call to be worth what you paid.

**What it means for you.** Being right on direction is not enough with options. Check implied volatility and the expected move before buying calls or puts into an event.

**Our take.** Treat implied volatility as part of the price tag. This is education, not financial advice.

**How we checked.** Every number comes from a script you can run yourself: https://github.com/ypratap11/augaster-reels/blob/main/moneylab/episodes.py
