"""
Version 9 check of the continuing-slot rates (review of version 8, finding 12).

continuing_v9.py measures each chosen setting as a slot run back to back with the plan's 5-hour momentum direction rule
on paths 151-166; the final run measures it as a random-start ratio with a coin-flip direction on paths 121-136. The two
differ in three ways at once: the measurement (start states, credits, price levels and calendar carried from attempt to
attempt), the direction rule, and the paths. This check separates them. On the continuing stage's own paths it runs
1,500 random-start attempts per path for every chosen setting twice, once with the momentum rule and once with a coin
flip:
  - continuing slot against random start, same rule and same paths, paired path by path: the measurement alone;
  - momentum against coin flip, random start on the same paths: the direction rule alone. Under the model no rule that
    uses only past prices changes a trade's outcome distribution, so the two have the same expectation; the momentum
    rule makes attempts that overlap on one path take the same side at the same time, so its per-path figures scatter
    more.
Paired intervals: Student t over the 16 paths (15 degrees of freedom). Writes cont_check_v9.json.
"""
import json, math, random
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, optimize_v9 as O, continuing_v9 as CV

N = 1500
RULES = {"trend5": 9100, "random": 9200}       # seeds: per rule, plus the path's index

def job(a):
    c, i, rule = a
    F = O.firm_rules(c)
    rng = random.Random(RULES[rule] + i); s0 = PF.A.STUCK[0]
    R = [PF.attempt(F, c["instr"], CV.PATHS[i], c["m"], c["L"], c["k"], c["X1"], c["X"], rng, dir_rule=rule) for _ in range(N)]
    return float(sum(r["v"] for r in R)), float(sum(r["days"] for r in R)), int(PF.A.STUCK[0] - s0)

def ratio_ci(V, D):
    G = len(V); r = V.sum() / D.sum(); u = V - r * D
    return 30.44 * r, 30.44 * O.tq(G - 1) * math.sqrt(G / (G - 1) * np.sum(u ** 2)) / D.sum()

def paired(a, b):
    d = np.asarray(a) - np.asarray(b); G = len(d)
    return float(d.mean()), float(O.tq(G - 1) * d.std(ddof=1) / math.sqrt(G))

if __name__ == "__main__":
    CONT = json.load(open("continuing_v9.json"))["rows"]
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
    rows = [r for r in CONT if r["tag"] == "chosen"]
    C = [{k: r[k] for k in keys if k in r} for r in rows]
    K = [(i, rule, ci) for i in range(len(CV.PATHS)) for rule in RULES for ci in range(len(C))]   # path-major: each process reuses its paths
    with Pool(4) as p:
        R = p.map(job, [(C[ci], i, rule) for i, rule, ci in K], chunksize=1)
    res = dict(zip(K, R))
    out = []
    for ci, (c, cr) in enumerate(zip(C, rows)):
        o = dict(c, continuing=cr["rate"], continuing_CI=cr["CI"], random_start_final=cr["random_start"], random_start_final_CI=cr["random_start_CI"])
        per = {}
        for rule in RULES:
            V = np.array([res[(i, rule, ci)][0] for i in range(len(CV.PATHS))]); D = np.array([res[(i, rule, ci)][1] for i in range(len(CV.PATHS))])
            o[rule], o[rule + "_CI"] = ratio_ci(V, D)
            per[rule] = 30.44 * V / D
            o[rule + "_per_path"] = per[rule].tolist()
        o["method_diff"], o["method_diff_CI"] = paired(cr["per_path"], per["trend5"])        # continuing - random start, momentum rule
        o["rule_diff"], o["rule_diff_CI"] = paired(per["trend5"], per["random"])              # momentum - coin flip, random start
        o["scatter_trend5"] = float(np.std(per["trend5"], ddof=1)); o["scatter_random"] = float(np.std(per["random"], ddof=1))
        out.append(o)
        print(f"{c['prog'][:34]:34s} {c['instr']:7s} continuing {cr['rate']:6.0f} ± {cr['CI']:4.0f} | random start, momentum {o['trend5']:6.0f} ± {o['trend5_CI']:4.0f}"
              f" | coin flip {o['random']:6.0f} ± {o['random_CI']:4.0f} | continuing - momentum {o['method_diff']:+5.0f} ± {o['method_diff_CI']:3.0f}"
              f" | momentum - coin flip {o['rule_diff']:+5.0f} ± {o['rule_diff_CI']:3.0f}", flush=True)
    stuck = sum(r[2] for r in R)
    json.dump(dict(rows=out, paths=CV.PATHS, attempts_per_path=N, rules=list(RULES), stuck=stuck), open("cont_check_v9.json", "w"), indent=0)
