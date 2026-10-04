"""
Shared data and helpers for the version 6 mathematics document (build_math_v6.py).
Every number in the document is read from the files below or computed here from them; nothing is typed in by hand
except the firms' written rules (progs_v6.py) and the reference prices of 2 October 2026.
"""
import json, math, re, collections, copy
import numpy as np
import analytic_v6 as AN, firms_v5 as F5, calibrate as CB
import optimize_v6 as O
from progs_v6 import P as SHEET

FIN = json.load(open("opt_v6_final.json"))
REF = [json.loads(l) for l in open("opt_v6_refine.jsonl")]
GRID = [json.loads(l) for l in open("opt_v6_grid.jsonl")]
FUTG = [json.loads(l) for l in open("opt_v6_futures.jsonl")]
VER = json.load(open("verify_v6.json"))
LOCK = json.load(open("lockstep_v6.json"))
SENS = json.load(open("sens_v6.json"))
EXTRA = json.load(open("extra_v6.json"))
SIG = json.load(open("sigma_v32.json"))
TIMING = json.load(open("timing_v6.json"))
def timing(prog, instr, size=100_000):
    rs = [r for r in TIMING if r["prog"] == prog and r["instr"] == instr and r["size"] == size]
    return rs[0] if rs else None
PRICE = {"US100": 31070.0, "USDJPY": 157.83, "EURUSD": 1.1256, "XAUUSD": 4176.8, "MNQ_fut": 31070.0}   # last hourly closes, 2 Oct 2026
MNAME = {"US100": "Nasdaq 100 CFD (US100)", "USDJPY": "USDJPY", "EURUSD": "EURUSD", "XAUUSD": "gold (XAUUSD)", "MNQ_fut": "micro Nasdaq futures (MNQ)"}
MSHORT = {"US100": "Nasdaq", "USDJPY": "USDJPY", "EURUSD": "EURUSD", "XAUUSD": "gold", "MNQ_fut": "MNQ"}
# what one "point" is on each market, and what a standard lot moves per point
UNIT = {"US100": ("point", 1.0), "USDJPY": ("pip", 0.01), "EURUSD": ("pip", 0.0001), "XAUUSD": ("dollar", 1.0), "MNQ_fut": ("point", 1.0)}
S1, S2, S3, S4, NEG = "#2a78d6", "#eb6834", "#1baf7a", "#8a63d2", "#e34948"
INK, MUT, RULE, TINT = "#15191f", "#5b6370", "#d5dae2", "#f1f4f8"
TIERC = {"A": S1, "B": S3, "D": S2}
DAYS_MONTH = 30.44

def kappa(instr): return CB.INSTR[instr][1] / 100.0
def phi(instr): return CB.INSTR[instr][2] / 100.0
def hours(instr): return CB.INSTR[instr][3]

# ------------------------------------------------------------------ formatting
def usd(x, dec=0):
    if x is None: return "&ndash;"
    s = f"{abs(x):,.{dec}f}"
    return f"&minus;${s}" if x < -0.5 * 10 ** (-dec) else f"${s}"
def sgn(x, dec=0):
    s = f"{abs(x):,.{dec}f}"
    return f"&minus;${s}" if x < 0 else f"+${s}"
def pm(x, ci): return f"{usd(x)} &plusmn; {usd(ci)}"
def pct(x, d=1): return f"{100 * x:.{d}f}%"
def num(x, d=3): return f"{x:,.{d}f}".replace("-", "&minus;")
def r10(x): return int(round(x / 10.0)) * 10
def r100(x): return int(round(x / 100.0)) * 100
def k_(x): return (f"&minus;${abs(x) / 1000:,.1f}K" if x < 0 else f"${x / 1000:,.1f}K")
def kk(size): return f"{size / 1000:g}K"
def esc(s): return s.replace("&", "&amp;") if "&" in s and ";" not in s else s

def table(head, rows, cls="", num_from=1, hl=(), w0=None, cap=None):
    st0 = f' style="width:{w0}"' if w0 else ""
    th = "".join(f'<th class="n">{h}</th>' if i >= num_from else (f"<th{st0}>{h}</th>" if i == 0 else f"<th>{h}</th>") for i, h in enumerate(head))
    body = ""
    for j, r in enumerate(rows):
        tds = "".join(f'<td class="n">{c}</td>' if i >= num_from else f"<td>{c}</td>" for i, c in enumerate(r))
        body += f'<tr class="hl">{tds}</tr>' if j in hl else f"<tr>{tds}</tr>"
    c = f' class="{cls}"' if cls else ""
    out = f"<table{c}><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"
    if cap: out += f'<p class="cap">{cap}</p>'
    return out
def note(txt): return f'<p class="note">{txt}</p>'
def box(title, body, cls="key"): return f'<div class="box {cls}"><h4>{title}</h4>{body}</div>'
def formula(lbl, tex): return f'<div class="formula"><span class="lbl">{lbl}</span>\n$${tex}$$\n</div>'
def t(x, y, s, size=9, anchor="start", fill=MUT, mono=False, weight=400):
    f = "font-family:'IBM Plex Mono',monospace" if mono else "font-family:Archivo,Arial,sans-serif"
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" style="{f}" font-weight="{weight}">{s}</text>'
def fig(svg, cap): return f'<figure>{svg}<figcaption>{cap}</figcaption></figure>'
def fill(txt, subs):
    for _ in range(3):                     # generated sections may themselves contain placeholders
        for k, v in subs.items():
            txt = txt.replace(f"[[{k}]]", str(v))
    left = re.findall(r"\[\[[A-Z0-9_]+\]\]", txt)
    assert not left, left
    return txt
def tex_num(x, d=0):
    s = f"{abs(x):,.{d}f}".replace(",", "{,}")
    return ("-" if x < 0 else "") + s

# ------------------------------------------------------------------ data access
def fin(prog, instr=None, tag="chosen", data="synth", size=None):
    rs = [r for r in FIN if r["prog"] == prog and r["tag"] == tag and r["data"] == data and (instr is None or r["instr"] == instr)
          and (size is None or r["size"] == size)]
    return rs[0] if rs else None
def ver(prog, instr, tag="chosen", size=None):
    rs = [r for r in VER["programmes"] if r["prog"] == prog and r["instr"] == instr and r["tag"] == tag and (size is None or r["size"] == size)]
    return rs[0] if rs else None
def refs(prog, instr): return [r for r in REF if r["prog"] == prog and r["instr"] == instr]
def grids(prog, instr): return [r for r in GRID if r["prog"] == prog and r["instr"] == instr]
def sens(tag, prog=None, instr=None):
    return [r for r in SENS if r["tag"] == tag and (prog is None or r["prog"] == prog) and (instr is None or r["instr"] == instr)]
def rules(prog, size=100_000, kind="cfd", fee=None, override=None):
    return F5.rules_for(prog, size, kind, fee, override)
def firm_of(prog): return F5.firm_of(prog)
def tier(prog): return F5.TIER.get(firm_of(prog), "?")
def binom_ci(P, n): return 1.96 * math.sqrt(max(P * (1 - P), 1e-12) / n)

def trade_numbers(instr, m, L, w, lev=None, size=100_000):
    """everything about one bracket at stop m (hourly sd), risk L and net win w"""
    sig = SIG[instr]; kap = kappa(instr); fi = phi(instr); price = PRICE[instr]
    s = m * sig; N = L / s; c = kap * N; rho = c / L
    unit, tick = UNIT[instr]
    stop_pts = s * price / tick
    u = s * (w + c) / L; tgt_pts = u * price / tick
    p = L / (L + w + c); v = L * (w + c)
    a, b = 1.0, (w + c) / L      # stop and target in units of the stop distance
    dur = m * m * a * b; dur_win = m * m * (b * b + 2 * a * b) / 3; dur_loss = m * m * (a * a + 2 * a * b) / 3
    out = dict(sig=sig, kappa=kap, phi=fi, price=price, s=s, N=N, c=c, rho=rho, unit=unit, tick=tick, stop_pts=stop_pts,
               usd_per_pt=L / stop_pts, u=u, tgt_pts=tgt_pts, p=p, mean=-c, var=v, sd=math.sqrt(v), fin_night=fi * N,
               dur=dur, dur_win=dur_win, dur_loss=dur_loss, units=N / price)
    if instr == "USDJPY": out["lot_value"] = 100_000 * tick / price         # $ per pip per standard lot (100,000 USD)
    elif instr == "EURUSD": out["lot_value"] = 100_000 * tick                # $10 per pip per lot (100,000 EUR)
    elif instr == "XAUUSD": out["lot_value"] = 100.0                         # 100 oz per lot: $100 per $1
    elif instr == "MNQ_fut": out["lot_value"] = 2.0                          # MNQ: $2 per index point
    else: out["lot_value"] = None                                            # index CFDs: read $ per point per lot from the platform
    if out["lot_value"]: out["lots"] = out["usd_per_pt"] / out["lot_value"]
    if lev:
        out["margin"] = N / lev; out["margin_pct"] = N / lev / size; out["lev"] = lev
        out["m_min"] = (L / size) / (0.6 * lev * sig)
    return out

def lev_of(prog, instr):
    f = firm_of(prog)
    return O.LEV.get(f, {}).get(instr)

# ------------------------------------------------------------------ the stylesheet (version 5's, plus what this document adds)
def css():
    s = open("prop_firm_option_v5.html").read()
    i = s.index("<style>"); j = s.index("</style>", i)
    base = s[i + 7:j]
    extra = """
.note { font-family: "Archivo", Arial, sans-serif; font-size: 8.4pt; color: var(--muted); margin: -1mm 0 3.5mm; }
.big { font-family: "Archivo", Arial, sans-serif; font-size: 40pt; font-weight: 800; font-stretch: 110%; line-height: 1; margin: 2mm 0 1mm; color: var(--ink); }
.big small { font-size: 13pt; font-weight: 600; color: var(--muted); font-stretch: 100%; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4mm; margin: 4mm 0 5mm; }
.kpi { border-top: 1.2pt solid var(--ink); padding-top: 2mm; font-family: "Archivo", Arial, sans-serif; }
.kpi .v { font-size: 15pt; font-weight: 750; font-family: "Archivo", Arial, sans-serif; }
.kpi .l { font-size: 7.8pt; color: var(--muted); line-height: 1.3; }
.steps td.n { font-size: 7.6pt; }
table.heat td.n { font-size: 7.2pt; padding: 1.1mm 1.2mm; }
table.heat th.n { font-size: 7pt; padding: 1.1mm 1.2mm; }
table.tight td, table.tight th { padding: 1.1mm 1.6mm; }
.katex { font-size: 1.04em; }
.formula .katex-display { margin: 0.6mm 0; }
.katex-display { margin: 2.2mm 0; overflow-x: hidden; overflow-y: hidden; }
.calc { font-family: "Source Serif 4", Georgia, serif; background: #fbfcfd; border: 0.6pt solid var(--rule); padding: 2.5mm 4mm; margin: 2.5mm 0 3.5mm; break-inside: avoid; }
.calc p { margin: 0 0 1.4mm; }
.pp { break-inside: avoid; }
h3.sub { font-size: 10.4pt; margin: 4mm 0 1.5mm; color: var(--ink); }
.tierA { color: #2a78d6; } .tierB { color: #138a5f; } .tierD { color: #c4511d; }
"""
    return base + extra
