"""
Version 8 end-of-run audit: independent checks of every output before the document is released.
    python3 audit_v8.py          the results (run after rerun_v8.sh)
    python3 audit_v8.py doc      the built document as well (run after build_math_v8.py)
Writes audit_v8.json; every check prints PASS or FAIL.

  stalls      no account ended by the stall detector in any stage (search, validation, checks, sensitivities, portfolios)
  coverage    the grid holds every setting once; every programme and market has a chosen, validated setting
  choice      each chosen setting is the best refined one inside the plan's limits, and respects them
  replay      every chosen 100K CFD setting and both futures settings replayed on the rule-test path, trade by trade: risk below every firm's 2%
              rules, the day's loss inside the firm's allowance, the day's profit inside the caps, FXIFY's best day,
              GFT's day cap, Maven's ceiling and 30-day window, the 10-minute gap, the take-profit distance, the margin
              cap at every entry, Maven's 1:1.5
  chain       the accounting identity of every chain solved for the document, and the cost-free checks against it
  portfolio   the first-year figures recomputed from the lives; no two accounts ever opposite; refusals never add cash
  document    no unfilled placeholder, no nan / None in the text, the headline equal to the recomputed figure
"""
import json, math, random, sys, collections, glob, re, os
import numpy as np
import acct_mc as A, pathfirm as PF, optimize_v8 as O, firms_v8 as F8
from firms_v8 import firm_of

OUT = {}
def check(name, ok, info=""):
    OUT[name] = dict(ok=bool(ok), info=info)
    print(("PASS " if ok else "FAIL ") + name, info, flush=True)

def jl(fn): return [json.loads(l) for l in open(fn) if l.strip()]

GRID = jl("opt_v8_grid.jsonl"); REF = jl("opt_v8_refine.jsonl"); FUT = jl("opt_v8_futures.jsonl")
FIN = json.load(open("opt_v8_final.json"))
VER = json.load(open("verify_v8.json")); SENS = json.load(open("sens_v8.json"))
TESTS = json.load(open("tests_v8.json"))

# ---------------------------------------------------------------- stalls
def stuck(rows, key=lambda r: (r.get("st") or {}).get("stuck", 0)):
    return sum(1 for r in rows if key(r))
life_files = sorted(glob.glob("lockstep_v8*.json"))
lives = []
for fn in life_files:
    d = json.load(open(fn))
    if isinstance(d, dict) and isinstance(d.get("R"), list): lives += d["R"]
s_counts = dict(grid=stuck(GRID), refine=stuck(REF), futures=stuck(FUT), final=stuck(FIN),
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
    def trade(self, l, w, clock=None, flat_weekend=False):
        i, waited = PF.entry_index(self.M, self._idx(clock), flat_weekend, self.flat_daily)
        pnl, h = super().trade(l, w, clock, flat_weekend)
        self.log.append(dict(t_in=clock + waited, l=l, w=w, pnl=pnl, i=i, exit=self.st.last_exit))
        return pnl, h

def replay(r, n=int(os.environ.get("AUDIT_N", 150)), data="synth901y4", seed=17):
    c = {k: r[k] for k in O.FINAL_KEYS if k in r}
    F = O.firm_rules(c); S = F["size"]; rng = random.Random(seed); M = PF.market(c["instr"], data)
    s = c["m"] * M["sig"]; lev = F.get("lev")
    v = collections.Counter(); worst = collections.defaultdict(lambda: -1e18); ntr = 0
    def days(log, st, cap, dcap=None):
        by = collections.OrderedDict()
        for (tag, te, xb, pnl) in log: by.setdefault(int(te // A.DAY), []).append((xb, pnl))
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
            A.TRADELOG = []; n0 = len(tr.log)
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            caps = [x for x in (st.get("best") and st["best"] * st["target"], st.get("conc") and st["conc"] * st["target"]) if x]
            days(A.TRADELOG, st, min(caps) if caps else None)
            segs.append(("eval", st, A.TRADELOG, tr.log[n0:]))
            if not ok: break
        if ok:
            A.TRADELOG = []; n0 = len(tr.log); fd = F["funded"]
            A.run_funded(fd, tr, rng, F, clock, c["X1"], c["X"])
            days(A.TRADELOG, fd, None, fd.get("day_profit_cap"))
            segs.append(("funded", fd, A.TRADELOG, tr.log[n0:]))
        A.TRADELOG = None
        for kind, st, tl, sl in segs:
            assert len(tl) == len(sl)
            for (tag, te, xb, pnl), t in zip(tl, sl):
                ntr += 1
                if c.get("kind", "cfd") == "cfd":                  # the firms' 2% rules are CFD-firm rules
                    worst["loss_share_of_account"] = max(worst["loss_share_of_account"], -pnl / S)
                fee = M["cost"] * t["l"] / s
                worst["target_distance_short_of_0.6sd"] = max(worst["target_distance_short_of_0.6sd"],
                                                               PF.WMIN_SD - s * (t["w"] + fee) / t["l"] / M["sig"])
                if lev:
                    lv = lev[0] if kind == "eval" else lev[1]
                    lim = lv * s * (lev[2] * (S + xb) if kind == "eval" else min(lev[2] * (S + xb), lev[3] * S))
                    worst["risk_over_margin_cap"] = max(worst["risk_over_margin_cap"], t["l"] - lim)
                if st.get("min_rr"): worst["below_min_reward_risk"] = max(worst["below_min_reward_risk"], st["min_rr"] * t["l"] - t["w"])
            for a, b in zip(sl, sl[1:]):
                (ie, mi) = a["exit"]; ib = b["i"]
                if ib < ie: ib += M["T"]
                worst["gap_short_of_10min"] = max(worst["gap_short_of_10min"], PF.GAP_MIN - ((ib - ie) * 60.0 - mi))
            if kind == "funded":
                fdx = st
                if fdx.get("profit_ceiling") or fdx.get("roll_profit_cap") or fdx.get("best"):
                    days_p = {}; closes = []
                    for j, ((tag, te, xb, pnl), t) in enumerate(zip(tl, sl)):
                        xa = xb + pnl
                        if fdx.get("profit_ceiling"): worst["maven_profit_over_ceiling"] = max(worst["maven_profit_over_ceiling"], xa - fdx["profit_ceiling"])
                        (ie, mi) = t["exit"]; db = ie - t["i"]
                        if db < 0: db += M["T"]
                        closes.append((t["t_in"] + db + mi / 60.0, pnl))       # when the trade closed (exit bar and minute)
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
       "below_min_reward_risk": 1e-6, "gap_short_of_10min": 1e-9, "maven_profit_over_ceiling": 1e-6,
       "maven_30d_over_10000": 1e-6, "fxify_best_day_over_25pct": 0.0}
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

# ---------------------------------------------------------------- portfolio
main = json.load(open("lockstep_v8.json")) if os.path.exists("lockstep_v8.json") else None
if main:
    import lockstep_portfolio_v8 as LP
    R = [r for r in main["R"] if r["p"] == LP.REC and r["months"] == 12]
    ev = float(np.mean([np.mean(r["monthly"][:12]) for r in R]))
    ci = 1.96 * float(np.std([np.mean(r["monthly"][:12]) for r in R])) / math.sqrt(len(R))
    OUT["recomputed_headline"] = dict(ev=ev, ci=ci, lives=len(R))
    conf = sum(r.get("conflicts", 0) for r in lives)
    tier = [np.mean(r["refusal"]["tiered"]) for r in R]; harsh = [np.mean(r["refusal"]["harsh"]) for r in R]
    check("portfolio", conf == 0 and np.mean(harsh) <= np.mean(tier) <= ev + 1e-6,
          f"recommended plan, first year: {ev:,.0f} ± {ci:,.0f} a month over {len(R):,} lives; opposite positions {conf}; "
          f"refusals: tiered {np.mean(tier):,.0f}, harsh {np.mean(harsh):,.0f} (on average at most the baseline: a refusal removes payouts, and the fees it saves are smaller)")

# ---------------------------------------------------------------- document
if len(sys.argv) > 1 and sys.argv[1] == "doc":
    import html as H
    h = open("prop_firm_math_v8.html").read()
    txt = H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)))
    ph = sorted(set(re.findall(r"\[\[[A-Z0-9_]+\]\]", h)))
    bad_words = [w for w in (" nan", "NaN", " None", " inf ", "{usd(", "{pm(") if w in txt]
    check("doc_placeholders", not ph and not bad_words, f"unfilled placeholders {ph or 'none'}; suspicious text {bad_words or 'none'}")
    if main:
        from doc8_common import usd
        check("doc_headline", usd(ev) in txt, f"recomputed headline {usd(ev)} {'found' if usd(ev) in txt else 'NOT found'} in the document")
    try:
        from pypdf import PdfReader
        n = len(PdfReader("The_Prop_Firm_Option_v8_Mathematics.pdf").pages); OUT["pages"] = n
        check("pdf", n > 50, f"{n} pages")
    except ImportError:
        pass

json.dump(OUT, open("audit_v8.json", "w"), indent=1, default=float)
print("all passed" if all(v.get("ok", True) for v in OUT.values() if isinstance(v, dict) and "ok" in v) else "SOME FAILED")
