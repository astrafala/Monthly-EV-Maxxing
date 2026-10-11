"""
Version 9 sensitivities and timing, every row on fresh paths 141-144 (3,000 attempts per path) with the same random
numbers across the columns of a table (paired):
  cost    every chosen programme at cost x1, x1.5, x2: value of an attempt, its length, EV per month (value and time
          effects separated), plus timing (evaluation days, funded days, trades, payouts)
  risk    FTMO 2-Step at its chosen stop, k and cycle with risk per trade 1.0% ... 2.0%
  conc    what the 40% concentration policy costs: FTMO, The5ers, Fintokei, FundingPips with conc 0.4 / 0.6 / none
  flat    what the daily flat costs: FTMO and FundingPips with and without it (overnight financing then applies)
  dir     FTMO with the plan's direction rule (5-hour momentum) against a coin flip
  dll     what the daily-loss base costs: the relative-base firms run with a fixed base instead (version 7's input)
  nofill  version 9: every programme that uses filler trades (a 0.01-lot position for 3 minutes on a missing trading day)
          run instead with ordinary trades, one a day, as at Fintokei and Alpha Capital: what the assumption that the
          firms accept minimal day-completing trades is worth
  nohold  version 9: Blue Guardian without the 3-minute hold (its bracket placed at entry; a trade closed in under 2
          minutes then ends the account, the plan's reading of the tick-scalping rule)
Writes sens_v9.json.
"""
import json, random, math, copy, sys
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, firms_v9 as F7, optimize_v9 as O

PATHS = ["synth141", "synth142", "synth143", "synth144"]
FIN = json.load(open("opt_v9_final.json"))

def rules(c, tweak=None):
    F = O.firm_rules(c)
    if tweak == "conc0.6" or tweak == "conc_none":
        v = 0.6 if tweak == "conc0.6" else None
        for st in F["phases"]: st["conc"] = v
        F["funded"]["conc"] = v
    if tweak == "noflat": F.pop("flat_daily", None)
    if tweak == "dllfixed":
        for st in F["phases"] + [F["funded"]]: st["dll_mode"] = "fixed"
    if tweak == "nofill": F["no_fillers"] = True
    if tweak == "nohold": F.pop("hold_min", None)
    return F

def run(a):
    tag, c, cost_mult, rule, n, tweak = a
    F = rules(c, tweak)
    R = []; s0 = PF.A.STUCK[0]; h0 = dict(PF.A.RULE_HITS)
    for i, data in enumerate(PATHS):
        rng = random.Random(900 + i)
        R += [PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng, cost_mult=cost_mult, dir_rule=rule)
              for _ in range(n)]
    v = np.array([r["v"] for r in R]); d = np.array([r["days"] for r in R]); ratio = v.sum() / d.sum()
    Vc = np.array([v[i * n:(i + 1) * n].sum() for i in range(len(PATHS))]); Dc = np.array([d[i * n:(i + 1) * n].sum() for i in range(len(PATHS))])
    ci_cl = O.tq(len(PATHS) - 1) * math.sqrt(len(PATHS) / (len(PATHS) - 1) * np.sum((Vc - ratio * Dc) ** 2)) / d.sum() * 30.44
    ci = max(1.96 * (v - ratio * d).std() / math.sqrt(len(v)) / d.mean() * 30.44, ci_cl)
    npass = len(F["phases"])
    fail = [r for r in R if r["passed"] < npass]; fund = [r for r in R if r["passed"] == npass]
    return dict(tag=tag, tweak=tweak, prog=c["prog"], instr=c["instr"], size=c["size"], m=c["m"], k=c["k"], X=c["X"], L=c["L"],
                cost_mult=cost_mult, rule=rule, EV=float(v.mean()), days=float(d.mean()), EV_month=float(ratio * 30.44), CI=float(ci),
                P=len(fund) / len(R), P1=float(np.mean([r["passed"] >= 1 for r in R])),
                t_eval_fail=float(np.mean([r["t_eval"] for r in fail])) if fail else None,
                t_eval_pass=float(np.mean([r["t_eval"] for r in fund])) if fund else None,
                t_fund=float(np.mean([r["t_fund"] for r in fund])) if fund else None,
                trades=float(np.mean([r["trades"] for r in R])), payouts=float(np.mean([r["npay"] for r in fund])) if fund else None,
                paid=float(np.mean([r["paid"] for r in fund])) if fund else 0.0, stuck=PF.A.STUCK[0] - s0,
                rule_hits={k: PF.A.RULE_HITS[k] - h0[k] for k in h0},
                fillers=float(sum(r["st"]["fillers"] for r in R)), filler_pnl=float(sum(r["st"]["filler_pnl"] for r in R)),
                Vc=Vc.tolist(), Dc=Dc.tolist())

def dir_brackets(a):
    """trade-level test of the direction rule: cost-free 1:3 brackets on the Nasdaq, momentum rule against a coin flip"""
    rule, data, seed, n = a
    d = PF.free_market("US100", data)
    rng = random.Random(seed)
    tr = PF.PathTrader("US100", d, 0.75, 1000, 3, rng, 1.0, rule, None)
    res = []; clock = 0.0
    for _ in range(n):
        pnl, h = tr.trade(1000.0, 3000.0, clock, False); clock += h + rng.random() * 24
        res.append(pnl / (tr.last_info["notional"] * tr.s))
    return rule, res

if __name__ == "__main__":
    chosen = [r for r in FIN if r["tag"] == "chosen"]
    J = []
    for c in chosen:
        for cm in (1.0, 1.5, 2.0): J.append(("cost", c, cm, "random", 3000, None))
    ftmo = [c for c in chosen if c["prog"] == "FTMO 2-Step"][0]
    for lf in (0.010, 0.0125, 0.015, 0.0175, 0.020):
        J.append(("risk", dict(ftmo, L=lf * 100_000), 1.0, "random", 3000, None))
    for prog in ("FTMO 2-Step", "The5ers High Stakes", "Fintokei ProTrader", "FundingPips 2-Step Flex (80%)"):
        cs = [c for c in chosen if c["prog"] == prog]
        if not cs: continue
        c = max(cs, key=lambda r: r["EV_month"])
        for tw in ("conc0.6", "conc_none"): J.append(("conc", c, 1.0, "random", 3000, tw))
        if prog in ("FTMO 2-Step", "FundingPips 2-Step Flex (80%)"): J.append(("flat", c, 1.0, "random", 3000, "noflat"))
    for rule in ("trend5", "random"): J.append(("dir", ftmo, 1.0, rule, 12000, None))      # 48,000 attempts each
    for c in chosen:                                   # daily-loss base: relative (the rules) against fixed (version 7)
        if c["size"] == 100_000 and O.firm_rules(c)["phases"][0].get("dll_mode") in ("rel", "min"):
            J.append(("dll", c, 1.0, "random", 3000, "dllfixed"))
    for c in chosen:                                   # filler trades against ordinary trades (version 9)
        F = O.firm_rules(c)
        if not F.get("no_fillers") and (any(st.get("min_days") for st in F["phases"]) or F["funded"].get("cycle_days")):
            J.append(("nofill", c, 1.0, "random", 3000, "nofill"))
    for c in chosen:
        if c["prog"] == "Blue Guardian 2-Step": J.append(("nohold", c, 1.0, "random", 3000, "nohold"))
    with Pool(4) as p:
        R = p.map(run, J, chunksize=1)
    with Pool(4) as p:
        D = p.map(dir_brackets, [(rule, f"synth{461 + i}y4", 100 + i, 15000) for rule in ("trend5", "random") for i in range(4)])
    for rule in ("trend5", "random"):
        x = np.concatenate([np.array(d[1]) for d in D if d[0] == rule])
        R.append(dict(tag="dirbr", rule=rule, n=len(x), meanR=float(x.mean()), ci=float(1.96 * x.std() / math.sqrt(len(x))), win=float(np.mean(x > 0)),
                      prog="", instr="US100", size=100_000, m=0.75, k=3, X=0, L=1000, cost_mult=0.0, EV=0, days=0, EV_month=0, CI=0, P=0, tweak=None))
    json.dump(R, open("sens_v9.json", "w"), indent=0)
    for r in R:
        print(f"{r['tag']:5s} {str(r['tweak']):9s} {r['prog'][:34]:34s} {r['instr']:7s} L={r['L']:.0f} cost x{r['cost_mult']} {r['rule']:7s} "
              f"EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} EV={r['EV']:6.0f} days={r['days']:5.1f} P={r['P']:.3f}", flush=True)
