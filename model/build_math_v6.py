"""
Version 6 document: "The Prop Firm Option - every positive-EV programme, optimised and derived".
Reads the optimiser's final run (opt_v6_final.json), the refined search (opt_v6_refine.jsonl), the grid (opt_v6_grid.jsonl),
the verification (verify_v6.json), the sensitivities (sens_v6.json, extra_v6.json), the portfolios (lockstep_v6.json) and
the programme sheets (progs_v6.py); writes prop_firm_math_v6.html and The_Prop_Firm_Option_v6_Mathematics.pdf.
Formulas are TeX, typeset by KaTeX (model/katex) in the browser before printing.
"""
import json, math, pathlib, re, sys
import numpy as np
from doc6_common import *
import doc6_part1 as P1, doc6_part2 as P2, doc6_part3 as P3

N_PART1 = 11
CH0 = N_PART1 + 1                                   # first programme chapter
CH_ALLOC = CH0 + len(P2.SPECS); CH_LOCK = CH_ALLOC + 1; CH_REF = CH_LOCK + 1
CH_RUN = CH_REF + 1; CH_RISK = CH_RUN + 1

# ------------------------------------------------------------------ the answer first
def contrib_fig():
    rows = []
    for f in P3.FIRM_ORDER[:13]:
        v, n = P2.alloc_value(P2.ALLOC[f]["rec"])
        rows.append((f, v, n, F5.TIER.get(f, "B")))
    rows.sort(key=lambda r: -r[1])
    W, rowh, l0, r0, t0 = 640, 19, 120, 70, 26
    H = t0 + rowh * len(rows) + 30
    vmax = max(r[1] for r in rows) * 1.05
    X = lambda v: l0 + v / vmax * (W - l0 - r0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for x in range(0, int(vmax) + 1, 5000):
        g.append(f'<line x1="{X(x):.1f}" x2="{X(x):.1f}" y1="{t0 - 4}" y2="{t0 + rowh * len(rows)}" stroke="{RULE}" stroke-width="0.5"/>')
        g.append(t(X(x), t0 + rowh * len(rows) + 12, k_(x), 7.5, "middle", MUT, True))
    for i, (f, v, n, tr) in enumerate(rows):
        y = t0 + i * rowh
        g.append(f'<rect x="{l0}" y="{y + 3}" width="{max(X(v) - l0, 1):.1f}" height="{rowh - 6}" rx="2" fill="{TIERC.get(tr, S4)}"/>')
        g.append(t(l0 - 6, y + rowh / 2 + 3, f"{f} ({n})", 8.2, "end", INK))
        g.append(t(X(v) + 5, y + rowh / 2 + 3, usd(v), 8, "start", INK, True))
    lx = l0
    for tr, lab in (("A", "tier A"), ("B", "tier B"), ("D", "tier D")):
        g.append(f'<rect x="{lx}" y="6" width="9" height="9" rx="2" fill="{TIERC[tr]}"/>'); g.append(t(lx + 13, 14, lab, 8, "start", MUT)); lx += 70
    g.append("</svg>")
    return fig("".join(g), "Expected cash per month by firm in the recommended plan (number of accounts in brackets), from each account's renewal&ndash;reward value on fresh paths. Colour: the firm's reliability tier (Chapter %d)." % CH_REF)

def bill():
    rows = []; tot = 0.0; nacc = 0
    for f in P3.FIRM_ORDER[:13]:
        for p, i, s, n in P2.ALLOC[f]["rec"]:
            r = P2.acct_row(p, i, s); tot += n * r["EV_month"]; nacc += n
            rows.append([f"{P1.short(p)}", F5.TIER.get(f, "?"), MSHORT[i], f"{n} &times; {kk(s)}", f"{r['k']} / {r['m']:g} / {r['X'] / r['size']:.0%}", pm(r["EV_month"], r["CI"]), usd(n * r["EV_month"])])
    rows.append([f"<strong>{nacc} accounts at 13 firms</strong>", "", "", "", "", "", f"<strong>{usd(tot)}</strong>"])
    return table(["Programme", "Tier", "Market", "Accounts", "k / m / X", "EV/month per account", "EV/month"], rows, cls="small tight", num_from=4, hl=(len(rows) - 1,)), tot

def answer():
    s = P3.pstats(P3.REC); bl, tot = bill()
    t_a = P3.pstats("Tier A"); t_ab = P3.pstats("Tier A + B"); full = P3.pstats("All firms at full caps"); fut = P3.pstats("Recommended + futures (Topstep 5, Apex 20)")
    try:
        v5 = json.load(open("lockstep_portfolio_v5.json"))
        v5r = [r for r in v5 if r["p"] == "Tier A + B + one account at each tier-D firm (13 firms, 23 accounts)" and r["data"].startswith("synth")]
        v5ev = float(np.mean([np.mean(r["monthly"]) for r in v5r]))
    except Exception:
        v5ev = None
    kp = lambda v, l: f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>'
    return f"""
<section class="chapter"><span class="eyebrow">The answer</span><h1>Expected cash per month, one person</h1>
<div class="big">{usd(s['ev'])} <small>a month, &plusmn; {usd(s['ci'])} (95%)</small></div>
<p>That is the expected cash, after every fee, that one person receives per month in the first year of the recommended plan: {s['acc']} accounts at 13 prop firms, each traded with zero predictive skill under every written rule of its firm, with the settings optimised in this document. From the second month on, once the first payouts arrive, the average is {usd(s['ss'])} a month. The total for the first year has a median of {usd(s['p50'])}; in 90% of simulated years it lies between {usd(s['p05'])} and {usd(s['p95'])}.</p>
<div class="kpis">{kp(usd(t_a['ev']), 'Tier A firms only (15 accounts, 5 firms)')}{kp(usd(t_ab['ev']), 'Tiers A and B (22 accounts, 7 firms)')}{kp(usd(full['ev']), 'Every firm at its full allowance (35 accounts)')}{kp(usd(fut['ev']), 'Recommended + futures layer (53 accounts)')}</div>
<div class="kpis">{kp(usd(s['tiered']), 'If payouts are refused 2% / 5% / 15% of the time by tier (Chapter ' + str(CH_REF) + ')')}{kp(usd(s['harsh']), 'If refused 5% / 10% / 30% of the time')}{kp(usd(-s['tr50']), 'Cash needed for fees before payouts arrive (median; 5%: ' + usd(-s['tr05']) + ')')}{kp(f"{s['orders']:.0f}", 'Bracket orders a day across all accounts')}</div>
{contrib_fig()}
<h2>Where it comes from</h2>
{bl}
<p class="note">k / m / X: reward-to-risk, stop in hourly standard deviations, funded cycle target as a share of the account. EV per account from the final run on fresh paths; the total ({usd(tot)}) is the long-run rate, and the portfolio simulation's first-year average ({usd(s['ev'])}) agrees within its interval.</p>
<h2>What the number means, and what it does not</h2>
<ul>
<li>It is an <strong>expected value</strong>: the average over many possible years. A single year's cash is spread widely (the percentiles above) because funded-account payouts come in large, rare pieces.</li>
<li>It assumes <strong>zero skill</strong>: every trade is a fair bet before costs. The value comes from the contract (a capped loss, a share of the gains), not from predicting prices. Part I proves why that is positive and how large.</li>
<li>It assumes the firms <strong>pay as their rules say</strong>. The two scenarios above price the risk that they do not. That risk is real, and not measurable from public data.</li>
<li>It assumes the <strong>costs measured</strong> in Chapter 3. Chapter {CH_RISK} reruns every programme at 1.5 and 2 times those costs.</li>
<li>It is <strong>per person</strong>: every firm limits what one person may hold, and Chapter {CH_ALLOC} fills each limit. Accounts in anyone else's name are not allowed and are not in the plan.</li>
</ul>
<h2>How it was found</h2>
<ol>
<li>Part I derives every formula from first principles: the bracket trade, the pass probability (exactly, for any reward-to-risk), the funded account's payout (the withdrawal identity), time and value per month.</li>
<li>Every programme's settings (reward-to-risk \\(k\\), stop \\(m\\), funded cycle \\(X\\), market, account size) were searched over {len(GRID):,} grid settings and {len(REF):,} refined ones: {(len(GRID) * 4000 + len(REF) * 24000) / 1e6:,.0f} million simulated attempts under each firm's full rules.</li>
<li>Every reported figure was re-measured on price paths not used to choose it, and on the real 2024&ndash;26 history, and checked against exact equations written separately (Chapter 11).</li>
<li>The accounts were then run together, one person at a time, on one shared price path and calendar, 2,800 simulated years in all (Chapter {CH_LOCK}).</li>
</ol>
""" + (f"<p class='note'>Version 5's comparable plan (23 accounts at default settings) was worth {usd(v5ev)} a month in its own simulation. The gain comes from the optimised settings (Chapter 9), FXIFY's smaller accounts, a fifth Fintokei account and FundedNext at 200K.</p>" if v5ev else "") + "</section>"

def contents():
    items = [("p", "", "The answer"), ("p", "", "Notation"), ("p", "I", "The mathematics, from zero")]
    titles1 = ["What is being bought", "The probability toolkit", "The price model", "The bracket trade", "Reaching a target before a floor", "The evaluation in full",
               "What a funded account pays", "Time, and value per month", "Optimising every setting", "Position size, leverage and margin", "Checking the engine against the formulas"]
    items += [("c", str(i + 1), x) for i, x in enumerate(titles1)]
    items.append(("p", "II", "Every programme, optimised and derived"))
    items += [("c", str(CH0 + i), SHEET[sp["sheet"]]["title"]) for i, sp in enumerate(P2.SPECS)]
    items.append(("p", "III", "One person, many accounts"))
    items += [("c", str(CH_ALLOC), "The maximum allocation per person"), ("c", str(CH_LOCK), "Running every account at once"), ("c", str(CH_REF), "If payouts can be refused")]
    items.append(("p", "IV", "Running it"))
    items += [("c", str(CH_RUN), "The routine"), ("c", str(CH_RISK), "What could make the numbers wrong")]
    items.append(("p", "", "Appendices"))
    items += [("c", "A", "Formula sheet"), ("c", "B", "Glossary"), ("c", "C", "How every number was computed"), ("c", "D", "Sources")]
    lis = "".join(f'<li class="p"><span class="n">{n}</span><span class="t">{tt}</span></li>' if k == "p" else f'<li><span class="n">{n}</span><span class="t">{tt}</span></li>' for k, n, tt in items)
    return f'<section class="chapter"><span class="eyebrow">Contents</span><h1>Contents</h1><ul class="toc">{lis}</ul></section>'

def notation():
    rows = [("\\(S\\)", "account size"), ("\\(F\\)", "fee per attempt"), ("\\(A, A_1, A_2\\)", "profit target of a phase"), ("\\(B\\)", "maximum loss of a phase (distance to the floor)"),
            ("\\(d\\)", "daily loss limit"), ("\\(D\\)", "funded allowance (maximum loss of the funded account)"), ("\\(\\alpha\\)", "profit split"), ("\\(R\\)", "fee refund"),
            ("\\(X_1, X\\)", "funded cycle target: first, later"), ("\\(l, L\\)", "risk of a trade (L: the normal 1.5%)"), ("\\(k\\)", "reward-to-risk; a full win nets \\(w = kl\\)"),
            ("\\(w\\)", "net win of a trade (after cost)"), ("\\(c\\)", "round-trip cost of a trade"), ("\\(\\rho\\)", "cost per dollar of risk, \\(c/l = \\kappa/(m\\sigma)\\)"),
            ("\\(\\sigma\\)", "hourly standard deviation of the log price"), ("\\(m\\)", "stop distance in hourly standard deviations"), ("\\(s, u\\)", "stop and target distance as a fraction of the price"),
            ("\\(N\\)", "notional of a position, \\(l/s\\)"), ("\\(\\kappa, \\varphi\\)", "round-trip cost and overnight financing, as fractions of the notional"),
            ("\\(\\lambda\\)", "leverage (1:\\(\\lambda\\))"), ("\\(p\\)", "win probability of one bracket"), ("\\(v\\)", "variance of one trade"), ("\\(P, P_1, P_2\\)", "pass probability"),
            ("\\(q_1, q\\)", "probability that a funded cycle reaches its target"), ("\\(\\theta\\)", "\\(2c/v\\), the exponent of the Brownian formula"), ("\\(V, C, T\\)", "value of an attempt, funded cash, duration"),
            ("\\(K\\)", "expected total cost of a phase or cycle"), ("EV/month", "\\(30.44\\,\\mathbb{E}[V]/\\mathbb{E}[T]\\) in days")]
    return ('<section class="chapter"><span class="eyebrow">Notation</span><h1>Notation and conventions</h1>' +
            table(["Symbol", "Meaning"], [[a, b] for a, b in rows], num_from=9, w0="22%") +
            "<p>Money is in US dollars. A 100K account is $100,000 of simulated capital. &plusmn; is a 95% interval. \"Fresh paths\" are synthetic price paths that played no part in choosing the setting they measure. \"Engine\" is the rule-by-rule simulation; \"chain\" is the exact trade-level equations; \"Brownian\" is the continuous approximation. Tiers A, B, D are the firms' reliability classes (Chapter " + str(CH_REF) + ").</p></section>")

def part2_intro():
    return f"""<section class="part"><span class="num">Part II</span><h1>Every programme, optimised and derived</h1>
<p>One chapter per programme, each built the same way: the firm's rules as published; exactly what the engine simulates; the search and its results; the chosen setting on fresh paths and the real history; one trade worked through in dollars and points; the evaluation and the funded account derived with the exact chain; value per attempt and per month; account sizes and the number of accounts; what higher costs do; and how the plan meets every rule.</p></section>"""

def cover(s):
    return f"""<section class="cover">
<span class="eyebrow">Mathematics &middot; Version 6 &middot; 4 October 2026</span>
<h1>The Prop Firm Option</h1>
<p class="sub">Every positive-expected-value prop-firm programme, optimised setting by setting and derived step by step: how much one person can expect to make per month, and the mathematics behind every number.</p>
<div class="grow"></div>
<div class="big" style="color:#ffffff">{usd(s['ev'])}<small style="color:#c9d4ea"> expected per month, one person, recommended plan</small></div>
<div class="grow"></div>
<p class="disc">Expected values for a trader with no predictive skill, under each firm's written rules as read on 4 October 2026, from simulations and exact calculations described in full inside. Firms may refuse payouts (Chapter {CH_REF} prices that risk). Not investment advice. Do not share or sell this plan: several firms close traders who run the same marketed strategy together.</p>
</section>"""

def katex_head():
    return ('<link rel="stylesheet" href="katex/katex.min.css">'
            '<script src="katex/katex.min.js"></script><script src="katex/contrib/auto-render.min.js"></script>'
            '<script>document.addEventListener("DOMContentLoaded",function(){renderMathInElement(document.body,{delimiters:['
            '{left:"$$",right:"$$",display:true},{left:"\\\\(",right:"\\\\)",display:false}],throwOnError:false});window.__katex_done=true;});</script>')

def build():
    s = P3.pstats(P3.REC)
    f1 = P1.fills(); f3 = P3.part3_fills(CH_ALLOC, CH_LOCK, CH_REF)
    subs = dict(f1); subs.update(f3)
    p1 = "".join(open(f).read() for f in ("math_v6_part1a.html", "math_v6_part1b.html", "math_v6_part1c.html", "math_v6_part1d.html"))
    p2 = part2_intro() + "".join(P2.prog_chapter(CH0 + i, sp) for i, sp in enumerate(P2.SPECS))
    p3 = open("math_v6_part3.html").read()
    p4 = P3.part4(CH_RUN, CH_RISK) + P3.appendices()
    body = cover(s) + answer() + contents() + notation() + p1 + p2 + p3 + p4
    body = fill(body, subs)
    # thousands separators inside formulas: write 1{,}000 so TeX does not add the space it puts after a comma
    def _fix(mm): return re.sub(r"(?<!\\)%", r"\\%", re.sub(r"(?<=\d),(?=\d{3})", "{,}", mm.group(0)))
    body = re.sub(r"\\\(.*?\\\)", _fix, body, flags=re.S)
    body = re.sub(r"\$\$.*?\$\$", _fix, body, flags=re.S)
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The Prop Firm Option v6: Mathematics</title>'
            f'<style>{css()}</style>{katex_head()}</head><body>{body}</body></html>')
    open("prop_firm_math_v6.html", "w").write(html)
    return html

def pdf():
    from playwright.sync_api import sync_playwright
    footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
              'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v6 &middot; Mathematics</span>'
              '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        exe = "/opt/pw-browsers/chromium"
        b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + str(pathlib.Path("prop_firm_math_v6.html").resolve()), wait_until="networkidle")
        pg.wait_for_function("window.__katex_done === true", timeout=120000)
        pg.evaluate("document.fonts.ready")
        errs = pg.evaluate("Array.from(document.querySelectorAll('.katex-error')).map(e => e.getAttribute('title') || e.textContent).slice(0, 30)")
        left = pg.evaluate("(document.body.innerText.match(/\\\\\\(|\\$\\$/g) || []).length")
        pg.wait_for_timeout(1500)
        pg.pdf(path="The_Prop_Firm_Option_v6_Mathematics.pdf", format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer)
        b.close()
    return errs, left

if __name__ == "__main__":
    build()
    errs, left = pdf()
    print("KaTeX errors:", len(errs)); [print("  ", e) for e in errs]
    print("unrendered delimiters:", left)
    print("built v6 mathematics")
