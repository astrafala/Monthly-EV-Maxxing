"""Run whole per-person portfolios in lockstep over many independent price paths."""
import json, sys, math, collections
import numpy as np
from multiprocessing import Pool
import lockstep as LS

DAY = 24.0
def S(firm, kind="cfd", n=1, L=1500, k=5, X1=10000, X=10000):
    return [dict(firm=firm, kind=kind, L=L, k=k, X1=X1, X=X) for _ in range(n)]
TOP = lambda n: S("Topstep 50K", "fut", n, L=950, k=5, X1=0, X=0)
FP = "FundingPips 2-Step Flex (95%)"
def GOLD(x):
    for e in x: e["instr"] = "XAUUSD"
    return x
def SINGLES():      # firms where only one account is used (duplicate/replication rules or caps); FundedNext on gold
    return (S("The5ers High Stakes") + S("FXIFY Two-Phase") + S("GFT 2-Step Standard", X1=7000) + S("FunderPro Classic") +
            S("Maven 2-Step", X1=8000, X=8000) + GOLD(S("FundedNext Stellar 2-Step")))
def stage(slots, day):
    for x in slots: x["start_day"] = day
    return slots
PORTFOLIOS = {
  "FTMO only (4 x 100K)": S("FTMO 2-Step", n=4),
  "One account per firm (11 firms)": (S("FTMO 2-Step") + S(FP, X1=12000, X=12000) + S("Alpha Capital Pro 10%") +
      S("BrightFunded 2-Step Classic") + S("Blue Guardian 2-Step") + SINGLES()),
  "Two per firm where copying is allowed (16 accounts)": (S("FTMO 2-Step", n=2) + S(FP, n=2, X1=12000, X=12000) +
      S("Alpha Capital Pro 10%", n=2) + S("BrightFunded 2-Step Classic", n=2) + S("Blue Guardian 2-Step", n=2) + SINGLES()),
  "Full caps, rules-strict (25 accounts)": (S("FTMO 2-Step", n=4) + S(FP, n=4, X1=12000, X=12000) + S("Alpha Capital Pro 10%", n=3) +
      S("BrightFunded 2-Step Classic", n=4) + S("Blue Guardian 2-Step", n=4) + SINGLES()),
  "Full caps, staged start (25 accounts)": (stage(S("FTMO 2-Step", n=4), 0) + stage(S(FP, n=4, X1=12000, X=12000) + S("The5ers High Stakes"), 30) +
      stage(GOLD(S("FundedNext Stellar 2-Step")) + S("Alpha Capital Pro 10%", n=3), 60) +
      stage(S("BrightFunded 2-Step Classic", n=4) + S("Blue Guardian 2-Step", n=4) + S("FunderPro Classic"), 90) +
      stage(S("FXIFY Two-Phase") + S("GFT 2-Step Standard", X1=7000) + S("Maven 2-Step", X1=8000, X=8000), 120)),
}

def life(args):
    pname, data, seed = args
    slots = PORTFOLIOS[pname]
    if not data.startswith("synth"):
        slots = [dict(s, instr=None) if s.get("instr") == "XAUUSD" else s for s in slots]
    ledger, st = LS.run_life(slots, data=data, seed=seed, rule="trend5")
    ledger.sort()
    cum = 0.0; trough = 0.0; path = []
    for (t, sid, kind, cash) in ledger:
        if t > 12 * 30.44 * DAY: break
        cum += cash; trough = min(trough, cum)
    m = LS.monthly(ledger)
    firm_of = [s["firm"] for s in slots]
    breaches = collections.Counter(); payouts = collections.Counter(); buys = collections.Counter()
    for (t, sid, kind, cash) in ledger:
        if t > 12 * 30.44 * DAY: continue
        if kind.endswith("_fail") or kind == "funded_end": breaches[firm_of[sid]] += 1
        if kind == "payout": payouts[firm_of[sid]] += cash
        if kind == "buy": buys[firm_of[sid]] += 1
    tl = st["trade_log"]
    days = collections.Counter(int(e // 24) for e, sid in tl)
    entry_events = collections.Counter(int(e // 24) for e in set(e for e, sid in tl))
    busy = [v for v in days.values()]
    return dict(p=pname, data=data, seed=seed, monthly=m.tolist(), trough=trough, conflicts=st["conflicts"],
                breaches=dict(breaches), payouts=dict(payouts), buys=dict(buys),
                orders_per_trading_day=float(np.mean(busy)) if busy else 0.0,
                orders_p90=float(np.percentile(busy, 90)) if busy else 0.0,
                entry_bars_per_day=float(np.mean(list(entry_events.values()))) if entry_events else 0.0)

if __name__ == "__main__":
    which = sys.argv[1:] or list(PORTFOLIOS)
    J = []
    for p in which:
        for sd in range(21, 29):
            for j in range(25): J.append((p, f"synth{sd}", sd * 100 + j))
        for j in range(40): J.append((p, "real", 9000 + j))
    with Pool(4) as pool:
        R = pool.map(life, J, chunksize=2)
    json.dump(R, open("lockstep_portfolio_v32.json", "w"))
    for p in which:
        for dsel in ("synth", "real"):
            rs = [r for r in R if r["p"] == p and r["data"].startswith(dsel)]
            M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1)
            print(f"== {p} [{dsel}] lives={len(rs)} conflicts={sum(r['conflicts'] for r in rs)}")
            print("   mean monthly cash:", M.mean(0).round(0).tolist())
            print("   EV/month (12-mo avg) %.0f, months 3-12 avg %.0f" % (M.mean(), M[:, 2:].mean()))
            print("   P(ahead) 1/2/3/6/12 m:", [round(float(np.mean(C[:, h - 1] > 0)), 2) for h in (1, 2, 3, 6, 12)])
            print("   12m cash p05/p50/p95:", np.percentile(C[:, 11], [5, 50, 95]).round(0).tolist())
            tr = np.array([r["trough"] for r in rs]); print("   trough p50/p05:", np.percentile(tr, [50, 5]).round(0).tolist())
            br = collections.Counter(); 
            for r in rs:
                for f, v in r["breaches"].items(): br[f] += v
            print("   breaches per firm per month:", {f: round(v / len(rs) / 12, 1) for f, v in br.items()})
            print("   order tickets per trading day mean %.1f (p90 %.1f); distinct entry times per day %.1f" % (
                np.mean([r["orders_per_trading_day"] for r in rs]), np.mean([r["orders_p90"] for r in rs]), np.mean([r["entry_bars_per_day"] for r in rs])))
