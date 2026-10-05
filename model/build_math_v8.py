"""
Version 8 document: "The Prop Firm Option, version 8 - corrected after the review of version 7".
Reads the version 8 results (opt_v8_*, verify_v8.json, sens_v8.json, lockstep_v8*.json), the rule sheets (progs_v8.py)
and the review response (review_v8.py); writes prop_firm_math_v8.html and The_Prop_Firm_Option_v8_Mathematics.pdf.
"""
import json, math, pathlib, re, sys
import numpy as np
from doc8_common import *
import doc8_part1 as P1, doc8_part2 as P2, doc8_part3 as P3

N_PART1 = 11
CH0 = N_PART1 + 1
CH_ALLOC = CH0 + len(P2.SPECS); CH_LOCK = CH_ALLOC + 1; CH_REF = CH_LOCK + 1
CH_RUN = CH_REF + 1; CH_RISK = CH_RUN + 1
CH0_T5 = CH0 + [i for i, sp in enumerate(P2.SPECS) if sp["firm"] == "The5ers"][0] if any(sp["firm"] == "The5ers" for sp in P2.SPECS) else CH0

def contrib_fig():
    rows = []
    for f in P3.CFD_FIRMS:
        v, n = P2.alloc_value(P2.ALLOC[f]["rec"])
        if n: rows.append((f, v, n, TIER.get(f, "B")))
    rows.sort(key=lambda r: -r[1])
    W, rowh, l0, r0, t0 = 640, 19, 120, 70, 26
    H = t0 + rowh * len(rows) + 30
    vmax = max(r[1] for r in rows) * 1.08
    X = lambda v: l0 + max(v, 0) / vmax * (W - l0 - r0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    step = 2000 if vmax < 16000 else 5000
    for x in range(0, int(vmax) + 1, step):
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
    return fig("".join(g), f"Long-run value per month by firm in the recommended plan (number of accounts in brackets): each account's renewal&ndash;reward value on fresh paths. Colour: reliability tier (Chapter {CH_REF}).")

def bill():
    rows = []; tot = 0.0; nacc = 0; nf = 0
    for f in P3.CFD_FIRMS:
        rec = P2.ALLOC[f]["rec"]
        if rec: nf += 1
        for p, i, s, n in rec:
            r = P2.acct_row(p, i, s); tot += n * r["EV_month"]; nacc += n
            rows.append([P1.short(p), TIER.get(f, "?"), MSHORT[i], f"{n} &times; {kk(s)}", P1.sett(r), pm(r["EV_month"], r["CI"]), usd(n * r["EV_month"])])
    rows.append([f"<strong>{nacc} accounts at {nf} firms</strong>", "", "", "", "", "", f"<strong>{usd(tot)}</strong>"])
    return table(["Programme", "Tier", "Market", "Accounts", "Risk / k / m / X", "EV/month per account (95%)", "EV/month"], rows, cls="small tight", num_from=4, hl=(len(rows) - 1,)), tot, nacc, nf

def changed_text(s):
    """the change from version 7, measured: the headline, and per programme and market how many moved each way"""
    import doc8_common as C
    v7 = None
    try:
        L7 = json.load(open("lockstep_v7.json"))["R"]
        r7 = [r for r in L7 if r["p"] == P3.REC and r["months"] == 12]
        if r7: v7 = float(np.mean([np.mean(r["monthly"][:12]) for r in r7]))
    except FileNotFoundError:
        pass
    pairs = [(r, C.fin7(r["prog"], r["instr"])) for r in P1.chosen_rows() if r.get("kind") != "fut"]
    pairs = [(a, b) for a, b in pairs if b]
    lower = [a for a, b in pairs if a["EV_month"] + a["CI"] < b["EV_month"]]
    higher = [a for a, b in pairs if a["EV_month"] - a["CI"] > b["EV_month"]]
    import review_v8 as RV
    head = (f"<p>A second detailed review, of version 7, raised {len(RV.R)} findings (Appendix A); fixing them, and checking the corrected engine with new tests, "
            f"found {len(RV.NEW)} further errors: n1&ndash;n7 in version 7, n8&ndash;n11, n14 and n15 in version 8's own first engine and checks, and n12, n13 and n16 in both. Every rule finding was checked against the firms' own pages and every model finding against the code. "
            + (f"The figure moves from version 7's {usd(v7)} a month to {usd(s['ev'])}. " if v7 else "")
            + "The changes push in both directions. ")
    body = ("<strong>Lower:</strong> at FundingPips, The5ers, FXIFY, GFT, Hola Prime, Maven and Alpha Capital the daily loss limit is a share of the day's starting balance, so it shrinks after losses, and at FunderPro the stricter of its two possible bases is used; "
            "FXIFY Classic returns no fee; Maven needs three profitable days for every payout, and the plan keeps Maven's funded profit at or below $4,900 so that its 50% rule (above $5,000) never applies; "
            "Alpha's first payout needs five trading days; FunderPro Classic has minimum trading days; no position re-enters within 10 minutes of a close; no target or stop is closer than 0.6 hourly standard deviations; "
            "and every trade is now decided, and its result counted, on the day it opens, and a payout no longer restarts the day's caps (versions 7 and 8's first engine let some days exceed the 40% cap and GFT's day cap, n12 and n13). "
            "<strong>Higher:</strong> Hola Prime's 40% rule belongs to on-demand payouts, not the bi-weekly option; Fintokei's and GFT's minimum payouts were overstated; "
            "an account near its floor is now traded out (a small chance to recover) instead of abandoned. "
            "<strong>Neither way by construction:</strong> the random numbers of every stage and market are now independent streams, the paths have one-minute sub-steps, and micro futures are valued at the path's price. ")
    tail = (f"Programme by programme (Chapter 9.4), {len(lower)} of {len(pairs)} chosen settings are below their version 7 value by more than their interval, {len(higher)} above it, "
            f"and the rest within it. The figure is a new measurement under the corrected rules, not version 7's plus a list. "
            "Version 6's $138,412 rested on bold play, which several firms forbid; version 7 replaced it with the 40% policy.</p>")
    return head + body + tail

def answer():
    s = P3.pstats(P3.REC); bl, tot, nacc, nf = bill()
    k = lambda p: P3.pstats(p) if p in P3.SLOTS else None
    t_a = k("Tier A"); t_ab = k("Tier A + B"); full = k("All firms at full caps"); fut = k("Recommended + futures")
    L = LONG.get("R", [])
    lr = np.mean([np.mean(r["monthly"][12:]) for r in L]) if L else None
    lr_ci = 1.96 * np.std([np.mean(r["monthly"][12:]) for r in L]) / math.sqrt(len(L)) if L else None
    o12 = np.mean([r["open12"] for r in L]) if L else None
    st2 = [r for r in STRESS.get("R", []) if r["kw"].get("cost_mult") == 2.0]; c2 = np.mean([np.mean(r["monthly"]) for r in st2]) if st2 else None
    B = BUDGET.get("R", [])
    bud = {}
    for b in (10_000, 20_000, 50_000):
        g = [r for r in B if r["kw"].get("budget") == b]
        if g: bud[b] = np.mean([np.mean(r["monthly"]) for r in g])
    v6 = 138_412
    kp = lambda v, l: f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>'
    kp1 = (kp(usd(s["ss"]), "Months 2&ndash;12 average (first year)") + (kp(usd(lr), f"Average of months 13&ndash;36 of 36-month lives (&plusmn;{usd(lr_ci)})") if lr else "") +
           (kp(usd(o12), "Value still to come at month 12 from accounts then open") if o12 else "") + kp(usd(tot), "Sum of the accounts' long-run rates (Part II)"))
    kp2 = (kp(usd(s["tiered"]), f"If payouts are refused 2% / 5% / 15% by tier (Chapter {CH_REF})") + kp(usd(s["harsh"]), "If refused 5% / 10% / 30%") +
           (kp(usd(c2), "If every trading cost is twice the assumption") if c2 is not None else "") +
           (kp(usd(bud[20_000]), "First year with only $20,000 of starting cash") if 20_000 in bud else ""))
    kp3 = ((kp(usd(t_a["ev"]), f"Tier A firms only ({t_a['acc']} accounts)") if t_a else "") + (kp(usd(t_ab["ev"]), f"Tiers A and B ({t_ab['acc']} accounts)") if t_ab else "") +
           (kp(usd(full["ev"]), f"Every firm at its full modelled allowance ({full['acc']} accounts)") if full else "") + (kp(usd(fut["ev"]), f"Recommended + futures ({fut['acc']} accounts)") if fut else ""))
    return f"""
<section class="chapter"><span class="eyebrow">The answer</span><h1>Expected cash per month, one person</h1>
<div class="big">{usd(s['ev'])} <small>a month in the first year, &plusmn; {usd(s['ci'])} (95%)</small></div>
<p>That is the expected cash, after the fees modelled (evaluation fees, activation and monthly fees, refunds and credits as each firm's rules give them; not taxes or payment costs), that one person receives per month in the <em>first year</em> of the recommended plan: {s['acc']} accounts at {nf} prop firms, each traded with zero predictive skill under every rule of its firm that the model contains and the plan's own policies (flat every evening; no trade and no day above 40% of a target; at least 10 minutes between trades and no target or stop closer than 0.6 hourly standard deviations; an account near its floor traded out with a last stop at the floor, so that it ends in a breach that frees its allocation). In 90% of simulated first years the total lies between {usd(s['p05'])} and {usd(s['p95'])} (median {usd(s['p50'])}).</p>
<div class="kpis">{kp1}</div>
<div class="kpis">{kp2}</div>
<div class="kpis">{kp3}</div>
<h2>What changed from version 7</h2>
{changed_text(s)}
{contrib_fig()}
<h2>Where it comes from</h2>
{bl}
<p class="note">Risk / k / m / X: risk per trade and payout target as a share of the account, reward-to-risk, stop in hourly standard deviations. Per-account values are long-run rates from sixteen fresh paths; their sum ({usd(tot)}) is a different quantity from the first-year average ({usd(s['ev'])}), see 8.5.</p>
<h2>What the number means, and what it does not</h2>
<ul>
<li>It is an <strong>expected value under a model</strong>: the average over many possible years if prices are fair random walks with the measured volatility and costs. The &plusmn; is the simulation's precision, not a range for real income.</li>
<li>It assumes <strong>zero skill</strong>: the value comes from the contract (a capped loss, a share of gains), not from predicting prices.</li>
<li>It assumes the firms <strong>pay as their rules say</strong> and do not judge the plan's trading to break their behavioural rules (Chapter {CH_RISK}.2). The refusal scenarios above price random refusals only.</li>
<li>It assumes every slot is <strong>refilled at once</strong>, which needs cash for fees; with a finite budget the first year is lower (Chapter {CH_LOCK}.7).</li>
<li>It is <strong>per person</strong>: every firm limits what one person may hold. Accounts in anyone else's name are not allowed and are not in the plan.</li>
</ul>
<h2>How it was found</h2>
<ol>
<li>Part I derives every formula and says which model it is exact for; the exact chain of 5.5 implements the plan's actual rule near the floor. tests_v8.py checks every new rule mechanism of the engine directly (Chapter 11).</li>
<li>Every programme's settings (risk, \\(k\\), stop, payout target, market) were searched over {len(GRID):,} grid settings and {len(REF):,} refined ones ({(len(GRID) * 2000 + len(REF) * 16000) / 1e6:,.0f} million simulated attempts), then re-measured on sixteen fresh paths each.</li>
<li>The engine was checked against the chain with the daily rules switched off (Chapter 11), and the rules' own effect measured with them on.</li>
<li>The accounts were run together, one person at a time, each simulated life on its own new paths: {sum(len(P3.lives(p)) for p in P3.PNAMES):,} first years, {len(L)} three-year lives, and the budget and stress scenarios.</li>
</ol>
</section>"""

def contents():
    items = [("p", "", "The answer"), ("p", "", "Notation"), ("p", "I", "The mathematics, from zero")]
    titles1 = ["What is being bought", "The probability toolkit", "The price model", "The bracket trade", "Reaching a target before a floor", "The evaluation in full",
               "What a funded account pays", "Time, and value per month", "Optimising the settings", "Position size, leverage and margin", "Checking the engine against the formulas"]
    items += [("c", str(i + 1), x) for i, x in enumerate(titles1)]
    items.append(("p", "II", "Every programme in the plan"))
    items += [("c", str(CH0 + i), SHEET[sp["sheet"]]["title"]) for i, sp in enumerate(P2.SPECS)]
    items.append(("p", "III", "One person, many accounts"))
    items += [("c", str(CH_ALLOC), "The maximum allocation per person"), ("c", str(CH_LOCK), "Running every account at once"), ("c", str(CH_REF), "If payouts can be refused")]
    items.append(("p", "IV", "Running it"))
    items += [("c", str(CH_RUN), "The routine"), ("c", str(CH_RISK), "What could make the numbers wrong")]
    items.append(("p", "", "Appendices"))
    items += [("c", "A", "Corrections: the version 7 review, point by point"), ("c", "A2", "The version 6 review, in brief"), ("c", "B", "Formula sheet"), ("c", "C", "Glossary"), ("c", "D", "How every number was computed"), ("c", "E", "Sources")]
    lis = "".join(f'<li class="p"><span class="n">{n}</span><span class="t">{tt}</span></li>' if k == "p" else f'<li><span class="n">{n}</span><span class="t">{tt}</span></li>' for k, n, tt in items)
    return f'<section class="chapter"><span class="eyebrow">Contents</span><h1>Contents</h1><ul class="toc">{lis}</ul></section>'

def notation():
    rows = [("\\(S\\)", "account size"), ("\\(F\\)", "fee per attempt"), ("\\(A, A_1, A_2\\)", "profit target of a phase"), ("\\(B\\)", "maximum loss of a phase (distance to the floor)"),
            ("\\(b\\)", "safety buffer above the floor ($100 per $100K)"), ("\\(d\\)", "daily loss limit"), ("\\(D\\)", "funded allowance"), ("\\(\\alpha\\)", "profit split"), ("\\(R\\)", "fee refund"),
            ("\\(X_1, X\\)", "funded payout target: first, later"), ("\\(L, l\\)", "risk per trade: the plan's, and the one actually used"), ("\\(k\\)", "reward-to-risk setting"),
            ("\\(w\\)", "net win of a trade, after caps and costs"), ("\\(c, \\rho\\)", "round-trip cost of a trade; per dollar of risk, \\(\\rho = \\kappa/(m\\sigma)\\)"),
            ("\\(\\sigma\\)", "hourly standard deviation of the log price"), ("\\(m\\)", "stop distance in hourly standard deviations"), ("\\(N\\)", "notional of a position, \\(l/(m\\sigma)\\)"),
            ("\\(\\kappa\\)", "round-trip cost as a fraction of the notional"), ("\\(\\lambda\\)", "leverage (1:\\(\\lambda\\))"), ("\\(p\\)", "win probability of one bracket"),
            ("\\(P, P_1, P_2\\)", "pass probability"), ("\\(q_1, q\\)", "probability that a funded cycle reaches its payout target"), ("\\(X_\\text{end}\\)", "balance at which an attempt or account ends"),
            ("\\(V, C, T\\)", "value of an attempt, funded cash, duration"), ("\\(K\\)", "expected total cost of a phase or cycle"), ("EV/month", "\\(30.44\\,\\mathbb{E}[V]/\\mathbb{E}[T]\\) in days, a long-run rate")]
    return ('<section class="chapter"><span class="eyebrow">Notation</span><h1>Notation and conventions</h1>' +
            table(["Symbol", "Meaning"], [[a, b] for a, b in rows], num_from=9, w0="22%") +
            f"<p>Money is in US dollars. A 100K account is $100,000 of simulated capital. &plusmn; is a 95% Monte Carlo interval under the model. \"Fresh paths\" are synthetic price paths that played no part in choosing the setting they measure. \"Engine\" is the rule-by-rule simulation; \"chain\" the exact trade-level equations; \"Brownian\" the continuous approximation. Tiers A, B, D are the firms' reliability classes (Chapter {CH_REF}).</p></section>")

def part2_intro():
    return """<section class="part"><span class="num">Part II</span><h1>Every programme in the plan</h1>
<p>One chapter per firm, for the programme and market the plan uses there: the rules as published; exactly what the engine simulates; the search; the chosen setting and its alternatives on fresh paths; one trade in dollars and points; the evaluation and the funded account from the exact chain; value per attempt and per month; sizes and number of accounts; higher costs; and how the plan meets the rules.</p></section>"""

def cover(s):
    return f"""<section class="cover">
<span class="eyebrow">Mathematics &middot; Version 8 &middot; corrected after the second review &middot; 5 October 2026</span>
<h1>The Prop Firm Option</h1>
<p class="sub">The prop-firm programmes worth trading under each firm's rules and the plan's compliance policies, optimised setting by setting and derived step by step: how much one person can expect per month, and the mathematics behind every number.</p>
<div class="grow"></div>
<div class="big" style="color:#ffffff">{usd(s['ev'])}<small style="color:#c9d4ea"> expected per month in the first year, one person, recommended plan</small></div>
<div class="grow"></div>
<p class="disc">Expected values under a model of fair prices, for a trader with no predictive skill, under each firm's written rules as read on 4 October 2026. Firms may refuse payouts or apply behavioural rules at their discretion (Chapters {CH_REF} and {CH_RISK}). Not investment advice. Do not share or sell this plan: several firms close traders who run the same marketed strategy together.</p>
</section>"""

def katex_head():
    return ('<link rel="stylesheet" href="katex/katex.min.css">'
            '<script src="katex/katex.min.js"></script><script src="katex/contrib/auto-render.min.js"></script>'
            '<script>document.addEventListener("DOMContentLoaded",function(){renderMathInElement(document.body,{delimiters:['
            '{left:"$$",right:"$$",display:true},{left:"\\\\(",right:"\\\\)",display:false}],throwOnError:false});window.__katex_done=true;});</script>')

def review_subs(f1, f3):
    """the numbers the review appendix quotes"""
    import json as _j
    L = LONG.get("R", [])
    win = ""
    if L:
        M = np.array([r["monthly"] for r in L]); d = M[:, 12:24].mean(1) - M[:, 24:36].mean(1)
        win = f"months 13&ndash;24 minus 25&ndash;36 {sgn(d.mean())} &plusmn; {usd(1.96 * d.std() / math.sqrt(len(d)))} a month over {len(L)} lives"
    try:
        man = _j.load(open("stream_manifest_v8.json"))
        streams = f"{sum(v['streams'] for v in man['stages'].values()):,} streams over {len(man['stages'])} stages, " + ("no clash" if not man["clashes"] else f"{len(man['clashes'])} clashes")
    except FileNotFoundError:
        streams = ""
    dl = [r for r in SENS if r.get("tag") == "dll"]
    dll = ""
    if dl:
        parts = []
        for r in dl:
            base = [x for x in SENS if x.get("tag") == "cost" and x["prog"] == r["prog"] and x["instr"] == r["instr"] and x["cost_mult"] == 1.0]
            if base: parts.append(f"{P1.short(r['prog'])} {usd(base[0]['EV_month'])} with its own base against {usd(r['EV_month'])} with a fixed one")
        if parts: dll = "Measured on paths 141&ndash;144 (one 100K account, a month): " + "; ".join(parts) + "."
    return dict(GAP_MAX=f1.get("GAP_MAX", ""), TEXTBOOK_DIFF=f1.get("TEXTBOOK_DIFF", ""), TIE_RESULT=f1.get("TIE_RESULT", ""), SCALE_RESULT=f1.get("SCALE_RESULT", ""),
                SHORT_RESULT=f1.get("SHORT_RESULT", ""), BRIDGE_BOUND=f1.get("BRIDGE_BOUND", ""), GAP_RESULT=f1.get("GAP_RESULT", ""),
                STREAMS=streams, WINDOWS=win, DLL_SENS=dll)

def build():
    s = P3.pstats(P3.REC)
    f1 = P1.fills(); f3 = P3.part3_fills(CH_ALLOC, CH_LOCK, CH_REF)
    subs = dict(f1); subs.update(f3); subs.update(CH_RISK=CH_RISK, CH0_T5=CH0_T5); subs.update(review_subs(f1, f3))
    rsubs = review_subs(f1, f3)
    p1 = "".join(open(f).read() for f in ("math_v8_part1a.html", "math_v8_part1b.html", "math_v8_part1c.html", "math_v8_part1d.html"))
    p2 = part2_intro() + "".join(P2.prog_chapter(CH0 + i, sp) for i, sp in enumerate(P2.SPECS))
    p3 = open("math_v8_part3.html").read()
    p4 = P3.part4(CH_RUN, CH_RISK) + P3.appendices(rsubs)
    body = cover(s) + answer() + contents() + notation() + p1 + p2 + p3 + p4
    body = fill(body, subs)
    def _fix(mm): return re.sub(r"(?<!\\)%", r"\\%", re.sub(r"(?<=\d),(?=\d{3})", "{,}", mm.group(0)))
    body = re.sub(r"\\\(.*?\\\)", _fix, body, flags=re.S)
    body = re.sub(r"\$\$.*?\$\$", _fix, body, flags=re.S)
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The Prop Firm Option v8: Mathematics</title>'
            f'<style>{css()}</style>{katex_head()}</head><body>{body}</body></html>').replace("The Prop Firm Option v7: Mathematics", "The Prop Firm Option v8: Mathematics")
    open("prop_firm_math_v8.html", "w").write(html)
    return html

def pdf():
    from playwright.sync_api import sync_playwright
    footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
              'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v8 &middot; Mathematics</span>'
              '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        exe = "/opt/pw-browsers/chromium"
        b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + str(pathlib.Path("prop_firm_math_v8.html").resolve()), wait_until="networkidle")
        pg.wait_for_function("window.__katex_done === true", timeout=120000)
        pg.evaluate("document.fonts.ready")
        errs = pg.evaluate("Array.from(document.querySelectorAll('.katex-error')).map(e => e.getAttribute('title') || e.textContent).slice(0, 30)")
        left = pg.evaluate("(document.body.innerText.match(/\\\\\\(|\\$\\$/g) || []).length")
        pg.wait_for_timeout(1500)
        pg.pdf(path="The_Prop_Firm_Option_v8_Mathematics.pdf", format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer)
        b.close()
    return errs, left

def review_md(rsubs):
    """the review response as Markdown for the repository (docs/v8_review_response.md)"""
    import review_v8 as RV, html
    def clean(x):
        for k, v in rsubs.items(): x = x.replace(f"[[{k}]]", str(v))
        x = re.sub(r"<[^>]+>", "", x)
        return html.unescape(x).replace("\\(", "").replace("\\)", "")
    out = ["# Version 8: response to the review of version 7", "",
           "Every finding of the review (4 October 2026) checked against the firms' own pages (model/rules_snapshot_v8.json quotes them) and against the code, "
           "and what version 8 does about it. The PDF's Appendix A holds the same table.", ""]
    for x in RV.R:
        out += [f"## {x['n']}. {x['title']} ({x['verdict']})", "", f"**Wrong in version 7.** {clean(x['wrong'])}", "", f"**Version 8.** {clean(x['fix'])}", ""]
    out += ["## Further errors found while fixing the review's findings", ""]
    for x in RV.NEW:
        out += [f"- **{x['n']}. {x['title']}.** {clean(x['what'])}"]
    open("../docs/v8_review_response.md", "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    build()
    f1 = P1.fills(); review_md(review_subs(f1, None))
    errs, left = pdf()
    print("KaTeX errors:", len(errs)); [print("  ", e) for e in errs]
    print("unrendered delimiters:", left)
    print("built v8 mathematics")
