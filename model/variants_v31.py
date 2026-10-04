import json, firms_v3 as FV, pathfirm as PF
from multiprocessing import Pool
def job(a):
    name, X1, X, seed = a
    F = FV.cfd_firms()[name]
    r = PF.evaluate(F, data="synth", m=0.75, L=1500, k=5, X1=X1, X=X, n=6000, seed=seed)
    return dict(firm=name, X1=X1, X=X, seed=seed, **{x: float(r[x]) for x in ("EV", "CI", "days", "EV_month", "EV_month_CI", "P", "Vf", "t_fund", "t_first_med")})
J = []
for seed in (101, 202):
    for name, XS in [("FundingPips 2-Step (bi-weekly 80%)", [(10000, 10000)]),
                     ("FundingPips 2-Step Flex (85%)", [(10000, 10000), (12000, 12000)]),
                     ("FundingPips 2-Step (on-demand 90%)", [(10000, 10000), (6000, 6000)]),
                     ("Alpha Capital Pro 10%", [(10000, 10000)]),
                     ("Alpha Capital Pro 10% (on-demand)", [(10000, 10000), (6000, 6000)])]:
        for X1, X in XS: J.append((name, X1, X, seed))
with Pool(3) as p: R = p.map(job, J, chunksize=1)
json.dump(R, open("v31_variants.json", "w"), indent=0)
import collections
agg = collections.defaultdict(list)
for r in R: agg[(r["firm"], r["X1"], r["X"])].append(r)
for k, rs in agg.items():
    ev = sum(r["EV"] for r in rs) / len(rs); d = sum(r["days"] for r in rs) / len(rs)
    print(f"{k[0][:36]:36s} X1={k[1]:6.0f} X={k[2]:6.0f}  EV={ev:6.0f} days={d:5.1f} EV/mo={ev/d*30.44:6.0f} P={sum(r['P'] for r in rs)/len(rs):.3f} Vf={sum(r['Vf'] for r in rs)/len(rs):6.0f} tf={sum(r['t_fund'] for r in rs)/len(rs):5.1f}")
