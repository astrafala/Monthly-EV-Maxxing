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
PAYLOG = None      # if a list, run_funded appends (time the cash arrives, cash, request time, kind, time processed) for every
                   # payout (kind 'payout'), and a row taking the cash back for a payout cancelled by a breach before it was
                   # processed (kind 'payout_cancelled', negative cash, the breach time in place of the request time)
TRADELOG = None    # if a list, every trade appends (stage, entry, balance before, pnl, exit, kind, minutes held)
STUCK = [0]        # accounts ended because nothing could happen for STALL_DAYS (should stay 0: a check, not a rule)
STALL_DAYS = 120
STUCK_INFO = []     # (stage, state) of each stalled account, for diagnosis

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

    def trade(self, l, w, clock=None, flat_weekend=False, opts=None):
        """returns (pnl, hours)"""
        if opts and opts.get("kind") == "filler": return 0.0, 1.0
        if w >= self.k * l * 0.999:
            p = (1 + self.e) / (1 + self.k)
        else:
            p = (l - self.cost * l) / (w + l)
        p = min(max(p, 0.0), 1.0)
        hrs = self.dur[self.rng.randrange(len(self.dur))]
        if w < self.k * l * 0.999:   # nearer target resolves sooner (fair-walk time ~ w*l)
            hrs = max(1.0, hrs * (w / (self.k * l)))
        return (w if self.rng.random() < p else -l), hrs


def _dll_at(dll, mode, size, day_ref):
    """today's loss allowance. 'fixed': a share of the initial balance (FTMO, FundedNext, BrightFunded, Blue Guardian);
    'rel': the same share of the day's starting balance (FundingPips, The5ers, FXIFY, GFT, Hola Prime, Maven, Alpha
    Capital, Fintokei); 'min': the smaller of the two, where the firm's wording does not settle it (FunderPro). The plan
    is flat at every reset, so the day's starting balance is also its starting equity. (Version 7 used 'fixed' for every
    firm but Fintokei: review of version 7, finding 1.)"""
    if not dll: return None
    f = (size + day_ref) / size
    if mode == "rel": return dll * f
    if mode == "min": return dll * min(1.0, f)
    return dll

def _mode(st):
    return st.get("dll_mode") or ("rel" if st.get("dll_rel") else "fixed")

def _next_entry(tr, clock, fw):
    """when the next trade would open (the market's entry hours, the daily cut-off, weekends, blocked news hours). Every
    trade is decided on the day it opens, with that day's limits and caps: version 8's first engine decided a trade after
    the cut-off or on a weekend with the previous day's figures and booked its result there, so the next day's daily
    loss allowance and profit caps restarted after it (version 8, n12)"""
    return tr.next_entry(clock, fw) if hasattr(tr, "next_entry") else clock

def _bdays(tr, clock, n):
    """n working days after clock on the trader's market calendar (phase reviews, payout processing). Version 9: version 8
    added n x 24 hours, so a three-working-day review after a Friday ended on Monday (review of version 8, finding 20).
    Without a calendar (the calibration trader): 7/5 calendar days per working day."""
    if not n: return clock
    return tr.bdays(clock, n) if hasattr(tr, "bdays") else clock + n * DAY * 7.0 / 5.0

def _lmin(tr, clock, fw):
    """(smallest planned trade, smallest position): a tenth of the planned risk or the smallest position, whichever is
    larger, and the risk of the smallest position itself (0.01 lot of a CFD, one micro contract) at the next entry's price"""
    lm = tr.lmin_at(clock, fw) if hasattr(tr, "lmin_at") else getattr(tr, "min_l", 0.0)
    return max(0.1 * tr.L, lm), lm

def _risk(tr, x, floor, room_day, lmin, lm, bs, rho, max_rule):
    """(risk, terminal) for the next trade, or (None, False) to wait for tomorrow.
    Normal: l = min(L, room above floor less a buffer, today's room) net of cost (never below the smallest position).
    Terminal (room above the floor below a normal trade): the plan trades the rest with the stop at the floor itself, so
    the account either recovers or ends in a breach that closes it and frees its allocation. Version 9: the stop is the
    account's breach level, a barrier of the trade (pathfirm.resolve), at whatever volume the smallest position allows; if
    today's room is the nearer limit, a normal stop inside it (version 8 rounded the risk up to $1 and clipped the loss
    back to the floor afterwards, which changed the payoff without changing the chance of reaching the floor: review of
    version 8, finding 3)."""
    mr = max_rule or 1e18
    room_floor = (x - floor - 100.0 * bs) / (1.0 + rho)
    if room_floor >= lmin:
        l = min(max(tr.L, lm), room_floor, room_day, mr)
        return (l, False) if l >= lmin else (None, False)
    room0 = (x - floor) / (1.0 + rho)
    if room_day < room0:
        l = min(room_day, mr)
        return (l, False) if l >= lm and l > 0 else (None, False)
    return min(room0, mr), True

def _win(tr, l, plan_cap, rule_cap, bs, fresh=False, lc=0.0, lv=None):
    """the win: k l, capped by the plan's own targets (phase or cycle target, the day's profitable-day target) and by the
    rules' caps (concentration, best day, day caps, Maven's ceiling and rolling cap). The take-profit is never placed closer
    than WMIN_SD hourly sd to the entry (a plan choice); lv: the risk of the volume actually traded (at least the smallest
    position), whose notional sets that distance; above a plan cap that only overshoots the target, but a rule cap below
    it means no trade now (None)."""
    wf = getattr(tr, "wmin_frac", 0.0); wmin = wf * (l if lv is None else max(l, lv))
    w = min(tr.k * l, plan_cap)
    w = max(w, wmin, 1.0 * bs)
    if w > rule_cap:
        w = rule_cap
        if w < max(wmin, 0.5 * bs) - 1e-9:
            # a rule cap below the smallest allowed win with nothing made today (fresh): the cap is structural (a small
            # payout target, Maven's ceiling), so trade smaller - the risk lowered until the cap is a full minimum-distance
            # win - rather than never trading; with profit already made today, wait for tomorrow instead. The lower limit
            # is the market's smallest position (lc)
            if fresh and wf > 0 and rule_cap >= 1.0 * bs and rule_cap / wf >= lc: return w, rule_cap / wf
            return None, l
    return w, l

RULE_HITS = {"alpha_phase": 0, "alpha_funded": 0, "short_breach": 0,       # rule consequences applied (counts)
             "payout_cancelled": 0, "shield_first": 0, "shield_second": 0, "abandoned": 0, "rr_wait": 0,
             "rr_raised": 0, "rr_lowered": 0, "lots_capped": 0, "min_net_wait": 0, "cap_held": 0, "excluded_day": 0,
             "expired": 0, "voided": 0, "keepalive": 0}

def _dur_ok(m, durs):
    """Alpha Capital's duration rule over the trades of a phase or of the funded account: average duration above m
    minutes, most trades above m minutes, and at least half of the gross profit from trades above m minutes (durations are
    lower bounds: the minute of the exit is counted from its start)"""
    if not m or not durs: return True
    n = len(durs)
    avg = sum(dd for dd, p in durs) / n
    longn = sum(1 for dd, p in durs if dd > m)
    gp = sum(p for dd, p in durs if p > 0); gl = sum(p for dd, p in durs if p > 0 and dd > m)
    return avg > m and longn > n / 2.0 and (gp <= 0 or gl >= 0.5 * gp)

def _trade_info(tr, clock, h):
    """(entry clock, exit clock, minutes held, breach) of the trade just made"""
    te = tr.last_entry if getattr(tr, "last_entry", None) is not None else clock
    tx = tr.last_exit if getattr(tr, "last_exit", None) is not None else clock + h
    info = getattr(tr, "last_info", None) or {}
    return te, tx, info.get("dur", 60.0), bool(info.get("breach", False))

def _why(tr):
    return (getattr(tr, "last_info", None) or {}).get("why")

def _expiry(tr, clock, st):
    """the clock at which an evaluation with a time limit expires (Apex: 30 days, at 6 p.m. New York time on the 30th day,
    the purchase day counting as the first; version 10: version 9 used the purchase time plus 720 hours and accepted a
    target reached after it, review of version 9, finding 13). None: no time limit"""
    md = st.get("max_days")
    if not md: return None
    loc = st.get("expiry_local")
    if loc and hasattr(tr, "utc"):
        import datetime as _d, zoneinfo
        tz = zoneinfo.ZoneInfo(loc[1]); now = tr.utc(clock)
        d0 = now.astimezone(tz).date() + _d.timedelta(days=md - 1)
        dl = _d.datetime(d0.year, d0.month, d0.day, loc[0], 0, tzinfo=tz)
        return clock + (dl - now).total_seconds() / 3600.0
    return clock + md * DAY

def _ct(tr, t):
    import zoneinfo
    return tr.utc(t).astimezone(zoneinfo.ZoneInfo("America/Chicago"))

def _session_req(tr, clock, earliest):
    """Topstep (version 10, review of version 9, finding 18): (request time, engine day of the request's session). A request
    found at an engine day boundary (22:00 UTC: the plan stopped for the day, or the day's result completed the five
    winning days) is made one minute after the completed session's results lock, 4:00 p.m. Chicago time (21:00 UTC in
    summer, 22:00 UTC in winter), inside the payout window (Sunday to Friday, 5 p.m. to 5 p.m. Chicago) and inside that
    session, which has already been counted; otherwise at the clock (the plan trades 01:00-20:00 UTC, inside one Chicago
    session). The session of a time: the engine day, except from 22:00 to 23:00 UTC in winter, which is still the
    previous Chicago session (it ends at 5 p.m. CST = 23:00 UTC)"""
    b = math.floor(clock / DAY + 1e-12) * DAY
    t_req = max(clock, earliest)
    if clock - b < 1.0:
        lock = b - 1.0 if _ct(tr, b).hour == 17 else b       # 22:00 UTC is 5 p.m. CDT (lock an hour before) or 4 p.m. CST
        if lock + 1.0 / 60.0 >= earliest - 1e-9: t_req = lock + 1.0 / 60.0
    d = int(math.floor(t_req / DAY + 1e-12))
    u = tr.utc(t_req)
    if u.hour == 22 and _ct(tr, t_req).hour == 16: d -= 1
    return t_req, d

def _rr_fix(tr, clock, fw, l, w, opts, min_rr, rule_cap, bs):
    """Maven: the plan never places a trade whose take-profit distance is below min_rr times its stop distance (prices
    measured from the entry; the stop is the nearest adverse barrier: the stop loss, or the account's breach level on a
    terminal trade). Checked on the position actually placed (rounded volume, at least the smallest position), not on the
    requested risk (version 10: version 9 lowered the requested risk and the volume was then raised to the smallest
    position, so the actual ratio could fall below the policy: review of version 9, finding 5). Returns (l, w, keep_w)
    to trade, or None to wait: the win is fixed at the amount the trade would make, then the volume is lowered until its
    take-profit is far enough, then, at the smallest position, the win is raised to min_rr times the stop distance if
    the rule caps allow it."""
    if not hasattr(tr, "plan_at"):                          # the calibration trader: no positions, the old rule
        if opts.get("terminal"): return l, max(w, min(rule_cap, min_rr * opts.get("breach", l))), None
        return ((w / min_rr, w) if w < min_rr * l else (l, w)) + (None,)
    o = dict(opts)                                          # keep_w as the trade itself would set it
    for _ in range(4):
        P = tr.plan_at(clock, l, w, o, fw)
        if not P["afford"] or P["td"] >= min_rr * P["sd"] * (1 + 1e-9):
            return l, w, o.get("keep_w")
        if not o.get("keep_w"): w = P["win"]                # the win the trade would make, now fixed
        o["keep_w"] = True
        if not opts.get("terminal") and P["sd"] >= P["s"] * (1 - 1e-12):     # the stop loss is the nearest barrier
            den = P["uv"] * (min_rr * P["s"] - P["cost"])   # td/sd >= min_rr  <=>  vol <= w / (uv (min_rr s - cost))
            if den > 0:
                vmax = math.floor(w / den / P["step"] + 1e-9) * P["step"]
                if P["vmin"] - 1e-12 <= vmax < P["vol"] - 1e-12:
                    RULE_HITS["rr_lowered"] += 1; l = vmax * P["uv"] * P["s"] * (1 + 1e-9); continue
        need = min_rr * P["sd"] * (1 + 2e-9) * P["notional"] - P["fee"]    # the win whose take-profit is min_rr x away
        if w < need <= rule_cap + 1e-9:
            RULE_HITS["rr_raised"] += 1; w = need; continue
        RULE_HITS["rr_wait"] += 1
        return None
    return None

def run_stage(st, tr, rng, firm, clock, eval_phase=True, fund=None):
    """Evaluation phase. Returns (passed, clock)."""
    A, dd, eod, dll = st["target"], st["dd"], st["eod"], st.get("dll")
    trail_dll = st.get("dll_trailing", False); mode = _mode(st)
    best = st.get("best"); cap_day = best * A if best else None
    max_rule = firm.get("max_risk_rule")
    bs = firm.get("buffer_scale", 1.0)                 # safety margins below are in dollars of a 100K account
    hold = firm.get("hold_min", 0)                     # minimum holding time (Blue Guardian): the bracket after `hold` min
    dmin = firm.get("day_min_minutes")                 # a day counts only with a trade held this long (BrightFunded: 1)
    durm = firm.get("dur_rule")                        # Alpha Capital's 2-minute duration rule
    tr.news = st.get("news")                           # the stage's news rule (version 10, news_v10): None, "all", "cpi"
    x = 0.0; H = 0.0; floor = -dd
    day = int(clock // DAY); day_ref = 0.0; day_peak = 0.0; day_pnl = 0.0
    days_traded = set(); day_profits = {}; durs = []
    target = A
    rho = getattr(tr, "rho", 0.0)                      # round-trip cost per dollar of risk (risk sized net of cost)
    conc = st.get("conc")                              # concentration policy: no trade and no day above conc x target
    if conc:
        cap_day = conc * A if cap_day is None else min(cap_day, conc * A)
    fw = firm.get("flat_weekend_eval", False)
    fill = bool(st.get("min_days")) and not firm.get("no_fillers")
    if bool(st.get("min_days")) and not firm.get("no_target_buffer"):
        # the phase's own stopping point is $20 per $100K above the target wherever minimum trading days may need filler
        # trades (a filler's cost or loss cannot take the account back under the target); version 10: the buffer no
        # longer depends on whether fillers are allowed, so the no-filler sensitivity changes only the fillers (review of
        # version 9, finding 25). Firms that object to minimal trades (Fintokei, Alpha Capital) have no_target_buffer:
        # their missing days are ordinary trades of the plan, which need no buffer
        target = A + 20.0 * bs
    filling = False                                    # the plan target was reached and fillers complete the days
    t_stage0 = clock; t_act = clock
    exp = _expiry(tr, clock, st)                       # evaluation time limit (Apex), as a clock time
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
        reached = x >= target - 0.01 or (filling and x >= A - 0.01)   # one cent: a win that closes the gap lands on it
        if not reached: filling = False
        kind = "trade"
        if reached and not short_pdays:
            if best and day_profits:
                tot = x; bd = max(day_profits.values())
                if bd > best * tot + 1e-6:
                    target = bd / best + 1.0 * bs           # keep going until the best day is diluted ($1 past it,
                    filling = False; continue               # so the next pass trades instead of re-checking at once)
            need = st.get("min_days", 0) - len(days_traded)
            if need <= 0:
                if durm and not _dur_ok(durm, durs):        # Alpha: the duration rule fails: the phase restarts
                    RULE_HITS["alpha_phase"] += 1; return False, clock
                return True, _bdays(tr, clock, st.get("review", 1))
            # trading days missing: a filler trade (0.01 lot, closed after 3 minutes) on each missing day, or where the
            # firm objects to minimal trades (Fintokei, Alpha Capital) an ordinary trade a day (version 9: version 8 counted
            # filler days without trading them, review of version 8, findings 5 and 8)
            if fill: filling = True; kind = "filler"
            else: kind = "gate"
        if x <= floor + 1e-6:
            return False, clock
        if clock - t_act > STALL_DAYS * DAY:
            STUCK[0] += 1; STUCK_INFO.append(("stage", dict(x=x, floor=floor, A=A, target=target, days=len(days_traded))))
            return False, clock
        te0 = _next_entry(tr, clock, fw)
        if exp is not None and te0 >= exp:             # the next trade would open after the evaluation has expired
            RULE_HITS["expired"] += 1; return False, clock
        if int(te0 // DAY) != day:                     # the next entry opens on a later day: decide it there (n12)
            clock = te0; continue
        if kind != "trade" and day in days_traded:     # one day-completing trade a day
            clock = (day + 1) * DAY + 0.01; continue
        lmin, lm = _lmin(tr, clock, fw)
        room_day = 1e18; brk = x - floor               # breach: the loss (cost included) that reaches a limit
        if dll:
            ref = day_peak if trail_dll else day_ref
            allow = _dll_at(dll, mode, firm["size"], day_ref) - (ref - x)
            room_day = (allow - 200.0 * bs) / (1.0 + rho); brk = min(brk, allow)
        if kind == "filler":
            l = w = 0.0; opts = dict(kind="filler", breach=brk)
        else:
            l, terminal = _risk(tr, x, floor, room_day, lmin, lm, bs, rho, max_rule)
            lev = firm.get("lev")                      # margin = (l / s) / leverage <= 60% of the current balance
            if l is not None and lev:
                l = min(l, lev[2] * lev[0] * tr.s * (firm["size"] + x))
                if not terminal and l < lmin: l = None
            if l is None:
                clock = (day + 1) * DAY + 0.01; continue       # today's loss room is used up: wait for tomorrow
            rule_cap = 1e18
            if cap_day is not None: rule_cap = cap_day - day_pnl
            if conc: rule_cap = min(rule_cap, conc * A)
            if st.get("max_win"): rule_cap = min(rule_cap, st["max_win"])   # per-trade cap on a win (a firm's rule)
            if rule_cap <= 0.5 * bs:
                clock = (day + 1) * DAY + 0.01; continue
            if kind == "gate":
                plan_cap = 1e18                           # an ordinary trade of the plan (no minimal trade)
            elif pdn and cap_today is not None:           # profitable-days rule: today's profit target, then stop for the day
                if cap_today - day_pnl <= 0.5 * bs:
                    clock = (day + 1) * DAY + 0.01; continue
                plan_cap = cap_today - day_pnl
            else:
                plan_cap = target - x
            w, l = _win(tr, l, plan_cap, rule_cap, bs, fresh=day_pnl <= 0, lc=lm, lv=lm)
            if w is None:
                clock = (day + 1) * DAY + 0.01; continue
            opts = dict(breach=brk, terminal=terminal, hold=hold)
            if st.get("min_rr"):                          # Maven: reward:risk policy on the position actually placed
                r = _rr_fix(tr, clock, fw, l, w, opts, st["min_rr"], rule_cap, bs)
                if r is None:
                    clock = (day + 1) * DAY + 0.01; continue
                l, w, kw = r
                if kw is not None: opts["keep_w"] = kw
        tr.last_entry = None; tr.last_exit = None; tr.last_info = None
        pnl, h = tr.trade(l, w, clock, fw, opts)
        if _why(tr) == "unaffordable":                 # not even the smallest position fits the breach room: abandoned
            RULE_HITS["abandoned"] += 1; return False, clock
        te, tx, dur, breached = _trade_info(tr, clock, h)
        t_act = clock + h
        de = int(te // DAY)                            # the day the trade was opened
        x += pnl; clock += h; day_pnl += pnl
        if TRADELOG is not None: TRADELOG.append(("eval", te, x - pnl, pnl, tx, opts.get("kind", "trade"), dur))
        if dmin is None or dur >= dmin - 1e-9: days_traded.add(de)
        durs.append((dur, pnl))
        dk = int(tx // DAY); day_profits[dk] = day_profits.get(dk, 0.0) + pnl     # by the day of the close
        if breached: return False, clock               # the trade reached the floor or today's limit: account closed
        if exp is not None and tx > exp:               # a position still open when the evaluation expired
            RULE_HITS["expired"] += 1; return False, clock
        if firm.get("short_breach") and dur < 2.0 - 1e-9:  # Blue Guardian: a trade under 2 minutes (only a breach can be)
            RULE_HITS["short_breach"] += 1; return False, clock
        if dll and ((day_peak if trail_dll else day_ref) - x) > _dll_at(dll, mode, firm["size"], day_ref) + 1e-6:
            return False, clock                        # daily loss limit breached (only possible through a gap)
        day_peak = max(day_peak, x)
    STUCK[0] += 1; STUCK_INFO.append(("stage-loop", dict(x=x, A=A)))
    return False, clock

def run_funded(fd, tr, rng, firm, clock, X1, X):
    """Funded stage. Returns (cash_received, clock_end, t_first_payout or None, n_payouts).
    Payouts (version 10, review of version 9, findings 1, 2, 16-21): a request is made at least req_wait hours after the
    last close (FundingPips: 15 minutes) with the account flat. It is then
      - deducted and final at once where the firm says so (Topstep: protected), or
      - pending until processed (review working days, then review_h hours): a breach before then cancels it (the
        cautious reading where a firm says nothing); where the firm locks the account during processing (Alpha
        Capital, FundingPips, FXIFY) or the plan pauses (Apex, whose request is denied if the balance falls below its
        threshold), nothing is traded until it is processed.
    The cash arrives transfer_bd working days after processing. The next request counts from the request, or from the
    processing where the firm says so (Fintokei, The5ers)."""
    dd, eod, dll = fd["dd"], fd["eod"], fd.get("dll")
    trail_dll = fd.get("dll_trailing", False); mode = _mode(fd)
    x = 0.0; H = 0.0; floor = -dd; lock = fd.get("lock")
    t0 = clock; day = int(clock // DAY); day_ref = 0.0; day_peak = 0.0; day_pnl = 0.0; day_pnl_c = 0.0
    # day_pnl: the calendar day's P&L (daily caps and best-day rules; a payout does not reset it); day_pnl_c: the part of
    # the day since the current payout cycle began (profitable and qualifying days of the cycle; reset at each payout).
    # Version 8's first engine reset the one counter at a payout, so a day's profit before a mid-day payout escaped the
    # day caps (GFT's $3,000) and the best-day measures (version 8, n13)
    paid = 0.0; npay = 0; tfirst = None
    # the first payout date counts from the first trade on the funded account (FTMO, FundingPips, Fintokei, GFT, Alpha
    # Capital, Maven say so)
    next_pay = 1e18 if fd.get("clock_first_trade", True) else t0 + fd["first_payout"] * DAY
    qdays = 0; cyc_best = 0.0; cyc_profit_start = 0.0; refunded = False
    dbest_c = 0.0; dbest_e = 0.0                       # best day of this payout cycle / of the account (FXIFY: ever)
    tgt_up = 0.0                                       # raised cycle target when a consistency rule blocks a payout
    caps = fd.get("caps"); maxp = fd.get("max_payouts")
    pdn = fd.get("profit_days"); pdates = []            # funded profitable days of this payout cycle (engine days)
    pdw = fd.get("profit_days_window")                 # Hola Prime: the days must fall within 14 calendar days (version 9)
    cdays = fd.get("cycle_days"); cyc_days = set()      # trading days per payout cycle (Fintokei: 3)
    first_days = fd.get("first_days"); all_days = set() # trading days before the first payout (Alpha: 5)
    nofill = bool(firm.get("no_fillers"))              # firms that object to minimal day-completing trades
    ceiling = fd.get("profit_ceiling")                 # Maven: $4,900; The5ers: under the 10% scaling milestone
    rcap = fd.get("roll_profit_cap"); closed = []      # Maven: $10,000 of closed profit per rolling 30 days (by close date)
    bs = firm.get("buffer_scale", 1.0)
    hold = firm.get("hold_min", 0); durm = firm.get("dur_rule"); durs = []
    rho = getattr(tr, "rho", 0.0)
    conc = fd.get("conc")
    fw = fd.get("flat_weekend", False)
    best_eff = fd.get("best")
    if conc: best_eff = conc if best_eff is None else min(best_eff, conc)
    minpay = fd.get("min_payout", 0.0)
    tr.news = fd.get("news")                           # the funded account's news rule (version 10, news_v10)
    split = fd["split"]; shields = 0                   # Blue Guardian: 50% after the first Guardian Shield, then a breach
    pend = None                                        # a payout requested and not yet processed
    excl_day = None                                    # Topstep: the session of a request does not count for the next one
    last_exit = -1e18                                  # the last close (a request waits req_wait hours after it)
    t_act = clock                                      # last trade or payout (stall detector)
    def _end(t_breach):
        """the account ends (t_breach: the time of a breach, None otherwise): a payout still pending at a breach is
        cancelled, with a ledger row that takes its cash back on the date it would have arrived"""
        nonlocal paid, npay, tfirst
        if pend is not None and t_breach is not None and t_breach < pend["t_proc"] - 1e-9:
            paid -= pend["cash"]; npay -= 1; RULE_HITS["payout_cancelled"] += 1
            if pend["first"]: tfirst = None
            if PAYLOG is not None: PAYLOG.append((pend["t_cash"], -pend["cash"], t_breach, "payout_cancelled", pend["t_proc"]))
        return paid, clock, tfirst, npay
    def _npd(dcur):
        """profitable days that count today: the cycle's, or those inside the firm's window ending today"""
        if pdw: return sum(1 for t in pdates if t >= dcur - (pdw - 1))
        return len(pdates)
    def _fcap():
        if not pdn: return None
        need = pdn[0] - _npd(day)
        if need <= 0: return None
        T = X1 if npay == 0 else X
        if ceiling: T = min(T, ceiling)
        return max(1.1 * pdn[1], (T - x) / need)
    fcap = _fcap()
    for _ in range(400000):
        d = int(clock // DAY)
        if pend is not None and clock >= pend["t_proc"] - 1e-9:
            pend = None                                # processed: final
        if d != day:
            if pdn and day_pnl_c >= pdn[1]: pdates.append(day)
            if eod:
                H = max(H, x)
                lvl = H - dd
                if lock is not None and not fd.get("lock_after_first_payout"):
                    lvl = min(lvl, lock)
                if fd.get("lock_after_first_payout"):
                    lvl = min(lvl, lock) if npay == 0 else lock
                floor = max(floor, lvl) if not fd.get("reset_on_payout") else lvl
            if fd.get("q_days"):
                if day_pnl_c >= fd["q_min"]:
                    if day == excl_day: RULE_HITS["excluded_day"] += 1
                    else: qdays += 1
                cyc_best = max(cyc_best, day_pnl_c)
            dbest_c = max(dbest_c, day_pnl); dbest_e = max(dbest_e, day_pnl)
            day = d; day_ref = x; day_peak = x; day_pnl = 0.0; day_pnl_c = 0.0
            fcap = _fcap()
        if x <= floor + 1e-6:
            return _end(clock)
        cyc_pdays = _npd(day) if pdn else 0
        if clock - t_act > STALL_DAYS * DAY:
            STUCK[0] += 1; STUCK_INFO.append(("funded", dict(x=x, floor=floor, npay=npay, cyc_pdays=cyc_pdays, day_pnl=day_pnl,
                                                              fcap=fcap, next_pay=next_pay - clock, closed=closed[-6:])))
            return _end(None)
        pdays_ok = (not pdn) or (cyc_pdays + (1 if day_pnl_c >= pdn[1] else 0) >= pdn[0])
        gate_first = bool(first_days) and npay == 0 and len(all_days) < first_days
        days_short = bool(cdays) and len(cyc_days) < cdays     # Fintokei: trading days missing in this cycle
        gate = gate_first or (days_short and nofill)          # ordinary trades, one a day, until the days are met
        # ---- payout opportunity
        target_now = max(X1 if npay == 0 else X, tgt_up)
        if ceiling: target_now = min(target_now, ceiling)
        can_pay = False; kind = "trade"
        if pend is not None:
            pass                                           # one request at a time
        elif fd.get("q_days"):
            prof = x - cyc_profit_start
            buf = fd.get("buffer", 0.0)
            avail = x - max(buf, 0.0) if buf else x
            if qdays >= fd["q_days"] and avail >= max(minpay, 1.0):
                if fd.get("need_profit") and npay > 0 and prof <= 0:
                    pass                                         # Topstep: positive net profit since the last payout
                elif not fd.get("best") or max(cyc_best, day_pnl_c) < fd["best"] * prof:
                    # Apex: every day of the cycle, today's included, under 50% of the cycle's profit (version 10: version 9
                    # left today out, review of version 9, finding 21)
                    can_pay = True
        else:
            if (clock >= next_pay and x >= max(minpay, fd.get("min_profit", 0.0), 0.01) and pdays_ok and not gate
                    and (not fd.get("pay_at_target_only") or x >= target_now - 0.01
                         or (ceiling and ceiling - x < 1.0 * bs))):    # (flag: the chain's cycle model; within $1 of
                                                                       # Maven's ceiling no win fits, so that is the target)
                if days_short:                                  # trading days missing: a filler trade a day
                    kind = "filler"
                else:
                    need = 0.0                                  # profit the consistency rules need for this request
                    if fd.get("best") and not fd.get("no_best_check"):     # best-day rule checked at the request
                        need = max(need, max(dbest_e if fd.get("best_ever") else dbest_c, day_pnl) / fd["best"])
                    can_pay = need <= x + 1e-6                 # strict: the rule's limit itself, no tolerance (n13)
                    if not can_pay and x >= target_now - 0.01:   # at the target but a rule fails: trade on to the profit
                        tgt_up = need + 1.0 * bs
        if can_pay and durm and not _dur_ok(durm, durs):
            # Alpha Capital: the duration rule fails at a request: the profits are removed and the account restarts at
            # its initial balance (the firm's stated consequence on a qualified account)
            RULE_HITS["alpha_funded"] += 1; x = min(x, 0.0); durs = []; can_pay = False
            day_ref = min(day_ref, x); day_peak = min(day_peak, x); continue
        if can_pay and (x >= target_now - 0.01 or not fd["ondemand"] or fd.get("q_days")):
            amt = x if not fd.get("buffer") else x - fd["buffer"]
            if fd.get("pct_bal"): amt = min(amt, fd["pct_bal"] * x)
            rnow = 0.0                                          # fee refund paid with this payout
            rsplit = fd.get("refund_split")
            if rsplit and fd.get("refund", 0):
                if npay < rsplit: rnow = fd["refund"] / rsplit      # fee returned in equal parts with the first payouts
            elif not refunded and npay + 1 >= fd.get("refund_after", 1) and fd.get("refund", 0):
                rnow = fd["refund"]
            if caps:
                cap = caps[min(npay, len(caps) - 1)]
                if fd.get("cap_includes_refund"): cap = cap - rnow   # The5ers: the refund counted inside the cap (cautious)
                if amt > cap + 1e-9: RULE_HITS["cap_held"] += 1     # the rest stays in the account
                amt = min(amt, cap)
            if amt > 0 and split * amt < fd.get("min_net", 0.0) - 1e-9:
                RULE_HITS["min_net_wait"] += 1; amt = 0.0       # under the firm's minimum payout: not requested yet
            if amt > 0:
                cash = split * amt + rnow
                if npay == 0 and fd.get("eval_share"):
                    cash += fd["eval_share"] * sum(s["target"] for s in firm["phases"])
                if rnow and not rsplit: refunded = True
                t_req = max(clock, last_exit + fd.get("req_wait", 0.25))   # at least 15 minutes after the last close
                sday = None
                if fd.get("session_tz") and hasattr(tr, "utc"):
                    t_req, sday = _session_req(tr, clock, last_exit + fd.get("req_wait", 0.25))
                if fd.get("protected"):                         # deducted at once and final (Topstep)
                    t_proc = t_req
                else:
                    t_proc = _bdays(tr, t_req, fd.get("review_bd", fd.get("process", 1))) + fd.get("review_h", 0.0)
                t_cash = _bdays(tr, t_proc, fd.get("transfer_bd", 0))
                clock = max(clock, t_req)
                paid += cash; npay += 1; x -= amt; day_ref -= amt; day_peak -= amt; t_act = clock
                if fd.get("session_tz"):                       # Topstep: the request's session is not counted again
                    excl_day = sday if sday is not None else int(t_req // DAY)
                pdates = []; day_pnl_c = 0.0; cyc_days = set()
                if PAYLOG is not None: PAYLOG.append((t_cash, cash, t_req, "payout", t_proc))
                if tfirst is None: tfirst = t_cash
                pend = dict(t_proc=t_proc, t_cash=t_cash, cash=cash, first=npay == 1) if t_proc > t_req + 1e-9 else None
                if fd.get("reset_on_payout"):
                    H = x; floor = x - dd
                if fd.get("lock_after_first_payout") and npay == 1:
                    floor = max(floor, lock)
                cyc_profit_start = x; qdays = 0; cyc_best = 0.0; dbest_c = 0.0; tgt_up = 0.0; fcap = _fcap()
                # the next request: cycle days after this one, or (Fintokei, The5ers) after the payout is processed
                t_next = t_proc if fd.get("cycle_from_processed") else t_req
                next_pay = t_next + max(fd["cycle"], 1) * DAY if not fd["ondemand"] else t_req + DAY
                if maxp and npay >= maxp:
                    return _end(None)
                if pend is not None and (fd.get("lock_processing") or fd.get("pause_pending")):
                    clock = pend["t_proc"]; pend = None        # locked (or paused) until processed: nothing can happen
                continue
        # ---- reached this cycle's target: wait for the payout date (not while trading days are still being collected);
        # the account is never left 25 days without a trade (version 10: several firms close or deactivate an account
        # after 30 days without one, BrightFunded among them): a minimal position held 3 minutes keeps it active
        if (x >= target_now - 0.01 and not fd.get("q_days") and pdays_ok and not gate and kind == "trade"
                and next_pay < 1e17):
            ka = fd.get("keepalive_days", 25)
            if ka and next_pay > max(last_exit, t0) + ka * DAY and not nofill:
                clock = max(clock + 0.01, max(last_exit, t0) + ka * DAY); kind = "filler"
                RULE_HITS["keepalive"] += 1
            else:
                clock = max(clock + 0.01, next_pay); continue
        te0 = _next_entry(tr, clock, fw)
        if int(te0 // DAY) != day:                     # the next entry opens on a later day: decide it there (n12)
            clock = te0; continue
        if kind == "filler" and day in cyc_days:       # one filler a day
            clock = (day + 1) * DAY + 0.01; continue
        dp = 0.0 if fd.get("per_trade") else day_pnl      # per_trade: caps apply to each trade, not each day (analytic check)
        lmin, lm = _lmin(tr, clock, fw)
        room_day = 1e18; brk = x - floor
        if dll:
            ref = day_peak if trail_dll else day_ref
            allow = _dll_at(dll, mode, firm["size"], day_ref) - (ref - x)
            room_day = (allow - 200.0 * bs) / (1.0 + rho); brk = min(brk, allow)
        if kind == "filler":
            l = w = 0.0; opts = dict(kind="filler", breach=brk)
        else:
            # ---- best-day rule on cycle-based accounts: cap each day's profit
            if best_eff and not fd.get("q_days") and dp >= best_eff * max(target_now, 1.0) - 0.5 * bs:
                clock = (day + 1) * DAY + 0.01; continue
            # ---- futures-style: stop for the day once the day qualifies
            if fd.get("q_days") and day_pnl_c >= fd["q_min"]:
                clock = (day + 1) * DAY + 0.01; continue
            l, terminal = _risk(tr, x, floor, room_day, lmin, lm, bs, rho, firm.get("max_risk_rule"))
            lev = firm.get("lev")                      # margin cap at the current balance (and FunderPro's 20% of the start)
            if l is not None and lev:
                l = min(l, lev[1] * tr.s * min(lev[2] * (firm["size"] + x), lev[3] * firm["size"]))
                if not terminal and l < lmin: l = None
            if l is None:
                clock = (day + 1) * DAY + 0.01; continue
            rule_cap = 1e18
            if best_eff and not fd.get("q_days"):            # best-day / concentration rule: cap today's win
                rule_cap = best_eff * max(target_now, 1.0) - dp
                if fd.get("best"): rule_cap -= 1.0 * bs     # a firm best-day rule (FXIFY): $1 per $100K under its limit
            if fd.get("max_win"): rule_cap = min(rule_cap, fd["max_win"])   # per-trade cap (used by the analytic check)
            dcap = fd.get("day_profit_cap")
            if dcap:
                if dp >= dcap - 1.0:
                    clock = (day + 1) * DAY + 0.01; continue
                rule_cap = min(rule_cap, dcap - dp)
            if ceiling:
                rule_cap = min(rule_cap, ceiling - x)
                if pdn and not pdays_ok:                     # keep room under the ceiling for the profitable days still
                    # needed: a win that makes today a profitable day keeps 1.1 x the day's minimum for each day still
                    # needed after today (a win that does not is limited further below)
                    rule_cap = min(rule_cap, ceiling - x - 1.1 * pdn[1] * (pdn[0] - cyc_pdays - 1))
            if rcap:                                         # every rolling window that will contain this trade stays
                run_s = 0.0; top = 0.0                        # under the cap: the largest suffix sum of the last 30 days'
                for (tc, p) in reversed(closed):              # closed trades (a window grows when an old loss drops out)
                    if tc <= clock - rcap[1] * DAY: break
                    run_s += p; top = max(top, run_s)
                rule_cap = min(rule_cap, rcap[0] - top)
            if rule_cap <= 0.5 * bs:
                if ceiling and ceiling - x <= 0.5 * bs and next_pay < 1e17 and pdays_ok:   # at the ceiling: wait
                    clock = max(clock + 0.01, next_pay); continue
                clock = (day + 1) * DAY + 0.01; continue
            if fd.get("q_days"): plan_cap = 1e18
            elif gate and x >= target_now - 0.01: plan_cap = 1e18     # collecting trading days: an ordinary trade a day
            else: plan_cap = target_now - x
            if pdn and fcap is not None and not pdays_ok:       # daily profit target until the cycle has its profitable days
                if fcap - day_pnl_c <= 0.5 * bs:
                    clock = (day + 1) * DAY + 0.01; continue
                plan_cap = min(plan_cap, fcap - day_pnl_c)
                if ceiling and x >= target_now - 0.01: plan_cap = fcap - day_pnl_c     # Maven: target reached, days missing
            w, l = _win(tr, l, plan_cap, rule_cap, bs, fresh=dp <= 0, lc=lm, lv=lm)
            if w is None and ceiling and not pdays_ok and getattr(tr, "wmin_frac", 0.0) > 0 and rule_cap >= 1.0 * bs:
                # at Maven's ceiling with profitable days still missing: a smaller trade whose target is the room left,
                # its risk lowered so the take-profit keeps the minimum distance (otherwise the account could never move)
                w = rule_cap; l = min(l, w / tr.wmin_frac)
            if w is not None and ceiling and pdn and not pdays_ok and day_pnl_c + w < pdn[1] - 1e-9:
                # a win that would leave today short of a profitable day must keep room under the ceiling for today as
                # well: it is cut to the room above that reserve (risk lowered to keep the minimum distance), or the plan
                # waits for tomorrow (version 8, n10)
                nq = min(rule_cap, ceiling - x - 1.1 * pdn[1] * (pdn[0] - cyc_pdays))
                if nq < 1.0 * bs: w = None
                elif nq < w:
                    w = nq
                    if getattr(tr, "wmin_frac", 0.0) > 0: l = min(l, w / tr.wmin_frac)
            if w is None:
                clock = (day + 1) * DAY + 0.01; continue
            opts = dict(breach=brk, terminal=terminal, hold=hold)
            if fd.get("shield"): opts["shield"] = fd["shield"]          # Blue Guardian's Guardian Shield (2% floating loss)
            if fd.get("max_lots"): opts["max_lots"] = fd["max_lots"]    # Alpha Capital's lot limit
            if fd.get("void_min"): opts["void_min"] = fd["void_min"]    # GFT: wins held under a minute are removed
            if fd.get("min_rr"):                          # Maven: reward:risk policy on the position actually placed
                r = _rr_fix(tr, clock, fw, l, w, opts, fd["min_rr"], rule_cap, bs)
                if r is None:
                    clock = (day + 1) * DAY + 0.01; continue
                l, w, kw = r
                if kw is not None: opts["keep_w"] = kw
        one_a_day = gate_first or (gate and x >= target_now - 0.01)   # Alpha before its first payout; Fintokei above target
        tr.last_entry = None; tr.last_exit = None; tr.last_info = None
        pnl, h = tr.trade(l, w, clock, fw, opts)
        if _why(tr) == "unaffordable":                 # not even the smallest position fits the breach room: abandoned
            RULE_HITS["abandoned"] += 1; return _end(None)
        te, tx, dur, breached = _trade_info(tr, clock, h)
        info = getattr(tr, "last_info", None) or {}
        t_act = clock + h; last_exit = tx
        if next_pay > 1e17 and not fd.get("q_days"): next_pay = te + fd["first_payout"] * DAY
        dtr = int(te // DAY)
        x += pnl; clock += h; day_pnl += pnl; day_pnl_c += pnl
        if TRADELOG is not None: TRADELOG.append(("funded", te, x - pnl, pnl, tx, opts.get("kind", "trade"), dur))
        cyc_days.add(dtr); all_days.add(dtr); durs.append((dur, pnl))
        if info.get("voided"): RULE_HITS["voided"] += 1
        if rcap: closed.append((tx, pnl))               # dated by the close (version 9: version 8 used the next-entry time)
        if breached: return _end(tx)                    # the trade reached the floor or today's limit: account lost
        if info.get("shield"):                          # Blue Guardian: the first Guardian Shield cuts the split to 50% for
            shields += 1                                # good, the second breaches the account (version 10: review of
            if shields >= 2:                            # version 9, finding 6)
                RULE_HITS["shield_second"] += 1; return _end(tx)
            RULE_HITS["shield_first"] += 1; split = fd.get("shield_split", 0.5)
        if firm.get("short_breach") and dur < 2.0 - 1e-9:
            RULE_HITS["short_breach"] += 1; return _end(tx)
        if dll and ((day_peak if trail_dll else day_ref) - x) > _dll_at(dll, mode, firm["size"], day_ref) + 1e-6:
            return _end(tx)                             # daily loss limit breached: account lost
        day_peak = max(day_peak, x)
        if one_a_day: clock = max(clock, (int(clock // DAY) + 1) * DAY + 0.01)   # one trade a day while collecting days
    STUCK[0] += 1; STUCK_INFO.append(("funded-loop", dict(x=x, npay=npay)))
    return _end(None)


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
