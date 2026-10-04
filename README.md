# Monthly EV Maxxing

A prop-firm evaluation ("challenge") works like an option. You pay a fee. If you pass, you trade a funded account: the firm absorbs the losses and you keep a share of the profits. This repository values that option from first principles and assumes **no trading skill at all**: every trade is a fair bet, so any value comes only from the payoff's shape and the firm's rules. Every number is checked by simulating trades on synthetic and real price paths. The result is a plan that maximises expected value (EV) per month for one person and follows every firm's rules.

## Documents

| File | Contents |
|---|---|
| [`docs/The_Prop_Firm_Option_v4.pdf`](docs/The_Prop_Firm_Option_v4.pdf) | Current version, 76 pages. Part 1: the mathematics. Chapters 17–23: price-path simulations, every firm compared, the per-person maximum, and a rule audit for each firm. Chapters 24–32: the execution plan, a simulated sign-up diary, and month-by-month cash and odds. |
| `docs/archive/` | Versions 1–3, superseded. Version 3 overstated some results: The5ers was too high, and it ran several accounts at FXIFY and GFT, which their duplicate-account rules do not allow. Version 4 corrects both. |

## Key results (version 4)

The plan:

- **Instrument:** the Nasdaq 100 CFD (US100).
- **Trades:** one position per account. Stop at 0.75 × the hourly sigma, target at 5 × the stop (1:5 reward:risk), risk 1.5% of the account per trade.
- **Direction:** 5-hour momentum. This rule has no edge; it only keeps every account on the same side of the market.
- **Calendar:** entries Monday–Friday, 01:00–20:00 UTC. Flat by 20:30 UTC on Friday. No new trades around news releases.
- **Funded accounts:** payout cycles at +10%.

EV per month for one account slot. The slot buys a new evaluation as soon as the previous attempt ends. Figures are on synthetic zero-edge paths, 24,000 attempts per firm (from `model/final_v32.json`):

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

Per person: every account is run at once on one shared price path and one calendar, with every firm's rules applied, including its limits on duplicate and copied accounts. Results over 200 synthetic lives (from `model/lockstep_portfolio_v32.log`):

| Portfolio | EV/month, months 3–12 | First-year average | Ahead after 1 / 2 / 3 / 6 / 12 months | Lowest cash point (median / 1 in 20) |
|---|---:|---:|---|---|
| FTMO only (4 × 100K) | 17.4K | 15.7K | 21 / 61 / 79 / 89 / 95% | −12.6K / −53.1K |
| One account per firm (11 firms) | 49.1K | 43.8K | 31 / 70 / 90 / 98 / 100% | −21.9K / −47.0K |
| Two per firm where copying is allowed (16) | 71.8K | 64.0K | 32 / 67 / 89 / 98 / 100% | −31.7K / −74.2K |
| Full caps, rules-strict (25) | 113.6K | 101.0K | 30 / 67 / 84 / 97 / 100% | −51.9K / −126.1K |
| Full caps, staged start (25) | 97.6K | 82.4K | 21 / 61 / 70 / 96 / 100% | −21.1K / −91.4K |

## What the numbers assume

- **No skill.** Trades are fair bets. The value comes from the fee-versus-payout structure, not from predicting prices.
- **The firm pays as its rules say.** If each payout has a chance of being refused, value falls: by 10% at a 2% chance, 23% at 5%, 41% at 10% and 64% at 20%.
- **Trading costs as modelled.** At 1.5× the costs, value falls 4–11%; at 2×, 12–19%.
- **Rules as published in October 2026.** Firms change their rules often. Check the firm-by-firm sheet (chapter 27) against each firm's current terms before every purchase.
- **One person, their own accounts, their own money.** Accounts are copied only where a firm allows copying between your own accounts. There is no hedging across accounts and no account in anyone else's name.
- **Large drawdowns are normal.** Even with one account per firm, the cash balance typically falls about 22K before it recovers.
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
| `firms_v3.py` | | Rule set for every programme modelled |
| `final_v3.py` | `final_v32.json` | Per-firm results: 4 × 6,000 synthetic attempts plus 8,000 on the real path |
| `sens_v32.py` | `sens_v32.json` | How results change with risk, stop, reward:risk, payout cycle and account size |
| `lockstep.py`, `lockstep_portfolio.py` | `lockstep_portfolio_v32.*` | Whole portfolios on one shared path and calendar |
| `weekly_v32.py`, `diary_v32.py`, `milestones_v3.py`, `robust_v32.py` | `*_v32.json` | Week-by-week cash, the sign-up diary, milestones, cost and refusal sensitivity |
| `build_doc4.py` | `prop_firm_option_v4.html`, PDF | Builds the document (needs Playwright with Chromium) |
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
python3 build_doc4.py                                   # writes prop_firm_option_v4.html and the PDF
```

Synthetic-path results rebuild exactly without the price files: the hourly sigmas they use are stored in `model/sigma_v32.json`. Set `SIGMA_FROM_DATA=1` to recompute the sigmas from downloaded data instead. Real-path results need the price files. Yahoo Finance serves only about the last 730 days of hourly bars and its terms do not allow republishing them, so the files are not included, and a later download covers a different window and gives slightly different real-path numbers.

The fonts in `model/fonts/` (Archivo, IBM Plex Mono, Source Serif 4) are under the SIL Open Font License 1.1; the licence texts are in that folder.
