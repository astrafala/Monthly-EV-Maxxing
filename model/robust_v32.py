"""(1) cost sensitivity for the plan; (2) payout-refusal sensitivity for the default portfolio (lockstep ledgers)."""
import json, random, numpy as np
from multiprocessing import Pool
import firms_v3 as FV, pathfirm as PF, lockstep as LS, lockstep_portfolio as LP
DAY = 24.0
def cost_job(a):
    name, cm, seed = a
    F = FV.cfd_firms()[name]
    X = 12000 if "Flex" in name else 10000
    r = PF.evaluate(F, data="synth", m=0.75, L=1500, k=5, X1=X, X=X, n=8000, seed=seed, cost_mult=cm)
    return name, cm, float(r["EV"]), float(r["days"]), float(r["EV_month"]), float(r["P"])
def life(j):
    slots = LP.PORTFOLIOS["One account per firm (11 firms)"]
    ledger, st = LS.run_life(slots, data=f"synth{21 + j % 8}", seed=9100 + j, rule="trend5")
    ledger.sort(); firm_of = [s["firm"] for s in slots]
    return [(t, firm_of[sid], kind, cash) for (t, sid, kind, cash) in ledger]
if __name__ == "__main__":
    J = [(n, cm, 77) for n in ("FTMO 2-Step", "FundingPips 2-Step Flex (95%)", "Blue Guardian 2-Step") for cm in (1.0, 1.5, 2.0, 3.0)]
    with Pool(4) as p: R = p.map(cost_job, J)
    out = {"cost": [dict(firm=a, cost_mult=b, EV=c, days=d, EV_month=e, P=f) for a, b, c, d, e, f in R]}
    for r in out["cost"]: print("cost", r["firm"][:28], r["cost_mult"], round(r["EV_month"]), round(r["P"], 3))
    with Pool(4) as p: lives = p.map(life, range(200))
    res = {}
    rng = random.Random(5)
    for q in (0.0, 0.02, 0.05, 0.10, 0.20):
        tot12 = []; steady = []; lost_firms = []
        for led in lives:
            for rep in range(5):
                banned = {}; m = np.zeros(12)
                for (t, f, kind, cash) in led:
                    if banned.get(f): continue
                    if kind == "payout" and rng.random() < q:
                        banned[f] = True; continue               # payout refused, account closed, no more purchases there
                    mth = int(t // (30.44 * DAY))
                    if 0 <= mth < 12: m[mth] += cash
                tot12.append(m.sum()); steady.append(m[2:].mean()); lost_firms.append(len(banned))
        res[q] = dict(year_avg=float(np.mean(tot12)) / 12, steady=float(np.mean(steady)), p_ahead12=float(np.mean(np.array(tot12) > 0)),
                      p05_12=float(np.percentile(tot12, 5)), firms_lost=float(np.mean(lost_firms)))
        print("refusal q=%.2f: first-year avg/month %.0f, months 3-12 avg %.0f, P(ahead at 12m) %.2f, 12m p05 %.0f, firms lost %.1f" % (
            q, res[q]["year_avg"], res[q]["steady"], res[q]["p_ahead12"], res[q]["p05_12"], res[q]["firms_lost"]))
    out["refusal"] = {str(k): v for k, v in res.items()}
    json.dump(out, open("robust_v32.json", "w"), indent=1)
