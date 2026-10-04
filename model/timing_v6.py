"""Time and activity of one attempt at each chosen setting (fresh path 29, 6,000 attempts): days in the evaluation,
days of funded life, trades per attempt, payouts per funded account. Writes timing_v6.json."""
import json, random
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, firms_v5 as F5

FIN = json.load(open("opt_v6_final.json"))

def one(c):
    F = F5.rules_for(c["prog"], c["size"], c.get("kind", "cfd"), c.get("fee"), c.get("override"))
    rng = random.Random(77)
    R = [PF.attempt(F, c["instr"], "synth29", c["m"], c["L"], c["k"], c["X1"], c["X"], rng) for _ in range(6000)]
    npass = len(F["phases"])
    fail = [r for r in R if r["passed"] < npass]; fund = [r for r in R if r["passed"] == npass]
    return dict(prog=c["prog"], instr=c["instr"], size=c["size"], n=len(R),
                t_eval_fail=float(np.mean([r["t_eval"] for r in fail])) if fail else None,
                t_eval_pass=float(np.mean([r["t_eval"] for r in fund])) if fund else None,
                t_fund=float(np.mean([r["t_fund"] for r in fund])) if fund else None,
                trades=float(np.mean([r["trades"] for r in R])),
                trades_fail=float(np.mean([r["trades"] for r in fail])) if fail else None,
                payouts=float(np.mean([r["npay"] for r in fund])) if fund else None,
                fail_p1=float(np.mean([r["passed"] == 0 for r in R])),
                days=float(np.mean([r["days"] for r in R])))

if __name__ == "__main__":
    C = [r for r in FIN if r["tag"] == "chosen" and r["data"] == "synth" and r["size"] in (100_000, 50_000)]
    with Pool(3) as p:
        R = p.map(one, C, chunksize=1)
    json.dump(R, open("timing_v6.json", "w"), indent=0)
    for r in R: print(r)
