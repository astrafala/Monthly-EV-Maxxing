"""
Shared data and helpers for the version 8 document (build_math_v9.py). Every number in the document is read from the
version 8 result files below or computed here from them; nothing is typed in by hand except the firms' written rules
(progs_v9.py) and the reference prices of 2 October 2026.
"""
import json, math, re, collections, copy, os
import numpy as np
import analytic_v9 as AN, firms_v9 as F7, calibrate as CB
import optimize_v9 as O
from progs_v9 import P as SHEET
from doc6_common import (usd, sgn, pm, pct, num, r10, r100, k_, kk, esc, table, note, box, formula, t, fig, fill, tex_num, css as css6,
                         PRICE, MNAME, MSHORT, UNIT, S1, S2, S3, S4, NEG, INK, MUT, RULE, TINT, TIERC, DAYS_MONTH, kappa, phi, hours)

def _j(f, default=None):
    return json.load(open(f)) if os.path.exists(f) else default
def _jl(f):
    return [json.loads(l) for l in open(f)] if os.path.exists(f) else []

FIN = _j("opt_v9_final.json", [])
REF = _jl("opt_v9_refine.jsonl")
GRID = _jl("opt_v9_grid.jsonl")
FUTJ = _jl("opt_v9_futures.jsonl")
VER = _j("verify_v9.json", {})
SENS = _j("sens_v9.json", [])
LOCK = _j("lockstep_v9.json", {"R": [], "slots": {}})
LONG = _j("lockstep_v9_long.json", {"R": []})
BUDGET = _j("lockstep_v9_budget.json", {"R": []})
STRESS = _j("lockstep_v9_stress.json", {"R": []})
CORR = _j("lockstep_v9_corr.json", {"R": []})
NEWS = _j("lockstep_v9_news.json", {"R": []})
BEHAV = _j("lockstep_v9_behav.json", {"R": []})
FIN6 = _j("opt_v6_final.json", [])
FIN7 = _j("opt_v7_final.json", [])
FIN8 = _j("opt_v8_final.json", [])
LOCK8 = _j("lockstep_v8.json", {"R": [], "slots": {}})
CONTJ = _j("continuing_v9.json", {"rows": []})
CONT = {(r["prog"], r["instr"], r["size"], r["tag"]): r for r in CONTJ["rows"]}
LOCK6 = _j("lockstep_v6.json", {"R": [], "slots": {}})
SIG = json.load(open("sigma_v32.json"))
TIER = F7.TIER

# ------------------------------------------------------------------ data access
def fin(prog, instr=None, tag=None, size=None):
    rs = [r for r in FIN if r["prog"] == prog and (instr is None or r["instr"] == instr) and (size is None or r["size"] == size)
          and (tag is None or r["tag"] == tag)]
    if size is None: rs = [r for r in rs if r["size"] == (50_000 if r.get("kind") == "fut" else 100_000)] or rs
    return max(rs, key=lambda r: r["EV_month"]) if rs else None
def fin6(prog, instr):
    rs = [r for r in FIN6 if r["prog"] == prog and r["instr"] == instr and r["tag"] == "chosen" and r["data"] == "synth" and r["size"] in (100_000, 50_000)]
    return rs[0] if rs else None
def fin7(prog, instr):
    rs = [r for r in FIN7 if r["prog"] == prog and r["instr"] == instr and r["tag"] == "chosen" and r["size"] in (100_000, 50_000)]
    return rs[0] if rs else None
def fin8(prog, instr):
    rs = [r for r in FIN8 if r["prog"] == prog and r["instr"] == instr and r["tag"] == "chosen" and r["size"] in (100_000, 50_000)]
    return rs[0] if rs else None
def cont(r):
    """the continuing-slot row of a final row (continuing_v9.json), or None"""
    return CONT.get((r["prog"], r["instr"], r["size"], r["tag"]))
def p_ci(r):
    """95% interval of a pass rate: the larger of the cluster-robust and the attempt-level interval (version 9)"""
    return r.get("P_CI", binom_ci(r["P"], r["n"]))
def path_rates(r):
    """EV per month on each path of a row (from its per-path sums)"""
    c = r.get("clu")
    if not c: return None
    return np.array([30.44 * v / d for v, d in zip(c["V"], c["D"])])
def paired_diff(a, b):
    """mean and 95% interval of the paired per-path difference a - b of two rows run on the same paths and seeds; the ratio
    estimates' difference with its cluster interval (Student t, G - 1 degrees of freedom)"""
    ca, cb = a.get("clu"), b.get("clu")
    if not ca or not cb or len(ca["V"]) != len(cb["V"]): return None
    G = len(ca["V"])
    Va, Da, Vb, Db = (np.array(x) for x in (ca["V"], ca["D"], cb["V"], cb["D"]))
    ra, rb = Va.sum() / Da.sum(), Vb.sum() / Db.sum()
    u = (Va - ra * Da) / Da.sum() - (Vb - rb * Db) / Db.sum()          # influence of each path on the difference
    se = math.sqrt(G / (G - 1) * np.sum(u ** 2))
    return 30.44 * (ra - rb), 30.44 * O.tq(G - 1) * se
def sum_ci(items):
    """the sum of n_j x rate_j over programme rows that share their paths, with the full covariance: items = [(row, n)];
    rows are final rows (per-path sums) or continuing rows (per-path rates). Returns (sum, 95% half-width, clusters)"""
    if not items: return 0.0, 0.0, 0
    if all("per_path" in r for r, n in items):
        P = np.array([[n * x for x in r["per_path"]] for r, n in items]).sum(0); G = len(P)
        return float(P.mean()), float(O.tq(G - 1) * P.std(ddof=1) / math.sqrt(G)), G
    G = len(items[0][0]["clu"]["V"]); U = np.zeros(G); tot = 0.0
    for r, n in items:
        V, D = np.array(r["clu"]["V"]), np.array(r["clu"]["D"]); ra = V.sum() / D.sum()
        U += n * 30.44 * (V - ra * D) / D.sum(); tot += n * 30.44 * ra
    return float(tot), float(O.tq(G - 1) * math.sqrt(G / (G - 1) * np.sum(U ** 2))), G
def two_barrier_exit(a, b, T, K=40):
    """P(a driftless Brownian motion with unit variance per unit time, started at 0, leaves (-a, b) by time T): one minus
    the image-series probability of staying inside"""
    from math import erf, sqrt
    W = a + b; x0 = a; sT = sqrt(T)
    Phi = lambda z: 0.5 * (1.0 + erf(z / sqrt(2.0)))
    stay = 0.0
    for k in range(-K, K + 1):
        stay += (Phi((W - x0 - 2 * k * W) / sT) - Phi((-x0 - 2 * k * W) / sT)
                 - Phi((W + x0 - 2 * k * W) / sT) + Phi((x0 - 2 * k * W) / sT))
    return 1.0 - stay

def ver(prog, instr):
    rs = [r for r in VER.get("programmes", []) if r["prog"] == prog and r["instr"] == instr]
    return rs[0] if rs else None
def refs(prog, instr): return [r for r in REF if r["prog"] == prog and r["instr"] == instr]
def grids(prog, instr): return [r for r in GRID if r["prog"] == prog and r["instr"] == instr]
def sens(tag, prog=None, instr=None):
    return [r for r in SENS if r["tag"] == tag and (prog is None or r["prog"] == prog) and (instr is None or r["instr"] == instr)]
def firm_of(prog): return F7.firm_of(prog)
def tier(prog): return TIER.get(firm_of(prog), "?")
def binom_ci(P, n): return 1.96 * math.sqrt(max(P * (1 - P), 1e-12) / n)

def rules(prog, size=100_000, kind="cfd", fee=None, override=None, instr=None):
    c = dict(prog=prog, firm=firm_of(prog), instr=instr or "US100", size=size, kind=kind, fee=fee, override=override)
    F = F7.rules_for(prog, size, kind, fee, override)
    if kind == "cfd" and instr: F["lev"] = O.lev_tuple(firm_of(prog), instr)
    return F
def rules_of(r):
    return rules(r["prog"], r["size"], r.get("kind", "cfd"), r.get("fee"), r.get("override"), r["instr"])

def lev_of(prog, instr):
    t_ = O.LEV.get(firm_of(prog), {}).get(instr)
    return t_
def mmin_of(prog, instr, L_frac):
    return O.m_min(firm_of(prog), instr, L_frac) if lev_of(prog, instr) else None

def chain_of(r, cost_mult=1.0, F=None):
    """the exact chain at a result row's setting (memoised)"""
    key = (r["prog"], r["instr"], r["size"], r["m"], r["k"], r["L"], r["X1"], r["X"], cost_mult, id(F) if F else None)
    if key not in _CH:
        _CH[key] = AN.programme(r["prog"], r["instr"], r["m"], r["k"], r["X1"], r["X"], L=r["L"], size=r["size"],
                                F=F or rules_of(r), cost_mult=cost_mult, kind=r.get("kind", "cfd"))
    return _CH[key]
_CH = {}

def trade_numbers(instr, m, L, w, lev=None, size=100_000, cost_mult=1.0):
    """everything about one bracket at stop m (hourly sd), risk L and net win w; lev = (eval, funded, cap, funded cap) or int"""
    sig = SIG[instr]; kap = kappa(instr) * cost_mult; price = PRICE[instr]
    s = m * sig; N = L / s; c = kap * N; rho = c / L
    unit, tick = UNIT[instr]
    stop_pts = s * price / tick
    u = s * (w + c) / L; tgt_pts = u * price / tick
    p = L / (L + w + c); v = L * (w + c)
    a, b = 1.0, (w + c) / L
    dur = m * m * a * b; dur_win = m * m * (b * b + 2 * a * b) / 3; dur_loss = m * m * (a * a + 2 * a * b) / 3
    out = dict(sig=sig, kappa=kap, price=price, s=s, N=N, c=c, rho=rho, unit=unit, tick=tick, stop_pts=stop_pts,
               usd_per_pt=L / stop_pts, u=u, tgt_pts=tgt_pts, p=p, mean=-c, var=v, sd=math.sqrt(v), dur=dur, dur_win=dur_win,
               dur_loss=dur_loss, units=N / price)
    if instr == "USDJPY": out["lot_value"] = 100_000 * tick / price
    elif instr == "EURUSD": out["lot_value"] = 100_000 * tick
    elif instr == "XAUUSD": out["lot_value"] = 100.0
    elif instr == "MNQ_fut": out["lot_value"] = 2.0
    else: out["lot_value"] = 1.0                       # index CFD: one index unit a lot, $1 a point (pathfirm.LOTS)
    out["lots"] = out["usd_per_pt"] / out["lot_value"]
    step = 1.0 if instr == "MNQ_fut" else 0.01         # volumes rounded down to the step, never below the smallest
    out["vol"] = max(step, math.floor(out["lots"] / step + 1e-9) * step)
    out["l_round"] = out["vol"] * out["lot_value"] * stop_pts
    if lev:
        # lev: an int, optimize_v9.LEV's (evaluation, funded, funded cap) or lev_tuple's (evaluation, funded, 0.6, funded cap)
        lf = lev[1] if isinstance(lev, tuple) else lev
        if isinstance(lev, tuple) and len(lev) == 3: cap = min(lev[2], 0.6)
        elif isinstance(lev, tuple) and len(lev) == 4: cap = lev[3] if lev[3] < 1 else lev[2]
        else: cap = 0.6
        out["margin"] = N / lf; out["margin_pct"] = N / lf / size; out["lev"] = lf; out["cap"] = cap
        out["m_min"] = (L / size) / (cap * lf * sig)
    return out

def css():
    return css6() + """
.appx td { vertical-align: top; }
.verdict { font-family: "Archivo", Arial, sans-serif; font-size: 7.6pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #138a5f; }
"""

def ci_of(r):
    """95% interval of a result row: the larger of the attempt-level and the cluster-robust interval, the latter with Student's
    t for G - 1 degrees of freedom (rows written before that correction stored the cluster interval with 1.96)"""
    G = r.get("clusters") or 1
    cl = r.get("CI_cluster", 0.0)
    if G > 1 and not r.get("t_adjusted"): cl = cl * O.tq(G - 1) / 1.96
    return max(r.get("CI_iid", r.get("CI", 0.0)), cl)

def td(x, dec=0):
    """a dollar amount inside TeX: -\\$9,896 rather than \\$-9,896"""
    return ("-" if x < 0 else "") + "\\$" + f"{abs(x):,.{dec}f}"
