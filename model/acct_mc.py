"""
Account-level Monte Carlo with calendar time, driven by per-instrument calibration.

Each trade: risk l (<= L, the room above the floor, and the room left in today's loss limit),
target w = min(k*l, distance to phase target). Full-size trades use the measured real-data
edge for (instrument, stop, k); partial-target trades are fair minus costs. Trade duration
(calendar hours, including waiting for the next allowed entry) is drawn from the measured
distribution. Clock, trading days, daily loss limits, end-of-day trailing floors, best-day
consistency caps, payout calendars, caps, refunds and fees follow each firm's rules.
"""
import json, math, random

DAY = 24.0
PAYLOG = None      # if a list, run_funded appends (clock_hours, cash) for every payout

def firm_defs(size=100_000):
    K = size / 100_000
    F = {}
    F["FTMO 2-Step"] = dict(size=size, fee=632 * K, monthly=False, activation=0,
        phases=[dict(target=10_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=4, review=1),
                dict(target=5_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=4, review=3)],
        funded=dict(dd=10_000*K, eod=False, reset_on_payout=False, lock=None, dll=5_000*K, split=0.80,
                    refund=632*K, refund_after=1, first_payout=14, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=None)
    F["FTMO 1-Step"] = dict(size=size, fee=584 * K, monthly=False, activation=0,
        phases=[dict(target=10_000*K, dd=10_000*K, eod=True, dll=3_000*K, best=0.5, min_days=0, review=3)],
        funded=dict(dd=10_000*K, eod=True, reset_on_payout=True, lock=None, dll=3_000*K, split=0.90,
                    refund=584*K, refund_after=1, first_payout=14, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=0.5, process=1),
        max_risk_rule=None)
    F["FundingPips 2-Step (bi-weekly 80%)"] = dict(size=size, fee=529*K, monthly=False, activation=0,
        phases=[dict(target=8_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=3, review=1),
                dict(target=5_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=3, review=2)],
        funded=dict(dd=10_000*K, eod=False, reset_on_payout=False, lock=None, dll=5_000*K, split=0.80,
                    refund=529*K, refund_after=4, first_payout=14, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=None)
    F["FundingPips 2-Step (weekly 60%)"] = json.loads(json.dumps(F["FundingPips 2-Step (bi-weekly 80%)"]))
    F["FundingPips 2-Step (weekly 60%)"]["funded"].update(split=0.60, first_payout=7, cycle=7)
    F["FundedNext Stellar 2-Step"] = dict(size=size, fee=550*K, monthly=False, activation=0,
        phases=[dict(target=8_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=5, review=1),
                dict(target=5_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=5, review=2)],
        funded=dict(dd=10_000*K, eod=False, reset_on_payout=False, lock=None, dll=5_000*K, split=0.80,
                    refund=550*K, refund_after=1, first_payout=21, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=None)
    F["The5ers High Stakes"] = dict(size=size, fee=545*K, monthly=False, activation=0,
        phases=[dict(target=8_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=3, review=1),
                dict(target=5_000*K, dd=10_000*K, eod=False, dll=5_000*K, best=None, min_days=3, review=2)],
        funded=dict(dd=10_000*K, eod=False, reset_on_payout=False, lock=None, dll=5_000*K, split=0.80,
                    refund=545*K, refund_after=1, first_payout=14, cycle=14, ondemand=False, min_payout=0,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=None)
    F["Breakout 2-Step (crypto)"] = dict(size=size, fee=725*K, monthly=False, activation=0,
        phases=[dict(target=5_000*K, dd=6_000*K, eod=False, dll=4_000*K, best=None, min_days=0, review=1),
                dict(target=10_000*K, dd=6_000*K, eod=False, dll=4_000*K, best=None, min_days=0, review=2)],
        funded=dict(dd=6_000*K, eod=False, reset_on_payout=False, lock=None, dll=4_000*K, split=0.80,
                    refund=725*K, refund_after=1, first_payout=1, cycle=1, ondemand=True, min_payout=50,
                    caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=None)
    F["HyroTrader 2-Step (crypto)"] = dict(size=size, fee=599*K, monthly=False, activation=0,
        phases=[dict(target=10_000*K, dd=10_000*K, eod=False, dll=5_000*K, dll_trailing=True, best=None, min_days=10, review=1),
                dict(target=5_000*K, dd=10_000*K, eod=False, dll=5_000*K, dll_trailing=True, best=None, min_days=5, review=2)],
        funded=dict(dd=10_000*K, eod=False, reset_on_payout=False, lock=None, dll=5_000*K, dll_trailing=True,
                    split=0.70, refund=599*K, refund_after=1, first_payout=1, cycle=1, ondemand=True,
                    min_payout=100, caps=None, pct_bal=None, q_days=0, q_min=0, best=None, process=1),
        max_risk_rule=3_000*K)
    return F

def futures_defs():
    F = {}
    F["Topstep 50K"] = dict(size=50_000, fee=49, monthly=True, activation=149,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=None, best=0.5, min_days=2, review=1, lock=None)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=0.0, lock_after_first_payout=True,
                    dll=None, split=0.90, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=0, caps=[5000]*99, pct_bal=0.5, q_days=5, q_min=150, best=None, process=1),
        max_risk_rule=None)
    F["Apex 50K EOD"] = dict(size=50_000, fee=58, monthly=False, activation=139,
        phases=[dict(target=3_000, dd=2_000, eod=True, dll=1_000, best=None, min_days=1, review=1, lock=None)],
        funded=dict(dd=2_000, eod=True, reset_on_payout=False, lock=100.0, lock_after_first_payout=False,
                    dll=1_000, split=1.0, refund=0, refund_after=1, first_payout=0, cycle=0, ondemand=True,
                    min_payout=500, caps=[1500, 1500, 2000, 2500, 2500, 3000], pct_bal=None, q_days=5,
                    q_min=250, best=0.5, process=1, max_payouts=6, buffer=600.0),
        max_risk_rule=None)
    return F


class Trader:
    def __init__(self, cal_point, L, k, rng):
        self.g = cal_point; self.L = L; self.k = k; self.rng = rng
        self.e = cal_point["edge"]                      # per full-size trade, units of risk
        self.cost = cal_point["kappa"] + cal_point["phi"]
        self.dur = cal_point["dur"]

    def trade(self, l, w, clock=None, flat_weekend=False):
        """returns (pnl, hours)"""
        if w >= self.k * l * 0.999:
            p = (1 + self.e) / (1 + self.k)
        else:
            p = (l - self.cost * l) / (w + l)
        p = min(max(p, 0.0), 1.0)
        hrs = self.dur[self.rng.randrange(len(self.dur))]
        if w < self.k * l * 0.999:   # nearer target resolves sooner (fair-walk time ~ w*l)
            hrs = max(1.0, hrs * (w / (self.k * l)))
        return (w if self.rng.random() < p else -l), hrs


def run_stage(st, tr, rng, firm, clock, eval_phase=True, fund=None):
    """Evaluation phase. Returns (passed, clock)."""
    A, dd, eod, dll = st["target"], st["dd"], st["eod"], st.get("dll")
    trail_dll = st.get("dll_trailing", False)
    best = st.get("best"); cap_day = best * A if best else None
    max_rule = firm.get("max_risk_rule")
    bs = firm.get("buffer_scale", 1.0)                 # safety margins below are in dollars of a 100K account
    x = 0.0; H = 0.0; floor = -dd
    day = int(clock // DAY); day_ref = 0.0; day_peak = 0.0; day_pnl = 0.0
    days_traded = set(); best_day = 0.0; day_profits = {}
    target = A
    rho = getattr(tr, "rho", 0.0)                      # round-trip cost per dollar of risk (v7: risk sized net of cost)
    conc = st.get("conc")                              # v7 concentration policy: no trade and no day above conc x target
    if conc:
        cap_day = conc * A if cap_day is None else min(cap_day, conc * A)
    if st.get("min_days"):                             # v7: the minimal filler trades must not take the balance under A
        target = A + 20.0 * bs
    t_stage0 = clock
    lmin = max(0.1 * tr.L, getattr(tr, "min_l", 0.0))  # smallest real trade: 10% of L, or one whole futures contract
    pdn = st.get("profit_days")                        # (days needed, minimum profit for a day to count)
    def _cap_today():
        if not pdn: return None
        need = pdn[0] - sum(1 for v in day_profits.values() if v >= pdn[1])
        if need <= 0: return None
        return max(1.1 * pdn[1], (target - x) / need)
    cap_today = _cap_today()
    for _ in range(200000):
        d = int(clock // DAY)
        if d != day:                                   # new trading day
            if eod:
                H = max(H, x); floor = min(H - dd, st.get("lock") if st.get("lock") is not None else 1e18)
            day = d; day_ref = x; day_peak = x; day_pnl = 0.0
            cap_today = _cap_today()
        short_pdays = bool(pdn) and sum(1 for v in day_profits.values() if v >= pdn[1]) < pdn[0]
        if x >= target - 0.01 and not short_pdays:          # one cent of tolerance: a win that closes the gap lands on it
            if best and day_profits:
                tot = x; bd = max(day_profits.values())
                if bd > best * tot + 1e-6:
                    target = bd / best                      # keep going until the best day is diluted
                    continue
            need = st.get("min_days", 0) - len(days_traded)
            if need > 0: clock += need * DAY * 7.0 / 5.0   # v7: filler days are weekdays (5 in every 7 calendar days)
            return True, clock + st.get("review", 1) * DAY
        if x <= floor + 1e-6:
            return False, clock
        if st.get("max_days") and clock - t_stage0 > st["max_days"] * DAY:
            return False, clock                        # v7: evaluation expired (Apex: 30 days)
        room_floor = (x - floor - 100.0 * bs) / (1.0 + rho)
        if room_floor < lmin:
            return False, clock                        # v7: too little room above the floor for a real trade: the attempt ends here
        room_day = 1e18
        if dll:
            ref = day_peak if trail_dll else day_ref
            dll_now = dll * (1.0 + day_ref / firm["size"]) if st.get("dll_rel") else dll   # Fintokei: % of start-of-day equity
            room_day = (dll_now - (ref - x) - 200.0 * bs) / (1.0 + rho)
        room_cap = 1e18
        if cap_day is not None:
            room_cap = cap_day - day_pnl
        if pdn and cap_today is not None:              # profitable-days rule: daily profit target, then stop
            room_cap = min(room_cap, cap_today - day_pnl)
        l = min(tr.L, room_floor, room_day, max_rule or 1e18)
        lev = firm.get("lev")                          # v7: margin = (l / s) / leverage <= 60% of the current balance
        if lev: l = min(l, lev[2] * lev[0] * tr.s * (firm["size"] + x))
        if l < lmin:
            clock = (day + 1) * DAY + 0.01; continue       # today's loss room is used up: wait for tomorrow
        if room_cap <= 0.5 * bs:
            clock = (day + 1) * DAY + 0.01; continue
        if pdn and cap_today is not None:
            w = min(tr.k * l, room_cap)                    # profitable days still missing: aim at today's target
        else:
            w = min(tr.k * l, target - x, room_cap if cap_day is not None else 1e18)
        if st.get("max_win"): w = min(w, st["max_win"])      # per-trade cap on a win (e.g. a profit-concentration rule)
        if conc: w = min(w, conc * A)
        w = max(w, 1.0 * bs)
        if st.get("min_rr") and w < st["min_rr"] * l:   # never a trade at a lower reward:risk (Maven's gambling definition)
            l = max(w / st["min_rr"], lmin); w = max(w, st["min_rr"] * l)
        pnl, h = tr.trade(l, w, clock, firm.get("flat_weekend_eval", False))
        x += pnl; clock += h; day_pnl += pnl
        days_traded.add(int((clock - h) // DAY))
        dk = int(clock // DAY); day_profits[dk] = day_profits.get(dk, 0.0) + pnl
        if dll and ((day_peak if trail_dll else day_ref) - x) > (dll * (1.0 + day_ref / firm["size"]) if st.get("dll_rel") else dll) + 1e-6:
            return False, clock                        # daily loss limit breached (only possible through a gap)
        day_peak = max(day_peak, x)
        if x < floor: x = floor
    return False, clock


def run_funded(fd, tr, rng, firm, clock, X1, X):
    """Funded stage. Returns (cash_received, clock_end, t_first_payout or None, n_payouts)."""
    dd, eod, dll = fd["dd"], fd["eod"], fd.get("dll")
    trail_dll = fd.get("dll_trailing", False)
    x = 0.0; H = 0.0; floor = -dd; lock = fd.get("lock")
    t0 = clock; day = int(clock // DAY); day_ref = 0.0; day_peak = 0.0; day_pnl = 0.0
    paid = 0.0; npay = 0; tfirst = None; next_pay = t0 + fd["first_payout"] * DAY
    qdays = 0; cyc_best = 0.0; cyc_profit_start = 0.0; refunded = False
    tbest = fd.get("trade_best"); cyc_tbest = 0.0       # Maven: largest winning trade <= 20% of the profit withdrawn
    dbest_c = 0.0; dbest_e = 0.0                       # best day of this payout cycle / of the account (FXIFY: ever)
    tgt_up = 0.0                                       # raised cycle target when a consistency rule blocks a payout
    caps = fd.get("caps"); maxp = fd.get("max_payouts")
    pdn = fd.get("profit_days"); cyc_pdays = 0          # funded profitable-days rule per payout cycle
    bs = firm.get("buffer_scale", 1.0)
    rho = getattr(tr, "rho", 0.0)
    conc = fd.get("conc")
    roll = fd.get("roll_cap"); roll_log = []            # (net cap, window days): Maven's $10,000 per rolling 30 days
    best_eff = fd.get("best")
    lmin = max(0.1 * tr.L, getattr(tr, "min_l", 0.0))
    if conc: best_eff = conc if best_eff is None else min(best_eff, conc)
    def _fcap():
        if not pdn: return None
        need = pdn[0] - cyc_pdays
        if need <= 0: return None
        return max(1.1 * pdn[1], ((X1 if npay == 0 else X) - x) / need)
    fcap = _fcap()
    for _ in range(400000):
        d = int(clock // DAY)
        if d != day:
            if pdn and day_pnl >= pdn[1]: cyc_pdays += 1
            if eod:
                H = max(H, x)
                lvl = H - dd
                if lock is not None and not fd.get("lock_after_first_payout"):
                    lvl = min(lvl, lock)
                if fd.get("lock_after_first_payout"):
                    lvl = min(lvl, lock) if npay == 0 else lock
                floor = max(floor, lvl) if not fd.get("reset_on_payout") else lvl
            if fd.get("q_days"):
                if day_pnl >= fd["q_min"]: qdays += 1
                cyc_best = max(cyc_best, day_pnl)
            dbest_c = max(dbest_c, day_pnl); dbest_e = max(dbest_e, day_pnl)
            day = d; day_ref = x; day_peak = x; day_pnl = 0.0
            fcap = _fcap()
        if x <= floor + 1e-6:
            return paid, clock, tfirst, npay
        pdays_ok = (not pdn) or (cyc_pdays + (1 if day_pnl >= pdn[1] else 0) >= pdn[0])
        # ---- payout opportunity
        target_now = max(X1 if npay == 0 else X, tgt_up)
        can_pay = False
        if fd.get("q_days"):
            prof = x - cyc_profit_start
            buf = fd.get("buffer", 0.0)
            avail = x - max(buf, 0.0) if buf else x
            if qdays >= fd["q_days"] and avail >= max(fd.get("min_payout", 0), 1.0):
                if fd.get("need_profit") and npay > 0 and prof <= 0:
                    pass                                         # Topstep: positive net profit since the last payout
                elif not fd.get("best") or cyc_best < fd["best"] * max(prof, 1e-9):
                    can_pay = True
        else:
            if (clock >= next_pay and x > max(fd.get("min_payout", 0), 0) and pdays_ok
                    and (not fd.get("pay_at_target_only") or x >= target_now - 0.01)):   # (flag: the chain's cycle model)
                need = 0.0                                  # profit the consistency rules need for this request
                if tbest: need = max(need, cyc_tbest / tbest)
                if fd.get("best") and not fd.get("no_best_check"):     # best-day rule checked at the request (v7)
                    need = max(need, max(dbest_e if fd.get("best_ever") else dbest_c, day_pnl) / fd["best"])
                can_pay = need <= x + 1.0 * bs
                if not can_pay and x >= target_now - 0.01:   # at the target but a rule fails: trade on to the profit it needs
                    tgt_up = need + 1.0 * bs
        if can_pay and (x >= target_now - 0.01 or not fd["ondemand"] or fd.get("q_days")):
            amt = x if not fd.get("buffer") else x - fd["buffer"]
            if fd.get("pct_bal"): amt = min(amt, fd["pct_bal"] * x)
            if caps: amt = min(amt, caps[min(npay, len(caps) - 1)])
            if amt > 0 and roll:                                # rolling cap on the trader's share (Maven); the excess
                win = sorted((tc, c) for (tc, c) in roll_log if tc > clock - roll[1] * DAY)   # would be voided, so the
                allow = roll[0] - sum(c for _, c in win)                                     # request waits until the
                if fd["split"] * amt > allow + 0.5 and fd["split"] * amt <= roll[0]:         # window has room for it
                    for tc, c in win:
                        allow += c
                        if fd["split"] * amt <= allow + 0.5:
                            next_pay = tc + roll[1] * DAY + 0.01; break
                    continue
            if amt > 0:
                cash = fd["split"] * amt
                if roll:
                    recent = sum(c for (tc, c) in roll_log if tc > clock - roll[1] * DAY)
                    cash = max(0.0, min(cash, roll[0] - recent))
                    roll_log.append((clock, cash))
                if npay == 0 and fd.get("eval_share"):
                    cash += fd["eval_share"] * sum(s["target"] for s in firm["phases"])
                rsplit = fd.get("refund_split")
                if rsplit and fd.get("refund", 0):
                    if npay < rsplit: cash += fd["refund"] / rsplit      # fee returned in equal parts with the first payouts
                elif not refunded and npay + 1 >= fd.get("refund_after", 1) and fd.get("refund", 0):
                    cash += fd["refund"]; refunded = True
                paid += cash; npay += 1; x -= amt; day_ref -= amt; day_peak -= amt
                cyc_pdays = 0; day_pnl = 0.0
                if PAYLOG is not None: PAYLOG.append((clock + fd.get("process", 1) * DAY, cash))
                if tfirst is None: tfirst = clock + fd.get("process", 1) * DAY
                if fd.get("reset_on_payout"):
                    H = x; floor = x - dd
                if fd.get("lock_after_first_payout") and npay == 1:
                    floor = max(floor, lock)
                cyc_profit_start = x; qdays = 0; cyc_best = 0.0; cyc_tbest = 0.0; dbest_c = 0.0; tgt_up = 0.0; fcap = _fcap()
                next_pay = clock + max(fd["cycle"], 1) * DAY if not fd["ondemand"] else clock + DAY
                if maxp and npay >= maxp:
                    return paid, clock, tfirst, npay
                continue
        # ---- reached this cycle's target: wait for the payout date
        if x >= target_now - 0.01 and not fd.get("q_days") and pdays_ok:
            clock = max(clock + 0.01, next_pay); continue
        dp = 0.0 if fd.get("per_trade") else day_pnl      # per_trade: caps apply to each trade, not each day (analytic check)
        # ---- best-day rule on cycle-based accounts: cap each day's profit
        if best_eff and not fd.get("q_days") and dp >= best_eff * max(target_now, 1.0) - 0.5 * bs:
            clock = (day + 1) * DAY + 0.01; continue
        # ---- futures-style: stop for the day once the day qualifies
        if fd.get("q_days") and day_pnl >= fd["q_min"]:
            clock = (day + 1) * DAY + 0.01; continue
        room_floor = (x - floor - 100.0 * bs) / (1.0 + rho)
        if room_floor < lmin:
            return paid, clock, tfirst, npay               # v7: too little room above the floor: the account ends here
        room_day = 1e18
        dll_now = dll * (1.0 + day_ref / firm["size"]) if (dll and fd.get("dll_rel")) else dll
        if dll:
            ref = day_peak if trail_dll else day_ref
            room_day = (dll_now - (ref - x) - 200.0 * bs) / (1.0 + rho)
        l = min(tr.L, room_floor, room_day, firm.get("max_risk_rule") or 1e18)
        lev = firm.get("lev")                          # margin cap at the current balance (and FunderPro's 20% of the start)
        if lev: l = min(l, lev[1] * tr.s * min(lev[2] * (firm["size"] + x), lev[3] * firm["size"]))
        if l < lmin:
            clock = (day + 1) * DAY + 0.01; continue
        w = tr.k * l
        if not fd.get("q_days"):
            w = min(w, max(target_now - x, 1.0 * bs))
        if best_eff and not fd.get("q_days"):            # best-day / consistency rule: cap today's win
            w = min(w, max(best_eff * max(target_now, 1.0) - dp, 1.0 * bs))
        if fd.get("max_win"): w = min(w, fd["max_win"])   # per-trade cap (used by the analytic check)
        if tbest: w = min(w, max(tbest * target_now, 1.0 * bs))
        dcap = fd.get("day_profit_cap")
        if dcap:
            if dp >= dcap - 1.0:
                clock = (day + 1) * DAY + 0.01; continue
            w = min(w, dcap - dp)
        if pdn and fcap is not None and not pdays_ok:       # daily profit target until the cycle has its profitable days
            if fcap - day_pnl <= 0.5 * bs:
                clock = (day + 1) * DAY + 0.01; continue
            w = min(w, fcap - day_pnl)
        if fd.get("min_rr") and w < fd["min_rr"] * l:
            l = max(w / fd["min_rr"], lmin); w = max(w, fd["min_rr"] * l)
        pnl, h = tr.trade(l, w, clock, fd.get("flat_weekend", False))
        x += pnl; clock += h; day_pnl += pnl
        if pnl > 0: cyc_tbest = max(cyc_tbest, pnl)
        if dll and ((day_peak if trail_dll else day_ref) - x) > dll_now + 1e-6:
            return paid, clock, tfirst, npay               # daily loss limit breached: account lost
        day_peak = max(day_peak, x)
        if x < floor: x = floor
    return paid, clock, tfirst, npay


def attempt(firm, cal_point, L, k, X1, X, rng, max_months=36):
    tr = Trader(cal_point, L, k, rng)
    clock = rng.random() * DAY
    t_start = clock
    fees = firm["fee"]
    for st in firm["phases"]:
        ok, clock = run_stage(st, tr, rng, firm, clock)
        if not ok:
            if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * DAY)))
            return -fees, (clock - t_start) / DAY, None, 0, False
    if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * DAY)))
    fees += firm.get("activation", 0)
    paid, clock, tfirst, npay = run_funded(firm["funded"], tr, rng, firm, clock, X1, X)
    return paid - fees, (clock - t_start) / DAY, (tfirst - t_start) / DAY if tfirst else None, npay, True


def evaluate(firm, cal_point, L, k, X1, X, n=3000, seed=7):
    rng = random.Random(seed)
    ev = 0.0; dur = 0.0; nf = 0; tf = []; ev2 = 0.0; prof = 0
    for _ in range(n):
        v, d, t1, npay, f = attempt(firm, cal_point, L, k, X1, X, rng)
        ev += v; ev2 += v * v; dur += d; nf += f; prof += v > 0
        if t1 is not None: tf.append(t1)
    ev /= n; dur /= n
    sd = math.sqrt(max(ev2 / n - ev * ev, 0))
    return dict(EV=ev, CI=1.96 * sd / math.sqrt(n), days=dur, EV_month=ev / (dur / 30.44),
                Pf=nf / n, Pprofit=prof / n, t_first_pay=(sorted(tf)[len(tf) // 2] if tf else None))
