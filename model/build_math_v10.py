"""
Version 10 document: "The Prop Firm Option, version 10 - corrected after the review of version 9".
Reads the version 10 results (opt_v10_*, continuing_v10*.json, cont_check_v10.json, verify_v10.json, sens_v10.json,
lockstep_v10*.json, tests_v10.json, audit_v10.json, rules_inventory_v10.json), the programme sheets (progs_v10.py) and the
review response (review_v10.py); writes prop_firm_math_v10.html, The_Prop_Firm_Option_v10_Mathematics.pdf,
../docs/v10_review_response.md and layout_v10.json.

The build fails (and writes no PDF) if a [[placeholder]] is left unfilled, if KaTeX reports an error or leaves a formula
unrendered, or if a table, figure or displayed formula is wider than the text column in the printed layout (version 10:
version 9 printed a clipped table, review of version 9, finding 14).
"""
import json, math, pathlib, re, sys, datetime, collections
import numpy as np
from doc10_common import *
import doc10_part1 as P1, doc10_part2 as P2, doc10_part3 as P3

N_PART1 = 11
CH0 = N_PART1 + 1
CH_ALLOC = CH0 + len(P2.SPECS); CH_LOCK = CH_ALLOC + 1; CH_REF = CH_LOCK + 1
CH_RUN = CH_REF + 1; CH_RISK = CH_RUN + 1
CH0_T5 = CH0 + [i for i, sp in enumerate(P2.SPECS) if sp["firm"] == "The5ers"][0] if any(sp["firm"] == "The5ers" for sp in P2.SPECS) else CH0
TODAY = datetime.date.today()
DATE = f"{TODAY.day} {TODAY.strftime('%B %Y')}"
CONTENT_PX = 172 / 25.4 * 96          # A4 (210 mm) less the 19 mm side margins of @page, in CSS pixels

def contrib_fig():
    rows = []
    for f in P3.CFD_FIRMS:
        v, n = P2.alloc_value(P2.ALLOC[f]["rec"])
        if n: rows.append((f, v, n, TIER.get(f, "B")))
    rows.sort(key=lambda r: -r[1])
    W, rowh, l0, r0_, t0 = 640, 19, 120, 70, 26
    H = t0 + rowh * len(rows) + 30
    vmax = max(r[1] for r in rows) * 1.08
    X = lambda v: l0 + max(v, 0) / vmax * (W - l0 - r0_)
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
    return fig("".join(g), f"Value per month by firm in the recommended plan (number of accounts in brackets): each account's continuing-slot rate (8.3), rounded to the dollar and summed. Colour: reliability tier (Chapter {CH_REF}).")

def bill():
    rows = []; tot = 0.0; nacc = 0; nf = 0
    for f in P3.CFD_FIRMS:
        rec = P2.ALLOC[f]["rec"]
        if rec: nf += 1
        for p, i, s, n in rec:
            r = P2.acct_row(p, i, s); tot += n * r0(r["EV_month"]); nacc += n
            rows.append([P1.short(p), TIER.get(f, "?"), MSHORT[i], f"{n} &times; {kk(s)}", P1.sett(r), pm(r["EV_month"], r["CI"]), usd(n * r0(r["EV_month"]))])
    rows.append([f"<strong>{nacc} accounts at {nf} firms</strong>", "", "", "", "", "", f"<strong>{usd(tot)}</strong>"])
    return table(["Programme", "Tier", "Market", "Accounts", "Risk / k / m / X", "Continuing-slot rate per account (95%)", "EV/month"], rows, cls="small tight", num_from=4, hl=(len(rows) - 1,)), tot, nacc, nf

def _v9_headline():
    try:
        L9 = json.load(open("lockstep_v9.json"))["R"]
    except FileNotFoundError:
        return None, 0
    r9 = [r for r in L9 if r["p"] == P3.REC and r["months"] == 12]
    return (float(np.mean([np.mean(r["monthly"][:12]) for r in r9])), len(r9)) if r9 else (None, 0)

def changed_text(s):
    """the change from version 9, measured: the headline, and per programme and market how many moved each way"""
    import review_v10 as RV
    v9, n9 = _v9_headline()
    pairs = [(r, fin9(r["prog"], r["instr"])) for r in P1.chosen_rows() if r.get("kind") != "fut"]
    pairs = [(a, b) for a, b in pairs if b]
    def beyond(a, b): return abs(a["EV_month"] - b["EV_month"]) > math.hypot(a["CI"], b["CI"])
    lower = [a for a, b in pairs if a["EV_month"] < b["EV_month"] and beyond(a, b)]
    higher = [a for a, b in pairs if a["EV_month"] > b["EV_month"] and beyond(a, b)]
    head = (f"<p>A detailed review of version 9 raised {len(RV.R)} findings (Appendix A), every one reproduced on version 9's code before it was fixed; our own claim-by-claim reading of version 9, and the version 10 work itself, found {len(RV.NEW)} further errors (Appendix A2, which also says why the review found its errors first). "
            f"Every rule the model uses is listed with its source, the date it was read and its treatment in the inventory of Appendix [[APP_INV]]: {inv_read_sentence()}. "
            + (f"The first-year figure moves from version 9's {usd(v9)} a month to {usd(s['ev'])}; the difference is a new measurement under the corrected model, not version 9's figure minus a list of corrections. " if v9 else ""))
    body = ("<strong>The model is stricter where the review found it lenient:</strong> a payout request is pending until the firm processes it, a breach before then cancels it, and Alpha Capital, FundingPips, FXIFY and Blue Guardian lock the account meanwhile; every request waits 15 minutes after the last close; "
            "every published minimum payout is applied to the trader's share, and the fees GFT, The5ers, FundedNext and Blue Guardian take from every payout are deducted; The5ers' payout cap and profit gate apply, and its refund covers only the cash paid; Topstep's request session and $125 minimum, and Apex's pending requests, expiry and consistency, follow the firms' rules; "
            "Alpha Capital's lot limit, Blue Guardian's Guardian Shield and Maven's 1:1.5 on the position actually placed are enforced; the plan is flat around high-impact releases wherever a firm restricts news; and USDJPY results are exact in dollars. "
            "<strong>The measurement is named for what it is:</strong> Part II's per-account figure is the continuing-slot rate, the average cash per month in years 2 to 9 of a slot from today's prices, with its horizon and price-level sensitivity reported; refusals are drawn inside the event engine; every validation interval is computed over independent paths. ")
    tail = (f"Programme by programme (Chapter 9.4, random-start ratios), {len(lower)} of {len(pairs)} chosen settings are below their version 9 value by more than the two intervals combined (the square root of the sum of their squares), {len(higher)} above it, "
            "and the rest within it.</p>")
    return head + body + tail

def answer():
    s = P3.pstats(P3.REC); bl, tot, nacc, nf = bill()
    k = lambda p: P3.pstats(p) if p in P3.SLOTS else None
    t_a = k("Tier A"); t_ab = k("Tier A + B"); full = k("All firms at full caps"); fut = k("Recommended + futures")
    L = LONG.get("R", [])
    y23 = np.array([np.mean(r["monthly"][12:]) for r in L]) if L else None
    o12 = np.array([r["open12"] for r in L]) if L else None
    st2 = [r for r in STRESS.get("R", []) if r["kw"].get("cost_mult") == 2.0]
    c2 = float(np.mean([np.mean(r["monthly"][:12]) for r in st2])) if st2 else None
    base200 = float(np.mean([np.mean(r["monthly"][:12]) for r in P3.lives(P3.REC) if r["seed"] < P3.MAIN0 + 200]))
    B = BUDGET.get("R", [])
    bud = {}
    for b in (10_000, 20_000, 50_000):
        g = [r for r in B if r["kw"].get("budget") == b]
        if g: bud[b] = float(np.mean([np.mean(r["monthly"][:12]) for r in g]))
    rt, rh = P3._refus("tiered"), P3._refus("harsh")
    seeds_r = {x["seed"] for x in rt}
    base_r = float(np.mean([np.mean(r["monthly"][:12]) for r in P3.lives(P3.REC) if r["seed"] in seeds_r])) if rt else None
    ev_t = P3.stats_of(rt)["ev"] if rt else None; ev_h = P3.stats_of(rh)["ev"] if rh else None
    rs_ci, _ = P3.renewal_sum_ci(P3.REC)
    kp = lambda v, l: f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>'
    kp1 = (kp(usd(s["ss"]), "Months 2&ndash;12 average (first year)")
           + (kp(usd(y23.mean()), f"Average of months 13&ndash;36 of {len(L)} three-year lives (&plusmn;{usd(P3.ci95(y23))})") if L else "")
           + (kp(usd(o12.mean()), "Cash still to come after month 12 from accounts open then") if L else "")
           + kp(usd(tot), f"Sum of the accounts' continuing-slot rates (&plusmn;{usd(rs_ci)}; Part II)"))
    kp2 = ((kp(usd(ev_t), f"If payouts are refused 2% / 5% / 15% by tier ({len(rt)} lives: {usd(base_r)} on the same paths with all paid)") if rt else "")
           + (kp(usd(ev_h), "If refused 5% / 10% / 30%") if rh else "")
           + (kp(usd(c2), f"If every trading cost is twice the assumption ({len(st2)} lives: {usd(base200)} at the assumed costs)") if c2 is not None else "")
           + (kp(usd(bud[20_000]), "First year with only $20,000 of starting cash") if 20_000 in bud else ""))
    kp3 = ((kp(usd(t_a["ev"]), f"Tier A firms only ({t_a['acc']} accounts)") if t_a else "") + (kp(usd(t_ab["ev"]), f"Tiers A and B ({t_ab['acc']} accounts)") if t_ab else "")
           + (kp(usd(full["ev"]), f"Every firm at the largest allocation modelled ({full['acc']} accounts)") if full else "") + (kp(usd(fut["ev"]), f"Recommended + futures ({fut['acc']} accounts)") if fut else ""))
    ntests = len(TESTS); nok = sum(1 for v in TESTS.values() if v.get("ok"))
    return f"""
<section class="chapter"><span class="eyebrow">The answer</span><h1>Expected cash per month, one person</h1>
<div class="big">{usd(s['ev'])} <small>a month in the first year, &plusmn; {usd(s['ci'])} (95%)</small></div>
<p>That is the expected cash, after the fees modelled (evaluation fees, activation and monthly fees, the fees five firms take from every payout and Maven's $20 a payout, refunds and credits as each firm's rules give them; not taxes or the costs of a payout method), that one person receives per month in the <em>first year</em> of the recommended plan: {s['acc']} accounts at {nf} prop firms, each traded with zero predictive skill under the rules of the inventory (Appendix [[APP_INV]]: every rule that can change what the plan may do or what it is paid, with the cautious readings and the assumptions it names) and the plan's own policies (flat every evening and around restricted news; no trade and no day above 40% of a target; at least 10 minutes between trades and no target or stop closer than 0.6 hourly standard deviations; one direction per market, and one dollar direction for EURUSD and USDJPY; an account near its floor traded out with a last stop at the floor, so that it ends in a breach that frees its slot). In 90% of simulated first years the total lies between {usd(s['p05'])} and {usd(s['p95'])} (median {usd(s['p50'])}).</p>
<div class="kpis">{kp1}</div>
<div class="kpis">{kp2}</div>
<div class="kpis">{kp3}</div>
<h2>What changed from version 9</h2>
{changed_text(s)}
{contrib_fig()}
<h2>Where it comes from</h2>
{bl}
<p class="note">Risk / k / m / X: risk per trade and payout target as a share of the account, reward-to-risk, stop in hourly standard deviations. Per-account values are continuing-slot rates on sixteen new paths (8.3: the average cash per month in years 2 to 9 of a slot refilled at once, from today's prices), rounded to the dollar; the total is the sum of the printed values, and its interval (&plusmn;{usd(rs_ci)}) is computed from the per-path totals of all of them, which share their paths (8.4). It is a different quantity from the first-year average ({usd(s['ev'])}): see 8.5.</p>
<h2>What the number means, and what it does not</h2>
<ul>
<li>It is an <strong>expected value under a model</strong>: the average over many possible years if prices are fair random walks with the measured volatility and costs, and the firms apply their written rules as the inventory reads them. Three different things limit it: the model's own assumptions; the Monte Carlo error of computing its expectation, which is what the &plusmn; measures; and the difference between the model and real trading (fills, spreads, news, the firms' discretion, rules that change), which no interval here covers (Chapter {CH_RISK}).</li>
<li>It assumes <strong>zero skill</strong>: the value comes from the contract (a capped loss, a share of gains), not from predicting prices.</li>
<li>It assumes the firms <strong>pay as their rules say</strong> and do not judge the plan's trading to break their behavioural rules (Chapter {CH_RISK}.2). The refusal scenarios above price random refusals only.</li>
<li>It assumes every slot is <strong>refilled at once</strong>, which needs cash for fees; with a finite budget the first year is lower (Chapter {CH_LOCK}.7).</li>
<li>It is <strong>per person</strong>: every firm limits what one person may hold. Accounts in anyone else's name are not allowed and are not in the plan.</li>
</ul>
<h2>How it was found</h2>
<ol>
<li>Part I derives every formula and states the model it is exact for; the exact chain of 5.5 implements the plan's rule near the floor. tests_v10.py runs {ntests} direct tests of the engine's rule mechanisms, one for each correction of version 10 and the review's own witnesses included ({nok} pass; Chapter 11), and audit_v10.py replays every chosen setting trade by trade against the rules it lists.</li>
<li>Every rule was listed with its source, the date it was read and its treatment in the model (Appendix [[APP_INV]]: {inv_read_sentence()}), and the list was compared with the engine's rule parameters row by row.</li>
<li>Every programme's settings (risk, \\(k\\), stop, payout target, market) were searched over {len(GRID):,} grid settings and {len(REF):,} refined ones, then re-measured on sixteen fresh paths each, and run as continuing slots on sixteen more.</li>
<li>The engine was checked against the chain on the chain's own rules (Chapter 11), and the rules' own effect measured with them on.</li>
<li>The accounts were run together, one person at a time, each simulated life on its own new paths: {len(P3.R):,} first years, {len(L)} three-year lives, and the budget, stress and refusal scenarios.</li>
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
    items += [("c", "A", "Corrections: the version 9 review, point by point"), ("c", "A2", "Errors we found ourselves, and why the review found its errors first"),
              ("c", "A3", "The earlier reviews, in brief"), ("c", "B", "Every rule, its source, and what the model does with it"), ("c", "C", "Formula sheet"),
              ("c", "D", "Glossary"), ("c", "E", "How every number was computed"), ("c", "F", "Sources")]
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
            ("\\(V, C, T\\)", "value of an attempt, funded cash, duration"), ("\\(K\\)", "expected total cost of a phase or cycle"),
            ("EV/month", "cash per month: as a continuing-slot rate, the average cash per month in years 2 to 9 of a slot refilled at once, from today's prices; or as the search's random-start ratio \\(30.44\\sum V/\\sum T\\) (8.3)")]
    return ('<section class="chapter"><span class="eyebrow">Notation</span><h1>Notation and conventions</h1>' +
            table(["Symbol", "Meaning"], [[a, b] for a, b in rows], num_from=9, w0="22%") +
            f"<p>Money is in US dollars. A 100K account is $100,000 of simulated capital. &plusmn; is a 95% Monte Carlo interval under the model. Dollar figures are rounded half away from zero, and a printed total is the sum of the printed parts. \"Fresh paths\" are synthetic price paths that played no part in choosing the setting they measure. \"Engine\" is the rule-by-rule simulation; \"chain\" the exact trade-level equations; \"Brownian\" the continuous approximation. Tiers A, B, D are the firms' reliability classes (Chapter {CH_REF}).</p></section>")

def part2_intro():
    return """<section class="part"><span class="num">Part II</span><h1>Every programme in the plan</h1>
<p>One chapter per firm, for the programme and market the plan uses there: the rules as published (from the inventory, Appendix B); exactly what the engine simulates; the search; the chosen setting and its alternatives on fresh paths; one trade in dollars and points; the evaluation and the funded account from the exact chain; value per attempt and per month; sizes and number of accounts; higher costs; and how the plan meets the rules.</p></section>"""

def cover(s):
    return f"""<section class="cover">
<span class="eyebrow">Mathematics &middot; Version 10 &middot; corrected after the review of version 9 &middot; {DATE}</span>
<h1>The Prop Firm Option</h1>
<p class="sub">The prop-firm programmes worth trading under each firm's rules and the plan's compliance policies, optimised setting by setting and derived step by step: how much one person can expect per month, and the mathematics behind every number.</p>
<div class="grow"></div>
<div class="big" style="color:#ffffff">{usd(s['ev'])}<small style="color:#c9d4ea"> expected per month in the first year, one person, recommended plan</small></div>
<div class="grow"></div>
<p class="disc">Expected values under a model of fair prices, for a trader with no predictive skill, under each firm's written rules as read on 11 and 12 October 2026 (older readings marked in Appendix B). Firms may refuse payouts or apply behavioural rules at their discretion (Chapters {CH_REF} and {CH_RISK}). Not investment advice. Do not share or sell this plan: several firms close traders who run the same marketed strategy together.</p>
</section>"""

def katex_head():
    return ('<link rel="stylesheet" href="katex/katex.min.css">'
            '<script src="katex/katex.min.js"></script><script src="katex/contrib/auto-render.min.js"></script>'
            '<script>document.addEventListener("DOMContentLoaded",function(){renderMathInElement(document.body,{delimiters:['
            '{left:"$$",right:"$$",display:true},{left:"\\\\(",right:"\\\\)",display:false}],throwOnError:false});window.__katex_done=true;});</script>')

def _durations():
    """the review's exact counterexample (finding 24): expected durations of a long and a short bracket, stop s = sigma,
    target 3 s, on dP/P = sigma dW (no cost), by optional stopping for the log price"""
    sg = SIG["US100"]; s_ = sg; u = 3 * sg; p = s_ / (s_ + u)
    tl = -2 * (p * math.log(1 + u) + (1 - p) * math.log(1 - s_)) / sg ** 2
    ts = -2 * (p * math.log(1 - u) + (1 - p) * math.log(1 + s_)) / sg ** 2
    return p, tl, ts

def review_subs(f1):
    """the numbers the review appendices quote"""
    out = {}
    for name, d in TESTS.items():
        out[f"T:{name}"] = ("tests_v10.py, " + name + ": " + d.get("info", "") + ("." if not d.get("info", "").endswith(".") else "")) if d.get("ok") else f"tests_v10.py, {name}: FAILED ({d.get('info', '')})"
    for k in ("ABANDONED", "ALPHA_LOTS", "BG_OVER", "NEWS_STATS", "INV_N", "APP_INV", "MAVEN_RR"):
        out[k] = f1.get(k, "")
    out["F9_RESULT"] = f1.get("JOINT_RESULT", "")
    n_new, n_all = inv_read_counts()
    out["INV_READ"] = (f"all {n_all} rows read on 11&ndash;12 October 2026" if n_new == n_all else
                       f"{n_new} of its {n_all} rows read on 11&ndash;12 October 2026, the other {n_all - n_new} on 4 October 2026 for version 9")
    # 11: horizon and price level
    items = P3._slot_items(P3.REC); txt = ""
    if items and all("per_path_y2_5" in c for c, n in items):
        e = np.array([[n * x for x in c["per_path_y2_5"]] for c, n in items]).sum(0); l = np.array([[n * x for x in c["per_path_y6_9"]] for c, n in items]).sum(0)
        d = l - e; G = len(d)
        dci = float(O.tq(G - 1) * d.std(ddof=1) / math.sqrt(G))
        txt = (f"For the recommended plan's accounts, years 2 to 5 average {usd(e.mean())} a month and years 6 to 9 {usd(l.mean())}: a difference of {sgn(d.mean())} &plusmn; {usd(dci)} "
               f"({P3.iv_words(d.mean(), dci)}; paired over the {G} paths). ")
    pt = re.sub(r"<[^>]+>", "", P3.price_text()).replace("The price level. ", "")
    out["F11_RESULT"] = txt + pt
    # 12: refusals in the engine
    rt, rh = P3._refus("tiered"), P3._refus("harsh")
    if rt and rh:
        seeds = {x["seed"] for x in rt}
        b = float(np.mean([np.mean(r["monthly"][:12]) for r in P3.lives(P3.REC) if r["seed"] in seeds]))
        out["F12_RESULT"] = (f"On the same {len(rt)} paths the recommended plan's first year is {usd(b)} a month with every payout honoured, {usd(P3.stats_of(rt)['ev'])} in the tiered scenario and {usd(P3.stats_of(rh)['ev'])} in the harsh one "
                             f"(version 9's ledger filter gave $41,579 and $27,820 against its $60,714).")
    else:
        out["F12_RESULT"] = ""
    out["F14_RESULT"] = "[[LAYOUT_RESULT]]"
    out["F22_RESULT"] = ("Per trade, cost-free 1:3 brackets on the Nasdaq: " + f1.get("CHK_DIR", "") + " (the plan's rule / a coin flip, 16 paths); brackets with costs (k = 3, m = 1): "
                         + f1.get("CHK_R3", "") + " R against the theory's " + f1.get("CHK_R3_TH", "") + "; scaling, " + f1.get("SCALE_TEST", "") + ".")
    out["F23_RESULT"] = (("Summed over the chosen settings, with intervals from the per-path contributions: the measurement (continuing minus random start, the plan's rule) "
                          + f1.get("CONT_M_SUM", "") + " a month, the direction rule (the plan's rule minus a coin flip, random starts) " + f1.get("CONT_R_SUM", "")
                          + f" a month; setting by setting, the measurement lies within its interval for {f1.get('CONT_M_INSIDE', '?')} of {f1.get('CONT_CK_N', '?')} and the direction rule for {f1.get('CONT_R_INSIDE', '?')}.") if f1.get("CONT_M_SUM") else "")
    p, tl, ts = _durations()
    out["F24_RESULT"] = (f"With the Nasdaq's hourly \\(\\sigma\\) = {SIG['US100']:.6f} the long and the short bracket both win with chance {p:.2f} and last {tl:.4f} and {ts:.4f} hours on average (the review's figures). "
                         + (f"Measured, the direction rule changes the chosen settings' summed random-start rate by {f1.get('CONT_R_SUM')} a month." if f1.get("CONT_R_SUM") else ""))
    out["CH_RISK"] = CH_RISK
    return out

def build():
    s = P3.pstats(P3.REC)
    f1 = P1.fills(); f3 = P3.part3_fills(CH_ALLOC, CH_LOCK, CH_REF)
    rsubs = review_subs(f1)
    subs = dict(f1); subs.update(f3); subs.update(CH_RISK=CH_RISK, CH_RUN=CH_RUN, CH0_T5=CH0_T5); subs.update(rsubs)
    p1 = "".join(open(f).read() for f in ("math_v10_part1a.html", "math_v10_part1b.html", "math_v10_part1c.html", "math_v10_part1d.html"))
    p2 = part2_intro() + "".join(P2.prog_chapter(CH0 + i, sp) for i, sp in enumerate(P2.SPECS))
    p3 = open("math_v10_part3.html").read()
    p4 = P3.part4(CH_RUN, CH_RISK) + P3.appendices(rsubs)
    body = cover(s) + answer() + contents() + notation() + p1 + p2 + p3 + p4
    n_tab = body.count("<table"); n_svg = body.count("<svg"); n_disp = body.count("$$") // 2
    subs["LAYOUT_RESULT"] = (f"in this document {n_tab} tables, {n_svg} figures and {n_disp} displayed formulas were measured in the printed layout, and none is wider than the text column (layout_v10.json)")
    for _ in range(3):                                     # placeholders inside filled values
        body = fill(body, subs)
    left = sorted(set(re.findall(r"\[\[[A-Za-z0-9_:]+\]\]", body)))
    if left: raise SystemExit(f"unfilled placeholders: {left}")
    def _fix(mm): return re.sub(r"(?<!\\)%", r"\\%", re.sub(r"(?<=\d),(?=\d{3})", "{,}", mm.group(0)))
    body = re.sub(r"\\\(.*?\\\)", _fix, body, flags=re.S)
    body = re.sub(r"\$\$.*?\$\$", _fix, body, flags=re.S)
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The Prop Firm Option v10: Mathematics</title>'
            f'<style>{css()}</style>{katex_head()}</head><body>{body}</body></html>')
    open("prop_firm_math_v10.html", "w").write(html)
    return html, rsubs, dict(tables=n_tab, figures=n_svg, formulas=n_disp)

LAYOUT_JS = """(W) => {
  const out = [];
  const sel = 'table, svg, .formula, .katex-display, .kpis, .calc, figure';
  document.querySelectorAll(sel).forEach((el, i) => {
    if (el.closest('.cover')) return;
    const r = el.getBoundingClientRect();
    const wide = Math.max(r.width, el.scrollWidth);
    if (r.width === 0) return;
    if (wide > W + 1.5 || r.right > W + 1.5 || r.left < -1.5) {
      const h = el.closest('section') ? (el.closest('section').querySelector('h1') || {}).textContent : '';
      out.push({tag: el.tagName, cls: el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className, width: wide, right: r.right,
                section: h, text: (el.textContent || '').slice(0, 120)});
    }
  });
  return out;
}"""

def pdf(counts):
    from playwright.sync_api import sync_playwright
    footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
              'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v10 &middot; Mathematics</span>'
              '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        exe = "/opt/pw-browsers/chromium"
        b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
        pg = b.new_page(viewport=dict(width=int(round(CONTENT_PX)), height=1100))
        pg.emulate_media(media="print")
        pg.goto("file://" + str(pathlib.Path("prop_firm_math_v10.html").resolve()), wait_until="networkidle")
        pg.wait_for_function("window.__katex_done === true", timeout=180000)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1500)
        errs = pg.evaluate("Array.from(document.querySelectorAll('.katex-error')).map(e => e.getAttribute('title') || e.textContent).slice(0, 30)")
        left = pg.evaluate("(document.body.innerText.match(/\\\\\\(|\\$\\$/g) || []).length")
        over = pg.evaluate(LAYOUT_JS, CONTENT_PX)
        json.dump(dict(content_px=CONTENT_PX, overflow=over, katex_errors=errs, unrendered=left, **counts), open("layout_v10.json", "w"), indent=1)
        if errs or left or over:
            b.close()
            raise SystemExit(f"layout check failed: {len(errs)} KaTeX errors, {left} unrendered delimiters, {len(over)} elements wider than the column (layout_v10.json)")
        pg.pdf(path="The_Prop_Firm_Option_v10_Mathematics.pdf", format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer)
        b.close()
    return errs, left, over

def review_md(rsubs):
    """the review response as Markdown for the repository (docs/v10_review_response.md)"""
    import review_v10 as RV, html
    def clean(x):
        for _ in range(3):
            for k, v in rsubs.items(): x = x.replace(f"[[{k}]]", str(v))
        x = x.replace("[[APP_INV]]", "B").replace("[[CH_RISK]]", str(CH_RISK)).replace("[[CH_RUN]]", str(CH_RUN))
        x = re.sub(r"</(p|li)>", "\n", x); x = re.sub(r"<li>", "- ", x)
        x = re.sub(r"<[^>]+>", "", x)
        return html.unescape(x).replace("\\(", "").replace("\\)", "").replace("\\text{", "").replace("\\mathbb{E}", "E").replace("\\min", "min").replace("\\ell", "l")
    out = ["# Version 10: response to the review of version 9", "",
           "Every finding of the review (consolidated 12 October 2026, findings 1-25) reproduced on version 9's code, checked against the firms' own pages "
           "(model/rules_inventory_v10.json lists every rule with its source) and fixed, with the test that checks the fix. The PDF's Appendices A and A2 hold the same text.", ""]
    for x in RV.R:
        out += [f"## {x['n']}. {x['title']} ({x['verdict']})", "", f"**Wrong in version 9.** {clean(x['wrong'])}", "", f"**Version 10.** {clean(x['fix'])}", ""]
    out += ["## Errors we found ourselves", ""]
    for x in RV.NEW:
        out += [f"- **{x['n']}. {x['title']}.** {clean(x['what'])}"]
    out += ["", "## Why the review found these errors first, and what changed", "", clean(RV.INTRO), "", clean(RV.PROCESS), ""]
    open("../docs/v10_review_response.md", "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    html, rsubs, counts = build()
    errs, left, over = pdf(counts)
    rsubs = dict(rsubs, LAYOUT_RESULT=json.load(open("layout_v10.json")) and "every table, figure and displayed formula of the document was measured in the printed layout, and none is wider than the text column")
    rsubs["F14_RESULT"] = rsubs["LAYOUT_RESULT"]
    review_md(rsubs)
    print("KaTeX errors:", len(errs), " unrendered:", left, " overflow:", len(over))
    print("built v10 mathematics")
