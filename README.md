# Monthly EV Maxxing

A prop-firm evaluation ("challenge") works like an option. You pay a fee. If you pass, you trade a funded account: the firm absorbs the losses and you keep a share of the profits. This repository values that option from first principles and assumes **no trading skill at all**: every trade is a fair bet, so any value comes only from the payoff's shape and the firm's rules. Every number is checked by simulating trades on synthetic and real price paths. The result is a plan that maximises expected value (EV) per month for one person and follows every firm's rules.

## Documents

| File | Contents |
|---|---|
| [`docs/The_Prop_Firm_Option_v5.pdf`](docs/The_Prop_Firm_Option_v5.pdf) | Current version, 88 pages. Part 1: the mathematics. Chapters 17–23: price-path simulations, every firm compared, the per-person maximum, and a rule audit for each firm. Part 2 (chapters 24–32): the execution plan, a simulated sign-up diary, and month-by-month cash and odds. **Part 3 (chapters 33–36, new in version 5):** firm reliability tiers, payout-refusal scenarios, every rule re-checked (seven corrections), two added firms, and the revised per-person plan. |
| `docs/archive/` | Versions 1–4, superseded. Version 3 overstated some results: The5ers was too high, and it ran several accounts at FXIFY and GFT, which their duplicate-account rules do not allow. Version 4 corrected both. Version 4 assumed every payout is paid at every firm; six of its eleven firms have since had their TrustPilot ratings withheld for fake reviews, and seven of its programmes' rules had changed or were recorded wrongly. |

## Key results (version 5, 4 October 2026)

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
- **Trading costs as modelled.** At 1.5× the costs, value falls 4–11%; at 2×, 12–19%.
- **Rules as published in October 2026.** Firms change their rules often. Check the firm-by-firm sheet (chapter 27) against each firm's current terms before every purchase.
- **One person, their own accounts, their own money.** Accounts are copied only where a firm allows copying between your own accounts. There is no hedging across accounts and no account in anyone else's name.
- **Large drawdowns are normal.** In the recommended version, the cash balance typically falls about 43K before it recovers; in 1 case in 20 it falls about 105K.
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

The other scripts are earlier versions and checks, kept for the record.

## Reproducing

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
