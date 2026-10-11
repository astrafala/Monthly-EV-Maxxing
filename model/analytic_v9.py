"""
Version 9 closed-form check of the engine: the exact trade-level Markov chain of the version 9 rules.

State: the account's P&L x relative to the start of the phase (or of the payout cycle), floor at -B, target at A.
    room(x)  = (x + B - buf) / (1 + rho)                risk that keeps stop loss + cost a buffer above the floor
    normal   (room(x) >= l_min):  l(x) = min(max(L, l_c), room(x)),  c = rho l
    terminal (room(x) <  l_min):  the stop is the floor itself (version 9: a barrier of the trade, as in the engine).
             The volume's risk at the plan's stop is l_v = max(room0, l_m) (CFDs: at least the smallest lot) or l_c times
             max(1, floor(room0 / l_c)) contracts (futures), room0 = (x + B) / (1 + rho); its cost c = rho l_v; a loss ends
             the attempt at -B exactly, so the trade's lower barrier is l_e = x + B - c below the entry before cost
    w(x)     = min( max( min(k l, A - x), w_min max(l, l_m), bs ), cap(x) )    w_min = max(0, 0.6 / m - rho)
             cap(x) = the per-trade rule cap, and with a profit ceiling C (Maven) also C - x: below the smallest allowed
             win the risk is lowered to cap / w_min (the engine's rule), and with C - x < bs the cycle is paid at x
             (the engine's payout band); a win may pass A (overshoot) up to the caps
    p(x)     = l_e / (l_e + w + c)  (l_e = l on a normal trade)      zero-edge bracket: the trade's mean is exactly -c
Solved on a fine grid by value iteration:
    V(x) = P(success),  N(x) = E[trades],  K(x) = E[total cost],  T(x) = E[P&L at the end]
Optional stopping (every trade has mean -c, bounded, and the number of trades has finite mean) gives
    T(0) = P E[X_end | success] + (1 - P) E[X_end | fail] = -K(0)
With the terminal rule every failure ends at -B, so E[X_end | fail] = -B and
    P = (B - K(0)) / (E[X_end | success] + B),
the textbook form with A replaced by the mean balance at success (A plus the mean overshoot).
Daily loss limits, the per-day part of the concentration policy, minimum and profitable days, payout dates, the daily
flat time, weekends, lot rounding and filler trades are not in the chain; they are in the engine.
"""
import json, math
import numpy as np
import firms_v9 as F7, calibrate as CB

SIG = json.load(open("sigma_v32.json"))
WMIN_SD = 0.6

def rho_of(instr, m, cost_mult=1.0):
    return cost_mult * CB.INSTR[instr][1] / 100.0 / (m * SIG[instr])

def min_lot_risk(instr, m):
    """risk of 0.01 lot with the plan's stop (m hourly sd) at the market's reference level (pathfirm.LOTS)"""
    import pathfirm as PF
    sp = PF.LOTS.get(instr, PF.LOTS["US100"])
    uv = sp["cs"] * sp["ref"] if sp["usd_quote"] else sp["cs"]
    return sp["vmin"] * uv * m * SIG[instr]

def chain(A, B, L, k, rho, cap=None, buf=100.0, lmin=None, bs=1.0, h=None, tol=1e-11, it_max=40000, min_rr=None,
          wmin_frac=0.0, lc=0.0, lm=0.0, ceiling=None):
    """lc: one futures contract's risk at the plan's stop; lm: the smallest CFD position's risk; ceiling: a profit ceiling
    (Maven) measured from the cycle start"""
    lmx = lc if lc > 0 else lm                          # the smallest position
    lmin = max(0.1 * L, lmx) if lmin is None else lmin
    lo = -B
    h = h or max(0.25, (A - lo) / 8000.0)
    top_x = A
    xs = np.arange(lo, top_x + 1e-9, h)
    if xs[-1] < top_x - 1e-9: xs = np.append(xs, top_x)
    room = (xs + B - buf) / (1.0 + rho)
    term = room < lmin                                   # the terminal trade: stop at the floor
    room0 = (xs + B) / (1.0 + rho)
    l_norm = np.minimum(max(L, lc), np.maximum(room, 0.0))
    l = np.where(term, room0, l_norm)
    if lc > 0: lv_t = lc * np.maximum(1.0, np.floor(room0 / lc + 1e-9))
    else: lv_t = np.maximum(room0, lm)
    w = np.minimum(k * l, A - xs)
    w = np.maximum(np.maximum(w, wmin_frac * np.maximum(l, lmx)), 1.0 * bs)
    capx = np.full_like(xs, cap if cap else 1e18)
    if ceiling is not None: capx = np.minimum(capx, ceiling - xs)
    over = w > capx
    w = np.where(over, capx, w)
    if wmin_frac > 0:                                    # a cap below the smallest allowed win: the engine lowers the risk
        shrink = over & (capx < wmin_frac * np.maximum(l, lmx) - 1e-9) & (capx >= 1.0 * bs) & (capx / wmin_frac >= lmx)
        l = np.where(shrink, capx / wmin_frac, l)
    lv = np.where(term, np.where(l < room0 - 1e-9, np.maximum(l, lmx), lv_t), l)
    stopped = np.zeros_like(xs, dtype=bool)
    if ceiling is not None:
        stopped = (ceiling - xs) < 1.0 * bs - 1e-9      # within $1 of the ceiling no win fits: the cycle is paid at x
    if min_rr:                                           # minimum reward:risk (Maven): shrink the risk of a normal trade;
        low = ~term & (w < min_rr * l)                   # a terminal trade's target is raised to it where the caps allow
        l = np.where(low, w / min_rr, l); lv = np.where(low, l, lv)
        w = np.where(term, np.maximum(w, np.minimum(capx, min_rr * (xs + B))), w)
    c = rho * lv
    le = np.where(term, xs + B - c, l)                  # distance (before cost) to the lower barrier
    p = np.where(le > 0, le / np.maximum(le + w + c, 1e-12), 0.0)
    up = xs + w; dn = np.where(term, -B, np.maximum(xs - l - c, -B))
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
    lm = 0.0 if lc else min_lot_risk(instr, m)                               # 0.01 lot at the reference level
    lmin = max(0.1 * L, lc, lm)
    wf = max(0.0, WMIN_SD / m - rho)
    ph = []
    for st in F["phases"]:
        fill = st.get("min_days") and not F.get("no_fillers")
        tgt = st["target"] + (20.0 * bs if fill else 0.0)                    # the engine's filler margin
        r = chain(tgt, st["dd"], L, k, rho, cap=caps_phase(st, L), buf=100.0 * bs, lmin=lmin, bs=bs,
                  min_rr=st.get("min_rr"), wmin_frac=wf, lc=lc, lm=lm)
        ph.append(dict(A=st["target"], B=st["dd"], cap=caps_phase(st, L), **{kk: r[kk] for kk in
                  ("P", "N", "Ecost", "T", "X_fail", "X_succ", "identity_gap", "P_identity", "P_textbook")}))
    reach = [1.0]
    for p in ph: reach.append(reach[-1] * p["P"])
    P = reach[-1]
    credits = sum(c * reach[j + 1] for j, c in enumerate(F.get("phase_credit") or []))
    fd = F["funded"]; D = fd["dd"]; caps = fd.get("caps")
    def target(i):
        a = X1 if i == 0 else X
        if fd.get("profit_ceiling"): a = min(a, fd["profit_ceiling"])
        return min(a, caps[min(i, len(caps) - 1)]) if caps else a
    cache = {}
    def fch(a):
        if a not in cache:
            cache[a] = chain(a, D, L, k, rho, cap=caps_funded(fd, a), buf=100.0 * bs, lmin=lmin, bs=bs,
                             min_rr=fd.get("min_rr"), wmin_frac=wf, lc=lc, lm=lm, ceiling=fd.get("profit_ceiling"))
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
    # E[cash | exactly n cycles paid] in the chain's reset model (version 9: the paid amount of a cycle is its mean balance
    # at success m_i = E[X_succ], not the nominal target; review of version 8, finding 16)
    def cash_given(n):
        v = sum(split * succ[i] for i in range(n))
        if fd.get("refund_split"): v += ref / fd["refund_split"] * min(n, fd["refund_split"])
        elif ref and n >= fd.get("refund_after", 1): v += ref
        return v
    return dict(rho=rho, c=rho * L, phases=ph, P=P, credits=credits, cyc=cyc, pr=pr, q1=chs[0]["P"],
                m1=succ[0], m=succ[1] if len(succ) > 1 else None, cash_given=[cash_given(n) for n in range(0, 7)],
                q=chs[1]["P"] if len(chs) > 1 else None, cash_funded=cash, withdrawn=withdrawn, cost_funded=ecost,
                trades_funded=ntr, x_end=x_end, identity_gap=withdrawn + x_end + ecost, n_paid=sum(pr),
                EV=credits + P * cash - fee - P * F.get("activation", 0), fee=fee)

if __name__ == "__main__":
    r = programme("FTMO 2-Step", "US100", 1.0, 3, 15000, 15000)
    print({k: v for k, v in r.items() if k not in ("phases", "cyc", "pr")})
    for p in r["phases"]: print(p)
