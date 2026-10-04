import re, json, math, html, pathlib, collections
import numpy as np
src = open("build_doc.py").read()
exec(src[:src.index('doc = open("doc_template.html").read()')])   # helpers: t, fig, colours

FINAL = json.load(open("final_v32.json"))
SENS = {(r["tag"], r["data"]): r for r in json.load(open("sens_v32.json"))}
LOCK = json.load(open("lockstep_portfolio_v32.json"))
WEEK = json.load(open("weekly_v32.json"))
DIARY = json.load(open("diary_staged_v32.json"))
MILE = json.load(open("milestones_v32.json"))
GOLD = json.load(open("v32_gold.json"))
ROB = json.load(open("robust_v32.json"))
MULTI = [json.loads(l) for l in open("grid1d.jsonl")]

def usd(x, dec=0):
    s = f"{abs(x):,.{dec}f}"
    return f"&minus;${s}" if x < -0.5 else f"${s}"
def pct(x, d=0): return f"{100*x:.{d}f}%"
def r100(x): return int(round(x / 100.0)) * 100
def r1000(x): return int(round(x / 1000.0)) * 1000
def k_(x):
    return (f"&minus;${abs(x)/1000:,.0f}K" if x < 0 else f"${x/1000:,.0f}K")

def table(head, rows, cls="", num_from=1, hl=(), w0=None):
    st0 = f' style="width:{w0}"' if w0 else ""
    th = "".join(f'<th class="n" style="white-space:normal">{h}</th>' if i >= num_from else (f"<th{st0}>{h}</th>" if i == 0 else f"<th>{h}</th>") for i, h in enumerate(head))
    body = ""
    for j, r in enumerate(rows):
        tds = "".join(f'<td class="n">{c}</td>' if i >= num_from else f"<td>{c}</td>" for i, c in enumerate(r))
        body += f'<tr class="hl">{tds}</tr>' if j in hl else f"<tr>{tds}</tr>"
    c = f' class="{cls}"' if cls else ""
    return f"<table{c}><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"
def note(txt): return f'<p style="font-size:8.5pt;color:#5b6370">{txt}</p>'

def hbars(rows, unit_fmt, caption, color=S1, maxv=None, label_w=250, W=600):
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
CFD = [f for f in FINAL if FINAL[f]["setting"]["kind"] == "cfd"]
CFD.sort(key=lambda f: -S(f)["EV_month"])
FUT = ["Topstep 50K", "Tradeify Select 50K", "Lucid Flex 50K", "Apex 50K EOD"]
SHORT = {"FundingPips 2-Step (bi-weekly 80%)": "FundingPips 2-Step, bi-weekly 80%", "FundingPips 2-Step (monthly 100%)": "FundingPips 2-Step, monthly 100%",
         "FundingPips 2-Step (on-demand 90%)": "FundingPips 2-Step, on-demand 90%", "FundingPips 2-Step Flex (95%)": "FundingPips 2-Step Flex, 95%",
         "FundingPips 2-Step Flex (85%)": "FundingPips 2-Step Flex, 85%"}
sh = lambda f: SHORT.get(f, f)

# ------------------------------------------------------------------ lockstep summaries
PNAMES = ["One account per firm (11 firms)", "Two per firm where copying is allowed (16 accounts)",
          "Full caps, rules-strict (25 accounts)", "Full caps, staged start (25 accounts)", "FTMO only (4 x 100K)"]
LABEL = {"One account per firm (11 firms)": "One account per firm (11)", "Two per firm where copying is allowed (16 accounts)": "Two per firm where allowed (16)",
         "Full caps, rules-strict (25 accounts)": "Full caps (25)", "Full caps, staged start (25 accounts)": "Full caps, firms added monthly (25)",
         "FTMO only (4 x 100K)": "FTMO only (4)"}
def lock(p, data="synth"):
    rs = [r for r in LOCK if r["p"] == p and r["data"].startswith(data)]
    M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1)
    br = collections.Counter()
    for r in rs:
        for f, v in r["breaches"].items(): br[f] += v
    br = {f: v / len(rs) / 12 for f, v in br.items()}
    tr = np.array([r["trough"] for r in rs])
    return dict(n=len(rs), steady=float(M[:, 2:].mean()), year=float(M.mean()), C=C,
                ahead={h: float(np.mean(C[:, h - 1] > 0)) for h in (1, 2, 3, 6, 12)},
                low50=float(np.median(tr)), low05=float(np.percentile(tr, 5)), breaches=br, maxbr=max(br.values()),
                orders=float(np.mean([r["orders_per_trading_day"] for r in rs])), orders90=float(np.mean([r["orders_p90"] for r in rs])),
                entries=float(np.mean([r["entry_bars_per_day"] for r in rs])), conflicts=sum(r["conflicts"] for r in rs),
                cum_p={h: (float(np.percentile(C[:, h - 1], 5)), float(np.median(C[:, h - 1])), float(np.percentile(C[:, h - 1], 95))) for h in (1, 3, 6, 12)})
L = {p: lock(p) for p in PNAMES}
LR = {p: lock(p, "real") for p in PNAMES}
LIVES = sum(1 for r in LOCK)

# ------------------------------------------------------------------ chapter 17
def v2v4_table():
    k3 = SENS[("k3", "synth")]; x1 = SENS[("X1000_10000", "synth")]
    rows = [["Version 2 account model (1 : 3, funded +$1,000 then +$10,000)", "$2,444", "&mdash;"],
            ["Path engine, 1 : 3, funded cycles of +10%", usd(k3["EV_month"]), f'{k3["days"]:.1f}'],
            ["Path engine, 1 : 5, funded +$1,000 first", usd(x1["EV_month"]), f'{x1["days"]:.1f}'],
            ["<strong>The plan: 1 : 5, funded cycles of +10%</strong>", f'<strong>{usd(S("FTMO 2-Step")["EV_month"])}</strong>', f'{S("FTMO 2-Step")["days"]:.1f}'],
            ["The plan on the real 2024&ndash;26 path", usd(Rl("FTMO 2-Step")["EV_month"]), f'{Rl("FTMO 2-Step")["days"]:.1f}']]
    return table(["FTMO 2-Step 100K, zero edge", "EV per month per slot", "Days per attempt"], rows, hl=(3,))

# ------------------------------------------------------------------ chapter 18 (unchanged data)
def multi_table():
    by = {(r["tag"].split()[0], r["data"]): r for r in MULTI}
    spec = [("A1", "Nasdaq alone, 1.5%", "one position"), ("B1", "Nasdaq + S&amp;P 500, same direction, 0.75% each", "total 1.5%"),
            ("B2", "Nasdaq + S&amp;P 500, same direction, 1.5% each", "&asymp; 2.9% on one idea"), ("A2", "Nasdaq alone, 3% (reference, beyond guidance)", "one position"),
            ("C1", "Nasdaq + gold, 1.5% each, at most 1.5% open", "one at a time"), ("C3", "Nasdaq + gold, 1.5% each", "up to 3% open"),
            ("C5", "Nasdaq + gold + yen + euro, 1.5% each", "up to 4.5% open"), ("T2", "Two independent Nasdaq-like markets (imaginary)", "up to 3% open"),
            ("T6", "Four independent Nasdaq-like markets (imaginary)", "up to 6% open"), ("Z1", "Nasdaq alone, no costs at all", "one position"),
            ("Z3", "Four independent markets, no costs at all", "up to 6% open")]
    base = by[("A1", "synth")]["EV_month"]; rows = []
    for tag, name, risk in spec:
        r = by[(tag, "synth")]
        rows.append([name, risk, usd(r["EV_month"]), f'{(r["EV_month"]/base-1)*100:+.0f}%', f'{r["days"]:.1f}', pct(r["pass_by_phase"][-1])])
    return (table(["Set-up (FTMO 2-Step 100K)", "Open risk", "EV per month", "vs one position", "Days per attempt", "Pass both phases"], rows, num_from=2, hl=(0,)) +
            note("Synthetic zero-edge paths, 6,000 attempts per row, combined target capped. These runs used the version 2 settings (1 : 3, funded +$1,000 first), so compare rows with each other rather than with later chapters. Noise is about &plusmn;$330 per month per row."))

# ------------------------------------------------------------------ chapter 19
def size_table():
    rows = []
    for tag, lab in (("size50000", "FTMO 2-Step 50K"), ("base", "FTMO 2-Step 100K"), ("size200000", "FTMO 2-Step 200K"),
                     ("1step100", "FTMO 1-Step 100K"), ("1step200", "FTMO 1-Step 200K")):
        r = SENS[(tag, "synth")]; K = r["size"] / 100000
        rows.append([lab, usd(r["fee"]), pct(r["fee"] / r["size"], 2), usd(r["EV_month"]), usd(r["EV_month"] / K)])
    return table(["Account", "Fee", "Fee &divide; size", "EV per month", "per $100K of allowance"], rows) + note("1 : 5, funded cycles of +10% of the account, 10,000 synthetic attempts each; noise about &plusmn;8% per row.")
def sens_table():
    def row(label, key):
        r = SENS[key]; return [label, usd(r["EV_month"]), f'{r["days"]:.1f}', pct(r["P"])]
    rows = [row("<strong>The plan</strong> (stop 0.75, 1 : 5, risk 1.5%, +10% cycles)", ("base", "synth")),
            row("&hellip; on the real 2024&ndash;26 path", ("base", "real"))]
    rows += [row(f"Risk {L/1000:g}% per trade" + (" (beyond FTMO's guidance)" if L > 1500 else ""), (f"L{L}", "synth")) for L in (1000, 2000, 3000)]
    rows += [row(f"Stop {m:g} hourly moves", (f"m{m}", "synth")) for m in (0.5, 1.0, 1.5, 3.0)]
    rows += [row(f"Reward : risk 1 : {k}", (f"k{k}", "synth")) for k in (1, 2, 3, 4, 6, 8, 10)]
    rows += [row(f"Reward : risk 1 : {k}, real path", (f"k{k}", "real")) for k in (3, 4, 6, 8)]
    rows += [row(f"Funded: first cycle +${a:,}, then +${b:,}", (f"X{a}_{b}", "synth")) for a, b in ((1000, 10000), (3000, 10000), (5000, 10000), (10000, 20000))]
    return table(["Setting (all else as in the plan)", "EV per month", "Days per attempt", "Pass both phases"], rows, cls="small", hl=(0,)) + \
        note("10,000 attempts per row (seed 31); noise about &plusmn;$300 per month. The plan's final figure from 24,000 attempts with other seeds is " + usd(S("FTMO 2-Step")["EV_month"]) + " (Chapter 20).")

# ------------------------------------------------------------------ chapter 20
NOTES = {"FTMO 2-Step": "10/5%, 4 days per phase, payouts every 14 days", "FTMO 1-Step": "10%, 3% daily, trailing floor, best day &le; 50%",
         "FundingPips 2-Step Flex (95%)": "10/6%, 4% daily, 12% static, 3 profitable days per payout cycle", "FundingPips 2-Step Flex (85%)": "10/6%, 4% daily, 12% static",
         "FundingPips 2-Step (on-demand 90%)": "8/5%, payout any time at &ge; 2%, no day &gt; 35%", "FundingPips 2-Step (bi-weekly 80%)": "8/5%, refund with 4th payout",
         "FundingPips 2-Step (monthly 100%)": "8/5%, 100% split, monthly", "FundedNext Stellar 2-Step": "8/5%, 5 days, +15% of challenge profit, first payout day 21",
         "The5ers High Stakes": "10/5%, 3 profitable days per phase", "The5ers High Stakes Classic": "8/5%, 3 profitable days per phase, $545",
         "Alpha Capital Pro 10%": "10/5%, 3 days, no refund assumed", "FXIFY Two-Phase": "10/5%, refund with 1st payout",
         "GFT 2-Step Standard": "10/5%, funded &le; $3,000/day, first 2 payouts &le; 6%", "BrightFunded 2-Step Classic": "10/5%, 5 days, first payout day 30",
         "Blue Guardian 2-Step": "8/4%, 4% daily, 8% max, 85%", "FunderPro Classic": "10/8%, refund with 1st payout",
         "Maven 2-Step": "8/5%, 4% daily, 8% max, 3 profitable days, $10K/30 days payout cap"}
def cfd_table():
    rows = []
    for f in CFD:
        s, r = S(f), Rl(f)
        rows.append([f"<strong>{sh(f)}</strong><br><span style='color:#5b6370;font-size:7.6pt'>{NOTES.get(f, '')}</span>", usd(FINAL[f]["fee"]),
                     pct(s["P"]), usd(r100(s["Vf"])), f'{s["t_fund"]:.0f}', usd(s["EV"]), f'{s["days"]:.1f}',
                     f'<strong>{usd(s["EV_month"])}</strong>', usd(r["EV_month"]), f'{s["t_first_med"]:.0f}'])
    return table(["Programme (100K)", "Fee", "Pass", "Paid per funded acct", "Funded days", "EV per attempt", "Days per attempt",
                  "EV / month", "Real path", "1st payout (day)"], rows, cls="small", w0="27%")
def fig_firms():
    rows = [(sh(f), S(f)["EV_month"]) for f in CFD] + [(f + " (futures)", S(f)["EV_month"]) for f in FUT]
    rows.sort(key=lambda r: -r[1])
    return hbars(rows, lambda v: (f"${v:,.0f}" if v >= 0 else f"&minus;${-v:,.0f}"),
                 "Figure 20.1 &middot; EV per month per slot, the plan, synthetic zero-edge paths (CFD slots are 100K, futures 50K).")
def fut_table():
    rows = []
    for f in FUT:
        s, r = S(f), Rl(f); st = FINAL[f]["setting"]
        fee = f'{usd(FINAL[f]["fee"])}' + ("/month" if FINAL[f]["monthly"] else "") + (f' + {usd(FINAL[f]["activation"])}' if FINAL[f]["activation"] else "")
        rows.append([f"<strong>{f}</strong><br><span style='color:#5b6370;font-size:8pt'>risk ${st['L']:.0f}, 1 : {st['k']}, flat by 20:00 UTC</span>", fee,
                     pct(s["P"]), usd(s["Vf"]), f'{s["t_fund"]:.0f}', usd(s["EV"]), f'{s["days"]:.1f}',
                     f'<strong>{usd(s["EV_month"])}</strong> &plusmn;{s["EV_month_CI"]:,.0f}', usd(r["EV_month"])])
    return table(["Programme (50K)", "Fee", "Pass", "Paid per funded acct", "Funded days", "EV per attempt", "Days per attempt", "EV / month", "Real path"], rows, cls="small", w0="22%")
def apex_note():
    s = S("Apex 50K EOD"); ev = s["EV"]; d = s["days"]; out = []
    for fee in (147, 98):
        e2 = ev + (490 - fee); out.append(f"at {usd(fee)} (a {100 - fee/4.9:.0f}% discount) it would be {usd(e2)} per attempt, about {usd(e2 / d * 30.44)} per month")
    return "; ".join(out) + "."
def gold_table():
    rows = []
    by = {(g["firm"], g["instr"], g["m"]): g for g in GOLD}
    for firm in ("FundedNext Stellar 2-Step", "FunderPro Classic", "GFT 2-Step Standard"):
        n = by[(firm, "US100", 0.75)]["EV_month"]; g = by[(firm, "XAUUSD", 0.75)]["EV_month"]; e = by[(firm, "EURUSD", 1.0)]["EV_month"]
        rows.append([firm, usd(n), usd(g), f"{(g/n-1)*100:+.0f}%", usd(e), f"{(e/n-1)*100:+.0f}%"])
    return table(["Firm (one account)", "Nasdaq", "Gold", "change", "EURUSD", "change"], rows) + note("EV per month per slot, 12,000 synthetic attempts each, stop 0.75 hourly moves of the market traded (EURUSD: 1.0), 1 : 5.")

# ------------------------------------------------------------------ chapter 21
CAPS = [("FTMO", "$400,000 per trader or strategy, all accounts (treated as including evaluations)", "allowed within the cap", "4"),
        ("FundingPips", "$400,000 across evaluation, funded and Prime accounts", "own FundingPips accounts; no copier services", "4"),
        ("Alpha Capital", "$400,000 per household; $300,000 per strategy", "allowed from own accounts with proof", "3"),
        ("BrightFunded", "$400,000 funded; evaluations unlimited", "allowed between own accounts at any firm", "4"),
        ("Blue Guardian", "$400,000; evaluations up to $200,000 each", "own accounts only", "4"),
        ("The5ers", "one 100K High Stakes account (plus smaller ones)", "allowed", "1"),
        ("FXIFY", "reported $805,000 (one account per size); confirm", "only after approval; herd trading prohibited", "1"),
        ("GFT", "$400,000 funded", "no duplicated trades between GFT accounts", "1"),
        ("FunderPro", "$200,000", "no replicating across FunderPro accounts", "1"),
        ("Maven", "$200,000; payouts &le; $10,000 per 30 days", "own 2-Step accounts", "1"),
        ("FundedNext", "$300,000 funded; evaluations unlimited", "never involving a funded account", "1 (gold)")]
def caps_table():
    rows = [[f"<strong>{a}</strong>", b, c, d] for a, b, c, d in CAPS]
    return table(["Firm", "Allocation cap", "Copying the same trades on several of your accounts", "Max. accounts used"], rows, cls="small", num_from=3, w0="14%")
def portf_table():
    rows = []
    for p in PNAMES:
        x = L[p]
        rows.append([LABEL[p], f'<strong>{usd(r100(x["steady"]))}</strong>', usd(r100(x["year"])),
                     f'{pct(x["ahead"][1])} / {pct(x["ahead"][3])} / {pct(x["ahead"][12])}',
                     f'{k_(x["low50"])} / {k_(x["low05"])}', f'{x["maxbr"]:.0f}'])
    return table(["Version", "Steady month", "First-year average", "Ahead after 1 / 3 / 12 months", "Cash low: typical / bad case (1 in 20)", "Most failed accounts at one firm per month"],
                 rows, hl=(0,), w0="26%") + note(f"Lockstep engine: {L[PNAMES[0]]['n']} simulated years per version on 8 independent zero-edge price paths; shared direction enforced; no opposite positions occurred.")
def real_note():
    a = LR["One account per firm (11 firms)"]; b = LR["Full caps, rules-strict (25 accounts)"]
    return f"{usd(r100(a['steady']))} (one per firm) and {usd(r100(b['steady']))} (full caps) per steady month, with the gold account mapped to the Nasdaq because the real gold series is not aligned with it"
def breach_table():
    one = L["One account per firm (11 firms)"]["breaches"]; full = L["Full caps, rules-strict (25 accounts)"]["breaches"]
    order = sorted(full, key=lambda f: -full[f]); rows = []
    for f in order:
        rows.append([f, f"{one.get(f, 0):.1f}", f"{full[f]:.1f}"])
    return table(["Firm", "One account per firm", "Full caps"], rows, cls="small") + note("Failed evaluations plus lost funded accounts, per firm per month, lockstep engine.")
def staged_table():
    a = L["Full caps, rules-strict (25 accounts)"]; b = L["Full caps, staged start (25 accounts)"]
    rows = []
    for lab, x in (("All 25 accounts on day one", a), ("Firms added month by month (FTMO; then FundingPips and The5ers; then FundedNext and Alpha; then BrightFunded, Blue Guardian, FunderPro; then FXIFY, GFT, Maven)", b)):
        rows.append([lab, usd(r100(x["year"])), f'{pct(x["ahead"][1])} / {pct(x["ahead"][3])} / {pct(x["ahead"][6])}', f'{k_(x["low50"])} / {k_(x["low05"])}'])
    return table(["Full caps", "First-year average", "Ahead after 1 / 3 / 6 months", "Cash low: typical / bad case"], rows, w0="46%")

# ------------------------------------------------------------------ chapter 22
def dir_table():
    rows = [["Random direction (version 2)", "$1,802 / $1,928", "$3,587 / $3,755", "30%"],
            ["Trend, 20 hours", "$885 / $869", "$2,074 / $2,024", "30%"],
            ["Trend, 5 hours", "$2,733 / $2,801", "$4,613 / $4,740", "35&ndash;36%"],
            ["Reversal, 5 hours", "$1,064 / $1,110", "$2,327 / $2,427", "25%"]]
    return table(["Rule (FTMO 2-Step, 1 : 3, real 2024&ndash;26 path)", "EV per attempt (two runs)", "EV per month (two runs)", "Pass both"], rows)
DIRP = [(21, 3955, 5239), (22, 3989, 3739), (23, 4610, 4208), (24, 4303, 3609), (25, 4188, 4949), (26, 3999, 4981), (27, 4239, 5089), (28, 4019, 3729)]
def dir_paths():
    rows = [[f"Path {i+1}", usd(a), usd(b), (f"+${b-a:,}" if b >= a else f"&minus;${a-b:,}")] for i, (_, a, b) in enumerate(DIRP)]
    d = np.array([b - a for _, a, b in DIRP])
    rows.append(["<strong>Average</strong>", usd(np.mean([a for _, a, _ in DIRP])), usd(np.mean([b for _, _, b in DIRP])), f"+${d.mean():,.0f} &plusmn; {1.96*d.std(ddof=1)/len(d)**.5:,.0f}"])
    return table(["Independent zero-edge path", "Random", "Trend, 5 hours", "Difference"], rows, cls="small", hl=(len(rows) - 1,)) + note("FTMO 2-Step, the plan, 4,000 attempts per cell; EV per month per slot.")

# ------------------------------------------------------------------ chapter 23: audit
AUDIT = [
 ("FTMO", "Risk 1&ndash;1.5% recommended; gambling (no plan, all-in) monitored; account rolling forbidden; $400,000 per strategy; no opposite positions across accounts or providers; funded Standard: no weekend holding, &plusmn;2 min news; gap trading forbidden", "1.5% with stop; written rules; every account traded identically (none sacrificed); 4 &times; 100K; shared direction; flat at weekends and 10 min before news", "ok"),
 ("FundingPips Flex", "Risk per trade idea 2% on funded (Master) accounts; no opposite account trading; no weekend holding on Master; &plusmn;5 min restricted news; copying only between own FundingPips accounts; 95% split needs 3 profitable days per cycle", "1.5%; shared direction; flat at weekends and before news; one own program per account; daily profit target until 3 days of +0.5%", "ok"),
 ("Alpha Capital", "Never risk or lose 2% or more in one trade or group closed together; no all-or-nothing (large lot and length swings); group trading forbidden; $300,000 per strategy", "1.5%, one position; constant size; own accounts only; 3 accounts", "ok"),
 ("BrightFunded", "Trades at least 60 seconds; no gap trading around news; no over-exposure; funded &plusmn;5 min news; copying between own accounts allowed", "trades last hours; flat before news; one position", "ok"),
 ("Blue Guardian", "Funded: all trades closed at &minus;2% open loss (first time split cut to 50%, second time account closed); no 3&ndash;4% risk without stop; copying own accounts only", "1.5% with stop: open loss stays below 2% unless a gap", "ok, watch gaps"),
 ("The5ers", "Profitable days must not be constructed artificially; no abrupt size changes or over-exposure; no new orders &plusmn;2 min of high-impact news; programs need written approval", "daily profit target with full risk; constant size; news window wider than required; trade by hand or get approval", "check the daily profit target with The5ers"),
 ("FXIFY", "Herd trading and collusion forbidden; copying own accounts only after approval; gambling forbidden", "one account", "ok"),
 ("GFT", "No duplicated trades between GFT accounts; no third-party or marketed strategy; no martingale; no all-or-nothing", "one account; own rules; size never increases after a loss", "ok, if the plan stays private"),
 ("FunderPro", "Risk per trade at most 2%; no replicating trades across accounts; no copying from accounts you do not own", "1.5%; one account", "ok"),
 ("Maven", "3 profitable days of +0.5% per phase; after $5,000 paid, no day above 50% of profit; payouts at most $10,000 per 30 days", "daily profit target; capped take-profit; one account", "ok"),
 ("FundedNext", "No copying when a funded account is involved; one-sided betting, account rolling and gambling (including many quick breaches) prohibited; trades shorter than 30 s, hyperactivity", "one account, on gold, independent of the others; one position", "ok, quick breaches unavoidable"),
]
def audit_table():
    rows = [[f"<strong>{a}</strong>", b, c, d] for a, b, c, d in AUDIT]
    return table(["Firm", "Rules that touch the plan", "How the plan meets them", "Status"], rows, cls="small", num_from=9, w0="11%")

# ------------------------------------------------------------------ part 2
def sizing_v3():
    V, stop, spread = 1.0, 64, 1.4
    cases = [("Phase 1, start", 100000, 100000, 110000), ("Phase 1, near target", 106500, 106500, 110000),
             ("Phase 1, after a bad morning", 95400, 99000, 110000), ("Phase 1, near the floor", 90900, 90900, 110000),
             ("Phase 2, near target", 104000, 104000, 105000)]
    rows = []
    for name, bal, sod, tgt in cases:
        room = bal - 90000; dayroom = 5000 - (sod - bal); risk = min(1500, room - 100, dayroom - 200)
        lots = math.floor(risk / (stop * V) * 100) / 100; cost = (spread + 0.6) * lots * V
        togo = tgt - bal; target = min(5 * risk, togo + cost + 5); tp = target / (lots * V); p = stop / (stop + tp)
        rows.append([name, f"${bal:,}", f"${room:,}", f"${dayroom:,}", f"${risk:,.0f}", f"{lots:.2f}", f"${cost:,.0f}", f"${target:,.0f}", f"{tp:.0f}", f"{p*100:.0f}%"])
    return table(["Situation", "Balance", "Room to floor", "Day room", "Risk", "Lots", "Cost", "Target $", "Target pts", "Win chance"], rows, cls="small")
RULES = [
 ("FTMO 2-Step", "10% / 5%", "5% / 10% static", "4 per phase", "every 14 days, 80%", "1st payout", "no", "&plusmn;2 min", "none"),
 ("FundingPips Flex 95%", "10% / 6%", "4% / 12% static", "none", "every 14 days, 95% (3 profitable days per cycle)", "4th payout (assumed)", "no", "&plusmn;5 min", "risk per idea &le; 2%"),
 ("Alpha Capital Pro 10%", "10% / 5%", "5% / 10% static", "3 per phase", "14-day cycle, 80%", "not assumed", "no", "&plusmn;2 min", "risk &lt; 2%; best day 40% on on-demand"),
 ("BrightFunded Classic", "10% / 5%", "5% / 10% static", "5 per phase", "day 30, then every 14 days, 80%", "1st payout", "allowed", "&plusmn;5 min", "trades &ge; 60 s"),
 ("Blue Guardian 2-Step", "8% / 4%", "4% / 8%", "3 per phase", "every 14 days, 85%", "not assumed", "check", "check", "funded: shield at &minus;2% open loss"),
 ("The5ers High Stakes", "10% / 5%", "5% / 10%", "3 profitable days (&ge; 0.5%)", "every 14 days, 80%", "check", "allowed", "&plusmn;2 min", "programs need approval"),
 ("FXIFY Two-Phase", "10% / 5%", "5% / 10% (one source: 4% / trailing)", "check", "14 days 80% or 30 days 100%", "1st payout", "allowed", "allowed", "copying needs approval"),
 ("GFT 2-Step Standard", "10% / 5%", "5% / 10% static", "check", "every 14 days, 80%", "refundable", "check", "check", "funded &le; $3,000/day; first 2 payouts &le; 6%"),
 ("FunderPro Classic", "10% / 8%", "5% / 10% static", "none", "every 14 days, 80%", "1st payout", "check", "check", "risk per trade &le; 2%"),
 ("Maven 2-Step", "8% / 5%", "4% / 8% static", "3 profitable days (&ge; 0.5%)", "about every 10 business days, 80%", "3rd payout", "check", "check", "$10,000 per 30 days; 50% best day after $5,000"),
 ("FundedNext Stellar 2-Step", "8% / 5%", "5% / 10% static", "5 per phase", "day 21, then every 14 days, 80%", "1st payout; +15% of challenge profit", "check", "check", "no copying with funded accounts"),
]
def rules_table():
    h1 = ["Programme (100K)", "Targets", "Daily / max loss", "Minimum days", "Funded payouts", "Fee refund"]
    h2 = ["Programme (100K)", "Weekend (funded)", "News (funded)", "Other limits"]
    r1 = [[f"<strong>{r[0]}</strong>"] + list(r[1:6]) for r in RULES]
    r2 = [[f"<strong>{r[0]}</strong>"] + list(r[6:]) for r in RULES]
    return table(h1, r1, cls="small", num_from=99, w0="18%") + table(h2, r2, cls="small", num_from=99, w0="18%") + \
        note('"check": not found in a reliable public source; ask the firm before buying. The plan is flat at weekends and around news on every account, so those columns rarely bind.')
def work_table():
    rows = []
    for p in ("One account per firm (11 firms)", "Two per firm where copying is allowed (16 accounts)", "Full caps, rules-strict (25 accounts)", "FTMO only (4 x 100K)"):
        x = L[p]; rows.append([LABEL[p], f'{x["entries"]:.0f}', f'{x["orders"]:.0f}', f'{x["orders90"]:.0f}'])
    return table(["Version", "Entry moments per trading day", "Order tickets per trading day", "Busy day (1 in 10)"], rows) + note("Lockstep engine averages over simulated trading days.")
FUNDED_FIRMS = ["FTMO 2-Step", "FundingPips 2-Step Flex (95%)", "Alpha Capital Pro 10%", "BrightFunded 2-Step Classic", "Blue Guardian 2-Step",
                "The5ers High Stakes", "FXIFY Two-Phase", "GFT 2-Step Standard", "FunderPro Classic", "Maven 2-Step", "FundedNext Stellar 2-Step"]
def funded_table():
    rows = []
    for f in FUNDED_FIRMS:
        s = S(f); rows.append([sh(f), pct(s["P"]), usd(r100(s["Vf"])), f'{s["t_fund"]:.0f}', f'{s["t_first_med"]:.0f}'])
    return table(["Programme", "Attempts that reach funded", "Paid per funded account (average)", "Funded account lasts (days)", "First payout (day, median)"], rows)
def milestones():
    M = MILE
    rows = [["Phase 1 decided (pass about " + pct(M["P1"]) + ")", f'day {M["p1_day"][0]:.0f} (middle half {M["p1_day"][1]:.0f}&ndash;{M["p1_day"][2]:.0f})'],
            ["Phase 2 decided (pass about " + pct(M["P2_given_1"]) + " of those who reach it)", f'day {M["p2_day"][0]:.1f}'],
            ["Funded account issued", f'day {M["funded_day"][0]:.0f}'],
            ["First payout received, fee refunded (" + pct(M["share_funded_paid"]) + " of funded accounts)", f'day {M["first_pay_day"][0]:.0f} (middle half {M["first_pay_day"][1]:.0f}&ndash;{M["first_pay_day"][2]:.0f})'],
            ["Funded account ends", f'day {M["end_day"][0]:.0f} (middle half {M["end_day"][1]:.0f}&ndash;{M["end_day"][2]:.0f})']]
    return table(["Milestone, FTMO 2-Step, from the day you buy", "Typical day"], rows)
def weekly_table():
    rows = []
    o = WEEK["One account per firm (11 firms)"]; f4 = WEEK["FTMO only (4 x 100K)"]
    for w in (1, 2, 3, 4, 6, 8, 10, 13, 17, 26):
        i = w - 1
        rows.append([f"Week {w}", usd(r100(o["p10"][i])), f'<strong>{usd(r100(o["p50"][i]))}</strong>', usd(r100(o["p90"][i])), pct(o["ahead"][i]),
                     usd(r100(f4["p50"][i])), pct(f4["ahead"][i])])
    return table(["After", "Eleven firms: bad (1 in 10)", "typical", "good (1 in 10)", "ahead", "FTMO only: typical", "ahead"], rows) + note("Cumulative cash from the day all accounts are opened; 160 simulated years per version.")
def diary_table():
    rows = []
    for r in DIARY["rows"]:
        rows.append([f'{r["week"]}', f'{r["buys"]}', usd(r["fees"]), f'{r["p1_pass"]} / {r["p1_fail"]}', f'{r["funded"]} / {r["p2_fail"]}',
                     f'{r["funded_lost"]}', (f'{r["payouts"]} ({", ".join(r["paid_by"])})' if r["payouts"] else "&ndash;"), usd(r["cash_in"]) if r["cash_in"] else "&ndash;", usd(r["cum"])])
    t1 = table(["Week", "Evaluations bought", "Fees", "Phase 1 pass / fail", "Funded / Phase 2 fail", "Funded lost", "Payouts (firms)", "Cash in", "Cumulative cash"], rows, cls="small", num_from=1)
    cum = np.cumsum(DIARY["monthly"])
    t2 = table(["Month"] + [str(i) for i in range(1, 13)], [["Cumulative cash"] + [k_(c) for c in cum]], cls="small")
    return t1 + t2 + note(f"Lowest point of cumulative cash in this year: {usd(r100(DIARY['low13w']))}.")
def months_table():
    rows = []
    for p in ("One account per firm (11 firms)", "Full caps, rules-strict (25 accounts)", "FTMO only (4 x 100K)"):
        x = L[p]
        for h in (1, 3, 6, 12):
            lo, md, hi = x["cum_p"][h]
            rows.append([LABEL[p] if h == 1 else "", f"{h}", pct(x["ahead"][h]), k_(md), k_(lo), k_(hi)])
    return table(["Version", "Months", "Chance ahead", "Median cash", "Bad case (1 in 20)", "Good case (1 in 20)"], rows, num_from=1) + \
        note("Cumulative cash (payouts minus fees), all accounts opened at the start, lockstep engine. Cash low points are in Chapter 21.")

def cost_table():
    by = {(r["firm"], r["cost_mult"]): r for r in ROB["cost"]}; rows = []
    for f in ("FTMO 2-Step", "FundingPips 2-Step Flex (95%)", "Blue Guardian 2-Step"):
        base = by[(f, 1.0)]["EV_month"]
        rows.append([sh(f)] + [f'{usd(by[(f, c)]["EV_month"])}' + ("" if c == 1.0 else f' ({(by[(f, c)]["EV_month"]/base-1)*100:+.0f}%)') for c in (1.0, 1.5, 2.0, 3.0)])
    return table(["Programme", "Measured costs", "&times; 1.5", "&times; 2", "&times; 3"], rows) + note("EV per month per slot, 8,000 synthetic attempts per cell; the cost multiplier applies to spread, commission and slippage.")
def refusal_table():
    rows = []
    for q in ("0.0", "0.02", "0.05", "0.1", "0.2"):
        r = ROB["refusal"][q]; base = ROB["refusal"]["0.0"]["year_avg"]
        rows.append([f"{float(q)*100:.0f}%", usd(r100(r["year_avg"])), f'{(r["year_avg"]/base-1)*100:+.0f}%' if q != "0.0" else "&ndash;",
                     f'{r["firms_lost"]:.1f}', pct(r["p_ahead12"]), k_(r["p05_12"])])
    return table(["Chance each payout is refused", "First-year average per month", "vs all paid", "Firms lost in the year", "Ahead after 12 months", "12-month cash, bad case (1 in 20)"], rows)

# ------------------------------------------------------------------ key results
def key_results():
    one = L["One account per firm (11 firms)"]; full = L["Full caps, rules-strict (25 accounts)"]; ftmo = L["FTMO only (4 x 100K)"]
    best = max(CFD, key=lambda f: S(f)["EV_month"])
    rows = [
      ["Chance a zero-skill trader passes FTMO Phase 1 / both phases (the plan)", f'{pct(MILE["P1"])} / {pct(S("FTMO 2-Step")["P"])}', "Ch. 3&ndash;4, 29"],
      ["The plan: Nasdaq, one position, stop 0.75 hourly moves, <strong>1 : 5</strong>, risk 1.5%, funded cycles of the full allowance", f'{usd(S("FTMO 2-Step")["EV"])} per FTMO attempt, {S("FTMO 2-Step")["days"]:.1f} days', "Ch. 19, 24"],
      ["EV per month per FTMO 100K slot (synthetic / real path)", f'{usd(r100(S("FTMO 2-Step")["EV_month"]))} / {usd(r100(Rl("FTMO 2-Step")["EV_month"]))}', "Ch. 20"],
      ["Best programme found: " + sh(best), f'{usd(r100(S(best)["EV_month"]))} per month per slot', "Ch. 20"],
      ["Several positions at once (Nasdaq + S&amp;P, many pairs)", "no gain at the same risk", "Ch. 18"],
      ["100K vs 200K accounts, per dollar of allowance", "about the same; 50K worse", "Ch. 19"],
      ["Futures programmes", "small or negative; left out", "Ch. 20"],
      ["<strong>Per person, one account at each of 11 firms (default)</strong>", f'<strong>{usd(r100(one["steady"]))}</strong> per steady month', "Ch. 21"],
      ["&hellip; chance ahead after 1 / 3 / 12 months; bad-case cash low", f'{pct(one["ahead"][1])} / {pct(one["ahead"][3])} / {pct(one["ahead"][12])}; {k_(one["low05"])}', "Ch. 21, 30"],
      ["Per person, full caps (25 accounts)", f'{usd(r100(full["steady"]))} per steady month; up to {full["maxbr"]:.0f} failed accounts a month at one firm', "Ch. 21"],
      ["Per person, FTMO only (4 &times; 100K or 2 &times; 200K)", f'{usd(r100(ftmo["steady"]))} per steady month', "Ch. 21"],
      ["Rule audit: firms where only one account may carry the plan's trades", "GFT, FunderPro, FundedNext (gold), FXIFY", "Ch. 23"],
      ["If each payout had a 5% chance of being refused (and the firm lost)", f'{(ROB["refusal"]["0.05"]["year_avg"]/ROB["refusal"]["0.0"]["year_avg"]-1)*100:+.0f}% of the value', "Ch. 31"],
    ]
    rr = ""
    for i, (a, b, c) in enumerate(rows):
        cls = ' class="hl"' if i in (2, 7) else ""
        rr += f'<tr{cls}><td>{a}</td><td class="n">{b}</td><td>{c}</td></tr>'
    return f"""
<!-- ================================================================ KEY RESULTS -->
<section class="chapter">
  <span class="eyebrow">Summary</span>
  <h1>Key results at a glance</h1>
  <p>Version 4 re-runs every figure on price paths with the firms' rules as written, checks every rule that touches the plan (Chapter 23), adds four more firms and better programmes, and simulates one person running all accounts at once in lockstep. "Zero skill" means no trade direction is better than chance. Every figure assumes the firms pay every payout.</p>
  <table><thead><tr><th>Quantity</th><th class="n">Value</th><th>Where</th></tr></thead><tbody>{rr}</tbody></table>
  <div class="box key"><h4>What changed in version 4</h4>
  <ol>
    <li><strong>Rules as written.</strong> Gaps through the daily limit, weekend and overnight rules, profitable days that may not be manufactured, best-day caps: all enforced. The5ers fell by about a quarter; futures got weaker.</li>
    <li><strong>Copying rules decide the shape.</strong> GFT, FunderPro, FundedNext (funded) and FXIFY limit or forbid the same trades on several of their accounts: one account each.</li>
    <li><strong>One account per firm by default.</strong> Eleven firms with one account each give about three times FTMO-alone's value with a similar bad-case cash low, and only about two failed accounts a month at each firm.</li>
    <li><strong>New and better products:</strong> FundingPips Flex 95% (12% allowance), Blue Guardian, BrightFunded, FunderPro, Maven.</li>
    <li><strong>Lockstep test:</strong> {LIVES:,} simulated years of one person running every account on one price path; no two accounts ever held opposite positions.</li>
    <li><strong>Private use only.</strong> The same rules traded by several people would be prohibited group trading.</li>
  </ol></div>
</section>
"""

TOC = [("p", "", "Key results at a glance"), ("p", "I", "Part 1 &middot; The mathematics"),
    ("", "1", "The contract you are buying"), ("", "2", "Probability from zero"), ("", "3", "Reaching a target before a floor"),
    ("", "4", "The challenge, step by step"), ("", "5", "What a funded account is worth"), ("", "6", "Putting it together"), ("", "7", "Trading costs"),
    ("", "8", "Time: how long an attempt takes"), ("", "9", "Instruments, leverage and platforms (crypto, futures)"),
    ("", "10", "Maximising expected value per month (version 2)"), ("", "11", "Other firms and other rule types (version 1)"),
    ("", "12", "Variance, bankroll and Kelly"), ("", "13", "Hedging"), ("", "14", "Testing on real market data"),
    ("", "15", "Errors in the earlier documents"), ("", "16", "What the mathematics cannot tell you"),
    ("", "17", "Every trade resolved on a price path"), ("", "18", "Many positions at once"),
    ("", "19", "Account size, account type and the settings that matter"), ("", "20", "Every firm, compared on the same paths"),
    ("", "21", "The maximum per person"), ("", "22", "Direction rules, and what one price history can tell you"),
    ("", "23", "Rule audit: every firm, every rule that touches the plan"),
    ("p", "II", "Part 2 &middot; Execution"), ("", "24", "The plan on one page"), ("", "25", "Before you start"),
    ("", "26", "The trade, step by step"), ("", "27", "Firm-by-firm rule sheet"), ("", "28", "Running many accounts: the daily routine"),
    ("", "29", "Funded accounts and payouts"), ("", "30", "Signing up: the first three months, simulated"),
    ("", "31", "Month by month: cash, odds and when to stop"), ("", "32", "Final checklist"),
    ("p", "A&ndash;D", "Appendices: formula sheet and glossary, account types (version 1), method and sources, version 4 sources")]

APPX_D = """
<section class="chapter">
  <span class="eyebrow">Appendix D</span>
  <h1>Versions 3&ndash;4: firm rules and sources</h1>
  <p>Collected in October 2026 from the firms' own pages where possible and otherwise from review sites. Prices change with promotions; the fee used is shown in Chapter 20. Check every item against the firm's current terms before buying.</p>
  <table class="small"><thead><tr><th>Topic</th><th>Source</th></tr></thead><tbody>
  <tr><td>FTMO: accounts, $400,000 cap, identical strategies</td><td>ftmo.com/en/faq/how-many-accounts-can-i-have/</td></tr>
  <tr><td>FTMO: monitored behaviour, forbidden practices, account rolling</td><td>ftmo.com/en/blog/why-ftmo-monitors-certain-patterns-in-trading-behaviour/; ftmo.com/en/forbidden-trading-practices/</td></tr>
  <tr><td>FTMO: 1-Step / 2-Step rules, news and weekend, minimum days</td><td>propfirmbriefing.com/prop-firm-rules/ftmo/; tradetanto.com (FTMO rules)</td></tr>
  <tr><td>FundingPips: models, Flex, payouts, caps, risk per trade idea, copying, weekend</td><td>proptradingvibes.com/blog/fundingpips-rules; help.fundingpips.com (2 Step Flex); fundingpips.com/blog/fundingpips-maximum-allocation</td></tr>
  <tr><td>FundedNext: caps, prohibited strategies, copy-trading rule</td><td>help.fundednext.com (How many accounts; Restricted/Prohibited Trading Strategies; Copy Trading Rule)</td></tr>
  <tr><td>The5ers: High Stakes, prohibited practices, copying, programs</td><td>the5ers.com/high-stakes/; the5ers.com/faqs/prohibited-trading-practices/; propfirmbridge.com</td></tr>
  <tr><td>Alpha Capital: rules, risk limit, caps, prohibited strategies</td><td>tradetanto.com (Alpha Capital rules); help.alphacapitalgroup.uk; propvator.com</td></tr>
  <tr><td>FXIFY: programmes, copy-trading approval, cap</td><td>tradingfinder.com/props/fxify/rules/; fxify.com FAQs; propvator.com/blog/fxify-max-capital-allocation/</td></tr>
  <tr><td>GFT: prohibited practices (duplicates, marketed strategies), cap</td><td>help.goatfundedtrader.com (What are Prohibited Trading Practices?); propvator.com</td></tr>
  <tr><td>BrightFunded: 2-Step Classic, cap, refund, copying, prohibited practices</td><td>tradetanto.com (BrightFunded rules); proptradingvibes.com (BrightFunded); tradingfinder.com</td></tr>
  <tr><td>Blue Guardian: 2-Step, Guardian Shield, cap, copying</td><td>help.blueguardian.com (2 Step Standard Rules); blueguardian.com blog (Guardian Shield)</td></tr>
  <tr><td>FunderPro: Classic, cap, risk per trade, replication rule</td><td>support.funderpro.com; thetrustedprop.com; traderfuel.net</td></tr>
  <tr><td>Maven: 2-Step, cap, payout cap, copying</td><td>propfirmmatch.com (Maven); thepropfirmguide.com; propfirmsradar.com</td></tr>
  <tr><td>Apex, Topstep, Tradeify, Lucid: rules, prices, payouts, account limits</td><td>proptradingvibes.com (Apex, Topstep, Lucid); phidiaspropfirm.com (Tradeify); blog.traderspost.io</td></tr>
  </tbody></table>
  <h2>D.1 Method in one paragraph</h2>
  <p>Synthetic paths: 12 years of hourly bars, zero-drift random walk at the market's hourly volatility (Nasdaq 0.27%), exact Brownian-bridge extremes, weekends closed; eight independent paths for portfolios. Costs: 0.0064% of notional per round trip (US100 CFD), 0.0108% (gold), 0.0027% (micro futures), plus financing. 24,000 synthetic and 8,000 real-path attempts per programme; portfolios from the lockstep engine (all accounts on one path and calendar, shared direction enforced).</p>
</section>
"""

# ------------------------------------------------------------------ assemble from version 2
s = open("prop_firm_option_v2.html").read()
i_kr = s.index("<!-- ================================================================ KEY RESULTS -->")
i_p1 = s.index("<!-- ================================================================ PART 1 -->")
i_p2 = s.index("<!-- ================================================================ PART 2 -->")
i_ap = s.index("<!-- ================================================================ APPENDICES -->")
head, p1, appx = s[:i_kr], s[i_p1:i_p2], s[i_ap:]
tail_i = appx.rindex("</body>"); appx_body, appx_end = appx[:tail_i], appx[tail_i:]
def rep(txt, a, b):
    assert a in txt, a[:80]; return txt.replace(a, b)
head = rep(head, "Mathematics and execution &middot; Version 2 &middot; October 2026", "Mathematics and execution &middot; Version 4 &middot; October 2026")
head = rep(head, "how to get it as fast as possible, and how to run it inside the firm's rules.",
           "how to get it as fast as possible, how far it scales per person, and how to run it inside every firm's written rules.")
head = rep(head, "In the execution plan about three attempts in four lose their full fee; after one month the chance of being ahead is about 5%",
           "In the execution plan about seven attempts in ten lose their full fee; the first month is usually negative")
toc_old = head[head.index('<ul class="toc">'):head.index("</ul>", head.index('<ul class="toc">')) + 5]
toc_new = '<ul class="toc">' + "".join(f'<li class="{c}"><span class="n">{n}</span><span class="t">{tx}</span></li>' if c else
    f'<li><span class="n">{n}</span><span class="t">{tx}</span></li>' for c, n, tx in TOC) + "</ul>"
head = head.replace(toc_old, toc_new)
head = head.replace("</head>", "<style>.toc{font-size:8.6pt}.toc li{padding:0.45mm 0}</style></head>", 1)
NOTE10 = ('<div class="box warn"><h4>Version 4 note</h4><p style="margin:0">This chapter is version 2\'s analysis. Chapters 17&ndash;23 redo it on price paths with the firms\' rules as written and find a better plan '
          '(1 : 5, funded cycles of the full allowance) and higher values per month. Where the figures differ, Chapters 17&ndash;23 hold.</p></div>')
m = re.search(r'(<span class="eyebrow">Chapter 10</span>\s*<h1>[^<]*</h1>)', p1); assert m
p1 = p1.replace(m.group(1), m.group(1) + "\n  " + NOTE10, 1)
m = re.search(r'(<span class="eyebrow">Chapter 11</span>\s*<h1>[^<]*</h1>)', p1); assert m
p1 = p1.replace(m.group(1), m.group(1) + "\n  " + NOTE10.replace("This chapter is version 2's analysis.", "This chapter is version 1's firm comparison.").replace("(1 : 5, funded cycles of the full allowance) and higher values per month", "for every major firm (Chapter 20)"), 1)

new1 = open("v4_part1_new.html").read(); new2 = open("v4_part2.html").read()
one = L["One account per firm (11 firms)"]; full = L["Full caps, rules-strict (25 accounts)"]; ftmo = L["FTMO only (4 x 100K)"]
dd = np.array([b - a for _, a, b in DIRP])
subs = {
  "{{LIVES}}": f"{LIVES:,}", "{{V2V4_TABLE}}": v2v4_table(), "{{MULTI_TABLE}}": multi_table(), "{{SIZE_TABLE}}": size_table(),
  "{{FTMO1}}": usd(r100(S("FTMO 1-Step")["EV_month"])), "{{FTMO2}}": usd(r100(S("FTMO 2-Step")["EV_month"])), "{{SENS_TABLE}}": sens_table(),
  "{{X_GAIN}}": f'{usd(SENS[("base","synth")]["EV_month"])} per month with +10% cycles against {usd(SENS[("X1000_10000","synth")]["EV_month"])} with +$1,000 first',
  "{{CFD_TABLE}}": fig_firms() + cfd_table(),
  "{{CFD_LO}}": usd(r100(np.percentile([S(f)["EV_month"] for f in CFD], 15))), "{{CFD_HI}}": usd(r100(np.percentile([S(f)["EV_month"] for f in CFD], 85))),
  "{{GOLD_TABLE}}": gold_table(), "{{FUT_TABLE}}": fut_table(), "{{APEX_NOTE}}": apex_note(),
  "{{CAPS_TABLE}}": caps_table(), "{{PORTF_TABLE}}": portf_table(), "{{REAL_NOTE}}": real_note(), "{{BREACH_TABLE}}": breach_table(),
  "{{STAGED_TABLE}}": staged_table(),
  "{{UNCAPPED}}": usd(r100(S("FundedNext Stellar 2-Step")["EV_month_funded_slot"])), "{{CAPPED}}": usd(r100(S("FundedNext Stellar 2-Step")["EV_month"])),
  "{{DIR_TABLE}}": dir_table(), "{{DIR_PATHS}}": dir_paths(), "{{DIR_MEAN}}": f"+${dd.mean():,.0f} &plusmn; {1.96*dd.std(ddof=1)/len(dd)**.5:,.0f}",
  "{{DIR_MIN}}": f"&minus;${abs(dd.min()):,.0f}", "{{DIR_MAX}}": f"+${dd.max():,.0f}", "{{AUDIT_TABLE}}": audit_table(),
  "{{AHEAD_W6}}": pct(WEEK["One account per firm (11 firms)"]["ahead"][5]), "{{AHEAD_W13}}": pct(WEEK["One account per firm (11 firms)"]["ahead"][12]),
  "{{LOW_ONE}}": k_(one["low05"]).replace("&minus;", ""), "{{LOW_FTMO}}": k_(ftmo["low05"]).replace("&minus;", ""),
  "{{SIZING_V3}}": sizing_v3(), "{{RULES_TABLE}}": rules_table(), "{{WORK_TABLE}}": work_table(), "{{FUNDED_TABLE}}": funded_table(),
  "{{MILESTONES}}": milestones(), "{{WEEKLY_TABLE}}": weekly_table(),
  "{{FIRSTPAY_ONE}}": f'{WEEK["One account per firm (11 firms)"]["first_payout_day"][1]:.0f}', "{{FIRSTPAY_ONE_P90}}": f'{WEEK["One account per firm (11 firms)"]["first_payout_day"][2]:.0f}',
  "{{FIRSTPAY_FTMO}}": f'{WEEK["FTMO only (4 x 100K)"]["first_payout_day"][1]:.0f}',
  "{{DIARY_TABLE}}": diary_table(), "{{MONTHS_TABLE}}": months_table(),
  "{{COST_TABLE}}": cost_table(), "{{REFUSAL_TABLE}}": refusal_table(),
  "{{HEAD_ONE}}": usd(r1000(one["steady"])), "{{HEAD_FULL}}": usd(r1000(full["steady"])),
}
body = new1 + new2
for k, v in subs.items():
    assert k in body, k
    body = body.replace(k, v)
assert "{{" not in body, re.findall(r"\{\{\w+\}\}", body)
doc = head + key_results() + p1 + body + appx_body + APPX_D + appx_end
open("prop_firm_option_v4.html", "w").write(doc)

from playwright.sync_api import sync_playwright
footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
          'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v4</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium"
    b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + str(pathlib.Path("prop_firm_option_v4.html").resolve()), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(1500)
    pg.pdf(path="The_Prop_Firm_Option_v4.pdf", format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<div></div>", footer_template=footer)
    b.close()
print("built v4")
