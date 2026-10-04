import re, json, math, html, pathlib
src = open("build_doc.py").read()
exec(src[:src.index('doc = open("doc_template.html").read()')])   # figure helpers & data

FIRMS_OPT = json.load(open("opt_firms.json"))
FINE = json.load(open("opt_ftmo_fine.json")) + json.load(open("opt_ftmo_grid.json"))

# ------------------------------------------------------------------ new figures
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

def fig_eff():
    rows = [("Nasdaq micro futures (MNQ)", 1141), ("US100 CFD (FTMO)", 481), ("USDJPY", 265), ("Gold XAUUSD", 257),
            ("US500 CFD", 242), ("EURUSD", 147), ("GBPUSD", 120), ("ETHUSD CFD (FTMO)", 91),
            ("BTCUSD CFD (FTMO)", 63), ("BTC (Breakout)", 59), ("BTC perp (HyroTrader)", 49)]
    return hbars(rows, lambda v: f"{v:,.0f}", "Figure 9.1 &middot; Weekly move divided by round-trip cost. Higher means an instrument can be traded faster for the same cost.")

def fig_stop():
    # EV/month vs stop (hourly moves) for US100, FTMO 2-Step, risk 1.5%, cycle target 10k; k=2 and k=3
    def series(k):
        best = {}
        for r in FINE:
            if r["instr"] == "US100" and r["k"] == k and r["L"] == 1500 and r["X"] == 10000:
                if r["m"] not in best or r["n"] > best[r["m"]]["n"]: best[r["m"]] = r
        return sorted((m, v["EV_month"]) for m, v in best.items())
    s2, s3 = series(2), series(3)
    ms = sorted(set(m for m, _ in s2 + s3))
    W, H, ml, mr, mt, mb = 600, 220, 52, 30, 12, 36
    pw, ph = W - ml - mr, H - mt - mb
    xs = [0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 9]
    import math as _m
    X = lambda m: ml + pw * (_m.log(m) - _m.log(0.5)) / (_m.log(9) - _m.log(0.5))
    Y = lambda v: mt + ph * (1 - v / 2800)
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for v in (0, 700, 1400, 2100, 2800):
        o.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{RULE}" stroke-width="0.8"/>')
        o.append(t(ml - 6, Y(v) + 3, f"${v:,}", 8, "end", MUT, True))
    for m in xs:
        o.append(t(X(m), H - mb + 14, f"{m:g}", 8, "middle", MUT, True))
    o.append(t(ml + pw / 2, H - 4, "stop size, in hourly moves (log scale)", 8.5, "middle"))
    for ser, col, name, dy in ((s2, S1, "1 : 2", 4), (s3, S2, "1 : 3", -6)):
        pts = " ".join(f"{X(m):.1f},{Y(v):.1f}" for m, v in ser)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
        for m, v in ser:
            o.append(f'<circle cx="{X(m):.1f}" cy="{Y(v):.1f}" r="3.4" fill="#fff" stroke="{col}" stroke-width="1.8"/>')
        if name == "1 : 3":
            m0, v0 = ser[0]
            o.append(t(X(m0) + 4, Y(v0) - 9, f"reward : risk {name}", 8.6, "start", S2))
        else:
            m_last, v_last = ser[-1]
            o.append(t(X(m_last) - 4, Y(v_last) - 9, f"reward : risk {name}", 8.6, "end", S1))
    o.append("</svg>")
    return fig("".join(o), "Figure 10.1 &middot; EV per month per slot against stop size. FTMO 2-Step, US100, 1.5% risk, zero edge. The best stops are short.")

def fig_firms_month():
    rows = [("The5ers High Stakes", 3183), ("FundingPips 2-Step bi-weekly", 2967), ("FTMO 1-Step", 2859),
            ("FundedNext Stellar 2-Step", 2676), ("FundingPips 2-Step weekly", 2503), ("FTMO 2-Step", 2444),
            ("Apex 50K EOD (futures)", 462), ("HyroTrader 2-Step (BTC)", 479), ("Topstep 50K (futures)", 349),
            ("Breakout 2-Step (BTC)", -102)]
    rows.sort(key=lambda r: -r[1])
    return hbars(rows, lambda v: (f"${v:,.0f}" if v >= 0 else f"&minus;${-v:,.0f}"),
                 "Figure 10.2 &middot; EV per month per account slot, best set-up found for each programme (zero edge, payouts honoured).")

def sizing_v2():
    V, stop, spread = 1.0, 64, 1.4
    cases = [("Phase 1, start", 100000, 100000, 110000), ("Phase 1, near target", 108800, 108800, 110000),
             ("Phase 1, after a bad morning", 95400, 99000, 110000), ("Phase 1, near the floor", 90900, 90900, 110000),
             ("Phase 2, near target", 104000, 104000, 105000), ("Funded, first cycle", 100000, 100000, 101000),
             ("Funded, later cycle", 100000, 100000, 110000)]
    rows = []
    for name, bal, sod, tgt in cases:
        room = bal - 90000; dayroom = 5000 - (sod - bal)
        risk = min(1500, room - 100, dayroom - 200)
        lots = math.floor(risk / (stop * V) * 100) / 100
        cost = (spread + 0.6) * lots * V
        togo = tgt - bal
        target = min(3 * risk, togo + cost + 5)
        tp = target / (lots * V)
        p = stop / (stop + tp)
        rows.append(f'<tr><td>{name}</td><td class="n">${bal:,}</td><td class="n">${room:,}</td><td class="n">${dayroom:,}</td>'
                    f'<td class="n">${risk:,.0f}</td><td class="n">{lots:.2f}</td><td class="n">${cost:,.0f}</td>'
                    f'<td class="n">${target:,.0f}</td><td class="n">{tp:.0f}</td><td class="n">{p*100:.0f}%</td></tr>')
    return ('<table><thead><tr><th>Situation</th><th class="n">Balance</th><th class="n">Room to floor</th><th class="n">Day room</th>'
            '<th class="n">Risk</th><th class="n">Lots</th><th class="n">Cost</th><th class="n">Target $</th>'
            '<th class="n">Target pts</th><th class="n">Win chance</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")

# ------------------------------------------------------------------ assemble
s = open("doc_template.html").read()
i_p1 = s.index("<!-- ================================================================ PART 1 -->")
i_8 = s.index("<!-- 8 -->")
i_p2 = s.index("<!-- ================================================================ PART 2 -->")
i_ap = s.index("<!-- ================================================================ APPENDICES -->")
head, ch1_7, ch8_13, appx = s[:i_p1], s[i_p1:i_8], s[i_8:i_p2], s[i_ap:]

CH = {8: 11, 9: 12, 10: 13, 11: 14, 12: 15, 13: 16, 14: 17, 22: 25}
def remap(txt):
    return re.sub(r"(Chapter|Ch\.)\s+(\d+)\b", lambda m: f"{m.group(1)} {CH.get(int(m.group(2)), int(m.group(2)))}", txt)
def renum_sections(txt):
    # h2 "8.1 ..." -> "11.1 ..." for old chapters 8-13
    return re.sub(r"<h2>(\d+)\.(\d+) ", lambda m: f"<h2>{CH.get(int(m.group(1)), int(m.group(1)))}.{m.group(2)} ", txt)

def rep(txt, a, b):
    assert a in txt, a[:70]
    return txt.replace(a, b)

# --- head: cover, contents, key results
head = rep(head, '<span class="eyebrow">Mathematics and execution &middot; October 2026</span>',
           '<span class="eyebrow">Mathematics and execution &middot; Version 2 &middot; October 2026</span>')
head = rep(head, "exactly how large that value is, and how to run it inside the firm's rules.",
           "exactly how large that value is, how to get it as fast as possible, and how to run it inside the firm's rules.")
head = rep(head, "In the execution plan about three attempts in four lose their full fee",
           "In the execution plan about three attempts in four lose their full fee; after one month the chance of being ahead is about 5%")
toc_old = head[head.index('<ul class="toc">'):head.index("</ul>", head.index('<ul class="toc">')) + 5]
toc_items = [("p", "", "Key results at a glance"), ("p", "I", "Part 1 &middot; The mathematics"),
    ("", "1", "The contract you are buying"), ("", "2", "Probability from zero"),
    ("", "3", "Reaching a target before a floor"), ("", "4", "The challenge, step by step"),
    ("", "5", "What a funded account is worth"), ("", "6", "Putting it together"), ("", "7", "Trading costs"),
    ("", "8", "Time: how long an attempt takes"), ("", "9", "Instruments, leverage and platforms (crypto, futures)"),
    ("", "10", "Maximising expected value per month"), ("", "11", "Other firms and other rule types"),
    ("", "12", "Variance, bankroll and Kelly"), ("", "13", "Hedging"), ("", "14", "Testing on real market data"),
    ("", "15", "Errors in the earlier documents"), ("", "16", "What the mathematics cannot tell you"),
    ("p", "II", "Part 2 &middot; Execution"), ("", "17", "The plan, and why this one"), ("", "18", "Before you start"),
    ("", "19", "The plan on one page"), ("", "20", "Sizing, step by step"), ("", "21", "Stop, target and direction"),
    ("", "22", "Running it: by program or by hand"), ("", "23", "Phases and timeline"),
    ("", "24", "The funded account and payouts"), ("", "25", "Several accounts, other firms and the bankroll"),
    ("", "26", "Records, tax and checks"), ("", "27", "Final checklist"),
    ("p", "A&ndash;C", "Appendices: formula sheet and glossary, every account type modelled, method and sources")]
toc_new = '<ul class="toc">' + "".join(
    f'<li class="{c}"><span class="n">{n}</span><span class="t">{tx}</span></li>' if c else
    f'<li><span class="n">{n}</span><span class="t">{tx}</span></li>' for c, n, tx in toc_items) + "</ul>"
head = head.replace(toc_old, toc_new)
kr_start = head.index("<!-- ================================================================ KEY RESULTS -->")
key_results = open("v2_keyresults.html").read()
head = head[:kr_start] + key_results

# --- chapters 1-7 edits
ch1_7 = rep(ch1_7, "Part 2 reaches the same pass probabilities with 1% trades, more slowly.",
            "Part 2 keeps risk at 1.5% per trade and gets its speed from the instrument and the stop size instead (Chapters 8&ndash;10).")
ch1_7 = rep(ch1_7, '<tr><td>Part 2 plan</td><td class="n">$1,000</td>', '<tr><td>Slow 1% plan (version 1)</td><td class="n">$1,000</td>')
ch1_7 = rep(ch1_7, "<li><strong>Wide stops.</strong> A stop around one day's typical range (about 55&ndash;65 pips on EURUSD in 2024&ndash;26) keeps &kappa; near 1&ndash;1.5%.</li>",
            "<li><strong>Wide stops are cheap but slow.</strong> A stop of about one day's range keeps &kappa; near 1&ndash;1.5% on EURUSD, but each trade then lasts days. Chapter 8 shows how to trade cost against time.</li>")
ch1_7 = remap(ch1_7)

# --- old chapters 8-13 -> 11-16
ch8_13 = rep(ch8_13, "Bootstrap from 6,000 (bold) and 3,000 (Part 2) simulated attempts on real EURUSD data.",
             "Bootstrap from 6,000 (bold) and 3,000 (slow 1% plan) simulated attempts on real EURUSD data. The fast plan of Part 2 is shown month by month in Section 10.7.")
ch8_13 = rep(ch8_13, "<td>Chance of being ahead, Part 2 plan</td>", "<td>Chance of being ahead, slow 1% plan</td>")
ch8_13 = rep(ch8_13, "The Part 2 plan is riskier per attempt", "The slow 1% plan is riskier per attempt")
ch8_13 = rep(ch8_13, "&asymp; <strong>$6,000</strong> (Part 2)", "&asymp; <strong>$6,000</strong> (slow 1% plan)")
ch8_13 = rep(ch8_13, '<tr class="hl"><td>Part 2 plan: 1% risk, 1 : 1, 3,000 attempts</td>', '<tr class="hl"><td>Slow 1% plan (version 1): 1% risk, 1 : 1, 3,000 attempts</td>')
ch8_13 = rep(ch8_13, "The sign and size are confirmed.</p>",
             "The sign and size are confirmed. The fast plan of Part 2 was tested the same way in Section 10.6.</p>")
ch8_13 = rep(ch8_13, "<tr><td>$4,600&ndash;5,000 per month from four accounts.</td><td>The fast version is the prohibited one. The compliant version earns roughly $70 per account-slot per month (Chapter 22).</td><td><span class=\"pill bad\">overstated</span></td></tr>",
             "<tr><td>$4,600&ndash;5,000 per month from four accounts.</td><td>Derived from wrong per-attempt maths with a losing protocol. A corrected fast plan inside the risk guidance (Chapter 10) reaches a similar order, about $2,400 per FTMO slot per month in the zero-edge model, if payouts are honoured.</td><td><span class=\"pill bad\">wrong derivation</span></td></tr>")
ch8_13 = renum_sections(remap(ch8_13))

appx = remap(appx)
appx = rep(appx, '<tr><td>Kelly bankroll for one attempt</td>',
  '<tr><td>Expected trades per phase (1 : k)</td><td>A &times; B &divide; (k &times; L<sup>2</sup>)</td><td>1.5%, 1 : 3: &asymp; 15</td></tr>'
  '<tr><td>Duration of one bracket</td><td>&asymp; k &times; s<sup>2</sup> &divide; &sigma;<sup>2</sup></td><td>s = 0.75&sigma;, 1 : 3: &asymp; 1.7 active hours</td></tr>'
  '<tr><td>Phase time and cost</td><td>&prop; (s &divide; L)<sup>2</sup> and &prop; c &divide; (k L s)</td><td>Chapter 8</td></tr>'
  '<tr><td>Instrument efficiency</td><td>weekly move &divide; round-trip cost</td><td>US100 481, EURUSD 147, BTC 49&ndash;63</td></tr>'
  '<tr><td>Tightest stop from leverage &lambda;</td><td>L &divide; (&lambda; &times; size)</td><td>1.5% at 1:50: 0.03%</td></tr>'
  '<tr><td>EV per month per slot</td><td>EV per attempt &divide; attempt length</td><td>Fast plan &asymp; $2,400</td></tr>'
  '<tr><td>Kelly bankroll for one attempt</td>')

new_p1 = open("v2_new_part1.html").read()
new_p2 = open("v2_part2.html").read()
doc = head + ch1_7 + new_p1 + ch8_13 + new_p2 + appx

fonts = open("fonts_local.css").read()
subs = {"{{FONTS}}": fonts, "{{COVER_SVG}}": cover(), "{{FIG_LINE}}": fig_line(), "{{FIG_TREE}}": fig_tree(),
        "{{FIG_DIST}}": fig_dist(),
        "{{FIG_RULES}}": fig_rules().replace("Figure 8.1", "Figure 11.1"),
        "{{FIG_FIRMS}}": fig_firms().replace("Figure 8.2", "Figure 11.2"),
        "{{FIG_AHEAD}}": fig_ahead().replace("Figure 9.1", "Figure 12.1").replace("Part 2 plan", "Slow 1% plan"),
        "{{AHEAD_BOLD}}": ahead_cells(BK["bold"]["rows"]), "{{AHEAD_COMP}}": ahead_cells(CP["rr1"]["ahead"]),
        "{{FIRM_TABLE}}": firm_table(), "{{FIG_EFF}}": fig_eff(), "{{FIG_STOP}}": fig_stop(),
        "{{FIG_FIRMS_MONTH}}": fig_firms_month(), "{{SIZING_V2}}": sizing_v2()}
for k, v in subs.items():
    assert k in doc, k
    doc = doc.replace(k, v)
assert "{{" not in doc, re.findall(r"\{\{\w+\}\}", doc)
open("prop_firm_option_v2.html", "w").write(doc)

from playwright.sync_api import sync_playwright
footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
          'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v2</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium"
    b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + str(pathlib.Path("prop_firm_option_v2.html").resolve()), wait_until="networkidle")
    pg.wait_for_timeout(800)
    pg.pdf(path="The_Prop_Firm_Option_v2.pdf", format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<div></div>", footer_template=footer)
    b.close()
print("built v2")
