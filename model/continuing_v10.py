"""
Version 10 continuing slots: what one account slot earns run back to back.

Part II's search ranks settings by a random-start attempt ratio (optimize_v10.run): each attempt starts a new trader at a
random point of a path, with no state carried over. This stage runs, for every row of opt_v10_final.json, one slot that
buys an evaluation, trades it to its end (failed phase or lost funded account), buys the next one at once, and so on, on
one continuous path and calendar, carrying everything a real slot carries: the path position and price level, the
calendar, The5ers' hub credit (spent on the next purchase, whose refund is then 70% of the cash actually paid: version 10,
review of version 9, finding 17), monthly subscriptions (Topstep) and activation fees, payouts dated when their cash
arrives (a payout cancelled by a breach before it was processed is taken back), and the plan's direction rule (5-hour
momentum: one account alone is always flat at its entries).

What the number is (version 10, review of version 9, finding 11): the average cash per month dated in years 2 to 9 of a
slot started in the first two years of a path whose price starts at today's level (each synthetic path starts at the
market's close of 2 October 2026). It is not a proven stationary long-run rate: the price in the model is a driftless
geometric random walk with no stationary distribution, and the price level matters to whole contracts and lots (and to
Alpha Capital's lot limit), so the rate can depend on the horizon and on the starting price. Both are reported: the rate of
years 2-5 and of years 6-9 separately, and (stage 'price') every chosen setting with the starting price at half and at
twice today's level.

12 slots start at different days of the first two years of each of 16 independent paths (1151-1166, used by no other
stage); intervals: path clusters (Student t, 15 degrees of freedom); per-path rates are kept so that sums of programmes
(which share these paths) get their full covariance. Writes continuing_v10.json (and continuing_v10_price.json).
"""
import json, math, random, sys, copy
import numpy as np
from multiprocessing import Pool
import acct_mc as A, pathfirm as PF, optimize_v10 as O

PATHS = [f"synth{1151 + i}" for i in range(16)]
SLOTS = 12
WARM_Y, RUN_Y, MID_Y = 1.0, 9.0, 5.0
DAY = 24.0
YH = 365.25 * 24.0
MONTHS = (RUN_Y - WARM_Y) * 365.25 / 30.44
M_EARLY = (MID_Y - WARM_Y) * 365.25 / 30.44
M_LATE = (RUN_Y - MID_Y) * 365.25 / 30.44

def slot_life(F, c, data, seed, ref_mult=1.0):
    """one slot, attempts back to back for RUN_Y years; returns (cash dated in years 2-9, in years 2-5, in years 6-9,
    attempts started in the window, payouts in it, stalls)"""
    rng = random.Random(seed)
    tr = PF.PathTrader(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "trend5", F.get("flat_daily"))
    tr.base = 24 * rng.randrange(730) + (22 - tr.M["h0"]) % 24        # a start in the path's first two years: no wrap
    t0, t1, tm = WARM_Y * YH, RUN_Y * YH, MID_Y * YH
    clock = rng.random() * DAY; credit = 0.0; flows = []; n_att = 0; s0 = A.STUCK[0]; npay = 0
    while clock < t1:
        use = min(credit, F["fee"]); credit -= use; cash_fee = F["fee"] - use
        t_buy = clock; flows.append((t_buy, -cash_fee)); n_att += t_buy >= t0
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
        fd = copy.deepcopy(F["funded"])
        if fd.get("refund") and F.get("refund_frac") is not None:
            fd["refund"] = F["refund_frac"] * cash_fee                  # 70% of the cash paid for this account (The5ers)
        A.PAYLOG = []
        paid, clock, tf, n_ = A.run_funded(fd, tr, rng, F, clock, c["X1"], c["X"])
        for it in A.PAYLOG:
            flows.append((it[0], it[1]))
            if t0 <= it[0] < t1: npay += 1 if it[3] == "payout" else -1
        A.PAYLOG = None
    cash = sum(v for t, v in flows if t0 <= t < t1)
    early = sum(v for t, v in flows if t0 <= t < tm); late = sum(v for t, v in flows if tm <= t < t1)
    return cash, early, late, n_att, npay, A.STUCK[0] - s0

def job(a):
    c, i = a[:2]; ref_mult = a[2] if len(a) > 2 else 1.0; slots = a[3] if len(a) > 3 else SLOTS
    old = {k: dict(v) for k, v in PF.LOTS.items()}; old_nq = PF.REF_NQ
    if ref_mult != 1.0:                                          # the starting price at ref_mult x today's level
        for v in PF.LOTS.values(): v["ref"] *= ref_mult
        PF.REF_NQ = old_nq * ref_mult
    try:
        F = O.firm_rules(c)
        data = PATHS[i]
        R = [slot_life(F, c, data, 7000 + 100 * i + j) for j in range(slots)]
    finally:
        for k, v in old.items(): PF.LOTS[k].update(v)
        PF.REF_NQ = old_nq
    return (i, [r[0] for r in R], [r[1] for r in R], [r[2] for r in R], sum(r[3] for r in R), sum(r[4] for r in R),
            sum(r[5] for r in R))

KEYS = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")

def summarise(C, R, FIN, n_slots):
    out = []
    for ci, c in enumerate(C):
        rows = [R[i * len(C) + ci] for i in range(len(PATHS))]
        per_path = np.array([np.mean(r[1]) / MONTHS for r in rows])     # cash per month per slot, by path
        early = np.array([np.mean(r[2]) / M_EARLY for r in rows]); late = np.array([np.mean(r[3]) / M_LATE for r in rows])
        G = len(per_path); t = O.tq(G - 1)
        def ci_(v): return float(t * np.std(v, ddof=1) / math.sqrt(G))
        d = late - early
        f = [r for r in FIN if all(r.get(k) == c.get(k) for k in KEYS if k in c)][0]
        out.append(dict(c, rate=float(per_path.mean()), CI=ci_(per_path), per_path=per_path.tolist(),
                        rate_y2_5=float(early.mean()), CI_y2_5=ci_(early), rate_y6_9=float(late.mean()), CI_y6_9=ci_(late),
                        late_minus_early=float(d.mean()), late_minus_early_CI=ci_(d),
                        attempts=int(sum(r[4] for r in rows)), payouts=int(sum(r[5] for r in rows)),
                        stuck=int(sum(r[6] for r in rows)), random_start=f["EV_month"], random_start_CI=f["CI"],
                        slots=n_slots * G, months=MONTHS))
    return out

if __name__ == "__main__":
    FIN = json.load(open("opt_v10_final.json"))
    C = [{k: r[k] for k in KEYS if k in r} for r in FIN]
    stage = sys.argv[1] if len(sys.argv) > 1 else "main"
    if stage == "main":
        J = [(c, i) for i in range(len(PATHS)) for c in C]                # path-major: each process reuses its paths
        with Pool(4) as p:
            R = p.map(job, J, chunksize=1)
        out = summarise(C, R, FIN, SLOTS)
        for o in out:
            print(f"{o['prog'][:38]:38s} {o['instr']:7s} {o['size'] // 1000:>3}K {o['tag']:7s} years 2-9 {o['rate']:7.0f} ± {o['CI']:4.0f}  "
                  f"(2-5 {o['rate_y2_5']:6.0f}, 6-9 {o['rate_y6_9']:6.0f}, difference {o['late_minus_early']:+5.0f} ± {o['late_minus_early_CI']:4.0f})  "
                  f"random-start {o['random_start']:7.0f} ± {o['random_start_CI']:4.0f}  attempts {o['attempts']} stuck {o['stuck']}", flush=True)
        json.dump(dict(rows=out, paths=PATHS, slots=SLOTS, warm_years=WARM_Y, run_years=RUN_Y, mid_year=MID_Y, months=MONTHS),
                  open("continuing_v10.json", "w"), indent=0)
    if stage == "price":                                               # starting price at half and twice today's level
        Cc = [c for c in C if c.get("tag") == "chosen"]
        res = {}
        for mult in (0.5, 2.0):
            J = [(c, i, mult, 4) for i in range(len(PATHS)) for c in Cc]
            with Pool(4) as p:
                R = p.map(job, J, chunksize=1)
            res[str(mult)] = summarise(Cc, R, FIN, 4)
        base = {(r["prog"], r["instr"], r["size"]): r for r in json.load(open("continuing_v10.json"))["rows"]}
        for mult, rows in res.items():
            for o in rows:
                b = base[(o["prog"], o["instr"], o["size"])]
                print(f"price x{mult}: {o['prog'][:36]:36s} {o['instr']:7s} {o['rate']:7.0f} ± {o['CI']:4.0f}  (today's level {b['rate']:7.0f})", flush=True)
        json.dump(res, open("continuing_v10_price.json", "w"), indent=0)
