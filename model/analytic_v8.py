"""
Version 8 closed-form check of the engine: the exact trade-level Markov chain of the version 8 rules.

State: the account's P&L x relative to the start of the phase (or of the payout cycle), floor at -B, target at A.
    room(x)  = (x + B - buf) / (1 + rho)                risk that keeps stop loss + cost a buffer above the floor
    normal   (room(x) >= l_min):  l(x) = min(L, room(x))
    terminal (room(x) <  l_min):  l(x) = max((x + B) / (1 + rho), bs)   the stop sits at the floor: a loss ends the
             attempt at -B exactly (a breach that frees the allocation; version 7 abandoned the attempt above the floor)
    w(x)     = min( max( min(k l, A - x), w_min l, bs ), cap )    w_min = max(0, 0.6 / m - rho): no take-profit closer
             than 0.6 hourly sd (2-minute holding rules); a win may therefore pass A (overshoot); cap = per-trade rule cap
             (no_overshoot: also w <= A - x, and a state with A - x below the smallest allowed win stops and is paid at x)
    c(x)     = rho l(x),   p(x) = l / (l + w + c)       zero-edge bracket: the trade's mean is exactly -c
Solved on a fine grid by value iteration:
    V(x) = P(success),  N(x) = E[trades],  K(x) = E[total cost],  T(x) = E[P&L at the end]
Optional stopping (every trade has mean -c, bounded, and the number of trades has finite mean) gives
    T(0) = P E[X_end | success] + (1 - P) E[X_end | fail] = -K(0)
With the terminal rule every failure ends at -B, so E[X_end | fail] = -B and
    P = (B - K(0)) / (E[X_end | success] + B),
the textbook form with A replaced by the mean balance at success (A plus the mean overshoot).
Daily loss limits, the per-day part of the concentration policy, minimum and profitable days, payout dates, the daily
flat time and weekends are not in the chain; they are in the engine.
"""
import json, math
import numpy as np
import firms_v8 as F7, calibrate as CB

SIG = json.load(open("sigma_v32.json"))
WMIN_SD = 0.6

def rho_of(instr, m, cost_mult=1.0):
    return cost_mult * CB.INSTR[instr][1] / 100.0 / (m * SIG[instr])

def chain(A, B, L, k, rho, cap=None, buf=100.0, lmin=None, bs=1.0, h=None, tol=1e-11, it_max=40000, min_rr=None,
          wmin_frac=0.0, lc=0.0, no_overshoot=False):
    """lc: one futures contract's risk (terminal trades are one contract); wmin_frac: smallest win as a share of risk"""
    lmin = 0.1 * L if lmin is None else lmin
    lo = -B
    h = h or max(0.25, (A - lo) / 8000.0)
    xs = np.arange(lo, A + 1e-9, h)
    if xs[-1] < A - 1e-9: xs = np.append(xs, A)
    room = (xs + B - buf) / (1.0 + rho)
    term = room < lmin                                   # the terminal trade: stop at the floor
    room0 = (xs + B) / (1.0 + rho)
    l = np.where(term, (lc if lc > 0 else np.maximum(room0, 1.0 * bs)), np.minimum(L, np.maximum(room, 0.0)))
    w = np.minimum(k * l, A - xs)
    w = np.maximum(np.maximum(w, wmin_frac * l), 1.0 * bs)
    if cap:
        w = np.minimum(w, cap)
        if wmin_frac > 0:                                 # a cap below the smallest allowed win: the engine lowers the risk
            shrink = (cap < wmin_frac * l - 1e-9) & (cap >= 1.0 * bs) & (cap / wmin_frac >= lc)
            l = np.where(shrink, cap / wmin_frac, l)
    stopped = np.zeros_like(xs, dtype=bool)
    if no_overshoot:
        stopped = (A - xs) < np.maximum(wmin_frac * l, 1.0 * bs) - 1e-9
        w = np.minimum(w, A - xs)
    if min_rr:                                           # minimum reward:risk (Maven): shrink the risk instead
        low = w < min_rr * l
        l = np.where(low, w / min_rr, l)
    c = rho * l
    p = l / np.maximum(l + w + c, 1e-12)
    up = xs + w; dn = np.maximum(xs - l - c, -B)
    won = up >= A - 1e-9
    floor_hit = dn <= -B + 1e-9
    dead = xs <= -B + 1e-9
    top = (xs >= A - 1e-9) | stopped
    live = ~dead & ~top
    V = np.zeros_like(xs); N = np.zeros_like(xs); K = np.zeros_like(xs); T = xs.copy()
    V[top] = 1.0; T[top] = xs[top]
    def at(arr, y): return np.interp(y, xs, arr)
    for _ in range(it_max):
        Vu = np.where(won, 1.0, at(V, up)); Tu = np.where(won, up, at(T, up))      # a win may pass A (overshoot)
        Nu = np.where(won, 0.0, at(N, up)); Ku = np.where(won, 0.0, at(K, up))
        Vd = np.where(floor_hit, 0.0, at(V, dn)); Td = np.where(floor_hit, -B, at(T, dn))
        Nd = np.where(floor_hit, 0.0, at(N, dn)); Kd = np.where(floor_hit, 0.0, at(K, dn))
        Vn = np.where(live, p * Vu + (1 - p) * Vd, V)
        Tn = np.where(live, p * Tu + (1 - p) * Td, T)
        Nn = np.where(live, 1 + p * Nu + (1 - p) * Nd, N)
        Kn = np.where(live, c + p * Ku + (1 - p) * Kd, K)
        d = max(np.abs(Vn - V).max(), np.abs(Tn - T).max() / max(A, 1.0), np.abs(Nn - N).max() * 1e-4,
                np.abs(Kn - K).max() / max(A, 1.0))
        V, T, N, K = Vn, Tn, Nn, Kn
        if d < tol: break
    P0, T0, N0, K0 = (float(at(arr, 0.0)) for arr in (V, T, N, K))
    Xs = (T0 + (1.0 - P0) * B) / max(P0, 1e-12)          # E[P&L at the end | success] (every failure ends at -B)
    return dict(P=P0, N=N0, Ecost=K0, T=T0, X_fail=-float(B), X_succ=Xs, identity_gap=T0 + K0,
                P_identity=(B - K0) / (Xs + B), P_textbook=(B - K0) / (A + B), cost=float(rho * L), xs=xs, V=V)

def bold_path(A, B, L, k, rho, cap=None, buf=100.0, lmin=None, n=40):
    """the state-wise first steps from x = 0: x_j, l_j, w_j = min(k l_j, A - x_j, cap), p_j. The product formula
    P = sum_j p_j prod_{i<j} (1 - p_i) holds only while every win ends the phase (w_j = A - x_j); 'terminal' marks it."""
    lmin = 0.1 * L if lmin is None else lmin
    rows = []; x = 0.0; surv = 1.0; P = 0.0; exact = True
    for j in range(n):
        room = (x + B - buf) / (1 + rho)
        if room < lmin: break
        l = min(L, room); w = min(k * l, A - x, cap or 1e18); c = rho * l; p = l / (l + w + c)
        term = w >= A - x - 1e-9
        exact &= term
        P += surv * p * (1.0 if term else float("nan"))
        rows.append(dict(j=j, x=x, l=l, w=w, c=c, p=p, surv=surv, terminal=term))
        surv *= (1 - p); x -= l + c
    return rows, (P if exact else None)

# ---------------------------------------------------------------- Brownian approximations (labelled as such)
def hit_bm(A, B, c, v):
    """P(+A before -B) for a Brownian motion with drift -c and variance v per trade (an approximation for a sum of
    bracket trades; exact only in the small-trade limit)"""
    if c <= 1e-12: return B / (A + B)
    th = 2 * c / v
    return math.expm1(th * B) / math.expm1(th * (A + B))

# ---------------------------------------------------------------- one programme
def caps_phase(st, L):
    cs = [st.get("max_win"), st["best"] * st["target"] if st.get("best") else None,
          st["conc"] * st["target"] if st.get("conc") else None]
    cs = [c for c in cs if c]
    return min(cs) if cs else None

def caps_funded(fd, Xc):
    cs = [fd.get("max_win"), fd["best"] * Xc if fd.get("best") else None, fd["conc"] * Xc if fd.get("conc") else None,
          fd.get("day_profit_cap"), fd["trade_best"] * Xc if fd.get("trade_best") else None]
    cs = [c for c in cs if c]
    return min(cs) if cs else None

def programme(prog, instr, m, k, X1, X, L=1500, size=100_000, F=None, cost_mult=1.0, kind="cfd"):
    F = F or F7.rules_for(prog, size, kind)
    rho = rho_of(instr, m, cost_mult)
    bs = F.get("buffer_scale", 1.0)
    lc = (2.0 * 31070.0 * m * SIG[instr]) if instr == "MNQ_fut" else 0.0     # one contract at the reference level
    lmin = max(0.1 * L, lc)
    wf = max(0.0, WMIN_SD / m - rho)
    ph = []
    for st in F["phases"]:
        tgt = st["target"] + (20.0 * bs if st.get("min_days") else 0.0)      # the engine's filler margin
        r = chain(tgt, st["dd"], L, k, rho, cap=caps_phase(st, L), buf=100.0 * bs, lmin=lmin, bs=bs,
                  min_rr=st.get("min_rr"), wmin_frac=wf, lc=lc)
        ph.append(dict(A=st["target"], B=st["dd"], cap=caps_phase(st, L), **{kk: r[kk] for kk in
                  ("P", "N", "Ecost", "T", "X_fail", "X_succ", "identity_gap", "P_identity", "P_textbook")}))
    reach = [1.0]
    for p in ph: reach.append(reach[-1] * p["P"])
    P = reach[-1]
    credits = sum(c * reach[j + 1] for j, c in enumerate(F.get("phase_credit") or []))
    fd = F["funded"]; D = fd["dd"]; caps = fd.get("caps")
    def target(i):
        a = X1 if i == 0 else X
        return min(a, caps[min(i, len(caps) - 1)]) if caps else a
    cache = {}
    def fch(a):
        if a not in cache:
            cache[a] = chain(a, D, L, k, rho, cap=caps_funded(fd, a), buf=100.0 * bs, lmin=lmin, bs=bs,
                             min_rr=fd.get("min_rr"), wmin_frac=wf, lc=lc, no_overshoot=bool(fd.get("profit_ceiling")))
        return cache[a]
    # Maven's rolling 30-day cap on closed profit is not in the chain (it delays wins, the engine has it)
    cyc, pr, chs = [], [], []
    reach_c = 1.0
    for i in range(400):
        a = target(i); ch = fch(a)
        cyc.append(a); chs.append(ch); reach_c *= ch["P"]; pr.append(reach_c)
        if reach_c < 1e-10: break
    split = fd["split"]
    succ = [ch["X_succ"] for ch in chs]                 # the balance paid out: the cycle target plus any overshoot
    pay = [split * xs_ for xs_ in succ]
    cash = sum(x * q for x, q in zip(pay, pr))
    ref = fd.get("refund", 0) or 0
    if fd.get("refund_split"): cash += ref / fd["refund_split"] * sum(pr[:fd["refund_split"]])
    elif ref: cash += ref * pr[fd.get("refund_after", 1) - 1]
    # the funded account's accounting identity: E[withdrawn] = -E[P&L at the end] - E[total cost]
    started = [1.0] + pr[:-1]                       # cycle i is traded if cycles 0..i-1 paid
    withdrawn = sum(xs_ * q for xs_, q in zip(succ, pr))
    ecost = sum(s * ch["Ecost"] for s, ch in zip(started, chs))
    ntr = sum(s * ch["N"] for s, ch in zip(started, chs))
    x_end = sum(s * (1 - ch["P"]) * ch["X_fail"] for s, ch in zip(started, chs))
    fee = F["fee"]
    return dict(rho=rho, c=rho * L, phases=ph, P=P, credits=credits, cyc=cyc, pr=pr, q1=chs[0]["P"],
                q=chs[1]["P"] if len(chs) > 1 else None, cash_funded=cash, withdrawn=withdrawn, cost_funded=ecost,
                trades_funded=ntr, x_end=x_end, identity_gap=withdrawn + x_end + ecost, n_paid=sum(pr),
                EV=credits + P * cash - fee - P * F.get("activation", 0), fee=fee)

if __name__ == "__main__":
    r = programme("FTMO 2-Step", "US100", 1.0, 3, 15000, 15000)
    print({k: v for k, v in r.items() if k not in ("phases", "cyc", "pr")})
    for p in r["phases"]: print(p)
