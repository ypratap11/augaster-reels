# Augaster Money Lab 04: An 80% win rate can still lose money

## Instagram / YouTube Shorts caption

This strategy wins 80% of its trades. It still loses money. 📉

✅ Strategy A: wins 80%, +$100 per win, −$500 per loss → −$20 per trade on average
✅ Strategy B: wins 40%, +$300 per win, −$100 per loss → +$60 per trade on average
⚠️ In 20,000 simulated runs of 200 trades, A finished down 88% of the time

Our take: judge a strategy by its average trade (expectancy), not its win rate.

Education only, not financial advice. Simulation code and full breakdown: augaster.com (link in bio)

#AugasterMoneyLab #Trading #RiskManagement #Expectancy #Investing #PersonalFinance #LearnToTrade

---

## LinkedIn post

A strategy can win 80% of the time and still lose money.

I simulated two strategies over 200 trades, starting from $10,000:
• A wins 80% of trades, makes $100 per win, loses $500 per loss.
• B wins 40% of trades, makes $300 per win, loses $100 per loss.

A's average trade (expectancy) is 0.8 × $100 − 0.2 × $500 = −$20. B's is +$60. In one typical run, A drifts to $6,000 while B reaches $20,400. Across 20,000 simulated runs, A finished below its starting balance 88% of the time; B never did.

The lesson carries well beyond trading: a high hit rate means little if the occasional miss is five times bigger than the usual win.

Education only, not financial advice. The simulation code is public on GitHub (ypratap11/augaster-reels).

#RiskManagement #Trading #DecisionMaking

---

## Website article (augaster.com/digest)

### An 80% win rate can still lose money: why expectancy beats win rate

**The setup.** Two simple strategies each make 200 trades from a $10,000 start. Strategy A wins 80% of the time, gaining $100 on a win and losing $500 on a loss. Strategy B wins only 40% of the time, gaining $300 on a win and losing $100 on a loss.

**What happens.** In a typical simulated run, A drifts down to $6,000 while B climbs to $20,400. Across 20,000 simulated runs, A finished below $10,000 88% of the time. B finished below $10,000 in none of them.

**Why: expectancy.** Expectancy is the average result per trade: win rate × average win − loss rate × average loss. For A that is 0.8 × $100 − 0.2 × $500 = −$20 per trade. For B it is 0.4 × $300 − 0.6 × $100 = +$60 per trade. Over many trades, the average wins; the win rate only decides how it feels along the way.

**What it means for you.** A strategy that "almost always works" can hide rare, large losses that erase many small gains. Before trusting a strategy, check its average win, its average loss, and how often each happens, and size positions so one loss cannot wipe out weeks of wins.

**Our take.** Judge any repeated decision by its average outcome, not its hit rate. This is education, not financial advice.

**How we checked.** The numbers come from a simulation script you can run yourself: github.com/ypratap11/augaster-reels/blob/main/moneylab/ep04_expectancy.py
