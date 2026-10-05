"""Print the version 8 results section of README.md from the version 8 result files (so the README and the PDF agree)."""
import numpy as np, math
from doc8_common import *
import doc8_part1 as P1, doc8_part2 as P2, doc8_part3 as P3

def k1(x): return f"{x / 1000:,.1f}K"
def m2(x): return ("\u2212" if x < -5e3 else "") + f"{abs(x) / 1e6:.2f}M"

def main():
    s = P3.pstats(P3.REC)
    L = LONG.get("R", [])
    lr = np.mean([np.mean(r["monthly"][12:]) for r in L]) if L else None
    o12 = np.mean([r["open12"] for r in L]) if L else None
    out = [f"## Key results (version 8, corrected after the review of version 7, 5 October 2026)", "",
           f"**Expected cash per month for one person, recommended plan, first year: ${s['ev']:,.0f} ± ${s['ci']:,.0f}** "
           f"({s['acc']} accounts, {s['n']:,} simulated first years, each on its own new price paths; zero predictive skill; every rule the model contains, plus the plan's policies: flat every day by 20:00 UTC, "
           f"no trade and no day above 40% of a target, at least 10 minutes between trades, no target or stop closer than 0.6 hourly standard deviations, and a last trade with its stop at the floor when an account is nearly spent). Months 2–12 average ${s['ss']:,.0f}"
           + (f"; months 13–36 of 36-month lives average ${lr:,.0f} a month, and the accounts open at month 12 go on to pay ${o12:,.0f} more" if lr else "") + ". "
           f"With payouts refused 2% / 5% / 15% of the time by tier: ${s['tiered']:,.0f}; at 5% / 10% / 30%: ${s['harsh']:,.0f}.", "",
           "| Portfolio | Accounts | EV/month, first year | Months 2–12 | Tiered refusals | Harsh refusals | First-year cash: median (5th–95th) | Cash low: median / 1 in 20 |",
           "|---|---:|---:|---:|---:|---:|---|---|"]
    for p in P3.PNAMES:
        x = P3.pstats(p)
        bold = "**" if p == P3.REC else ""
        out.append(f"| {bold}{P3.PLABEL.get(p, p).replace('&times;', '×')}{bold} | {x['acc']} | {bold}{k1(x['ev'])} ± {k1(x['ci'])}{bold} | {k1(x['ss'])} | {k1(x['tiered'])} | {k1(x['harsh'])} | "
                   f"{m2(x['p50'])} ({m2(x['p05'])} to {m2(x['p95'])}) | {k1(-x['tr50'])} / {k1(-x['tr05'])} |")
    out += ["", "The recommended plan, account by account (risk / k / m / X = risk per trade and payout target as shares of the account, reward-to-risk, stop in hourly standard deviations; "
            "EV per month is each account's long-run rate on sixteen fresh paths):", "",
            "| Programme | Market | Accounts | Risk / k / m / X | EV/month each | EV/month |", "|---|---|---|---|---:|---:|"]
    tot = 0; n = 0
    for f in P3.CFD_FIRMS:
        for p, i, sz, c in P2.ALLOC[f]["rec"]:
            r = P2.acct_row(p, i, sz); tot += c * r["EV_month"]; n += c
            out.append(f"| {p} | {MSHORT[i]} | {c} × {kk(sz)} | {P1.sett(r).replace('&times;', '×')} | {r['EV_month']:,.0f} | {c * r['EV_month']:,.0f} |")
    out.append(f"| **Total** | | **{n} accounts** | | | **{tot:,.0f}** |")
    B = BUDGET.get("R", [])
    if B:
        out += ["", "With a finite starting budget (purchases wait until the cash is there):", "", "| Starting cash | EV/month, first year |", "|---|---:|"]
        for b in sorted({r["kw"].get("budget") for r in B if r["kw"].get("budget")}):
            g = [r for r in B if r["kw"].get("budget") == b]
            out.append(f"| ${b:,.0f} | {np.mean([np.mean(r['monthly']) for r in g]):,.0f} |")
        g = [r for r in B if not r["kw"].get("budget")]
        if g: out.append(f"| no limit (same {len(g)} seeds) | {np.mean([np.mean(r['monthly']) for r in g]):,.0f} |")
    rows = P3.scen_rows()
    if rows:
        out += ["", "Scenarios (full portfolio runs, paired with the baseline):", "", "| Scenario | EV/month, first year | Difference to baseline |", "|---|---:|---:|"]
        import html, re
        for r in rows:
            out.append("| " + " | ".join(html.unescape(re.sub(r"<[^>]+>", "", str(x))) for x in r[:3]) + " |")
    print("\n".join(out))

if __name__ == "__main__":
    main()
