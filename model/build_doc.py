import json, math, random, html
R = json.load(open("results.json"))
BK = json.load(open("bankroll.json"))
CP = json.load(open("compliant.json"))
S1, S2, S3, NEG = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
INK, MUT, RULE = "#15191f", "#5b6370", "#d5dae2"
FONT = "font-family:Archivo,Arial,sans-serif"
MONO = "font-family:'IBM Plex Mono',monospace"

def money(x, sign=True):
    s = f"{abs(x):,.0f}"
    if x < -0.5: return f"&minus;${s}"
    return f"+${s}" if sign else f"${s}"

def t(x, y, s, size=9, anchor="start", fill=MUT, mono=False, weight=400):
    f = MONO if mono else FONT
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" style="{f}" font-weight="{weight}">{s}</text>'

# ---------------------------------------------------------------- cover: simulated paths
def cover():
    W, H = 600, 210
    rng = random.Random(11)
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    yT, yF, y0 = 20, 190, 105
    out.append(f'<line x1="0" x2="{W}" y1="{yT}" y2="{yT}" stroke="#7fd1b0" stroke-width="1" stroke-dasharray="4 4"/>')
    out.append(f'<line x1="0" x2="{W}" y1="{yF}" y2="{yF}" stroke="#f08a7a" stroke-width="1" stroke-dasharray="4 4"/>')
    out.append(t(W, yT - 6, "target +$10,000", 9, "end", "#9fd8bf", True))
    out.append(t(W, yF + 14, "floor &minus;$10,000", 9, "end", "#f3a497", True))
    for k in range(14):
        x, y = 0.0, 0.0; pts = [(0, y0)]
        while abs(y) < 1 and x < W:
            x += 6; y += rng.choice((-1, 1)) * 0.11
            pts.append((x, y0 - y * (y0 - yT)))
        col = "#7fd1b0" if y >= 1 else ("#f08a7a" if y <= -1 else "#c9d4ea")
        d = " ".join(f"{a:.1f},{min(max(b,yT),yF):.1f}" for a, b in pts)
        out.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-opacity="0.75" stroke-width="1.2"/>')
    out.append(t(4, y0 - 6, "start", 9, "start", "#c9d4ea", True))
    out.append("</svg>")
    return "".join(out)

def fig(svg, cap):
    return f'<figure>{svg}<figcaption>{cap}</figcaption></figure>'

# ---------------------------------------------------------------- P(x) straight line
def fig_line():
    W, H, ml, mr, mt, mb = 600, 220, 54, 20, 14, 36
    pw, ph = W - ml - mr, H - mt - mb
    X = lambda x: ml + pw * (x + 10000) / 20000
    Y = lambda p: mt + ph * (1 - p)
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for p in (0, .25, .5, .75, 1):
        o.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" stroke="{RULE}" stroke-width="0.8"/>')
        o.append(t(ml - 6, Y(p) + 3, f"{int(p*100)}%", 8, "end", MUT, True))
    for x in (-10000, -5000, 0, 5000, 10000):
        lab = "floor" if x == -10000 else ("target" if x == 10000 else (f"{x/1000:+.0f}k".replace("+0k","0")))
        o.append(t(X(x), H - mb + 14, lab, 8, "middle", MUT, True))
    o.append(t(ml + pw / 2, H - 4, "balance relative to start, Phase 1", 8.5, "middle"))
    o.append(f'<line x1="{X(-10000)}" y1="{Y(0)}" x2="{X(10000)}" y2="{Y(1)}" stroke="{S1}" stroke-width="2.2"/>')
    for x, lab in ((-5000, "25%"), (0, "50%"), (5000, "75%"), (-9900, "0.5%")):
        p = (x + 10000) / 20000
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(p):.1f}" r="4" fill="#fff" stroke="{S1}" stroke-width="2"/>')
        o.append(t(X(x) + 7, Y(p) + 12, lab, 8.5, "start", INK, True))
    o.append("</svg>")
    return fig("".join(o), "Figure 3.1 &middot; Chance of passing Phase 1 from each balance. It is a straight line from 0 at the floor to 1 at the target, whatever the sizing.")

# ---------------------------------------------------------------- decision tree
def fig_tree():
    W, H = 620, 270
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    def box(x, y, w, h, title, sub, col=INK, fill="#f1f4f8"):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="{RULE}"/>')
        o.append(t(x + w / 2, y + 15, title, 9, "middle", col, False, 700))
        o.append(t(x + w / 2, y + 28, sub, 8, "middle", MUT, True))
    def arrow(x1, y1, x2, y2, lab, col=MUT):
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1.2"/>')
        o.append(f'<circle cx="{x2}" cy="{y2}" r="2.2" fill="{col}"/>')
        o.append(t((x1 + x2) / 2 + 3, (y1 + y2) / 2 - 3, lab, 7.8, "start", col, True))
    # Phase 1
    box(10, 20, 130, 36, "Phase 1 · $0", "risk 5k / win 10k")
    box(10, 120, 130, 36, "Phase 1 · −$5k", "risk 5k / win 15k")
    box(10, 220, 130, 36, "Fail", "lose fee", NEG, "#fdeeee")
    arrow(75, 56, 75, 120, "2/3 lose", NEG); arrow(75, 156, 75, 220, "3/4 lose", NEG)
    # Phase 2
    box(240, 20, 130, 36, "Phase 2 · $0", "risk 5k / win 5k")
    box(240, 120, 130, 36, "Phase 2 · −$5k", "risk 5k / win 10k")
    box(240, 220, 130, 36, "Fail", "lose fee", NEG, "#fdeeee")
    arrow(140, 38, 240, 38, "1/3 win", S3); arrow(140, 138, 240, 46, "1/4 win", S3)
    arrow(305, 56, 305, 120, "1/2 lose", NEG); arrow(305, 156, 305, 220, "2/3 lose", NEG)
    # Funded
    box(470, 20, 140, 36, "Funded", "worth ≈ $8,600")
    arrow(370, 38, 470, 38, "1/2 win", S3); arrow(370, 138, 470, 46, "1/3 win", S3)
    o.append(t(540, 80, "P(funded)", 8.5, "middle", MUT))
    o.append(t(540, 96, "= ½ × ⅔ = ⅓", 10, "middle", INK, True, 600))
    o.append(t(540, 124, "EV = −$632 + ⅓ × $8,602", 8.5, "middle", MUT, True))
    o.append(t(540, 140, "= +$2,235", 11, "middle", S1, True, 700))
    o.append(t(75, 12, "P(pass) = 1/2", 8.5, "middle", MUT, True))
    o.append(t(305, 12, "P(pass) = 2/3", 8.5, "middle", MUT, True))
    o.append("</svg>")
    return fig("".join(o), "Figure 4.1 &middot; Bold play through both phases. Each trade risks the daily limit and aims exactly at the target.")

# ---------------------------------------------------------------- outcome distribution
def fig_dist():
    rows = [("Lose fee", 68.25, -632, NEG), ("+$400", 10.58, 400, S1), ("+$4,400", 7.05, 4400, S1),
            ("+$8,400", 4.70, 8400, S1), ("+$12,400", 3.13, 12400, S1), ("+$16,400 or more", 6.27, 16400, S1)]
    W, H, ml, mr, mt, mb = 600, 170, 120, 60, 8, 8
    rowh = (H - mt - mb) / len(rows)
    sc = (W - ml - mr) / 70
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for i, (lab, p, v, col) in enumerate(rows):
        y = mt + i * rowh
        o.append(t(ml - 8, y + rowh / 2 + 3, lab, 8.8, "end", INK))
        o.append(f'<rect x="{ml}" y="{y+4:.1f}" width="{p*sc:.1f}" height="{rowh-8:.1f}" rx="2" fill="{col}"/>')
        o.append(t(ml + p * sc + 6, y + rowh / 2 + 3, f"{p:.1f}%", 8.5, "start", INK, True))
    o.append("</svg>")
    return fig("".join(o), "Figure 6.1 &middot; One FTMO 100K attempt under bold play, no costs. The expected value is positive, but the most likely single outcome is losing the fee.")

# ---------------------------------------------------------------- rule impact
def fig_rules():
    rows = [("Static floor", .400), ("EOD trailing, one-day pass allowed", .400), ("EOD trailing + $1,000 daily limit", .400),
            ("EOD trailing + best day ≤ 50%", .327), ("EOD trailing + best day ≤ 40%", .300),
            ("EOD trailing + best day ≤ 30%", .285), ("Intraday trailing (e^−A/D)", .223)]
    W, H, ml, mr, mt, mb = 600, 190, 210, 50, 6, 18
    rowh = (H - mt - mb) / len(rows); sc = (W - ml - mr) / .45
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for i, (lab, p) in enumerate(rows):
        y = mt + i * rowh
        o.append(t(ml - 8, y + rowh / 2 + 3, lab, 8.6, "end", INK))
        o.append(f'<rect x="{ml}" y="{y+4:.1f}" width="{p*sc:.1f}" height="{rowh-8:.1f}" rx="2" fill="{S1 if p>=.4 else S2}"/>')
        o.append(t(ml + p * sc + 6, y + rowh / 2 + 3, f"{p*100:.1f}%", 8.5, "start", INK, True))
    o.append(t(ml, H - 3, "maximum pass probability, $3,000 target, $2,000 drawdown", 8, "start", MUT))
    o.append("</svg>")
    return fig("".join(o), "Figure 8.1 &middot; How each rule type changes the best achievable pass probability (dynamic programming; intraday is the continuous-price bound).")

# ---------------------------------------------------------------- firm EV bars
def fig_firms():
    rows = sorted(R, key=lambda r: -r["k1"]["EV"])
    W = 600; rowh = 11.2; mt = 6; H = mt + rowh * len(rows) + 22
    ml, mr = 230, 56; lo, hi = -200, 3600
    X = lambda v: ml + (W - ml - mr) * (v - lo) / (hi - lo)
    o = [f'<svg viewBox="0 0 {W} {H:.0f}" xmlns="http://www.w3.org/2000/svg">']
    for v in (0, 1000, 2000, 3000):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{mt}" y2="{H-18:.1f}" stroke="{RULE}" stroke-width="0.7"/>')
        o.append(t(X(v), H - 6, money(v, False), 7.5, "middle", MUT, True))
    for i, r in enumerate(rows):
        y = mt + i * rowh; ev = r["k1"]["EV"]
        dag = " †" if r["conf"] == "low" else ""
        o.append(t(ml - 6, y + rowh - 3, f"{html.escape(r['firm'])} · {html.escape(r['prog'])}{dag}", 7.4, "end", INK))
        x0, x1 = sorted((X(0), X(ev)))
        o.append(f'<rect x="{x0:.1f}" y="{y+2:.1f}" width="{max(x1-x0,0.8):.1f}" height="{rowh-3.5:.1f}" fill="{S1 if ev>=0 else NEG}"/>')
        o.append(t(W - 2, y + rowh - 3, money(ev), 7.4, "end", INK, True))
    o.append("</svg>")
    return fig("".join(o), "Figure 8.2 &middot; Expected value per attempt, zero skill, 1% costs, payouts honoured. † rule set partly inferred.")

# ---------------------------------------------------------------- P(ahead)
def fig_ahead():
    ns = [1, 3, 5, 10, 20, 50]
    b = dict((r[0], r[1]) for r in BK["bold"]["rows"])
    c = dict((r[0], r[1]) for r in CP["rr1"]["ahead"])
    W, H, ml, mr, mt, mb = 600, 220, 48, 130, 12, 34
    pw, ph = W - ml - mr, H - mt - mb
    X = lambda i: ml + pw * i / (len(ns) - 1); Y = lambda p: mt + ph * (1 - p)
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for p in (0, .25, .5, .75, 1):
        o.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" stroke="{RULE}" stroke-width="0.8"/>')
        o.append(t(ml - 6, Y(p) + 3, f"{int(p*100)}%", 8, "end", MUT, True))
    for i, n in enumerate(ns):
        o.append(t(X(i), H - mb + 14, str(n), 8, "middle", MUT, True))
    o.append(t(ml + pw / 2, H - 4, "attempts bought", 8.5, "middle"))
    for d, col, name, dy in ((b, S1, "Bold plan", -6), (c, S2, "Part 2 plan", 10)):
        pts = " ".join(f"{X(i):.1f},{Y(d[n]):.1f}" for i, n in enumerate(ns))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
        for i, n in enumerate(ns):
            o.append(f'<circle cx="{X(i):.1f}" cy="{Y(d[n]):.1f}" r="3.5" fill="#fff" stroke="{col}" stroke-width="1.8"/>')
        o.append(t(X(len(ns) - 1) + 8, Y(d[50]) + 3 + dy, f"{name} {d[50]*100:.0f}%", 8.8, "start", INK))
    o.append("</svg>")
    return fig("".join(o), "Figure 9.1 &middot; Chance of being ahead after buying n FTMO 100K attempts (real EURUSD data, bootstrap).")

def ahead_cells(rows):
    d = dict((r[0], r[1]) for r in rows)
    return "".join(f'<td class="n">{d[n]*100:.0f}%</td>' for n in (1, 3, 5, 10, 20, 50))

# ---------------------------------------------------------------- sizing table
def sizing_table():
    stop = 60
    cases = [("Phase 1", 100000, 110000), ("Phase 1", 106200, 110000), ("Phase 1", 109400, 110000),
             ("Phase 1", 91500, 110000), ("Phase 1", 90700, 110000), ("Phase 1", 90180, 110000),
             ("Phase 2", 104550, 105000), ("Funded, first payout", 100000, 100500)]
    rows = []
    for ph, bal, tgt in cases:
        room = bal - 90000
        risk = min(1000, room - 100)
        remaining = tgt - bal
        tg = min(risk, remaining)
        lots = math.floor(risk / (stop * 10) * 100) / 100
        risk_real = lots * stop * 10
        tpips = tg / (lots * 10)
        p = risk_real / (risk_real + tg)
        rows.append(f'<tr><td>{ph}</td><td class="n">${bal:,}</td><td class="n">${room:,}</td><td class="n">${remaining:,}</td>'
                    f'<td class="n">${risk:,.0f}</td><td class="n">{lots:.2f}</td><td class="n">{stop}</td>'
                    f'<td class="n">${tg:,.0f}</td><td class="n">{tpips:.0f}</td><td class="n">{p*100:.0f}%</td></tr>')
    return ('<table><thead><tr><th>Stage</th><th class="n">Balance</th><th class="n">Room above floor</th>'
            '<th class="n">To target</th><th class="n">Risk</th><th class="n">Lots</th><th class="n">Stop pips</th>'
            '<th class="n">Target $</th><th class="n">Target pips</th><th class="n">Win chance</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>")

# ---------------------------------------------------------------- firm table
def rules_summary(r):
    parts = []
    for (A, D, typ, dll, cap) in r["phases"]:
        tt = {"static": "static", "eod": "EOD trail", "intraday": "intraday"}[typ]
        if r["market"] == "CFD": s = f"{A/r['size']*100:g}/{D/r['size']*100:g}% {tt}"
        else: s = f"${A/1000:g}k/${D/1000:g}k {tt}"
        if cap: s += " +cons."
        parts.append(s)
    return " → ".join(parts) if parts else "instant"

def firm_table():
    rows = []
    for r in sorted(R, key=lambda r: (r["market"], -r["k1"]["EV"])):
        fee = f"${r['fee']:,.0f}" + ("/mo" if r["monthly"] else "")
        if r["activation"]: fee += f" +${r['activation']:,.0f}"
        dag = " †" if r["conf"] == "low" else ""
        rows.append(f'<tr><td>{html.escape(r["firm"])}{dag}</td><td>{html.escape(r["prog"])}</td><td class="n">{fee}</td>'
                    f'<td>{rules_summary(r)}</td><td class="n">{r["split"]*100:.0f}% × ${r["D_funded"]/1000:g}k</td>'
                    f'<td class="n">{r["k1"]["P"]*100:.0f}%</td><td class="n">{money(r["k1"]["VF"], False)}</td>'
                    f'<td class="n">{money(r["k1"]["EV"])}</td><td class="n">{money(r["c1"]["EV"])}</td></tr>')
    return ('<table class="small" style="table-layout:fixed"><colgroup><col style="width:15%"><col style="width:15%"><col style="width:10%"><col style="width:21%"><col style="width:10%"><col style="width:7%"><col style="width:8%"><col style="width:7%"><col style="width:7%"></colgroup><thead><tr><th>Firm</th><th>Account</th><th class="n">Price</th><th>Target / max loss</th>'
            '<th class="n">Funded</th><th class="n">P(fund.)</th><th class="n">Value</th><th class="n">EV</th>'
            '<th class="n">1% risk</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")

doc = open("doc_template.html").read()
fonts = open("fonts_local.css").read()
subs = {"{{FONTS}}": fonts, "{{COVER_SVG}}": cover(), "{{FIG_LINE}}": fig_line(), "{{FIG_TREE}}": fig_tree(),
        "{{FIG_DIST}}": fig_dist(), "{{FIG_RULES}}": fig_rules(), "{{FIG_FIRMS}}": fig_firms(),
        "{{FIG_AHEAD}}": fig_ahead(), "{{AHEAD_BOLD}}": ahead_cells(BK["bold"]["rows"]),
        "{{AHEAD_COMP}}": ahead_cells(CP["rr1"]["ahead"]), "{{SIZING_TABLE}}": sizing_table(),
        "{{FIRM_TABLE}}": firm_table()}
for k, v in subs.items():
    assert k in doc, k
    doc = doc.replace(k, v)
assert "{{" not in doc
open("prop_firm_option.html", "w").write(doc)

from playwright.sync_api import sync_playwright
import pathlib
footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
          'display:flex;justify-content:space-between"><span>The Prop Firm Option</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium"
    b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + str(pathlib.Path("prop_firm_option.html").resolve()), wait_until="networkidle")
    pg.wait_for_timeout(800)
    pg.pdf(path="The_Prop_Firm_Option.pdf", format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<div></div>", footer_template=footer)
    b.close()
print("built")
