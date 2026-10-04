"""Part I of the version 6 document: the computed tables and worked examples that fill the chapter templates."""
import math, collections, json
import numpy as np
from doc6_common import *

FT = "FTMO 2-Step"
MARKETS = ["US100", "USDJPY", "EURUSD", "XAUUSD", "MNQ_fut"]

def sigma_table():
    rows = []
    for mk in MARKETS:
        sg = SIG[mk]; h = hours(mk)
        daily = sg * math.sqrt(23 if mk != "USDJPY" and mk != "EURUSD" else 24)
        rows.append([MNAME[mk], f"{PRICE[mk]:,.4g}" if PRICE[mk] < 10 else f"{PRICE[mk]:,.2f}", pct(sg, 4), pct(daily, 2),
                     pct(kappa(mk), 4), pct(phi(mk), 4), f"{kappa(mk) / sg:.3f}", f"{h[0]:02d}&ndash;{h[1]:02d}" if h else "all"])
    return table(["Market", "Price, 2 Oct 2026", "Hourly &sigma;", "Daily &sigma;", "Round-trip cost &kappa;", "Financing &phi; per night",
                  "&kappa;/&sigma;", "Entry hours (UTC)"], rows, cls="small",
                 cap="&sigma;: standard deviation of hourly log returns on 2024&ndash;26 data (sigma_v32.json); daily = hourly &times; &radic;23 (indices, gold) or &radic;24 (currencies). "
                     "&kappa;: spread + commission + slippage allowance as a fraction of the notional, per round trip (calibrate.py). &phi;: overnight financing per rollover, as a fraction of the notional. "
                     "&kappa;/&sigma; is the cost of one hourly standard deviation of movement: the lower, the cheaper the market. Micro Nasdaq futures carry no financing (the cost is in the price) and are used only by the futures firms.")

def sig_day(): return pct(SIG["US100"] * math.sqrt(23), 2)

def cost_table():
    rows = []
    for mk in MARKETS[:4]:
        sg = SIG[mk]
        rows.append([MNAME[mk]] + [pct(kappa(mk) / (m * sg), 1) for m in (0.35, 0.5, 0.75, 1.0)] + [pct(phi(mk) / (m * sg), 1) for m in (0.35, 1.0)])
    return table(["Market", "c/l at m = 0.35", "0.5", "0.75", "1.0", "financing per night / l at m = 0.35", "at m = 1.0"], rows, cls="small",
                 cap="The cost of one round trip, and of one night held, in units of the risk \\(l\\), for stops of \\(m\\) hourly standard deviations: \\(c/l = \\kappa/(m\\sigma)\\) and \\(\\varphi/(m\\sigma)\\). "
                     "A Nasdaq position with a stop of 0.35 hourly moves pays 6.7% of its risk to open and close, and 15.7% of its risk for every night it is held. "
                     "Overnight financing is the larger cost for the plan's long-running winners, and the engine charges it on every rollover.")

def _calc(lines): return '<div class="calc">' + "".join(f"<p>{x}</p>" for x in lines) + "</div>"

def trade_example():
    c = fin(FT); m, k, L = c["m"], c["k"], c["L"]
    A = 10_000
    T1 = trade_numbers("US100", m, L, A, lev=50)              # the first trade of phase 1: the win is cut to the target
    Tf = trade_numbers("US100", m, L, k * L, lev=50)          # an uncut win (k L)
    out = [f"<p>The plan's FTMO setting is \\(l = \\${L:,.0f}\\) (1.5% of $100,000), a stop of \\(m = {m}\\) hourly standard deviations, and \\(k = {k}\\). Take the very first trade of phase 1, when the account is at its start and the target is \\(A = \\$10{{,}}000\\) away. Since \\(k\\,l = \\${k * L:,.0f}\\) is more than the distance to the target, the win is cut to \\(w = \\$10{{,}}000\\) (5.5). With the Nasdaq at {PRICE['US100']:,.0f}:</p>"]
    out.append(_calc([
        f"Stop distance: \\(s = m\\sigma = {m} \\times {SIG['US100'] * 100:.4f}\\% = {T1['s'] * 100:.4f}\\%\\) of the price, i.e. \\({T1['stop_pts']:.1f}\\) index points.",
        f"Notional: \\(N = l/s = {L:,.0f} / {T1['s']:.6f} = \\${T1['N']:,.0f}\\), i.e. \\(\\${T1['usd_per_pt']:.2f}\\) per index point (\\(= l/\\text{{stop points}}\\)). If one lot is worth $1 per point (read the contract specification; some platforms use $10 or $20), that is \\({T1['usd_per_pt']:.2f}\\) lots, rounded <em>down</em> to the lot step.",
        f"Cost: \\(c = \\kappa N = {kappa('US100') * 100:.4f}\\% \\times \\${T1['N']:,.0f} = \\${T1['c']:.2f}\\), so \\(c/l = {T1['rho'] * 100:.2f}\\%\\).",
        f"Target: \\(u = s(w+c)/l = {T1['s'] * 100:.4f}\\% \\times {A + T1['c']:,.2f}/{L:,.0f} = {T1['u'] * 100:.4f}\\%\\), i.e. \\({T1['tgt_pts']:.1f}\\) points above the entry (for a long).",
        f"Win probability: \\(p = l/(l+w+c) = {L:,.0f}/({L:,.0f} + {A:,.0f} + {T1['c']:.2f}) = {T1['p']:.4f}\\).",
        f"Mean: \\(-c = -\\${T1['c']:.2f}\\). Check: \\(p\\,w - (1-p)(l+c) = {T1['p']:.5f}\\times{A:,.0f} - {1 - T1['p']:.5f}\\times{L + T1['c']:,.2f} = {T1['p'] * A - (1 - T1['p']) * (L + T1['c']):.2f}\\).",
        f"Variance: \\(v = l(w+c) = {L:,.0f}\\times{A + T1['c']:,.2f} = {T1['var']:,.0f}\\), standard deviation \\(\\${T1['sd']:,.0f}\\).",
        f"Overnight financing if held through a rollover: \\(\\varphi N = {phi('US100') * 100:.3f}\\%\\times\\${T1['N']:,.0f} = \\${T1['fin_night']:,.0f}\\) per night.",
        f"Margin at 1:50: \\(N/50 = \\${T1['margin']:,.0f}\\) = {pct(T1['margin_pct'])} of the balance (the plan's limit is 60%; the smallest stop FTMO's leverage allows is \\(m_{{\\min}} = {T1['m_min']:.3f}\\), Chapter 10).",
        f"Duration (8.1): on average \\(m^2 (w+c)/l = {m}^2 \\times {(A + T1['c']) / L:.3f} = {T1['dur']:.2f}\\) hours of open market; a losing trade lasts \\({T1['dur_loss']:.2f}\\) hours on average and a winning one \\({T1['dur_win']:.2f}\\) hours (8.1).",
    ]))
    out.append(f"<p>The same position with its target uncut, \\(w = k\\,l = \\${k * L:,.0f}\\) (as on a funded cycle, whose target is {usd(c['X'])}): \\(p = {Tf['p']:.4f}\\), target {Tf['tgt_pts']:,.0f} points away ({Tf['u'] * 100:.2f}% of the price), average duration {Tf['dur']:.1f} hours, winners {Tf['dur_win']:.0f} hours on average, so a winner is usually held through one or more nights and pays {usd(Tf['fin_night'])} per night in financing. The engine charges every one of those nights.</p>")
    return "".join(out)

def _steps_table(A, B, L, rho, buf=100.0, cap=None):
    rows, P = AN.bold_steps(A, B, L, rho, buf=buf)
    body = [[str(r["j"] + 1), usd(r["x"]), usd(r["l"]), usd(r["c"], 2), usd(r["w"]), f"{r['p']:.4f}", f"{r['surv']:.4f}", f"{r['surv'] * r['p']:.4f}", f"{r['P']:.4f}"] for r in rows]
    return table(["Trade \\(j\\)", "Balance \\(x_j\\)", "Risk \\(l_j\\)", "Cost \\(c_j\\)", "Win \\(A - x_j\\)", "\\(p_j\\)", "Still trading", "Passes on this trade", "Passed so far"],
                 body, cls="small steps", num_from=1), P

def phase_example():
    c = fin(FT); m, k, L = c["m"], c["k"], c["L"]
    F = rules(FT); rho = kappa("US100") / (m * SIG["US100"])
    e = AN.programme_exact(FT, "US100", m, k, c["X1"], c["X"], L=L, F=F)
    a = AN.programme(FT, "US100", m, k, c["X1"], c["X"], L=L, F=F)
    v = ver(FT, "US100")
    t1, P1b = _steps_table(10_000, 10_000, L, rho)
    t2, P2b = _steps_table(5_000, 10_000, L, rho)
    ph1, ph2 = e["phases"]
    tr = a["trade"]; th = 2 * tr["c"] / tr["var"]
    out = [f"<p><strong>Phase 1</strong> (\\(A = \\$10{{,}}000\\), \\(B = \\$10{{,}}000\\)) at the plan's setting. Because \\(k\\,l = \\${k * L:,.0f} \\ge A + B\\), every win ends the phase, and the chain of 5.6 is the sequence below. Each loss moves the balance down by \\(l + c = \\${L + rho * L:,.2f}\\); the last trade risks only what is left above the floor less the $100 buffer.</p>", t1,
           f"<p>The product formula gives \\(P_1 = {P1b:.4f}\\). The full chain (which also counts the last tiny trades a few dollars above the floor) gives \\(P_1 = {ph1['P']:.4f}\\), with an expected {ph1['N']:.2f} trades and an expected total cost \\(K(0) = \\${ph1['Ecost']:,.0f}\\). The identity of 5.6 checks it: \\((B - K)/(A+B) = ({10_000:,} - {ph1['Ecost']:,.0f})/20{{,}}000 = {ph1['P_identity']:.4f}\\).</p>",
           f"<p><strong>Phase 2</strong> (\\(A = \\$5{{,}}000\\), \\(B = \\$10{{,}}000\\), a fresh account):</p>", t2,
           f"<p>\\(P_2 = {ph2['P']:.4f}\\) (product {P2b:.4f}), {ph2['N']:.2f} trades and \\(\\${ph2['Ecost']:,.0f}\\) of cost on average; identity \\((10{{,}}000 - {ph2['Ecost']:,.0f})/15{{,}}000 = {ph2['P_identity']:.4f}\\). Together \\(P = P_1 P_2 = {ph1['P']:.4f}\\times{ph2['P']:.4f} = {e['P']:.4f}\\).</p>",
           f"<p><strong>The Brownian formula of 5.2</strong> at the same setting uses \\(c = \\${tr['c']:.2f}\\), \\(v = l(kl + c) = {tr['var']:,.0f}\\) and \\(\\theta = 2c/v = {th:.3e}\\), and gives \\(P = {a['P']:.4f}\\): too high, because it treats a 1 : 30 trade as if it could overshoot the target, and so undercounts how many trades (and costs) a phase takes. At the version 5 default (\\(k = 5\\), \\(m = 0.75\\)), where trades are small next to the distances, the Brownian formula and the exact chain agree: {ver(FT, 'US100', 'v5 default')['P_formula']:.4f} against {ver(FT, 'US100', 'v5 default')['P_exact']:.4f}.</p>",
           f"<p><strong>The engine</strong>, with the daily loss limit, minimum days, weekends, gaps and overnight financing, gives \\(P = {v['P_engine']:.4f} \\pm {binom_ci(v['P_engine'], 24000):.4f}\\) on the fresh paths: {pct(v['P_exact'] - v['P_engine'])} below the chain, the cost of the nights a winning trade is held and of the trades cut at the Friday close.</p>"]
    return "".join(out)

def bold_example():
    c = fin(FT); m, L = 0.35, 1500.0
    F = rules(FT)
    rows = []
    for k in (1, 2, 3, 5, 8, 12, 20, 30, 50):
        e = AN.programme_exact(FT, "US100", m, k, 30_000, 30_000, L=L, F=F)
        s = [r for r in sens("kcurve") if r["k"] == k][0]
        rows.append([str(k), f"{e['phases'][0]['N']:.1f}", usd(e["phases"][0]["Ecost"]), f"{e['phases'][0]['P']:.4f}", f"{e['P']:.4f}", usd(e["cash_funded"]), sgn(e["EV"]),
                     f"{s['P']:.3f}", pm(s["EV_month"], s["CI"])])
    tb = table(["\\(k\\)", "Phase 1 trades", "Phase 1 cost \\(K\\)", "\\(P_1\\) exact", "\\(P\\) exact", "Funded cash, exact", "Value of an attempt, exact", "\\(P\\), engine", "EV per month, engine"],
               rows, cls="small")
    pts = [r for r in sens("kcurve")]; pts.sort(key=lambda r: r["k"])
    W, H, l0, r0, t0, b0 = 640, 230, 60, 20, 20, 40
    xs = [math.log(r["k"]) for r in pts]; x0, x1 = min(xs), max(xs)
    ymin, ymax = -2000, 7000
    X = lambda v: l0 + (v - x0) / (x1 - x0) * (W - l0 - r0)
    Y = lambda v: t0 + (ymax - v) / (ymax - ymin) * (H - t0 - b0)
    g = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for yv in range(-2000, 7001, 1000):
        g.append(f'<line x1="{l0}" x2="{W - r0}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RULE}" stroke-width="{1 if yv == 0 else 0.5}"/>')
        g.append(t(l0 - 6, Y(yv) + 3, k_(yv), 8, "end", MUT, True))
    for r in pts:
        g.append(t(X(math.log(r["k"])), H - b0 + 14, str(r["k"]), 8, "middle", MUT, True))
        g.append(f'<line x1="{X(math.log(r["k"])):.1f}" x2="{X(math.log(r["k"])):.1f}" y1="{Y(r["EV_month"] - r["CI"]):.1f}" y2="{Y(r["EV_month"] + r["CI"]):.1f}" stroke="{S1}" stroke-width="1.2" stroke-opacity="0.55"/>')
    g.append('<polyline points="' + " ".join(f"{X(math.log(r['k'])):.1f},{Y(r['EV_month']):.1f}" for r in pts) + f'" fill="none" stroke="{S1}" stroke-width="2"/>')
    for r in pts:
        g.append(f'<circle cx="{X(math.log(r["k"])):.1f}" cy="{Y(r["EV_month"]):.1f}" r="3.2" fill="{S1}" stroke="#fff" stroke-width="1.5"/>')
    g.append(t((l0 + W - r0) / 2, H - 6, "reward-to-risk k (log scale)", 8.5, "middle", MUT))
    g.append(t(l0, 12, "EV per month, FTMO 2-Step 100K, m = 0.35, cycle 30% (engine, fresh paths, 95% interval)", 8.5, "start", INK))
    g.append("</svg>")
    return (f"<p>For FTMO at a stop of 0.35 and a cycle of $30,000, the table follows the chain and the engine as \\(k\\) grows. The pass probability rises because the expected cost falls (fewer trades), exactly as 5.6 says, and the value per month follows.</p>" + tb +
            fig("".join(g), "Bold play in the engine: value per month against k, FTMO 2-Step, everything else fixed. Below k = 3 the cost of many small trades eats the option; the gain flattens beyond k = 20, where one win already reaches every target."))

def funded_example():
    c = fin(FT); m, k, L, X = c["m"], c["k"], c["L"], c["X"]
    F = rules(FT); fd = F["funded"]; D = fd["dd"]; a = fd["split"]; R = fd["refund"]
    e = AN.programme_exact(FT, "US100", m, k, c["X1"], X, L=L, F=F)
    rho = kappa("US100") / (m * SIG["US100"])
    tb, qb = _steps_table(X, D, L, rho)
    q = e["q"]; n = q / (1 - q)
    v = ver(FT, "US100")
    dist = "".join(f"<tr><td>{j}</td><td class='n'>{(q ** j) * (1 - q):.4f}</td><td class='n'>{usd(a * X * j + (R if j >= 1 else 0))}</td></tr>" for j in range(0, 5))
    out = [f"<p>FTMO's funded account at the plan's setting: allowance \\(D = \\${D:,.0f}\\) (static), cycle target \\(X_1 = X = \\${X:,.0f}\\), split \\(\\alpha = {a:.0%}\\), refund \\(R = \\${R:,.0f}\\) with the first payout. One cycle is the bold chain from 0 to \\(+X\\) before \\(-D\\):</p>", tb,
           f"<p>The full chain gives the cycle's success chance \\(q = {q:.4f}\\) (product {qb:.4f}). Cycles repeat until one fails, so</p>",
           _calc([f"\\(\\mathbb{{E}}[\\text{{paid cycles}}] = q/(1-q) = {q:.4f}/{1 - q:.4f} = {n:.4f}\\)",
                  f"\\(\\mathbb{{E}}[\\text{{withdrawn before the split}}] = X\\,q/(1-q) = {X:,.0f}\\times{n:.4f} = \\${X * n:,.0f}\\)",
                  f"Withdrawal identity (7.1): \\(D - \\mathbb{{E}}[\\text{{cost of all funded trades}}] = {D:,.0f} - {e['cost_funded']:,.0f} = \\${e['identity']:,.0f}\\) (the same, to the grid's precision)",
                  f"\\(\\mathbb{{E}}[C] = \\alpha \\times {e['withdrawn']:,.0f} + R\\,q = {a} \\times {e['withdrawn']:,.0f} + {R:,.0f}\\times{q:.4f} = \\${e['cash_funded']:,.0f}\\)"]),
           f"<p>The engine, on fresh paths, pays {usd(v['cash_engine'])} per funded account: {pct(1 - v['cash_engine'] / v['cash_exact'])} less than the chain, almost all of it overnight financing on the long-running winners (a cycle's winning trade must travel {pct(Tf_u(m, k, L))} of the price and is usually held through nights at {usd(phi('US100') * L / (m * SIG['US100']))} each). The cash comes in large, rare pieces:</p>",
           f"<table class='small' style='width:60%'><thead><tr><th>Paid cycles</th><th class='n'>Probability \\(q^j(1-q)\\)</th><th class='n'>Cash (split + refund)</th></tr></thead><tbody>{dist}</tbody></table>",
           f"<p>{pct(1 - q, 0)} of funded accounts never pay; {pct(q, 0)} pay at least {usd(a * X + R)}. That is the price of bold play: the same average as many small payouts, in fewer, larger ones. Chapter {{CH_REF}} returns to what that means if payouts can be refused.</p>"]
    return "".join(out).replace("{CH_REF}", "[[CH_REF]]")

def Tf_u(m, k, L):
    T = trade_numbers("US100", m, L, 30_000)
    return T["u"]

def time_example():
    c = fin(FT); m, k, L = c["m"], c["k"], c["L"]
    e = AN.programme_exact(FT, "US100", m, k, c["X1"], c["X"], L=L, F=rules(FT))
    ph1, ph2 = e["phases"]
    T = trade_numbers("US100", m, L, 10_000)
    att = DAYS_MONTH / c["days"]
    out = [f"<p>FTMO at the plan's setting. Phase 1 takes on average {ph1['N']:.2f} trades (5.6); the first lasts {T['dur']:.2f} hours of open market on average (4.5), later ones a little longer (the target is farther). So the market time of a phase is a few hours, and the calendar is set by the rules: four trading days per phase, a review of one day after phase 1 and up to three after phase 2, the 14-day wait for the first payout, and the trading window (no new trades after 20:00 UTC, none at weekends).</p>",
           _calc([f"Engine, fresh paths: an attempt lasts \\(\\mathbb{{E}}[T] = {c['days']:.2f}\\) days on average, from the purchase to the failed phase or the lost funded account.",
                  f"So one slot buys \\(30.44/{c['days']:.2f} = {att:.2f}\\) evaluations a month and pays \\({att:.2f}\\times\\${rules(FT)['fee']:,.0f} = \\${att * rules(FT)['fee']:,.0f}\\) a month in fees before refunds.",
                  f"Value of an attempt (engine): \\(\\mathbb{{E}}[V] = \\${c['EV']:,.0f}\\); pass rate {pct(c['P'])}; cash per funded account {usd(c['Vf'])}.",
                  f"Renewal&ndash;reward (8.3): \\(30.44 \\times {c['EV']:,.0f} / {c['days']:.2f} = \\${c['EV_month']:,.0f}\\) per month, &plusmn; {usd(c['CI'])} (95%).",
                  f"The median time from buying an attempt that pays to its first payout is {c['t1']:.0f} days; {pct(c['P_paid'])} of attempts reach a payout."])]
    tm = timing(FT, "US100")
    if tm:
        out.append(f"<p>Decomposed (engine, 6,000 attempts on path 29): {pct(tm['fail_p1'], 0)} of attempts fail in phase 1, and an attempt that fails anywhere in the evaluation lasts {tm['t_eval_fail']:.1f} days on average, mostly the minimum days and the wait to the next trading day. "
                   f"An attempt that passes spends {tm['t_eval_pass']:.1f} days in the evaluation (four trading days per phase and the reviews) and {tm['t_fund']:.1f} days funded, making {tm['payouts']:.2f} payouts on average. "
                   f"The weighted average, \\((1-P)\\times{tm['t_eval_fail']:.1f} + P\\times({tm['t_eval_pass']:.1f} + {tm['t_fund']:.1f})\\), is the {tm['days']:.1f} days of an attempt on this path.</p>")
    return "".join(out)

def n_grid(): return f"{len(GRID):,}"
def n_grid_attempts(): return f"{len(GRID) * 4000 / 1e6:,.1f} million"
def n_refine(): return f"{len(REF):,}"
def n_refine_attempts(): return f"{len(REF) * 24000 / 1e6:,.1f} million"

def curse():
    d = []
    for r in FIN:
        if r["tag"] not in ("chosen",) or r["data"] != "synth" or r.get("robust"): continue
        rs = [x for x in REF if x["prog"] == r["prog"] and x["instr"] == r["instr"] and x["m"] == r["m"] and x["k"] == r["k"] and abs(x["X"] - r["X"]) < 1 and x["L"] == r["L"]]
        if rs: d.append((max(x["EV_month"] for x in rs) - r["EV_month"]) / max(x["EV_month"] for x in rs))
    return pct(float(np.mean(d)), 0)

PLAN_PROGS = [("FTMO 2-Step", "US100"), ("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY"), ("The5ers High Stakes Classic", "US100"),
              ("FXIFY Two Phase Classic (100%, 30 days)", "US100"), ("FundedNext Stellar 2-Step v5", "EURUSD"), ("Fintokei ProTrader", "US100"),
              ("Hola Prime 2-Step Prime (bi-weekly 80%)", "XAUUSD"), ("Alpha Capital Pro 10%", "US100"), ("FunderPro Classic v5", "US100"),
              ("GFT 2-Step Standard v5", "US100"), ("BrightFunded 2-Step Classic v5", "US100"), ("Blue Guardian 2-Step v5", "US100"), ("Maven 2-Step", "US100")]
OTHER_PROGS = [("FTMO 1-Step", "US100"), ("FundingPips 2-Step Flex (85%) v6 4days", "USDJPY"), ("FundingPips 2-Step Flex (95%) v5", "USDJPY"),
               ("The5ers High Stakes", "US100"), ("FXIFY Two Phase Classic (80%)", "US100"), ("FXIFY Two Phase Classic (100%, 30 days)", "USDJPY"),
               ("FXIFY Two Phase Classic (80%)", "USDJPY"), ("FundedNext Stellar 2-Step v5", "XAUUSD"), ("Hola Prime 2-Step Prime (bi-weekly 80%)", "EURUSD"),
               ("Alpha Capital Pro 10% (on-demand)", "US100")]

def short(prog):
    return (prog.replace(" v5", "").replace(" v6 cap", " (cap)").replace(" v6 4days", " (4 days)").replace("2-Step Prime (bi-weekly 80%)", "2-Step Prime")
            .replace("Two Phase Classic", "Classic").replace("Stellar 2-Step", "Stellar").replace("2-Step Classic", "Classic").replace("2-Step Standard", "Standard"))
def sett(r): return f"{r['k']} / {r['m']:g} / {r['X'] / r['size']:.0%}"

def opt_table():
    rows = []; hl = []
    for i, (p, ins) in enumerate(PLAN_PROGS + OTHER_PROGS):
        ch = fin(p, ins); d5 = fin(p, ins, "v5 default"); un = fin(p, ins, "uncapped"); re_ = fin(p, ins, data="real")
        if not ch: continue
        if i < len(PLAN_PROGS): hl.append(len(rows))
        rows.append([f"{short(p)}, {MSHORT[ins]}", sett(d5) if d5 else "=", usd(d5["EV_month"]) if d5 else "=", sett(ch), pm(ch["EV_month"], ch["CI"]),
                     usd(re_["EV_month"]) if re_ else "", (f"{sett(un)}: {usd(un['EV_month'])}" if un else "within limits")])
    return table(["Programme, market", "v5 setting k / m / X", "v5 EV/month", "Chosen k / m / X", "Chosen EV/month (95%)", "Real history", "Best outside the limits"],
                 rows, cls="small", hl=hl,
                 cap="All values per month for one 100K account (Fintokei, FXIFY, FundedNext etc. at 100K here; Part II gives the sizes the plan uses), from the final run on fresh paths 29&ndash;32 "
                     "(33&ndash;36 for FundedNext, re-chosen for robustness), 24,000 attempts each, and 8,000 attempts on the real 2024&ndash;26 history. Shaded rows are the programmes in the plan. "
                     "X is the funded cycle target as a share of the account. \"=\" means the version 5 default is the chosen setting.")

def opt_general():
    plan = [(p, i) for p, i in PLAN_PROGS]
    d5 = sum(fin(p, i, "v5 default")["EV_month"] for p, i in plan if fin(p, i, "v5 default"))
    ch = sum(fin(p, i)["EV_month"] for p, i in plan if fin(p, i, "v5 default"))
    un_gain = [(p, i, fin(p, i, "uncapped")["EV_month"] - fin(p, i)["EV_month"]) for p, i in plan if fin(p, i, "uncapped")]
    ks = sens("kcurve")
    ft = fin(FT); ftu = fin(FT, tag="uncapped"); ftr = fin(FT, tag="uncapped", data="real"); ftcr = fin(FT, data="real")
    fpold = fin("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY", "refine best"); fpn = fin("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY")
    rob = {(r["prog"], r["m"], r["cost_mult"]): r for r in EXTRA["robust"]}
    kk_ = [fin(p, i)["k"] for p, i in plan if fin(p, i)]; kmin, kmax = min(kk_), max(kk_)
    sig_, eq_ = [], []
    for p, i in plan:
        a_, b_ = fin(p, i), fin(p, i, "v5 default")
        if not (a_ and b_): continue
        (sig_ if a_["EV_month"] - b_["EV_month"] > math.hypot(a_["CI"], b_["CI"]) else eq_).append(short(p))
    beat_txt = (f"the chosen setting beats the version 5 default by more than their combined 95% interval in {len(sig_)} of the {len(sig_) + len(eq_)} programmes; "
                f"in the others ({', '.join(eq_)}) the two are equal within the noise, and the plan keeps the searched setting." if eq_ else
                f"the chosen setting beats the version 5 default by more than their combined interval in every programme.")
    kcurve_txt = ", ".join("k = %d: %s" % (r["k"], usd(r["EV_month"])) for r in sorted(ks, key=lambda r: r["k"]) if r["k"] in (3, 8, 20, 30))
    fpc = lambda m_, cm: rob[("FundingPips 2-Step Flex (85%) v6 cap", m_, cm)]["EV_month"]
    fnc = lambda m_, cm: rob[("FundedNext Stellar 2-Step v5", m_, cm)]["EV_month"]
    plan = PLAN_PROGS
    out = [f"<p><strong>Every programme moved the same way.</strong> Compared with version 5's default (\\(k = 5\\), \\(m = 0.75\\), cycles of 10%), the chosen settings have a larger \\(k\\) ({kmin} to {kmax}), the tightest stop the leverage and the limits below allow, and cycles of 20&ndash;30% of the account. Over the thirteen programmes in the plan, one 100K account each, the value rises from {usd(d5)} to {usd(ch)} a month ({sgn(ch - d5)}, {pct(ch / d5 - 1, 0)}), measured on paths that played no part in the choice.</p>",
           "<p><strong>Why.</strong> Three effects, each derived in Part I, point the same way:</p><ol>"
           "<li><em>Cost per trade falls with a wider target</em> (bold play, 5.6): the pass probability is \\((B - \\mathbb{E}[\\text{cost}])/(A+B)\\) exactly, and the fewest trades means the least cost. A 1 : 30 bracket reaches the target in one win; a 1 : 5 bracket needs two or three wins and more losses in between.</li>"
           "<li><em>Time falls with a tighter stop</em> (8.2): the market time of a phase is \\((A/l)(B/l)m^2\\) hours, so halving \\(m\\) quarters it. The cost per trade rises like \\(1/m\\), which the large \\(k\\) offsets.</li>"
           "<li><em>Fewer, larger payouts</em> (7.3): a funded account pays its allowance \\(\\alpha D\\) on average whatever the cycle; larger cycles mean fewer trades (less cost) and fewer payout dates to wait for.</li></ol>",
           f"<p><strong>Where it stops: the plan's limits.</strong> Left free, the search keeps going toward \\(k = 50\\), cycles of 40&ndash;50% and stops of 0.25. The plan stops at a stop of 0.35, a cycle of 30% and \\(k = 30\\), for reasons the model cannot price:</p><ul>"
           f"<li><em>Stop of at least 0.35 hourly moves</em> (30 Nasdaq points, 6.6 USDJPY pips, $4.1 on gold). The cost \\(\\kappa\\) is an average of measured spreads and commissions. Real spreads widen several-fold at the daily break, at the open and around news, and a stop a few spreads from the price is hit by the widening alone. The engine does not model this, and its effect grows as the stop tightens. For FTMO the uncapped setting ({sett(ftu)}) is worth {usd(ftu['EV_month'])} a month on the fresh paths and {usd(ftr['EV_month'])} on the real history, against {usd(ft['EV_month'])} and {usd(ftcr['EV_month'])} for the plan's. The difference is real in the model and is given up deliberately.</li>"
           "<li><em>Cycle of at most 30% of the account.</em> A $40,000&ndash;$50,000 payout on a $100,000 account after one trade invites a review of the kind every firm reserves the right to make. Beyond 30% the measured gains are within the noise for most programmes.</li>"
           "<li><em>\\(k\\) of at most 30.</em> With cycles of at most 30% and a 1.5% risk, a win of \\(k\\,l\\) already reaches every target at \\(k \\approx 27\\). Larger \\(k\\) changes nothing but the order size on paper.</li></ul>",
           f"<p><strong>Robustness to costs.</strong> The cost check (Chapter 31) asks what each setting is worth if real costs are 1.5 or 2 times the assumption. Two accounts trade the dearer currency markets and were checked at neighbouring stops. FundingPips on USDJPY: at \\(m = 0.35\\) {usd(fpc(0.35, 1.0))}, {usd(fpc(0.35, 1.5))} and {usd(fpc(0.35, 2.0))} a month at 1, 1.5 and 2 times the cost; at the search's own choice \\(m = 0.5\\) {usd(fpc(0.5, 1.0))}, {usd(fpc(0.5, 1.5))} and {usd(fpc(0.5, 2.0))}; at 0.75 {usd(fpc(0.75, 1.0))}, {usd(fpc(0.75, 1.5))}, {usd(fpc(0.75, 2.0))}. The search's choice is already the robust one. FundedNext on EURUSD: at the search's choice \\(m = 0.75\\) {usd(fnc(0.75, 1.0))}, {usd(fnc(0.75, 1.5))}, {usd(fnc(0.75, 2.0))}; at \\(m = 1.0\\) {usd(fnc(1.0, 1.0))}, {usd(fnc(1.0, 1.5))}, {usd(fnc(1.0, 2.0))}. A small loss at the assumed cost buys protection against losing the whole account's value, so the plan uses \\(m = 1.0\\) for FundedNext and reports its figures from new paths 33&ndash;36.</p>",
           f"<p><strong>Large gains, large noise.</strong> Near the optimum the value per month is flat: many settings sit within each other's 95% intervals. The k-curve of 5.6 shows the shape: {kcurve_txt}. The ranking near the top is not reliable, but the direction is: {beat_txt}</p>"]
    return "".join(out)

def lev_table():
    rows = []
    for p, ins in PLAN_PROGS + [("FTMO 1-Step", "US100")]:
        ch = fin(p, ins); lev = lev_of(p, ins)
        if not ch or not lev: continue
        T = trade_numbers(ins, ch["m"], ch["L"], ch["k"] * ch["L"], lev=lev, size=ch["size"])
        rows.append([f"{short(p)}", MSHORT[ins], f"1:{lev}", f"{T['m_min']:.3f}", f"{ch['m']:g}", usd(T["N"]), pct(T["margin_pct"], 0)])
    return table(["Programme", "Market", "Leverage", "\\(m_{\\min}\\)", "Plan's \\(m\\)", "Notional per 100K", "Margin / balance"], rows, cls="small",
                 cap="Leverage as published by each firm on 4 October 2026 (optimize_v6.LEV). \\(m_{\\min} = (l/S)/(0.6\\lambda\\sigma)\\) is the smallest stop whose margin fits in 60% of the balance at 1.5% risk. "
                     "FundingPips gives 1:5 on indices and metals above half a lot (dynamic leverage), so its accounts trade USDJPY. The plan's stop is the larger of \\(m_{\\min}\\), 0.35 and the searched optimum.")

def risk_sens():
    rs = sorted(sens("risk"), key=lambda r: r["L"])
    rows = [[pct(r["L"] / 100_000, 2), pm(r["EV_month"], r["CI"]), usd(r["EV"]), pct(r["P"]), f"{r['days']:.1f}"] for r in rs]
    return (table(["Risk per trade", "EV per month (95%)", "Value of an attempt", "Pass rate", "Days per attempt"], rows, cls="small",
                  cap=f"FTMO 2-Step 100K at the plan's k = {rs[0]['k']}, m = {rs[0]['m']:g}, cycle {rs[0]['X'] / 1000:.0f}K, fresh paths 29&ndash;32, 12,000 attempts per row.") +
            "<p>Within the noise of 12,000 attempts the value per month barely moves with the risk between 1% and 2%. The theory says why: risk changes the <em>market</em> time of a phase (8.2), but at these stops the market time is a few hours, and the calendar (minimum days, reviews, payout dates) is what an attempt is waiting for. There is nothing here worth breaking a firm's guidance for. The plan keeps 1.5%.</p>")

def chk():
    z = VER["zero_cost_ftmo"]; Z = {x["name"]: x for x in EXTRA["zero"]}
    b = Z["FTMO phase 1, bold setting"]; t5a = Z["The5ers phase 1 with profitable days"]; t5b = Z["The5ers phase 1 without profitable days"]
    d = {r["rule"]: r for r in sens("dir")}
    tb = json.load(open("tie_v0/tie_check_before.json"))
    bt = {b["k"]: b for b in VER.get("brackets_tight", [])}
    fz = VER.get("fp_phase2_zero", {})
    tie = dict(TIE_BEFORE=" and ".join(f"{b['meanR']:+.3f} &plusmn; {b['ci']:.3f} R at k = {b['k']}" for b in tb["brackets_m035"]),
               TIE_FP_BEFORE=f"{pct(tb['fp_phase2_zero']['with_daily_limit'], 1)} &plusmn; {pct(tb['fp_phase2_zero']['ci'], 1)}",
               TIE_AFTER=" and ".join(f"{bt[k]['meanR']:+.3f} &plusmn; {bt[k]['ci']:.3f} R at k = {k}" for k in (2, 3) if k in bt),
               TIE_FP_AFTER=f"{pct(fz.get('P', 0), 1)} &plusmn; {pct(fz.get('ci', 0), 1)}",
               CHK_TIGHT=" / ".join(f"{pct(bt[k]['win'], 2)}" for k in (1, 2, 3, 6) if k in bt),
               CHK_TIGHT_TH=" / ".join(f"{pct(1 / (1 + k), 2)}" for k in (1, 2, 3, 6)))
    b0 = {b["k"]: b for b in VER["brackets"]}
    tie.update(CHK_W1=pct(b0[1]["win"], 2), CHK_W2=pct(b0[2]["win"], 2), CHK_R3=f"{b0[3]['meanR']:+.3f} &plusmn; {b0[3]['ci']:.3f}")
    return dict(**tie, CHK_P1_ZERO=f"{pct(z['P1'], 2)} &plusmn; {pct(z['P1_ci'], 2)}", CHK_W_ZERO=f"{usd(z['W'])} &plusmn; {usd(z['W_ci'])}",
                CHK_BOLD_ZERO=f"{pct(b['P'], 2)} &plusmn; {pct(b['ci'], 2)}", CHK_T5_ZERO=f"{pct(t5a['P'], 1)} / {pct(t5b['P'], 1)} (&plusmn; {pct(t5a['ci'], 1)})",
                CHK_DIR=f"{pct(d['trend5']['P'], 1)} / {pct(d['random']['P'], 1)}; {usd(d['trend5']['EV_month'])} / {usd(d['random']['EV_month'])} a month",
                THE5ERS_P1=f"{pct(t5a['P'], 1)} &plusmn; {pct(t5a['ci'], 1)} with costs removed")

def verify_table():
    rows = []
    for p, ins in PLAN_PROGS + OTHER_PROGS:
        v = ver(p, ins)
        if not v: continue
        rows.append([f"{short(p)}, {MSHORT[ins]}", f"{v['k']} / {v['m']:g}", f"{v['P_formula']:.3f}", f"{v['P_exact']:.3f}", f"{v['P_engine']:.3f}",
                     usd(v["cash_exact"]), usd(v["cash_engine"]), sgn(v["EV_exact"]), sgn(v["EV_engine"])])
    return table(["Programme", "k / m", "P Brownian (5.2)", "P exact chain (5.6)", "P engine", "Funded cash, chain", "Funded cash, engine", "Attempt value, chain", "Attempt value, engine"],
                 rows, cls="small", num_from=1,
                 cap="Chain and Brownian columns: analytic_v6.py, written separately from the engine; they leave out daily limits, minimum and profitable days, payout dates, weekends, gaps and overnight financing. Engine: the final run on fresh paths (24,000 attempts; pass rates &plusmn;0.006).")

def verify_text():
    rows = [ver(p, i) for p, i in PLAN_PROGS if ver(p, i)]
    dP = np.array([r["P_exact"] - r["P_engine"] for r in rows]); dC = np.array([1 - r["cash_engine"] / r["cash_exact"] for r in rows])
    one = ver("FTMO 1-Step", "US100"); dl = VER["dll_ftmo"]
    nf = {r["tag"]: r for r in sens("nofin") + sens("fin") if r["prog"] == FT}
    return (f"<p><strong>Pass probabilities.</strong> For the thirteen programmes in the plan, the exact chain is above the engine by {pct(dP.mean(), 1)} on average (range {pct(dP.min(), 1)} to {pct(dP.max(), 1)}). "
            "The gap is what the chain leaves out, and each part has a known sign: overnight financing on winners held through the night (always a cost), trades cut at the Friday close or the daily window (fair, but each extra trade costs \\(c\\)), the profitable-day and best-day rules that keep the balance exposed longer, and the rare gap through a daily loss limit. "
            f"The Brownian formula is too high for bold settings (it undercounts trades) and accurate for small \\(k\\). The one large gap is FTMO 1-Step ({one['P_exact']:.3f} against {one['P_engine']:.3f}): its maximum loss trails the best end-of-day balance, which the chain (a static floor) does not model. That is also why the 1-Step is worth less.</p>"
            f"<p><strong>Funded cash.</strong> The engine pays {pct(dC.mean(), 0)} less than the chain on average. Most of it is financing. FTMO with financing switched off is worth {usd(nf['nofin']['EV_month'])} a month against {usd(nf['fin']['EV_month'])} with it. The daily loss limit, also left out of the chain, costs a little value and more time: in an engine experiment without it, an FTMO attempt is worth {usd(dl['without']['EV'])} against {usd(dl['with']['EV'])} with it, but {usd(dl['without']['EV_month'])} a month against {usd(dl['with']['EV_month'])}, because stopping for the day after two or three losses stretches the calendar.</p>"
            "<p><strong>Conclusion.</strong> Two independent programs, one a rule-by-rule simulation on price paths and the other a set of exact equations on the trade-level chain, agree on every programme to within the effects the equations leave out, and those effects have the expected signs. Every reported value comes from the engine, the more conservative of the two.</p>")

def fills():
    d = dict(SIGMA_TABLE=sigma_table(), SIG_DAY=sig_day(), COST_TABLE=cost_table(), TRADE_EXAMPLE=trade_example(), PHASE_EXAMPLE=phase_example(),
             BOLD_EXAMPLE=bold_example(), FUNDED_EXAMPLE=funded_example(), TIME_EXAMPLE=time_example(), N_GRID=n_grid(), N_GRID_ATTEMPTS=n_grid_attempts(),
             N_REFINE=n_refine(), N_REFINE_ATTEMPTS=n_refine_attempts(), CURSE=curse(), OPT_GENERAL=opt_general(), OPT_TABLE=opt_table(),
             LEV_TABLE=lev_table(), RISK_SENS=risk_sens(), VERIFY_TABLE=verify_table(), VERIFY_TEXT=verify_text())
    d.update(chk())
    return d
