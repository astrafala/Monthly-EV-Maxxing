"""
Version 9 continuing-slot rates (review of version 8, finding 12).

Part II's search ranks settings by a random-start attempt ratio: each attempt starts a new trader at a random point of a
path and at a random hour, with no state carried over (optimize_v9.run). That ratio, 30.44 x sum(value) / sum(days), is
not by itself the long-run rate of one account slot run back to back, because the states at which a continuing slot
starts its attempts (weekday, hour, the futures price level, credits carried from earlier attempts) need not be
distributed like the random starts.

This stage measures the long-run rate directly. For every row of opt_v9_final.json (every chosen setting and size), one
slot buys an evaluation, trades it to its end (failed phase or lost funded account), buys the next one at once, and so
on, on one continuous path and calendar, with everything a real slot carries: the path position and price level, the
calendar, The5ers' credits (spent on the next purchase), monthly subscriptions (Topstep) and activation fees, payouts
dated when they arrive, and the plan's direction rule (5-hour momentum: one account alone is always flat at its entries).
Each slot runs 9 years on a 12-year path; the first year is a warm-up and its cash is discarded; the rate is the cash
dated in years 2 to 9 over those 96 months. 12 slots start at different days of the first two years of each of 16
independent paths (151-166, used by no other stage). Interval: path clusters (Student t, 15 degrees of freedom); the
per-path rates are kept so that sums of programmes (which share these paths) get their full covariance.
Writes continuing_v9.json.
"""
import json, math, random, sys
import numpy as np
from multiprocessing import Pool
import acct_mc as A, pathfirm as PF, optimize_v9 as O

PATHS = [f"synth{151 + i}" for i in range(16)]
SLOTS = 12
WARM_Y, RUN_Y = 1.0, 9.0
DAY = 24.0
YH = 365.25 * 24.0
MONTHS = (RUN_Y - WARM_Y) * 365.25 / 30.44

def slot_life(F, c, data, seed):
    """one slot, attempts back to back for RUN_Y years; returns (cash dated in the measured window, attempts started in
    it, payouts in it, stalls)"""
    rng = random.Random(seed)
    tr = PF.PathTrader(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "trend5", F.get("flat_daily"))
    tr.base = 24 * rng.randrange(730) + (22 - tr.M["h0"]) % 24        # a start in the path's first two years: no wrap
    t0, t1 = WARM_Y * YH, RUN_Y * YH
    clock = rng.random() * DAY; credit = 0.0; flows = []; n_att = 0; s0 = A.STUCK[0]
    while clock < t1:
        use = min(credit, F["fee"]); credit -= use
        t_buy = clock; flows.append((t_buy, -(F["fee"] - use))); n_att += t_buy >= t0
        ok = True
        for j, st in enumerate(F["phases"]):
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            if ok and F.get("phase_credit"): credit += F["phase_credit"][j]
            if not ok: break
        if F["monthly"]:
            for mth in range(1, max(1, math.ceil((clock - t_buy) / (30 * DAY)))):
                flows.append((t_buy + 30 * DAY * mth, -F["fee"]))
        if not ok: continue
        if F.get("activation"): flows.append((clock, -F["activation"]))
        A.PAYLOG = []
        paid, clock, tf, npay = A.run_funded(F["funded"], tr, rng, F, clock, c["X1"], c["X"])
        flows += [(t, cash) for (t, cash, _) in A.PAYLOG]; A.PAYLOG = None
    cash = sum(v for t, v in flows if t0 <= t < t1)
    pays = sum(1 for t, v in flows if t0 <= t < t1 and v > 0)
    return cash, n_att, pays, A.STUCK[0] - s0

def job(a):
    c, i = a
    F = O.firm_rules(c)
    data = PATHS[i]
    R = [slot_life(F, c, data, 7000 + 100 * i + j) for j in range(SLOTS)]
    return i, [r[0] for r in R], sum(r[1] for r in R), sum(r[2] for r in R), sum(r[3] for r in R)

if __name__ == "__main__":
    FIN = json.load(open("opt_v9_final.json"))
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
    C = [{k: r[k] for k in keys if k in r} for r in FIN]
    J = [(c, i) for i in range(len(PATHS)) for c in C]                # path-major: each process reuses its paths
    with Pool(4) as p:
        R = p.map(job, J, chunksize=1)
    out = []
    for ci, c in enumerate(C):
        rows = [R[i * len(C) + ci] for i in range(len(PATHS))]
        per_path = np.array([np.mean(r[1]) / MONTHS for r in rows])     # cash per month per slot, by path
        G = len(per_path)
        rate = float(per_path.mean()); ci_ = float(O.tq(G - 1) * per_path.std(ddof=1) / math.sqrt(G))
        f = [r for r in FIN if all(r.get(k) == c.get(k) for k in keys if k in c)][0]
        out.append(dict(c, rate=rate, CI=ci_, per_path=per_path.tolist(), attempts=int(sum(r[2] for r in rows)),
                        payouts=int(sum(r[3] for r in rows)), stuck=int(sum(r[4] for r in rows)),
                        random_start=f["EV_month"], random_start_CI=f["CI"], slots=SLOTS * G, months=MONTHS))
        o = out[-1]
        print(f"{c['prog'][:38]:38s} {c['instr']:7s} {c['size'] // 1000:>3}K {c['tag']:7s} continuing {rate:7.0f} ± {ci_:4.0f}  "
              f"random-start {f['EV_month']:7.0f} ± {f['CI']:4.0f}  attempts {o['attempts']} stuck {o['stuck']}", flush=True)
    json.dump(dict(rows=out, paths=PATHS, slots=SLOTS, warm_years=WARM_Y, run_years=RUN_Y, months=MONTHS),
              open("continuing_v9.json", "w"), indent=0)
