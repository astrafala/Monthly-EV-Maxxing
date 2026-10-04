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
