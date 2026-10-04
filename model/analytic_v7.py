"""
Version 7 closed-form check of the engine: the exact trade-level Markov chain of the corrected rules.

State: the account's P&L x relative to the start of the phase (or of the payout cycle), floor at -B, target at A.
    room(x) = (x + B - buf) / (1 + rho)              risk that keeps stop loss + round-trip cost above the floor
    the attempt ends at x (a failure) if room(x) < l_min = max(0.1 L, one futures contract)
    l(x)    = min(L, room(x))
    w(x)    = max(min(k l(x), A - x, cap), bs)       cap = the per-trade cap (40% concentration policy, firm caps)
    c(x)    = rho l(x),   rho = kappa / (m sigma)
    p(x)    = l / (l + w + c)                        zero-edge bracket: the trade's mean is exactly -c
    x -> x + w (success if x + w >= A) with chance p,  x -> x - l - c otherwise.
Because l(x) (1 + rho) <= x + B - buf the account never reaches the floor itself: every failure is an abandonment at a
P&L between -B + buf and -B + buf + l_min (1 + rho). Solved on a fine grid by value iteration:
    V(x) = P(success),  N(x) = E[trades],  K(x) = E[total cost],  T(x) = E[P&L at the end]
Optional stopping (every trade has mean -c) gives the general accounting identity, checked numerically:
    T(0) = P A + (1 - P) E[X_end | fail] = -K(0)
    =>  P = (E[-X_end | fail] - K(0)) / (A + E[-X_end | fail])
The textbook form P = (B - E[cost]) / (A + B) is the special case where every failure ends exactly at -B.
Daily loss limits, the per-day part of the concentration policy, minimum and profitable days, payout dates, the daily
flat time and weekends are not in the chain; they are in the engine.
"""
import json, math
import numpy as np
import firms_v7 as F7, calibrate as CB

SIG = json.load(open("sigma_v32.json"))

def rho_of(instr, m, cost_mult=1.0):
    return cost_mult * CB.INSTR[instr][1] / 100.0 / (m * SIG[instr])

def chain(A, B, L, k, rho, cap=None, buf=100.0, lmin=None, bs=1.0, h=None, tol=1e-11, it_max=40000, min_rr=None):
    lmin = 0.1 * L if lmin is None else lmin
    lo = -B + buf
    h = h or max(0.25, (A - lo) / 8000.0)
    xs = np.arange(lo, A + 1e-9, h)
    if xs[-1] < A - 1e-9: xs = np.append(xs, A)
    room = (xs + B - buf) / (1.0 + rho)
    dead = room < lmin                                   # the attempt ends here
    l = np.minimum(L, np.maximum(room, 0.0))
    w = np.minimum(k * l, A - xs)
    if cap: w = np.minimum(w, cap)
    w = np.maximum(w, 1.0 * bs)
    if min_rr:                                           # minimum reward:risk (Maven): shrink the risk instead
        low = w < min_rr * l
        l = np.where(low, np.maximum(w / min_rr, lmin), l); w = np.where(low, np.maximum(w, min_rr * l), w)
    c = rho * l
    p = np.where(dead, 0.0, l / np.maximum(l + w + c, 1e-12))
    up = xs + w; dn = xs - l - c
    won = up >= A - 1e-9
    live = ~dead
    V = np.zeros_like(xs); N = np.zeros_like(xs); K = np.zeros_like(xs); T = xs.copy()
    top = xs >= A - 1e-9
    V[top] = 1.0; T[top] = A
    def at(arr, y): return np.interp(y, xs, arr)
    for _ in range(it_max):
        Vu = np.where(won, 1.0, at(V, up)); Tu = np.where(won, up, at(T, up))      # a minimum-size win may pass A
        Nu = np.where(won, 0.0, at(N, up)); Ku = np.where(won, 0.0, at(K, up))
        Vn = np.where(live & ~top, p * Vu + (1 - p) * at(V, dn), V)
        Tn = np.where(live & ~top, p * Tu + (1 - p) * at(T, dn), T)
        Nn = np.where(live & ~top, 1 + p * Nu + (1 - p) * at(N, dn), N)
        Kn = np.where(live & ~top, c + p * Ku + (1 - p) * at(K, dn), K)
        d = max(np.abs(Vn - V).max(), np.abs(Tn - T).max() / max(A, 1.0), np.abs(Nn - N).max() * 1e-4,
                np.abs(Kn - K).max() / max(A, 1.0))
        V, T, N, K = Vn, Tn, Nn, Kn
        if d < tol: break
    P0, T0, N0, K0 = (float(at(arr, 0.0)) for arr in (V, T, N, K))
    Xf = (T0 - P0 * A) / max(1.0 - P0, 1e-12)               # E[P&L at the end | failure]
    return dict(P=P0, N=N0, Ecost=K0, T=T0, X_fail=Xf, identity_gap=T0 + K0,
                P_identity=(-Xf - K0) / (A - Xf), P_textbook=(B - K0) / (A + B), cost=float(rho * L), xs=xs, V=V)

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
    lmin = max(0.1 * L, (2.0 * 31070.0 * m * SIG[instr]) if instr == "MNQ_fut" else 0.0)
    ph = []
    for st in F["phases"]:
        r = chain(st["target"], st["dd"], L, k, rho, cap=caps_phase(st, L), buf=100.0 * bs, lmin=lmin, bs=bs,
                  min_rr=st.get("min_rr"))
        ph.append(dict(A=st["target"], B=st["dd"], cap=caps_phase(st, L), **{kk: r[kk] for kk in
                  ("P", "N", "Ecost", "T", "X_fail", "identity_gap", "P_identity", "P_textbook")}))
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
                             min_rr=fd.get("min_rr"))
        return cache[a]
    # Maven's rolling cap does not enter: the plan never requests a payout the cap would cut (it waits until the
    # 30-day window has room), so the cap changes when cash arrives, not how much
    cyc, pr, chs = [], [], []
    reach_c = 1.0
    for i in range(400):
        a = target(i); ch = fch(a)
        cyc.append(a); chs.append(ch); reach_c *= ch["P"]; pr.append(reach_c)
        if reach_c < 1e-10: break
    split = fd["split"]
    pay = [split * a for a in cyc]
    cash = sum(x * q for x, q in zip(pay, pr))
    ref = fd.get("refund", 0) or 0
    if fd.get("refund_split"): cash += ref / fd["refund_split"] * sum(pr[:fd["refund_split"]])
    elif ref: cash += ref * pr[fd.get("refund_after", 1) - 1]
    # the funded account's accounting identity: E[withdrawn] = -E[P&L at the end] - E[total cost]
    started = [1.0] + pr[:-1]                       # cycle i is traded if cycles 0..i-1 paid
    withdrawn = sum(a * q for a, q in zip(cyc, pr))
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
