"""Part II of the version 10 document: one chapter per programme in the plan (and the futures layer)."""
import math, collections, json
import numpy as np
from doc10_common import *
from doc10_part1 import short, sett, xpct, _calc, _first_win, _row_steps, funded_win, risk_for
import lockstep_portfolio_v10 as LP

def acct_row(prog, instr, size):
    """a final row with EV_month and CI replaced by the continuing-slot rate (8.3: the average cash per month in years 2-9);
    the random-start ratio stays as EV_month_rs and CI_rs"""
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
    "FTMO": ("no limit on Challenge and Verification accounts; $400,000 per trader or strategy in active FTMO Rewards Accounts (the plan keeps four slots of one account each: Appendix B)", "your own accounts, within the cap"),
    "FundingPips": ("$400,000 across evaluation, funded and Prime accounts", "between your own FundingPips accounts; no copier services (the plan enters each account itself)"),
    "The5ers": ("one 50K or 100K account across Classic and New together; New also 3 &times; 2.5K, 3 &times; 5K, 3 &times; 10K and 1 &times; 25K (Classic's own small slots not used: fees not readable)", "copy trading 'with other traders or accounts' prohibited; your own accounts allowed by the FAQ's descriptions (confirmed in writing before trading: Part IV)"),
    "FXIFY": ("one active account of each size, challenge and funded alike", "allowed with FXIFY's prior approval (asked before trading: Part IV); third-party copying prohibited"),
    "FundedNext": ("$300,000 funded; evaluations unlimited", "between your own challenge accounts, never into a funded account"),
    "Fintokei": ("400,000 EUR/USD of funded ProTrader accounts (evaluations not counted)", "your own trades, from other firms and brokers too"),
    "Hola Prime": ("two 100K funded accounts (or four 50K, or one 200K)", "only between your own Hola Prime accounts (funded: one master and one copier); never from other firms"),
    "Alpha Capital": ("$400,000 per household, $300,000 per strategy", "from your own external accounts with proof"),
    "FunderPro": ("$200,000", "between your own accounts"),
    "GFT": ("$400,000 funded", "between your own accounts, evaluation and funded"),
    "BrightFunded": ("$400,000 funded; evaluations unlimited", "allowed between your own accounts"),
    "Blue Guardian": ("$400,000 across funded accounts", "between your own accounts, at Blue Guardian and elsewhere"),
    "Maven": ("$200,000 of funded accounts; at most $10,000 per 30-day cycle per trader, all accounts together, counted on the date the profit is closed, the excess voided (one account held: the model keeps every 30-day window under it)", "no copying of another person's trades, no account mirroring, no EAs (one account, entered by hand)"),
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
        if r: tot += k * r0(r["EV_month"]); n += k
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
INV_FIRM = {"FTMO": "FTMO", "FundingPips": "FundingPips", "The5ers": "The5ers", "FXIFY": "FXIFY", "FundedNext": "FundedNext", "Fintokei": "Fintokei",
            "Hola Prime": "Hola Prime", "Alpha Capital": "Alpha Capital", "FunderPro": "FunderPro", "GFT": "GFT", "BrightFunded": "BrightFunded",
            "Blue Guardian": "Blue Guardian", "Maven": "Maven", "Topstep": "Topstep", "Apex": "Apex"}
SHEET_KEEP = ("Leverage",)          # fees, refunds and splits are inventory rows (version 10)

def rules_table(sh, firm):
    """the firm's rules from the inventory (rules_inventory_v10.json), with the leverage row of the programme sheet; each row
    with the date its page was read"""
    rows = [[a, b, "4 Oct 2026 (version 9 reading)"] for a, b in sh["rules"] if a in SHEET_KEEP]
    for r in inv_rows(INV_FIRM.get(firm, firm)):
        rows.append([r["area"][0].upper() + r["area"][1:], r["rule"] + (f" <span style='color:var(--muted)'>(model: {r['model']})</span>" if r["status"] in ("cautious", "assumption", "not binding") else ""), r["read"]])
    return table(["Rule", "As published", "Read"], rows, num_from=9, w0="22%",
                 cap="Rules as published, from the inventory of Appendix B, which gives each rule's page, the basis of the reading (the firm's page read directly, its text as a search engine returned it, or a reviewer's description where no page could be read) and how the model treats it; the leverage row is version 9's reading.")

def _fpct(x):
    """a fee in per cent with no needless decimals: 3% or 3.5%"""
    return f"{100 * x:.1f}".rstrip("0").rstrip(".") + "%"

def _split_txt(fd):
    """the split, and a firm's fee on every withdrawal (GFT 3%, The5ers 3.5%, FundedNext up to 3.5%, Blue Guardian 3%, Hola
    Prime 2.5% with at least $5; Maven $20 a payout by Rise): the trader keeps alpha = split x (1 - fee) of the profit
    withdrawn, less any fixed amount"""
    if fd.get("fee_pct"):
        a = fd["split"] * (1 - fd["fee_pct"])
        return (f"{pct(fd['split'], 0)}, less a {_fpct(fd['fee_pct'])} fee on every withdrawal" + (f" (at least {usd(fd['fee_min'])})" if fd.get("fee_min") else "")
                + (", the refund included" if fd.get("refund") else "")
                + f" (the trader keeps \\(\\alpha = {a:.4f}\\)".replace("0\\)", "\\)") + " of the profit withdrawn)")
    if fd.get("fee_min"):
        return (f"{pct(fd['split'], 0)}, less {usd(fd['fee_min'])} from every payout" + (", the one with the refund included" if fd.get("refund") else ""))
    return pct(fd["split"], 0)

def _dll_txt(st, F):
    md = st.get("dll_mode") or ("rel" if st.get("dll_rel") else "fixed"); pc = pct(st["dll"] / F["size"], 0)
    return {"fixed": f"daily loss {usd(st['dll'])} ({pc} of the initial balance) below the day's reference",
            "rel": f"daily loss {pc} of the day's starting balance, recomputed at every reset",
            "min": f"daily loss {pc} of the smaller of the initial and the day's starting balance (base not stated by the firm: the stricter)"}[md]

def model_table(F, prog):
    fut = prog in ("Topstep 50K", "Apex 50K EOD")
    minimal = "a one-contract filler trade held 3 minutes" if fut else "a 0.01-lot filler trade held 3 minutes"
    rows = [["Fee per attempt", usd(F["fee"], 2 if F["fee"] % 1 else 0) + (" a month (renewed while the evaluation lasts)" if F.get("monthly") else "") +
             (f"; activation {usd(F['activation'])} on passing" if F.get("activation") else "")]]
    if F.get("phase_credit"): rows.append(["Fee credit", "non-cash credit of " + " and ".join(usd(c, 2) for c in F["phase_credit"]) + " on passing phase 1 and phase 2, spent on the next evaluation"])
    for j, st in enumerate(F.get("phases", [])):
        bits = [f"target {usd(st['target'])}", f"maximum loss {usd(st['dd'])} below the start, " + ("trailing the best end-of-day balance" if st["eod"] else "static")]
        bits.append(_dll_txt(st, F) if st.get("dll") else "no daily loss limit")
        if st.get("min_days"): bits.append(f"at least {st['min_days']} trading day{'s' if st['min_days'] != 1 else ''}" + (" (no filler trades: ordinary trades, one a day, if days are missing)" if F.get("no_fillers") else f" (a missing day: {minimal})"))
        if st.get("news"): bits.append("flat around " + ("US CPI releases" if st["news"] == "cpi" else "high-impact releases") + " (6.5)")
        if st.get("profit_days"): bits.append(f"{st['profit_days'][0]} profitable days of at least {usd(st['profit_days'][1])}")
        if st.get("best"): bits.append(f"best day at most {pct(st['best'], 0)} of the profit")
        if st.get("conc"): bits.append(f"plan: no trade and no day above {pct(st['conc'], 0)} of the target ({usd(st['conc'] * st['target'])})")
        if st.get("min_rr"): bits.append(f"every trade at least 1:{st['min_rr']:g}")
        if st.get("max_days"): bits.append(f"expires at 6 pm New York on day {st['max_days']}, the purchase day counting as day 1" if st.get("expiry_local") else f"expires after {st['max_days']} days")
        rows.append([f"Phase {j + 1}" if len(F["phases"]) > 1 else "Evaluation", "; ".join(bits)])
    fd = F["funded"]
    bits = [f"maximum loss {usd(fd['dd'])}, " + ("trailing the best end-of-day balance" if fd["eod"] else "static"),
            _dll_txt(fd, F) if fd.get("dll") else "no daily loss limit",
            f"split {_split_txt(fd)}"]
    if fd.get("refund"):
        if fd.get("refund_split"): bits.append(f"fee returned in {fd['refund_split']} equal parts with the first {fd['refund_split']} payouts")
        elif F.get("refund_frac") is not None and F["refund_frac"] < 1:
            bits.append(f"{pct(F['refund_frac'], 0)} of the cash paid for the account returned with payout number {fd.get('refund_after', 1)} ({usd(fd['refund'], 2)} when no hub credit paid part of the fee)")
        else: bits.append(f"{usd(fd['refund'], 2)} of the fee returned with payout number {fd.get('refund_after', 1)}")
    else: bits.append("no fee refund")
    if fd.get("q_days"): bits.append(f"a payout needs {fd['q_days']} qualifying days of at least {usd(fd['q_min'])}")
    elif fd.get("ondemand"): bits.append("payouts on demand")
    else: bits.append(f"first payout {fd['first_payout']} days after the first funded trade, then every {fd['cycle']} days")
    if fd.get("best_vs_worst"): bits.append("a request needs the best trade to have made more than the worst trade lost, since the last payout and over the account (the firm's rule for accounts bought from 9 October 2026)")
    fee_any = fd.get("fee_pct") or fd.get("fee_min")
    if fd.get("min_net") and fd.get("min_payout") and fd["min_payout"] > fd["min_net"] + 1e-9:
        bits.append(f"a request needs {usd(fd['min_payout'])} of profit before the split and {usd(fd['min_net'])} of share after it" + (" and the fee" if fee_any else "") + " (the firm's statement)")
    elif fd.get("min_net") or fd.get("min_payout"):
        bits.append(f"minimum payout {usd(fd.get('min_net') or fd['min_payout'])} on the trader's share after the split" + (" and the fee" if fee_any else "") + " (at least as strict as any reading of the firm's wording)")
    if fd.get("caps"):
        cps = [c for c in fd["caps"] if c < 1e9]
        if len(set(cps)) == 1 and len(cps) > 6: bits.append(f"every payout at most {usd(cps[0])}" + (" with the fee refund counted inside it" if fd.get("cap_includes_refund") else "") + ", the rest kept in the account")
        else: bits.append("payout caps " + ", ".join(usd(c) for c in cps[:6]) + (" for the first payouts" if len(cps) < 6 else "") + ", the rest kept in the account")
    if fd.get("min_profit"): bits.append(f"a request needs {usd(fd['min_profit'])} of profit")
    if fd.get("pct_bal"): bits.append(f"a payout at most {pct(fd['pct_bal'], 0)} of the balance")
    if fd.get("best"): bits.append((f"best day below {pct(fd['best'], 0)} of a payout's profit (strictly)" if fd.get("q_days") else f"best day at most {pct(fd['best'], 0)} of a payout's profit") + (", measured against the account's best day ever" if fd.get("best_ever") else ""))
    if fd.get("first_days"): bits.append(f"first payout only after {fd['first_days']} trading days (no fillers; the plan trades at most once a day until then)")
    if fd.get("cycle_days"): bits.append(f"{fd['cycle_days']} trading days in every payout cycle" + (" (no filler trades: ordinary trades, one a day, while days are missing)" if F.get("no_fillers") else " (filler trades)"))
    if fd.get("cycle_from_processed"): bits.append("the next payout 14 days after the last one was processed")
    if fd.get("profit_days_window"): bits.append(f"the profitable days within {fd['profit_days_window']} calendar days ending on the request day")
    if fd.get("profit_ceiling"):
        if prog.startswith("Maven"): bits.append(f"plan: funded profit never above {usd(fd['profit_ceiling'])}, a margin under the $5,000 above which the firm's 50% rule applies")
        else: bits.append(f"plan: the balance kept under +{pct(fd['profit_ceiling'] / F['size'], 1)}, below the +10% at which the account scales")
    if fd.get("roll_profit_cap"): bits.append(f"plan: closed profit in any {fd['roll_profit_cap'][1]} days never above {usd(fd['roll_profit_cap'][0])} (the firm voids profit above {usd(fd['roll_profit_cap'][0])} per {fd['roll_profit_cap'][1]}-day cycle per trader, counted on the date the profit is closed; every window kept under it meets the rule however the cycles are anchored)")
    if fd.get("min_rr"): bits.append(f"every trade at least 1:{fd['min_rr']:g}")
    if fd.get("day_profit_cap"): bits.append(f"profit above {usd(fd['day_profit_cap'])} a day not counted")
    if fd.get("profit_days"): bits.append(f"{fd['profit_days'][0]} profitable days of {usd(fd['profit_days'][1])}+ per cycle")
    if fd.get("need_profit"): bits.append("each later payout needs net profit since the last")
    if fd.get("max_payouts"): bits.append(f"at most {fd['max_payouts']} payouts")
    if fd.get("buffer"): bits.append(f"buffer {usd(fd['buffer'])} kept in the account")
    if fd.get("conc"): bits.append(f"plan: no trade and no day above {pct(fd['conc'], 0)} of the payout target")
    if fd.get("shield"): bits.append(f"Guardian Shield: open trades closed at a floating loss of {usd(fd['shield'])}; the first time the split falls to {pct(fd.get('shield_split', 0.5), 0)}, the second time the account is breached")
    if fd.get("max_lots"): bits.append(f"at most {fd['max_lots']:g} open lots")
    if fd.get("void_min"): bits.append(f"a winning trade held under {fd['void_min']:g} minute has its profit removed")
    if fd.get("news"): bits.append("flat around " + ("US CPI releases" if fd["news"] == "cpi" else "high-impact releases") + " (6.5)")
    rows.append(["Funded account", "; ".join(bits)])
    if F.get("no_terminal"):
        rows.append(["Near the floor", "no last trade to the floor, at either stage (the firm prohibits 'all or nothing' trading): an account whose room above its floor falls below the smallest normal risk is left as it is and its slot buys the next evaluation (5.4)"])
    pp = []
    if fd.get("req_wait"): pp.append(f"a request at least {60 * fd['req_wait']:.0f} minutes after the last close, flat")
    if fd.get("session_tz"): pp.append("made one minute after the 4 p.m. Chicago lock of a qualifying session")
    if fd.get("protected"): pp.append("deducted at once and protected from a later breach")
    elif fd.get("review_bd") or fd.get("review_h"):
        parts = ([f"{fd['review_bd']} working day" + ("s" if fd["review_bd"] != 1 else "")] if fd.get("review_bd") else []) + \
                ([f"{fd['review_h']:g} hour" + ("s" if fd["review_h"] != 1 else "")] if fd.get("review_h") else [])
        pp.append("pending " + " and ".join(parts) + (" (assumed)" if prog.startswith("Maven") else ""))
    else: pp.append("processed at once")
    if fd.get("lock_processing"): pp.append("the account locked until processed")
    elif fd.get("pause_pending"): pp.append("the plan pauses the account until processed")
    elif not fd.get("protected") and (fd.get("review_bd") or fd.get("review_h")): pp.append("trading continues; a breach before processing cancels the request")
    pp.append(f"cash {fd.get('transfer_bd', 0)} working day" + ("s" if fd.get("transfer_bd", 0) != 1 else "") + " after processing")
    if fd.get("cycle_from_processed"): pp.append("the next cycle counted from the processing")
    rows.append(["Payout processing", "; ".join(pp) + " (6.6)"])
    if F.get("flat_daily"): rows.append(["Trading hours", f"positions opened at the hourly opens from 01:00 UTC (07:00 on EURUSD) to {F['flat_daily'] - 2}:00 UTC, flat at {F['flat_daily']}:00 UTC every day; flat at weekends; at least 10 minutes between a close and the next entry; no stop or target closer than 0.6 hourly sd"])
    rows.append(["Positions", ("whole micro contracts, rounded down, never fewer than one" if fut else "whole volume steps of 0.01 lot, rounded down; the smallest position traded only where the rooms allow it") + "; the account's breach level (floor or today's limit, the nearer) is a barrier of every trade; reviews and payout processing in working days"])
    dur = []
    if F.get("hold_min"): dur.append(f"the bracket is placed {F['hold_min']} minutes after the entry (minimum holding time 2 minutes); until then only the breach level" + (" and the Guardian Shield" if F["funded"].get("shield") else "") + " can close the position, and a trade closed in under 2 minutes ends the account in the engine (the cautious reading of 'may be flagged for tick scalping')")
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
            f'<p class="cap">Grid value per month ($ thousands; 2,000 attempts each on paths 1101&ndash;1104, so &plusmn;${np.percentile([r["CI"] for r in rs], 10) / 1000:.1f}&ndash;{np.percentile([r["CI"] for r in rs], 90) / 1000:.1f}K for most cells) at risk {usd(L)} and stop m = {m:g}, by k (rows) and payout target X (columns). '
            f'Darker is more. The chosen setting is in the table above it, re-measured on fresh paths.</p>')

def search_section(sp):
    prog, instr = sp["prog"], sp["instr"]
    ng = sum(1 for r in GRID if r["prog"] == prog); nr = sum(1 for r in REF if r["prog"] == prog)
    instrs = sorted({r["instr"] for r in GRID if r["prog"] == prog})
    rs = sorted(refs(prog, instr), key=lambda r: -r["EV_month"])[:8]
    ch = fin(prog, instr)
    hl = [i for i, r in enumerate(rs) if ch and (abs(r["m"] - ch["m"]) < 1e-9 and r["k"] == ch["k"] and abs(r["X"] - ch["X"]) < 1 and abs(r["L"] - ch["L"]) < 1)]
    lmax = O.L_MAX.get(firm_of(prog))
    elig = lambda r: r["m"] + 1e-9 >= O.CAP_M and r["X"] <= O.CAP_X * r["size"] + 1 and (lmax is None or r["L"] <= lmax * r["size"] + 1)
    rows = [[pct(r["L"] / r["size"], 2) + ("" if elig(r) else "*"), f"{r['k']:g}", f"{r['m']:g}", xpct(r["X"] / r["size"]), pm(r["EV_month"], ci_of(r)), pct(r["P"]), f"{r['days']:.1f}"] for r in rs]
    out = [f"<p>Searched: {ng:,} grid settings ({', '.join(MSHORT[i] for i in instrs)}; 2,000 attempts each) and {nr:,} refined settings (16,000 attempts each, paths 1111&ndash;1114). The eight best refined settings on {MSHORT[instr]}"
           + (" (* not eligible: above the firm's own risk guidance, 10.5)" if any(not elig(r) for r in rs) else "") + ":</p>",
           table(["Risk", "k", "m", "X", "EV/month (95%)", "Pass rate", "Days per attempt"], rows, cls="small", hl=hl, num_from=0),
           note("Refine-path values, chosen as the best of many, so biased upward; the plan reports the fresh-path run below. "
                + (lambda pdd: (f"The settings share paths and random numbers, so the ranking is judged on paired differences, not on overlapping intervals: the best eligible setting against the next, paired over the four paths, {sgn(pdd[0])} &plusmn; {usd(pdd[1])} a month (Student t, 3 degrees of freedom)"
                                + (", so the refinement cannot tell them apart." if abs(pdd[0]) <= pdd[1] else ".")) if pdd else "")(
                    (lambda el: paired_diff(el[0], el[1]) if len(el) > 1 else None)([r for r in rs if elig(r)])))]
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
    v9 = fin9(sp["prog"], sp["instr"])
    return table(["Setting", "Risk / k / m / X", "Continuing-slot rate, years 2&ndash;9 (95%)", "Random-start ratio (95%)", "Pass rate (95%)", "Cash per funded account", "Days per attempt", "Value of an attempt"],
                 rows, cls="small", hl=hl,
                 cap="One 100K account; each row's own chosen setting. Continuing-slot rate: 12 slots run back to back on each of 16 new paths (1151&ndash;1166), the average cash per month in years 2&ndash;9 (8.3). Random-start ratio and the other columns: 24,000 attempts started at random points of sixteen fresh paths (1121&ndash;1136), each trade's direction a coin flip (the continuing slots and the portfolio use the plan's own direction rule). Cluster-robust 95% intervals (8.4)." +
                     (f" Version 9 reported {usd(v9['EV_month'])} a month (random-start) for this programme under its rules and engine (Chapter 9.4 lists what changed)." if v9 else ""))

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
    stop_txt = (f"at {pstr} that is <strong>{T['stop_pts_long']:.1f} {units}</strong> below the entry for a long USDJPY position and {T['stop_pts_short']:.1f} above it for a short (the dollar value of a yen, \\(X = 1/\\text{{USDJPY}}\\), is the martingale and moves by \\(s\\): 3.2)"
                if instr == "USDJPY" else f"at {pstr} that is <strong>{T['stop_pts']:.1f} {units}</strong>")
    lines = [f"Risk \\(l = \\${L:,.0f}\\); stop \\(s = m\\sigma = {m:g} \\times {SIG[instr] * 100:.4f}\\% = {T['s'] * 100:.4f}\\%\\) of the price; {stop_txt}.",
             f"Notional \\(N = l/s = \\${T['N']:,.0f}\\); <strong>" + ("about " if instr == "USDJPY" else "") + f"\\(\\${T['usd_per_pt']:,.2f}\\) per {unit}</strong>; at {usd(T['lot_value'], 2)} per {unit} per lot, {T['lots']:.4f} lots, rounded down to <strong>{T['vol']:.2f} " + ("contracts" if instr == "MNQ_fut" else "lots") + f"</strong>, a risk of \\(\\${T['l_round']:,.2f}\\) at the stop (10.1; the figures below are unrounded).",
             f"Cost \\(c = \\kappa N = \\${T['c']:,.2f}\\), \\(\\rho = c/l = {T['rho'] * 100:.2f}\\%\\); the risk is sized so that \\(l(1+\\rho)\\) fits the room (5.4).",
             f"First trade of phase 1: \\(w = \\min(k\\,l,\\ A_1,\\ \\text{{caps}}) = \\${w1:,.0f}\\); take-profit " + (f"\\({T['tgt_pts_long']:.1f}\\) {units} above the entry for a long ({T['tgt_pts_short']:.1f} below for a short)" if instr == "USDJPY" else f"\\({T['tgt_pts']:.1f}\\) {units} away") + f"; \\(p = l/(l+w+c) = {T['p']:.4f}\\).",
             f"Mean \\(-c\\); variance \\(l(w+c) = {T['var']:,.0f}\\); duration about {T['dur']:.2f} h of open market (losers {T['dur_loss']:.2f} h, winners {T['dur_win']:.1f} h), cut at 20:00 UTC.",
             (f"A full funded win, with every cap the engine applies (the plan's 40%, the firm's best-day share, day cap or ceiling): \\(\\${wf:,.0f}\\) at risk \\(\\${Lf:,.0f}\\)" + (f" (lowered from \\(\\${L:,.0f}\\) so that the reward:risk is at least 1:{F['funded']['min_rr']:g})" if Lf < L - 0.5 else "") + (f": take-profit {Tf['tgt_pts_long']:,.0f} {units} above the entry for a long ({Tf['tgt_pts_short']:,.0f} below for a short), \\(p = {Tf['p']:.4f}\\)." if instr == "USDJPY" else f": take-profit {Tf['tgt_pts']:,.0f} {units} away, \\(p = {Tf['p']:.4f}\\)."))]
    if lv:
        lines.append(f"Margin at the funded leverage 1:{T['lev']}: \\(\\${T['margin']:,.0f}\\) = {pct(T['margin_pct'])} of the starting balance (limit {pct(T['cap'], 0)}); smallest stop \\(m_{{\\min}} = {T['m_min']:.3f}\\).")
    return _calc(lines)

def phases_section(sp, ch, F, e):
    out = []
    bs = F.get("buffer_scale", 1.0)
    for j, (st, ph) in enumerate(zip(F["phases"], e["phases"])):
        A, B = st["target"], st["dd"]
        At = A + (20.0 * bs if st.get("min_days") and not F.get("no_target_buffer") else 0.0)    # the target the engine trades to (6.3)
        out.append(f"<h3 class='sub'>Phase {j + 1}: \\(A = \\${A:,.0f}\\), \\(B = \\${B:,.0f}\\)" + (f"; the engine trades to \\(A' = A + \\${At - A:,.0f} = \\${At:,.0f}\\) (6.3)" if At > A else "") + "</h3>")
        why = [f"every win at most {usd(ph['cap'])}" if ph.get("cap") else ""]
        if st.get("profit_days"): why.append(f"{st['profit_days'][0]} profitable days needed: the engine aims at a daily target (6.4), which the chain leaves out")
        if st.get("min_days"): why.append(f"{st['min_days']} trading day{'s' if st['min_days'] != 1 else ''} (" + ("ordinary trades only; the 40% policy already needs three winning days" if F.get("no_fillers") else ("one-contract" if sp.get("fut") else "0.01-lot") + " filler trades held 3 minutes in the engine") + ")")
        if st.get("news"): why.append("flat around " + ("US CPI releases" if st["news"] == "cpi" else "high-impact releases") + " in the engine (6.5)")
        (dK,), Ptb = chain(lambda K_: (B - K_) / (At + B), [ph["Ecost"]], [0], out_dec=4)
        tb = (f"textbook \\((B-K)/(A'+B) = ({B:,.0f} - {ph['Ecost']:,.{dK}f})/{At + B:,.0f} = {Ptb:.4f}\\)" if At > A else
              f"textbook \\((B-K)/(A+B) = ({B:,.0f} - {ph['Ecost']:,.{dK}f})/{A + B:,.0f} = {Ptb:.4f}\\)")
        out.append(_calc([f"Chain (5.5): \\(P_{j + 1} = {ph['P']:.4f}\\), \\(\\mathbb{{E}}[\\text{{trades}}] = {ph['N']:.2f}\\), \\(K = \\${ph['Ecost']:,.{dK}f}\\), \\(\\mathbb{{E}}[X_\\text{{end}}\\mid\\text{{fail}}] = {td(ph['X_fail'])}\\); "
                          f"the solver's identity gap {ph['identity_gap']:+.4f}; {tb}; zero cost, exact landing on the firm's target, \\(B/(A+B) = {B / (A + B):.4f}\\).",
                          "Rules in play: " + "; ".join(x for x in why if x) + "." if any(why) else ""]))
        if st.get("dll"):
            rho = e["rho"]; L = ch["L"]
            nfull = int((st['dll'] - 200 * bs) // (L * (1 + rho)))
            rel = (st.get("dll_mode") or ("rel" if st.get("dll_rel") else "fixed")) != "fixed"
            out.append(f"<p>Daily loss limit {usd(st['dll'])}" + (" at the starting balance (it is recomputed from each day's reference, 6.2)" if rel else "") + f": each trade's risk plus cost fits today's room less {usd(200 * bs)}; after {nfull} full loss{'es' if nfull != 1 else ''} in one day the remaining room is smaller than a full trade, so the plan trades smaller or waits until tomorrow.</p>")
    Ps = [ph["P"] for ph in e["phases"]]
    if len(Ps) == 2:
        (d1, d2), Pp = chain(lambda a_, b_: a_ * b_, Ps, [4, 4], out_dec=4)
        prod = f"{Ps[0]:.{d1}f} \\times {Ps[1]:.{d2}f} = {Pp:.4f}"
    else:
        prod = f"{Ps[0]:.4f}"
    out.append(f"<p><strong>{'Both phases' if len(Ps) == 2 else 'The evaluation'}:</strong> \\(P = {prod}\\) (chain" + (", whose phases are calendar-free and independent; 6.1" if len(Ps) == 2 else "") + f"). Engine with every rule" + (", both phases in sequence on one path (so \\(P_2\\) is the conditional chance given phase 1)" if len(Ps) == 2 else "") + f", fresh paths: <strong>{ch['P']:.4f} &plusmn; {p_ci(ch):.4f}</strong> (cluster-robust).</p>")
    return "".join(out)

def funded_section(sp, ch, F, e):
    fd = F["funded"]; D = fd["dd"]; g_fee = 1.0 - fd.get("fee_pct", 0.0)
    a = fd["split"] * g_fee; R = (fd.get("refund", 0) or 0) * g_fee      # the trader's share and refund, net of a payout fee
    X1, X = ch["X1"], ch["X"]
    q1 = e["q1"]; q = e["q"] if e["q"] is not None else q1
    caps = [c for c in (fd.get("caps") or []) if c < 1e9]
    (dx, dco), W2 = chain(lambda x_, c_: x_ - c_, [-e["x_end"], e["cost_funded"]], [0, 0], out_dec=0)
    lines = [f"Allowance \\(D = \\${D:,.0f}\\); payout targets \\(X_1 = \\${X1:,.0f}\\)" + (f", \\(X = \\${X:,.0f}\\)" if abs(X - X1) > 1 else "") + f"; split {_split_txt(fd)}; per-trade cap \\(\\${AN.caps_funded(fd, X):,.0f}\\).",
             f"Cycle success chances in the chain: \\(q_1 = {q1:.4f}\\)" + (f", later \\(q = {q:.4f}\\)" if abs(q - q1) > 1e-6 else "") + f"; expected paid cycles {e['n_paid']:.4f}; expected balance taken out of the account at successes \\(\\${e['withdrawn']:,.0f}\\).",
             f"Identity (7.1): \\(-\\mathbb{{E}}[X_\\text{{end}}] - \\mathbb{{E}}[\\text{{cost}}] = {-e['x_end']:,.{dx}f} - {e['cost_funded']:,.{dco}f} = \\${W2:,.0f}\\) (the solver's gap {e['identity_gap']:+.2f}).",
             f"Cash (chain): \\(\\${e['cash_funded']:,.0f}\\) per funded account" + (f", of which the refund term \\(\\${R * (sum(e['pr'][:fd['refund_split']]) / fd['refund_split'] if fd.get('refund_split') else e['pr'][fd.get('refund_after', 1) - 1]):,.0f}\\)." if R else "."),
             f"Engine, fresh paths: <strong>{usd(ch['Vf'])}</strong> per funded account; {pct(ch['P_paid'])} of attempts reach a payout" + (f"; median {ch['t1']:.0f} days from purchase to the first payout's cash for those that do." if ch.get("t1") else ".")]
    if caps:
        lines.insert(1, ("Every payout is capped at " + usd(caps[0]) + (" with the fee refund inside the cap" if fd.get("cap_includes_refund") else "") if len(set(caps)) == 1 and len(caps) > 6 else
                         "The first payouts are capped at " + ", ".join(usd(c) for c in caps[:6])) + "; the chain's cycle targets are capped likewise and a success withdraws the smaller of its balance and the cap (7.2; the excess stays in the account, which the chain's reset cycles leave out and the engine carries).")
    rows = []
    cyc, pr = e["cyc"], e["pr"]
    for j in range(0, 5):
        if j >= len(pr): break
        pj = (1 - pr[0]) if j == 0 else pr[j - 1] - pr[j]
        nom = (sum(AN.A_.payout_net(fd, fd["split"] * c_) for c_ in cyc[:j])     # each payout less the firm's fee (Maven: $20)
               + (R if (R and j >= fd.get("refund_after", 1) and not fd.get("refund_split")) else (R * min(j, fd.get("refund_split", 0)) / fd["refund_split"] if fd.get("refund_split") else 0)))
        rows.append([str(j), f"{pj:.4f}", usd(e["cash_given"][j]), usd(nom)])
    lines.insert(2, (f"A paid cycle withdraws the smaller of its balance at success and the cap: the mean balance at success is \\(\\${e['m1']:,.2f}\\) in the first cycle" if caps else
                     f"A paid cycle pays its balance at success: on average \\(m_1 = \\${e['m1']:,.2f}\\) in the first cycle") + (f" and \\(\\${e['m']:,.2f}\\) later" if e.get("m") else "") + " (7.2), not exactly the target.")
    return _calc(lines) + table(["Paid cycles", "Probability", "Mean cash given that many", "Nominal (targets only)"], rows, cls="small", num_from=1,
                                cap="Chain values in its model of independent cycles that each start from zero: mean cash given the number of paid cycles, the split times the amounts withdrawn (each the smaller of the balance at success and the cap) plus the refund, less any fee the firm takes from every payout (7.2, 7.4). The nominal column (targets only) is for comparison; version 8 printed it as the cash.")

def value_section(sp, ch, F, e):
    fee = F["fee"]
    s = [r for r in sens("cost", sp["prog"], sp["instr"]) if r["cost_mult"] == 1.0]
    s = s[0] if s else None
    pf = per_month_fee(ch["days"], fee)
    rl, _ = rate_line(ch["EV"], ch["days"])
    cr = e.get("credits") or 0.0
    (dP, dC), EVc = chain(lambda P_, C_: P_ * C_ + cr - fee, [e["P"], e["cash_funded"]], [4, 0], out_dec=0)
    ct = cont(ch)
    lines = [f"Value of an attempt: chain \\(\\mathbb{{E}}[V] = {e['P']:.{dP}f}\\times{e['cash_funded']:,.{dC}f}" + (f" + {cr:,.2f}" if cr else "") + f" - {fee:,.2f} = \\${EVc:,.0f}\\)" + (" (the credit at face value; the engine also charges the smaller refund it leaves, 1.2)" if cr else "") + f"; engine <strong>\\(\\${ch['EV']:,.0f}\\)</strong>.",
             f"Time (engine): \\(\\mathbb{{E}}[T] = {pf['T']}\\) days per attempt, so {pf['a']} attempts a month per slot and \\(\\${pf['fee']:,.0f}\\) of fees a month before refunds.",
             (f"Where the time goes (paths 1201&ndash;1204): a failed evaluation lasts {s['t_eval_fail']:.1f} days on average; a passed one {s['t_eval_pass']:.1f} days, then {s['t_fund']:.1f} days funded with {s['payouts']:.2f} payouts; {s['trades']:.1f} trades per attempt." if s and s.get("t_fund") is not None else ""),
             f"Random-start ratio (8.3; the search's yardstick): {rl} &plusmn; {usd(ch['CI'])} (95%, cluster-robust) per account on sixteen fresh paths.",
             (f"Continuing-slot rate (8.3; continuing_v10.py, 12 slots on each of 16 new paths): <strong>{usd(ct['rate'])}</strong> &plusmn; {usd(ct['CI'])} a month in years 2&ndash;9 (years 2&ndash;5 {usd(ct['rate_y2_5'])}, years 6&ndash;9 {usd(ct['rate_y6_9'])}); the figure Part III's choices use." if ct else "")]
    return _calc(lines)

def size_section(sp):
    a = ALLOC[sp["firm"]]
    prog, instr = sp["prog"], sp["instr"]
    rows = []
    def per100(v, size): return r0(v) * 100_000 / size
    for size in (100_000, 200_000, 50_000, 25_000, 15_000, 10_000, 5_000):
        r = acct_row(prog, instr, size)
        if not r: continue
        F = rules_of(r)
        rows.append([kk(size), short(r["prog"]), sett(r) + ("" if size == 100_000 else " (the 100K setting scaled)"), usd(F["fee"], 2 if F["fee"] % 1 else 0), usd(F["fee"] * 100_000 / size), pm(r0(r["EV_month"]), r["CI"]), usd(per100(r["EV_month"], size))])
    for p, i, s, n in a["full"]:
        if p != prog and "The5ers" in p:
            r = acct_row(p, i, s)
            if not r: continue
            F = rules_of(r)
            rows.append([f"{kk(s)}", short(p), sett(r) + " (New's own setting scaled)", usd(F["fee"]), usd(F["fee"] * 100_000 / s), pm(r0(r["EV_month"]), r["CI"]), usd(per100(r["EV_month"], s))])
    tb = table(["Size", "Programme", "Risk / k / m / X", "Fee", "Fee per $100K", "Continuing-slot rate (95%)", "Per $100K"], rows, cls="small", num_from=3,
               cap="Each row names its programme and its setting: other sizes of a programme run its 100K setting scaled in proportion (risk, targets, payout target, safety margins); The5ers' small accounts are New High Stakes accounts with New's own chosen setting scaled, not the plan's 100K programme. Continuing-slot rates (8.3), rounded to the dollar before they are scaled, so the last column is the printed rate times 100K over the size.") if rows else ""
    rv, rn = alloc_value(a["rec"]); fv, fn_ = alloc_value(a["full"])
    rec = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["rec"]) or "not in the recommended plan"
    full = "; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in a["full"])
    txt = (f"<p><strong>Per person:</strong> {a['cap']}. <strong>Copying:</strong> {a['copy']}. <strong>The plan:</strong> {rec}" + (f", worth {usd(rv)} a month ({rn} account{'s' if rn > 1 else ''})" if rn else "") +
           (f"; at the largest allocation the plan models (one account per slot, Chapter [[CH_ALLOC]]): {full}, worth {usd(fv)} a month ({fn_} accounts)." if full else "."))
    return tb + txt + "</p>"

def sens_section(sp, ch):
    rows = []
    cs = sorted(sens("cost", sp["prog"], sp["instr"]), key=lambda r: r["cost_mult"])
    for r in cs:
        rows.append([f"&times; {r['cost_mult']:g}", pm(r["EV_month"], r["CI"]), sgn(r["EV"]), f"{r['days']:.1f}", pct(r["P"])])
    if not rows: return ""
    return table(["Trading cost", "EV/month (95%)", "Value of an attempt", "Days per attempt", "Pass rate"], rows, cls="small", num_from=1,
                 cap="The plan's setting with every round-trip cost multiplied (spread, commission, slippage), 3,000 attempts on each of the four paths 1201&ndash;1204 (12,000 in all) with the same seeds in every row. "
                     "The rows share their paths and seeds but not their trades: a different cost changes the first trade's result, and the account's later trades with it, so the rows also differ by Monte Carlo noise of the size of the interval"
                     + (f" (on the micro Nasdaq future a round trip costs {100 * kappa(sp['instr']) / (ch['m'] * SIG[sp['instr']]):.1f}% of the risk at this stop, and doubling it moves the value by less than that noise). " if sp.get("fut") else ". ") +
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
            f'<strong>{usd(cr["EV_month"])} a month per 100K</strong> (&plusmn; {usd(cr["CI"])}, continuing-slot rate, years 2&ndash;9); in the plan: '
            + ("; ".join(f"{n} &times; {kk(s)}" for p, i, s, n in ALLOC[sp['firm']]['rec']) or "not in the recommended plan") + (f", {usd(rv)} a month." if rn else ".") + "</p>")
    parts = [head,
             f"<h2>{num}.1 The rules</h2>", rules_table(sh, sp["firm"]),
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
           f"<p>Micro Nasdaq futures in whole contracts, shared direction with the Nasdaq CFD accounts. Futures firms set no percentage risk rule, so the risk per trade is searched as well; the choice keeps the plan's stop of at least 0.6 hourly standard deviations (the grid also tries 0.5, which the first version 9 run chose for Apex: version 9's corrections, n21).</p>",
           f"<h2>{num}.1 The rules</h2>", rules_table(sh, sp["firm"]), f"<h2>{num}.2 What the engine simulates</h2>", model_table(F, prog),
           f"<h2>{num}.3 The search</h2>", table(["k", "m", "Risk", "Refined EV/month", "Pass rate", "Days"], rows, cls="small", num_from=0,
                                                 cap=f"The ten best grid settings (4,000 attempts each on paths 1101&ndash;1104) re-run for 16,000 attempts on paths 1111&ndash;1114, best first; the first {len(fr)} shown. The choice keeps the plan's minimum stop of 0.6 hourly sd."),
           f"<h2>{num}.4 The chosen setting</h2>",
           _calc([f"Plan: \\(k = {ch['k']:g}\\), \\(m = {ch['m']:g}\\), risk \\(\\${ch['L']:,.0f}\\): at the reference level of 31,070 the stop is {T['stop_pts']:.1f} points and one MNQ contract loses \\(\\${2 * T['stop_pts']:,.0f}\\) at the stop, so {contracts} contracts (rounded down), a risk of \\(\\${contracts * 2 * T['stop_pts']:,.0f}\\); the engine recomputes this at every entry from the path's price (10.1).",
                  f"Fresh paths: {pm(ch['EV_month'], ch['CI'])} a month per account as a random-start ratio (pass rate {pct(ch['P'])} &plusmn; {pct(p_ci(ch))}, {ch['days']:.1f} days per attempt)" + (f"; continuing-slot rate, years 2&ndash;9 (price level and calendar carried from attempt to attempt): <strong>{pm(cont(ch)['rate'], cont(ch)['CI'])}</strong>." if cont(ch) else "."),
                  "Why so little: the funded account's maximum loss trails the balance, payouts are capped per request and (Apex) in number, the evaluation fee recurs monthly (Topstep), Apex's figures assume a discount code (its list price is $550: Appendix B), and whole contracts make the smallest trade large next to a $2,000 allowance. The static withdrawal identity does not apply to these accounts (7.1); the values are the engine's."]),
           f"<h2>{num}.5 How many</h2><p>{ALLOC[sp['firm']]['cap']}: {nfull} accounts, worth {nfull} &times; {usd(r0(acct_row(prog, instr, 50_000)['EV_month']))} = {usd(nfull * r0(acct_row(prog, instr, 50_000)['EV_month']))} a month together. This layer is optional and is not in the recommended plan's headline figure.</p>",
           f"<h2>{num}.6 How the plan meets the rules</h2>", plan_section(sp), "</section>"]
    return "\n".join(out)
