"""Value of a fee discount: the same attempts (common random numbers) priced at the list fee and at 10% off.
The refund, where a firm gives one, is the amount actually paid, so it shrinks with the discount too."""
import json, copy, random
from multiprocessing import Pool
import firms_v5 as F5, pathfirm as PF

SET = [("FTMO 2-Step", "US100", .75, 10_000), ("FundingPips 2-Step Flex (85%) v5", "US100", .75, 12_000),
       ("The5ers High Stakes", "US100", .75, 10_000), ("FXIFY Two Phase Classic (100%, 30 days)", "US100", .75, 10_000),
       ("FundedNext Stellar 2-Step v5", "XAUUSD", .75, 10_000), ("Fintokei ProTrader", "US100", .75, 10_000),
       ("Hola Prime 2-Step Prime (bi-weekly 80%)", "USDJPY", .75, 10_000), ("Alpha Capital Pro 10%", "US100", .75, 10_000),
       ("BrightFunded 2-Step Classic v5", "US100", .75, 10_000), ("Blue Guardian 2-Step v5", "US100", .75, 10_000),
       ("FunderPro Classic v5", "US100", .75, 10_000), ("Maven 2-Step", "US100", .75, 8_000), ("GFT 2-Step Standard v5", "US100", .75, 10_000)]

def job(a):
    name, instr, m, X, disc, seed = a
    F = copy.deepcopy(F5.cfd_firms()[name])
    F["fee"] *= (1 - disc); F["funded"]["refund"] *= (1 - disc)
    X1 = 6_000 if name.startswith("GFT") else X
    r = PF.evaluate(F, instr, "synth", m, 1500, 5, X1, X, 6000, seed, 1.0, "random")
    return name, disc, seed, r["EV_month"], r["days"]

if __name__ == "__main__":
    J = [(n, i, m, X, d, s) for (n, i, m, X) in SET for d in (0.0, 0.10) for s in (101, 102)]
    with Pool(4) as p: R = p.map(job, J, chunksize=1)
    out = {}
    for (n, i, m, X) in SET:
        base = sum(r[3] for r in R if r[0] == n and r[1] == 0.0) / 2
        off = sum(r[3] for r in R if r[0] == n and r[1] == 0.10) / 2
        fee = F5.cfd_firms()[n]["fee"]
        out[n] = dict(fee=fee, EV_month=base, EV_month_10off=off, gain_per_10pct=off - base, gain_pct=(off - base) / base)
        print(f"{n[:40]:40s} fee {fee:6.0f}  EV/mo {base:6.0f} -> {off:6.0f} at 10% off: +{off - base:4.0f} (+{100 * (off - base) / base:.1f}%)")
    json.dump(out, open("discount_v5.json", "w"), indent=1)
