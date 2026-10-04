"""
Zero-edge prop-firm valuation engine.

Model: the trader controls a martingale (zero drift before costs). Each trading day
the trader may place one two-point bet (+w, -l): a bracket order with take-profit w and
stop-loss l (in $). With a driftless mid-price, P(win) = l / (w + l). Costs are a drift:
a bet with outcomes (+w,-l) costs kappa * sqrt(w*l) on average, which we model by
lowering the win probability to (l - c)/(w + l), so the expected P&L of the bet is -c.

Why sqrt(w*l): to resolve within a day, stop s and target t (price units) must satisfy
s*t ~ sigma_day^2. Position size N gives w = N t, l = N s, and the round-trip cost is
proportional to N, i.e. ~ sqrt(w*l)/sigma_day. kappa = cost / risk of a 1:1 bet whose
stop equals one daily sigma (EURUSD ~ 0.6-0.8 pip on a ~60 pip day => ~1-1.3%).
"""
import math
from functools import lru_cache
import numpy as np


# ---------------------------------------------------------------- evaluation phases
def eval_pass_prob(A, D, trailing=False, dll=None, daily_cap=None, kappa=0.0,
                   g=None, lock_floor=None, max_loss_bet=None, max_win_bet=None,
                   tol=1e-11, max_sweeps=4000):
    """
    Max probability of reaching +A before the floor, starting from 0.
      static floor   : floor = -D
      EOD trailing   : floor = min(H - D, lock_floor), H = highest end-of-day balance (>=0)
    dll        : daily loss limit (max l per day)
    daily_cap  : max profit per day (approximates a best-day consistency rule)
    max_*_bet  : optional caps to model 'risk per trade' rules
    Returns (P(pass), expected number of trading days under the optimal policy).
    """
    if g is None:
        g = D / 40.0
    a = int(round(A / g)); d = int(round(D / g))
    dl = int(round(dll / g)) if dll else 10**9
    cap = int(round(daily_cap / g)) if daily_cap else 10**9
    if max_loss_bet: dl = min(dl, int(round(max_loss_bet / g)))
    if max_win_bet: cap = min(cap, int(round(max_win_bet / g)))
    lockf = int(round(lock_floor / g)) if lock_floor is not None else 10**9
    k = kappa  # cost per sqrt(w l) in grid units is k*sqrt(w*l)

    if not trailing:
        # state x in (-d, a); value array index x+d
        V = np.zeros(a + d + 1); V[a + d] = 1.0
        T = np.zeros(a + d + 1)
        for _ in range(max_sweeps):
            delta = 0.0
            for x in range(a - 1, -d, -1):
                ls = np.arange(1, min(dl, x + d) + 1)
                ws = np.arange(1, min(cap, a - x) + 1)
                L, W = np.meshgrid(ls, ws, indexing="ij")
                c = k * np.sqrt(W * L)
                p = (L - c) / (W + L)
                p = np.clip(p, 0, 1)
                val = p * V[x + W + d] + (1 - p) * V[x - L + d]
                i = np.unravel_index(np.argmax(val), val.shape)
                best = val[i]
                pw = p[i]
                tnew = 1 + pw * T[x + W[i] + d] + (1 - pw) * T[x - L[i] + d]
                delta = max(delta, abs(best - V[x + d]))
                V[x + d] = best; T[x + d] = tnew
            if delta < tol:
                break
        return V[d], T[d]

    # EOD trailing: state (x, H), floor f(H) = min(H - d, lockf)
    def floor(H):
        return min(H - d, lockf)
    # H ranges 0..a-1 ; x ranges floor(H)+1 .. min(H, a-1)? x can exceed H only
    # within a day; end-of-day x>H sets H=x. So stored states satisfy x<=H.
    V = {}
    T = {}
    states = []
    for H in range(0, a):
        for x in range(floor(H) + 1, H + 1):
            states.append((x, H)); V[(x, H)] = 0.0; T[(x, H)] = 0.0

    def val_of(x, H):
        if x >= a:
            return 1.0, 0.0
        if x <= floor(H):
            return 0.0, 0.0
        return V[(x, H)], T[(x, H)]

    states.sort(key=lambda s: (-s[1], -s[0]))
    for _ in range(max_sweeps):
        delta = 0.0
        for (x, H) in states:
            f = floor(H)
            best = -1; bt = 0
            lmax = min(dl, x - f)
            wmax = min(cap, a - x)
            for l in range(1, lmax + 1):
                vl, tl = val_of(x - l, H)
                for w in range(1, wmax + 1):
                    c = k * math.sqrt(w * l)
                    p = (l - c) / (w + l)
                    if p <= 0:
                        continue
                    xn = x + w
                    Hn = max(H, xn)
                    vw, tw = val_of(xn, Hn)
                    v = p * vw + (1 - p) * vl
                    if v > best + 1e-15:
                        best = v; bt = 1 + p * tw + (1 - p) * tl
            delta = max(delta, abs(best - V[(x, H)]))
            V[(x, H)] = best; T[(x, H)] = bt
        if delta < tol:
            break
    return V[(0, 0)], T[(0, 0)]


def intraday_trailing_pass_prob(A, D, kappa=0.0):
    """Continuous-path bound: max over all strategies of P(reach A before a drawdown of D
    from the running equity peak). For driftless BM the peak at the drawdown time is
    Exp(mean D) => exp(-A/D) regardless of sizing (Dambis-Dubins-Schwarz). Costs act as
    a negative drift; with bet scale ~D/2 this inflates the exponent by ~(1+2 kappa)."""
    return math.exp(-(A / D) * (1 + 2 * kappa))


# ---------------------------------------------------------------- funded stage
def funded_value_static(D, split, kappa, refund=0.0, refund_after=1, first_payout=None):
    """Static floor D below the payout-reset balance.
    Identity: E[sum of gross withdrawals] = E[initial - final balance] + E[trading P&L]
    -> with zero drift and running to bust: = D - E[costs]. Bold play (bets of size ~D,
    payout target h=D) minimises costs at ~2*kappa*D.
    Refund: paid with the n-th payout; small payouts h make it likely: q ~ D/(D+n h)."""
    h = first_payout if first_payout else 0.005 * 100_000 * D / 10_000  # 0.5% of a 100k
    q = D / (D + refund_after * h)
    return split * D * (1 - 2 * kappa) + refund * q, q


def funded_value_trail_lock(D, split, kappa, c=100.0, total_cap=None, b_max_mult=5.0,
                            intraday=False):
    """Futures-style funded account: EOD (or intraday) trailing floor D that stops
    trailing ('locks') at initial + c. After the lock the account is static with floor c,
    worth (balance - c) to a zero-edge trader, but extraction is limited by total_cap.
    EOD: bold play to level b in one day: P = D/(b+D); value = D*min(b-c, cap)/(b+D).
    Intraday (continuous paths): P(reach D+c before drawdown D) = exp(-(D+c)/D)."""
    if intraday:
        p_lock = math.exp(-((D + c) / D) * (1 + 2 * kappa))
        body = D  # balance at lock = D + c -> worth D
        if total_cap is not None:
            body = min(body, total_cap)
        return split * p_lock * body * (1 - 2 * kappa)
    best = 0.0
    cap = total_cap if total_cap is not None else float("inf")
    b_hi = min(cap + c, b_max_mult * D + c)
    for b in np.linspace(D + c, max(D + c, b_hi), 400):
        v = D * min(b - c, cap) / (b + D)
        best = max(best, v)
    # costs: one bold bet ~ kappa*sqrt(b*D) + post-lock extraction ~2 kappa per $ of floor
    return split * best * (1 - 2 * kappa)


def ev_attempt(fee, phases, funded_value, activation=0.0):
    """phases: list of pass probabilities. EV per attempt (fee paid once)."""
    p = 1.0
    for q in phases:
        p *= q
    return -fee + p * (funded_value - activation), p
