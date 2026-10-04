"""
Version 7 optimiser: the corrected rules (firms_v7) and the corrected engine (cost-aware sizing, end of an attempt when
the room above the floor is too small for a real trade, flat every day by 20:00 UTC, 40% concentration policy, whole
futures contracts, The5ers phase credits, Maven's rolling cap, Apex's 30-day expiry, Topstep's net-profit condition).

Settings searched per programme and market: risk per trade L (1.0%, 1.5%, 1.75% of the account; every firm's 2% rule
stays out of reach after costs), stop m (hourly standard deviations, at least the leverage floor below), reward:risk k
and funded payout target X (fraction of the account).

Leverage floor. Margin = notional / leverage, notional = L / (m sigma). The plan keeps margin at most 60% of the initial
balance (FunderPro's funded accounts: at most 20% per asset class, its written rule), on the evaluation's and on the
funded account's leverage:
    m >= L / (cap x size x leverage x sigma)

Stages (each on paths no earlier stage used):
  grid    every setting, 2,000 attempts (4 paths x 500)              paths 101-104
  refine  the 14 best per programme and market + neighbours, 16,000   paths 111-114
  final   the chosen setting, 24,000 attempts in 16 clusters          paths 121-136 (cluster-robust CI)
"""
import json, sys, math, random, collections
import numpy as np
from multiprocessing import Pool
import firms_v7 as F7, pathfirm as PF

SIG = json.load(open("sigma_v32.json"))
MARGIN_CAP = 0.60
# (evaluation leverage, funded leverage, funded margin cap) per firm and market, checked 4 October 2026
LEV = {
    "FTMO": {"US100": (50, 50, MARGIN_CAP)},
    "FundingPips": {"USDJPY": (100, 100, MARGIN_CAP), "EURUSD": (100, 100, MARGIN_CAP)},
    "FundedNext": {"EURUSD": (100, 100, MARGIN_CAP), "XAUUSD": (10, 10, MARGIN_CAP)},
    "The5ers": {"US100": (25, 25, MARGIN_CAP)},
    "FXIFY": {"US100": (10, 10, MARGIN_CAP), "USDJPY": (30, 30, MARGIN_CAP)},
    "Fintokei": {"US100": (50, 50, MARGIN_CAP)},
    "Hola Prime": {"XAUUSD": (10, 10, MARGIN_CAP), "EURUSD": (50, 50, MARGIN_CAP)},
    "Alpha Capital": {"US100": (20, 20, MARGIN_CAP)},
    "GFT": {"US100": (20, 10, MARGIN_CAP), "USDJPY": (100, 50, MARGIN_CAP)},
    "FunderPro": {"US100": (30, 30, 0.20), "USDJPY": (100, 100, 0.20)},
    "BrightFunded": {"US100": (20, 20, MARGIN_CAP)},
    "Blue Guardian": {"US100": (10, 10, MARGIN_CAP)},
    "Maven": {"US100": (20, 20, MARGIN_CAP)},
}
M_GRID = [0.35, 0.5, 0.75, 1.0, 1.25]
K_GRID = [1.5, 2, 3, 4, 6, 8, 12]
L_GRID = [0.010, 0.015, 0.0175]
X_STD = [0.05, 0.08, 0.10, 0.15, 0.20, 0.30]
CAP_M, CAP_X = 0.35, 0.30        # practical caps: stop at least 0.35 sd, one payout target at most 30% of the account

def m_min(firm, instr, risk_frac):
    le, lf, cf = LEV[firm][instr]
    return max(risk_frac / (MARGIN_CAP * le * SIG[instr]), risk_frac / (cf * lf * SIG[instr]))

def m_grid(firm, instr, rf):
    mm = max(m_min(firm, instr, rf), CAP_M)        # below 0.35 sd the stop sits within a few spreads of the entry
    ms = [m for m in M_GRID if m + 1e-9 >= mm]
    if not ms or ms[0] > mm + 0.05: ms = [math.ceil(mm * 100) / 100] + ms
    return ms[:4]

PROGS = [   # programme, firm, markets, payout-target grid
    ("FTMO 2-Step", "FTMO", ["US100"], X_STD),
    ("FundingPips 2-Step Flex (80%)", "FundingPips", ["USDJPY", "EURUSD"], X_STD),
    ("FundingPips 2-Step Flex (95%)", "FundingPips", ["USDJPY", "EURUSD"], X_STD),
    ("FundedNext Stellar 2-Step", "FundedNext", ["EURUSD", "XAUUSD"], X_STD),
    ("The5ers High Stakes", "The5ers", ["US100"], X_STD),
    ("The5ers High Stakes Classic", "The5ers", ["US100"], X_STD),
    ("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY", ["US100", "USDJPY"], X_STD),
    ("FXIFY Two Phase Classic (80%)", "FXIFY", ["US100", "USDJPY"], X_STD),
    ("Fintokei ProTrader", "Fintokei", ["US100"], X_STD),
    ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", ["XAUUSD", "EURUSD"], X_STD),
    ("Alpha Capital Pro 10%", "Alpha Capital", ["US100"], X_STD),
    ("GFT 2-Step Standard", "GFT", ["US100", "USDJPY"], [0.04, 0.06, 0.08, 0.10, 0.15, 0.20]),
    ("FunderPro Classic", "FunderPro", ["US100", "USDJPY"], X_STD),
    ("BrightFunded 2-Step Classic", "BrightFunded", ["US100"], X_STD),
    ("Blue Guardian 2-Step", "Blue Guardian", ["US100"], [0.04, 0.06, 0.08, 0.10, 0.15]),
    ("Maven 2-Step", "Maven", ["US100"], [0.04, 0.06, 0.08, 0.10, 0.125]),
]
META = {p[0]: p for p in PROGS}
GRID_PATHS = ["synth101", "synth102", "synth103", "synth104"]
REFINE_PATHS = ["synth111", "synth112", "synth113", "synth114"]
FINAL_PATHS = [f"synth{121 + i}" for i in range(16)]

def x1_of(firm, x, size):
    return min(x * size, 0.06 * size, 10_000.0) if firm == "GFT" else x * size

def configs(size=100_000):
    out = []
    for prog, firm, markets, xs in PROGS:
        for instr in markets:
            for rf in L_GRID:
                for m in m_grid(firm, instr, rf):
                    for k in K_GRID:
                        for x in xs:
                            out.append(dict(prog=prog, firm=firm, instr=instr, m=m, k=k, X1=x1_of(firm, x, size), X=x * size,
                                            L=rf * size, size=size))
    return out

def lev_tuple(firm, instr):
    """(evaluation leverage, funded leverage, plan's margin cap on the current balance, funded cap on the start)"""
    if firm not in LEV or instr not in LEV[firm]: return None
    le, lf, cf = LEV[firm][instr]
    return (le, lf, MARGIN_CAP, cf if cf < MARGIN_CAP else 1e9)

def firm_rules(c):
    F = F7.rules_for(c["prog"], c["size"], c.get("kind", "cfd"), c.get("fee"), c.get("override"))
    if c.get("kind", "cfd") == "cfd": F["lev"] = lev_tuple(c["firm"], c["instr"])
    return F

def run(c, data, seed, n, cost_mult=1.0):
    F = firm_rules(c)
    rng = random.Random(seed)
    R = [PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng, cost_mult=cost_mult) for _ in range(n)]
    npass = len(F["phases"])
    return dict(v=[r["v"] for r in R], d=[r["days"] for r in R], funded=sum(r["passed"] == npass for r in R),
                paid=sum(r["paid"] for r in R if r["passed"] == npass), t1=[r["t1"] for r in R if r["t1"] is not None],
                npay=[r["npay"] for r in R if r["passed"] == npass])

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}
def tq(df):
    """97.5% quantile of Student's t with df degrees of freedom (a cluster-robust interval with G clusters uses df = G - 1)"""
    if df in T975: return T975[df]
    return 1.96 + 2.4 / df if df > 30 else T975[min(k for k in T975 if k >= df)]

def stats(parts):
    """ratio estimator EV/month = 30.44 sum(v)/sum(d); CI from the attempts and, more conservatively, from the paths
    as clusters (attempts on one path share its price history)"""
    v = np.concatenate([p["v"] for p in parts]); d = np.concatenate([p["d"] for p in parts]); n = len(v)
    ratio = v.sum() / d.sum(); resid = v - ratio * d
    ci_iid = 1.96 * resid.std() / math.sqrt(n) / d.mean() * 30.44
    C = len(parts)
    if C >= 2:
        Vc = np.array([np.sum(p["v"]) for p in parts]); Dc = np.array([np.sum(p["d"]) for p in parts])
        u = Vc - ratio * Dc
        var = C / (C - 1) * np.sum(u ** 2) / d.sum() ** 2
        ci_cl = tq(C - 1) * math.sqrt(var) * 30.44
    else:
        ci_cl = ci_iid
    funded = sum(p["funded"] for p in parts); t1 = sum([p["t1"] for p in parts], [])
    npay = sum([p["npay"] for p in parts], [])
    return dict(n=n, EV=float(v.mean()), days=float(d.mean()), EV_month=float(ratio * 30.44), CI=float(max(ci_iid, ci_cl)),
                CI_iid=float(ci_iid), CI_cluster=float(ci_cl), clusters=C, t_adjusted=True, P=funded / n,
                Vf=sum(p["paid"] for p in parts) / max(funded, 1), P_paid=len(t1) / n,
                t1=float(np.median(t1)) if t1 else None, npay=float(np.mean(npay)) if npay else 0.0)

def job(a):
    c, paths, seeds, n = a[:4]
    cm = a[4] if len(a) > 4 else 1.0
    parts = [run(c, data, seed, n, cm) for data, seed in zip(paths, seeds)]
    return dict(c, **stats(parts), cost_mult=cm)

def candidates(grid, top=14):
    by = collections.defaultdict(list)
    for r in grid: by[(r["prog"], r["instr"])].append(r)
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size")
    out = []
    for (prog, instr), rs in by.items():
        _, firm, _, xs = META[prog]
        rs.sort(key=lambda r: -r["EV_month"])
        seen = set()
        def add(c):
            key = (round(c["m"], 3), c["k"], round(c["X"]), round(c["L"]))
            if key in seen: return
            seen.add(key); out.append(c)
        for r in rs[:top]: add({k: r[k] for k in keys})
        b = rs[0]
        # neighbours of the best setting off the grid: k between grid points, a larger payout target at the top edge
        kk = sorted(K_GRID); i = kk.index(b["k"])
        for k2 in {(kk[max(i - 1, 0)] + b["k"]) / 2, (kk[min(i + 1, len(kk) - 1)] + b["k"]) / 2} - {b["k"]}:
            add(dict({k: b[k] for k in keys}, k=k2))
        if b["k"] == max(K_GRID): add(dict({k: b[k] for k in keys}, k=16))
        if b["k"] == min(K_GRID): add(dict({k: b[k] for k in keys}, k=1.2))
        if b["X"] >= max(xs) * b["size"] - 1 and max(xs) < CAP_X:
            x2 = min(max(xs) + 0.05, CAP_X); add(dict({k: b[k] for k in keys}, X=x2 * b["size"], X1=x1_of(firm, x2, b["size"])))
    return out

if __name__ == "__main__" and sys.argv[1] == "grid":
    C = configs()
    print(len(C), "configurations", flush=True)
    J = [(c, GRID_PATHS, (1, 2, 3, 4), 500) for c in C]
    with Pool(4) as p, open("opt_v7_grid.jsonl", "w") as f:
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=8)):
            f.write(json.dumps(r) + "\n")
            if i % 500 == 0: print(i, flush=True)

if __name__ == "__main__" and sys.argv[1] == "refine":
    grid = [json.loads(l) for l in open("opt_v7_grid.jsonl")]
    C = candidates(grid)
    print(len(C), "candidates", flush=True)
    J = [(c, REFINE_PATHS, (11, 12, 13, 14), 4000) for c in C]
    with Pool(4) as p, open("opt_v7_refine.jsonl", "w") as f:
        for r in p.imap_unordered(job, J, chunksize=1):
            f.write(json.dumps(r) + "\n"); f.flush()

# ---------------------------------------------------------------- futures: risk per trade is searched too (no percentage rules)
FUT = [("Topstep 50K", None), ("Apex 50K EOD", dict(fee=55, activation=99))]
def fut_configs():
    C = []
    for prog, ov in FUT:
        for k in [1.5, 2, 3, 4, 5, 6, 8]:
            for m in [0.5, 0.75, 1.0]:
                for L in [400, 600, 800, 950, 1100]:
                    C.append(dict(prog=prog, firm=prog.split()[0], kind="fut", instr="MNQ_fut", m=m, k=k, X1=0, X=0, L=L,
                                  size=50_000, override=ov))
    return C
if __name__ == "__main__" and sys.argv[1] == "futures":
    C = fut_configs()
    J = [(c, GRID_PATHS, (5, 6, 7, 8), 1000) for c in C]
    with Pool(4) as p:
        R = p.map(job, J, chunksize=2)
    keys = ("prog", "firm", "kind", "instr", "m", "k", "X1", "X", "L", "size", "override")
    by = collections.defaultdict(list)
    for r in R: by[r["prog"]].append(r)
    Cr = []
    for prog, rs in by.items():
        Cr += [{k: r[k] for k in keys} for r in sorted(rs, key=lambda r: -r["EV_month"])[:10]]
    with Pool(4) as p:
        Rr = p.map(job, [(c, REFINE_PATHS, (15, 16, 17, 18), 4000) for c in Cr], chunksize=1)
    with open("opt_v7_futures.jsonl", "w") as f:
        for r in R: f.write(json.dumps(dict(r, stage="grid")) + "\n")
        for r in Rr: f.write(json.dumps(dict(r, stage="refine")) + "\n")
    for r in sorted(Rr, key=lambda r: -r["EV_month"])[:10]:
        print(r["prog"], r["k"], r["m"], r["L"], round(r["EV_month"]), round(r["CI"]), flush=True)

# ---------------------------------------------------------------- final: chosen settings on 16 fresh paths, plus sizes
FEE_SIZES = {      # list prices of the other sizes a person may hold (firms_v7 has the 100K and 200K prices)
    "FXIFY Two Phase Classic (100%, 30 days)": {50_000: 379, 25_000: 199, 10_000: 89, 5_000: 59},
}
THE5ERS_SMALL = {25_000: "The5ers High Stakes 25K", 10_000: "The5ers High Stakes 10K", 5_000: "The5ers High Stakes 5K",
                 2_500: "The5ers High Stakes 2.5K"}
HAS200 = {"FTMO 2-Step", "FundedNext Stellar 2-Step", "FunderPro Classic", "GFT 2-Step Standard", "Alpha Capital Pro 10%",
          "BrightFunded 2-Step Classic", "Blue Guardian 2-Step", "Fintokei ProTrader"}

# firms whose own guidance sets a lower risk per trade than the plan's 1.75% ceiling: FTMO recommends 1-1.5% of the initial
# balance and monitors larger risk as possible gambling (ftmo.com/en/blog/how-much-should-you-risk-on-one-trade/)
L_MAX = {"FTMO": 0.015}

def choose(refine):
    by = collections.defaultdict(list)
    for r in refine: by[(r["prog"], r["instr"])].append(r)
    out = []
    for key, rs in by.items():
        ok = [r for r in rs if r["m"] + 1e-9 >= CAP_M and r["X"] <= CAP_X * r["size"] + 1
              and r["L"] <= L_MAX.get(r["firm"], 1.0) * r["size"] + 1]
        best = max(ok, key=lambda r: r["EV_month"])
        out.append(dict(best, tag="chosen"))
    return out

def scaled(c, size, fee=None, prog=None, tag=None):
    f = size / c["size"]
    return dict(c, prog=prog or c["prog"], size=size, L=c["L"] * f, X=c["X"] * f,
                X1=x1_of(c["firm"], c["X"] / c["size"], size) if c.get("firm") == "GFT" else c["X1"] * f,
                **({"fee": fee} if fee is not None else {}), tag=tag or f"{size // 1000}K")

FINAL_KEYS = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
if __name__ == "__main__" and sys.argv[1] == "final":
    # programmes with a firm-specific risk ceiling: refine their best grid settings inside the ceiling too (appended once)
    refine = [json.loads(l) for l in open("opt_v7_refine.jsonl")]
    if not any(r.get("stage") == "lmax" for r in refine):
        grid = [json.loads(l) for l in open("opt_v7_grid.jsonl")]
        gl = [r for r in grid if r["firm"] in L_MAX and r["L"] <= L_MAX[r["firm"]] * r["size"] + 1]
        done = {(r["prog"], r["instr"], round(r["m"], 3), r["k"], round(r["X"]), round(r["L"])) for r in refine}
        C = [c for c in candidates(gl) if (c["prog"], c["instr"], round(c["m"], 3), c["k"], round(c["X"]), round(c["L"])) not in done]
        print(len(C), "extra candidates inside firm risk ceilings", flush=True)
        with Pool(4) as p:
            Rx = p.map(job, [(c, REFINE_PATHS, (11, 12, 13, 14), 4000) for c in C], chunksize=1)
        with open("opt_v7_refine.jsonl", "a") as f:
            for r in Rx: f.write(json.dumps(dict(r, stage="lmax")) + "\n")
        refine += [dict(r, stage="lmax") for r in Rx]
    fut = [json.loads(l) for l in open("opt_v7_futures.jsonl")]
    C = [{k: c[k] for k in FINAL_KEYS if k in c} for c in choose(refine)]
    for prog, _ in FUT:
        rs = [r for r in fut if r["prog"] == prog and r["stage"] == "refine"]
        b = max(rs, key=lambda r: r["EV_month"])
        C.append(dict({k: b[k] for k in FINAL_KEYS if k in b}, tag="chosen"))
    chosen = [c for c in C if c["tag"] == "chosen"]
    for c in [c for c in chosen if c["prog"] in HAS200]:
        C.append(scaled(c, 200_000, tag="200K"))
    for c in [c for c in chosen if c["prog"] in FEE_SIZES and c["instr"] == "US100"]:
        for sz, fee in FEE_SIZES[c["prog"]].items(): C.append(scaled(c, sz, fee))
    for c in [c for c in chosen if c["prog"] == "The5ers High Stakes"]:
        for sz, prog in THE5ERS_SMALL.items(): C.append(scaled(c, sz, None, prog=prog))
    print(len(C), "final configurations", flush=True)
    J = [(dict(c, data="synth"), FINAL_PATHS, tuple(range(201, 217)), 1500) for c in C]
    with Pool(4) as p:
        R = p.map(job, J, chunksize=1)
    json.dump(R, open("opt_v7_final.json", "w"), indent=0)
    for r in sorted(R, key=lambda r: (r["prog"], r["instr"], r["size"])):
        print(f"{r['prog'][:38]:38s} {r['instr']:7s} {r['size']//1000:>3}K {r['tag']:7s} k={r['k']:>4} m={r['m']:.2f} L={r['L']:.0f} "
              f"X={r['X']/1000:5.1f}K EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} (iid ±{r['CI_iid']:.0f}) P={r['P']:.3f} days={r['days']:5.1f}",
              flush=True)
