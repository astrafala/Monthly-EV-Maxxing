"""
Programme sheets for the version 10 document: version 6's sheets (progs_v6.py) with every rule the reviews or the official
pages corrected (versions 8 to 10, in order below), the plan's policies in every plan list, and source URLs. Since version
10 each chapter's rule table is built from the rule inventory (rules_inventory_v10.json) and only the fee and leverage rows
of these sheets; the sheets keep the plan lists.
"""
import copy, json
from progs_v6 import P as P6
from firms_v10 import SOURCES as U

P = copy.deepcopy(P6)

def setrule(sheet, label, text, after=None):
    rows = P[sheet]["rules"]
    for i, (a, b) in enumerate(rows):
        if a == label:
            rows[i] = (label, text); return
    if after:
        j = [a for a, b in rows].index(after)
        rows.insert(j + 1, (label, text))
    else:
        rows.append((label, text))

def droprule(sheet, label):
    P[sheet]["rules"] = [(a, b) for a, b in P[sheet]["rules"] if a != label]

COMMON = ["flat every day by 20:00 UTC (no entry from 19:00 UTC), so the account is flat through every daily reset and pays no "
          "overnight financing; flat at weekends",
          "concentration policy: no trade and no day makes more than 40% of the current phase or payout target, so every phase and "
          "every payout takes at least three winning days",
          "risk per trade sized so that the stop loss plus the round-trip cost fits the room under the floor and under the day's "
          "limit; when that room is below a tenth of the normal risk the account is closed (stopped and replaced), never traded "
          "in micro size",
          "minimum and qualifying days completed with trades held at least 2 minutes"]

# ---------------------------------------------------------------- FTMO
setrule("FTMO 2-Step", "Fee", "&euro;540 for 100K ($607.82 at 1.1256), &euro;1,080 for 200K ($1,215.65); refunded with the first reward")
setrule("FTMO 2-Step", "Prohibited", "gambling (no plan, all-in), account rolling, opposite positions across accounts or providers, "
        "gap trading (opening within 2 hours of a market close to profit from the gap), latency arbitrage")
setrule("FTMO 2-Step", "Risk guidance", "FTMO recommends risking 1&ndash;1.5% of the initial balance per trade; larger risk can trigger risk monitoring (a recommendation, not a written rule)")
P["FTMO 2-Step"]["sources"] = f"ftmo.com (trading objectives; FAQ on accounts and the $400,000 cap; forbidden practices); {U['FTMO risk']}; FTMO leverage 1:50 on indices"

# ---------------------------------------------------------------- FundingPips
fp = P["FundingPips Flex"]
fp["title"] = "FundingPips 2-Step Flex"
setrule("FundingPips Flex", "Phase 1 / phase 2 target", "10% / 8%")
setrule("FundingPips Flex", "Minimum days", "80% option: 1 trading day per phase (accounts from 26 August 2026); 95% option: 3 profitable days (at least +0.5%) per phase")
setrule("FundingPips Flex", "Funded split and payouts", "chosen at purchase and locked: 80% with 1 minimum trading day, or 95% with 3 profitable days in every reward cycle; bi-weekly")
setrule("FundingPips Flex", "Maximum daily loss / maximum loss", "4% (of the higher of the opening balance and equity) / 12% static")
setrule("FundingPips Flex", "Weekends and news", "overnight and weekend holding allowed on evaluations; on Master accounts only with the Swing add-on; profits from 5 minutes before to 5 minutes after restricted news may be deducted")
fp["plan"] = ["USDJPY or EURUSD at 1:100 (the Nasdaq would need 1:7 and FundingPips gives 1:5 at that size)",
              "risk at most 1.75%, below the 2% trade-idea limit; at least 10 minutes after any loss before the next trade in the same direction",
              "the 40% concentration policy keeps every trade idea under the Profit Concentration Policy's 60%",
              "4 &times; 100K Flex (the largest Flex size) fills the $400,000 cap", "own entry on each account; no copier service"] + COMMON
fp["sources"] = f"{U['FundingPips']} (2 Step Flex, read 4 Oct 2026); {U['FundingPips PCP']} (Risk Per Trade Idea; Profit Concentration Policy)"

# ---------------------------------------------------------------- The5ers
setrule("The5ers High Stakes", "Fee return", "10% of the fee as hub credit (not cash) after phase 1, 20% after phase 2, 70% added to the funded account and paid with the first payout (at least $150, 14 days after funding); the model keeps the credit apart from cash and spends it on the next The5ers evaluation")
setrule("The5ers High Stakes", "Prohibited", "one-trade target attainment (permanent ban)")
P["The5ers High Stakes"]["plan"] = ["Nasdaq, shared direction", "daily profit target while profitable days are missing; never tiny trades",
                                   "one 100K account; the small accounts are optional"] + COMMON

# ---------------------------------------------------------------- FXIFY
setrule("FXIFY Two Phase Classic", "Prohibited", "gambling and all-or-nothing ('YOLO') trading")
P["FXIFY Two Phase Classic"]["plan"] = ["Nasdaq with the stop widened to fit 1:10 leverage (USDJPY was searched too)",
    "each day's take-profit capped at 25% of the cycle target less $1 per $100K (and 40% per trade), so the best-day rule always holds",
    "one Classic account of each size: 100K, 50K, 25K, 10K and 5K"] + COMMON

# ---------------------------------------------------------------- FundedNext
setrule("FundedNext Stellar 2-Step", "Funded split and payouts", "80%; first reward 21 days after the funded account opens, then every 14 days (the 21-day option); 3-day and on-demand options exist with other conditions")
setrule("FundedNext Stellar 2-Step", "Monitored as gambling", "one-sided betting (remedy: a 1% risk limit), account rolling, breaching several accounts in a short span, losses exceeding gains (remedies: 40% consistency on on-demand rewards or a lower split)")
P["FundedNext Stellar 2-Step"]["plan"] = ["its own market (no other account trades it), with its own direction rule: its trades are never copies",
    "one account at the larger size if it is worth more", "flat around news"] + COMMON
P["FundedNext Stellar 2-Step"]["sources"] = f"{U['FundedNext Stellar']}; help.fundednext.com (copy trading; prohibited strategies)"

# ---------------------------------------------------------------- Fintokei
setrule("Fintokei ProTrader", "Maximum daily loss / maximum loss", "5% of the equity at the start of the day (midnight UTC; it rises with open profit at midnight) / 10% static")
setrule("Fintokei ProTrader", "Prohibited", "reaching a phase target in one or a few identical trades ('all-in'); token trades to complete days")
P["Fintokei ProTrader"]["sources"] = f"{U['Fintokei loss limits']}; {U['Fintokei all-in']}; fintokei.com (ProTrader page and terms)"

# ---------------------------------------------------------------- Hola Prime
setrule("Hola Prime 2-Step Prime", "Prohibited", "one-sided betting, grid trading, excessive margin use, hedging across accounts, profitability materially dependent on concentrated outcomes")

# ---------------------------------------------------------------- Alpha
setrule("Alpha Capital Pro 10%", "Funded split and payouts", "80%; bi-weekly; or on demand with at least 2% gross profit and no day above 40% of the profit (the 40% rule applies to on-demand payouts only)")
setrule("Alpha Capital Pro 10%", "Duration", "the average trade must last more than 2 minutes, and at least half of the profit must come from trades longer than 2 minutes", after="Risk")
setrule("Alpha Capital Pro 10%", "Prohibited", "gambling, 'all or nothing' trading")
P["Alpha Capital Pro 10%"]["sources"] = f"{U['Alpha on-demand']}; {U['Alpha duration']}; alphacapitalgroup.uk"

# ---------------------------------------------------------------- FunderPro
setrule("FunderPro Classic", "Margin (funded)", "at most 20% of the starting balance as margin per asset class (FX, metals, energies, US and EU indices, shares, crypto); first breach: the profit of the breaching trades is removed; second: the account fails. No margin rule on challenges.", after="Risk per trade")
setrule("FunderPro Classic", "Leverage", "1:100 forex; 1:30 indices (Classic and Pro challenges)")
P["FunderPro Classic"]["plan"] = ["one account, the larger size if it is worth more", "risk at most 1.75%, below the 2% limit",
    "stop at least 0.92 hourly standard deviations on the Nasdaq (or USDJPY), so the funded margin stays under 20% of the starting balance"] + COMMON
P["FunderPro Classic"]["sources"] = f"{U['FunderPro margin']}; {U['FunderPro leverage']}; tradelocker.com hub (prices)"

# ---------------------------------------------------------------- GFT
g = "GFT 2-Step Standard"
setrule(g, "Phase 1 / phase 2 target", "10% / 5%")
setrule(g, "Maximum daily loss / maximum loss", "5% of the higher of balance and equity at 5 pm New York / 10% static")
setrule(g, "Minimum trading days", "3 valid days per phase; a day is valid only with at least 0.5% profit")
setrule(g, "Funded split and payouts", "80% every 14 days; 4 valid days (+0.5%) per payout cycle for accounts bought from 25 July 2026; first payout at least 3% profit (the model asks for 3% at every payout, which slightly understates the value); the first two payouts at most 6% of the account or $10,000")
setrule(g, "Daily profit cap (funded)", "$3,000 a day at every account size; profit above it is deducted (not a breach)")
setrule(g, "Leverage", "evaluation 1:20 on indices; funded 1:10 on indices, 1:50 forex")
setrule(g, "Goat Guard (funded)", "a combined floating loss of 2%: the first time the split falls to 50%, the second time the account is breached")
P[g]["plan"] = ["one account; Nasdaq with a stop of at least 0.92 sd (funded 1:10) or USDJPY", "take-profit capped at the day's remaining $3,000",
                "one open position at a time, risking at most 1.75% plus cost: Goat Guard's 2% cannot trigger without an intraday gap"] + COMMON
P[g]["sources"] = f"https://help.goatfundedtrader.com/en/articles/13575169-2-step-standard; {U['GFT rewards']}; {U['GFT Goat Guard']}"

# ---------------------------------------------------------------- BrightFunded
setrule("BrightFunded 2-Step Classic", "Fee", "&euro;497 for 100K ($559.42 at 1.1256); &euro;997 for 200K ($1,122.22); refund only with the paid refund add-on")
setrule("BrightFunded 2-Step Classic", "Copying", "allowed between your own accounts at any firm")
setrule("BrightFunded 2-Step Classic", "Trading days", "a day counts only if at least one trade stays open 60 seconds or more")
P["BrightFunded 2-Step Classic"]["plan"] = ["one account (recommended) or four, Nasdaq",
    "every counted day includes a trade held at least 2 minutes (the plan's trades last hours on average, but a stop can be hit in seconds, so the day's count never relies on it)"] + COMMON
P["BrightFunded 2-Step Classic"]["sources"] = f"{U['BrightFunded evaluation']}; help.brightfunded.com (refund add-on)"

# ---------------------------------------------------------------- Blue Guardian
setrule("Blue Guardian 2-Step", "Maximum daily loss / maximum loss", "4% (of the higher of balance and equity at 5 pm New York) / 8% static")
setrule("Blue Guardian 2-Step", "Prohibited", "margin use above 80% counts as gambling")
P["Blue Guardian 2-Step"]["plan"] = ["one account, Nasdaq with the stop widened to fit 1:10", "risk at most 1.75%: a stop-out stays below the 2% shield unless the price gaps"] + COMMON

# ---------------------------------------------------------------- Maven
m = "Maven 2-Step"
setrule(m, "Funded split and payouts", "80%; a withdrawal every 10 business days; at most $10,000 per rolling 30 days per trader across all accounts (the excess is voided)")
setrule(m, "Consistency (funded)", "the largest winning trade at most 20% of the profit withdrawn")
setrule(m, "Risk interview", "after $5,000 of total profit; a payout is not processed without it")
setrule(m, "News", "no opening or closing within 2 minutes of a red-folder release, in evaluations and funded accounts")
setrule(m, "Gambling", "large bets at a reward:risk of 1:1.25 or lower ('random odds')")
setrule(m, "Refund", "with the third withdrawal")
P[m]["plan"] = ["one 100K account, Nasdaq", "every trade at a reward:risk of at least 1:1.5", "each winning trade capped at 20% of the cycle target",
                "a payout request only when the 30-day window has room for all of it", "the risk interview booked as soon as it is offered"] + COMMON
P[m]["sources"] = f"{U['Maven FAQ']} (read 4 Oct 2026)"

# ---------------------------------------------------------------- futures
setrule("Topstep 50K", "Funded payouts", "after 5 winning days of $150+; at most 50% of the balance and $2,000 a request; 90%; every payout after the first needs net profit since the last; after the first payout the maximum loss level moves to the starting balance")
P["Topstep 50K"]["sources"] = f"{U['Topstep payouts']}; help.topstep.com (pricing)"
setrule("Apex 50K EOD", "Funded payouts", "100% split; 5 qualifying days per request; no day may make 50% or more of the request's profit; $500 minimum; caps $1,500, $1,500, $2,000, $2,500, $2,500, $3,000; at most 6 payouts, then the account closes; safety net of drawdown + $100")
P["Apex 50K EOD"]["sources"] = f"{U['Apex EOD payouts']}; apextraderfunding.com help centre"
for s in ("Topstep 50K", "Apex 50K EOD"):
    P[s]["plan"] = P[s]["plan"] + ["whole micro contracts, risk rounded down, never fewer than one", "no trade and no day above 40% of the evaluation target"]
for s in ("FTMO 2-Step", "Fintokei ProTrader", "Hola Prime 2-Step Prime", "Alpha Capital Pro 10%"):
    P[s]["plan"] = [x for x in P[s]["plan"] if "10 minutes before" not in x] + COMMON

# ================================================================ version 8 (review of version 7; rules re-read 4 October 2026)
import optimize_v10 as _O
def _mmin(firm, instr, rf=0.0175): return _O.m_min(firm, instr, rf)
try:
    _FIN = [r for r in json.load(open("opt_v10_final.json")) if r["tag"] == "chosen" and r["size"] == 100_000]
except FileNotFoundError:
    _FIN = []
def _rf(prog, instr, default=0.0175):
    """the chosen risk per trade of a programme and market, as a share of the account (the plan's ceiling until results exist)"""
    rs = [r for r in _FIN if r["prog"] == prog and r["instr"] == instr]
    return rs[0]["L"] / rs[0]["size"] if rs else default
def _p(x): return f"{x * 100:.2f}".rstrip("0").rstrip(".") + "%"

_OLD_COMMON = list(COMMON)
COMMON[:] = ["flat every day by 20:00 UTC (no entry from 19:00 UTC), so the account is flat through every daily reset and pays no "
             "overnight financing; flat at weekends",
             "concentration policy: no trade and no day makes more than 40% of the current phase or payout target, so every phase takes "
             "at least three winning days",
             "at least 10 minutes between a close and the next entry; no take-profit and no stop closer than 0.6 hourly standard "
             "deviations to the entry, so fewer than 1 trade in 1,000 can close within 2 minutes",
             "risk per trade sized so that the stop loss plus the round-trip cost fits the room under the floor and under the day's "
             "limit; when the room above the floor is below a tenth of the normal risk, one last trade with its stop at the floor: "
             "the account recovers or ends in a breach that frees its allocation",
             "minimum trading days completed, where fillers are allowed, with one minimal trade a day held at least 2 minutes and a "
             "stop of at most $3 per $100K"]

setrule("FTMO 2-Step", "Funded split and payouts", "80% (90% after scaling); first reward on the 14th day after the first trade on the account, then every 14 days; $20 minimum by bank transfer")
P["FTMO 2-Step"]["plan"] = [(f"{_p(_rf('FTMO 2-Step', 'US100', 0.015))} risk (inside FTMO's stated 1&ndash;1.5% guidance) with the stop attached at entry" if "FTMO's stated" in x else x) for x in P["FTMO 2-Step"]["plan"]]
P["FTMO 2-Step"]["sources"] = (f"ftmo.com/en/faq/how-do-i-withdraw-my-profits/ (first reward 14 days after the first trade); ftmo.com/faq/how-many-accounts-can-i-have/ ($400,000 per trader); "
                               f"{U['FTMO risk']}; ftmo.com (trading objectives, forbidden practices)")

setrule("FundingPips Flex", "Maximum daily loss / maximum loss", "4% of the higher of the day's opening balance and equity (relative: $3,760 on a day that opens at $94,000), reset at platform midnight (UTC+3) / 12% static")
setrule("FundingPips Flex", "Funded split and payouts", "chosen at purchase and locked: 80% with 1 minimum trading day, or 95% with 3 profitable days (+0.5% of the starting size) in every reward cycle; every 14 days from the first executed trade on the Master account; minimum reward 1% of the account")
setrule("FundingPips Flex", "Risk per trade idea (Master)", "accounts above $25K: a trade idea (related positions, realised and floating) may not lose 2%; immediate closure")
P["FundingPips Flex"]["plan"] = ["USDJPY or EURUSD at 1:100 (the Nasdaq would need 1:7 and FundingPips gives 1:5 at that size)",
    "risk at most 1.75% plus cost, below the 2% trade-idea limit; at least 10 minutes after any close before the next trade",
    "the 40% concentration policy keeps every trade idea under the Profit Concentration Policy's 60%",
    "4 &times; 100K Flex (the largest Flex size) fills the $400,000 cap", "own entry on each account; no copier service"] + COMMON

setrule("The5ers High Stakes", "Maximum daily loss / maximum loss", "5% of the previous day's closing balance or equity, the higher (relative: the firm's example is $5,500 at $110,000), reset 00:00 server time / 10% of the initial balance, static")
setrule("The5ers High Stakes", "Per person", "Classic: one 2.5K, one 5K, one 10K or 25K, one 50K or 100K; New: three each of 2.5K, 5K and 10K, one 25K, one 50K or 100K; the 50K/100K account is one across both programmes")
P["The5ers High Stakes"]["plan"] = ["Nasdaq, shared direction", "daily profit target while profitable days are missing",
    "one 100K account; optionally New's small accounts (3 &times; 2.5K, 3 &times; 5K, 3 &times; 10K, 1 &times; 25K), each on New's own contract and fee"] + COMMON
P["The5ers High Stakes"]["sources"] = "the5ers.com/faqs/what-is-the-drawdown-rule-for-high-stakes/; the5ers.com/faqs/how-many-high-stakes-accounts-can-i-have/; the5ers.com/high-stakes/"

setrule("FXIFY Two Phase Classic", "Fee", "$549 for 100K (largest Classic size); no refund on Classic (the refund belongs to Two Phase Standard)")
setrule("FXIFY Two Phase Classic", "Maximum daily loss / maximum loss", "4% of the previous day's balance at 5 pm EST (relative) / 10% static")
setrule("FXIFY Two Phase Classic", "Funded split and payouts", "80% every 14 days, or 100% every 30 days (chosen at purchase); minimum payout $50")
P["FXIFY Two Phase Classic"]["sources"] = "intercom.help/fxify/en/articles/12130186-2-phase-account-types (refunds by type); intercom.help/fxify/en/articles/14834680-the-2-phase-classic-account; fxify.com/blog/cheapest-path-funded-50k-fxify/ (refund guide, 14 September 2026)"

setrule("Fintokei ProTrader", "Minimum days", "3 separate trading days (a trade opened on the day, any result) per phase and before every payout request")
setrule("Fintokei ProTrader", "Funded split and payouts", "80%; a request 14 days after the first trade or the last processed payout; minimum $100 (the 3% minimum profit belongs to SwiftTrader); all positions closed at the request")
P["Fintokei ProTrader"]["plan"] = ["Nasdaq, shared direction; 5 &times; 100K: $500,000 is about &euro;444,000 at 1.1256, inside the &euro;500,000 cap, and 100K is cheaper per dollar than 200K",
    f"risk {_p(_rf('Fintokei ProTrader', 'US100'))}, below the 3% limit", "every position closed before a payout request"] + COMMON
P["Fintokei ProTrader"]["sources"] = (f"{U['Fintokei loss limits']}; support.fintokei.com/en/articles/6538884 (withdrawals, minimum amount); "
                                      f"support.fintokei.com/en/articles/8428030 (minimum trading days); {U['Fintokei all-in']}")

setrule("Hola Prime 2-Step Prime", "Maximum daily loss / maximum loss", "5% of the previous day's closing balance (relative), reset 17:00 EST / 10% of the initial balance, static")
setrule("Hola Prime 2-Step Prime", "Funded split and payouts", "bi-weekly 80% with 3 profitable days (+0.5% of the initial balance) within the 14 days; monthly 95% with 7; on-demand 80% with a consistency score of at most 40% and 2% minimum profit")
setrule("Hola Prime 2-Step Prime", "Consistency (funded)", "the 40% consistency score applies to on-demand payouts only")
setrule("Hola Prime 2-Step Prime", "Trade ideas", "positions on the same asset and direction that overlap, or one opened within 10 minutes of closing another, are one trade idea; combined risk at most 2%")
P["Hola Prime 2-Step Prime"]["plan"] = ["its own market, traded by no other account (so nothing is copied from another firm)",
    "two accounts: one master and one copier, the most Hola Prime allows to share trades",
    "bi-weekly payouts; daily profit target until 3 profitable days in the cycle", "at least 10 minutes after any close before the next trade, so no two trades are one idea"] + COMMON
P["Hola Prime 2-Step Prime"]["sources"] = "holaprime.com/forex/faq/hola-prime-challenges/hola-prime-2-step-prime-challenge/"

setrule("Alpha Capital Pro 10%", "Maximum daily loss / maximum loss", "5% of the day's starting balance (relative) / 10% static")
setrule("Alpha Capital Pro 10%", "Funded split and payouts", "80% bi-weekly: the first request 14 days after the first trade on the funded account, with 5 trading days of the same strategy (a trade opened and closed on the day; minimal lots to complete days not allowed) and at least $100 of profit; then every 14 days (on-demand payouts, with their 40% rule, are a different option)")
P["Alpha Capital Pro 10%"]["plan"] = [f"Nasdaq, {_p(_rf('Alpha Capital Pro 10%', 'US100'))} risk (below the 2% rule after cost)", "bi-weekly payouts; until the funded account has 5 trading days, at most one normal trade a day",
    "trade durations recorded: the plan's trades last hours on average"] + COMMON
P["Alpha Capital Pro 10%"]["sources"] = (f"help.alphacapitalgroup.uk/en/articles/10570531-bi-weekly-performance-fee; {U['Alpha duration']}; "
                                         "help.alphacapitalgroup.uk/en/articles/8420429-alpha-pro-8-10")

setrule("FunderPro Classic", "Minimum days", "a minimum number of trading days per phase by default (a 'No Minimum Trading Days' add-on is sold for Classic only); 4 per phase as published by reviewers (the official pages read do not state the number)", after="Phase 1 / phase 2 target")
setrule("FunderPro Classic", "Maximum daily loss / maximum loss", "5%, balance-based, reset 00:00 GMT+3; the base is not stated (the model takes the stricter of the initial and the day's balance) / 10% static")
setrule("FunderPro Classic", "Funded split and payouts", "80% every 14 days; at least $100 of profit for every reward")
P["FunderPro Classic"]["plan"] = ["one account, the larger size if it is worth more", "risk at most 1.75%, below the 2% limit",
    f"stop at least {_mmin('FunderPro', 'US100', _rf('FunderPro Classic', 'US100')):.3f} hourly standard deviations on the Nasdaq at {_p(_rf('FunderPro Classic', 'US100'))} risk (USDJPY: {_mmin('FunderPro', 'USDJPY', _rf('FunderPro Classic', 'USDJPY')):.3f} at {_p(_rf('FunderPro Classic', 'USDJPY'))}), so the funded margin stays under 20% of the starting balance"] + COMMON
P["FunderPro Classic"]["sources"] = (f"{U['FunderPro margin']}; support.funderpro.com/en/articles/419844 (rewards, $100 minimum); support.funderpro.com/en/articles/412020 (add-ons); {U['FunderPro leverage']}")

setrule(g, "Funded split and payouts", "80% every 14 days from the first trade; 4 valid days (+0.5%) per payout cycle for accounts bought from 25 July 2026; minimum $100 (the 3% minimum belongs to on-demand rewards); the first two payouts at most 6% of the account or $10,000")
setrule(g, "Maximum daily loss / maximum loss", "5% subtracted from the higher of balance and equity at 5 pm New York (relative) / 10% static")
P[g]["plan"] = [f"one account; Nasdaq with a stop of at least {_mmin('GFT', 'US100', _rf('GFT 2-Step Standard', 'US100')):.3f} sd at {_p(_rf('GFT 2-Step Standard', 'US100'))} risk (funded 1:10, margin at most 60%) or USDJPY",
                "take-profit capped at the day's remaining $3,000", "one open position at a time, risking at most 1.75% plus cost: Goat Guard's 2% cannot trigger without an intraday gap"] + COMMON
P[g]["sources"] = "help.goatfundedtrader.com/en/articles/13575169-2-step-standard; help.goatfundedtrader.com/en/articles/9549359-all-about-rewards-and-profit-splits; " + U["GFT Goat Guard"]

setrule("Blue Guardian 2-Step", "Maximum daily loss / maximum loss", "4% of the initial balance below the higher of balance and equity at 5 pm New York (fixed) / 8% static")
setrule("Blue Guardian 2-Step", "Funded split and payouts", "85% every 14 days; the payout requires the minimum trading days requirement (read strictly as 3 profitable days in the cycle), the account above its initial balance and all positions closed; minimum $100 by crypto, $500 by Rise")
setrule("Blue Guardian 2-Step", "Holding time", "the minimum holding time is 2 minutes (tick scalping)")
setrule("Blue Guardian 2-Step", "News (funded)", "no opening or closing 5 minutes before and after red-folder news")
P["Blue Guardian 2-Step"]["sources"] = "help.blueguardian.com/en/articles/14062291-2-step-standard-rules"

setrule(m, "Maximum daily loss / maximum loss", "4% of the higher of equity and balance at 00:00 UTC (relative: 4% of $1,100 in the FAQ's example) / 8% static")
setrule(m, "Funded split and payouts", "80%; a withdrawal every 10 business days after the first trade; 3 profitable days (+0.5%) in the funded phase before a withdrawal; at most $10,000 per trader per rolling 30 days, counted on the date the profit is closed, the excess voided")
setrule(m, "Consistency (funded)", "if the total profit exceeds $5,000, the best day (trades with less than 24 hours between a close and the next opening count as one day) or single trade may not exceed 50% of the cycle's profit; the 20% consistency score belongs to instant accounts")
P[m]["plan"] = ["one 100K account, Nasdaq", "every trade at a reward:risk of at least 1:1.5",
                "funded profit never above $4,900 (payout targets of 2&ndash;4.9%), $100 under the threshold, so the 50% rule never applies even with a take-profit filled a few points better",
                "no win placed that could take the profit closed in any 30 days above $10,000", "the risk interview booked as soon as it is offered"] + COMMON
P[m]["sources"] = f"{U['Maven FAQ']} (read 4 Oct 2026)"

for _k, _sh in P.items():                       # replace version 7's common policy lines in every sheet built before this section
    if any(x in _OLD_COMMON for x in _sh["plan"]):
        _sh["plan"] = [x for x in _sh["plan"] if x not in _OLD_COMMON and x not in COMMON] + COMMON

# ================================================================ version 9 (review of version 8; rules re-read 5 October 2026)
_V8_COMMON = list(COMMON)
COMMON[:] = ["flat every day by 20:00 UTC (no entry from 19:00 UTC), so the account is flat through every daily reset and pays no "
             "overnight financing; flat at weekends",
             "concentration policy: no trade and no day makes more than 40% of the current phase or payout target, so every phase takes "
             "at least three winning days",
             "at least 10 minutes between a close and the next entry; no take-profit and no stop closer than 0.6 hourly standard "
             "deviations to the entry (a plan choice: a bracket with both levels at that distance still closes within 2 minutes about 0.2% of the time, so a firm's "
             "duration rule is met by a holding time where it has one, not by this distance)",
             "positions in whole lots (0.01-lot steps; whole futures contracts), rounded down; risk sized so that the stop loss plus the "
             "round-trip cost fits the room under the floor and under the day's limit; when the room above the floor is below a tenth of "
             "the normal risk, one last trade with its stop order at the floor itself: the account recovers or ends in a breach that frees "
             "its allocation",
             "missing trading days, where the firm counts any opened position, completed with one 0.01-lot trade a day, opened at the day's "
             "first permitted hour and closed at the market after 3 minutes (none at Fintokei and Alpha Capital)"]
for _k, _sh in P.items():                       # replace version 8's common policy lines everywhere
    if any(x in _V8_COMMON for x in _sh["plan"]):
        _sh["plan"] = [x for x in _sh["plan"] if x not in _V8_COMMON and x not in COMMON] + COMMON

setrule("FTMO 2-Step", "Trading days", "4 per phase; a trading day is 'any day ... during which at least one position is opened' (FTMO trading objectives); no minimum volume stated")
P["FTMO 2-Step"]["sources"] += f"; {U['FTMO trading objectives']}"

setrule("Fintokei ProTrader", "Small trades", "the all-in article objects to traders who reached the target and then 'opened additional, much smaller trades ... just to meet the minimum 3-day trading requirement'; a trading day needs an executed trade 'with a real market outcome'")
setrule("Fintokei ProTrader", "Funded split and payouts", "80%; a request at least 14 days after the first trade or after the last successfully processed payout; minimum $100 (the 3% minimum profit belongs to SwiftTrader); all positions closed at the request")
P["Fintokei ProTrader"]["plan"] = [x for x in P["Fintokei ProTrader"]["plan"] if x not in COMMON] + [
    "no filler trades: the 40% policy already needs three winning days per phase; a payout cycle short of its 3 trading days collects them with ordinary trades, one a day",
    "the next payout requested 14 days after the last one was processed (the model assumes one working day of processing)"] + COMMON[:-1]
P["Fintokei ProTrader"]["sources"] += f"; {U['Fintokei payouts']}"

P["Blue Guardian 2-Step"]["plan"] = [x for x in P["Blue Guardian 2-Step"]["plan"] if x not in COMMON] + [
    "every position opened with only an emergency stop at the account's breach level; the bracket placed 3 minutes after the entry, "
    "or the position closed at the market if the price is then already beyond the stop or the take-profit, so no trade lasts under 2 minutes"] + COMMON

P["BrightFunded 2-Step Classic"]["plan"] = [x for x in P["BrightFunded 2-Step Classic"]["plan"] if not x.startswith("every counted day")]
P["BrightFunded 2-Step Classic"]["plan"].insert(1, "a day counts only with a trade held at least 60 seconds: the engine counts it only then (filler trades are held 3 minutes)")

P["Alpha Capital Pro 10%"]["plan"] = [x for x in P["Alpha Capital Pro 10%"]["plan"] if not x.startswith("trade durations recorded") and x not in COMMON] + [
    "the 2-minute rule checked on the account's own trades at every phase pass and payout request (average, majority, half of gross profit), with the firm's consequence applied on failure",
    "no minimal-lot trades to complete days, in evaluations too"] + COMMON[:-1]

P["Hola Prime 2-Step Prime"]["plan"] = [("bi-weekly payouts; daily profit target until 3 profitable days within the 14 days ending on the request day" if x.startswith("bi-weekly payouts") else x)
                                        for x in P["Hola Prime 2-Step Prime"]["plan"]]

import calibrate as _CB
def _n3(m, rf, instr="US100"):
    """a loss of 2% of the account at the close after a 3-minute hold: the move against the position, in standard deviations
    of 3 minutes, at a stop of m hourly sd and risk rf (the cost of the round trip counted in the loss)"""
    rho = (_CB.INSTR[instr][1] / 100.0) / (m * _O.SIG[instr])
    return m * (0.02 / rf - rho) / (3 / 60) ** 0.5
_bg = [r for r in _FIN if r["prog"] == "Blue Guardian 2-Step" and r["instr"] == "US100"]
_bg_rf = _rf("Blue Guardian 2-Step", "US100"); _bg_mm = _mmin("Blue Guardian", "US100", _bg_rf)
_bg_txt = (f"; {_n3(_bg[0]['m'], _bg_rf):.1f} at the chosen stop of {_bg[0]['m']:g} sd" if _bg else "")
P["Blue Guardian 2-Step"]["plan"] = [(f"risk at most {_p(_bg_rf)}: a stop-out stays below the 2% shield (a position closed at the market at the end of its 3-minute hold "
                                      f"can lose a little more than its stop; reaching 2% would take a move against it of more than {_n3(_bg_mm, _bg_rf):.1f} standard deviations "
                                      f"of 3 minutes at the narrowest stop the margin allows, {_bg_mm:.2f} hourly sd{_bg_txt})"
                                      if x.startswith("risk at most 1.75%: a stop-out stays below the 2% shield") else x) for x in P["Blue Guardian 2-Step"]["plan"]]


# ================================================================ version 10 (review of version 9 and the self-audit; rules re-read 11-12 October 2026)
_V9_COMMON = list(COMMON)
COMMON[:] = ["positions opened only at the hourly opens from 01:00 UTC (07:00 on EURUSD) to 18:00 UTC; flat every day by 20:00 UTC, "
             "so the account is flat through every daily reset and pays no overnight financing; flat at weekends",
             "flat around high-impact releases wherever the firm restricts news at the account's stage: no position open in any hour "
             "that overlaps the window from 10 minutes before to 10 minutes after a release that moves the market, none opened in the "
             "hour before, a position still open closed at the start of such an hour (6.5)",
             "concentration policy: no trade and no day makes more than 40% of the current phase or payout target, so every phase takes "
             "at least three winning days",
             "at least 10 minutes between a close and the next entry; no take-profit and no stop closer than 0.6 hourly standard "
             "deviations to the entry (a plan choice: a bracket with both levels at that distance still closes within 2 minutes about "
             "0.2% of the time, so a firm's duration rule is met by a holding time where it has one, not by this distance)",
             "positions in whole lots (0.01-lot steps; whole futures contracts), rounded down; risk sized so that the stop loss plus the "
             "round-trip cost fits the room under the floor and under the day's limit; when the room above the floor is below a tenth of "
             "the normal risk, one last trade with its stop order at the floor itself: the account recovers or ends in a breach that frees "
             "its allocation; an account whose room is below even the smallest position's cost is closed on request",
             "payout requests only when the firm's conditions hold, flat; the request pending until the firm processes it (6.6): no trading "
             "where the firm locks the account, a breach before processing cancels the request elsewhere",
             "missing trading days, where the firm counts any opened position, completed with one minimal position a day (0.01 lot; one "
             "micro contract on futures), opened at the day's first permitted hour and closed at the market after 3 minutes (none at "
             "Fintokei and Alpha Capital)"]
for _k, _sh in P.items():                       # replace version 9's common policy lines everywhere
    if any(x in _V9_COMMON for x in _sh["plan"]) or any(x in _V9_COMMON[:-1] for x in _sh["plan"]):
        keep_fill = any(x == _V9_COMMON[-1] for x in _sh["plan"])
        _sh["plan"] = [x for x in _sh["plan"] if x not in _V9_COMMON and x not in COMMON] + (COMMON if keep_fill else COMMON[:-1])

def _sub(sheet, startswith, new):
    """replace the plan item of a sheet that starts with the given text"""
    pl = P[sheet]["plan"]; hits = [i for i, x in enumerate(pl) if x.startswith(startswith)]
    assert len(hits) == 1, (sheet, startswith, hits)
    pl[hits[0]] = new

_sub("FTMO 2-Step", "every account traded the same way", "every account traded the same way; none sacrificed. FTMO's $400,000 counts active FTMO Rewards Accounts and Challenges are unlimited, but the plan keeps one account per slot, four slots (inventory: account rolling and overexposure are prohibited and undefined)") if any(x.startswith("every account traded the same way") for x in P["FTMO 2-Step"]["plan"]) else None
_sub("FundingPips Flex", "USDJPY or EURUSD at 1:100", "USDJPY or EURUSD at 1:100: the Nasdaq position at the plan's risk needs about 1:9 even at the widest stop searched (m = 1.25) to keep margin under 60%, and FundingPips gives 1:5 on indices above 0.5 lots")
_sub("FundingPips Flex", "risk at most 1.75% plus cost", "risk at most 1.75% plus cost, below the 2% trade-idea limit; at least 10 minutes after any close before the next trade; a payout request at least 15 minutes after the last close, and no trading while the reward is processed")
P["FXIFY Two Phase Classic"]["plan"] = [("each day's take-profit capped at 25% of the cycle target less $1 per $100K (and 40% per trade), and a payout requested only when the account's best day ever is at most 25% of the request's profit; no trading until the withdrawal is approved" if x.startswith("each day's take-profit capped at 25%") else x)
                                        for x in P["FXIFY Two Phase Classic"]["plan"]]
P["FundedNext Stellar 2-Step"]["plan"] = [("flat around high-impact releases on the funded account (simulated: 6.5)" if x == "flat around news" else x) for x in P["FundedNext Stellar 2-Step"]["plan"]]
P["Fintokei ProTrader"]["plan"] = [("the next payout requested 14 days after the last one was processed (Fintokei approves automatically and sends the cash within one business day)" if x.startswith("the next payout requested 14 days after") else x)
                                   for x in P["Fintokei ProTrader"]["plan"]]
P["Fintokei ProTrader"]["plan"] = [(x.replace("5 &times; 100K: $500,000 is about &euro;444,000 at 1.1256, inside the &euro;500,000 cap, and 100K is cheaper per dollar than 200K",
                                              "5 &times; 100K: $500,000 is about &euro;444,000 at 1.1256, inside the &euro;500,000 cap (about &euro;56,000 of it unused: no smaller ProTrader size is modelled), and 100K is cheaper per dollar than 200K")) for x in P["Fintokei ProTrader"]["plan"]]
P["GFT 2-Step Standard"]["plan"] = [(x.replace("Goat Guard's 2% cannot trigger without an intraday gap", "a stop at 1.75% plus cost stays inside Goat Guard's 2% (at most 1.97% of the balance where the room to the floor limits the risk), and no position is held through a gap") if "Goat Guard" in x else x)
                                    for x in P["GFT 2-Step Standard"]["plan"]]
P["GFT 2-Step Standard"]["plan"].insert(2, "payouts: the first two at most the smaller of 6% of the account and $10,000, the rest left in the account; a win held under a minute is voided on the funded account (rare with the plan's distances)")
P["Blue Guardian 2-Step"]["plan"] = [(x.split(": a stop-out stays below the 2% shield")[0] + ": a stop-out stays below the 2% Guardian Shield; during the 3-minute hold the position has no stop, so the engine applies the Shield there too (first time: the split falls to 50%; second: a breach)" if x.startswith("risk at most") and "shield" in x else x)
                                     for x in P["Blue Guardian 2-Step"]["plan"]]
P["Maven 2-Step"]["plan"] = [("every position placed at a reward:risk of at least 1:1.5, checked on the rounded position actually placed; where rounding to the smallest volume would break it, the plan waits" if x.startswith("every trade at a reward:risk of at least 1:1.5") else x)
                             for x in P["Maven 2-Step"]["plan"]]
P["Alpha Capital Pro 10%"]["plan"].insert(1, "on the funded account, every position at most 40 lots per $100K (80 at 200K), the lot limit counted at its strictest; no trading while a payout is processed")
P["The5ers High Stakes"]["plan"].insert(2, "payout requests of at most $4,000 on 100K with the fee refund counted inside it, only with at least $500 of profit and $150 after the split; the balance kept under +9.5% so the account does not scale")
for s_ in ("Topstep 50K", "Apex 50K EOD"):
    P[s_]["plan"] = [x for x in P[s_]["plan"] if x not in COMMON]
P["Topstep 50K"]["plan"] += ["a payout requested one minute after the 4 p.m. Chicago lock of a session that completes five winning sessions after the previous request's session, at least $125 after the split", "flat ahead of US CPI releases (6.5)"]
P["Apex 50K EOD"]["plan"] += ["while a payout request is pending the account does not trade, so the balance cannot fall below the threshold that would deny it; today's profit counted in the 50% rule", "a target reached after 6 pm New York on day 30 is too late: the evaluation has expired"]
for _k in P:                                    # sources: the inventory gives each rule's page and the date it was read
    P[_k]["sources"] = P[_k]["sources"] + "; every rule's page and reading date: the inventory, Appendix B"
_NEWS_LINE = COMMON[1]
for _k in ("Fintokei ProTrader", "Hola Prime 2-Step Prime"):        # firms that allow news trading
    P[_k]["plan"] = [x for x in P[_k]["plan"] if x != _NEWS_LINE] + ["news trading allowed by the firm: the plan trades through releases (a real stop can fill beyond its level there, 3.4)"]
P["FundedNext Stellar 2-Step"]["plan"] = [x for x in P["FundedNext Stellar 2-Step"]["plan"] if not x.startswith("flat around high-impact releases on the funded account")]
P["Maven 2-Step"]["plan"] = [(x.replace("so the 50% rule never applies even with a take-profit filled a few points better",
                                        "so the 50% rule never applies even with a take-profit filled a few points better (read per payout cycle, as the FAQ's sentence ends; inventory)") if x.startswith("funded profit never above $4,900") else x)
                             for x in P["Maven 2-Step"]["plan"]]
P["Blue Guardian 2-Step"]["plan"] = [(x.replace("so no trade lasts under 2 minutes", "so the plan closes no trade within 2 minutes (only a breach or the Guardian Shield could end one sooner)") if x.startswith("every position opened with only an emergency stop") else x)
                                     for x in P["Blue Guardian 2-Step"]["plan"]]
P["GFT 2-Step Standard"]["plan"] = [("one open position at a time whose stop loss plus cost stays inside Goat Guard's 2% (at most 1.97% of the balance where the room to the floor limits the risk); no position held through a gap" if x.startswith("one open position at a time, risking at most 1.75% plus cost") else x)
                                    for x in P["GFT 2-Step Standard"]["plan"]]

# ================================================================ version 10, the readings of 12 October 2026 (every inventory row read
# again: rules_inventory_v10.py; the plan notes below follow the engine's rules in firms_v10 and the portfolio in lockstep_portfolio_v10)
_TERM = COMMON[4]
_FILL = COMMON[6]
_TERM_NEW = _TERM + " (not at GFT and Alpha Capital, whose all-or-nothing rules rule it out: there the account is closed on request instead)"
_FILL_NEW = _FILL.replace("(none at Fintokei and Alpha Capital)", "(none at Fintokei, Alpha Capital, FunderPro and Hola Prime)")
for _k, _sh in P.items():
    _sh["plan"] = [(_TERM_NEW if x == _TERM else _FILL_NEW if x == _FILL else x) for x in _sh["plan"]]
COMMON[4] = _TERM_NEW; COMMON[6] = _FILL_NEW

def _repl(sheet, startswith, new):
    """replace the plan item of a sheet that starts with the given text (it must exist once)"""
    pl = P[sheet]["plan"]; hits = [i for i, x in enumerate(pl) if x.startswith(startswith)]
    assert len(hits) == 1, (sheet, startswith, hits)
    pl[hits[0]] = new

def _drop(sheet, x):
    P[sheet]["plan"] = [y for y in P[sheet]["plan"] if y != x]

# FTMO: its guidance per trade idea (1%) binds the plan's single-position trade idea (optimize_v10.L_MAX)
_ftmo_rf = min(_rf("FTMO 2-Step", "US100", _O.L_MAX["FTMO"]), _O.L_MAX["FTMO"])
setrule("FTMO 2-Step", "Risk guidance", "FTMO 'generally recommends not risking more than 1% per trade idea', and at most 1&ndash;1.5% of the initial balance on one position; larger risk can trigger its risk monitoring (guidance, which the plan treats as a rule)")
_repl("FTMO 2-Step", f"{_p(_rf('FTMO 2-Step', 'US100', 0.015))} risk",
      f"risk {_p(_ftmo_rf)} at most (FTMO 'generally recommends not risking more than 1% per trade idea' and at most 1&ndash;1.5% on one position; the plan's trade idea is one position), with the stop attached at entry")
# FundingPips: index leverage
_repl("FundingPips Flex", "USDJPY or EURUSD at 1:100",
      "USDJPY or EURUSD at 1:100. The Nasdaq is not traded there: version 9 read FundingPips' index leverage as 1:5 above 0.5 lots "
      "(4 October 2026), at which the plan's Nasdaq position would need about 1:9 even at the widest stop searched (m = 1.25); listings of "
      "October 2026 differ (1:20, or a leverage falling from 1:50 to 1:5 with the position's size)")
_repl("FundingPips Flex", "risk at most 1.75% plus cost, below the 2% trade-idea limit",
      "risk at most 1.75% plus cost, below the trade-idea limit of 2% (3% on some models); at least 10 minutes after any close before the next trade; a payout request at least 15 minutes after the last close, and no trading while the reward is processed")
P["FundingPips Flex"]["sources"] = P["FundingPips Flex"]["sources"].replace(" (2 Step Flex, read 4 Oct 2026)", " (2 Step Flex)")
# The5ers
_repl("The5ers High Stakes", "payout requests of at most $4,000",
      "payout requests of at most $4,000 on 100K with the fee refund counted inside it, only with at least $500 of profit and $150 after the split and the 3.5% commission; the balance kept under +9.5% so the account does not scale")
_repl("The5ers High Stakes", "one 100K account; optionally New's small accounts",
      "one 100K account; optionally New's small accounts (3 &times; 2.5K, 3 &times; 5K, 3 &times; 10K, 1 &times; 25K), each on New's own contract and fee: not recommended, because The5ers' rule on position sizes 'substantially larger or smaller ... compared across your own accounts' could be read against their smaller positions ([[CH_RISK]].2)")
P["The5ers High Stakes"]["plan"].insert(1, "own entries on each account; The5ers asked in writing, before the first trade, to confirm that this is not the 'copy trading with other traders or accounts' its prohibited-practices page names ([[CH_RUN]].3)")
# FXIFY
_repl("FXIFY Two Phase Classic", "one Classic account of each size",
      "one Classic account of each size: 100K, 50K, 25K, 15K, 10K and 5K (version 9 left out the 15K)")
P["FXIFY Two Phase Classic"]["plan"].insert(1, "the same trades on several of your accounts only after FXIFY's approval, asked before the first trade (it allows copy trading with prior approval: [[CH_RUN]].3)")
# FundedNext: the dollar direction is shared with USDJPY when it trades EURUSD (10.3)
_repl("FundedNext Stellar 2-Step", "its own market (no other account trades it)",
      "its own market, traded by no other account, so nothing is copied from another firm; on EURUSD its direction follows the dollar direction of any open USDJPY position (10.3), a direction and not a copied trade")
# Fintokei: 400,000 EUR/USD of funded accounts
_repl("Fintokei ProTrader", "Nasdaq, shared direction; 5 &times; 100K",
      "Nasdaq, shared direction; 4 &times; 100K: Fintokei allows 400,000 EUR/USD of funded ProTrader accounts (evaluations not counted), and 100K is cheaper per dollar than 200K ($549 against $1,249)")
# Hola Prime: no fillers
P["Hola Prime 2-Step Prime"]["plan"] = [x for x in P["Hola Prime 2-Step Prime"]["plan"] if x != _FILL_NEW]
P["Hola Prime 2-Step Prime"]["plan"].insert(4, "no filler trades (its prohibited practices name 'unexplained deviations in position size'): a phase's three days come from the 40% policy's three winning days")
# Alpha Capital: no last trade to the floor
P["Alpha Capital Pro 10%"]["plan"].insert(4, "no last trade to the floor ('all or nothing' strategies are prohibited): an account whose room falls below the smallest normal risk is closed on request")
# FunderPro
_repl("FunderPro Classic", "one account, the larger size if it is worth more",
      "one account in the recommended plan, the larger size if it is worth more; at the full allowance two 100K or one 200K, whichever is worth more (FunderPro allows copying between your own accounts)")
_repl("FunderPro Classic", "risk at most 1.75%, below the 2% limit",
      "risk at most 1.75% (FunderPro's 2% per-trade rule is published for its Instant programme, which the plan does not use)")
P["FunderPro Classic"]["plan"] = [x for x in P["FunderPro Classic"]["plan"] if x != _FILL_NEW]
P["FunderPro Classic"]["plan"].insert(3, "no filler trades (its lot-size policy names 'abrupt or unjustified changes in lot sizes'): a phase short of its 4 trading days after the target collects them with ordinary trades, one a day; positions closed 2 hours before any market closure of 2 hours or more ([[CH_RUN]].3)")
# GFT
_repl("GFT 2-Step Standard", "one account; Nasdaq with a stop of at least",
      P["GFT 2-Step Standard"]["plan"][[i for i, x in enumerate(P["GFT 2-Step Standard"]["plan"]) if x.startswith("one account; Nasdaq with a stop of at least")][0]]
      .replace("one account; ", "one account in the recommended plan, four 100K or two 200K at the full allowance (GFT allows copying between your own accounts); "))
_repl("GFT 2-Step Standard", "one open position at a time whose stop loss plus cost stays inside Goat Guard's 2%",
      "one open position at a time whose stop loss plus cost (at most $1,750 plus cost per $100K) stays inside Goat Guard's 2% of the initial size; no position held through a gap")
P["GFT 2-Step Standard"]["plan"].insert(4, "no last trade to the floor ('All-Or-Nothing Trading, where you can lose the account in one trade', is prohibited): an account whose room falls below the smallest normal risk is closed on request")
# BrightFunded, Blue Guardian
_repl("BrightFunded 2-Step Classic", "one account (recommended) or four, Nasdaq",
      "one account in the recommended plan; at the full allowance $400,000 in 100K or 200K accounts, whichever is worth more; Nasdaq")
_repl("Blue Guardian 2-Step", "one account, Nasdaq with the stop widened to fit 1:10",
      "one account in the recommended plan ($400,000 in 100K or 200K accounts at the full allowance), Nasdaq with the stop widened to fit 1:10, the lowest leverage any source gives")
# Maven
_repl("Maven 2-Step", "funded profit never above $4,900",
      "funded profit never above $4,900 (payout targets of 2&ndash;4.9%), $100 under the threshold, so the 50% rule never applies even with a take-profit filled a few points better; 'total profit' read as the profit since the last payout, after which Maven resets the account (the less strict of two readings: inventory)")
P["Maven 2-Step"]["plan"].insert(3, "one Maven account only: the $10,000 per 30 days is per trader, all accounts together; payouts by Rise at $20 each where bank transfer is not offered")
P["Maven 2-Step"]["sources"] = P["Maven 2-Step"]["sources"].replace(" (read 4 Oct 2026)", "")

# keep-alive (n47, 12 October 2026): the plan's 25-day rule on every sheet, as the engine applies it (acct_mc.run_funded)
_KA = ("never 25 days without a trade: on the day 22 days after the last entry, if nothing has been traded since, one minimal "
       "keep-alive position (0.01 lot, one contract on futures, closed after 3 minutes) at its first permitted hour, or before a "
       "payout request that would lock the account past that day (most firms close an account after 30 days without a trade; FXIFY "
       "after 60)")
_KA_NOFILL = ("never 25 days without a trade: no wait for a payout comes near it here (14-day cycles), so no keep-alive position "
              "is needed, and none would be placed (no minimal positions at this firm)")
for _k, _sh in P.items():
    _nofill = _k.startswith(("Fintokei", "Alpha Capital", "FunderPro", "Hola Prime"))
    _sh["plan"].append(_KA_NOFILL if _nofill else _KA)
P["FXIFY Two Phase Classic"]["plan"].append("on the 30-day option an account at its target waits for the payout date and then for FXIFY's "
    "read-only review: the keep-alive position comes first where that wait would pass the 22nd day")
P["Maven 2-Step"]["plan"].append("Maven's $10,000 per 30 days can stop trading for more than three weeks after two quick payout cycles: "
    "the keep-alive position then carries a take-profit 1.5 times as far as its emergency stop, and any gain from it above the cap is "
    "voided; Maven closes an account 'dormant for more than 30 calendar days' and defines inactivity as 'having no executed trades', "
    "but its gambling rules say that 'Trades with vastly smaller lot sizes will NOT count as a trade': that the keep-alive counts is an "
    "assumption (inventory)")

# the 40% policy as the engine applies it (12 October 2026): every trade and every day of an evaluation, every day (net) of a funded
# cycle; acct_mc.run_stage caps a win at 40% of the phase target, run_funded caps the day's net profit only (the firms' funded rules
# limit days, not single trades)
_CONC_OLD = ("concentration policy: no trade and no day makes more than 40% of the current phase or payout target, so every phase takes "
             "at least three winning days")
_CONC_NEW = ("concentration policy: no day makes more than 40% of the current phase or payout target, net of its earlier trades, and in "
             "an evaluation no single trade either, so every phase takes at least three winning days")
_FX_OLD = ("each day's take-profit capped at 25% of the cycle target less $1 per $100K (and 40% per trade), and a payout requested only "
           "when the account's best day ever is at most 25% of the request's profit; no trading until the withdrawal is approved")
_FX_NEW = ("each day's profit capped at 25% of the cycle target less $1 per $100K, net of the day's earlier trades (each take-profit "
           "placed so that the day cannot end above it), and a payout requested only when the account's best day ever is at most 25% of "
           "the request's profit; no trading until the withdrawal is approved")
_n_conc = 0
for _k, _sh in P.items():
    _n_conc += sum(1 for x in _sh["plan"] if x == _CONC_OLD)
    _sh["plan"] = [(_CONC_NEW if x == _CONC_OLD else _FX_NEW if x == _FX_OLD else x) for x in _sh["plan"]]
assert _n_conc > 0 and not any(x == _CONC_OLD for _sh in P.values() for x in _sh["plan"])
assert any(x == _FX_NEW for x in P["FXIFY Two Phase Classic"]["plan"])

# the last-trade item, in the order of its clauses (the GFT and Alpha Capital exception belongs to the last trade, not to the closing of
# an account below the smallest position's cost), with the threshold as acct_mc._risk applies it: a tenth of the normal risk or the
# smallest position's risk, whichever is larger (one micro contract on futures can be the larger)
_TERM_OLD = ("positions in whole lots (0.01-lot steps; whole futures contracts), rounded down; risk sized so that the stop loss plus the "
             "round-trip cost fits the room under the floor and under the day's limit; when the room above the floor is below a tenth of "
             "the normal risk, one last trade with its stop order at the floor itself: the account recovers or ends in a breach that frees "
             "its allocation; an account whose room is below even the smallest position's cost is closed on request (not at GFT and Alpha "
             "Capital, whose all-or-nothing rules rule it out: there the account is closed on request instead)")
_TERM_FIX = ("positions in whole lots (0.01-lot steps; whole futures contracts), rounded down; risk sized so that the stop loss plus the "
             "round-trip cost fits the room under the floor and under the day's limit; when the room above the floor is below a tenth of "
             "the normal risk (or below the smallest position's risk, where that is larger), one last trade with its stop order at the "
             "floor itself: the account recovers or ends in a breach that frees its allocation (not at GFT and Alpha Capital, whose "
             "all-or-nothing rules rule it out: there the account is closed on request instead); an account whose room is below even the "
             "smallest position's cost is closed on request")
_n_term = sum(1 for _sh in P.values() for x in _sh["plan"] if x == _TERM_OLD)
for _k, _sh in P.items():
    _sh["plan"] = [(_TERM_FIX if x == _TERM_OLD else x) for x in _sh["plan"]]
assert _n_term > 0 and not any(x == _TERM_OLD for _sh in P.values() for x in _sh["plan"])
