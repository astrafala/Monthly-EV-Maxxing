import json, random, math, sys
import numpy as np
import acct_mc as A
from optimize import point
F = A.firm_defs()
def one(firm, pt, L, k, X1, X, rng):
    tr = A.Trader(pt, L, k, rng); clock = rng.random() * 24; t0 = clock; marks = []
    for st in firm["phases"]:
        ok, clock = A.run_stage(st, tr, rng, firm, clock)
        marks.append((clock - t0) / 24)
        if not ok: return dict(ok=False, marks=marks, end=(clock - t0) / 24, cash=-firm["fee"], tfirst=None)
    paid, clock, tfirst, npay = A.run_funded(firm["funded"], tr, rng, firm, clock, X1, X)
    return dict(ok=True, marks=marks, end=(clock - t0) / 24, cash=paid - firm["fee"],
                tfirst=(tfirst - t0) / 24 if tfirst else None, npay=npay)
def slot_path(firm, pt, L, k, X1, X, rng, months=12):
    """one account slot: buy a new attempt as soon as the previous ends; cash at month marks
    (fee at purchase; all payouts booked at the end of the attempt: conservative timing)"""
    t = 0.0; events = []
    while t < months * 30.44:
        r = one(firm, pt, L, k, X1, X, rng)
        events.append((t, -firm["fee"])); events.append((t + r["end"], r["cash"] + firm["fee"]))
        t += r["end"]
    out = []
    for mth in (1, 3, 6, 12):
        out.append(sum(v for (tt, v) in events if tt <= mth * 30.44))
    return out
if __name__ == "__main__":
    firm_name = sys.argv[1] if len(sys.argv) > 1 else "FTMO 2-Step"
    pt = point("US100", 0.75, 3); rng = random.Random(21)
    rs = [one(F[firm_name], pt, 1500, 3, 1000, 10000, rng) for _ in range(6000)]
    p1 = [r["marks"][0] for r in rs if len(r["marks"]) >= 1 and (r["ok"] or len(r["marks"]) > 1)]
    fail1 = [r["end"] for r in rs if not r["ok"] and len(r["marks"]) == 1]
    p2 = [r["marks"][1] for r in rs if len(r["marks"]) > 1 and (r["ok"])]
    fund = [r for r in rs if r["ok"]]
    out = dict(firm=firm_name,
        P1_pass_day_med=float(np.median(p1)), P1_fail_day_med=float(np.median(fail1)),
        funded_day_med=float(np.median(p2)) if p2 else None,
        first_pay_med=float(np.median([r["tfirst"] for r in fund if r["tfirst"]])),
        first_pay_p25=float(np.percentile([r["tfirst"] for r in fund if r["tfirst"]], 25)),
        first_pay_p75=float(np.percentile([r["tfirst"] for r in fund if r["tfirst"]], 75)),
        npay_mean=float(np.mean([r["npay"] for r in fund])), end_funded_med=float(np.median([r["end"] for r in fund])),
        paid_given_funded=float(np.mean([r["cash"] + F[firm_name]["fee"] for r in fund])),
        P_funded=len(fund) / len(rs))
    paths = np.array([slot_path(F[firm_name], pt, 1500, 3, 1000, 10000, rng) for _ in range(2000)])
    out["slot_months"] = [1, 3, 6, 12]
    out["slot_mean"] = paths.mean(0).tolist(); out["slot_p_ahead"] = (paths > 0).mean(0).tolist()
    out["slot_p10"] = np.percentile(paths, 10, axis=0).tolist(); out["slot_p90"] = np.percentile(paths, 90, axis=0).tolist()
    out["slot_median"] = np.median(paths, axis=0).tolist()
    print(json.dumps(out, indent=1)); json.dump(out, open(f"timeline_{firm_name.split()[0]}.json", "w"))
