"""
Version 8 checks of the engine against theory:
  1. brackets   single brackets with costs on synthetic paths: win rate l/(l+w+c) and mean result -c (in units of l)
  2. ties       convergence in the number of sub-steps: brackets at the tightest stop the plan allows (0.6 sd) with 12, 60
                and 240 sub-steps per hour, against the exact win rate l/(l+w)
  3. zero       FTMO with no costs and no daily rules: phase pass rate and average withdrawal against the chain's exact
                values (with the terminal rule every failure ends at the floor; wins may pass the target)
  4. chain      every chosen programme: engine with the daily rules switched off against the exact chain, then the
                full engine; the difference between the two engine runs is what the daily rules cost
  5. dll        what the daily loss limit costs at the chosen FTMO setting
  6. scale      200K against two 100K accounts on the same seeds: once with the 200K fee set to twice the 100K fee (a
                test that the trading rules scale), once with the firm's real 200K fee (the actual contract)
Writes verify_v8.json.
"""
import json, random, copy, math, sys
import numpy as np
from multiprocessing import Pool
import pathfirm as PF, firms_v8 as F7, analytic_v8 as AN

def free(instr, data):
    key = (instr, data + "_free")
    if key not in PF._DATA:
        M = dict(PF.market(instr, data)); M["fin"] = 0.0; M["cost"] = 0.0
        PF._DATA[key] = M
    return data + "_free"

def brackets(a):
    k, m, data, n, seed, costs = a
    rng = random.Random(seed); d = data if costs else free("US100", data)
    tr = PF.PathTrader("US100", d, m, 1000, k, rng)
    c = tr.cost / (m * tr.M["sig"]) * 1000.0
    res = []; clock = 0.0
    for _ in range(n):
        pnl, h = tr.trade(1000.0, 1000.0 * k, clock, False)
        clock += h + rng.random() * 24
        res.append(pnl / 1000.0)
    r = np.array(res)
    p_th = 1000.0 / (1000.0 + 1000.0 * k + c)
    return dict(k=k, m=m, data=data, costs=costs, n=n, win=float(np.mean(r > 0)), theory=p_th,
                win_ci=1.96 * math.sqrt(p_th * (1 - p_th) / n), meanR=float(r.mean()), mean_theory=-c / 1000.0,
                ci=float(1.96 * r.std() / math.sqrt(n)))

def simplified(F):
    """the rules the chain models: no daily loss limit, no minimum or profitable days, no daily flat; payouts only at the
    payout target; the concentration policy as a per-trade cap only. Weekends stay flat: the synthetic markets close at
    weekends, and a position held through one would gap, which the chain cannot represent."""
    F = copy.deepcopy(F)
    F.pop("flat_daily", None); F["flat_weekend_eval"] = True      # flat at weekends: no weekend gaps (the chain has none)
    for st in F["phases"]:
        st["dll"] = None; st["min_days"] = 0; st.pop("profit_days", None); st["review"] = 0
        if st.get("conc"): st["max_win"] = min(st.get("max_win") or 1e18, st["conc"] * st["target"]); st["conc"] = None
        if st.get("best"): st["max_win"] = min(st.get("max_win") or 1e18, st["best"] * st["target"]); st["best"] = None
    fd = F["funded"]
    fd["dll"] = None; fd.pop("profit_days", None); fd["flat_weekend"] = True; fd["per_trade"] = True
    for kk in ("cycle_days", "first_days", "roll_profit_cap"): fd.pop(kk, None)    # not in the chain
    fd["min_payout"] = 0.0
    fd["pay_at_target_only"] = True  # the chain's cycles end only at the payout target or the floor
    fd["no_best_check"] = True       # the chain caps each trade, not each day, and has no request-time best-day test
    return F

VPATHS = [f"synth{5000 + j}y2" for j in range(24)]      # 24 independent two-year paths: clusters for the intervals

def _cl_mean(vals):
    """mean of per-path means with a cluster-robust 95% interval (Student t, G - 1 degrees of freedom)"""
    import optimize_v8 as O
    m = np.array([np.mean(x) for x in vals]); G = len(m)
    return float(m.mean()), float(O.tq(G - 1) * m.std(ddof=1) / math.sqrt(G))

def _cl_ratio(num, den):
    import optimize_v8 as O
    N = np.array([np.sum(x) for x in num]); D = np.array([np.sum(x) for x in den]); G = len(N)
    r = N.sum() / max(D.sum(), 1e-9)
    se = math.sqrt(G / (G - 1) * np.sum((N - r * D) ** 2)) / max(D.sum(), 1e-9)
    return float(r), float(O.tq(G - 1) * se)

def _engine(a):
    c, F, paths, seeds, n = a
    per = []; s0 = PF.A.STUCK[0]
    for data, seed in zip(paths, seeds):
        rng = random.Random(seed)
        per.append([PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng) for _ in range(n)])
        PF.evict(data)
    np_ = len(F["phases"])
    P, P_ci = _cl_mean([[r["passed"] == np_ for r in g] for g in per])
    EV, EV_ci = _cl_mean([[r["v"] for r in g] for g in per])
    cash, cash_ci = _cl_ratio([[r["paid"] for r in g if r["passed"] == np_] for g in per], [[1.0 for r in g if r["passed"] == np_] for g in per])
    days, _ = _cl_mean([[r["days"] for r in g] for g in per])
    return dict(P=P, P_ci=P_ci, EV=EV, EV_ci=EV_ci, cash=cash, cash_ci=cash_ci, days=days, n=sum(len(g) for g in per), clusters=len(per),
                stuck=PF.A.STUCK[0] - s0)

def funded_free(a):
    """FTMO funded account alone, no costs, no daily rules, split 100%, no refund: E[withdrawn] against the chain"""
    data, seed, n, k, X = a
    F = simplified(F7.rules_for("FTMO 2-Step")); F["phases"] = []
    F["funded"]["split"] = 1.0; F["funded"]["refund"] = 0
    d = free("US100", data); rng = random.Random(seed)
    out = [PF.attempt(F, "US100", d, 1.0, 1500, k, X, X, rng)["paid"] for _ in range(n)]
    PF.evict(data); PF.evict(data + "_free")
    return out

def phase_free(a):
    data, seed, n, k = a
    F = simplified(F7.rules_for("FTMO 2-Step")); F["phases"] = F["phases"][:1]
    F["funded"]["split"] = 0.0; F["funded"]["refund"] = 0
    d = free("US100", data); rng = random.Random(seed)
    out = [PF.attempt(F, "US100", d, 1.0, 1500, k, 10000, 10000, rng)["passed"] for _ in range(n)]
    PF.evict(data); PF.evict(data + "_free")
    return out

def scale_test(a):
    """a 200K account against two 100K accounts on the same seeds. fee='double': the 200K fee is set to twice the 100K
    fee, so the comparison isolates the trading rules (exact where every rule scales with the account); fee='real': the
    firm's actual 200K fee (and every fixed-dollar rule as published), i.e. the real contracts"""
    import optimize_v8 as O
    prog, firm, instr, n, fee = a
    c1 = dict(prog=prog, firm=firm, instr=instr, m=1.0, k=3, L=1500, X1=10000, X=10000, size=100_000)
    if firm == "GFT": c1["X1"] = 6000
    F1 = O.firm_rules(c1)
    c2 = dict(c1, L=3000, X1=2 * c1["X1"], X=20000, size=200_000)
    if fee == "double": c2["fee"] = 2 * F1["fee"]
    F2 = O.firm_rules(c2)
    r1, r2 = random.Random(5), random.Random(5)
    a1 = np.array([PF.attempt(F1, instr, "synth441", 1.0, c1["L"], 3, c1["X1"], c1["X"], r1)["v"] for _ in range(n)])
    a2 = np.array([PF.attempt(F2, instr, "synth441", 1.0, c2["L"], 3, c2["X1"], c2["X"], r2)["v"] for _ in range(n)])
    d = np.abs(a2 - 2 * a1)
    return dict(prog=prog, fee=fee, fee100=F1["fee"], fee200=F2["fee"], n=n, max_abs=float(d.max()),
                mismatches=int((d > 0.01).sum()), v100=float(a1.mean()), v200_half=float(a2.mean() / 2))

if __name__ == "__main__":
    out = {}
    with Pool(4) as pool:
        out["scale"] = pool.map(scale_test, [(p, f, "US100", 1500, fee) for fee in ("double", "real") for p, f in
                                             (("FTMO 2-Step", "FTMO"), ("The5ers High Stakes", "The5ers"),
                                              ("Fintokei ProTrader", "Fintokei"), ("GFT 2-Step Standard", "GFT"))])
    for s in out["scale"]: print("scale", s, flush=True)
    with Pool(4) as pool:
        # 1. brackets with costs (paths 401-404), tight and normal stops
        J = [(k, m, f"synth{401 + i}y4", 15000, 10 + i, True) for k in (1, 2, 3, 6) for m in (0.6, 1.0) for i in range(4)]
        R = pool.map(brackets, J)
        agg = []
        for k in (1, 2, 3, 6):
            for m in (0.6, 1.0):
                rs = [r for r in R if r["k"] == k and r["m"] == m]
                n = sum(r["n"] for r in rs); win = sum(r["win"] * r["n"] for r in rs) / n
                meanR = sum(r["meanR"] * r["n"] for r in rs) / n
                th = rs[0]["theory"]
                agg.append(dict(k=k, m=m, n=n, win=win, theory=th, win_ci=1.96 * math.sqrt(th * (1 - th) / n), meanR=meanR,
                                mean_theory=rs[0]["mean_theory"], ci=float(np.sqrt(np.mean([r["ci"] ** 2 for r in rs]) / len(rs)))))
        out["brackets"] = agg
        for b in agg: print("bracket", b, flush=True)
        # 2. sub-step convergence at the tightest stop the plan allows (0.6 sd): 12, 60 (the plan's paths) and 240 sub-steps
        #    per hour, no costs, six independent 2-year paths per cell, against the exact win rate 1 / (1 + k)
        SUBS = (12, 60, 240)
        J = [(k, 0.6, f"synth{411 + i}y2s{sb}", 20000, 30 + i, False) for k in (1, 2, 3, 6) for sb in SUBS for i in range(6)]
        R = pool.map(brackets, J)
        ties = []
        for k in (1, 2, 3, 6):
            for sb in SUBS:
                rs = [r for r in R if r["k"] == k and r["data"].endswith(f"s{sb}")]
                n = sum(r["n"] for r in rs); w = sum(r["win"] * r["n"] for r in rs) / n
                th = 1 / (1 + k); ci = 1.96 * math.sqrt(th * (1 - th) / n)
                # cluster interval over the six paths (Student t, 5 df)
                ws = np.array([r["win"] for r in rs]); ci_cl = 2.571 * ws.std(ddof=1) / math.sqrt(len(ws))
                ties.append(dict(k=k, sub=sb, n=n, win=w, theory=th, ci=ci, ci_cluster=float(ci_cl), z=(w - th) / (ci / 1.96)))
        out["ties"] = ties
        json.dump(ties, open("verify_v8_ties.json", "w"), indent=1)
        for t in ties: print("ties", t, flush=True)
        # 3. zero-cost FTMO phase 1 and funded account against the exact chain
        PG = pool.map(phase_free, [(f"synth{6000 + i}y2", 40 + i, 2000, 3) for i in range(32)])
        WG = pool.map(funded_free, [(f"synth{6100 + i}y2", 50 + i, 1000, 3, 15000) for i in range(32)])
        P = [x for o in PG for x in o]; W = [x for o in WG for x in o]
    ch1 = AN.chain(10000, 10000, 1500, 3, 0.0, cap=4000, wmin_frac=AN.WMIN_SD / 1.0)
    chf = AN.programme("FTMO 2-Step", "US100", 1.0, 3, 15000, 15000, F=dict(simplified(F7.rules_for("FTMO 2-Step")), phases=[]),
                       cost_mult=0.0)
    P1, P1_ci = _cl_mean([[x >= 1 for x in o] for o in PG]); Wm, W_ci = _cl_mean(WG)
    out["zero"] = dict(P1=P1, P1_ci=P1_ci, P1_chain=ch1["P"], P1_half=0.5, X_succ_chain=ch1["X_succ"],
                       X_fail_chain=ch1["X_fail"], W=Wm, W_ci=W_ci,
                       W_chain=chf["withdrawn"], W_identity=-chf["x_end"], D=10000.0, n=len(P), n_funded=len(W))
    print("zero", out["zero"], flush=True)
    # 4. every chosen programme
    FIN = json.load(open("opt_v8_final.json"))
    rows = []
    jobs = []
    sel = [r for r in FIN if r["tag"] == "chosen" and r.get("kind", "cfd") == "cfd"]
    for r in sel:
        F = F7.rules_for(r["prog"], r["size"], fee=r.get("fee"))
        jobs.append((r, simplified(F), VPATHS, tuple(range(60, 84)), 500))
    with Pool(4) as pool:
        E = pool.map(_engine, jobs, chunksize=1)
    for r, e, j in zip(sel, E, jobs):
        a = AN.programme(r["prog"], r["instr"], r["m"], r["k"], r["X1"], r["X"], L=r["L"], size=r["size"], F=j[1])
        a_full = AN.programme(r["prog"], r["instr"], r["m"], r["k"], r["X1"], r["X"], L=r["L"], size=r["size"],
                              F=F7.rules_for(r["prog"], r["size"], fee=r.get("fee")))
        rows.append(dict(prog=r["prog"], instr=r["instr"], size=r["size"], m=r["m"], k=r["k"], L=r["L"], X=r["X"], X1=r["X1"],
                         rho=a["rho"], c=a["c"], P_chain=a["P"], P_simpl=e["P"], P_simpl_ci=e["P_ci"], P_full=r["P"],
                         cash_chain=a["cash_funded"], cash_simpl=e["cash"], cash_simpl_ci=e["cash_ci"], cash_full=r["Vf"],
                         EV_chain=a["EV"], EV_simpl=e["EV"], EV_simpl_ci=e["EV_ci"], EV_full=r["EV"], days_full=r["days"],
                         days_simpl=e["days"], EV_chain_fullcaps=a_full["EV"], identity_gap=a["identity_gap"],
                         withdrawn=a["withdrawn"], x_end=a["x_end"], cost_funded=a["cost_funded"], trades_funded=a["trades_funded"],
                         st=r.get("st"), stuck_simpl=e["stuck"],
                         phases=[{kk: p[kk] for kk in ("A", "B", "cap", "P", "N", "Ecost", "X_fail", "X_succ", "P_identity", "P_textbook")}
                                 for p in a["phases"]], q1=a["q1"], q=a["q"], n_paid=a["n_paid"], credits=a["credits"]))
        x = rows[-1]
        print(f"{x['prog'][:34]:34s} {x['instr']:7s} P {x['P_chain']:.3f}/{x['P_simpl']:.3f}±{x['P_simpl_ci']:.3f}/{x['P_full']:.3f} "
              f"cash {x['cash_chain']:7.0f}/{x['cash_simpl']:7.0f}/{x['cash_full']:7.0f} EV {x['EV_chain']:6.0f}/{x['EV_simpl']:6.0f}±{x['EV_simpl_ci']:.0f}/{x['EV_full']:6.0f}",
              flush=True)
    out["programmes"] = rows
    json.dump(out, open("verify_v8.json", "w"), indent=1, default=float)
