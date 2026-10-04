"""Part III (one person, many accounts), Part IV (running it; what could go wrong) and the appendices."""
import math, collections
import numpy as np
from doc6_common import *
from doc6_part1 import short, sett, _calc, PLAN_PROGS
from doc6_part2 import ALLOC, SPECS, acct_row, alloc_value

R = LOCK["R"]; SLOTS = LOCK["slots"]
PNAMES = list(SLOTS.keys())
REC = "Recommended: A + B + one account at each tier-D firm"
PLABEL = {"Tier A": "Tier A only", "Tier A + B": "Tiers A and B", REC: "Recommended (A + B + one account per tier-D firm)",
          "Recommended, FTMO as 2 x 200K": "Recommended, FTMO as 2 &times; 200K", "All firms at full caps": "All firms at full allowance",
          "All firms at full caps + The5ers small accounts": "Full allowance + The5ers small accounts",
          "Recommended + futures (Topstep 5, Apex 20)": "Recommended + futures (Topstep 5, Apex 20)"}
FIRM_ORDER = ["FTMO", "FundingPips", "The5ers", "FXIFY", "FundedNext", "Fintokei", "Hola Prime", "Alpha Capital", "FunderPro", "GFT", "BrightFunded", "Blue Guardian", "Maven", "Topstep", "Apex"]

def lives(p): return [r for r in R if r["p"] == p]
def pstats(p):
    rs = lives(p); M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1)
    ev = M.mean(); ci = 1.96 * M.mean(1).std() / math.sqrt(len(rs))
    tier_ = np.mean([np.mean(r["refusal"]["tiered"]) for r in rs]); harsh = np.mean([np.mean(r["refusal"]["harsh"]) for r in rs])
    tr = np.array([r["trough"] for r in rs])
    return dict(n=len(rs), acc=len(SLOTS[p]), firms=len({firm_of(s["firm"]) for s in SLOTS[p]}), ev=ev, ci=ci, ss=M[:, 1:].mean(), tiered=tier_, harsh=harsh,
                p05=np.percentile(C[:, 11], 5), p50=np.percentile(C[:, 11], 50), p95=np.percentile(C[:, 11], 95), ahead3=np.mean(C[:, 2] > 0), ahead1=np.mean(C[:, 0] > 0),
                tr50=np.percentile(tr, 50), tr05=np.percentile(tr, 5), M=M, C=C, conflicts=sum(r["conflicts"] for r in rs),
                orders=np.mean([r["orders_per_trading_day"] for r in rs]))

def per_firm(p):
    rs = lives(p); out = collections.defaultdict(lambda: dict(pay=0.0, fee=0.0, req=0.0, buys=0.0))
    for r in rs:
        for f, v in r["payouts"].items(): out[f]["pay"] += v
        for f, v in r["fees"].items(): out[f]["fee"] += v
        for f, v in r["requests"].items(): out[f]["req"] += v
        for f, v in r["buys"].items(): out[f]["buys"] += v
    n = len(rs) * 12
    return {f: {k: v / n for k, v in d.items()} for f, d in out.items()}

# ------------------------------------------------------------------ chapter 27: allocation
def alloc_table():
    rows = []; tr = tf = 0
    for f in FIRM_ORDER:
        a = ALLOC[f]; rv, rn = alloc_value(a["rec"]); fv, fn_ = alloc_value(a["full"])
        if f not in ("Topstep", "Apex"): tr += rv; tf += fv
        rec = ", ".join(f"{n}&times;{kk(s)}" for p, i, s, n in a["rec"]) or "&ndash;"
        full = ", ".join(f"{n}&times;{kk(s)}" for p, i, s, n in a["full"])
        mk = MSHORT[a["full"][0][1]]
        rows.append([f"{f} <span class='tier{F5.TIER.get(f, 'B')}'>({F5.TIER.get(f, '?')})</span>", a["cap"], a["copy"], mk, rec, usd(rv) if rn else "&ndash;", full, usd(fv)])
    rows.append(["<strong>Total, CFD firms</strong>", "", "", "", "", f"<strong>{usd(tr)}</strong>", "", f"<strong>{usd(tf)}</strong>"])
    return table(["Firm (tier)", "Per-person limit", "Copying between accounts", "Market", "Recommended", "EV/month", "Full allowance", "EV/month"], rows, cls="small", num_from=5, hl=(len(rows) - 1,),
                 cap="EV per month: the sum of each account's value from its programme chapter (renewal&ndash;reward, fresh paths). The portfolio simulation of Chapter [[CH_LOCK]] gives the same totals within its noise. "
                     "Futures (Topstep, Apex) are an optional layer and are not in either total.")

def size_table():
    rows = []
    for prog, instr in [("FTMO 2-Step", "US100"), ("FundedNext Stellar 2-Step v5", "EURUSD"), ("Fintokei ProTrader", "US100"), ("Alpha Capital Pro 10%", "US100"),
                        ("FunderPro Classic v5", "US100"), ("GFT 2-Step Standard v5", "US100"), ("BrightFunded 2-Step Classic v5", "US100"), ("Blue Guardian 2-Step v5", "US100")]:
        a = fin(prog, instr); b = fin(prog, instr, "200K", size=200_000)
        if not (a and b): continue
        fa = rules(prog, 100_000, fee=a.get("fee"))["fee"]; fb = rules(prog, 200_000, fee=b.get("fee"))["fee"]
        d = b["EV_month"] - 2 * a["EV_month"]
        ci = math.sqrt(a["CI"] ** 2 * 4 + b["CI"] ** 2) / 2      # the two runs share paths and random numbers: this overstates the noise of d
        better = "equal" if abs(fb - 2 * fa) <= 0.01 * fb else ("200K" if fb < 2 * fa else "100K")
        rows.append([short(prog), usd(fa, 2 if fa % 1 else 0), usd(fb, 2 if fb % 1 else 0), usd(fb - 2 * fa, 2 if (fb - 2 * fa) % 1 else 0).replace("$", "$"), usd(2 * a["EV_month"]), usd(b["EV_month"]), sgn(d), better])
    return table(["Programme", "100K fee", "200K fee", "200K &minus; 2 &times; 100K fee", "2 &times; 100K: EV/month", "1 &times; 200K: EV/month", "Difference", "Cheaper per dollar"], rows, cls="small",
                 cap="Same setting scaled, same paths and random numbers (so the difference is mostly the fee and the rules that do not scale, such as GFT's $10,000 payout cap, which is 5% of a 200K account but 6% would be allowed on 100K).")

def size_text():
    a = pstats(REC); b = pstats("Recommended, FTMO as 2 x 200K")
    pf = per_firm(REC); pf2 = per_firm("Recommended, FTMO as 2 x 200K")
    gf = fin("GFT 2-Step Standard v5", "US100"); gf2 = fin("GFT 2-Step Standard v5", "US100", "200K", size=200_000)
    return (f"<p><strong>The answer, firm by firm.</strong> Where the 200K fee is exactly twice the 100K fee (FTMO, Alpha Capital), the two choices are worth the same. Where the 200K fee is lower per dollar (FundedNext, FunderPro, GFT), 200K is worth more, by about the saving times the number of attempts a month. Where it is higher (Fintokei: $1,249 against 2 &times; $549), 100K is worth more. "
            f"Rules can override the fee: GFT's first two payouts are capped at $10,000, which binds a 200K account's 6% cycle ($12,000), so 2 &times; 100K would be worth {usd(2 * gf['EV_month'])} against {usd(gf2['EV_month'])}; but GFT forbids duplicated trades between its accounts, so only one account can be used, and the larger one is worth more.</p>"
            f"<p><strong>Where only one account is allowed</strong> (FunderPro, GFT, FundedNext on its own market), the largest size the cap allows is used, because one 200K account is worth about twice one 100K account.</p>"
            f"<p><strong>FTMO, 4 &times; 100K or 2 &times; 200K.</strong> Same fee per dollar, same value: the whole recommended portfolio is worth {usd(a['ev'])} &plusmn; {usd(a['ci'])} a month with four 100K accounts and {usd(b['ev'])} &plusmn; {usd(b['ci'])} with two 200K accounts. "
            f"The differences are second-order. Two accounts make half as many payout requests ({pf['FTMO']['req']:.2f} against {pf2['FTMO']['req']:.2f} a month), so if payouts can be refused, two 200K accounts lose the firm a little less often (Chapter [[CH_REF]]: {usd(b['tiered'])} against {usd(a['tiered'])} in the tiered scenario, within the noise). "
            f"Four accounts give a smoother cash path. The plan uses four 100K accounts for the headline figure; two 200K accounts are an equally good choice with half the orders.</p>")

# ------------------------------------------------------------------ chapter 28: portfolios
def portf_table():
    rows = []
    for p in PNAMES:
        s = pstats(p)
        rows.append([PLABEL[p], str(s["acc"]), str(s["firms"]), pm(s["ev"], s["ci"]), usd(s["ss"]), usd(s["p05"]), usd(s["p50"]), usd(s["p95"]), usd(s["tr50"]), usd(s["tr05"])])
    return table(["Portfolio", "Accounts", "Firms", "EV/month, first year (95%)", "Months 2&ndash;12", "First-year cash p5", "median", "p95", "Lowest cumulative cash: median", "p5"],
                 rows, cls="small", hl=(PNAMES.index(REC),),
                 cap="400 simulated first years per portfolio (lockstep_portfolio_v6.py). EV/month: total cash over the year &divide; 12, including the first month's fees before any payout. "
                     "Lowest cumulative cash: the deepest point of the running total of fees paid minus cash received, i.e. the money that must be available to pay fees before the payouts arrive.")

def portf_text():
    a = pstats(REC); s = sum(alloc_value(ALLOC[f]["rec"])[0] for f in FIRM_ORDER)
    pf = per_firm(REC)
    full = pstats("All firms at full caps"); fut = pstats("Recommended + futures (Topstep 5, Apex 20)"); t5 = pstats("All firms at full caps + The5ers small accounts")
    return (f"<p><strong>The portfolio adds up.</strong> The recommended portfolio's simulated first year averages {usd(a['ev'])} a month; the sum of its accounts' renewal&ndash;reward values from Part II is {usd(s)}. Linearity (2.1) says these must agree, and they do within the simulation's interval (&plusmn;{usd(a['ci'])}). "
            f"From the second month on, when the first payouts arrive, the average is {usd(a['ss'])} a month. {('Every one of the ' + str(a['n']) + ' simulated first years ended ahead (the lowest at ' + usd(a['C'][:, 11].min()) + ')') if a['C'][:, 11].min() > 0 else (pct(np.mean(a['C'][:, 11] > 0), 1) + ' of simulated first years ended ahead; the lowest ended at ' + usd(a['C'][:, 11].min()))}; the 5th percentile of the first year's cash is {usd(a['p05'])}.</p>"
            f"<p><strong>No account ever opposed another.</strong> In {sum(len(lives(p)) for p in PNAMES):,} simulated years the engine recorded {sum(pstats(p)['conflicts'] for p in PNAMES)} moments when two accounts held opposite positions on the same market. A person running the recommended plan places about {a['orders']:.0f} orders a day across all accounts.</p>"
            f"<p><strong>More accounts.</strong> The full allowance (35 accounts) adds {usd(full['ev'] - a['ev'])} a month, all of it at tier-D firms. The futures layer adds {usd(fut['ev'] - a['ev'])}, and The5ers' ten small accounts change nothing measurable ({usd(t5['ev'] - full['ev'])}, inside the noise of &plusmn;{usd(t5['ci'])}). "
            f"Whether the extra tier-D accounts are worth it depends on how far their payouts can be trusted, which is the subject of Chapter [[CH_REF]].</p>")

def month_fig():
    s = pstats(REC); C = s["C"] / 1e6
    med = np.percentile(C, 50, axis=0); lo = np.percentile(C, 5, axis=0); hi = np.percentile(C, 95, axis=0); mean = C.mean(0)
    W, H, l0, r0, t0, b0 = 640, 250, 56, 90, 22, 34
    xs = np.arange(0, 13); ymax = math.ceil(hi.max() * 2) / 2 + 0.25; ymin = min(0, lo.min()) - 0.1
    X = lambda i: l0 + i / 12 * (W - l0 - r0); Y = lambda v: t0 + (ymax - v) / (ymax - ymin) * (H - t0 - b0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    yv = 0.0
    while yv <= ymax + 1e-9:
        g.append(f'<line x1="{l0}" x2="{W - r0}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RULE}" stroke-width="{1 if yv == 0 else 0.5}"/>')
        g.append(t(l0 - 6, Y(yv) + 3, f"${yv:.1f}M", 8, "end", MUT, True)); yv += 0.5
    for i in range(0, 13, 1): g.append(t(X(i), H - b0 + 14, str(i), 8, "middle", MUT, True))
    pts_hi = [(X(i + 1), Y(hi[i])) for i in range(12)]; pts_lo = [(X(i + 1), Y(lo[i])) for i in range(12)]
    band = [(X(0), Y(0))] + pts_hi + pts_lo[::-1] + [(X(0), Y(0))]
    g.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in band) + f'" fill="{S1}" fill-opacity="0.14" stroke="none"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(med[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S1}" stroke-width="2"/>')
    g.append('<polyline points="' + f"{X(0):.1f},{Y(0):.1f} " + " ".join(f"{X(i + 1):.1f},{Y(mean[i]):.1f}" for i in range(12)) + f'" fill="none" stroke="{S2}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    g.append(t(X(12) + 6, Y(hi[11]) + 3, f"95th pct ${hi[11]:.2f}M", 8, "start", MUT))
    g.append(t(X(12) + 6, Y(med[11]) + 3, f"median ${med[11]:.2f}M", 8, "start", INK))
    g.append(t(X(12) + 6, Y(mean[11]) + 14, f"mean ${mean[11]:.2f}M", 8, "start", S2))
    g.append(t(X(12) + 6, Y(lo[11]) + 3, f"5th pct ${lo[11]:.2f}M", 8, "start", MUT))
    g.append(t((l0 + W - r0) / 2, H - 4, "months since starting", 8.5, "middle", MUT))
    g.append(t(l0, 12, "Cumulative cash of the recommended plan: median (solid), mean (dashed), 5th to 95th percentile (band)", 8.5, "start", INK))
    g.append("</svg>")
    return fig("".join(g), f"400 simulated first years of the recommended plan (28 accounts at 13 firms). Cash = payouts received minus fees paid. The table below gives the same numbers month by month.")

def month_table():
    s = pstats(REC); M = s["M"]; C = s["C"]
    rows = []
    for i in range(12):
        rows.append([str(i + 1), usd(M[:, i].mean()), usd(np.percentile(M[:, i], 10)), usd(np.percentile(M[:, i], 50)), usd(np.percentile(M[:, i], 90)),
                     usd(C[:, i].mean()), pct(np.mean(C[:, i] > 0), 0)])
    return table(["Month", "Mean cash", "p10", "median", "p90", "Cumulative mean", "Ahead (cumulative &gt; 0)"], rows, cls="small", num_from=1)

# ------------------------------------------------------------------ chapter 29: refusals
def tier_table():
    rows = []
    for tr, desc in (("A", "PropFirmMap A/A+, TrustPilot profile active"), ("B", "PropFirmMap B+, TrustPilot active"), ("D", "TrustPilot rating withheld for fake reviews; PropFirmMap D")):
        firms = [f for f in FIRM_ORDER if F5.TIER.get(f) == tr]
        rows.append([tr, desc, ", ".join(firms), pct({"A": 0.02, "B": 0.05, "D": 0.15}[tr], 0), pct({"A": 0.05, "B": 0.10, "D": 0.30}[tr], 0)])
    return table(["Tier", "Evidence (4 October 2026)", "Firms", "Refusal chance per request: tiered", "harsh"], rows, cls="small", num_from=3)

def refusal_table():
    rows = []
    for p in PNAMES:
        s = pstats(p)
        rows.append([PLABEL[p], usd(s["ev"]), usd(s["tiered"]), pct(s["tiered"] / s["ev"], 0), usd(s["harsh"]), pct(s["harsh"] / s["ev"], 0)])
    return table(["Portfolio", "All payouts honoured", "Tiered", "kept", "Harsh", "kept"], rows, cls="small", hl=(PNAMES.index(REC),),
                 cap="First-year average per month. Each payout request is refused with its firm's probability; after a refusal the person stops using that firm. Ten random draws of refusals per simulated year.")

def refusal_text():
    pf = per_firm(REC); s = pstats(REC); full = pstats("All firms at full caps")
    rows = []
    for f in FIRM_ORDER:
        if f not in pf: continue
        d = pf[f]; tr = F5.TIER.get(f, "B"); rho = {"A": 0.02, "B": 0.05, "D": 0.15}[tr]
        life = 1 / (rho * d["req"]) if d["req"] > 0 else float("inf")
        rows.append([f, tr, f"{d['req']:.2f}", usd(d["pay"] / max(d["req"], 1e-9)), usd(d["pay"] + d["fee"]), f"{life:.0f}"])
    tb = table(["Firm", "Tier", "Payout requests a month", "Average request", "Net cash a month", "Expected months until a refusal (tiered)"], rows, cls="small", num_from=2,
               cap="Recommended plan, first-year averages from the portfolio simulation.")
    return (tb + f"<p>Bold play makes requests rare and large: the recommended plan's 28 accounts make about {sum(d['req'] for d in pf.values()):.1f} payout requests a month in all. "
            f"In the tiered scenario the plan keeps {pct(s['tiered'] / s['ev'], 0)} of its value over the first year; in the harsh scenario {pct(s['harsh'] / s['ev'], 0)}. "
            f"The full allowance, with three more tier-D accounts at BrightFunded and at Blue Guardian and a second Alpha account, is worth {usd(full['ev'] - s['ev'])} more if every payout is honoured, "
            f"but only {usd(full['tiered'] - s['tiered'])} more in the tiered scenario and {usd(full['harsh'] - s['harsh'])} in the harsh one: more requests at the doubtful firms mean losing them sooner. That is why the recommended plan holds one account at each tier-D firm.</p>")

def ref_example():
    pf = per_firm(REC)
    ft = pf["FTMO"]["req"]; fp_ = pf["FunderPro"]["req"]
    return (f"In the recommended plan the four FTMO accounts together make about {ft:.2f} requests a month: at \\(\\rho = 2\\%\\), FTMO is expected to last \\(1/(0.02 \\times {ft:.2f}) = {1 / (0.02 * ft):.0f}\\) months. "
            f"The single FunderPro 200K account makes {fp_:.2f} requests a month: at \\(\\rho = 15\\%\\), it is expected to last \\(1/(0.15\\times{fp_:.2f}) = {1 / (0.15 * fp_):.0f}\\) months.")

def part3_fills(ch_alloc, ch_lock, ch_ref):
    return dict(CH_ALLOC=ch_alloc, CH_LOCK=ch_lock, CH_REF=ch_ref, ALLOC_TABLE=alloc_table(), SIZE_TABLE=size_table(), SIZE_TEXT=size_text(),
                LIVES=f"{sum(len(lives(p)) for p in PNAMES):,}", PORTF_TABLE=portf_table(), PORTF_TEXT=portf_text(), MONTH_FIG=month_fig(), MONTH_TABLE=month_table(),
                TIER_TABLE=tier_table(), REFUSAL_TABLE=refusal_table(), REFUSAL_TEXT=refusal_text(), REF_EXAMPLE=ref_example())

# ------------------------------------------------------------------ Part IV
def settings_card():
    rows = []
    for f in FIRM_ORDER[:13]:
        for p, i, s, n in ALLOC[f]["rec"]:
            r = acct_row(p, i, s)
            T = trade_numbers(i, r["m"], r["L"], r["k"] * r["L"])
            unit = T["unit"]
            lots = f"{T['lots']:.2f} lots" if T.get("lots") else f"${T['usd_per_pt']:,.2f}/pt"
            rows.append([f"{short(p)}", f"{n} &times; {kk(s)}", MSHORT[i], usd(r["L"]), f"{r['m']:g} &sigma; = {T['stop_pts']:.1f} {unit}s", lots, str(r["k"]), usd(r["X"]), usd(r["EV_month"] * n)])
    return table(["Programme", "Accounts", "Market", "Risk per trade", "Stop", "Size", "k (target cap)", "Cycle target", "EV/month"], rows, cls="small tight", num_from=3,
                 cap="Stops in points (Nasdaq), pips (USDJPY, EURUSD) or dollars (gold) at the prices of 2 October 2026. They move with the market: recompute \\(m\\sigma \\times\\) price every week with the current price; \\(\\sigma\\) is re-measured monthly. "
                     "Size: lots for currency pairs (standard lot) and gold (100 oz); for index CFDs, dollars per index point, to be divided by the contract's dollars per point per lot. The take-profit is the smaller of \\(k\\) times the risk and the distance to the current target, plus the cost (4.1).")

def part4(ch_run, ch_risk):
    rec = pstats(REC)
    rb = {(r["prog"], r["m"], r["cost_mult"]): r for r in EXTRA["robust"]}
    cost_rows = []
    for f in FIRM_ORDER[:13]:
        for p, i, s, n in ALLOC[f]["rec"][:1]:
            ch = fin(p, i)
            rs = [x for x in EXTRA["robust"] if x["prog"] == p and x["instr"] == i and abs(x["m"] - ch["m"]) < 1e-9] or \
                 [x for x in SENS if x["tag"] == "cost" and x["prog"] == p and x["instr"] == i and abs(x["m"] - ch["m"]) < 1e-9]
            d = {x["cost_mult"]: x for x in rs}
            if 1.0 in d and 1.5 in d and 2.0 in d:
                F = rules(p, 100_000, fee=ch.get("fee"))
                ex = [AN.programme_exact(p, i, ch["m"], ch["k"], ch["X1"], ch["X"], L=ch["L"], F=F, cost_mult=cm)["EV"] for cm in (1.0, 1.5, 2.0)]
                cost_rows.append([short(p), MSHORT[i], usd(d[1.0]["EV_month"]), usd(d[1.5]["EV_month"]), usd(d[2.0]["EV_month"]),
                                  usd(ex[0]), pct(ex[1] / ex[0] - 1, 0), pct(ex[2] / ex[0] - 1, 0)])
    tot = [sum(acct_row(p, i, s)["EV_month"] * n for f in FIRM_ORDER[:13] for p, i, s, n in ALLOC[f]["rec"])]
    def scaled(cm):
        out = 0.0
        for f in FIRM_ORDER[:13]:
            for p, i, s, n in ALLOC[f]["rec"]:
                ch = fin(p, i)
                rs = [x for x in EXTRA["robust"] if x["prog"] == p and x["instr"] == i and abs(x["m"] - ch["m"]) < 1e-9] or \
                     [x for x in SENS if x["tag"] == "cost" and x["prog"] == p and x["instr"] == i and abs(x["m"] - ch["m"]) < 1e-9]
                d = {x["cost_mult"]: x for x in rs}
                ratio = d[cm]["EV_month"] / max(d[1.0]["EV_month"], 1) if (cm in d and 1.0 in d) else 1.0
                out += acct_row(p, i, s)["EV_month"] * n * ratio
        return out
    c15, c20 = scaled(1.5), scaled(2.0)
    st = {}
    for f in FIRM_ORDER[:13]:
        for p, i, s_, n in ALLOC[f]["rec"]:
            r = acct_row(p, i, s_); T = trade_numbers(i, r["m"], r["L"], r["L"])
            st.setdefault(i, []).append((r["m"], T["stop_pts"], T["unit"]))
    ms = [m for v in st.values() for m, _, _ in v]
    stop_range = (f"{min(ms):g}&ndash;{max(ms):g} hourly standard deviations: " +
                  "; ".join(f"{MSHORT[i]} {min(x[1] for x in v):.1f}&ndash;{max(x[1] for x in v):.1f} {v[0][2]}s" if len({x[1] for x in v}) > 1 else f"{MSHORT[i]} {v[0][1]:.1f} {v[0][2]}s" for i, v in st.items()))
    s1 = f"""
<section class="part"><span class="num">Part IV</span><h1>Running it</h1><p>The settings of every account in one place, the routine that runs them, and everything that could make the numbers wrong.</p></section>
<section class="chapter"><span class="eyebrow">Chapter {ch_run}</span><h1>The routine</h1>
<h2>{ch_run}.1 Every account's settings</h2>
{settings_card()}
<h2>{ch_run}.2 Placing a trade, step by step</h2>
<ol>
<li><strong>Is a trade allowed now?</strong> Entry hours (Nasdaq 01:00&ndash;20:00 UTC, USDJPY 00:00&ndash;20:00, EURUSD 07:00&ndash;20:00, gold 01:00&ndash;20:00), weekdays only, nothing new after 19:00 UTC on Friday, nothing from 15 minutes before to 5 minutes after a high-impact US release, and at least 10 minutes since this account's last losing trade in the same direction (FundingPips' trade-idea rule, applied everywhere).</li>
<li><strong>Direction.</strong> If any of your accounts holds this market, the same direction. Otherwise the plan's rule: long if the last completed hourly close is above the close five hours earlier, short if below. The rule has no edge (Chapter 11); its only job is that no two of your accounts are ever opposite.</li>
<li><strong>Risk.</strong> \\(l\\) = the smallest of 1.5% of the account, the room above the maximum-loss floor less 0.1% of the account, and the room left in today's daily loss less 0.2%. If that is under 0.15% of the account, stop for the day.</li>
<li><strong>Stop.</strong> \\(m\\sigma\\) times the current price, from the settings card; the size is \\(l\\) divided by the stop in points times the dollars per point per lot, rounded <em>down</em>.</li>
<li><strong>Take-profit.</strong> The win \\(w\\) is the smallest of \\(k\\,l\\), the distance to the phase target or the cycle target, and any cap the firm sets (best day, daily profit, FundingPips' 55% of the phase target). The take-profit distance is the stop distance times \\((w + c)/l\\), with \\(c\\) the measured round-trip cost of this size.</li>
<li><strong>Place it as one bracket order</strong>: entry, stop and take-profit together. Never move either.</li>
<li><strong>Log it</strong>: time, account, market, direction, size, stop, target, and the fill. The log is the evidence for any review.</li>
</ol>
<h2>{ch_run}.3 Phases, payouts and refills</h2>
<ul>
<li>When a phase target is reached: stop. If the firm requires more trading days, place one minimal trade (the smallest lot) on each remaining day where it counts <em>trading</em> days; where it counts <em>profitable</em> days the daily target of 6.4 has already met it.</li>
<li>When a funded account reaches its cycle target: stop trading it, request the payout on the first allowed day, withdraw everything above the starting balance, and start the next cycle at the start balance.</li>
<li>When an account fails (phase or funded): buy the next evaluation of the same programme the same day. A slot is never left empty: the renewal&ndash;reward value assumes it.</li>
<li>Never let an account lapse for inactivity, never abandon a funded account, never trade an account to lose it. Account rolling is prohibited at most firms, and the plan's value does not need it.</li>
</ul>
<h2>{ch_run}.4 Cash needed</h2>
<p>Fees are paid before payouts arrive. In the simulation the running total of the recommended plan (fees out, payouts in) falls to {usd(rec['tr50'])} at its lowest in a typical first year, and to {usd(rec['tr05'])} in the worst 5%. Starting with that much available (or starting fewer slots and adding them as payouts arrive) keeps every slot filled. The first month alone costs about {usd(-rec['M'][:, 0].mean())} net.</p>
<h2>{ch_run}.5 Workload</h2>
<p>About {rec['orders']:.0f} bracket orders a day across 28 accounts, each set and left, plus payout requests and evaluation purchases. The order times follow the market, so the routine is best run from a written checklist with alarms at the entry hours.</p>
</section>
<section class="chapter"><span class="eyebrow">Chapter {ch_risk}</span><h1>What could make the numbers wrong</h1>
<h2>{ch_risk}.1 Higher trading costs</h2>
<p>The single most important assumption is the cost \\(\\kappa\\) of a round trip. Every programme was rerun with all costs (spreads, commissions, slippage and financing) multiplied by 1.5 and by 2:</p>
{table(["Programme", "Market", "Engine EV/month: cost &times; 1", "&times; 1.5", "&times; 2", "Chain: value of an attempt", "&times; 1.5", "&times; 2"], cost_rows, cls="small", num_from=2, cap="One 100K account. Engine: 12,000 attempts per cell on fresh paths with the same random numbers in each row, so the columns are paired; even so each cell is uncertain by &plusmn;$150&ndash;$650 (8.4), and a row can rise by chance. Chain: the exact equations of 5.6 with the cost scaled, noise-free but without financing or time effects; it shows the size of the cost effect on the value of one attempt.")}
<p>Scaled to the recommended plan, the value per month is about {usd(tot[0])} at the assumed costs, {usd(c15)} at 1.5 times and {usd(c20)} at twice. The Nasdaq and gold accounts hold up best (their \\(\\kappa/\\sigma\\) is lowest); the currency accounts lose more. <strong>Measure your real costs in the first week</strong> (the fill against the quoted price, spread and commission, per account) and redo the settings card if they differ from the table of 3.1 by more than a quarter.</p>
<h2>{ch_risk}.2 Payouts refused, accounts closed</h2>
<p>Chapter [[CH_REF]] puts numbers on it: {usd(rec['tiered'])} a month if payouts are refused at 2/5/15% per request by tier, {usd(rec['harsh'])} at 5/10/30%. The plan's defence is to follow every written rule exactly and keep the evidence (the trade log), not to disguise anything. Firms most often cite "gambling", "one-sided betting", copy trading from others and hedging across accounts. The plan risks 1.5% with a stop on every trade, trades both directions, copies nobody, and never holds opposite positions. But bold play does produce large single-trade wins, and a firm may still review them. That is a real risk that no model can price.</p>
<h2>{ch_risk}.3 Spread widening and tight stops</h2>
<p>The stops are {stop_range}. Spreads on CFDs widen several-fold at the daily break (about 21:00&ndash;22:00 UTC), at the weekly open and around news. A stop within a widened spread of the price can be filled without the mid price touching it. The engine's cost is an average and does not model this; it is the reason for the plan's 0.35 limit. If positions held through the daily break are stopped noticeably more often than the model's win rates (4.2) imply, close them before the break. A forced close is a fair stopping time, so it costs only the extra round trip.</p>
<h2>{ch_risk}.4 Rules change</h2>
<p>Every rule in Part II was read on 4 October 2026, and prop firms change them often: leverage, consistency rules, payout schedules, prices and per-person limits most of all. Recheck each firm's rules page before buying, and rerun the programme's optimisation (optimize_v6.py) when a rule that enters the model changes.</p>
<h2>{ch_risk}.5 The model itself</h2>
<ul>
<li><strong>Zero skill is an assumption in your favour only if it is true.</strong> If entries are systematically late, fills systematically worse, or the price moves against new positions (adverse selection), the edge is negative and the cost check of {ch_risk}.1 is the guide: twice the cost is an extra cost of \\(c/l = \\kappa/(m\\sigma)\\) per trade: {pct(kappa('US100') / (0.5 * SIG['US100']), 1)} of the risk on the Nasdaq at \\(m = 0.5\\), {pct(kappa('US100') / (0.35 * SIG['US100']), 1)} at 0.35.</li>
<li><strong>Volatility changes.</strong> \\(\\sigma\\) moves over time; stops are set in units of the current \\(\\sigma\\), so the plan adapts, and the calibration is the 2024&ndash;26 average.</li>
<li><strong>Gaps and limits.</strong> The engine fills gaps at the open and fails accounts whose daily or maximum loss a gap breaks, as the firms do.</li>
<li><strong>Independence of firms.</strong> Values add (linearity), but in a bad week every Nasdaq account loses together; the month table of Chapter [[CH_LOCK]] shows the spread.</li>
<li><strong>Taxes and payment costs</strong> are not modelled.</li>
</ul>
<h2>{ch_risk}.6 What is not allowed, and is not in the plan</h2>
<p>No hedging across accounts or firms; no accounts in anyone else's name; no copy-trading services or other people's signals; no trading of news windows the firm restricts; no tick scalping, latency or gap arbitrage; no grid or martingale sizing; no abandoned or deliberately failed accounts. Do not share or sell the plan: several firms treat traders who run the same marketed strategy as a group, and close them together.</p>
</section>"""
    return s1

def appendices():
    sheet = """
<section class="chapter"><span class="eyebrow">Appendix A</span><h1>Formula sheet</h1>
<table><thead><tr><th style="width:38%">Quantity</th><th>Formula</th><th>Where</th></tr></thead><tbody>
<tr><td>Value of one attempt</td><td>\\(\\mathbb{E}[V] = \\Pr(\\text{pass})\\,\\mathbb{E}[C] - F\\)</td><td>1.2</td></tr>
<tr><td>Notional, target distance</td><td>\\(N = l/(m\\sigma)\\), \\(u = m\\sigma\\,(w + c)/l\\)</td><td>4.1</td></tr>
<tr><td>Win probability of a bracket</td><td>\\(p = l/(l + w + c)\\)</td><td>4.2</td></tr>
<tr><td>Mean and variance of a trade</td><td>\\(-c\\) and \\(l(w + c)\\)</td><td>4.3</td></tr>
<tr><td>Cost per unit of risk</td><td>\\(c/l = \\kappa/(m\\sigma)\\); financing per night \\(\\varphi/(m\\sigma)\\)</td><td>4.4</td></tr>
<tr><td>Pass probability, no cost</td><td>\\(B/(A + B)\\)</td><td>5.1</td></tr>
<tr><td>Pass probability, Brownian with cost</td><td>\\((e^{\\theta B} - 1)/(e^{\\theta(A+B)} - 1)\\), \\(\\theta = 2c/v\\)</td><td>5.2</td></tr>
<tr><td>Expected trades, Brownian</td><td>\\(((1-P)B - PA)/c\\) &rarr; \\(AB/v\\)</td><td>5.3</td></tr>
<tr><td>Exact chain</td><td>\\(V(x) = p\\,V(x + w) + (1-p)\\,V(x - l - c)\\)</td><td>5.6</td></tr>
<tr><td>Pass probability, exact, any k</td><td>\\(P = (B - \\mathbb{E}[\\text{total cost}])/(A + B)\\)</td><td>5.6</td></tr>
<tr><td>Bold play</td><td>\\(P = 1 - \\prod_j (1 - p_j)\\), \\(p_j = l/(l + A - x_j + c)\\), \\(x_j = -j(l + c)\\)</td><td>5.6</td></tr>
<tr><td>Two phases</td><td>\\(P = P_1 P_2\\)</td><td>6.1</td></tr>
<tr><td>Withdrawal identity</td><td>\\(\\mathbb{E}[W] = D - \\mathbb{E}[\\text{cost of funded trades}]\\)</td><td>7.1</td></tr>
<tr><td>Funded cash, cycle form</td><td>\\(\\alpha\\,(X_1 q_1 + X q_1 q/(1 - q)) + R\\,q_1 q^{r-1}\\)</td><td>7.2</td></tr>
<tr><td>Trade duration (hours of open market)</td><td>\\(m^2 (w + c)/l\\); winners \\(m^2(b^2 + 2b)/3\\), losers \\(m^2(1 + 2b)/3\\), \\(b = (w+c)/l\\)</td><td>8.1</td></tr>
<tr><td>Phase market time, zero cost</td><td>\\((A/l)(B/l)\\,m^2\\) hours</td><td>8.2</td></tr>
<tr><td>Value per month</td><td>\\(30.44\\,\\mathbb{E}[V]/\\mathbb{E}[T_\\text{days}]\\)</td><td>8.3</td></tr>
<tr><td>Standard error of a ratio estimate</td><td>\\(\\operatorname{sd}(V_i - \\hat r T_i)/(\\sqrt n\\,\\bar T)\\)</td><td>8.4</td></tr>
<tr><td>Smallest stop the leverage allows</td><td>\\(m_{\\min} = (l/S)/(0.6\\lambda\\sigma)\\)</td><td>10.2</td></tr>
<tr><td>Scaling an account</td><td>\\(\\mathbb{E}[V](\\lambda S) = \\lambda\\Pr(\\text{pass})\\mathbb{E}[C](S) - F(\\lambda S)\\)</td><td>[[CH_ALLOC]].2</td></tr>
<tr><td>Refusals</td><td>\\(\\mathbb{E}[\\text{paid requests}] = (1-\\rho)/\\rho\\); firm life \\(1/(\\rho r)\\)</td><td>[[CH_REF]].1</td></tr>
</tbody></table></section>
<section class="chapter"><span class="eyebrow">Appendix B</span><h1>Glossary</h1>
<table><tbody>
<tr><td style="width:24%"><strong>Allowance \\(D\\)</strong></td><td>The funded account's maximum loss: the floor sits \\(D\\) below the starting balance.</td></tr>
<tr><td><strong>Attempt</strong></td><td>One evaluation bought, from purchase until a phase fails or the funded account that followed it is lost.</td></tr>
<tr><td><strong>Bold play</strong></td><td>Staking enough on each bet to reach the goal in one win; optimal in fair and unfavourable games (Dubins and Savage).</td></tr>
<tr><td><strong>Bracket</strong></td><td>A position with its stop-loss and take-profit attached at entry and never moved.</td></tr>
<tr><td><strong>Cycle target \\(X\\)</strong></td><td>The profit at which the funded account stops and requests a payout.</td></tr>
<tr><td><strong>Engine</strong></td><td>The rule-by-rule simulation of an account on hourly price paths (acct_mc.py, pathfirm.py, lockstep.py).</td></tr>
<tr><td><strong>Exact chain</strong></td><td>The trade-level Markov chain of 5.6, solved by iteration (analytic_v6.py).</td></tr>
<tr><td><strong>\\(k\\)</strong></td><td>Reward-to-risk: a full win nets \\(k\\) times the risk after costs.</td></tr>
<tr><td><strong>\\(m\\)</strong></td><td>The stop distance in hourly standard deviations of the market.</td></tr>
<tr><td><strong>Renewal&ndash;reward</strong></td><td>The long-run value per unit time of a repeated process: \\(\\mathbb{E}[V]/\\mathbb{E}[T]\\).</td></tr>
<tr><td><strong>Slot</strong></td><td>One account position at one firm, refilled with a new evaluation whenever an attempt ends.</td></tr>
<tr><td><strong>Tier</strong></td><td>A firm's reliability class (A, B, D) from public evidence, used for the refusal scenarios.</td></tr>
<tr><td><strong>Winner's curse</strong></td><td>The upward bias of the best of many noisy estimates; removed here by reporting every figure from paths not used to choose it.</td></tr>
</tbody></table></section>"""
    files = [("fetch_data.py", "downloads two years of hourly bars from Yahoo Finance (not redistributed)"),
             ("calibrate.py, sigma_v32.json", "costs, financing and trading hours per market; hourly volatilities"),
             ("multi.py, pathfirm.py", "synthetic price paths (12 years, Brownian-bridge extremes) and the bracket trader on a path"),
             ("acct_mc.py, firms_v3.py, firms_v5.py", "the rule engine (phases, funded accounts, payouts) and every firm's rules"),
             ("optimize_v6.py", "grid, refine, edges, bold play, final, robust stages (opt_v6_*.jsonl / .json)"),
             ("analytic_v6.py", "the Brownian formulas and the exact chain, written independently of the engine"),
             ("verify_v6.py, extra_v6.py, sens_v6.py", "checks against theory; zero-cost checks; cost, risk, k, direction and financing sensitivities"),
             ("lockstep.py, lockstep_portfolio_v6.py", "one person's accounts on one shared path and calendar; refusal scenarios (lockstep_v6.json)"),
             ("progs_v6.py", "the firms' written rules and sources, as quoted in Part II"),
             ("build_math_v6.py, doc6_*.py", "this document: every number is read from the files above")]
    code = table(["File", "What it does"], [[f"<span class='k'>{a}</span>", b] for a, b in files], num_from=9, w0="34%")
    repro = """<p>To reproduce: <span class="k">python3 fetch_data.py</span> (real-history checks only); <span class="k">python3 optimize_v6.py grid</span>, then <span class="k">refine</span>, <span class="k">extra</span>, <span class="k">edge</span>, <span class="k">futures</span>, <span class="k">futures_refine</span>, <span class="k">bold</span>, <span class="k">final6</span>, <span class="k">robust</span>; <span class="k">python3 sens_v6.py</span>; <span class="k">python3 extra_v6.py</span>; <span class="k">python3 verify_v6.py</span>; <span class="k">python3 lockstep_portfolio_v6.py --lives=50</span>; <span class="k">python3 build_math_v6.py</span>. Synthetic paths are rebuilt exactly from their seeds and sigma_v32.json; no price data is needed for them.</p>"""
    src_rows = [[SHEET[sp["sheet"]]["title"], SHEET[sp["sheet"]]["sources"]] for sp in SPECS]
    src = table(["Programme", "Sources (read 4 October 2026)"], src_rows, cls="small", num_from=9, w0="30%")
    return (sheet + f'<section class="chapter"><span class="eyebrow">Appendix C</span><h1>How every number was computed</h1>{code}{repro}</section>'
            f'<section class="chapter"><span class="eyebrow">Appendix D</span><h1>Sources</h1>{src}'
            '<p class="note">Reliability evidence: TrustPilot company pages (rating withheld notices, August&ndash;September 2026) and PropFirmMap safety grades, both checked on 4 October 2026.</p></section>')
