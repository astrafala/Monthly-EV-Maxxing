"""
Programme sheets for the version 7 document: version 6's sheets (progs_v6.py) with every rule the review or the
official pages corrected, the plan's three version 7 policies in every plan list, and exact source URLs.
"""
import copy
from progs_v6 import P as P6
from firms_v7 import SOURCES as U

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
    "each day's take-profit capped at 25% of the cycle target (and 40% per trade), so the best-day rule always holds",
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
    P[s]["plan"] = P[s]["plan"] + ["whole micro contracts, risk rounded down", "no trade and no day above 40% of the evaluation target"]
for s in ("FTMO 2-Step", "Fintokei ProTrader", "Hola Prime 2-Step Prime", "Alpha Capital Pro 10%"):
    P[s]["plan"] = [x for x in P[s]["plan"] if "10 minutes before" not in x] + COMMON
