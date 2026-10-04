"""Part II of the version 6 document: one chapter per programme, every number derived at the chosen setting."""
import math
import numpy as np
from doc6_common import *
from doc6_part1 import short, sett, _calc, _steps_table

# per-person allocation, firm by firm (firms' terms as checked on 4 October 2026; Part III uses the same table)
ALLOC = {
    "FTMO": dict(cap="$400,000 per trader across all accounts, evaluations included", copy="your own accounts, within the cap",
                 rec=[("FTMO 2-Step", "US100", 100_000, 4)], full=[("FTMO 2-Step", "US100", 100_000, 4)],
                 why="4 &times; 100K or 2 &times; 200K (the same value, Chapter [[CH_ALLOC]])"),
    "FundingPips": dict(cap="$400,000 across evaluation, funded and Prime accounts", copy="your own FundingPips accounts; no copier services",
                        rec=[("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY", 100_000, 4)], full=[("FundingPips 2-Step Flex (85%) v6 cap", "USDJPY", 100_000, 4)],
                        why="Flex goes up to 100K, so four accounts"),
    "The5ers": dict(cap="one 100K (or 50K) High Stakes account, plus 1 &times; 25K, 3 &times; 10K, 3 &times; 5K, 3 &times; 2.5K", copy="your own accounts",
                    rec=[("The5ers High Stakes Classic", "US100", 100_000, 1)],
                    full=[("The5ers High Stakes Classic", "US100", 100_000, 1), ("The5ers High Stakes 25K", "US100", 25_000, 1), ("The5ers High Stakes 10K", "US100", 10_000, 3),
                          ("The5ers High Stakes 5K", "US100", 5_000, 3), ("The5ers High Stakes 2.5K", "US100", 2_500, 3)],
                    why="the small accounts add about 2% for ten more accounts; optional"),
    "FXIFY": dict(cap="one active account of each size ($805,000 in all)", copy="between your own FXIFY accounts; Pro may not receive copied trades",
                  rec=[("FXIFY Two Phase Classic (100%, 30 days)", "US100", s, 1) for s in (100_000, 50_000, 25_000, 10_000, 5_000)],
                  full=[("FXIFY Two Phase Classic (100%, 30 days)", "US100", s, 1) for s in (100_000, 50_000, 25_000, 10_000, 5_000)],
                  why="every Classic size with a published price; 15K and the 2 Phase Pro sizes are left out (Chapter [[CH_ALLOC]])"),
    "FundedNext": dict(cap="$300,000 funded; evaluations unlimited", copy="between your own challenge accounts, never into a funded account",
                       rec=[("FundedNext Stellar 2-Step v5", "EURUSD", 200_000, 1)], full=[("FundedNext Stellar 2-Step v5", "EURUSD", 200_000, 1)],
                       why="one 200K account on its own market; a second account would need a third independent market"),
    "Fintokei": dict(cap="&euro;500,000 of accounts", copy="your own trades across your own accounts",
                     rec=[("Fintokei ProTrader", "US100", 100_000, 5)], full=[("Fintokei ProTrader", "US100", 100_000, 5)],
                     why="5 &times; 100K = $500,000 &asymp; &euro;444,000"),
    "Hola Prime": dict(cap="$500,000", copy="only between your own Hola Prime accounts (funded: one master and one copier); never from other firms",
                       rec=[("Hola Prime 2-Step Prime (bi-weekly 80%)", "XAUUSD", 100_000, 2)], full=[("Hola Prime 2-Step Prime (bi-weekly 80%)", "XAUUSD", 100_000, 2)],
                       why="a master and a copier on gold; more accounts would need more independent markets"),
    "Alpha Capital": dict(cap="$400,000 per household, $300,000 per strategy", copy="from your own external accounts with proof",
                          rec=[("Alpha Capital Pro 10%", "US100", 200_000, 1)], full=[("Alpha Capital Pro 10%", "US100", 200_000, 1), ("Alpha Capital Pro 10%", "US100", 100_000, 1)],
                          why="one 200K (recommended); 200K + 100K reaches the $300,000 strategy cap"),
    "FunderPro": dict(cap="$200,000", copy="no replicating trades across FunderPro accounts", rec=[("FunderPro Classic v5", "US100", 200_000, 1)],
                      full=[("FunderPro Classic v5", "US100", 200_000, 1)], why="one account, so the largest size"),
    "GFT": dict(cap="$400,000 funded", copy="no duplicated trades or trade ideas between GFT accounts", rec=[("GFT 2-Step Standard v5", "US100", 200_000, 1)],
                full=[("GFT 2-Step Standard v5", "US100", 200_000, 1)], why="one account, so the largest size"),
    "BrightFunded": dict(cap="$400,000 funded; evaluations unlimited", copy="allowed between your own accounts", rec=[("BrightFunded 2-Step Classic v5", "US100", 100_000, 1)],
                         full=[("BrightFunded 2-Step Classic v5", "US100", 100_000, 4)], why="one account (recommended, tier D) or four"),
    "Blue Guardian": dict(cap="$400,000; evaluations up to $200,000 each", copy="your own accounts only", rec=[("Blue Guardian 2-Step v5", "US100", 100_000, 1)],
                          full=[("Blue Guardian 2-Step v5", "US100", 100_000, 4)], why="one account (recommended, tier D) or four"),
    "Maven": dict(cap="$200,000; payouts at most $10,000 per 30 days per person", copy="&ndash;", rec=[("Maven 2-Step", "US100", 100_000, 1)],
                  full=[("Maven 2-Step", "US100", 100_000, 1)], why="the payout cap binds before the account cap"),
    "Topstep": dict(cap="5 Express Funded Accounts at once", copy="your own accounts", rec=[], full=[("Topstep 50K", "MNQ_fut", 50_000, 5)], why="optional futures layer"),
    "Apex": dict(cap="20 funded accounts", copy="your own accounts", rec=[], full=[("Apex 50K EOD", "MNQ_fut", 50_000, 20)], why="optional, only at 80&ndash;90% off"),
}

def acct_row(prog, instr, size):
    """the final-run row for an account of this size (the chosen setting, scaled)"""
    if size == 100_000: return fin(prog, instr)
    for tg in ("200K", "50K", "25K", "10K", "5K", "2K"):
        r = fin(prog, instr, tg, size=size)
        if r: return r
    return fin(prog, instr, size=size)

def alloc_value(lst):
    tot = 0.0; n = 0
    for p, i, s, k in lst:
        r = acct_row(p, i, s); tot += k * r["EV_month"]; n += k
    return tot, n

SPECS = [
    dict(sheet="FTMO 2-Step", prog="FTMO 2-Step", instr="US100", firm="FTMO", alts=[("FTMO 1-Step", "US100", "FTMO 1-Step (one phase, trailing loss, 90%)")]),
    dict(sheet="FundingPips Flex", prog="FundingPips 2-Step Flex (85%) v6 cap", instr="USDJPY", firm="FundingPips",
         alts=[("FundingPips 2-Step Flex (85%) v6 4days", "USDJPY", "85%, concentration policy accepted (4 profitable days per cycle)"),
               ("FundingPips 2-Step Flex (95%) v5", "USDJPY", "95% option (3 profitable days per phase and cycle)")],
         excluded=[("FundingPips 2-Step Flex (85%) v5", "USDJPY", "85%, no cap on single trades: breaks the Profit Concentration Policy's conditions on new evaluations"),
                   ("FundingPips 2-Step (bi-weekly 80%)", "USDJPY", "2-Step Standard: rules last checked in version 3")]),
    dict(sheet="The5ers High Stakes", prog="The5ers High Stakes Classic", instr="US100", firm="The5ers",
         alts=[("The5ers High Stakes", "US100", "High Stakes New (10% / 5%, $491)")]),
    dict(sheet="FXIFY Two Phase Classic", prog="FXIFY Two Phase Classic (100%, 30 days)", instr="US100", firm="FXIFY",
         alts=[("FXIFY Two Phase Classic (80%)", "US100", "80% every 14 days, Nasdaq"), ("FXIFY Two Phase Classic (100%, 30 days)", "USDJPY", "100% every 30 days, USDJPY"),
               ("FXIFY Two Phase Classic (80%)", "USDJPY", "80% every 14 days, USDJPY")]),
    dict(sheet="FundedNext Stellar 2-Step", prog="FundedNext Stellar 2-Step v5", instr="EURUSD", firm="FundedNext",
         alts=[("FundedNext Stellar 2-Step v5", "XAUUSD", "on gold (taken by Hola Prime in the plan)")]),
    dict(sheet="Fintokei ProTrader", prog="Fintokei ProTrader", instr="US100", firm="Fintokei", alts=[]),
    dict(sheet="Hola Prime 2-Step Prime", prog="Hola Prime 2-Step Prime (bi-weekly 80%)", instr="XAUUSD", firm="Hola Prime",
         alts=[("Hola Prime 2-Step Prime (bi-weekly 80%)", "EURUSD", "on EURUSD (taken by FundedNext in the plan)")]),
    dict(sheet="Alpha Capital Pro 10%", prog="Alpha Capital Pro 10%", instr="US100", firm="Alpha Capital",
         alts=[("Alpha Capital Pro 10% (on-demand)", "US100", "on-demand payouts (40% best-day rule)")]),
    dict(sheet="FunderPro Classic", prog="FunderPro Classic v5", instr="US100", firm="FunderPro", alts=[]),
    dict(sheet="GFT 2-Step Standard", prog="GFT 2-Step Standard v5", instr="US100", firm="GFT", alts=[]),
    dict(sheet="BrightFunded 2-Step Classic", prog="BrightFunded 2-Step Classic v5", instr="US100", firm="BrightFunded", alts=[]),
    dict(sheet="Blue Guardian 2-Step", prog="Blue Guardian 2-Step v5", instr="US100", firm="Blue Guardian", alts=[]),
    dict(sheet="Maven 2-Step", prog="Maven 2-Step", instr="US100", firm="Maven", alts=[]),
    dict(sheet="Topstep 50K", prog="Topstep 50K", instr="MNQ_fut", firm="Topstep", fut=True, alts=[]),
    dict(sheet="Apex 50K EOD", prog="Apex 50K EOD", instr="MNQ_fut", firm="Apex", fut=True, alts=[]),
]

# ------------------------------------------------------------------ pieces
def rules_table(sh):
    return table(["Rule", "As published (checked 4 October 2026)"], [[a, b] for a, b in sh["rules"]], num_from=9, w0="30%")

def model_table(F, prog):
    rows = [["Fee per attempt", usd(F["fee"], 2 if F["fee"] % 1 else 0) + (" a month (renewed while the evaluation lasts)" if F.get("monthly") else "") +
             (f"; activation {usd(F['activation'])} on passing" if F.get("activation") else "")]]
    for j, st in enumerate(F.get("phases", [])):
        bits = [f"target {usd(st['target'])}", f"maximum loss {usd(st['dd'])} below the start, " + ("trailing the best end-of-day balance" if st["eod"] else "static")]
        bits.append(f"daily loss {usd(st['dll'])}" if st.get("dll") else "no daily loss limit")
        if st.get("min_days"): bits.append(f"at least {st['min_days']} trading days")
        if st.get("profit_days"): bits.append(f"{st['profit_days'][0]} profitable days of at least {usd(st['profit_days'][1])}")
        if st.get("best"): bits.append(f"best day at most {pct(st['best'], 0)} of the profit")
        if st.get("max_win"): bits.append(f"one trade may make at most {usd(st['max_win'])} ({pct(st['max_win'] / st['target'], 0)} of the target)")
        if st.get("lock") is not None: bits.append(f"trailing loss locks at {usd(st['lock'])}")
        rows.append([f"Phase {j + 1}" if len(F["phases"]) > 1 else "Evaluation", "; ".join(bits)])
    fd = F["funded"]
    bits = [f"maximum loss {usd(fd['dd'])}, " + ("trailing the best end-of-day balance" if fd["eod"] else "static"),
            f"daily loss {usd(fd['dll'])}" if fd.get("dll") else "no daily loss limit", f"split {pct(fd['split'], 0)}"]
    if fd.get("refund"):
        if fd.get("refund_split"): bits.append(f"fee returned in {fd['refund_split']} equal parts with the first {fd['refund_split']} payouts")
        else: bits.append(f"fee refunded with payout number {fd.get('refund_after', 1)}")
    else: bits.append("no fee refund")
    if fd.get("q_days"): bits.append(f"a payout needs {fd['q_days']} qualifying days of at least {usd(fd['q_min'])}")
    elif fd.get("ondemand"): bits.append("payouts on demand")
    else: bits.append(f"first payout {fd['first_payout']} days after funding, then every {fd['cycle']} days")
    if fd.get("min_payout"): bits.append(f"minimum payout {usd(fd['min_payout'])}")
    if fd.get("caps"): bits.append("first payouts capped at " + ", ".join(usd(c) for c in fd["caps"][:2] if c < 1e9))
    if fd.get("pct_bal"): bits.append(f"a payout at most {pct(fd['pct_bal'], 0)} of the balance")
    if fd.get("best"): bits.append(f"best day at most {pct(fd['best'], 0)} of a payout's profit")
    if fd.get("day_profit_cap"): bits.append(f"profit above {usd(fd['day_profit_cap'])} a day not counted")
    if fd.get("profit_days"): bits.append(f"{fd['profit_days'][0]} profitable days of {usd(fd['profit_days'][1])}+ per cycle")
    if fd.get("max_payouts"): bits.append(f"at most {fd['max_payouts']} payouts")
    if fd.get("buffer"): bits.append(f"buffer {usd(fd['buffer'])} kept in the account")
    bits.append("flat at weekends" if fd.get("flat_weekend") else "weekend holding allowed")
    rows.append(["Funded account", "; ".join(bits)])
    if F.get("flat_daily"): rows.append(["Trading hours", f"flat by {F['flat_daily']}:00 UTC every day"])
    return table(["Part", "What the engine simulates"], rows, num_from=9, w0="22%")

def heat(prog, instr, m):
    rs = [r for r in refs(prog, instr) if abs(r["m"] - m) < 1e-9]
    if not rs: return ""
    ks = sorted({r["k"] for r in rs}); xs = sorted({round(r["X"] / r["size"], 2) for r in rs})
    cell = {}
    for r in rs: cell[(r["k"], round(r["X"] / r["size"], 2))] = max(cell.get((r["k"], round(r["X"] / r["size"], 2)), -1e9), r["EV_month"])
    vals = list(cell.values()); lo, hi = min(vals), max(vals)
    ch = fin(prog, instr)
    head = "<tr><th>k \\ X</th>" + "".join(f'<th class="n">{x:.0%}</th>' for x in xs) + "</tr>"
    body = ""
    for k in ks:
        tds = ""
        for x in xs:
            v = cell.get((k, x))
            if v is None: tds += '<td class="n" style="color:#b0b6c0">&middot;</td>'; continue
            a = 0.08 + 0.5 * (v - lo) / max(hi - lo, 1)
            mark = ch and ch["k"] == k and abs(ch["X"] / ch["size"] - x) < 1e-6 and abs(ch["m"] - m) < 1e-9
            st = f"background:rgba(42,120,214,{a:.2f});" + ("outline:1.4pt solid #15191f;outline-offset:-1.4pt;font-weight:700;" if mark else "")
            tds += f'<td class="n" style="{st}">{v / 1000:.2f}</td>'
        body += f"<tr><td class='n' style='text-align:left'>{k}</td>{tds}</tr>"
    return (f'<table class="heat"><thead>{head}</thead><tbody>{body}</tbody></table>'
            f'<p class="cap">Refined value per month ($ thousands, 24,000 attempts on paths 25&ndash;28, &plusmn;0.2&ndash;0.6) at the stop m = {m:g}, by k (rows) and cycle target X as a share of the account (columns). '
            f'Darker is more. The outlined cell is the plan\'s setting. Dots: not tried at this stop.</p>')

def search_section(sp, ch):
    prog, instr = sp["prog"], sp["instr"]
    instrs = sorted({r["instr"] for r in REF if r["prog"] == prog})
    ng = sum(1 for r in GRID if r["prog"] == prog); nr = sum(1 for r in REF if r["prog"] == prog)
    allr = sorted(refs(prog, instr), key=lambda r: -r["EV_month"])
    rs = [r for r in allr if O.admissible(r)][:7] + [r for r in allr if not O.admissible(r)][:3]
    rows = []; hl = []
    for i, r in enumerate(rs):
        ok = O.admissible(r)
        if ch and (r["m"], r["k"], round(r["X"])) == (ch["m"], ch["k"], round(ch["X"])): hl.append(i)
        rows.append([str(r["k"]), f"{r['m']:g}", pct(r["X"] / r["size"], 0), pm(r["EV_month"], r["CI"]), pct(r["P"]), f"{r['days']:.1f}",
                     r.get("tag", "") or "", "yes" if ok else "no"])
    out = [f"<p>Searched: {ng} grid settings ({', '.join(MSHORT[i] for i in instrs)}; 4,000 attempts each) and {nr} refined settings (24,000 attempts each). The seven best refined settings on {MSHORT[instr]} within the plan's limits (stop at least 0.35, cycle at most 30%, k at most 30), then the three best outside them:</p>",
           table(["k", "m", "X", "EV/month (95%)", "Pass rate", "Days per attempt", "Stage", "Within limits"], rows, cls="small", hl=hl, num_from=0),
           note("Stage: blank = grid or edge setting, \"bold\" = bold-play round, \"v5 default\" = version 5's setting. These are refine-path values, chosen as the best of many, so they are biased upward; the plan reports the fresh-path run below.")]
    if ch: out.append(heat(prog, instr, ch["m"] if not ch.get("robust") else fin(prog, instr, "refine best")["m"] if fin(prog, instr, "refine best") else ch["m"]))
    ms = sorted({r["m"] for r in refs(prog, instr)})
    mrows = []
    for m in ms:
        ok = [r for r in refs(prog, instr) if r["m"] == m and O.admissible(dict(r, m=max(r["m"], O.CAP_M)))]
        allr = [r for r in refs(prog, instr) if r["m"] == m]
        b = max(allr, key=lambda r: r["EV_month"])
        mrows.append([f"{m:g}", str(len(allr)), f"{b['k']} / {b['X'] / b['size']:.0%}", pm(b["EV_month"], b["CI"]), pct(b["P"]), f"{b['days']:.1f}"])
    out.append(table(["Stop m", "Settings refined", "Best k / X", "Best EV/month", "Pass rate", "Days"], mrows, cls="small", num_from=0,
                     cap="The best refined setting at each stop. A tighter stop is faster (8.2) and dearer per trade (4.4); where the firm's leverage allows, the gain from speed wins down to the plan's limit of 0.35."))
    return "".join(out)

def settings_table(sp):
    prog, instr = sp["prog"], sp["instr"]
    rows = []; hl = [0]
    def add(label, p, i, tag):
        s = fin(p, i, tag); r = fin(p, i, tag, data="real")
        if not s: return
        rows.append([label, sett(s), pm(s["EV_month"], s["CI"]), pm(r["EV_month"], r["CI"]) if r else "", pct(s["P"]), usd(s["Vf"]), f"{s['days']:.1f}", usd(s["EV"])])
    add("<strong>Plan</strong>", prog, instr, "chosen")
    add("Refined best before the robustness check", prog, instr, "refine best")
    add("Best outside the plan's limits", prog, instr, "uncapped")
    add("Version 5 default", prog, instr, "v5 default")
    for p, i, lab in sp.get("alts", []):
        add(lab, p, i, "chosen")
    return table(["Setting", "k / m / X", "EV/month, fresh paths", "EV/month, real history", "Pass rate", "Cash per funded account", "Days per attempt", "Value of an attempt"],
                 rows, cls="small", hl=hl,
                 cap="One 100K account. Fresh paths: 24,000 attempts on paths 29&ndash;32 (33&ndash;36 for re-chosen settings); real history: 8,000 attempts on the 2024&ndash;26 hourly prices. &plusmn; is a 95% interval.")

def trade_section(sp, ch, F):
    prog, instr = sp["prog"], sp["instr"]
    m, k, L = ch["m"], ch["k"], ch["L"]
    A1 = F["phases"][0]["target"]
    cap1 = F["phases"][0].get("max_win")
    w1 = min(k * L, A1, cap1 or 1e18)
    lev = lev_of(prog, instr)
    T = trade_numbers(instr, m, L, w1, lev=lev)
    Tf = trade_numbers(instr, m, L, min(k * L, ch["X"]), lev=lev)
    unit = T["unit"]; units = unit + "s"
    price = PRICE[instr]
    pstr = f"{price:,.2f}" if price > 100 else f"{price:.4f}"
    lines = [f"Risk \\(l = \\${L:,.0f}\\); stop \\(s = m\\sigma = {m:g} \\times {SIG[instr] * 100:.4f}\\% = {T['s'] * 100:.4f}\\%\\) of the price; at {pstr} that is <strong>{T['stop_pts']:.1f} {units}</strong>.",
             f"Notional \\(N = l/s = \\${T['N']:,.0f}\\); <strong>\\(\\${T['usd_per_pt']:,.2f}\\) per {unit}</strong>" +
             (f"; at {usd(T['lot_value'], 2)} per {unit} per standard lot, <strong>{T['lots']:.2f} lots</strong> (round down)." if T.get("lot_value") else
              "; lots = this divided by the contract's dollars per point per lot (platform specification), rounded down."),
             f"Cost \\(c = \\kappa N = \\${T['c']:,.2f}\\), i.e. \\(c/l = {T['rho'] * 100:.2f}\\%\\); financing \\(\\${T['fin_night']:,.0f}\\) per night held.",
             f"First trade of phase 1: the win is \\(w = \\min(kl, A_1{', cap' if cap1 else ''}) = \\${w1:,.0f}\\); the take-profit sits \\(u = s(w+c)/l = {T['u'] * 100:.3f}\\%\\) away, <strong>{T['tgt_pts']:.1f} {units}</strong>; \\(p = l/(l+w+c) = {T['p']:.4f}\\).",
             f"Mean \\(-c = -\\${T['c']:,.2f}\\); variance \\(l(w+c) = {T['var']:,.0f}\\) (sd \\(\\${T['sd']:,.0f}\\)); duration {T['dur']:.2f} h on average (losers {T['dur_loss']:.2f} h, winners {T['dur_win']:.1f} h of open market).",
             f"A funded-cycle win of \\(\\${min(k * L, ch['X']):,.0f}\\): take-profit {Tf['tgt_pts']:,.0f} {units} away, \\(p = {Tf['p']:.4f}\\), winners {Tf['dur_win']:.0f} h on average, so usually held through nights."]
    if lev:
        lines.append(f"Margin at 1:{lev}: \\(N/{lev} = \\${T['margin']:,.0f}\\) = {pct(T['margin_pct'])} of the balance; the smallest stop the leverage allows at the plan's 60% limit is \\(m_{{\\min}} = {T['m_min']:.3f}\\).")
    return _calc(lines)

def phases_section(sp, ch, F, e, v):
    prog, instr = sp["prog"], sp["instr"]
    m, k, L = ch["m"], ch["k"], ch["L"]
    rho = e["rho"]; bs = F.get("buffer_scale", 1.0)
    out = []
    for j, (st, ph) in enumerate(zip(F["phases"], e["phases"])):
        A, B = st["target"], st["dd"]
        bold = k * L >= A + B - 100 * bs and not st.get("max_win") and not st.get("profit_days")
        out.append(f"<h3 class='sub'>Phase {j + 1}: \\(A = \\${A:,.0f}\\), \\(B = \\${B:,.0f}\\)</h3>")
        if bold:
            tb, Pb = _steps_table(A, B, L, rho, buf=100 * bs)
            out.append(f"<p>\\(k\\,l = \\${k * L:,.0f} \\ge A + B\\): every win ends the phase. The bold chain (5.6):</p>" + tb)
            out.append(f"<p>Product formula \\(P_{j + 1} = {Pb:.4f}\\); full chain \\({ph['P']:.4f}\\).</p>")
        else:
            why = []
            if st.get("max_win"): why.append(f"one trade may make at most {usd(st['max_win'])}, so at least {math.ceil(A / st['max_win'])} wins are needed")
            if st.get("profit_days"): why.append(f"the phase needs {st['profit_days'][0]} profitable days, so the plan aims at a daily target and wins are smaller (6.4); the chain below ignores that rule, which changes time, not the average (11.1)")
            if k * L < A + B - 100 * bs: why.append(f"\\(k\\,l = \\${k * L:,.0f} < A + B\\), so from deep below the start one win does not reach the target")
            out.append(f"<p>Not a pure bold chain: {'; '.join(why)}. The chain of 5.6 is solved numerically:</p>")
        out.append(_calc([f"\\(P_{j + 1} = {ph['P']:.4f}\\), \\(\\mathbb{{E}}[\\text{{trades}}] = {ph['N']:.2f}\\), \\(\\mathbb{{E}}[\\text{{total cost}}] = K = \\${ph['Ecost']:,.0f}\\)",
                          f"Identity: \\((B - K)/(A + B) = ({B:,.0f} - {ph['Ecost']:,.0f})/{A + B:,.0f} = {ph['P_identity']:.4f}\\)",
                          f"Zero-cost value \\(B/(A+B) = {B / (A + B):.4f}\\): cost lowers it by {pct(B / (A + B) - ph['P'], 2)}."]))
        if st.get("dll"):
            nfull = int((st['dll'] - 200 * bs) // (L * (1 + rho))); rem = st['dll'] - 200 * bs - nfull * L * (1 + rho)
            after = (f"after {nfull} full losses in one day only {usd(rem)} of risk is left for the day, so the plan takes one smaller trade and then stops until tomorrow" if rem >= 0.1 * L
                     else f"after {nfull} full losses in one day the plan stops until tomorrow")
            out.append(f"<p>Daily loss limit {usd(st['dll'])}: the plan's risk never exceeds today's room less {usd(200 * bs)}, so a stop-out cannot break it; {after}. Only a price gap through the stop can break it, which the engine models.</p>")
    prod = " \\times ".join("%.4f" % ph["P"] for ph in e["phases"])
    out.append(f"<p><strong>Both phases:</strong> \\(P = {prod} = {e['P']:.4f}\\) (chain). Engine on fresh paths: <strong>{v['P_engine']:.4f} &plusmn; {binom_ci(v['P_engine'], 24000):.4f}</strong>; the Brownian formula gives {v['P_formula']:.4f}.</p>")
    return "".join(out)

def funded_section(sp, ch, F, e, v):
    fd = F["funded"]; D = fd["dd"]; a = fd["split"]; R = fd.get("refund", 0) or 0
    X1, X = ch["X1"], ch["X"]
    caps = fd.get("caps")
    q1, q = e["q1"], e["q"]
    lines = [f"Allowance \\(D = \\${D:,.0f}\\); cycle targets \\(X_1 = \\${X1:,.0f}\\)" + (f", \\(X = \\${X:,.0f}\\)" if X != X1 else "") +
             (f" (the first payouts are capped at {', '.join(usd(c) for c in caps[:2])}, so the first cycles aim at the cap)" if caps else "") + f"; split \\(\\alpha = {a:.0%}\\).",
             f"One cycle (the chain from 0 to the cycle target before \\(-D\\)): \\(q_1 = {q1:.4f}\\)" + (f", later cycles \\(q = {q:.4f}\\)" if abs(q - q1) > 1e-6 else "") + ".",
             f"Expected paid cycles \\(q_1/(1-q) = {e['n_cycles_paid'] if 'n_cycles_paid' in e else v['cycles_paid']:.4f}\\); expected withdrawn before the split \\(\\${e['withdrawn']:,.0f}\\).",
             f"Withdrawal identity: \\(D - \\mathbb{{E}}[\\text{{funded cost}}] = {D:,.0f} - {e['cost_funded']:,.0f} = \\${e['identity']:,.0f}\\)" + (" (equal to the withdrawn amount to within the grid's precision: the identity holds)" if abs(e['identity'] - e['withdrawn']) < 0.01 * D else f" against {usd(e['withdrawn'])} withdrawn") + ".",
             f"Cash: \\(\\alpha \\times {e['withdrawn']:,.0f}" + (f" + R\\cdot\\Pr(\\text{{refund}}) = {a:g}\\times{e['withdrawn']:,.0f} + {e['cash_funded'] - a * e['withdrawn']:,.0f}" if R else "") + f" = \\${e['cash_funded']:,.0f}\\) per funded account (chain)" +
             (f"; the refund term is {usd(e['cash_funded'] - a * e['withdrawn'])}, the fee \\(R = \\${R:,.2f}\\) times the chance of reaching the payout that carries it." if R else ".")]
    if fd.get("best"): lines.append(f"Best-day rule ({pct(fd['best'], 0)}): each day's take-profit is capped at {usd(fd['best'] * X)} less what the day has made, so a cycle needs at least {math.ceil(1 / fd['best'])} profitable days; the chain applies it as a cap per win.")
    if fd.get("day_profit_cap"): lines.append(f"Daily profit cap {usd(fd['day_profit_cap'])}: each day's take-profit is capped at what is left of it.")
    if fd.get("profit_days"): lines.append(f"Profitable days per cycle ({fd['profit_days'][0]} of {usd(fd['profit_days'][1])}+): a daily target until they are complete (6.4); time, not value.")
    lines.append(f"Engine, fresh paths: <strong>{usd(v['cash_engine'])}</strong> per funded account ({pct(v['cash_engine'] / v['cash_exact'] - 1, 1)} against the chain: financing, gaps, weekend closes); {pct(ch['P_paid'])} of attempts reach a payout; median {ch['t1']:.0f} days from purchase to the first payout of those that do.")
    # distribution of the number of paid cycles
    rows = []
    cyc, pr = e["cyc"], e["pr"]
    for j in range(0, 5):
        pj = (1 - pr[0]) if j == 0 else pr[j - 1] - pr[j]
        cash = a * sum(cyc[:j]) + (R if (R and j >= fd.get("refund_after", 1) and not fd.get("refund_split")) else (R * min(j, fd.get("refund_split", 0)) / fd["refund_split"] if fd.get("refund_split") else 0))
        rows.append([str(j), f"{pj:.4f}", usd(cash)])
    return _calc(lines) + table(["Paid cycles", "Probability", "Cash (split + refund)"], rows, cls="small", num_from=1, cap="Chain values, before financing. The cash of a funded account is lumpy: most pay nothing, a few pay one or more full cycles.")

def value_section(sp, ch, F, e, v):
    re_ = fin(sp["prog"], sp["instr"], data="real")
    fee = F["fee"]; att = DAYS_MONTH / ch["days"]
    tm = timing(sp["prog"], sp["instr"])
    tline = (f"Where the time goes (engine, 6,000 attempts on path 29): {pct(tm['fail_p1'], 0)} of attempts fail in phase 1; a failed attempt lasts {tm['t_eval_fail']:.1f} days on average; "
             f"a passed one spends {tm['t_eval_pass']:.1f} days in the evaluation and then {tm['t_fund']:.1f} days funded, making {tm['payouts']:.2f} payouts on average; {tm['trades']:.1f} trades per attempt.") if tm else ""
    lines = [f"Value of an attempt (1.2): \\(\\mathbb{{E}}[V] = P\\,\\mathbb{{E}}[C] - F = {e['P']:.4f}\\times{e['cash_funded']:,.0f} - {fee:,.2f} = \\${e['EV']:,.0f}\\) (chain); engine <strong>\\(\\${ch['EV']:,.0f}\\)</strong>.",
             f"Time (engine): \\(\\mathbb{{E}}[T] = {ch['days']:.2f}\\) days per attempt, so {att:.2f} attempts a month per slot and \\(\\${att * fee:,.0f}\\) of fees a month before refunds.", tline,
             f"Value per month (8.3): \\(30.44 \\times {ch['EV']:,.0f}/{ch['days']:.2f} = \\)<strong>\\(\\${ch['EV_month']:,.0f}\\)</strong> &plusmn; {usd(ch['CI'])} (95%) per 100K account on fresh paths" +
             (f"; {usd(re_['EV_month'])} &plusmn; {usd(re_['CI'])} on the real 2024&ndash;26 history." if re_ else ".")]
    return _calc([x for x in lines if x])

def size_section(sp):
    a = ALLOC[sp["firm"]]
    prog, instr = sp["prog"], sp["instr"]
    rows = []
    for tg, size in (("chosen", 100_000), ("200K", 200_000), ("50K", 50_000), ("25K", 25_000), ("10K", 10_000), ("5K", 5_000)):
        r = fin(prog, instr, tg, size=size)
        if not r: continue
        F = rules(prog, size, fee=r.get("fee"))
        rows.append([kk(size), usd(F["fee"], 2 if F["fee"] % 1 else 0), usd(F["fee"] * 100_000 / size), pm(r["EV_month"], r["CI"]), usd(r["EV_month"] * 100_000 / size)])
    for p, i, s, n in a["full"]:
        if p != prog and s != 100_000 and "The5ers" in p:
            r = acct_row(p, i, s); F = rules(p, s)
            rows.append([f"{kk(s)} (New rules)", usd(F["fee"]), usd(F["fee"] * 100_000 / s), pm(r["EV_month"], r["CI"]), usd(r["EV_month"] * 100_000 / s)])
    tb = table(["Size", "Fee", "Fee per $100K", "EV/month (95%)", "EV/month per $100K"], rows, cls="small", num_from=1,
               cap="Every size uses the plan's setting scaled to the account (risk, targets and cycle all in proportion), on the same paths and random numbers, so the differences are the fee and the rules that do not scale.")
    rv, rn = alloc_value(a["rec"]); fv, fn_ = alloc_value(a["full"])
    rec = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["rec"]) or "not in the recommended plan"
    full = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["full"])
    txt = (f"<p><strong>Per person:</strong> {a['cap']}. <strong>Copying:</strong> {a['copy']}. <strong>The plan:</strong> {rec}" + (f", worth {usd(rv)} a month ({rn} account{'s' if rn > 1 else ''})" if rn else "") +
           f"; at the firm's full allowance: {full}, worth {usd(fv)} a month ({fn_} accounts). {a['why'][0].upper() + a['why'][1:]}.</p>")
    return tb + txt

def sens_section(sp, ch):
    prog, instr = sp["prog"], sp["instr"]
    rows = []
    rb = [r for r in EXTRA["robust"] if r["prog"] == prog and r["instr"] == instr and abs(r["m"] - ch["m"]) < 1e-9]
    cs = rb if rb else [r for r in SENS if r["tag"] == "cost" and r["prog"] == prog and r["instr"] == instr and abs(r["m"] - ch["m"]) < 1e-9]
    for r in sorted(cs, key=lambda r: r["cost_mult"]):
        rows.append([f"&times; {r['cost_mult']:g}", pm(r["EV_month"], r["CI"]), pct(r["P"]), f"{r['days']:.1f}"])
    if not rows: return ""
    return table(["Trading cost", "EV/month (95%)", "Pass rate", "Days per attempt"], rows, cls="small", num_from=1,
                 cap="The plan's setting with every round-trip cost (spread, commission, slippage) and every night's financing multiplied, 12,000 attempts on fresh paths.")

def plan_section(sp, ch):
    sh = SHEET[sp["sheet"]]
    items = "".join(f"<li>{x}</li>" for x in sh["plan"])
    return (f"<ul>{items}</ul><p class='note'>Sources: {sh['sources']}.</p>")

def excluded_section(sp):
    ex = sp.get("excluded")
    if not ex: return ""
    rows = []
    for p, i, why in ex:
        rs = refs(p, i)
        if not rs: continue
        b = max(rs, key=lambda r: r["EV_month"])
        rows.append([why, sett(b), pm(b["EV_month"], b["CI"])])
    return table(["Searched but not used", "Best k / m / X", "Refined EV/month"], rows, cls="small", num_from=1)

# ------------------------------------------------------------------ the chapter
def prog_chapter(num, sp):
    if sp.get("fut"): return fut_chapter(num, sp)
    prog, instr = sp["prog"], sp["instr"]; sh = SHEET[sp["sheet"]]
    ch = fin(prog, instr); F = rules(prog, 100_000, fee=ch.get("fee"))
    v = ver(prog, instr)
    e = AN.programme_exact(prog, instr, ch["m"], ch["k"], ch["X1"], ch["X"], L=ch["L"], F=F)
    rv, rn = alloc_value(ALLOC[sp["firm"]]["rec"])
    tr = tier(prog)
    head = (f'<section class="chapter"><span class="eyebrow">Chapter {num} &middot; tier {tr}</span><h1>{sh["title"]}</h1>'
            f'<p>{MNAME[instr]}; plan setting \\(k = {ch["k"]}\\), \\(m = {ch["m"]:g}\\), cycle {pct(ch["X"] / ch["size"], 0)} of the account; '
            f'<strong>{usd(ch["EV_month"])} a month per 100K</strong> (&plusmn; {usd(ch["CI"])}); in the plan: '
            + ("; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in ALLOC[sp['firm']]['rec']) or "optional") + (f", {usd(rv)} a month." if rn else ".") + "</p>")
    parts = [head,
             f"<h2>{num}.1 The rules</h2>", rules_table(sh),
             f"<h2>{num}.2 What the engine simulates</h2>", model_table(F, prog),
             f"<p>Trades: {MNAME[instr]}, entries {hours(instr)[0]:02d}:00&ndash;{hours(instr)[1]:02d}:00 UTC on weekdays, risk 1.5% of the account (\\(\\${ch['L']:,.0f}\\) per 100K), every rule of 5.5 and 6.2&ndash;6.6.</p>",
             f"<h2>{num}.3 The search</h2>", search_section(sp, fin(prog, instr, "refine best") or ch), excluded_section(sp),
             f"<h2>{num}.4 The chosen setting, on fresh paths</h2>", settings_table(sp),
             f"<h2>{num}.5 One trade</h2>", trade_section(sp, ch, F),
             f"<h2>{num}.6 The evaluation</h2>", phases_section(sp, ch, F, e, v),
             f"<h2>{num}.7 The funded account</h2>", funded_section(sp, ch, F, e, v),
             f"<h2>{num}.8 Value per attempt and per month</h2>", value_section(sp, ch, F, e, v),
             f"<h2>{num}.9 Account size and number of accounts</h2>", size_section(sp),
             f"<h2>{num}.10 If costs are higher</h2>", sens_section(sp, ch),
             f"<h2>{num}.11 How the plan meets every rule</h2>", plan_section(sp, ch), "</section>"]
    return "\n".join(parts)

def fut_chapter(num, sp):
    prog, instr = sp["prog"], sp["instr"]; sh = SHEET[sp["sheet"]]
    ch = fin(prog, instr, size=50_000); re_ = fin(prog, instr, data="real", size=50_000); d5 = fin(prog, instr, "v5 default", size=50_000)
    F = rules(prog, 50_000, "fut", override=ch.get("override"))
    fg = sorted([r for r in FUTG if r["prog"] == prog], key=lambda r: -r["EV_month"])[:8]
    fr = sorted([r for r in REF if r["prog"] == prog], key=lambda r: -r["EV_month"])[:8]
    T = trade_numbers(instr, ch["m"], ch["L"], ch["k"] * ch["L"])
    contracts = T["usd_per_pt"] / 2.0
    rows = [[str(r["k"]), f"{r['m']:g}", usd(r["L"]), pm(r["EV_month"], r["CI"]), pct(r["P"]), f"{r['days']:.1f}"] for r in fr]
    full = ALLOC[sp["firm"]]["full"][0]
    out = [f'<section class="chapter"><span class="eyebrow">Chapter {num} &middot; tier {tier(prog)} &middot; optional futures layer</span><h1>{sh["title"]}</h1>',
           f"<p>Micro Nasdaq futures, shared direction with the Nasdaq CFD accounts. Futures firms set no percentage risk rule, so the search covers the risk per trade as well: \\(k \\in \\{{2,\\dots,8\\}}\\), \\(m \\in \\{{0.5, 0.75, 1\\}}\\), risk $600&ndash;$1,100 ({sum(1 for r in FUTG if r['prog'] == prog)} grid settings, then the eight best refined).</p>",
           f"<h2>{num}.1 The rules</h2>", rules_table(sh), f"<h2>{num}.2 What the engine simulates</h2>", model_table(F, prog),
           f"<h2>{num}.3 The search</h2>", table(["k", "m", "Risk", "Refined EV/month", "Pass rate", "Days"], rows, cls="small", num_from=0),
           f"<h2>{num}.4 The chosen setting</h2>",
           _calc([f"Plan: \\(k = {ch['k']}\\), \\(m = {ch['m']:g}\\), risk \\(\\${ch['L']:,.0f}\\): stop {T['stop_pts']:.1f} points, \\(\\${T['usd_per_pt']:.0f}\\) per point = {contracts:.1f} MNQ contracts at $2 per point (round down).",
                  f"Fresh paths: <strong>{pm(ch['EV_month'], ch['CI'])}</strong> a month per account (pass rate {pct(ch['P'])}, {ch['days']:.1f} days per attempt); real history {pm(re_['EV_month'], re_['CI'])}." +
                  (f" Version 5's setting ({d5['k']} / {d5['m']:g} / {usd(d5['L'])}): {pm(d5['EV_month'], d5['CI'])}." if d5 else ""),
                  f"Why so little: the funded account's maximum loss trails the balance until it locks, payouts are capped per request and (Apex) in number, and the evaluation fee recurs monthly (Topstep) or is only worth paying at a deep discount (Apex). The withdrawal identity of 7.1 still holds, but the allowance it pays out is small: $2,000 of trailing loss on a $50,000 account."]),
           f"<h2>{num}.5 How many</h2><p>{ALLOC[sp['firm']]['cap']}: {full[3]} accounts, worth {usd(full[3] * ch['EV_month'])} a month together. The intervals are wide (the funded stage is short and lumpy), and the real-history figure differs from the synthetic one by more than for the CFD programmes. This layer is optional and is not in the recommended plan's headline figure.</p>",
           f"<h2>{num}.6 How the plan meets every rule</h2>", plan_section(sp, ch), "</section>"]
    return "\n".join(out)
