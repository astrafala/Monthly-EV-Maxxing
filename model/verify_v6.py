"""
Independent checks of the engine against theory (Chapter 11):
  1. single brackets on a cost-free, financing-free synthetic path: win rates and mean result;
  2. FTMO phase 1 and the funded account with no costs: pass rate 50%, average withdrawn = allowance;
  3. every chosen programme: the closed-form values of analytic_v6 against the engine's final run;
  4. what the daily loss limit costs (FTMO, chosen settings, with and without it).
"""
import json, random, copy, math
import numpy as np
import pathfirm as PF, firms_v5 as F5, analytic_v6 as AN, acct_mc as A

def nocost(data):
    key = ("US100", data + "_free")
    if key not in PF._DATA:
        M = dict(PF.market("US100", data)); M["fin"] = 0.0; M["cost"] = 0.0
        PF._DATA[key] = M
    return data + "_free"

def brackets(k, n=40000, seed=1, m=0.75):
    rng = random.Random(seed); data = nocost("synth29")
    tr = PF.PathTrader("US100", data, m, 1000, k, rng)
    res = []
    clock = 0.0
    for _ in range(n):
        pnl, h = tr.trade(1000.0, 1000.0 * k, clock, False)
        clock += h + rng.random() * 24
        res.append(pnl / 1000.0)
    r = np.array(res)
    return dict(k=k, m=m, win=float(np.mean(r > 0)), theory=1 / (1 + k), meanR=float(r.mean()), ci=float(1.96 * r.std() / math.sqrt(n)))

def fp_phase2_zero(n=6000):
    """FundingPips Flex phase 2 (6% target, 12% floor, wins capped at 55% of the target) with no costs: theory 2/3.
    This is the check that exposed the same-bar tie bias of the first version of the engine."""
    out = []
    for i in range(4):
        key = ("USDJPY", f"synth{29 + i}_free")
        if key not in PF._DATA:
            M = dict(PF.market("USDJPY", f"synth{29 + i}")); M["fin"] = 0.0; M["cost"] = 0.0; PF._DATA[key] = M
        F = copy.deepcopy(F5.cfd_firms()["FundingPips 2-Step Flex (85%) v6 cap"]); F["phases"] = [F["phases"][1]]
        rng = random.Random(50 + i)
        out += [PF.attempt(F, "USDJPY", f"synth{29 + i}_free", 0.5, 1500, 30, 30000, 30000, rng)["passed"] >= 1 for _ in range(n)]
    P = float(np.mean(out))
    return dict(P=P, ci=1.96 * math.sqrt(P * (1 - P) / len(out)), n=len(out))

def _zc(a):
    data, seed, n = a
    F = copy.deepcopy(F5.cfd_firms()["FTMO 2-Step"])
    F["funded"]["refund"] = 0; F["funded"]["split"] = 1.0; F["funded"]["dll"] = None
    for st in F["phases"]: st["dll"] = None; st["min_days"] = 0
    d = nocost(data); rng = random.Random(seed)
    R = [PF.attempt(F, "US100", d, 0.75, 1500, 5, 10000, 10000, rng) for _ in range(n)]
    return [r["passed"] for r in R], [r["paid"] for r in R if r["passed"] == 2]

def zero_cost_ftmo(n=20000):
    """FTMO 2-Step with no costs, no daily limit, split 100%: phase 1 passes half the time and a funded account
    withdraws its allowance ($10,000) on average. Four paths (30-33), 20,000 attempts each."""
    from multiprocessing import Pool
    with Pool(4) as p:
        out = p.map(_zc, [(f"synth{30 + i}", 101 + i, n) for i in range(4)])
    passed = [x for o in out for x in o[0]]; paid = [w for o in out for w in o[1]]
    P1 = float(np.mean([x >= 1 for x in passed])); P = float(np.mean([x == 2 for x in passed]))
    return dict(P1=P1, P1_ci=1.96 * math.sqrt(P1 * (1 - P1) / len(passed)), P=P, W=float(np.mean(paid)),
                W_ci=float(1.96 * np.std(paid) / math.sqrt(len(paid))), n_funded=len(paid), n=len(passed))

def dll_effect(c, n=6000):
    out = {}
    for lab in ("with", "without"):
        F = copy.deepcopy(F5.rules_for(c["prog"], c["size"], fee=c.get("fee")))
        if lab == "without":
            for st in F["phases"]: st["dll"] = None
            F["funded"]["dll"] = None
        rs = []
        for i, data in enumerate(["synth29", "synth30", "synth31", "synth32"]):
            rng = random.Random(100 + i)
            rs += [PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng) for _ in range(n // 4)]
        v = np.array([r["v"] for r in rs]); d = np.array([r["days"] for r in rs])
        out[lab] = dict(P=float(np.mean([r["passed"] == len(F["phases"]) for r in rs])), EV=float(v.mean()), EV_month=float(v.mean() / d.mean() * 30.44))
    return out

if __name__ == "__main__":
    out = {"brackets": [brackets(k) for k in (1, 2, 3, 5, 10)]}
    out["brackets_tight"] = [brackets(k, n=60000, seed=2, m=0.35) for k in (1, 2, 3, 6)]
    for b in out["brackets"] + out["brackets_tight"]: print(b)
    out["fp_phase2_zero"] = fp_phase2_zero(); print(out["fp_phase2_zero"])
    out["zero_cost_ftmo"] = zero_cost_ftmo(); print(out["zero_cost_ftmo"])
    FIN = json.load(open("opt_v6_final.json"))
    rows = []
    for r in FIN:
        if r["data"] != "synth" or r.get("kind", "cfd") != "cfd": continue
        F = F5.rules_for(r["prog"], r["size"], fee=r.get("fee"))
        a = AN.programme(r["prog"], r["instr"], r["m"], r["k"], r["X1"], r["X"], L=r["L"], size=r["size"], F=F)
        e = AN.programme_exact(r["prog"], r["instr"], r["m"], r["k"], r["X1"], r["X"], L=r["L"], size=r["size"], F=F)
        rows.append(dict(prog=r["prog"], instr=r["instr"], tag=r["tag"], size=r["size"], k=r["k"], m=r["m"], X=r["X"], X1=r["X1"], L=r["L"],
                         fee=F["fee"], EV_month=r["EV_month"], days=r["days"], CI=r["CI"], P_paid=r["P_paid"],
                         P_exact=e["P"], cash_exact=e["cash_funded"], EV_exact=e["EV"], q_exact=e["q"], q1_exact=e["q1"],
                         withdrawn_exact=e["withdrawn"], identity_exact=e["identity"], trades_funded=e["trades_funded"],
                         cost_funded=e["cost_funded"], cycles_paid=e["n_cycles_paid"], rho=e["rho"],
                         phases_exact=[{kk: p[kk] for kk in ("A", "B", "P", "N", "Ecost", "P_identity")} for p in e["phases"]],
                         P_formula=a["P"], P_engine=r["P"], P1_formula=a["phases"][0]["P"],
                         cash_formula=a["cash_funded"], cash_engine=r["Vf"], EV_formula=a["EV"], EV_engine=r["EV"],
                         c=a["trade"]["c"], cR=a["trade"]["cR"], p=a["trade"]["p"], v=a["trade"]["var"],
                         q=a["q"], q1=a["q1"], cycles=a["paid_cycles"], kf=a["k_funded"],
                         phases=[{kk: p[kk] for kk in ("A", "B", "P", "N", "k")} for p in a["phases"]]))
    out["programmes"] = rows
    for x in rows:
        print(f"{x['prog'][:34]:34s} {x['instr']:7s} {x['tag']:10s} P {x['P_formula']:.3f}/{x['P_exact']:.3f}/{x['P_engine']:.3f} cash {x['cash_formula']:7.0f}/{x['cash_exact']:7.0f}/{x['cash_engine']:7.0f} EV {x['EV_formula']:6.0f}/{x['EV_exact']:6.0f}/{x['EV_engine']:6.0f}")
    ftmo = [r for r in FIN if r["prog"] == "FTMO 2-Step" and r["tag"] == "chosen" and r["data"] == "synth"][0]
    out["dll_ftmo"] = dll_effect(ftmo); print(out["dll_ftmo"])
    json.dump(out, open("verify_v6.json", "w"), indent=1)
