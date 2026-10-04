"""
Firm rule sets added in version 5 (checked 4 October 2026), on top of firms_v3.

Every firm also carries a reliability tier from its public reputation on 4 October 2026:
  A  PropFirmMap safety grade A or A+, TrustPilot profile active
  B  grade B+, TrustPilot profile active
  D  TrustPilot has withheld the firm's rating for a guidelines breach ("we've removed a number of fake reviews");
     PropFirmMap grade D. This says nothing direct about payouts, but it removes the main public check on them.
"""
import firms_v3 as V3

TIER = {
    "FTMO": "A", "FundingPips": "A", "FundedNext": "A", "The5ers": "A", "FXIFY": "A",
    "Fintokei": "B", "Hola Prime": "B",
    "Alpha Capital": "D", "GFT": "D", "BrightFunded": "D", "Blue Guardian": "D", "FunderPro": "D", "Maven": "D",
    "Topstep": "A", "Lucid": "B", "Tradeify": "?", "Apex": "B",
}

def firm_of(name):
    for f in TIER:
        if name.startswith(f): return f
    return name.split()[0]

THE5ERS_HS_FEE = {2_500: 19, 5_000: 35, 10_000: 69, 25_000: 176, 50_000: 278, 100_000: 491}

def cfd_firms(size=100_000):
    F = V3.cfd_firms(size)
    K = size / 100_000
    # Fintokei ProTrader (2-step): $549 per 100K ($1,249 per 200K); 8% / 6%; daily loss 5% of start-of-day equity;
    # 10% static; at least 3 profitable days per phase (the home page says "profitable", the plan page "trading";
    # the stricter reading is used); open risk per trade at most 3%; weekend holding allowed; 80% reward; the first
    # payout can be requested 14 days after the funded account opens, then every 14 days, at least 3% profit each,
    # with every position closed; the fee is returned with the first payout (sign-up bonus, ProTrader terms);
    # at most EUR 500,000 of accounts per person; copying your own trades is allowed, other people's is not.
    F["Fintokei ProTrader"] = V3._cfd_2step(size, {100_000: 549, 200_000: 1249}.get(size, 549 * K), 0.08, 0.06,
        min_days=0, first=14, cycle=14, funded_extra=dict(min_payout=0.03 * size))
    for ph in F["Fintokei ProTrader"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    # Hola Prime 2-Step Prime: $599 per 100K assumed (published prices range $409-$599 with the payout option);
    # 8% / 5%; daily loss 5% of the previous day's closing balance; 10% static; 3 trading days per phase; news and
    # weekends allowed. Funded: stop loss on every trade, risk per trade at most 2%; bi-weekly 80% needs 3 profitable
    # days in the cycle, monthly 95% needs 7; best day at most 40% of the payout's profit; the fee comes back 25% with
    # each of the first four payouts; $500,000 per person. Copying is allowed only between your own Hola Prime
    # accounts, and copying from other prop firms is prohibited, so the account trades its own instrument (USDJPY).
    F["Hola Prime 2-Step Prime (bi-weekly 80%)"] = V3._cfd_2step(size, 599 * K, 0.08, 0.05, min_days=3,
        funded_extra=dict(refund_split=4, best=0.40, profit_days=(3, 0.005 * size)))
    F["Hola Prime 2-Step Prime (monthly 95%)"] = V3._cfd_2step(size, 599 * K, 0.08, 0.05, min_days=3, split=0.95,
        first=30, cycle=30, funded_extra=dict(refund_split=4, best=0.40, profit_days=(7, 0.005 * size)))
    # FXIFY, corrected in version 5 (version 4's "Two-Phase" used a 5% daily loss, no minimum days and $480):
    # Two Phase Classic: $549 per 100K; 5% then 10%; 4% daily loss; 10% static; 4 trading days per phase; funded:
    # best day at most 25% of the profit paid out (the benchmark is the account's best day ever), 80% every 14 days or
    # 100% every 30 days; fee refunded with the first payout; copying between your own FXIFY accounts allowed.
    F["FXIFY Two Phase Classic (80%)"] = V3._cfd_2step(size, 549 * K, 0.05, 0.10, dll=0.04, dd=0.10, min_days=4,
        funded_extra=dict(best=0.25))
    F["FXIFY Two Phase Classic (100%, 30 days)"] = V3._cfd_2step(size, 549 * K, 0.05, 0.10, dll=0.04, dd=0.10, min_days=4,
        split=1.0, first=30, cycle=30, funded_extra=dict(best=0.25))
    # 2 Phase Pro: $599 per 100K; 4% then 8%; 4% daily loss; 8% static; 3 profitable days (+0.5%) per phase; funded:
    # $4,000 a day at most, 80% every 10 days; no refund; one account per size; it may not receive copied trades.
    F["FXIFY 2 Phase Pro"] = V3._cfd_2step(size, 599 * K, 0.04, 0.08, dll=0.04, dd=0.08, min_days=0, first=10, cycle=10,
        refund=False, funded_extra=dict(day_profit_cap=4_000 * K))
    for ph in F["FXIFY 2 Phase Pro"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    # FundingPips 2-Step Flex, corrected in version 5 (rules page updated 16 September 2026): no registration-fee refund
    # on Flex; the 95% option needs 3 profitable days (+0.5%) in each evaluation phase as well as in each reward cycle;
    # the 85% option needs one trading day (new accounts from 26 August 2026). Risk per trade idea at most 2% above $25K.
    F["FundingPips 2-Step Flex (95%) v5"] = V3._cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=0,
        split=0.95, refund=False, funded_extra=dict(profit_days=(3, 0.005 * size)))
    for ph in F["FundingPips 2-Step Flex (95%) v5"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    F["FundingPips 2-Step Flex (85%) v5"] = V3._cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=1,
        split=0.85, refund=False)
    # FundingPips Profit Concentration Policy (evaluations bought from 27 June 2026, accounts of $25K and more): if one
    # trade idea makes more than 60% of a phase's target the phase still passes, but the funded account then needs four
    # profitable days (+0.5%) before every reward request, for good. Two ways to live with it:
    #   "cap"   - cap every evaluation trade's win at 55% of the phase target, so it never triggers;
    #   "4days" - let it trigger and meet four profitable days per reward cycle on the funded account.
    f = V3._cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=1, split=0.85, refund=False)
    for ph in f["phases"]:
        ph["max_win"] = 0.55 * ph["target"]          # every trade idea makes at most 55% of the phase target
    F["FundingPips 2-Step Flex (85%) v6 cap"] = f
    F["FundingPips 2-Step Flex (85%) v6 4days"] = V3._cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=1,
        split=0.85, refund=False, funded_extra=dict(profit_days=(4, 0.005 * size)))
    # FundedNext Stellar 2-Step, corrected in version 5 (help centre, updated 2 October 2026): for accounts bought or reset
    # from 12 January 2026 the 15% challenge reward is tied to Scale-Up eligibility, so it is not paid with the first
    # reward; rewards on the default 21-day cycle. Fee refunded with the first reward; 80%.
    F["FundedNext Stellar 2-Step v5"] = V3._cfd_2step(size, 549.99 * K, 0.08, 0.05, min_days=5, first=21, cycle=21)
    # Tier-D firms, rules re-checked in version 5 (4 October 2026):
    # GFT 2-Step Standard: 8% / 5% (not 10% / 5%), 5% daily, 10% static, 3 trading days per phase, 80% every 14 days,
    # first payout needs 3% profit, first two payouts capped at 6%, $524, fee refundable; funded $3,000-a-day cap kept.
    F["GFT 2-Step Standard v5"] = V3._cfd_2step(size, 524 * K, 0.08, 0.05, min_days=3, flat_weekend=True,
        funded_extra=dict(day_profit_cap=3_000 * K, caps=[min(0.06 * size, 10_000)] * 2 + [1e12] * 98, min_payout=0.03 * size))
    # FunderPro Classic: 10% / 5% (not 10% / 8%), 5% daily, 10% static, bi-weekly 80%, fee refunded with the first reward, $431.
    F["FunderPro Classic v5"] = V3._cfd_2step(size, 431 * K, 0.10, 0.05, min_days=0)
    # BrightFunded 2-Step Classic: the fee comes back only with a paid refund add-on; without it, no refund.
    F["BrightFunded 2-Step Classic v5"] = V3._cfd_2step(size, 580 * K, 0.10, 0.05, min_days=5, first=30, refund=False)
    # Blue Guardian 2-Step Standard: $579 list, 8% / 4%, 4% daily, 8% static, 3 profitable days per phase, 85% every
    # 14 days, fee refunded after the fourth payout.
    F["Blue Guardian 2-Step v5"] = V3._cfd_2step(size, 579 * K, 0.08, 0.04, dll=0.04, dd=0.08, min_days=0, split=0.85,
        refund_after=4)
    for ph in F["Blue Guardian 2-Step v5"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    # The5ers High Stakes (New) at the smaller sizes a person may hold next to the 100K account:
    # 3 x 2.5K, 3 x 5K, 3 x 10K, 1 x 25K (and 1 x 50K or 100K). Same rules as the 100K.
    if size in THE5ERS_HS_FEE:
        f = V3._cfd_2step(size, THE5ERS_HS_FEE[size], 0.10, 0.05, min_days=0, flat_weekend=True,
                          buffer_scale=size / 100_000)
        for ph in f["phases"]:
            ph["profit_days"] = (3, 0.005 * size)
        F[f"The5ers High Stakes {size // 1000 if size % 1000 == 0 else size / 1000:g}K"] = f
    return F

def futures_firms():
    return V3.futures_firms()

def rules_for(prog, size=100_000, kind="cfd", fee=None, override=None):
    """A programme's rule set at a given size, with an exact fee where the stored one would be scaled linearly
    (the refund follows the fee actually paid) and safety margins scaled to the account."""
    import copy
    F = cfd_firms(size)[prog] if kind == "cfd" else futures_firms()[prog]
    if fee is None and not override and size == 100_000:
        return F
    F = copy.deepcopy(F)
    if kind == "cfd": F["buffer_scale"] = size / 100_000
    if fee is not None:
        F["fee"] = fee
        if F["funded"].get("refund"): F["funded"]["refund"] = fee
    F.update(override or {})
    return F
