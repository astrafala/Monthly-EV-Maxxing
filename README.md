# Monthly EV Maxxing

A prop-firm evaluation ("challenge") works like an option. You pay a fee. If you pass, you trade a funded account: the firm absorbs the losses and you keep a share of the profits. This repository values that option from first principles and assumes **no trading skill at all**: every trade is a fair bet, so any value comes only from the payoff's shape and the firm's rules. Every number is checked by simulating trades on synthetic and real price paths. The result is a plan that maximises expected value (EV) per month for one person and follows every firm's rules.

## Documents

| File | Contents |
|---|---|
| [`docs/The_Prop_Firm_Option_v7_Mathematics.pdf`](docs/The_Prop_Firm_Option_v7_Mathematics.pdf) | **Current version, 89 pages.** Version 6 corrected after a 35-point review, with 11 further errors found and fixed. The expected cash per month for one person first, then every formula derived from first principles (Part I), one chapter per programme with every number worked through at its chosen setting (Part II), the allocation, the portfolio simulation, budget, cost and refusal scenarios (Part III), the execution routine and risks (Part IV), and the corrections, point by point (Appendix A). |
| [`docs/v7_review_response.md`](docs/v7_review_response.md) | The same corrections as Appendix A, as text: each review point, what was wrong and what version 7 does. |
| `docs/archive/` | Versions 1–6, superseded. Version 5 (88 pages) holds the sign-up diary and the firm-by-firm rule audit; version 6 (98 pages) is the version the review checked. |

## Key results (version 7, corrected after review, 4 October 2026)

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

What changed from version 6:

- **The review was right on almost every point.** All 35 points were checked against the code, the data and the firms' pages: 34 agreed, one in part. Appendix A of the PDF and [`docs/v7_review_response.md`](docs/v7_review_response.md) give each one with what was wrong and what changed.
- **Eleven further errors found and fixed** (N1–N11 in Appendix A). The largest: version 6's FunderPro setting broke the firm's funded margin limit (20% of the starting balance), and GFT's $3,000 daily profit cap is flat, not scaled with size. The engine also overwrote the target cap in one funded branch, counted weekend days as trading days, could place an extra trade after a win that closed the gap to the target by a rounding error, and did not check FXIFY's and Hola Prime's best-day rules at the payout request. Maven's consistency rules were missing.
- **The strategy is more conservative, so the value is lower.** No trade and no day may make more than 40% of a target (several firms forbid passing with one or a few trades, so bold play is gone); every position is closed by 20:00 UTC, so the account is flat at every firm's daily reset; an account is closed near its floor instead of being traded in micro size; risk is sized net of cost and margin is checked at every entry; FTMO risk stays at or below its own 1.5% guidance. These policies cost value but make the plan executable as written. Together with the rule corrections they explain why the figure is lower than version 6's $138,412; they interact, so the new figure is a new measurement, not version 6's minus a list.
- **Cleaner statistics.** Every figure is re-measured on price paths no earlier stage used. Intervals are cluster-robust with Student's t, because attempts on one path share its history. The engine is checked against the exact chain on 24 independent paths. The first-year average, the long-run rate and the value of accounts still open after a year are reported separately.

## Version 6 results (superseded by version 7; see the corrections above)


**Expected cash per month for one person, recommended plan: $138,400 ± $4,900** (first-year average, 400 simulated years; 28 accounts at 13 firms, zero predictive skill, every written rule followed). From the second month on the average is $151,600 a month. If payouts are refused 2% / 5% / 15% of the time by tier, it is $93,700; at 5% / 10% / 30%, $64,500.

| Portfolio | Accounts | EV/month, first year | Tiered refusals | Harsh refusals | First-year cash: median (5th–95th) | Cash low: median / 1 in 20 |
|---|---:|---:|---:|---:|---|---|
| Tier A only | 15 | 63.4K ± 2.7K | 52.2K | 39.9K | 0.71M (0.30–1.40M) | 36K / 93K |
| Tiers A and B | 22 | 95.6K ± 3.7K | 70.8K | 52.0K | 1.11M (0.47–1.97M) | 47K / 111K |
| **Recommended (A + B + one account per tier-D firm)** | **28** | **138.4K ± 4.9K** | **93.7K** | **64.5K** | 1.55M (0.86–2.75M) | 59K / 136K |
| Recommended, FTMO as 2 × 200K | 26 | 138.4K ± 4.8K | 95.9K | 68.3K | 1.55M (0.84–2.75M) | 59K / 136K |
| All firms at full allowance | 35 | 163.2K ± 6.0K | 96.7K | 63.0K | 1.85M (0.93–3.21M) | 75K / 176K |
| Full allowance + The5ers small accounts | 45 | 169.6K ± 5.9K | 98.8K | 63.3K | 1.93M (1.04–3.42M) | 76K / 179K |
| Recommended + futures (Topstep 5, Apex 20) | 53 | 151.7K ± 5.6K | 94.6K | 62.8K | 1.71M (0.87–3.05M) | 71K / 155K |

The recommended plan, account by account (k / m / X = reward-to-risk, stop in hourly standard deviations, funded cycle target as a share of the account; EV per month from fresh paths not used to choose the setting):

| Programme | Market | Accounts | k / m / X | EV/month each | EV/month |
|---|---|---|---|---:|---:|
| FTMO 2-Step | Nasdaq | 4 × 100K | 20 / 0.5 / 30% | 5,463 | 21,852 |
| FundingPips 2-Step Flex (85%), single trades capped at 55% of the phase target | USDJPY | 4 × 100K | 20 / 0.5 / 25% | 5,716 | 22,866 |
| The5ers High Stakes Classic | Nasdaq | 1 × 100K | 20 / 0.5 / 25% | 4,775 | 4,775 |
| FXIFY Two Phase Classic (100%, 30 days) | Nasdaq | 100K + 50K + 25K + 10K + 5K | 12 / 1 / 30% | 4,046 (100K) | 7,096 |
| FundedNext Stellar 2-Step | EURUSD | 1 × 200K | 20 / 1 / 25% | 7,679 | 7,679 |
| Fintokei ProTrader | Nasdaq | 5 × 100K | 12 / 0.5 / 25% | 4,072 | 20,361 |
| Hola Prime 2-Step Prime | gold | 2 × 100K | 10 / 1 / 20% | 4,578 | 9,156 |
| Alpha Capital Pro 10% | Nasdaq | 1 × 200K | 30 / 0.5 / 30% | 12,757 | 12,757 |
| FunderPro Classic | Nasdaq | 1 × 200K | 30 / 0.35 / 30% | 15,903 | 15,903 |
| GFT 2-Step Standard | Nasdaq | 1 × 200K | 8 / 0.75 / 8% | 7,591 | 7,591 |
| BrightFunded 2-Step Classic | Nasdaq | 1 × 100K | 12 / 0.5 / 25% | 4,183 | 4,183 |
| Blue Guardian 2-Step | Nasdaq | 1 × 100K | 8 / 1 / 18% | 2,810 | 2,810 |
| Maven 2-Step | Nasdaq | 1 × 100K | 7 / 1 / 8% | 2,341 | 2,341 |
| **Total** | | **28 accounts** | | | **139,369** |

What changed from version 5:

- **Every setting optimised.** Each programme was searched over reward-to-risk, stop, funded cycle target and market: 4,950 grid settings, then about 1,300 refined ones. The optimum moves toward *bold play* (Dubins–Savage): a large k, so that one win reaches the target, the tightest stop the leverage allows, and cycles of 20–30%. The plan stops at a stop of 0.35, a cycle of 30% and k = 30, for reasons the model cannot price: spread widening against tight stops, and the review risk of very large single payouts.
- **More allocation.** FXIFY allows one active account of each size, so the plan adds 50K, 25K, 10K and 5K Classic accounts. Fintokei's €500,000 limit fits a fifth 100K account. FundedNext moves to one 200K account, which is cheaper per dollar.
- **An exact check.** `model/analytic_v6.py` solves the trade-level Markov chain exactly for any k. The pass probability is exactly (B − expected total cost)/(A + B). It agrees with the engine on every programme to within what the chain leaves out (financing, gaps, calendar).
- **An engine bias found and fixed.** When a stop and a target were both touched within one hourly bar, the engine decided the order with the trade's overall fair chance. For narrow brackets this gave about +0.03 R per trade. The engine now replays the bar's five-minute sub-steps; everything was re-run on the corrected engine.
- **Robust choices.** FundedNext on EURUSD uses a stop of 1.0 instead of the searched 0.75. That costs about $600 a month at the assumed cost but keeps the account valuable if costs are twice the assumption.

## Version 5 results (superseded by version 6)


### Firm reliability changes the plan

Six of the eleven firms in the version 4 plan now show "This company's rating is unavailable due to a breach of our guidelines" and "We've removed a number of fake reviews for this company" on TrustPilot: Alpha Capital, BrightFunded, Blue Guardian, FunderPro, Maven and Goat Funded Trader (GFT). PropFirmMap grades all six D. Version 5 sorts firms into tiers:

- **Tier A** (A or A+, clean TrustPilot record): FTMO, The5ers, FundingPips, FundedNext, FXIFY, and Topstep (futures).
- **Tier B** (B+): Hola Prime and Fintokei (both new), and Apex (futures).
- **Tier D**: the six flagged firms.

Version 5 also adds two payout-refusal scenarios. In both, the first refused payout ends that firm:

- **Tiered:** each payout is refused with probability 2% (tier A), 5% (B) or 15% (D).
- **Harsh:** 5% (A), 10% (B) or 30% (D).

Per person, steady month (months 3–12). Results are from 200 synthetic lives per version (`model/lockstep_portfolio_v5.log`):

| Version | Accounts | All paid | Tiered refusals | Harsh refusals | Cash low (median / 1 in 20) |
|---|---:|---:|---:|---:|---|
| Tier A only | 11 | 51.4K | 37.6K | 24.9K | −22.8K / −63.0K |
| Tier A + B (adds Fintokei 4, Hola Prime 2) | 17 | 72.4K | 47.6K | 30.7K | −33.4K / −81.1K |
| **Recommended: A + B + one account at each tier-D firm** | **23** | **95.7K** | **58.2K** | **35.6K** | −42.6K / −104.9K |
| All tiers at full caps | 31 | 122.8K | 58.7K | 35.0K | −59.1K / −146.9K |
| Tier A + B + futures (Topstep 5, Apex 20 at 90% off) | 42 | 92.4K | 50.7K | 31.6K | −46.0K / −111.9K |
| Version 4 full caps, as published | 25 | 113.6K | 52.4K | 32.1K | −51.9K / −126.1K |
| Version 4 full caps, rules corrected | 25 | 103.3K | 49.1K | 29.4K | −50.4K / −127.5K |

Under refusal risk, spreading accounts across many firms beats stacking them at a few firms: each payout request is another chance to lose the whole firm. The refusal probabilities are judgements, not measurements. No firm publishes how often it refuses payouts.

### Every rule re-checked

Version 5 re-checked every firm's current rules, using the firm's own help pages where possible. Seven programmes had changed, or had been recorded wrongly in version 4. EV per month per 100K account (synthetic):

| Programme | What changed | Version 4 | Version 5 |
|---|---|---:|---:|
| FXIFY | Now Two Phase Classic: 5% then 10%, 4% daily loss, 4 minimum days, $549; on funded accounts no day may exceed 25% of the payout's profit | 4,894 | 3,025 |
| FundingPips Flex | No fee refund on Flex. Since 26 Aug 2026 the 95% option needs 3 profitable days per evaluation phase, so use the 85% option | 6,123 | 5,522 |
| FundedNext Stellar 2-Step (gold) | 15% challenge reward only after Scale-Up; 21-day cycles | 4,316 | 3,490 |
| GFT 2-Step Standard | 8% / 5% targets, 3 minimum days | 3,625 | 3,725 |
| FunderPro Classic | Phase 2 target is 5%, not 8% | 4,222 | 5,020 |
| BrightFunded 2-Step Classic | Fee refunded only with a paid add-on | 3,328 | 3,160 |
| Blue Guardian 2-Step | $579 list, 3 profitable days per phase, refund after the 4th payout | 4,071 | 2,858 |

FTMO, The5ers, Alpha Capital and Maven were re-checked and are unchanged.

New programmes, EV per month per account (synthetic; `model/final_v5.json`):

| Programme | EV per month |
|---|---:|
| Fintokei ProTrader 100K | 3,500 |
| Hola Prime 2-Step Prime 100K, bi-weekly 80%, on USDJPY | 4,130 |
| The5ers High Stakes 25K / 10K / 5K / 2.5K | 790 / 320 / 160 / 70 |
| Topstep 50K | 960 |
| Apex 50K EOD at 90% off | 550 |

Hola Prime prohibits copying trades from other prop firms, so its accounts trade USDJPY, independently of the Nasdaq accounts. Each 10% fee discount adds 2–5% to an account's value (`model/discount_v5.json`).

### The trade (unchanged since version 4)

The plan:

- **Instrument:** the Nasdaq 100 CFD (US100).
- **Trades:** one position per account. Stop at 0.75 × the hourly sigma, target at 5 × the stop (1:5 reward:risk), risk 1.5% of the account per trade.
- **Direction:** 5-hour momentum. This rule has no edge; it only keeps every account on the same side of the market.
- **Calendar:** entries Monday–Friday, 01:00–20:00 UTC. Flat by 20:30 UTC on Friday. No new trades around news releases.
- **Funded accounts:** payout cycles at +10%.

EV per month for one account slot, version 4 firms. The slot buys a new evaluation as soon as the previous attempt ends. Figures are on synthetic zero-edge paths, 24,000 attempts per firm (from `model/final_v32.json`):

| Programme (100K) | EV / month | | Programme (100K) | EV / month |
|---|---:|---|---|---:|
| FundingPips 2-Step Flex (95%) | 6,123 | | FTMO 2-Step | 4,229 (real path 4,322) |
| FundingPips 2-Step (on-demand 90%) | 5,697 | | FunderPro Classic | 4,222 |
| FundingPips 2-Step Flex (85%) | 5,542 | | Blue Guardian 2-Step | 4,071 |
| FundingPips 2-Step (bi-weekly 80%) | 4,996 | | The5ers High Stakes | 3,737 |
| FXIFY Two-Phase | 4,894 | | GFT 2-Step Standard | 3,625 |
| FundedNext Stellar 2-Step | 4,680 | | BrightFunded 2-Step Classic | 3,328 |
| Alpha Capital Pro 10% | 4,514 | | Maven 2-Step | 2,371 |

Futures firms are much weaker on the same paths (Topstep 957, Lucid 373, Tradeify 274, Apex −1,072 per month).

Version 4 per-person results, every payout assumed paid. Every account is run at once on one shared price path and one calendar, with every firm's rules applied, including its limits on duplicate and copied accounts. Results over 200 synthetic lives (from `model/lockstep_portfolio_v32.log`):

| Portfolio | EV/month, months 3–12 | First-year average | Ahead after 1 / 2 / 3 / 6 / 12 months | Lowest cash point (median / 1 in 20) |
|---|---:|---:|---|---|
| FTMO only (4 × 100K) | 17.4K | 15.7K | 21 / 61 / 79 / 89 / 95% | −12.6K / −53.1K |
| One account per firm (11 firms) | 49.1K | 43.8K | 31 / 70 / 90 / 98 / 100% | −21.9K / −47.0K |
| Two per firm where copying is allowed (16) | 71.8K | 64.0K | 32 / 67 / 89 / 98 / 100% | −31.7K / −74.2K |
| Full caps, rules-strict (25) | 113.6K | 101.0K | 30 / 67 / 84 / 97 / 100% | −51.9K / −126.1K |
| Full caps, staged start (25) | 97.6K | 82.4K | 21 / 61 / 70 / 96 / 100% | −21.1K / −91.4K |

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

The other scripts are earlier versions and checks, kept for the record.

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
