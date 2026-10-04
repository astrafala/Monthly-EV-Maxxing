"""
Version 7 rule sets. Every programme of the plan, rebuilt from firms_v5 with the corrections of the version 6 review
(rules re-read on the firms' own help pages, 4 October 2026; the URL behind each is listed in SOURCES below), plus
three policies of the plan itself that apply to every CFD programme:

  flat_daily = 20   no entry at or after 19:00 UTC and every position closed at the 20:00 UTC open, so the account is
                    flat through every firm's daily reset (FTMO and BrightFunded near midnight Prague time, GFT and
                    Blue Guardian at 5 pm New York, Maven and Fintokei at midnight UTC). Daily-loss limits measured
                    on equity or on the higher of balance and equity then equal the balance-based limit the engine
                    applies, and no position pays overnight financing or carries a weekend or overnight gap.
  conc = 0.40       concentration policy: no single trade and no single day may make more than 40% of the current
                    phase target (evaluation) or of the current payout target (funded). Several firms forbid passing
                    with one or a few trades (Fintokei, The5ers "one-trade target attainment", Alpha "all or nothing",
                    FundingPips' Profit Concentration Policy at 60%, FundedNext, Hola Prime, FTMO and FXIFY gambling
                    clauses); at 40% every phase and every payout needs at least three winning days.
  sizing            risk per trade is sized so that the stop loss plus the round-trip cost fits the room left under
                    the floor and under today's loss limit; an attempt or a funded account whose room above the floor
                    falls below one tenth of the planned risk (or one futures contract) is ended there and recorded
                    as a failure (version 6's engine kept trading micro positions; its text said to stop).
"""
import copy
import firms_v3 as V3, firms_v5 as F5

TIER = dict(F5.TIER)
firm_of = F5.firm_of
CONC = 0.40
EUR = 1.1256                     # EURUSD reference close, 2 October 2026

def _policy(f, conc=CONC, flat=True):
    if flat: f["flat_daily"] = 20
    for ph in f["phases"]: ph["conc"] = conc
    f["funded"]["conc"] = conc
    return f

def _profit_days(f, n, frac, size, funded=None):
    for ph in f["phases"]: ph["profit_days"] = (n, frac * size)
    if funded: f["funded"]["profit_days"] = (funded, frac * size)
    return f

def _fee(table, size, per100):
    return table.get(size, per100 * size / 100_000)

def cfd_firms(size=100_000):
    K = size / 100_000
    F = {}
    # FTMO 2-Step (FTMO Account, Standard): 10% / 5%; 5% daily (balance at midnight Prague time); 10% static; 4 trading
    # days per phase; 80% every 14 days; fee refunded with the first reward; no weekend holding. Price EUR 540 per 100K,
    # EUR 1,080 per 200K (converted at 1.1256).
    F["FTMO 2-Step"] = V3._cfd_2step(size, _fee({100_000: 540 * EUR, 200_000: 1080 * EUR}, size, 540 * EUR), 0.10, 0.05)
    # FundingPips 2-Step Flex (help centre "2 Step Flex"): 10% / 8%; 4% daily; 12% maximum loss; 1:100 forex leverage;
    # choice at purchase: 80% split with 1 minimum trading day per phase (accounts from 26 August 2026), or 95% with 3
    # profitable days (>= 0.5%) per phase and per reward cycle; bi-weekly rewards; no fee refund on Flex; holding
    # overnight and over weekends only with the Swing add-on on the Master account (the plan is flat daily anyway).
    # The Profit Concentration Policy (one trade idea > 60% of a phase target) never triggers under the 40% policy.
    F["FundingPips 2-Step Flex (80%)"] = V3._cfd_2step(size, 499 * K, 0.10, 0.08, dll=0.04, dd=0.12, min_days=1,
                                                       split=0.80, refund=False)
    F["FundingPips 2-Step Flex (95%)"] = _profit_days(V3._cfd_2step(size, 499 * K, 0.10, 0.08, dll=0.04, dd=0.12,
                                                      min_days=0, split=0.95, refund=False), 3, 0.005, size, funded=3)
    # FundedNext Stellar 2-Step: 8% / 5%; 5% daily; 10% static; 5 trading days per phase; first reward 21 days after
    # the funded account opens, then every 14 days (the 80% "21-day" option); fee refunded with the first reward.
    F["FundedNext Stellar 2-Step"] = V3._cfd_2step(size, _fee({100_000: 549.99, 200_000: 1049.99}, size, 549.99), 0.08, 0.05,
                                                   min_days=5, first=21, cycle=14)
    # The5ers High Stakes (New, 10% / 5%) and Classic (8% / 5%): 5% daily; 10% static; 3 profitable days (>= 0.5%)
    # per phase; 80%; first payout after 14 days and at least $150. Fee return: 10% of the fee as hub credit when
    # phase 1 is passed, 20% when phase 2 is passed (credit is spent on the next evaluation, which the plan always
    # buys), and 70% added to the funded account and paid with the first payout.
    for name, t1, per in (("The5ers High Stakes", 0.10, 491), ("The5ers High Stakes Classic", 0.08, 545)):
        fee = (F5.THE5ERS_HS_FEE.get(size, 491 * K) if name == "The5ers High Stakes" else 545 * K)
        f = _profit_days(V3._cfd_2step(size, fee, t1, 0.05, min_days=0, flat_weekend=True,
                                       funded_extra=dict(min_payout=150.0)), 3, 0.005, size)
        f["refund_frac"] = 0.70; f["credit_frac"] = (0.10, 0.20)
        F[name] = f
    if size in F5.THE5ERS_HS_FEE and size < 100_000:
        F[f"The5ers High Stakes {size // 1000 if size % 1000 == 0 else size / 1000:g}K"] = F["The5ers High Stakes"]
    # FXIFY Two Phase Classic: 5% then 10%; 4% daily; 10% static; 4 trading days per phase; best day at most 25% of the
    # profit paid; 80% every 14 days or 100% every 30 days; fee refunded with the first payout. $549 per 100K.
    F["FXIFY Two Phase Classic (80%)"] = V3._cfd_2step(size, 549 * K, 0.05, 0.10, dll=0.04, dd=0.10, min_days=4,
                                                       funded_extra=dict(best=0.25, best_ever=True))
    F["FXIFY Two Phase Classic (100%, 30 days)"] = V3._cfd_2step(size, 549 * K, 0.05, 0.10, dll=0.04, dd=0.10, min_days=4,
                                                                 split=1.0, first=30, cycle=30, funded_extra=dict(best=0.25, best_ever=True))
    # Fintokei ProTrader: 8% / 6%; daily loss 5% of the equity at the start of the day (midnight UTC); 10% static; 3
    # profitable days per phase; 80%; first payout after 14 days then every 14, at least 3% profit; fee returned with
    # the first payout.
    f = _profit_days(V3._cfd_2step(size, _fee({100_000: 549, 200_000: 1249}, size, 549), 0.08, 0.06, min_days=0, first=14,
                                   cycle=14, funded_extra=dict(min_payout=0.03 * size, dll_rel=True)), 3, 0.005, size)
    for ph in f["phases"]: ph["dll_rel"] = True
    F["Fintokei ProTrader"] = f
    # Hola Prime 2-Step Prime, bi-weekly 80%: 8% / 5%; 5% daily; 10% static; 3 trading days per phase; funded best day
    # at most 40% of the payout's profit, 3 profitable days per cycle, risk per trade at most 2%; fee back 25% with each
    # of the first four payouts. $599 per 100K.
    F["Hola Prime 2-Step Prime (bi-weekly 80%)"] = V3._cfd_2step(size, 599 * K, 0.08, 0.05, min_days=3,
        funded_extra=dict(refund_split=4, best=0.40, profit_days=(3, 0.005 * size)))
    # Alpha Capital Alpha Pro 10%: 10% / 5%; 5% daily; 10% static; 3 trading days; bi-weekly 80%; no refund assumed;
    # no trade may risk or lose 2% or more; average trade duration above 2 minutes (bi-weekly payouts: the 40% best-day
    # rule applies to on-demand payouts only).
    F["Alpha Capital Pro 10%"] = V3._cfd_2step(size, _fee({100_000: 497, 200_000: 997}, size, 497), 0.10, 0.05, min_days=3,
                                               refund=False)
    # GFT 2-Step Standard (rules of 17 August 2026): 10% / 5%; a trading day counts only with >= 0.5% profit, 3 per
    # phase; 5% daily (higher of balance and equity, 5 pm New York); 10% static; funded: 80% every 14 days, 4 such days
    # per cycle (accounts bought from 25 July 2026), first two payouts at most min(6%, $10,000), first payout at least
    # 3%, $3,000 a day at most at every account size (the excess is deducted). Leverage on indices 1:10 once funded.
    F["GFT 2-Step Standard"] = _profit_days(V3._cfd_2step(size, _fee({100_000: 524, 200_000: 974}, size, 524), 0.10, 0.05,
        min_days=0, flat_weekend=True, funded_extra=dict(day_profit_cap=3_000.0, min_payout=0.03 * size,
        caps=[min(0.06 * size, 10_000)] * 2 + [1e12] * 98)), 3, 0.005, size, funded=4)
    # FunderPro Classic: 10% / 5%; 5% daily; 10% static; no minimum days; bi-weekly 80%; fee refunded with the first
    # reward; list price $539 per 100K, $989 per 200K. Funded accounts may use at most 20% of the starting balance as
    # margin per asset class (optimiser: stop floor).
    F["FunderPro Classic"] = V3._cfd_2step(size, _fee({100_000: 539, 200_000: 989}, size, 539), 0.10, 0.05, min_days=0)
    # BrightFunded 2-Step Classic: 10% / 5%; 5% daily (of the original balance); 10% static; 5 trading days per phase
    # (a day counts with one trade open for at least 60 seconds); first payout 30 days after funding then every 14;
    # 80%; no refund without the paid add-on. EUR 497 per 100K, EUR 997 per 200K.
    F["BrightFunded 2-Step Classic"] = V3._cfd_2step(size, _fee({100_000: 497 * EUR, 200_000: 997 * EUR}, size, 497 * EUR),
                                                     0.10, 0.05, min_days=5, first=30, refund=False)
    # Blue Guardian 2-Step Standard: 8% / 4%; 4% daily; 8% static; 3 profitable days per phase; 85% every 14 days; fee
    # refunded after the fourth payout. $579 per 100K, $1,162 per 200K.
    F["Blue Guardian 2-Step"] = _profit_days(V3._cfd_2step(size, _fee({100_000: 579, 200_000: 1162}, size, 579), 0.08, 0.04,
                                             dll=0.04, dd=0.08, min_days=0, split=0.85, refund_after=4), 3, 0.005, size)
    # Maven 2-Step: 8% / 5%; 4% daily; 8% static; 3 profitable days per phase; 80%; payouts every 10 business days;
    # fee back with the third payout; at most $10,000 paid per trader per rolling 30 days across all Maven accounts
    # (the excess is voided; the plan waits until the window has room). Version 6's 50% best-day rule is replaced by the
    # FAQ's largest-trade rule below.
    # Funded payouts also need the largest winning trade to be at most 20% of the profit withdrawn (FAQ, consistency for
    # standard accounts), and the FAQ calls large bets at a reward:risk of 1:1.25 or lower gambling: the plan never
    # takes a Maven trade below 1:1.5. Profits within 2 minutes of red-folder news are not credited (sensitivity only).
    f = _profit_days(V3._cfd_2step(size, 440 * K, 0.08, 0.05, dll=0.04, dd=0.08, min_days=0, refund_after=3,
                     funded_extra=dict(roll_cap=(10_000.0, 30), trade_best=0.20, min_rr=1.5)), 3, 0.005, size)
    for ph in f["phases"]: ph["min_rr"] = 1.5
    F["Maven 2-Step"] = f
    for f in F.values(): _policy(f)
    return F

def futures_firms():
    F = copy.deepcopy(V3.futures_firms())
    F["Apex 50K EOD"]["phases"][0]["max_days"] = 30          # the evaluation expires 30 days after purchase
    F["Topstep 50K"]["funded"]["need_profit"] = True          # a payout needs net profit since the last payout
    for f in F.values():
        for ph in f["phases"]: ph["conc"] = CONC
    return F

def _apply_fee(F, fee):
    F["fee"] = fee
    if F["funded"].get("refund"): F["funded"]["refund"] = F.get("refund_frac", 1.0) * fee
    if F.get("credit_frac"): F["phase_credit"] = [c * fee for c in F["credit_frac"]]

def rules_for(prog, size=100_000, kind="cfd", fee=None, override=None):
    """A programme's rule set at a given size, with an exact fee where given (the refund follows the fee actually
    paid) and safety margins scaled to the account."""
    F = copy.deepcopy(cfd_firms(size)[prog] if kind == "cfd" else futures_firms()[prog])
    if kind == "cfd": F["buffer_scale"] = size / 100_000
    _apply_fee(F, F["fee"] if fee is None else fee)
    F.update(override or {})
    return F

# official pages read for version 7 (4 October 2026)
SOURCES = {
    "FundingPips": "https://help.fundingpips.com/hc/en-us/articles/47835196271249-2-Step-Flex",
    "FundingPips PCP": "https://help.fundingpips.com/hc/en-us/articles/48174287980177-Risk-Per-Trade-Idea",
    "GFT rewards": "https://help.goatfundedtrader.com/en/articles/11472001-funded-account-reward-guidelines",
    "GFT 2-Step": "https://help.goatfundedtrader.com/en/articles/13575348-2-step-goat-model",
    "FunderPro margin": "https://support.funderpro.com/en/articles/421458-is-there-a-margin-rule-on-funded-accounts",
    "FunderPro leverage": "https://support.funderpro.com/en/articles/422676-leverage-on-funderpro-challenges",
    "Alpha on-demand": "https://help.alphacapitalgroup.uk/en/articles/10102634-performance-fee-on-demand",
    "Alpha duration": "https://help.alphacapitalgroup.uk/en/articles/8447268-what-is-the-2-minute-average-trade-duration-rule",
    "Maven FAQ": "https://maventrading.com/faqs",
    "FTMO risk": "https://ftmo.com/en/blog/how-much-should-you-risk-on-one-trade/",
    "GFT Goat Guard": "https://help.goatfundedtrader.com/en/articles/10742107-what-is-goat-guard",
    "Fintokei loss limits": "https://support.fintokei.com/en/articles/6538826-how-are-the-daily-loss-limit-and-maximum-loss-limit-calculated",
    "Fintokei all-in": "https://support.fintokei.com/en/articles/9464503-what-is-all-in-trading-and-why-is-it-forbidden-to-achieve-profit-target-in-one-trade",
    "FundedNext Stellar": "https://help.fundednext.com/en/articles/9430123-is-there-a-minimum-trading-day-and-profit-target-in-the-fundednext-account-of-the-stellar-2-step-model",
    "Topstep payouts": "https://help.topstep.com/en/articles/8284233-topstep-payout-policy",
    "Apex EOD payouts": "https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-payouts/",
    "BrightFunded evaluation": "https://help.brightfunded.com/en/articles/9241611-what-are-the-current-rules-for-the-evaluation-process",
}
