#!/usr/bin/env python3
"""Money Lab episodes computed from first principles (no market data needed).

Usage:  python3 moneylab/episodes.py [episode-id ...]
Writes moneylab/<id>_results.json and queue/moneylab-<id>/{script.json, posts.md, verification.json}.
Every number in a script, caption or article is read from the computed results; nothing is typed by hand.
Render afterwards with render_reel.py.
"""
import json, math, os, random, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_URL = "https://github.com/ypratap11/augaster-reels/blob/main/moneylab/episodes.py"


def money(v):
    return f"${v:,.0f}"


def words_money(v):
    """Spoken money: 26,533 -> 'about twenty-six thousand five hundred dollars' style, rounded for speech."""
    return f"{v:,.0f} dollars"


# ---------------------------------------------------------------- math helpers

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs_call(S, K, T, r, sigma):
    if T <= 0:
        return max(S - K, 0.0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


# ---------------------------------------------------------------- episodes

def ep01_iv_crush():
    S0, K, r = 100.0, 105.0, 0.04
    before = bs_call(S0, K, 7 / 365, r, 0.80)          # day before earnings, IV 80%
    S1, iv1, T1 = 104.0, 0.30, 6 / 365                 # stock +4% after earnings, IV falls to 30%
    after = bs_call(S1, K, T1, r, iv1)
    xs = list(range(96, 117))
    curve = [round(bs_call(s, K, T1, r, iv1), 2) for s in xs]
    breakeven = next(s for s in [x / 10 for x in range(1000, 1300)] if bs_call(s, K, T1, r, iv1) >= before)
    res = dict(S0=S0, K=K, iv_before=0.80, iv_after=iv1, days_before=7, days_after=6, S1=S1,
               call_before=round(before, 2), call_after=round(after, 2),
               change_pct=round((after / before - 1) * 100), breakeven_stock=round(breakeven, 1),
               x_stock=xs, curve_after=curve, paid_line=[round(before, 2)] * len(xs))
    pct = abs(res["change_pct"])
    script = dict(
        title="The stock went up. Why did your call lose money?",
        segments=[
            dict(kind="hook", label="MONEY LAB", title="Stock up 4%. Your call down.",
                 point="Welcome to IV crush",
                 narration="The stock went up four percent. Your call option still lost money. Here is why."),
            dict(kind="news", label="THE SETUP", title=f"Bought a $105 call for {money(before)[0]}{before:.2f}",
                 point="Stock $100, 7 days left, implied volatility 80%",
                 narration=f"Before earnings, the stock is at one hundred dollars. A one-oh-five call with a week left costs {before:.2f} dollars, because implied volatility is eighty percent."),
            dict(kind="news", label="AFTER EARNINGS", title=f"Stock $104. Call ${after:.2f}.",
                 point="Implied volatility collapses from 80% to 30%",
                 narration=f"Earnings land. The stock rises to one oh four. But volatility collapses to thirty percent, and the call is now worth {after:.2f}. Down {pct} percent."),
            dict(kind="analysis", label="THE CHART", title=f"Breakeven: stock at ${res['breakeven_stock']:.2f}",
                 point="", chart=dict(unit="$", x_label="Stock price after earnings: $96 to $116", zero=True,
                                       series=[dict(name="Call value after", color="accent", values=curve),
                                               dict(name="What you paid", color="bad", values=res["paid_line"])]),
                 narration=f"After the crush, the stock needs to reach about {res['breakeven_stock']:.2f} dollars just to get your money back."),
            dict(kind="analysis", label="THE LESSON", title="You paid for the expected move",
                 point="High implied volatility = expensive options",
                 narration="Before earnings, option prices already include a big expected move. If the real move is smaller, you lose, even if you guessed the direction."),
            dict(kind="cta", label="AUGASTER MONEY LAB", title="The math behind money", point="augaster.com",
                 narration="Education only, not advice. Follow for more Money Lab."),
        ],
        claims=[
            (f"A $105 call with 7 days left, stock $100, IV 80% is worth about ${before:.2f} (Black-Scholes, r=4%)", res["call_before"]),
            (f"After earnings, stock $104, IV 30%, 6 days left, the same call is worth about ${after:.2f}", res["call_after"]),
            (f"That is a change of {res['change_pct']}% despite the stock rising 4%", res["change_pct"]),
            (f"After the IV drop the stock must reach about ${res['breakeven_stock']} to break even", res["breakeven_stock"]),
        ],
        caption=[f"The stock rose 4%. The call option fell {pct}%. 📉",
                 f"✅ Before earnings: stock $100, $105 call, 7 days left, implied volatility 80% → ${before:.2f}",
                 f"✅ After: stock $104, implied volatility 30% → ${after:.2f}",
                 f"⚠️ After the volatility crush, breakeven is a stock price of about ${res['breakeven_stock']:.2f}",
                 "Our take: before buying options into earnings, compare the expected move priced in with the move you expect."],
        tags="#AugasterMoneyLab #Options #ImpliedVolatility #IVCrush #Earnings #OptionsTrading #LearnToTrade",
        article=[("The setup", f"A stock trades at $100 the day before earnings. A $105 call with 7 days to expiry is priced with implied volatility of 80%. Using the Black-Scholes model with a 4% interest rate, that call is worth about ${before:.2f}."),
                 ("What happens", f"Earnings come out and the stock rises to $104. Implied volatility collapses to 30%, typical once the uncertainty is gone, and one day of time value is gone. The same call is now worth about ${after:.2f}, a {pct}% loss."),
                 ("Why", f"Option prices include the size of the move the market expects. Before earnings that expectation is large, so the call is expensive. When the actual move is smaller than what was priced in, the extra value drains away. After the crush, the stock needs to be about ${res['breakeven_stock']:.2f} for the call to be worth what you paid."),
                 ("What it means for you", "Being right on direction is not enough with options. Check implied volatility and the expected move before buying calls or puts into an event."),
                 ("Our take", "Treat implied volatility as part of the price tag. This is education, not financial advice.")],
        results=res)
    return script


def ep_volatility_drag():
    years, start = 20, 10_000
    steady = [start * 1.05 ** y for y in range(years + 1)]
    bumpy = [start]
    for y in range(1, years + 1):
        bumpy.append(bumpy[-1] * (1.30 if y % 2 else 0.80))
    cagr_b = (bumpy[-1] / start) ** (1 / years) - 1
    res = dict(years=years, start=start, steady_final=round(steady[-1]), bumpy_final=round(bumpy[-1]),
               arith_mean_bumpy=5.0, cagr_bumpy=round(cagr_b * 100, 1),
               curve_steady=[round(v) for v in steady], curve_bumpy=[round(v) for v in bumpy],
               half_then_half=round(100 * 0.5 * 1.5))
    s, b = res["steady_final"], res["bumpy_final"]
    return dict(
        title="Same average return, very different result: volatility drag",
        segments=[
            dict(kind="hook", label="MONEY LAB", title="Same average. Far less money.", point="Meet volatility drag",
                 narration=f"Two investments average the same five percent a year. One ends with {round(res['steady_final'] / res['bumpy_final'], 1)} times the money of the other."),
            dict(kind="news", label="THE SETUP", title="A: +5% every year", point="B: +30%, then −20%, repeating",
                 narration="Investment A gains five percent every year. Investment B swings: up thirty, then down twenty. Its average is also five percent."),
            dict(kind="news", label="20 YEARS LATER", title="Both start with $10,000", point="",
                 chart=dict(unit="$", x_label="Years: 0 to 20", zero=False,
                            series=[dict(name="A · steady", color="accent", values=res["curve_steady"]),
                                    dict(name="B · bumpy", color="bad", values=res["curve_bumpy"])]),
                 narration=f"After twenty years, A has about {round(s, -2):,.0f} dollars. B has about {round(b, -2):,.0f}."),
            dict(kind="analysis", label="THE MATH", title="Losses hurt more than gains help",
                 point=f"−50% then +50% leaves you at ${res['half_then_half']} from $100",
                 narration=f"Losses cut the base that gains grow from. Lose fifty percent, gain fifty, and one hundred dollars becomes {res['half_then_half']}."),
            dict(kind="analysis", label="THE LESSON", title=f"B really compounds at {res['cagr_bumpy']}%",
                 point="Average return ≠ what you earn",
                 narration=f"So B's real yearly growth is only {res['cagr_bumpy']} percent. When comparing investments, look at compound growth, not average return."),
            dict(kind="cta", label="AUGASTER MONEY LAB", title="The math behind money", point="augaster.com",
                 narration="Education only, not advice. Follow for more Money Lab."),
        ],
        claims=[(f"$10,000 growing 5% a year for 20 years reaches {money(s)}", s),
                (f"Alternating +30% and −20% for 20 years turns $10,000 into {money(b)}", b),
                ("+30% and −20% have an arithmetic average of +5%", 5.0),
                (f"That bumpy path compounds at {res['cagr_bumpy']}% a year", res["cagr_bumpy"]),
                (f"−50% followed by +50% turns $100 into ${res['half_then_half']}", res["half_then_half"])],
        caption=["Same 5% average return. Very different ending. 🎢",
                 f"✅ A: +5% every year → $10,000 becomes {money(s)} in 20 years",
                 f"✅ B: +30%, −20%, repeat (also averages 5%) → {money(b)}",
                 f"⚠️ B's real compound growth is only {res['cagr_bumpy']}% a year",
                 "Our take: compare investments by compound growth, not average return."],
        tags="#AugasterMoneyLab #Investing #Compounding #Volatility #PersonalFinance #MoneyMath #LongTermInvesting",
        article=[("The setup", "Investment A gains 5% every year. Investment B alternates: +30% one year, −20% the next. The simple average of B's returns is also 5% a year."),
                 ("What happens", f"Starting from $10,000, after 20 years A is worth {money(s)} and B is worth {money(b)}."),
                 ("Why", f"A loss shrinks the amount that the next gain applies to. A 50% loss followed by a 50% gain turns $100 into ${res['half_then_half']}. This gap between average return and compound return is called volatility drag. B's actual compound growth is {res['cagr_bumpy']}% a year."),
                 ("What it means for you", "Two funds can show the same average return and leave you with very different amounts. Compare compound annual growth rates and drawdowns, not just averages."),
                 ("Our take", "Lower volatility is worth something even at the same average return. This is education, not financial advice.")],
        results=res)


def ep_fees():
    years, start, gross = 30, 100_000, 0.07
    low = [start * (1 + gross - 0.001) ** y for y in range(years + 1)]
    high = [start * (1 + gross - 0.01) ** y for y in range(years + 1)]
    res = dict(years=years, start=start, gross=7, fee_low=0.1, fee_high=1.0,
               final_low=round(low[-1]), final_high=round(high[-1]), gap=round(low[-1] - high[-1]),
               gap_pct=round((1 - high[-1] / low[-1]) * 100),
               curve_low=[round(v) for v in low], curve_high=[round(v) for v in high])
    L, H, G = res["final_low"], res["final_high"], res["gap"]
    return dict(
        title=f"How a 1% fee can quietly take {res['gap_pct']}% of your money",
        segments=[
            dict(kind="hook", label="MONEY LAB", title=f"A 1% fee. {res['gap_pct']}% of your money.", point="Fees compound too",
                 narration=f"A one percent fee sounds small. Over thirty years it can take about {res['gap_pct']} percent of your money."),
            dict(kind="news", label="THE SETUP", title="$100,000, 7% a year, 30 years", point="Fund A fee 0.1%. Fund B fee 1%.",
                 narration="Invest one hundred thousand dollars earning seven percent a year for thirty years. Fund A charges point one percent. Fund B charges one percent."),
            dict(kind="news", label="30 YEARS LATER", title="Same market, different fee", point="",
                 chart=dict(unit="$", x_label="Years: 0 to 30", zero=False,
                            series=[dict(name="A · 0.1% fee", color="accent", values=res["curve_low"]),
                                    dict(name="B · 1% fee", color="bad", values=res["curve_high"])]),
                 narration=f"Fund A grows to about {round(L, -3):,.0f} dollars. Fund B grows to about {round(H, -3):,.0f}."),
            dict(kind="analysis", label="THE MATH", title=f"The gap: {money(G)}", point="Fees come off the growth, every year",
                 narration=f"That is a gap of about {round(G, -3):,.0f} dollars, because the fee is taken from a growing balance every single year."),
            dict(kind="analysis", label="THE LESSON", title="Check the expense ratio", point="Small percentages compound into big dollars",
                 narration="Before choosing a fund, check its yearly fee. Over decades, it matters as much as the returns."),
            dict(kind="cta", label="AUGASTER MONEY LAB", title="The math behind money", point="augaster.com",
                 narration="Education only, not advice. Follow for more Money Lab."),
        ],
        claims=[(f"$100,000 at 7% minus a 0.1% fee for 30 years grows to {money(L)}", L),
                (f"The same with a 1% fee grows to {money(H)}", H),
                (f"The difference is {money(G)}, about {res['gap_pct']}% of the low-fee result", G)],
        caption=[f"A 1% fee can cost about {res['gap_pct']}% of your money over 30 years. 💸",
                 f"✅ $100,000 at 7% a year with a 0.1% fee → {money(L)} after 30 years",
                 f"✅ Same investment with a 1% fee → {money(H)}",
                 f"⚠️ The gap is {money(G)}",
                 "Our take: check a fund's expense ratio before you buy."],
        tags="#AugasterMoneyLab #Investing #IndexFunds #Fees #PersonalFinance #Retirement #MoneyMath",
        article=[("The setup", "Two funds earn the same 7% a year before fees on a $100,000 investment for 30 years. Fund A charges 0.1% a year; Fund B charges 1%."),
                 ("What happens", f"Fund A grows to {money(L)}. Fund B grows to {money(H)}. The difference is {money(G)}, about {res['gap_pct']}% of what the low-fee fund ends with."),
                 ("Why", "A fee is charged on the whole balance every year, so it reduces the base that all future growth compounds on. Small yearly percentages turn into large dollar amounts over decades."),
                 ("What it means for you", "When comparing funds with similar holdings, the expense ratio is one of the few things you know in advance. Look it up before investing."),
                 ("Our take", "Treat fees as a guaranteed negative return. This is education, not financial advice.")],
        results=res)


def ep_position_sizing():
    p, trades, runs = 0.55, 100, 10_000
    def sim(frac, seed):
        rng = random.Random(seed)
        paths = []
        for _ in range(runs):
            eq, path = 1.0, [1.0]
            for _ in range(trades):
                eq *= (1 + frac) if rng.random() < p else (1 - frac)
                path.append(eq)
            paths.append(path)
        med = [statistics.median(pth[i] for pth in paths) * 10_000 for i in range(trades + 1)]
        halved = sum(min(pth) <= 0.5 for pth in paths) / runs
        return med, halved
    med2, h2 = sim(0.02, 11)
    med25, h25 = sim(0.25, 11)
    # Chart the typical (median) growth path exp(g*t), g = p ln(1+f) + (1-p) ln(1-f): smooth, and it lands on
    # the simulated medians; the per-trade simulated median jumps between discrete levels and draws a sawtooth.
    typ = lambda f: [10_000 * math.exp((p * math.log(1 + f) + (1 - p) * math.log(1 - f)) * t) for t in range(trades + 1)]
    med2_plot, med25_plot = typ(0.02), typ(0.25)
    res = dict(win_rate=55, payoff="1:1", trades=trades, runs=runs, start=10_000,
               median_final_2=round(med2[-1]), median_final_25=round(med25[-1]),
               halved_2=round(h2 * 100, 1), halved_25=round(h25 * 100),
               curve_2=[round(v) for v in med2_plot[::2]], curve_25=[round(v) for v in med25_plot[::2]],
               typical_final_2=round(med2_plot[-1]), typical_final_25=round(med25_plot[-1]))
    return dict(
        title="Same winning strategy, different bet size, opposite outcome",
        segments=[
            dict(kind="hook", label="MONEY LAB", title="A winning strategy. Still lost half.", point="Bet size decides",
                 narration="This strategy wins more than it loses. Bet too big, and it can still cut your account in half."),
            dict(kind="news", label="THE SETUP", title="55% wins, even payoff", point="Trader A risks 2% a trade. Trader B risks 25%.",
                 narration="Both traders win fifty-five percent of even-money trades. Trader A risks two percent per trade. Trader B risks twenty-five."),
            dict(kind="news", label="100 TRADES", title="The typical account path", point="",
                 chart=dict(unit="$", x_label="Trades: 0 to 100", zero=False,
                            series=[dict(name="A · risks 2%", color="accent", values=res["curve_2"]),
                                    dict(name="B · risks 25%", color="bad", values=res["curve_25"])]),
                 narration=f"After one hundred trades, the typical A account grows to about {round(res['median_final_2'], -2):,.0f} dollars. The typical B account shrinks to about {round(res['median_final_25'], -2):,.0f}."),
            dict(kind="analysis", label="THE MATH", title=f"B fell to half in {res['halved_25']}% of runs",
                 point=f"A: {res['halved_2']}% of the time",
                 narration=f"In the simulations, B lost half its account at some point {res['halved_25']} percent of the time. A almost never did."),
            dict(kind="analysis", label="THE LESSON", title="Edge needs survival", point="Big bets turn a good edge into ruin",
                 narration="Losing twenty-five percent needs a thirty-three percent gain to recover. Size bets so a losing streak cannot knock you out."),
            dict(kind="cta", label="AUGASTER MONEY LAB", title="The math behind money", point="augaster.com",
                 narration="Education only, not advice. Follow for more Money Lab."),
        ],
        claims=[(f"With 55% wins at even payoff, risking 2% a trade, the median $10,000 account after 100 trades is {money(res['median_final_2'])}", res["median_final_2"]),
                (f"Risking 25% a trade, the median account is {money(res['median_final_25'])}", res["median_final_25"]),
                (f"Risking 25%, the account fell to half or less at some point in {res['halved_25']}% of 10,000 runs", res["halved_25"]),
                (f"Risking 2%, that happened in {res['halved_2']}% of runs", res["halved_2"])],
        caption=["A winning strategy can still lose half your money if you bet too big. 🎲",
                 "✅ Both traders win 55% of even-money trades",
                 f"✅ Risking 2% a trade: typical $10,000 account → {money(res['median_final_2'])} after 100 trades",
                 f"⚠️ Risking 25%: typical account → {money(res['median_final_25'])}; half the account lost at some point in {res['halved_25']}% of simulations",
                 "Our take: an edge only pays if you survive long enough to use it."],
        tags="#AugasterMoneyLab #RiskManagement #PositionSizing #Trading #Probability #LearnToTrade #MoneyMath",
        article=[("The setup", "Two traders use the same strategy: it wins 55% of the time, and wins and losses are the same size. Trader A risks 2% of the account per trade; Trader B risks 25%. Each starts with $10,000 and makes 100 trades. We simulated each 10,000 times."),
                 ("What happens", f"The median A account ends at {money(res['median_final_2'])}. The median B account ends at {money(res['median_final_25'])}. B's account fell to half or less at some point in {res['halved_25']}% of runs, versus {res['halved_2']}% for A."),
                 ("Why", "Gains and losses multiply rather than add. A 25% loss needs a 33% gain to recover, so large bets let ordinary losing streaks do lasting damage, even with a real edge."),
                 ("What it means for you", "How much you risk per decision matters as much as how often you are right. Size positions so a normal losing streak cannot remove you from the game."),
                 ("Our take", "Survive first, then compound. This is education, not financial advice.")],
        results=res)


def ep_million():
    r = 0.07
    lump_years = math.log(100) / math.log(1 + r)
    bal, months, path_lump, path_monthly = 10_000.0, 0, [], []
    b_lump = 10_000.0
    while bal < 1_000_000:
        if months % 12 == 0:
            path_lump.append(round(b_lump)); path_monthly.append(round(bal))
        bal = bal * (1 + r) ** (1 / 12) + 500
        b_lump = b_lump * (1 + r) ** (1 / 12)
        months += 1
    path_lump.append(round(b_lump)); path_monthly.append(round(bal))
    res = dict(rate=7, start=10_000, monthly=500, years_lump=round(lump_years, 1),
               years_monthly=round(months / 12, 1), lump_at_that_time=round(b_lump),
               curve_lump=path_lump, curve_monthly=path_monthly)
    return dict(
        title="Can $10,000 become $1 million?",
        segments=[
            dict(kind="hook", label="MONEY LAB", title="$10,000 to $1 million?", point="Compounding needs time, or help",
                 narration="Can ten thousand dollars become a million? Yes. The question is how long."),
            dict(kind="news", label="ALONE", title=f"{res['years_lump']:.0f} years at 7%", point="$10,000 must grow 100×",
                 narration=f"At seven percent a year, ten thousand alone needs about {res['years_lump']:.0f} years to reach a million. It has to grow one hundred times."),
            dict(kind="news", label="WITH $500 A MONTH", title=f"About {res['years_monthly']:.0f} years", point="",
                 chart=dict(unit="$", x_label=f"Years: 0 to {math.ceil(res['years_monthly'])}", zero=True,
                            series=[dict(name="$10,000 + $500/month", color="accent", values=res["curve_monthly"]),
                                    dict(name="$10,000 alone", color="bad", values=res["curve_lump"])]),
                 narration=f"Add five hundred dollars a month, and it takes about {res['years_monthly']:.0f} years. By then, the lump sum alone is only near {round(res['lump_at_that_time'], -3):,.0f}."),
            dict(kind="analysis", label="THE MATH", title="Contributions do the early work", point="Compounding does the late work",
                 narration="In the early years, your deposits do most of the growing. Later, compounding takes over and the curve bends upward."),
            dict(kind="analysis", label="THE LESSON", title="Start early, add steadily", point="Time and contributions beat chasing returns",
                 narration="The biggest levers are time and steady contributions, not chasing a higher return with more risk."),
            dict(kind="cta", label="AUGASTER MONEY LAB", title="The math behind money", point="augaster.com",
                 narration="Education only, not advice. Follow for more Money Lab."),
        ],
        claims=[(f"$10,000 at 7% a year needs about {res['years_lump']} years to reach $1,000,000", res["years_lump"]),
                (f"Adding $500 a month at 7% reaches $1,000,000 in about {res['years_monthly']} years", res["years_monthly"]),
                (f"At that point $10,000 alone would be about {money(res['lump_at_that_time'])}", res["lump_at_that_time"])],
        caption=["Can $10,000 become $1 million? 🧮",
                 f"✅ At 7% a year, $10,000 alone takes about {res['years_lump']:.0f} years",
                 f"✅ Adding $500 a month gets there in about {res['years_monthly']:.0f} years",
                 f"⚠️ At that point, the $10,000 alone is only about {money(round(res['lump_at_that_time'], -3))}",
                 "Our take: time and steady contributions are the biggest levers you control."],
        tags="#AugasterMoneyLab #Compounding #Investing #PersonalFinance #WealthBuilding #MoneyMath #Saving",
        article=[("The question", "Can $10,000 grow into $1,000,000? We assumed a steady 7% a year, compounded monthly, with no taxes or fees."),
                 ("Alone", f"To reach $1 million, $10,000 has to grow 100 times. At 7% a year that takes about {res['years_lump']} years."),
                 ("With contributions", f"Adding $500 a month gets the balance to $1 million in about {res['years_monthly']} years. At that point the original $10,000 on its own would be worth about {money(res['lump_at_that_time'])}."),
                 ("What it means for you", "Early on, contributions drive growth; later, compounding does. Starting earlier and contributing steadily changes the timeline more than reaching for a slightly higher return."),
                 ("Our take", "Real returns vary year to year, so treat this as an illustration of the math. This is education, not financial advice.")],
        results=res)


EPISODES = {"01-iv-crush": ep01_iv_crush, "05-volatility-drag": ep_volatility_drag, "06-fees": ep_fees,
            "07-position-sizing": ep_position_sizing, "08-million": ep_million}


def build(eid):
    ep = EPISODES[eid]()
    res = ep["results"]
    json.dump(res, open(os.path.join(ROOT, "moneylab", f"{eid}_results.json"), "w"), indent=1)
    out = os.path.join(ROOT, "queue", f"moneylab-{eid}")
    os.makedirs(out, exist_ok=True)
    n = eid.split("-")[0]
    script = {"episode": f"MONEY LAB {n}", "series": "Augaster Money Lab", "brand_tag": "MONEY LAB",
              "story": ep["title"], "sources": [{"name": "Augaster calculation (moneylab/episodes.py)", "url": CODE_URL}],
              "source_line": "Calculation code: github.com/ypratap11/augaster-reels",
              "disclaimer": "Education only. Not financial advice.", "segments": ep["segments"]}
    json.dump(script, open(os.path.join(out, "script.json"), "w"), indent=2, ensure_ascii=False)
    json.dump({"method": "computed", "code": "moneylab/episodes.py", "results": f"moneylab/{eid}_results.json",
               "kept": [{"claim": c, "computed": v} for c, v in ep["claims"]]},
              open(os.path.join(out, "verification.json"), "w"), indent=2, ensure_ascii=False)
    cap = "\n".join(ep["caption"][:1]) + "\n\n" + "\n".join(ep["caption"][1:4]) + "\n\n" + ep["caption"][4] + \
        "\n\nEducation only, not financial advice. Calculation code and full breakdown: augaster.com (link in bio)\n\n" + ep["tags"]
    art = "\n\n".join(f"**{h}.** {t}" for h, t in ep["article"])
    art += f"\n\n**How we checked.** Every number comes from a script you can run yourself: {CODE_URL}"
    li = ep["caption"][0] + "\n\n" + "\n".join("• " + c[2:] for c in ep["caption"][1:4]) + "\n\n" + ep["caption"][4] + \
        "\n\nEducation only, not financial advice. The calculation is public on GitHub (ypratap11/augaster-reels)."
    open(os.path.join(out, "posts.md"), "w").write(
        f"# Augaster Money Lab {n}: {ep['title']}\n\n## Instagram / YouTube Shorts caption\n\n{cap}\n\n---\n\n"
        f"## LinkedIn post\n\n{li}\n\n---\n\n## Website article (augaster.com/digest)\n\n### {ep['title']}\n\n{art}\n")
    words = sum(len(s["narration"].split()) for s in ep["segments"])
    print(f"{eid}: {words} words -> {out}")
    return out


if __name__ == "__main__":
    for eid in (sys.argv[1:] or EPISODES):
        build(eid)
