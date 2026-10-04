"""
Account-type dataset (as published Sept/Oct 2026; promo pricing changes weekly).
Units: USD (EUR prices converted at 1.17). Sizes: 100K for CFD/forex, 50K for futures.
phase tuple: (target $, max-loss $, dd_type, daily-loss $ or None, best-day cap $ or None)
dd_type: 'static' | 'eod' (end-of-day trailing) | 'intraday' (trailing on live equity)
funded: dict(kind=..., D=$, split=, c=lock offset, cap=total payout cap or None,
             refund=$ refunded, refund_after=n-th payout)
'conf' marks how sure we are of the rule set: 'high' (official page / multiple sources),
'med' (one aggregator), 'low' (inferred: phase-2 target or funded terms not published).
"""
EUR = 1.17

F = []

def add(firm, prog, market, size, fee, phases, funded, activation=0.0, monthly=False,
        conf="med", note=""):
    F.append(dict(firm=firm, prog=prog, market=market, size=size, fee=fee, phases=phases,
                  funded=funded, activation=activation, monthly=monthly, conf=conf, note=note))

K = 1000
# ------------------------------------------------------------------ CFD / forex, 100K
add("FTMO", "2-Step", "CFD", 100*K, 540*EUR,
    [(10*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=540*EUR, refund_after=1), conf="high",
    note="80% split (90% via scaling); fee refunded with 1st reward")
add("FTMO", "1-Step", "CFD", 100*K, 499*EUR,
    [(10*K, 10*K, "eod", 3*K, 5*K)],
    dict(kind="static", D=10*K, split=0.90, refund=499*EUR, refund_after=1), conf="high",
    note="EOD trailing max loss, resets on reward; best-day 50% rule")
add("The5ers", "High Stakes 2-Step", "CFD", 100*K, 545,
    [(8*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=545, refund_after=1), conf="med")
add("FundedNext", "Stellar 2-Step", "CFD", 100*K, 549.99,
    [(8*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=549.99, refund_after=1), conf="high",
    note="+15% reward share on challenge profit (ignored)")
add("FundedNext", "Stellar 1-Step", "CFD", 100*K, 569.99,
    [(10*K, 6*K, "static", 3*K, None)],
    dict(kind="static", D=6*K, split=0.90, refund=0, refund_after=1), conf="med")
add("FundedNext", "Stellar Lite", "CFD", 100*K, 399.99,
    [(8*K, 8*K, "static", 4*K, None), (4*K, 8*K, "static", 4*K, None)],
    dict(kind="static", D=8*K, split=0.80, refund=0, refund_after=1), conf="med")
add("FundingPips", "2-Step", "CFD", 100*K, 529,
    [(8*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=529, refund_after=4), conf="high",
    note="refund after 4th payout; split 60-100% by payout frequency")
add("FundingPips", "2-Step Pro", "CFD", 100*K, 399,
    [(6*K, 6*K, "static", 3*K, 2.7*K), (6*K, 6*K, "static", 3*K, 2.7*K)],
    dict(kind="static", D=6*K, split=0.80, refund=0, refund_after=1), conf="med",
    note="45% consistency")
add("FundingPips", "1-Step", "CFD", 100*K, 555,
    [(10*K, 6*K, "static", 3*K, None)],
    dict(kind="static", D=6*K, split=0.80, refund=555, refund_after=4), conf="med")
add("FundingPips", "Zero (instant)", "CFD", 100*K, 499, [],
    dict(kind="trail", D=5*K, split=0.95, c=0.0, cap=None, intraday=True), conf="med",
    note="5% intraday trailing; 15% daily-profit consistency; 3% buffer")
add("Alpha Capital", "Alpha Pro 10%", "CFD", 100*K, 497,
    [(10*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=497, refund_after=1), conf="low",
    note="phase-2 target assumed 5%")
add("Alpha Capital", "Alpha Pro 8%", "CFD", 100*K, 577,
    [(8*K, 8*K, "static", 4*K, None), (5*K, 8*K, "static", 4*K, None)],
    dict(kind="static", D=8*K, split=0.80, refund=577, refund_after=1), conf="low")
add("Alpha Capital", "Alpha Three", "CFD", 100*K, 397,
    [(8*K, 6*K, "static", 4*K, None), (8*K, 6*K, "static", 4*K, None), (8*K, 6*K, "static", 4*K, None)],
    dict(kind="static", D=6*K, split=0.80, refund=0, refund_after=1), conf="low",
    note="3-step; per-phase targets assumed equal")
add("Blue Guardian", "2-Step Pro", "CFD", 100*K, 464,
    [(10*K, 10*K, "eod", 4*K, None), (10*K, 10*K, "eod", 4*K, None)],
    dict(kind="static", D=10*K, split=0.85, refund=0, refund_after=1), conf="low",
    note="EOD trailing DD; funded modelled as reset-on-payout")
add("Blue Guardian", "Instant", "CFD", 100*K, 779, [],
    dict(kind="trail", D=6*K, split=0.80, c=0.0, cap=None), conf="med",
    note="6% EOD trailing, 3% DLL")
add("Maven", "2-Step", "CFD", 100*K, 396,
    [(8*K, 8*K, "static", 4*K, None), (5*K, 8*K, "static", 4*K, None)],
    dict(kind="static", D=8*K, split=0.80, refund=0, refund_after=1), conf="low")
add("Maven", "3-Step", "CFD", 100*K, 269.10,
    [(3*K, 3*K, "static", 2*K, None), (3*K, 3*K, "static", 2*K, None), (3*K, 3*K, "static", 2*K, None)],
    dict(kind="static", D=3*K, split=0.80, refund=0, refund_after=1), conf="low")
add("Goat Funded", "2-Step Standard", "CFD", 100*K, 594,
    [(10*K, 10*K, "static", 5*K, None), (5*K, 10*K, "static", 5*K, None)],
    dict(kind="static", D=10*K, split=0.80, refund=0, refund_after=1), conf="low")
add("Goat Funded", "3-Step GOAT", "CFD", 100*K, 365,
    [(6*K, 8*K, "static", 4*K, None), (6*K, 8*K, "static", 4*K, None), (6*K, 8*K, "static", 4*K, None)],
    dict(kind="static", D=8*K, split=0.80, refund=0, refund_after=1), conf="low")
add("Goat Funded", "Instant GOAT", "CFD", 100*K, 838, [],
    dict(kind="trail", D=6*K, split=0.80, c=0.0, cap=None), conf="med")
add("E8 Markets", "E8 One (6% DD)", "CFD", 100*K, 463.60,
    [(9*K, 6*K, "eod", 4*K, None)],
    dict(kind="trail", D=6*K, split=0.80, c=0.0, cap=None), conf="low",
    note="target for 6% tier assumed 9%")

# ------------------------------------------------------------------ futures, 50K
add("Topstep", "Combine 50K (Standard)", "Futures", 50*K, 49,
    [(3*K, 2*K, "eod", None, 1.5*K)],
    dict(kind="trail", D=2*K, split=0.90, c=0.0, cap=None), activation=149, monthly=True,
    conf="high", note="XFA starts at $0, MLL locks at $0 after 1st payout")
add("Topstep", "Combine 50K (No-Activation)", "Futures", 50*K, 109,
    [(3*K, 2*K, "eod", None, 1.5*K)],
    dict(kind="trail", D=2*K, split=0.90, c=0.0, cap=None), activation=0, monthly=True,
    conf="med")
add("Apex", "50K EOD", "Futures", 50*K, 197 - 139,
    [(3*K, 2*K, "eod", 1*K, None)],
    dict(kind="trail", D=2*K, split=1.00, c=100.0, cap=13*K), activation=139,
    conf="high", note="6 payouts max, ladder $1.5k..$3k, total $13k")
add("Apex", "50K Intraday", "Futures", 50*K, 131 - 99,
    [(3*K, 2*K, "intraday", None, None)],
    dict(kind="trail", D=2*K, split=1.00, c=100.0, cap=14.5*K, intraday=True), activation=99,
    conf="high")
add("Tradeify", "Growth 50K", "Futures", 50*K, 139,
    [(3*K, 2*K, "eod", 1.25*K, None)],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=None), conf="med",
    note="35% consistency once funded")
add("Tradeify", "Select 50K", "Futures", 50*K, 159,
    [(3*K, 2*K, "eod", None, 1.2*K)],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=None), conf="med",
    note="40% eval consistency, min 3 days")
add("Tradeify", "Lightning 25K (instant)", "Futures", 25*K, 329, [],
    dict(kind="trail", D=1*K, split=0.90, c=100.0, cap=None), conf="med")
add("Lucid", "Flex 50K", "Futures", 50*K, 130,
    [(3*K, 2*K, "eod", None, None)],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=10*K), conf="med",
    note="5 payouts x $2k cap, then moved to live")
add("Lucid", "Pro 50K", "Futures", 50*K, 185,
    [(3*K, 2*K, "eod", 1.2*K, None)],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=None), conf="med")
add("Lucid", "Direct 50K (instant)", "Futures", 50*K, 520, [],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=None), conf="med")
add("Take Profit Trader", "PRO 50K", "Futures", 50*K, 170,
    [(3*K, 2*K, "eod", None, None)],
    dict(kind="trail", D=2*K, split=0.80, c=0.0, cap=None, intraday=True), activation=130,
    conf="med", note="PRO funded uses intraday trailing")
add("My Funded Futures", "Flex 50K", "Futures", 50*K, 107,
    [(3*K, 2*K, "eod", None, 1.5*K)],
    dict(kind="trail", D=2*K, split=0.80, c=100.0, cap=None), monthly=True, conf="med")
add("My Funded Futures", "Rapid 50K", "Futures", 50*K, 157,
    [(3*K, 2*K, "intraday", None, None)],
    dict(kind="trail", D=2*K, split=0.90, c=100.0, cap=None, intraday=True), monthly=True,
    conf="med")
add("Bulenox", "50K Opt.2 (EOD)", "Futures", 50*K, 175,
    [(3*K, 2.5*K, "eod", 1.1*K, 1.2*K)],
    dict(kind="trail", D=2.5*K, split=1.00, c=100.0, cap=None), activation=148, monthly=True,
    conf="med", note="40% consistency")
add("Bulenox", "50K Opt.1 (intraday)", "Futures", 50*K, 175,
    [(3*K, 2.5*K, "intraday", None, None)],
    dict(kind="trail", D=2.5*K, split=1.00, c=100.0, cap=None, intraday=True), activation=148,
    monthly=True, conf="med")
add("The5ers", "Futures Basecamp 50K", "Futures", 50*K, 100,
    [(3*K, 1.5*K, "static", None, None)],
    dict(kind="trail", D=1.5*K, split=0.80, c=0.0, cap=None), conf="low",
    note="3% static per aggregator; funded terms assumed")
