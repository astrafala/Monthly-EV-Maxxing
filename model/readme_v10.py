"""Print the version 10 results section of README.md from the version 10 result files, so the README and the PDF agree:
every figure comes from the same functions the document uses (doc10_*), dollar figures are rounded half away from zero
(doc10_common.usd), and every total is the sum of the figures printed above it (doc10_common.total; review of version 9's
corrections, n26)."""
import html, re
import numpy as np
from doc10_common import *
import doc10_part1 as P1, doc10_part2 as P2, doc10_part3 as P3

def k1(x): return f"{x / 1000:,.1f}K"
def m2(x): return ("−" if x < -5e3 else "") + f"{abs(x) / 1e6:.2f}M"
def plain(x): return html.unescape(re.sub(r"<[^>]+>", "", str(x))).replace("&times;", "×")

def main():
    s = P3.pstats(P3.REC)
    L = P3.LONG.get("R", []) if hasattr(P3, "LONG") else []
    lr = float(np.mean([np.mean(r["monthly"][12:]) for r in L])) if L else None
    out = ["## Key results (version 10, corrected after the review of version 9, 12 October 2026)", "",
           f"**Expected cash per month for one person, recommended plan, first year: {usd(s['ev'])} ± {usd(s['ci'])}** "
           f"({s['acc']} accounts at {s['firms']} firms, {s['n']:,} simulated first years, each on its own new price paths; zero predictive skill; "
           "every rule of the inventory (`model/rules_inventory_v10.json`, every row read on 11–12 October 2026) and the plan's policies: "
           "flat every day by 20:00 UTC and around high-impact releases wherever a firm restricts news, no day above 40% of a target and no "
           "evaluation trade either, at least 10 minutes between trades, no target or stop closer than 0.6 hourly standard deviations, whole lots, payout "
           "requests pending until processed, the firms' payout fees, real filler trades only where a firm counts any opened position and "
           "does not object to them, never 25 days without a trade on an account, and a last trade with its stop at the floor when an account is nearly spent, except at GFT and Alpha "
           f"Capital, where the account is closed instead). Months 2–12 average {usd(s['ss'])}"
           + (f"; months 13–36 of 36-month lives average {usd(lr)} a month" if lr is not None else "") + ". "
           f"With payouts refused 2% / 5% / 15% of the time by tier: {usd(s['tiered'])}; at 5% / 10% / 30%: {usd(s['harsh'])}.", "",
           "| Portfolio | Accounts | EV/month, first year | Months 2–12 | Tiered refusals | Harsh refusals | First-year cash: median (5th–95th) | Cash low: median / 1 in 20 |",
           "|---|---:|---:|---:|---:|---:|---|---|"]
    for p in P3.PNAMES:
        x = P3.pstats(p)
        b = "**" if p == P3.REC else ""
        label = plain(P3.PLABEL.get(p, p)).replace("[[CH_RISK]]", str(P3.CH_RISK) if hasattr(P3, "CH_RISK") else "Part IV")
        out.append(f"| {b}{label}{b} | {x['acc']} | {b}{k1(x['ev'])} ± {k1(x['ci'])}{b} | {k1(x['ss'])} | {k1(x['tiered'])} | {k1(x['harsh'])} | "
                   f"{m2(x['p50'])} ({m2(x['p05'])} to {m2(x['p95'])}) | {k1(-x['tr50'])} / {k1(-x['tr05'])} |")
    out += ["", "The recommended plan, account by account (risk / k / m / X = risk per trade and payout target as shares of the account, "
            "reward-to-risk, stop in hourly standard deviations; EV per month is each account's continuing-slot rate: the average cash per "
            "month in years 2 to 9 of a slot refilled at once, from today's prices, on sixteen new paths):", "",
            "| Programme | Market | Accounts | Risk / k / m / X | EV/month each | EV/month |", "|---|---|---|---|---:|---:|"]
    parts = []; n = 0
    for f in P3.CFD_FIRMS:
        for p, i, sz, c in P2.ALLOC[f]["rec"]:
            r = P2.acct_row(p, i, sz)
            each = r0(r["EV_month"]); parts.append((each, c)); n += c
            out.append(f"| {p} | {MSHORT[i]} | {c} × {kk(sz)} | {plain(P1.sett(r))} | {each:,.0f} | {c * each:,.0f} |")
    out.append(f"| **Total** | | **{n} accounts** | | | **{total(parts):,.0f}** |")
    B = P3.BUDGET.get("R", []) if hasattr(P3, "BUDGET") else []
    if B:
        out += ["", "With a finite starting budget (each purchase paid only from cash already received, in time order):", "",
                "| Starting cash | EV/month, first year |", "|---|---:|"]
        for bud in sorted({r["kw"].get("budget") for r in B if r["kw"].get("budget")}):
            g = [r for r in B if r["kw"].get("budget") == bud]
            out.append(f"| {usd(bud)} | {usd(float(np.mean([np.mean(r['monthly']) for r in g])))} |")
        g = [r for r in B if not r["kw"].get("budget")]
        if g: out.append(f"| no limit (same {len(g)} seeds) | {usd(float(np.mean([np.mean(r['monthly']) for r in g])))} |")
    rows = P3.scen_rows() if hasattr(P3, "scen_rows") else []
    if rows:
        out += ["", "Scenarios (full portfolio runs, paired with the baseline):", "", "| Scenario | EV/month, first year | Difference to baseline |", "|---|---:|---:|"]
        for r in rows:
            out.append("| " + " | ".join(plain(x) for x in r[:3]) + " |")
    return "\n".join(out)

def docs_table(npages=None):
    import review_v10 as RV
    return "\n".join([
        "## Documents", "",
        "| File | Contents |", "|---|---|",
        f"| [`docs/The_Prop_Firm_Option_v10_Mathematics.pdf`](docs/The_Prop_Firm_Option_v10_Mathematics.pdf) | **Current version"
        + (f", {npages} pages" if npages else "") + f".** Version 9 corrected after a fourth detailed review ({len(RV.R)} findings), with "
        f"{len(RV.NEW)} further errors we found ourselves (Appendix A2, which also says why the review found its errors first). The expected "
        "cash per month for one person first, then every formula derived from first principles (Part I), one chapter per programme (Part II), "
        "the allocation, the portfolio simulation, budget, cost and refusal scenarios (Part III), the execution routine and risks (Part IV), "
        "the corrections (Appendices A, A2, A3), every rule the model uses with its source and the date it was read (Appendix B), a formula "
        "sheet and a glossary. |",
        "| [`docs/v10_review_response.md`](docs/v10_review_response.md) | The same corrections as Appendices A and A2, as text. |",
        "| [`model/rules_inventory_v10.json`](model/rules_inventory_v10.json) | Every rule of every programme the plan uses that can change "
        "what the plan may do or what it is paid: the rule as published, its page, the date and basis of the reading, and what the model does "
        "with it (written by `rules_inventory_v10.py`). |",
        "| [`docs/v9_review_response.md`](docs/v9_review_response.md), [`docs/v8_review_response.md`](docs/v8_review_response.md), "
        "[`docs/v7_review_response.md`](docs/v7_review_response.md) | The responses to the reviews of versions 8, 7 and 6. |",
        "| `docs/archive/` | Versions 1&ndash;9, superseded. |"])

def assume():
    """the assumptions, with the version 10 figures (the version 9 README quoted version 7's)"""
    s = P3.pstats(P3.REC)
    b200 = {r["seed"]: float(np.mean(r["monthly"][:12])) for r in P3.lives(P3.REC) if r["seed"] < P3.MAIN0 + 200}
    def cost_pct(c):
        rs = [r for r in STRESS.get("R", []) if r["kw"].get("cost_mult") == c and r["seed"] in b200]
        if not rs: return None
        base = np.mean([b200[r["seed"]] for r in rs]); var = np.mean([np.mean(r["monthly"][:12]) for r in rs])
        return 100.0 * (base - var) / base
    c15, c20 = cost_pct(1.5), cost_pct(2.0)
    costs = (f"At 1.5&times; the costs the recommended plan's first year is worth about {c15:.0f}% less, and at 2&times; about {c20:.0f}% "
             "less (paired portfolio runs, Part III)." if c15 is not None and c20 is not None else "The cost stress of Part III measures what higher costs take.")
    return "\n".join([
        "## What the numbers assume", "",
        "- **No skill.** Trades are fair bets. The value comes from the fee-versus-payout structure, not from predicting prices.",
        "- **The firm pays as its rules say.** If it might not, see the refusal scenarios above. The value lost depends on how many accounts sit at each firm.",
        f"- **Trading costs as modelled.** {costs} Measure real spreads and commissions in the first week.",
        "- **Rules as read on 11&ndash;12 October 2026.** Firms change their rules often. Check each programme's rule table (Part II; every rule's "
        "page and date in Appendix B) against the firm's current terms before every purchase.",
        "- **The plan's own policies are part of the numbers.** Flat every day by 20:00 UTC and around high-impact releases where a firm "
        "restricts news, no day above 40% of a target (and no evaluation trade either), risk at most 1.75% plus cost (FTMO 1%), margin at "
        "most 60% of the balance (FunderPro funded: 20% of the starting balance), a trade on every account at least every 25 days, and "
        "closing an account near its floor (with a last trade to the floor, except at GFT and Alpha Capital, where the account is closed on "
        "request). Trading differently changes the value and can break a firm's rules.",
        "- **One person, their own accounts, their own money.** Accounts trade alike only where a firm allows it between your own accounts "
        "(with FXIFY's approval and The5ers' written confirmation asked first); FundedNext and Hola Prime trade markets no other account "
        "trades. There is no hedging across accounts and no account in anyone else's name.",
        f"- **Large drawdowns are normal.** In the recommended plan the cash balance typically falls about {usd(-s['tr50'])} (fees paid before "
        f"payouts arrive) before it recovers; in 1 case in 20 it falls about {usd(-s['tr05'])}. With less starting cash the plan buys fewer "
        "accounts at once and is worth less in the first year (the budget table above).",
        "- **Private use.** If several people traded the same written rules, the result would be prohibited group trading at several firms.",
        "- **This is research, not financial advice.**"])

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        print(docs_table(int(sys.argv[2]) if len(sys.argv) > 2 else None)); print(); print(main()); print(); print(assume())
    else:
        print(main())
