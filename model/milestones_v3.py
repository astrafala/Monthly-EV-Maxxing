import json, random, numpy as np
import acct_mc as A, pathfirm as PF, firms_v3 as FV
F = FV.cfd_firms()["FTMO 2-Step"]
rng = random.Random(21); rows = []
for _ in range(8000):
    tr = PF.PathTrader("US100", "synth", 0.75, 1500, 5, rng)
    clock = rng.random() * A.DAY; t0 = clock; rec = dict(p1=None, p2=None, pass1=False, pass2=False, first=None, end=None, npay=0, paid=0.0)
    ok, clock = A.run_stage(F["phases"][0], tr, rng, F, clock); rec["p1"] = (clock - t0) / 24; rec["pass1"] = ok
    if ok:
        ok, clock = A.run_stage(F["phases"][1], tr, rng, F, clock); rec["p2"] = (clock - t0) / 24; rec["pass2"] = ok
        if ok:
            A.PAYLOG = []
            paid, c2, tf, npay = A.run_funded(F["funded"], tr, rng, F, clock, 10000, 10000)
            rec.update(first=(A.PAYLOG[0][0] - t0) / 24 if A.PAYLOG else None, end=(c2 - t0) / 24, npay=npay, paid=paid)
            A.PAYLOG = None
    rows.append(rec)
def med(xs): xs = [x for x in xs if x is not None]; return (float(np.median(xs)), float(np.percentile(xs, 25)), float(np.percentile(xs, 75)), len(xs))
out = dict(
    P1=float(np.mean([r["pass1"] for r in rows])), P2_given_1=float(np.mean([r["pass2"] for r in rows if r["pass1"]])),
    p1_day=med([r["p1"] for r in rows]), p1_fail_day=med([r["p1"] for r in rows if not r["pass1"]]),
    p2_day=med([r["p2"] for r in rows if r["pass1"]]), funded_day=med([r["p2"] for r in rows if r["pass2"]]),
    first_pay_day=med([r["first"] for r in rows]), end_day=med([r["end"] for r in rows if r["pass2"]]),
    npay_funded=float(np.mean([r["npay"] for r in rows if r["pass2"]])),
    share_funded_paid=float(np.mean([r["npay"] > 0 for r in rows if r["pass2"]])),
    paid_p50=float(np.median([r["paid"] for r in rows if r["pass2"]])), paid_p75=float(np.percentile([r["paid"] for r in rows if r["pass2"]], 75)),
    share_zero_pay=float(np.mean([r["paid"] == 0 for r in rows if r["pass2"]])))
print(json.dumps(out, indent=1)); json.dump(out, open("milestones_v32.json", "w"), indent=1)
