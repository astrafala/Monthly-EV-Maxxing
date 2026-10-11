"""
Version 9 witness of n20: the chain check of Chapter 11 runs the engine without the daily flat, so its positions are held
overnight; until version 9's fix they paid the markets' overnight financing, which the chain does not have and the plan
(flat every evening) never pays. FTMO's funded account at its chosen setting on the chain's rules (verify_v9.simplified),
on the verification's 48 paths, with and without financing, against the chain: the first cycle's success rate, paid
cycles per account, cash per account, and the mean result of a normal trade in units of its risk (theory: -rho).
A second witness reruns the largest remaining differences of the check (the USDJPY programmes share their 48 paths) on
192 fresh paths: FunderPro's first funded cycle on USDJPY against the chain, with the cost and trades of the cycle.
Writes fin_check_v9.json.
"""
import json, math, random
import numpy as np
from multiprocessing import Pool
import acct_mc as A, pathfirm as PF, optimize_v9 as O, verify_v9 as VF, firms_v9 as F7, analytic_v9 as AN

PROG, INSTR, N = "FTMO 2-Step", "US100", 300
# second witness: the largest remaining differences of the chain check (the USDJPY programmes, which share their 48
# paths) rerun on 192 fresh paths: FunderPro's first funded cycle on USDJPY, no financing, against the chain, with the
# cycle's cost and trades (the engine's Friday closes add trades the chain does not have)
PROG2, INSTR2, PATHS2, N2 = "FunderPro Classic", "USDJPY", [f"synth{6200 + j}y2" for j in range(192)], 300

def chosen(prog=PROG, instr=INSTR):
    return [r for r in json.load(open("opt_v9_final.json")) if r["prog"] == prog and r["instr"] == instr and r["tag"] == "chosen"][0]

def job(a):
    i, fin = a
    c = chosen(); data = VF.VPATHS[i]
    F = VF.simplified(F7.rules_for(c["prog"], c["size"], fee=c.get("fee"))); rng = random.Random(777 + i)
    dn = data if fin else PF.nofin_market(c["instr"], data)
    R = []; orig = PF.PathTrader.trade
    def logged(self, l, w, clock, fw, opts=None):
        r = orig(self, l, w, clock, fw, opts)
        if not (opts or {}).get("terminal") and l > 0: R.append(r[0] / l)
        return r
    PF.PathTrader.trade = logged
    out = []
    try:
        for _ in range(N):
            tr = PF.PathTrader(c["instr"], dn, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
            paid, _, _, npay = A.run_funded(F["funded"], tr, rng, F, rng.random() * A.DAY, c["X1"], c["X"])
            out.append((paid, npay))
    finally:
        PF.PathTrader.trade = orig
    PF.evict(data); PF.evict(dn)
    return out, float(np.sum(R)), len(R), float(np.sum(np.square(R)))

def job2(i):
    """FunderPro's first funded cycle on USDJPY (no financing): paid or not, the cycle's cost and trades"""
    c = chosen(PROG2, INSTR2); data = PATHS2[i]; dn = PF.nofin_market(c["instr"], data)
    F = VF.simplified(F7.rules_for(c["prog"], c["size"], fee=c.get("fee"))); F["funded"]["max_payouts"] = 1
    rng = random.Random(9900 + i); orig = PF.PathTrader.trade; T = []
    def logged(self, l, w, clock, fw, opts=None):
        r = orig(self, l, w, clock, fw, opts); info = self.last_info or {}
        T.append((self.cost * info.get("notional", 0.0), info.get("why") == "fri")); return r
    PF.PathTrader.trade = logged
    out = []
    try:
        for _ in range(N2):
            T.clear()
            tr = PF.PathTrader(c["instr"], dn, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
            paid, _, _, npay = A.run_funded(F["funded"], tr, rng, F, rng.random() * A.DAY, c["X1"], c["X"])
            out.append((npay >= 1, sum(f for f, _ in T), len(T), sum(1 for _, x in T if x)))
    finally:
        PF.PathTrader.trade = orig
    PF.evict(data); PF.evict(dn)
    return out

def summary(res):
    G = len(res); t = O.tq(G - 1)
    def cl(v):
        v = np.array(v); return float(v.mean()), float(t * v.std(ddof=1) / math.sqrt(G))
    q1 = cl([np.mean([n >= 1 for _, n in g]) for g, *_ in res]); npd = cl([np.mean([n for _, n in g]) for g, *_ in res])
    cash = cl([np.mean([p for p, _ in g]) for g, *_ in res])
    s = sum(x[1] for x in res); n = sum(x[2] for x in res); s2 = sum(x[3] for x in res)
    mean = s / n; sd = math.sqrt(max(s2 / n - mean ** 2, 0.0))
    per = [x[1] / x[2] for x in res]                                     # per-path means: cluster interval
    return dict(q1=q1[0], q1_ci=q1[1], n_paid=npd[0], n_paid_ci=npd[1], cash=cash[0], cash_ci=cash[1],
                meanR=mean, meanR_ci=float(t * np.std(per, ddof=1) / math.sqrt(G)), meanR_ci_iid=1.96 * sd / math.sqrt(n), trades=n,
                accounts=G * N, q1_path=[float(np.mean([n_ >= 1 for _, n_ in g])) for g, *_ in res], meanR_path=[float(v) for v in per],
                cash_path=[float(np.mean([p_ for p_, _ in g])) for g, *_ in res])

def paired(a, b):
    d = np.array(a) - np.array(b); G = len(d)
    return float(d.mean()), float(O.tq(G - 1) * d.std(ddof=1) / math.sqrt(G))

if __name__ == "__main__":
    c = chosen()
    out = {}
    with Pool(4) as p:
        for fin in (True, False):
            out["with_financing" if fin else "without_financing"] = summary(p.map(job, [(i, fin) for i in range(len(VF.VPATHS))]))
    F = VF.simplified(F7.rules_for(c["prog"], c["size"], fee=c.get("fee")))
    a = AN.programme(c["prog"], c["instr"], c["m"], c["k"], c["X1"], c["X"], L=c["L"], size=c["size"], F=F)
    out["chain"] = dict(q1=a["q1"], n_paid=a["n_paid"], cash=a["cash_funded"], meanR=-a["rho"])
    out["setting"] = {k: c[k] for k in ("prog", "instr", "m", "k", "L", "X1", "X")}
    out["paths"] = len(VF.VPATHS)
    w, o = out["with_financing"], out["without_financing"]          # same paths and seeds: paired differences
    out["paired"] = dict(q1=paired(w["q1_path"], o["q1_path"]), cash=paired(w["cash_path"], o["cash_path"]),
                         meanR=paired(w["meanR_path"], o["meanR_path"]))
    with Pool(4) as p:
        R2 = p.map(job2, range(len(PATHS2)))
    c2 = chosen(PROG2, INSTR2)
    F2 = VF.simplified(F7.rules_for(c2["prog"], c2["size"], fee=c2.get("fee"))); fd2 = F2["funded"]
    rho2 = AN.rho_of(INSTR2, c2["m"]); lm2 = AN.min_lot_risk(INSTR2, c2["m"])
    ch2 = AN.chain(c2["X1"], fd2["dd"], c2["L"], c2["k"], rho2, cap=AN.caps_funded(fd2, c2["X1"]), buf=100.0,
                   lmin=max(0.1 * c2["L"], lm2), wmin_frac=max(0.0, AN.WMIN_SD / c2["m"] - rho2), lm=lm2)
    G2 = len(R2); q = np.array([np.mean([x[0] for x in g]) for g in R2])
    K2 = float(np.mean([x[1] for g in R2 for x in g])); N2t = float(np.mean([x[2] for g in R2 for x in g])); Nf = float(np.mean([x[3] for g in R2 for x in g]))
    out["usdjpy"] = dict(setting={k: c2[k] for k in ("prog", "instr", "m", "k", "L", "X1", "X")}, paths=G2, accounts=G2 * N2,
                         q1=float(q.mean()), q1_ci=float(O.tq(G2 - 1) * q.std(ddof=1) / math.sqrt(G2)), q1_chain=ch2["P"],
                         cost=K2, cost_chain=ch2["Ecost"], trades=N2t, trades_chain=ch2["N"], friday_closes=Nf,
                         q1_identity=float((fd2["dd"] - K2) / (ch2["X_succ"] + fd2["dd"])))
    u = out["usdjpy"]
    print(f"{PROG2} {INSTR2}, first funded cycle on {G2} fresh paths: {u['q1']:.4f} ± {u['q1_ci']:.4f} against the chain's {u['q1_chain']:.4f}; "
          f"cost per cycle {u['cost']:.0f} against {u['cost_chain']:.0f}; trades {u['trades']:.2f} against {u['trades_chain']:.2f} ({u['friday_closes']:.3f} Friday closes); "
          f"chain with the engine's cost {u['q1_identity']:.4f}", flush=True)
    for k in ("with_financing", "without_financing"):
        o = out[k]
        print(f"{k:18s} first cycle {o['q1']:.4f} ± {o['q1_ci']:.4f}  paid cycles {o['n_paid']:.4f} ± {o['n_paid_ci']:.4f}  "
              f"cash {o['cash']:7.0f} ± {o['cash_ci']:4.0f}  mean trade {o['meanR']:+.4f} ± {o['meanR_ci']:.4f} R  ({o['trades']:,} trades)", flush=True)
    ch = out["chain"]
    print(f"{'chain':18s} first cycle {ch['q1']:.4f}           paid cycles {ch['n_paid']:.4f}           cash {ch['cash']:7.0f}         mean trade {ch['meanR']:+.4f} R")
    pq, pc, pr = out["paired"]["q1"], out["paired"]["cash"], out["paired"]["meanR"]
    print(f"with minus without (paired by path): first cycle {pq[0]:+.4f} ± {pq[1]:.4f}, cash {pc[0]:+.0f} ± {pc[1]:.0f}, mean trade {pr[0]:+.4f} ± {pr[1]:.4f} R")
    json.dump(out, open("fin_check_v9.json", "w"), indent=1)
