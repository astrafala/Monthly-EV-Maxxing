"""
Programme sheets for the version 6 document: the written rules of every programme in the plan (as checked on
4 October 2026), what each firm allows per person, and how the plan meets each rule. Numbers that come from the
simulations are filled in by build_math_v6.py; everything here is a statement about the firm's own terms.
"""

P = {}

P["FTMO 2-Step"] = dict(
    firm="FTMO", tier="A", title="FTMO 2-Step Challenge",
    rules=[
        ("Fee", "&euro;540 for 100K (about $632), &euro;1,080 for 200K; refunded with the first reward"),
        ("Phase 1 / phase 2 target", "10% / 5% of the initial balance"),
        ("Maximum daily loss", "5% of the initial balance, measured from the balance at 00:00 CE(S)T"),
        ("Maximum loss", "10% of the initial balance, static"),
        ("Minimum trading days", "4 per phase (a day with at least one position opened)"),
        ("Funded split and payouts", "80% (90% after scaling); first reward 14 days after the first trade, then every 14 days; no minimum"),
        ("Consistency rule", "none on the 2-Step (the 1-Step has a 50% best-day rule)"),
        ("Leverage", "1:50 on indices (Normal account)"),
        ("News and weekends", "funded Standard account: no new orders 2 minutes around restricted news; no weekend holding"),
        ("Per person", "$400,000 per trader or strategy across all accounts, evaluations included; the same strategy may run on several accounts within the cap"),
        ("Prohibited", "gambling (no plan, all-in), account rolling, opposite positions across accounts or providers, gap trading, latency arbitrage"),
    ],
    plan=["Nasdaq 100 CFD, one position per account, shared direction with every other Nasdaq account",
          "1.5% risk (inside FTMO's stated 1&ndash;1.5% guidance) with the stop attached at entry",
          "minimum days filled with one minimal trade per day after the target, where needed",
          "flat at weekends and 10 minutes before high-impact news on funded accounts",
          "every account traded the same way; none abandoned or sacrificed (no account rolling)"],
    sources="ftmo.com (trading objectives; FAQ on accounts and the $400,000 cap; forbidden practices); propfirmmatch.com (FTMO leverage)",
)

P["FundingPips Flex"] = dict(
    firm="FundingPips", tier="A", title="FundingPips 2-Step Flex",
    rules=[
        ("Fee", "$499 for 100K (largest size); no registration-fee refund on Flex"),
        ("Phase 1 / phase 2 target", "10% / 6%"),
        ("Maximum daily loss / maximum loss", "4% / 12% static"),
        ("Minimum days", "85% option: 1 trading day (accounts from 26 August 2026); 95% option: 3 profitable days (+0.5%) in each phase"),
        ("Funded split and payouts", "85% or 95%, chosen at purchase; every 14 days; the 95% option needs 3 profitable days in every reward cycle"),
        ("Risk per trade idea", "at most 2% above $25K; a trade idea is all positions on one market in one direction, including one opened within 10 minutes of closing a loss; a breach closes the account"),
        ("Profit Concentration Policy", "evaluations from 27 June 2026, $25K and up: if one trade idea makes more than 60% of a phase target, the funded account needs 4 profitable days (+0.5%) before every reward request, permanently"),
        ("Leverage", "1:100 on forex; indices and metals on dynamic leverage falling to 1:5 above 0.5 lots"),
        ("Weekends and news", "weekend holding blocked on Master accounts since 29 January 2026; profits from 5 minutes before to 5 minutes after restricted news may be deducted"),
        ("Per person", "$400,000 across evaluation, funded and Prime accounts"),
        ("Copying", "only between your own FundingPips accounts; no copier services"),
    ],
    plan=["USDJPY, because the Nasdaq position would need 1:7 leverage and FundingPips gives 1:5 at that size",
          "1.5% risk, below the 2% trade-idea limit; at least 10 minutes after any loss before the next trade in the same direction",
          "the Profit Concentration Policy handled as chosen in this chapter",
          "4 &times; 100K Flex (the largest Flex size) fills the $400,000 cap",
          "own program or manual entry on each account; no copier service"],
    sources="proptradingvibes.com (FundingPips rules, updated 16 Sep 2026; account types and leverage); help.fundingpips.com (2 Step Flex; Risk Per Trade Idea); search summaries of the Profit Concentration Policy",
)

P["The5ers High Stakes"] = dict(
    firm="The5ers", tier="A", title="The5ers High Stakes",
    rules=[
        ("Fee", "New (10% / 5%): $491 for 100K; Classic (8% / 5%): $545; smaller sizes $19&ndash;$278"),
        ("Phase 1 / phase 2 target", "New 10% / 5%; Classic 8% / 5%"),
        ("Maximum daily loss / maximum loss", "5% / 10% static"),
        ("Profitable days", "3 per phase (at least +0.5%); may not be manufactured"),
        ("Funded split and payouts", "80% rising with scaling; first payout 14 days after funding, then every 14 days; $150 minimum"),
        ("Fee return", "10% as hub credit after phase 1, 20% after phase 2, 70% with the first payout (the model counts it all at the first payout)"),
        ("Consistency rule", "none"),
        ("Leverage", "1:100 forex; 1:25 metals and indices"),
        ("News", "no new orders from 2 minutes before to 2 minutes after high-impact news"),
        ("Per person", "one 50K or 100K High Stakes account, plus up to 1 &times; 25K, 3 &times; 10K, 3 &times; 5K, 3 &times; 2.5K"),
        ("Copying", "allowed across your own accounts"),
    ],
    plan=["Nasdaq, shared direction", "daily profit target while profitable days are missing (6.4); never tiny trades",
          "news window wider than required", "one 100K account; the small accounts are optional (Chapter [[CH_ALLOC]])"],
    sources="the5ers.com (High Stakes page; payout policy and hub credit FAQ); propfirmbridge.com (High Stakes review, 15 Sep 2026)",
)

P["FXIFY Two Phase Classic"] = dict(
    firm="FXIFY", tier="A", title="FXIFY Two Phase Classic",
    rules=[
        ("Fee", "$549 for 100K (largest Classic size); refunded with the first payout"),
        ("Phase 1 / phase 2 target", "5% / 10%"),
        ("Maximum daily loss / maximum loss", "4% / 10% static"),
        ("Minimum trading days", "4 per phase"),
        ("Funded split and payouts", "80% every 14 days, or 100% every 30 days (chosen at purchase)"),
        ("Consistency rule (funded)", "no day may exceed 25% of the profit of a payout; the benchmark is the account's best day ever and does not reset"),
        ("Leverage", "1:10 on indices; 1:30 forex and metals (1:50 with an add-on)"),
        ("Per person", "one active account of each size, challenge and funded alike (5K, 10K, 15K, 25K, 50K, 100K, 200K, 400K; $805,000 in all, rule of 25 November 2024); Classic goes up to 100K; Classic prices 5K $59, 10K $89, 25K $199, 50K $379, 100K $549"),
        ("Copying", "between your own FXIFY accounts allowed; into FXIFY from external accounts only with approval (30-day statement); third-party copying prohibited"),
    ],
    plan=["Nasdaq with the stop widened to fit 1:10 leverage (USDJPY was searched too and is worth less)",
          "each day's take-profit capped at 25% of the cycle target, so the best-day rule always holds",
          "100% every 30 days (better value than 80% every 14 days in the search)",
          "one Classic account of each size: 100K, 50K, 25K, 10K and 5K (15K has no published Classic price and is left out)",
          "2 Phase Pro is not used: it may not receive copied trades (only be the master), so it would need a market of its own, and its $4,000 daily profit cap is flat at every size"],
    sources="cryptoslate.com (FXIFY review, updated 4 Oct 2026: Classic and Pro prices and rules); fxify.com FAQs (\u201cWhat is the max allocation?\u201d; 2 Phase Pro max allocation; copy trading); search summaries of FXIFY leverage",
)

P["FundedNext Stellar 2-Step"] = dict(
    firm="FundedNext", tier="A", title="FundedNext Stellar 2-Step",
    rules=[
        ("Fee", "$549.99 for 100K; $1,049.99 for 200K (from August 2026); refunded with the first reward"),
        ("Phase 1 / phase 2 target", "8% / 5%"),
        ("Maximum daily loss / maximum loss", "5% / 10%"),
        ("Minimum trading days", "5 per phase"),
        ("Funded split and payouts", "80%; rewards on a 21-day cycle"),
        ("15% challenge reward", "for accounts bought from 12 January 2026, paid only on Scale-Up eligibility (not counted)"),
        ("Consistency rule", "none on Stellar accounts; profit around high-impact news counts at 40% on funded accounts"),
        ("Leverage", "1:100 forex; 1:10 gold (from January 2026); 1:10 indices (from May 2026)"),
        ("Per person", "$300,000 funded; evaluations unlimited"),
        ("Copying", "between your own challenge accounts; never into a funded account"),
        ("Monitored as gambling", "one-sided betting, account rolling, many quick breaches, losses exceeding gains"),
    ],
    plan=["its own market (no other account trades it), with its own direction rule: its trades are never copies",
          "one account at the largest size, 200K (cheaper per dollar), within the $300,000 cap",
          "flat around news, so the 40% news share never applies"],
    sources="help.fundednext.com (Stellar 2-Step, updated 2 Oct 2026; copy trading; prohibited strategies); proptradingvibes.com (Stellar 2-Step; consistency rule); search summaries of FundedNext leverage and 200K price",
)

P["Fintokei ProTrader"] = dict(
    firm="Fintokei", tier="B", title="Fintokei ProTrader",
    rules=[
        ("Fee", "$549 for 100K; $1,249 for 200K; $2,599 for 400K; returned with the first payout as a sign-up bonus"),
        ("Phase 1 / phase 2 target", "8% / 6%"),
        ("Maximum daily loss / maximum loss", "5% of start-of-day equity / 10% static"),
        ("Minimum days", "3 profitable days per phase (the stricter of two published readings)"),
        ("Maximum risk per trade", "3% on open trades (a warning, after which consistency rules can apply)"),
        ("Funded split and payouts", "80%; first request 14 days after the funded account opens, then every 14 days; at least 3% profit; all positions closed at the request"),
        ("Discretionary consistency rules", "if trading is flagged unsustainable: leverage 1:10, daily profit and loss capped at 1%"),
        ("Leverage", "1:100 forex, gold and silver; 1:50 indices"),
        ("Per person", "&euro;500,000 of accounts in total"),
        ("Copying", "your own trades across your own accounts allowed; other people's signals prohibited"),
    ],
    plan=["Nasdaq, shared direction; 5 &times; 100K: $500,000 is about &euro;444,000 at 1.1256, inside the &euro;500,000 cap, and 100K is cheaper per dollar than 200K", "1.5% risk, half the 3% limit",
          "every position closed before a payout request"],
    sources="fintokei.com (ProTrader page); Fintokei ProTrader terms (version 6); support.fintokei.com (consistency rules); propfirmmap.com",
)

P["Hola Prime 2-Step Prime"] = dict(
    firm="Hola Prime", tier="B", title="Hola Prime 2-Step Prime",
    rules=[
        ("Fee", "about $599 for 100K (published $409&ndash;$599 with the payout option); returned 25% with each of the first four payouts"),
        ("Phase 1 / phase 2 target", "8% / 5% (the 200K size has 4% / 8% limits)"),
        ("Maximum daily loss / maximum loss", "5% of the previous day's closing balance / 10% static"),
        ("Minimum trading days", "3 per phase"),
        ("Funded split and payouts", "bi-weekly 80% with 3 profitable days in the cycle; monthly 95% with 7; on-demand 80%"),
        ("Consistency (funded)", "best day at most 40% of the payout's profit"),
        ("Risk (funded)", "stop-loss on every trade; at most 2% risk per trade"),
        ("Leverage", "1:50 forex; 1:10 indices and metals"),
        ("Per person", "$500,000"),
        ("Copying", "only between your own Hola Prime accounts (funded: one master and one copier); copying from accounts at other prop firms prohibited"),
        ("Prohibited", "one-sided betting, grid trading, excessive margin use, hedging across accounts"),
    ],
    plan=["its own market, traded by no other account (so nothing is copied from another firm)",
          "two accounts: one master and one copier, the most Hola Prime allows to share trades",
          "take-profit capped at 40% of the cycle target per day; daily profit target until 3 profitable days"],
    sources="holaprime.com (2-Step Prime FAQ; prohibited trading practices); propfirmmap.com; thetrustedprop.com",
)

P["Alpha Capital Pro 10%"] = dict(
    firm="Alpha Capital", tier="D", title="Alpha Capital Alpha Pro 10%",
    rules=[
        ("Fee", "$497 for 100K; $997 for 200K; refund policy reported inconsistently (assumed none)"),
        ("Phase 1 / phase 2 target", "10% / 5%"),
        ("Maximum daily loss / maximum loss", "5% (balance) / 10% static"),
        ("Minimum trading days", "3 per phase"),
        ("Funded split and payouts", "80%; bi-weekly from 14 days after the first funded trade (first request after 5 trading days); or on demand with a 40% best-day rule and 2% minimum"),
        ("Risk", "never risk or lose 2% or more on one trade or group of trades closed together"),
        ("Leverage", "1:100 forex; 1:20 indices; 1:30 metals"),
        ("Per person", "$400,000 per household; $300,000 per strategy"),
        ("Copying", "from your own external accounts with proof of ownership"),
    ],
    plan=["Nasdaq, 1.5% risk (well below 2%)", "bi-weekly payouts (no best-day rule)", "one account in the recommended plan"],
    sources="alphacapitalgroup.uk; tradetanto.com; quantvps.com (Alpha payout rules); trustpilot.com (rating withheld)",
)

P["FunderPro Classic"] = dict(
    firm="FunderPro", tier="D", title="FunderPro Classic",
    rules=[
        ("Fee", "$539 for 100K list (often 20% off); $989 for 200K; refunded with the first reward"),
        ("Phase 1 / phase 2 target", "10% / 5%"),
        ("Maximum daily loss / maximum loss", "5% / 10% static"),
        ("Minimum days", "none"),
        ("Funded split and payouts", "80% bi-weekly"),
        ("Consistency rule", "none on Classic"),
        ("Risk per trade", "at most 2%"),
        ("Leverage", "1:100 forex; 1:30 indices and metals"),
        ("Per person", "$200,000"),
        ("Copying", "no replicating trades across FunderPro accounts; no copying from accounts you do not own"),
    ],
    plan=["one account at 200K (the cap), Nasdaq", "1.5% risk, below the 2% limit"],
    sources="support.funderpro.com (leverage; consistency rule); tradelocker.com hub (prices); trustpilot.com (rating withheld)",
)

P["GFT 2-Step Standard"] = dict(
    firm="GFT", tier="D", title="Goat Funded Trader 2-Step Standard",
    rules=[
        ("Fee", "$524 for 100K; $974 for 200K; refundable"),
        ("Phase 1 / phase 2 target", "8% / 5%"),
        ("Maximum daily loss / maximum loss", "5% / 10% static"),
        ("Minimum trading days", "3 per phase"),
        ("Funded split and payouts", "80% every 14 days; first payout needs 3% profit; the first two payouts at most 6% of the account or $10,000; no open positions at a request"),
        ("Daily profit cap (funded)", "$3,000 a day on 100K; profit above it is deducted"),
        ("Consistency rule", "none"),
        ("Leverage", "1:50 forex; 1:15 indices; 1:20 metals"),
        ("Per person", "$400,000 funded"),
        ("Copying", "no duplicated trades or trade ideas between GFT accounts"),
    ],
    plan=["one account, Nasdaq", "take-profit capped at the day's remaining profit cap", "first two cycles at 6%"],
    sources="help.goatfundedtrader.com (2-Step Standard); cryptoslate.com; tradelocker.com hub (prices); trustpilot.com (rating withheld)",
)

P["BrightFunded 2-Step Classic"] = dict(
    firm="BrightFunded", tier="D", title="BrightFunded 2-Step Classic",
    rules=[
        ("Fee", "&euro;497 for 100K (about $580); &euro;997 for 200K; refund only with the paid refund add-on"),
        ("Phase 1 / phase 2 target", "10% / 5%"),
        ("Maximum daily loss / maximum loss", "5% / 10% static"),
        ("Minimum trading days", "5 per phase"),
        ("Funded split and payouts", "80%; first payout about 30 days after funding, then every 14 days"),
        ("Consistency rule", "none"),
        ("Leverage", "1:100 forex; 1:20 indices; 1:40 gold"),
        ("Per person", "$400,000 funded; evaluations unlimited"),
        ("Copying", "allowed between your own accounts at any firm; trades must last at least 60 seconds"),
    ],
    plan=["one account, Nasdaq", "trades last hours, far above 60 seconds"],
    sources="tradetanto.com; proptradingvibes.com (BrightFunded leverage); help.brightfunded.com (refund); trustpilot.com (rating withheld)",
)

P["Blue Guardian 2-Step"] = dict(
    firm="Blue Guardian", tier="D", title="Blue Guardian 2-Step Standard",
    rules=[
        ("Fee", "$579 for 100K list (often half price with a code); $1,162 for 200K; refunded after the fourth payout"),
        ("Phase 1 / phase 2 target", "8% / 4%"),
        ("Maximum daily loss / maximum loss", "4% / 8% static"),
        ("Minimum days", "3 profitable days per phase"),
        ("Funded split and payouts", "85% every 14 days"),
        ("Guardian Shield (funded)", "all trades closed at a 2% open loss; first time the split falls to 50%, second time the account closes"),
        ("Leverage", "1:10 on indices"),
        ("Per person", "$400,000; evaluations up to $200,000 each"),
        ("Copying", "your own accounts only"),
    ],
    plan=["one account, Nasdaq with the stop widened to fit 1:10", "1.5% risk: a stop-out stays below the 2% shield unless the price gaps"],
    sources="help.blueguardian.com (2 Step Standard rules); propfirmbridge.com; trustpilot.com (rating withheld)",
)

P["Maven 2-Step"] = dict(
    firm="Maven", tier="D", title="Maven 2-Step",
    rules=[
        ("Fee", "$440 for 100K (largest 2-Step size); refunded with the third payout"),
        ("Phase 1 / phase 2 target", "8% / 5%"),
        ("Maximum daily loss / maximum loss", "4% (from the higher of balance or equity) / 8% static"),
        ("Profitable days", "3 per phase, each at least +0.5%"),
        ("Funded split and payouts", "80%, about every 10 business days; at most $10,000 of payouts per 30 days per person; after $5,000 paid, no day above 50% of a payout's profit"),
        ("Leverage", "1:75 forex; 1:20 indices and commodities"),
        ("Per person", "$200,000"),
    ],
    plan=["one 100K account, Nasdaq", "daily take-profit capped at 50% of the cycle target", "cycles of 8% or less, inside the $10,000 per 30 days cap"],
    sources="propfirmsradar.com; thepropfirmguide.com; lunefi.com (Maven rules); trustpilot.com (rating withheld)",
)

P["Topstep 50K"] = dict(
    firm="Topstep", tier="A", title="Topstep 50K Trading Combine (futures, optional)",
    rules=[
        ("Fee", "$49 a month (Standard path); a reset after a breach $49; $149 activation per Express Funded Account"),
        ("Target / maximum loss", "$3,000 / $2,000 trailing at the end of each day, locking at the start balance"),
        ("Consistency (Combine)", "best day at most 55% of the profit target (the model uses 50%)"),
        ("Funded payouts", "after 5 winning days of $150+; at most 50% of the balance and $2,000 a request; 90%"),
        ("Per person", "up to 5 Express Funded Accounts at once"),
        ("Trading hours", "flat by the daily close (the plan: by 20:00 UTC)"),
    ],
    plan=["micro Nasdaq futures, shared direction with the Nasdaq CFD accounts", "risk and \\(k\\) searched (no percentage rule applies)"],
    sources="help.topstep.com (pricing); proptradingvibes.com (Combine rules, Sep 2026)",
)

P["Apex 50K EOD"] = dict(
    firm="Apex", tier="B", title="Apex 4.0 50K EOD (futures, optional)",
    rules=[
        ("Fee", "$550 list; public 80&ndash;90% codes most of 2026 (about $55); $99 activation when passed"),
        ("Target / maximum loss", "$3,000 / $2,000 trailing end of day; $1,000 daily loss limit; evaluations expire after 30 days"),
        ("Funded payouts", "100% split; 5 qualifying days per request; best day under 50%; $500 minimum; at most 6 payouts, then the account closes; safety net of drawdown + $100"),
        ("Per person", "up to 20 funded accounts; copying between your own accounts allowed"),
        ("Trading hours", "flat by 4:59 pm ET every session"),
    ],
    plan=["micro Nasdaq futures, shared direction", "only at 80&ndash;90% off: at the list price the value is negative"],
    sources="phidiaspropfirm.com (Apex 4.0); apextraderfunding.com help centre; propfirmmap.com (Apex)",
)
