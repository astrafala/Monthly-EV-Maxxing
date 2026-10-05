# Monthly EV Maxxing

A prop-firm evaluation ("challenge") works like an option. You pay a fee. If you pass, you trade a funded account: the firm absorbs the losses and you keep a share of the profits. This repository values that option from first principles and assumes **no trading skill at all**: every trade is a fair bet, so any value comes only from the payoff's shape and the firm's rules. Every number is checked by simulating trades on synthetic and real price paths. The result is a plan that maximises expected value (EV) per month for one person and follows every firm's rules.

## Documents

| File | Contents |
|---|---|
| [`docs/The_Prop_Firm_Option_v8_Mathematics.pdf`](docs/The_Prop_Firm_Option_v8_Mathematics.pdf) | **Current version, 94 pages.** Version 7 corrected after a second detailed review (27 findings), with further errors found and fixed. The expected cash per month for one person first, then every formula derived from first principles (Part I), one chapter per programme with every number worked through at its chosen setting (Part II), the allocation, the portfolio simulation, budget, cost and refusal scenarios (Part III), the execution routine and risks (Part IV), and the corrections, point by point (Appendix A). |
| [`docs/v8_review_response.md`](docs/v8_review_response.md) | The same corrections as Appendix A, as text: each finding of the review of version 7, what was wrong and what version 8 does. |
| [`docs/v7_review_response.md`](docs/v7_review_response.md) | Version 7's response to the review of version 6 (35 points). |
| `docs/archive/` | Versions 1–7, superseded. |
| [`model/rules_snapshot_v8.json`](model/rules_snapshot_v8.json) | The sentences from the firms' own pages behind every rule input, with URLs (read 4 October 2026). |

## Key results (version 8, corrected after the review of version 7, 5 October 2026)

**Expected cash per month for one person, recommended plan, first year: $62,198 ± $2,116** (28 accounts, 1,200 simulated first years, each on its own new price paths; zero predictive skill; every rule the model contains, plus the plan's policies: flat every day by 20:00 UTC, no trade and no day above 40% of a target, at least 10 minutes between trades, no target or stop closer than 0.6 hourly standard deviations, and a last trade with its stop at the floor when an account is nearly spent). Months 2–12 average $70,488; months 13–36 of 36-month lives average $73,157 a month, and the accounts open at month 12 go on to pay $168,447 more. With payouts refused 2% / 5% / 15% of the time by tier: $42,403; at 5% / 10% / 30%: $28,593.

| Portfolio | Accounts | EV/month, first year | Months 2–12 | Tiered refusals | Harsh refusals | First-year cash: median (5th–95th) | Cash low: median / 1 in 20 |
|---|---:|---:|---:|---:|---:|---|---|
| Tier A only | 15 | 25.3K ± 0.9K | 28.8K | 21.3K | 16.5K | 0.28M (0.01M to 0.68M) | 27.5K / 79.0K |
| Tiers A and B | 22 | 41.6K ± 1.4K | 47.0K | 30.7K | 22.4K | 0.48M (0.08M to 1.05M) | 38.4K / 96.4K |
| **Recommended (A + B + one account per tier-D firm)** | 28 | **62.2K ± 2.1K** | 70.5K | 42.4K | 28.6K | 0.71M (0.10M to 1.56M) | 55.5K / 137.0K |
| Recommended, FTMO as 2 × 200K | 26 | 62.2K ± 2.1K | 70.5K | 43.2K | 29.8K | 0.71M (0.10M to 1.56M) | 55.5K / 137.0K |
| Full allowance (each firm at the largest allocation modelled) | 35 | 71.9K ± 2.6K | 81.6K | 41.6K | 26.1K | 0.81M (0.10M to 1.87M) | 66.2K / 167.4K |
| Full allowance + The5ers' small New accounts | 45 | 73.5K ± 2.6K | 83.4K | 42.3K | 25.6K | 0.82M (0.09M to 1.92M) | 67.8K / 167.9K |
| Recommended + futures layer | 53 | 68.2K ± 2.4K | 77.3K | 42.5K | 27.6K | 0.77M (0.09M to 1.78M) | 63.8K / 163.7K |

The recommended plan, account by account (risk / k / m / X = risk per trade and payout target as shares of the account, reward-to-risk, stop in hourly standard deviations; EV per month is each account's long-run rate on sixteen fresh paths):

| Programme | Market | Accounts | Risk / k / m / X | EV/month each | EV/month |
|---|---|---|---|---:|---:|
| FTMO 2-Step | Nasdaq | 4 × 100K | 1.5% / 8 / 0.75 / 20% | 2,512 | 10,049 |
| FundingPips 2-Step Flex (95%) | USDJPY | 4 × 100K | 1.75% / 12 / 1.25 / 20% | 2,479 | 9,917 |
| The5ers High Stakes Classic | Nasdaq | 1 × 100K | 1.5% / 10 / 0.75 / 30% | 3,099 | 3,099 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 100K | 1.75% / 12 / 1.07 / 15% | 2,097 | 2,097 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 50K | 1.75% / 12 / 1.07 / 15% | 936 | 936 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 25K | 1.75% / 12 / 1.07 / 15% | 458 | 458 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 10K | 1.75% / 12 / 1.07 / 15% | 173 | 173 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 5K | 1.75% / 12 / 1.07 / 15% | 71 | 71 |
| FundedNext Stellar 2-Step | EURUSD | 1 × 200K | 1.75% / 12 / 1.25 / 20% | 2,841 | 2,841 |
| Fintokei ProTrader | Nasdaq | 5 × 100K | 1.75% / 10 / 1 / 20% | 2,877 | 14,386 |
| Hola Prime 2-Step Prime (bi-weekly 80%) | gold | 2 × 100K | 1.75% / 6 / 1.03 / 20% | 2,413 | 4,826 |
| Alpha Capital Pro 10% | Nasdaq | 1 × 200K | 1.75% / 12 / 0.75 / 30% | 5,278 | 5,278 |
| FunderPro Classic | Nasdaq | 1 × 200K | 1.75% / 8 / 1.07 / 30% | 5,976 | 5,976 |
| GFT 2-Step Standard | Nasdaq | 1 × 200K | 1.75% / 3.5 / 1.07 / 15% | 3,558 | 3,558 |
| BrightFunded 2-Step Classic | Nasdaq | 1 × 200K | 1.75% / 12 / 1 / 30% | 5,208 | 5,208 |
| Blue Guardian 2-Step | Nasdaq | 1 × 200K | 1.75% / 4 / 1.25 / 15% | 4,469 | 4,469 |
| Maven 2-Step | Nasdaq | 1 × 100K | 1.5% / 3 / 1 / 4.9% | 1,409 | 1,409 |
| **Total** | | **28 accounts** | | | **74,751** |

With a finite starting budget (purchases wait until the cash is there):

| Starting cash | EV/month, first year |
|---|---:|
| $5,000 | 11,327 |
| $10,000 | 17,907 |
| $20,000 | 27,517 |
| $30,000 | 38,757 |
| $50,000 | 52,210 |
| $75,000 | 56,693 |
| $100,000 | 59,009 |
| no limit (same 200 seeds) | 61,227 |

Scenarios (full portfolio runs, paired with the baseline):

| Scenario | EV/month, first year | Difference to baseline |
|---|---:|---:|
| Baseline (same 200 seeds) | $61,227 ± $5,422 |  |
| All trading costs × 1.5 | $52,910 ± $4,996 | −$8,318 ± $2,782 |
| All trading costs × 2 | $44,146 ± $5,073 | −$17,082 ± $2,822 |
| Markets correlated 0.3 (one joint path) | $61,080 ± $5,137 | −$148 ± $7,072 |
| News proxy: flat 12:00–14:00 UTC every weekday | $57,114 ± $5,003 | −$4,113 ± $4,120 |
| FundedNext 1% risk (behavioural remedy) | $60,002 ± $5,454 | −$1,225 ± $401 |
| FundedNext 7-day pause (behavioural remedy) | $60,842 ± $5,454 | −$386 ± $414 |

What changed from version 7 (a second detailed review raised 27 findings; 26 agreed in full, one in part; fixing them and testing the corrected engine found 16 further errors, listed in Appendix A and `docs/v8_review_response.md`). The figure moves from $70,128 to $62,198 a month:

- **Lower.** The daily loss limit is a share of the day's starting balance at FundingPips, The5ers, FXIFY, GFT, Hola Prime, Maven and Alpha Capital (the stricter base at FunderPro); FXIFY Classic returns no fee; Maven needs three profitable days for every payout and the plan keeps Maven's funded profit at or below $4,900 (its 50% rule applies above $5,000); Alpha's first payout needs five trading days; FunderPro Classic has minimum trading days; ten minutes between a close and the next entry; no stop or target closer than 0.6 hourly standard deviations; every trade is decided, and counted, on the day it opens, and a payout no longer restarts the day's caps (versions 7 and 8's first engine let some days exceed the 40% cap and GFT's day cap).
- **Higher.** Hola Prime's 40% rule belongs to on-demand payouts only; Fintokei's and GFT's minimum payouts were overstated; an account near its floor is traded out (a small chance to recover) instead of abandoned.
- **Neither way by construction.** Independent random streams for every stage and market, one-minute sub-steps, futures valued at the path's price, payouts written to the ledger (and to a finite budget) on the day they are paid.
- **Checked.** `tests_v8.py` (14 rule tests, including every day's loss and profit against the firm's limits by each trade's entry day) and `audit_v8.py` (no stalled account in any stage, every chosen setting replayed trade by trade against every rule: 136,727 trades, no violation; chain identities; the document's numbers) all pass.

## Version 7 results (superseded by version 8; see the corrections above)

**Expected cash per month for one person, recommended plan, first year: $70,128 ± $2,427** (28 accounts, 1,200 simulated first years, each on its own new price paths; zero predictive skill; every rule the model contains, plus the plan's policies: flat every day by 20:00 UTC, no trade and no day above 40% of a target, accounts closed before they are traded down to the floor). Months 2–12 average $79,208; the long-run rate (months 13–36 of 36-month lives) is $82,062 a month, and the accounts open at month 12 go on to pay $169,478 more. With payouts refused 2% / 5% / 15% of the time by tier: $47,758; at 5% / 10% / 30%: $32,157.

| Portfolio | Accounts | EV/month, first year | Months 2–12 | Tiered refusals | Harsh refusals | First-year cash: median (5th–95th) | Cash low: median / 1 in 20 |
|---|---:|---:|---:|---:|---:|---|---|
| Tier A only | 15 | 27.7K ± 1.0K | 31.4K | 23.1K | 18.1K | 0.31M (−0.01M to 0.71M) | 30.1K / 86.2K |
| Tiers A and B | 22 | 45.8K ± 1.6K | 51.8K | 34.1K | 25.1K | 0.51M (0.05M to 1.19M) | 43.0K / 115.2K |
| **Recommended (A + B + one account per tier-D firm)** | 28 | **70.1K ± 2.4K** | 79.2K | 47.8K | 32.2K | 0.78M (0.09M to 1.78M) | 56.9K / 156.1K |
| Recommended, FTMO as 2 × 200K | 26 | 70.1K ± 2.4K | 79.2K | 48.5K | 33.8K | 0.78M (0.09M to 1.78M) | 56.9K / 156.1K |
| All firms at full allowance | 35 | 81.3K ± 2.9K | 91.9K | 46.9K | 29.4K | 0.90M (0.11M to 2.06M) | 67.7K / 185.0K |
| Full allowance + The5ers small accounts | 45 | 83.2K ± 2.9K | 94.1K | 47.1K | 28.7K | 0.93M (0.11M to 2.14M) | 69.9K / 188.0K |
| Recommended + futures layer | 53 | 77.0K ± 2.8K | 87.0K | 47.5K | 30.7K | 0.85M (0.06M to 1.97M) | 69.2K / 197.9K |

The recommended plan, account by account (risk / k / m / X = risk per trade and payout target as shares of the account, reward-to-risk, stop in hourly standard deviations; EV per month is each account's long-run rate on sixteen fresh paths):

| Programme | Market | Accounts | Risk / k / m / X | EV/month each | EV/month |
|---|---|---|---|---:|---:|
| FTMO 2-Step | Nasdaq | 4 × 100K | 1.5% / 8 / 0.75 / 20% | 2,930 | 11,722 |
| FundingPips 2-Step Flex (95%) | USDJPY | 4 × 100K | 1.75% / 8 / 1 / 15% | 2,829 | 11,315 |
| The5ers High Stakes Classic | Nasdaq | 1 × 100K | 1.75% / 7 / 1 / 30% | 3,592 | 3,592 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 100K | 1.75% / 6 / 1.07 / 30% | 2,877 | 2,877 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 50K | 1.75% / 6 / 1.07 / 30% | 1,310 | 1,310 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 25K | 1.75% / 6 / 1.07 / 30% | 643 | 643 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 10K | 1.75% / 6 / 1.07 / 30% | 246 | 246 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 1 × 5K | 1.75% / 6 / 1.07 / 30% | 105 | 105 |
| FundedNext Stellar 2-Step | EURUSD | 1 × 200K | 1.75% / 6 / 1 / 20% | 3,265 | 3,265 |
| Fintokei ProTrader | Nasdaq | 5 × 100K | 1.75% / 10 / 1 / 30% | 3,209 | 16,043 |
| Hola Prime 2-Step Prime (bi-weekly 80%) | gold | 2 × 100K | 1.75% / 10 / 1.03 / 20% | 2,813 | 5,627 |
| Alpha Capital Pro 10% | Nasdaq | 1 × 200K | 1.75% / 6 / 1 / 20% | 6,392 | 6,392 |
| FunderPro Classic | Nasdaq | 1 × 200K | 1.75% / 8 / 1.07 / 20% | 6,961 | 6,961 |
| GFT 2-Step Standard | Nasdaq | 1 × 200K | 1.75% / 3 / 1.07 / 10% | 4,035 | 4,035 |
| BrightFunded 2-Step Classic | Nasdaq | 1 × 200K | 1.75% / 6 / 1 / 20% | 5,526 | 5,526 |
| Blue Guardian 2-Step | Nasdaq | 1 × 200K | 1.75% / 4 / 1.07 / 15% | 4,648 | 4,648 |
| Maven 2-Step | Nasdaq | 1 × 100K | 1.75% / 4 / 1.25 / 10% | 1,627 | 1,627 |
| **Total** | | **28 accounts** | | | **85,934** |

With a finite starting budget (purchases wait until the cash is there):

| Starting cash | EV/month, first year |
|---|---:|
| $5,000 | 9,033 |
| $10,000 | 19,888 |
| $20,000 | 28,754 |
| $30,000 | 36,411 |
| $50,000 | 50,158 |
| $75,000 | 55,472 |
| $100,000 | 59,471 |
| no limit (same 200 seeds) | 65,125 |

Scenarios (full portfolio runs, paired with the baseline):

| Scenario | EV/month, first year | Difference to baseline |
|---|---:|---:|
| Baseline (same 200 seeds) | $65,125 ± $5,894 |  |
| All trading costs × 1.5 | $53,418 ± $5,520 | −$11,707 ± $2,725 |
| All trading costs × 2 | $43,877 ± $5,284 | −$21,247 ± $3,234 |
| Markets correlated 0.3 (one joint path) | $72,340 ± $6,483 | +$7,216 ± $9,322 |
| News proxy: flat 12:00–14:00 UTC every weekday | $61,637 ± $5,492 | −$3,488 ± $4,368 |
| FundedNext 1% risk (behavioural remedy) | $63,629 ± $5,905 | −$1,496 ± $512 |
| FundedNext 7-day pause (behavioural remedy) | $64,142 ± $5,900 | −$982 ± $481 |

Versions 5 and 6 are in `docs/archive/` and in the git history.

## What the numbers assume

- **No skill.** Trades are fair bets. The value comes from the fee-versus-payout structure, not from predicting prices.
- **The firm pays as its rules say.** If it might not, see the refusal scenarios above. The value lost depends on how many accounts sit at each firm.
- **Trading costs as modelled.** At 1.5× the costs the recommended plan's first year is worth about 18% less, and at 2× about 33% less (version 7, Part III; paired runs). Measure real spreads and commissions in the first week.
- **Rules as published in October 2026.** Firms change their rules often. Check each programme's rule table (version 7, Part II, with the source URLs) against the firm's current terms before every purchase.
- **The plan's own policies are part of the numbers.** Flat every day by 20:00 UTC, no trade and no day above 40% of a target, the risk caps, margin at most 60% of the balance (FunderPro funded: 20% of the start balance), and closing an account near its floor. Trading differently changes the value and can break a firm's rules.
- **One person, their own accounts, their own money.** Accounts are copied only where a firm allows copying between your own accounts. There is no hedging across accounts and no account in anyone else's name.
- **Large drawdowns are normal.** In the recommended version 7 plan, the cash balance typically falls about $57K (fees paid before payouts arrive) before it recovers; in 1 case in 20 it falls about $156K. With less starting cash the plan buys fewer accounts at once and is worth less in the first year (the budget table above).
- **Private use.** If several people traded the same written rules, the result would be prohibited group trading at several firms.
- **This is research, not financial advice.**

## Layout

```
docs/     the PDF (current) and archived versions
model/    simulation code, results (.json/.jsonl/.log), document sources (.html) and fonts
```

The main pipeline is in `model/`:

| Script | Output | What it does |
|---|---|---|
| `calibrate.py` | | Instrument costs, financing, trading hours; hourly sigma from the price files |
| `multi.py` | | Synthetic zero-edge paths (Brownian-bridge highs and lows, weekends closed) and real-data alignment |
| `acct_mc.py` | | Firm-rule engine: phases, daily and maximum loss, minimum and profitable days, best-day caps, payouts |
| `pathfirm.py` | | Runs the rule engine on a price path, one trade at a time |
| `firms_v3.py`, `firms_v5.py` | | Rule set for every programme modelled; version 5 adds Fintokei, Hola Prime, small The5ers accounts and the reliability tiers |
| `final_v3.py` | `final_v32.json` | Per-firm results: 4 × 6,000 synthetic attempts plus 8,000 on the real path |
| `sens_v32.py` | `sens_v32.json` | How results change with risk, stop, reward:risk, payout cycle and account size |
| `lockstep.py`, `lockstep_portfolio.py` | `lockstep_portfolio_v32.*` | Whole portfolios on one shared path and calendar |
| `weekly_v32.py`, `diary_v32.py`, `milestones_v3.py`, `robust_v32.py` | `*_v32.json` | Week-by-week cash, the sign-up diary, milestones, cost and refusal sensitivity |
| `final_v5.py` | `final_v5.json` | Per-account results for the programmes added in version 5 |
| `lockstep_portfolio_v5.py` | `lockstep_portfolio_v5.*` | Version 5 portfolios by tier, with tiered and harsh refusal scenarios |
| `discount_v5.py`, `instr_v5.py` | `discount_v5.json`, `instr_v5.json` | Value of a fee discount; which market an independent account should trade |
| `build_doc4.py`, `build_doc5.py` | `prop_firm_option_v5.html`, PDF | Build the document (needs Playwright with Chromium); version 5 runs the version 4 build and adds Part 3 |
| `fetch_data.py` | `*_1h.csv` | Downloads the hourly price history (not included; see below) |
| `verify.py` | | Independent check: a pure coin-flip FTMO attempt, written from scratch |
| `optimize_v6.py` | `opt_v6_grid.jsonl`, `opt_v6_refine.jsonl`, `opt_v6_futures.jsonl`, `opt_v6_final.json` | Version 6 search: grid, refine, edges, futures, bold play, the final run inside the plan's limits, the robust re-choice |
| `analytic_v6.py` | | Brownian formulas and the exact trade-level chain (pass probability, trades, expected cost, funded cash), written independently of the engine |
| `verify_v6.py`, `extra_v6.py`, `sens_v6.py`, `timing_v6.py` | `verify_v6.json`, `extra_v6.json`, `sens_v6.json`, `timing_v6.json` | Checks against theory; zero-cost and robustness checks; cost, risk, k, direction and financing sensitivities; time per attempt |
| `lockstep_portfolio_v6.py` | `lockstep_v6.json` | Version 6 portfolios, 400 simulated first years each, with the refusal scenarios |
| `build_math_v6.py`, `doc6_*.py`, `math_v6_*.html`, `katex/` | `prop_firm_math_v6.html`, PDF | Build the version 6 document; formulas typeset with KaTeX (MIT licence, `katex/LICENSE`) |
| `tie_v0/` | | Results of the first version 6 run, before the same-bar tie correction, kept for the record |
| `firms_v7.py` | | Version 7 rule sets: every programme re-read on the firms' pages (URLs in `SOURCES`), plus the plan's policies (daily flat by 20:00 UTC, 40% concentration, closing near the floor) |
| `optimize_v7.py` | `opt_v7_grid.jsonl`, `opt_v7_refine.jsonl`, `opt_v7_futures.jsonl`, `opt_v7_final.json` | Version 7 search on the corrected engine: grid, refine, futures, final run on fresh paths with cluster-robust Student-t intervals |
| `analytic_v7.py` | | The exact trade-level chain of the corrected rules (pass probability, trades, cost, end balance, funded cash, accounting identities), written independently of the engine |
| `verify_v7.py`, `sens_v7.py` | `verify_v7.json`, `verify_v7_ties2.json`, `sens_v7.json` | Engine against the chain on 24 independent paths; same-bar tie convergence; cost, risk, concentration, daily-flat and direction-rule sensitivities |
| `lockstep_portfolio_v7.py` | `lockstep_v7*.json` | Version 7 portfolios: 1,200 first years each, 36-month lives, linearity check, finite budgets, cost stress, correlated markets, news blackout, behaviour scenarios |
| `build_math_v7.py`, `doc7_*.py`, `math_v7_*.html`, `progs_v7.py`, `review_v7.py`, `readme_v7.py` | `prop_firm_math_v7.html`, PDF, `docs/v7_review_response.md` | Build the version 7 document, the corrections appendix and this README's results section |
| `firms_v8.py` | | Version 8 rule sets: every review finding re-read on the firms' pages (quotes in `rules_snapshot_v8.json`); daily-loss bases per firm, Maven's ceiling and 30-day window, Alpha's five trading days, GFT's day cap |
| `acct_mc.py`, `pathfirm.py` (version 8) | | Engine corrections: terminal trade at the floor, 10-minute gap from the exit minute, minimum target distance, calendar fillers, payout clocks from the first trade, futures at the path's price, every trade decided on the day it opens, calendar-day caps across payouts, stall detector |
| `optimize_v8.py` | `opt_v8_grid.jsonl`, `opt_v8_refine.jsonl`, `opt_v8_futures.jsonl`, `opt_v8_final.json` | Version 8 search and the final run on sixteen fresh paths |
| `analytic_v8.py` | | The exact chain with terminal trades, the minimum target distance and Maven's ceiling |
| `verify_v8.py`, `sens_v8.py` | `verify_v8.json`, `verify_v8_ties.json`, `sens_v8.json` | Engine against the chain; one-minute sub-step convergence and error bound; cost, risk, concentration, daily-flat, daily-loss-base and direction-rule sensitivities |
| `lockstep_portfolio_v8.py` | `lockstep_v8*.json` | Version 8 portfolios on independent streams |
| `streams_v8.py`, `tests_v8.py`, `audit_v8.py` | `stream_manifest_v8.json`, `tests_v8.json`, `audit_v8.json` | Random-stream manifest; direct rule tests of the engine; the end-of-run audit (stalls, limits, a trade-by-trade rule replay of every chosen setting, chain identities, portfolio and document checks) |
| `rerun_v8.sh` | `stage_v8_*.done` | The whole pipeline after the grid, resumable stage by stage |
| `build_math_v8.py`, `doc8_*.py`, `math_v8_*.html`, `progs_v8.py`, `review_v8.py`, `readme_v8.py` | `prop_firm_math_v8.html`, PDF, `docs/v8_review_response.md` | Build the version 8 document, its corrections appendix and this README's results section |

The other scripts are earlier versions and checks, kept for the record.

## Reproducing version 8

```bash
cd model
python3 fetch_data.py            # hourly price history (needed for calibration and real-path checks)
python3 optimize_v8.py grid      # grid search (the longest stage; "grid resume" continues an interrupted run)
./rerun_v8.sh                    # rule tests, refine, futures, final, verification, sensitivities, every portfolio stage
python3 audit_v8.py              # end-of-run audit of every output
python3 build_math_v8.py         # writes prop_firm_math_v8.html, the PDF and docs/v8_review_response.md
python3 audit_v8.py doc          # the audit again, with the built document
python3 readme_v8.py             # prints the results section of this README
```

Python 3.11, numpy 2.4 and pandas 3.0 (`environment_v8.json`); the PDF needs Playwright with Chromium.

## Reproducing version 7

```bash
cd model
python3 fetch_data.py            # hourly price history (needed for calibration and real-path checks)
python3 optimize_v7.py grid      # grid search on the corrected engine (the longest stage)
./rerun_v7.sh                    # refine, futures, final, verification, sensitivities, every portfolio stage
python3 build_math_v7.py         # writes prop_firm_math_v7.html, the PDF and docs/v7_review_response.md
python3 readme_v7.py             # prints the results section of this README
```

## Reproducing version 6

```bash
cd model
./rerun_v6.sh                    # grid, refine, edges, futures, bold play, final run (about 25 minutes on 4 cores)
python3 extra_v6.py              # cost robustness of the currency accounts; zero-cost checks
python3 optimize_v6.py robust    # FundedNext EURUSD at the robust stop, on fresh paths 33-36
./downstream_v6.sh               # sensitivities, timing, verification against the exact chain, portfolios
python3 build_math_v6.py         # writes prop_firm_math_v6.html and The_Prop_Firm_Option_v6_Mathematics.pdf
```

## Reproducing version 5

```bash
pip install numpy pandas yfinance playwright pypdf
cd model
python3 fetch_data.py                                   # needed for real-path runs only
python3 final_v3.py best_v32.json final_v32.json
python3 sens_v32.py
python3 lockstep_portfolio.py > lockstep_portfolio_v32.log
python3 weekly_v32.py
python3 diary_v32.py "Full caps, staged start (25 accounts)" diary_staged_v32.json
python3 diary_v32.py "One account per firm (11 firms)" diary_one_v32.json
python3 robust_v32.py
python3 milestones_v3.py
python3 final_v5.py best_v5.json final_v5.json
python3 lockstep_portfolio_v5.py > lockstep_portfolio_v5.log
python3 discount_v5.py
python3 instr_v5.py
python3 build_doc5.py                                   # writes prop_firm_option_v5.html and the PDF
```

Synthetic-path results rebuild exactly without the price files: the hourly sigmas they use are stored in `model/sigma_v32.json`. Set `SIGMA_FROM_DATA=1` to recompute the sigmas from downloaded data instead. Real-path results need the price files. Yahoo Finance serves only about the last 730 days of hourly bars and its terms do not allow republishing them, so the files are not included, and a later download covers a different window and gives slightly different real-path numbers.

The fonts in `model/fonts/` (Archivo, IBM Plex Mono, Source Serif 4) are under the SIL Open Font License 1.1; the licence texts are in that folder.
