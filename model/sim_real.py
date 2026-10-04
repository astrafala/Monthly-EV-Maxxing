"""
Real-data check: zero-edge (random direction) trading of an FTMO 100K 2-Step attempt on
actual EURUSD hourly bars (Dec 2023 - Oct 2026), with spread/commission/slippage.

Bracket resolution on hourly bars: if a bar touches both stop and target we cannot know
which came first -> coin flip (unbiased). Entry at a random hour's open between
07:00-16:00 UTC on weekdays.
"""
import sys, math, random
import numpy as np, pandas as pd

d = pd.read_csv("eurusd_1h.csv", header=[0, 1], index_col=0)
d.columns = [c[0] for c in d.columns]
d.index = pd.to_datetime(d.index, utc=True)
O = d["Open"].values; H = d["High"].values; L = d["Low"].values; C = d["Close"].values
T = d.index
DAY = (T.tz_convert("Europe/Prague").normalize()).values  # FTMO day = CE(S)T midnight
day_id = pd.factorize(DAY)[0]
hour = T.hour.values; wd = T.weekday.values
ENTRY_OK = np.where((hour >= 7) & (hour <= 16) & (wd < 5))[0]
N = len(O)
PIP = 1e-4
SIGMA_PIPS = 55.0           # ~ EURUSD daily sigma 2024-26
COST_PIPS = 0.75            # 0.15 raw spread + 0.5 commission ($5/lot rt) + 0.1 slippage

def bracket(i0, direction, stop_p, tgt_p, rng):
    """Return (won, exit_index). Prices in pips relative to entry at O[i0]."""
    e = O[i0]
    if direction > 0:
        sl = e - stop_p * PIP; tp = e + tgt_p * PIP
        for i in range(i0, N):
            hs = L[i] <= sl; ht = H[i] >= tp
            if hs and ht: return (rng.random() < 0.5), i
            if hs: return False, i
            if ht: return True, i
    else:
        sl = e + stop_p * PIP; tp = e - tgt_p * PIP
        for i in range(i0, N):
            hs = H[i] >= sl; ht = L[i] <= tp
            if hs and ht: return (rng.random() < 0.5), i
            if hs: return False, i
            if ht: return True, i
    return None, N

def next_entry(i, rng, skip_day=True):
    """first allowed entry bar on a later FTMO day than bar i, with a random hour"""
    if i >= N - 1: return None
    di = day_id[i]
    j = np.searchsorted(ENTRY_OK, i + 1)
    while j < len(ENTRY_OK) and skip_day and day_id[ENTRY_OK[j]] == di:
        j += 1
    if j >= len(ENTRY_OK): return None
    # choose a random allowed hour within that day
    dj = day_id[ENTRY_OK[j]]
    k = j
    cands = []
    while k < len(ENTRY_OK) and day_id[ENTRY_OK[k]] == dj:
        cands.append(ENTRY_OK[k]); k += 1
    return cands[rng.randrange(len(cands))]

def place(w, l, i, rng):
    """Bet that wins w or loses l (dollars). Stop/target in pips with s*t ~ sigma^2."""
    s = SIGMA_PIPS * math.sqrt(l / w); t = SIGMA_PIPS * math.sqrt(w / l)
    lots_value = l / s  # $ per pip
    cost = COST_PIPS * lots_value
    dirn = 1 if rng.random() < 0.5 else -1
    won, j = bracket(i, dirn, s + 0.0, t + 0.0, rng)
    if won is None: return None, j
    # spread/commission/slippage paid on every trade
    pnl = (w if won else -l) - cost
    return pnl, j

def phase(A, B, dll, i, rng, policy, min_days=4):
    """Returns (passed, end_index, n_trades). x = profit; floor = -B."""
    x = 0.0; days = 0; n = 0
    while True:
        if x >= A and days >= min_days: return True, i, n
        if x <= -B + 1e-9: return False, i, n
        if i >= N - 1: i = 0
        i = next_entry(i, rng)
        if i is None: i = next_entry(0, rng)
        if x >= A:            # padding day: negligible micro trade
            days += 1; continue
        w, l = policy(x, A, B, dll)
        pnl, j = place(w, l, i, rng)
        if pnl is None:
            i = 0; continue
        n += 1; days += 1
        x += pnl
        if x < -B: x = -B
        i = j if j < N - 1 else 0

def bold(x, A, B, dll):
    l = min(dll, x + B) * 0.97          # 3% buffer for cost/slippage vs hard limit
    w = A - x + 50                       # aim at the target
    return max(w, 100.0), max(l, 50.0)

def compliant(x, A, B, dll):
    l = min(1000.0, (x + B) * 0.97)      # 1% risk per trade
    return 1000.0 * min(1.0, l / 1000.0), max(l, 50.0)   # 1:1

def funded(i, rng, policy_name, B=10_000.0, dll=5000.0, split=0.8, refund=632.0,
           cycle_days=14, max_days=3000):
    """Run to bust. Payout every `cycle_days` FTMO days if profit > 0 (withdraw all).
    Returns total paid to trader."""
    x = 0.0; paid = 0.0; first = True; day_count = 0; n = 0
    h = 500.0 if policy_name == "bold" else 1000.0
    while True:
        if x <= -B + 1e-9: return paid, n
        i2 = next_entry(i, rng)
        if i2 is None:  # wrap around the data (bootstrap)
            i2 = next_entry(0, rng)
        day_count += 1
        if day_count % cycle_days == 0 and x > 0:
            paid += split * x + (refund if first else 0.0); first = False; x = 0.0
            h = 5000.0 if policy_name == "bold" else 1000.0
        if day_count > max_days: return paid, n
        if policy_name == "bold":
            if x >= h:  # sit flat until payout day
                i = i2; continue
            l = min(dll, x + B) * 0.97
            w = max(h - x, 100.0)
        else:
            l = min(1000.0, (x + B) * 0.97); w = l
        pnl, j = place(w, max(l, 50.0), i2, rng)
        if pnl is None:
            i = 0; continue
        n += 1
        x += pnl
        if x < -B: x = -B
        i = j if j < N - 1 else 0

def attempt(rng, pol):
    fee = 632.0
    i = ENTRY_OK[rng.randrange(len(ENTRY_OK) // 2)]   # start in first half of the data
    policy = bold if pol == "bold" else compliant
    ok, i, n1 = phase(10_000, 10_000, 5000, i, rng, policy)
    if not ok: return -fee, 0, n1
    ok, i, n2 = phase(5_000, 10_000, 5000, i, rng, policy)
    if not ok: return -fee, 1, n1 + n2
    paid, n3 = funded(i, rng, pol)
    return -fee + paid, 2, n1 + n2 + n3

def win_rate_test(rng, n=20000, stop=50, tgt=50):
    w = 0; tot = 0
    for _ in range(n):
        i = ENTRY_OK[rng.randrange(len(ENTRY_OK) - 200)]
        dirn = 1 if rng.random() < 0.5 else -1
        won, j = bracket(i, dirn, stop, tgt, rng)
        if won is None: continue
        w += won; tot += 1
    return w / tot, tot

if __name__ == "__main__":
    rng = random.Random(7)
    for s in (25, 50, 100):
        wr, tot = win_rate_test(rng, 20000, s, s)
        se = math.sqrt(wr * (1 - wr) / tot)
        print(f"random-direction {s}/{s} pip bracket win rate (mid, before costs): "
              f"{wr:.4f} +- {1.96*se:.4f}  (n={tot})", flush=True)
    for pol in ("bold", "compliant"):
        M = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
        res = [attempt(rng, pol) for _ in range(M)]
        ev = np.array([r[0] for r in res]); st = np.array([r[1] for r in res])
        se = ev.std() / math.sqrt(M)
        print(f"{pol:9s}: EV/attempt = {ev.mean():8.1f} +- {1.96*se:6.1f} | "
              f"P(pass1)={np.mean(st>=1):.3f} P(funded)={np.mean(st>=2):.3f} "
              f"P(profit)={np.mean(ev>0):.3f} median={np.median(ev):.0f} "
              f"trades/attempt={np.mean([r[2] for r in res]):.1f}", flush=True)
        np.save(f"ev_{pol}.npy", ev)


# ------------------------------------------------------------------ the PDF's protocol
def bracket_ts(i0, direction, stop_p, tgt_p, rng, close_hour=20):
    """bracket with a same-day time stop at close_hour UTC (PDF: flatten before NY close).
    returns pips gained (signed), exit index"""
    e = O[i0]; d0 = day_id[i0]
    for i in range(i0, N):
        if direction > 0:
            hs = L[i] <= e - stop_p * PIP; ht = H[i] >= e + tgt_p * PIP
        else:
            hs = H[i] >= e + stop_p * PIP; ht = L[i] <= e - tgt_p * PIP
        if hs and ht: return (tgt_p if rng.random() < 0.5 else -stop_p), i
        if hs: return -stop_p, i
        if ht: return tgt_p, i
        if hour[i] >= close_hour or day_id[i] != d0:
            return direction * (C[i] - e) / PIP, i
    return None, N

def pdf_attempt(rng, fee=632.0):
    i = ENTRY_OK[rng.randrange(len(ENTRY_OK) // 2)]
    def step(x, B, rr):
        risk = min(4800.0, x + B - 200.0)
        return risk
    def run_phase(A, quit_rule):
        nonlocal i
        x = 0.0; days = 0; consec = 0
        while True:
            if x >= A and days >= 4: return True
            if x <= -10_000: return False
            i = next_entry(i, rng) or next_entry(0, rng)
            if x >= A: days += 1; continue
            risk = step(x, 10_000, 1)
            if risk < 300 and quit_rule: return False      # PDF: abandon
            if risk <= 0: return False
            dirn = 1 if rng.random() < 0.5 else -1
            pips, j = bracket_ts(i, dirn, 50, 50, rng)
            if pips is None: i = 0; continue
            v = risk / 50.0
            x += v * pips - COST_PIPS * v
            days += 1
            if pips < 0 and risk >= 4000: consec += 1
            elif pips > 0: consec = 0
            if quit_rule and consec >= 2: return False     # PDF: quit after 2 full losses
            i = j if j < N - 1 else 0
    if not run_phase(10_000, True): return -fee, 0
    if not run_phase(5_000, False): return -fee, 1
    # funded: 1:2 RR, withdraw every 14 days, run to bust
    x = 0.0; paid = 0.0; first = True; dc = 0
    while x > -10_000 + 1e-9 and dc < 3000:
        i = next_entry(i, rng) or next_entry(0, rng)
        dc += 1
        if dc % 14 == 0 and x > 0:
            paid += 0.8 * x + (fee if first else 0); first = False; x = 0.0
        risk = min(4800.0, x + 10_000 - 200.0)
        if risk < 50: break
        dirn = 1 if rng.random() < 0.5 else -1
        pips, j = bracket_ts(i, dirn, 50, 100, rng)
        if pips is None: i = 0; continue
        v = risk / 50.0
        x += v * pips - COST_PIPS * v
        i = j if j < N - 1 else 0
    return -fee + paid, 2

if __name__ == "__main__" and len(sys.argv) > 2:
    M = int(sys.argv[2])
    res = [pdf_attempt(rng) for _ in range(M)]
    ev = np.array([r[0] for r in res]); st = np.array([r[1] for r in res])
    print(f"PDF protocol: EV/attempt = {ev.mean():8.1f} +- {1.96*ev.std()/math.sqrt(M):6.1f} | "
          f"P(pass1)={np.mean(st>=1):.3f} P(funded)={np.mean(st>=2):.3f} P(profit)={np.mean(ev>0):.3f}")
    np.save("ev_pdf.npy", ev)
