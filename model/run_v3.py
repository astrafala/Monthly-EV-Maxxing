import sys, json, itertools
from multiprocessing import Pool
import firms_v3 as FV, pathfirm as PF

def job(a):
    kind, name, size, instr, data, m, k, L, X1, X, n = a
    F = FV.cfd_firms(size)[name] if kind == "cfd" else FV.futures_firms()[name]
    r = PF.evaluate(F, instr=instr, data=data, m=m, L=L, k=k, X1=X1, X=X, n=n, seed=11)
    r = {k_: (float(v) if v is not None else None) for k_, v in r.items()}
    r.update(kind=kind, firm=name, size=size, instr=instr, data=data, m=m, k=k, L=L, X1=X1, X=X, n=n,
             fee=F["fee"], activation=F.get("activation", 0))
    return r

if __name__ == "__main__":
    stage = sys.argv[1]; J = []
    if stage == "cfd":
        for name in FV.cfd_firms(100_000):
            for X1, X in [(1000, 10000), (1000, 5000), (3000, 10000), (500, 10000)]:
                J.append(("cfd", name, 100_000, "US100", "synth", 0.75, 3, 1500, X1, X, 6000))
    elif stage == "sizes":
        for size in (50_000, 100_000, 200_000):
            K = size / 100_000
            J.append(("cfd", "FTMO 2-Step", size, "US100", "synth", 0.75, 3, 1500 * K, 1000 * K, 10000 * K, 6000))
        for size in (100_000, 200_000):
            K = size / 100_000
            J.append(("cfd", "FTMO 1-Step", size, "US100", "synth", 0.75, 3, 1500 * K, 1000 * K, 10000 * K, 6000))
    elif stage == "fut":
        for name in FV.futures_firms():
            for m, k, L in itertools.product((0.75, 1.5), (1, 2, 3), (200, 350, 500)):
                J.append(("fut", name, 50_000, "MNQ_fut", "synth", m, k, L, 0, 0, 3000))
    elif stage == "fut2":
        for name in FV.futures_firms():
            for m, k, L in itertools.product((0.5, 0.75, 1.0), (2, 3), (500, 650, 800, 950)):
                J.append(("fut", name, 50_000, "MNQ_fut", "synth", m, k, L, 0, 0, 6000))
    elif stage == "cfd2":
        for name in ("FTMO 2-Step", "FundedNext Stellar 2-Step", "The5ers High Stakes", "FundingPips 2-Step (bi-weekly 80%)", "FXIFY Two-Phase"):
            for X1, X in [(3000, 15000), (5000, 10000), (5000, 20000), (3000, 20000)]:
                J.append(("cfd", name, 100_000, "US100", "synth", 0.75, 3, 1500, X1, X, 6000))
            for L in (2000, 2500, 3000):
                J.append(("cfd", name, 100_000, "US100", "synth", 0.75, 3, L, 3000, 10000, 6000))
            for m in (0.5, 1.0):
                J.append(("cfd", name, 100_000, "US100", "synth", m, 3, 1500, 3000, 10000, 6000))
    elif stage == "cfd3":
        for name in FV.cfd_firms(100_000):
            for X1, X in [(5000, 10000), (7000, 10000), (10000, 10000), (5000, 15000), (7000, 15000), (4000, 8000)]:
                J.append(("cfd", name, 100_000, "US100", "synth", 0.75, 3, 1500, X1, X, 8000))
    elif stage == "sizes2":
        for size in (50_000, 100_000, 200_000):
            K = size / 100_000
            J.append(("cfd", "FTMO 2-Step", size, "US100", "synth", 0.75, 3, 1500 * K, 10000 * K, 10000 * K, 12000))
        for size in (100_000, 200_000):
            K = size / 100_000
            J.append(("cfd", "FTMO 1-Step", size, "US100", "synth", 0.75, 3, 1500 * K, 5000 * K, 10000 * K, 12000))
    elif stage == "sens":
        for L in (1000, 1500, 2000, 3000):
            J.append(("cfd", "FTMO 2-Step", 100_000, "US100", "synth", 0.75, 3, L, 10000, 10000, 12000))
        for m in (0.5, 1.0, 1.5, 3.0):
            J.append(("cfd", "FTMO 2-Step", 100_000, "US100", "synth", m, 3, 1500, 10000, 10000, 12000))
        for k in (1, 2):
            J.append(("cfd", "FTMO 2-Step", 100_000, "US100", "synth", 0.75, k, 1500, 10000, 10000, 12000))
        for X1, X in ((1000, 10000), (3000, 10000), (5000, 10000), (10000, 20000)):
            J.append(("cfd", "FTMO 2-Step", 100_000, "US100", "synth", 0.75, 3, 1500, X1, X, 12000))
    elif stage == "real":
        best = json.load(open(sys.argv[2]))
        for b in best:
            J.append((b["kind"], b["firm"], b["size"], b["instr"], "real", b["m"], b["k"], b["L"], b["X1"], b["X"], 8000))
    elif stage == "final":
        best = json.load(open(sys.argv[2]))
        for b in best:
            for seed_n in range(4):
                J.append((b["kind"], b["firm"], b["size"], b["instr"], "synth", b["m"], b["k"], b["L"], b["X1"], b["X"], 6000))
    with Pool(4) as p:
        R = p.map(job, J, chunksize=1)
    json.dump(R, open(f"v3_{stage}.json", "w"), indent=0)
    for r in sorted(R, key=lambda r: (r["firm"], -r["EV_month"])):
        print(f"{r['firm'][:34]:34s} {r['size']:>7.0f} {r['data']:5s} m={r['m']} k={r['k']} L={r['L']:.0f} X1={r['X1']:.0f} X={r['X']:.0f} "
              f"EV={r['EV']:7.0f}±{r['CI']:4.0f} days={r['days']:5.1f} EV/mo={r['EV_month']:6.0f} P={r['P']:.3f} "
              f"Vf={r['Vf']:6.0f} tf={r['t_fund']:5.1f} slotU={r.get('EV_month_funded_slot') or 0:6.0f} t1={r['t_first_med'] or 0:5.1f}")
