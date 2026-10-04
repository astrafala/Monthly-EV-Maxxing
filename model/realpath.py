"""
Full real-price-path validation of a fast plan on FTMO 2-Step 100K.
Back-to-back random-direction brackets on real hourly bars of one instrument, with:
 risk = min(L, room above floor - 100, room left in today's 5% limit - 200),
 target = min(k * risk, distance to phase target), stop s = m * hourly sigma,
 costs (% of notional per round trip) and overnight financing per rollover crossed,
 FTMO day = midnight Prague; min 4 trading days per phase; reviews 1 and 3 days;
 funded: first payout 14 days after start, then every 14 days; per-cycle target X
 (stop trading once reached and wait for payout day); 80% split; fee refunded with 1st payout.
"""
import sys, math, random, json
import numpy as np, pandas as pd
import calibrate as CB

class Path:
    def __init__(self, name):
        self.mk = CB.Market(name)
        fn = CB.INSTR[name][0]
        d = CB.load(fn)
        self.day = pd.factorize(d.index.tz_convert("Europe/Prague").normalize())[0]
        self.cost = CB.INSTR[name][1] / 100; self.fin = CB.INSTR[name][2] / 100

def run(name, m, k, L, X1, X, n, seed=5, fee=632.0):
    P = Path(name); mk = P.mk; rng = random.Random(seed)
    s = m * mk.sig_h; span = mk.t[-1] - mk.t[0]
    res = []
    for _ in range(n):
        i = int(mk.entry_ok[rng.randrange(len(mk.entry_ok) // 2)])
        t_start = mk.t[i]; t_off = 0.0       # t_off accumulates wraps and added waits
        def now(ii): return mk.t[ii] + t_off
        def next_entry(ii):
            nonlocal t_off
            j = mk.next_entry(ii)
            if j is None:
                t_off += span + 1; j = mk.next_entry(0)
            return j
        def one_trade(ii, l, w):
            nonlocal t_off
            d = 1 if rng.random() < 0.5 else -1
            tg = s * w / l
            won, j, ro = mk.bracket(ii, d, s, tg, rng)
            if won is None:
                return None, 0
            notional = l / s
            pnl = (w if won else -l) - P.cost * notional - P.fin * notional * ro
            return pnl, j
        stage_ok = True
        for (A, minday, review) in ((10_000, 4, 1), (5_000, 4, 3)):
            x = 0.0; days = set(); cur_day = P.day[i]; day_ref = 0.0
            while True:
                if x >= A:
                    extra = max(0, minday - len(days))
                    t_off += (extra + review) * 24; break
                if x <= -10_000 + 1e-6: stage_ok = False; break
                if P.day[i] != cur_day: cur_day = P.day[i]; day_ref = x
                room_floor = x + 10_000 - 100; room_day = 5_000 - (day_ref - x) - 200
                l = min(L, room_floor, room_day)
                if room_day < 0.1 * L and room_floor >= 0.1 * L:
                    # wait for the next FTMO day
                    j = i
                    while j < mk.N - 1 and P.day[j] == cur_day: j += 1
                    i = next_entry(j); continue
                if l < 1: l = max(x + 10_000 - 1, 1)
                fee_est = P.cost * l / s + 5.0
                w = min(k * l, A - x + fee_est); w = max(w, fee_est + 1.0)
                pnl, j = one_trade(i, l, w)
                if pnl is None: i = next_entry(0); continue
                days.add(P.day[i]); x += pnl; x = max(x, -10_000)
                i = next_entry(j + 1)
            if not stage_ok: break
        if not stage_ok:
            res.append((-fee, (now(i) - t_start) / 24, None)); continue
        # funded
        x = 0.0; paid = 0.0; npay = 0; t_f0 = now(i); next_pay = t_f0 + 14 * 24
        cur_day = P.day[i]; day_ref = 0.0; t_first = None
        while x > -10_000 + 1e-6 and npay < 200:
            if P.day[i] != cur_day: cur_day = P.day[i]; day_ref = x
            if now(i) >= next_pay:
                if x > 0:
                    paid += 0.8 * x + (fee if npay == 0 else 0); npay += 1; x = 0.0
                    if t_first is None: t_first = now(i) + 24
                next_pay += 14 * 24
            tgt = X1 if npay == 0 else X
            if x >= tgt:   # wait for payout day
                while now(i) < next_pay:
                    i = next_entry(i + 1)
                continue
            room_floor = x + 10_000 - 100; room_day = 5_000 - (day_ref - x) - 200
            l = min(L, room_floor, room_day)
            if room_day < 0.1 * L and room_floor >= 0.1 * L:
                j = i
                while j < mk.N - 1 and P.day[j] == cur_day: j += 1
                i = next_entry(j); continue
            if l < 1: l = max(x + 10_000 - 1, 1)
            fee_est = P.cost * l / s + 5.0
            w = min(k * l, max(tgt - x, 0.0) + fee_est)
            pnl, j = one_trade(i, l, w)
            if pnl is None: i = next_entry(0); continue
            x += pnl; x = max(x, -10_000)
            i = next_entry(j + 1)
        res.append((-fee + paid, (now(i) - t_start) / 24, (t_first - t_start) / 24 if t_first else None))
    ev = np.array([r[0] for r in res]); dd = np.array([r[1] for r in res])
    tf = [r[2] for r in res if r[2] is not None]
    out = dict(instr=name, m=m, k=k, L=L, X1=X1, X=X, n=n, EV=float(ev.mean()),
               CI=float(1.96 * ev.std() / math.sqrt(n)), days=float(dd.mean()),
               EV_month=float(ev.mean() / (dd.mean() / 30.44)), Pprofit=float(np.mean(ev > 0)),
               t_first_med=float(np.median(tf)) if tf else None, Pfunded=len(tf) / n)
    return out

if __name__ == "__main__":
    nm, m, k, L, X1, X, n = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), \
        float(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7])
    r = run(nm, m, k, L, X1, X, n)
    print(json.dumps(r))
    json.dump(r, open(f"real_{nm}_{m}_{k}_{int(L)}_{int(X)}.json", "w"))
