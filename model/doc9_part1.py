"""Part I of the version 9 document: the computed tables and worked examples that fill the chapter templates."""
import math, collections, json, copy, re
import numpy as np
from doc9_common import *

FT = "FTMO 2-Step"
MARKETS = ["US100", "USDJPY", "EURUSD", "XAUUSD", "MNQ_fut"]

def short(prog):
    return (prog.replace("2-Step Prime (bi-weekly 80%)", "2-Step Prime").replace("Two Phase Classic", "Classic").replace("Stellar 2-Step", "Stellar")
            .replace("2-Step Classic", "Classic").replace("2-Step Standard", "Standard").replace("High Stakes Classic", "HS Classic").replace("High Stakes", "HS"))
def xpct(x): return pct(x, 1 if round(x * 1000) % 10 else 0)       # a payout target: 20%, or 4.9%
def sett(r): return f"{pct(r['L'] / r['size'], 2 if (r['L'] / r['size'] * 1000) % 5 else 1)} / {r['k']:g} / {r['m']:g} / {xpct(r['X'] / r['size'])}" if r.get("kind", "cfd") == "cfd" else f"{usd(r['L'])} / {r['k']:g} / {r['m']:g}"
def _calc(lines): return '<div class="calc">' + "".join(f"<p>{x}</p>" for x in lines if x) + "</div>"

def chosen_rows():
    return [r for r in FIN if r["tag"] == "chosen"]

def sigma_table():
    rows = []
    for mk in MARKETS:
        sg = SIG[mk]; h = hours(mk)
        daily = sg * math.sqrt(23 if mk not in ("USDJPY", "EURUSD") else 24)
        rows.append([MNAME[mk], f"{PRICE[mk]:,.4g}" if PRICE[mk] < 10 else f"{PRICE[mk]:,.2f}", pct(sg, 4), pct(daily, 2),
                     pct(kappa(mk), 4), f"{kappa(mk) / sg:.3f}", f"{h[0]:02d}&ndash;{min(h[1], 18):02d}" if h else "00&ndash;18"])
    return table(["Market", "Price, 2 Oct 2026", "Hourly &sigma;", "Daily &sigma;", "Round-trip cost &kappa;", "&kappa;/&sigma;", "Entry hours used (UTC)"], rows, cls="small",
                 cap="&sigma;: standard deviation of hourly log returns on 2024&ndash;26 data (sigma_v32.json); daily = hourly &times; &radic;23 (indices, gold) or &radic;24 (currencies). "
                     "&kappa;: spread + commission + slippage allowance as a fraction of the notional, per round trip (calibrate.py). &kappa;/&sigma; is the cost of one hourly standard deviation of movement. "
                     "Entry hours: the market's hours, cut at 19:00 UTC by the daily flat (no entry from 19:00, everything closed at 20:00).")

def sig_day(): return pct(SIG["US100"] * math.sqrt(23), 2)

def cost_table():
    rows = []
    for mk in MARKETS[:4]:
        sg = SIG[mk]
        rows.append([MNAME[mk]] + [pct(kappa(mk) / (m * sg), 2) for m in (0.6, 0.75, 1.0, 1.25)] + [pct(2 * kappa(mk) / (m * sg), 2) for m in (0.6, 1.0)])
    return table(["Market", "\\(\\rho\\) at m = 0.6", "0.75", "1.0", "1.25", "at cost &times; 2, m = 0.6", "m = 1.0"], rows, cls="small",
                 cap="The round-trip cost in units of the risk, \\(\\rho = c/l = \\kappa/(m\\sigma)\\), for stops of \\(m\\) hourly standard deviations. "
                     "The plan holds nothing through a daily reset, so there is no financing to add (version 6 paid up to 16% of the risk per night held at a tight Nasdaq stop).")

def dll_table():
    """each firm's daily loss limit as published (rules_snapshot_v9.json) and how the engine applies it"""
    rows = [["FTMO", "balance at the reset", "00:00 Prague (22:00/23:00 UTC)", "5% of the initial balance", "fixed"],
            ["FundingPips", "higher of the day's opening balance and equity", "platform midnight, UTC+3 (21:00 UTC)", "4% of that level", "relative"],
            ["The5ers", "higher of the previous day's closing balance and equity", "00:00 server time", "5% of that level ($5,500 at $110,000)", "relative"],
            ["FXIFY", "previous day's balance", "17:00 New York", "4% of that balance", "relative"],
            ["FundedNext", "the day's starting balance", "00:00 server time", "5% of the initial balance", "fixed"],
            ["Fintokei", "equity at the start of the day", "00:00 server time", "5% of that equity", "relative"],
            ["Hola Prime", "previous day's closing balance", "17:00 New York", "5% of that balance", "relative"],
            ["Alpha Capital", "the day's starting balance (close of the daily candle)", "00:00 broker time", "5% of that balance", "relative"],
            ["GFT", "higher of balance and equity", "17:00 New York", "5% of that level", "relative"],
            ["FunderPro", "the day's starting balance (balance-based)", "00:00 GMT+3", "5%; base not stated", "the stricter of the two"],
            ["BrightFunded", "higher of balance and equity at rollover", "rollover, Prague time", "5% of the original size", "fixed"],
            ["Blue Guardian", "higher of balance and equity", "17:00 New York", "4% of the initial balance", "fixed"],
            ["Maven", "higher of equity and balance", "00:00 UTC", "4% of that level (4% of $1,100 in its example)", "relative"]]
    return table(["Firm", "Reference fixed at the reset", "Reset", "Allowance", "Engine"], rows, cls="small", num_from=9,
                 cap="As published (4 October 2026; rules_snapshot_v9.json quotes the pages). Engine: 'fixed' subtracts a share of the initial balance from the reference; "
                     "'relative' a share of the day's reference itself, recomputed at every reset (version 7 used 'fixed' everywhere but Fintokei). Every reset falls between 20:00 UTC and 00:00 UTC, while the plan holds no position, so balance and equity are equal whenever a reference is fixed.")

def _first_win(F, r, phase=0):
    st = F["phases"][phase]; A = st["target"]
    caps = [r["k"] * r["L"], A]
    if st.get("conc"): caps.append(st["conc"] * A)
    if st.get("max_win"): caps.append(st["max_win"])
    if st.get("profit_days"): caps.append(max(1.1 * st["profit_days"][1], A / st["profit_days"][0]))
    return min(caps)

def funded_win(F, r):
    """the largest win the engine allows on the funded account at the start of a cycle: k L, the cycle target, the plan's 40%,
    the firm's best-day share, its day cap and Maven's ceiling, never below the minimum target distance"""
    fd = F["funded"]; X = r["X1"]
    caps = [r["k"] * r["L"], X]
    if fd.get("conc"): caps.append(fd["conc"] * X)
    if fd.get("best"): caps.append(fd["best"] * X)
    if fd.get("day_profit_cap"): caps.append(fd["day_profit_cap"])
    if fd.get("profit_ceiling"): caps.append(fd["profit_ceiling"])
    return min(caps)

def risk_for(F, r, w, funded=True):
    """the risk the engine uses for a win w: Maven's minimum reward:risk lowers it to w / 1.5"""
    st = F["funded"] if funded else F["phases"][0]
    mr = st.get("min_rr")
    return min(r["L"], w / mr) if mr and w < mr * r["L"] else r["L"]

def trade_example():
    c = fin(FT, "US100"); m, k, L = c["m"], c["k"], c["L"]
    F = rules_of(c); A = F["phases"][0]["target"]
    w1 = _first_win(F, c)
    lev = lev_of(FT, "US100")
    T1 = trade_numbers("US100", m, L, w1, lev=lev)
    wf = funded_win(F, c)
    Tf = trade_numbers("US100", m, L, wf, lev=lev)
    out = [f"<p>The plan's FTMO setting is risk \\(L = \\${L:,.0f}\\) ({pct(L / 1e5, 2)} of $100,000), a stop of \\(m = {m:g}\\) hourly standard deviations, \\(k = {k:g}\\) and a payout target of {usd(c['X'])}. "
           f"The first trade of phase 1 aims at \\(w = \\min(k\\,L,\\ A,\\ 0.4A) = \\min(\\${k * L:,.0f},\\ \\${A:,.0f},\\ \\${0.4 * A:,.0f}) = \\${w1:,.0f}\\). With the Nasdaq at {PRICE['US100']:,.0f}:</p>"]
    out.append(_calc([
        f"Stop distance: \\(s = m\\sigma = {m:g} \\times {SIG['US100'] * 100:.4f}\\% = {T1['s'] * 100:.4f}\\%\\) of the price, i.e. \\({T1['stop_pts']:.1f}\\) index points.",
        f"Notional: \\(N = l/s = \\${T1['N']:,.0f}\\), i.e. \\(\\${T1['usd_per_pt']:.2f}\\) per index point. One lot is $1 per point (contract size 1, 10.1), so \\({T1['lots']:.3f}\\) lots, rounded <em>down</em> to \\({T1['vol']:.2f}\\): the risk actually taken is \\(\\${T1['l_round']:,.2f}\\) (the engine trades the rounded volume; below, the unrounded figures keep the algebra readable).",
        f"Cost: \\(c = \\kappa N = {kappa('US100') * 100:.4f}\\% \\times \\${T1['N']:,.0f} = \\${T1['c']:.2f}\\), so \\(\\rho = c/l = {T1['rho'] * 100:.2f}\\%\\).",
        f"Target: \\(u = s(w+c)/l = {T1['s'] * 100:.4f}\\% \\times {w1 + T1['c']:,.2f}/{L:,.0f} = {T1['u'] * 100:.4f}\\%\\), i.e. \\({T1['tgt_pts']:.1f}\\) points from the entry.",
        f"Win probability: \\(p = l/(l+w+c) = {L:,.0f}/({L:,.0f} + {w1:,.0f} + {T1['c']:.2f}) = {T1['p']:.4f}\\).",
        f"Mean \\(-c = -\\${T1['c']:.2f}\\); check: \\(p\\,w - (1-p)(l+c) = {T1['p'] * w1 - (1 - T1['p']) * (L + T1['c']):.2f}\\). Variance \\(l(w+c) = {T1['var']:,.0f}\\), standard deviation \\(\\${T1['sd']:,.0f}\\).",
        f"Margin at 1:{T1['lev']}: \\(N/{T1['lev']} = \\${T1['margin']:,.0f}\\) = {pct(T1['margin_pct'])} of the starting balance; the engine re-checks it against the current balance at every entry (10.2)." if lev else "",
        f"Duration (8.1, approximate): \\(m^2 (w+c)/l = {T1['dur']:.2f}\\) hours of open market on average; losers \\({T1['dur_loss']:.2f}\\) h, winners \\({T1['dur_win']:.2f}\\) h. A trade still open at 20:00 UTC is closed there.",
    ]))
    out.append(f"<p>On the funded account (payout target {usd(c['X'])}) a full win is \\(\\min(k\\,L, X, 0.4X) = \\${wf:,.0f}\\): take-profit {Tf['tgt_pts']:,.0f} points away, \\(p = {Tf['p']:.4f}\\), winners {Tf['dur_win']:.1f} hours of open market on average, so some are cut by the daily flat and some wait for the next day's cap. "
               f"No take-profit is ever closer than 0.6 hourly standard deviations ({0.6 * SIG['US100'] * PRICE['US100']:.0f} points): a target closer than that is reached a little past it.</p>")
    return "".join(out)

def _row_steps(A, B, L, k, rho, cap, bs=1.0, lmin=None):
    rows, P = AN.bold_path(A, B, L, k, rho, cap=cap, buf=100.0 * bs, lmin=lmin, n=12)
    body = [[str(r["j"] + 1), usd(r["x"]), usd(r["l"]), usd(r["c"], 2), usd(r["w"]), f"{r['p']:.4f}", "yes" if r["terminal"] else "no"] for r in rows]
    return table(["Trade \\(j\\) on the all-loss path", "Balance \\(x_j\\)", "Risk \\(l_j\\)", "Cost \\(c_j\\)", "Win \\(w_j\\)", "\\(p_j\\)", "A win ends the phase?"],
                 body, cls="small steps", num_from=1), P

def phase_example():
    c = fin(FT, "US100"); m, k, L = c["m"], c["k"], c["L"]
    e = chain_of(c); F = rules_of(c)
    ph1, ph2 = e["phases"]
    rho = e["rho"]
    tb, _ = _row_steps(10_000, 10_000, L, k, rho, 0.4 * 10_000)
    tr_c = rho * L; v = L * (min(k * L, 4000) + tr_c)
    Pbm1 = AN.hit_bm(10_000, 10_000, tr_c, v)
    out = [f"<p><strong>FTMO phase 1</strong> (\\(A = B = \\$10{{,}}000\\), buffer $100) at the plan's setting (risk {usd(L)}, \\(k = {k:g}\\), \\(m = {m:g}\\), \\(\\rho = {rho * 100:.2f}\\%\\)). "
           f"No win can exceed \\(0.4A = \\$4{{,}}000\\), so no single win ends the phase from the start; the first trades along the all-loss path:</p>", tb,
           _calc([f"Chain (5.5): \\(P_1 = {ph1['P']:.4f}\\), \\(\\mathbb{{E}}[\\text{{trades}}] = {ph1['N']:.2f}\\), \\(K(0) = \\${ph1['Ecost']:,.0f}\\), \\(\\mathbb{{E}}[X_\\text{{end}}\\mid\\text{{fail}}] = {td(ph1['X_fail'])}\\).",
                  f"Identity: \\(P_1\\,\\mathbb{{E}}[X_\\text{{end}}\\mid\\text{{pass}}] + (1-P_1)(-B) = {ph1['P']:.4f}\\times{ph1['X_succ']:,.0f} - {1 - ph1['P']:.4f}\\times10{{,}}000 = {ph1['T']:,.2f} = -K(0)\\) (gap {ph1['identity_gap']:+.4f}); the mean balance at a pass is {usd(ph1['X_succ'])}, above \\(A\\) by the $20 filler margin and the small overshoot of minimum-distance targets.",
                  f"Exact form \\(P = (B - K)/(\\mathbb{{E}}[X_\\text{{end}}\\mid\\text{{pass}}] + B) = {ph1['P_identity']:.4f}\\); the textbook form \\((B - K)/(A + B) = {ph1['P_textbook']:.4f}\\) (with \\(A\\) the target the engine trades to, the firm's target plus the $20 filler margin of 6.3) is {(ph1['P_textbook'] - ph1['P']) * 100:.2f} percentage points higher, because a pass ends a little above \\(A\\). Every failure ends exactly at \\(-B\\) under the terminal rule (5.4).",
                  f"Brownian approximation (5.2) with a constant full-size trade: \\(P_1 \\approx {Pbm1:.4f}\\).",
                  f"Phase 2 (\\(A = \\$5{{,}}000\\), wins capped at $2,000): \\(P_2 = {ph2['P']:.4f}\\), {ph2['N']:.2f} trades, \\(K = \\${ph2['Ecost']:,.0f}\\). Both: \\(P = {e['P']:.4f}\\) (chain)."]),
           (f"<p><strong>The engine</strong> (with the daily limit, the daily flat, minimum days, the per-day concentration cap and weekends), on sixteen fresh paths: \\(P = {c['P']:.4f} \\pm {p_ci(c):.4f}\\) (cluster-robust, 8.4). "
            + (f"With those rules switched off (11.2) it gives {ver(FT, 'US100')['P_simpl']:.4f} &plusmn; {ver(FT, 'US100')['P_simpl_ci']:.4f}, against the chain's {ver(FT, 'US100')['P_chain']:.4f}." if ver(FT, "US100") else "") + "</p>")]
    return "".join(out)

def textbook_diff():
    d = []
    for r in chosen_rows():
        if r.get("kind") == "fut": continue
        e = chain_of(r)
        d += [p["P_textbook"] - p["P"] for p in e["phases"]]
    return f"{100 * min(d):.2f} to {100 * max(d):.2f} percentage points" if d else "&ndash;"

def bold_example():
    """what the concentration policy costs: the chain at FTMO's chosen stop and risk, with and without the 40% cap"""
    c = fin(FT, "US100"); m, L = c["m"], c["L"]
    F0 = rules_of(c); F1 = copy.deepcopy(F0)
    for st in F1["phases"]: st["conc"] = None
    F1["funded"]["conc"] = None
    rows = []
    for k in (1.5, 2, 3, 4, 6, 8, 12, 20, 30):
        a = AN.programme(FT, "US100", m, k, c["X1"], c["X"], L=L, F=F0); b = AN.programme(FT, "US100", m, k, c["X1"], c["X"], L=L, F=F1)
        rows.append([f"{k:g}", f"{a['phases'][0]['N']:.1f}", f"{a['P']:.4f}", sgn(a["EV"]), f"{b['phases'][0]['N']:.1f}", f"{b['P']:.4f}", sgn(b["EV"])])
    tb = table(["\\(k\\)", "Phase 1 trades, 40% cap", "\\(P\\), 40% cap", "Attempt value, 40% cap", "Phase 1 trades, no cap", "\\(P\\), no cap", "Attempt value, no cap"],
               rows, cls="small", cap=f"Exact chain, FTMO 2-Step 100K at the plan's stop m = {m:g}, risk {usd(L)} and payout target {usd(c['X'])}. Without the cap the value keeps rising with \\(k\\) toward bold play; with it, \\(k\\) beyond the cap changes nothing.")
    cs = [r for r in sens("conc") if r["prog"] == FT]
    eng = ""
    if cs:
        d = {r["tweak"]: r for r in cs}
        base = c
        eng = (f"<p>In the engine, at the plan's setting: {pm(base['EV_month'], base['CI'])} a month with the 40% policy, "
               + (f"{pm(d['conc0.6']['EV_month'], d['conc0.6']['CI'])} with a 60% cap" if "conc0.6" in d else "")
               + (f" and {pm(d['conc_none']['EV_month'], d['conc_none']['CI'])} with no cap at the same \\(k\\) (paths 141&ndash;144). Version 6's uncapped FTMO setting (k = 20, m = 0.5, X = 30%) was worth {usd(fin6(FT, 'US100')['EV_month'])} a month in its own final run." if "conc_none" in d and fin6(FT, "US100") else "") + "</p>")
    return tb + eng

def funded_example():
    c = fin(FT, "US100"); F = rules_of(c); fd = F["funded"]; D = fd["dd"]; a = fd["split"]; R = fd["refund"]
    e = chain_of(c); X = c["X"]
    q1, q = e["q1"], e["q"] if e["q"] is not None else e["q1"]
    n = sum(e["pr"])
    rows = []
    for j in range(0, 5):
        pj = (1 - e["pr"][0]) if j == 0 else e["pr"][j - 1] - e["pr"][j]
        rows.append([str(j), f"{pj:.4f}", usd(e["cash_given"][j]), usd(a * sum(e["cyc"][:j]) + (R if j >= 1 else 0))])
    return ("<p>FTMO's funded account at the plan's setting: allowance \\(D = \\${:,.0f}\\) (static), payout target \\(X = \\${:,.0f}\\), wins capped at \\(0.4X = \\${:,.0f}\\), split {:.0%}, refund \\(R = \\${:,.2f}\\) with the first payout.</p>".format(D, X, 0.4 * X, a, R) +
            _calc([f"One cycle is the chain of 5.5 from 0 to \\(X\\): \\(q = {q1:.4f}\\), with \\({e['trades_funded'] / max(1 + n, 1):.1f}\\) trades per cycle on average.",
                   f"\\(\\mathbb{{E}}[\\text{{paid cycles}}] = q/(1-q) = {n:.4f}\\); \\(\\mathbb{{E}}[W] = m\\,q/(1-q) = \\${e['withdrawn']:,.0f}\\), where a paid cycle withdraws its balance at success, on average \\(m = \\${e['m1']:,.2f}\\) rather than \\(X = \\${X:,.0f}\\) (the minimum-distance overshoot, 7.2).",
                   f"General identity (7.1): \\(-\\mathbb{{E}}[X_\\text{{end}}] - \\mathbb{{E}}[\\text{{cost}}] = {-e['x_end']:,.0f} - {e['cost_funded']:,.0f} = \\${-e['x_end'] - e['cost_funded']:,.0f}\\) (gap {e['identity_gap']:+.2f}). "
                   f"Under the terminal rule every account ends at the floor, so \\(\\mathbb{{E}}[X_\\text{{end}}] = -D\\) and the static form \\(D - \\mathbb{{E}}[\\text{{cost}}]\\) holds again; no profit is forfeited under the plan (\\(Q = 0\\)).",
                   f"\\(\\mathbb{{E}}[C] = \\alpha\\,\\mathbb{{E}}[W] + R\\,q = {a:g}\\times{e['withdrawn']:,.0f} + {R:,.2f}\\times{q1:.4f} = \\${e['cash_funded']:,.0f}\\) (chain)."]) +
            table(["Paid cycles", "Probability", "Mean cash given that many (split + refund)", "Nominal (targets only)"], rows, cls="small", num_from=1,
                  cap=f"Chain values, in the chain's model of independent cycles that each start from zero. A paid cycle pays its balance at success, on average {usd(e['m1'])} in the first cycle and {usd(e['m'] or e['m1'])} in later ones (\\(m_1, m\\) of 7.2), not exactly the target; the last column, the targets alone, is shown only for comparison (version 8 printed it as the cash). The cash of a funded account is lumpy: many pay nothing, a few pay several cycles.") +
            (f"<p>The engine, on fresh paths, pays {usd(c['Vf'])} per funded account (the chain with the daily rules switched off in the engine: {usd(ver(FT, 'US100')['cash_simpl'])} &plusmn; {usd(ver(FT, 'US100')['cash_simpl_ci'])}).</p>" if ver(FT, "US100") else ""))

def time_example():
    c = fin(FT, "US100"); F = rules_of(c)
    s = [r for r in sens("cost", FT, "US100") if r["cost_mult"] == 1.0]
    att = DAYS_MONTH / c["days"]
    lines = [f"Engine, sixteen fresh paths: an attempt lasts \\(\\mathbb{{E}}[T] = {c['days']:.2f}\\) days on average, from the purchase to the failed phase or the closed funded account.",
             f"So one slot buys \\(30.44/{c['days']:.2f} = {att:.2f}\\) evaluations a month and pays \\({att:.2f}\\times\\${F['fee']:,.2f} = \\${att * F['fee']:,.0f}\\) a month in fees before refunds.",
             f"Value of an attempt: \\(\\mathbb{{E}}[V] = \\${c['EV']:,.0f}\\); pass rate {pct(c['P'])}; cash per funded account {usd(c['Vf'])}.",
             f"Random-start ratio (8.3): \\(30.44 \\times {c['EV']:,.0f} / {c['days']:.2f} = \\${c['EV_month']:,.0f}\\) per month, &plusmn; {usd(c['CI'])} (95%, cluster-robust over 16 paths; attempt-level &plusmn; {usd(c['CI_iid'])}).",
             (f"Continuing slot (8.3: one slot run back to back for eight years after a year's warm-up, 12 slots on each of 16 new paths): <strong>{usd(cont(c)['rate'])}</strong> &plusmn; {usd(cont(c)['CI'])} a month, the long-run rate this slot is valued at in Part II." if cont(c) else "")]
    if s:
        s = s[0]
        lines.append(f"Where the time goes (paths 141&ndash;144): an attempt that fails in the evaluation lasts {s['t_eval_fail']:.1f} days on average; one that passes spends {s['t_eval_pass']:.1f} days in the evaluation and {s['t_fund']:.1f} days funded, with {s['payouts']:.2f} payouts on average; {s['trades']:.1f} trades per attempt.")
    return _calc(lines)

def n_grid(): return f"{len(GRID):,}"
def n_grid_attempts(): return f"{len(GRID) * 2000 / 1e6:,.1f} million"
def n_refine(): return f"{len(REF):,}"
def n_refine_attempts(): return f"{len(REF) * 16000 / 1e6:,.1f} million"

def curse():
    d = []
    for r in chosen_rows():
        if r.get("kind") == "fut": continue
        rs = [x for x in REF if x["prog"] == r["prog"] and x["instr"] == r["instr"] and abs(x["m"] - r["m"]) < 1e-9 and x["k"] == r["k"]
              and abs(x["X"] - r["X"]) < 1 and abs(x["L"] - r["L"]) < 1]
        if rs and rs[0]["EV_month"] > 0: d.append((rs[0]["EV_month"] - r["EV_month"]) / rs[0]["EV_month"])
    return pct(float(np.mean(d)), 0) if d else "&ndash;"

def opt_table():
    rows = []; hl = []
    plan = {(s_["firm"], s_["instr"]) for s_ in LOCK.get("slots", {}).get("Recommended: A + B + one account at each tier-D firm", [])}
    for r in sorted([r for r in chosen_rows() if r.get("kind") != "fut"], key=lambda r: (firm_of(r["prog"]), -r["EV_month"])):
        v8 = fin8(r["prog"], r["instr"]); ct = cont(r)
        if (r["prog"], r["instr"]) in plan: hl.append(len(rows))
        rows.append([f"{short(r['prog'])}, {MSHORT[r['instr']]}", sett(r), pm(r["EV_month"], r["CI"]), (pm(ct["rate"], ct["CI"]) if ct else "&ndash;"),
                     f"{pct(r['P'], 1)} &plusmn; {pct(p_ci(r), 1)}", f"{r['days']:.1f}", (f"{usd(v8['EV_month'])}" if v8 else "&ndash;")])
    return table(["Programme, market", "Chosen L / k / m / X", "Random-start EV/month (95%)", "Continuing slot (95%)", "Pass rate (95%)", "Days per attempt", "Version 8"],
                 rows, cls="small", hl=hl,
                 cap="One 100K account. Random-start: sixteen fresh paths (121&ndash;136), 24,000 attempts each, the ratio of 8.3 used by the search; continuing slot: 12 slots run back to back on each of 16 new paths (151&ndash;166), years 2&ndash;9, Part II's long-run rate (8.3). 95% intervals: the larger of the attempt-level and the cluster-robust interval (Student t, 15 degrees of freedom), for the pass rate too (8.4). L: risk per trade; X: payout target, both as a share of the account. "
                     "Shaded: in the recommended plan. Version 8: its chosen setting's random-start value under version 8's engine (no lots, the floor clipped after a trade, calendar fillers, Fintokei fillers, calendar-day reviews, Hola Prime's days counted per cycle, Fintokei's clock from the request); not a measure of the same thing.")

def risk_text(ch):
    """how many chosen settings sit at the risk ceiling, and for the others the best refined value at the ceiling"""
    def ceil_of(r): return O.L_MAX.get(firm_of(r["prog"]), 0.0175)
    top = [r for r in ch if r["L"] / r["size"] >= ceil_of(r) - 1e-9]; low = [r for r in ch if r not in top]
    t = (f"<p><strong>Risk per trade.</strong> With wins capped at 40% of the target, a larger risk mainly makes the account move faster (market time \\(\\propto 1/L^2\\), 8.2) at almost the same pass probability, "
         f"which favours the largest risk the plan allows: 1.75%, set by the firms' 2% rules, and 1.5% at FTMO (10.5). {len(top)} of {len(ch)} chosen settings use that ceiling.")
    if low:
        parts = []
        for r in low:
            alt = [x for x in REF if x["prog"] == r["prog"] and x["instr"] == r["instr"] and abs(x["L"] / x["size"] - ceil_of(r)) < 1e-9]
            b = max(alt, key=lambda x: x["EV_month"]) if alt else None
            rr = [x for x in REF if x["prog"] == r["prog"] and x["instr"] == r["instr"] and abs(x["m"] - r["m"]) < 1e-9 and x["k"] == r["k"]
                  and abs(x["X"] - r["X"]) < 1 and abs(x["L"] - r["L"]) < 1]
            pd_ = paired_diff(rr[0], b) if b and rr else None
            parts.append(f"{short(r['prog'])} on {MSHORT[r['instr']]} at {pct(r['L'] / r['size'], 2)}"
                         + (f" ({pm(rr[0]['EV_month'], rr[0]['CI'])} in the refinement, against {pm(b['EV_month'], b['CI'])} for the best setting at {pct(ceil_of(r), 2)}"
                            + (f"; paired difference on the same four paths and seeds {sgn(pd_[0])} &plusmn; {usd(pd_[1])}" if pd_ else "") + ")" if b and rr else ""))
        t += (" The others chose a smaller risk because a lower setting measured higher on the refinement paths: " + "; ".join(parts)
              + ". The settings of one programme are run on the same paths and random numbers, so the paired difference (Student t, 3 degrees of freedom) is the test of a choice, "
                "not whether the separate intervals overlap; a paired interval that includes zero means the refinement cannot tell the two apart.")
    return t + "</p>"

def opt_general():
    ch = [r for r in chosen_rows() if r.get("kind") != "fut"]
    Ls = collections.Counter(round(r["L"] / r["size"], 4) for r in ch); ks = [r["k"] for r in ch]; ms = [r["m"] for r in ch]; xs = [r["X"] / r["size"] for r in ch]
    neg = [r for r in ch if r["EV_month"] - r["CI"] <= 0]
    out = [f"<p><strong>The policy moves the optimum.</strong> Under the 40% cap no win can end a phase, so the version 6 corner (k of 20&ndash;30, one trade per phase) is gone. "
           f"The chosen settings use risk {', '.join(f'{pct(l, 2)} ({n})' for l, n in sorted(Ls.items()))}, \\(k\\) from {min(ks):g} to {max(ks):g}, stops from {min(ms):g} to {max(ms):g} and payout targets from {xpct(min(xs))} to {xpct(max(xs))} of the account.</p>",
           risk_text(ch),
           (f"<p><strong>Payout targets.</strong> {sum(1 for x in xs if x >= 0.299)} of {len(xs)} chosen settings use the plan's ceiling of 30% of the account (one payout of more than 30% invites review); "
            "a larger target means fewer payout dates to wait for and, under the 40% cap, larger wins per trade, against more funded trades (7.3). Firms with payout caps or ceilings (GFT, Maven) are held below them.</p>")]
    if neg:
        out.append("<p><strong>Not worth it under the policy:</strong> " + "; ".join(f"{short(r['prog'])} on {MSHORT[r['instr']]} ({pm(r['EV_month'], r['CI'])})" for r in neg) + ". Their interval reaches zero or below; they are left out of the plan.</p>")
    return "".join(out)

def lev_table():
    rows = []
    for r in sorted([r for r in chosen_rows() if r.get("kind") != "fut"], key=lambda r: firm_of(r["prog"])):
        lv = lev_of(r["prog"], r["instr"])
        if not lv: continue
        T = trade_numbers(r["instr"], r["m"], r["L"], r["L"], lev=O.lev_tuple(firm_of(r["prog"]), r["instr"]), size=r["size"])
        rows.append([short(r["prog"]), MSHORT[r["instr"]], f"1:{lv[0]} / 1:{lv[1]}" + (f" (20% cap)" if lv[2] < 0.6 else ""), pct(r["L"] / r["size"], 2),
                     f"{mmin_of(r['prog'], r['instr'], r['L'] / r['size']):.3f}", f"{r['m']:g}", usd(T["N"]), pct(T["margin_pct"], 0)])
    return table(["Programme", "Market", "Leverage: evaluation / funded", "Risk", "\\(m_{\\min}\\)", "Plan's \\(m\\)", "Notional per 100K", "Funded margin / start balance"], rows, cls="small",
                 cap="Leverage as published on 4 October 2026 (optimize_v9.LEV). \\(m_{\\min}\\): the smallest stop whose margin fits 60% of the starting balance at both leverages (FunderPro funded: 20%). "
                     "At every entry the engine also requires margin at most 60% of the current balance, lowering the risk if needed.")

def risk_sens():
    rs = sorted(sens("risk"), key=lambda r: r["L"])
    if not rs: return ""
    rows = [[pct(r["L"] / 100_000, 2), pm(r["EV_month"], r["CI"]), usd(r["EV"]), pct(r["P"]), f"{r['days']:.1f}"] for r in rs]
    return table(["Risk per trade", "EV per month (95%)", "Value of an attempt", "Pass rate", "Days per attempt"], rows, cls="small",
                 cap=f"FTMO 2-Step 100K at the plan's k = {rs[0]['k']:g}, m = {rs[0]['m']:g}, payout target {rs[0]['X'] / 1000:.0f}K, paths 141&ndash;144, 12,000 attempts per row, same random numbers in every row. 2% is shown for reference only.")

def _tests():
    try: return json.load(open("tests_v9.json"))
    except FileNotFoundError: return {}

PF_WMIN = 0.6           # pathfirm.WMIN_SD

def duration_summary():
    """trades that may have lasted under 2 minutes, average duration and share of gross profit from short trades, over the
    final runs of every chosen programme (one-minute sub-steps; a trade counts as short if its exit minute is at most 2)"""
    rows = [r for r in chosen_rows() if r.get("kind") != "fut" and r.get("st")]
    if not rows: return None
    n = sum(r["st"]["n"] for r in rows); sh = sum(r["st"]["short"] for r in rows)
    worst = max(rows, key=lambda r: r["st"]["short"] / max(r["st"]["n"], 1))
    avg_min = min(r["st"]["minutes"] / max(r["st"]["n"], 1) for r in rows)
    gshare = max(r["st"]["gross_win_short"] / max(r["st"]["gross_win"], 1e-9) for r in rows)
    eps = max(r["st"]["bridge_eps"] / max(r["st"]["n"], 1) for r in rows)
    late = sum(r["st"]["late"] for r in rows) / max(n, 1)
    # the exact chance that a bracket of the chosen setting closes within 2 minutes, driftless Brownian motion (6, 3.3):
    # stop m hourly sd away, take-profit at the minimum distance (the closest the plan allows) or at k m
    th = []
    for r in rows:
        th.append((r, two_barrier_exit(r["m"], PF_WMIN, 2.0 / 60.0), two_barrier_exit(r["m"], r["k"] * r["m"], 2.0 / 60.0)))
    eps_tot = sum(r["st"]["bridge_eps"] for r in rows)
    return dict(n=n, short=sh, frac=sh / max(n, 1), worst=worst, worst_frac=worst["st"]["short"] / max(worst["st"]["n"], 1),
                min_avg_minutes=avg_min, max_short_profit_share=gshare, eps=eps, eps_tot=eps_tot, late=late,
                th_min=min(x[1] for x in th), th_max=max(x[1] for x in th), th_full_max=max(x[2] for x in th),
                sub2=sum(r["st"].get("sub2", 0) for r in rows))

def checks():
    out = {}
    B = {(b["k"], b["m"]): b for b in VER.get("brackets", [])}
    if B:
        out["CHK_W_TH"] = " / ".join(pct(B[(k, 1.0)]["theory"], 1) for k in (1, 2, 3, 6))
        out["CHK_W"] = " / ".join(pct(B[(k, 1.0)]["win"], 1) for k in (1, 2, 3, 6))
        out["CHK_WT_TH"] = " / ".join(pct(B[(k, 0.6)]["theory"], 1) for k in (1, 2, 3, 6))
        out["CHK_WT"] = " / ".join(pct(B[(k, 0.6)]["win"], 1) for k in (1, 2, 3, 6))
        b3 = B[(3, 1.0)]
        out["CHK_R3_TH"] = f"{b3['mean_theory']:+.4f}"; out["CHK_R3"] = f"{b3['meanR']:+.4f} &plusmn; {b3['ci']:.4f}"
    T = {(t_["k"], t_["sub"]): t_ for t_ in VER.get("ties", [])}
    if T:
        ks = sorted({k for k, _ in T}); subs = sorted({s_ for _, s_ in T})
        out["TIE_TH"] = " / ".join(pct(1 / (1 + k), 2) for k in ks)
        for sb in subs: out[f"TIE_{sb}"] = " / ".join(f"{pct(T[(k, sb)]['win'], 2)}" for k in ks)
        cells = [(k, sb, (T[(k, sb)]["win"] - 1 / (1 + k)) * 100, max(T[(k, sb)]["ci"], T[(k, sb)]["ci_cluster"]) * 100) for k in ks for sb in subs]
        outside = [c for c in cells if abs(c[2]) > c[3]]
        out["TIE_TEXT"] = ("<p><strong>Sub-step convergence.</strong> At the tightest stop the plan allows (0.6 hourly standard deviations), cost-free brackets on six independent "
                           "two-year paths per cell (120,000 each) win at rates that differ from \\(1/(1+k)\\) by "
                           + "; ".join(f"k = {k}: " + ", ".join(f"{d:+.2f} &plusmn; {ci:.2f} points at {sb}" for kk2, sb, d, ci in cells if kk2 == k) for k in ks)
                           + " sub-steps per hour (the larger of the binomial and the cluster interval). "
                           + (f"{len(outside)} of {len(cells)} cells lie outside their interval. " if outside else f"Every cell lies inside its interval. ")
                           + "These intervals say how far each estimate can be from the truth under the model; they are not a bound on the generator's error, which is the bound of 3.3 below. "
                           "Version 7's claim of a quarter-point bound did not follow from its own cells and is withdrawn.</p>")
        out["TIE_RESULT"] = "; ".join(f"k = {k}: " + ", ".join(f"{d:+.2f} &plusmn; {ci:.2f}" for kk2, sb, d, ci in cells if kk2 == k) + " points at " + "/".join(str(x) for x in subs) for k in ks)
    ds = duration_summary()
    if ds:
        out["BRIDGE_BOUND"] = (f"at most {ds['eps']:.1e} per trade in the programme where it is largest, and {ds['eps_tot']:.1e} summed over all {ds['n']:,.0f} trades of every chosen programme's final run ({ds['sub2']:,.0f} watched sub-steps)"
                               if ds["eps"] > 0 else "below 1e-300 per trade (numerically zero) over every chosen programme's final run")
        out["SHORT_RESULT"] = (f"Exact chance (driftless Brownian motion) that a bracket of a chosen setting closes within 2 minutes: {ds['th_min'] * 100:.3f}% to {ds['th_max'] * 100:.3f}% with the take-profit at the minimum distance, at most {ds['th_full_max'] * 100:.4f}% at the full k m. "
                               f"Measured in the final runs: {ds['short']:,.0f} of {ds['n']:,.0f} trades ({ds['frac'] * 100:.3f}%) may have closed within 2 minutes (the most in one programme: {ds['worst_frac'] * 100:.3f}%, {short(ds['worst']['prog'])}); "
                               f"the shortest programme average is {ds['min_avg_minutes']:.0f} minutes, and at most {ds['max_short_profit_share'] * 100:.3f}% of any programme's gross profit came from such trades. These are observations, not a guarantee; the firms with duration rules are handled by 7 and 11.")
        out["CHK_SHORT_TH"] = f"{ds['th_min'] * 100:.2f}&ndash;{ds['th_max'] * 100:.2f}% (at 0.6 sd)"
        out["CHK_SHORT"] = f"{ds['frac'] * 100:.3f}% of trades &lt; 2 min"
        out["CHK_BRIDGE"] = f"&le; {ds['eps']:.0e} per trade" if ds["eps"] > 0 else "&lt; 1e-300 per trade"
    tv = _tests()
    if tv:
        out["CHK_TESTS"] = f"{sum(1 for v in tv.values() if v['ok'])} of {len(tv)} pass"
        g = tv.get("gap_rule", {}).get("info", "")
        out["GAP_RESULT"] = g
    z = VER.get("zero")
    if z:
        out["Z_P1_TH"] = pct(z["P1_chain"], 2); out["Z_P1"] = f"{pct(z['P1'], 2)} &plusmn; {pct(z['P1_ci'], 2)}"
        out["Z_W_TH"] = usd(z["W_chain"]); out["Z_W"] = f"{usd(z['W'])} &plusmn; {usd(z['W_ci'])}"
    sc = VER.get("scale")
    if sc:
        dbl = [x for x in sc if x.get("fee") == "double"]; real = [x for x in sc if x.get("fee") == "real"]
        flat = {"The5ers High Stakes": "its $150 minimum payout is a flat amount", "GFT 2-Step Standard": "its $3,000 day cap and $10,000 payout cap are flat amounts",
                "Fintokei ProTrader": "its $100 minimum payout is a flat amount"}
        out["SCALE_TEST"] = "fee doubled: " + ", ".join(f"{x['prog'].split()[0]} {sgn(x.get('diff', 0.0))} &plusmn; {usd(x.get('diff_ci', 0.0))}" for x in dbl)
        txt = ("<p><strong>The scaling test, twice.</strong> <em>Rules:</em> with the 200K fee set to twice the 100K fee, half a 200K attempt against the matching 100K attempt, path by path on the same seeds (1,500 pairs each): "
               + "; ".join(f"{x['prog'].split()[0]} {sgn(x.get('diff', 0.0))} &plusmn; {usd(x.get('diff_ci', 0.0))} per attempt ({x['mismatches']:,} of {x['n']:,} pairs differ by more than a cent)" for x in dbl)
               + ". Since version 9 the two are equal only up to rounding: volumes are whole 0.01-lot steps (two 100K positions rounded separately are not one 200K position rounded once), and a filler trade is 0.01 lot at either size; a rounding difference changes a trade's result by cents and can move an attempt's path from there on, so individual pairs can differ by a whole outcome while the means agree. "
               + " ".join(f"{x['prog'].split()[0]} also has a rule that does not scale: {flat.get(x['prog'], 'a rule is a flat amount')}." for x in dbl if x["prog"] in flat)
               + " <em>Contracts:</em> with the firms' real 200K fees, "
               + "; ".join(f"{x['prog'].split()[0]} {usd(x['v200_half'])} per 100K at 200K against {usd(x['v100'])} at 100K (fee {usd(x['fee200'], 2)} against 2 &times; {usd(x['fee100'], 2)})" for x in real if x["prog"] in O.HAS200)
               + "".join(f" ({x['prog'].split()[0]} sells no 200K account of this programme, so its 200K row checks the rules only.)" for x in real if x["prog"] not in O.HAS200)
               + " The fee difference is the whole of the gap where the rules scale; [[CH_ALLOC]].2 values it.</p>")
        out["SCALE_TEXT"] = txt; out["SCALE_RESULT"] = re.sub(r"<[^>]+>", "", txt)
    mv = VER.get("maven")
    if mv:
        out["MAVEN_TH"] = f"{usd(mv['paid_chain'], 2)}; {pct(mv['q1_chain'], 1)}"
        out["MAVEN_ENG"] = f"{usd(mv['paid'], 2)} &plusmn; {usd(mv['paid_ci'], 2)}; {pct(mv['q1'], 1)} &plusmn; {pct(mv['q1_ci'], 1)}"
        out["MAVEN_RESULT"] = (f"At the chosen setting the engine (the chain's rules, 24 paths, {mv['n']:,} funded accounts, {mv['n_pay']:,} payouts) pays {usd(mv['paid'], 2)} &plusmn; {usd(mv['paid_ci'], 2)} per successful cycle "
                               f"against the chain's {usd(mv['paid_chain'], 2)}, and the first cycle succeeds in {pct(mv['q1'], 1)} &plusmn; {pct(mv['q1_ci'], 1)} against {pct(mv['q1_chain'], 1)}.")
    cr = [(r, cont(r)) for r in chosen_rows() if cont(r)]
    if cr:
        z = [(c_["rate"] - r["EV_month"]) / math.sqrt(c_["CI"] ** 2 + r["CI"] ** 2) * 1.96 for r, c_ in cr]
        out["CONT_N"] = str(len(cr))
        out["CONT_INSIDE"] = str(sum(abs(x) <= 1.96 for x in z))
        out["CONT_ZMAX"] = f"{max(z, key=abs):+.1f}"
    gaps = []
    for r in chosen_rows():
        if r.get("kind") == "fut": continue
        e = chain_of(r)
        gaps += [abs(p["identity_gap"]) for p in e["phases"]] + [abs(e["identity_gap"])]
    out["GAP_MAX"] = usd(max(gaps), 4) if gaps else "&ndash;"
    d = {r["rule"]: r for r in sens("dir")}
    out["DIR_TEXT"] = ""
    if d:
        b = {r["rule"]: r for r in sens("dirbr")}
        out["CHK_DIR"] = (f"per trade {b['trend5']['meanR']:+.4f} / {b['random']['meanR']:+.4f} R (&plusmn;{b['random']['ci']:.3f})" if b else
                          f"{usd(d['trend5']['EV_month'])} / {usd(d['random']['EV_month'])}")
        out["DIR_TEXT"] = (f"<p><strong>The direction rule.</strong> Per trade (cost-free 1 : 3 brackets on the Nasdaq, {b['trend5']['n']:,} each), the plan's momentum rule averages {b['trend5']['meanR']:+.4f} &plusmn; {b['trend5']['ci']:.4f} R and a coin flip {b['random']['meanR']:+.4f} &plusmn; {b['random']['ci']:.4f} R. "
                           f"Per month (FTMO, 48,000 attempts each on paths 141&ndash;144) the momentum rule gives {pm(d['trend5']['EV_month'], d['trend5']['CI'])} and the coin flip {pm(d['random']['EV_month'], d['random']['CI'])}. "
                           "The momentum rule's interval is wider because attempts that overlap on one path take the same direction at the same time, so they are correlated. "
                           "Under the model no rule that uses only past prices can have an edge (2.3); the plan uses the momentum rule only so that all of one person's accounts take the same side.</p>") if b else ""
    return out

def verify_table():
    rows = []
    for v in VER.get("programmes", []):
        rows.append([f"{short(v['prog'])}, {MSHORT[v['instr']]}", f"{v['P_chain']:.3f}", f"{v['P_simpl']:.3f} &plusmn; {v['P_simpl_ci']:.3f}", f"{v['P_full']:.3f}",
                     usd(v["cash_chain"]), f"{usd(v['cash_simpl'])} &plusmn; {usd(v['cash_simpl_ci'])}", usd(v["cash_full"])])
    return table(["Programme", "P: chain", "P: engine, chain's rules", "P: engine, all rules", "Funded cash: chain", "engine, chain's rules", "engine, all rules"],
                 rows, cls="small tight", num_from=1, w0="24%",
                 cap="Chain: analytic_v9.py. Engine with the chain's rules: the same engine with the daily loss limit, minimum and profitable days and the daily flat switched off, the concentration caps applied per trade, and payouts only at the payout target; it stays flat at weekends, because a position held through a weekend gaps and a gap is not in the chain. "
                     "24 independent two-year paths &times; 500 attempts, intervals cluster-robust over paths (Student t, 23 degrees of freedom). Engine with all rules: the final run. The middle columns test the implementation; the gap between them and the last columns is what the daily rules do.")

def verify_text():
    vs = VER.get("programmes", [])
    if not vs: return ""
    z = [(v["P_simpl"] - v["P_chain"]) / max(v["P_simpl_ci"], 1e-9) for v in vs]
    zc = [(v["cash_simpl"] - v["cash_chain"]) / max(v["cash_simpl_ci"], 1e-9) for v in vs]
    inside = sum(abs(x) <= 1 for x in z); insidec = sum(abs(x) <= 1 for x in zc)
    dfull = [v["EV_full"] - v["EV_simpl"] for v in vs]
    return (f"<p><strong>Implementation.</strong> With the chain's rules, the engine's pass rate is within its 95% interval of the chain's in {inside} of {len(vs)} programmes and its funded cash in {insidec} of {len(vs)}; "
            f"the largest standardised differences are {max(z, key=abs):+.1f} and {max(zc, key=abs):+.1f} intervals. Remaining differences come from Monte Carlo noise and from what the engine still does that the chain does not: it closes positions at the Friday close (a fair outcome between stop and target, which the binary chain does not have), and the chain is solved on a grid. They go both ways, so neither is 'the conservative one'.</p>"
            f"<p><strong>What the daily rules do.</strong> Switching the daily rules back on changes the value of an attempt by {sgn(min(dfull))} to {sgn(max(dfull))} across programmes. These are the effects the formulas of Part I do not contain; every reported figure comes from the engine with every rule on.</p>")

def fills():
    d = dict(SIGMA_TABLE=sigma_table(), SIG_DAY=sig_day(), COST_TABLE=cost_table(), DLL_TABLE=dll_table(), TRADE_EXAMPLE=trade_example(),
             PHASE_EXAMPLE=phase_example(), TEXTBOOK_DIFF=textbook_diff(), BOLD_EXAMPLE=bold_example(), FUNDED_EXAMPLE=funded_example(),
             TIME_EXAMPLE=time_example(), N_GRID=n_grid(), N_GRID_ATTEMPTS=n_grid_attempts(), N_REFINE=n_refine(), N_REFINE_ATTEMPTS=n_refine_attempts(),
             CURSE=curse(), OPT_GENERAL=opt_general(), OPT_TABLE=opt_table(), LEV_TABLE=lev_table(), RISK_SENS=risk_sens(),
             VERIFY_TABLE=verify_table(), VERIFY_TEXT=verify_text())
    d.update(checks())
    return d
