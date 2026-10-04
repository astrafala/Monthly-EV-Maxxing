import re, json, math, html, pathlib
src = open("build_doc.py").read()
exec(src[:src.index('doc = open("doc_template.html").read()')])   # helpers: t, fig, money, colours

FINAL = json.load(open("final_v3.json"))
PORT = json.load(open("portfolio_v3.json"))
MILE = json.load(open("milestones_v3.json"))
SIZES = json.load(open("v3_sizes2.json"))
SENS = json.load(open("v3_sens.json"))
KG = json.load(open("v3_kgrid.json")) + json.load(open("v3_kgrid2.json"))
MULTI = [json.loads(l) for l in open("grid1d.jsonl")]

def usd(x, dec=0):
    s = f"{abs(x):,.{dec}f}"
    return f"&minus;${s}" if x < -0.5 else f"${s}"
def k_(x): return f"${x/1000:,.1f}K" if abs(x) < 99500 else f"${x/1000:,.0f}K"
def pct(x, d=0): return f"{100*x:.{d}f}%"
def r100(x): return int(round(x / 100.0)) * 100

def table(head, rows, cls="", num_from=1, hl=(), w0=None):
    st0 = f' style="width:{w0}"' if w0 else ""
    th = "".join(f'<th class="n" style="white-space:normal">{h}</th>' if i >= num_from else (f"<th{st0}>{h}</th>" if i == 0 else f"<th>{h}</th>") for i, h in enumerate(head))
    body = ""
    for j, r in enumerate(rows):
        tds = "".join(f'<td class="n">{c}</td>' if i >= num_from else f"<td>{c}</td>" for i, c in enumerate(r))
        body += f'<tr class="hl">{tds}</tr>' if j in hl else f"<tr>{tds}</tr>"
    c = f' class="{cls}"' if cls else ""
    return f"<table{c}><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"

def hbars(rows, unit_fmt, caption, color=S1, maxv=None, label_w=230, W=600):
    rowh = 16; mt = 4; H = mt + rowh * len(rows) + 6
    maxv = maxv or max(v for _, v in rows) * 1.08
    sc = (W - label_w - 70) / maxv
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for i, (lab, v) in enumerate(rows):
        y = mt + i * rowh
        o.append(t(label_w - 8, y + rowh - 4.5, lab, 8.4, "end", INK))
        wv = max(v, 0) * sc
        o.append(f'<rect x="{label_w}" y="{y+3:.1f}" width="{max(wv,0.8):.1f}" height="{rowh-6:.1f}" rx="1.5" fill="{color if v>=0 else NEG}"/>')
        o.append(t(label_w + wv + 6, y + rowh - 4.5, unit_fmt(v), 8.2, "start", INK, True))
    o.append("</svg>")
    return fig("".join(o), caption)

S = lambda f: FINAL[f]["synth"]; Rl = lambda f: FINAL[f]["real"]
CFD = ["FundingPips 2-Step (bi-weekly 80%)", "FXIFY Two-Phase", "The5ers High Stakes", "FundedNext Stellar 2-Step",
       "FundingPips 2-Step (monthly 100%)", "Alpha Capital Pro 10%", "FTMO 2-Step", "FTMO 1-Step", "GFT 2-Step Standard"]
CFD.sort(key=lambda f: -S(f)["EV_month"])
FUT = ["Topstep 50K", "Tradeify Select 50K", "Lucid Flex 50K", "Apex 50K EOD"]
SHORT = {"FundingPips 2-Step (bi-weekly 80%)": "FundingPips 2-Step, bi-weekly 80%",
         "FundingPips 2-Step (monthly 100%)": "FundingPips 2-Step, monthly 100%"}
sh = lambda f: SHORT.get(f, f)

# ------------------------------------------------------------------ chapter 17
def v2v3_table():
    k3x1 = [r for r in SENS if r["X1"] == 1000 and r["k"] == 3 and r["L"] == 1500 and r["m"] == 0.75][0]
    k3x10 = [r for r in SENS if r["X1"] == 10000 and r["X"] == 10000 and r["k"] == 3 and r["L"] == 1500 and r["m"] == 0.75][0]
    rows = [["Version 2 account model (1 : 3, funded +$1,000 then +$10,000)", "$2,444", "&mdash;"],
            ["Version 3 path engine, same settings", usd(k3x1["EV_month"]), f'{k3x1["days"]:.1f} days'],
            ["&hellip; with +10% funded cycles", usd(k3x10["EV_month"]), f'{k3x10["days"]:.1f} days'],
            ["&hellip; and 1 : 5 instead of 1 : 3 (the version 3 plan)", usd(S("FTMO 2-Step")["EV_month"]), f'{S("FTMO 2-Step")["days"]:.1f} days'],
            ["Version 3 plan on the real 2024&ndash;26 path", usd(Rl("FTMO 2-Step")["EV_month"]), f'{Rl("FTMO 2-Step")["days"]:.1f} days']]
    return table(["FTMO 2-Step 100K, zero edge", "EV per month per slot", "Average attempt"], rows, hl=(3,))

# ------------------------------------------------------------------ chapter 18
def multi_table():
    by = {(r["tag"].split()[0], r["data"]): r for r in MULTI}
    spec = [("A1", "Nasdaq alone, 1.5%", "one position"),
            ("B1", "Nasdaq + S&amp;P 500, same direction, 0.75% each", "total 1.5%"),
            ("B2", "Nasdaq + S&amp;P 500, same direction, 1.5% each", "&asymp; 2.9% on one idea"),
            ("A2", "Nasdaq alone, 3% (reference, beyond guidance)", "one position"),
            ("C1", "Nasdaq + gold, 1.5% each, at most 1.5% open", "one at a time"),
            ("C3", "Nasdaq + gold, 1.5% each", "up to 3% open"),
            ("C5", "Nasdaq + gold + yen + euro, 1.5% each", "up to 4.5% open"),
            ("T2", "Two independent Nasdaq-like markets, 1.5% each (imaginary)", "up to 3% open"),
            ("T6", "Four independent Nasdaq-like markets, 1.5% each (imaginary)", "up to 6% open"),
            ("Z1", "Nasdaq alone, no costs at all", "one position"),
            ("Z3", "Four independent markets, no costs at all", "up to 6% open")]
    base = by[("A1", "synth")]["EV_month"]
    rows = []
    for tag, name, risk in spec:
        r = by[(tag, "synth")]
        rows.append([name, risk, usd(r["EV_month"]), f'{(r["EV_month"]/base-1)*100:+.0f}%', f'{r["days"]:.1f}', pct(r["pass_by_phase"][-1])])
    return (table(["Set-up (FTMO 2-Step 100K)", "Open risk", "EV per month", "vs one position", "Days per attempt", "Pass both phases"],
                  rows, num_from=2, hl=(0,)) +
            '<p class="cap" style="font-size:8.5pt;color:#5b6370">Synthetic zero-edge paths, 6,000 attempts per row, combined target capped. '
            'These runs used the version 2 settings (1 : 3, funded +$1,000 first), so compare rows with each other rather than with later chapters. '
            'Noise is about &plusmn;$330 per month per row.</p>')

# ------------------------------------------------------------------ chapter 19
def size_table():
    rows = []
    for r in sorted(SIZES, key=lambda r: (r["firm"], r["size"])):
        K = r["size"] / 100000
        rows.append([f'{r["firm"]} {r["size"]/1000:.0f}K', usd(r["fee"]), pct(r["fee"] / r["size"], 2), usd(r["EV_month"]), usd(r["EV_month"] / K)])
    return table(["Account", "Fee", "Fee &divide; size", "EV per month", "per $100K of allowance"], rows) + \
        '<p style="font-size:8.5pt;color:#5b6370">1 : 3, funded cycles of +10% (1-Step: +5% first), 12,000 synthetic attempts each; noise about &plusmn;4% per row.</p>'

def sens_table():
    def row(label, r, note=""):
        return [label + note, usd(r["EV_month"]), f'{r["days"]:.1f}', pct(r["P"])]
    rows = []
    base3 = [r for r in SENS if r["L"] == 1500 and r["m"] == 0.75 and r["k"] == 3 and r["X1"] == 10000 and r["X"] == 10000][0]
    rows.append(row("Baseline at 1 : 3 (stop 0.75, risk 1.5%, +10% cycles)*", base3))
    for L in (1000, 2000, 3000):
        r = [x for x in SENS if x["L"] == L][0]
        rows.append(row(f"Risk {L/1000:g}% per trade*" + (" (beyond FTMO guidance)" if L > 1500 else ""), r))
    for m in (0.5, 1.0, 1.5, 3.0):
        r = [x for x in SENS if x["m"] == m and x["L"] == 1500 and x["k"] == 3][0]
        rows.append(row(f"Stop {m:g} hourly moves*", r))
    for X1, X in ((1000, 10000), (3000, 10000), (5000, 10000), (10000, 20000)):
        r = [x for x in SENS if x["X1"] == X1 and x["X"] == X and x["k"] == 3 and x["L"] == 1500 and x["m"] == 0.75][0]
        rows.append(row(f"Funded: first cycle +${X1:,}, then +${X:,}*", r))
    for k in (1, 2):
        r = [x for x in SENS if x["k"] == k][0]
        rows.append(row(f"Reward : risk 1 : {k}*", r))
    for k in (4, 5, 6, 8, 10, 15):
        r = [x for x in KG if x["k"] == k and x["m"] == 0.75 and x["data"] == "synth"][0]
        rr = [x for x in KG if x["k"] == k and x["m"] == 0.75 and x["data"] == "real"]
        lab = f"Reward : risk 1 : {k}" + (f" &nbsp;(real path: {usd(rr[0]['EV_month'])})" if rr else "")
        rows.append(row(lab, r))
    real3 = [x for x in KG if x["k"] == 3 and x["data"] == "real"][0]
    rows.append(["Reward : risk 1 : 3 on the real path", usd(real3["EV_month"]), f'{real3["days"]:.1f}', pct(real3["P"])])
    hl = [i for i, r in enumerate(rows) if r[0].startswith("Reward : risk 1 : 5")]
    return table(["Setting (all else as in the plan)", "EV per month", "Days per attempt", "Pass both phases"], rows, cls="small", hl=hl) + \
        f'<p style="font-size:8.5pt;color:#5b6370">12,000 synthetic attempts per row (seed 11); noise about &plusmn;$300 per month. The final figure for the 1 : 5 plan, from 24,000 attempts with other seeds, is {usd(r100(S("FTMO 2-Step")["EV_month"]))} (Chapter 20): the same within noise.</p>'

# ------------------------------------------------------------------ chapter 20
NOTES = {"FTMO 2-Step": "10/5%, 4 days per phase, 14-day payouts",
         "FTMO 1-Step": "10%, 3% daily, trailing floor, best day &le; 50%",
         "FundingPips 2-Step (bi-weekly 80%)": "8/5%, refund with 4th payout",
         "FundingPips 2-Step (monthly 100%)": "8/5%, 100% split, monthly",
         "FundedNext Stellar 2-Step": "8/5%, 5 days, +15% of challenge profit, first payout day 21",
         "The5ers High Stakes": "10/5%, 3 profitable days",
         "Alpha Capital Pro 10%": "10/5%, 3 days, no refund assumed",
         "FXIFY Two-Phase": "10/5%, refund with 1st payout",
         "GFT 2-Step Standard": "10/5%, funded profit &le; $3,000/day, first 2 payouts &le; 6%"}
def cfd_table():
    rows = []
    for f in CFD:
        s, r = S(f), Rl(f)
        rows.append([f"<strong>{sh(f)}</strong><br><span style='color:#5b6370;font-size:8pt'>{NOTES[f]}</span>", usd(FINAL[f]["fee"]),
                     pct(s["P"]), usd(s["Vf"]), f'{s["t_fund"]:.0f}', usd(s["EV"]), f'{s["days"]:.1f}',
                     f'<strong>{usd(s["EV_month"])}</strong>', usd(r["EV_month"]), f'{s["t_first_med"]:.0f}'])
    return table(["Programme (100K)", "Fee", "Pass", "Paid per funded acct", "Funded days", "EV per attempt", "Days per attempt",
                  "EV / month", "Real path", "1st payout (day)"], rows, cls="small", w0="27%")
def fut_table():
    rows = []
    for f in FUT:
        s, r = S(f), Rl(f); st = FINAL[f]["setting"]
        fee = f'{usd(FINAL[f]["fee"])}' + ("/month" if FINAL[f]["monthly"] else "") + (f' + {usd(FINAL[f]["activation"])}' if FINAL[f]["activation"] else "")
        rows.append([f"<strong>{f}</strong><br><span style='color:#5b6370;font-size:8pt'>risk ${st['L']:.0f}, 1 : {st['k']}</span>", fee,
                     pct(s["P"]), usd(s["Vf"]), f'{s["t_fund"]:.0f}', usd(s["EV"]), f'{s["days"]:.1f}',
                     f'<strong>{usd(s["EV_month"])}</strong> &plusmn;{s["EV_month_CI"]:,.0f}', usd(r["EV_month"])])
    return table(["Programme (50K)", "Fee", "Pass", "Paid per funded acct", "Funded days", "EV per attempt", "Days per attempt",
                  "EV / month", "Real path"], rows, cls="small", w0="22%")
def apex_note():
    s = S("Apex 50K EOD"); ev = s["EV"]; d = s["days"]
    out = []
    for fee in (147, 98):
        e2 = ev + (490 - fee)
        out.append(f"at {usd(fee)} (a {100 - fee/4.9:.0f}% discount) it would be {usd(e2)} per attempt, about {usd(e2 / d * 30.44)} per month")
    return "; ".join(out) + ". Only the price decides whether Apex is worth running, and even then it is small."

# ------------------------------------------------------------------ chapter 21
CAPS = [("FTMO", "$400,000 per trader or strategy across all accounts, 1-Step and 2-Step combined. Treated as including evaluations.", "4 &times; 100K", "A"),
        ("FundingPips", "$400,000 across Evaluation, Master and Prime accounts (evaluations count).", "4 &times; 100K", "A"),
        ("FundedNext", "$300,000 in funded accounts; evaluations not limited.", "3 &times; 100K", "A"),
        ("The5ers", "High Stakes: one 50K or 100K account (plus smaller ones).", "1 &times; 100K", "A"),
        ("Alpha Capital", "$400,000 per household; $300,000 per strategy.", "3 &times; 100K", "B"),
        ("FXIFY", "Reported as $805,000 in total, one active account per size. Confirm with support.", "4 &times; 100K (assumed)", "C"),
        ("GFT", "$400,000 in funded accounts.", "4 &times; 100K", "B"),
        ("Topstep", "5 Express Funded accounts at a time.", "5 &times; 50K", "A"),
        ("Apex / Tradeify / Lucid", "20 / 5 / not stated. Not used: negative or marginal value (Chapter 20).", "&mdash;", "B")]
def caps_table():
    rows = [[f"<strong>{a}</strong>", b, c, d] for a, b, c, d in CAPS]
    return table(["Firm", "Allocation rule (October 2026)", "Slots used", "Source quality"], rows, cls="small", num_from=9) + \
        '<p style="font-size:8.5pt;color:#5b6370">Source quality: A = the firm\'s own help pages or several consistent sources; B = consistent secondary sources; C = one secondary source, to be confirmed. Details in Appendix D.</p>'
def portf_table():
    rows = []
    for name, r in PORT.items():
        rows.append([name, f'{r["n_slots"]}', f'<strong>{usd(r100(r["EV_month"]))}</strong>', usd(r100(r["EV_month_real"])), usd(r100(r["fees_month"]))])
    return table(["Portfolio (each slot runs the version 3 plan)", "Slots", "EV per month", "Real path", "Fees per month"], rows, hl=(2,))
def spread_table():
    rows = []
    for name, r in PORT.items():
        for mode, lab in (("together", "together"), ("independent", "independent (not achievable)")):
            rows.append([f"{name.split(':')[0]}<br><span style='color:#5b6370;font-size:8pt'>{lab}</span>",
                         pct(r[f"{mode}_P_ahead_1"]), pct(r[f"{mode}_P_ahead_3"]), pct(r[f"{mode}_P_ahead_12"]),
                         usd(r100(r[f"{mode}_median_12"])), usd(r100(r[f"{mode}_p05_12"])),
                         usd(r100(r[f"{mode}_trough_median"])), usd(r100(r[f"{mode}_trough_p05"]))])
    return table(["Portfolio", "Ahead at 1 month", "3 months", "12 months", "Median after 12 months", "Bad case (1 in 20)", "Typical cash low", "Bad-case cash low"],
                 rows, cls="small", hl=[i for i in range(0, len(rows), 2)], w0="24%") + \
        '<p style="font-size:8.5pt;color:#5b6370">2,000 simulated 12-month histories per firm. "Together": all slots at the same rank of luck. "Cash low": the lowest point of cumulative cash (fees paid minus payouts received).</p>'

# ------------------------------------------------------------------ chapter 22
def dir_table():
    rows = [["Random direction (version 2)", "$1,802 / $1,928", "$3,587 / $3,755", "30%"],
            ["Trend, 20 hours: direction of the last 20 hourly closes", "$885 / $869", "$2,074 / $2,024", "30%"],
            ["Trend, 5 hours: direction of the last 5 hourly closes", "$2,733 / $2,801", "$4,613 / $4,740", "35&ndash;36%"],
            ["Reversal, 5 hours: against the last 5 hourly closes", "$1,064 / $1,110", "$2,327 / $2,427", "25%"]]
    return table(["Rule (FTMO 2-Step, 1 : 3, real 2024&ndash;26 path)", "EV per attempt (two runs)", "EV per month (two runs)", "Pass both"], rows) + \
        '<p style="font-size:8.5pt;color:#5b6370">Two runs of 6,000 attempts with different random start dates. On a synthetic zero-edge path the 20-hour trend rule gave $1,107 &plusmn; 142 per attempt against $1,282 &plusmn; 156 for random: the same within noise.</p>'

# ------------------------------------------------------------------ part 2 tables
def scale_table():
    steps = [("1", "FTMO 2-Step &times; 4", {"FTMO 2-Step": 4}),
             ("2 (after first payouts)", "+ FundingPips &times; 4, The5ers &times; 1", {"FTMO 2-Step": 4, "FundingPips 2-Step (bi-weekly 80%)": 4, "The5ers High Stakes": 1}),
             ("3", "+ FundedNext &times; 3, Alpha Capital &times; 3", {"FTMO 2-Step": 4, "FundingPips 2-Step (bi-weekly 80%)": 4, "The5ers High Stakes": 1, "FundedNext Stellar 2-Step": 3, "Alpha Capital Pro 10%": 3}),
             ("4 (caps confirmed)", "+ FXIFY &times; 4, GFT &times; 4", {"FTMO 2-Step": 4, "FundingPips 2-Step (bi-weekly 80%)": 4, "The5ers High Stakes": 1, "FundedNext Stellar 2-Step": 3, "Alpha Capital Pro 10%": 3, "FXIFY Two-Phase": 4, "GFT 2-Step Standard": 4})]
    rows = []
    for stg, what, P in steps:
        ev = sum(n * S(f)["EV_month"] for f, n in P.items())
        fees = sum(n * (FINAL[f]["fee"] + S(f)["P"] * FINAL[f]["activation"]) * 30.44 / S(f)["days"] for f, n in P.items())
        rows.append([stg, what, f"{sum(P.values())}", usd(r100(ev)), usd(r100(fees))])
    return table(["Stage", "Accounts", "Slots", "EV per month", "Fees per month"], rows, num_from=2)

def sizing_v3():
    V, stop, spread = 1.0, 64, 1.4
    cases = [("Phase 1, start", 100000, 100000, 110000), ("Phase 1, near target", 106500, 106500, 110000),
             ("Phase 1, after a bad morning", 95400, 99000, 110000), ("Phase 1, near the floor", 90900, 90900, 110000),
             ("Phase 2, near target", 104000, 104000, 105000)]
    rows = []
    for name, bal, sod, tgt in cases:
        room = bal - 90000; dayroom = 5000 - (sod - bal)
        risk = min(1500, room - 100, dayroom - 200)
        lots = math.floor(risk / (stop * V) * 100) / 100
        cost = (spread + 0.6) * lots * V
        togo = tgt - bal
        target = min(5 * risk, togo + cost + 5)
        tp = target / (lots * V)
        p = stop / (stop + tp)
        rows.append([name, f"${bal:,}", f"${room:,}", f"${dayroom:,}", f"${risk:,.0f}", f"{lots:.2f}", f"${cost:,.0f}",
                     f"${target:,.0f}", f"{tp:.0f}", f"{p*100:.0f}%"])
    return table(["Situation", "Balance", "Room to floor", "Day room", "Risk", "Lots", "Cost", "Target $", "Target pts", "Win chance"], rows, cls="small")

RULES = [
 ("FTMO 2-Step", "10% / 5%", "5% / 10% static", "4 per phase", "every 14 days, 80% (90% with scaling)", "1st payout", "no (Standard)", "&plusmn;2 min high impact", "none", "own accounts, within cap"),
 ("FundingPips 2-Step", "8% / 5%", "5% / 10% static", "3 per phase", "bi-weekly 80%; monthly 100%; on-demand 90%", "4th reward", "no (Master)", "&plusmn;5 min restricted items", "35% on on-demand and monthly", "own FundingPips accounts; no inbound copier services"),
 ("FundedNext Stellar 2-Step", "8% / 5%", "5% / 10% static", "5 per phase", "day 21, then every 14 days, 80%", "1st reward; +15% of challenge profit", "check", "allowed (check funded terms)", "none", "check"),
 ("The5ers High Stakes", "10% / 5%", "5% / 10%", "3 profitable days (&ge; 0.5%)", "bi-weekly, 80% rising with scaling", "check", "allowed", "&plusmn;2 min high impact", "none", "check"),
 ("Alpha Capital Pro 10%", "10% / 5%", "5% (balance) / 10% static", "3 per phase", "14-day cycle from first trade, 80%", "not assumed", "no (funded Pro)", "&plusmn;2 min high impact", "40% for on-demand only", "check; lot limit 40 on 100K"),
 ("FXIFY Two-Phase", "10% / 5%", "5% / 10% (one source: 4% / trailing)", "check", "14 days 80% or 30 days 100%", "1st payout", "allowed", "allowed", "none (30% only on Lightning)", "check"),
 ("GFT 2-Step Standard", "10% / 5%", "5% / 10% static", "check", "bi-weekly, 80%", "refundable", "check", "check", "funded: &le; $3,000 profit/day; first 2 payouts &le; 6%", "check"),
 ("Topstep 50K", "$3,000", "$2,000 end-of-day trailing", "2 (best day &le; $1,500)", "5 winning days of $150+; &le; 50% of balance, &le; $2,000; 90%", "&mdash; ($49/month + $149 activation)", "futures hours", "check", "50% in the Combine", "trade copier across own accounts"),
]
def rules_table():
    h1 = ["Programme", "Targets", "Daily / max loss", "Min days", "Funded payouts", "Fee refund"]
    h2 = ["Programme", "Weekend (funded)", "News (funded)", "Consistency / caps", "Copying"]
    r1 = [[f"<strong>{r[0]}</strong>"] + list(r[1:6]) for r in RULES]
    r2 = [[f"<strong>{r[0]}</strong>"] + list(r[6:]) for r in RULES]
    return table(h1, r1, cls="small", num_from=99, w0="18%") + table(h2, r2, cls="small", num_from=99, w0="18%") + \
        '<p style="font-size:8.5pt;color:#5b6370">"check": not found in a reliable public source; ask the firm before buying. The plan already avoids weekends and news on every account, so those columns rarely bind.</p>'

def funded_table():
    rows = []
    for f in CFD:
        s = S(f)
        rows.append([sh(f), pct(s["P"]), usd(r100(s["Vf"])), f'{s["t_fund"]:.0f}', f'{s["t_first_med"]:.0f}'])
    return table(["Programme", "Attempts that reach funded", "Paid per funded account (average)", "Funded account lasts (days, average)", "First payout (day, median)"], rows)

def milestones():
    M = MILE
    rows = [["Phase 1 decided (pass about " + pct(M["P1"]) + ")", f'day {M["p1_day"][0]:.0f} (middle half {M["p1_day"][1]:.0f}&ndash;{M["p1_day"][2]:.0f})'],
            ["Phase 2 decided (pass about " + pct(M["P2_given_1"]) + " of those who reach it)", f'day {M["p2_day"][0]:.1f}'],
            ["Funded account issued", f'day {M["funded_day"][0]:.0f}'],
            ["First payout received, fee refunded (" + pct(M["share_funded_paid"]) + " of funded accounts)", f'day {M["first_pay_day"][0]:.0f} (middle half {M["first_pay_day"][1]:.0f}&ndash;{M["first_pay_day"][2]:.0f})'],
            ["Funded account ends", f'day {M["end_day"][0]:.0f} (middle half {M["end_day"][1]:.0f}&ndash;{M["end_day"][2]:.0f})']]
    return table(["Milestone, FTMO 2-Step, from the day you buy", "Typical day"], rows) + \
        f'<p>With +10% cycles about half of funded accounts end before their first payout, fee unrefunded: the price of speed. If a dependable refund matters more, run the first cycle to +$1,000 (91% reach it) at a cost of about 10% of the value per month (Section 19.3).</p>'

def months_table():
    rows = []
    for name in ("FTMO only: 4 x 100K", "Seven CFD firms: 23 slots"):
        r = PORT[name]
        for h in ("1", "3", "6", "12"):
            rows.append([name.split(":")[0] if h == "1" else "", f"{h}", pct(r[f"together_P_ahead_{h}"]), usd(r100(r[f"together_median_{h}"])), usd(r100(r[f"together_p05_{h}"])), usd(r100(r[f"together_p95_{h}"]))])
    return table(["Portfolio", "Months", "Chance ahead", "Median cash", "Bad case (1 in 20)", "Good case (1 in 20)"], rows, num_from=1) + \
        f'<p style="font-size:8.5pt;color:#5b6370">Cumulative cash (payouts minus fees), all slots moving together. Typical cash low point: {usd(r100(PORT["FTMO only: 4 x 100K"]["together_trough_median"]))} (FTMO only) and {usd(r100(PORT["Seven CFD firms: 23 slots"]["together_trough_median"]))} (23 slots); bad case {usd(r100(PORT["FTMO only: 4 x 100K"]["together_trough_p05"]))} and {usd(r100(PORT["Seven CFD firms: 23 slots"]["together_trough_p05"]))}.</p>'

def fig_firms_v3():
    rows = [(sh(f), S(f)["EV_month"]) for f in CFD] + [(f + " (futures)", S(f)["EV_month"]) for f in FUT]
    rows.sort(key=lambda r: -r[1])
    return hbars(rows, lambda v: (f"${v:,.0f}" if v >= 0 else f"&minus;${-v:,.0f}"),
                 "Figure 20.1 &middot; EV per month per slot, version 3 plan, synthetic zero-edge paths (CFD slots are 100K, futures 50K).")

# ------------------------------------------------------------------ key results
def key_results():
    f2 = S("FTMO 2-Step"); best = max(CFD, key=lambda f: S(f)["EV_month"]); worst = min(CFD, key=lambda f: S(f)["EV_month"])
    P4 = PORT["FTMO only: 4 x 100K"]; P23 = PORT["Seven CFD firms: 23 slots"]; P15 = PORT["Five best-documented CFD firms: 15 slots"]
    rows = [
      ["Chance a zero-skill trader passes FTMO Phase 1 / both phases (version 3 plan)", f'{pct(MILE["P1"])} / {pct(f2["P"])}', "Ch. 3&ndash;4, 28"],
      ["Expected value per attempt, no costs (exact, FTMO 2-Step)", "+$2,235", "Ch. 6"],
      ["Version 3 plan: Nasdaq, stop 0.75 hourly moves, <strong>1 : 5</strong>, risk 1.5%, funded cycles +10%", f'{usd(f2["EV"])} per attempt, {f2["days"]:.1f} days', "Ch. 19, 23"],
      ["&hellip; EV per month per FTMO 100K slot (synthetic / real path)", f'<strong>{usd(r100(f2["EV_month"]))}</strong> / {usd(r100(Rl("FTMO 2-Step")["EV_month"]))}', "Ch. 20"],
      ["&hellip; same plan, best and worst CFD firm per slot", f'{usd(r100(S(best)["EV_month"]))} ({best.split(" ")[0]}) / {usd(r100(S(worst)["EV_month"]))} ({worst.split(" ")[0]})', "Ch. 20"],
      ["Futures firms per 50K account (Topstep best; Apex at list price)", f'{usd(r100(S("Topstep 50K")["EV_month"]))} / {usd(r100(S("Apex 50K EOD")["EV_month"]))}', "Ch. 20"],
      ["Several positions at once (Nasdaq + S&amp;P, many pairs)", "no gain at the same risk", "Ch. 18"],
      ["100K vs 200K accounts, per dollar of allowance", "the same; 50K about 8% worse", "Ch. 19"],
      ["<strong>Per person, FTMO only (4 &times; 100K or 2 &times; 200K)</strong>", f'<strong>{usd(r100(P4["EV_month"]))}</strong> per month', "Ch. 21"],
      ["<strong>Per person, five best-documented CFD firms (15 slots)</strong>", f'<strong>{usd(r100(P15["EV_month"]))}</strong> per month', "Ch. 21"],
      ["<strong>Per person, seven CFD firms (23 slots)</strong>", f'<strong>{usd(r100(P23["EV_month"]))}</strong> per month; fees {usd(r100(P23["fees_month"]))}', "Ch. 21"],
      ["23 slots: chance ahead after 1 / 3 / 12 months (accounts move together)", f'{pct(P23["together_P_ahead_1"])} / {pct(P23["together_P_ahead_3"])} / {pct(P23["together_P_ahead_12"])}', "Ch. 21, 29"],
      ["23 slots: typical / bad-case (1 in 20) cash low point", f'{usd(r100(P23["together_trough_median"]))} / {usd(r100(P23["together_trough_p05"]))}', "Ch. 21, 29"],
    ]
    rr = ""
    for i, (a, b, c) in enumerate(rows):
        cls = ' class="hl"' if i in (3, 10) else ""
        rr += f'<tr{cls}><td>{a}</td><td class="n">{b}</td><td>{c}</td></tr>'
    return f"""
<!-- ================================================================ KEY RESULTS -->
<section class="chapter">
  <span class="eyebrow">Summary</span>
  <h1>Key results at a glance</h1>
  <p>Version 3 re-runs every figure on price paths (Chapter 17), tests trading many positions at once, compares account sizes and every major firm, and adds up the maximum per person. "Zero skill" means no trade direction is better than chance. Every figure assumes the firms pay every payout.</p>
  <table><thead><tr><th>Quantity</th><th class="n">Value</th><th>Where</th></tr></thead><tbody>{rr}</tbody></table>
  <div class="box key"><h4>What changed in version 3</h4>
  <ol>
    <li><strong>1 : 5, not 1 : 3.</strong> Fewer trades, less spread, same time per phase: about 15% more per month.</li>
    <li><strong>Funded cycles of +10%</strong> instead of +$1,000 first: accounts finish sooner and slots recycle faster.</li>
    <li><strong>One position at a time.</strong> Several positions (correlated or not) never beat one Nasdaq position at the same risk; correlated stacking is a bigger bet in disguise.</li>
    <li><strong>Scale with accounts, not risk.</strong> The per-person maximum comes from running the same plan within the caps of several firms.</li>
    <li><strong>A written direction rule</strong> instead of a coin flip, applied identically everywhere, so no account ever opposes another.</li>
    <li><strong>Figures supersede version 2.</strong> Where Chapters 10&ndash;11 differ from Chapters 17&ndash;21, the later chapters hold.</li>
  </ol></div>
</section>
"""

TOC = [("p", "", "Key results at a glance"), ("p", "I", "Part 1 &middot; The mathematics"),
    ("", "1", "The contract you are buying"), ("", "2", "Probability from zero"),
    ("", "3", "Reaching a target before a floor"), ("", "4", "The challenge, step by step"),
    ("", "5", "What a funded account is worth"), ("", "6", "Putting it together"), ("", "7", "Trading costs"),
    ("", "8", "Time: how long an attempt takes"), ("", "9", "Instruments, leverage and platforms (crypto, futures)"),
    ("", "10", "Maximising expected value per month (version 2)"), ("", "11", "Other firms and other rule types"),
    ("", "12", "Variance, bankroll and Kelly"), ("", "13", "Hedging"), ("", "14", "Testing on real market data"),
    ("", "15", "Errors in the earlier documents"), ("", "16", "What the mathematics cannot tell you"),
    ("", "17", "Version 3: every trade resolved on a price path"), ("", "18", "Many positions at once"),
    ("", "19", "Account size, account type and the settings that matter"), ("", "20", "Every firm, compared on the same paths"),
    ("", "21", "The maximum per person"), ("", "22", "Direction rules, and what one price history can tell you"),
    ("p", "II", "Part 2 &middot; Execution"), ("", "23", "The plan on one page"), ("", "24", "Before you start"),
    ("", "25", "The trade, step by step"), ("", "26", "Firm-by-firm rule sheet"), ("", "27", "Running many accounts: the daily routine"),
    ("", "28", "Funded accounts and payouts"), ("", "29", "Month by month: cash, odds and when to stop"), ("", "30", "Final checklist"),
    ("p", "A&ndash;D", "Appendices: formula sheet and glossary, every account type modelled, method and sources, version 3 sources")]

APPX_D = """
<section class="chapter">
  <span class="eyebrow">Appendix D</span>
  <h1>Version 3: firm rules and sources</h1>
  <p>Firm rules, caps and prices were collected in October 2026 from the firms' own pages where possible and otherwise from review sites. Prices change with promotions; the fee used is shown in Chapter 20. Check every item against the firm's current terms before buying.</p>
  <table class="small"><thead><tr><th>Topic</th><th>Source</th></tr></thead><tbody>
  <tr><td>FTMO: account limit, $400,000 cap, identical strategies</td><td>ftmo.com/en/faq/how-many-accounts-can-i-have/</td></tr>
  <tr><td>FTMO: monitored behaviour (gambling, all-in, no fixed risk limit, 1&ndash;1.5% guidance)</td><td>ftmo.com/en/blog/why-ftmo-monitors-certain-patterns-in-trading-behaviour/</td></tr>
  <tr><td>FTMO: 1-Step and 2-Step rules, news and weekend rules</td><td>propfirmbriefing.com/prop-firm-rules/ftmo/</td></tr>
  <tr><td>FundedNext: $300,000 funded cap, evaluations unlimited</td><td>help.fundednext.com (How many accounts can I have with FundedNext?)</td></tr>
  <tr><td>FundedNext Stellar 2-Step: targets, price, 21-day first reward, refund, 15% challenge share</td><td>fundednext.com/cfds/stellar-2-step; help.fundednext.com; proptradingvibes.com/blog/fundednext-stellar-2-step</td></tr>
  <tr><td>FundingPips: models, payouts, refund with 4th reward, $400,000 cap incl. evaluations, copying and weekend rules</td><td>proptradingvibes.com/blog/fundingpips-rules; fundingpips.com/blog/fundingpips-maximum-allocation</td></tr>
  <tr><td>The5ers High Stakes: targets, profitable days, prices, account limits</td><td>the5ers.com/high-stakes/; propfirmbridge.com (High Stakes review); tradetanto.com</td></tr>
  <tr><td>Alpha Capital: programmes, lot limits, news and weekend rules, $400,000 / $300,000 caps, price</td><td>tradetanto.com/learn/alpha-capital-group-rules-what-traders-need-to-know; propvator.com/blog/alpha-capital-max-capital-allocation/</td></tr>
  <tr><td>FXIFY: programmes, consistency rule (Lightning only), cap</td><td>tradingfinder.com/props/fxify/rules/; propvator.com/blog/fxify-max-capital-allocation/</td></tr>
  <tr><td>Goat Funded Trader: 2-Step Standard, funded caps, $400,000 cap, price</td><td>propvator.com/blog/goat-funded-trader-max-capital-allocation/; review summaries (bestprop.io, cryptoslate.com)</td></tr>
  <tr><td>E8 Markets: $4.85M household cap (not modelled: rules too product-specific to verify)</td><td>propvator.com/blog/e8-markets-max-capital-allocation/</td></tr>
  <tr><td>Apex (after the 2026 update): prices, drawdowns, payouts, 20 accounts, no automation</td><td>proptradingvibes.com/blog/apex-trader-funding-rules-overview; proptradingvibes.com/blog/apex-trader-funding-payout-rules</td></tr>
  <tr><td>Topstep: Combine, Express Funded payouts, $49 + $149, 5 accounts</td><td>proptradingvibes.com/blog/topstep-trading-combine-rules; proptradingvibes.com/blog/topstep-pricing-breakdown; topstep.com</td></tr>
  <tr><td>Tradeify Select and Lucid Flex: rules, prices, payouts</td><td>phidiaspropfirm.com/education/tradeify-select; proptradingvibes.com/blog/lucid-trading-lucidflex-account</td></tr>
  </tbody></table>
  <h2>D.1 Method in one paragraph</h2>
  <p>Synthetic paths: 12 years of hourly bars, zero-drift random walk at the Nasdaq's hourly volatility (0.27%), exact Brownian-bridge extremes, weekends closed. Costs: 0.0064% of notional per round trip (US100 CFD), 0.0027% (micro futures), plus financing. 24,000 synthetic and 8,000 real-path attempts per firm; portfolios from 2,000 twelve-month histories per firm.</p>
</section>
"""

# ------------------------------------------------------------------ assemble
s = open("prop_firm_option_v2.html").read()
i_kr = s.index("<!-- ================================================================ KEY RESULTS -->")
i_p1 = s.index("<!-- ================================================================ PART 1 -->")
i_p2 = s.index("<!-- ================================================================ PART 2 -->")
i_ap = s.index("<!-- ================================================================ APPENDICES -->")
head, p1, appx = s[:i_kr], s[i_p1:i_p2], s[i_ap:]
tail_i = appx.rindex("</body>")
appx_body, appx_end = appx[:tail_i], appx[tail_i:]

def rep(txt, a, b):
    assert a in txt, a[:80]
    return txt.replace(a, b)

head = rep(head, "Mathematics and execution &middot; Version 2 &middot; October 2026", "Mathematics and execution &middot; Version 3 &middot; October 2026")
head = rep(head, "how to get it as fast as possible, and how to run it inside the firm's rules.",
           "how to get it as fast as possible, how far it scales per person, and how to run it inside every firm's rules.")
head = rep(head, "In the execution plan about three attempts in four lose their full fee; after one month the chance of being ahead is about 5%",
           "In the execution plan about seven attempts in ten lose their full fee; after one month the chance of being ahead is about one in five")
toc_old = head[head.index('<ul class="toc">'):head.index("</ul>", head.index('<ul class="toc">')) + 5]
toc_new = '<ul class="toc">' + "".join(
    f'<li class="{c}"><span class="n">{n}</span><span class="t">{tx}</span></li>' if c else
    f'<li><span class="n">{n}</span><span class="t">{tx}</span></li>' for c, n, tx in TOC) + "</ul>"
head = head.replace(toc_old, toc_new)

# version notes inside the old chapters 10 and 11
NOTE10 = ('<div class="box warn"><h4>Version 3 note</h4><p style="margin:0">This chapter is version 2\'s analysis. Chapters 17&ndash;21 redo it on price paths and find a better plan '
          '(1 : 5, funded cycles of +10%) and higher values per month. Where the figures differ, Chapters 17&ndash;21 hold.</p></div>')
m = re.search(r'(<span class="eyebrow">Chapter 10</span>\s*<h1>[^<]*</h1>)', p1); assert m
p1 = p1.replace(m.group(1), m.group(1) + "\n  " + NOTE10, 1)
m = re.search(r'(<span class="eyebrow">Chapter 11</span>\s*<h1>[^<]*</h1>)', p1); assert m
p1 = p1.replace(m.group(1), m.group(1) + "\n  " + NOTE10.replace("This chapter is version 2's analysis.", "This chapter is version 1's firm comparison.").replace("(1 : 5, funded cycles of +10%) and higher values per month", "for every major firm (Chapter 20)"), 1)

new1 = open("v3_part1_new.html").read()
new2 = open("v3_part2.html").read()
P23 = PORT["Seven CFD firms: 23 slots"]
subs = {
  "{{V2V3_TABLE}}": v2v3_table(), "{{MULTI_TABLE}}": multi_table(), "{{SIZE_TABLE}}": size_table(),
  "{{FTMO1}}": usd(r100(S("FTMO 1-Step")["EV_month"])), "{{FTMO2}}": usd(r100(S("FTMO 2-Step")["EV_month"])),
  "{{SENS_TABLE}}": sens_table(),
  "{{TL_ADD}}": usd(r100(5 * S("Tradeify Select 50K")["EV_month"] + 5 * S("Lucid Flex 50K")["EV_month"])),
  "{{X_GAIN}}": (lambda a, b: f"{usd(b['EV_month'])} per month with +10% cycles against {usd(a['EV_month'])} with +$1,000 first")(
      [r for r in SENS if r["X1"] == 1000 and r["k"] == 3][0], [r for r in SENS if r["X1"] == 10000 and r["X"] == 10000 and r["k"] == 3 and r["L"] == 1500 and r["m"] == 0.75][0]),
  "{{CFD_TABLE}}": fig_firms_v3() + cfd_table(), "{{CFD_LO}}": usd(r100(min(S(f)["EV_month"] for f in CFD))),
  "{{CFD_HI}}": usd(r100(max(S(f)["EV_month"] for f in CFD))), "{{FUT_TABLE}}": fut_table(), "{{APEX_NOTE}}": apex_note(),
  "{{CAPS_TABLE}}": caps_table(), "{{PORTF_TABLE}}": portf_table(), "{{SPREAD_TABLE}}": spread_table(),
  "{{UNCAPPED}}": usd(r100(S("FundedNext Stellar 2-Step")["EV_month_funded_slot"])), "{{CAPPED}}": usd(r100(S("FundedNext Stellar 2-Step")["EV_month"])),
  "{{DIR_TABLE}}": dir_table(),
  "{{SCALE_TABLE}}": scale_table(), "{{SIZING_V3}}": sizing_v3(), "{{RULES_TABLE}}": rules_table(),
  "{{FUNDED_TABLE}}": funded_table(), "{{MILESTONES}}": milestones(), "{{MONTHS_TABLE}}": months_table(),
  "{{HEAD_SLOT}}": usd(r100(S("FTMO 2-Step")["EV_month"])), "{{HEAD_PERSON}}": usd(r100(P23["EV_month"])),
}
body = new1 + new2
for k, v in subs.items():
    assert k in body, k
    body = body.replace(k, v)
assert "{{" not in body, re.findall(r"\{\{\w+\}\}", body)

doc = head + key_results() + p1 + body + appx_body + APPX_D + appx_end
open("prop_firm_option_v3.html", "w").write(doc)

from playwright.sync_api import sync_playwright
footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
          'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v3</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium"
    b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + str(pathlib.Path("prop_firm_option_v3.html").resolve()), wait_until="networkidle")
    pg.wait_for_timeout(800)
    pg.pdf(path="The_Prop_Firm_Option_v3.pdf", format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<div></div>", footer_template=footer)
    b.close()
print("built v3")
