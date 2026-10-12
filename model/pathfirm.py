"""
Firm-rule engine (acct_mc) driven by actual price paths instead of random draws.

PathTrader.trade(l, w, clock, flat_weekend, opts): waits for the next allowed entry hour, opens a position at that bar's
open in the plan's direction and resolves it on the path (resolve below). Version 9: positions are whole lots (CFDs) or
whole contracts (futures) at each instrument's contract size; the account's own breach level (the floor or today's loss
limit, whichever is nearer) is a barrier of every trade, so a trade that reaches it ends the account at that moment even if
the price later recovers (review of version 8, finding 3); on accounts with a minimum holding time the bracket is placed
only after the first three minutes; filler trades are real minimal positions closed after three minutes; and every
trade reports its exit time (exposure, dated profits) separately from the time the next entry may be considered.
Price data: synthetic zero-edge random walks with the instrument's real hourly volatility and one-minute sub-steps.
"""
import json, math, random, sys
import numpy as np
import acct_mc as A
import multi

import collections, datetime as _dt
_DATA = collections.OrderedDict()
EPOCH_TS = __import__("pandas").Timestamp("2030-01-01", tz="UTC")     # bar 0 of every synthetic path (news calendar)
EPOCH = _dt.datetime(2030, 1, 1, tzinfo=_dt.timezone.utc)
MAX_CACHE = 8           # paths kept in memory per process (a 12-year path with one-minute sub-steps takes ~150 MB)

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
                      T=len(idx), h0=int(hr[0]), hour=hr.tolist(), wd=wd.tolist(), norm=bool(d.get("norm", False)),
                      instr=key[0], dated=bool(idx[0] == EPOCH_TS))
    if "sH" in d: _DATA[key].update(sH=d["sH"], sL=d["sL"], sC=d["sC"], sub=d["sub"])

CORR_NAMES = ["US100", "XAUUSD", "EURUSD", "USDJPY"]
def _load_corr(data):
    """'corrR_NyY': the four markets on one joint path, every pair with correlation R/100 (sensitivity runs); the
    micro Nasdaq future follows the Nasdaq CFD's path with its own costs"""
    r, rest = data[4:].split("_")
    sd, yrs, sub = synth_name("synth" + rest, True)
    idx, D, day = multi.load_synth(CORR_NAMES, int(r) / 100.0, seed=sd, years=yrs, sub=sub)
    for nm in CORR_NAMES: _store((nm, data), idx, D[nm])
    u = D["US100"]; f = multi._finish(idx, "MNQ_fut", u["O"], u["H"], u["L"], u["C"], u["sig"])
    f.update(sH=u["sH"], sL=u["sL"], sC=u["sC"], sub=u["sub"], norm=True)
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
        _store(key, idx, D[instr])
    return _DATA[key]

def free_market(instr, data):
    """the same path with no costs and no financing (theory checks); returns the name to trade it under"""
    key = (instr, data + "_free")
    if key not in _DATA:
        M = dict(market(instr, data)); M["fin"] = 0.0; M["cost"] = 0.0
        _DATA[key] = M
    return data + "_free"

def nofin_market(instr, data):
    """the same path with its trading costs but no overnight financing; returns the name to trade it under. The chain
    checks of verify_v9 run the engine without the daily flat, so its positions are held overnight; the chain has no
    financing and the plan pays none (it is flat every evening), so those runs must not pay it either (version 9, n20)"""
    key = (instr, data + "_nofin")
    if key not in _DATA:
        M = dict(market(instr, data)); M["fin"] = 0.0
        _DATA[key] = M
    return data + "_nofin"

# ---------------------------------------------------------------- contracts (version 9)
REF_NQ = 31070.0        # Nasdaq 100 level on 2 October 2026; synthetic Nasdaq paths start at 100
# Contract specifications (review of version 8, finding 4). ref: the market's close on 2 October 2026 (synthetic paths
# start at 100 and are scaled to it); cs: units per lot; usd_quote: the price is quoted in dollars (USDJPY: a lot is
# worth cs dollars); vmin, step: the smallest position and the volume step. Index CFDs: one lot = one unit of the index
# ($1 a point; FTMO's MT5 contract size for its index CFDs is 1); gold: 100 ounces a lot; currency pairs: 100,000 units of
# the base currency a lot; CFD volumes from 0.01 lot in steps of 0.01; micro Nasdaq future: $2 a point, whole contracts.
LOTS = {
    "US100": dict(ref=REF_NQ, cs=1.0, usd_quote=True, vmin=0.01, step=0.01),
    "XAUUSD": dict(ref=4176.80, cs=100.0, usd_quote=True, vmin=0.01, step=0.01),
    "EURUSD": dict(ref=1.1256, cs=100_000.0, usd_quote=True, vmin=0.01, step=0.01),
    "USDJPY": dict(ref=157.83, cs=100_000.0, usd_quote=False, vmin=0.01, step=0.01),
    "MNQ_fut": dict(ref=REF_NQ, cs=2.0, usd_quote=True, vmin=1.0, step=1.0),
}

def lot_spec(M):
    return LOTS.get(M.get("instr"), LOTS["US100"])

def unit_value(M, price):
    """dollars per 1.0 of relative price move for one lot (one contract) at this price"""
    sp = lot_spec(M)
    P = sp["ref"] * price / 100.0 if M.get("norm") else price
    return sp["cs"] * P if sp["usd_quote"] else sp["cs"]

def contract_value(M, price):
    """dollars per 1.0 of relative price move for one micro Nasdaq contract ($2 per index point) at this price; the
    normalised synthetic price is converted back to the index level, 31,070 x price / 100"""
    return 2.0 * (REF_NQ * price / 100.0 if M.get("norm") else price)

def min_risk(M, price, s):
    """the risk of the smallest position (0.01 lot of a CFD, one micro contract) with its stop s (relative) from the entry"""
    return lot_spec(M)["vmin"] * unit_value(M, price) * s

# ---------------------------------------------------------------- the path generator's error bound (version 9)
LOG3 = math.log(3.0)
_BE = {}
def bridge_err(r):
    """A valid bound on the chance that one sub-step of an open bracket resolves differently from the exact Brownian law.
    r = W / sqrt(v): the bracket's log width over the sub-step's standard deviation (less the drift per sub-step).
    The generator draws each sub-step's maximum and minimum from their exact laws given the sub-step's end points, but
    independently. Given end points a, b inside the bracket [l, u] (W = u - l), the two laws differ only through the event
    that both barriers are touched: the generator's chance is P_ind = exp(-2[(a-l)(b-l) + (u-a)(u-b)]/v), the exact chance
    is at most exp(-2[(a-l)(b-l) + W(u-b)]/v) + exp(-2[(u-a)(u-b) + W(b-l)]/v) <= 2 P_ind (strong Markov property of the
    bridge at the first touch), so the sub-step's outcome (none, stop, target) differs in total variation by at most
    3 P_ind; with an end point outside the bracket by at most 2 exp(-2(a-l)(b-l)/v), which is smaller. For an increment
    delta = b - a the largest P_ind over the start point a is exp(-(W^2 - delta^2)/v) (at a = l + (W - delta)/2). The
    increment is independent of where the sub-step starts and of whether the trade is still open, so the expected error
    per watched sub-step is at most G(r) = E[min(1, 3 exp(-(r^2 - Z^2)))], Z standard normal (1 for |Z| > r):
        G(r) = 6/sqrt(2 pi) exp(-(r^2 + ln 3)/2) J(x) + erfc(x/sqrt(2)),  x = sqrt(r^2 - ln 3),  J(x) = int_0^x e^((t^2-x^2)/2) dt.
    The expected error of a trade is at most the expected number of watched sub-steps times G (a union bound over sub-steps).
    Version 8 claimed exp(-W^2/v) per sub-step, which is false when the two end points lie near opposite barriers (review
    of version 8, finding 2); G(r) is close to exp(-r^2/2), the square root of the old figure."""
    key = math.floor(r * 100.0) / 100.0          # r rounded down: the bound only grows
    if key in _BE: return _BE[key]
    if key * key <= LOG3:
        val = 1.0
    else:
        x = math.sqrt(key * key - LOG3); n = 400
        t = np.linspace(0.0, x, n + 1); f = np.exp((t * t - x * x) / 2.0)
        J = (x / n) / 3.0 * (f[0] + f[-1] + 4.0 * f[1:-1:2].sum() + 2.0 * f[2:-1:2].sum())
        val = min(1.0, 6.0 / math.sqrt(2.0 * math.pi) * math.exp(-(key * key + LOG3) / 2.0) * J + math.erfc(x / math.sqrt(2.0)))
    _BE[key] = val
    return val

def joint_bound(M, intervals, c=5.0):
    """The path generator's error bound for every position on one market path at once (version 10: version 9's bound
    covered one bracket; for several accounts sharing a path, the per-bracket bounds do not add up to a bound on the joint
    outcome, review of version 9, finding 9).
    intervals: (first sub-step, end sub-step, log upper barrier, log lower barrier) of every position, as global sub-step
    indices of the path. In a sub-step with end points a, b (log prices), let u be the lowest upper barrier and l the
    highest lower barrier of all positions open in it. Everything the engine decides in the sub-step (which barriers are
    touched; the order, where a bracket's two barriers are both touched) is a function of the sub-step's maximum and
    minimum; the generator draws them independently from their exact marginal laws, so the joint law of the decisions
    differs from the exact one only through the event B that the sub-step touches both u and l. With P_g(B) =
    P(max >= u) P(min <= l) <= P_ind = exp(-2[(u-a)(u-b) + (a-l)(b-l)]/v) (each factor 1 when an end point is already
    beyond its barrier) and P_exact(B) <= 2 P_ind (strong Markov property at the first barrier touched), splitting the
    outcomes into 'nothing touched', 'only upper barriers', 'only lower barriers' and B gives a total variation distance of
    at most (|P_e - P_g| + 3 (P_e + P_g)) / 2 <= 5 P_ind per sub-step. Coupling the sub-steps one after another, the
    probability that the simulated outcomes of all positions differ from those of an exact Brownian path through the same
    sub-step end points is at most the sum over sub-steps of min(1, c P_ind), c = 5. Returns that sum."""
    if not intervals or not M.get("sub"): return 0.0
    sub = M["sub"]; v = M["sig"] ** 2 / sub
    j_lo = min(iv[0] for iv in intervals); j_hi = max(iv[1] for iv in intervals)
    n = j_hi - j_lo
    U = np.full(n, np.inf); Lw = np.full(n, -np.inf)
    for (j0, j1, up, lo) in intervals:
        a, b = j0 - j_lo, j1 - j_lo
        np.minimum(U[a:b], up, out=U[a:b]); np.maximum(Lw[a:b], lo, out=Lw[a:b])
    mask = np.isfinite(U) & np.isfinite(Lw)
    if not mask.any(): return 0.0
    idx = np.nonzero(mask)[0] + j_lo
    sC = np.asarray(M["sC"]); NS = len(sC)
    b_ = np.log(sC[idx % NS]); a_ = np.log(sC[(idx - 1) % NS])
    u = U[mask]; l = Lw[mask]
    pu = np.where(np.maximum(a_, b_) >= u, 1.0, np.exp(-2.0 * np.clip((u - a_) * (u - b_), 0.0, None) / v))
    pl = np.where(np.minimum(a_, b_) <= l, 1.0, np.exp(-2.0 * np.clip((a_ - l) * (b_ - l), 0.0, None) / v))
    return float(np.minimum(1.0, c * pu * pl).sum())

GAP_MIN = 10            # minutes between a close and the next entry at every firm (Hola Prime, FundingPips trade ideas)
SHORT_MIN = 2           # a trade that may have lasted under 2 minutes (Blue Guardian, Alpha Capital duration rules)
HOLD_MIN = 3            # minimum holding time of the plan where a firm has a duration rule, and of every filler trade

def hold_steps(minutes, sub):
    """sub-steps that cover at least `minutes` minutes at `sub` sub-steps per hour (version 10: version 9 used the number
    of minutes as a number of sub-steps, which is a number of minutes only at 60 sub-steps per hour: review of version 9,
    finding 7)"""
    if not minutes or not sub: return 0
    n = int(math.ceil(minutes * sub / 60.0 - 1e-9))
    assert n <= sub, "a holding time longer than an hour is not supported"
    return n

def news_bars(M, kind):
    """the plan's news blocks for a stage's news rule on this market (news_v10): None, or a list over the path's bars,
    True where the bar overlaps a restricted window. kind: None (the firm and stage have no news rule), "all" (every
    high-impact release that moves this market), "cpi" (US CPI releases only: Topstep)"""
    if not kind or not M.get("dated"): return None
    key = "news_" + kind
    if key not in M:
        import news_v10 as NW
        M[key] = NW.blocked(M["instr"], M["T"], cpi_only=(kind == "cpi")).tolist()
    return M[key]

class Stats:
    """per-trader record of what the firms' duration rules look at, and of the path generator's error bound"""
    def __init__(self):
        self.n = 0; self.short = 0; self.minutes = 0.0; self.gross_win = 0.0; self.gross_win_short = 0.0
        self.bridge_eps = 0.0; self.sub2 = 0; self.late = 0; self.contracts = 0.0; self.last_exit = None
        self.breach = 0; self.fillers = 0; self.filler_pnl = 0.0; self.min_lot = 0; self.hold_close = 0
        self.shield = 0; self.voided = 0; self.news_close = 0; self.unaffordable = 0; self.lots_capped = 0
        self.hold_over = 0
    def as_dict(self):
        return dict(n=self.n, short=self.short, minutes=self.minutes, gross_win=self.gross_win,
                    gross_win_short=self.gross_win_short, bridge_eps=self.bridge_eps, sub2=self.sub2, late=self.late,
                    breach=self.breach, fillers=self.fillers, filler_pnl=self.filler_pnl, min_lot=self.min_lot,
                    hold_close=self.hold_close, contracts=self.contracts, shield=self.shield, voided=self.voided,
                    news_close=self.news_close, unaffordable=self.unaffordable, lots_capped=self.lots_capped,
                    hold_over=self.hold_over)

def plan(M, i, l, w, s, cost, opts=None):
    """The position the plan places at bar i's open, before the market moves (version 10: one function for the trade
    itself and for every check the plan makes before placing it, so a check sees the rounded position actually traded).
    Returns dict(vol, notional, fee, e (entry price), sd, td (relative distances of the adverse barrier and of the
    take-profit, cost excluded), loss (dollars lost at the adverse barrier, cost included), win (dollars made at the
    take-profit, net of cost), capped (the volume was cut to a lot limit), afford (the position's cost is below the
    breach room)).
    Volume: l / (value of one lot x s), rounded down to the volume step, at least the smallest volume, at most the
    firm's lot limit (opts max_lots: Alpha Capital's 40 lots per $100K of funded account, version 10: review of version
    9, finding 4). The adverse barrier is the stop, the account's breach level (opts breach: dollars, cost included) or
    the firm's floating-loss shield (opts shield: dollars, cost included; Blue Guardian's funded Guardian Shield, version
    10: review of version 9, finding 6), whichever is nearest."""
    o = opts or {}
    e = M["O"][i]; sp = lot_spec(M); uv = unit_value(M, e)
    kind = o.get("kind", "trade"); breach = o.get("breach"); capped = False
    if kind == "filler":
        vol = sp["vmin"]
    else:
        vol = math.floor(l / (uv * s) / sp["step"] + 1e-9) * sp["step"]
        if vol < sp["vmin"] - 1e-12: vol = sp["vmin"]
        ml = o.get("max_lots")
        if ml is not None:
            cap = math.floor(ml / sp["step"] + 1e-9) * sp["step"]
            if vol > cap + 1e-12: vol = cap; capped = True
    notional = vol * uv; fee = cost * notional
    afford = breach is None or breach > fee + 1e-9
    bd = (breach - fee) / notional if breach is not None else math.inf
    shd = (o["shield"] - fee) / notional if o.get("shield") else math.inf
    if kind == "filler":
        sd = min(bd, shd); td = math.inf
    elif o.get("terminal"):
        sd = min(bd, shd); td = (w + fee) / notional
    else:
        sd = min(s, bd, shd)
        if not o.get("keep_w"): w = w * (notional * s) / l
        td = (w + fee) / notional
    loss = notional * sd + fee if sd < math.inf else math.inf
    win = notional * td - fee if td < math.inf else math.inf
    return dict(vol=vol, notional=notional, fee=fee, e=e, sd=sd, td=td, bd=bd, shd=shd, loss=loss, win=win,
                capped=capped, afford=afford, uv=uv, s=s, cost=cost, vmin=sp["vmin"], step=sp["step"])

def resolve(M, i, d, l, w, s, cost, flat_weekend, flat_daily, rng, block=None, st=None, opts=None, nb=None):
    """A position opened at bar i's open in direction d. Returns (pnl, hours until the next entry may be considered, info),
    info = dict(exit: hours from the entry to the exit (an upper bound inside its minute), dur: minutes held (a lower
    bound), breach: the account's breach level was reached, vol: lots or contracts, why: the exit, shield: the firm's
    floating-loss shield closed it, voided: its profit was removed by a minimum-holding rule).
    opts:
      kind      'trade': a bracket, stop s (relative) from the entry for a risk of l, a win netting w after the round-trip
                cost; 'filler': the smallest position, closed after HOLD_MIN minutes (a minimal trading-day trade)
      breach    the loss (dollars, cost included) at which the account breaches: the nearer of its floor and today's loss
                limit. It is a barrier of every trade: reaching it ends the account then, whatever the price does later
      shield    the floating loss (dollars, cost included) at which the firm closes the position (Blue Guardian funded)
      terminal  the stop is the breach level itself (the plan's last trade on an account near its floor)
      keep_w    the win was set by a cap (the target or a rule): rounding the volume down keeps the win (the take-profit is
                placed for exactly that amount) instead of scaling it with the risk
      hold      minutes before the bracket is placed (accounts with a minimum holding time): until then only the breach
                level and the shield can close the position; at the end of the hold it is closed at once if the price is
                already beyond the stop or the take-profit
      max_lots  the firm's lot limit (plan)
      void_min  a winning trade held under this many minutes has its profit removed (GFT funded accounts): its result is
                then minus its cost
    nb: the plan's news blocks (news_bars) or None. block: hours of the day the plan is flat (the news proxy stress test).
    A position whose cost alone reaches the breach room is not opened (version 10: version 9 returned minus the breach room,
    so the cost charged was clipped: review of version 9, finding 8); info why = 'unaffordable', and the plan stops
    trading the account. Exits: a barrier touched inside a one-minute sub-step (in time order; a sub-step that touches
    both barriers is decided by the martingale chance from the sub-step's start, an error bound_err bounds), a gap
    through a barrier at a bar's open, the daily flat time, a blocked (news) bar, the Friday close on weekend-flat
    accounts. An exit after minute 50 of a bar delays the next entry by one more hour, so at least 10 minutes pass
    between a close and the next entry."""
    o = opts or {}
    T = M["T"]; sp = lot_spec(M)
    kind = o.get("kind", "trade"); breach = o.get("breach"); sub = M.get("sub")
    sH = M.get("sH"); sL = M.get("sL"); sC = M.get("sC")
    P = plan(M, i, l, w, s, cost, o)
    e = P["e"]; vol = P["vol"]; notional = P["notional"]; fee = P["fee"]
    hold = hold_steps(HOLD_MIN if kind == "filler" else o.get("hold", 0), sub) if sub else 0
    info = dict(exit=0.0, dur=0.0, breach=False, vol=vol, why=None, shield=False, voided=False, notional=notional,
                loss_plan=P["loss"], win_plan=P["win"], capped=P["capped"])
    if not P["afford"]:                                  # the smallest position's cost alone reaches the breach level
        info.update(why="unaffordable")
        if st is not None: st.unaffordable += 1
        return 0.0, 0, info
    bd, shd, sd, td = P["bd"], P["shd"], P["sd"], P["td"]
    lo_d = sd                                             # the nearest adverse barrier (stop, breach level or shield)
    if kind != "filler" and not o.get("terminal") and s <= min(bd, shd): adv = "stop"
    else: adv = "breach" if bd <= shd else "shield"
    lo_px = e * (1 - d * lo_d) if lo_d < math.inf else (-math.inf if d > 0 else math.inf)
    sl_px = lo_px
    tp = e * (1 + d * td) if td < math.inf else None
    hold_d = min(bd, shd)                                 # watched during the hold: the breach level and the shield
    rolls = 0; bars = 0; first = True; last = e; exit_px = None; why = None
    t_ex = 0.0; dur = 0.0; n2 = 0

    def scan(b0, j0, j1):
        """sub-steps j0..j1-1 of the bar whose first sub-step is b0: (j, target first) at the first touch, or None"""
        for j in range(j0, j1):
            lo = sL[b0 + j]; hi = sH[b0 + j]
            if d > 0: hs = lo <= lo_px; ht = tp is not None and hi >= tp
            else:     hs = hi >= lo_px; ht = tp is not None and lo <= tp
            if hs or ht:
                if hs and ht:
                    a = sC[b0 + j - 1] if b0 + j > 0 else e
                    ht = rng.random() < min(max((a - lo_px) / (tp - lo_px), 0.0), 1.0)
                return j, ht
        return None

    while True:
        if M["ok"][i]:
            op = M["O"][i]
            if not first:
                if M["roll"][i]: rolls += 1
                if d * (op - lo_px) <= 0 or (tp is not None and d * (op - tp) >= 0):
                    exit_px = op; why = "gap"; t_ex = float(bars); break
                if flat_daily is not None and M["hour"][i] == flat_daily: exit_px = op; why = "flat"; t_ex = float(bars); break
                if block and M["hour"][i] in block: exit_px = op; why = "block"; t_ex = float(bars); break
                if nb is not None and nb[i]: exit_px = op; why = "news"; t_ex = float(bars); break
            if first and hold:
                b0 = i * sub; hit = None
                if hold_d < math.inf:                    # the holding time: only the breach level and the shield
                    h_px = e * (1 - d * hold_d)
                    for j in range(hold):
                        if (sL[b0 + j] <= h_px) if d > 0 else (sH[b0 + j] >= h_px): hit = j; break
                if hit is not None:
                    exit_px = h_px; why = "breach" if bd <= shd + 1e-15 else "shield"
                    t_ex = (hit + 1) / sub; dur = hit * 60.0 / sub; break
                c = sC[b0 + hold - 1]
                if kind == "filler" or d * (c - sl_px) <= 0 or (tp is not None and d * (c - tp) >= 0):
                    exit_px = c; why = "time" if kind == "filler" else "hold"; t_ex = hold / sub; dur = hold * 60.0 / sub
                    if kind != "filler" and tp is not None and d * (c - tp) > 0: info["over_target"] = True
                    break
                r = scan(b0, hold, sub)
                if r is not None:
                    j, won = r; n2 += j - hold + 1
                    exit_px = tp if won else lo_px; why = "target" if won else adv
                    t_ex = (j + 1) / sub; dur = j * 60.0 / sub; break
                n2 += sub - hold
            else:
                if d > 0: hs = M["L"][i] <= lo_px; ht = tp is not None and M["H"][i] >= tp
                else:     hs = M["H"][i] >= lo_px; ht = tp is not None and M["L"][i] <= tp
                if hs or ht:
                    if sub:
                        j, won = scan(i * sub, 0, sub); n2 += j + 1
                        t_ex = bars + (j + 1) / sub; dur = (bars * sub + j) * 60.0 / sub
                    else:                                # no sub-steps (real hourly data): a fair chance, the worst minute
                        won = ht if not (hs and ht) else rng.random() < min(max((e - lo_px) / (tp - lo_px), 0.0), 1.0)
                        t_ex = bars + 1.0; dur = bars * 60.0
                    exit_px = tp if won else lo_px; why = "target" if won else adv
                    break
                if sub: n2 += sub
            last = M["C"][i]
            if flat_weekend and M["fri_close"][i]: exit_px = last; why = "fri"; t_ex = bars + 1.0; dur = t_ex * 60.0; break
        first = False; bars += 1; i += 1
        if i >= T: exit_px = last; why = "end"; t_ex = float(bars); dur = t_ex * 60.0; i = T - 1; break
    if why == "breach":
        pnl = -float(breach)
    elif why == "shield":
        pnl = -float(o["shield"])
    else:
        pnl = notional * d * (exit_px - e) / e - fee - M["fin"] * notional * rolls
    breached = why == "breach" or (breach is not None and pnl <= -breach + 1e-9)
    if not breached and why != "shield" and o.get("shield") and pnl <= -o["shield"] + 1e-9:
        why = "shield"                                    # a gap through the shield level: the firm's close
    if why in ("gap", "flat", "block", "news", "end"): dur = t_ex * 60.0
    vm = o.get("void_min")
    if vm and pnl > 0 and dur < vm - 1e-9:               # a win held under the firm's minimum: its profit is removed
        pnl = -fee; info["voided"] = True
    eb = int(math.floor(t_ex - 1e-9)) if t_ex > 0 else 0            # the bar of the exit, counted from the entry bar
    minute = (t_ex - eb) * 60.0
    late = minute > 60 - GAP_MIN + 1e-9 or (sub is None and why in ("target", "stop", "breach", "shield"))
    hours = eb + 1 + (1 if late else 0)
    if why in ("gap", "flat", "block", "news", "end"): hours = int(round(t_ex)) + 1; late = False; minute = 0.0
    info.update(exit=t_ex, dur=dur, breach=breached, why=why, shield=why == "shield", td=td / M["sig"],
                sd=lo_d / M["sig"], sd_rel=lo_d, td_rel=td, e=e, d=d, lo_px=lo_px, tp=tp)
    if st is not None:
        st.last_exit = (i, minute)
        st.n += 1; st.minutes += dur; st.late += late; st.contracts += vol
        st.breach += breached; st.hold_close += why == "hold"; st.shield += why == "shield"
        st.voided += bool(info["voided"]); st.news_close += why == "news"; st.lots_capped += bool(P["capped"])
        st.hold_over += bool(info.get("over_target"))
        st.min_lot += kind != "filler" and vol <= sp["vmin"] + 1e-12
        if kind == "filler": st.fillers += 1; st.filler_pnl += pnl
        short = dur < SHORT_MIN - 1e-9
        st.short += short
        if pnl > 0:
            st.gross_win += pnl
            if short: st.gross_win_short += pnl
        if sub and n2 and tp is not None:              # the generator's error bound for this trade
            W = abs(math.log(tp / lo_px)); sv = M["sig"] / math.sqrt(sub)
            st.sub2 += n2; st.bridge_eps += n2 * bridge_err(W / sv - 0.5 * sv)     # r less the drift per sub-step (sigma^2/2 per hour, in sd)
    return pnl, hours, info

def entry_index(M, i, flat_weekend, flat_daily, block=None, nb=None):
    """the first bar at or after i where the plan may open a position: market open, inside the instrument's entry hours,
    not Friday evening on weekend-flat accounts, before the daily flat cut-off (no entry in the hour before it), and not
    in or just before a blocked hour (news proxy) or a blocked news bar (nb). Returns (index, bars waited)."""
    T = M["T"]; waited = 0
    while (not M["entry"][i] or (flat_weekend and M["fri_late"][i])
           or (flat_daily is not None and M["hour"][i] >= flat_daily - 1)
           or (block and (M["hour"][i] in block or (M["hour"][i] + 1) in block))
           or (nb is not None and (nb[i] or nb[(i + 1) % T]))):
        i = (i + 1) % T; waited += 1
    return i, waited

def next_bar(clock):
    """the start of the first hourly bar that has not begun before the clock"""
    return int(math.ceil(clock - 1e-9))

def add_bdays(M, idx_of, clock, n):
    """clock plus n working days (Monday to Friday, by the UTC calendar of the path), at the same time of day: a review of
    n working days that starts on a Friday ends after the weekend (version 9; version 8 added n x 24 hours, review of
    version 8, finding 20)"""
    t = clock; k = 0
    while k < n:
        t += 24.0
        if M["wd"][idx_of(t)] < 5: k += 1
    return t

WMIN_SD = 0.6           # the plan never places a take-profit closer than 0.6 hourly sd to the entry (a plan choice; the
                        # firms' duration rules are met by the minimum holding time, HOLD_MIN, not by this distance)

class PathTrader:
    def __init__(self, instr, data, m, L, k, rng, cost_mult=1.0, dir_rule="random", flat_daily=None):
        self.M = market(instr, data); self.m = m; self.L = L; self.k = k; self.rng = rng
        self.dir_rule = dir_rule
        self.flat_daily = flat_daily          # e.g. 20: no entry at or after 19:00 UTC, close at the 20:00 UTC open
        self.cost = self.M["cost"] * cost_mult
        self.rho = self.cost / (m * self.M["sig"])      # round-trip cost per dollar of risk (v7 sizing)
        self.s = m * self.M["sig"]                       # stop distance as a fraction of the price (margin check)
        self.futures = instr == "MNQ_fut"
        self.min_l = 0.0
        # smallest win as a share of the risk: the take-profit sits at least WMIN_SD hourly sd from the entry
        self.wmin_frac = max(0.0, WMIN_SD / m - self.rho)
        # engine day boundaries (clock = 0 mod 24) fall at 22:00 UTC, the futures/CFD daily reset
        self.base = 24 * rng.randrange(self.M["T"] // 48) + (22 - self.M["h0"]) % 24
        self.trades = 0; self.st = Stats(); self.last_entry = None; self.last_exit = None; self.last_info = None
        self.news = None                       # the current stage's news rule (set by acct_mc): None, "all" or "cpi"

    @property
    def nb(self):
        return news_bars(self.M, self.news)

    def _idx(self, clock):
        return (self.base + int(clock)) % self.M["T"]

    def utc(self, clock):
        """the UTC date and time of the clock on the path's calendar"""
        return EPOCH + _dt.timedelta(hours=self._idx(clock) + (clock - math.floor(clock)))

    def lmin_at(self, clock, flat_weekend=False):
        """the risk of the smallest position (0.01 lot, one micro contract) at the bar where the next trade would open"""
        i, _ = entry_index(self.M, self._idx(next_bar(clock)), flat_weekend, self.flat_daily, nb=self.nb)
        return min_risk(self.M, self.M["O"][i], self.s)

    def plan_at(self, clock, l, w, opts=None, flat_weekend=False):
        """the position the next trade would place (plan): its rounded volume, its loss at the stop and its win at the
        take-profit, at the next entry's open price"""
        i, _ = entry_index(self.M, self._idx(next_bar(clock)), flat_weekend, self.flat_daily, nb=self.nb)
        o = dict(opts or {})
        if "keep_w" not in o: o["keep_w"] = l > 0 and w < self.k * l * (1 - 1e-9)
        return plan(self.M, i, l, w, self.s, self.cost, o)

    def bdays(self, clock, n):
        return add_bdays(self.M, self._idx, clock, n)

    def next_entry(self, clock, flat_weekend=False):
        """the time the next trade would open (as trade() computes it): the open of the first permitted bar that has not
        started before the clock"""
        c0 = next_bar(clock)
        _, waited = entry_index(self.M, self._idx(c0), flat_weekend, self.flat_daily, nb=self.nb)
        return float(c0 + waited)

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

    def trade(self, l, w, clock=None, flat_weekend=False, opts=None):
        """opens the plan's next position at the next allowed entry and resolves it (resolve); returns (pnl, hours from the
        clock until the next entry may be considered). last_entry, last_exit (clock) and last_info describe the trade.
        A position opens at a bar's open, so never at a bar that started before the clock (version 9: version 8 opened
        it at the open of the bar containing the clock, up to an hour earlier)"""
        c0 = next_bar(clock); nb = self.nb
        i, waited = entry_index(self.M, self._idx(c0), flat_weekend, self.flat_daily, nb=nb)
        d = self._direction(i)
        o = dict(opts or {})
        if "keep_w" not in o: o["keep_w"] = l > 0 and w < self.k * l * (1 - 1e-9)
        pnl, hours, info = resolve(self.M, i, d, l, w, self.s, self.cost, flat_weekend, self.flat_daily, self.rng,
                                   st=self.st, opts=o, nb=nb)
        te = float(c0 + waited)                           # the bar's open, when the position is opened
        self.last_entry = te; self.last_exit = te + info["exit"]; self.last_info = info
        if info["why"] != "unaffordable": self.trades += 1
        return pnl, (te - clock) + float(hours)

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
                        t_eval=(clock - t_start) / A.DAY, paid=0.0, t_fund=0.0, trades=tr.trades, st=tr.st.as_dict(),
                        credit=credits)
        passed += 1
    if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * A.DAY)))
    fees += firm.get("activation", 0)
    t_eval = (clock - t_start) / A.DAY
    paid, clock2, tfirst, npay = A.run_funded(firm["funded"], tr, rng, firm, clock, X1, X)
    return dict(v=paid - fees + credits, days=(clock2 - t_start) / A.DAY,
                t1=(tfirst - t_start) / A.DAY if tfirst else None, npay=npay, passed=passed,
                t_eval=t_eval, paid=paid, t_fund=(clock2 - clock) / A.DAY, trades=tr.trades, fees=fees,
                st=tr.st.as_dict(), credit=credits)

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
