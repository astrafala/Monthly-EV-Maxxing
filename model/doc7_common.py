"""
Shared data and helpers for the version 7 document (build_math_v7.py). Every number in the document is read from the
version 7 result files below or computed here from them; nothing is typed in by hand except the firms' written rules
(progs_v7.py) and the reference prices of 2 October 2026.
"""
import json, math, re, collections, copy, os
import numpy as np
import analytic_v7 as AN, firms_v7 as F7, calibrate as CB
import optimize_v7 as O
from progs_v7 import P as SHEET
from doc6_common import (usd, sgn, pm, pct, num, r10, r100, k_, kk, esc, table, note, box, formula, t, fig, fill, tex_num, css as css6,
                         PRICE, MNAME, MSHORT, UNIT, S1, S2, S3, S4, NEG, INK, MUT, RULE, TINT, TIERC, DAYS_MONTH, kappa, phi, hours)

def _j(f, default=None):
    return json.load(open(f)) if os.path.exists(f) else default
def _jl(f):
    return [json.loads(l) for l in open(f)] if os.path.exists(f) else []

FIN = _j("opt_v7_final.json", [])
REF = _jl("opt_v7_refine.jsonl")
GRID = _jl("opt_v7_grid.jsonl")
FUTJ = _jl("opt_v7_futures.jsonl")
VER = _j("verify_v7.json", {})
SENS = _j("sens_v7.json", [])
LOCK = _j("lockstep_v7.json", {"R": [], "slots": {}})
LONG = _j("lockstep_v7_long.json", {"R": []})
BUDGET = _j("lockstep_v7_budget.json", {"R": []})
STRESS = _j("lockstep_v7_stress.json", {"R": []})
CORR = _j("lockstep_v7_corr.json", {"R": []})
NEWS = _j("lockstep_v7_news.json", {"R": []})
BEHAV = _j("lockstep_v7_behav.json", {"R": []})
FIN6 = _j("opt_v6_final.json", [])
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
    else: out["lot_value"] = None
    if out["lot_value"]: out["lots"] = out["usd_per_pt"] / out["lot_value"]
    if lev:
        # lev: an int, optimize_v7.LEV's (evaluation, funded, funded cap) or lev_tuple's (evaluation, funded, 0.6, funded cap)
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
