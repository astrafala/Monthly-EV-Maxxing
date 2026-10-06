"""
Version 9 end-of-run audit: independent checks of every output before the document is released.
    python3 audit_v9.py          the results (run after rerun_v9.sh)
    python3 audit_v9.py doc      the built document as well (run after build_math_v9.py)
Writes audit_v9.json; every check prints PASS or FAIL.

  stalls      no account ended by the stall detector in any stage (search, validation, checks, sensitivities, portfolios)
  coverage    the grid holds every setting once; every programme and market has a chosen, validated setting
  choice      each chosen setting is the best refined one inside the plan's limits, and respects them
  replay      every chosen 100K CFD setting and both futures settings replayed on the rule-test path, trade by trade: risk below every firm's 2%
              rules, the day's loss inside the firm's allowance, the day's profit inside the caps, FXIFY's best day,
              GFT's day cap, Maven's ceiling and 30-day window (by close date), the 10-minute gap from the exit time, the
              take-profit distance, the margin cap at every entry, Maven's 1:1.5, whole volume steps, no balance below a
              static floor, filler trades of 3 minutes, Blue Guardian's 3-minute hold, BrightFunded's counted days
  continuing  every final row has a continuing-slot row, with no stall
  budget      the cash dated by the ledger of every finite-budget life never below zero
  chain       the accounting identity of every chain solved for the document, and the cost-free checks against it
  portfolio   the first-year figures recomputed from the lives; no two accounts ever opposite; refusals never add cash
  document    no unfilled placeholder, no nan / None in the text, the headline equal to the recomputed figure
"""
import json, math, random, sys, collections, glob, re, os
import numpy as np
import acct_mc as A, pathfirm as PF, optimize_v9 as O, firms_v9 as F8
from firms_v9 import firm_of

OUT = {}
def check(name, ok, info=""):
    OUT[name] = dict(ok=bool(ok), info=info)
    print(("PASS " if ok else "FAIL ") + name, info, flush=True)

def jl(fn): return [json.loads(l) for l in open(fn) if l.strip()]

GRID = jl("opt_v9_grid.jsonl"); REF = jl("opt_v9_refine.jsonl"); FUT = jl("opt_v9_futures.jsonl")
FIN = json.load(open("opt_v9_final.json"))
VER = json.load(open("verify_v9.json")); SENS = json.load(open("sens_v9.json"))
TESTS = json.load(open("tests_v9.json"))
CONT = json.load(open("continuing_v9.json")) if os.path.exists("continuing_v9.json") else {"rows": []}

# ---------------------------------------------------------------- stalls
def stuck(rows, key=lambda r: (r.get("st") or {}).get("stuck", 0)):
    return sum(1 for r in rows if key(r))
life_files = sorted(glob.glob("lockstep_v9*.json"))
lives = []
for fn in life_files:
    d = json.load(open(fn))
    if isinstance(d, dict) and isinstance(d.get("R"), list): lives += d["R"]
s_counts = dict(grid=stuck(GRID), refine=stuck(REF), futures=stuck(FUT), final=stuck(FIN), continuing=sum(1 for r in CONT["rows"] if r.get("stuck")),
                verify=sum(1 for r in VER.get("programmes", []) if r.get("stuck_simpl")),
                sens=sum(1 for r in SENS if r.get("stuck")), lives=sum(1 for r in lives if r.get("stuck")))
check("stalls", all(v == 0 for v in s_counts.values()) and len(lives) > 0,
      f"rows or lives with a stalled account: {s_counts} ({len(lives):,} portfolio lives read)")

# ---------------------------------------------------------------- coverage
keys = [O._ckey(r) for r in GRID]
cfg_keys = {O._ckey(c) for c in O.configs()}
check("grid_coverage", len(keys) == len(set(keys)) and set(keys) == cfg_keys,
      f"{len(keys):,} grid rows, {len(set(keys)):,} distinct, {len(cfg_keys):,} settings defined")
pairs = {(p, i) for p, f, ms, xs in O.PROGS for i in ms}
chosen = {(r["prog"], r["instr"]): r for r in FIN if r["tag"] == "chosen" and r["size"] == 100_000}
check("final_coverage", pairs <= set(chosen), f"{len(pairs)} programme-market pairs searched, {len(set(chosen) & pairs)} validated")

# ---------------------------------------------------------------- choice and limits
bad = []
for (p, i), r in chosen.items():
    firm = r["firm"]; S = r["size"]; rf = r["L"] / S
    if r["m"] < O.CAP_M - 1e-9: bad.append((p, i, "stop below 0.6 sd"))
    if r["m"] < O.m_min(firm, i, rf) - 1e-6: bad.append((p, i, "stop below the margin floor"))
    if r["X"] > O.CAP_X * S + 1e-6: bad.append((p, i, "payout target above 30%"))
    if rf > 0.0175 + 1e-9: bad.append((p, i, "risk above 1.75%"))
    if firm in O.L_MAX and rf > O.L_MAX[firm] + 1e-9: bad.append((p, i, "risk above the firm's guidance"))
    if firm == "Maven" and r["X"] > 4_900 + 1e-6: bad.append((p, i, "Maven payout target above $4,900"))
    if firm == "GFT" and r["X1"] > min(0.06 * S, 10_000) + 1e-6: bad.append((p, i, "GFT first payouts above their cap"))
best = {(c["prog"], c["instr"]): c for c in O.choose(REF)}
mism = [(p, i) for (p, i), c in best.items() if (p, i) in chosen and
        (abs(c["m"] - chosen[(p, i)]["m"]) > 1e-9 or c["k"] != chosen[(p, i)]["k"] or abs(c["X"] - chosen[(p, i)]["X"]) > 1e-6
         or abs(c["L"] - chosen[(p, i)]["L"]) > 1e-6)]
check("choice", not bad and not mism, f"limit violations {bad or 'none'}; chosen setting differs from the refined best: {mism or 'none'}")

# ---------------------------------------------------------------- replay of every chosen setting, trade by trade
class Spy(PF.PathTrader):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.log = []
    def trade(self, l, w, clock=None, flat_weekend=False, opts=None):
        pnl, h = super().trade(l, w, clock, flat_weekend, opts)
        self.log.append(dict(t_in=self.last_entry, t_out=self.last_exit, l=l, w=w, pnl=pnl, kind=(opts or {}).get("kind", "trade"),
                             terminal=bool((opts or {}).get("terminal")), **self.last_info))
        return pnl, h

def replay(r, n=int(os.environ.get("AUDIT_N", 150)), data="synth901y4", seed=17):
    c = {k: r[k] for k in O.FINAL_KEYS if k in r}
    F = O.firm_rules(c); S = F["size"]; rng = random.Random(seed); M = PF.market(c["instr"], data)
    s = c["m"] * M["sig"]; lev = F.get("lev"); sp = PF.lot_spec(M)
    v = collections.Counter(); worst = collections.defaultdict(lambda: -1e18); ntr = 0
    def days(log, st, cap, dcap=None):
        by = collections.OrderedDict()
        for (tag, te, xb, pnl, tx, kind, dur) in log: by.setdefault(int(te // A.DAY), []).append((xb, pnl))
        for d, tl in by.items():
            run = 0.0; low = 0.0
            for xb, pnl in tl: run += pnl; low = min(low, run)
            if st.get("dll") and not st.get("dll_trailing"):
                worst["day_loss_over_allowance"] = max(worst["day_loss_over_allowance"],
                                                       -low - A._dll_at(st["dll"], A._mode(st), S, tl[0][0]))
            if cap: worst["day_profit_over_cap"] = max(worst["day_profit_over_cap"], run - cap)
            if dcap: worst["day_profit_over_firm_day_cap"] = max(worst["day_profit_over_firm_day_cap"], run - dcap)
    for _ in range(n):
        tr = Spy(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
        clock = rng.random() * A.DAY; ok = True; segs = []
        for st in F["phases"]:
            A.TRADELOG = []; n0 = len(tr.log); t0 = clock
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            caps = [x for x in (st.get("best") and st["best"] * st["target"], st.get("conc") and st["conc"] * st["target"]) if x]
            days(A.TRADELOG, st, min(caps) if caps else None)
            segs.append(("eval", st, A.TRADELOG, tr.log[n0:], ok))
            if not ok: break
        if ok:
            A.TRADELOG = []; n0 = len(tr.log); fd = F["funded"]
            A.run_funded(fd, tr, rng, F, clock, c["X1"], c["X"])
            days(A.TRADELOG, fd, None, fd.get("day_profit_cap"))
            segs.append(("funded", fd, A.TRADELOG, tr.log[n0:], None))
        A.TRADELOG = None
        for kind, st, tl, sl, passed in segs:
            assert len(tl) == len(sl)
            if kind == "eval" and passed and F.get("day_min_minutes"):          # BrightFunded: counted days held a minute
                dd = {int(t["t_in"] // A.DAY) for t in sl if t["dur"] >= F["day_min_minutes"] - 1e-9}
                worst["brightfunded_days_short"] = max(worst["brightfunded_days_short"], st.get("min_days", 0) - len(dd))
            for (tag, te, xb, pnl, tx, k_, dur), t in zip(tl, sl):
                ntr += 1
                vol = t["vol"]
                worst["volume_off_step"] = max(worst["volume_off_step"], abs(vol / sp["step"] - round(vol / sp["step"])))
                worst["volume_below_smallest"] = max(worst["volume_below_smallest"], sp["vmin"] - vol)
                if not st.get("eod"):                                         # static floor: never below it
                    worst["balance_below_static_floor"] = max(worst["balance_below_static_floor"], -(xb + pnl) - st["dd"])
                if t["kind"] == "filler":
                    if not t["breach"]: worst["filler_not_3_minutes"] = max(worst["filler_not_3_minutes"], abs(t["dur"] - 3.0))
                    continue
                if F.get("hold_min") and not t["breach"]:
                    worst["blue_guardian_under_3_minutes"] = max(worst["blue_guardian_under_3_minutes"], 3.0 - t["dur"])
                if c.get("kind", "cfd") == "cfd" and not t["terminal"]:      # the firms' 2% rules are CFD-firm rules
                    worst["loss_share_of_account"] = max(worst["loss_share_of_account"], -pnl / S)
                worst["target_distance_short_of_0.6sd"] = max(worst["target_distance_short_of_0.6sd"], PF.WMIN_SD - t["td"])
                risk = t["notional"] * s
                if lev and not t["terminal"]:
                    lv = lev[0] if kind == "eval" else lev[1]
                    lim = lv * s * (lev[2] * (S + xb) if kind == "eval" else min(lev[2] * (S + xb), lev[3] * S))
                    worst["risk_over_margin_cap"] = max(worst["risk_over_margin_cap"], risk - lim - sp["step"] * PF.unit_value(M, 100.0) * s)
                if st.get("min_rr") and not t["terminal"] and vol > sp["vmin"] + 1e-12:
                    wn = t["td"] * M["sig"] * t["notional"] - M["cost"] * t["notional"]          # the win at the take-profit, net of cost
                    worst["below_min_reward_risk"] = max(worst["below_min_reward_risk"], st["min_rr"] * risk - wn)
            for a, b in zip(sl, sl[1:]):
                worst["gap_short_of_10min"] = max(worst["gap_short_of_10min"], PF.GAP_MIN - (b["t_in"] - a["t_out"]) * 60.0)
            if kind == "funded":
                fdx = st
                if fdx.get("profit_ceiling") or fdx.get("roll_profit_cap") or fdx.get("best"):
                    days_p = {}; closes = []
                    for j, ((tag, te, xb, pnl, tx, k_, dur), t) in enumerate(zip(tl, sl)):
                        xa = xb + pnl
                        if fdx.get("profit_ceiling"): worst["maven_profit_over_ceiling"] = max(worst["maven_profit_over_ceiling"], xa - fdx["profit_ceiling"])
                        closes.append((t["t_out"], pnl))                     # when the trade closed
                        d = int(te // A.DAY); days_p[d] = days_p.get(d, 0.0) + pnl
                        amt = (xa - tl[j + 1][2]) if j + 1 < len(tl) else 0.0
                        if amt > 1.0 and fdx.get("best") and not fdx.get("q_days"):   # FXIFY (Apex's is a cycle rule)
                            worst["fxify_best_day_over_25pct"] = max(worst["fxify_best_day_over_25pct"], max(days_p.values()) - fdx["best"] * amt)
                    if fdx.get("roll_profit_cap"):        # every window of 30 days: the largest sum of closes inside one
                        cap, w30 = fdx["roll_profit_cap"]; cs = sorted(closes)
                        for b in range(len(cs)):
                            run = 0.0
                            for a in range(b, -1, -1):
                                if cs[b][0] - cs[a][0] >= w30 * A.DAY: break
                                run += cs[a][1]
                                worst["maven_30d_over_10000"] = max(worst["maven_30d_over_10000"], run - cap)
    return ntr, dict(worst)

LIM = {"loss_share_of_account": 0.02 - 1e-9, "day_loss_over_allowance": 0.0, "day_profit_over_cap": 1.0,
       "day_profit_over_firm_day_cap": 1e-6, "target_distance_short_of_0.6sd": 1e-6, "risk_over_margin_cap": 1e-6,
       "below_min_reward_risk": 1e-6, "gap_short_of_10min": 1e-6, "maven_profit_over_ceiling": 1e-6,
       "maven_30d_over_10000": 1e-6, "fxify_best_day_over_25pct": 0.0, "volume_off_step": 1e-6, "volume_below_smallest": 1e-12,
       "balance_below_static_floor": 1e-6, "filler_not_3_minutes": 1e-9, "blue_guardian_under_3_minutes": 1e-9,
       "brightfunded_days_short": 0}
viol = []; tot_tr = 0; W = {}
futs = {(r["prog"], r["instr"]): r for r in FIN if r["tag"] == "chosen" and r.get("kind") == "fut"}
for (p, i), r in sorted(chosen.items()) + sorted(futs.items()):
    ntr, w = replay(r); tot_tr += ntr; W[f"{p} | {i}"] = w
    for k, v in w.items():
        if k == "loss_share_of_account":
            if v >= LIM[k]: viol.append((p, i, k, round(v, 5)))
        elif v > LIM[k]: viol.append((p, i, k, round(v, 4)))
check("replay", not viol, f"{tot_tr:,} trades of {len(W)} chosen settings replayed; violations: {viol or 'none'}")
OUT["replay_worst"] = W

# ---------------------------------------------------------------- chain
gaps = [abs(r["identity_gap"]) for r in VER.get("programmes", [])]
check("chain_identity", gaps and max(gaps) < 1e-6, f"largest accounting-identity gap over {len(gaps)} chosen programmes: {max(gaps) if gaps else None:.2e}")
Z = VER.get("zero", {})
if Z:
    z1 = (Z["P1"] - Z["P1_chain"]) / (Z["P1_ci"] / 1.96); z2 = (Z["W"] - Z["W_chain"]) / (Z["W_ci"] / 1.96)
    check("chain_zero_cost", abs(z1) < 3.5 and abs(z2) < 3.5,
          f"cost-free FTMO, engine against chain: phase 1 {Z['P1']:.4f} against {Z['P1_chain']:.4f} (z = {z1:+.2f}); "
          f"funded withdrawal {Z['W']:,.0f} against {Z['W_chain']:,.0f} (z = {z2:+.2f})")
check("tests", all(v["ok"] for v in TESTS.values()), f"{sum(v['ok'] for v in TESTS.values())} of {len(TESTS)} rule tests pass")

# ---------------------------------------------------------------- continuing slots, intervals, the generator's bound
ck = {(r["prog"], r["instr"], r["size"], r["tag"]) for r in CONT["rows"]}
miss = [(r["prog"], r["instr"], r["size"], r["tag"]) for r in FIN if (r["prog"], r["instr"], r["size"], r["tag"]) not in ck]
check("continuing", not miss and CONT["rows"] and all(len(r["per_path"]) == 16 for r in CONT["rows"]),
      f"{len(CONT['rows'])} continuing rows for {len(FIN)} final rows; missing {miss or 'none'}; {sum(r['attempts'] for r in CONT['rows']):,} attempts in the measured years")
check("pass_rate_intervals", all(r.get("P_CI") and r["P_CI"] >= r.get("P_CI_iid", 0) - 1e-12 for r in FIN),
      "every final row has a pass-rate interval at least the attempt-level one (cluster-robust where wider)")
eps = [r["st"]["bridge_eps"] / max(r["st"]["n"], 1) for r in FIN if r.get("st")]
check("bridge_bound", eps and max(eps) < 1e-6, f"the generator's error bound, largest per trade over every final row: {max(eps) if eps else None:.2e}")
mv = VER.get("maven")
if mv:
    zp = (mv["paid"] - mv["paid_chain"]) / max(mv["paid_ci"] / 1.96, 1e-9); zq = (mv["q1"] - mv["q1_chain"]) / max(mv["q1_ci"] / 1.96, 1e-9)
    check("maven_stopping_set", abs(zp) < 3.5 and abs(zq) < 3.5,
          f"Maven, engine against chain on one stopping set: paid per cycle {mv['paid']:,.2f} against {mv['paid_chain']:,.2f} (z = {zp:+.2f}); "
          f"first cycle {mv['q1']:.4f} against {mv['q1_chain']:.4f} (z = {zq:+.2f})")

# ---------------------------------------------------------------- portfolio
main = json.load(open("lockstep_v9.json")) if os.path.exists("lockstep_v9.json") else None
if main:
    import lockstep_portfolio_v9 as LP
    R = [r for r in main["R"] if r["p"] == LP.REC and r["months"] == 12]
    ev = float(np.mean([np.mean(r["monthly"][:12]) for r in R]))
    ci = 1.96 * float(np.std([np.mean(r["monthly"][:12]) for r in R])) / math.sqrt(len(R))
    OUT["recomputed_headline"] = dict(ev=ev, ci=ci, lives=len(R))
    conf = sum(r.get("conflicts", 0) for r in lives)
    tier = [np.mean(r["refusal"]["tiered"]) for r in R]; harsh = [np.mean(r["refusal"]["harsh"]) for r in R]
    check("portfolio", conf == 0 and np.mean(harsh) <= np.mean(tier) <= ev + 1e-6,
          f"recommended plan, first year: {ev:,.0f} ± {ci:,.0f} a month over {len(R):,} lives; opposite positions {conf}; "
          f"refusals: tiered {np.mean(tier):,.0f}, harsh {np.mean(harsh):,.0f} (on average at most the baseline: a refusal removes payouts, and the fees it saves are smaller)")

# ---------------------------------------------------------------- finite budgets: dated cash
if os.path.exists("lockstep_v9_budget.json"):
    B = [r for r in json.load(open("lockstep_v9_budget.json"))["R"] if r["kw"].get("budget")]
    low = min(r["kw"]["budget"] + r["trough"] for r in B)
    check("budget_dated_cash", low >= -1e-6 and all(r["wallet_low"] >= -1e-6 for r in B),
          f"{len(B):,} budget lives: lowest cash dated by the ledger {low:,.2f}; lowest wallet balance {min(r['wallet_low'] for r in B):,.2f}")

# ---------------------------------------------------------------- document
if len(sys.argv) > 1 and sys.argv[1] == "doc":
    import html as H
    h = open("prop_firm_math_v9.html").read()
    txt = H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)))
    ph = sorted(set(re.findall(r"\[\[[A-Z0-9_]+\]\]", h)))
    bad_words = [w for w in (" nan", "NaN", " None", " inf ", "{usd(", "{pm(") if w in txt]
    check("doc_placeholders", not ph and not bad_words, f"unfilled placeholders {ph or 'none'}; suspicious text {bad_words or 'none'}")
    if main:
        from doc9_common import usd
        check("doc_headline", usd(ev) in txt, f"recomputed headline {usd(ev)} {'found' if usd(ev) in txt else 'NOT found'} in the document")
    try:
        from pypdf import PdfReader
        n = len(PdfReader("The_Prop_Firm_Option_v9_Mathematics.pdf").pages); OUT["pages"] = n
        check("pdf", n > 50, f"{n} pages")
    except ImportError:
        pass

json.dump(OUT, open("audit_v9.json", "w"), indent=1, default=float)
print("all passed" if all(v.get("ok", True) for v in OUT.values() if isinstance(v, dict) and "ok" in v) else "SOME FAILED")
