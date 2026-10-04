import json, sys, numpy as np
from multiprocessing import Pool
import lockstep as LS, lockstep_portfolio as LP
DAY = 24.0
def one(args):
    pname, j = args
    slots = LP.PORTFOLIOS[pname]
    ledger, st = LS.run_life(slots, data=f"synth{21 + j % 8}", seed=8000 + j, rule="trend5")
    ledger.sort()
    W = 26; cum = np.zeros(W); c = 0.0; k = 0
    for w in range(W):
        while k < len(ledger) and ledger[k][0] < (w + 1) * 7 * DAY:
            c += ledger[k][3]; k += 1
        cum[w] = c
    first_pay = min([t for (t, s, kind, cash) in ledger if kind == "payout"] or [1e9]) / DAY
    return pname, cum.tolist(), first_pay
if __name__ == "__main__":
    out = {}
    J = [(p, j) for p in ("One account per firm (11 firms)", "Full caps, staged start (25 accounts)", "FTMO only (4 x 100K)") for j in range(160)]
    with Pool(4) as pool: R = pool.map(one, J, chunksize=4)
    for p in set(r[0] for r in R):
        C = np.array([r[1] for r in R if r[0] == p]); fp = np.array([r[2] for r in R if r[0] == p])
        out[p] = dict(p10=np.percentile(C, 10, 0).tolist(), p50=np.percentile(C, 50, 0).tolist(), p90=np.percentile(C, 90, 0).tolist(),
                      ahead=(C > 0).mean(0).tolist(), first_payout_day=np.percentile(fp, [10, 50, 90]).tolist())
        print(p, "first payout day p10/50/90", np.percentile(fp, [10, 50, 90]).round(0))
        for w in (1, 2, 3, 4, 6, 8, 10, 13, 17, 26):
            print(f"   week {w:2d}: p10 {out[p]['p10'][w-1]:9.0f}  p50 {out[p]['p50'][w-1]:9.0f}  p90 {out[p]['p90'][w-1]:9.0f}  ahead {out[p]['ahead'][w-1]:.2f}")
    json.dump(out, open("weekly_v32.json", "w"), indent=0)
