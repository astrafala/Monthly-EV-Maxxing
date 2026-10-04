"""
Version 6 portfolios: every account runs the setting chosen for its programme by the optimiser (opt_v6_final.json,
tag "chosen", and the "200K" / small-size rows), on one shared price path and calendar per person (lockstep.py).

Markets: Nasdaq group (shared direction) for every firm that allows it; USDJPY group for FundingPips (leverage);
gold for Hola Prime and EURUSD for FundedNext, each traded by no other account (both firms forbid copying trades from
other firms' accounts, and FundedNext forbids copying into its funded accounts).
Synthetic paths only (8 independent paths x 25 lives of 12 months); the real-history check is per programme
(optimize_v6.py final6), because the real history has no independent gold/euro/yen paths aligned with the Nasdaq.
"""
import json, sys, collections
import numpy as np
from multiprocessing import Pool
import lockstep as LS
from firms_v5 import TIER, firm_of

DAY = 24.0
FIN = json.load(open("opt_v6_final.json"))

def setting(prog, instr, size=100_000, tag=None):
    rs = [r for r in FIN if r["prog"] == prog and r["instr"] == instr and r["data"] == "synth" and r["size"] == size
          and (r["tag"] == tag if tag else r["tag"] in ("chosen", "200K") or r["tag"] in ("50K", "25K", "10K", "5K", "2K"))]
    assert len(rs) == 1, (prog, instr, size, tag, len(rs))
    return rs[0]

def S(prog, instr="US100", n=1, size=100_000, tag=None):
    r = setting(prog, instr, size, tag)
    e = dict(firm=prog, kind=r.get("kind", "cfd"), size=size, L=r["L"], k=r["k"], X1=r["X1"], X=r["X"], m=r["m"], instr=instr)
    if r.get("fee") is not None: e["fee"] = r["fee"]
    if r.get("override"): e["override"] = r["override"]
    return [dict(e) for _ in range(n)]

FTMO, FP, T5, T5N = "FTMO 2-Step", "FundingPips 2-Step Flex (85%) v6 cap", "The5ers High Stakes Classic", "The5ers High Stakes"
FX, FN, FK, HP = "FXIFY Two Phase Classic (100%, 30 days)", "FundedNext Stellar 2-Step v5", "Fintokei ProTrader", "Hola Prime 2-Step Prime (bi-weekly 80%)"
AL, BF, BG, GF, FPR, MV = ("Alpha Capital Pro 10%", "BrightFunded 2-Step Classic v5", "Blue Guardian 2-Step v5",
                           "GFT 2-Step Standard v5", "FunderPro Classic v5", "Maven 2-Step")

def FXIFY_ALL():
    return S(FX) + sum((S(FX, size=sz) for sz in (50_000, 25_000, 10_000, 5_000)), [])
def THE5ERS_SMALL():
    return (S("The5ers High Stakes 25K", size=25_000) + S("The5ers High Stakes 10K", n=3, size=10_000) +
            S("The5ers High Stakes 5K", n=3, size=5_000) + S("The5ers High Stakes 2.5K", n=3, size=2_500))
def TIER_A(ftmo200=False, fxify_small=True):
    return ((S(FTMO, n=2, size=200_000) if ftmo200 else S(FTMO, n=4)) + S(FP, "USDJPY", n=4) + S(T5) +
            (FXIFY_ALL() if fxify_small else S(FX)) + S(FN, "EURUSD", size=200_000))
def TIER_B():
    return S(FK, n=5) + S(HP, "XAUUSD", n=2)
def TIER_D_SINGLE():
    return (S(FPR, size=200_000) + S(AL, size=200_000) + S(GF, size=200_000) + S(BF) + S(BG) + S(MV))
def TIER_D_FULL():
    return (S(FPR, size=200_000) + S(AL, size=200_000) + S(AL) + S(GF, size=200_000) + S(BF, n=4) + S(BG, n=4) + S(MV))
def FUTURES():
    tp = S("Topstep 50K", "MNQ_fut", n=5, size=50_000)
    ap = S("Apex 50K EOD", "MNQ_fut", n=20, size=50_000)
    for s in tp + ap: s["X1"] = s["X"] = 0
    return tp + ap

def _n(sl): return len(sl)
PORTFOLIOS = {
    "Tier A": TIER_A(),
    "Tier A + B": TIER_A() + TIER_B(),
    "Recommended: A + B + one account at each tier-D firm": TIER_A() + TIER_B() + TIER_D_SINGLE(),
    "Recommended, FTMO as 2 x 200K": TIER_A(ftmo200=True) + TIER_B() + TIER_D_SINGLE(),
    "All firms at full caps": TIER_A() + TIER_B() + TIER_D_FULL(),
    "All firms at full caps + The5ers small accounts": TIER_A() + THE5ERS_SMALL() + TIER_B() + TIER_D_FULL(),
    "Recommended + futures (Topstep 5, Apex 20)": TIER_A() + TIER_B() + TIER_D_SINGLE() + FUTURES(),
}

def life(args):
    pname, data, seed = args
    slots = PORTFOLIOS[pname]
    ledger, st = LS.run_life(slots, data=data, seed=seed, rule="trend5")
    ledger.sort()
    H = 12 * 30.44 * DAY
    cum = 0.0; trough = 0.0
    for (t, sid, kind, cash) in ledger:
        if t > H: break
        cum += cash; trough = min(trough, cum)
    m = LS.monthly(ledger)
    names = [s["firm"] for s in slots]
    breaches = collections.Counter(); payouts = collections.Counter(); buys = collections.Counter()
    fees = collections.Counter(); requests = collections.Counter()
    for (t, sid, kind, cash) in ledger:
        if t > H: continue
        f = firm_of(names[sid])
        if kind.endswith("_fail") or kind == "funded_end": breaches[f] += 1
        if kind == "payout": payouts[f] += cash; requests[f] += 1
        if kind in ("buy", "monthly_fee", "activation"): fees[f] += cash
        if kind == "buy": buys[f] += 1
    led = [(t, firm_of(names[sid]), kind, cash) for (t, sid, kind, cash) in ledger if t <= H]
    tl = st["trade_log"]; days = collections.Counter(int(e // 24) for e, sid in tl)
    return dict(p=pname, data=data, seed=seed, monthly=m.tolist(), trough=trough, conflicts=st["conflicts"],
                trades=st["trades"], copied=st["copied"], breaches=dict(breaches), payouts=dict(payouts),
                requests=dict(requests), fees=dict(fees), buys=dict(buys), refusal=refusals(led, seed),
                orders_per_trading_day=float(np.mean(list(days.values()))) if days else 0.0)

# payout-refusal scenarios: each payout is refused with the firm's probability; after a refusal the person stops
# using that firm (no more fees or payouts there)
SCEN = {"tiered": {"A": 0.02, "B": 0.05, "D": 0.15}, "harsh": {"A": 0.05, "B": 0.10, "D": 0.30}}
def refusals(led, seed, reps=10):
    import random
    rng = random.Random(seed * 7 + 3); out = {}
    for name, q in SCEN.items():
        Ms = []
        for _ in range(reps):
            banned = set(); m = np.zeros(12)
            for (t, f, kind, cash) in led:
                if f in banned: continue
                if kind == "payout" and rng.random() < q.get(TIER.get(f, "B"), 0.05):
                    banned.add(f); continue
                mth = int(t // (30.44 * DAY))
                if 0 <= mth < 12: m[mth] += cash
            Ms.append(m)
        out[name] = np.mean(Ms, 0).tolist()
    return out

if __name__ == "__main__":
    args = sys.argv[1:]
    out = "lockstep_v6.json"
    if args and args[0].startswith("--out="): out = args.pop(0)[6:]
    lives = 25
    if args and args[0].startswith("--lives="): lives = int(args.pop(0)[8:])
    which = args or list(PORTFOLIOS)
    J = [(p, f"synth{sd}", sd * 100 + j) for p in which for sd in range(21, 29) for j in range(lives)]
    with Pool(4) as pool:
        R = pool.map(life, J, chunksize=1)
    json.dump(dict(R=R, slots={p: PORTFOLIOS[p] for p in which}), open(out, "w"))
    for p in which:
        rs = [r for r in R if r["p"] == p]
        M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1)
        print(f"== {p}: {len(PORTFOLIOS[p])} accounts, lives={len(rs)} conflicts={sum(r['conflicts'] for r in rs)}")
        print("   mean monthly cash:", M.mean(0).round(0).tolist())
        print("   EV/month (12-mo avg) %.0f ± %.0f, months 3-12 avg %.0f" % (M.mean(), 1.96 * M.mean(1).std() / len(rs) ** 0.5, M[:, 2:].mean()))
        for sc in SCEN:
            Ms = np.array([r["refusal"][sc] for r in rs]); print(f"   refusal {sc}: {Ms.mean():.0f}/month")
        print("   P(ahead) 1/2/3/6/12 m:", [round(float(np.mean(C[:, h - 1] > 0)), 2) for h in (1, 2, 3, 6, 12)])
        print("   12m cash p05/p50/p95:", np.percentile(C[:, 11], [5, 50, 95]).round(0).tolist())
        tr = np.array([r["trough"] for r in rs]); print("   trough p50/p05:", np.percentile(tr, [50, 5]).round(0).tolist())
