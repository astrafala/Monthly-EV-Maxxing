"""
Version 10 rule inventory: every rule of every programme the plan uses that can change what the plan may do or what it
is paid, with its source and how the model treats it (python3 rules_inventory_v10.py writes rules_inventory_v10.json).
Version 9 listed the rules it modelled; this inventory starts from the firms' rules instead, so that a rule the model leaves
out has to appear here with a reason (the review of version 9 found rules that no list contained: The5ers' payout cap and
profit gate, the payout locks, Topstep's request session, Apex's pending requests).

status:  modelled     the engine applies the rule as stated
         plan         the plan avoids the situation the rule governs (the engine applies the plan's own, stricter rule)
         cautious     the rule's wording leaves a question; the engine applies the stricter reading, named here
         assumption   no published figure: the engine uses the value named here
         not binding  the rule exists but the plan's settings cannot reach it (the reason is given)
basis:   page         the firm's own help centre, FAQ or rules page, read directly
         snippet      the firm's own page as returned by a search engine (the page itself refused automated reading)
         secondary    a reviewer's or comparison site's description, used only where no firm page could be read
Read: 11-12 October 2026 (every row; the first version 10 inventory had carried over version 9's readings of 4 October 2026).
"""
import json

R = []
def r(firm, area, rule, model, status, source, basis="page", read="11 Oct 2026"):
    R.append(dict(firm=firm, area=area, rule=rule, model=model, status=status, source=source, basis=basis, read=read))

# the plan's own policies against the firms' undefined or judgement-based prohibitions (gambling, overexposure and the like)
PLANB = "the plan's policies: no day above 40% of a target and no evaluation trade above 40% of its phase target, risk at most 1.75% plus cost (FTMO 1%), margin at most 60%, every account traded the same way, no account sacrificed; the firm's judgement is not modelled"

# ---------------------------------------------------------------- FTMO 2-Step (FTMO Account, Standard)
U = "https://ftmo.com/en/"
r("FTMO", "targets and limits", "Phase 1 10%, phase 2 5%; maximum daily loss 5% and maximum loss 10% of the initial balance; "
  "4 trading days per phase (a day on which a position is opened)", "as stated", "modelled", U + "trading-objectives/", read="4 Oct 2026")
r("FTMO", "news (funded)", "FTMO Account (Standard): no order opened or closed, stop-loss and take-profit hits included, from 2 "
  "minutes before to 2 minutes after selected releases on the targeted instruments (US indices, XAUUSD, USD pairs ...); "
  "evaluations free", "flat in every hourly bar overlapping 10 minutes either side of a high-impact release (news_v10), "
  "funded stage only", "plan", U + "faq/can-i-trade-news/")
r("FTMO", "weekends (funded)", "FTMO Account (Standard): positions closed before the weekend close and before breaks over two hours",
  "flat every day at 20:00 UTC", "plan", U + "faq/can-i-hold-positions-overnight-or-over-the-weekend/")
r("FTMO", "payouts", "First reward on the 14th day after the first trade or later, then bi-weekly; all positions and pending "
  "orders closed; review within 1-2 business days, sent 1-2 business days after the invoice is approved; minimum $20 closed "
  "profit (wire); 80% split; fee refunded with the first reward", "request at least 14 days after the first funded trade, "
  "flat; pending 2 working days (a breach before then cancels it: the page does not say trading continues safely), cash 2 "
  "working days later; the $20 minimum applied to the trader's share (version 10: version 9 had no minimum)", "cautious",
  U + "faq/how-do-i-withdraw-my-profits/")
r("FTMO", "trading during processing", "not stated", "allowed; a breach before processing cancels the payout", "cautious",
  U + "faq/how-do-i-withdraw-my-profits/")
r("FTMO", "allocation", "no limit on the number of Challenge and Verification accounts; once verified, at most $400,000 of "
  "simulated funds (before scaling) per trader or strategy at any time in active FTMO Rewards Accounts traded the same way",
  "four 100K slots, each holding one account (evaluation or funded) at a time: the cap is never exceeded, and the plan does "
  "not run further Challenges in parallel (FTMO prohibits 'account rolling', 'overexposure' and 'one-sided bets' without "
  "defining them; whether a passed Challenge may wait for a free place is not published)", "cautious",
  "https://ftmo.oanda.com/faq/how-many-accounts-can-i-have/", read="12 Oct 2026 (version 9 read 'evaluations included': wrong)")
r("FTMO", "risk guidance", "FTMO recommends 1-1.5% risk per trade and monitors larger risk as possible gambling",
  "risk per trade at most 1.5% at FTMO (L_MAX)", "plan", "https://ftmo.com/en/blog/how-much-should-you-risk-on-one-trade/", read="4 Oct 2026")
r("FTMO", "scaling", "+25% every 4 months with 10% profit and 2 processed rewards in 4 months", "not modelled (the model "
  "keeps the purchased size, which forgoes any gain from scaling)", "not binding", U + "reward-growth-and-scaling-plan/")
r("FTMO", "inactivity", "the CFD pages read state none; FTMO's futures rules close an account after 30 days without trading",
  "the plan never leaves an account 25 days without a trade", "plan", "https://ftmo.com/en/futures/forbidden-trading-practices/", basis="snippet")

# ---------------------------------------------------------------- FundingPips 2-Step Flex
U = "https://help.fundingpips.com/hc/en-us/articles/"
r("FundingPips", "targets and limits", "10% / 8%; daily loss 4% of the higher of the day's opening balance and equity; 12% "
  "maximum loss; 80% split with 1 minimum day per phase, or 95% with 3 profitable days (+0.5%) per phase and reward cycle",
  "as stated (dll relative)", "modelled", U + "47835196271249-2-Step-Flex", basis="snippet", read="4 Oct 2026")
r("FundingPips", "risk per trade idea", "Master accounts above $25K: a trade idea may not lose 2%", "risk at most 1.75% plus cost",
  "not binding", U + "48174287980177-Risk-Per-Trade-Idea", basis="snippet", read="4 Oct 2026")
r("FundingPips", "payouts", "every 14 calendar days from the first executed trade; minimum 1% of the account; positions and "
  "pending orders closed and at least 15 minutes after the last close before a request; trading disabled while the reward is "
  "processed (1-3 working days)", "request 15 minutes after the last close, flat; the account locked 3 working days (the slow "
  "end), cash then", "modelled", U + "34504564970385-Reward-Methods", basis="secondary")
r("FundingPips", "news (funded)", "Master accounts: profit of trades opened or closed within 5 minutes of high-impact news "
  "deducted (some sources: 10 minutes)", "flat in every bar overlapping 10 minutes either side (funded)", "plan",
  "https://www.luxalgo.com/prop-firms/funding-pips/", basis="secondary")
r("FundingPips", "allocation", "$400,000 across evaluation, funded and Prime accounts", "four 100K accounts", "modelled",
  "https://propvator.com/blog/?p=3491", basis="secondary")

# ---------------------------------------------------------------- FundedNext Stellar 2-Step
U = "https://help.fundednext.com/en/articles/"
r("FundedNext", "targets and limits", "8% / 5%; daily loss 5% and maximum loss 10% of the initial balance; 5 trading days per "
  "phase", "as stated (dll fixed)", "modelled", U + "9430123", read="4 Oct 2026")
r("FundedNext", "payouts", "first reward 21 days after the funded account opens, then every 14 days; 80%; fee refunded with the "
  "first reward; processed within 24 hours of the request; 'a processing fee is applied to all Performance Reward requests', "
  "'up to 3.5%' by RiseWorks and by other methods, set by the payment provider; no request under $20 (USDT, USDC; Rise from $50, "
  "bank transfer from $1,000)", "pending 1 working day; cash then; every reward, the refund included, less 3.5% (the upper end; "
  "version 10: version 9 had no fee); $20 minimum after the split and the fee", "cautious",
  U + "12673935-what-is-the-minimum-performance-reward-limit-for-fundednext", read="12 Oct 2026")
r("FundedNext", "news (funded)", "trades opened or closed (take-profit and stop-loss included) within 5 minutes before or after "
  "a listed high-impact release count 40% of their profit; holding through is allowed; evaluations free",
  "flat in every bar overlapping 10 minutes either side (funded)", "plan", U + "10701447-is-news-trading-allowed-at-fundednext", basis="snippet")
r("FundedNext", "copying", "copying trades from other firms' accounts is not allowed", "FundedNext's account trades a market no "
  "other account of the plan trades", "plan", U + "10701447", basis="snippet", read="4 Oct 2026")
r("FundedNext", "allocation", "$300,000 funded; evaluations unlimited", "one account", "modelled", U + "9430123", read="4 Oct 2026")

# ---------------------------------------------------------------- The5ers High Stakes
U = "https://the5ers.com/faqs/"
r("The5ers", "targets and limits", "10% / 5% (Classic 8% / 5%); daily loss 5% of the previous day's higher of balance and equity; "
  "maximum loss 10%; 3 profitable days (+0.5%) per phase", "as stated (dll relative)", "modelled", U + "what-is-the-drawdown-rule-for-high-stakes/", read="4 Oct 2026")
r("The5ers", "payout cap", "$4,000 per payout for the $100K account, $3,000 for $50K (page updated 15 September 2026); basis not "
  "stated; smaller sizes not published", "the withdrawal (before the split) with the fee refund counted inside the cap; below "
  "$50K 4% of the size (the lowest published ratio); profit above the cap stays in the account", "cautious",
  U + "what-are-the-general-rules-for-the-high-stakes-program/")
r("The5ers", "profit gate", "minimum P&L for a payout $500 ($100K), $300 ($50K)", "a request needs that profit; below $50K 0.6% "
  "of the size", "modelled", U + "payout-policy-and-hub-credit-in-the-high-stakes-program/")
r("The5ers", "payouts", "first withdrawal 14 days after the funded account is activated; then every 2 weeks from the last approved "
  "withdrawal; a withdrawal from $150 of profit ($150 after the split on the High Stakes payout page); review 24-48 business "
  "hours, processing up to 3 business days; 'Commission: 3.5% per withdrawal' by Rise, crypto (at most $1,500 a withdrawal) or "
  "bank transfer, none on hub credits; all trades closed", "pending 2 working days, cash 3 working days later, next request 14 "
  "days after approval; every cash withdrawal, the refund included, less 3.5% (version 10: version 9 had no commission); the "
  "$150 applied after the split and the commission", "modelled", U + "withdrawals-everything-you-need-to-know/", read="12 Oct 2026")
r("The5ers", "fee refund and hub credit", "10% of the fee as hub credit after phase 1, 20% after phase 2 (for a new challenge); 70% "
  "of the fee paid with external funds refunded with the first payout (credit-paid fee not refunded)", "credit spent on the "
  "next purchase; each account's refund 70% of the cash paid for it", "modelled", U + "payout-policy-and-hub-credit-in-the-high-stakes-program/")
r("The5ers", "news", "no order executed from 2 minutes before to 2 minutes after high-impact news (every programme); profits "
  "deducted", "flat in every bar overlapping 10 minutes either side, every stage", "plan", U + "what-are-the-general-rules-for-the-high-stakes-program/")
r("The5ers", "scaling", "the account scales up on each 10% target with 3 profitable days (table on the programme page); timing, "
  "opt-out and interaction with payouts not stated", "the plan keeps the balance under +9.5%, so the 10% milestone is never "
  "reached and the account keeps its purchased rules", "plan", "https://the5ers.com/high-stakes/")
r("The5ers", "accounts", "New: three each of 2.5K, 5K, 10K, one 25K, one 50K or 100K (shared with Classic)", "as stated",
  "modelled", U + "how-many-high-stakes-accounts-can-i-have/", read="4 Oct 2026")
r("The5ers", "inactivity", "30 consecutive days for evaluation accounts, counted from registration, and 60 for funded accounts (the "
  "general rules page); the High Stakes programme page: 'Accounts that show no activity for more than 30 consecutive days will be "
  "set to expire', counted from the day the account is registered", "never 25 days without a trade, which meets either reading",
  "plan", U + "what-are-the-general-rules-for-the-high-stakes-program/", read="12 Oct 2026")

# ---------------------------------------------------------------- FXIFY Two Phase Classic
U = "https://intercom.help/fxify/en/articles/"
r("FXIFY", "targets and limits", "5% / 10%; daily loss 4% of the previous day's balance; maximum loss 10% static; 4 days per phase",
  "as stated (dll relative)", "modelled", U + "14834680-the-2-phase-classic-account")
r("FXIFY", "payouts", "80% every 14 days or 100% every 30 days; minimum $50; biggest profit day at most 25% of total profit at "
  "the withdrawal; no refund on Classic; account read-only until the withdrawal is approved; processed within 3 business days",
  "best day checked at every request (against the account's best day ever); locked 3 working days", "modelled",
  "https://fxify.com/faqs/all-faqs/how-do-i-withdraw-my-profits/")
r("FXIFY", "news", "the Classic article lists news trading as allowed; FXIFY's programme comparison says no opening or closing "
  "within 5 minutes of red-folder events", "flat around releases at every stage (the stricter source)", "cautious",
  "https://fxify.com/blog/top-prop-firms-no-consistency-rule/", basis="page")
r("FXIFY", "scaling", "performance scale-up reviewed every 3 months (10% in 3 months, 2 profitable months)", "not modelled "
  "(forgoes any gain)", "not binding", U + "14834680-the-2-phase-classic-account")
r("FXIFY", "inactivity", "60 days", "never 25 days without a trade", "plan", U + "14834680-the-2-phase-classic-account")

# ---------------------------------------------------------------- Fintokei ProTrader
U = "https://support.fintokei.com/en/articles/"
r("Fintokei", "targets and limits", "8% / 6%; daily loss 5% of the day's starting equity; 10% maximum (version 9 reading); 3 "
  "separate trading days (a trade opened on the day, with a real market outcome) before passing a phase and before requesting a "
  "payout, accounts bought from 15 July 2026", "as stated; the 3 days required again in every payout cycle (the page does not "
  "say whether they count once or per cycle: the stricter reading)", "cautious",
  U + "8428030-what-does-the-rule-minimum-trading-days-mean-3-or-5-days", read="12 Oct 2026")
r("Fintokei", "minimal trades", "much smaller trades just to meet the minimum days are objected to", "no filler trades: missing "
  "days are ordinary trades, one a day", "plan", U + "9464503", read="4 Oct 2026")
r("Fintokei", "payouts", "14 days from the last processed payout or the first trade; minimum 100 in the account's currency (USD 100; EUR 100, "
  "JPY 20,000, CZK 2,000; 120 on 400K ProTrader); all trades closed; approved automatically, sent "
  "within one business day", "next request 14 days after processing; cash one working day later", "modelled", U + "11904545", basis="snippet")
r("Fintokei", "news", "allowed on every programme", "no news block", "modelled", "https://www.fintokei.com/protrader/", basis="snippet")
r("Fintokei", "open risk", "open risk per setup at most 3%", "one position at a time, risking at most 1.75% plus cost (the first version 10 draft: '1.5% per trade', a stale figure)", "not binding", "https://www.fintokei.com/protrader/", basis="snippet")

# ---------------------------------------------------------------- Hola Prime 2-Step Prime
U = "https://holaprime.com/forex/faq/hola-prime-challenges/hola-prime-2-step-prime-challenge/"
r("Hola Prime", "targets and limits", "8% / 5%; daily loss 5% of the previous day's closing balance; 10%; 3 trading days",
  "as stated", "modelled", U, read="4 Oct 2026")
r("Hola Prime", "payouts", "bi-weekly 80% with 3 profitable days (+0.5%) within 14 days; fee back 25% with each of the first "
  "four payouts; paid within one hour of the request (98%)", "pending one hour", "modelled", U, read="4 Oct 2026")
r("Hola Prime", "trade ideas", "a position opened within 10 minutes of a close on the same market and direction is one trade idea",
  "10 minutes between every close and the next entry", "plan", U, read="4 Oct 2026")
r("Hola Prime", "news", "no restriction on 2-Step Prime (restrictions apply to other account types)", "no news block",
  "modelled", "https://propvator.com/blog/hola-prime-news-trading-rule/", basis="secondary")
r("Hola Prime", "risk per trade", "funded: stop loss on every trade; risk per trade at most 2%", "1.75% plus cost, every trade "
  "bracketed", "not binding", U, read="4 Oct 2026")

# ---------------------------------------------------------------- Alpha Capital Pro 10%
U = "https://help.alphacapitalgroup.uk/en/articles/"
r("Alpha Capital", "targets and limits", "10% / 5%; daily loss 5% of the day's starting balance; 10%; 3 days", "as stated",
  "modelled", U + "8420429-alpha-pro-8-10", basis="snippet", read="4 Oct 2026")
r("Alpha Capital", "payouts", "bi-weekly: first request 14 days after the first funded trade, 5 trading days; all trades closed "
  "before a request; paid within 2 business days; the account locked until the balance is reset; 'The minimum performance fee "
  "amount is $100 ($100 gross, $80 net)' (bi-weekly article, 7 July 2026); a discretionary bonus of 0.25% of the initial size "
  "on the fourth request; no payout fee stated", "locked 2 working days; $100 of profit before the split, $80 of share after it "
  "(version 9: $100 after the split); the discretionary bonus not modelled", "modelled", U + "10570531-bi-weekly-performance-fee",
  read="12 Oct 2026")
r("Alpha Capital", "lot limit", "qualified accounts: at most 40 open lots per $100K (80 at $200K), aggregate; first breach: "
  "the profit from the excess not paid; second: account deactivated", "every funded position at most the limit (one position "
  "per account at a time); index lots counted at 1 unit a lot (the most lots any common contract size gives)", "modelled",
  U + "6934289-what-is-the-lot-size-limit-on-qualified-analyst-accounts")
r("Alpha Capital", "duration rule", "average trade over 2 minutes, most trades over 2 minutes, at least half the gross profit from "
  "trades over 2 minutes", "checked at every phase pass and request", "modelled", U + "8447268", read="4 Oct 2026")
r("Alpha Capital", "news (funded)", "qualified accounts: no trade opened or closed within 5 minutes of a listed release on the "
  "targeted instruments; evaluations free", "flat in every bar overlapping 10 minutes either side (funded)", "plan",
  U + "9293522-can-i-trade-news", basis="snippet")
r("Alpha Capital", "allocation", "$400,000 per household; $300,000 per strategy (the same asset)", "200K + 100K on the Nasdaq",
  "modelled", "https://alphacapitalgroup.uk/terms-and-conditions", basis="snippet")

# ---------------------------------------------------------------- GFT 2-Step Standard
U = "https://help.goatfundedtrader.com/en/articles/"
r("GFT", "targets and limits", "10% / 5%; 3 profitable days (+0.5%) per phase; daily 5% of the higher of balance and equity at "
  "5 pm New York; 10%", "as stated", "modelled", U + "13575169-2-step-standard", read="4 Oct 2026")
r("GFT", "payouts", "80% every 14 days, 4 profitable days (+0.5% of the initial balance) per cycle; first two payouts at most "
  "min(6%, $10,000) of the initial balance; $3,000 profit a day at most (the excess deducted); minimum withdrawal $100; "
  "processed within 2 business days; no open trades or pending orders; 'All rewards are subject to a 3% processing fee', "
  "calculated on the reward after the split", "pending 2 working days; capped amount paid, the rest kept; the trader receives "
  "97% of the 80% (77.6% of the profit withdrawn); the $100 applied to that amount (version 10: version 9 had no processing "
  "fee)", "modelled", "https://help.goatfundedtrader.com/rewards.html", read="12 Oct 2026")
r("GFT", "best and worst trade", "accounts bought from 9 October 2026: 'your most profitable trade must have made more profit "
  "than your worst trade lost' for a reward", "a request needs the best win to exceed the worst loss both since the last "
  "payout and over the account's life (it holds under either reading); otherwise the account trades on", "cautious",
  "https://help.goatfundedtrader.com/rewards.html", read="12 Oct 2026")
r("GFT", "minimum holding (funded)", "profit of trades held under 1 minute removed (accounts bought from 6 October 2026; 2 minutes "
  "before)", "such a win counts minus its cost", "modelled", U + "12849041-what-is-the-minimum-holding-time-for-trades", basis="snippet")
r("GFT", "news", "profit of a trade opened or closed within 5 minutes of a high-impact release capped at 1% of the account "
  "(evaluations and funded)", "flat around releases at every stage", "plan", U + "10742084-is-news-trading-allowed", basis="snippet")
r("GFT", "Goat Guard (funded)", "a combined floating loss of 2% closes the open trades; the first time the split falls to 50%, the "
  "second time the account is breached", "not reached: one position at a time whose stop loss plus cost is at most $1,750 plus "
  "cost per $100K, and the room above the floor caps it when the balance is low (at most 1.97% of the current balance); the "
  "plan holds no position through a gap", "not binding", U + "10742107-what-is-goat-guard", read="4 Oct 2026 (version 9 reading)")
r("GFT", "prohibited practices", "exploiting errors or latency; non-public information; front-running; trading that harms GFT's "
  "relationship with its broker; 'All-Or-Nothing Trading, where you can lose the account in one trade' (its article of 27 July "
  "2026 defines gambling-style trading as more than 80% of the available margin in one trading idea); hedging in one account, "
  "between your own accounts or with other traders; third-party or marketed EAs and strategies (your own EAs allowed); an EA in "
  "the assessment and manual trading when funded, or the reverse; martingale and grid recovery; large-volume trading 'without a "
  "clear or logical trading strategy'", PLANB + "; no last trade to the floor at GFT (5.4: an account whose room falls below "
  "the smallest normal risk is not traded further and is closed on request; version 9 placed that trade); margin at most 60%; every stage traded by hand",
  "plan", U + "10742118-what-are-prohibited-trading-practices", read="12 Oct 2026")

# ---------------------------------------------------------------- FunderPro Classic
U = "https://support.funderpro.com/en/articles/"
r("FunderPro", "targets and limits", "10% / 5%; daily 5% (base not settled: the stricter of initial and daily balance); 10%; "
  "4 days per phase", "as stated (dll min)", "modelled", U + "412020", read="4 Oct 2026")
r("FunderPro", "payouts", "every 14 days with at least $100 profit; processed within one working day of approval",
  "pending 1 working day, cash 1 later", "modelled", U + "419844", read="4 Oct 2026")
r("FunderPro", "margin", "funded accounts: at most 20% of the starting balance as margin per asset class", "stop floor in the search",
  "modelled", U + "421458", read="4 Oct 2026")
r("FunderPro", "news (funded)", "funded accounts without the Swing add-on: no 'news trading' (opening or closing a position during a "
  "restricted economic news event) and no 'news holding' (keeping a position open during one); challenges free (article of 1 "
  "December 2025); the terms: no entry within 2 minutes of a high-impact release", "flat around releases (funded): no position "
  "open in any bar overlapping 10 minutes either side", "plan", U + "378023-are-news-holding-and-news-trading-allowed", read="12 Oct 2026")
r("FunderPro", "lot sizes", "'Abrupt or unjustified changes in lot sizes may be deemed reckless behavior or gambling', for example "
  "'trading one (1) lot followed by ten (10) lots without a clear strategic basis'; lot sizes 'reasonably aligned' with the "
  "strategy and the balance (Trading Consistency and Lot Size Policy, 4 June 2026)", "every position sized by one stated rule "
  "(the risk share over the stop); no filler trades at FunderPro (version 10: version 9 completed missing days with 0.01-lot "
  "fillers, the kind of jump the policy names); the firm's judgement is not modelled", "plan",
  U + "696134-trading-consistency-and-lot-size-policy", read="12 Oct 2026")
r("FunderPro", "consistency", "Classic phase 1, phase 2 and funded stages: 'No Consistency Rule' (One-Phase 40%, Pro 45%)",
  "none applied", "modelled", U + "377852-what-is-the-consistency-rule-and-how-does-it-affect-my-challenge", read="12 Oct 2026")
r("FunderPro", "inactivity", "no trade placed or closed for 30 consecutive days: the account is failed (challenge and funded)",
  "never 25 days without a trade", "plan", U + "377851-how-does-the-inactivity-rule-affect-my-challenge", read="12 Oct 2026")
r("FunderPro", "market closures", "without the Swing add-on, every position closed at least 2 hours before a market closure of 2 "
  "hours or more (weekends, holidays, halts); not for daily pauses", "flat every day at 20:00 UTC and over weekends; holidays "
  "are not on the model's calendar: Part IV closes positions 2 hours before a holiday closure", "plan",
  U + "531445-position-closure-requirements-before-extended-market-closures", read="12 Oct 2026")

# ---------------------------------------------------------------- BrightFunded 2-Step Classic
U = "https://help.brightfunded.com/en/articles/"
r("BrightFunded", "targets and limits", "10% / 5%; daily 5% of the original size; 10%; 5 days per phase (a day counts with a "
  "trade open at least 60 seconds)", "as stated", "modelled", U + "9241611", read="11 Oct 2026")
r("BrightFunded", "payouts", "first request 30 days after the first funded trade, then every 14; all trades and orders closed; "
  "processed within a day", "pending 1 working day", "modelled", U + "11468668-how-can-i-request-my-payout", basis="snippet")
r("BrightFunded", "news (funded)", "profit of trades opened or closed (stops and targets included) within 5 minutes of significant "
  "news deducted", "flat around releases (funded)", "plan", U + "9241694-can-i-trade-news", basis="snippet")
r("BrightFunded", "inactivity", "a trade (held a minute) within 30 days of the last close, or the account is deactivated",
  "never 25 days without a trade", "plan", U + "11774572-inactivity-rule-policy", basis="snippet")
r("BrightFunded", "allocation", "$400,000 funded per trader; evaluations unlimited", "the recommended plan holds one; at the full allowance four 100K or two 200K, whichever is worth more in all", "modelled",
  "https://brightfunded.com/terms-and-conditions", basis="snippet")

# ---------------------------------------------------------------- Blue Guardian 2-Step Standard
U = "https://help.blueguardian.com/en/articles/14062291-2-step-standard-rules"
r("Blue Guardian", "targets and limits", "8% / 4%; daily 4% of the initial balance below the higher of balance and equity at 5 pm "
  "EST; 8% static; 3 profitable days (+0.5%)", "as stated", "modelled", U)
r("Blue Guardian", "minimum holding", "2 minutes; a trade closed sooner may be flagged", "bracket placed after 3 minutes; a trade "
  "under 2 minutes (only a breach can be) ends the account", "plan", U)
r("Blue Guardian", "Guardian Shield (funded)", "open trades closed at a 2% floating loss; first time the split falls to 50% for good, "
  "second time the account is breached", "modelled during and after the hold (cost counted in the loss, the cautious side)",
  "modelled", U)
r("Blue Guardian", "news (funded)", "no opening or closing 5 minutes before and after red-folder news (FOMC included)",
  "flat around releases (funded)", "plan", U)
r("Blue Guardian", "payouts", "85% (90% with an add-on); after the first payout, every 14 days from the previous request; minimum $100 "
  "by crypto (under $5,000), $500 by Rise; processed within 24 business hours; 'Trading can resume once the payout has been "
  "approved'; account flat and above its starting balance; 'All payouts are subject to a 3% processing fee'; fee back after the "
  "fourth payout (version 9 reading; the payouts page does not mention it)", "locked until processed (1 working day); every "
  "payout, the refund included, less 3% (version 10: version 9 had neither the lock nor the fee); $100 after the split and the "
  "fee", "modelled", "https://help.blueguardian.com/en/articles/9660857-how-do-payouts-work", read="12 Oct 2026")
r("Blue Guardian", "allocation", "$400,000 across funded accounts", "the recommended plan holds one; at the full allowance four 100K or two 200K, whichever is worth more in all", "modelled",
  "https://blueguardian.com/blogs/complete-scaling-path-for-funded-traders", basis="page")

# ---------------------------------------------------------------- Maven 2-Step
U = "https://maventrading.com/faqs"
r("Maven", "targets and limits", "8% / 5%; daily 4% of the higher of equity and balance at 00:00 UTC; 8% static; 3 profitable "
  "days (+0.5%) per phase and per withdrawal", "as stated", "modelled", U)
r("Maven", "payouts", "a withdrawal every 10 business days after the first trade; the fee refunded in full 'on the third "
  "withdrawal'; by direct bank transfer only from South Africa, Nigeria, Kenya and Ghana, elsewhere 'through Rise or other "
  "options' (the others not named), 'Payments via Rise incur a $20 withdrawal fee'; the account reset to its starting balance "
  "after each payout; processing time of a funded payout not stated", "requests every 14 calendar days (10 business days; "
  "public holidays not modelled); the fee with the third payout; $20 from every payout, the refund's included (version 10: "
  "version 9 had none); pending 3 working days (assumed)", "cautious", U, read="12 Oct 2026")
r("Maven", "withdrawal cap", "'a maximum withdrawal of $10,000 per 30-day rolling cycle (per trader)', a trader's accounts "
  "treated as one; 'calculated from the date on which you close the profit'; 'Any profits generated over the $10,000 limit "
  "will be voided'; the cycle 'calculated from your first available withdrawal date'", "closed profit in every 30-day window "
  "at most $10,000: no win is placed that could take a window above it, which meets the rule whether the $10,000 counts the "
  "profit or the amount paid and however the cycles are anchored; one Maven account in every portfolio, so the trader's cap "
  "is the account's", "cautious", U, read="12 Oct 2026")
r("Maven", "consistency above $5,000", "'If your total profit exceeds $5,000, your best trading day (day counted between two "
  "singular trades, with not 24h between closing trade 1 and opening trade 2) or singular trade ... may not exceed 50% of your "
  "profit in the funded stage payout cycle'; above it the profit is 'contracted to the 50% mark'", "funded profit never above "
  "$4,900, so the rule never applies. 'Total profit' is read as the profit since the account was last reset, which it is "
  "after every payout (the less strict of two readings: if it meant the profit of all cycles together, the rule would apply "
  "from the second cycle and would cut a cycle's profit whenever one 'day' held more than half of it, as a week of daily "
  "trades, one 'day' under that definition, usually would; the model does not apply that)", "plan", U, read="12 Oct 2026")
r("Maven", "gambling", "large bets at a reward:risk of 1:1.25 or lower", "every position's take-profit at least 1.5 times as far "
  "as its stop, checked on the position actually placed (a keep-alive position too: a protective stop at the plan's distance and a "
  "take-profit 1.5 times as far, closed after 3 minutes)", "plan", U)
r("Maven", "prohibited practices", "copying another individual's trades (both breached); grid and gap trading; reverse or group hedging "
  "(an account betting against another, at Maven or another firm); trading only hedges; EAs on every platform; 'all in' (no stop, "
  "or risk above the drawdown limit: 4% on the 2-Step), funded stage included; excessive scalping (50% or more of trades held "
  "under a minute); 'account mirroring' (listed among the standard rules); trades of vastly smaller lots do not count as trades",
  PLANB + "; trades entered by hand, no EA; one Maven account, never opposite another account; a stop on every position at 1.75% "
  "of the account; no Maven trade in the engine closes within a minute (the shortest last 2-3 minutes at the tightest stop: "
  "200 funded accounts, 10,403 trades)", "plan", U, read="12 Oct 2026")
r("Maven", "news", "no opening or closing 2 minutes either side of a red-folder release, take-profits included; evaluations and "
  "funded", "flat around releases at every stage", "plan", U)
r("Maven", "risk interview", "above $5,000 of payouts a risk interview; risking more than the amount stated in its email breaches",
  "not modelled: the plan's risk (1.75%) must be checked against the email's figure", "assumption", U)

# ---------------------------------------------------------------- Topstep 50K
U = "https://help.topstep.com/en/articles/8284233-topstep-payout-policy"
r("Topstep", "payouts", "Standard path: 5 winning days of $150+ net (days lock at 4 pm CT); positive net profit since the last "
  "payout; at most 50% of the balance up to $2,000 per request at 50K (a limited-time option, a Daily Loss Limit added at the "
  "Combine's checkout, raises it to $4,000); minimum $125; 90%; the request's session does not count toward the next five; "
  "requests Sunday 5 pm to Friday 5 pm CT; deducted at once, trading may continue, a deducted payout is protected from a later "
  "breach; $30 by ACH or wire, no Topstep fee by Aeropay or Wise", "as stated, by Wise or Aeropay; requests one minute after the "
  "4 pm CT lock; $125 read after the split; the $4,000 option not taken", "modelled",
  "https://help.topstep.com/en/articles/8284233-topstep-payout-policy", read="12 Oct 2026")
r("Topstep", "news", "new positions in equity index futures restricted ahead of CPI releases", "flat around US CPI releases",
  "plan", "https://help.topstep.com/en/articles/13613539-risk-adjustments-high-risk-high-volatility", basis="snippet")
r("Topstep", "consistency path", "alternative path: 3 trading days, largest day at most 40% of net profit, $3,000 cap at 50K",
  "not used (the Standard path is modelled)", "not binding", U)

# ---------------------------------------------------------------- Apex 50K EOD
U = "https://apextraderfunding.com/help-center/"
r("Apex", "evaluation", "30 days of access, expiring at 6 pm ET on day 30", "the target must be reached before that time",
  "modelled", U + "billing/evaluation-plan-fees-and-access-explained/", basis="secondary")
r("Apex", "payouts", "minimum balance $52,600 to request (safety net $52,100 + $500); 5 qualifying days ($250, conflicting reports "
  "of $200); every profitable day under 50% of net profit since the last approved payout; at most $1,500, $1,500, $2,000, "
  "$2,500, $2,500 and $3,000 for the first six requests; at most 6 payouts; 100% split; a pending request denied if the "
  "balance falls below the threshold", "the plan pauses trading while a request is pending (2 "
  "working days), so no denial can occur; today's profit counted in the 50% rule", "plan",
  U + "eod-trailing-drawdown-accounts/eod-payouts/", basis="secondary")
r("Apex", "news", "directional news trading allowed", "no news block", "modelled", U, basis="secondary")

# ---------------------------------------------------------------- rules stated in version 9's programme chapters that no list
# contained (version 10 self-audit), and each firm's behavioural rules (applied at the firm's discretion: Chapter 31.2)
V9b = "4 Oct 2026 (version 9 reading)"
r("FTMO", "prohibited practices", "overleveraging, overexposure, one-sided bets and account rolling (none defined on the page); simulated trades for manipulative purposes, including opposite positions across connected accounts or accounts with other providers; gap trading; exploiting platform errors", PLANB, "plan",
  "https://ftmo.oanda.com/forbidden-trading-practices/", read="12 Oct 2026")
r("FundingPips", "profit concentration", "evaluations bought from 27 June 2026, $25K and up: if one trade idea makes more than 60% of a phase target, the funded account needs 4 profitable days (+0.5%) before every reward request, permanently",
  "not reached: no evaluation trade above 40% of its phase target", "not binding", "https://help.fundingpips.com/hc/en-us/articles/48174287980177-Risk-Per-Trade-Idea", read=V9b)
r("FundedNext", "monitored as gambling", "one-sided betting (remedy: a 1% risk limit), account rolling, breaching several accounts in a short span, losses exceeding gains (remedies: 40% consistency on on-demand rewards or a lower split)",
  PLANB + "; the remedies are measured as scenarios (Chapter 28.7)", "plan", "https://help.fundednext.com/", read=V9b)
r("The5ers", "prohibited practices", "one-trade target attainment (permanent ban)", "no single trade can reach a target (40% cap)", "plan", "https://the5ers.com/high-stakes/", read=V9b)
r("FXIFY", "prohibited practices", "gambling and all-or-nothing ('YOLO') trading", PLANB, "plan", "https://intercom.help/fxify/en/", read=V9b)
r("Fintokei", "prohibited practices", "reaching a phase target in one or a few identical trades ('all-in'); if trading is flagged unsustainable, leverage 1:10 and daily profit and loss capped at 1%", PLANB, "plan",
  "https://support.fintokei.com/en/articles/9464503-what-is-all-in-trading-and-why-is-it-forbidden-to-achieve-profit-target-in-one-trade", read=V9b)
r("Hola Prime", "prohibited practices", "one-sided betting, grid trading, excessive margin use, hedging across accounts, profitability materially dependent on concentrated outcomes", PLANB, "plan",
  "https://holaprime.com/forex/faq/", read=V9b)
r("Alpha Capital", "risk per trade", "never risk or lose 2% or more on one trade or group of trades closed together", "risk at most 1.75% plus cost; one position at a time", "not binding",
  "https://help.alphacapitalgroup.uk/", read=V9b)
r("Alpha Capital", "prohibited practices", "gambling; 'all or nothing' trading; minimal lots to complete trading days on qualified accounts", PLANB + "; no filler trades at Alpha Capital", "plan", "https://help.alphacapitalgroup.uk/", read=V9b)
r("Blue Guardian", "prohibited practices", "margin use above 80% counts as gambling", "margin at most 60% of the balance", "not binding", "https://help.blueguardian.com/", read=V9b)
r("Topstep", "targets and limits", "$3,000 target; $2,000 maximum loss trailing the end-of-day balance and locking at the starting balance; after the first payout the maximum loss level is the starting balance; positions closed by the daily close",
  "as stated; flat at 20:00 UTC", "modelled", "https://help.topstep.com/", read=V9b)
r("Topstep", "consistency (Combine)", "best day at most 55% of the profit target (version 9 reading)", "not reached: no day above 40% of the target (the engine also caps a day at 50% of the target, stricter than the published 55%)", "not binding", "https://help.topstep.com/", read=V9b)
r("Apex", "targets and limits", "$3,000 target; $2,000 maximum loss trailing the end-of-day balance, which stops trailing at the starting balance plus $100 once funded; $1,000 daily loss limit; flat by 4:59 pm ET every session",
  "as stated; flat at 20:00 UTC", "modelled", "https://apextraderfunding.com/help-center/", basis="secondary", read=V9b)

# ---------------------------------------------------------------- per-person limits and copying rules (version 10: added to the
# inventory; version 9 stated them in its programme chapters and Chapter 27 but no list contained them). Readings of
# 4-5 October 2026 (version 9), not re-read for version 10 unless marked; source: the firm's help centre.
V9 = "4 Oct 2026 (version 9 reading)"
r("FTMO", "copying", "the same strategy on your own accounts within the $400,000 cap; accounts under other registrations "
  "prohibited", "every FTMO account trades the shared Nasdaq direction", "plan", "https://ftmo.oanda.com/faq/how-many-accounts-can-i-have/",
  read="12 Oct 2026")
r("FundingPips", "copying", "only between your own FundingPips accounts; no copier services", "own entries on each account",
  "plan", "https://help.fundingpips.com/", read=V9)
r("The5ers", "copying", "allowed across your own accounts", "the shared Nasdaq direction", "plan", "https://the5ers.com/faqs/", read=V9)
r("FXIFY", "allocation", "one active account of each size, challenge and funded alike (5K to 400K, $805,000 in all; rule of 25 "
  "November 2024); Classic up to 100K", "at full allowance one Classic account of each size from 5K to 100K", "modelled",
  "https://intercom.help/fxify/en/", read=V9)
r("FXIFY", "copying", "between your own FXIFY accounts; from external accounts only with approval; third-party copying prohibited",
  "the shared Nasdaq direction across your own accounts", "plan", "https://intercom.help/fxify/en/", read=V9)
r("Fintokei", "allocation", "EUR 500,000 of accounts in total", "five 100K (USD 500,000, about EUR 444,000 at 1.1256)", "modelled",
  "https://support.fintokei.com/", read=V9)
r("Fintokei", "copying", "your own trades across your own accounts; other people's signals prohibited", "the shared Nasdaq direction",
  "plan", "https://support.fintokei.com/", read=V9)
r("Hola Prime", "allocation", "$500,000", "two 100K", "modelled", "https://holaprime.com/forex/faq/", read=V9)
r("Hola Prime", "copying", "only between your own Hola Prime accounts (funded: one master and one copier); copying from other prop "
  "firms' accounts prohibited", "two accounts on a market no other account of the plan trades", "plan",
  "https://holaprime.com/forex/faq/", read=V9)
r("Alpha Capital", "copying", "from your own external accounts with proof of ownership", "the shared Nasdaq direction", "plan",
  "https://help.alphacapitalgroup.uk/", read=V9)
r("GFT", "allocation", "$400,000 funded", "one account", "modelled", "https://help.goatfundedtrader.com/", read=V9)
r("GFT", "copying", "no duplicated trades or trade ideas between GFT accounts", "one GFT account (a second would need a market of "
  "its own: not modelled)", "plan", "https://help.goatfundedtrader.com/", read=V9)
r("FunderPro", "allocation", "$200,000", "one account (200K where it is worth more)", "modelled", "https://support.funderpro.com/", read=V9)
r("FunderPro", "copying", "no replicating trades across FunderPro accounts; no copying from accounts you do not own", "one account",
  "plan", "https://support.funderpro.com/", read=V9)
r("FunderPro", "risk per trade", "at most 2%", "1.75% plus cost", "not binding", "https://support.funderpro.com/", read=V9)
r("BrightFunded", "copying", "allowed between your own accounts", "the shared Nasdaq direction", "plan",
  "https://help.brightfunded.com/", read=V9)
r("Blue Guardian", "copying", "your own accounts only", "the shared Nasdaq direction", "plan", "https://help.blueguardian.com/", read=V9)
r("Maven", "allocation", "$200,000 per person", "one 100K", "modelled", "https://maventrading.com/faqs", read=V9)
r("Topstep", "allocation", "5 Express Funded Accounts at once", "five 50K (the optional futures layer)", "modelled",
  "https://help.topstep.com/", read=V9)
r("Apex", "allocation", "20 funded accounts", "twenty 50K (the optional futures layer)", "modelled",
  "https://apextraderfunding.com/help-center/", basis="secondary", read=V9)

# ---------------------------------------------------------------- fees, refunds and splits (version 10: added to the inventory; version
# 9 printed them from its programme sheets, read 4-5 October 2026, and they are not re-read here unless marked)
FS = "fee, refund and split"
r("FTMO", FS, "EUR 540 for 100K ($607.82 at 1.1256), EUR 1,080 for 200K ($1,215.65); fee refunded with the first reward; 80% split "
  "(90% after scaling)", "as stated (scaling not modelled)", "modelled", "https://ftmo.oanda.com/", read=V9)
r("FundingPips", FS, "$499 for 100K (the largest Flex size); no registration-fee refund on Flex; 80% or 95%, chosen at purchase",
  "as stated", "modelled", "https://help.fundingpips.com/", read=V9)
r("The5ers", FS, "New (10% / 5%) $491 for 100K, Classic (8% / 5%) $545; smaller New sizes $19 to $278; 80% split, rising with "
  "scaling", "as stated; the plan never reaches the first scaling milestone, so the split stays 80%", "modelled",
  "https://the5ers.com/high-stakes/", read=V9)
r("FXIFY", FS, "$549 for 100K (the largest Classic size); no refund on Classic; 80% every 14 days or 100% every 30 days, chosen "
  "at purchase", "as stated", "modelled", "https://fxify.com/", read=V9)
r("FundedNext", FS, "$549.99 for 100K, $1,049.99 for 200K (from August 2026); refunded with the first reward; 80%", "as stated",
  "modelled", "https://help.fundednext.com/", read=V9)
r("Fintokei", FS, "$549 for 100K, $1,249 for 200K, $2,599 for 400K; returned with the first payout as a sign-up bonus; 80%",
  "as stated", "modelled", "https://support.fintokei.com/", read=V9)
r("Hola Prime", FS, "$409 to $599 for 100K, by payout option; returned 25% with each of the first four payouts; bi-weekly 80%",
  "$599, the upper end", "cautious", "https://holaprime.com/", read=V9)
r("Alpha Capital", FS, "$497 for 100K, $997 for 200K; refund policy reported inconsistently; 80%", "no refund (the cautious "
  "reading)", "cautious", "https://alphacapitalgroup.uk/", read=V9)
r("FunderPro", FS, "$539 for 100K at list price (often 20% off), $989 for 200K; refunded with the first reward; 80%",
  "the list price; refund with the first payout", "modelled", "https://funderpro.com/", read=V9)
r("GFT", FS, "$524 for 100K, $974 for 200K (version 9 reading); the fee is called 'refundable' on GFT's how-it-works page, but "
  "neither its 2-Step Standard page (updated 5 October 2026) nor its rewards page (9 October 2026) says when, and third-party "
  "descriptions conflict (the first, third or fourth payout, or after passing); 80% split", "no fee refund (the cautious "
  "reading; version 9 refunded the fee with the first payout)", "cautious", "https://help.goatfundedtrader.com/2-step-standard.html",
  read="12 Oct 2026")
r("BrightFunded", FS, "EUR 497 for 100K ($559.42 at 1.1256), EUR 997 for 200K ($1,122.22); refund only with a paid add-on; 80%",
  "no refund (the add-on is not bought)", "modelled", "https://help.brightfunded.com/", read=V9)
r("Blue Guardian", FS, "$579 for 100K at list price (often half price with a code), $1,162 for 200K; refunded after the fourth "
  "payout; 85%", "the list price; refund with the fourth payout", "modelled", "https://help.blueguardian.com/", read=V9)
r("Maven", FS, "$440 for 100K (the largest 2-Step size); refunded with the third payout; 80%", "as stated", "modelled",
  "https://maventrading.com/faqs", read=V9)
r("Topstep", FS, "$49 a month (Standard path); a reset after a breach $49; $149 activation per Express Funded Account; 90%",
  "as stated", "modelled", "https://help.topstep.com/", read=V9)
r("Apex", FS, "$550 at list price; public codes of 80-90% off for most of 2026 (about $55); $99 activation when passed; 100% split",
  "$55 and $99 (a discount code assumed; at the list price the futures layer is worth less)", "assumption",
  "https://apextraderfunding.com/", basis="secondary", read=V9)
r("every firm", "minimum payouts", "FTMO $20 (bank transfer); FundedNext $20 ('a reward under $20 cannot be requested'); "
  "FundingPips 1% of the account; FXIFY $50; Hola Prime $50 (bank wire or crypto); Fintokei 100 in the account's currency; GFT "
  "$100; Blue Guardian $100; Alpha Capital and FunderPro $100 of profit (Alpha: '$100 gross, $80 net'); The5ers $150 after the "
  "split; Topstep $125; Apex $500; BrightFunded and Maven state none on the pages read", "each applied to the trader's share "
  "after the split and any payout fee, the stricter reading where a page does not say which; where a page states the minimum as "
  "profit (Alpha Capital, FunderPro), as that profit ($80 of share); none where none is stated (version 10: version 9 had no "
  "minimum at FTMO, FundedNext or Hola Prime, and applied Alpha's and FunderPro's after the split)", "cautious",
  "the firms' payout pages (rows above)", read="12 Oct 2026")

r("every firm", "payout fees", "firm fees on every payout: GFT 3% after the split (rewards page, 9 October 2026), The5ers 3.5% per "
  "cash withdrawal (24 August 2026), FundedNext up to 3.5% on every request (29 September 2026), Blue Guardian 3% (31 August "
  "2026), Hola Prime 2.5% on every method, at least $5 by crypto and $25 by Rise or bank wire (its rules pages, 12 October 2026; "
  "its payout FAQ still says bank wire and crypto are free); stated as none: FXIFY (its blog), BrightFunded ('no additional "
  "fees'; banks or networks may take $5-$50), FTMO (bank and network costs only), Fintokei (the firm covers withdrawal fees, "
  "except 2.5% plus EUR 10-20 on crypto); not stated on the pages read: FundingPips (crypto rewards carry service, exchange and "
  "network charges; Rise and bank from $500), Alpha Capital, FunderPro, Maven ($20 by Rise; direct bank transfer only in four "
  "countries; 'other options', which reviews describe as crypto at network fees only), Topstep ($30 by ACH or wire; Wise and "
  "Aeropay free), Apex (a third-party claim of 15% on the first payout and 4% after, not found on its pages)", "the five firm "
  "fees are modelled on every withdrawal, the refund included (Hola Prime's at least $5), with minimums checked after them; where "
  "a firm offers a method without a charge the plan uses it, and method costs (banks, networks, currency conversion) are not "
  "modelled", "cautious", "the firms' payout pages (rows above)", read="12 Oct 2026")

# ---------------------------------------------------------------- every firm
r("every firm", "conflicting positions", "no hedging across accounts or firms", "one direction per market group across all "
  "accounts (shared-direction rule)", "plan", "the firms' prohibited-practice pages", read="4 Oct 2026")
r("every firm", "identity", "accounts only in the trader's own name", "one person's accounts", "plan", "the firms' terms", read="4 Oct 2026")
r("every firm with minimum trading days", "minimal trades", "FTMO, FXIFY, FundedNext, BrightFunded (a trade open 60 seconds), "
  "Topstep and Apex count a day on which a position is opened and state no minimum volume; Fintokei and Alpha Capital object to "
  "minimal trades that complete days, and FunderPro (abrupt lot-size changes) and Hola Prime (unexplained deviations in position "
  "size) to the size jump such a trade makes", "at the first six, a missing day after the target is completed with one minimal "
  "position (0.01 lot or one micro contract, a protective stop at the plan's distance) held 3 minutes; that those firms accept it is "
  "an assumption; Fintokei, Alpha "
  "Capital, FunderPro and Hola Prime get no fillers (missing days are ordinary trades, one a day; version 9 gave FunderPro and "
  "Hola Prime fillers, and this row did not list Hola Prime); the plan is also measured without fillers", "assumption",
  "the firms' trading-day definitions and prohibited-practice pages (programme rows above)", read="12 Oct 2026")

# ---------------------------------------------------------------- leverage (12 October 2026; version 9's table kept it in the
# programme sheets, unread since 4 October). Where the leverage binds the plan's stop (optimize_v10.m_min above 0.6 hourly sd)
# it was read on the firm's own page, or the model uses the lowest figure any source gives
r("FTMO", "leverage", "FTMO Account (Standard): indices 1:50, forex 1:100 (comparison listings; FTMO's symbol pages do not render "
  "the figures as text)", "1:50 on the Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd) and FTMO's 1% risk", "not binding", "https://ftmo.com/en/symbols/",
  basis="secondary", read="12 Oct 2026")
r("FundingPips", "leverage", "2-Step Flex: forex up to 1:100 (the programme's launch notes; the help centre refuses automated "
  "reading); indices 1:5 above 0.5 lots in version 9's reading of the help centre (4 October 2026), while listings of October 2026 "
  "give 1:20 or a leverage falling from 1:50 to 1:5 with the position's size, so the plan does not trade indices there", "1:100 on USDJPY and EURUSD; at 1:50 the plan's own 60% margin cap would raise EURUSD's stop floor to 0.68 hourly sd "
  "(USDJPY's would stay below 0.6; FundingPips states no margin rule)", "modelled", "https://fundingpips.com/2-step-flex", basis="secondary", read="12 Oct 2026")
r("FundedNext", "leverage", "Stellar 2-Step: forex 1:100; gold under the commodities tier, 1:25 in the challenge and 1:15 funded "
  "(secondary descriptions, which differ)", "EURUSD 1:100; gold 1:10, below every reading, so its stop floor (1.03 hourly sd at "
  "1.75% risk) is at least as strict as the firm's", "cautious", "https://help.fundednext.com/", basis="secondary", read="12 Oct 2026")
r("The5ers", "leverage", "High Stakes: forex 1:100, indices and metals 1:25 (the firm's trading-conditions announcement, as "
  "listed)", "1:25 on the Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd)", "not binding", "https://the5ers.com/high-stakes/", basis="secondary", read="12 Oct 2026")
r("FXIFY", "leverage", "2-Phase Classic, fixed: FX and gold 30:1, indices 10:1", "as stated: it binds (the Nasdaq stop at least "
  "1.07 hourly sd at 1.75% risk, USDJPY 0.82)", "modelled", "https://intercom.help/fxify/en/articles/14834680-the-2-phase-classic-account",
  read="12 Oct 2026")
r("Fintokei", "leverage", "ProTrader: forex 1:100, indices 1:50 (secondary listings; one gives 1:20 for indices)", "1:50 on the "
  "Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd)", "not binding", "https://www.fintokei.com/protrader/", basis="secondary", read="12 Oct 2026")
r("Hola Prime", "leverage", "2-Step Prime: forex 50:1, metals 10:1, indices 10:1, commodities 2:1", "as stated: it binds (EURUSD "
  "stop at least 0.68 hourly sd, gold 1.03, at 1.75% risk)", "modelled", "https://holaprime.com/forex/forex-trading-rules/", read="12 Oct 2026")
r("Alpha Capital", "leverage", "Alpha Pro: FX 1:100, metals 1:30, indices 1:20, oil 1:10", "1:20 on the Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd)", "not binding",
  "https://help.alphacapitalgroup.uk/en/articles/8420429-alpha-pro-8-10", read="12 Oct 2026")
r("GFT", "leverage", "2-Step Standard: evaluation forex 1:100, indices 1:20; funded forex 1:50, indices 1:10", "as stated: the funded "
  "1:10 binds (the Nasdaq stop at least 1.07 hourly sd at 1.75% risk)", "modelled",
  "https://help.goatfundedtrader.com/en/articles/13575169-2-step-standard", read="12 Oct 2026")
r("FunderPro", "leverage", "challenges and funded: forex 1:100; metals, oil and indices 1:30 (with the funded 20% margin rule, its "
  "own row)", "as stated: with the 20% rule it binds (the Nasdaq stop at least 1.07 hourly sd at 1.75% risk, USDJPY 0.73)", "modelled",
  "https://funderpro.com/", read="12 Oct 2026")
r("BrightFunded", "leverage", "forex 1:100, indices 1:20, the same in challenge and funded (secondary descriptions)", "1:20 on the "
  "Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd)", "not binding", "https://brightfunded.com/2-step-classic", basis="secondary", read="12 Oct 2026")
r("Blue Guardian", "leverage", "2-Step indices 1:10 in one listing, 1:20 in another; the firm's pages read state only 'Leverage "
  "1:30 Max'", "1:10, the lowest reading, so its stop floor (1.07 hourly sd at 1.75% risk) is at least as strict as the firm's",
  "cautious", "https://blueguardian.com/", basis="secondary", read="12 Oct 2026")
r("Maven", "leverage", "forex 75:1; commodities, indices and precious metals 20:1", "1:20 on the Nasdaq; not binding: at the plan's risk, any leverage of 1:20 or more lets 60% of the balance carry a position at the plan's tightest stop (0.6 hourly sd)", "not binding",
  "https://maventrading.com/faqs", read="12 Oct 2026")

# ---------------------------------------------------------------- inactivity (12 October 2026): the firms whose rows above had
# none. The plan's own rule (never 25 days without a trade; acct_mc's keep-alive) is stricter than every limit found;
# FundingPips, Fintokei and Apex state none on the pages read (FundingPips' help centre and Apex's site refuse automated
# reading). The rows above (FTMO, The5ers, FXIFY, FunderPro, BrightFunded) say "never 25 days without a trade" too
NOFILL_KA = ("never 25 days without a trade: no wait comes near it there (14-day payout cycles, no minimal positions); the audit "
             "measures the longest time without a trade")
KA = ("never 25 days without a trade: a minimal position held 3 minutes on the day 22 days after the last entry if nothing has been "
      "traded since, or before a payout request that would lock the account past that day")
r("FundedNext", "inactivity", "an account on which no trade is placed for 30 consecutive calendar days, weekends and holidays "
  "included, is deactivated (article of 27 July 2026)", KA, "plan",
  "https://help.fundednext.com/en/articles/8019664-is-there-an-inactivity-period-for-my-accounts-in-fundednext-cfd", read="12 Oct 2026")
r("Hola Prime", "inactivity", "any account, challenge or funded, inactive for 30 consecutive calendar days is permanently suspended; "
  "only opening a trade counts ('If your last trade was opened on January 1st, you must open a new position by January 30th')",
  NOFILL_KA, "plan", "https://holaprime.com/forex/faq/hola-prime-challenges/hola-prime-2-step-prime-challenge/", read="12 Oct 2026")
r("Alpha Capital", "inactivity", "all accounts at every stage: an account not traded for more than 30 consecutive days is deactivated "
  "for good; activity is a trade that changes the balance, not a login (article of 6 July 2026)", NOFILL_KA, "plan",
  "https://help.alphacapitalgroup.uk/en/articles/8420080-inactivity", read="12 Oct 2026")
r("GFT", "inactivity", "evaluation and funded accounts: breached if no trade is placed for 30 consecutive days, with no reinstatement "
  "(article of 27 July 2026)", KA, "plan",
  "https://help.goatfundedtrader.com/en/articles/10742197-is-there-any-inactivity-limit", read="12 Oct 2026")
r("Blue Guardian", "inactivity", "'At least one trade every 30 days is required to keep the account active'; otherwise the account is "
  "breached (article of 25 June 2026); the clock starts when the account is created (its general-information rules)", KA, "plan",
  "https://help.blueguardian.com/en/articles/9661512-prohibited-trading-practices-account-policies", read="12 Oct 2026")
r("Maven", "inactivity", "'Accounts must not be dormant for more than 30 calendar days. Inactivity is defined as having no executed "
  "trades.' Its gambling rules add: 'Trades with vastly smaller lot sizes will NOT count as a trade'", KA + "; needed only when the "
  "$10,000 per 30 days stops trading for more than three weeks. That the dormancy rule counts the minimal position (an executed trade) "
  "is an assumption; a gain from it above the 30-day cap is voided, as Maven states", "assumption", "https://maventrading.com/faqs",
  read="12 Oct 2026")
r("Topstep", "inactivity", "'XFAs with no trading activity for more than 30 days may be closed. XFAs can't be put on hold.'", KA,
  "plan", "https://help.topstep.com/en/articles/8284215", read="12 Oct 2026")

# ---------------------------------------------------------------- re-read on 12 October 2026
# The rows above dated 4 October 2026 are version 9's readings, which the first version 10 inventory had carried over.
# They were read again on 12 October 2026 (pages that refuse automated reading were fetched as a browser would, or read
# from a search engine's copy: basis 'snippet'; where neither was possible, from reviews and listings: basis 'secondary');
# each update below replaces the fields it names. Every row now carries an October 11 or 12 date.
D12 = "12 Oct 2026"
REREAD = {
 ("FTMO", "targets and limits"): dict(read=D12),
 ("FTMO", "risk guidance"): dict(rule="FTMO generally recommends not risking more than 1% per trade idea, and at most 1-1.5% of the initial "
    "balance on one position, so as not to fall into its high-risk monitoring", model="risk at most 1% of the account at FTMO (L_MAX): "
    "the plan's trade idea is one position, so the stricter figure binds (version 9 and the first version 10 draft: 1.5%)", read=D12),
 ("FTMO", FS): dict(rule="EUR 540 for 100K ($607.82 at 1.1256), EUR 1,080 for 200K ($1,215.65) at list price (a promotion of October 2026 "
    "sells the 100K at EUR 439; the price list does not render as text, the prices are version 9's reading and secondary listings); "
    "the 2-Step fee refunded with the first reward; 80% split (90% with the Scaling Plan or the Premium Programme)", read=D12,
    source="https://ftmo.com/en/faq/is-the-entry-fee-refunded/"),
 ("FundingPips", "targets and limits"): dict(read=D12, basis="snippet"),
 ("FundingPips", "risk per trade idea"): dict(rule="Master accounts: the loss of one trade idea (positions on one instrument in one direction; a "
    "new one within 10 minutes of a losing close counts with it) at most 2% or 3% of the account by model; not in evaluations",
    model="risk at most 1.75% plus cost; more than 10 minutes between a close and the next entry", read=D12, basis="snippet"),
 ("FundingPips", "profit concentration"): dict(read=D12, basis="snippet"),
 ("FundingPips", FS): dict(rule="$555 for 100K at list price (the largest Flex size; version 9 recorded $499, a discounted price); no "
    "registration-fee refund on Flex; 80% or 95%, chosen at purchase", model="$555", read=D12, basis="snippet",
    source="https://fundingpips.com/2-step-flex"),
 ("FundedNext", "targets and limits"): dict(read=D12, source="https://help.fundednext.com/en/articles/17255124-stellar-2-step-challenge"),
 ("FundedNext", "copying"): dict(rule="copying only between your own challenge accounts; copying between a FundedNext Account and any other "
    "FundedNext account prohibited; other people's trades and cloud copiers prohibited; copying from your own accounts at other firms "
    "not addressed", model="FundedNext's account trades a market no other account of the plan trades", status="cautious", read=D12,
    source="https://help.fundednext.com/en/articles/8019805-what-is-the-copy-trading-rule-at-fundednext"),
 ("FundedNext", "allocation"): dict(rule="$300,000 across Stellar funded accounts ($50,000 in some countries); challenge accounts unlimited",
    read=D12, source="https://help.fundednext.com/en/articles/8027523-how-many-accounts-can-i-have-with-fundednext"),
 ("FundedNext", FS): dict(rule="$549.99 for 100K, $1,099.99 for 200K (the product page; its help centre shows $999.99 for 200K); refunded "
    "with the first reward; 80%; 15% of both phases' profit targets paid once the Scale-Up criteria are met", model="$549.99 and "
    "$1,099.99, the higher 200K figure (version 9: $1,049.99); the 15% reward left out (the plan does not scale)", status="cautious",
    read=D12, source="https://fundednext.com/cfds/stellar-2-step"),
 ("The5ers", "targets and limits"): dict(read=D12),
 ("The5ers", "accounts"): dict(read=D12),
 ("The5ers", FS): dict(read=D12, basis="secondary", rule="New (10% / 5%) $491 for 100K, Classic (8% / 5%) $545 (comparison listings of "
    "October 2026; the firm's price slider does not render as text); smaller New sizes $19 to $278; 80% split, rising with scaling"),
 ("FXIFY", "allocation"): dict(read=D12, basis="snippet", source="https://fxify.com/faqs/all-faqs/what-the-max-allocation/"),
 ("FXIFY", "copying"): dict(rule="copy trading allowed with prior approval; third-party copying prohibited", read=D12,
    source="https://intercom.help/fxify/en/articles/14834680-the-2-phase-classic-account"),
 ("FXIFY", FS): dict(rule="Classic $549 for 100K, $379 for 50K, $199 for 25K, $119 for 15K, $89 for 10K, $59 for 5K; no refund on Classic; "
    "80% every 14 days or 100% every 30 days, chosen at purchase", model="as stated (version 9 left out the 15K size)", read=D12,
    source="https://fxify.com/"),
 ("Fintokei", "targets and limits"): dict(rule="8% / 6%; daily loss 5% of the day's starting equity; 10% maximum; 3 separate trading days (a "
    "trade opened on the day, with a real market outcome) before passing a phase and before requesting a payout, accounts bought from 15 "
    "July 2026 (the support article and the ProTrader page; the plan table on fintokei.com reads 'Min 3 profitable days' for ProTrader "
    "10K-400K)", model="as stated; the 3 days required again in every payout cycle (the stricter reading); in the evaluations either "
    "reading is met, because under the plan's 40% policy every phase has at least three days with a net profit"),
 ("Fintokei", "minimal trades"): dict(read=D12, source="https://support.fintokei.com/en/articles/9464503-what-is-all-in-trading-and-why-is-it-forbidden-to-achieve-profit-target-in-one-trade"),
 ("Fintokei", "prohibited practices"): dict(rule="reaching a phase target with one trade idea (a trade, or same-symbol same-direction trades "
    "overlapping in time) ('all-in'); much smaller trades just to meet the minimum days; if trading is flagged unsustainable, leverage 1:10 "
    "and daily profit and loss capped at 1%", read=D12),
 ("Fintokei", "allocation"): dict(rule="400,000 EUR/USD of virtually funded ProTrader and ProTrader Swing accounts together (evaluations not "
    "counted)", model="four 100K (USD 400,000; version 9 read EUR 500,000 and held five)", read=D12,
    source="https://support.fintokei.com/en/articles/6538886-how-many-accounts-and-open-positions-can-i-have"),
 ("Fintokei", "copying"): dict(rule="copying your own trades from other prop firms or brokers allowed; other people's trades, signals, "
    "third-party EAs and reversed copies prohibited", read=D12,
    source="https://support.fintokei.com/en/articles/10419735-copy-trading-and-eas-what-is-allowed-and-what-prohibited"),
 ("Fintokei", FS): dict(rule="$549 for 100K, $1,249 for 200K, $2,599 for 400K (ProTrader page); 80%; the English pages state no fee "
    "return; the Japanese plan pages return the fee 'via the Scaling Dojo', which the English FAQ says was retired on 21 January 2026 "
    "(a secondary review describes a return after 20 trading days and two payout requests)", model="no fee return, the cautious "
    "reading (version 9: the fee with the first payout)", status="cautious", read=D12, source="https://www.fintokei.com/protrader/"),
 ("Hola Prime", "targets and limits"): dict(rule="8% / 5%; daily loss 5% of the previous day's closing balance (4% at 200K; reset 17:00 "
    "New York); maximum loss 10% of the initial balance, static (8% at 200K); 3 trading days per phase", model="as stated at 100K, "
    "the only size the plan holds there", read=D12),
 ("Hola Prime", "payouts"): dict(rule="bi-weekly 80% with 3 profitable days (closed profit of at least 0.5% of the initial balance) within "
    "14 days; an account review of up to 24 business hours, then paid within one hour; minimum $50 by bank wire or crypto ($500 by Rise); "
    "'A 2.5% payout processing fee applies to all payment methods, subject to a minimum fee of $25 for Rise and Bank Wire and $5 for "
    "Crypto'; the challenge fee refunded in full 'with your 4th successful payout' on the same account", model="pending one working "
    "day and one hour, trading on; 2.5% of every payout, at least $5; $50 after the split and the fee; the fee with the 4th payout "
    "(version 9: no fee, a quarter of the refund with each of the first four payouts, paid within the hour)", read=D12),
 ("Hola Prime", "trade ideas"): dict(read=D12, source="https://holaprime.com/forex/forex-trading-rules/"),
 ("Hola Prime", "risk per trade"): dict(rule="Sim. Funded: a stop-loss on every trade; the risk of a trade idea at most 2% of the initial "
    "balance (positions overlapping in time, or a same-direction re-entry within 10 minutes, are one idea)", read=D12),
 ("Hola Prime", "prohibited practices"): dict(rule="gambling or speculative trading (excessive or concentrated risk, unexplained deviations "
    "in position size), one-sided betting (repeated positions in one direction without analysis), grid trading, excessive margin, "
    "account rolling, hedging across accounts, copying beyond the permitted master and copier", read=D12,
    source="https://holaprime.com/trading-rules-list/trading-rules-prohibited-trading-practices"),
 ("Hola Prime", "allocation"): dict(rule="up to two $100K (or four $50K, or one $200K) Sim. Funded and Direct accounts; $800,000 forex and "
    "futures combined", read=D12, source="https://holaprime.com/forex/forex-trading-rules/"),
 ("Hola Prime", "copying"): dict(rule="only between your own Hola Prime accounts (funded: one master and one copier); copying from accounts "
    "at other prop firms prohibited (accounts bought from 15 September 2026)", read=D12,
    source="https://holaprime.com/trading-rules-list/trading-rules-prohibited-trading-practices"),
 ("Hola Prime", FS): dict(rule="$599 for the 100K 2-Step Prime (MyFXBook's listing; other listings $569; the firm's checkout does not render "
    "as text), monthly 95% at +20%; the fee refunded in full with the 4th successful payout; bi-weekly 80%", model="$599, the higher "
    "listing; the fee with the 4th payout", status="cautious", read=D12, basis="secondary"),
 ("Alpha Capital", "targets and limits"): dict(read=D12, basis="page"),
 ("Alpha Capital", "duration rule"): dict(read=D12),
 ("Alpha Capital", "risk per trade"): dict(rule="qualified accounts bought from 21 July 2026: the open loss on one asset at most 2% at 100K "
    "and 200K (3% up to 25K), losing positions on the asset combined, and a same-direction re-entry within 10 minutes combined with the "
    "trade before it (the Max Risk Rule)", model="risk at most 1.75% plus cost; one position at a time; more than 10 minutes between "
    "trades", read=D12, source="https://help.alphacapitalgroup.uk/en/articles/15888623-what-is-the-max-risk-rule-and-how-does-it-work"),
 ("Alpha Capital", "prohibited practices"): dict(rule="'all or nothing' strategies (a significant change in lot size against the account's "
    "average, unusual trade durations, trades opened just before and closed just after the news window); minimal lots to complete "
    "trading days on qualified accounts; position spamming", model=PLANB + "; no filler trades and no last trade to the floor at "
    "Alpha Capital (5.4: an account whose room falls below the smallest normal risk is not traded further and is closed on request; version 9 placed that trade)",
    read=D12,
    source="https://help.alphacapitalgroup.uk/en/articles/7060909-what-is-alpha-capital-group-s-policy-against-gambling-in-trading"),
 ("Alpha Capital", "copying"): dict(read=D12, source="https://help.alphacapitalgroup.uk/en/articles/8786973-is-copy-trading-allowed"),
 ("Alpha Capital", FS): dict(rule="$497 for 100K, $997 for 200K (secondary listings); 'All our evaluation plans are non-refundable' (help "
    "centre, 6 July 2026); 80% (90% with an add-on)", model="no refund", status="modelled", read=D12,
    source="https://help.alphacapitalgroup.uk/en/articles/8420592-is-it-possible-to-receive-a-refund-for-the-evaluation-fees-once-i-have-completed-my-evaluation"),
 ("GFT", "targets and limits"): dict(read=D12),
 ("GFT", "Goat Guard (funded)"): dict(rule="a combined floating loss of 2% of the initial size: the first time the split falls to 50% and "
    "the positions stay open, the second time the account is breached", model="not reached: one position at a time whose stop loss "
    "plus cost (at most $1,750 plus cost per $100K) stays inside 2% of the initial size; the plan holds no position through a gap",
    read=D12),
 ("GFT", "allocation"): dict(model="the recommended plan holds one; at the full allowance four 100K or two 200K, whichever is worth more in all (copying between a trader's own GFT accounts is allowed: the copying row)", read=D12, source="https://help.goatfundedtrader.com/en/articles/10742191-what-is-the-maximum-simulated-capital-you-can-have-with-goatfundedtrader"),
 ("GFT", "copying"): dict(rule="copying trades between your own accounts allowed, evaluation and funded alike; other traders', signal "
    "providers' and third-party services' trades prohibited", model="the shared direction on every GFT account (version 9 read duplicated "
    "trades between GFT accounts as forbidden and held one account at the full allowance)", status="plan", read=D12,
    source="https://help.goatfundedtrader.com/en/articles/10742118-what-are-prohibited-trading-practices"),
 ("GFT", FS): dict(rule="$628 for 100K, $1,198 for 200K at list price (GFT's pricing table, raised on 3 August 2026; version 9 recorded "
    "$524 and $974); the fee is called 'refundable' on GFT's how-it-works page, but neither its 2-Step Standard page (updated 5 October "
    "2026) nor its rewards page (9 October 2026) says when, and third-party descriptions conflict (the first, third or fourth payout, "
    "or after passing); 80% split", read=D12, source="https://www.goatfundedtrader.com/model"),
 ("FunderPro", "targets and limits"): dict(rule="10% / 5%; daily 5%, computed on the balance at 5 pm New York (base not settled: the "
    "stricter of the initial and the day's balance); 10% static; 4 trading days per phase", read=D12, source="https://funderpro.com/"),
 ("FunderPro", "payouts"): dict(rule="every 14 days (Classic) with at least $100 of profit on the funded account; the fee credited within 7 "
    "days of the first reward", model="every 14 days; $100 of profit before the split, $80 of share after it; the fee with the first "
    "payout", read=D12),
 ("FunderPro", "margin"): dict(read=D12),
 ("FunderPro", "allocation"): dict(model="one account; at the full allowance two 100K or one 200K, whichever is worth more in all", read=D12, source="https://support.funderpro.com/en/articles/377857-what-is-the-maximum-trading-capital-i-can-access-with-funderpro"),
 ("FunderPro", "copying"): dict(rule="copying allowed between your own accounts; between different people prohibited", model="the shared "
    "direction on every FunderPro account (version 9 read 'no replicating trades across FunderPro accounts')", read=D12,
    source="https://support.funderpro.com/en/articles/378022-is-copy-trading-allowed"),
 ("FunderPro", FS): dict(rule="$539 for 100K (funderpro.com: 'will be processed with 1st reward'), $989 for 200K (version 9 reading); "
    "80%", read=D12),
 ("BrightFunded", "copying"): dict(rule="allowed between your own accounts, at BrightFunded and at other firms or brokers; opposite "
    "positions across accounts prohibited", read=D12, basis="snippet",
    source="https://help.brightfunded.com/en/articles/9241709-is-copy-trading-allowed"),
 ("BrightFunded", FS): dict(rule="EUR 497 for 100K ($559.42 at 1.1256), EUR 997 for 200K ($1,122.22) (2-Step Classic page); refund only with "
    "a paid add-on; payout ratio 'up to 90%', 90% being a paid add-on (80% without it, version 9's reading); a 15% evaluation profit "
    "reward ($2,250 at 100K) added to the next funded account after 10% growth", model="80%, no refund (no add-on is bought); the "
    "evaluation profit reward left out", read=D12, source="https://brightfunded.com/2-step-classic"),
 ("Blue Guardian", "prohibited practices"): dict(read=D12, basis="snippet"),
 ("Blue Guardian", "copying"): dict(rule="allowed between your own accounts (evaluation, funded and external)", read=D12, basis="snippet"),
 ("Blue Guardian", FS): dict(rule="$463 for 100K, $930 for 200K at list price (the 2 Step Standard product list on blueguardian.com; a code "
    "takes 35% off); refunded after the fourth payout; 85% (90% with an add-on)", model="$463 and $930 (version 9: $579 and $1,162)",
    read=D12, source="https://blueguardian.com/"),
 ("Maven", "allocation"): dict(rule="up to $200,000 of starting capital on funded accounts", model="one 100K (the largest 2-Step size) in "
    "every portfolio: a second account would share the trader's $10,000 per 30 days (the withdrawal cap row), which the engine does "
    "not model across accounts", read=D12),
 ("Maven", FS): dict(rule="$440 for 100K (the largest 2-Step size; $396 with a coupon); refunded with the third withdrawal; 80%", read=D12,
    source="https://maventrading.com/"),
 ("Topstep", FS): dict(read=D12, basis="secondary"),
 ("FundedNext", "monitored as gambling"): dict(read=D12, source="https://help.fundednext.com/en/articles/8020351-what-are-the-restricted-prohibited-trading-strategies"),
 ("every firm", "conflicting positions"): dict(read=D12, source="the firms' prohibited-practice pages read on 12 October 2026 (rows above)"),
 ("every firm", "identity"): dict(read=D12, source="the firms' prohibited-practice and copying pages read on 12 October 2026 (rows above)"),
 ("Apex", FS): dict(rule="$490 at list price (a guide of August 2026; the firm's checkout does not render as text); public codes of 80-90% "
    "off for most of 2026 (about $55); $99 activation when passed (EOD); 100% split", read=D12, basis="secondary"),
 ("The5ers", "prohibited practices"): dict(rule="bulk trading (several trades open at once, 'clearly showing a trader is not behind the "
    "strategy'); 'Trade coordination or copy trading with other traders or accounts'; one-sided bets ('consistently takes positions in "
    "one single direction'); tick scalping; hedge and reverse arbitrage; coordinated trading across firms for manipulative purposes "
    "(opposite positions); strategies that 'artificially distribute profit across multiple days without proportionally distributing "
    "market risk' (opposing positions, or one trade idea partly closed across days); 'position sizes or a number of positions that are substantially "
    "larger or smaller than your typical trading activity, whether compared across your own accounts or between your evaluation and "
    "funded account stages'; overleveraging, concentrated speculative exposure and gambling-like positions; no order executed 2 "
    "minutes either side of high-impact news", model=PLANB + "; one position per account at a time; the direction follows the "
    "trend rule, so it changes with the market; the same risk share and stop rule in both stages; flat around releases; flat every "
    "evening, so each day's profit comes from that day's own trades at the full risk (no position held, split or hedged across days: the "
    "40% day cap ends a day's trading, it does not move profit to another day). The optional "
    "portfolio with The5ers' small accounts holds positions far smaller in dollars than the 100K account's (the same share of each "
    "account): whether The5ers compares sizes in proportion to the account is not stated, so that portfolio is not recommended",
    read=D12, source="https://the5ers.com/faqs/prohibited-trading-practices/"),
 ("The5ers", "copying"): dict(rule="the prohibited-practices page (12 October 2026) prohibits 'Trade coordination or copy trading with other "
    "traders or accounts' (its example: a group of traders sharing signals) and third-party EAs whose trades others hold; "
    "descriptions of The5ers' FAQ (secondary: its help centre refuses automated reading) allow copying between your own High Stakes "
    "accounts and from your own external accounts", model="the plan's own entries on each account, in the shared Nasdaq direction "
    "(no copier), read as your own trading, which the FAQ's descriptions allow; confirmed with The5ers in writing before trading "
    "(Part IV)", read=D12, source="https://the5ers.com/faqs/prohibited-trading-practices/"),
 ("FXIFY", "prohibited practices"): dict(rule="high-frequency trading; reverse and group hedging (offsetting positions across accounts); "
    "account management and accounts under other names; latency arbitrage; order-book spamming; herd trading and collusion "
    "(coordinated trading among users; one provider's EA); exploiting errors; high-leverage news trading; statistical arbitrage "
    "('high-risk trades based on statistical models, aiming for significant wins to offset losses from multiple accounts'); the terms "
    "(section 5.4) add one-sided bets, overleveraging, overexposure and account rolling", model=PLANB + "; flat around high-impact "
    "releases; every account in the same direction at a moderate risk, so no account's loss is offset by another account's opposite "
    "bet", read=D12, source="https://fxify.com/faqs/all-faqs/what-strategies-can-i-use/"),
 ("FundingPips", "copying"): dict(rule="copying between your own FundingPips accounts allowed; copier services and other people's trades "
    "prohibited; to an external account only with the FundingPips account as the master (descriptions of the help centre, which "
    "refuses automated reading)", model="the plan's own entries on each account (no copier)", read=D12, basis="secondary",
    source="https://help.fundingpips.com/"),
 ("Topstep", "targets and limits"): dict(rule="$3,000 target at 50K; Maximum Loss Limit $2,000, trailing the end-of-day balance (monitored in "
    "real time, unrealized P&L included) and locking at the starting balance; the Express Funded Account starts at $0 with the limit "
    "at -$2,000, locking at $0; after the first payout the limit is $0", read=D12,
    source="https://help.topstep.com/en/articles/8284204"),
 ("Topstep", "consistency (Combine)"): dict(rule="the best day at most 55% of the total profit, a hard limit; above it the target becomes the "
    "best day divided by 0.55 ('Best Day Recommendation' under $1,650 at 50K)", read=D12,
    source="https://help.topstep.com/en/articles/8284208"),
 ("Topstep", "allocation"): dict(rule="up to 5 active Express Funded Accounts (sizes may be mixed); a Combine passed at the limit waits until "
    "one closes", read=D12, source="https://help.topstep.com/en/articles/8284215"),
 ("Apex", "targets and limits"): dict(rule="EOD 50K: $3,000 target, $2,000 maximum drawdown trailing the end-of-day balance, $1,000 daily loss "
    "limit (reviews of August 2026: Apex's site refuses automated reading); the trail's stop at the starting balance plus $100 once "
    "funded and the flat time of 4:59 pm ET are version 9's readings, not found again", read=D12, basis="secondary"),
 ("Apex", "allocation"): dict(rule="up to 20 Performance Accounts per trader (reviews of August 2026, consistent; Apex's site refuses automated "
    "reading)", read=D12, basis="secondary"),
 ("FunderPro", "risk per trade"): dict(rule="a 2% risk rule is published for the Instant program ('[Instant] Risk Management Rules (2% Rule & "
    "Gambling Policy)'); the Classic pages read state no per-trade limit (secondary descriptions differ)", model="1.75% plus cost, "
    "within 2% either way", read=D12, source="https://support.funderpro.com/en/collections/879028-funded-accounts"),
}
for x in R:
    key = (x["firm"], x["area"])
    if key in REREAD: x.update(REREAD.pop(key))
assert not REREAD, sorted(REREAD)              # every update names a row that exists

if __name__ == "__main__":
    out = dict(read="11-12 October 2026", note=__doc__.strip(), rules=R,
               counts={s: sum(x["status"] == s for x in R) for s in ("modelled", "plan", "cautious", "assumption", "not binding")})
    json.dump(out, open("rules_inventory_v10.json", "w"), indent=1)
    print(len(R), "rules;", out["counts"])
