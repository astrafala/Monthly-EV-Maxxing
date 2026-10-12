"""Part III (one person, many accounts), Part IV (running it; what could go wrong) and the appendices of version 10.

Display rules (version 10): every dollar figure is rounded half away from zero (doc10_common.usd); a total of per-account
rates is the sum of the rates as printed (doc10_common.total); every interval of a mean over simulated lives uses Student's
t with n - 1 degrees of freedom and the sample standard deviation; an interval of a sum of programme rates that share
their paths is computed from the per-path sums (doc10_common.sum_ci); a sentence that reads a comparison ("no measurable
difference", "lower") is chosen from the interval it describes, never written in advance."""
import math, collections, json, os
import numpy as np
from doc10_common import *
from doc10_part1 import short, sett, _calc
from doc10_part2 import ALLOC, SPECS, acct_row, alloc_value, FIRMS, PROGS_OF
import lockstep_portfolio_v10 as LP
import review_v10 as RV

R = LOCK["R"]; SLOTS = LOCK["slots"]
PNAMES = list(SLOTS.keys())
REC = LP.REC
PLABEL = {"Tier A": "Tier A only", "Tier A + B": "Tiers A and B", REC: "Recommended (A + B + one account per tier-D firm)",
          "Recommended, FTMO as 2 x 200K": "Recommended, FTMO as 2 &times; 200K",
          "All firms at full caps": "Largest allocation modelled",
          "All firms at full caps + The5ers small accounts": "Largest allocation + The5ers' small New accounts (not recommended: [[CH_RISK]].2)",
          "Recommended + futures": "Recommended + futures layer"}
CFD_FIRMS = [f for f in FIRMS if f not in ("Topstep", "Apex")]
MAIN0 = 500_000                     # first path number (and seed) of the 12-month lives (lockstep_portfolio_v10 'main')

def ci95(x):
    """95% half-width of the mean of independent values: Student t with n - 1 degrees of freedom, sample sd"""
    x = np.asarray(x, dtype=float); n = len(x)
    return float(O.tq(n - 1) * x.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")

def lives(p, RR=None): return [r for r in (RR if RR is not None else R) if r["p"] == p]
def stats_of(rs):
    M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1); n = len(rs)
    y = M[:, :12].mean(1)
    tr = np.array([r["trough"] for r in rs])
    return dict(n=n, ev=float(y.mean()), ci=ci95(y), ss=float(M[:, 1:12].mean()), M=M, C=C,
                p05=np.percentile(C[:, 11], 5), p50=np.percentile(C[:, 11], 50), p95=np.percentile(C[:, 11], 95),
                ahead12=float(np.mean(C[:, 11] > 0)), tr50=np.percentile(tr, 50), tr05=np.percentile(tr, 5), tr01=np.percentile(tr, 1),
                conflicts=int(sum(r["conflicts"] for r in rs)), orders=float(np.mean([r["orders_per_trading_day"] for r in rs])))
_PS = {}
def pstats(p):
    if p not in _PS:
        s = stats_of(lives(p)); s["acc"] = len(SLOTS[p]); s["firms"] = len({firm_of(x["firm"]) for x in SLOTS[p]}); _PS[p] = s
    return _PS[p]
def paired(pa, pb, RR=None, RR2=None):
    """paired difference b - a of first-year EV/month between two portfolios on the same seeds (same paths)"""
    a = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(pa, RR)}
    b = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(pb, RR2 if RR2 is not None else RR)}
    ks = sorted(set(a) & set(b)); d = np.array([b[k] - a[k] for k in ks])
    return float(d.mean()), ci95(d), len(d)
def within(d, ci): return abs(d) <= ci
def iv_words(d, ci):
    """the reading of a 95% interval d +- ci, for the sentence that quotes it"""
    return "the interval contains zero" if within(d, ci) else ("the interval lies above zero" if d > 0 else "the interval lies below zero")

def per_firm(rs):
    out = collections.defaultdict(lambda: dict(pay=0.0, fee=0.0, req=0.0, buys=0.0, credits=0.0, cancelled=0.0))
    for r in rs:
        for key, k2 in (("payouts", "pay"), ("fees", "fee"), ("requests", "req"), ("buys", "buys"), ("credits", "credits"), ("cancelled", "cancelled")):
            for f, v in (r.get(key) or {}).items(): out[f][k2] += v
    n = len(rs) * 12
    return {f: {k: v / n for k, v in d.items()} for f, d in out.items()}

def _slot_items(p):
    """[(continuing row, count)] of a portfolio's accounts"""
    g = collections.Counter((s["firm"], s["instr"], s["size"]) for s in SLOTS[p])
    items = []
    for (prog, instr, size), n in g.items():
        r = fin(prog, instr, size=size); c = cont(r) if r else None
        if c: items.append((c, n))
    return items
def renewal_sum(p):
    """the sum of the accounts' continuing-slot rates as printed (each rounded to the dollar first)"""
    return total([(c["rate"], n) for c, n in _slot_items(p)])
def renewal_sum_ci(p):
    """the 95% half-width of that sum from the per-path sums of every programme in it (they share their paths: their errors
    are correlated; review of version 8, finding 15), and the number of paths"""
    tot, ci, G = sum_ci(_slot_items(p))
    return ci, G

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
    return table(["Firm (tier)", "Per-person limit", "Copying between accounts", "Market", "Recommended", "EV/month", "Largest modelled", "EV/month"], rows, cls="small", num_from=5, hl=(len(rows) - 1,),
                 cap="EV per month: each account's continuing-slot rate (8.3: the average cash per month dated in years 2 to 9 of a slot that buys a new evaluation whenever its attempt ends, starting from today's prices), rounded to the dollar and summed; each total is the sum of the figures printed above it. "
                     "A firm whose programme is not worth it under the plan's policies has no accounts. "
                     "'Largest modelled' is the largest allocation the plan models under each firm's limit and copying rule, one account per slot at a time: at FTMO four slots under its $400,000 cap on funded accounts (Challenges themselves are unlimited; running more Challenges in parallel is not modelled, Appendix [[APP_INV]]); "
                     "at GFT, FunderPro, BrightFunded and Blue Guardian, which allow a trader's own accounts to trade alike, the limit filled with 100K or 200K accounts, whichever is worth more in all; at FundedNext, which forbids copying between its own accounts, one account (a second on a market of its own, within its $300,000, is not modelled); at Maven one account, because a second would share the trader's $10,000 per 30 days, which the engine does not model across accounts; at Fintokei four 100K accounts fill its 400,000 EUR/USD of funded accounts. "
                     "It includes The5ers' optional small New accounts, which a literal reading of The5ers' size rule could flag ([[CH_RISK]].2: not recommended). Futures (Topstep, Apex) are an optional layer, in neither total.")

def _pair_rows():
    """for each CFD firm: the plan's programme and market, its 100K and 200K final rows and their continuing rows"""
    out = []
    for f in CFD_FIRMS:
        pi = [(p, i) for p, i, s, n in ALLOC[f]["rec"][:1]] or ([PROGS_OF[f][0]] if PROGS_OF.get(f) else [])
        for p, i in pi:
            a = fin(p, i, size=100_000); b = fin(p, i, size=200_000)
            if not (a and b): continue
            ca, cb = cont(a), cont(b)
            if not (ca and cb): continue
            out.append((f, p, i, a, b, ca, cb))
    return out

def size_table():
    rows = []
    for f, p, i, a, b, ca, cb in _pair_rows():
        fa = rules_of(a)["fee"]; fb = rules_of(b)["fee"]
        d, dci, G = sum_ci([(cb, 1), (ca, -2)])
        shown = r0(cb["rate"]) - 2 * r0(ca["rate"])
        rows.append([short(p), usd(fa, 2), usd(fb, 2), sgn(fb - 2 * fa, 2), usd(2 * r0(ca["rate"])), usd(r0(cb["rate"])), f"{sgn(shown)} &plusmn; {usd(dci)}"])
    return table(["Programme", "100K fee", "200K fee", "200K &minus; 2 &times; 100K fee", "2 &times; 100K: EV/month", "1 &times; 200K: EV/month", "Difference (95%)"], rows, cls="small",
                 cap="Continuing-slot rates (8.3) of the plan's setting at 100K and scaled to 200K, run on the same sixteen paths with the same seeds; the difference is that of the printed rates, its interval computed from the per-path differences (Student t, 15 degrees of freedom). "
                     "Where every rule scales with the account the difference is the fee and the refund that follows it, up to the rounding of whole lots and the 0.01-lot filler and keep-alive positions, which do not scale (11.1 measures the scaling path by path). "
                     "Rules in fixed dollars do not scale: GFT's $3,000 day cap and the $10,000 limit in its first-payout cap min(6%, $10,000), and the minimum payouts.")

def size_text():
    rows = {f: (p, i, a, b, ca, cb) for f, p, i, a, b, ca, cb in _pair_rows()}
    out = ("<p><strong>The answer, firm by firm.</strong> With the formula of [[CH_ALLOC]].2, one account of size \\(2S\\) beats two of size \\(S\\) exactly when \\(F(2S) &lt; 2F(S)\\), by \\((2F(S) - F(2S))\\big(1 - (1-f)P q_R\\big)\\) per attempt where the refund is the fee paid (the whole saving where there is none), unless a rule fails to scale. "
           "Where the recommended plan holds one account (the tier-D firms and FundedNext), it uses the size whose continuing-slot rate is higher. At the full allowance GFT, FunderPro, BrightFunded and Blue Guardian, which allow a trader's own accounts to trade alike, fill their limits with 100K or 200K accounts, whichever is worth more in all; FundedNext, which forbids copying between its own accounts, keeps one (a second would need a market no other account of the firm trades). ")
    if "GFT" in rows:
        p, i, a, b, ca, cb = rows["GFT"]
        d, dci, G = sum_ci([(cb, 1), (ca, -2)]); d1, d1ci, _ = sum_ci([(cb, 1), (ca, -1)])
        out += (f"GFT is the case where the formula fails: at 200K its first two payouts are capped at $10,000 rather than at 6% (which would be $12,000), and its $3,000 day cap binds twice as hard. "
                f"One 200K account against two 100K accounts: {sgn(r0(cb['rate']) - 2 * r0(ca['rate']))} &plusmn; {usd(dci)} a month ({iv_words(d, dci)}); both are allowed (GFT's prohibited-practices page, updated 6 October 2026, allows copying between a trader's own accounts whenever they were bought; version 9 read the opposite). "
                f"One 200K account against one 100K account: {sgn(r0(cb['rate']) - r0(ca['rate']))} &plusmn; {usd(d1ci)} ({iv_words(d1, d1ci)}).")
    out += "</p>"
    if "Recommended, FTMO as 2 x 200K" in SLOTS:
        d = paired(REC, "Recommended, FTMO as 2 x 200K")
        out += (f"<p><strong>FTMO, 4 &times; 100K or 2 &times; 200K.</strong> The same fee per dollar and the same rules. The paired difference of the whole portfolio's first year on the same {d[2]:,} paths is "
                f"{sgn(d[0])} &plusmn; {usd(d[1])} a month ({iv_words(d[0], d[1])}). In the model the four 100K accounts start together and take the same trades, and they stay in step until their outcomes first differ; "
                f"four 100K accounts and two 200K accounts (both $400,000) therefore bring in nearly the same cash; the standard deviation of a first year's cash per month is {usd(_sd12(REC))} with four 100K accounts and {usd(_sd12('Recommended, FTMO as 2 x 200K'))} with two 200K accounts (the whole portfolio, the rest unchanged). "
                "Two accounts make half as many payout requests, which matters only if refusals are a per-request risk (Chapter [[CH_REF]]). The plan uses four 100K accounts for the headline.</p>")
    return out

def _sd12(p):
    """the sample standard deviation over lives of a first year's cash per month"""
    return float(np.std([np.mean(r["monthly"][:12]) for r in lives(p)], ddof=1))

# ------------------------------------------------------------------ portfolios
def portf_table():
    rows = []
    for p in PNAMES:
        s = pstats(p)
        rows.append([PLABEL.get(p, p), str(s["acc"]), str(s["firms"]), pm(s["ev"], s["ci"]), usd(s["ss"]), usd(renewal_sum(p)), usd(s["p05"]), usd(s["p50"]), usd(s["p95"]), usd(s["tr50"]), usd(s["tr05"])])
    return table(["Portfolio", "Accounts", "Firms", "First year, EV/month (95%)", "Months 2&ndash;12", "Sum of continuing-slot rates", "First-year cash p5", "median", "p95", "Lowest cumulative cash: median", "p5"],
                 rows, cls="small", hl=(PNAMES.index(REC),) if REC in PNAMES else (),
                 cap=f"{len(lives(REC)):,} simulated first years per portfolio, each on its own new price paths (path numbers {MAIN0:,} to {MAIN0 + len(lives(REC)) - 1:,}; the same paths and seeds for every portfolio, so differences are paired). "
                     "First year: total cash over 12 months &divide; 12, after every fee modelled. Sum of continuing-slot rates: the accounts' Part II rates (8.3), each rounded to the dollar and summed; a different quantity (8.5). "
                     "Lowest cumulative cash: the deepest point of fees paid minus cash received.")

def conflict_sentence():
    n = len(R); c = sum(r["conflicts"] for r in R)
    if c == 0: return f"In {n:,} simulated years no two accounts held opposite positions on one market."
    return f"In {n:,} simulated years the engine recorded {c:,} moments when two accounts held opposite positions on one market."

def portf_text():
    a = pstats(REC)
    out = [f"<p><strong>Three quantities.</strong> The recommended portfolio's first year averages {usd(a['ev'])} a month (&plusmn;{usd(a['ci'])}); months 2&ndash;12 average {usd(a['ss'])}; the sum of its accounts' continuing-slot rates is {usd(renewal_sum(REC))} (&plusmn;{usd(renewal_sum_ci(REC)[0])}). "
           f"They answer different questions (8.5), and Section [[CH_LOCK]].6 follows the portfolio itself into its second and third years. {pct(a['ahead12'], 1)} of simulated first years ended ahead; the 5th percentile of first-year cash is {usd(a['p05'])}.</p>",
           f"<p><strong>Opposite positions.</strong> {conflict_sentence()} The recommended plan places about {a['orders']:.0f} orders a trading day across all its accounts.</p>"]
    pairs = [("All firms at full caps", REC), ("All firms at full caps + The5ers small accounts", "All firms at full caps"), ("Recommended + futures", REC), ("Tier A + B", "Tier A"), (REC, "Tier A + B")]
    lines = []
    for b_, a_ in pairs:
        if a_ in SLOTS and b_ in SLOTS:
            d, ci, n = paired(a_, b_)
            lines.append(f"{PLABEL.get(b_, b_)} minus {PLABEL.get(a_, a_)}: {sgn(d)} &plusmn; {usd(ci)}")
    if lines: out.append("<p><strong>Paired differences</strong> of first-year EV per month (same paths and seeds, 95%): " + "; ".join(lines) + ".</p>")
    return "".join(out)

def month_fig():
    s = pstats(REC); C = s["C"] / 1e6
    mm = lambda v: ("\u2212" if v < -1e-9 else "") + f"${abs(v):.2f}M"
    med = np.percentile(C, 50, axis=0); lo = np.percentile(C, 5, axis=0); hi = np.percentile(C, 95, axis=0); mean = C.mean(0)
    W, H, l0, r0_, t0, b0 = 640, 250, 56, 96, 22, 34
    ymax = math.ceil(hi.max() * 4) / 4 + 0.1; ymin = min(0, lo.min()) - 0.05
    step = 0.25 if ymax < 2 else 0.5
    X = lambda i: l0 + i / 12 * (W - l0 - r0_); Y = lambda v: t0 + (ymax - v) / (ymax - ymin) * (H - t0 - b0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    yv = math.floor(ymin / step) * step
    while yv <= ymax + 1e-9:
        g.append(f'<line x1="{l0}" x2="{W - r0_}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RULE}" stroke-width="{1 if abs(yv) < 1e-9 else 0.5}"/>')
        g.append(t(l0 - 6, Y(yv) + 3, mm(yv), 8, "end", MUT, True)); yv += step
    for i in range(0, 13): g.append(t(X(i), H - b0 + 14, str(i), 8, "middle", MUT, True))
    band = [(X(0), Y(0))] + [(X(i + 1), Y(hi[i])) for i in range(12)] + [(X(i + 1), Y(lo[i])) for i in range(12)][::-1] + [(X(0), Y(0))]
    g.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in band) + f'" fill="{S1}" fill-opacity="0.14" stroke="none"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(med[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S1}" stroke-width="2"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(mean[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S2}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    g.append(t(X(12) + 6, Y(hi[11]) + 3, "95th pct " + mm(hi[11]), 8, "start", MUT))
    g.append(t(X(12) + 6, Y(med[11]) + 3, "median " + mm(med[11]), 8, "start", INK))
    g.append(t(X(12) + 6, Y(mean[11]) + 14, "mean " + mm(mean[11]), 8, "start", INK))
    g.append(t(X(12) + 6, Y(lo[11]) + 3, "5th pct " + mm(lo[11]), 8, "start", MUT))
    g.append(t((l0 + W - r0_) / 2, H - 4, "months since starting", 8.5, "middle", MUT))
    g.append(t(l0, 12, "Cumulative cash of the recommended plan: median (solid), mean (dashed), 5th to 95th percentile (band)", 8.5, "start", INK))
    g.append("</svg>")
    return fig("".join(g), f"{len(lives(REC)):,} simulated first years of the recommended plan ({len(SLOTS[REC])} accounts), each on its own paths. Cash = payouts received minus fees paid.")

def month_table():
    s = pstats(REC); M = s["M"]; C = s["C"]
    rows = [[str(i + 1), usd(M[:, i].mean()), usd(np.percentile(M[:, i], 10)), usd(np.percentile(M[:, i], 50)), usd(np.percentile(M[:, i], 90)), usd(C[:, i].mean()), pct(np.mean(C[:, i] > 0), 0)] for i in range(12)]
    return table(["Month", "Mean cash", "p10", "median", "p90", "Cumulative mean", "Ahead"], rows, cls="small", num_from=1,
                 cap="Ahead: the share of lives whose cumulative cash is above zero at the end of the month.")

def long_text():
    rs = LONG.get("R", [])
    if not rs: return "<p>(36-month runs not available.)</p>"
    M = np.array([r["monthly"] for r in rs]); n = len(rs)
    y1 = M[:, :12].mean(1); y23 = M[:, 12:].mean(1); o12 = np.array([r["open12"] for r in rs])
    s0 = min(r["seed"] for r in rs)
    rows = [[f"months {a + 1}&ndash;{b}", pm(M[:, a:b].mean(), ci95(M[:, a:b].mean(1)))] for a, b in ((0, 12), (12, 24), (24, 36))]
    rows.append(["month 12 alone", pm(M[:, 11].mean(), ci95(M[:, 11]))])
    rows.append(["months 11 and 13", f"{usd(M[:, 10].mean())} and {usd(M[:, 12].mean())}"])
    tb = table(["Period (36-month lives)", "Average cash per month (95%)"], rows, cls="small", num_from=1,
               cap=f"{n} simulated 36-month lives of the recommended plan, each on its own new paths (path numbers {s0:,} to {s0 + n - 1:,}).")
    rs_ = renewal_sum(REC); rs_ci, G = renewal_sum_ci(REC)
    d23 = M[:, 12:24].mean(1) - M[:, 24:36].mean(1); d23m = float(d23.mean()); d23ci = ci95(d23)
    gap = rs_ - y23.mean()
    se_w = ci95(y23) / O.tq(n - 1); se_s = rs_ci / O.tq(G - 1)
    z = abs(gap) / math.hypot(se_w, se_s)
    txt = (f"<p><strong>Months 13&ndash;36.</strong> They average {pm(y23.mean(), ci95(y23))} a month. That is the average over a finite window that starts from today's prices, not a stationary rate (8.3: the price in the model has no stationary distribution). "
           f"Its two annual windows differ by {sgn(d23m)} &plusmn; {usd(d23ci)} a month (months 13&ndash;24 minus 25&ndash;36, paired over the same lives, 95%; {iv_words(d23m, d23ci)}). "
           f"The sum of the accounts' continuing-slot rates from Part II (each account alone, years 2 to 9 of a slot) is {pm(rs_, rs_ci)}, its interval computed from the per-path totals of all the portfolio's programmes, which share their paths; "
           f"the portfolio's window average is {usd(abs(gap))} {'lower' if gap > 0 else 'higher'}, {z:.1f} combined standard errors (the two estimates are independent). The two are not the same quantity: the slot rate averages years 2 to 9 of one account alone, the lives months 13 to 36 of all accounts together. "
           "The sum is also not a selection-free estimate: the same continuing-slot figures chose between each firm's programmes, markets and sizes, so it can carry a little winner's bias, while the portfolio lives run on fresh paths. "
           + (f"The first year is lower ({usd(y1.mean())}) because it carries the start-up: fees at once, payouts later. " if y1.mean() < y23.mean() else f"The first year averages {usd(y1.mean())}. ")
           + slot_text(rs) +
           f"<strong>Value of the accounts open at month 12</strong>: the cash those accounts (evaluations in progress and funded accounts) go on to pay after month 12 averages {usd(o12.mean())} (&plusmn;{usd(ci95(o12))}); it belongs to the first year's purchases but arrives later.</p>")
    return tb + txt + pair_text()

def slot_text(rs):
    """each firm's accounts inside the 36-month portfolio (months 13-36) against their continuing-slot rates alone, with both
    intervals (version 10: version 9 gave the portfolio's interval only; the slot rates have their own)"""
    if not rs or "slot_cash" not in rs[0]: return ""
    sl = rs[0]["slot_prog"]; n = len(rs); months = 24.0
    by = collections.defaultdict(list)
    for r in rs:
        acc = collections.Counter()
        for sid, v in r["slot_cash"].items(): acc[firm_of(sl[int(sid)][0])] += v / months
        for f in {firm_of(x[0]) for x in sl}: by[f].append(acc.get(f, 0.0))
    items = collections.defaultdict(list)
    for (prog, instr, size), k in collections.Counter((p, i, s) for p, i, s in sl).items():
        r = fin(prog, instr, size=size); c = cont(r) if r else None
        if c: items[firm_of(prog)].append((c, k))
    parts = []; far = 0
    order = sorted(by, key=lambda f: -total([(c["rate"], k) for c, k in items.get(f, [])]))
    for f in order:
        v = np.array(by[f]); a_m, a_ci = float(v.mean()), ci95(v)
        s_tot = total([(c["rate"], k) for c, k in items.get(f, [])]); _, s_ci, G = sum_ci(items.get(f, []))
        zz = abs(a_m - s_tot) / max(math.hypot(a_ci / O.tq(n - 1), s_ci / O.tq(max(G - 1, 1))), 1e-9)
        far += zz > 2
        parts.append(f"{f} {usd(a_m)} &plusmn; {usd(a_ci)} against {usd(s_tot)} &plusmn; {usd(s_ci)} ({zz:.1f})")
    return ("Firm by firm, the portfolio's accounts in months 13&ndash;36 against the sum of the same accounts' continuing-slot rates alone, each with its 95% interval (in brackets the difference in combined standard errors): " + "; ".join(parts) + ". "
            f"{far} of the {len(parts)} firms differ by more than two combined standard errors. The two need not agree beyond sampling error: inside the portfolio an account copies the direction of any position already open in its market, so its trades differ from those of the slot alone, and the windows differ (months 13&ndash;36 against years 2 to 9). ")

def pair_text():
    q = PAIRF
    if not q: return ""
    lv = json.load(open("lockstep_v10_pairfirms_lives.json"))["R"] if os.path.exists("lockstep_v10_pairfirms_lives.json") else []
    tot = collections.defaultdict(float)
    for r in lv: tot[r["seed"]] += float(np.mean(r["monthly"][12:]))
    sa = np.array(list(tot.values())) if tot else np.array([q["sum_alone"]])
    ren = total([(v, 1) for v in q["renewal"].values()])
    t1 = f"{sgn(q['diff'])} &plusmn; {usd(q['ci'])} a month over months 13&ndash;36 ({iv_words(q['diff'], q['ci'])})"
    t2 = f"{sgn(q['diff_y1'])} &plusmn; {usd(q['ci_y1'])} in the first year ({iv_words(q['diff_y1'], q['ci_y1'])})"
    return (f"<p><strong>Each firm alone, on the same paths.</strong> On the first {q['n']} of these lives, every firm's accounts were also run alone, on the same paths and calendar. "
            "This compares two policies, not a test of linearity: alone, a firm's account chooses its own direction where in the portfolio it copies the direction of an account already open, so the trades differ. "
            f"Full portfolio minus the sum of the firms alone (paired, 95%): {t1}; {t2}. "
            f"On those paths the firms alone average {pm(sa.mean(), ci95(sa))} a month in months 13&ndash;36, against {usd(ren)} for the sum of their continuing-slot rates in Part II; "
            "every account on the Nasdaq trades the same path, largely in the same direction, so the accounts' sampling errors move together, which is why that interval is wide.</p>")

def budget_table():
    rs = BUDGET.get("R", [])
    if not rs: return ""
    rows = []
    base = [r for r in rs if not r["kw"].get("budget")]
    bev = np.mean([np.mean(r["monthly"]) for r in base]) if base else None
    for b in sorted({r["kw"].get("budget") for r in rs if r["kw"].get("budget")}) + [None]:
        g = [r for r in rs if r["kw"].get("budget") == b]
        s = stats_of(g)
        buys = np.mean([sum((r.get("buys") or {}).values()) for r in g])
        rows.append([usd(b) if b else "unlimited", pm(s["ev"], s["ci"]), pct(s["ev"] / bev, 0) if bev else "", f"{buys:.0f}", pct(s["ahead12"], 0), usd(s["p05"]),
                     usd(np.mean([r["wallet_low"] for r in g])) if b else "&ndash;"])
    lowest = min((r["kw"]["budget"] + r["trough"] for r in rs if r["kw"].get("budget")), default=None)
    n = len(base)
    return table(["Starting cash", "First year, EV/month", "of unlimited", "Evaluations bought in the year", "Ahead at 12 months", "First-year cash p5", "Lowest cash left (mean)"], rows, cls="small", num_from=1,
                 cap="The recommended plan with a finite budget. Every purchase is an event at its own time, processed in time order with every trade: it is paid from the cash dated at or before it (the starting cash, less earlier purchases, plus payouts received by then), and otherwise waits a day at a time (version 9; version 8 let a purchase use a payout dated after it: review of version 8, finding 1). "
                     + (f"The cash dated by the ledger never falls below zero in any life (asserted in every run; lowest {usd(lowest, 2)}). " if lowest is not None else "")
                     + f"Slots are filled in order of continuing-slot rate per fee dollar. {n} lives per row, on the main stage's first {n} paths and seeds in every row.")

def scen_rows():
    out = []
    base = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(REC)}
    def add(label, rs, paired_=True):
        if not rs: return
        s = stats_of(rs)
        d = ""
        if paired_:
            dd = np.array([np.mean(r["monthly"][:12]) - base[r["seed"]] for r in rs if r["seed"] in base])
            d = f"{sgn(dd.mean())} &plusmn; {usd(ci95(dd))}" if len(dd) > 1 else ""
        out.append([label, pm(s["ev"], s["ci"]), d, usd(s["p05"]), usd(s["tr05"])])
    b200 = [r for r in lives(REC) if r["seed"] < MAIN0 + 200]
    add(f"Baseline (the same {len(b200)} paths)", b200, False)
    for c in (1.5, 2.0): add(f"All trading costs &times; {c:g}", [r for r in STRESS.get("R", []) if r["kw"].get("cost_mult") == c])
    add("Markets correlated 0.3 (one joint path)", CORR.get("R", []))
    for name in ("FundedNext 1% risk", "FundedNext 7-day pause"):
        add(f"{name} (behavioural remedy)", [r for r in BEHAV.get("R", []) if r["p"] == name])
    return out

def scen_table():
    rows = scen_rows()
    if not rows: return ""
    return table(["Scenario (recommended plan)", "First year, EV/month (95%)", "Difference to the baseline (paired, 95%)", "First-year cash p5", "Lowest cumulative cash p5"], rows, cls="small", num_from=1,
                 cap="Full portfolio runs, 200 lives each, with the seeds of the main stage's first 200 lives; the cost and behaviour scenarios also use the same paths, so their differences are paired life by life. "
                     "The correlated run draws all four markets from one joint path per life (different paths with the same seeds), so its difference is paired by seed only.")

# ------------------------------------------------------------------ refusals
TIERP = {"tiered": {"A": 0.02, "B": 0.05, "D": 0.15}, "harsh": {"A": 0.05, "B": 0.10, "D": 0.30}}
def tier_table():
    rows = []
    for tr, desc in (("A", "PropFirmMap A/A+, TrustPilot profile active"), ("B", "PropFirmMap B+, TrustPilot active"), ("D", "TrustPilot rating withheld for fake reviews; PropFirmMap D")):
        firms = [f for f in FIRMS if TIER.get(f) == tr]
        rows.append([tr, desc, ", ".join(firms), pct(TIERP["tiered"][tr], 0), pct(TIERP["harsh"][tr], 0)])
    return table(["Tier", "Evidence (read 4 October 2026 and again 12 October 2026, unchanged)", "Firms", "Refusal chance per request: tiered", "harsh"], rows, cls="small", num_from=3,
                 cap="Chosen scenarios, not measurements: public ratings do not calibrate refusal rates.")

def _refus(name):
    return [r for r in REFUS.get("R", []) if r["kw"].get("refuse") == LP.SCEN[name]]

def refusal_table():
    rows = []
    base = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(REC)}
    rs0 = None
    for name in ("tiered", "harsh"):
        rs = _refus(name)
        if not rs: continue
        if rs0 is None:
            rs0 = [r for r in lives(REC) if r["seed"] in {x["seed"] for x in rs}]
            s0 = stats_of(rs0)
            rows.append([f"All payouts honoured (the same {len(rs0)} paths)", pm(s0["ev"], s0["ci"]), "&ndash;", "100%", "0", "0%"])
        s = stats_of(rs)
        dd = np.array([np.mean(r["monthly"][:12]) - base[r["seed"]] for r in rs])
        nref = np.array([r.get("n_refused") or 0 for r in rs])
        rows.append([name.capitalize(), pm(s["ev"], s["ci"]), f"{sgn(dd.mean())} &plusmn; {usd(ci95(dd))}", pct(s["ev"] / s0["ev"], 0) if s0["ev"] > 0 else "",
                     f"{nref.mean():.2f}", pct(np.mean(nref > 0), 0)])
    if not rows: return ""
    return table(["Scenario", "First year, EV/month (95%)", "Difference (paired, 95%)", "Kept", "Refusals per life", "Lives with a refusal"], rows, cls="small", num_from=1,
                 cap=f"The recommended plan, {len(_refus('tiered'))} simulated first years per scenario with the paths and seeds of the main stage's first lives (paired). "
                     "Each payout request is refused with its firm's chance for the scenario, drawn inside the event engine when the request is made. A refusal voids that payout and every payout of the firm not yet processed, and the firm's accounts stop trading and buying at once, so the other accounts go on with the positions actually open "
                     "(version 9 removed a refused firm's later rows from a finished ledger, which left its positions steering the shared direction: review of version 9, finding 12).")

def refusal_text():
    pf = per_firm(lives(REC)); rows = []
    for f in FIRMS:
        if f not in pf: continue
        d = pf[f]; tr = TIER.get(f, "B"); rho = TIERP["tiered"][tr]
        life = 1 / (rho * d["req"]) if d["req"] > 0 else float("inf")
        rows.append([f, tr, f"{d['req']:.2f}", usd(d["pay"] / max(d["req"], 1e-9)) if d["req"] > 0 else "&ndash;", usd(d["pay"] + d["fee"]), f"{life:.0f}" if life < 1e6 else "&ndash;"])
    tb = table(["Firm", "Tier", "Payout requests a month", "Average payout", "Net cash a month", "Expected months until a refusal (tiered)"], rows, cls="small", num_from=2,
               cap="Recommended plan, first-year averages of the main stage with every payout honoured. Expected months until a refusal: \\(1/(\\phi r)\\) for requests at \\(r\\) a month, each refused with chance \\(\\phi\\).")
    s0 = None; kept = {}
    base = {r["seed"]: np.mean(r["monthly"][:12]) for r in lives(REC)}
    for name in ("tiered", "harsh"):
        rs = _refus(name)
        if not rs: continue
        b = np.mean([base[r["seed"]] for r in rs]); kept[name] = stats_of(rs)["ev"] / b if b > 0 else None
    txt = f"<p>The recommended plan's accounts make about {sum(d['req'] for d in pf.values()):.1f} payout requests a month. "
    if kept.get("tiered") is not None and kept.get("harsh") is not None:
        txt += f"In the tiered scenario it keeps {pct(kept['tiered'], 0)} of its first-year value on the same paths, in the harsh one {pct(kept['harsh'], 0)}. "
    txt += "Every request carries its firm's refusal chance, so a firm the plan asks for payouts more often is more exposed; the request rates in the table are what the scenarios price.</p>"
    return tb + txt

def ref_example():
    pf = per_firm(lives(REC))
    if "FTMO" not in pf: return ""
    ft = pf["FTMO"]["req"]
    (dd,), v = chain(lambda r_: 1 / (0.02 * r_), [ft], [2], 0)
    return (f"In the recommended plan the FTMO accounts together make about {ft:.{dd}f} requests a month: at \\(\\phi = 2\\%\\), FTMO is expected to last \\(1/(0.02 \\times {ft:.{dd}f}) = {v:.0f}\\) months.")

def part3_fills(ch_alloc, ch_lock, ch_ref):
    return dict(CH_ALLOC=ch_alloc, CH_LOCK=ch_lock, CH_REF=ch_ref, ALLOC_TABLE=alloc_table(), SIZE_TABLE=size_table(), SIZE_TEXT=size_text(),
                LIVES=f"{len(R):,}", CONFLICT_SENTENCE=conflict_sentence(), PORTF_TABLE=portf_table(), PORTF_TEXT=portf_text(), MONTH_FIG=month_fig(), MONTH_TABLE=month_table(),
                LONG_TEXT=long_text(), BUDGET_TABLE=budget_table(), SCEN_TABLE=scen_table(), BOUND_TEXT=bound_text(),
                TIER_TABLE=tier_table(), REFUSAL_TABLE=refusal_table(), REFUSAL_TEXT=refusal_text(), REF_EXAMPLE=ref_example(),
                FN_HP_MKTS=f"FundedNext {_MK[LP.FN_I]}, Hola Prime {_MK[LP.HP_I]}", EUR_FIRM="FundedNext" if LP.FN_I == "EURUSD" else "Hola Prime")
_MK = {"EURUSD": "EURUSD", "XAUUSD": "gold"}

def bound_text():
    """the path generator's joint error bound over every account of a life (3.3), from the 'bound' stage"""
    rs = BOUND.get("R", [])
    if not rs: return ""
    jb = np.array([sum((r.get("joint_bound") or {}).values()) for r in rs])
    sb = np.array([r.get("single_bound") or 0.0 for r in rs])
    return (f"<p><strong>The path generator's error, jointly.</strong> Over {len(rs)} lives of the recommended plan (the main stage's first {len(rs)} paths and seeds), the joint bound of 3.3, summed over every sub-step of a life in which some position watches a barrier on each side, averages {jb.mean():.1e} per life "
            f"(largest {jb.max():.1e}); the per-bracket bounds of the same lives add up to {sb.mean():.1e} on average. Either way, the chance that a simulated life differs anywhere from one on exact Brownian paths is negligible.</p>")

# ------------------------------------------------------------------ Part IV
def settings_card():
    rows = []
    for f in CFD_FIRMS:
        for p, i, s, n in ALLOC[f]["rec"]:
            r = acct_row(p, i, s)
            if not r: continue
            T = trade_numbers(i, r["m"], r["L"], r["L"])
            lots = f"{T['vol']:.2f} lots"
            if i == "USDJPY": stop = f"{r['m']:g} &sigma;: {T['stop_pts_long']:.1f} pips long, {T['stop_pts_short']:.1f} short"
            else: stop = f"{r['m']:g} &sigma; = {T['stop_pts']:.1f} {T['unit']}s"
            rows.append([short(p), f"{n} &times; {kk(s)}", MSHORT[i], usd(r["L"]), stop, lots, f"{r['k']:g}", usd(r["X"]), usd(n * r0(r["EV_month"]))])
    return table(["Programme", "Accounts", "Market", "Risk per trade", "Stop", "Size", "k", "Payout target", "EV/month"], rows, cls="small tight", num_from=3,
                 cap="Stops in points (Nasdaq), pips (USDJPY, EURUSD) or dollars (gold) at the prices of 2 October 2026; a USDJPY stop sits a little closer for a long position than for a short one (3.2: the yen's dollar price is the model's price). Recompute \\(m\\sigma\\times\\)price weekly and re-measure \\(\\sigma\\) monthly. "
                     "Size: the volume of a trade at the full risk, rounded down to 0.01 lot. The take-profit is the smallest of \\(k\\) times the risk, the distance to the current target, 40% of the current target less today's profit (in an evaluation at most 40% of it), and any firm cap, plus the cost (4.1). EV/month: the accounts' continuing-slot rates as in Chapter [[CH_ALLOC]].")

def cost_rows():
    out = []
    for sp in SPECS:
        if sp.get("fut"): continue
        cs = {r["cost_mult"]: r for r in sens("cost", sp["prog"], sp["instr"])}
        if not all(c in cs for c in (1.0, 1.5, 2.0)): continue
        out.append([short(sp["prog"]), MSHORT[sp["instr"]]] + [usd(cs[c]["EV_month"]) for c in (1.0, 1.5, 2.0)] + [f"{cs[c]['days']:.1f}" for c in (1.0, 2.0)])
    return out

def _variant_rows(tags, labels):
    """sensitivity variants against the same programme's own baseline on the same paths and seeds (sens 'cost' at x1),
    with the paired difference over the four paths"""
    out = []
    for tag in tags:
        for r in sens(tag):
            b = [x for x in sens("cost", r["prog"], r["instr"]) if x["cost_mult"] == 1.0 and x["size"] == r["size"]]
            if not b: continue
            b = b[0]
            d = paired_diff(dict(clu=dict(V=r["Vc"], D=r["Dc"])), dict(clu=dict(V=b["Vc"], D=b["Dc"]))) if r.get("Vc") and b.get("Vc") else None
            out.append(dict(tag=tag, prog=r["prog"], instr=r["instr"], label=labels[tag], base=b, var=r, d=d))
    return out

def nofill_rows():
    out = []
    for x in _variant_rows(("nofill", "nohold"), {"nofill": "ordinary trades instead of fillers (the $20 margin and the keep-alive positions kept)",
                                                 "nohold": "no 3-minute hold (a trade under 2 minutes ends the account)"}):
        b, r, d = x["base"], x["var"], x["d"]
        out.append([short(x["prog"]), MSHORT[x["instr"]], x["label"], usd(b["EV_month"]), usd(r["EV_month"]), (f"{sgn(d[0])} &plusmn; {usd(d[1])}" if d else "&ndash;"),
                    f"{b.get('fillers', 0) / 12000:.2f}", f"{r.get('fillers', 0) / 12000:.2f}"])
    return out

def v10_variant_rows():
    plan = {(sp["prog"], sp["instr"]) for sp in SPECS}
    out = []
    for x in _variant_rows(("nonews", "fastpay", "nolock", "t5net"),
                           {"nonews": "trading through news (not permitted)", "fastpay": "payouts processed at the fast end of the stated time",
                            "nolock": "trading while a payout is processed (not permitted)", "t5net": "The5ers' cap on the trader's share, refund outside it"}):
        if (x["prog"], x["instr"]) not in plan: continue
        b, r, d = x["base"], x["var"], x["d"]
        out.append([short(x["prog"]), MSHORT[x["instr"]], x["label"], usd(b["EV_month"]), usd(r["EV_month"]), (f"{sgn(d[0])} &plusmn; {usd(d[1])}" if d else "&ndash;")])
    return out

def price_text():
    """the continuing-slot rates at half and at twice today's prices (continuing_v10.py price)"""
    if not CONTP: return ""
    out = []
    for mult, word in (("0.5", "half"), ("2.0", "twice")):
        rows = {(r["prog"], r["instr"], r["size"]): r for r in CONTP.get(mult, [])}
        items = []; base = []
        for (prog, instr, size), n in collections.Counter((s["firm"], s["instr"], s["size"]) for s in SLOTS[REC]).items():
            c = rows.get((prog, instr, size)); r = fin(prog, instr, size=size); b = cont(r) if r else None
            if c and b: items.append((c, n)); base.append((b, n))
        if not items: continue
        tot, ci, _ = sum_ci(items); btot, bci, _ = sum_ci(base)
        cov = sum(n for _, n in items); alln = len(SLOTS[REC])
        out.append(f"at {word} today's prices {pm(total([(c['rate'], n) for c, n in items]), ci)} against {pm(total([(b['rate'], n) for b, n in base]), bci)} at today's"
                   + (f" ({cov} of the {alln} accounts)" if cov != alln else ""))
    if not out: return ""
    return ("<p><strong>The price level.</strong> Because lots and contracts are whole steps, and Alpha Capital's lot limit counts lots, the value of a setting depends a little on the price level, and the model's price has no level it returns to (8.3). "
            "The recommended plan's accounts' continuing-slot rates, summed: " + "; ".join(out) + " (4 slots per path at the other price levels, against 12 at today's: the first four of the same seeds).</p>")

def part4(ch_run, ch_risk):
    rec = pstats(REC)
    st = STRESS.get("R", [])
    def mean12(rs): return float(np.mean([np.mean(r["monthly"][:12]) for r in rs])) if rs else None
    c15 = mean12([r for r in st if r["kw"].get("cost_mult") == 1.5]); c20 = mean12([r for r in st if r["kw"].get("cost_mult") == 2.0])
    base200 = mean12([r for r in lives(REC) if r["seed"] < MAIN0 + 200])
    rt = _refus("tiered"); rh = _refus("harsh")
    honoured = stats_of([r for r in lives(REC) if r["seed"] in {x["seed"] for x in rt}])["ev"] if rt else None
    s1 = f"""
<section class="part"><span class="num">Part IV</span><h1>Running it</h1><p>The settings of every account in one place, the routine that runs them, and everything that could make the numbers wrong.</p></section>
<section class="chapter"><span class="eyebrow">Chapter {ch_run}</span><h1>The routine</h1>
<h2>{ch_run}.1 Every account's settings</h2>
{settings_card()}
<h2>{ch_run}.2 Placing a trade, step by step</h2>
<ol>
<li><strong>Is a trade allowed now?</strong> A position opens at the start of an hourly bar, on a weekday, from 01:00 to 18:00 UTC (EURUSD from 07:00), and only if the market is open: never at 19:00 UTC or later, and everything still open is closed at 20:00 UTC. At an account whose firm restricts news at its current stage (6.5), no position is open during an hourly bar that overlaps the 10 minutes before or after a high-impact release moving that market, none is opened in the bar before such a bar, and a position still open when such a bar starts is closed at its open. At least 10 minutes since this account's last close, whatever its result and direction (Hola Prime groups any re-entry within 10 minutes; FundingPips groups trade ideas).</li>
<li><strong>Direction.</strong> If any of your accounts holds this market, the same direction; EURUSD and USDJPY count as one market in dollars, so a position in one of them takes the dollar direction of any open position in the other (a long EURUSD goes with a short USDJPY). Otherwise the plan's rule: long if the last hourly close is above the one five closes before it (hours when the market is closed skipped), short if not. The rule has no edge (Chapter 11); its job is that no two of your accounts are ever opposite.</li>
<li><strong>Room.</strong> Floor room \\(= (\\text{{balance}} - \\text{{floor}} - \\$100 \\text{{ per }} \\$100\\text{{K}})/(1+\\rho)\\); day room \\(= (\\text{{daily limit}} - \\text{{today's loss}} - \\$200 \\text{{ per }} \\$100\\text{{K}})/(1+\\rho)\\); margin room \\(= 0.6\\,\\lambda\\, m\\sigma \\times \\text{{balance}}\\). If the floor room is under a tenth of the normal risk (or under the smallest position's risk, where that is larger, as one micro contract can be on futures), <strong>trade the rest</strong>: the largest volume whose stop at the plan's distance fits the room between the balance and the floor (at least 0.01 lot, or one contract), with its stop order placed at the floor level itself, so that a loss ends exactly at the floor (if today's room is smaller than the floor room, a normal stop inside today's room instead). It either recovers or ends the account in a breach, which frees its slot; buy the replacement only then. <strong>Not at GFT and Alpha Capital</strong>, whose rules prohibit "all or nothing" trading (GFT: "where you can lose the account in one trade"): there no such trade is placed; instead ask the firm to close the account, then buy the slot's next evaluation ([[LEFT_FLOOR]]). If even the smallest position's cost alone would reach the breach level, no position can be opened: ask the firm to close the account, then buy the slot's next evaluation (the model counts these: [[ABANDONED]]). If only the day room is short, wait until tomorrow.</li>
<li><strong>Risk.</strong> \\(l\\) = the smallest of the plan's risk and the three rooms. <strong>Stop</strong>: \\(m\\sigma\\times\\) price; size \\(= l /\\) (stop in points \\(\\times\\) dollars per point per lot), rounded down to the volume step (0.01 lot; whole contracts on futures, never fewer than one: if one contract at this stop risks more than \\(l\\), trade one contract if the floor and day rooms allow it). At Alpha Capital's funded accounts, never more than 40 lots per $100K.</li>
<li><strong>Take-profit.</strong> \\(w\\) = the smaller of \\(k\\,l\\) and the distance to the current target (or today's profitable-day target), but never a take-profit closer than 0.6 hourly standard deviations (finishing a little above a target is fine); then capped by 40% of the current target less today's profit (the whole calendar day's, including any made before a payout request today; in an evaluation never more than 40% of the target itself) and any firm cap (FXIFY 25% of the payout target per day less $1 per $100K, GFT's $3,000 a day less today's profit, Maven: the distance to $4,900 of funded profit less $550 per $100K for each profitable day the cycle still needs after today, and for today as well if this win would leave today short of +0.5%, and the distance to $10,000 of closed profit in any 30 days). If a cap leaves less than the minimum distance: with nothing made today, lower the risk until the cap is a full minimum-distance win; otherwise no further trade today. Place the take-profit for the win \\(w\\) at the rounded volume: distance \\(= (w + c)/\\)(volume \\(\\times\\) dollars per point per lot). <strong>At Maven</strong>, check the position actually placed: after the rounding, its take-profit must be at least 1.5 times as far from the entry as its stop (on the last trade of step 3, as its breach level). If it is not, keep the win the trade would make and lower the volume until it is; at the smallest position, raise the win to 1.5 times the stop distance if the caps allow it; otherwise wait until the next day.</li>
<li><strong>Place one bracket order</strong>; never move it. <strong>At Blue Guardian</strong>, whose minimum holding time is 2 minutes: open with an emergency stop at the account's breach level only, and place the bracket 3 minutes after the entry; if by then the price is already beyond the stop or the take-profit, close at the market. A funded Blue Guardian position whose floating loss reaches 2% of the account is closed by the firm's Guardian Shield. <strong>At 20:00 UTC close everything still open</strong>, and close at once any position open when a restricted news bar begins (step 1).</li>
<li><strong>Log it</strong>: time, account, market, direction, size, stop, target, fill, and the closing reason. The log is the evidence for any review.</li>
</ol>
<h2>{ch_run}.3 Phases, payouts and refills</h2>
<ul>
<li>When a phase target (plus $20 per $100K) is reached: stop. Where the firm counts trading days and accepts any opened position, place one minimal trade (0.01 lot, one contract on futures) on each of the next trading days not yet traded, at the day's first permitted hour, with a protective stop at the plan's stop distance, and close it at the market after 3 minutes; if a filler's loss takes the balance under the firm's target, resume normal trading. At Fintokei and Alpha Capital, which object to minimal trades, and at FunderPro and Hola Prime, whose rules object to abrupt or unexplained changes in position size, there are no fillers and no $20 margin: missing days are traded with ordinary trades, one a day. Where the firm counts profitable days, the daily target of 6.4 has met it.</li>
<li>When a funded account reaches its payout target: stop, and request the payout on the first allowed day (counted from the account's first trade), with no position open and at least 15 minutes after the last close. Withdraw everything above the starting balance (at Apex, above its $52,100 safety net), or the firm's cap where it binds (The5ers $4,000 a request at 100K with the fee refund inside it; GFT's first two payouts min(6%, $10,000) of the account; Topstep 50% of the balance up to $2,000; Apex $1,500 to $3,000 by request), and start the next cycle. While the request is pending (6.6): at Alpha Capital, FundingPips, FXIFY and Blue Guardian the firm locks the account; at Apex the plan pauses it; at Topstep the payout is deducted at once and protected; elsewhere trading goes on, and a breach before the request is processed cancels it.</li>
<li>Firm by firm: at Alpha Capital the first request also needs five trading days (until then trade at most once a day, past the target if needed). At Fintokei every request needs three trading days in the cycle (ordinary trades, one a day, if days are missing; no fillers) and comes at least 14 days after the previous payout was processed; The5ers also counts its 14 days from the processed payout, and a The5ers request needs $500 of profit at 100K. At Hola Prime the three profitable days must fall within the 14 days before the request. At Topstep a request is made one minute after a session's 4 p.m. Chicago close, after five winning sessions of $150 or more since the previous request's session, which does not count again. At Apex a request needs a balance of $52,600 and five qualifying days, every profitable day under 50% of the cycle's profit, today's included.</li>
<li>Take every payout by a method without a charge where the firm offers one (Wise or Aeropay at Topstep, a method other than crypto at Fintokei). At GFT, The5ers, FundedNext, Blue Guardian and Hola Prime every method carries the firm's fee (3%, 3.5%, up to 3.5%, 3%, and 2.5% with at least $5 by crypto or $25 by bank wire or Rise), which the figures include, Hola Prime's by crypto; Maven pays by bank transfer only in South Africa, Nigeria, Kenya and Ghana and elsewhere through Rise at $20 a payout (included) or by other options it does not name.</li>
<li>When a payout date arrives before the target is reached, request whatever profit the account holds, provided your share after the split (and after the firm's fee) reaches the firm's minimum (FTMO and FundedNext $20; FXIFY and Hola Prime $50; Fintokei, GFT and Blue Guardian $100; Alpha Capital and FunderPro $100 of profit, which is $80 of share; The5ers $150, with $500 of profit at 100K; FundingPips 1% of the account) and the firm's consistency and day rules allow it (FXIFY: no day above 25% of the payout's profit; profitable days at FundingPips 95%, GFT, Hola Prime, Maven and Blue Guardian), and start the next cycle; if a rule does not allow it, keep trading toward a target large enough for the rule to hold.</li>
<li>When an account fails (a breach, including the last trade of step 3) or is closed at your request (step 3): buy the next evaluation of the same programme (at FundedNext, after a pause if its gambling indicators are a concern: [[CH_LOCK]].7).</li>
<li>Never let 25 days pass without a trade on an account (most firms close or breach an account after 30 days without one, FXIFY after 60): on the day 22 days after the last entry, if nothing has been traded since, open one minimal position at the first permitted hour, as a filler (at Maven with a take-profit 1.5 times as far as its stop), and close it after 3 minutes, and open it before a payout request instead if the firm would lock the account past that day. The waits that need it are FXIFY's 30-day payout cycle with its read-only review and Maven's $10,000 per 30 days, which can stop trading for more than three weeks. At Fintokei, Alpha Capital, FunderPro and Hola Prime, which get no minimal trades, no wait comes near 25 days: their payout cycles are 14 days. Credits (The5ers) are spent on the next evaluation at that firm.</li>
<li>Before a market closure of two hours or more other than the weekend (a holiday, an announced halt), close everything two hours before it (FunderPro's rule; the model's calendar has no holidays).</li>
<li>Every order is placed by hand on its own account: no EA, script or trade copier (Maven allows no EA on any platform, FundingPips no copier service, GFT only EAs of your own). Before the first trade, ask FXIFY for its approval of the same trades on several of your accounts (it allows copy trading with prior approval) and ask The5ers to confirm in writing that your own entries on your own accounts are not the "copy trading with other traders or accounts" its prohibited-practices page names; keep both answers with the log.</li>
</ul>
<h2>{ch_run}.4 Cash needed</h2>
<p>Fees are paid before payouts arrive. In the simulation the running total of the recommended plan falls to {usd(rec['tr50'])} at its lowest in a typical first year, {usd(rec['tr05'])} in the worst 5% and {usd(rec['tr01'])} in the worst 1%. These are not amounts that keep every slot filled in every year: Section [[CH_LOCK]].7 runs the plan with fixed budgets, each purchase paid only from cash already received, and shows what each budget gives.</p>
<h2>{ch_run}.5 Workload</h2>
<p>About {rec['orders']:.0f} bracket orders a trading day across {len(SLOTS.get(REC, []))} accounts, a daily close-out at 20:00 UTC, the news blocks, payout requests and evaluation purchases.</p>
</section>
<section class="chapter"><span class="eyebrow">Chapter {ch_risk}</span><h1>What could make the numbers wrong</h1>
<h2>{ch_risk}.1 Higher trading costs</h2>
{table(["Programme", "Market", "EV/month: cost &times; 1", "&times; 1.5", "&times; 2", "Days per attempt &times; 1", "&times; 2"], cost_rows(), cls="small", num_from=2,
       cap="One 100K account at the plan's setting with a coin-flip direction, paths 1201&ndash;1204, 3,000 attempts on each (12,000 per cell), the same seeds in each row: random-start ratios (8.3), which rank and compare but are not the continuing-slot rates of Chapter [[CH_ALLOC]]. Higher costs lower the value of an attempt and also shorten attempts (more fail, sooner), which is why a value per month can fall less than proportionally.")}
<p>For the whole recommended portfolio, full portfolio runs (not ratios) give {usd(c15) if c15 is not None else '&ndash;'} a month at 1.5 times the costs and {usd(c20) if c20 is not None else '&ndash;'} at twice, against {usd(base200) if base200 is not None else '&ndash;'} for the same 200 lives at the assumed costs (Section [[CH_LOCK]].7; the {len(lives(REC)):,}-life headline is {usd(rec['ev'])}, a larger sample of the same quantity). <strong>Measure your real costs in the first week</strong> and redo the settings if they differ from 3.1 by more than a quarter.</p>
<h2>{ch_risk}.2 Behavioural rules the model cannot state</h2>
<p>These rules are applied at the firm's discretion. The figures in this document assume the plan's trading is not judged to break them; if it is, the affected payouts are lost, which is not the same as the random refusals of Chapter [[CH_REF]]:</p>
<ul>
<li><strong>FTMO</strong>: overleveraging, overexposure, one-sided bets and account rolling (none defined on its page); trades for manipulative purposes, including opposite positions across connected accounts; gap trading.</li>
<li><strong>Fintokei</strong>: "hitting the target through one or few identical trades"; token trades and "much smaller trades ... just to meet the minimum 3-day trading requirement". No trade makes more than 40% of a phase target, and the plan places no filler trades at Fintokei.</li>
<li><strong>The5ers</strong> (its prohibited-practices page, read 12 October 2026): bulk trading; "copy trading with other traders or accounts" (its example is a group of traders sharing signals; the plan's own entries on your own accounts are read as allowed, which descriptions of its FAQ support: confirm in writing, {ch_run}.3); one-sided bets; position sizes "substantially larger or smaller than your typical trading activity, whether compared across your own accounts or between your evaluation and funded account stages"; overleveraging and concentrated speculative positions; strategies that "artificially distribute profit across multiple days without proportionally distributing market risk" (opposing positions, or one trade idea partly closed across days). One position per account at a time, the same risk share and stop rule in both stages, no evaluation trade and no day above 40% of the target, flat every evening (each day's profit comes from that day's own trades at the full risk), and a direction that changes with the trend rule. The optional portfolio with The5ers' small accounts holds positions far smaller in dollars than its 100K account's (the same share of each account), which a literal reading of the size rule could flag: that portfolio is not recommended.</li>
<li><strong>FundedNext</strong>: one-sided betting (remedy: a 1% risk limit), account rolling, several breached accounts in a short span (remedies: 40% consistency on on-demand rewards or a lower split). Section [[CH_LOCK]].7 measures the remedies.</li>
<li><strong>Hola Prime</strong>: excessive or concentrated risk, unexplained deviations in position size (no fillers at Hola Prime), one-sided betting ("repeated positions in one direction without analysis"), profitability "materially dependent on concentrated outcomes". <strong>Alpha Capital</strong>: "all or nothing" (a significant change in lot size against the account's average; no last trade to the floor at Alpha), risk or loss of 2% or more, an open loss on one asset above 2% (its Max Risk Rule, which the plan's 1.75% plus cost stays under), trades under 2 minutes on average, minimal lots to pass trading days. <strong>GFT</strong>: "All-Or-Nothing Trading, where you can lose the account in one trade" (no last trade to the floor at GFT) and, in its own definition, more than 80% of the margin in one idea; martingale; large-volume trading "without a clear or logical trading strategy". <strong>FunderPro</strong>: "abrupt or unjustified changes in lot sizes" (no fillers at FunderPro). <strong>FXIFY</strong>: high-leverage news trading (the plan is flat around releases), statistical arbitrage ("high-risk trades ... aiming for significant wins to offset losses from multiple accounts": every account takes the same direction at a moderate risk, so no account's loss is another's win), herd trading, and in its terms one-sided bets, overleveraging and overexposure. <strong>Blue Guardian</strong>: margin above 80%, holding under 2 minutes (met by the 3-minute hold of step 6). <strong>Maven</strong>: large bets at 1:1.25 or worse (every position the plan places is at least 1:1.5, step 5); "excessive scalping", half or more of the trades held under a minute (no Maven trade in the engine closes within a minute); no EAs, no account mirroring; above $5,000 of payouts a risk interview, after which risking more than the amount its email states is a breach: check the plan's risk against that figure. <strong>One-sided bets</strong> (FTMO, The5ers, FXIFY, FundedNext, Hola Prime): the plan's direction follows the trend rule and changes with the market, but over a steadily trending week it can stay on one side for days, which a firm could read as one-sided. <strong>Other firms' fillers</strong> (FTMO, FXIFY, FundedNext, BrightFunded, the futures firms): their day definitions count a day on which a position is opened and state no minimum volume; that a 0.01-lot trade held 3 minutes is accepted is an assumption, and Section {ch_risk}.8 measures the plan without it. The last trade of step 3, at the firms that allow it, is a normal bracket at the plan's reward to risk with a small risk; a firm could still read a final trade sized to the floor as deliberate, which the model cannot price.</li>
</ul>
<h2>{ch_risk}.3 Payouts refused, accounts closed</h2>
<p>Chapter [[CH_REF]]: {usd(stats_of(rt)['ev']) if rt else '&ndash;'} a month in the first year if payouts are refused at 2/5/15% per request by tier, {usd(stats_of(rh)['ev']) if rh else '&ndash;'} at 5/10/30%, on the same paths as the {usd(honoured) if honoured is not None else '&ndash;'} with every payout honoured.</p>
<h2>{ch_risk}.4 Spreads, gaps and news</h2>
<p>The engine's cost is an average. Spreads widen at the daily break (outside the plan's hours), at the open and around news. Since version 10 the plan's news blocks are simulated at every account and stage where the firm restricts news (6.5), on a calendar built from each agency's usual release pattern (no official calendar exists for the simulated years); wider spreads just outside the blocked bars, and stops filled beyond their level where the plan trades through a release (where the firm allows it), remain outside the model, and the cost stress of {ch_risk}.1 is the only allowance for them.</p>
<h2>{ch_risk}.5 Rules change</h2>
<p>Every rule the model uses is in the inventory of Appendix [[APP_INV]], with the page it was read from and the date it was read: {inv_read_sentence()}. Leverage, consistency rules, payout schedules, prices and per-person limits change often. Recheck before buying, and rerun the programme's optimisation (optimize_v10.py) when a rule that enters the model changes.</p>
<h2>{ch_risk}.6 The model itself</h2>
<ul>
<li><strong>Zero skill, zero drift.</strong> If entries are systematically late or fills worse, the edge is negative; the cost stress is the guide. A real trend in a market (the Nasdaq's long-run rise) is left out of the model (3.2); the plan's direction rule is symmetric, but over a given year a trend can favour or hurt it.</li>
<li><strong>Markets move together.</strong> The baseline gives gold, euro and yen independent paths; Section [[CH_LOCK]].7 measures a correlation of 0.3. Real correlations change and rise in crises.</li>
<li><strong>Taxes, and the costs of a payout method</strong> (banks, networks, currency conversion), are not modelled; the fees five firms take from every payout, and Maven's $20 a payout by Rise, are (7.4).</li>
</ul>
{price_text()}
<h2>{ch_risk}.7 What is not allowed, and is not in the plan</h2>
<p>No hedging across accounts or firms; no accounts in anyone else's name; no copy-trading services, EAs or other people's signals; no trading in restricted news windows (the plan's blocks, 6.5); no tick scalping, latency or gap arbitrage; no grid or martingale sizing; no deliberately failed accounts. Do not share or sell the plan: several firms treat traders who run the same marketed strategy as a group.</p>
<h2>{ch_risk}.8 Filler trades and holding times</h2>
<p>Where a firm counts any day on which a position is opened, the plan completes missing trading days with 0.01-lot trades held 3 minutes (6.3). The firms' day definitions state no minimum volume, but none says in so many words that such a trade is welcome, Fintokei and Alpha Capital object to it, and FunderPro and Hola Prime object to the size change it makes (none is placed at those four); so the plan's value is also measured without fillers at the other firms, missing days traded with ordinary trades of the plan, one a day, everything else unchanged (the phase still stops $20 per $100K above its target, and the keep-alive positions of 6.3 stay). Blue Guardian's 3-minute hold is measured the same way.</p>
{table(["Programme", "Market", "Variant", "EV/month: plan", "variant", "Paired difference (95%)", "Fillers per attempt: plan", "variant"], nofill_rows(), cls="small", num_from=3,
       cap="One 100K account at the plan's setting with a coin-flip direction, paths 1201&ndash;1204, 3,000 attempts on each, the same seeds in both cells of a row (random-start ratios); the paired difference is over the four paths (Student t, 3 degrees of freedom). Version 9's variant also removed the $20 margin, so two of its rows changed with no filler executed (review of version 9, finding 25).") if nofill_rows() else ""}
<h2>{ch_risk}.9 What the version 10 rules and readings cost</h2>
<p>Each of the plan's programmes run again with one rule or reading changed, everything else equal: trading through news where the firm restricts it, and trading while a payout is processed where the firm locks the account, are not permitted and are shown only to measure what the rule costs; payouts processed at the fast end of each firm's stated time, and The5ers' cap read as a cap on the trader's share with the refund outside it, are the other readings of what the firms state.</p>
{table(["Programme", "Market", "Variant", "EV/month: plan", "variant", "Paired difference (95%)"], v10_variant_rows(), cls="small", num_from=3,
       cap="As in the table above: one 100K account, paths 1201&ndash;1204, 12,000 attempts per cell, the same seeds in both cells, random-start ratios; paired over the four paths (Student t, 3 degrees of freedom).") if v10_variant_rows() else ""}
</section>"""
    return s1

# ------------------------------------------------------------------ appendices
def _f(subs):
    def f(x):
        for k, v in subs.items(): x = x.replace(f"[[{k}]]", str(v))
        return x
    return f

def review_appendix(subs):
    f = _f(subs)
    rows = [[f"{x['n']}", f"<strong>{x['title']}</strong><br><span class='verdict'>{x['verdict']}</span>", f(x["wrong"]), f(x["fix"])] for x in RV.R]
    t1 = table(["#", "Finding", "What was wrong in version 9", "What version 10 does"], rows, cls="small appx", num_from=9, w0="4%")
    na = sum(1 for x in RV.R if x["verdict"].startswith("agreed") and "part" not in x["verdict"])
    return (f'<section class="chapter"><span class="eyebrow">Appendix A</span><h1>Corrections: the version 9 review, point by point</h1>'
            f"<p>A detailed review of version 9 raised {len(RV.R)} findings, with the repository at hand. Every rule finding was checked on the firms' own pages (the inventory of Appendix [[APP_INV]] gives each page and date) "
            f"and every model finding was reproduced on version 9's code before it was fixed (the reproductions are listed in the table); {na} are agreed in full"
            + (f" and {len(RV.R) - na} in part" if len(RV.R) - na else "") + ". "
            "Each fix is described with the test that checks it (tests_v10.py) and, where a result moved, the new figure.</p>" + t1 + "</section>")

def audit_appendix(subs):
    f = _f(subs)
    rows2 = [[x["n"], f"<strong>{x['title']}</strong>", f(x["what"])] for x in RV.NEW]
    t2 = table(["#", "Error", "What it was, and the fix"], rows2, cls="small appx", num_from=9, w0="5%")
    return (f'<section class="chapter"><span class="eyebrow">Appendix A2</span><h1>Errors we found ourselves, and why the review found its errors first</h1>{f(RV.INTRO)}{t2}{f(RV.PROCESS)}</section>'
            f'<section class="chapter"><span class="eyebrow">Appendix A3</span><h1>The earlier reviews, in brief</h1><p>{RV.PRIOR}</p></section>')

def inventory_appendix():
    rules = INV.get("rules", [])
    order = FIRMS + ["every firm", "every firm with minimum trading days"]
    rows = []
    for firm in order:
        for r in [x for x in rules if x["firm"] == firm]:
            src = r["source"]
            src_txt = (f"<span class='k'>{src.replace('https://', '')}</span>" if src.startswith("http") else src)
            rows.append([firm, r["area"], r["rule"], r["model"], r["status"], f"{r['read']}; {r['basis']}: {src_txt}"])
    cnt = collections.Counter(r["status"] for r in rules)
    cap = ("Status: <em>modelled</em>, the engine applies the rule as stated; <em>plan</em>, the plan avoids the situation the rule governs with a stricter rule of its own; <em>cautious</em>, the wording leaves a question and the engine applies the stricter reading named; "
           "<em>assumption</em>, no published figure, and the engine uses the value named; <em>not binding</em>, the rule exists but the plan's settings cannot reach it, for the reason given. "
           "Basis: <em>page</em>, the firm's own page read directly; <em>snippet</em>, the firm's page as a search engine returned it (the page refused automated reading); <em>secondary</em>, a reviewer's description, where no firm page could be read. "
           f"{len(rules)} rows: " + ", ".join(f"{cnt[k]} {k}" for k in ("modelled", "plan", "cautious", "assumption", "not binding")) + ".")
    return (f'<section class="chapter"><span class="eyebrow">Appendix [[APP_INV]]</span><h1>Every rule, its source, and what the model does with it</h1>'
            "<p>Version 9 listed the rules it modelled. This inventory starts from the firms' rules instead, so that a rule the model leaves out has to appear here with its reason; it is written by rules_inventory_v10.py (rules_inventory_v10.json), and every programme chapter's rules table is drawn from it. "
            "Version 10 also compared every row with the engine's rule parameters (firms_v10.py), which found FTMO's $20 minimum payout missing from the engine (now applied) and the fees, refunds, splits and leverage missing from the inventory (now rows), and read every row again on 11&ndash;12 October 2026, which found the errors n39&ndash;n46 of Appendix A2; checking the plan's own limits and instructions against the engine then found n47 to n49 and added the inactivity rows of seven firms.</p>"
            + table(["Firm", "Area", "Rule as published", "What the model does", "Status", "Read; basis: source"], rows, cls="small appx", num_from=9, w0="9%", cap=cap) + "</section>")

def formula_sheet():
    return """
<section class="chapter"><span class="eyebrow">Appendix C</span><h1>Formula sheet</h1>
<table><thead><tr><th style="width:34%">Quantity</th><th>Formula</th><th>Exact for</th><th>Where</th></tr></thead><tbody>
<tr><td>Value of one attempt</td><td>\\(\\mathbb{E}[V] = \\Pr(\\text{pass})\\,\\mathbb{E}[C] + \\text{credits} - F\\)</td><td>always</td><td>1.2</td></tr>
<tr><td>Zero-cost example</td><td>\\(-F + P(\\alpha D + qR)\\), \\(q = D/(D+X)\\)</td><td>idealised model</td><td>1.3</td></tr>
<tr><td>Notional, target distance</td><td>\\(N = l/(m\\sigma)\\), \\(u = m\\sigma\\,(w + c)/l\\)</td><td>always (USDJPY: on the yen's dollar price, 3.2)</td><td>4.1</td></tr>
<tr><td>Win probability, mean, variance</td><td>\\(p = l/(l+w+c)\\); \\(-c\\); \\(l(w+c)\\)</td><td>fixed cost, binary outcome</td><td>4.2&ndash;4.3</td></tr>
<tr><td>Cost per unit of risk</td><td>\\(\\rho = \\kappa/(m\\sigma)\\)</td><td>always</td><td>4.4</td></tr>
<tr><td>Pass probability, no cost</td><td>\\(B/(A + B)\\)</td><td>exact landing on \\(A\\) or \\(-B\\)</td><td>5.1</td></tr>
<tr><td>Pass probability with cost</td><td>\\((e^{\\theta B} - 1)/(e^{\\theta(A+B)} - 1)\\), \\(\\theta = 2c/v\\)</td><td>approximation</td><td>5.2</td></tr>
<tr><td>Risk of the next trade; the terminal trade</td><td>\\(l = \\min(L, (x+B-b)/(1+\\rho), \\dots)\\); if that is \\(&lt; l_{\\min}\\): the volume of \\((x+B)/(1+\\rho)\\) at the plan's stop (at least the smallest), its stop order at the floor; win chance \\(l_e/(l_e + w + c)\\), \\(l_e = x + B - c\\); at GFT and Alpha Capital no terminal trade, the account closed instead</td><td>the plan's rule</td><td>5.4</td></tr>
<tr><td>Exact chain</td><td>\\(V(x) = p\\,V(x + w) + (1-p)\\,V(x - l - c)\\), and \\(N, K, T\\)</td><td>binary trades, per-trade caps</td><td>5.5</td></tr>
<tr><td>Accounting identity</td><td>\\(P\\,\\mathbb{E}[X_\\text{end}\\mid\\text{pass}] + (1-P)\\,\\mathbb{E}[X_\\text{end}\\mid\\text{fail}] = -\\mathbb{E}[\\text{cost}]\\); with every failure at \\(-B\\): \\(P = (B - K)/(\\mathbb{E}[X_\\text{end}\\mid\\text{pass}] + B)\\)</td><td>bounded stopped sum, mean of each trade \\(-c\\)</td><td>5.5</td></tr>
<tr><td>Two phases</td><td>\\(P = P_1 \\Pr(2 \\mid 1)\\); the engine estimates \\(\\Pr(2 \\mid 1)\\) directly; \\(= P_1P_2\\) with unconditional \\(P_2\\) in the calendar-free chain</td><td>always / the chain</td><td>6.1</td></tr>
<tr><td>Withdrawal identity</td><td>\\(\\mathbb{E}[W] = -\\mathbb{E}[X_\\text{end}] - \\mathbb{E}[\\text{funded cost}] - \\mathbb{E}[Q]\\), \\(Q\\) = profit forfeited (voided, cancelled or held back by a cap)</td><td>cycle-by-cycle stopping</td><td>7.1</td></tr>
<tr><td>Funded cash, cycle form</td><td>\\(\\alpha\\,(m_1 q_1 + m\\, q_1 q/(1 - q)) + R\\,q_1 q^{r-1}\\); \\(m_1, m\\) = the mean amount withdrawn at a cycle's success, \\(\\mathbb{E}[\\min(\\text{balance}, \\text{cap})]\\)</td><td>independent reset cycles</td><td>7.2</td></tr>
<tr><td>Two special first cycles (GFT)</td><td>\\(\\mathbb{E}[\\text{paid}] = q_a + q_a^2/(1-q_b)\\); \\(\\mathbb{E}[W] = m_a(q_a + q_a^2) + m_b\\,q_a^2 q_b/(1-q_b)\\), \\(m_a\\) the mean capped withdrawal</td><td>independent reset cycles</td><td>7.2</td></tr>
<tr><td>Cash given \\(n\\) paid cycles</td><td>\\(\\alpha(m_1 + (n-1)\\,m)\\) + refund (less $20\\(n\\) at Maven)</td><td>independent reset cycles (a mean: cash is random)</td><td>7.2</td></tr>
<tr><td>Trade duration</td><td>\\(m^2 (w + c)/l\\)</td><td>approximation (arithmetic motion)</td><td>8.1</td></tr>
<tr><td>Continuing-slot rate</td><td>cash dated in years 2 to 9 of a slot refilled at once, &divide; the months in them; averaged over 12 slots on each of 16 paths</td><td>a finite-horizon average from today's prices (no stationary distribution)</td><td>8.3</td></tr>
<tr><td>Random-start ratio</td><td>\\(30.44\\sum V/\\sum T\\) over attempts started at random points of a path</td><td>ranks settings</td><td>8.3, 9.1</td></tr>
<tr><td>Cluster-robust variance of a ratio</td><td>\\(\\frac{G}{G-1}\\sum_g (V_g - \\hat r T_g)^2/(\\sum_g T_g)^2\\); a sum of programmes: the same from the per-path sums of all of them</td><td>independent clusters</td><td>8.4</td></tr>
<tr><td>Path generator's error, one bracket, per watched sub-step</td><td>\\(G(r) = \\mathbb{E}\\min(1, 3e^{-(r^2 - Z^2)})\\), \\(r = W/\\sqrt v\\)</td><td>a valid bound</td><td>3.3</td></tr>
<tr><td>Path generator's error, all positions on a path, per sub-step</td><td>\\(5\\,P_\\text{ind}(u^*, \\ell^*)\\), \\(u^*, \\ell^*\\) the nearest barriers of all open positions</td><td>a valid bound</td><td>3.3</td></tr>
<tr><td>Margin at entry</td><td>\\(l \\le 0.6\\,\\lambda\\, m\\sigma\\,(S + x)\\)</td><td>the plan's rule</td><td>10.2</td></tr>
<tr><td>Scaling an account</td><td>\\(\\mathbb{E}[V(\\lambda S)] = P[\\lambda G(S) + q_R R(\\lambda S)] - F(\\lambda S)\\)</td><td>rules that scale</td><td>[[CH_ALLOC]].2</td></tr>
<tr><td>Paid cash under refusals</td><td>\\(a r (1-\\phi)(1 - e^{-\\phi r H})/(\\phi r)\\); \\(n\\) scheduled requests: \\(a(1-\\phi)(1-(1-\\phi)^n)/\\phi\\)</td><td>Poisson requests; a fixed schedule</td><td>[[CH_REF]].1</td></tr>
</tbody></table></section>"""

def glossary():
    return """
<section class="chapter"><span class="eyebrow">Appendix D</span><h1>Glossary</h1>
<table><tbody>
<tr><td style="width:24%"><strong>Keep-alive position</strong></td><td>A minimal position like a filler, opened on the day 22 days after an account's last entry if nothing has been traded since, so that no account goes 25 days without a trade (6.3).</td></tr>
<tr><td style="width:24%"><strong>Terminal trade</strong></td><td>The last bracket of an account whose room above the floor is too small for a normal trade: its stop order sits at the floor, so the account recovers or ends in a breach (5.4). Not placed at GFT and Alpha Capital, whose accounts are closed instead.</td></tr>
<tr><td><strong>Breach level</strong></td><td>The loss at which an account breaches: the nearer of its floor and today's loss limit. A barrier of every trade in the engine (4.1).</td></tr>
<tr><td><strong>Continuing slot</strong></td><td>One slot run back to back on one path and calendar, carrying everything an attempt passes to the next; its rate is the average cash per month dated in years 2 to 9 from today's prices (8.3).</td></tr>
<tr><td><strong>Random-start ratio</strong></td><td>\\(30.44\\sum V/\\sum T\\) over attempts started at random points of a path: the search's yardstick (8.3).</td></tr>
<tr><td><strong>Filler trade</strong></td><td>A 0.01-lot position (one micro contract on futures) held 3 minutes on a missing trading day, where a firm counts any opened position; none at Fintokei, Alpha Capital, FunderPro and Hola Prime (6.3).</td></tr>
<tr><td><strong>Allowance \\(D\\)</strong></td><td>The funded account's maximum loss: the floor sits \\(D\\) below the starting balance.</td></tr>
<tr><td><strong>Attempt</strong></td><td>One evaluation bought, from purchase until a phase fails, the account is closed because not even the smallest position fits its room (or, at GFT and Alpha Capital, because its room is below the smallest normal risk), or the funded account that followed it ends.</td></tr>
<tr><td><strong>Bold play</strong></td><td>Staking enough on each bet to reach the goal in one win; not used by the plan (5.6).</td></tr>
<tr><td><strong>Bracket</strong></td><td>A position with its stop-loss and take-profit attached at entry and never moved.</td></tr>
<tr><td><strong>Concentration policy</strong></td><td>No day above 40% of the current target (net), and in an evaluation no single trade either (6.7).</td></tr>
<tr><td><strong>Daily flat</strong></td><td>No entry from 19:00 UTC, everything closed at 20:00 UTC (6.5).</td></tr>
<tr><td><strong>News block</strong></td><td>An hourly bar that overlaps 10 minutes either side of a high-impact release moving the market, at a firm and stage that restricts news: no position open in it, none opened in the bar before (6.5).</td></tr>
<tr><td><strong>Engine</strong></td><td>The rule-by-rule simulation of an account on hourly price paths with one-minute sub-steps (acct_mc.py, pathfirm.py, lockstep.py).</td></tr>
<tr><td><strong>Exact chain</strong></td><td>The trade-level Markov chain of 5.5, solved by iteration (analytic_v10.py).</td></tr>
<tr><td><strong>Stream</strong></td><td>The random numbers of one synthetic path, keyed by path number, market, length and sub-steps (3.3; stream_manifest_v10.json).</td></tr>
<tr><td><strong>Payout target \\(X\\)</strong></td><td>The profit at which a funded account stops and requests a payout.</td></tr>
<tr><td><strong>Payout states</strong></td><td>A request is pending until the firm processes it; a breach before then cancels it unless the firm protects it, and some firms lock the account meanwhile (6.6).</td></tr>
<tr><td><strong>Renewal&ndash;reward</strong></td><td>The value per unit time of a repeated process, \\(\\mathbb{E}[V]/\\mathbb{E}[T]\\) when attempts start in a stationary state; the model's price has no stationary distribution, so the document reports finite-window averages instead (8.3).</td></tr>
<tr><td><strong>Slot</strong></td><td>One account position at one firm, refilled with a new evaluation whenever an attempt ends.</td></tr>
<tr><td><strong>Tier</strong></td><td>A firm's reliability class (A, B, D) from public evidence, used for the refusal scenarios.</td></tr>
<tr><td><strong>Winner's curse</strong></td><td>The upward bias of the best of many noisy estimates; every reported setting is re-measured on paths not used to choose it, but the choice between a firm's programmes, markets and sizes reuses the continuing-slot figures that are also reported (9.2).</td></tr>
</tbody></table></section>"""

def appendices(subs):
    files = [("calibrate.py, sigma_v32.json", "costs and trading hours per market; hourly volatilities"),
             ("multi.py, pathfirm.py", "synthetic price paths (one-minute Brownian-bridge sub-steps with their closes, one random stream per path and market; USDJPY's yen price as the martingale) and the trader (whole lots and contracts, the breach barrier, holding times, filler trades, exit times, the 10-minute gap, news blocks, the generator's error bounds)"),
             ("acct_mc.py", "the rule engine: phases, funded accounts, payout states (pending, cancelled, locked, protected), daily-loss bases, the terminal rule, cost-aware sizing, concentration, minimum target distance, margin, payout clocks, gates and minimums, duration rules, working days"),
             ("news_v10.py", "the release calendar and the blocked bars of every market"),
             ("firms_v3.py &hellip; firms_v9.py, firms_v10.py", "every firm's rules; firms_v10 holds the version 10 inputs and the plan's policies"),
             ("rules_inventory_v10.py &rarr; rules_inventory_v10.json", "every rule with its page, date, basis and model treatment (Appendix [[APP_INV]])"),
             ("optimize_v10.py", "grid (paths 1101&ndash;1104), refine (1111&ndash;1114), futures, final (1121&ndash;1136) &rarr; opt_v10_*.json(l)"),
             ("continuing_v10.py &rarr; continuing_v10.json, continuing_v10_price.json", "every final setting as a continuing slot (paths 1151&ndash;1166): Part II's rates; the chosen settings at half and twice today's prices"),
             ("cont_check_v10.py &rarr; cont_check_v10.json", "every chosen setting as random starts on the continuing paths with both direction rules: the measurement and the direction rule separated"),
             ("analytic_v10.py", "the exact chain with the terminal rule, the minimum target distance and payout caps, written separately from the engine"),
             ("tests_v10.py, tests_v10b.py &rarr; tests_v10.json", "direct tests of the engine's rule mechanisms, one per correction of version 10"),
             ("streams_v10.py &rarr; stream_manifest_v10.json", "every random stream of every stage; fails if two independent stages share one"),
             ("verify_v10.py, sens_v10.py", "checks against theory, sub-step convergence, scaling, Maven's stopping set; cost, risk, concentration, flat, daily-loss base, direction, filler, holding-time, news, processing, lock and The5ers-cap sensitivities"),
             ("lockstep.py, lockstep_portfolio_v10.py", "one person's accounts on one calendar; portfolios, 36-month lives, budgets, stress, correlation, refusals inside the event engine, behaviour, the joint error bound"),
             ("progs_v10.py, review_v10.py", "the programme sheets (leverage, plan notes, sources); the review response and the self-audit"),
             ("build_math_v10.py, doc10_*.py, math_v10_*.html", "this document: every number is read from the files above"),
             ("rerun_v10.sh, environment_v10.json", "the whole pipeline, in order; the software versions used"),
             ("audit_v10.py &rarr; audit_v10.json", "the end-of-run audit: stalls, coverage, a trade-by-trade replay of every chosen setting against the rules it lists, the chain's identity, the tests, the budget lives' dated cash, the document's numbers")]
    code = table(["File", "What it does"], [[f"<span class='k'>{a}</span>", b] for a, b in files], num_from=9, w0="34%")
    det = AUDIT.get("determinism", {})
    repro = ("<p>The repository: <span class='k'>github.com/astrafala/Monthly-EV-Maxxing</span>. To reproduce: <span class='k'>sh rerun_v10.sh</span> (every stage, the grid included), then <span class='k'>python3 build_math_v10.py</span>. "
             "Synthetic paths are rebuilt exactly from their stream keys and sigma_v32.json; no market data is needed. Every key and seed is fixed in the code; "
             + (f"rerunning {det.get('what', 'a stage')} with the versions in environment_v10.json reproduced its output exactly ({det.get('detail', '')}). " if det.get("ok") else "the versions used are in environment_v10.json. ")
             + "Version 10 uses no real-history run: one two-year history is one sample, and its attempts are not independent validations.</p>")
    src_rows = []
    for firm in FIRMS:
        urls = []
        for r in INV.get("rules", []):
            if r["firm"] == firm and r["source"].startswith("http"):
                u = r["source"].replace("https://", "")
                if u not in urls: urls.append(u)
        src_rows.append([firm, "; ".join(f"<span class='k'>{u}</span>" for u in urls)])
    src = table(["Firm", "Pages read (the inventory, Appendix [[APP_INV]], gives the page and date of every rule)"], src_rows, cls="small", num_from=9, w0="18%")
    return (review_appendix(subs) + audit_appendix(subs) + inventory_appendix() + formula_sheet() + glossary()
            + f'<section class="chapter"><span class="eyebrow">Appendix E</span><h1>How every number was computed</h1>{code}{repro}</section>'
            f'<section class="chapter"><span class="eyebrow">Appendix F</span><h1>Sources</h1>{src}'
            '<p class="note">Reliability evidence for the tiers: TrustPilot company pages (the tier-D firms' ratings shown as 'unavailable due to a breach of our guidelines', fake reviews removed; the others rated, from 3.7 to 4.8) and PropFirmMap safety grades (tier A: A or A+; tier B: B+; tier D: D), read on 4 October 2026 and again on 12 October 2026, every firm unchanged. Rules change; keep dated copies of the pages that apply to each purchase.</p></section>')
