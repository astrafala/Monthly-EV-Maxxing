"""
Version 10 check of the continuing-slot rates against the random-start ratios, with matched estimands.

continuing_v10.py measures each chosen setting as a slot run back to back with the plan's 5-hour momentum direction rule
on paths 1151-1166 (the average over the 16 paths of each path's cash per month in years 2-9); the final stage measures it as
a random-start ratio of totals with a coin-flip direction on other paths. This check runs, on the continuing stage's own
paths, 1,500 random-start attempts per path for every chosen setting, once with the momentum rule and once with a coin
flip, and compares:
  - the measurement: continuing rate minus the random-start ratio (momentum rule, same paths);
  - the direction rule: the random-start ratio with the momentum rule minus the one with a coin flip (same paths).
Each compared quantity is the estimator the document reports (version 10: version 9 compared averages of per-path ratios
while reporting ratios of totals, so its centres were not the differences of the displayed rates and in one case had the
other sign; review of version 9, finding 23): the random-start rate is 30.44 x sum(V)/sum(D) over all paths, the
continuing rate the mean of the per-path rates. Intervals: paired over paths, from each path's contribution to the
difference of the two estimators (delta method: a ratio of totals R = 30.44 sum V / sum D moves by
30.44 (V_c - (R/30.44) D_c) / sum D for path c; the mean of per-path rates by (r_c - mean)/G), Student t with 15 degrees of
freedom.
What the comparison can and cannot show (version 10, review of version 9, finding 24): with zero-edge prices every
trade's gross result has mean zero under either direction rule, but that does not make the two rules' account outcomes,
durations or rates per month equal (a long and a short with the same stop and target have the same win chance on a
driftless price and different expected durations); the differences below are measured quantities with their
uncertainty, not theoretical equalities, and failing to reject zero is not a proof of equality. Writes
cont_check_v10.json.
"""
import json, math, random
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, optimize_v10 as O, continuing_v10 as CV

N = 1500
RULES = {"trend5": 9100, "random": 9200}       # seeds: per rule, plus the path's index

def job(a):
    c, i, rule = a
    F = O.firm_rules(c)
    rng = random.Random(RULES[rule] + i); s0 = PF.A.STUCK[0]
    R = [PF.attempt(F, c["instr"], CV.PATHS[i], c["m"], c["L"], c["k"], c["X1"], c["X"], rng, dir_rule=rule) for _ in range(N)]
    cbar = float(np.mean([r.get("credit", 0.0) for r in R]))
    v = [r["v"] - ((1.0 - F["funded"].get("fee_pct", 0.0)) * F.get("refund_frac", 1.0) * cbar * (r["npay"] >= 1) if F.get("credit_frac") and F["funded"].get("refund") else 0.0)
         for r in R]                                          # The5ers: the refund the credit costs (optimize_v10)
    return float(sum(v)), float(sum(r["days"] for r in R)), int(PF.A.STUCK[0] - s0)

def ratio(V, D):
    return 30.44 * V.sum() / D.sum()

def infl_ratio(V, D):
    """each path's contribution to a ratio of totals (delta method)"""
    R = V.sum() / D.sum()
    return 30.44 * (V - R * D) / D.sum()

def infl_mean(r):
    return (r - r.mean()) / len(r)

def paired(e):
    """interval half-width of a difference whose per-path contributions are e (they sum to zero)"""
    G = len(e)
    return float(O.tq(G - 1) * math.sqrt(G / (G - 1) * np.sum(e ** 2)))

if __name__ == "__main__":
    CONT = json.load(open("continuing_v10.json"))["rows"]
    keys = CV.KEYS
    rows = [r for r in CONT if r["tag"] == "chosen"]
    C = [{k: r[k] for k in keys if k in r} for r in rows]
    K = [(i, rule, ci) for i in range(len(CV.PATHS)) for rule in RULES for ci in range(len(C))]   # path-major
    with Pool(4) as p:
        R = p.map(job, [(C[ci], i, rule) for i, rule, ci in K], chunksize=1)
    res = dict(zip(K, R))
    out = []; agree_m = 0; agree_r = 0
    for ci, (c, cr) in enumerate(zip(C, rows)):
        o = dict(c, continuing=cr["rate"], continuing_CI=cr["CI"], random_start_final=cr["random_start"],
                 random_start_final_CI=cr["random_start_CI"])
        VD = {}
        for rule in RULES:
            V = np.array([res[(i, rule, ci)][0] for i in range(len(CV.PATHS))]); D = np.array([res[(i, rule, ci)][1] for i in range(len(CV.PATHS))])
            VD[rule] = (V, D)
            o[rule] = float(ratio(V, D)); o[rule + "_CI"] = paired(infl_ratio(V, D))
            o[rule + "_V"] = V.tolist(); o[rule + "_D"] = D.tolist()
        rc = np.array(cr["per_path"])
        e_m = infl_mean(rc) - infl_ratio(*VD["trend5"])
        e_r = infl_ratio(*VD["trend5"]) - infl_ratio(*VD["random"])
        o["method_diff"] = float(rc.mean() - o["trend5"]); o["method_diff_CI"] = paired(e_m)
        o["rule_diff"] = float(o["trend5"] - o["random"]); o["rule_diff_CI"] = paired(e_r)
        agree_m += abs(o["method_diff"]) <= o["method_diff_CI"]; agree_r += abs(o["rule_diff"]) <= o["rule_diff_CI"]
        out.append(o)
        print(f"{c['prog'][:34]:34s} {c['instr']:7s} continuing {cr['rate']:6.0f} ± {cr['CI']:4.0f} | random start, momentum {o['trend5']:6.0f} ± {o['trend5_CI']:4.0f}"
              f" | coin flip {o['random']:6.0f} ± {o['random_CI']:4.0f} | continuing - momentum {o['method_diff']:+5.0f} ± {o['method_diff_CI']:3.0f}"
              f" | momentum - coin flip {o['rule_diff']:+5.0f} ± {o['rule_diff_CI']:3.0f}", flush=True)
    stuck = sum(r[2] for r in R)
    tot = {k: float(sum(o[k] for o in out)) for k in ("continuing", "trend5", "random", "method_diff", "rule_diff")}
    print(f"sums over the {len(out)} chosen settings: continuing {tot['continuing']:.0f}, momentum {tot['trend5']:.0f}, coin flip "
          f"{tot['random']:.0f}; continuing - momentum {tot['method_diff']:+.0f} (= {tot['continuing'] - tot['trend5']:+.0f}), "
          f"momentum - coin flip {tot['rule_diff']:+.0f} (= {tot['trend5'] - tot['random']:+.0f}); intervals covering zero: "
          f"{agree_m} and {agree_r} of {len(out)}", flush=True)
    json.dump(dict(rows=out, paths=CV.PATHS, attempts_per_path=N, rules=list(RULES), stuck=stuck, sums=tot,
                   zero_inside=dict(method=agree_m, rule=agree_r, n=len(out))), open("cont_check_v10.json", "w"), indent=0)
