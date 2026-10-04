"""
Rule-compliant execution test on real EURUSD hourly data (FTMO 100K 2-Step).
Risk per trade capped at 1% of initial balance ($1,000). One trade per FTMO day.
Stop/target in pips follow s*t = SIG^2 (resolves within ~a day); near the target the
take-profit is set to the exact remaining distance; near the floor risk = room left - $100.
Tracks elapsed market hours so we can report timelines.
"""
import sys, math, random
import numpy as np
import sim_real as S

SIG = 55.0
COST = S.COST_PIPS
B = 10_000.0
FEE = 632.0

class Clock:
    def __init__(self, i): self.i = i; self.hours = 0
    def advance_to(self, j):
        if j >= self.i: self.hours += j - self.i
        else: self.hours += (S.N - self.i) + j   # wrapped around the data
        self.i = j

def trade(clock, w, l, rng):
    """place one bracket at the next day's random hour; returns pnl"""
    i = S.next_entry(clock.i, rng)
    if i is None: i = S.next_entry(0, rng)
    clock.advance_to(i)
    s = SIG * math.sqrt(l / w); t = SIG * math.sqrt(w / l)
    vpp = l / s
    d = 1 if rng.random() < 0.5 else -1
    won, j = S.bracket(i, d, s, t, rng)
    if won is None:
        clock.advance_to(0); return trade(clock, w, l, rng)
    clock.advance_to(min(j, S.N - 2))
    return (w if won else -l) - COST * vpp

def sizing(x, target, rr, risk_cap=1000.0, buffer=100.0):
    room = x + B - buffer
    l = min(risk_cap, room)
    if l < 25: l = max(x + B - 1.0, 1.0)          # last few dollars: risk what is left
    w = rr * l
    if target is not None: w = min(w, target - x)  # never overshoot the target
    return max(w, 10.0), l

def phase(A, clock, rng, rr, min_days=4):
    x = 0.0; n = 0
    while True:
        if x >= A and n >= min_days: return True, n
        if x <= -B + 1e-6: return False, n
        if x >= A:   # padding day: micro trade
            n += 1; clock.advance_to(S.next_entry(clock.i, rng) or S.next_entry(0, rng)); continue
        w, l = sizing(x, A, rr)
        x += trade(clock, w, l, rng); n += 1
        x = max(x, -B)

def funded(clock, rng, rr, cycle_days=14, first_target=500.0, horizon_trades=4000):
    x = 0.0; paid = 0.0; first = True; n = 0; npay = 0
    while x > -B + 1e-6 and n < horizon_trades:
        n += 1
        if n % cycle_days == 0 and x > 0:
            paid += 0.8 * x + (FEE if first else 0.0); first = False; x = 0.0; npay += 1
        if first and x >= first_target:          # first payout secured: wait for payout day
            clock.advance_to(S.next_entry(clock.i, rng) or S.next_entry(0, rng)); continue
        w, l = sizing(x, first_target if first else None, rr)
        x += trade(clock, w, l, rng)
        x = max(x, -B)
    return paid, n, npay

def attempt(rng, rr):
    i0 = S.ENTRY_OK[rng.randrange(len(S.ENTRY_OK) // 2)]
    c = Clock(i0)
    ok, n1 = phase(10_000, c, rng, rr)
    h1 = c.hours
    if not ok: return dict(ev=-FEE, stage=0, n=n1, weeks=c.hours / 120, w1=h1 / 120)
    ok, n2 = phase(5_000, c, rng, rr)
    if not ok: return dict(ev=-FEE, stage=1, n=n1 + n2, weeks=c.hours / 120, w1=h1 / 120)
    hf0 = c.hours
    paid, n3, npay = funded(c, rng, rr)
    return dict(ev=-FEE + paid, stage=2, n=n1 + n2 + n3, weeks=c.hours / 120, w1=h1 / 120,
                wf=(c.hours - hf0) / 120, npay=npay, paid=paid)

if __name__ == "__main__":
    M = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    rng = random.Random(4242)
    out = {}
    for rr in (1.0, 2.0):
        res = [attempt(rng, rr) for _ in range(M)]
        ev = np.array([r["ev"] for r in res]); st = np.array([r["stage"] for r in res])
        wk = np.array([r["weeks"] for r in res])
        fund = [r for r in res if r["stage"] == 2]
        se = ev.std() / math.sqrt(M)
        rows = []
        bs = np.random.default_rng(1)
        for n in (1, 3, 5, 10, 20, 50):
            s = bs.choice(ev, size=(20000, n)).sum(1); rows.append((n, float(np.mean(s > 0))))
        summ = dict(EV=float(ev.mean()), CI=float(1.96 * se), P1=float(np.mean(st >= 1)),
                    P2=float(np.mean(st[st >= 1] >= 2)), Pf=float(np.mean(st >= 2)),
                    Pprofit=float(np.mean(ev > 0)), weeks_mean=float(wk.mean()),
                    weeks_med=float(np.median(wk)),
                    weeks_fail_p1=float(np.mean([r["weeks"] for r in res if r["stage"] == 0])),
                    weeks_p1=float(np.mean([r["w1"] for r in res if r["stage"] >= 1])),
                    weeks_funded=float(np.mean([r["wf"] for r in fund])),
                    paid_funded=float(np.mean([r["paid"] for r in fund])),
                    npay=float(np.mean([r["npay"] for r in fund])),
                    p_nopay=float(np.mean([r["npay"] == 0 for r in fund])),
                    trades=float(np.mean([r["n"] for r in res])), ahead=rows)
        out[f"rr{rr:g}"] = summ
        print(f"RR 1:{rr:g}", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in summ.items()}, flush=True)
    import json; json.dump(out, open("compliant.json", "w"), indent=1)
