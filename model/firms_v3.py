"""
Firm rule sets used in version 3 (checked October 2026; see the source list in the document).
Amounts are for the stated account size. Where a public source was ambiguous the choice is noted.
Keys follow acct_mc: phases (target, dd, eod, dll, best, min_days, review) and funded
(dd, eod, lock, split, refund/refund_after, first_payout/cycle or futures-style q_days/q_min,
caps, pct_bal, buffer, max_payouts, flat_weekend, day_profit_cap, eval_share).
"""
import copy

def _cfd_2step(size, fee, t1, t2, dll=0.05, dd=0.10, min_days=4, split=0.80, first=14, cycle=14,
               refund_after=1, refund=True, flat_weekend=True, **extra):
    K = size / 100_000
    f = dict(size=size, fee=fee, monthly=False, activation=0, max_risk_rule=None, flat_weekend_eval=True,
        phases=[dict(target=t1 * size, dd=dd * size, eod=False, dll=dll * size, best=None, min_days=min_days, review=1),
                dict(target=t2 * size, dd=dd * size, eod=False, dll=dll * size, best=None, min_days=min_days, review=3)],
        funded=dict(dd=dd * size, eod=False, reset_on_payout=False, lock=None, dll=dll * size, split=split,
                    refund=fee if refund else 0, refund_after=refund_after, first_payout=first, cycle=cycle,
                    ondemand=False, min_payout=0, caps=None, pct_bal=None, q_days=0, q_min=0, best=None,
                    process=1, flat_weekend=flat_weekend))
    f["funded"].update(extra.pop("funded_extra", {}))
    f.update(extra)
    return f

def cfd_firms(size=100_000):
    K = size / 100_000
    F = {}
    # FTMO 2-Step: 10% / 5%, 5% daily, 10% static, 4 trading days per phase, 80%, refund with first
    # payout, payouts every 14 days, no weekend holding on the Standard FTMO Account.
    F["FTMO 2-Step"] = _cfd_2step(size, {50_000: 404, 100_000: 632, 200_000: 1264}.get(size, 632 * K), 0.10, 0.05)
    # FTMO 1-Step: 10%, 3% daily, 10% end-of-day trailing max loss, best day <= 50% of profit, 90% split
    F["FTMO 1-Step"] = dict(size=size, fee={100_000: 584, 200_000: 1168}.get(size, 584 * K), monthly=False,
        activation=0, max_risk_rule=None, flat_weekend_eval=True,
        phases=[dict(target=0.10 * size, dd=0.10 * size, eod=True, dll=0.03 * size, best=0.5, min_days=0, review=3)],
        funded=dict(dd=0.10 * size, eod=True, reset_on_payout=True, lock=None, dll=0.03 * size, split=0.90,
                    refund=584 * K, refund_after=1, first_payout=14, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=0.5, process=1, flat_weekend=True))
    # FundingPips 2-Step Standard: 8% / 5%, 5% daily, 10% static, 3 days, refund with the 4th reward,
    # no weekend holding on Master accounts. Payout options: bi-weekly 80% or monthly 100%.
    F["FundingPips 2-Step (bi-weekly 80%)"] = _cfd_2step(size, 529 * K, 0.08, 0.05, min_days=3, refund_after=4)
    F["FundingPips 2-Step (monthly 100%)"] = _cfd_2step(size, 529 * K, 0.08, 0.05, min_days=3, refund_after=4,
                                                         split=1.0, first=30, cycle=30)
    # FundedNext Stellar 2-Step: 8% / 5%, 5 days, first reward after 21 days then every 14, refund
    # with the first reward, 15% of challenge-phase profits paid with the first reward.
    F["FundedNext Stellar 2-Step"] = _cfd_2step(size, 549.99 * K, 0.08, 0.05, min_days=5, first=21,
                                                 funded_extra=dict(eval_share=0.15))
    # The5ers High Stakes (New): 10% / 5%, 3 profitable days, 80%, refund with first payout.
    F["The5ers High Stakes"] = _cfd_2step(size, 491 * K, 0.10, 0.05, min_days=0, flat_weekend=True)
    for ph in F["The5ers High Stakes"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)      # 3 days of at least +0.5%: daily profit target = remaining / days still needed
    # Alpha Capital Alpha Pro 10%: 10% / 5%, 5% daily (balance), 10% static, 3 days, bi-weekly 80%.
    # Refund policy reported inconsistently: assumed none.
    F["Alpha Capital Pro 10%"] = _cfd_2step(size, 497 * K, 0.10, 0.05, min_days=3, refund=False)
    # FXIFY Two-Phase: 10% / 5%, 5% daily, 10% static (one source says 4% / trailing), 80% every 14
    # days, refund with first payout. Price assumed ~$480 per 100K.
    F["FXIFY Two-Phase"] = _cfd_2step(size, 480 * K, 0.10, 0.05, min_days=0, flat_weekend=True)
    # Goat Funded Trader 2-Step Standard: 10% / 5%, 5% daily, 10% static, 80% bi-weekly, refundable
    # fee; funded: daily profit capped at $3,000 and the first two payouts at 6% of the account.
    F["GFT 2-Step Standard"] = _cfd_2step(size, 524 * K, 0.10, 0.05, min_days=0, flat_weekend=True,
        funded_extra=dict(day_profit_cap=3_000 * K, caps=[0.06 * size, 0.06 * size] + [1e12] * 98))
    # ---- variants tested in version 3.1
    # FundingPips 2-Step Flex: $499, 10% / 6%, 4% daily, 12% static, no minimum days, bi-weekly 85%,
    # risk per trade idea on Master accounts 2% (plan uses 1.5%); refund assumed with the 4th reward as on Standard
    F["FundingPips 2-Step Flex (85%)"] = _cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=0,
                                                     split=0.85, refund_after=4)
    F["FundingPips 2-Step Flex (95%)"] = _cfd_2step(size, 499 * K, 0.10, 0.06, dll=0.04, dd=0.12, min_days=0,
        split=0.95, refund_after=4, funded_extra=dict(profit_days=(3, 0.005 * size)))
    # The5ers High Stakes Classic: 8% / 5% at $545, otherwise as New
    F["The5ers High Stakes Classic"] = _cfd_2step(size, 545 * K, 0.08, 0.05, min_days=0, flat_weekend=True)
    for ph in F["The5ers High Stakes Classic"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    # FundingPips 2-Step Standard with on-demand rewards: 90%, each request needs >= 2% profit and no day > 35%
    F["FundingPips 2-Step (on-demand 90%)"] = _cfd_2step(size, 529 * K, 0.08, 0.05, min_days=3, refund_after=4,
        split=0.90, first=0, cycle=1, funded_extra=dict(ondemand=True, min_payout=0.02 * size, best=0.35))
    # Alpha Capital Pro 10% with on-demand payouts: >= 2% gross profit, best day <= 40%
    F["Alpha Capital Pro 10% (on-demand)"] = _cfd_2step(size, 497 * K, 0.10, 0.05, min_days=3, refund=False,
        first=0, cycle=1, funded_extra=dict(ondemand=True, min_payout=0.02 * size, best=0.40))
    # ---- additional firms checked in version 3.1 (October 2026, secondary sources; confirm before buying)
    # BrightFunded 2-Step Classic: EUR 497 (~$580), 10% / 5%, 5% daily, 10% static, 5 days per phase,
    # first payout 30 days after the funded account opens, then every 14 days, 80%, fee refunded with first payout,
    # $400,000 funded cap (evaluations unlimited), copying between own accounts allowed
    F["BrightFunded 2-Step Classic"] = _cfd_2step(size, 580 * K, 0.10, 0.05, min_days=5, first=30)
    # Blue Guardian 2-Step Standard: $497, 8% / 4%, 4% daily, 8% max, 3 days, 85% bi-weekly, refund not assumed,
    # $400,000 cap, copying between own accounts allowed
    F["Blue Guardian 2-Step"] = _cfd_2step(size, 497 * K, 0.08, 0.04, dll=0.04, dd=0.08, min_days=3, split=0.85,
                                           refund=False)
    # FunderPro Classic: $431, 10% / 8%, 5% daily, 10% static, no minimum days, bi-weekly 80%,
    # fee refunded with first reward, $200,000 cap, copying between own accounts allowed
    F["FunderPro Classic"] = _cfd_2step(size, 431 * K, 0.10, 0.08, min_days=0)
    # Maven 2-Step: $440, 8% / 5%, 4% daily, 8% static, 3 profitable days (>= 0.5%) per phase, 80%,
    # payouts about every 10 business days, refund with the 3rd payout, $200,000 cap, $10,000 payouts per 30 days
    F["Maven 2-Step"] = _cfd_2step(size, 440 * K, 0.08, 0.05, dll=0.04, dd=0.08, min_days=0, refund_after=3,
                                   funded_extra=dict(best=0.5))
    for ph in F["Maven 2-Step"]["phases"]:
        ph["profit_days"] = (3, 0.005 * size)
    return F

def futures_firms():
    """50K accounts traded with micro Nasdaq futures."""
    F = {}
    # Apex 50K EOD (rules after the 2026 '4.0' update): $3,000 target, $2,000 EOD trailing,
    # $1,000 daily loss, no evaluation consistency. Performance account: 100% of approved payout,
    # 5 qualifying days per request, best day < 50% of the request's profit, $500 minimum,
    # safety net = drawdown + $100, caps per request, at most 6 requests; floor stops trailing at +$100.
    F["Apex 50K EOD"] = dict(size=50_000, fee=490, monthly=False, activation=0, max_risk_rule=None, flat_daily=20,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=1_000, best=None, min_days=1, review=1)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=100.0, lock_after_first_payout=False,
                    dll=1_000, split=1.0, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=500, caps=[1500, 1500, 2000, 2500, 2500, 3000], pct_bal=None, q_days=5,
                    q_min=250, best=0.5, process=1, max_payouts=6, buffer=2_100.0))
    # Topstep 50K (Standard path): $49 a month + $149 activation; $3,000 target, $2,000 EOD trailing,
    # best day <= 50% of the target. Express Funded: 5 winning days of $150+, up to 50% of the
    # balance, capped at $2,000, 90%; after the first payout the floor sits at the starting balance.
    F["Topstep 50K"] = dict(size=50_000, fee=49, monthly=True, activation=149, max_risk_rule=None, flat_daily=20,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=None, best=0.5, min_days=2, review=1)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=0.0, lock_after_first_payout=True,
                    dll=None, split=0.90, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=0, caps=[2000] * 99, pct_bal=0.5, q_days=5, q_min=150, best=None, process=1))
    # Tradeify Select 50K (Flex payouts): $165 one-time; $3,000 target, $2,000 EOD, best day <= 40%,
    # 3 days. Funded: every 5 winning days, up to 50% of profit, cap $3,000, 90%; floor locks at +$100.
    F["Tradeify Select 50K"] = dict(size=50_000, fee=165, monthly=False, activation=0, max_risk_rule=None, flat_daily=20,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=None, best=0.4, min_days=3, review=1)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=100.0, lock_after_first_payout=False,
                    dll=None, split=0.90, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=0, caps=[3000] * 99, pct_bal=0.5, q_days=5, q_min=150, best=None, process=1))
    # Lucid Flex 50K: $146; $3,000 target, $2,000 EOD, best day <= 50%. Funded: 5 profitable days of
    # $150+, up to 50% of profit capped at $2,000, 90%; floor assumed to lock at +$100.
    F["Lucid Flex 50K"] = dict(size=50_000, fee=146, monthly=False, activation=0, max_risk_rule=None, flat_daily=20,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=None, best=0.5, min_days=2, review=1)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=100.0, lock_after_first_payout=False,
                    dll=None, split=0.90, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=0, caps=[2000] * 99, pct_bal=0.5, q_days=5, q_min=150, best=None, process=1))
    return F
