"""Part III (one person, many accounts), Part IV (running it; what could go wrong) and the appendices of version 7."""
import math, collections
import numpy as np
from doc7_common import *
from doc7_part1 import short, sett, _calc
from doc7_part2 import ALLOC, SPECS, acct_row, alloc_value, FIRMS
import lockstep_portfolio_v7 as LP
import review_v7 as RV

R = LOCK["R"]; SLOTS = LOCK["slots"]
PNAMES = list(SLOTS.keys())
REC = LP.REC
PLABEL = {"Tier A": "Tier A only", "Tier A + B": "Tiers A and B", REC: "Recommended (A + B + one account per tier-D firm)",
          "Recommended, FTMO as 2 x 200K": "Recommended, FTMO as 2 &times; 200K", "All firms at full caps": "All firms at full allowance",
          "All firms at full caps + The5ers small accounts": "Full allowance + The5ers small accounts", "Recommended + futures": "Recommended + futures layer"}
CFD_FIRMS = FIRMS[:13]

def lives(p, RR=None): return [r for r in (RR if RR is not None else R) if r["p"] == p]
def stats_of(rs, months=12):
    M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1); n = len(rs)
    y = M[:, :12].mean(1)
    tr = np.array([r["trough"] for r in rs])
    return dict(n=n, ev=M[:, :12].mean(), ci=1.96 * y.std() / math.sqrt(n), ss=M[:, 1:12].mean(), M=M, C=C,
                tiered=np.mean([np.mean(r["refusal"]["tiered"][:12]) for r in rs]), harsh=np.mean([np.mean(r["refusal"]["harsh"][:12]) for r in rs]),
                p05=np.percentile(C[:, 11], 5), p50=np.percentile(C[:, 11], 50), p95=np.percentile(C[:, 11], 95),
                ahead12=np.mean(C[:, 11] > 0), tr50=np.percentile(tr, 50), tr05=np.percentile(tr, 5), tr01=np.percentile(tr, 1),
                conflicts=sum(r["conflicts"] for r in rs), orders=np.mean([r["orders_per_trading_day"] for r in rs]))
def pstats(p):
    s = stats_of(lives(p)); s["acc"] = len(SLOTS[p]); s["firms"] = len({firm_of(x["firm"]) for x in SLOTS[p]}); return s
def paired(pa, pb, RR=None, RR2=None):
    """paired difference of first-year EV/month between two portfolios on the same seeds"""
    a = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(pa, RR)}; b = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(pb, RR2 if RR2 is not None else RR)}
    ks = sorted(set(a) & set(b)); d = np.array([b[k] - a[k] for k in ks])
    return d.mean(), 1.96 * d.std() / math.sqrt(len(d)), len(d)

def per_firm(p):
    rs = lives(p); out = collections.defaultdict(lambda: dict(pay=0.0, fee=0.0, req=0.0, buys=0.0, credits=0.0))
    for r in rs:
        for f, v in r.get("payouts", {}).items(): out[f]["pay"] += v
        for f, v in r.get("fees", {}).items(): out[f]["fee"] += v
        for f, v in r.get("requests", {}).items(): out[f]["req"] += v
        for f, v in r.get("buys", {}).items(): out[f]["buys"] += v
        for f, v in r.get("credits", {}).items(): out[f]["credits"] += v
    n = len(rs) * 12
    return {f: {k: v / n for k, v in d.items()} for f, d in out.items()}

def renewal_sum(p):
    return sum(s["ev"] for s in SLOTS[p])
def renewal_sum_ci(p):
    """the sum of the accounts' long-run rates with a 95% interval: accounts of one programme share one estimate (fully
    correlated), different programmes were estimated on different paths (independent)"""
    g = collections.defaultdict(float)
    for s in SLOTS[p]:
        r = fin(s["firm"], s["instr"], size=s["size"])
        g[(s["firm"], s["instr"])] += (r["CI"] if r else 0.0) / 1.96
    return renewal_sum(p), 1.96 * math.sqrt(sum(v * v for v in g.values()))

# ------------------------------------------------------------------ allocation
def alloc_table():
    rows = []; tr = tf = 0
    for f in FIRMS:
        a = ALLOC[f]; rv, rn = alloc_value(a["rec"]); fv, fn_ = alloc_value(a["full"])
        if not a["full"] and not a["rec"]: continue
        if f not in ("Topstep", "Apex"): tr += rv; tf += fv
        rec = ", ".join(f"{n}&times;{kk(s)}" for p, i, s, n in a["rec"]) or "&ndash;"
        full = ", ".join(f"{n}&times;{kk(s)}" for p, i, s, n in a["full"]) or "&ndash;"
        mk = MSHORT[(a["full"] or a["rec"])[0][1]]
        rows.append([f"{f} <span class='tier{TIER.get(f, 'B')}'>({TIER.get(f, '?')})</span>", a["cap"], a["copy"], mk, rec, usd(rv) if rn else "&ndash;", full, usd(fv) if fn_ else "&ndash;"])
    rows.append(["<strong>Total, CFD firms</strong>", "", "", "", "", f"<strong>{usd(tr)}</strong>", "", f"<strong>{usd(tf)}</strong>"])
    return table(["Firm (tier)", "Per-person limit", "Copying between accounts", "Market", "Recommended", "EV/month", "Full allowance", "EV/month"], rows, cls="small", num_from=5, hl=(len(rows) - 1,),
                 cap="EV per month: each account's long-run renewal&ndash;reward value from its programme chapter (fresh paths), summed. A firm whose programme is not worth it under the plan's policies has no accounts. "
                     "The full-allowance column includes The5ers' optional small accounts. Futures (Topstep, Apex) are an optional layer, not in either total.")

def size_table():
    rows = []
    for f in CFD_FIRMS:
        for p, i, s, n in ALLOC[f]["rec"][:1] or ([(r["prog"], r["instr"], 100_000, 0) for r in [fin(*PROGS_FIRST(f))] if r] if PROGS_FIRST(f) else []):
            a = fin(p, i, size=100_000); b = fin(p, i, size=200_000)
            if not (a and b): continue
            fa = rules_of(a)["fee"]; fb = rules_of(b)["fee"]
            d = b["EV_month"] - 2 * a["EV_month"]
            rows.append([short(p), usd(fa, 2), usd(fb, 2), usd(fb - 2 * fa, 2), usd(2 * a["EV_month"]), usd(b["EV_month"]), sgn(d)])
    return table(["Programme", "100K fee", "200K fee", "200K &minus; 2 &times; 100K fee", "2 &times; 100K: EV/month", "1 &times; 200K: EV/month", "Difference"], rows, cls="small",
                 cap="Same setting scaled, same sixteen paths and random numbers. Where every rule scales with the account, the only differences are the fee and the refund that follows it (11.1 checks the scaling path by path); GFT's flat $3,000 day cap and $10,000 payout cap do not scale.")
def PROGS_FIRST(f):
    from doc7_part2 import PROGS_OF
    return PROGS_OF.get(f, [None])[0]

def size_text():
    a = pstats(REC); b = pstats("Recommended, FTMO as 2 x 200K") if "Recommended, FTMO as 2 x 200K" in SLOTS else None
    d = paired(REC, "Recommended, FTMO as 2 x 200K") if b else None
    return (f"<p><strong>The answer, firm by firm.</strong> With the corrected formula of [[CH_ALLOC]].2, 200K beats 2 &times; 100K exactly when \\(F(2S) &lt; 2F(S)\\), by \\((2F(S) - F(2S))(1 - P q_R)\\) per attempt, unless a rule fails to scale. "
            f"Where only one account is allowed (FunderPro, GFT, FundedNext on its own market), the larger size is used if it is worth more than one smaller account. GFT is the case where the formula fails: its $3,000 day cap and $10,000 payout cap bind harder at 200K, so one 200K account is worth less than two 100K accounts would be, but GFT allows only one, and one 200K account is still worth more than one 100K account.</p>" +
            (f"<p><strong>FTMO, 4 &times; 100K or 2 &times; 200K.</strong> Same fee per dollar, same rules: the paired difference on the same {d[2]:,} seeds is {sgn(d[0])} &plusmn; {usd(d[1])} a month for the whole portfolio, i.e. no difference. Two accounts make half as many payout requests; four give a smoother cash path. The plan uses four 100K accounts for the headline.</p>" if d else ""))

# ------------------------------------------------------------------ portfolios
def portf_table():
    rows = []
    for p in PNAMES:
        s = pstats(p)
        rows.append([PLABEL.get(p, p), str(s["acc"]), str(s["firms"]), pm(s["ev"], s["ci"]), usd(s["ss"]), usd(renewal_sum(p)), usd(s["p05"]), usd(s["p50"]), usd(s["p95"]), usd(s["tr50"]), usd(s["tr05"])])
    return table(["Portfolio", "Accounts", "Firms", "First year, EV/month (95%)", "Months 2&ndash;12", "Sum of long-run rates", "First-year cash p5", "median", "p95", "Lowest cumulative cash: median", "p5"],
                 rows, cls="small", hl=(PNAMES.index(REC),) if REC in PNAMES else (),
                 cap=f"{len(lives(REC)):,} simulated first years per portfolio, each on its own new price paths (seeds from 100,000; the same seeds for every portfolio, so differences are paired). "
                     "First year: total cash over 12 months &divide; 12, after every fee modelled. Sum of long-run rates: the accounts' renewal&ndash;reward values from Part II, a different quantity (8.5). "
                     "Lowest cumulative cash: the deepest point of fees paid minus cash received.")

def portf_text():
    a = pstats(REC)
    out = [f"<p><strong>Three quantities.</strong> The recommended portfolio's first year averages {usd(a['ev'])} a month (&plusmn;{usd(a['ci'])}); months 2&ndash;12 average {usd(a['ss'])}; the sum of its accounts' long-run rates is {usd(renewal_sum(REC))}. "
           f"They answer different questions (8.5), and Section [[CH_LOCK]].6 measures the long-run rate of the portfolio itself. {pct(a['ahead12'], 1)} of simulated first years ended ahead; the 5th percentile of first-year cash is {usd(a['p05'])}.</p>",
           f"<p><strong>No account ever opposed another.</strong> In {sum(len(lives(p)) for p in PNAMES):,} simulated years the engine recorded {sum(pstats(p)['conflicts'] for p in PNAMES)} moments when two accounts held opposite positions on one market. The recommended plan places about {a['orders']:.0f} orders a trading day across all accounts.</p>"]
    pairs = [("All firms at full caps", REC), ("All firms at full caps + The5ers small accounts", "All firms at full caps"), ("Recommended + futures", REC), ("Tier A + B", "Tier A"), (REC, "Tier A + B")]
    lines = []
    for b_, a_ in pairs:
        if a_ in SLOTS and b_ in SLOTS:
            d, ci, n = paired(a_, b_)
            lines.append(f"{PLABEL.get(b_, b_)} minus {PLABEL.get(a_, a_)}: {sgn(d)} &plusmn; {usd(ci)}")
    if lines: out.append("<p><strong>Paired differences</strong> (same seeds, 95%): " + "; ".join(lines) + ".</p>")
    return "".join(out)

def month_fig():
    s = pstats(REC); C = s["C"] / 1e6
    mm = lambda v: ("\u2212" if v < -1e-9 else "") + f"${abs(v):.2f}M"
    med = np.percentile(C, 50, axis=0); lo = np.percentile(C, 5, axis=0); hi = np.percentile(C, 95, axis=0); mean = C.mean(0)
    W, H, l0, r0, t0, b0 = 640, 250, 56, 96, 22, 34
    ymax = math.ceil(hi.max() * 4) / 4 + 0.1; ymin = min(0, lo.min()) - 0.05
    step = 0.25 if ymax < 2 else 0.5
    X = lambda i: l0 + i / 12 * (W - l0 - r0); Y = lambda v: t0 + (ymax - v) / (ymax - ymin) * (H - t0 - b0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    yv = math.floor(ymin / step) * step
    while yv <= ymax + 1e-9:
        g.append(f'<line x1="{l0}" x2="{W - r0}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RULE}" stroke-width="{1 if abs(yv) < 1e-9 else 0.5}"/>')
        g.append(t(l0 - 6, Y(yv) + 3, mm(yv), 8, "end", MUT, True)); yv += step
    for i in range(0, 13): g.append(t(X(i), H - b0 + 14, str(i), 8, "middle", MUT, True))
    band = [(X(0), Y(0))] + [(X(i + 1), Y(hi[i])) for i in range(12)] + [(X(i + 1), Y(lo[i])) for i in range(12)][::-1] + [(X(0), Y(0))]
    g.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in band) + f'" fill="{S1}" fill-opacity="0.14" stroke="none"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(med[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S1}" stroke-width="2"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(mean[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S2}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    g.append(t(X(12) + 6, Y(hi[11]) + 3, "95th pct " + mm(hi[11]), 8, "start", MUT))
    g.append(t(X(12) + 6, Y(med[11]) + 3, "median " + mm(med[11]), 8, "start", INK))
    g.append(t(X(12) + 6, Y(mean[11]) + 14, "mean " + mm(mean[11]), 8, "start", S2))
    g.append(t(X(12) + 6, Y(lo[11]) + 3, "5th pct " + mm(lo[11]), 8, "start", MUT))
    g.append(t((l0 + W - r0) / 2, H - 4, "months since starting", 8.5, "middle", MUT))
    g.append(t(l0, 12, "Cumulative cash of the recommended plan: median (solid), mean (dashed), 5th to 95th percentile (band)", 8.5, "start", INK))
    g.append("</svg>")
    return fig("".join(g), f"{len(lives(REC)):,} simulated first years of the recommended plan ({len(SLOTS[REC])} accounts), each on its own paths. Cash = payouts received minus fees paid.")

def month_table():
    s = pstats(REC); M = s["M"]; C = s["C"]
    rows = [[str(i + 1), usd(M[:, i].mean()), usd(np.percentile(M[:, i], 10)), usd(np.percentile(M[:, i], 50)), usd(np.percentile(M[:, i], 90)), usd(C[:, i].mean()), pct(np.mean(C[:, i] > 0), 0)] for i in range(12)]
    return table(["Month", "Mean cash", "p10", "median", "p90", "Cumulative mean", "Ahead"], rows, cls="small", num_from=1)

def long_text():
    rs = LONG.get("R", [])
    if not rs: return "<p>(36-month runs not available.)</p>"
    M = np.array([r["monthly"] for r in rs]); n = len(rs)
    y1 = M[:, :12].mean(1); y23 = M[:, 12:].mean(1); o12 = np.array([r["open12"] for r in rs])
    blocks = [(a, b) for a, b in ((0, 12), (12, 24), (24, 36))]
    rows = [[f"months {a + 1}&ndash;{b}", pm(M[:, a:b].mean(), 1.96 * M[:, a:b].mean(1).std() / math.sqrt(n))] for a, b in blocks]
    rows.append(["month 12 alone", pm(M[:, 11].mean(), 1.96 * M[:, 11].std() / math.sqrt(n))])
    rows.append(["months 11 and 13", f"{usd(M[:, 10].mean())} and {usd(M[:, 12].mean())}"])
    tb = table(["Period (36-month lives)", "Average cash per month (95%)"], rows, cls="small", num_from=1,
               cap=f"{n} simulated 36-month lives of the recommended plan, each on its own new paths (seeds 300,000 and up).")
    rs_, rs_ci = renewal_sum_ci(REC)
    gap = renewal_sum(REC) - y23.mean(); gse = math.hypot(1.96 * y23.std() / math.sqrt(n) / 1.96, rs_ci / 1.96)
    return (tb + f"<p><strong>Long-run rate.</strong> Months 13&ndash;36 average {pm(y23.mean(), 1.96 * y23.std() / math.sqrt(n))} a month: the portfolio's own long-run rate. "
            f"The sum of its accounts' long-run rates from Part II is {pm(rs_, rs_ci)}; the portfolio is {usd(gap)} lower, {gap / gse:.1f} standard errors, and the paired check below finds no effect of running the accounts together, so the plan quotes the portfolio's own figure. "
            f"The first year is lower ({usd(y1.mean())}) because it carries the start-up: fees at once, payouts later. "
            f"<strong>Value of the accounts open at month 12</strong>: the cash those accounts (evaluations in progress and funded accounts) go on to pay after month 12 averages {usd(o12.mean())} (&plusmn;{usd(1.96 * o12.std() / math.sqrt(n))}); it belongs to the first year's purchases but arrives later. "
            f"Version 6's month-12 dip is checked by the month table above: in 36-month lives month 12 is {usd(M[:, 11].mean())} against {usd(M[:, 10].mean())} and {usd(M[:, 12].mean())} on either side, so a dip there would be a horizon effect of the 12-month runs, not a property of month 12.</p>" + pair_text())

def pair_text():
    import os, json
    if not os.path.exists("lockstep_v7_pairfirms.json"): return ""
    q = json.load(open("lockstep_v7_pairfirms.json"))
    return (f"<p><strong>Does the portfolio add up?</strong> On the first {q['n']} of these lives, every firm's accounts were also run alone, on the same paths and calendar. "
            f"Full portfolio minus the sum of the firms alone: {sgn(q['diff'])} &plusmn; {usd(q['ci'])} a month over months 13&ndash;36 and {sgn(q['diff_y1'])} &plusmn; {usd(q['ci_y1'])} in the first year (paired, 95%). "
            f"Running the accounts together (one calendar, one direction per market) changes nothing measurable, as linearity says it should for an unchanged policy. "
            f"On those same paths the firms alone average {usd(q['sum_alone'])} a month, below the sum of their long-run rates in Part II ({usd(sum(q['renewal'].values()))}): "
            f"every account on the Nasdaq trades the same path, largely in the same direction, so their sampling errors move together and a sample of a few hundred lives can sit some thousands of dollars from the expectation. "
            "That is why the interval of the portfolio's rate is much wider than a sum of independent per-account intervals would suggest.</p>")

def budget_table():
    rs = BUDGET.get("R", [])
    if not rs: return ""
    rows = []
    base = [r for r in rs if not r["kw"].get("budget")]
    bev = np.mean([np.mean(r["monthly"]) for r in base]) if base else None
    for b in sorted({r["kw"].get("budget") for r in rs if r["kw"].get("budget")}) + [None]:
        g = [r for r in rs if r["kw"].get("budget") == b]
        s = stats_of(g)
        buys = np.mean([sum(r.get("buys", {}).values()) for r in g])
        rows.append([usd(b) if b else "unlimited", pm(s["ev"], s["ci"]), pct(s["ev"] / bev, 0) if bev else "", f"{buys:.0f}", pct(s["ahead12"], 0), usd(s["p05"]),
                     usd(np.mean([r["wallet_low"] for r in g])) if b else "&ndash;"])
    return table(["Starting cash", "First year, EV/month", "of unlimited", "Evaluations bought in the year", "Ahead at 12 months", "First-year cash p5", "Lowest cash left (mean)"], rows, cls="small", num_from=1,
                 cap="The recommended plan with a finite budget: a purchase waits (checked daily) until the cash for it is there; payouts become spendable when they arrive. Slots are filled in order of value per fee dollar. 200 lives per row, same seeds in every row.")

def scen_rows():
    out = []
    def add(label, rs, ref=None):
        if not rs: return
        s = stats_of(rs)
        d = ""
        if ref is not None:
            a = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(REC)}
            ks = [r["seed"] for r in rs if r["seed"] in a]
            dd = np.array([np.mean(r["monthly"][:12]) - a[r["seed"]] for r in rs if r["seed"] in a])
            d = f"{sgn(dd.mean())} &plusmn; {usd(1.96 * dd.std() / math.sqrt(len(dd)))}" if len(dd) else ""
        out.append([label, pm(s["ev"], s["ci"]), d, usd(s["p05"]), usd(s["tr05"])])
    add("Baseline (same 200 seeds)", [r for r in lives(REC) if r["seed"] < 100_200])
    for c in (1.5, 2.0): add(f"All trading costs &times; {c:g}", [r for r in STRESS.get("R", []) if r["kw"].get("cost_mult") == c], True)
    add("Markets correlated 0.3 (one joint path)", CORR.get("R", []), True)
    add("News proxy: flat 12:00&ndash;14:00 UTC every weekday", NEWS.get("R", []), True)
    for name in ("FundedNext 1% risk", "FundedNext 7-day pause"):
        add(f"{name} (behavioural remedy)", [r for r in BEHAV.get("R", []) if r["p"] == name], True)
    return out

def scen_table():
    rows = scen_rows()
    if not rows: return ""
    return table(["Scenario (recommended plan)", "First year, EV/month", "Paired difference to baseline", "First-year cash p5", "Lowest cumulative cash p5"], rows, cls="small", num_from=1,
                 cap="Full portfolio runs, 200 lives each on the baseline's seeds (paired). The correlated run uses joint paths, so its pairing is by seed only.")

# ------------------------------------------------------------------ refusals
def tier_table():
    rows = []
    for tr, desc in (("A", "PropFirmMap A/A+, TrustPilot profile active"), ("B", "PropFirmMap B+, TrustPilot active"), ("D", "TrustPilot rating withheld for fake reviews; PropFirmMap D")):
        firms = [f for f in FIRMS if TIER.get(f) == tr]
        rows.append([tr, desc, ", ".join(firms), pct({"A": 0.02, "B": 0.05, "D": 0.15}[tr], 0), pct({"A": 0.05, "B": 0.10, "D": 0.30}[tr], 0)])
    return table(["Tier", "Evidence (4 October 2026)", "Firms", "Refusal chance per request: tiered", "harsh"], rows, cls="small", num_from=3,
                 cap="Chosen scenarios, not measurements: public ratings do not calibrate refusal rates.")

def refusal_table():
    rows = []
    for p in PNAMES:
        s = pstats(p)
        rows.append([PLABEL.get(p, p), usd(s["ev"]), usd(s["tiered"]), pct(s["tiered"] / s["ev"], 0) if s["ev"] > 0 else "", usd(s["harsh"]), pct(s["harsh"] / s["ev"], 0) if s["ev"] > 0 else ""])
    return table(["Portfolio", "All payouts honoured", "Tiered", "kept", "Harsh", "kept"], rows, cls="small", hl=(PNAMES.index(REC),) if REC in PNAMES else (),
                 cap="First-year average per month. Each payout request is refused with its firm's probability; the refused payout is not paid, and the person stops using that firm (no more fees or payouts there). Ten draws of refusals per simulated year.")

def refusal_text():
    pf = per_firm(REC); s = pstats(REC)
    rows = []
    for f in FIRMS:
        if f not in pf: continue
        d = pf[f]; tr = TIER.get(f, "B"); rho = {"A": 0.02, "B": 0.05, "D": 0.15}[tr]
        life = 1 / (rho * d["req"]) if d["req"] > 0 else float("inf")
        rows.append([f, tr, f"{d['req']:.2f}", usd(d["pay"] / max(d["req"], 1e-9)), usd(d["pay"] + d["fee"]), f"{life:.0f}" if life < 1e6 else "&ndash;"])
    tb = table(["Firm", "Tier", "Payout requests a month", "Average request", "Net cash a month", "Expected months until a refusal (tiered)"], rows, cls="small", num_from=2,
               cap="Recommended plan, first-year averages from the portfolio simulation.")
    return tb + (f"<p>The recommended plan's accounts make about {sum(d['req'] for d in pf.values()):.1f} payout requests a month. In the tiered scenario it keeps {pct(s['tiered'] / s['ev'], 0)} of its first-year value, in the harsh one {pct(s['harsh'] / s['ev'], 0)}. "
                 "Under the 40% policy requests are smaller and more frequent than in version 6, so each firm is exposed to more requests; the scenarios price that.</p>")

def ref_example():
    pf = per_firm(REC)
    if "FTMO" not in pf: return ""
    ft = pf["FTMO"]["req"]
    return (f"In the recommended plan the FTMO accounts together make about {ft:.2f} requests a month: at \\(\\rho = 2\\%\\), FTMO is expected to last \\(1/(0.02 \\times {ft:.2f}) = {1 / (0.02 * ft):.0f}\\) months.")

def part3_fills(ch_alloc, ch_lock, ch_ref):
    return dict(CH_ALLOC=ch_alloc, CH_LOCK=ch_lock, CH_REF=ch_ref, ALLOC_TABLE=alloc_table(), SIZE_TABLE=size_table(), SIZE_TEXT=size_text(),
                LIVES=f"{sum(len(lives(p)) for p in PNAMES):,}", PORTF_TABLE=portf_table(), PORTF_TEXT=portf_text(), MONTH_FIG=month_fig(), MONTH_TABLE=month_table(),
                LONG_TEXT=long_text(), BUDGET_TABLE=budget_table(), SCEN_TABLE=scen_table(),
                TIER_TABLE=tier_table(), REFUSAL_TABLE=refusal_table(), REFUSAL_TEXT=refusal_text(), REF_EXAMPLE=ref_example())

# ------------------------------------------------------------------ Part IV
def settings_card():
    rows = []
    for f in CFD_FIRMS:
        for p, i, s, n in ALLOC[f]["rec"]:
            r = acct_row(p, i, s)
            if not r: continue
            T = trade_numbers(i, r["m"], r["L"], r["L"])
            lots = f"{T['lots']:.2f} lots" if T.get("lots") else f"${T['usd_per_pt']:,.2f}/pt"
            rows.append([short(p), f"{n} &times; {kk(s)}", MSHORT[i], usd(r["L"]), f"{r['m']:g} &sigma; = {T['stop_pts']:.1f} {T['unit']}s", lots, f"{r['k']:g}", usd(r["X"]), usd(r["EV_month"] * n)])
    return table(["Programme", "Accounts", "Market", "Risk per trade", "Stop", "Size", "k", "Payout target", "EV/month"], rows, cls="small tight", num_from=3,
                 cap="Stops in points (Nasdaq), pips (USDJPY, EURUSD) or dollars (gold) at the prices of 2 October 2026; recompute \\(m\\sigma\\times\\)price weekly and re-measure \\(\\sigma\\) monthly. "
                     "The take-profit is the smallest of \\(k\\) times the risk, the distance to the current target, 40% of the current target less today's profit, and any firm cap, plus the cost (4.1).")

def cost_rows():
    out = []
    for sp in SPECS:
        if sp.get("fut"): continue
        cs = {r["cost_mult"]: r for r in sens("cost", sp["prog"], sp["instr"])}
        if not all(c in cs for c in (1.0, 1.5, 2.0)): continue
        out.append([short(sp["prog"]), MSHORT[sp["instr"]]] + [usd(cs[c]["EV_month"]) for c in (1.0, 1.5, 2.0)] + [f"{cs[c]['days']:.1f}" for c in (1.0, 2.0)])
    return out

def part4(ch_run, ch_risk):
    rec = pstats(REC)
    st = [s for s in STRESS.get("R", [])]
    c15 = np.mean([np.mean(r["monthly"]) for r in st if r["kw"].get("cost_mult") == 1.5]) if st else None
    c20 = np.mean([np.mean(r["monthly"]) for r in st if r["kw"].get("cost_mult") == 2.0]) if st else None
    s1 = f"""
<section class="part"><span class="num">Part IV</span><h1>Running it</h1><p>The settings of every account in one place, the routine that runs them, and everything that could make the numbers wrong.</p></section>
<section class="chapter"><span class="eyebrow">Chapter {ch_run}</span><h1>The routine</h1>
<h2>{ch_run}.1 Every account's settings</h2>
{settings_card()}
<h2>{ch_run}.2 Placing a trade, step by step</h2>
<ol>
<li><strong>Is a trade allowed now?</strong> Weekdays, inside the market's entry hours and not from 19:00 UTC onward; not before 00:05 UTC (after the midnight resets); no restricted news window for this firm, stage and market coming up before the trade could reasonably end; at least 10 minutes since this account's last losing trade in the same direction.</li>
<li><strong>Direction.</strong> If any of your accounts holds this market, the same direction. Otherwise the plan's rule: long if the last hourly close is above the close five hours earlier, short if below. The rule has no edge (Chapter 11); its job is that no two of your accounts are ever opposite.</li>
<li><strong>Room.</strong> Floor room \\(= (\\text{{balance}} - \\text{{floor}} - \\$100 \\text{{ per }} \\$100\\text{{K}})/(1+\\rho)\\); day room \\(= (\\text{{daily limit}} - \\text{{today's loss}} - \\$200 \\text{{ per }} \\$100\\text{{K}})/(1+\\rho)\\); margin room \\(= 0.6\\,\\lambda\\, m\\sigma \\times \\text{{balance}}\\). If the floor room is under a tenth of the normal risk, <strong>stop using this account</strong> and buy its replacement. If only the day room is, wait until tomorrow.</li>
<li><strong>Risk.</strong> \\(l\\) = the smallest of the plan's risk and the three rooms. <strong>Stop</strong>: \\(m\\sigma\\times\\) price; size \\(= l /\\) (stop in points \\(\\times\\) dollars per point per lot), rounded down (whole contracts on futures).</li>
<li><strong>Take-profit.</strong> \\(w\\) = the smallest of \\(k\\,l\\), the distance to the current target, 40% of the current target less today's profit, and any firm cap (FXIFY 25% of the payout per day, Maven 20% per trade, GFT's $3,000 a day less today's profit). At Maven, if \\(w &lt; 1.5\\,l\\), lower \\(l\\) to \\(w/1.5\\). Distance = stop distance \\(\\times (w + c)/l\\).</li>
<li><strong>Place one bracket order</strong>; never move it. <strong>At 20:00 UTC close everything still open.</strong></li>
<li><strong>Log it</strong>: time, account, market, direction, size, stop, target, fill, and the closing reason. The log is the evidence for any review.</li>
</ol>
<h2>{ch_run}.3 Phases, payouts and refills</h2>
<ul>
<li>When a phase target (plus $20 per $100K) is reached: stop. Where the firm counts trading days, place one minimal trade, held at least 2 minutes, on each remaining weekday; where it counts profitable days, the daily target of 6.4 has met it.</li>
<li>When a funded account reaches its payout target: stop, request the payout on the first allowed day (at Maven, only when the 30-day window has room for all of it, and only with the largest winning trade at most 20% of the payout), withdraw everything above the start, and start the next cycle.</li>
<li>When a payout date arrives before the target is reached, request whatever profit the account holds, if the firm's minimum and its consistency rules allow it (FXIFY: no day above 25% of it; Hola Prime: 40%; Maven: no trade above 20%), and start the next cycle; if a rule does not allow it, keep trading toward a target large enough for the rule to hold.</li>
<li>When an account fails or is closed under the floor rule: buy the next evaluation of the same programme (at FundedNext, after a pause if its gambling indicators are a concern: [[CH_LOCK]].7). Never trade an account to lose it, never let one lapse deliberately while it can still be traded under the rules.</li>
<li>Credits (The5ers) are spent on the next evaluation at that firm.</li>
</ul>
<h2>{ch_run}.4 Cash needed</h2>
<p>Fees are paid before payouts arrive. In the simulation the running total of the recommended plan falls to {usd(rec['tr50'])} at its lowest in a typical first year, {usd(rec['tr05'])} in the worst 5% and {usd(rec['tr01'])} in the worst 1%. These are not amounts that keep every slot filled in every year: Section [[CH_LOCK]].7 runs the plan with fixed budgets, purchases waiting for cash, and shows what each budget gives.</p>
<h2>{ch_run}.5 Workload</h2>
<p>About {rec['orders']:.0f} bracket orders a trading day across {len(SLOTS.get(REC, []))} accounts, a daily close-out at 20:00 UTC, payout requests and evaluation purchases.</p>
</section>
<section class="chapter"><span class="eyebrow">Chapter {ch_risk}</span><h1>What could make the numbers wrong</h1>
<h2>{ch_risk}.1 Higher trading costs</h2>
{table(["Programme", "Market", "EV/month: cost &times; 1", "&times; 1.5", "&times; 2", "Days per attempt &times; 1", "&times; 2"], cost_rows(), cls="small", num_from=2,
       cap="One 100K account at the plan's setting, paths 141&ndash;144, 12,000 attempts per cell, the same random numbers in each row. Higher costs lower the value of an attempt and also shorten attempts (more fail, sooner), which is why a value per month can fall less than proportionally.")}
<p>For the whole recommended portfolio, full portfolio runs (not ratios) give {usd(c15) if c15 is not None else '&ndash;'} a month at 1.5 times the costs and {usd(c20) if c20 is not None else '&ndash;'} at twice, against {usd(rec['ev'])} (Section [[CH_LOCK]].7). <strong>Measure your real costs in the first week</strong> and redo the settings if they differ from 3.1 by more than a quarter.</p>
<h2>{ch_risk}.2 Behavioural rules the model cannot state</h2>
<p>These rules are applied at the firm's discretion. The figures in this document assume the plan's trading is not judged to break them; if it is, the affected payouts are lost, which is not the same as the random refusals of Chapter [[CH_REF]]:</p>
<ul>
<li><strong>FTMO</strong>: gambling, "all-in" trading, account rolling; no gap trading within 2 hours of a close.</li>
<li><strong>Fintokei</strong>: reaching a target in one or a few identical trades; token trades. The plan's three-winning-day minimum and minimal filler trades held 2 minutes are its answer.</li>
<li><strong>The5ers</strong>: one-trade target attainment (permanent ban). No trade makes more than 40% of a target.</li>
<li><strong>FundedNext</strong>: one-sided betting (remedy: a 1% risk limit), account rolling, several breached accounts in a short span (remedies: 40% consistency on on-demand rewards or a lower split). Section [[CH_LOCK]].7 measures the remedies.</li>
<li><strong>Hola Prime</strong>: profitability "materially dependent on concentrated outcomes". <strong>Alpha</strong>: "all or nothing", risk or loss of 2% or more, trades under 2 minutes on average. <strong>FXIFY</strong>: gambling. <strong>Blue Guardian</strong>: margin above 80%. <strong>Maven</strong>: large bets at 1:1.25 or worse.</li>
</ul>
<h2>{ch_risk}.3 Payouts refused, accounts closed</h2>
<p>Chapter [[CH_REF]]: {usd(rec['tiered'])} a month if payouts are refused at 2/5/15% per request by tier, {usd(rec['harsh'])} at 5/10/30%.</p>
<h2>{ch_risk}.4 Spreads, gaps and news</h2>
<p>The engine's cost is an average. Spreads widen at the daily break (now outside the plan's hours), at the open and around news. The news proxy of Section [[CH_LOCK]].7 bounds the effect of staying flat around releases.</p>
<h2>{ch_risk}.5 Rules change</h2>
<p>Every rule in Part II was read on 4 October 2026, from the pages listed in Appendix E. Leverage, consistency rules, payout schedules, prices and per-person limits change often. Recheck before buying and rerun the programme's optimisation (optimize_v7.py) when a rule that enters the model changes.</p>
<h2>{ch_risk}.6 The model itself</h2>
<ul>
<li><strong>Zero skill.</strong> If entries are systematically late or fills worse, the edge is negative; the cost stress is the guide.</li>
<li><strong>Markets move together.</strong> The baseline gives gold, euro and yen independent paths; Section [[CH_LOCK]].7 measures a correlation of 0.3. Real correlations change and rise in crises.</li>
<li><strong>Taxes and payment costs</strong> are not modelled.</li>
</ul>
<h2>{ch_risk}.7 What is not allowed, and is not in the plan</h2>
<p>No hedging across accounts or firms; no accounts in anyone else's name; no copy-trading services or other people's signals; no trading of restricted news windows; no tick scalping, latency or gap arbitrage; no grid or martingale sizing; no deliberately failed accounts. Do not share or sell the plan: several firms treat traders who run the same marketed strategy as a group.</p>
</section>"""
    return s1

# ------------------------------------------------------------------ appendices
def review_appendix(subs):
    rows = []
    for x in RV.R:
        fix = x["fix"]
        for k, v in subs.items(): fix = fix.replace(f"[[{k}]]", str(v))
        rows.append([f"{x['n']}", f"<strong>{x['title']}</strong><br><span class='verdict'>{x['verdict']}</span>", x["wrong"], fix])
    t1 = table(["#", "Review point", "What was wrong in version 6", "What version 7 does"], rows, cls="small appx", num_from=9, w0="4%")
    rows2 = [[x["n"], f"<strong>{x['title']}</strong>", x["what"]] for x in RV.NEW]
    t2 = table(["#", "Further error", "What it was, and the fix"], rows2, cls="small appx", num_from=9, w0="5%")
    return (f'<section class="chapter"><span class="eyebrow">Appendix A</span><h1>Corrections: the version 6 review, point by point</h1>'
            f"<p>A detailed review of version 6 (4 October 2026) raised 35 points. Every point was checked against the code, the data and the firms' pages; all 35 are accepted (one in part), and fixing them uncovered the further errors in the second table. "
            f"Because several fixes change the strategy itself (the concentration policy, the daily flat, the floor rule), version 7's figures are a new measurement, not version 6's minus a list of corrections.</p>{t1}"
            f"<h2>Further errors found while fixing the review's points</h2>{t2}</section>")

def appendices(subs):
    sheet = """
<section class="chapter"><span class="eyebrow">Appendix B</span><h1>Formula sheet</h1>
<table><thead><tr><th style="width:36%">Quantity</th><th>Formula</th><th>Exact for</th><th>Where</th></tr></thead><tbody>
<tr><td>Value of one attempt</td><td>\\(\\mathbb{E}[V] = \\Pr(\\text{pass})\\,\\mathbb{E}[C] + \\text{credits} - F\\)</td><td>always</td><td>1.2</td></tr>
<tr><td>Zero-cost example</td><td>\\(-F + P(\\alpha D + qR)\\), \\(q = D/(D+X)\\)</td><td>idealised model</td><td>1.3</td></tr>
<tr><td>Notional, target distance</td><td>\\(N = l/(m\\sigma)\\), \\(u = m\\sigma\\,(w + c)/l\\)</td><td>always</td><td>4.1</td></tr>
<tr><td>Win probability, mean, variance</td><td>\\(p = l/(l+w+c)\\); \\(-c\\); \\(l(w+c)\\)</td><td>fixed cost, binary outcome</td><td>4.2&ndash;4.3</td></tr>
<tr><td>Cost per unit of risk</td><td>\\(\\rho = \\kappa/(m\\sigma)\\)</td><td>always</td><td>4.4</td></tr>
<tr><td>Pass probability, no cost</td><td>\\(B/(A + B)\\)</td><td>exact landing on \\(A\\) or \\(-B\\)</td><td>5.1</td></tr>
<tr><td>Pass probability with cost</td><td>\\((e^{\\theta B} - 1)/(e^{\\theta(A+B)} - 1)\\), \\(\\theta = 2c/v\\)</td><td>approximation</td><td>5.2</td></tr>
<tr><td>Risk of the next trade; end of an attempt</td><td>\\(l = \\min(L, (x+B-b)/(1+\\rho), \\dots)\\); ends if room \\(&lt; l_{\\min}\\)</td><td>the plan's rule</td><td>5.4</td></tr>
<tr><td>Exact chain</td><td>\\(V(x) = p\\,V(x + w) + (1-p)\\,V(x - l - c)\\), and \\(N, K, T\\)</td><td>binary trades, per-trade caps</td><td>5.5</td></tr>
<tr><td>General accounting identity</td><td>\\(PA + (1-P)\\mathbb{E}[X_\\text{end}\\mid\\text{fail}] = -\\mathbb{E}[\\text{cost}]\\)</td><td>always (bounded stopped sum)</td><td>5.5</td></tr>
<tr><td>Two phases</td><td>\\(P = P_1 \\Pr(2 \\mid 1)\\); \\(= P_1P_2\\) in the model</td><td>always / model</td><td>6.1</td></tr>
<tr><td>Withdrawal identity</td><td>\\(\\mathbb{E}[W] = -\\mathbb{E}[X_\\text{end}] - \\mathbb{E}[\\text{funded cost}]\\)</td><td>cycle-by-cycle stopping</td><td>7.1</td></tr>
<tr><td>Funded cash, cycle form</td><td>\\(\\alpha\\,(X_1 q_1 + X q_1 q/(1 - q)) + R\\,q_1 q^{r-1}\\)</td><td>repeated cycles</td><td>7.2</td></tr>
<tr><td>Two special first cycles (GFT)</td><td>\\(\\mathbb{E}[\\text{paid}] = q_a + q_a^2/(1-q_b)\\)</td><td>repeated cycles</td><td>7.2</td></tr>
<tr><td>Trade duration</td><td>\\(m^2 (w + c)/l\\)</td><td>approximation (arithmetic motion)</td><td>8.1</td></tr>
<tr><td>Value per month</td><td>\\(30.44\\,\\mathbb{E}[V]/\\mathbb{E}[T_\\text{days}]\\)</td><td>long-run rate</td><td>8.3</td></tr>
<tr><td>Cluster-robust variance of a ratio</td><td>\\(\\frac{G}{G-1}\\sum_g (V_g - \\hat r T_g)^2/(\\sum_g T_g)^2\\)</td><td>independent clusters</td><td>8.4</td></tr>
<tr><td>Margin at entry</td><td>\\(l \\le 0.6\\,\\lambda\\, m\\sigma\\,(S + x)\\)</td><td>the plan's rule</td><td>10.2</td></tr>
<tr><td>Scaling an account</td><td>\\(\\mathbb{E}[V(\\lambda S)] = P[\\lambda G(S) + q_R R(\\lambda S)] - F(\\lambda S)\\)</td><td>scale-free rules</td><td>[[CH_ALLOC]].2</td></tr>
<tr><td>Paid cash under refusals</td><td>\\(a r (1-\\rho)(1 - e^{-\\rho r H})/(\\rho r)\\)</td><td>Poisson requests</td><td>[[CH_REF]].1</td></tr>
</tbody></table></section>
<section class="chapter"><span class="eyebrow">Appendix C</span><h1>Glossary</h1>
<table><tbody>
<tr><td style="width:24%"><strong>Abandonment</strong></td><td>Closing an account (no more trades, replacement bought) when its room above the floor is too small for a real trade (5.4).</td></tr>
<tr><td><strong>Allowance \\(D\\)</strong></td><td>The funded account's maximum loss: the floor sits \\(D\\) below the starting balance.</td></tr>
<tr><td><strong>Attempt</strong></td><td>One evaluation bought, from purchase until a phase fails or the funded account that followed it ends.</td></tr>
<tr><td><strong>Bold play</strong></td><td>Staking enough on each bet to reach the goal in one win; not used by the plan (5.6).</td></tr>
<tr><td><strong>Bracket</strong></td><td>A position with its stop-loss and take-profit attached at entry and never moved.</td></tr>
<tr><td><strong>Concentration policy</strong></td><td>No trade and no day above 40% of the current target (6.7).</td></tr>
<tr><td><strong>Daily flat</strong></td><td>No entry from 19:00 UTC, everything closed at 20:00 UTC (6.5).</td></tr>
<tr><td><strong>Engine</strong></td><td>The rule-by-rule simulation of an account on hourly price paths (acct_mc.py, pathfirm.py, lockstep.py).</td></tr>
<tr><td><strong>Exact chain</strong></td><td>The trade-level Markov chain of 5.5, solved by iteration (analytic_v7.py).</td></tr>
<tr><td><strong>Payout target \\(X\\)</strong></td><td>The profit at which a funded account stops and requests a payout.</td></tr>
<tr><td><strong>Renewal&ndash;reward</strong></td><td>The long-run value per unit time of a repeated process: \\(\\mathbb{E}[V]/\\mathbb{E}[T]\\).</td></tr>
<tr><td><strong>Slot</strong></td><td>One account position at one firm, refilled with a new evaluation whenever an attempt ends.</td></tr>
<tr><td><strong>Tier</strong></td><td>A firm's reliability class (A, B, D) from public evidence, used for the refusal scenarios.</td></tr>
<tr><td><strong>Winner's curse</strong></td><td>The upward bias of the best of many noisy estimates; removed by reporting every figure from paths not used to choose it.</td></tr>
</tbody></table></section>"""
    files = [("calibrate.py, sigma_v32.json", "costs and trading hours per market; hourly volatilities"),
             ("multi.py, pathfirm.py", "synthetic price paths (Brownian-bridge sub-steps; independent or jointly correlated) and the bracket trader"),
             ("acct_mc.py", "the rule engine: phases, funded accounts, payouts, the floor rule, cost-aware sizing, concentration, margin"),
             ("firms_v3.py, firms_v5.py, firms_v7.py", "every firm's rules; firms_v7 holds the corrected inputs and the plan's policies"),
             ("optimize_v7.py", "grid (paths 101&ndash;104), refine (111&ndash;114), futures, final (121&ndash;136) &rarr; opt_v7_*.json(l)"),
             ("analytic_v7.py", "the exact chain with the floor rule, written separately from the engine"),
             ("verify_v7.py, sens_v7.py", "checks against theory, tie convergence, scaling; cost, risk, concentration, flat and direction sensitivities"),
             ("lockstep.py, lockstep_portfolio_v7.py", "one person's accounts on one calendar; portfolios, 36-month lives, budgets, stress, correlation, news, behaviour"),
             ("progs_v7.py, review_v7.py", "the firms' written rules and sources; the review response"),
             ("build_math_v7.py, doc7_*.py, math_v7_*.html", "this document: every number is read from the files above"),
             ("rerun_v7.sh", "the whole pipeline after the grid, in order")]
    code = table(["File", "What it does"], [[f"<span class='k'>{a}</span>", b] for a, b in files], num_from=9, w0="34%")
    repro = ("<p>To reproduce: <span class='k'>python3 optimize_v7.py grid</span>, then <span class='k'>sh rerun_v7.sh</span>, then <span class='k'>python3 build_math_v7.py</span>. "
             "Synthetic paths are rebuilt exactly from their seeds and sigma_v32.json; no market data is needed. Every seed is fixed in the code, so every figure is reproducible bit for bit. "
             "Version 7 uses no real-history run: one two-year history is one sample, and its attempts are not independent validations.</p>")
    src_rows = [[SHEET[sp["sheet"]]["title"], SHEET[sp["sheet"]]["sources"]] for sp in SPECS]
    src = table(["Programme", "Sources (read 4 October 2026)"], src_rows, cls="small", num_from=9, w0="30%")
    return (review_appendix(subs) + sheet + f'<section class="chapter"><span class="eyebrow">Appendix D</span><h1>How every number was computed</h1>{code}{repro}</section>'
            f'<section class="chapter"><span class="eyebrow">Appendix E</span><h1>Sources</h1>{src}'
            '<p class="note">Reliability evidence: TrustPilot company pages (rating-withheld notices, August&ndash;September 2026) and PropFirmMap safety grades, both read on 4 October 2026. Rules change; keep dated copies of the pages that apply to each purchase.</p></section>')
