import json, firms_v3 as FV, pathfirm as PF
from multiprocessing import Pool
def job(a):
    tag, name, size, m, k, L, X1, X, data = a
    F = FV.cfd_firms(size)[name]
    r = PF.evaluate(F, data=data, m=m, L=L, k=k, X1=X1, X=X, n=10000, seed=31)
    return dict(tag=tag, firm=name, size=size, m=m, k=k, L=L, X1=X1, X=X, data=data, fee=F["fee"],
                **{x: float(r[x]) for x in ("EV", "CI", "days", "EV_month", "EV_month_CI", "P")})
J = []
B = dict(name="FTMO 2-Step", size=100_000, m=0.75, k=5, L=1500, X1=10000, X=10000)
def add(tag, data="synth", **kw):
    c = dict(B); c.update(kw); J.append((tag, c["name"], c["size"], c["m"], c["k"], c["L"], c["X1"], c["X"], data))
add("base"); add("base", data="real")
for L in (1000, 2000, 3000): add(f"L{L}", L=L)
for m in (0.5, 1.0, 1.5, 3.0): add(f"m{m}", m=m)
for k in (1, 2, 3, 4, 6, 8, 10): add(f"k{k}", k=k)
for k in (3, 4, 6, 8): add(f"k{k}", data="real", k=k)
for X1, X in ((1000, 10000), (3000, 10000), (5000, 10000), (10000, 20000)): add(f"X{X1}_{X}", X1=X1, X=X)
for size in (50_000, 200_000):
    K = size / 100_000; add(f"size{size}", size=size, L=1500 * K, X1=10000 * K, X=10000 * K)
add("1step100", name="FTMO 1-Step"); add("1step200", name="FTMO 1-Step", size=200_000, L=3000, X1=20000, X=20000)
with Pool(4) as p: R = p.map(job, J, chunksize=1)
json.dump(R, open("sens_v32.json", "w"), indent=0)
for r in R: print(f"{r['tag']:12s} {r['data']:5s} {r['firm'][:12]:12s} {r['size']:>7} EV={r['EV']:6.0f} d={r['days']:5.1f} EV/mo={r['EV_month']:6.0f}±{r['EV_month_CI']:3.0f} P={r['P']:.3f}")
