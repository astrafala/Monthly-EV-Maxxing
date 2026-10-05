"""
Concurrent positions on several instruments, hourly bars, FTMO-style account.

Data: real aligned hourly bars (data="real") or synthetic zero-edge correlated random walks with the
same hourly volatility per instrument (data="synth", correlation rho between every pair).

Each instrument holds at most one bracket. A bracket opens at a bar's open; that same bar's high/low
can already resolve it. If a later bar opens beyond the stop or target (a gap), it fills at the open.
Ties inside one bar: target first with probability l/(l+w).
Constraints when opening a new position:
  risk_i <= the per-trade risk
  sum of open risk <= total_cap
  sum of (open risk + costs) <= room above the floor - 25 and <= today's loss room - 100
so a simultaneous stop-out of everything never breaches the daily or maximum loss.
'same_dir' forces every open position to share one direction (correlated stacking).
Phase: when the closed balance reaches the target, everything still open is closed at that bar's close.
Funded: cycle target X1 (first payout) then X; once reached, close all and wait for the payout date.
"""
import sys, os, json, math, random
import numpy as np, pandas as pd
import calibrate as CB

# twins for synthetic tests: same volatility and costs as US100, independent (or rho-correlated) paths
for _s in ["b", "c", "d"]:
    CB.INSTR["US100" + _s] = CB.INSTR["US100"]
    CB.INSTR["US100free" + _s] = (CB.INSTR["US100"][0], 0.0, 0.0, CB.INSTR["US100"][3])
CB.INSTR["US100free"] = (CB.INSTR["US100"][0], 0.0, 0.0, CB.INSTR["US100"][3])

def _finish(idx, nm, O, H, L, C, sig):
    f, c, fin, hrs = CB.INSTR[nm]
    hr = idx.hour.values; wd = idx.weekday.values
    ok = ~np.isnan(O)
    ok_entry = ok & (hr >= hrs[0]) & (hr <= hrs[1]) & (wd < 5) if hrs is not None else ok
    return dict(O=O, H=H, L=L, C=C, ok=ok, entry=ok_entry, cost=c / 100, fin=fin / 100, sig=sig,
                roll=(hr == (0 if hrs is None else 22)))

def load_aligned(names):
    frames = {}
    for nm in names:
        d = CB.load(CB.INSTR[nm][0]); frames[nm] = d[~d.index.duplicated()]
    start = max(d.index[0] for d in frames.values()); end = min(d.index[-1] for d in frames.values())
    idx = pd.date_range(start.floor("h"), end.floor("h"), freq="h", tz="UTC")
    data = {}
    for nm, d in frames.items():
        d = d[(d.index >= start) & (d.index <= end)].copy()
        d.index = d.index.floor("h"); d = d[~d.index.duplicated()]
        r = d.reindex(idx)
        lr = np.log(d.Close).diff(); gaps = d.index.to_series().diff().dt.total_seconds().div(3600)
        sig = float(lr[gaps <= 1.01].std())
        data[nm] = _finish(idx, nm, r.Open.values, r.High.values, r.Low.values, r.Close.values, sig)
    day = pd.factorize(idx.tz_convert("Europe/Prague").normalize())[0]
    return idx, data, day

SIGMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sigma_v32.json")

def hourly_sigma(nm):
    """hourly log-return sigma of the instrument's real series. The values the published runs used are
    stored in sigma_v32.json, so synthetic paths rebuild exactly without the price files;
    set SIGMA_FROM_DATA=1 to recompute them from the downloaded CSVs instead."""
    if not os.environ.get("SIGMA_FROM_DATA") and os.path.exists(SIGMA_FILE):
        s = json.load(open(SIGMA_FILE))
        if nm in s: return s[nm]
    _, rd, _ = load_aligned([nm])
    return rd[nm]["sig"]

# random-number streams (version 8): every path is drawn from its own stream, keyed by the path number, the market
# group, the length, the sub-step count and the correlation, so two paths share random numbers only if every key matches.
# Version 7 seeded numpy with the path number alone and gave other markets offset numbers (+50, +60, +70), so a gold
# path could reuse the random numbers of a yen path with another number (review of version 7, finding 14).
# The Nasdaq CFD and the micro Nasdaq future are one market group: they follow the same index path.
MARKET_GROUP = {"US100": 1, "MNQ_fut": 1, "US100free": 1, "XAUUSD": 2, "USDJPY": 3, "EURUSD": 4, "GBPUSD": 5,
                "US500": 6, "BTC": 7, "ETH": 8}
STREAM_LOG = []          # (seed, group key, years, sub, rho) of every path built in this process (stream manifest)

def stream_key(names, rho, years, sub, seed):
    g = [MARKET_GROUP.get(nm, 100 + sum(map(ord, nm))) for nm in names]
    return [int(seed), 1 + len(g)] + g + [int(round(years * 1000)), int(sub), int(round(rho * 1e6))]

def load_synth(names, rho, years=12, sub=60, seed=11):
    """correlated random walks of the log price with each instrument's real hourly sigma and drift -sigma^2/2 per hour,
    so that the price itself is a martingale (zero expected change: the zero-skill model of 3.2).
    Non-crypto markets are closed at weekends (the price keeps moving, so Monday can gap).
    sub sub-steps per hour (version 8: 60, one minute each; version 7: 12)."""
    idx = pd.date_range("2030-01-01", periods=int(years * 365.25 * 24), freq="h", tz="UTC")
    key = stream_key(names, rho, years, sub, seed); STREAM_LOG.append(tuple(key))
    n = len(idx); k = len(names); rs = np.random.default_rng(np.random.SeedSequence(key))
    cov = np.full((k, k), rho) + (1 - rho) * np.eye(k)
    Lc = np.linalg.cholesky(cov)
    z = rs.standard_normal((n * sub, k)) @ Lc.T
    data = {}
    for j, nm in enumerate(names):
        sig = hourly_sigma(nm)
        inc = z[:, j] * sig / math.sqrt(sub) - 0.5 * sig * sig / sub
        lp = np.concatenate([[0.0], np.cumsum(inc)])
        # the maximum and the minimum of the Brownian bridge between two sample points, each drawn from its exact
        # marginal law, independently of each other. The joint law differs only through the chance that one sub-step's
        # path spans both a stop and a target: at most exp(-W^2 / v) per sub-step for a bracket of width W, i.e.
        # exp(-60 m^2) for a stop of m hourly sd with one-minute sub-steps (below 5e-10 for m >= 0.6); verify_v8
        # adds this bound up over every simulated trade
        a, b = lp[:-1], lp[1:]; v = sig * sig / sub
        hi = 0.5 * (a + b + np.sqrt((b - a) ** 2 - 2 * v * np.log(rs.random(len(a)))))
        lo = 0.5 * (a + b - np.sqrt((b - a) ** 2 - 2 * v * np.log(rs.random(len(a)))))
        O = 100.0 * np.exp(lp[:-1][::sub]); C = 100.0 * np.exp(lp[sub::sub])
        H = 100.0 * np.exp(hi.reshape(n, sub).max(1)); L = 100.0 * np.exp(lo.reshape(n, sub).min(1))
        if CB.INSTR[nm][3] is not None:
            closed = idx.weekday.values >= 5
            O[closed] = np.nan; H[closed] = np.nan; L[closed] = np.nan; C[closed] = np.nan
        data[nm] = _finish(idx, nm, O, H, L, C, sig)
        # the sub-step extremes, in time order inside each hour: used to decide which of a stop and a target that
        # are both touched within one hourly bar was touched first (version 6; before, a fair coin decided)
        data[nm]["sH"] = 100.0 * np.exp(hi); data[nm]["sL"] = 100.0 * np.exp(lo)      # float64: exactly the hourly H/L
        data[nm]["sub"] = sub
        data[nm]["norm"] = True                  # normalised to 100 at the start (futures: see pathfirm.contract_value)
    day = pd.factorize(idx.tz_convert("Europe/Prague").normalize())[0]
    return idx, data, day

_CACHE = {}

def run(names, m, k, per_trade, total_cap, X1, X, n, seed=1, same_dir=False, fee=632.0,
        phases=((10_000, 4, 1), (5_000, 4, 3)), dll=5_000.0, dd=10_000.0, split=0.8, cycle=14,
        min_frac=0.1, max_days=1500, funded_risk=None, data="real", rho=0.0, tag=None, combined=True):
    key = (tuple(names), data, rho)
    if key not in _CACHE:
        _CACHE[key] = load_aligned(names) if data == "real" else load_synth(names, rho)
    idx, D0, day = _CACHE[key]
    T = len(idx); rng = random.Random(seed)
    day = day.tolist()
    D = {}
    for nm, v in D0.items():
        D[nm] = dict(O=v["O"].tolist(), H=v["H"].tolist(), L=v["L"].tolist(), C=v["C"].tolist(),
                     ok=v["ok"].tolist(), entry=v["entry"].tolist(), roll=v["roll"].tolist(),
                     cost=v["cost"], fin=v["fin"], sig=v["sig"])
    min_l = min_frac * per_trade
    def attempt():
        st = dict(t=rng.randrange(0, T // 2), passed=0, trades=0)
        pos = {}
        def settle(nm, p, price):
            dn = D[nm]
            return (p["notional"] * p["d"] * (price - p["entry"]) / p["entry"]
                    - dn["cost"] * p["notional"] - dn["fin"] * p["notional"] * p["rolls"])
        def close_all_at_close():
            t = st["t"]; pnl = 0.0
            for nm, p in list(pos.items()):
                c = D[nm]["C"][t]
                if c != c: c = p["last"]
                pnl += settle(nm, p, c); del pos[nm]
            return pnl
        def step():
            t = st["t"]; pnl = 0.0
            for nm, p in list(pos.items()):
                dn = D[nm]
                if not dn["ok"][t]: continue
                if dn["roll"][t] and not p["new"]: p["rolls"] += 1
                d = p["d"]; o = dn["O"][t]
                if not p["new"] and (d * (o - p["sl"]) <= 0 or d * (o - p["tp"]) >= 0):
                    pnl += settle(nm, p, o); del pos[nm]; continue
                p["new"] = False
                if d > 0: hs = dn["L"][t] <= p["sl"]; ht = dn["H"][t] >= p["tp"]
                else:     hs = dn["H"][t] >= p["sl"]; ht = dn["L"][t] <= p["tp"]
                if hs or ht:
                    won = ht if not (hs and ht) else (rng.random() < p["l"] / (p["l"] + p["w"]))
                    pnl += settle(nm, p, p["tp"] if won else p["sl"]); del pos[nm]
                else:
                    p["last"] = dn["C"][t]
            return pnl
        def open_new(x, day_ref, target, risk):
            t = st["t"]
            used = sum(p["l"] for p in pos.values()); used_f = sum(p["l"] + p["fee"] for p in pos.values())
            room_cap = total_cap - used
            room_loss = min(x + dd - 25, dll - (day_ref - x) - 100) - used_f
            shared = next(iter(pos.values()))["d"] if (same_dir and pos) else None
            for nm in names:
                if nm in pos or not D[nm]["entry"][t]: continue
                dn = D[nm]; s = m * dn["sig"]
                l = min(risk, room_cap, (room_loss - 5) / (1 + dn["cost"] / s))
                if l < min_l: continue
                notional = l / s; fee_est = dn["cost"] * notional + 5
                w = k * l
                if target is not None:
                    rem = target - x - sum(q["w"] - q["fee"] for q in pos.values())
                    if combined and pos and rem < min_l: continue
                    w = min(w, max((rem if combined else target - x), 0) + fee_est)
                w = max(w, fee_est + 1)
                d = shared if shared is not None else (1 if rng.random() < 0.5 else -1)
                if same_dir and shared is None: shared = d
                e = dn["O"][t]; tg = s * w / l
                pos[nm] = dict(d=d, entry=e, sl=e * (1 - d * s), tp=e * (1 + d * tg), l=l, w=w,
                               notional=notional, rolls=0, fee=fee_est, new=True, last=e)
                st["trades"] += 1
                room_cap -= l; room_loss -= l + fee_est
        def equity_open():
            t = st["t"]; e = 0.0
            for nm, p in pos.items():
                c = D[nm]["C"][t]
                if c != c: c = p["last"]
                e += settle(nm, p, c)
            return e
        def adv():
            st["t"] += 1
            if st["t"] >= T:      # wrap: close everything at the last close, restart the data
                st["t"] -= 1; pnl = close_all_at_close(); st["t"] = 0; return pnl
            return 0.0
        def dead(x):
            return (not pos) and (x + dd - 30 < min_l * 1.01)
        hours = 0
        for (A, mind, review) in phases:
            x = 0.0; cur = day[st["t"]]; day_ref = 0.0; tdays = set()
            while True:
                if day[st["t"]] != cur: cur = day[st["t"]]; day_ref = x
                open_new(x, day_ref, A, per_trade)
                if pos: tdays.add(day[st["t"]])
                x += step()
                if x >= A or (combined and pos and x + equity_open() >= A):
                    x += close_all_at_close()
                    if x >= A:
                        hours += 1 + (max(0, mind - len(tdays)) + review) * 24
                        st["passed"] += 1; x += adv()
                        break
                if x <= -dd or dead(x) or hours > max_days * 24:
                    pos.clear()
                    return -fee, hours / 24, None, 0, st["passed"], st["trades"]
                x += adv(); hours += 1
        x = 0.0; paid = 0.0; npay = 0; next_pay = hours + cycle * 24; tfirst = None
        cur = day[st["t"]]; day_ref = 0.0; waiting = False
        fr = funded_risk or per_trade
        while x > -dd and npay < 100 and hours < max_days * 24:
            if day[st["t"]] != cur: cur = day[st["t"]]; day_ref = x
            eligible = hours >= next_pay
            if eligible and x > 0 and not pos:          # request the payout as soon as flat after the date
                paid += split * x + (fee if npay == 0 else 0); npay += 1; x = 0.0; day_ref = 0.0
                if tfirst is None: tfirst = hours / 24 + 1
                waiting = False; next_pay = hours + cycle * 24; eligible = False
            tgt = X1 if npay == 0 else X
            if not waiting and not (eligible and x > 0): open_new(x, day_ref, tgt, fr)
            x += step()
            if not waiting and (x >= tgt or (combined and pos and x + equity_open() >= tgt)):
                x += close_all_at_close(); waiting = x >= tgt
            if not waiting and dead(x): break
            x += adv(); hours += 1
        return -fee + paid, hours / 24, tfirst, npay, st["passed"], st["trades"]
    res = [attempt() for _ in range(n)]
    ev = np.array([r[0] for r in res]); dd_ = np.array([r[1] for r in res])
    tf = [r[2] for r in res if r[2] is not None]
    return dict(tag=tag, data=data, rho=rho, names=names, m=m, k=k, per_trade=per_trade, total_cap=total_cap,
                same_dir=same_dir, n=n, X1=X1, X=X, funded_risk=funded_risk, fee=fee, combined=combined,
                EV=float(ev.mean()), CI=float(1.96 * ev.std() / math.sqrt(n)), days=float(dd_.mean()),
                EV_month=float(ev.mean() / (dd_.mean() / 30.44)),
                EV_month_CI=float(1.96 * ev.std() / math.sqrt(n) / (dd_.mean() / 30.44)),
                Ppaid=len(tf) / n, t_first_med=float(np.median(tf)) if tf else None,
                payouts_mean=float(np.mean([r[3] for r in res])),
                pass_by_phase=[float(np.mean([r[4] >= j + 1 for r in res])) for j in range(len(phases))],
                trades_mean=float(np.mean([r[5] for r in res])))

if __name__ == "__main__":
    cfg = json.loads(sys.argv[1])
    out = cfg.pop("out", "multi_results.jsonl")
    r = run(**cfg)
    print(json.dumps(r))
    with open(out, "a") as f: f.write(json.dumps(r) + "\n")
