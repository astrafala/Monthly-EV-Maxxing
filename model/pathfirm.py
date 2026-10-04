"""
Firm-rule engine (acct_mc) driven by actual price paths instead of random draws.

PathTrader.trade(l, w, clock): waits for the next allowed entry hour, opens a random-direction
bracket (stop = m x hourly sigma, target = stop x (w + cost)/l, so a win nets w) at that bar's open, walks the bars until the
stop or target is hit (gaps fill at the open, ties inside a bar go target-first with probability
l/(l+w)), charges spread/commission and overnight financing, and returns (pnl, hours elapsed).
With flat_weekend=True (funded accounts that forbid weekend holding) nothing opens after
Friday 19:00 UTC and an open position is closed at the Friday 20:00 UTC bar's close.
Price data: synthetic zero-edge random walk with the instrument's real hourly volatility
(data="synth") or the real hourly series (data="real").
"""
import json, math, random, sys
import numpy as np
import acct_mc as A
import multi

_DATA = {}

def synth_name(data, with_sub=False):
    """synth = seed 11, 12 years; synthN = seed N; synthNyY = Y years; ...sS = S sub-steps per hour (default 12)"""
    body = data[5:]; sub = 12
    if "s" in body: body, sb = body.split("s"); sub = int(sb)
    sd, yrs = 11, 12.0
    if body:
        if "y" in body: a, b = body.split("y"); sd, yrs = int(a), float(b)
        else: sd = int(body)
    return (sd, yrs, sub) if with_sub else (sd, yrs)

def sibling(data, off):
    """an independent synthetic path for a second market of the same life (same length, seed + off)"""
    sd, yrs, sub = synth_name(data, True)
    return f"synth{sd + off}" + (f"y{yrs:g}" if yrs != 12 else "") + (f"s{sub}" if sub != 12 else "")

def evict(data):
    for key in [k for k in _DATA if k[1] == data]: del _DATA[key]

def _store(key, idx, d):
    wd = idx.weekday.values; hr = idx.hour.values
    _DATA[key] = dict(O=d["O"].tolist(), H=d["H"].tolist(), L=d["L"].tolist(), C=d["C"].tolist(),
                      ok=d["ok"].tolist(), entry=d["entry"].tolist(), roll=d["roll"].tolist(),
                      sig=d["sig"], cost=d["cost"], fin=d["fin"],
                      fri_late=((wd == 4) & (hr >= 19)).tolist(), fri_close=((wd == 4) & (hr == 20)).tolist(),
                      T=len(idx), h0=int(hr[0]), hour=hr.tolist())
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
    f.update(sH=u["sH"], sL=u["sL"], sub=u["sub"])
    _store(("MNQ_fut", data), idx, f)

def market(instr, data):
    key = (instr, data)
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
                          T=len(idx), h0=int(hr[0]), hour=hr.tolist())
        if "sH" in d: _DATA[key].update(sH=d["sH"], sL=d["sL"], sub=d["sub"])
    return _DATA[key]

def first_touch(M, i, d, sl, tp, p_fair, rng):
    """stop and target both inside hourly bar i: replay the bar's sub-steps in time order (synthetic paths);
    only if both fall inside the same sub-step, or no sub-steps exist (real data), use the fair chance p_fair"""
    sH = M.get("sH")
    if sH is not None:
        sL = M["sL"]; n = M["sub"]; b = i * n
        for j in range(b, b + n):
            h = float(sH[j]); lo = float(sL[j])
            if d > 0: hs = lo <= sl; ht = h >= tp
            else:     hs = h >= sl; ht = lo <= tp
            if hs and ht: break
            if ht: return True
            if hs: return False
    return rng.random() < p_fair

class PathTrader:
    def __init__(self, instr, data, m, L, k, rng, cost_mult=1.0, dir_rule="random", flat_daily=None):
        self.M = market(instr, data); self.m = m; self.L = L; self.k = k; self.rng = rng
        self.dir_rule = dir_rule
        self.flat_daily = flat_daily          # e.g. 20: no entry at or after 19:00 UTC, close at the 20:00 UTC open
        self.cost = self.M["cost"] * cost_mult
        self.rho = self.cost / (m * self.M["sig"])      # round-trip cost per dollar of risk (v7 sizing)
        self.s = m * self.M["sig"]                       # stop distance as a fraction of the price (margin check)
        # v7: whole micro contracts. Synthetic paths are normalised to start at 100, so one contract's notional is fixed at
        # $2 per point x 31,070 points (the reference Nasdaq level of 2 Oct 2026): one contract loses 62,140 x s at the stop.
        self.contract = 2.0 * 31070.0 if instr == "MNQ_fut" else None
        self.min_l = self.contract * m * self.M["sig"] if self.contract else 0.0
        # engine day boundaries (clock = 0 mod 24) fall at 22:00 UTC, the futures/CFD daily reset
        self.base = 24 * rng.randrange(self.M["T"] // 48) + (22 - self.M["h0"]) % 24
        self.trades = 0

    def _idx(self, clock):
        return (self.base + int(clock)) % self.M["T"]

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
        M = self.M; T = M["T"]; i = self._idx(clock); waited = 0
        fd_h = self.flat_daily
        while (not M["entry"][i] or (flat_weekend and M["fri_late"][i])
               or (fd_h is not None and M["hour"][i] >= fd_h - 1)):
            i = (i + 1) % T; waited += 1
        d = self._direction(i)
        s = self.m * M["sig"]; e = M["O"][i]
        if self.contract:                               # whole contracts: risk rounded down to a multiple of one contract's stop
            per = self.contract * s                     # dollars lost by one contract at the stop
            n = max(1, math.floor(l / per + 1e-9))      # the rule engine never asks for less than one contract (min_l)
            f = n * per / l; l = l * f; w = w * f
        notional = l / s
        fee = self.cost * notional                     # target placed so that a win nets w after costs
        wg = w + fee
        sl = e * (1 - d * s); tp = e * (1 + d * s * wg / l)
        rolls = 0; bars = 0; first = True; exit_px = None; last = e
        while True:
            if M["ok"][i]:
                o = M["O"][i]
                if not first:
                    if M["roll"][i]: rolls += 1
                    if d * (o - sl) <= 0 or d * (o - tp) >= 0:
                        exit_px = o; break
                    if fd_h is not None and M["hour"][i] == fd_h:
                        exit_px = o; break                 # daily flat time (futures firms: no overnight positions)
                if d > 0: hs = M["L"][i] <= sl; ht = M["H"][i] >= tp
                else:     hs = M["H"][i] >= sl; ht = M["L"][i] <= tp
                if hs or ht:
                    won = ht if not (hs and ht) else first_touch(M, i, d, sl, tp, l / (l + wg), self.rng)
                    exit_px = tp if won else sl; break
                last = M["C"][i]
                if flat_weekend and M["fri_close"][i]:
                    exit_px = last; break
            first = False; bars += 1; i += 1
            if i >= T:                               # end of data: close at the last close, wrap
                exit_px = last; i = 0; break
        self.trades += 1
        pnl = notional * d * (exit_px - e) / e - fee - M["fin"] * notional * rolls
        return pnl, float(waited + bars + 1)

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
                        t_eval=(clock - t_start) / A.DAY, paid=0.0, t_fund=0.0, trades=tr.trades)
        passed += 1
    if firm["monthly"]: fees = firm["fee"] * max(1, math.ceil((clock - t_start) / (30 * A.DAY)))
    fees += firm.get("activation", 0)
    t_eval = (clock - t_start) / A.DAY
    paid, clock2, tfirst, npay = A.run_funded(firm["funded"], tr, rng, firm, clock, X1, X)
    return dict(v=paid - fees + credits, days=(clock2 - t_start) / A.DAY,
                t1=(tfirst - t_start) / A.DAY if tfirst else None, npay=npay, passed=passed,
                t_eval=t_eval, paid=paid, t_fund=(clock2 - clock) / A.DAY, trades=tr.trades, fees=fees)

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
