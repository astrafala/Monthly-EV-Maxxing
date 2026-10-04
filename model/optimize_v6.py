"""
Version 6 optimiser. For every programme, every market it may trade and every setting that the firm's leverage allows,
run attempts on four independent zero-edge synthetic paths and record EV per month.

Settings searched: reward:risk k, stop m (in hourly standard deviations), funded cycle target X (fraction of the account).
Risk per trade stays 1.5% of the account (2-Step Standard at FundingPips: 1.1%, below its 1.2% floating-loss strike).
A stop is allowed only if the margin it needs is at most 60% of the balance:
    notional = risk / (m * sigma),  margin = notional / leverage  <=  0.6 * size   =>   m >= risk / (0.6 * size * leverage * sigma)
"""
import json, sys, math, random, itertools
import numpy as np
from multiprocessing import Pool
import firms_v5 as F5, pathfirm as PF

SIG = json.load(open("sigma_v32.json"))
MARGIN_CAP = 0.60
# leverage the firm gives on each market (checked 4 October 2026); FundingPips' dynamic leverage on indices and
# metals falls to 1:5 above 0.5 lots, which a position of this size always exceeds
LEV = {
    "FTMO": {"US100": 50}, "FundingPips": {"US100": 5, "USDJPY": 100, "EURUSD": 100, "XAUUSD": 5},
    "The5ers": {"US100": 25}, "FXIFY": {"US100": 10, "USDJPY": 30, "XAUUSD": 30},
    "FundedNext": {"XAUUSD": 10, "EURUSD": 100, "USDJPY": 100}, "Fintokei": {"US100": 50},
    "Hola Prime": {"EURUSD": 50, "XAUUSD": 10, "USDJPY": 50}, "Alpha Capital": {"US100": 20},
    "BrightFunded": {"US100": 20}, "Blue Guardian": {"US100": 10}, "FunderPro": {"US100": 30},
    "Maven": {"US100": 20}, "GFT": {"US100": 15},
}
M_GRID = [0.5, 0.75, 1.0, 1.25, 1.5]
K_GRID = [2, 3, 4, 5, 6, 7, 8, 10, 12]

def m_min(firm, instr, risk_frac):
    return risk_frac / (MARGIN_CAP * LEV[firm][instr] * SIG[instr])

# programme, firm, markets, cycle targets (fractions; GFT's first two cycles are capped at 6%), risk fraction
PROGS = [
    ("FTMO 2-Step", "FTMO", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FTMO 1-Step", "FTMO", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundingPips 2-Step Flex (85%) v5", "FundingPips", ["USDJPY", "EURUSD"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundingPips 2-Step Flex (95%) v5", "FundingPips", ["USDJPY"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundingPips 2-Step Flex (85%) v6 cap", "FundingPips", ["USDJPY"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundingPips 2-Step Flex (85%) v6 4days", "FundingPips", ["USDJPY"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundingPips 2-Step (bi-weekly 80%)", "FundingPips", ["USDJPY"], [0.05, 0.08, 0.10], 0.011),
    ("The5ers High Stakes", "The5ers", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("The5ers High Stakes Classic", "The5ers", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FXIFY Two Phase Classic (80%)", "FXIFY", ["US100", "USDJPY"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY", ["US100", "USDJPY"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("FundedNext Stellar 2-Step v5", "FundedNext", ["XAUUSD", "EURUSD"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Fintokei ProTrader", "Fintokei", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", ["EURUSD", "XAUUSD"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Alpha Capital Pro 10%", "Alpha Capital", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Alpha Capital Pro 10% (on-demand)", "Alpha Capital", ["US100"], [0.02, 0.04, 0.06, 0.08, 0.10], 0.015),
    ("BrightFunded 2-Step Classic v5", "BrightFunded", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Blue Guardian 2-Step v5", "Blue Guardian", ["US100"], [0.04, 0.06, 0.08], 0.015),
    ("FunderPro Classic v5", "FunderPro", ["US100"], [0.05, 0.08, 0.10, 0.12, 0.15], 0.015),
    ("Maven 2-Step", "Maven", ["US100"], [0.04, 0.06, 0.08], 0.015),
    ("GFT 2-Step Standard v5", "GFT", ["US100"], [0.06, 0.08, 0.10, 0.12], 0.015),
]
PATHS = ["synth21", "synth22", "synth23", "synth24"]

def configs(size=100_000):
    out = []
    for prog, firm, markets, xs, rf in PROGS:
        for instr in markets:
            mm = m_min(firm, instr, rf)
            for m in M_GRID:
                if m + 1e-9 < mm: continue
                for k in K_GRID:
                    for x in xs:
                        X1 = min(x, 0.06) if firm == "GFT" else x
                        out.append(dict(prog=prog, firm=firm, instr=instr, m=m, k=k, X1=X1 * size, X=x * size, L=rf * size, size=size))
    return out

def firm_rules(c):
    import copy
    F = F5.cfd_firms(c["size"])[c["prog"]] if c.get("kind", "cfd") == "cfd" else F5.futures_firms()[c["prog"]]
    if c.get("fee") is not None or c.get("override") or c["size"] != 100_000:
        F = copy.deepcopy(F)
        if c.get("kind", "cfd") == "cfd": F["buffer_scale"] = c["size"] / 100_000
        if c.get("fee") is not None:
            F["fee"] = c["fee"]
            if F["funded"].get("refund"): F["funded"]["refund"] = c["fee"]
        F.update(c.get("override") or {})
    return F

def run(c, data, seed, n):
    F = firm_rules(c)
    rng = random.Random(seed)
    R = [PF.attempt(F, c["instr"], data, c["m"], c["L"], c["k"], c["X1"], c["X"], rng) for _ in range(n)]
    npass = len(F["phases"])
    return dict(v=[r["v"] for r in R], d=[r["days"] for r in R], funded=sum(r["passed"] == npass for r in R),
                paid=sum(r["paid"] for r in R if r["passed"] == npass), t1=[r["t1"] for r in R if r["t1"] is not None])

def stats(parts):
    v = np.concatenate([p["v"] for p in parts]); d = np.concatenate([p["d"] for p in parts]); n = len(v)
    ratio = v.mean() / d.mean(); resid = v - ratio * d
    funded = sum(p["funded"] for p in parts); t1 = sum([p["t1"] for p in parts], [])
    return dict(n=n, EV=float(v.mean()), days=float(d.mean()), EV_month=float(ratio * 30.44),
                CI=float(1.96 * resid.std() / math.sqrt(n) / d.mean() * 30.44), P=funded / n,
                Vf=sum(p["paid"] for p in parts) / max(funded, 1), P_paid=len(t1) / n,
                t1=float(np.median(t1)) if t1 else None)

def job(a):
    c, n, seeds = a
    parts = [run(c, data, seed, n) for data, seed in zip(PATHS, seeds)]
    return dict(c, **stats(parts))

if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "grid":
        C = configs()
        print(len(C), "configurations", flush=True)
        J = [(c, 1000, (11, 12, 13, 14)) for c in C]
        with Pool(4) as p, open("opt_v6_grid.jsonl", "w") as f:
            for i, r in enumerate(p.imap_unordered(job, J, chunksize=4)):
                f.write(json.dumps(r) + "\n")
                if i % 200 == 0: print(i, flush=True)

# ---------------------------------------------------------------- stage 2: refine the best settings on fresh paths
REFINE_PATHS = ["synth25", "synth26", "synth27", "synth28"]
FINAL_PATHS = ["synth29", "synth30", "synth31", "synth32"]

def default_cfg(prog, firm, instr, rf, size=100_000):
    mm = m_min(firm, instr, rf)
    m = min([x for x in M_GRID if x + 1e-9 >= mm])
    m = max(m, 0.75)
    x = 0.08 if firm in ("Blue Guardian", "Maven") else 0.10
    X1 = min(x, 0.06) if firm == "GFT" else x
    return dict(prog=prog, firm=firm, instr=instr, m=m, k=5, X1=X1 * size, X=x * size, L=rf * size, size=size, tag="v5 default")

def candidates(grid):
    import collections
    by = collections.defaultdict(list)
    for r in grid: by[(r["prog"], r["instr"])].append(r)
    meta = {p[0]: p for p in PROGS}
    out = []
    for (prog, instr), rs in by.items():
        _, firm, _, xs, rf = meta[prog]
        rs.sort(key=lambda r: -r["EV_month"])
        seen = set(); cands = []
        def add(c):
            key = (c["m"], c["k"], c["X"])
            if key in seen: return
            seen.add(key); cands.append(c)
        keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size")
        for r in rs[:8]: add({k: r[k] for k in keys})
        b = rs[0]
        mm = m_min(firm, instr, rf)
        # extend the grid where the best setting sits on its edge
        for k2 in ([15, 20] if b["k"] >= 12 else []):
            add(dict({k: b[k] for k in keys}, k=k2))
        if b["m"] <= 0.5 and 0.35 + 1e-9 >= mm:
            add(dict({k: b[k] for k in keys}, m=0.35))
        if b["X"] >= 0.15 * b["size"] - 1:
            x2 = 0.20 * b["size"]
            add(dict({k: b[k] for k in keys}, X=x2, X1=(min(0.06 * b["size"], x2) if firm == "GFT" else x2)))
        add(default_cfg(prog, firm, instr, rf))
        out += cands
    return out

def job_paths(a):
    c, n, paths, seeds = a
    parts = [run(c, data, seed, n) for data, seed in zip(paths, seeds)]
    return dict(c, **stats(parts))

if __name__ == "__main__" and sys.argv[1] == "refine":
    grid = [json.loads(l) for l in open("opt_v6_grid.jsonl")]
    C = candidates(grid)
    print(len(C), "candidates", flush=True)
    J = [(c, 6000, REFINE_PATHS, (21, 22, 23, 24)) for c in C]
    with Pool(4) as p, open("opt_v6_refine.jsonl", "w") as f:
        for i, r in enumerate(p.imap_unordered(job_paths, J, chunksize=1)):
            f.write(json.dumps(r) + "\n"); f.flush()


# ---------------------------------------------------------------- futures: risk per trade is free here (no percentage rules), so it is searched too
FUT = [("Topstep 50K", None), ("Apex 50K EOD", dict(fee=55, activation=99))]
if __name__ == "__main__" and sys.argv[1] == "futures":
    C = []
    for prog, ov in FUT:
        for k in [2, 3, 4, 5, 6, 8]:
            for m in [0.5, 0.75, 1.0]:
                for L in [600, 800, 950, 1100]:
                    C.append(dict(prog=prog, firm=prog.split()[0], kind="fut", instr="MNQ_fut", m=m, k=k, X1=0, X=0, L=L, size=50_000, override=ov))
    J = [(c, 1500, PATHS, (11, 12, 13, 14)) for c in C]
    with Pool(4) as p, open("opt_v6_futures.jsonl", "w") as f:
        for r in p.imap_unordered(job_paths, J, chunksize=2):
            f.write(json.dumps(r) + "\n"); f.flush()

# ---------------------------------------------------------------- stage 3: the chosen setting (and the version 5 default) on fresh paths and the real history
def choose(refine):
    import collections
    by = collections.defaultdict(list)
    for r in refine: by[(r["prog"], r["instr"])].append(r)
    out = []
    for key, rs in by.items():
        rs.sort(key=lambda r: -r["EV_month"])
        best = rs[0]
        out.append(dict(best, tag="chosen"))
        d = [r for r in rs if r.get("tag") == "v5 default"]
        if d and (d[0]["m"], d[0]["k"], d[0]["X"]) != (best["m"], best["k"], best["X"]):
            out.append(dict(d[0], tag="v5 default"))
    return out

def job_final(a):
    c, data_list, seeds, n = a
    parts = [run(c, data, seed, n) for data, seed in zip(data_list, seeds)]
    return dict(c, **stats(parts))

# list prices where the model's stored fee differs (FunderPro's $431 was a discounted price) and 200K list prices
FEE100 = {"FunderPro Classic v5": 539}
FEE200 = {"FTMO 2-Step": 1264, "FundedNext Stellar 2-Step v5": 1049.99, "FunderPro Classic v5": 989, "GFT 2-Step Standard v5": 974,
          "Alpha Capital Pro 10%": 997, "BrightFunded 2-Step Classic v5": 1163, "Blue Guardian 2-Step v5": 1162, "Fintokei ProTrader": 1249}

if __name__ == "__main__" and sys.argv[1] == "final":
    refine = [json.loads(l) for l in open("opt_v6_refine.jsonl")]
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
    C = [{k: c[k] for k in keys if k in c} for c in choose(refine)]
    for c in C:
        if c["prog"] in FEE100 and c.get("size", 100_000) == 100_000: c["fee"] = FEE100[c["prog"]]
    for c in [c for c in C if c["tag"] == "chosen" and c["prog"] in FEE200]:
        C.append(dict(c, size=200_000, L=2 * c["L"], X=2 * c["X"], X1=2 * c["X1"], fee=FEE200[c["prog"]], tag="200K"))
    J = []
    for c in C:
        J.append((dict(c, data="synth"), FINAL_PATHS, (31, 32, 33, 34), 6000))
        J.append((dict(c, data="real"), ["real"], (35,), 8000))
    with Pool(4) as p:
        R = p.map(job_final, J, chunksize=1)
    json.dump(R, open("opt_v6_final.json", "w"), indent=0)
    for r in sorted(R, key=lambda r: (r["prog"], r["instr"], r["tag"], r["data"])):
        print(f"{r['prog'][:38]:38s} {r['instr']:7s} {r['tag']:10s} {r['data']:5s} k={r['k']:>2} m={r['m']:.2f} X={r['X']/1000:4.1f}K "
              f"EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} P={r['P']:.3f} days={r['days']:5.1f}", flush=True)


# ---------------------------------------------------------------- programmes added after the main grid
if __name__ == "__main__" and sys.argv[1] == "extra":
    progs = set(sys.argv[2:])
    C = [c for c in configs() if c["prog"] in progs]
    J = [(c, 1000, (11, 12, 13, 14)) for c in C]
    with Pool(4) as p:
        R = p.map(job, J, chunksize=4)
    with open("opt_v6_grid.jsonl", "a") as f:
        for r in R: f.write(json.dumps(r) + "\n")
    grid = [r for r in R]
    Cr = candidates(grid)
    Jr = [(c, 6000, REFINE_PATHS, (21, 22, 23, 24)) for c in Cr]
    with Pool(4) as p:
        Rr = p.map(job_paths, Jr, chunksize=1)
    with open("opt_v6_refine.jsonl", "a") as f:
        for r in Rr: f.write(json.dumps(r) + "\n")
    for r in sorted(Rr, key=lambda r: -r["EV_month"])[:6]:
        print(r["prog"], r["k"], r["m"], r["X"], round(r["EV_month"]), round(r["CI"]))

# ---------------------------------------------------------------- edges: wherever the refined best sits on an edge, look one step further
if __name__ == "__main__" and sys.argv[1] == "edge":
    import collections
    refine = [json.loads(l) for l in open("opt_v6_refine.jsonl")]
    meta = {p[0]: p for p in PROGS}
    by = collections.defaultdict(list)
    for r in refine: by[(r["prog"], r["instr"])].append(r)
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size")
    C = []
    for (prog, instr), rs in by.items():
        b = max(rs, key=lambda r: r["EV_month"])
        _, firm, _, xs, rf = meta[prog]
        mm = m_min(firm, instr, rf)
        tried = {(r["m"], r["k"], round(r["X"])) for r in rs}
        ks = sorted({b["k"], b["k"] + 2, b["k"] + 4} | ({15, 20} if b["k"] >= 10 else set()))
        top = max(xs)
        xf = sorted({b["X"] / b["size"]} | ({b["X"] / b["size"] + 0.05, b["X"] / b["size"] + 0.10} if b["X"] / b["size"] >= top - 1e-9 else set()))
        ms = sorted({b["m"]} | ({round(b["m"] - 0.15, 2)} if b["m"] - 0.15 + 1e-9 >= mm and b["m"] - 0.15 >= 0.3 else set()))
        for k in ks:
            for x in xf:
                for m in ms:
                    if (m, k, round(x * b["size"])) in tried: continue
                    X1 = min(x, 0.06) if firm == "GFT" else x
                    C.append(dict(prog=prog, firm=firm, instr=instr, m=m, k=k, X1=X1 * b["size"], X=x * b["size"], L=b["L"], size=b["size"]))
    print(len(C), "edge candidates", flush=True)
    J = [(c, 6000, REFINE_PATHS, (21, 22, 23, 24)) for c in C]
    with Pool(4) as p:
        R = p.map(job_paths, J, chunksize=1)
    with open("opt_v6_refine.jsonl", "a") as f:
        for r in R: f.write(json.dumps(r) + "\n")

# futures: refine the best grid settings with 24,000 attempts
if __name__ == "__main__" and sys.argv[1] == "futures_refine":
    F = [json.loads(l) for l in open("opt_v6_futures.jsonl")]
    keys = ("prog", "firm", "kind", "instr", "m", "k", "X1", "X", "L", "size", "override")
    C = []
    for prog, ov in FUT:
        fs = sorted([r for r in F if r["prog"] == prog], key=lambda r: -r["EV_month"])[:8]
        C += [{k: r[k] for k in keys} for r in fs]
        C.append(dict(prog=prog, firm=prog.split()[0], kind="fut", instr="MNQ_fut", m=0.5 if prog.startswith("Apex") else 0.75,
                      k=2 if prog.startswith("Apex") else 5, X1=0, X=0, L=950, size=50_000, override=ov, tag="v5 default"))
    J = [(c, 6000, REFINE_PATHS, (21, 22, 23, 24)) for c in C]
    with Pool(4) as p:
        R = p.map(job_paths, J, chunksize=1)
    with open("opt_v6_refine.jsonl", "a") as f:
        for r in R: f.write(json.dumps(r) + "\n")
    for r in sorted(R, key=lambda r: -r["EV_month"])[:8]:
        print(r["prog"], r["k"], r["m"], r["L"], round(r["EV_month"]), round(r["CI"]))

# ---------------------------------------------------------------- bold play: how far does the trend go?
if __name__ == "__main__" and sys.argv[1] == "bold":
    import collections
    refine = [json.loads(l) for l in open("opt_v6_refine.jsonl")]
    meta = {p[0]: p for p in PROGS}
    by = collections.defaultdict(list)
    for r in refine:
        if r.get("kind", "cfd") == "cfd": by[(r["prog"], r["instr"])].append(r)
    C = []
    for (prog, instr), rs in by.items():
        _, firm, _, xs, rf = meta[prog]
        if firm in ("GFT", "Maven", "Blue Guardian") or "(on-demand)" in prog: continue
        b = max(rs, key=lambda r: r["EV_month"])
        mm = m_min(firm, instr, rf)
        tried = {(r["m"], r["k"], round(r["X"])) for r in rs}
        ms = sorted({b["m"]} | {m for m in (0.25, 0.3, 0.35) if m + 1e-9 >= mm and m < b["m"]})
        for k in (20, 30, 50):
            for x in (0.25, 0.30, 0.40, 0.50):
                for m in ms:
                    if (m, k, round(x * 1e5)) in tried: continue
                    C.append(dict(prog=prog, firm=firm, instr=instr, m=m, k=k, X1=x * 1e5, X=x * 1e5, L=b["L"], size=100_000))
    print(len(C), "bold-play candidates", flush=True)
    J = [(c, 6000, REFINE_PATHS, (21, 22, 23, 24)) for c in C]
    with Pool(4) as p:
        R = p.map(job_paths, J, chunksize=1)
    with open("opt_v6_refine.jsonl", "a") as f:
        for r in R: f.write(json.dumps(dict(r, tag="bold")) + "\n")

# ---------------------------------------------------------------- stage 4 (final6): the plan's settings, inside practical caps
# Caps on the searched settings (Chapter 9 of the document explains each):
#   stop m >= 0.35 hourly sd  - below it the stop is within a few spreads of the entry and the model's average cost
#                                understates stop slippage; the refine paths show no consistent gain below 0.35
#   cycle X <= 30% of the account - larger single payouts invite review and the gains beyond 30% are within noise
#   k <= 30                   - with X <= 30% every win already reaches the cycle target at k ~ 27
CAP_M, CAP_X, CAP_K = 0.35, 0.30, 30
# programmes searched but not in the plan, and why
EXCLUDE = {
    "FundingPips 2-Step Flex (85%) v5": "breaks the Profit Concentration Policy on new evaluations (use the v6 cap or 4days version)",
    "FundingPips 2-Step (bi-weekly 80%)": "rules last checked in version 3; the Profit Concentration Policy now applies",
}
# smaller accounts a person may hold next to the 100K one (FXIFY: one active account of each size; The5ers: 25K, 3x10K,
# 3x5K, 3x2.5K next to the 100K High Stakes) with their list prices (cryptoslate.com 4 Oct 2026; the5ers.com)
FXIFY_SMALL = {50_000: 379, 25_000: 199, 10_000: 89, 5_000: 59}
THE5ERS_SMALL = {25_000: "The5ers High Stakes 25K", 10_000: "The5ers High Stakes 10K", 5_000: "The5ers High Stakes 5K",
                 2_500: "The5ers High Stakes 2.5K"}

def admissible(r):
    if r.get("kind", "cfd") != "cfd": return True
    if r["prog"] == "Maven 2-Step" and r["X"] > 10_000 + 1: return False      # $10,000 per 30 days per person
    return r["m"] + 1e-9 >= CAP_M and r["X"] <= CAP_X * r["size"] + 1 and r["k"] <= CAP_K

def choose6(refine):
    import collections
    by = collections.defaultdict(list)
    for r in refine:
        if r["prog"] in EXCLUDE: continue
        by[(r["prog"], r["instr"])].append(r)
    out = []
    for key, rs in by.items():
        rs.sort(key=lambda r: -r["EV_month"])
        ok = [r for r in rs if admissible(r)]
        best = ok[0]
        out.append(dict(best, tag="chosen"))
        if (rs[0]["m"], rs[0]["k"], rs[0]["X"]) != (best["m"], best["k"], best["X"]):
            out.append(dict(rs[0], tag="uncapped"))
        meta = {p[0]: p for p in PROGS}
        if key[0] in meta:
            _, firm, _, xs, rf = meta[key[0]]
            dc = default_cfg(key[0], firm, key[1], rf)
            d = [r for r in rs if (abs(r["m"] - dc["m"]) < 1e-9 and r["k"] == dc["k"] and abs(r["X"] - dc["X"]) < 1 and abs(r["X1"] - dc["X1"]) < 1)]
        else:
            d = [r for r in rs if r.get("tag") == "v5 default"]
        if d and (d[0]["m"], d[0]["k"], d[0]["X"]) != (best["m"], best["k"], best["X"]):
            out.append(dict(d[0], tag="v5 default"))
    return out

def scaled(c, size, fee=None, prog=None, tag=None):
    f = size / c["size"]
    return dict(c, prog=prog or c["prog"], size=size, L=c["L"] * f, X=c["X"] * f, X1=c["X1"] * f,
                **({"fee": fee} if fee is not None else {}), tag=tag or f"{size // 1000}K")

if __name__ == "__main__" and sys.argv[1] == "final6":
    refine = [json.loads(l) for l in open("opt_v6_refine.jsonl")]
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
    C = [{k: c[k] for k in keys if k in c} for c in choose6(refine)]
    for c in C:
        if c["prog"] in FEE100 and c.get("size", 100_000) == 100_000: c["fee"] = FEE100[c["prog"]]
    chosen = [c for c in C if c["tag"] == "chosen"]
    for c in [c for c in chosen if c["prog"] in FEE200]:
        C.append(scaled(c, 200_000, FEE200[c["prog"]], tag="200K"))
    for c in [c for c in chosen if c["prog"] == "FXIFY Two Phase Classic (100%, 30 days)" and c["instr"] == "US100"]:
        for sz, fee in FXIFY_SMALL.items(): C.append(scaled(c, sz, fee))
    for c in [c for c in chosen if c["prog"] == "The5ers High Stakes"]:
        for sz, prog in THE5ERS_SMALL.items(): C.append(scaled(c, sz, None, prog=prog))
    print(len(C), "final configurations", flush=True)
    J = []
    for c in C:
        J.append((dict(c, data="synth"), FINAL_PATHS, (31, 32, 33, 34), 6000))
        J.append((dict(c, data="real"), ["real"], (35,), 8000))
    with Pool(4) as p:
        R = p.map(job_final, J, chunksize=1)
    json.dump(R, open("opt_v6_final.json", "w"), indent=0)
    for r in sorted(R, key=lambda r: (r["prog"], r["instr"], r["tag"], r["data"])):
        print(f"{r['prog'][:38]:38s} {r['instr']:7s} {r['size']//1000:>3}K {r['tag']:10s} {r['data']:5s} k={r['k']:>2} m={r['m']:.2f} X={r['X']/1000:5.1f}K "
              f"EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} P={r['P']:.3f} days={r['days']:5.1f}", flush=True)

# ---------------------------------------------------------------- stage 5 (robust): two settings re-chosen for cost robustness
# The cost check (extra_v6.py) showed that at its refined optimum FundedNext on EURUSD (m = 0.75) loses all its value if
# trading costs are twice the assumption; at m = 1.0 it keeps most of it and loses little at the assumed cost, so the plan
# uses m = 1.0. Because the choice was made on paths 29-32, its reported figures come from new paths 33-36.
ROBUST_PATHS = ["synth33", "synth34", "synth35", "synth36"]
ROBUST = {("FundedNext Stellar 2-Step v5", "EURUSD"): 1.0}      # FundingPips' search optimum is already m = 0.5 on the corrected engine
if __name__ == "__main__" and sys.argv[1] == "robust":
    FIN = json.load(open("opt_v6_final.json"))
    keys = ("prog", "firm", "instr", "m", "k", "X1", "X", "L", "size", "tag", "kind", "override", "fee")
    C = []
    for r in FIN:
        key = (r["prog"], r["instr"])
        if key in ROBUST and r["tag"] in ("chosen", "200K"):
            if r["data"] == "synth": C.append(dict({k: r[k] for k in keys if k in r}, m=ROBUST[key]))
            r["tag"] = "refine best" if r["tag"] == "chosen" else "refine best 200K"
    J = []
    for c in C:
        J.append((dict(c, data="synth"), ROBUST_PATHS, (41, 42, 43, 44), 6000))
        J.append((dict(c, data="real"), ["real"], (45,), 8000))
    with Pool(4) as p:
        R = p.map(job_final, J, chunksize=1)
    for r in R: r["robust"] = True
    json.dump(FIN + R, open("opt_v6_final.json", "w"), indent=0)
    for r in R:
        print(f"{r['prog'][:38]:38s} {r['instr']:7s} {r['size']//1000:>3}K {r['tag']:10s} {r['data']:5s} k={r['k']:>2} m={r['m']:.2f} X={r['X']/1000:5.1f}K "
              f"EV/mo={r['EV_month']:6.0f}±{r['CI']:4.0f} P={r['P']:.3f} days={r['days']:5.1f}", flush=True)
