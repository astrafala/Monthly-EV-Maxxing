"""Per-firm results for the programmes added in version 5 (same method as final_v3.py, rule sets from firms_v5).
Each setting may name its own instrument; "tag" distinguishes several settings of one programme."""
import json, sys
from multiprocessing import Pool
import random
import firms_v5 as F5, pathfirm as PF
from final_v3 import summarize

def firm(b):
    F = F5.cfd_firms(b["size"])[b["firm"]] if b["kind"] == "cfd" else F5.futures_firms()[b["firm"]]
    return dict(F, **b["override"]) if b.get("override") else F

def job(a):
    b, data, seed, n = a
    F = firm(b); rng = random.Random(seed)
    R = [PF.attempt(F, b["instr"], data, b["m"], b["L"], b["k"], b["X1"], b["X"], rng) for _ in range(n)]
    return b.get("tag", b["firm"]), data, R

if __name__ == "__main__":
    best = json.load(open(sys.argv[1]))
    J = []
    for b in best:
        for s in range(4): J.append((b, "synth", 100 + s, 6000))
        if b.get("real", True): J.append((b, "real", 200, 8000))
    with Pool(4) as p:
        out = p.map(job, J, chunksize=1)
    res = {}
    for b in best:
        tag = b.get("tag", b["firm"]); F = firm(b)
        Rs = sum([R for t, d, R in out if t == tag and d == "synth"], [])
        Rr = sum([R for t, d, R in out if t == tag and d == "real"], [])
        res[tag] = dict(setting=b, fee=F["fee"], activation=F.get("activation", 0), monthly=F["monthly"],
                        synth=summarize(F, Rs), real=summarize(F, Rr) if Rr else None)
        s, r = res[tag]["synth"], res[tag]["real"]
        print(f"{tag[:44]:44s} synth EV={s['EV']:6.0f}±{s['EV_CI']:3.0f} d={s['days']:5.1f} EV/mo={s['EV_month']:5.0f}±{s['EV_month_CI']:3.0f} "
              f"P={s['P']:.3f} Vf={s['Vf']:5.0f} t1={s['t_first_med'] or 0:4.1f}"
              + (f" | real EV/mo={r['EV_month']:5.0f}±{r['EV_month_CI']:3.0f}" if r else ""), flush=True)
    json.dump(res, open(sys.argv[2], "w"), indent=1)
