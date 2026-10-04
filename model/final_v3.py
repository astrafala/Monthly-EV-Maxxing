"""High-precision per-firm results at the chosen settings: synthetic (4 x 6000 attempts, different seeds) and real data."""
import json, sys, math
import numpy as np
from multiprocessing import Pool
import firms_v3 as FV, pathfirm as PF, random

def job(a):
    b, data, seed, n = a
    F = FV.cfd_firms(b["size"])[b["firm"]] if b["kind"] == "cfd" else FV.futures_firms()[b["firm"]]
    rng = random.Random(seed)
    R = [PF.attempt(F, b["instr"], data, b["m"], b["L"], b["k"], b["X1"], b["X"], rng) for _ in range(n)]
    return b["firm"], data, R

def summarize(F, R):
    v = np.array([r["v"] for r in R]); days = np.array([r["days"] for r in R]); n = len(R)
    npass = len(F["phases"]); funded = [r for r in R if r["passed"] == npass]
    P = len(funded) / n
    Vf = np.mean([r["paid"] for r in funded]); tf = np.mean([r["t_fund"] for r in funded])
    act = F.get("activation", 0)
    fee_eval = np.mean([(r["fees"] - act if r["passed"] == npass else -r["v"]) for r in R])
    t_eval = np.mean([r["t_eval"] for r in R])
    t1 = [r["t1"] for r in R if r["t1"] is not None]
    # EV per month by ratio estimator, CI by the delta method
    mv, md = v.mean(), days.mean(); ratio = mv / md
    resid = v - ratio * days
    ci_ratio = 1.96 * resid.std() / math.sqrt(n) / md
    out = dict(n=n, EV=mv, EV_CI=1.96 * v.std() / math.sqrt(n), days=md, EV_month=ratio * 30.44, EV_month_CI=ci_ratio * 30.44,
               P=P, P1=np.mean([r["passed"] >= 1 for r in R]), Vf=Vf, t_fund=tf, t_eval=t_eval, fee_eval=fee_eval,
               t_first_med=float(np.median(t1)) if t1 else None, P_paid=len(t1) / n,
               trades=np.mean([r["trades"] for r in R]), sd_attempt=v.std(),
               EV_month_funded_slot=(Vf - act - fee_eval / P) / (tf / 30.44) if P > 0 else None,
               evals_per_funded_slot=(t_eval / P) / tf if P > 0 else None)
    return {k: (float(x) if x is not None else None) for k, x in out.items()}

if __name__ == "__main__":
    best = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "best_v3.json"))
    J = []
    for b in best:
        for s in range(4): J.append((b, "synth", 100 + s, 6000))
        J.append((b, "real", 200, 8000))
    with Pool(4) as p:
        out = p.map(job, J, chunksize=1)
    res = {}
    for b in best:
        F = FV.cfd_firms(b["size"])[b["firm"]] if b["kind"] == "cfd" else FV.futures_firms()[b["firm"]]
        Rs = sum([R for f, d, R in out if f == b["firm"] and d == "synth"], [])
        Rr = sum([R for f, d, R in out if f == b["firm"] and d == "real"], [])
        res[b["firm"]] = dict(setting=b, fee=F["fee"], activation=F.get("activation", 0), monthly=F["monthly"],
                              synth=summarize(F, Rs), real=summarize(F, Rr))
        s, r = res[b["firm"]]["synth"], res[b["firm"]]["real"]
        print(f"{b['firm'][:34]:34s} synth EV={s['EV']:6.0f}±{s['EV_CI']:3.0f} d={s['days']:5.1f} EV/mo={s['EV_month']:5.0f}±{s['EV_month_CI']:3.0f} "
              f"P={s['P']:.3f} Vf={s['Vf']:5.0f} tf={s['t_fund']:4.1f} U={s['EV_month_funded_slot'] or 0:5.0f} | real EV/mo={r['EV_month']:5.0f}±{r['EV_month_CI']:3.0f} P={r['P']:.3f}", flush=True)
    json.dump(res, open(sys.argv[2] if len(sys.argv) > 2 else "final_v3.json", "w"), indent=1)
