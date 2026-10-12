"""
Version 10 rule sets: version 9's (firms_v9) with the corrections of the review of version 9 (11-12 October 2026) and of a
complete inventory of every firm's rules (rules_inventory_v10.json lists each rule with its source and how the model
treats it). Changes from version 9:
  payouts, every firm  a request is a state, not an instant (review of version 9, findings 1, 2, 20): it is made at
                       least 15 minutes after the last close with the account flat (FundingPips' rule, applied
                       everywhere); it is pending for the firm's stated review time, and a breach before it is processed
                       cancels it (the cautious reading where a firm says nothing); Alpha Capital ("your account will
                       remain locked while the payout is processed"), FundingPips (trading disabled during processing)
                       and FXIFY ("the account becomes read-only until the withdrawal is approved") lock the account
                       until it is processed; Topstep deducts it at once and protects it; the plan pauses an Apex account
                       while its request is pending (a request is denied if the balance falls below the threshold)
  news                 the plan is flat around high-impact releases wherever a firm restricts news at that stage
                       (news_v10); version 9 stated the policy but had no news calendar, so its headline was a model
                       without news restrictions, as its section 6.5 said (n22)
  The5ers              payout cap per request ($4,000 at 100K, $3,000 at 50K; smaller sizes unpublished: 4% of the size
                       assumed, the lowest published ratio), counted with the fee refund inside it (the cautious
                       reading; the cap's basis is unpublished); a request needs $500 of profit at 100K ($300 at 50K,
                       0.6% assumed below); the refund is 70% of the cash actually paid for the account, not of the fee
                       (hub credit is not refunded: review of version 9, findings 16, 17); the next request counts from
                       the last approved one; the plan keeps the balance under the 10% scaling milestone
                       (profit_ceiling 9.5%), so the account is never scaled and its rules stay those modelled
  Blue Guardian        funded Guardian Shield: a position whose floating loss reaches 2% of the account is closed;
                       the first time the split falls to 50% for good, the second time the account is breached
                       (review of version 9, finding 6)
  Alpha Capital        funded accounts hold at most 40 lots per $100K at a time (review of version 9, finding 4)
  GFT                  funded accounts: the profit of a trade held under a minute is removed (accounts bought from
                       6 October 2026)
  Topstep              the session of a request does not count toward the next five winning days; a payout must be at
                       least $125 (taken as $125 after the split, the cautious reading) (review of version 9, findings
                       18, 19)
  Apex                 the evaluation expires at 6 p.m. New York time on its 30th day (review of version 9, finding 13);
                       the best day of the cycle, today's included, must stay under 50% of the cycle's profit (finding 21)
  minimum payouts      every published minimum is applied to the trader's share after the split (min_net), the stricter
                       reading where a page does not say whether it counts before or after the split; FTMO's $20, in
                       the rules read on 11 October 2026, was missing from version 9 (found by comparing every row of
                       rules_inventory_v10.json with these parameters)
"""
import copy
import firms_v9 as F9

TIER = dict(F9.TIER)
firm_of = F9.firm_of
CONC = F9.CONC
EUR = F9.EUR

# payout processing: review = working days until the request is processed (approved and deducted); a breach before then
# cancels it unless the firm protects it; lock_processing / pause_pending: nothing is traded until then; transfer = working
# days from processing to the cash (rules_inventory_v10.json: each firm's stated time, its upper end where a range is given)
PROC = {
    "FTMO":          dict(review_bd=2, transfer_bd=2),            # review 1-2 working days, sent 1-2 working days after
    "FundingPips":   dict(review_bd=3, transfer_bd=0, lock_processing=True),   # 1-3 working days, trading disabled
    "FundedNext":    dict(review_bd=1, transfer_bd=0),            # paid within 24 hours of the request
    "The5ers":       dict(review_bd=2, transfer_bd=3, cycle_from_processed=True),  # review 24-48 business hours, then up to 3
    "FXIFY":         dict(review_bd=3, transfer_bd=0, lock_processing=True),   # within 3 business days; read-only until approved
    "Fintokei":      dict(review_bd=0, transfer_bd=1),            # approved automatically; sent within 1 business day
    "Hola Prime":    dict(review_bd=0, review_h=1.0, transfer_bd=0),   # paid within one hour of the request
    "Alpha Capital": dict(review_bd=2, transfer_bd=0, lock_processing=True),   # paid within 2 business days, account locked
    "GFT":           dict(review_bd=2, transfer_bd=0),            # processed within 2 business days
    "FunderPro":     dict(review_bd=1, transfer_bd=1),            # approval, then within 1 working day
    "BrightFunded":  dict(review_bd=1, transfer_bd=1),            # processed within a day
    "Blue Guardian": dict(review_bd=1, transfer_bd=0),            # 24 business hours
    "Maven":         dict(review_bd=3, transfer_bd=0),            # not stated: three working days assumed
    "Topstep":       dict(protected=True, review_bd=0, transfer_bd=6),  # deducted at the request; approval and ACH 1-3 each
    "Apex":          dict(pause_pending=True, review_bd=2, transfer_bd=1),  # automated, 24-48 hours; the plan pauses
}
# news: firms that restrict trading around high-impact releases, by stage ("all": every release that moves the market;
# "cpi": US CPI only)
NEWS_FUNDED = {"FTMO", "FundingPips", "FundedNext", "The5ers", "FXIFY", "Alpha Capital", "GFT", "FunderPro", "BrightFunded",
               "Blue Guardian", "Maven"}
NEWS_EVAL = {"The5ers", "FXIFY", "GFT", "Maven"}

THE5ERS_CAP = {100_000: 4_000.0, 50_000: 3_000.0}
THE5ERS_MIN_PROFIT = {100_000: 500.0, 50_000: 300.0}
MIN_PAYOUT = {"FTMO": 20.0}          # minimums missing from version 9's rule sets (the others are set in firms_v8)

def _v10(F, size=None):
    for name, f in F.items():
        firm = firm_of(name); fd = f["funded"]
        fd.update(PROC.get(firm, {}))
        fd["req_wait"] = 0.25
        fd["news"] = "cpi" if firm == "Topstep" else ("all" if firm in NEWS_FUNDED else None)
        for ph in f["phases"]:
            ph["news"] = "cpi" if firm == "Topstep" else ("all" if firm in NEWS_EVAL else None)
        if f.get("no_fillers"):
            f["no_target_buffer"] = True          # missing days are ordinary trades: no buffer above the target
        # a published minimum payout counts on the trader's share after the split (the stricter reading); a request
        # still needs the minimum as profit before the split (min_payout)
        mp = max(float(fd.get("min_payout") or 0.0), MIN_PAYOUT.get(firm, 0.0))
        fd["min_payout"] = mp
        if mp > 0: fd["min_net"] = max(float(fd.get("min_net") or 0.0), mp)
        sz = f.get("size", size or 100_000)
        if firm == "The5ers":
            fd["caps"] = [THE5ERS_CAP.get(sz, 0.04 * sz)] * 100
            fd["cap_includes_refund"] = True
            fd["min_profit"] = THE5ERS_MIN_PROFIT.get(sz, 0.006 * sz)
            fd["min_net"] = 150.0; fd["min_payout"] = 0.0
            fd["profit_ceiling"] = 0.095 * sz
        if firm == "Blue Guardian":
            fd["shield"] = 0.02 * sz; fd["shield_split"] = 0.50
        if firm == "Alpha Capital":
            fd["max_lots"] = 40.0 * sz / 100_000
        if firm == "GFT":
            fd["void_min"] = 1.0
        if firm == "Topstep":
            fd["min_net"] = 125.0
            fd["session_tz"] = "America/Chicago"      # request after the session's 4 p.m. lock; its session excluded
        if firm == "Apex":
            f["phases"][0]["expiry_local"] = (18, "America/New_York")
    return F

def cfd_firms(size=100_000):
    return _v10(F9.cfd_firms(size), size)

def futures_firms():
    return _v10(F9.futures_firms())

def _apply_fee(F, fee):
    F9._apply_fee(F, fee)

def rules_for(prog, size=100_000, kind="cfd", fee=None, override=None):
    """A programme's rule set at a given size, with an exact fee where given (the refund follows the fee actually
    paid) and safety margins scaled to the account."""
    F = copy.deepcopy(cfd_firms(size)[prog] if kind == "cfd" else futures_firms()[prog])
    if kind == "cfd": F["buffer_scale"] = size / 100_000
    _apply_fee(F, F["fee"] if fee is None else fee)
    F.update(override or {})
    return F

SOURCES = dict(F9.SOURCES)
SOURCES.update({
    "Alpha payouts": "https://help.alphacapitalgroup.uk/en/articles/6933755-how-do-i-get-paid-performance-fees",
    "Alpha lot limits": "https://help.alphacapitalgroup.uk/en/articles/6934289-what-is-the-lot-size-limit-on-qualified-analyst-accounts",
    "The5ers High Stakes rules": "https://the5ers.com/faqs/what-are-the-general-rules-for-the-high-stakes-program/",
    "The5ers payout policy": "https://the5ers.com/faqs/payout-policy-and-hub-credit-in-the-high-stakes-program/",
    "Topstep payout policy": "https://help.topstep.com/en/articles/8284233-topstep-payout-policy",
    "FTMO news": "https://ftmo.com/en/faq/can-i-trade-news/",
    "FXIFY payouts": "https://fxify.com/faqs/all-faqs/how-do-i-withdraw-my-profits/",
})
