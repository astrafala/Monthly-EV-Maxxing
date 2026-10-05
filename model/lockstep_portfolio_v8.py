"""
Version 8 portfolios. Every account runs the setting chosen for its programme by optimize_v8 (opt_v8_final.json), on
one shared calendar per person with the shared-direction rule inside each market group (lockstep.py). The settings are
frozen before any portfolio run, and every simulated life runs on its own new price paths (path numbers 100,000 and up for
12-month lives, 300,000 and up for 36-month lives, each market its own random stream: multi.stream_key), which no
optimisation stage used (stream_manifest_v8.json lists every stream of every stage).

Stages (python3 lockstep_portfolio_v7.py <stage>):
  main     every portfolio, 1,200 lives of 12 months
  long     the recommended plan, 800 lives of 36 months: long-run rate (months 13-36), value of open accounts at month 12
  budget   the recommended plan with a finite cash budget (purchases wait for cash), 200 lives per budget
  stress   recommended plan at cost x1.5 and x2 (full portfolio runs, paired seeds)
  corr     recommended plan with all four markets on one joint path, pairwise correlation 0.3
  news     recommended plan flat 12:00-14:00 UTC every weekday (and 08:00-09:00 on EURUSD): a bounding news proxy
  behav    FundedNext under its remedies (1% risk per trade; 7-day pause after each failed attempt)
"""
import json, sys, collections, random, math
import numpy as np
from multiprocessing import Pool
import lockstep as LS, pathfirm as PF, firms_v8 as F7, optimize_v8 as O
from firms_v8 import TIER, firm_of

LS.RULES = F7
DAY = 24.0
FIN = json.load(open("opt_v8_final.json"))

def row(prog, instr, size=100_000):
    rs = [r for r in FIN if r["prog"] == prog and r["instr"] == instr and r["size"] == size]
    assert len(rs) == 1, (prog, instr, size, len(rs))
    return rs[0]

def best_instr(prog, allowed):
    rs = [r for r in FIN if r["prog"] == prog and r["size"] == 100_000 and r["instr"] in allowed]
    return max(rs, key=lambda r: r["EV_month"])["instr"] if rs else None

def S(prog, instr, n=1, size=100_000):
    r = row(prog, instr, size)
    e = dict(firm=prog, kind=r.get("kind", "cfd"), size=size, L=r["L"], k=r["k"], X1=r["X1"], X=r["X"], m=r["m"], instr=instr,
             ev=r["EV_month"], fee_list=r.get("fee"))
    if r.get("fee") is not None: e["fee"] = r["fee"]
    if r.get("override"): e["override"] = r["override"]
    if e["kind"] == "cfd": e["lev"] = O.lev_tuple(firm_of(prog), instr)
    return [dict(e) for _ in range(n)]

# ---------------------------------------------------------------- which programme and market per firm
def pick(progs, allowed):
    """the programme (of alternatives at one firm) and market with the highest EV per month"""
    best = None
    for p in progs:
        i = best_instr(p, allowed)
        if i is None: continue
        v = row(p, i)["EV_month"]
        if best is None or v > best[2]: best = (p, i, v)
    return best

FP = pick(["FundingPips 2-Step Flex (80%)", "FundingPips 2-Step Flex (95%)"], ["USDJPY", "EURUSD"])
T5 = pick(["The5ers High Stakes", "The5ers High Stakes Classic"], ["US100"])
FX = pick(["FXIFY Two Phase Classic (100%, 30 days)", "FXIFY Two Phase Classic (80%)"], ["US100"])
GF = pick(["GFT 2-Step Standard"], ["US100", "USDJPY"])
FPR = pick(["FunderPro Classic"], ["US100", "USDJPY"])
# FundedNext and Hola Prime may not trade copies of other firms' accounts: each gets a market no other account trades
_fn = {i: row("FundedNext Stellar 2-Step", i)["EV_month"] for i in ("EURUSD", "XAUUSD")}
_hp = {i: row("Hola Prime 2-Step Prime (bi-weekly 80%)", i)["EV_month"] for i in ("EURUSD", "XAUUSD")}
FN_I, HP_I = max((("EURUSD", "XAUUSD"), ("XAUUSD", "EURUSD")), key=lambda a: _fn[a[0]] + 2 * _hp[a[1]])
FN_SIZE = 200_000 if row("FundedNext Stellar 2-Step", FN_I, 200_000)["EV_month"] > row("FundedNext Stellar 2-Step", FN_I)["EV_month"] else 100_000

def pos(prog, instr, size=100_000):
    return row(prog, instr, size)["EV_month"] > 0

def one_big(prog, instr):
    """a firm where one account is the plan: the larger size if it is worth more"""
    try:
        b = row(prog, instr, 200_000)
    except AssertionError:
        b = None
    s = row(prog, instr)
    if b and b["EV_month"] > s["EV_month"]: return S(prog, instr, size=200_000)
    return S(prog, instr)

FXIFY_SIZES = (50_000, 25_000, 10_000, 5_000)
def FXIFY_ALL():
    out = S(FX[0], FX[1])
    if FX[0] == "FXIFY Two Phase Classic (100%, 30 days)" and FX[1] == "US100":
        out += sum((S(FX[0], FX[1], size=sz) for sz in FXIFY_SIZES if pos(FX[0], FX[1], sz)), [])
    return out
def THE5ERS_SMALL():
    """The5ers' small accounts, all on the New High Stakes programme (10% / 5%, New's fees, its own chosen setting) up to
    New's limits: three each of 2.5K, 5K and 10K and one 25K. The one 50K/100K account allowed across Classic and New
    together is the plan's 100K account. Classic's own small slots (one 2.5K, one 5K, one 10K or 25K) are not used:
    their fees could not be read from the firm's pages (review of version 7, finding 4: the version 7 text described
    these accounts as scaled Classic accounts; the model already used the New contract)."""
    out = []
    for sz, n in ((25_000, 1), (10_000, 3), (5_000, 3), (2_500, 3)):
        p = O.THE5ERS_SMALL[sz]
        if pos(p, "US100", sz): out += S(p, "US100", n=n, size=sz)
    return out
def TIER_A(ftmo200=False):
    return ((S("FTMO 2-Step", "US100", n=2, size=200_000) if ftmo200 else S("FTMO 2-Step", "US100", n=4)) + S(FP[0], FP[1], n=4) +
            S(T5[0], "US100") + FXIFY_ALL() + S("FundedNext Stellar 2-Step", FN_I, size=FN_SIZE))
def TIER_B():
    return S("Fintokei ProTrader", "US100", n=5) + S("Hola Prime 2-Step Prime (bi-weekly 80%)", HP_I, n=2)
TIER_D = [("FunderPro Classic", FPR[1]), ("Alpha Capital Pro 10%", "US100"), ("GFT 2-Step Standard", GF[1]),
          ("BrightFunded 2-Step Classic", "US100"), ("Blue Guardian 2-Step", "US100"), ("Maven 2-Step", "US100")]
def TIER_D_SINGLE():
    return sum((one_big(p, i) for p, i in TIER_D if pos(p, i)), [])
def TIER_D_FULL():
    out = []
    for p, i in TIER_D:
        if not pos(p, i): continue
        if p == "Alpha Capital Pro 10%": out += one_big(p, i) + S(p, i)
        elif p in ("BrightFunded 2-Step Classic", "Blue Guardian 2-Step"): out += S(p, i, n=4)
        else: out += one_big(p, i)
    return out
def FUTURES():
    out = []
    for p, n in (("Topstep 50K", 5), ("Apex 50K EOD", 20)):
        if pos(p, "MNQ_fut", 50_000): out += S(p, "MNQ_fut", n=n, size=50_000)
    return out

REC = "Recommended: A + B + one account at each tier-D firm"
PORTFOLIOS = {
    "Tier A": TIER_A(),
    "Tier A + B": TIER_A() + TIER_B(),
    REC: TIER_A() + TIER_B() + TIER_D_SINGLE(),
    "Recommended, FTMO as 2 x 200K": TIER_A(ftmo200=True) + TIER_B() + TIER_D_SINGLE(),
    "All firms at full caps": TIER_A() + TIER_B() + TIER_D_FULL(),
    "All firms at full caps + The5ers small accounts": TIER_A() + TIER_B() + TIER_D_FULL() + THE5ERS_SMALL(),
    "Recommended + futures": TIER_A() + TIER_B() + TIER_D_SINGLE() + FUTURES(),
}

# ---------------------------------------------------------------- one life
SCEN = {"tiered": {"A": 0.02, "B": 0.05, "D": 0.15}, "harsh": {"A": 0.05, "B": 0.10, "D": 0.30}}
def refusals(led, seed, months, reps=10):
    rng = random.Random(seed * 7 + 3); out = {}
    for name, q in SCEN.items():
        Ms = []
        for _ in range(reps):
            banned = set(); m = np.zeros(months)
            for (t, f, kind, cash) in led:
                if f in banned: continue
                if kind == "payout" and rng.random() < q.get(TIER.get(f, "B"), 0.05):
                    banned.add(f); continue                     # the refused payout is not paid, nor anything later
                mth = int(t // (30.44 * DAY))
                if 0 <= mth < months: m[mth] += cash
            Ms.append(m)
        out[name] = np.mean(Ms, 0).tolist()
    return out

def life(args):
    pname, seed, months, kw, slots = args
    slots = slots or PORTFOLIOS[pname]
    years = 2 if months <= 12 else math.ceil(months / 12 + 1.5)      # a life starts up to a quarter of the way into its path
    data = kw.pop("data", None) or f"synth{seed}y{years}"
    s0 = LS.A.STUCK[0]
    ledger, st = LS.run_life(slots, data=data, months=months, seed=seed, rule="trend5", **kw)
    # paths stay in the process's bounded cache (pathfirm.MAX_CACHE): the next portfolio of the same life reuses them
    ledger.sort(key=lambda r: r[0])
    H = months * 30.44 * DAY
    cum = 0.0; trough = 0.0
    for r in ledger:
        if r[0] > H: break
        cum += r[3]; trough = min(trough, cum)
    m = LS.monthly(ledger, months)
    names = [s["firm"] for s in slots]
    agg = collections.defaultdict(collections.Counter)
    for (t, sid, kind, cash, att) in ledger:
        if t > H: continue
        f = firm_of(names[sid])
        if kind.endswith("_fail") or kind == "funded_end": agg["breaches"][f] += 1
        if kind == "payout": agg["payouts"][f] += cash; agg["requests"][f] += 1
        if kind in ("buy", "monthly_fee", "activation"): agg["fees"][f] += cash
        if kind == "buy": agg["buys"][f] += 1
        if kind == "credit_earned": agg["credits"][f] += 1
    # value at month 12 of the accounts then open: cash after month 12 from attempts bought before it
    t12 = 12 * 30.44 * DAY
    start = {(sid, att): t for (t, sid, kind, cash, att) in ledger if kind == "buy"}
    open12 = sum(cash for (t, sid, kind, cash, att) in ledger if t > t12 and start.get((sid, att), 1e18) <= t12) if months > 12 else None
    led = [(r[0], firm_of(names[r[1]]), r[2], r[3]) for r in ledger if r[0] <= H]
    tl = st["trade_log"]; days = collections.Counter(int(e // 24) for e, sid in tl)
    return dict(p=pname, seed=seed, months=months, kw={k: v for k, v in kw.items()}, monthly=m.tolist(), trough=trough,
                conflicts=st["conflicts"], trades=st["trades"], copied=st["copied"],
                **{k: dict(v) for k, v in agg.items()}, refusal=refusals(led, seed, months), open12=open12,
                wallet_low=st["wallet_low"], wallet_end=st["wallet_end"], stats=st["stats"],
                orders_per_trading_day=float(np.mean(list(days.values()))) if days else 0.0, stuck=LS.A.STUCK[0] - s0)

def run(J, out, chunk=1, block=560):
    """runs the lives in blocks and checkpoints after each (out + '.partial'), so an interrupted stage resumes"""
    import os, pickle
    part = out + ".partial"
    R = pickle.load(open(part, "rb")) if os.path.exists(part) else []
    if R: print(f"resuming {out}: {len(R)} of {len(J)} lives done", flush=True)
    with Pool(4) as pool:
        while len(R) < len(J):
            R += pool.map(life, J[len(R):len(R) + block], chunksize=chunk)
            pickle.dump(R, open(part + ".tmp", "wb")); os.replace(part + ".tmp", part)
    json.dump(dict(R=R, slots={p: PORTFOLIOS[p] for p in PORTFOLIOS}), open(out, "w"))
    os.remove(part)
    print(f"{out}: {sum(r.get('stuck', 0) for r in R)} accounts ended by the stall detector", flush=True)
    return R

def summary(R, label):
    M = np.array([r["monthly"] for r in R]); n = len(R); C = M.cumsum(1)
    y = M.mean(1)
    print(f"== {label}: lives={n} EV/month {M.mean():.0f} ± {1.96 * y.std() / math.sqrt(n):.0f}  months 2-12 {M[:, 1:12].mean():.0f}"
          f"  P(ahead 12m) {np.mean(C[:, min(11, M.shape[1] - 1)] > 0):.2f}  trough p50/p05 {np.percentile([r['trough'] for r in R], [50, 5]).round(0).tolist()}",
          flush=True)

if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "show":
        for p, sl in PORTFOLIOS.items():
            print(p, len(sl), round(sum(s["ev"] for s in sl)))
        print("FP", FP, "T5", T5, "FX", FX, "GFT", GF, "FunderPro", FPR, "FN", FN_I, FN_SIZE, "Hola", HP_I)
    if stage == "main":
        lives = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
        J = [(p, 100_000 + j, 12, {}, None) for j in range(lives) for p in PORTFOLIOS]     # one life's portfolios together
        R = run(J, "lockstep_v8.json", chunk=len(PORTFOLIOS))
        for p in PORTFOLIOS: summary([r for r in R if r["p"] == p], p)
    if stage == "long":
        J = [(REC, 300_000 + j, 36, {}, None) for j in range(800)]
        R = run(J, "lockstep_v8_long.json")
        summary(R, "36 months")
        M = np.array([r["monthly"] for r in R]); print("months 13-36:", M[:, 12:].mean().round(0), "open at 12:", np.mean([r["open12"] for r in R]).round(0))
    if stage == "budget":
        sl = sorted(PORTFOLIOS[REC], key=lambda s: -s["ev"] / max(s.get("fee") or F7.rules_for(s["firm"], s["size"], s["kind"])["fee"], 1))
        J = [(REC, 100_000 + j, 12, dict(budget=b), sl) for b in (5_000, 10_000, 20_000, 30_000, 50_000, 75_000, 100_000) for j in range(200)]
        J += [(REC, 100_000 + j, 12, {}, sl) for j in range(200)]
        R = run(J, "lockstep_v8_budget.json")
        for b in (5_000, 10_000, 20_000, 30_000, 50_000, 75_000, 100_000, None):
            summary([r for r in R if r["kw"].get("budget") == b], f"budget {b}")
    if stage == "stress":
        J = [(REC, 100_000 + j, 12, dict(cost_mult=c), None) for c in (1.5, 2.0) for j in range(200)]
        R = run(J, "lockstep_v8_stress.json")
        for c in (1.5, 2.0): summary([r for r in R if r["kw"].get("cost_mult") == c], f"cost x{c}")
    if stage == "corr":
        J = [(REC, 100_000 + j, 12, dict(data=f"corr30_{100_000 + j}y2"), None) for j in range(200)]
        R = run(J, "lockstep_v8_corr.json"); summary(R, "correlation 0.3")
    if stage == "news":
        J = [(REC, 100_000 + j, 12, dict(news=True), None) for j in range(200)]
        R = run(J, "lockstep_v8_news.json"); summary(R, "news proxy")
    if stage == "pairfirms":
        # linearity check: the same 200 long-run seeds with each firm's accounts run alone; full portfolio minus the sum
        by = collections.defaultdict(list)
        for s_ in PORTFOLIOS[REC]: by[firm_of(s_["firm"])].append(s_)
        J = [(f"alone: {f}", 300_000 + j, 36, {}, sl) for f, sl in by.items() for j in range(200)]
        R = run(J, "lockstep_v8_pairfirms_lives.json")
        full = {r["seed"]: np.array(r["monthly"]) for r in json.load(open("lockstep_v8_long.json"))["R"] if r["seed"] < 300_200}
        tot = collections.defaultdict(lambda: np.zeros(36)); alone = collections.defaultdict(list)
        for r in R:
            tot[r["seed"]] += np.array(r["monthly"]); alone[r["p"][7:]].append(np.mean(r["monthly"][12:]))
        d = np.array([full[k][12:].mean() - tot[k][12:].mean() for k in full]); d1 = np.array([full[k][:12].mean() - tot[k][:12].mean() for k in full])
        out = dict(n=len(d), diff=float(d.mean()), ci=float(1.96 * d.std() / math.sqrt(len(d))), diff_y1=float(d1.mean()), ci_y1=float(1.96 * d1.std() / math.sqrt(len(d1))),
                   full=float(np.mean([full[k][12:].mean() for k in full])), sum_alone=float(np.mean([tot[k][12:].mean() for k in full])),
                   alone={f: float(np.mean(v)) for f, v in alone.items()}, renewal={f: float(sum(x["ev"] for x in sl)) for f, sl in by.items()})
        json.dump(out, open("lockstep_v8_pairfirms.json", "w"), indent=1)
        print("pairfirms", {k: v for k, v in out.items() if k not in ("alone", "renewal")}, flush=True)
    if stage == "behav":
        base = PORTFOLIOS[REC]
        fn = [i for i, s in enumerate(base) if s["firm"].startswith("FundedNext")]
        variants = {}
        v = [dict(s) for s in base]
        for i in fn: v[i]["override"] = dict(max_risk_rule=0.01 * v[i]["size"])
        variants["FundedNext 1% risk"] = v
        v = [dict(s) for s in base]
        for i in fn: v[i]["gap_days"] = 7
        variants["FundedNext 7-day pause"] = v
        J = [(name, 100_000 + j, 12, {}, sl) for name, sl in variants.items() for j in range(200)]
        R = run(J, "lockstep_v8_behav.json")
        for name in variants: summary([r for r in R if r["p"] == name], name)
