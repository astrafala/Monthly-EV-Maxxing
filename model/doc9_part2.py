"""Part II of the version 9 document: one chapter per programme in the plan (and the futures layer)."""
import math, collections, json
import numpy as np
from doc9_common import *
from doc9_part1 import short, sett, xpct, _calc, _first_win, _row_steps, funded_win, risk_for
import lockstep_portfolio_v9 as LP

def acct_row(prog, instr, size):
    """a final row with EV_month and CI replaced by the continuing-slot rate (Part II's long-run rate, 8.3); the random-start
    ratio stays as EV_month_rs and CI_rs"""
    r = fin(prog, instr, size=size)
    if r is None: return None
    c = cont(r)
    return dict(r, EV_month_rs=r["EV_month"], CI_rs=r["CI"], EV_month=c["rate"], CI=c["CI"]) if c else dict(r, EV_month_rs=r["EV_month"], CI_rs=r["CI"])

def _cnt(slots):
    c = collections.Counter((s["firm"], s["instr"], s["size"]) for s in slots)
    return [(p, i, s, n) for (p, i, s), n in c.items()]

def _firm_slots(name, f):
    return [s for s in LP.PORTFOLIOS[name] if firm_of(s["firm"]) == f]

FIRMS = ["FTMO", "FundingPips", "The5ers", "FXIFY", "FundedNext", "Fintokei", "Hola Prime", "Alpha Capital", "FunderPro", "GFT",
         "BrightFunded", "Blue Guardian", "Maven", "Topstep", "Apex"]
CAPS = {
    "FTMO": ("$400,000 per trader across all accounts, evaluations included", "your own accounts, within the cap"),
    "FundingPips": ("$400,000 across evaluation, funded and Prime accounts", "your own FundingPips accounts; no copier services"),
    "The5ers": ("one 50K or 100K account across Classic and New together; New also 3 &times; 2.5K, 3 &times; 5K, 3 &times; 10K and 1 &times; 25K (Classic's own small slots not used: fees not readable)", "your own accounts"),
    "FXIFY": ("one active account of each size", "between your own FXIFY accounts"),
    "FundedNext": ("$300,000 funded; evaluations unlimited", "between your own challenge accounts, never into a funded account"),
    "Fintokei": ("&euro;500,000 of accounts", "your own trades across your own accounts"),
    "Hola Prime": ("$500,000", "only between your own Hola Prime accounts (funded: one master and one copier); never from other firms"),
    "Alpha Capital": ("$400,000 per household, $300,000 per strategy", "from your own external accounts with proof"),
    "FunderPro": ("$200,000", "no replicating trades across FunderPro accounts"),
    "GFT": ("$400,000 funded", "no duplicated trades or trade ideas between GFT accounts"),
    "BrightFunded": ("$400,000 funded; evaluations unlimited", "allowed between your own accounts"),
    "Blue Guardian": ("$400,000; evaluations up to $200,000 each", "your own accounts only"),
    "Maven": ("$200,000; at most $10,000 of profit closed per rolling 30 days per person", "&ndash;"),
    "Topstep": ("5 Express Funded Accounts at once", "your own accounts"),
    "Apex": ("20 funded accounts", "your own accounts"),
}
ALLOC = {}
for f in FIRMS:
    rec = _cnt(_firm_slots(LP.REC, f)); full = _cnt(_firm_slots("All firms at full caps + The5ers small accounts", f) or _firm_slots("Recommended + futures", f))
    ALLOC[f] = dict(cap=CAPS[f][0], copy=CAPS[f][1], rec=rec, full=full)

def alloc_value(lst):
    tot = 0.0; n = 0
    for p, i, s, k in lst:
        r = acct_row(p, i, s)
        if r: tot += k * r["EV_month"]; n += k
    return tot, n

SHEETMAP = {"FTMO": "FTMO 2-Step", "FundingPips": "FundingPips Flex", "The5ers": "The5ers High Stakes", "FXIFY": "FXIFY Two Phase Classic",
            "FundedNext": "FundedNext Stellar 2-Step", "Fintokei": "Fintokei ProTrader", "Hola Prime": "Hola Prime 2-Step Prime",
            "Alpha Capital": "Alpha Capital Pro 10%", "FunderPro": "FunderPro Classic", "GFT": "GFT 2-Step Standard",
            "BrightFunded": "BrightFunded 2-Step Classic", "Blue Guardian": "Blue Guardian 2-Step", "Maven": "Maven 2-Step",
            "Topstep": "Topstep 50K", "Apex": "Apex 50K EOD"}
PROGS_OF = {
    "FTMO": [("FTMO 2-Step", "US100")],
    "FundingPips": [(p, i) for p in ("FundingPips 2-Step Flex (80%)", "FundingPips 2-Step Flex (95%)") for i in ("USDJPY", "EURUSD")],
    "The5ers": [("The5ers High Stakes", "US100"), ("The5ers High Stakes Classic", "US100")],
    "FXIFY": [(p, i) for p in ("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY Two Phase Classic (80%)") for i in ("US100", "USDJPY")],
    "FundedNext": [("FundedNext Stellar 2-Step", "EURUSD"), ("FundedNext Stellar 2-Step", "XAUUSD")],
    "Fintokei": [("Fintokei ProTrader", "US100")],
    "Hola Prime": [("Hola Prime 2-Step Prime (bi-weekly 80%)", "XAUUSD"), ("Hola Prime 2-Step Prime (bi-weekly 80%)", "EURUSD")],
    "Alpha Capital": [("Alpha Capital Pro 10%", "US100")],
    "FunderPro": [("FunderPro Classic", "US100"), ("FunderPro Classic", "USDJPY")],
    "GFT": [("GFT 2-Step Standard", "US100"), ("GFT 2-Step Standard", "USDJPY")],
    "BrightFunded": [("BrightFunded 2-Step Classic", "US100")],
    "Blue Guardian": [("Blue Guardian 2-Step", "US100")],
    "Maven": [("Maven 2-Step", "US100")],
}

def plan_choice(f):
    """the programme and market the plan uses at firm f (from the portfolio), else the best"""
    sl = _firm_slots(LP.REC, f) or _firm_slots("All firms at full caps", f) or _firm_slots("Recommended + futures", f)
    if sl: return sl[0]["firm"], sl[0]["instr"]
    rs = [fin(p, i) for p, i in PROGS_OF.get(f, [])]
    rs = [r for r in rs if r]
    rs = [acct_row(r["prog"], r["instr"], r["size"]) for r in rs]
    b = max(rs, key=lambda r: r["EV_month"]) if rs else None
    return (b["prog"], b["instr"]) if b else (None, None)

SPECS = []
for f in FIRMS:
    if f in ("Topstep", "Apex"):
        p = SHEETMAP[f]
        if fin(p, "MNQ_fut", size=50_000): SPECS.append(dict(sheet=SHEETMAP[f], prog=p, instr="MNQ_fut", firm=f, fut=True))
        continue
    p, i = plan_choice(f)
    if p: SPECS.append(dict(sheet=SHEETMAP[f], prog=p, instr=i, firm=f, alts=[(pp, ii) for pp, ii in PROGS_OF[f] if (pp, ii) != (p, i)]))

# ------------------------------------------------------------------ pieces
def rules_table(sh):
    return table(["Rule", "As published (read 4 October 2026)"], [[a, b] for a, b in sh["rules"]], num_from=9, w0="30%")

def _dll_txt(st, F):
    md = st.get("dll_mode") or ("rel" if st.get("dll_rel") else "fixed"); pc = pct(st["dll"] / F["size"], 0)
    return {"fixed": f"daily loss {usd(st['dll'])} ({pc} of the initial balance) below the day's reference",
            "rel": f"daily loss {pc} of the day's starting balance, recomputed at every reset",
            "min": f"daily loss {pc} of the smaller of the initial and the day's starting balance (base not stated by the firm: the stricter)"}[md]

def model_table(F, prog):
    rows = [["Fee per attempt", usd(F["fee"], 2 if F["fee"] % 1 else 0) + (" a month (renewed while the evaluation lasts)" if F.get("monthly") else "") +
             (f"; activation {usd(F['activation'])} on passing" if F.get("activation") else "")]]
    if F.get("phase_credit"): rows.append(["Fee credit", "non-cash credit of " + " and ".join(usd(c, 2) for c in F["phase_credit"]) + " on passing phase 1 and phase 2, spent on the next evaluation"])
    for j, st in enumerate(F.get("phases", [])):
        bits = [f"target {usd(st['target'])}", f"maximum loss {usd(st['dd'])} below the start, " + ("trailing the best end-of-day balance" if st["eod"] else "static")]
        bits.append(_dll_txt(st, F) if st.get("dll") else "no daily loss limit")
        if st.get("min_days"): bits.append(f"at least {st['min_days']} trading days" + (" (no filler trades: ordinary trades, one a day, if days are missing)" if F.get("no_fillers") else " (a missing day: a 0.01-lot filler trade held 3 minutes)"))
        if st.get("profit_days"): bits.append(f"{st['profit_days'][0]} profitable days of at least {usd(st['profit_days'][1])}")
        if st.get("best"): bits.append(f"best day at most {pct(st['best'], 0)} of the profit")
        if st.get("conc"): bits.append(f"plan: no trade and no day above {pct(st['conc'], 0)} of the target ({usd(st['conc'] * st['target'])})")
        if st.get("min_rr"): bits.append(f"every trade at least 1:{st['min_rr']:g}")
        if st.get("max_days"): bits.append(f"expires after {st['max_days']} days")
        rows.append([f"Phase {j + 1}" if len(F["phases"]) > 1 else "Evaluation", "; ".join(bits)])
    fd = F["funded"]
    bits = [f"maximum loss {usd(fd['dd'])}, " + ("trailing the best end-of-day balance" if fd["eod"] else "static"),
            _dll_txt(fd, F) if fd.get("dll") else "no daily loss limit", f"split {pct(fd['split'], 0)}"]
    if fd.get("refund"):
        if fd.get("refund_split"): bits.append(f"fee returned in {fd['refund_split']} equal parts with the first {fd['refund_split']} payouts")
        else: bits.append(f"{usd(fd['refund'], 2)} of the fee returned with payout number {fd.get('refund_after', 1)}")
    else: bits.append("no fee refund")
    if fd.get("q_days"): bits.append(f"a payout needs {fd['q_days']} qualifying days of at least {usd(fd['q_min'])}")
    elif fd.get("ondemand"): bits.append("payouts on demand")
    else: bits.append(f"first payout {fd['first_payout']} days after the first funded trade, then every {fd['cycle']} days")
    if fd.get("min_payout"): bits.append(f"minimum payout {usd(fd['min_payout'])}")
    if fd.get("caps"): bits.append("payout caps " + ", ".join(usd(c) for c in fd["caps"][:6] if c < 1e9))
    if fd.get("pct_bal"): bits.append(f"a payout at most {pct(fd['pct_bal'], 0)} of the balance")
    if fd.get("best"): bits.append((f"best day below {pct(fd['best'], 0)} of a payout's profit (strictly)" if fd.get("q_days") else f"best day at most {pct(fd['best'], 0)} of a payout's profit") + (", measured against the account's best day ever" if fd.get("best_ever") else ""))
    if fd.get("first_days"): bits.append(f"first payout only after {fd['first_days']} trading days (no fillers; the plan trades at most once a day until then)")
    if fd.get("cycle_days"): bits.append(f"{fd['cycle_days']} trading days in every payout cycle" + (" (no filler trades: ordinary trades, one a day, while days are missing)" if F.get("no_fillers") else " (filler trades)"))
    if fd.get("cycle_from_processed"): bits.append("the next payout 14 days after the last one was processed")
    if fd.get("profit_days_window"): bits.append(f"the profitable days within {fd['profit_days_window']} calendar days ending on the request day")
    if fd.get("profit_ceiling"): bits.append(f"plan: funded profit never above {usd(fd['profit_ceiling'])}, a margin under the $5,000 above which the firm's 50% rule applies")
    if fd.get("roll_profit_cap"): bits.append(f"plan: closed profit in any {fd['roll_profit_cap'][1]} days never above {usd(fd['roll_profit_cap'][0])} (the excess would be voided)")
    if fd.get("min_rr"): bits.append(f"every trade at least 1:{fd['min_rr']:g}")
    if fd.get("day_profit_cap"): bits.append(f"profit above {usd(fd['day_profit_cap'])} a day not counted")
    if fd.get("profit_days"): bits.append(f"{fd['profit_days'][0]} profitable days of {usd(fd['profit_days'][1])}+ per cycle")
    if fd.get("need_profit"): bits.append("each later payout needs net profit since the last")
    if fd.get("max_payouts"): bits.append(f"at most {fd['max_payouts']} payouts")
    if fd.get("buffer"): bits.append(f"buffer {usd(fd['buffer'])} kept in the account")
    if fd.get("conc"): bits.append(f"plan: no trade and no day above {pct(fd['conc'], 0)} of the payout target")
    rows.append(["Funded account", "; ".join(bits)])
    if F.get("flat_daily"): rows.append(["Trading hours", f"no entry from {F['flat_daily'] - 1}:00 UTC, flat at {F['flat_daily']}:00 UTC every day; flat at weekends; at least 10 minutes between a close and the next entry; no stop or target closer than 0.6 hourly sd"])
    rows.append(["Positions", "whole volume steps at the contract size (0.01 lot; whole futures contracts), rounded down, never below the smallest; the account's breach level (floor or today's limit, the nearer) is a barrier of every trade; reviews and payout processing in working days"])
    dur = []
    if F.get("hold_min"): dur.append(f"the bracket is placed {F['hold_min']} minutes after the entry (minimum holding time 2 minutes); a trade that could close sooner ends the account")
    if F.get("dur_rule"): dur.append(f"the {F['dur_rule']:g}-minute rule checked on the account's own trades at every phase pass and payout request (average, majority, half of gross profit); failure: phase restarted or profits removed")
    if F.get("day_min_minutes"): dur.append(f"a trading day counts only with a trade held at least {60 * F['day_min_minutes']:.0f} seconds")
    if dur: rows.append(["Duration rules", "; ".join(dur)])
    if F.get("lev"):
        lv = F["lev"]; rows.append(["Margin", f"leverage 1:{lv[0]} (evaluation), 1:{lv[1]} (funded); margin at most {pct(lv[2], 0)} of the current balance at entry" + (f", and at most {pct(lv[3], 0)} of the starting balance on the funded account" if lv[3] < 1 else "")])
    return table(["Part", "What the engine simulates"], rows, num_from=9, w0="22%")

def heat(prog, instr, L, m):
    rs = [r for r in grids(prog, instr) if abs(r["m"] - m) < 1e-9 and abs(r["L"] - L) < 1]
    if not rs: return ""
    ks = sorted({r["k"] for r in rs}); xs = sorted({round(r["X"] / r["size"], 3) for r in rs})
    cell = {(r["k"], round(r["X"] / r["size"], 3)): r["EV_month"] for r in rs}
    vals = list(cell.values()); lo, hi = min(vals), max(vals)
    ch = fin(prog, instr)
    head = "<tr><th>k \\ X</th>" + "".join(f'<th class="n">{x:.1%}</th>' if x * 1000 % 10 else f'<th class="n">{x:.0%}</th>' for x in xs) + "</tr>"
    body = ""
    for k in ks:
        tds = ""
        for x in xs:
            v = cell.get((k, x))
            if v is None: tds += '<td class="n" style="color:#b0b6c0">&middot;</td>'; continue
            a = 0.08 + 0.5 * (v - lo) / max(hi - lo, 1)
            st = f"background:rgba(42,120,214,{a:.2f});"
            tds += f'<td class="n" style="{st}">{v / 1000:.2f}</td>'
        body += f"<tr><td class='n' style='text-align:left'>{k:g}</td>{tds}</tr>"
    return (f'<table class="heat"><thead>{head}</thead><tbody>{body}</tbody></table>'
            f'<p class="cap">Grid value per month ($ thousands; 2,000 attempts each on paths 101&ndash;104, so &plusmn;${np.percentile([r["CI"] for r in rs], 10) / 1000:.1f}&ndash;{np.percentile([r["CI"] for r in rs], 90) / 1000:.1f}K for most cells) at risk {usd(L)} and stop m = {m:g}, by k (rows) and payout target X (columns). '
            f'Darker is more. The chosen setting is in the table above it, re-measured on fresh paths.</p>')

def search_section(sp):
    prog, instr = sp["prog"], sp["instr"]
    ng = sum(1 for r in GRID if r["prog"] == prog); nr = sum(1 for r in REF if r["prog"] == prog)
    instrs = sorted({r["instr"] for r in GRID if r["prog"] == prog})
    rs = sorted(refs(prog, instr), key=lambda r: -r["EV_month"])[:8]
    ch = fin(prog, instr)
    hl = [i for i, r in enumerate(rs) if ch and (abs(r["m"] - ch["m"]) < 1e-9 and r["k"] == ch["k"] and abs(r["X"] - ch["X"]) < 1 and abs(r["L"] - ch["L"]) < 1)]
    rows = [[pct(r["L"] / r["size"], 2), f"{r['k']:g}", f"{r['m']:g}", xpct(r["X"] / r["size"]), pm(r["EV_month"], ci_of(r)), pct(r["P"]), f"{r['days']:.1f}"] for r in rs]
    out = [f"<p>Searched: {ng} grid settings ({', '.join(MSHORT[i] for i in instrs)}; 2,000 attempts each) and {nr} refined settings (16,000 attempts each, paths 111&ndash;114). The eight best refined settings on {MSHORT[instr]}:</p>",
           table(["Risk", "k", "m", "X", "EV/month (95%)", "Pass rate", "Days per attempt"], rows, cls="small", hl=hl, num_from=0),
           note("Refine-path values, chosen as the best of many, so biased upward; the plan reports the fresh-path run below. "
                + (lambda pdd: (f"The settings share paths and random numbers, so the ranking is judged on paired differences, not on overlapping intervals: the best against the second, paired over the four paths, {sgn(pdd[0])} &plusmn; {usd(pdd[1])} a month (Student t, 3 degrees of freedom)"
                                + (", so the refinement cannot tell them apart." if abs(pdd[0]) <= pdd[1] else ".")) if pdd else "")(paired_diff(rs[0], rs[1]) if len(rs) > 1 else None))]
    if ch: out.append(heat(prog, instr, ch["L"], ch["m"]))
    return "".join(out)

def settings_table(sp):
    rows = []; hl = [0]
    def add(label, p, i):
        s = fin(p, i)
        if not s: return
        c_ = cont(s)
        rows.append([label, sett(s), (pm(c_["rate"], c_["CI"]) if c_ else "&ndash;"), pm(s["EV_month"], s["CI"]), f"{pct(s['P'], 1)} &plusmn; {pct(p_ci(s), 1)}", usd(s["Vf"]), f"{s['days']:.1f}", sgn(s["EV"])])
    add("<strong>Plan</strong>", sp["prog"], sp["instr"])
    for p, i in sp.get("alts", []):
        add(f"{short(p)}, {MSHORT[i]}", p, i)
    v8 = fin8(sp["prog"], sp["instr"])
    return table(["Setting", "Risk / k / m / X", "Long-run EV/month: continuing slot (95%)", "Random-start ratio (95%)", "Pass rate (95%)", "Cash per funded account", "Days per attempt", "Value of an attempt"],
                 rows, cls="small", hl=hl,
                 cap="One 100K account; each row's own chosen setting. Continuing slot: 12 slots run back to back on each of 16 new paths (151&ndash;166), years 2&ndash;9 (8.3). Random-start ratio and the other columns: sixteen fresh paths (121&ndash;136), 24,000 attempts. Cluster-robust 95% intervals (8.4)." +
                     (f" Version 8 reported {usd(v8['EV_month'])} a month (random-start) for this programme under its rules and engine." if v8 else ""))

def trade_section(sp, ch, F):
    prog, instr = sp["prog"], sp["instr"]
    m, k, L = ch["m"], ch["k"], ch["L"]
    w1 = _first_win(F, ch)
    lv = F.get("lev")
    T = trade_numbers(instr, m, L, w1, lev=lv)
    wf = funded_win(F, ch); Lf = risk_for(F, ch, wf)
    Tf = trade_numbers(instr, m, Lf, wf, lev=lv)
    unit = T["unit"]; units = unit + "s"
    price = PRICE[instr]
    pstr = f"{price:,.2f}" if price > 100 else f"{price:.4f}"
    lines = [f"Risk \\(l = \\${L:,.0f}\\); stop \\(s = m\\sigma = {m:g} \\times {SIG[instr] * 100:.4f}\\% = {T['s'] * 100:.4f}\\%\\) of the price; at {pstr} that is <strong>{T['stop_pts']:.1f} {units}</strong>.",
             f"Notional \\(N = l/s = \\${T['N']:,.0f}\\); <strong>\\(\\${T['usd_per_pt']:,.2f}\\) per {unit}</strong>; at {usd(T['lot_value'], 2)} per {unit} per lot, {T['lots']:.3f} lots, rounded down to <strong>{T['vol']:.2f} " + ("contracts" if instr == "MNQ_fut" else "lots") + f"</strong>, a risk of \\(\\${T['l_round']:,.2f}\\) at the stop (10.1; the figures below are unrounded).",
             f"Cost \\(c = \\kappa N = \\${T['c']:,.2f}\\), \\(\\rho = c/l = {T['rho'] * 100:.2f}\\%\\); the risk is sized so that \\(l(1+\\rho)\\) fits the room (5.4).",
             f"First trade of phase 1: \\(w = \\min(k\\,l,\\ A_1,\\ \\text{{caps}}) = \\${w1:,.0f}\\); take-profit \\({T['tgt_pts']:.1f}\\) {units} away; \\(p = l/(l+w+c) = {T['p']:.4f}\\).",
             f"Mean \\(-c\\); variance \\(l(w+c) = {T['var']:,.0f}\\); duration about {T['dur']:.2f} h of open market (losers {T['dur_loss']:.2f} h, winners {T['dur_win']:.1f} h), cut at 20:00 UTC.",
             (f"A full funded win, with every cap the engine applies (the plan's 40%, the firm's best-day share, day cap or ceiling): \\(\\${wf:,.0f}\\) at risk \\(\\${Lf:,.0f}\\)" + (f" (lowered from \\(\\${L:,.0f}\\) so that the reward:risk is at least 1:{F['funded']['min_rr']:g})" if Lf < L - 0.5 else "") + f": take-profit {Tf['tgt_pts']:,.0f} {units} away, \\(p = {Tf['p']:.4f}\\).")]
    if lv:
        lines.append(f"Margin at the funded leverage 1:{T['lev']}: \\(\\${T['margin']:,.0f}\\) = {pct(T['margin_pct'])} of the starting balance (limit {pct(T['cap'], 0)}); smallest stop \\(m_{{\\min}} = {T['m_min']:.3f}\\).")
    return _calc(lines)

def phases_section(sp, ch, F, e):
    out = []
    for j, (st, ph) in enumerate(zip(F["phases"], e["phases"])):
        A, B = st["target"], st["dd"]
        out.append(f"<h3 class='sub'>Phase {j + 1}: \\(A = \\${A:,.0f}\\), \\(B = \\${B:,.0f}\\)</h3>")
        why = [f"every win at most {usd(ph['cap'])}" if ph.get("cap") else ""]
        if st.get("profit_days"): why.append(f"{st['profit_days'][0]} profitable days needed: the engine aims at a daily target (6.4), which the chain leaves out")
        if st.get("min_days"): why.append(f"{st['min_days']} trading days (" + ("ordinary trades only; the 40% policy already needs three winning days" if F.get("no_fillers") else "0.01-lot filler trades held 3 minutes in the engine") + ")")
        out.append(_calc([f"Chain (5.5): \\(P_{j + 1} = {ph['P']:.4f}\\), \\(\\mathbb{{E}}[\\text{{trades}}] = {ph['N']:.2f}\\), \\(K = \\${ph['Ecost']:,.0f}\\), \\(\\mathbb{{E}}[X_\\text{{end}}\\mid\\text{{fail}}] = {td(ph['X_fail'])}\\); "
                          f"identity gap {ph['identity_gap']:+.4f}; textbook \\((B-K)/(A+B) = {ph['P_textbook']:.4f}\\); zero cost, exact landing \\(B/(A+B) = {B / (A + B):.4f}\\).",
                          "Rules in play: " + "; ".join(x for x in why if x) + "." if any(why) else ""]))
        if st.get("dll"):
            bs = F.get("buffer_scale", 1.0); rho = e["rho"]; L = ch["L"]
            nfull = int((st['dll'] - 200 * bs) // (L * (1 + rho)))
            out.append(f"<p>Daily loss limit {usd(st['dll'])}: each trade's risk plus cost fits today's room less {usd(200 * bs)}; after {nfull} full losses in one day the remaining room is smaller than a full trade, so the plan trades smaller or waits until tomorrow.</p>")
    prod = " \\times ".join("%.4f" % ph["P"] for ph in e["phases"])
    out.append(f"<p><strong>Both phases:</strong> \\(P = {prod} = {e['P']:.4f}\\) (chain, whose phases are calendar-free and independent; 6.1). Engine with every rule, both phases in sequence on one path (so \\(P_2\\) is the conditional chance given phase 1), fresh paths: <strong>{ch['P']:.4f} &plusmn; {p_ci(ch):.4f}</strong> (cluster-robust).</p>")
    return "".join(out)

def funded_section(sp, ch, F, e):
    fd = F["funded"]; D = fd["dd"]; a = fd["split"]; R = fd.get("refund", 0) or 0
    X1, X = ch["X1"], ch["X"]
    q1 = e["q1"]; q = e["q"] if e["q"] is not None else q1
    lines = [f"Allowance \\(D = \\${D:,.0f}\\); payout targets \\(X_1 = \\${X1:,.0f}\\)" + (f", \\(X = \\${X:,.0f}\\)" if abs(X - X1) > 1 else "") + f"; split {pct(a, 0)}; per-trade cap \\(\\${AN.caps_funded(fd, X):,.0f}\\).",
             f"Cycle success chances: \\(q_1 = {q1:.4f}\\)" + (f", later \\(q = {q:.4f}\\)" if abs(q - q1) > 1e-6 else "") + f"; expected paid cycles {e['n_paid']:.4f}; expected withdrawn before the split \\(\\${e['withdrawn']:,.0f}\\).",
             f"Identity (7.1): \\(-\\mathbb{{E}}[X_\\text{{end}}] - \\mathbb{{E}}[\\text{{cost}}] = {-e['x_end']:,.0f} - {e['cost_funded']:,.0f} = \\${-e['x_end'] - e['cost_funded']:,.0f}\\) (gap {e['identity_gap']:+.2f}).",
             f"Cash (chain): \\(\\${e['cash_funded']:,.0f}\\) per funded account" + (f", of which the refund term \\(\\${e['cash_funded'] - a * e['withdrawn']:,.0f}\\)." if R else "."),
             f"Engine, fresh paths: <strong>{usd(ch['Vf'])}</strong> per funded account; {pct(ch['P_paid'])} of attempts reach a payout" + (f"; median {ch['t1']:.0f} days from purchase to the first payout of those that do." if ch.get("t1") else ".")]
    if fd.get("caps"): lines.insert(1, "The first payouts are capped at " + ", ".join(usd(c) for c in fd["caps"][:2] if c < 1e9) + " (7.2: two special first cycles).")
    rows = []
    cyc, pr = e["cyc"], e["pr"]
    for j in range(0, 5):
        if j >= len(pr): break
        pj = (1 - pr[0]) if j == 0 else pr[j - 1] - pr[j]
        nom = a * sum(cyc[:j]) + (R if (R and j >= fd.get("refund_after", 1) and not fd.get("refund_split")) else (R * min(j, fd.get("refund_split", 0)) / fd["refund_split"] if fd.get("refund_split") else 0))
        rows.append([str(j), f"{pj:.4f}", usd(e["cash_given"][j]), usd(nom)])
    lines.insert(2, f"A paid cycle pays its balance at success: on average \\(m_1 = \\${e['m1']:,.2f}\\) in the first cycle" + (f" and \\(m = \\${e['m']:,.2f}\\) later" if e.get("m") else "") + " (7.2), not exactly the target.")
    return _calc(lines) + table(["Paid cycles", "Probability", "Mean cash given that many", "Nominal (targets only)"], rows, cls="small", num_from=1,
                                cap="Chain values in its model of independent cycles that each start from zero: mean cash given the number of paid cycles, \\(\\alpha(m_1 + (n-1)m)\\) plus the refund (7.2). The nominal column (targets only) is for comparison; version 8 printed it as the cash.")

def value_section(sp, ch, F, e):
    fee = F["fee"]; att = DAYS_MONTH / ch["days"]
    s = [r for r in sens("cost", sp["prog"], sp["instr"]) if r["cost_mult"] == 1.0]
    s = s[0] if s else None
    lines = [f"Value of an attempt: chain \\(\\mathbb{{E}}[V] = {e['P']:.4f}\\times{e['cash_funded']:,.0f}" + (f" + {e['credits']:,.0f}" if e.get("credits") else "") + f" - {fee:,.2f} = \\${e['EV']:,.0f}\\); engine <strong>\\(\\${ch['EV']:,.0f}\\)</strong>.",
             f"Time (engine): \\(\\mathbb{{E}}[T] = {ch['days']:.2f}\\) days per attempt, so {att:.2f} attempts a month per slot and \\(\\${att * fee:,.0f}\\) of fees a month before refunds.",
             (f"Where the time goes (paths 141&ndash;144): a failed evaluation lasts {s['t_eval_fail']:.1f} days on average; a passed one {s['t_eval_pass']:.1f} days, then {s['t_fund']:.1f} days funded with {s['payouts']:.2f} payouts; {s['trades']:.1f} trades per attempt." if s and s.get("t_fund") is not None else ""),
             f"Random-start ratio (8.3; the search's yardstick): \\(30.44 \\times {ch['EV']:,.0f}/{ch['days']:.2f} = \\${ch['EV_month']:,.0f}\\) &plusmn; {usd(ch['CI'])} (95%, cluster-robust) per account on sixteen fresh paths.",
             (f"Long-run rate of one slot run back to back (8.3; continuing_v9.py, 12 slots on each of 16 new paths, years 2&ndash;9): <strong>{usd(cont(ch)['rate'])}</strong> &plusmn; {usd(cont(ch)['CI'])} a month; this is the figure Part III's allocation uses." if cont(ch) else "")]
    return _calc(lines)

def size_section(sp):
    a = ALLOC[sp["firm"]]
    prog, instr = sp["prog"], sp["instr"]
    rows = []
    for size in (100_000, 200_000, 50_000, 25_000, 10_000, 5_000):
        r = acct_row(prog, instr, size)
        if not r: continue
        F = rules_of(r)
        rows.append([kk(size), short(r["prog"]), sett(r) + ("" if size == 100_000 else " (the 100K setting scaled)"), usd(F["fee"], 2 if F["fee"] % 1 else 0), usd(F["fee"] * 100_000 / size), pm(r["EV_month"], r["CI"]), usd(r["EV_month"] * 100_000 / size)])
    for p, i, s, n in a["full"]:
        if p != prog and "The5ers" in p:
            r = acct_row(p, i, s)
            if not r: continue
            F = rules_of(r)
            rows.append([f"{kk(s)}", short(p), sett(r) + " (New's own setting scaled)", usd(F["fee"]), usd(F["fee"] * 100_000 / s), pm(r["EV_month"], r["CI"]), usd(r["EV_month"] * 100_000 / s)])
    tb = table(["Size", "Programme", "Risk / k / m / X", "Fee", "Fee per $100K", "Long-run EV/month (95%)", "EV/month per $100K"], rows, cls="small", num_from=3,
               cap="Each row names its programme and its setting: other sizes of a programme run its 100K setting scaled in proportion (risk, targets, payout target, safety margins); The5ers' small accounts are New High Stakes accounts with New's own chosen setting scaled, not the plan's 100K programme. Continuing-slot rates (8.3).") if rows else ""
    rv, rn = alloc_value(a["rec"]); fv, fn_ = alloc_value(a["full"])
    rec = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["rec"]) or "not in the recommended plan"
    full = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["full"])
    txt = (f"<p><strong>Per person:</strong> {a['cap']}. <strong>Copying:</strong> {a['copy']}. <strong>The plan:</strong> {rec}" + (f", worth {usd(rv)} a month ({rn} account{'s' if rn > 1 else ''})" if rn else "") +
           (f"; at the firm's full allowance: {full}, worth {usd(fv)} a month ({fn_} accounts)." if full else "."))
    return tb + txt + "</p>"

def sens_section(sp, ch):
    rows = []
    cs = sorted(sens("cost", sp["prog"], sp["instr"]), key=lambda r: r["cost_mult"])
    for r in cs:
        rows.append([f"&times; {r['cost_mult']:g}", pm(r["EV_month"], r["CI"]), sgn(r["EV"]), f"{r['days']:.1f}", pct(r["P"])])
    if not rows: return ""
    return table(["Trading cost", "EV/month (95%)", "Value of an attempt", "Days per attempt", "Pass rate"], rows, cls="small", num_from=1,
                 cap="The plan's setting with every round-trip cost multiplied (spread, commission, slippage), 12,000 attempts on paths 141&ndash;144 with the same random numbers in every row. "
                     "Higher cost lowers the value of an attempt and can also shorten it (more attempts fail sooner), so the value per month need not fall in proportion.")

def plan_section(sp):
    sh = SHEET[sp["sheet"]]
    items = "".join(f"<li>{x}</li>" for x in sh["plan"])
    return f"<ul>{items}</ul><p class='note'>Sources: {sh['sources']}.</p>"

def prog_chapter(num, sp):
    if sp.get("fut"): return fut_chapter(num, sp)
    prog, instr = sp["prog"], sp["instr"]; sh = SHEET[sp["sheet"]]
    ch = fin(prog, instr); F = rules_of(ch)
    e = chain_of(ch); cr = acct_row(prog, instr, ch["size"])
    rv, rn = alloc_value(ALLOC[sp["firm"]]["rec"])
    head = (f'<section class="chapter"><span class="eyebrow">Chapter {num} &middot; tier {tier(prog)}</span><h1>{sh["title"]}</h1>'
            f'<p>{MNAME[instr]}; plan setting: risk {pct(ch["L"] / ch["size"], 2)}, \\(k = {ch["k"]:g}\\), \\(m = {ch["m"]:g}\\), payout target {xpct(ch["X"] / ch["size"])} of the account; '
            f'<strong>{usd(cr["EV_month"])} a month per 100K</strong> (&plusmn; {usd(cr["CI"])}, long-run rate of a continuing slot); in the plan: '
            + ("; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in ALLOC[sp['firm']]['rec']) or "not in the recommended plan") + (f", {usd(rv)} a month." if rn else ".") + "</p>")
    parts = [head,
             f"<h2>{num}.1 The rules</h2>", rules_table(sh),
             f"<h2>{num}.2 What the engine simulates</h2>", model_table(F, prog),
             f"<h2>{num}.3 The search</h2>", search_section(sp),
             f"<h2>{num}.4 The chosen setting, on fresh paths</h2>", settings_table(sp),
             f"<h2>{num}.5 One trade</h2>", trade_section(sp, ch, F),
             f"<h2>{num}.6 The evaluation</h2>", phases_section(sp, ch, F, e),
             f"<h2>{num}.7 The funded account</h2>", funded_section(sp, ch, F, e),
             f"<h2>{num}.8 Value per attempt and per month</h2>", value_section(sp, ch, F, e),
             f"<h2>{num}.9 Account size and number of accounts</h2>", size_section(sp),
             f"<h2>{num}.10 If costs are higher</h2>", sens_section(sp, ch),
             f"<h2>{num}.11 How the plan meets the rules</h2>", plan_section(sp), "</section>"]
    return "\n".join(parts)

def fut_chapter(num, sp):
    prog, instr = sp["prog"], sp["instr"]; sh = SHEET[sp["sheet"]]
    ch = fin(prog, instr, size=50_000)
    F = rules_of(ch)
    fr = sorted([r for r in FUTJ if r["prog"] == prog and r.get("stage") == "refine"], key=lambda r: -r["EV_month"])[:8]
    T = trade_numbers(instr, ch["m"], ch["L"], min(ch["k"] * ch["L"], 0.4 * F["phases"][0]["target"]))
    contracts = max(1, math.floor(ch["L"] / (2.0 * 31070.0 * ch["m"] * SIG[instr]) + 1e-9))
    rows = [[f"{r['k']:g}", f"{r['m']:g}", usd(r["L"]), pm(r["EV_month"], ci_of(r)), pct(r["P"]), f"{r['days']:.1f}"] for r in fr]
    full = ALLOC[sp["firm"]]["full"]
    nfull = full[0][3] if full else 0
    out = [f'<section class="chapter"><span class="eyebrow">Chapter {num} &middot; tier {tier(prog)} &middot; optional futures layer</span><h1>{sh["title"]}</h1>',
           f"<p>Micro Nasdaq futures in whole contracts, shared direction with the Nasdaq CFD accounts. Futures firms set no percentage risk rule, so the risk per trade is searched as well.</p>",
           f"<h2>{num}.1 The rules</h2>", rules_table(sh), f"<h2>{num}.2 What the engine simulates</h2>", model_table(F, prog),
           f"<h2>{num}.3 The search</h2>", table(["k", "m", "Risk", "Refined EV/month", "Pass rate", "Days"], rows, cls="small", num_from=0,
                                                 cap="The ten best grid settings (4,000 attempts each), re-run for 16,000 attempts on paths 111&ndash;114."),
           f"<h2>{num}.4 The chosen setting</h2>",
           _calc([f"Plan: \\(k = {ch['k']:g}\\), \\(m = {ch['m']:g}\\), risk \\(\\${ch['L']:,.0f}\\): at the reference level of 31,070 the stop is {T['stop_pts']:.1f} points and one MNQ contract loses \\(\\${2 * T['stop_pts']:,.0f}\\) at the stop, so {contracts} contracts (rounded down), a risk of \\(\\${contracts * 2 * T['stop_pts']:,.0f}\\); the engine recomputes this at every entry from the path's price (10.1).",
                  f"Fresh paths: {pm(ch['EV_month'], ch['CI'])} a month per account as a random-start ratio (pass rate {pct(ch['P'])} &plusmn; {pct(p_ci(ch))}, {ch['days']:.1f} days per attempt)" + (f"; long-run rate of a continuing slot (whose price level and calendar carry from attempt to attempt): <strong>{pm(cont(ch)['rate'], cont(ch)['CI'])}</strong>." if cont(ch) else "."),
                  "Why so little: the funded account's maximum loss trails the balance, payouts are capped per request and (Apex) in number, the evaluation fee recurs monthly (Topstep) or is worth paying only at a deep discount (Apex), and whole contracts make the smallest trade large next to a $2,000 allowance. The static withdrawal identity does not apply to these accounts (7.1); the values are the engine's."]),
           f"<h2>{num}.5 How many</h2><p>{ALLOC[sp['firm']]['cap']}: {nfull} accounts, worth {usd(nfull * acct_row(prog, instr, 50_000)['EV_month'])} a month together. This layer is optional and is not in the recommended plan's headline figure.</p>",
           f"<h2>{num}.6 How the plan meets the rules</h2>", plan_section(sp), "</section>"]
    return "\n".join(out)
