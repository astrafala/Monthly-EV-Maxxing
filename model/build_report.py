import json, html, math

R = json.load(open("results.json"))
BK = json.load(open("bankroll.json"))

def money(x, sign=True):
    s = f"{abs(x):,.0f}"
    if x < -0.5: return f"&minus;${s}"
    return (f"+${s}" if sign else f"${s}")

def pct(x): return f"{100*x:.0f}%"

def rules_summary(r):
    parts = []
    for (A, D, typ, dll, cap) in r["phases"]:
        t = {"static": "static", "eod": "EOD trail", "intraday": "intraday trail"}[typ]
        if r["market"] == "CFD":
            s = f"{A/r['size']*100:g}% / {D/r['size']*100:g}% {t}"
        else:
            s = f"${A/1000:g}k / ${D/1000:g}k {t}"
        if cap: s += " + consistency"
        parts.append(s)
    if not parts:
        parts = ["instant (no evaluation)"]
    return " &rarr; ".join(parts)

conf_label = {"high": "high", "med": "medium", "low": "low"}

# ------------------------------------------------------------- EV bar chart (k = 1%)
rows = sorted(R, key=lambda r: -r["k1"]["EV"])
lo, hi = -200.0, 3600.0
def xpct(v): return 100.0 * (v - lo) / (hi - lo)
zero = xpct(0)
bars = []
for r in rows:
    ev = r["k1"]["EV"]
    left = min(zero, xpct(ev)); width = abs(xpct(ev) - zero)
    cls = "pos" if ev >= 0 else "neg"
    dag = "&dagger;" if r["conf"] == "low" else ""
    tip = (f"{r['firm']} {r['prog']}: EV {money(ev)} per attempt at 1% costs; "
           f"P(funded) {pct(r['k1']['P'])}; fee ${r['fee']:,.0f}")
    bars.append(f"""<div class="bar-row" title="{html.escape(tip)}">
  <span class="bar-label">{html.escape(r['firm'])} <span class="muted">{html.escape(r['prog'])}</span>{dag}</span>
  <span class="bar-track"><span class="bar {cls}" style="left:{left:.2f}%;width:{max(width,0.4):.2f}%"></span><span class="zero" style="left:{zero:.2f}%"></span></span>
  <span class="bar-val num">{money(ev)}</span>
</div>""")
ticks = "".join(f'<span class="tick" style="left:{xpct(v):.2f}%">{money(v, sign=False) if v>=0 else money(v)}</span>'
                for v in (0, 1000, 2000, 3000))
bar_chart = f"""<figure class="chart" aria-label="Expected value per attempt by account type">
<figcaption><strong>Expected value per attempt, zero skill, 1% trading costs, payouts honoured.</strong>
Sorted. &dagger; = rule set partly inferred (low confidence).</figcaption>
<div class="bars">{''.join(bars)}
<div class="bar-row axis"><span class="bar-label"></span><span class="bar-track ticks">{ticks}</span><span class="bar-val"></span></div>
</div></figure>"""

# ------------------------------------------------------------- line chart: P(ahead) vs attempts
ns = [1, 3, 5, 10, 20, 50, 100]
series = [("bold", "Corrected bold play", "s1"), ("compliant", "1%-risk swing", "s2"),
          ("pdf", "PDF protocol", "s3")]
W, H = 640, 300; ml, mr, mt, mb = 48, 150, 16, 40
pw, ph = W - ml - mr, H - mt - mb
def X(i): return ml + pw * i / (len(ns) - 1)
def Y(p): return mt + ph * (1 - p)
grid = ""
for p in (0, .25, .5, .75, 1):
    grid += f'<line x1="{ml}" x2="{ml+pw}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" class="grid"/>'
    grid += f'<text x="{ml-8}" y="{Y(p)+4:.1f}" class="axis-t" text-anchor="end">{int(p*100)}%</text>'
for i, n in enumerate(ns):
    grid += f'<text x="{X(i):.1f}" y="{H-mb+18}" class="axis-t" text-anchor="middle">{n}</text>'
grid += f'<text x="{ml+pw/2:.1f}" y="{H-6}" class="axis-t" text-anchor="middle">attempts bought</text>'
lines = ""
end_labels = []
for key, name, cls in series:
    ps = [r[1] for r in BK[key]["rows"]]
    pts = " ".join(f"{X(i):.1f},{Y(p):.1f}" for i, p in enumerate(ps))
    lines += f'<polyline points="{pts}" class="ln {cls}"/>'
    for i, p in enumerate(ps):
        lines += (f'<circle cx="{X(i):.1f}" cy="{Y(p):.1f}" r="4.5" class="pt {cls}">'
                  f'<title>{name}: {pct(p)} chance of being ahead after {ns[i]} attempts</title></circle>')
    end_labels.append([Y(ps[-1]) + 4, name, pct(ps[-1])])
end_labels.sort(key=lambda t: t[0])
for k in range(1, len(end_labels)):
    if end_labels[k][0] - end_labels[k-1][0] < 15:
        end_labels[k][0] = end_labels[k-1][0] + 15
for yv, name, pv in end_labels:
    lines += f'<text x="{X(len(ns)-1)+10:.1f}" y="{yv:.1f}" class="lbl">{name} <tspan class="lblv">{pv}</tspan></text>'
line_chart = f"""<figure class="chart">
<figcaption><strong>Chance of being ahead after buying <em>n</em> FTMO 100K attempts</strong>
(bootstrap of 6,000 simulated attempts per strategy on real EURUSD hourly data).</figcaption>
<div class="legend"><span><i class="sw s1"></i>Corrected bold play</span><span><i class="sw s2"></i>1%-risk swing</span><span><i class="sw s3"></i>PDF protocol</span></div>
<div class="svgwrap"><svg viewBox="0 0 {W} {H}" role="img" aria-label="Probability of cumulative profit by number of attempts">{grid}{lines}</svg></div>
</figure>"""

# ------------------------------------------------------------- big table
trs = []
for r in sorted(R, key=lambda r: (r["market"], -r["k1"]["EV"])):
    fee = f"${r['fee']:,.0f}" + ("/mo" if r["monthly"] else "")
    if r["activation"]: fee += f" + ${r['activation']:,.0f} act."
    ds = r["delta_star"]
    dtxt = "&mdash;" if (ds != ds or ds < 0) else pct(ds)
    trs.append(f"""<tr class="c-{r['conf']}">
<td>{html.escape(r['firm'])}</td><td>{html.escape(r['prog'])}</td>
<td class="num">{fee}</td><td>{rules_summary(r)}</td>
<td class="num">{pct(r['split'])} &times; ${r['D_funded']/1000:g}k</td>
<td class="num">{pct(r['k1']['P'])}</td><td class="num">{money(r['k1']['VF'], sign=False)}</td>
<td class="num">{money(r['k0']['EV'])}</td><td class="num strong">{money(r['k1']['EV'])}</td>
<td class="num">{money(r['c1']['EV'])}</td><td class="num">{r['k1']['EV']/r['fee']:.1f}&times;</td>
<td class="num">{dtxt}</td><td>{conf_label[r['conf']]}</td></tr>""")
big_table = f"""<div class="tablewrap"><table class="data">
<thead><tr><th>Firm</th><th>Account</th><th>Price</th><th>Target / max loss per phase</th>
<th>Funded budget</th><th>P(funded)</th><th>Funded value</th><th>EV frictionless</th>
<th>EV 1% costs</th><th>EV 1%-risk rule</th><th>EV &divide; fee</th><th>Breakeven denial</th><th>Rule data</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>"""

page = open("report_template.html").read()
page = page.replace("{{BAR_CHART}}", bar_chart).replace("{{LINE_CHART}}", line_chart) \
           .replace("{{BIG_TABLE}}", big_table).replace("{{N_ACCOUNTS}}", str(len(R))).replace("{{N_FIRMS}}", str(len({r["firm"] for r in R})))
open("prop-firm-convexity.html", "w").write(page)
print("ok", len(page))
