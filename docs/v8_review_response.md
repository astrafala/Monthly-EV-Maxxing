# Version 8: response to the review of version 7

Every finding of the review (4 October 2026) checked against the firms' own pages (model/rules_snapshot_v8.json quotes them) and against the code, and what version 8 does about it. The PDF's Appendix A holds the same table.

## 1. Being flat at the reset does not turn a share of the day's balance into a share of the initial balance (agreed)

**Wrong in version 7.** Version 7 applied every daily loss limit as a fixed share of the initial balance, except Fintokei's. FundingPips (4% of the higher of the day's opening balance and equity), The5ers (5% of the previous day's higher closing balance or equity: the firm's own example is $5,500 at $110,000), FXIFY (4% of the previous day's balance), GFT (5% subtracted from the higher of balance and equity), Hola Prime (5% of the previous day's closing balance), Maven (4% of the higher of equity and balance: 4% of $1,100 in its example) and Alpha Capital (5% of the day's starting balance) all take the share of the day's level. Response 5's claim that flattening alone made the engine's limit the firm's was false for them. Section 6.2 also described FundingPips' base as the initial balance and its reset as Prague time; Blue Guardian was described as 'of the higher', where its rule subtracts a fixed 4% of the initial balance from the higher reset level.

**Version 8.** Every programme now carries its base (acct_mc._dll_at): 'rel' (a share of the day's starting balance) for the seven firms above and Fintokei; 'fixed' for FTMO, FundedNext, BrightFunded and Blue Guardian; FunderPro, whose pages say only 'balance-based', takes the stricter of the two at every reset. The allowance is recomputed at every reset; tests_v8.py checks the FundingPips example ($94,000 start: $3,760). Section 6.2's table gives each base and reset time from the firms' pages. Measured on paths 141–144 (one 100K account, a month): FundingPips 2-Step Flex (80%) $2,231 with its own base against $2,270 with a fixed one; FundingPips 2-Step Flex (80%) $1,324 with its own base against $1,306 with a fixed one; FundingPips 2-Step Flex (95%) $2,629 with its own base against $2,692 with a fixed one; FundingPips 2-Step Flex (95%) $1,478 with its own base against $1,610 with a fixed one; The5ers HS $2,540 with its own base against $2,547 with a fixed one; The5ers HS Classic $2,791 with its own base against $2,775 with a fixed one; FXIFY Classic (100%, 30 days) $2,140 with its own base against $1,973 with a fixed one; FXIFY Classic (100%, 30 days) $2,241 with its own base against $2,319 with a fixed one; FXIFY Classic (80%) $1,650 with its own base against $1,718 with a fixed one; FXIFY Classic (80%) $1,666 with its own base against $1,513 with a fixed one; Fintokei ProTrader $2,810 with its own base against $2,475 with a fixed one; Hola Prime 2-Step Prime $2,129 with its own base against $2,075 with a fixed one; Hola Prime 2-Step Prime $1,308 with its own base against $1,416 with a fixed one; Alpha Capital Pro 10% $2,517 with its own base against $2,407 with a fixed one; GFT Standard $2,199 with its own base against $2,316 with a fixed one; GFT Standard $2,013 with its own base against $1,955 with a fixed one; FunderPro Classic $2,671 with its own base against $2,543 with a fixed one; FunderPro Classic $2,457 with its own base against $2,449 with a fixed one; Maven 2-Step $1,371 with its own base against $1,423 with a fixed one.

## 2. FXIFY Classic was given a fee refund (agreed)

**Wrong in version 7.** FXIFY's account-type comparison lists Classic as 'No Refund' and its September 2026 refund guide names Two Phase Standard, One Phase and Three Phase as the refunded programmes. Version 7 paid $549 back with the first payout of every Classic account.

**Version 8.** No refund on Classic at any size (firms_v8). The minimum payout of $50 is added. The search, the final run and the portfolios were all rerun with it.

## 3. Fintokei ProTrader carried SwiftTrader's payout minimum and a profit threshold on its trading days (agreed)

**Wrong in version 7.** The 3% minimum belongs to SwiftTrader; ProTrader's minimum is $100. ProTrader needs 3 separate trading days (a trade opened on the day, any result) per phase and before each payout, not 3 days of +0.5%. Section 6.4 presented the stricter reading as the firm's rule.

**Version 8.** 3 trading days per phase and per payout cycle (fillers allowed, as Fintokei counts any opened trade), minimum payout $100, payouts 14 days after the first trade or the last payout. A $100 minimum is a flat amount, so the 200K account is a scaled copy of the 100K only where the minimum does not bind; in the scaling test of Chapter 11 it never did (finding 17).

## 4. The5ers' Classic and New allowances (agreed in part)

**Wrong in version 7.** The engine already valued every small account under the New programme's contract (10% / 5%, New's fees) and the allocation (three each of 2.5K, 5K and 10K, one 25K, plus the plan's single 100K) fits New's limits and the shared large-account limit. The text, however, called them scaled Classic accounts and did not say which programme each slot belonged to.

**Version 8.** Every small slot is labelled New High Stakes, with New's fee and targets; the one 50K/100K slot allowed across both programmes is the plan's 100K account. Classic's own small slots (one 2.5K, one 5K, one 10K or 25K) are left out because their fees could not be read on the firm's pages; the full-allowance value is therefore a value of this allocation, not a maximum.

## 5. Maven's consistency rule was misattributed and its funded-day requirement omitted (agreed)

**Wrong in version 7.** The FAQ requires three profitable days of at least 0.5% in the funded phase before a withdrawal, which version 7 left out. The 20% rule is the consistency score of Maven's instant accounts. Above $5,000 of profit the best 'day' or single trade may not exceed 50% of the cycle's profit, where a 'day' is a run of trades with less than 24 hours between a close and the next opening: under daily trading a whole week is one such day. Response N6 said the 50% rule was absent.

**Version 8.** Funded payouts need 3 profitable days (+0.5%); the 20% rule is removed; the plan never lets a Maven funded account's profit exceed $4,900, $100 under the threshold so that a take-profit filled a few points better than its price cannot bring the rule in (payout targets of 2–4.9% of 100K searched, wins capped at the distance to $4,900), so the 50% rule never applies. tests_v8.py checks every trade of 400 attempts against the ceiling.

## 6. Maven's overflow rule cannot be met at the payout request (agreed)

**Wrong in version 7.** The $10,000 per rolling 30 days is counted on the date profit is closed and the excess is voided. Waiting at the request cannot restore voided profit.

**Version 8.** The engine keeps a ledger of closed trades and never places a trade whose full win could take the closed profit of any 30-day window containing it above $10,000 (read as net profit before the split, the stricter reading). The check uses the largest suffix sum of the last 30 days, because a window's total rises when an old loss leaves it; a first version that checked only the current window failed the rule test and was corrected (n8 below).

## 7. Alpha Capital's first bi-weekly payout had no qualification gates (agreed)

**Wrong in version 7.** Alpha's first bi-weekly request needs 14 days from the first trade on the funded account, five trading days with the same strategy (a trade opened and closed on the day; minimal-lot fillers are not allowed) and $100 of profit. Version 7 had only a 14-day wait from funding. Its source list pointed to the on-demand policy.

**Version 8.** All three gates are in the engine; until the account has five trading days it places at most one trade a day and keeps trading past its cycle target. tests_v8.py checks that no first payout comes before five distinct trading days. The source is the bi-weekly page.

## 8. Two-minute fillers do not establish the duration rules for the strategy (agreed)

**Wrong in version 7.** Alpha's duration rule concerns the average trade, the majority of trades and the share of profit from trades over 2 minutes; Blue Guardian states a 2-minute minimum holding time for all trades. A bracket can reach a close target within 2 minutes; version 7 gave no evidence about the strategy's own trades.

**Version 8.** Version 8 places no target and no stop closer than 0.6 hourly standard deviations to the entry, so even a trade at that distance is touched within 2 minutes with probability below 1 in 1,000; with one-minute sub-steps the engine records every trade's duration. Over every chosen programme: 362 of 20,955,242 trades (0.002%) may have closed within 2 minutes (the most in one programme: 0.007%, The5ers HS Classic); the shortest programme average is 102 minutes, and at most 0.005% of any programme's gross profit came from such trades. Where the plan's own target would have been closer, the target is set at the minimum distance and the account may finish slightly above its target.

## 9. Hola Prime's on-demand consistency rule was applied to the bi-weekly option (agreed)

**Wrong in version 7.** The 40% consistency score belongs to on-demand payouts; the bi-weekly option needs three profitable days in 14. Version 7 applied 40% as a payout gate and called it a compliance fix.

**Version 8.** The 40% rule is removed from the bi-weekly programme; its three profitable days (+0.5%) stay. The plan's own 40% concentration policy still caps every trade and day.

## 10. An entry at the next hour's open is not ten minutes after a close (agreed)

**Wrong in version 7.** A close at 12:59 followed by an entry at 13:00 broke the stated 10-minute rule, and Hola Prime groups any re-entry within 10 minutes, profitable or not.

**Version 8.** With one-minute sub-steps the engine knows each exit's minute; an exit after minute 50 delays the next entry by one more hour. tests_v8.py measures the shortest gap between an exit and the next entry: 10382 consecutive trades: shortest time from an exit to the next entry 10 minutes. The routine waits 10 minutes after any close, at every firm.

## 11. Payout clocks and minimum amounts were not specified per firm (agreed)

**Wrong in version 7.** FTMO counts the first 14 days from the first trade, FundingPips likewise (and has a 1% minimum reward), Alpha needs its gates, Blue Guardian has a $100 crypto minimum; version 7's engine counted from funding and left most minimums out.

**Version 8.** Every funded account's first payout date now counts from its first trade (for the firms that state it; for the others this is at most hours later than funding, a slightly conservative choice), and each firm's minimum is in its rules: FundingPips 1%, FXIFY $50, Fintokei, GFT, FunderPro, Blue Guardian and Alpha $100, The5ers $150. Each programme's table in Part II lists clock origin, cycle, eligible days and minimum.

## 12. Stopping an account does not free its allocation (agreed)

**Wrong in version 7.** Version 7 stopped trading an account near its floor and bought a replacement at once, although the old account was not breached and could still count against a per-person cap (FTMO's $400,000, FXIFY's one account per size). Its text was also inconsistent about whether accounts were abandoned.

**Version 8.** An account whose room above the floor is below a real trade now trades the rest: one last bracket with its stop at the floor itself (whole contracts on futures). It either recovers or ends in a breach, which closes the account and frees the allocation, with no request to the firm needed. The text, the engine and the chain use this one rule. tests_v8.py checks that every failed attempt ends exactly at the floor.

## 13. The 40% cap does not give three winning days before every payout (agreed)

**Wrong in version 7.** It does so for reaching a fixed target. A payout taken on its date before the target can rest on one winning day.

**Version 8.** The claim is withdrawn for payouts; it stays for phases. Where a firm requires profitable days per payout (FundingPips 95%, GFT, Hola Prime, Maven, Blue Guardian in the stricter reading), they are rules of that programme in the engine.

## 14. Seed offsets collided across stages and markets (agreed)

**Wrong in version 7.** Paths were seeded with their number alone and other markets used offsets: gold's refine paths reused the random numbers of yen's grid paths, gold's final paths those of yen's refine and euro's grid paths, and inside the portfolio a life's yen path was another life's Nasdaq path.

**Version 8.** Every path is drawn from its own numpy SeedSequence stream, keyed by path number, market group, length, sub-steps per hour and correlation. streams_v8.py lists every stream of every stage and checks that independent stages share none (8,501 streams over 8 stages, no clash); the only shared streams are the paired designs it names. Everything was rerun.

## 15. Independent maxima and minima are not an exact Brownian bridge (agreed)

**Wrong in version 7.** Version 7 called the sub-step extremes exact marginals (true) but drew the maximum and minimum independently, which misstates the chance that one sub-step reaches both levels; its effect was not bounded.

**Version 8.** The joint law differs from the product of the marginals only through events where one sub-step's path spans a whole bracket, whose probability is at most e^{-W^2/v} for a bracket of width W and sub-step variance v. Version 8 uses one-minute sub-steps and stops of at least 0.6 sd, so this is at most e^{-60 m^2} < 5\times10^{-10} per minute of a trade; the engine adds the bound up over every trade: at most 1.9e-48 per trade over every chosen programme's final run, i.e. no trade's outcome probabilities differ from an exact bridge by more than that. Section 3.3 now says the construction is exact up to that bound.

## 16. The tie tests did not bound the bias at 0.25 percentage points (agreed)

**Wrong in version 7.** Two of version 7's own cells were +0.32 and +0.29 points at z = 2.3, so the stated bound did not follow, and averaging cells of opposite sign bounds nothing.

**Version 8.** The claim is withdrawn. Version 8 tests convergence at the tightest stop the plan allows (0.6 sd) with 12, 60 and 240 sub-steps per hour on six independent paths per cell, and reports each cell with its interval (Chapter 11): k = 1: -0.09 ± 0.28, -0.08 ± 0.35, +0.04 ± 0.28 points at 12/60/240; k = 2: -0.02 ± 0.87, +0.01 ± 0.52, -0.09 ± 0.40 points at 12/60/240; k = 3: -0.34 ± 0.51, -0.06 ± 0.79, -0.16 ± 0.55 points at 12/60/240; k = 6: -0.01 ± 0.27, -0.24 ± 0.66, -0.03 ± 0.56 points at 12/60/240. The bound of finding 15 is the guarantee for the settings used.

## 17. The exact Fintokei scaling claim contradicted the fee table (agreed)

**Wrong in version 7.** The test set the 200K fee to twice the 100K fee, so it tested that the trading rules scale, not the real contracts ($1,249 against 2 × $549).

**Version 8.** Chapter 11 runs the test twice and labels each: with the fee doubled (the rules) and with the firm's real 200K fee (the contracts). The scaling test, twice. Rules: with the 200K fee set to twice the 100K fee, a 200K attempt equals twice the matching 100K attempt, path by path, for FTMO, The5ers, Fintokei (largest difference $0.00 over 4,500 pairs). GFT is not exact, because its $3,000 day cap and $10,000 payout cap are flat amounts: $1,394 per 100K at 200K against $1,515 at 100K. Contracts: with the firms' real 200K fees, FTMO $1,845 per 100K at 200K against $1,845 at 100K (fee $1,215.65 against 2 × $607.82); Fintokei $1,454 per 100K at 200K against $1,519 at 100K (fee $1,249.00 against 2 × $549.00); GFT $1,424 per 100K at 200K against $1,515 at 100K (fee $974.00 against 2 × $524.00) (The5ers sells no 200K account of this programme, so its 200K row checks the rules only.) The fee difference is the whole of the gap where the rules scale; [[CH_ALLOC]].2 values it.

## 18. Worked examples and minimum-stop prose conflicted with the policy (agreed)

**Wrong in version 7.** FXIFY's funded example showed a $10,500 win where its 25% best-day rule caps it at $7,500; Maven's showed w = \$2{,}000 against l = \$1{,}750, below its own 1:1.5 minimum; the FunderPro and GFT sheets kept a 0.92 sd minimum stop that is correct only at 1.5% risk (at 1.75%, 1:30 and a 20% cap, or 1:10 and 60%, it is 1.066).

**Version 8.** Every worked trade is now computed with every cap the engine applies (concentration, best day, day cap, ceiling, minimum target distance) and with Maven's risk lowered to w/1.5; minimum stops in the rule sheets are computed from the chosen risk, leverage and cap.

## 19. 7/5 calendar days per missing day is not a weekday calendar (agreed)

**Wrong in version 7.** Version 7 added 1.4 calendar days per missing filler day, an average.

**Version 8.** Filler days are found on the path's own calendar (the next days with a permitted entry hour not yet traded). tests_v8.py: a target reached on a Friday gets its two fillers on Monday and Tuesday. The routine places each filler with a stop of at most $3 per $100K, so at most five fillers cannot lose the $20 margin.

## 20. The fixed-hours news test is a sensitivity, not a bound (agreed)

**Wrong in version 7.** Blacking out 12:00–14:00 UTC does not contain every restricted release, and removing trading time has no proven monotone effect on cash per month.

**Version 8.** It is now called a stylised news-hours sensitivity. The headline is a model without a news calendar; the routine uses the firms' real calendars, which the model does not reproduce.

## 21. The calendar model does not give i.i.d. renewals, and months 13&ndash;36 are not an asymptotic rate (agreed)

**Wrong in version 7.** An attempt's start state includes the weekday, the hour, credits and rolling windows, so attempts are not independent and identically distributed; and the 36-month average is a finite-window estimate.

**Version 8.** Section 8.3 now rests the ratio on a Markov renewal argument: the attempt sequence is driven by a finite-state calendar chain plus independent price increments, and the long-run rate is the ratio of the stationary means, which the engine estimates by running attempts back to back on long paths. The months 13–36 figure is labelled as that window's average, and the two annual windows are compared with a paired interval: months 13–24 minus 25–36 +$747 ± $3,911 a month over 800 lives.

## 22. The standalone comparison changes the direction policy; linearity does not predict equality (agreed)

**Wrong in version 7.** Run alone, a firm's account takes its own direction where in the portfolio it copies another account's, so the two runs are different policies; and four synchronised 100K accounts are not smoother than two 200K accounts.

**Version 8.** The check is presented as a policy comparison on the same paths, with its measured difference and no appeal to linearity; the smoothing claim is removed (four 100K and two 200K FTMO accounts give the same cash in the model).

## 23. The general withdrawal identity needs a term for forfeited profit (agreed)

**Wrong in version 7.** With profit removed from the account without being paid (a day-cap deduction, voided overflow), \mathbb{E}[W] = -\mathbb{E}[X_\text{end}] - \mathbb{E}[K] - \mathbb{E}[Q].

**Version 8.** Section 7.1 states the identity with Q, and why Q = 0 under the plan: wins are capped below GFT's day cap and inside Maven's windows, and no position is open through a gap.

## 24. Smaller statements without their conditions (agreed)

**Wrong in version 7.** Wald's identity as stated lacked the i.i.d. or martingale-difference condition (the review's counterexample has mean-zero steps and a stopped mean of 1/2); equal long and short counts do not make drift irrelevant; a $1 minimum win can pass the target; a $20 buffer alone bounds no filler loss; the refusal formula needs Poisson requests.

**Version 8.** Each is restated with its condition: Wald for i.i.d. integrable steps, or for steps whose conditional mean given the past is fixed, with \mathbb{E}[\tau] < \infty and bounded conditional absolute means; zero drift as a modelling assumption, with direction chosen symmetrically; the minimum win now allows a small overshoot that the chain and the engine both count; fillers with stops of at most $3; the Poisson assumption stated at the formula, with the deterministic-schedule form next to it.

## 25. The futures conversion is valid only at the reference price (agreed)

**Wrong in version 7.** Version 7 valued one micro contract at 31,070 index points throughout, although the normalised path moves; at a path level of 125 a contract risks a quarter more.

**Version 8.** Every entry converts the path's price to the index level, 31,070 × price / 100, before rounding to whole contracts (pathfirm.contract_value); the smallest trade is one contract at that price. tests_v8.py checks the scaling.

## 26. Audit and reproducibility claims exceeded the materials (agreed)

**Wrong in version 7.** The review had the PDF and the response but no repository, no environment, no stream manifest and no dated rule snapshots; some sources were bare domains or secondary summaries.

**Version 8.** The code, the results and the document sources are in the repository (github.com/astrafala/Monthly-EV-Maxxing); environment_v8.json gives the versions, stream_manifest_v8.json every stream, rules_snapshot_v8.json the quoted sentences behind every rule input with its URL and date, and tests_v8.json the rule tests. Appendix E lists exact pages; where only secondary sources were available (FunderPro's number of minimum days) it says so.

## 27. Remaining text contradictions (agreed)

**Wrong in version 7.** Fintokei's and Alpha's sheets said 1.5% risk where the plan uses 1.75%; Apex's engine row said 'at most 50%' where the rule is strictly less; the FTMO caption pointed to a table without its chosen 1.5% setting; 'all firms at full allowance' was used for two different portfolios.

**Version 8.** Each is corrected; the two portfolios are named 'full allowance' and 'full allowance plus The5ers' small New accounts' everywhere.

## Further errors found while fixing the review's findings

- **n1. FunderPro Classic has minimum trading days.** Version 7 modelled none. FunderPro sells a 'No Minimum Trading Days' add-on for Classic only, so Classic has a default minimum; review sites give 4 per phase, which version 8 uses (the official pages read do not state the number). Its minimum reward of $100 is added.
- **n2. GFT's 3% minimum belongs to on-demand rewards.** Version 7 required 3% of profit for every GFT payout; the 3% is the first on-demand reward's condition. The bi-weekly minimum is $100.
- **n3. Blue Guardian's payout days.** Blue Guardian's payout requirements include completing 'the minimum trading days requirement'. Version 7 had no funded-day rule; version 8 takes the stricter reading, 3 profitable days (+0.5%) per payout.
- **n4. Trading days were counted on the wrong day.** A trade requested in the evening but opened after the night counted toward the day of the request in version 7; days now count on the day the trade opens.
- **n5. Hourly and sub-step extremes in different precision.** Version 7 stored sub-step extremes in single precision and hourly ones in double, so a level at the edge could be inside the hour and outside every sub-step; both are double now.
- **n6. The tie fallback used the entry's geometry.** When a stop and a target fall inside one sub-step, the engine draws the winner with the trade's overall chance l/(l+w), which is not the conditional chance from the sub-step's position. With one-minute sub-steps such sub-steps are covered by the bound of finding 15.
- **n7. Worked examples left out the funded best-day cap.** Beyond the two the review named, every programme's trade example now applies all funded caps the engine applies and the minimum target distance.
- **n8. A rolling cap checked on the current window only.** Found by tests_v8.py in version 8's own first implementation of Maven's overflow rule: a window's net profit grows when an old loss leaves it, so checking the current window at entry let later windows exceed $10,000. The check now covers every window that will contain the trade.
- **n9. A cap below the minimum target distance stopped an account for ever.** Found during version 8's own grid search: when a rule cap was smaller than the smallest allowed win at full risk (the plan's 40% of a 4% GFT payout target at the tightest USDJPY stop; Maven's small payout targets and its ceiling while profitable days were still missing), the first version 8 engine never traded and the account waited indefinitely (7 GFT settings and every Maven setting gave attempts of thousands of days). The engine now lowers the risk until the cap is a full minimum-distance win when nothing has been made that day, the chain does the same, the affected settings were rerun, and a stall detector, which ends and counts any account that can do nothing for 120 days, reads zero in every reported run.
- **n10. Maven: the fix for n9 still left ways to wait for ever.** Found by the stall detector after the fix for n9, in four steps. (a) The refine stage extended the search past the top of each payout-target grid; for Maven that proposed a $10,000 target, above the plan's own ceiling. Maven's grid already ends at the ceiling and is no longer extended. (b) The smaller trade of n9 was allowed only when the cap was at least half the minimum-distance win, an arbitrary limit: at a $2,000 payout target the plan's 40% daily cap is $800, below half the minimum win at a 1.75% risk and a 0.6 sd stop, and 65 of 300 accounts at that setting waited for ever. The only limit now is the market's smallest position (one futures contract; none for CFDs), in the engine and in the chain alike. (c) The room kept under the ceiling for the profitable days still needed was one day short once today had already counted, and a day that opened with a loss and was then cut by the ceiling ended below the $500 of a profitable day, so one account in 2,000 reached the ceiling a profitable day short and could never be paid. The reserve is now exact: a win that makes today a profitable day keeps 1.1 x $500 for each day still needed after today; a win that does not also keeps it for today, and is cut or waits for tomorrow. (d) An interim version raised a win to complete the day's amount without raising its risk; near the floor that gave take-profits thousands of times the stop distance, and it was removed. Every Maven setting was searched again (336 settings, 2,000 attempts each, no stall), and tests_v8.py now replays the account of (c) on its own path and seed.
- **n11. Futures: no trade when one contract risked more than the planned risk.** Found by the stall detector in the final validation. On a twelve-year synthetic path the Nasdaq rose 5.7-fold, and one micro contract at the planned stop then risked up to $969 against the plan's $600; the engine allowed neither fewer than one contract nor more than the planned risk, so funded Apex accounts on that path stopped trading (9 of 24,000 attempts). The plan now trades one contract when the rooms allow it, which is what whole-contract sizing does. The evaluation engine's loop limit, which had ended a few Topstep attempts silently as failures (all caused by n12), now counts as a stall too, and none occurs.
- **n12. Trades decided after the daily cut-off were booked to the wrong day.** Found while tracing n11; versions 7 and 8's first engine alike. When the engine decided a trade after the 19:00 UTC cut-off, on a weekend or before a closure, the trade waited for the next open but its result was booked to the day it was decided; the next day's loss allowance and profit caps then started again from zero, after that trade. Between 9% and 22% of trades were affected, depending on the programme: the plan's 40% day cap was exceeded on such days, and a day's realized loss could in principle exceed a firm's daily limit. Every trade is now decided on the day it opens, with that day's limits (the engine moves to the next entry before deciding), in the single-account engine and in the portfolio simulation alike. All of version 8's searches and simulations were run again with the corrected engine.
- **n13. A payout reset the day's profit, and FXIFY's check had a dollar of slack.** Found by the new daily-limits test; versions 7 and 8's first engine alike. The funded engine kept one figure for the day's profit and set it to zero at every payout, because the next cycle's profitable days must not count profit made before the request. But the day caps are calendar-day limits: after a payout requested mid-day, GFT's $3,000 cap and the plan's 40% cap restarted, and one GFT day made $3,900. The engine now keeps two figures, the calendar day's profit (for every day cap and best-day measure, never reset by a payout) and the part since the payout (for counting the cycle's profitable days). FXIFY's best-day check at a request tolerated a best day up to 25 cents per $100K above the 25% limit; it is now exact, and the plan keeps each FXIFY day $1 per $100K under the limit. tests_v8.py checks every day's loss against the firm's allowance and every day's profit against the caps, days taken from each trade's own entry time, and every FXIFY payout against its best day.
- **n14. The chain comparison could stall at Maven's ceiling.** Found by the stall counts of the verification stage. The engine run that is compared with the chain (Chapter 11) pays only at the payout target, as the chain does; a Maven trade closed at a fair price within $1 of the ceiling left no room for the smallest win and no payout, and 4 of 12,000 attempts waited for ever (a first fix covered only the last 50 cents and left one). In that comparison the band is now the target, as in the chain; the plan's own engine, which pays whatever profit there is on the payout date, was not affected.
- **n15. Maven's ceiling had no margin.** Found by the end-of-run audit (audit_v8.py), which replays every chosen setting trade by trade: Maven accounts reached exactly $5,000 of profit. That is within the rule (it applies above $5,000), but a take-profit filled a few points better than its price, which brokers allow, would take the account over and bring in the 50% rule, which a cycle traded daily cannot meet. The plan now keeps Maven's profit at or below $4,900 and searches payout targets up to 4.9%. The audit also shows days that end exactly at GFT's $3,000 cap and 30-day windows exactly at Maven's $10,000: there a better fill costs only the cents above the cap, which are deducted or voided, so those caps keep no margin.
- **n16. Portfolio payouts were recorded when an account ended.** Found by the stall counts of the portfolio simulation; version 7's portfolio engine alike. The portfolio engine wrote an account's payouts to the ledger only when the account ended, with their dates. The dates were right, but (a) a finite budget received the cash only when the account ended, so the budget scenarios made purchases wait for money that had already arrived, and (b) an account still open at the end of a life had to be traded on, on the wrapped price path, until it ended: a funded Topstep account, whose floor locks at the start after the first payout, could run to the loop limit (10 accounts in 8,400 lives, counted as stalls; nothing after the horizon entered a figure). Payouts are now written, and reach the budget, on the day they are paid, and accounts are no longer simulated a month after the end of a life; every portfolio stage was run again.
