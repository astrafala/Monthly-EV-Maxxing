"""Which market an independent account (one that must not repeat the Nasdaq trades) should trade:
FundedNext Stellar 2-Step rules, the plan's settings, 4 x 6,000 synthetic attempts per market and stop size."""
import json
from multiprocessing import Pool
import firms_v5 as F5, pathfirm as PF

def job(a):
    instr, m, seed = a
    F = F5.cfd_firms()["FundedNext Stellar 2-Step v5"]
    r = PF.evaluate(F, instr, "synth", m, 1500, 5, 10000, 10000, 6000, seed, 1.0, "random")
    return instr, m, seed, r["EV_month"], r["P"]

if __name__ == "__main__":
    CASES = [("US100", .75), ("USDJPY", .75), ("USDJPY", 1.0), ("XAUUSD", .75), ("US500", .75), ("EURUSD", 1.0), ("GBPUSD", 1.0)]
    J = [(i, m, s) for (i, m) in CASES for s in (101, 102, 103, 104)]
    with Pool(2) as p: R = p.map(job, J, chunksize=1)
    out = []
    for (i, m) in CASES:
        v = [r[3] for r in R if r[0] == i and r[1] == m]
        out.append(dict(instr=i, m=m, EV_month=sum(v) / len(v), P=sum(r[4] for r in R if r[0] == i and r[1] == m) / len(v)))
        print(i, m, round(out[-1]["EV_month"]), round(out[-1]["P"], 3))
    json.dump(out, open("instr_v5.json", "w"), indent=1)
