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
Read: 11-12 October 2026 unless stated (version 8 and 9 readings, 4-5 October 2026, are marked).
"""
import json

R = []
def r(firm, area, rule, model, status, source, basis="page", read="11 Oct 2026"):
    R.append(dict(firm=firm, area=area, rule=rule, model=model, status=status, source=source, basis=basis, read=read))

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
r("The5ers", "inactivity", "30 days (evaluation), 60 days (funded)", "never 25 days without a trade", "plan",
  U + "what-are-the-general-rules-for-the-high-stakes-program/")

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
r("Fintokei", "open risk", "open risk per setup at most 3%", "1.5% per trade", "not binding", "https://www.fintokei.com/protrader/", basis="snippet")

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
  "before a request; paid within 2 business days; the account locked until the balance is reset; at least $100 of profit "
  "(version 8 reading; not stated on the page read on 11 October); a 'performance fee bonus' added on the 4th successful "
  "withdrawal (amount not stated); no payout fee stated", "locked 2 working days; $100 applied to the trader's share; the bonus "
  "not modelled (the cautious side)", "modelled", U + "6933755-how-do-i-get-paid-performance-fees")
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

# ---------------------------------------------------------------- FunderPro Classic
U = "https://support.funderpro.com/en/articles/"
r("FunderPro", "targets and limits", "10% / 5%; daily 5% (base not settled: the stricter of initial and daily balance); 10%; "
  "4 days per phase", "as stated (dll min)", "modelled", U + "412020", read="4 Oct 2026")
r("FunderPro", "payouts", "every 14 days with at least $100 profit; processed within one working day of approval",
  "pending 1 working day, cash 1 later", "modelled", U + "419844", read="4 Oct 2026")
r("FunderPro", "margin", "funded accounts: at most 20% of the starting balance as margin per asset class", "stop floor in the search",
  "modelled", U + "421458", read="4 Oct 2026")
r("FunderPro", "news (funded)", "no entry within 2 minutes of a high-impact release without the Swing add-on; challenges free",
  "flat around releases (funded)", "plan", "https://funderpro.com/terms-conditions/", basis="snippet")

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
r("BrightFunded", "allocation", "$400,000 funded per trader; evaluations unlimited", "four 100K accounts", "modelled",
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
r("Blue Guardian", "allocation", "$400,000 across funded accounts", "four 100K accounts", "modelled",
  "https://blueguardian.com/blogs/complete-scaling-path-for-funded-traders", basis="page")

# ---------------------------------------------------------------- Maven 2-Step
U = "https://maventrading.com/faqs"
r("Maven", "targets and limits", "8% / 5%; daily 4% of the higher of equity and balance at 00:00 UTC; 8% static; 3 profitable "
  "days (+0.5%) per phase and per withdrawal", "as stated", "modelled", U)
r("Maven", "payouts", "every 10 business days after the first trade; $10,000 per rolling 30 days per trader; above $5,000 of "
  "profit the best day or trade at most 50% of profit; refund with the third withdrawal; processing time not stated",
  "funded profit kept at most $4,900 in every payout cycle ('total profit' read as the cycle's profit: the FAQ's sentence ends "
  "'in the funded stage payout cycle'; if it meant the account's lifetime profit, from the second cycle a cycle's profit would "
  "be cut to twice its best day, which the model does not apply); closed profit in any 30 days at most $10,000; requests every "
  "14 calendar days (10 business days; public holidays not modelled); pending 3 working days (assumed)", "cautious", U,
  read="12 Oct 2026")
r("Maven", "gambling", "large bets at a reward:risk of 1:1.25 or lower", "every position's take-profit at least 1.5 times as far "
  "as its stop, checked on the position actually placed", "plan", U)
r("Maven", "news", "no opening or closing 2 minutes either side of a red-folder release, take-profits included; evaluations and "
  "funded", "flat around releases at every stage", "plan", U)
r("Maven", "risk interview", "above $5,000 of payouts a risk interview; risking more than the amount stated in its email breaches",
  "not modelled: the plan's risk (1.75%) must be checked against the email's figure", "assumption", U)

# ---------------------------------------------------------------- Topstep 50K
U = "https://help.topstep.com/en/articles/8284233-topstep-payout-policy"
r("Topstep", "payouts", "Standard path: 5 winning days of $150+ net (days lock at 4 pm CT); positive net profit since the last "
  "payout; at most 50% of the balance up to $2,000 per request; minimum $125; 90%; the request's session does not count toward "
  "the next five; requests Sunday 5 pm to Friday 5 pm CT; deducted at once, trading may continue, a deducted payout is "
  "protected from a later breach", "as stated; requests one minute after the 4 pm CT lock; $125 read after the split",
  "modelled", U)
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
PLANB = "the plan's policies: no trade and no day above 40% of a target, risk at most 1.75% plus cost (FTMO 1.5%), margin at most 60%, every account traded the same way, no account sacrificed; the firm's judgement is not modelled"
r("FTMO", "prohibited practices", "overleveraging, overexposure, one-sided bets and account rolling (none defined on the page); simulated trades for manipulative purposes, including opposite positions across connected accounts or accounts with other providers; gap trading; exploiting platform errors", PLANB, "plan",
  "https://ftmo.oanda.com/forbidden-trading-practices/", read="12 Oct 2026")
r("FundingPips", "profit concentration", "evaluations bought from 27 June 2026, $25K and up: if one trade idea makes more than 60% of a phase target, the funded account needs 4 profitable days (+0.5%) before every reward request, permanently",
  "not reached: no trade and no day above 40% of a target", "not binding", "https://help.fundingpips.com/hc/en-us/articles/48174287980177-Risk-Per-Trade-Idea", read=V9b)
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
r("every firm", "minimum payouts", "FTMO $20 (bank transfer); FundingPips 1% of the account; FXIFY $50; Fintokei 100 in the "
  "account's currency; GFT $100; FunderPro $100 of profit; Blue Guardian $100; Alpha Capital $100 of profit (version 8 reading; "
  "not stated on the page read on 11 October); The5ers $150 after the split; Topstep $125; Apex $500; FundedNext $20 ('a reward "
  "under $20 cannot be requested', 29 September 2026); Hola Prime, BrightFunded and Maven state none on the pages read", "each applied to the trader's share after the split, the stricter "
  "reading where a page does not say (and stricter than a minimum stated as profit), and as profit before the split; none "
  "where none is stated (version 10: version 9 had no FTMO minimum)", "cautious", "the firms' payout pages (rows above)")

r("every firm", "payout fees", "firm fees on every payout: GFT 3% after the split (rewards page, 9 October 2026), The5ers 3.5% per "
  "cash withdrawal (24 August 2026), FundedNext up to 3.5% on every request (29 September 2026), Blue Guardian 3% (31 August "
  "2026); stated as none: FXIFY (its blog), BrightFunded ('no additional fees'; banks or networks may take $5-$50), FTMO (bank "
  "and network costs only), Fintokei (the firm covers withdrawal fees, except 2.5% plus EUR 10-20 on crypto), Hola Prime (bank "
  "wire and crypto; $25 by Rise); not stated on the pages read: FundingPips (crypto rewards carry service, exchange and network "
  "charges; Rise and bank from $500), Alpha Capital, FunderPro, Maven ($20 by Rise; bank transfer where available), Topstep "
  "($30 by ACH or wire; Wise and Aeropay free), Apex (a third-party claim of 15% on the first payout and 4% after, not found "
  "on its pages)", "the four firm fees are modelled on every withdrawal, the refund included, with minimums checked after "
  "them; where a firm offers a method without a charge the plan uses it, and method costs (banks, networks, currency "
  "conversion) are not modelled", "cautious", "the firms' payout pages (rows above)", read="12 Oct 2026")

# ---------------------------------------------------------------- every firm
r("every firm", "conflicting positions", "no hedging across accounts or firms", "one direction per market group across all "
  "accounts (shared-direction rule)", "plan", "the firms' prohibited-practice pages", read="4 Oct 2026")
r("every firm", "identity", "accounts only in the trader's own name", "one person's accounts", "plan", "the firms' terms", read="4 Oct 2026")
r("every firm with minimum trading days", "minimal trades", "FTMO, FXIFY, FundedNext, FunderPro, BrightFunded (a trade open 60 "
  "seconds), Topstep and Apex count a day on which a position is opened and state no minimum volume", "a missing day after the "
  "target is completed with one minimal position (0.01 lot or one micro contract) held 3 minutes; that the firms accept it is an "
  "assumption (Fintokei and Alpha Capital object to such trades and get none); the plan is also measured without fillers",
  "assumption", "the firms' trading-day definitions (programme rows above)", read="4 Oct 2026 (version 9 reading)")

if __name__ == "__main__":
    out = dict(read="11-12 October 2026 (rows marked otherwise: 4-5 October 2026)", note=__doc__.strip(), rules=R,
               counts={s: sum(x["status"] == s for x in R) for s in ("modelled", "plan", "cautious", "assumption", "not binding")})
    json.dump(out, open("rules_inventory_v10.json", "w"), indent=1)
    print(len(R), "rules;", out["counts"])
