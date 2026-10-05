"""
Version 8 stream manifest: every synthetic price path of every stage, as the random-stream key multi.load_synth seeds
numpy with (path number, market group(s), length in years, sub-steps per hour, correlation). Two paths share random
numbers only if their keys are equal. The script lists the keys of each stage, checks that stages meant to be
independent share none, and writes stream_manifest_v8.json (review of version 7, finding 14: version 7's offsets made
paths of different stages and markets collide).

Shared on purpose (paired designs, the same randomness is the point of the comparison):
  - the futures search uses the Nasdaq paths of the grid and refine stages (the micro future follows the Nasdaq index);
  - the budget, cost, news and behaviour scenarios run on the first 200 lives of the main portfolio stage;
  - the linearity check runs each firm alone on the first 200 lives of the 36-month stage.
"""
import json, math, itertools
import multi

def keys(seeds, markets, years, sub=60, rho=0.0, joint=False):
    out = []
    for sd in seeds:
        if joint: out.append(tuple(multi.stream_key(markets, rho, years, sub, sd)))
        else: out += [tuple(multi.stream_key([m], rho, years, sub, sd)) for m in markets]
    return out

CFD = ["US100", "USDJPY", "EURUSD", "XAUUSD"]
YL = math.ceil(36 / 12 + 1.5)
STAGES = {
    "grid (search)": keys(range(101, 105), CFD + ["MNQ_fut"], 12),
    "refine (search)": keys(range(111, 115), CFD + ["MNQ_fut"], 12),
    "final (validation)": keys(range(121, 137), CFD + ["MNQ_fut"], 12),
    "sensitivities": keys(range(141, 145), CFD, 12) + keys(range(461, 465), ["US100"], 4),
    "verification": (keys(range(401, 405), ["US100"], 4) + sum((keys(range(411, 417), ["US100"], 2, sub=s) for s in (12, 60, 240)), [])
                     + keys(range(6000, 6032), ["US100"], 2) + keys(range(6100, 6132), ["US100"], 2)
                     + keys(range(5000, 5024), CFD, 2) + keys([441], ["US100"], 12)),
    "rule tests": keys([901], ["US100", "USDJPY", "MNQ_fut"], 4),
    "portfolios, 12-month lives": keys(range(100_000, 101_200), CFD + ["MNQ_fut"], 2)
                                  + keys(range(100_000, 100_200), ["US100", "XAUUSD", "EURUSD", "USDJPY"], 2, rho=0.30, joint=True),
    "portfolios, 36-month lives": keys(range(300_000, 300_800), CFD + ["MNQ_fut"], YL),
}

def main():
    sets = {k: set(v) for k, v in STAGES.items()}
    clashes = []
    for a, b in itertools.combinations(sets, 2):
        common = sets[a] & sets[b]
        if common: clashes.append((a, b, len(common)))
    man = dict(key_format="(path number, number of markets + 1, market group..., years x 1000, sub-steps per hour, rho x 1e6)",
               groups=multi.MARKET_GROUP, stages={k: dict(streams=len(set(v)), first=list(v[0]), last=list(v[-1])) for k, v in STAGES.items()},
               clashes=clashes, shared_on_purpose=[
                   "Nasdaq CFD and micro Nasdaq future: one market group (one index path)",
                   "budget, cost, news and behaviour scenarios: lives 100,000-100,199 of the main stage (paired)",
                   "linearity check: lives 300,000-300,199 of the 36-month stage (paired)"])
    json.dump(man, open("stream_manifest_v8.json", "w"), indent=1)
    for k, v in sets.items(): print(f"{k:32s} {len(v):6d} streams")
    print("clashes between stages:", clashes or "none")
    return clashes

if __name__ == "__main__":
    assert not main(), "two stages share a random stream"
