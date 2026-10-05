"""
Firm-rule engine (acct_mc) driven by actual price paths instead of random draws.

PathTrader.trade(l, w, clock): waits for the next allowed entry hour, opens a random-direction
bracket (stop = m x hourly sigma, target = stop x (w + cost)/l, so a win nets w) at that bar's open, walks the bars until the
stop or target is hit (gaps fill at the open; inside a bar the one-minute sub-steps give the order; only if both are
touched inside one sub-step does a fair coin, l/(l+w), decide), charges spread/commission and overnight financing, and
returns (pnl, hours until the next entry may be considered; an exit after minute 50 adds an hour: the 10-minute gap).
With flat_weekend=True (funded accounts that forbid weekend holding) nothing opens after
Friday 19:00 UTC and an open position is closed at the Friday 20:00 UTC bar's close.
Price data: synthetic zero-edge random walk with the instrument's real hourly volatility
(data="synth") or the real hourly series (data="real").
"""
import json, math, random, sys
import numpy as np
import acct_mc as A
import multi

import collections
_DATA = collections.OrderedDict()
MAX_CACHE = 10          # paths kept in memory per process (a 12-year path with one-minute sub-steps takes ~130 MB)

def synth_name(data, with_sub=False):
    """synth = seed 11, 12 years; synthN = seed N; synthNyY = Y years; ...sS = S sub-steps per hour (default 60 since
    version 8, one minute each; version 7: 12)"""
    body = data[5:]; sub = 60
    if "s" in body: body, sb = body.split("s"); sub = int(sb)
    sd, yrs = 11, 12.0
    if body:
        if "y" in body: a, b = body.split("y"); sd, yrs = int(a), float(b)
        else: sd = int(body)
    return (sd, yrs, sub) if with_sub else (sd, yrs)

def sibling(data, off=0):
    """the path name another market of the same life uses. Version 8: the same name, because multi.load_synth keys
    every random stream by market as well as by path number (version 7 offset the number, which made paths collide)"""
    return data

def evict(data):
    for key in [k for k in _DATA if k[1] == data]: del _DATA[key]

def _store(key, idx, d):
    wd = idx.weekday.values; hr = idx.hour.values
    _DATA[key] = dict(O=d["O"].tolist(), H=d["H"].tolist(), L=d["L"].tolist(), C=d["C"].tolist(),
                      ok=d["ok"].tolist(), entry=d["entry"].tolist(), roll=d["roll"].tolist(),
                      sig=d["sig"], cost=d["cost"], fin=d["fin"],
                      fri_late=((wd == 4) & (hr >= 19)).tolist(), fri_close=((wd == 4) & (hr == 20)).tolist(),
                      T=len(idx), h0=int(hr[0]), hour=hr.tolist(), norm=bool(d.get("norm", False)))
    if "sH" in d: _DATA[key].update(sH=d["sH"], sL=d["sL"], sub=d["sub"])

CORR_NAMES = ["US100", "XAUUSD", "EURUSD", "USDJPY"]
def _load_corr(data):
    """'corrR_NyY': the four markets on one joint path, every pair with correlation R/100 (sensitivity runs); the
    micro Nasdaq future follows the Nasdaq CFD's path with its own costs"""
    r, rest = data[4:].split("_")
    sd, yrs, sub = synth_name("synth" + rest, True)
    idx, D, day = multi.load_synth(CORR_NAMES, int(r) / 100.0, seed=sd, years=yrs, sub=sub)
    for nm in CORR_NAMES: _store((nm, data), idx, D[nm])
    u = D["US100"]; f = multi._finish(idx, "MNQ_fut", u["O"], u["H"], u["L"], u["C"], u["sig"])
    f.update(sH=u["sH"], sL=u["sL"], sub=u["sub"], norm=True)
    _store(("MNQ_fut", data), idx, f)

def market(instr, data):
    key = (instr, data)
    if key in _DATA:
        _DATA.move_to_end(key); return _DATA[key]
    while len(_DATA) >= MAX_CACHE: _DATA.popitem(last=False)
    if key not in _DATA and data.startswith("corr"):
        _load_corr(data)
    if key not in _DATA:
        if data.startswith("synth"):
            sd, yrs, sub = synth_name(data, True)            # "synth" = seed 11; "synth23" = an independent path;
            idx, D, day = multi.load_synth([instr], 0.0, seed=sd, years=yrs, sub=sub)   # "synth5001y2" = 2 years
        else:
            idx, D, day = multi.load_aligned([instr])
        d = D[instr]
        wd = idx.weekday.values; hr = idx.hour.values
        _DATA[key] = dict(O=d["O"].tolist(), H=d["H"].tolist(), L=d["L"].tolist(), C=d["C"].tolist(),
                          ok=d["ok"].tolist(), entry=d["entry"].tolist(), roll=d["roll"].tolist(),
                          sig=d["sig"], cost=d["cost"], fin=d["fin"],
                          fri_late=((wd == 4) & (hr >= 19)).tolist(), fri_close=((wd == 4) & (hr == 20)).tolist(),
                          T=len(idx), h0=int(hr[0]), hour=hr.tolist(), norm=bool(d.get("norm", False)))
        if "sH" in d: _DATA[key].update(sH=d["sH"], sL=d["sL"], sub=d["sub"])
    return _DATA[key]

def first_touch(M, i, d, sl, tp, p_fair, rng):
    """stop and target both inside hourly bar i: replay the bar's sub-steps in time order (synthetic paths);
    only if both fall inside the same sub-step, or no sub-steps exist (real data), use the fair chance p_fair"""
    return _first_touch(M, i, d, sl, tp, p_fair, rng)[0]

def _first_touch(M, i, d, sl, tp, p_fair, rng):
    """(won, sub-step of the exit or None)"""
    sH = M.get("sH")
    if sH is not None:
        sL = M["sL"]; n = M["sub"]; b = i * n
        for j in range(n):
            h = sH[b + j]; lo = sL[b + j]
            if d > 0: hs = lo <= sl; ht = h >= tp
            else:     hs = h >= sl; ht = lo <= tp
            if hs and ht: return rng.random() < p_fair, j
            if ht: return True, j
            if hs: return False, j
    return rng.random() < p_fair, None

REF_NQ = 31070.0        # Nasdaq 100 level on 2 October 2026; synthetic Nasdaq paths start at 100
def contract_value(M, price):
    """dollars per 1.0 of relative price move for one micro Nasdaq contract ($2 per index point) at this price. Version 8
    converts the normalised synthetic price back to the index level at every entry, 31,070 x price / 100 (version 7
    used 31,070 throughout, review of version 7, finding 25)"""
    return 2.0 * (REF_NQ * price / 100.0 if M.get("norm") else price)

GAP_MIN = 10            # minutes between a close and the next entry at every firm (Hola Prime, FundingPips trade ideas)
SHORT_MIN = 2           # trades that may have lasted under 2 minutes (Blue Guardian, Alpha Capital duration rules)

class Stats:
    """per-trader record of what the firms' duration rules look at, and of the path generator's error bound"""
    def __init__(self):
        self.n = 0; self.short = 0; self.minutes = 0.0; self.gross_win = 0.0; self.gross_win_short = 0.0
        self.bridge_eps = 0.0; self.late = 0; self.contracts = 0; self.last_exit = None
    def as_dict(self):
        return dict(n=self.n, short=self.short, minutes=self.minutes, gross_win=self.gross_win,
                    gross_win_short=self.gross_win_short, bridge_eps=self.bridge_eps, late=self.late)

def resolve(M, i, d, l, w, s, cost, flat_weekend, flat_daily, rng, futures=False, block=None, st=None):
    """A bracket opened at bar i's open in direction d: stop at s below/above the entry, risk l, a win nets w after the
    round-trip cost. Exits: a barrier touched inside a bar (time order from the sub-steps), a gap through a barrier at a
    bar's open, the daily flat time, a blocked (news) hour, the Friday close on weekend-flat accounts.
    Returns (pnl, hours until the next entry may be considered, contracts). An exit after minute 50 of a bar delays
    the next entry by one more hour, so at least 10 minutes always pass between a close and the next entry (version 7
    could re-enter at the next hour's open one minute after a close, review finding 10)."""
    T = M["T"]; e = M["O"][i]; n_c = 0
    if futures:                                   # whole micro contracts at this entry's index level, rounded down
        per = contract_value(M, e) * s
        n_c = max(1, math.floor(l / per + 1e-9)); f = n_c * per / l; l *= f; w *= f
    notional = l / s; fee = cost * notional; wg = w + fee
    sl = e * (1 - d * s); tp = e * (1 + d * s * wg / l)
    rolls = 0; bars = 0; first = True; last = e; exit_px = None; minute = 0.0; late = False
    sub = M.get("sub")
    while True:
        if M["ok"][i]:
            o = M["O"][i]
            if not first:
                if M["roll"][i]: rolls += 1
                if d * (o - sl) <= 0 or d * (o - tp) >= 0: exit_px = o; break        # gap through a barrier
                if flat_daily is not None and M["hour"][i] == flat_daily: exit_px = o; break
                if block and M["hour"][i] in block: exit_px = o; break
            if d > 0: hs = M["L"][i] <= sl; ht = M["H"][i] >= tp
            else:     hs = M["H"][i] >= sl; ht = M["L"][i] <= tp
            if hs or ht:
                won, j = _first_touch(M, i, d, sl, tp, l / (l + wg), rng)
                if not (hs and ht): won = ht
                exit_px = tp if won else sl
                if j is None or sub is None: minute = 60.0; late = True          # unknown: assume the worst
                else: minute = (j + 1) * 60.0 / sub; late = minute > 60 - GAP_MIN
                break
            last = M["C"][i]
            if flat_weekend and M["fri_close"][i]: exit_px = last; minute = 60.0; late = True; break
        first = False; bars += 1; i += 1
        if i >= T: exit_px = last; break
    pnl = notional * d * (exit_px - e) / e - fee - M["fin"] * notional * rolls
    if st is not None:
        st.last_exit = (i, minute)                # bar of the exit and the minute inside it (upper bound)
        dur = bars * 60.0 + minute
        st.n += 1; st.minutes += dur; st.late += late; st.contracts += n_c
        short = dur <= SHORT_MIN + 1e-9
        st.short += short
        if pnl > 0:
            st.gross_win += pnl
            if short: st.gross_win_short += pnl
        if sub:                                   # path-generator error bound: exp(-W^2 / v) per sub-step spent in the trade
            W = abs(math.log(tp / sl)); v = M["sig"] ** 2 / sub
            st.bridge_eps += (bars * sub + max(minute * sub / 60.0, 1.0)) * math.exp(-W * W / v)
    return pnl, bars + 1 + (1 if late else 0), n_c

def entry_index(M, i, flat_weekend, flat_daily, block=None):
    """the first bar at or after i where the plan may open a position: market open, inside the instrument's entry hours,
    not Friday evening on weekend-flat accounts, before the daily flat cut-off (no entry in the hour before it), and not
    in or just before a blocked hour (news proxy). Returns (index, bars waited)."""
    T = M["T"]; waited = 0
    while (not M["entry"][i] or (flat_weekend and M["fri_late"][i])
           or (flat_daily is not None and M["hour"][i] >= flat_daily - 1)
           or (block and (M["hour"][i] in block or (M["hour"][i] + 1) in block))):
        i = (i + 1) % T; waited += 1
    return i, waited

def filler_days(M, idx_of, clock, need, traded, flat_weekend, flat_daily):
    """advance through the real calendar to `need` more trading days not yet traded, one minimal filler trade on each
    (opened at the day's first permitted hour, held for at least 2 minutes, stop at most $3 per $100,000 of account).
    Returns the clock one hour after the last filler's entry. Version 7 added 7/5 calendar days per missing day, an
    average rather than the calendar (review finding 19)."""
    t = clock
    while need > 0:
        j, waited = entry_index(M, idx_of(t), flat_weekend, flat_daily)
        te = t + waited; dd = int(te // A.DAY)
        if dd in traded:
            t = (dd + 1) * A.DAY + 0.01; continue
        traded.add(dd); need -= 1; t = te + 1.0
    return t

WMIN_SD = 0.6           # the take-profit is never closer than 0.6 hourly sd: P(touched within 2 minutes) < 0.1%

class PathTrader:
    def __init__(self, instr, data, m, L, k, rng, cost_mult=1.0, dir_rule="random", flat_daily=None):
        self.M = market(instr, data); self.m = m; self.L = L; self.k = k; self.rng = rng
        self.dir_rule = dir_rule
        self.flat_daily = flat_daily          # e.g. 20: no entry at or after 19:00 UTC, close at the 20:00 UTC open
        self.cost = self.M["cost"] * cost_mult
        self.rho = self.cost / (m * self.M["sig"])      # round-trip cost per dollar of risk (v7 sizing)
        self.s = m * self.M["sig"]                       # stop distance as a fraction of the price (margin check)
        self.futures = instr == "MNQ_fut"               # whole micro contracts at the entry's index level (version 8)
        self.min_l = 0.0
        # smallest win as a share of the risk: the target sits at least WMIN_SD hourly sd from the entry (version 8)
        self.wmin_frac = max(0.0, WMIN_SD / m - self.rho)
        # engine day boundaries (clock = 0 mod 24) fall at 22:00 UTC, the futures/CFD daily reset
        self.base = 24 * rng.randrange(self.M["T"] // 48) + (22 - self.M["h0"]) % 24
        self.trades = 0; self.st = Stats(); self.last_entry = None

    def _idx(self, clock):
        return (self.base + int(clock)) % self.M["T"]

    def lmin_at(self, clock, flat_weekend=False):
        """the risk of one micro contract at the bar where the next trade would open (0 for CFDs)"""
        if not self.futures: return 0.0
        i, _ = entry_index(self.M, self._idx(clock), flat_weekend, self.flat_daily)
        return contract_value(self.M, self.M["O"][i]) * self.s

    def filler_days(self, clock, need, traded, flat_weekend=False):
        return filler_days(self.M, self._idx, clock, need, traded, flat_weekend, self.flat_daily)

    def next_entry(self, clock, flat_weekend=False):
        """the time the next trade would open (as trade() computes it)"""
        _, waited = entry_index(self.M, self._idx(clock), flat_weekend, self.flat_daily)
        return clock + waited

    def _direction(self, i):
        if self.dir_rule == "random":
            return 1 if self.rng.random() < 0.5 else -1
        # mechanical trend rules on completed hourly closes
        M = self.M; C = M["C"]; ok = M["ok"]; T = M["T"]
        closes = []; j = i - 1
        look = {"trend20": 21, "trend5": 6, "revert5": 6}[self.dir_rule]
        while len(closes) < look and j > i - 400:
            if ok[j % T]: closes.append(C[j % T])
            j -= 1
        if len(closes) < look: return 1 if self.rng.random() < 0.5 else -1
        up = closes[0] > closes[-1]
        if self.dir_rule == "revert5": up = not up
        return 1 if up else -1

    def trade(self, l, w, clock=None, flat_weekend=False):
        i, waited = entry_index(self.M, self._idx(clock), flat_weekend, self.flat_daily)
        d = self._direction(i)
        self.last_entry = clock + waited
        pnl, hours, _ = resolve(self.M, i, d, l, w, self.s, self.cost, flat_weekend, self.flat_daily, self.rng,
                                futures=self.futures, st=self.st)
        self.trades += 1
        return pnl, float(waited + hours)

def attempt(firm, instr, data, m, L, k, X1, X, rng, cost_mult=1.0, dir_rule="random"):
    tr = PathTrader(instr, data, m, L, k, rng, cost_mult, dir_rule, firm.get("flat_daily"))
    clock = rng.random() * A.DAY; t_start = clock
    fees = firm["fee"]; passed = 0
    credits = 0.0
    for j, st in enumerate(firm["phases"]):
        ok, clock = A.run_stage(st, tr, rng, firm, clock)
        if ok and firm.get("phase_credit"): credits += firm["phase_credit"][j]
        if not ok:
            if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * A.DAY)))
            return dict(v=-fees + credits, days=(clock - t_start) / A.DAY, t1=None, npay=0, passed=passed,
                        t_eval=(clock - t_start) / A.DAY, paid=0.0, t_fund=0.0, trades=tr.trades, st=tr.st.as_dict())
        passed += 1
    if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * A.DAY)))
    fees += firm.get("activation", 0)
    t_eval = (clock - t_start) / A.DAY
    paid, clock2, tfirst, npay = A.run_funded(firm["funded"], tr, rng, firm, clock, X1, X)
    return dict(v=paid - fees + credits, days=(clock2 - t_start) / A.DAY,
                t1=(tfirst - t_start) / A.DAY if tfirst else None, npay=npay, passed=passed,
                t_eval=t_eval, paid=paid, t_fund=(clock2 - clock) / A.DAY, trades=tr.trades, fees=fees,
                st=tr.st.as_dict())

def evaluate(firm, instr="US100", data="synth", m=0.75, L=1500, k=3, X1=1000, X=10000, n=3000, seed=11,
             cost_mult=1.0, dir_rule="random"):
    rng = random.Random(seed)
    R = [attempt(firm, instr, data, m, L, k, X1, X, rng, cost_mult, dir_rule) for _ in range(n)]
    v = np.array([r["v"] for r in R]); days = np.array([r["days"] for r in R])
    npass = len(firm["phases"])
    P = np.mean([r["passed"] == npass for r in R])
    funded = [r for r in R if r["passed"] == npass]
    Vf = float(np.mean([r["paid"] for r in funded])) if funded else 0.0
    tf = float(np.mean([r["t_fund"] for r in funded])) if funded else 0.0
    t_eval = float(np.mean([r["t_eval"] for r in R]))
    act = firm.get("activation", 0)
    fee_attempt = float(np.mean([(r["fees"] - act if r["passed"] == npass else -r["v"]) for r in R]))
    t1 = [r["t1"] for r in R if r["t1"] is not None]
    out = dict(EV=float(v.mean()), CI=float(1.96 * v.std() / math.sqrt(n)), days=float(days.mean()),
               EV_month=float(v.mean() / (days.mean() / 30.44)),
               EV_month_CI=float(1.96 * v.std() / math.sqrt(n) / (days.mean() / 30.44)),
               P=float(P), Vf=Vf, t_fund=tf, t_eval=t_eval, fee_attempt=fee_attempt,
               t_first_med=float(np.median(t1)) if t1 else None,
               P_paid=len(t1) / n, payouts_per_funded=float(np.mean([r["npay"] for r in funded])) if funded else 0,
               trades=float(np.mean([r["trades"] for r in R])),
               P_ahead=float(np.mean(v > 0)))
    # if evaluations are not capped: one funded slot kept busy by parallel evaluations
    if P > 0 and tf > 0:
        out["EV_month_funded_slot"] = (Vf - act - fee_attempt / P) / (tf / 30.44)
        out["evals_per_funded_slot"] = (t_eval / P) / tf
    return out
