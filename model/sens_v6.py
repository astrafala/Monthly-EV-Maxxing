"""
Sensitivities of the version 6 settings (fresh paths 29-32, 3,000 attempts per path unless stated):
  cost   - every chosen programme with trading costs x1.5 and x2 (spread, commission and slippage all worse)
  risk   - FTMO 2-Step at its chosen stop, k and cycle with risk per trade 1.0% ... 2.0%
  kcurve - FTMO 2-Step at m = 0.35, X = 30%: k from 1 to 50 (the bold-play curve)
  dir    - FTMO 2-Step chosen setting with the plan's direction rule (5-hour momentum) against a coin flip
  nofin  - FTMO 2-Step and FundingPips chosen settings with overnight financing switched off (what financing costs)
Writes sens_v6.json.
"""
import json, random, math, sys
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, firms_v5 as F5
from optimize_v6 import FINAL_PATHS

FIN = json.load(open("opt_v6_final.json"))

def nofin(instr, data):
    key = (instr, data + "_nofin")
    if key not in PF._DATA:
        M = dict(PF.market(instr, data)); M["fin"] = 0.0
        PF._DATA[key] = M
    return data + "_nofin"

def run(a):
    tag, c, cost_mult, rule, n = a
    F = F5.rules_for(c["prog"], c["size"], c.get("kind", "cfd"), c.get("fee"), c.get("override"))
    vs, ds, P = [], [], 0
    for i, data in enumerate(FINAL_PATHS):
        if tag == "nofin": data = nofin(c["instr"], data)
        rng = random.Random(500 + i)
        for _ in range(n):
            r = PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng, cost_mult=cost_mult, dir_rule=rule)
            vs.append(r["v"]); ds.append(r["days"]); P += r["passed"] == len(F["phases"])
    v = np.array(vs); d = np.array(ds); ratio = v.mean() / d.mean()
    ci = 1.96 * (v - ratio * d).std() / math.sqrt(len(v)) / d.mean() * 30.44
    return dict(tag=tag, prog=c["prog"], instr=c["instr"], size=c["size"], m=c["m"], k=c["k"], X=c["X"], L=c["L"],
                cost_mult=cost_mult, rule=rule, EV=float(v.mean()), days=float(d.mean()), EV_month=float(ratio * 30.44),
                CI=float(ci), P=P / len(v))

if __name__ == "__main__" and len(sys.argv) == 1:
    chosen = [r for r in FIN if r["tag"] == "chosen" and r["data"] == "synth" and r.get("kind", "cfd") == "cfd"]
    J = []
    for c in chosen:
        for cm in (1.5, 2.0): J.append(("cost", c, cm, "random", 3000))
    ftmo = [c for c in chosen if c["prog"] == "FTMO 2-Step"][0]
    for lf in (0.010, 0.0125, 0.015, 0.0175, 0.020):
        J.append(("risk", dict(ftmo, L=lf * 100_000), 1.0, "random", 3000))
    for k in (1, 2, 3, 5, 8, 12, 20, 30, 50):
        J.append(("kcurve", dict(ftmo, k=k, m=0.35, X=30_000, X1=30_000), 1.0, "random", 3000))
    for rule in ("trend5", "random"):
        J.append(("dir", ftmo, 1.0, rule, 6000))
    fp = [c for c in chosen if c["prog"] == "FundingPips 2-Step Flex (85%) v6 cap"][0]
    for c in (ftmo, fp):
        J.append(("nofin", c, 1.0, "random", 6000)); J.append(("fin", c, 1.0, "random", 6000))
    with Pool(4) as p:
        R = p.map(run, J, chunksize=1)
    json.dump(R, open("sens_v6.json", "w"), indent=0)
    for r in R:
        print(f"{r['tag']:7s} {r['prog'][:34]:34s} {r['instr']:7s} k={r['k']:>2} m={r['m']:.2f} L={r['L']:.0f} cost x{r['cost_mult']} {r['rule']:7s} "
              f"EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} EV={r['EV']:6.0f} P={r['P']:.3f} days={r['days']:.1f}")

# cost x1 on the same seeds as the x1.5 / x2 rows, so the three columns of the cost table are paired
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "cost1":
    old = json.load(open("sens_v6.json"))
    done = {(r["prog"], r["instr"], r["m"]) for r in old if r["tag"] == "cost"}
    chosen = [r for r in FIN if r["tag"] in ("chosen", "refine best") and r["data"] == "synth" and r.get("kind", "cfd") == "cfd" and r["size"] == 100_000]
    J = [("cost", c, 1.0, "random", 3000) for c in chosen if (c["prog"], c["instr"], c["m"]) in done]
    with Pool(4) as p:
        R = p.map(run, J, chunksize=1)
    json.dump(old + R, open("sens_v6.json", "w"), indent=0)
    for r in R: print(f"{r['prog'][:34]:34s} {r['instr']:7s} m={r['m']:.2f} cost x1: EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f}")
