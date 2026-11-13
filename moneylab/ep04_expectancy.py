#!/usr/bin/env python3
"""Money Lab Ep 4: an 80% win rate can still lose money. Every number in the reel comes from here."""
import json, random, statistics, sys

TRADES, START = 200, 10_000
A = dict(name="80% wins", p=0.80, win=100, loss=500)   # many small wins, rare big losses
B = dict(name="40% wins", p=0.40, win=300, loss=100)   # fewer wins, small losses

def expectancy(s): return s["p"] * s["win"] - (1 - s["p"]) * s["loss"]

def run(s, rng):
    eq, curve = START, [START]
    for _ in range(TRADES):
        eq += s["win"] if rng.random() < s["p"] else -s["loss"]
        curve.append(eq)
    return curve

# Monte Carlo: how often does each finish below the starting balance?
mc = {}
for s in (A, B):
    rng = random.Random(7)
    finals = [run(s, rng)[-1] for _ in range(20_000)]
    mc[s["name"]] = dict(expectancy=expectancy(s), mean_final=statistics.mean(finals),
                         p_loss=sum(f < START for f in finals) / len(finals))

# One illustrative run: first seed whose two finals are both within 20% of their expected P&L.
for seed in range(1, 5000):
    ca, cb = run(A, random.Random(seed)), run(B, random.Random(seed + 10_000))
    ea, eb = TRADES * expectancy(A), TRADES * expectancy(B)
    if abs((ca[-1] - START) - ea) <= 0.2 * abs(ea) and abs((cb[-1] - START) - eb) <= 0.2 * abs(eb):
        break
out = {"trades": TRADES, "start": START, "A": {**A, **mc[A["name"]], "final": ca[-1]},
       "B": {**B, **mc[B["name"]], "final": cb[-1]}, "seed": seed,
       "curve_A": ca[::4] + ([ca[-1]] if TRADES % 4 else []), "curve_B": cb[::4] + ([cb[-1]] if TRADES % 4 else [])}
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "ep04_results.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if not k.startswith("curve")}, indent=1))
