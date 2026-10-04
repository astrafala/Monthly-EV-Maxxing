import json, sys, itertools
from multiprocessing import Pool
import acct_mc as A

CAL = json.load(open("calib_all.json"))

def point(instr, m, k, use_bias=False):
    for g in CAL[instr]["grid"]:
        if g["m"] == m and g["k"] == k:
            e = (g["p"] * (1 + k) - 1) if use_bias else 0.0
            return dict(edge=e - g["kappa"] - g["phi"], kappa=g["kappa"], phi=g["phi"], dur=g["dur"],
                        hours=g["hours"])
    raise KeyError((instr, m, k))

def job(args):
    firm_name, futures, instr, m, k, L, X1, X, n, bias = args
    firms = A.futures_defs() if futures else A.firm_defs()
    r = A.evaluate(firms[firm_name], point(instr, m, k, bias), L=L, k=k, X1=X1, X=X, n=n, seed=11)
    r.update(firm=firm_name, instr=instr, m=m, k=k, L=L, X1=X1, X=X, n=n, bias=bias,
             hours=point(instr, m, k)["hours"])
    return r

if __name__ == "__main__":
    stage = sys.argv[1]
    jobs = []
    MS = (1, 1.5, 2, 3, 4, 6, 9); KS = (1, 2)
    if stage == "ftmo_grid":
        for instr in ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US100", "US500", "BTC_FTMO", "ETH_FTMO"):
            for m, k, L in itertools.product(MS, KS, (1000, 1500)):
                jobs.append(("FTMO 2-Step", False, instr, m, k, L, 1000, 10000, 1200, False))
    elif stage == "ftmo_fine":
        for instr in ("US100", "XAUUSD", "USDJPY", "EURUSD"):
            for m, k, L, X in itertools.product((0.5, 0.75, 1, 1.5), (1, 2, 3), (1000, 1500), (3000, 10000)):
                jobs.append(("FTMO 2-Step", False, instr, m, k, L, 1000, X, 2500, False))
    elif stage == "firms":
        for firm in ("FTMO 2-Step", "FTMO 1-Step", "FundingPips 2-Step (bi-weekly 80%)", "FundingPips 2-Step (weekly 60%)",
                     "FundedNext Stellar 2-Step", "The5ers High Stakes"):
            for instr, m, k, X in (("US100", 0.75, 3, 10000), ("US100", 0.75, 3, 3000), ("US100", 1, 2, 10000),
                                   ("XAUUSD", 1, 3, 10000), ("EURUSD", 1, 3, 10000)):
                jobs.append((firm, False, instr, m, k, 1500, 1000, X, 4000, False))
    elif stage == "crypto_grid":
        for firm, instr in (("Breakout 2-Step (crypto)", "BTC_Breakout"), ("HyroTrader 2-Step (crypto)", "BTC_Hyro")):
            for m, k, L in itertools.product((1, 1.5, 2, 3, 4, 6), KS, (1500, 3000)):
                jobs.append((firm, False, instr, m, k, L, 500, 500, 1500, False))
    elif stage == "futures_grid":
        for firm in ("Topstep 50K", "Apex 50K EOD"):
            for m, k, L in itertools.product((1, 1.5, 2, 3, 4), KS, (250, 500)):
                jobs.append((firm, True, "MNQ_fut", m, k, L, 0, 0, 2000, False))
    with Pool(4) as p:
        res = p.map(job, jobs, chunksize=1)
    json.dump(res, open(f"opt_{stage}.json", "w"), default=float)
    res.sort(key=lambda r: -r["EV_month"])
    for r in res[:25]:
        print(f"{r['firm'][:26]:26s} {r['instr']:12s} m={r['m']:<4} k={r['k']} L={r['L']:5.0f} "
              f"hrs/trade={r['hours']:6.1f} EV={r['EV']:7.0f}±{r['CI']:4.0f} days={r['days']:6.0f} "
              f"EV/mo={r['EV_month']:6.0f} Pf={r['Pf']:.2f} 1st pay(med d)={r['t_first_pay']}")
