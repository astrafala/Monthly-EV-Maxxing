"""
One 'slot' = attempts run back to back for 12 months (a new evaluation is bought as soon as the previous
attempt ends: failed evaluation, or funded account lost). Cash flows: fee (and activation) at purchase,
payouts at their dates. Output: cumulative net cash at 1, 3, 6, 12 months, the worst point (bankroll needed),
for each firm at its best settings.
"""
import json, sys, random, math
import numpy as np
from multiprocessing import Pool
import acct_mc as A, pathfirm as PF, firms_v3 as FV

H = [1, 2, 3, 6, 9, 12]

def slot(args):
    kind, name, size, instr, m, k, L, X1, X, seed = args
    F = FV.cfd_firms(size)[name] if kind == "cfd" else FV.futures_firms()[name]
    rng = random.Random(seed)
    tr = PF.PathTrader(instr, "synth", m, L, k, rng)
    clock = rng.random() * A.DAY; t_end = 365.25 * A.DAY
    flows = []
    while clock < t_end:
        t0 = clock; ok_all = True
        flows.append((clock, -F["fee"]))
        for st in F["phases"]:
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            if not ok: ok_all = False; break
        if F["monthly"]:
            months = max(1, math.ceil((clock - t0) / (30 * A.DAY)))
            for j in range(1, months): flows.append((t0 + 30 * A.DAY * j, -F["fee"]))
        if not ok_all: continue
        if F.get("activation"): flows.append((clock, -F["activation"]))
        A.PAYLOG = []
        paid, clock, tfirst, npay = A.run_funded(F["funded"], tr, rng, F, clock, X1, X)
        flows += A.PAYLOG; A.PAYLOG = None
    flows.sort()
    out = {}
    cum = 0.0; worst = 0.0; i = 0
    for h in H:
        tlim = h * 30.44 * A.DAY
        while i < len(flows) and flows[i][0] <= tlim:
            cum += flows[i][1]; worst = min(worst, cum); i += 1
        out[h] = cum
    out["worst"] = worst
    return out

if __name__ == "__main__":
    best = json.load(open(sys.argv[1])); n = int(sys.argv[2])
    res = {}
    with Pool(4) as p:
        for b in best:
            J = [(b["kind"], b["firm"], b["size"], b["instr"], b["m"], b["k"], b["L"], b["X1"], b["X"], 1000 + s) for s in range(n)]
            R = p.map(slot, J, chunksize=20)
            res[b["firm"]] = {str(h): [r[h] for r in R] for h in H}
            res[b["firm"]]["worst"] = [r["worst"] for r in R]
            r12 = np.array(res[b["firm"]]["12"])
            print(f"{b['firm'][:34]:34s} mean 12m {r12.mean():8.0f}  P(ahead) 1m {np.mean(np.array(res[b['firm']]['1'])>0):.2f} "
                  f"3m {np.mean(np.array(res[b['firm']]['3'])>0):.2f} 6m {np.mean(np.array(res[b['firm']]['6'])>0):.2f} 12m {np.mean(r12>0):.2f} "
                  f"worst med {np.median(res[b['firm']]['worst']):7.0f} p05 {np.percentile(res[b['firm']]['worst'],5):8.0f}", flush=True)
    json.dump(res, open("timeline_v3.json", "w"))
