"""Version 5 portfolios: firms grouped by reliability tier (firms_v5.TIER), the added programmes, and a futures layer.
Same lockstep method as lockstep_portfolio.py: one shared price path and calendar, shared direction per market group."""
import json, sys, collections
import numpy as np
from multiprocessing import Pool
import lockstep as LS
import lockstep_portfolio as LP
from firms_v5 import TIER, firm_of

DAY = 24.0
def S(firm, n=1, size=100_000, kind="cfd", instr=None, m=None, k=5, X=None, override=None, L=None):
    e = dict(firm=firm, kind=kind, size=size, L=L or 0.015 * size, k=k, X1=X or 0.10 * size, X=X or 0.10 * size)
    if instr: e["instr"] = instr
    if m: e["m"] = m
    if override: e["override"] = override
    return [dict(e) for _ in range(n)]

# rule sets as re-checked on 4 October 2026 (firms_v5); version 4's own entries are kept for the comparison rows
FP = "FundingPips 2-Step Flex (85%) v5"
def THE5ERS_ALL():
    return (S("The5ers High Stakes") + S("The5ers High Stakes 25K", size=25_000) + S("The5ers High Stakes 10K", 3, 10_000) +
            S("The5ers High Stakes 5K", 3, 5_000) + S("The5ers High Stakes 2.5K", 3, 2_500))
def TIER_A(small=False):
    return (S("FTMO 2-Step", 4) + S(FP, 4, X=12_000) + (THE5ERS_ALL() if small else S("The5ers High Stakes")) +
            S("FXIFY Two Phase Classic (100%, 30 days)") + S("FundedNext Stellar 2-Step v5", instr="XAUUSD"))
def TIER_B():
    return S("Fintokei ProTrader", 4) + S("Hola Prime 2-Step Prime (bi-weekly 80%)", 2, instr="USDJPY")
D_FIRMS = [("Alpha Capital Pro 10%", 3, None), ("BrightFunded 2-Step Classic v5", 4, None), ("Blue Guardian 2-Step v5", 4, None),
           ("GFT 2-Step Standard v5", 1, 6_000), ("FunderPro Classic v5", 1, None), ("Maven 2-Step", 1, 8_000)]
def TIER_D(single=False):
    out = []
    for f, n, X1 in D_FIRMS:
        sl = S(f, 1 if single else n, X=8_000 if f == "Maven 2-Step" else None)
        for s in sl:
            if X1: s["X1"] = X1
        out += sl
    return out
def FUTURES():
    return (S("Topstep 50K", 5, 50_000, "fut", L=950, X=0) +
            S("Apex 50K EOD", 20, 50_000, "fut", m=0.5, k=2, L=950, X=0, override=dict(fee=55, activation=99)))
def _fix(slots):
    for s in slots:
        if s["kind"] == "fut": s["X1"] = s["X"] = 0
    return slots
V4C = {"FundingPips 2-Step Flex (95%)": FP, "FXIFY Two-Phase": "FXIFY Two Phase Classic (100%, 30 days)",
       "FundedNext Stellar 2-Step": "FundedNext Stellar 2-Step v5", "GFT 2-Step Standard": "GFT 2-Step Standard v5",
       "FunderPro Classic": "FunderPro Classic v5", "BrightFunded 2-Step Classic": "BrightFunded 2-Step Classic v5",
       "Blue Guardian 2-Step": "Blue Guardian 2-Step v5"}
def corrected(slots):
    out = []
    for s in slots:
        s = dict(s); s["firm"] = V4C.get(s["firm"], s["firm"])
        if s["firm"] == FP: s["X1"] = s["X"] = 12_000
        if s["firm"] == "GFT 2-Step Standard v5": s["X1"] = 6_000
        out.append(s)
    return out

PORTFOLIOS = {
    "Tier A (5 firms, 11 accounts)": TIER_A(),
    "Tier A + B (7 firms, 17 accounts)": TIER_A() + TIER_B(),
    "Tier A + B + one account at each tier-D firm (13 firms, 23 accounts)": TIER_A() + TIER_B() + TIER_D(True),
    "The same + The5ers small accounts (13 firms, 33 accounts)": TIER_A(True) + TIER_B() + TIER_D(True),
    "All tiers at full caps (13 firms, 31 accounts)": TIER_A() + TIER_B() + TIER_D(),
    "Tier A + B + futures (9 firms, 42 accounts)": _fix(TIER_A() + TIER_B() + FUTURES()),
    "Version 4 one per firm (11 firms)": [dict(s) for s in LP.PORTFOLIOS["One account per firm (11 firms)"]],
    "Version 4 full caps (11 firms, 25 accounts)": [dict(s) for s in LP.PORTFOLIOS["Full caps, rules-strict (25 accounts)"]],
    "Version 4 one per firm, rules corrected (11 firms)": corrected(LP.PORTFOLIOS["One account per firm (11 firms)"]),
    "Version 4 full caps, rules corrected (11 firms, 25 accounts)": corrected(LP.PORTFOLIOS["Full caps, rules-strict (25 accounts)"]),
}
LP.PORTFOLIOS.update(PORTFOLIOS)

def life(args):
    pname, data, seed = args
    slots = PORTFOLIOS[pname]
    if not data.startswith("synth"):         # real path: the gold and yen accounts are mapped to the Nasdaq
        slots = [dict(s, instr=None, m=None) if s.get("instr") in ("XAUUSD", "USDJPY") else s for s in slots]
    ledger, st = LS.run_life(slots, data=data, seed=seed, rule="trend5")
    ledger.sort()
    cum = 0.0; trough = 0.0
    for (t, sid, kind, cash) in ledger:
        if t > 12 * 30.44 * DAY: break
        cum += cash; trough = min(trough, cum)
    m = LS.monthly(ledger)
    names = [s["firm"] for s in slots]
    breaches = collections.Counter(); payouts = collections.Counter(); buys = collections.Counter()
    for (t, sid, kind, cash) in ledger:
        if t > 12 * 30.44 * DAY: continue
        f = firm_of(names[sid])
        if kind.endswith("_fail") or kind == "funded_end": breaches[f] += 1
        if kind == "payout": payouts[f] += cash
        if kind == "buy": buys[f] += 1
    led = [(t, firm_of(names[sid]), kind, cash) for (t, sid, kind, cash) in ledger if t <= 12 * 30.44 * DAY]
    tl = st["trade_log"]; days = collections.Counter(int(e // 24) for e, sid in tl)
    return dict(p=pname, data=data, seed=seed, monthly=m.tolist(), trough=trough, conflicts=st["conflicts"],
                breaches=dict(breaches), payouts=dict(payouts), buys=dict(buys), refusal=refusals(led, seed),
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
    out = "lockstep_portfolio_v5.json"
    if args and args[0].startswith("--out="): out = args.pop(0)[6:]
    which = args or list(PORTFOLIOS)
    J = []
    for p in which:
        for sd in range(21, 29):
            for j in range(25): J.append((p, f"synth{sd}", sd * 100 + j))
        for j in range(40): J.append((p, "real", 9000 + j))
    with Pool(4) as pool:
        R = pool.map(life, J, chunksize=2)
    json.dump(R, open(out, "w"))
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
            br = collections.Counter(); po = collections.Counter()
            for r in rs:
                for f, v in r["breaches"].items(): br[f] += v
                for f, v in r["payouts"].items(): po[f] += v
            print("   failed accounts per firm per month:", {f: round(v / len(rs) / 12, 1) for f, v in br.items()})
            print("   payouts per firm per month:", {f: round(v / len(rs) / 12) for f, v in po.items()})
            print("   order tickets per trading day %.1f" % np.mean([r["orders_per_trading_day"] for r in rs]))
            for sc in SCEN:
                Q = np.array([r["refusal"][sc] for r in rs])
                print(f"   refusals '{sc}': EV/month (12-mo avg) {Q.mean():.0f}, months 3-12 avg {Q[:, 2:].mean():.0f}", flush=True)
