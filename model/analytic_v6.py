"""
Closed-form check of the simulation, written independently of the path engine.

Each trade is a bracket around the entry: stop at distance s = m*sigma (price fraction), target placed so that a win
nets w after the round-trip cost c. On a driftless price path the chance of touching the target first is
    p = s / (s + s*(w+c)/l) = l / (l + w + c)
so the trade's mean is  p*w - (1-p)*(l+c) = -c  (exactly the cost) and its variance is
    v = p*w^2 + (1-p)*(l+c)^2 - c^2.
A run of such trades is approximated by a Brownian motion with drift -c and variance v per trade. For a target A above
and a floor B below the start:
    P(target first) = (e^{theta*B} - 1) / (e^{theta*(A+B)} - 1),   theta = 2c / v          (-> B/(A+B) as c -> 0)
    E[trades]       = (B*(1-P) - A*P) / c                                                  (Wald's identity)
Funded stage with a static floor D below the start and payouts of each cycle's profit X: every cycle starts afresh, so
the number of paid cycles is geometric with success chance q = P(X before -D):
    E[paid cycles] = q / (1-q),   E[cash] = split * (X1*q + X*q^2/(1-q)) + refund * P(refund reached)
With no cost q/(1-q) = D/X and E[cash] = split*D: the fair-game withdrawal identity.
The daily loss limit, minimum and profitable days, payout dates and best-day rules are left out here; they change
time much more than value, which is what the comparison with the engine shows.
"""
import json, math
import firms_v5 as F5, calibrate as CB

SIG = json.load(open("sigma_v32.json"))

def trade_stats(L, k, m, instr):
    sig = SIG[instr]; cost_rate = CB.INSTR[instr][1] / 100.0
    notional = L / (m * sig); c = cost_rate * notional
    l, w = L, k * L
    p = l / (l + w + c)
    mean = p * w - (1 - p) * (l + c)
    var = p * w * w + (1 - p) * (l + c) ** 2 - mean ** 2
    return dict(notional=notional, c=c, p=p, mean=mean, var=var, cR=c / L)

def hit(A, B, c, v):
    if c <= 1e-12: return B / (A + B)
    th = 2 * c / v
    x = math.expm1(th * B) / math.expm1(th * (A + B))
    return x

def trades(A, B, c, P):
    return (B * (1 - P) - A * P) / c if c > 1e-12 else A * B

def programme(prog, instr, m, k, X1, X, L=1500, size=100_000, F=None):
    """F: the firm's rule set (defaults to firms_v5). Caps on a single win (a per-trade cap, a best-day share or a
    daily profit cap) lower the effective k of that stage; nothing else in the rules changes the averages here."""
    F = F or F5.cfd_firms(size)[prog]
    t = trade_stats(L, k, m, instr)
    ph = []
    for st in F["phases"]:
        cap = st.get("max_win") or (st["best"] * st["target"] if st.get("best") else None)
        ts = trade_stats(L, min(k, cap / L), m, instr) if cap else t
        P = hit(st["target"], st["dd"], ts["c"], ts["var"])
        ph.append(dict(A=st["target"], B=st["dd"], P=P, N=trades(st["target"], st["dd"], ts["c"], P), k=ts and (min(k, cap / L) if cap else k)))
    Pboth = math.prod(p["P"] for p in ph)
    fd = F["funded"]; D = fd["dd"]
    caps = [c for c in (fd.get("best") and fd["best"] * X, fd.get("day_profit_cap")) if c]
    kf = min([k] + [c / L for c in caps])
    tf = trade_stats(L, kf, m, instr)
    q1 = hit(X1, D, tf["c"], tf["var"]); q = hit(X, D, tf["c"], tf["var"])
    # expected number of paid cycles: first cycle with chance q1, every later one with chance q
    n_paid = q1 / (1 - q)                       # q1 * (1 + q + q^2 + ...)
    cyc = [X1] + [X] * 199
    if fd.get("caps"): cyc = [min(a, fd["caps"][min(i, len(fd["caps"]) - 1)]) for i, a in enumerate(cyc)]
    pr = [q1 * q ** i for i in range(200)]       # chance of reaching paid cycle i+1
    cash = fd["split"] * sum(a * p for a, p in zip(cyc, pr))
    ref = fd.get("refund", 0) or 0
    if fd.get("refund_split"):
        cash += ref / fd["refund_split"] * sum(pr[:fd["refund_split"]])
    elif ref:
        cash += ref * pr[fd.get("refund_after", 1) - 1]
    fee = F["fee"] + F.get("activation", 0)
    return dict(trade=t, trade_funded=tf, k_funded=kf, phases=ph, P=Pboth, q1=q1, q=q, paid_cycles=n_paid, cash_funded=cash,
                EV=Pboth * cash - F["fee"] - Pboth * F.get("activation", 0), fee=F["fee"])

if __name__ == "__main__":
    import sys
    r = programme("FTMO 2-Step", "US100", 0.75, 5, 10000, 10000)
    print(json.dumps({k: (v if not isinstance(v, float) else round(v, 4)) for k, v in r.items() if k not in ("trade", "phases")}, indent=1))
    print({k: round(v, 4) for k, v in r["trade"].items()}); print([{k: round(v, 4) for k, v in p.items()} for p in r["phases"]])


# ---------------------------------------------------------------- the exact trade-level chain (any k, including bold play)
# The Brownian formulas above are accurate when each trade is small next to the distances (small k). The plan's settings
# are bold: a single win often reaches the target, and the take-profit is cut to the remaining distance. For those the
# account is a Markov chain on its P&L x in (-B, A):
#     risk  l(x) = min(L, x + B - buffer)            (never risk more than the room above the floor)
#     win   w(x) = min(k l(x), A - x, cap)           (never aim past the target; per-trade caps where rules impose them)
#     cost  c(x) = rho * l(x),  rho = kappa / (m sigma)
#     win chance p(x) = l / (l + w + c)              (zero-edge bracket)
#     x -> x + w with probability p,  x -> x - l - c otherwise.
# V(x) = P(reach A before -B) solves V = p V(x+w) + (1-p) V(x-l-c), V = 1 at A, 0 at -B; the expected number of trades
# N solves N = 1 + p N(x+w) + (1-p) N(x-l-c). Both are solved by iteration on a fine grid. Daily limits, minimum and
# profitable days, payout dates, weekends, gaps and financing are not in the chain (they are in the engine).
import numpy as np

def chain(A, B, L, k, rho, cap=None, buf=100.0, h=None, tol=1e-12, it_max=20000):
    h = h or max(0.5, (A + B) / 6000.0)
    xs = np.arange(-B + h, A, h)
    l = np.minimum(L, xs + B - buf)
    l = np.where(l <= 1.0, np.maximum(xs + B - 1.0, 1.0), l)
    w = np.minimum(k * l, A - xs)
    if cap: w = np.minimum(w, cap)
    w = np.maximum(w, 1.0)
    c = rho * l
    p = l / (l + w + c)
    up = xs + w; dn = xs - l - c
    up_done = up >= A - 1e-9; dn_done = dn <= -B + 1e-9
    V = np.zeros_like(xs); N = np.zeros_like(xs); K = np.zeros_like(xs)
    xe = np.concatenate([[-B], xs, [A]])           # the floor and the target are part of the grid: 0 / 1 there
    def ev(arr, y, done, val, top=None):
        return np.where(done, val, np.interp(y, xe, np.concatenate([[0.0], arr, [val if top is None else top]])))
    for _ in range(it_max):
        Vn = p * ev(V, up, up_done, 1.0) + (1 - p) * ev(V, dn, dn_done, 0.0, top=1.0)
        Nn = 1 + p * ev(N, up, up_done, 0.0) + (1 - p) * ev(N, dn, dn_done, 0.0)
        Kn = c + p * ev(K, up, up_done, 0.0) + (1 - p) * ev(K, dn, dn_done, 0.0)     # expected total cost
        d = max(np.abs(Vn - V).max(), np.abs(Nn - N).max() * 1e-6, np.abs(Kn - K).max() * 1e-8)
        V, N, K = Vn, Nn, Kn
        if d < tol: break
    P0 = float(np.interp(0.0, xe, np.concatenate([[0.0], V, [1.0]])))
    N0 = float(np.interp(0.0, xe, np.concatenate([[0.0], N, [0.0]]))); K0 = float(np.interp(0.0, xe, np.concatenate([[0.0], K, [0.0]])))
    # optional stopping: P*A - (1-P)*B = -E[total cost]  =>  P = (B - E[cost]) / (A + B)
    return dict(P=P0, N=N0, Ecost=K0, P_identity=(B - K0) / (A + B), cost=float(rho * L), xs=xs, V=V)

def bold_steps(A, B, L, rho, buf=100.0, n=12):
    """the bold chain written out: the j-th trade starts at x_j = -j (L + c) and wins A - x_j with chance p_j"""
    rows = []; x = 0.0; surv = 1.0; P = 0.0
    for j in range(n):
        l = min(L, x + B - buf)
        if l <= 1.0: break
        c = rho * l; w = A - x; p = l / (l + w + c)
        P += surv * p
        rows.append(dict(j=j, x=x, l=l, c=c, w=w, p=p, surv=surv, P=P))
        surv *= (1 - p); x -= l + c
    return rows, P

def programme_exact(prog, instr, m, k, X1, X, L=1500, size=100_000, F=None, cost_mult=1.0):
    F = F or F5.cfd_firms(size)[prog]
    sig = SIG[instr]; kappa = cost_mult * CB.INSTR[instr][1] / 100.0; rho = kappa / (m * sig)
    bs = F.get("buffer_scale", 1.0)
    ph = []
    for st in F["phases"]:
        cap = st.get("max_win") or (st["best"] * st["target"] if st.get("best") else None)
        r = chain(st["target"], st["dd"], L, k, rho, cap=cap, buf=100.0 * bs)
        ph.append(dict(A=st["target"], B=st["dd"], P=r["P"], N=r["N"], Ecost=r["Ecost"], P_identity=r["P_identity"], cap=cap))
    P = math.prod(p["P"] for p in ph)
    fd = F["funded"]; D = fd["dd"]
    def fcap(Xc):
        cs = [c for c in (fd.get("best") and fd["best"] * Xc, fd.get("day_profit_cap")) if c]
        return min(cs) if cs else None
    caps = fd.get("caps")
    X1e = min(X1, caps[0]) if caps else X1
    r1 = chain(X1e, D, L, k, rho, cap=fcap(X1e), buf=100.0 * bs)
    Xe = min(X, caps[1]) if caps and len(caps) > 1 else X
    rq = chain(Xe, D, L, k, rho, cap=fcap(Xe), buf=100.0 * bs)
    rl = chain(X, D, L, k, rho, cap=fcap(X), buf=100.0 * bs)
    q1, q, ql = r1["P"], rq["P"], rl["P"]
    # cycle sizes and chances: cycle i (0-based) is reached with chance q1 * q^(i-1) ...; caps apply to the first payouts
    cyc = [X1e]; pr = [q1]
    for i in range(1, 300):
        a = min(X, caps[min(i, len(caps) - 1)]) if caps else X
        qi = q if (caps and a == Xe) else ql
        cyc.append(a); pr.append(pr[-1] * qi)
    cash = fd["split"] * sum(a * p for a, p in zip(cyc, pr))
    ref = fd.get("refund", 0) or 0
    if fd.get("refund_split"): cash += ref / fd["refund_split"] * sum(pr[:fd["refund_split"]])
    elif ref: cash += ref * pr[fd.get("refund_after", 1) - 1]
    # expected funded trades and the withdrawal identity: E[withdrawn] = D - E[total cost]
    n_cycles = 1 + sum(pr)                       # every reached cycle is traded; the last one ends at the floor
    # cycle i+1 is traded with the chance pr[i] that cycle i paid; its chain depends on its own target
    chains = [r1] + [(rq if (caps and a == Xe) else rl) for a in cyc[1:]]
    ntr = r1["N"] + sum(p * ch["N"] for p, ch in zip(pr[:-1], chains[1:]))
    ecost = r1["Ecost"] + sum(p * ch["Ecost"] for p, ch in zip(pr[:-1], chains[1:]))
    withdrawn = sum(a * p for a, p in zip(cyc, pr))
    return dict(rho=rho, c=rho * L, phases=ph, P=P, q1=q1, q=ql, cash_funded=cash, withdrawn=withdrawn,
                trades_funded=ntr, cost_funded=ecost, identity=D - ecost, n_cycles_paid=sum(pr), r1=r1, rq=rl, pr=pr, cyc=cyc,
                EV=P * cash - F["fee"] - P * F.get("activation", 0), fee=F["fee"])
