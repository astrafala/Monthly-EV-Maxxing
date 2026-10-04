"""Independent check: pure coin-flip FTMO 100K 2-Step, no market data, written from scratch."""
import random, math, statistics as st

FEE, SPLIT, B, DLL = 632.0, 0.80, 10_000.0, 5_000.0

def phase_bold(A, kappa, rng):
    x = 0.0
    while True:
        if x >= A - 1e-9: return True
        if x <= -B + 1e-9: return False
        l = min(DLL, x + B)            # can never risk more than the room left above the floor
        w = A - x                      # aim exactly at the target
        c = kappa * math.sqrt(w * l)   # cost of this bracket
        p = (l - c) / (w + l)          # fair coin minus cost: E[trade] = -c
        x += (w if rng.random() < p else -l)

def phase_fixed(A, risk, rr, kappa, rng):
    """naive: fixed risk per trade, fixed RR, capped by room above the floor"""
    x = 0.0
    while True:
        if x >= A - 1e-9: return True
        if x <= -B + 1e-9: return False
        l = min(risk, x + B); w = rr * l
        c = kappa * math.sqrt(w * l)
        x += (w if rng.random() < (l - c) / (w + l) else -l)

def funded(policy, kappa, rng, cycle=14):
    """run to bust; every `cycle` trading days withdraw all profit; refund with 1st payout"""
    x = 0.0; paid = 0.0; first = True; day = 0
    while x > -B + 1e-9:
        day += 1
        if day % cycle == 0 and x > 0:
            paid += SPLIT * x + (FEE if first else 0); first = False; x = 0.0
        if policy == "bold":
            h = 500.0 if first else 5000.0
            if x >= h: continue            # sit flat until payout day
            l = min(DLL, x + B); w = h - x
        elif policy == "1pct_1to1":
            l = min(1000.0, x + B); w = l
        elif policy == "5pct_1to2":
            l = min(DLL, x + B); w = 2 * l
        c = kappa * math.sqrt(w * l)
        x += (w if rng.random() < (l - c) / (w + l) else -l)
    return paid

def attempt(kappa, rng, pol="bold"):
    if pol == "bold":
        ok1 = phase_bold(10_000, kappa, rng); ok2 = ok1 and phase_bold(5_000, kappa, rng)
    else:
        ok1 = phase_fixed(10_000, 1000, 1, kappa, rng); ok2 = ok1 and phase_fixed(5_000, 1000, 1, kappa, rng)
    if not ok2: return -FEE, ok1, False, 0.0
    paid = funded("bold" if pol == "bold" else "1pct_1to1", kappa, rng)
    return -FEE + paid, ok1, True, paid

rng = random.Random(2026)
N = 200_000
for kappa in (0.014,):
    for pol in ("bold", "1pct"):
        n = 100_000 if pol == "bold" else 20_000
        res = [attempt(kappa, rng, pol) for _ in range(n)]
        ev = [r[0] for r in res]
        p1 = sum(r[1] for r in res) / n; pf = sum(r[2] for r in res) / n
        paid_f = [r[3] for r in res if r[2]]
        se = st.pstdev(ev) / math.sqrt(n)
        print(f"kappa={kappa:.3f} {pol:5s}: P1={p1:.4f} Pfunded={pf:.4f} "
              f"E[paid|funded]={st.mean(paid_f):7.0f}  EV={st.mean(ev):7.0f} +- {1.96*se:4.0f}  "
              f"P(attempt profitable)={sum(e>0 for e in ev)/n:.3f}", flush=True)

print("\nfunded stage alone, different trading styles (should all be ~ 0.8*10,000 + refund):")
for pol in ("bold", "1pct_1to1", "5pct_1to2"):
    for kappa in (0.0, 0.014):
        xs = [funded(pol, kappa, rng) for _ in range(20_000)]
        print(f"  {pol:10s} kappa={kappa:.3f}: mean paid = {st.mean(xs):7.0f} +- {1.96*st.pstdev(xs)/math.sqrt(len(xs)):4.0f}   "
              f"P(any payout)={sum(v>0 for v in xs)/len(xs):.3f}", flush=True)
