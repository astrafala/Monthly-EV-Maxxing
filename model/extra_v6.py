"""
Extra checks for the version 6 document:
  robust  - wider stops for the cost-sensitive EURUSD / USDJPY accounts, at cost x1, x1.5, x2 (fresh paths 29-32)
  zero    - zero-cost checks: FTMO phase 1 at the plan's bold setting (theory 50%) and The5ers High Stakes phase 1
            with and without its profitable-days rule (theory 50% without)
Writes extra_v6.json.
"""
import json, random, copy, math
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, firms_v5 as F5
from sens_v6 import run
from optimize_v6 import FINAL_PATHS

FIN = json.load(open("opt_v6_final.json"))

def nocost(instr, data):
    key = (instr, data + "_free")
    if key not in PF._DATA:
        M = dict(PF.market(instr, data)); M["fin"] = 0.0; M["cost"] = 0.0
        PF._DATA[key] = M
    return data + "_free"

def zero(a):
    name, prog, m, k, X, pdays, n = a
    F = copy.deepcopy(F5.cfd_firms()[prog]); F["phases"] = F["phases"][:1]
    if not pdays: F["phases"][0].pop("profit_days", None)
    F["phases"][0]["dll"] = None
    out = []
    for i, data in enumerate(FINAL_PATHS):
        rng = random.Random(900 + i); d = nocost("US100", data)
        out += [PF.attempt(F, "US100", d, m, 1500, k, X, X, rng)["passed"] >= 1 for _ in range(n)]
    P = float(np.mean(out))
    return dict(name=name, prog=prog, m=m, k=k, P=P, ci=1.96 * math.sqrt(P * (1 - P) / len(out)), n=len(out))

if __name__ == "__main__":
    ch = {(r["prog"], r["instr"], r["size"]): r for r in FIN if r["tag"] in ("chosen",) and r["data"] == "synth"}
    J = []
    fn = ch[("FundedNext Stellar 2-Step v5", "EURUSD", 100_000)]
    hp = ch[("Hola Prime 2-Step Prime (bi-weekly 80%)", "EURUSD", 100_000)]
    fp = ch[("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY", 100_000)]
    for c, ms in ((fn, (0.75, 1.0, 1.25)), (hp, (0.75, 1.0, 1.25)), (fp, (0.35, 0.5, 0.75))):
        for m in ms:
            for cm in (1.0, 1.5, 2.0):
                J.append(("robust", dict(c, m=m), cm, "random", 3000))
    with Pool(4) as p:
        R = p.map(run, J, chunksize=1)
        Z = p.map(zero, [("FTMO phase 1, bold setting", "FTMO 2-Step", 0.35, 30, 30000, False, 5000),
                         ("FTMO phase 1, k = 5", "FTMO 2-Step", 0.75, 5, 10000, False, 5000),
                         ("The5ers phase 1 with profitable days", "The5ers High Stakes", 0.6, 30, 30000, True, 5000),
                         ("The5ers phase 1 without profitable days", "The5ers High Stakes", 0.6, 30, 30000, False, 5000)])
    json.dump(dict(robust=R, zero=Z), open("extra_v6.json", "w"), indent=0)
    for r in R:
        print(f"{r['prog'][:34]:34s} {r['instr']} m={r['m']:.2f} k={r['k']} cost x{r['cost_mult']}: EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} P={r['P']:.3f}")
    for z in Z: print(z)
