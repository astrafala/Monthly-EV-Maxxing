"""
Version 9 rule sets: version 8's (firms_v8) with the corrections of the review of version 8 (5 October 2026), each checked
again on the firm's own page (SOURCES below; rules_snapshot_v9.json quotes the sentences used).
Changes from version 8:
  Blue Guardian       "The minimum holding time is 2 minutes. If a trade is closed in under 2 minutes, it may be flagged
                      for tick scalping": the plan places its bracket only after 3 minutes (hold_min), and a trade that
                      could still close sooner (only a breach can) is treated as ending the account (short_breach)
  Alpha Capital       the 2-minute rule is checked on the account's own trades at every phase pass and payout request:
                      average duration above 2 minutes, most trades above 2 minutes, at least half of the gross profit from
                      trades above 2 minutes; a failure restarts the evaluation, or removes the funded profits (dur_rule).
                      No minimal-lot filler trades ("the use of minimal lots to pass trading days ... is not allowed")
  BrightFunded        a day counts as a trading day only if a trade on it was open for at least 60 seconds
  Fintokei            no filler trades: its all-in article objects to "much smaller trades ... just to meet the minimum
                      3-day trading requirement"; the 40% concentration policy already needs three winning days per phase,
                      and a funded cycle short of its 3 trading days collects them with ordinary trades, one a day.
                      The next payout may be requested 14 days after the last successfully processed payout
                      (cycle_from_processed), not after the request
  Hola Prime          the bi-weekly payout needs 3 profitable days within a 14-day period: counted in a window of 14
                      calendar days ending on the request day (profit_days_window), not since the last payout
  every firm          phase reviews and payout processing in working days (Monday to Friday), not calendar days
Filler trades elsewhere (FTMO, FundedNext, FXIFY, FunderPro, BrightFunded, Hola Prime phases, futures): a real 0.01-lot (one
contract) position closed after 3 minutes, with its cost and result, on each missing day. The firms' day definitions count
a day on which a position is opened (FTMO: "any day ... during which at least one position is opened") and state no
minimum volume; that such a trade is accepted is an assumption of the model, measured by the no-filler sensitivity.
"""
import copy
import firms_v8 as F8

TIER = dict(F8.TIER)
firm_of = F8.firm_of
CONC = F8.CONC
EUR = F8.EUR

def _v9(F):
    for name, f in F.items():
        if name.startswith("Blue Guardian"):
            f["hold_min"] = 3; f["short_breach"] = True
        if name.startswith("Alpha Capital"):
            f["dur_rule"] = 2.0; f["no_fillers"] = True
        if name.startswith("BrightFunded"):
            f["day_min_minutes"] = 1.0
        if name.startswith("Fintokei"):
            f["no_fillers"] = True; f["funded"]["cycle_from_processed"] = True
        if name.startswith("Hola Prime"):
            f["funded"]["profit_days_window"] = 14
    return F

def cfd_firms(size=100_000):
    return _v9(F8.cfd_firms(size))

def futures_firms():
    return _v9(F8.futures_firms())

def _apply_fee(F, fee):
    F8._apply_fee(F, fee)

def rules_for(prog, size=100_000, kind="cfd", fee=None, override=None):
    """A programme's rule set at a given size, with an exact fee where given (the refund follows the fee actually
    paid) and safety margins scaled to the account."""
    F = copy.deepcopy(cfd_firms(size)[prog] if kind == "cfd" else futures_firms()[prog])
    if kind == "cfd": F["buffer_scale"] = size / 100_000
    _apply_fee(F, F["fee"] if fee is None else fee)
    F.update(override or {})
    return F

SOURCES = dict(F8.SOURCES)
SOURCES.update({
    "Blue Guardian 2-Step": "https://help.blueguardian.com/en/articles/14062291-2-step-standard-rules",
    "BrightFunded trading day": "https://help.brightfunded.com/en/articles/9241611-what-are-the-current-rules-for-the-evaluation-process",
    "Fintokei trading days": "https://support.fintokei.com/en/articles/8428030-what-does-the-rule-minimum-trading-days-mean-3-or-5-days",
    "Fintokei payouts": "https://support.fintokei.com/en/articles/6538884-how-and-how-often-can-i-withdraw-my-performance-rewards-and-what-is-the-minimum-amount",
    "Hola Prime 2-Step Prime": "https://holaprime.com/forex/faq/hola-prime-challenges/hola-prime-2-step-prime-challenge/",
    "FTMO trading objectives": "https://ftmo.com/en/trading-objectives/",
})
