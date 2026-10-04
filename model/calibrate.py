"""
Per-instrument calibration on real hourly data.
For each instrument, stop size (multiple m of the hourly sigma) and reward:risk k,
sample random-direction brackets entered back-to-back at random allowed hours and measure:
  win rate (mid prices, before costs), mean calendar hours from entry to the NEXT possible
  entry (includes waiting through closed hours), and mean number of daily rollovers crossed.
"""
import json, math, random, sys
import numpy as np, pandas as pd

INSTR = {
  # name: file, round-trip cost % of price, overnight financing % of notional per rollover,
  #       allowed entry hours UTC (None = any), 24/7?
  "EURUSD": ("eurusd_1h.csv", 0.0062, 0.002, (7, 20)),
  "GBPUSD": ("gbpusd_1h.csv", 0.0076, 0.002, (7, 20)),
  "USDJPY": ("usdjpy_1h.csv", 0.0051, 0.002, (0, 20)),
  "XAUUSD": ("gold_1h.csv",   0.0108, 0.015, (1, 20)),
  "US100":  ("nq_1h.csv",     0.0064, 0.015, (1, 20)),
  "US500":  ("es_1h.csv",     0.0096, 0.015, (1, 20)),
  "BTC_FTMO": ("btc_1h.csv",  0.0930, 0.050, None),
  "ETH_FTMO": ("eth_1h.csv",  0.1050, 0.050, None),
  "BTC_Breakout": ("btc_1h.csv", 0.1000, 0.033, None),
  "BTC_Hyro": ("btc_1h.csv",  0.1200, 0.010, None),
  "MNQ_fut": ("nq_1h.csv",    0.0027, 0.000, (1, 20)),
}

def load(fn):
    d = pd.read_csv(fn, header=[0, 1], index_col=0)
    d.columns = [c[0] for c in d.columns]
    d.index = pd.to_datetime(d.index, utc=True)
    d = d.dropna()
    d = d[(d.High >= d.Low) & (d.Close > 0)]
    return d

class Market:
    def __init__(self, name):
        fn, self.cost, self.fin, hrs = INSTR[name]
        d = load(fn)
        self.O = d.Open.values; self.H = d.High.values; self.L = d.Low.values; self.C = d.Close.values
        self.t = ((d.index - pd.Timestamp("1970-01-01", tz="UTC")).total_seconds() / 3600.0).values
        hr = d.index.hour.values; wd = d.index.weekday.values
        self.N = len(d)
        if hrs is None:
            ok = np.ones(self.N, bool)
        else:
            ok = (hr >= hrs[0]) & (hr <= hrs[1]) & (wd < 5)
        self.entry_ok = np.where(ok)[0]
        r = np.log(self.C)
        gaps = np.diff(self.t)
        self.sig_h = float(np.std(np.diff(r)[gaps <= 1.01]))
        # rollover marker: 22:00 UTC for CFDs / 00:00 UTC crypto (count bars that start at that hour)
        self.roll = (hr == (0 if hrs is None else 22))
        self.span_h = self.t[-1] - self.t[0]

    def next_entry(self, i, rng=None):
        j = np.searchsorted(self.entry_ok, i)
        if j >= len(self.entry_ok): return None
        return int(self.entry_ok[j])

    def bracket(self, i0, d, s, tg, rng):
        """s, tg as fractions of entry price. returns (won, exit_index, rollovers)"""
        e = self.O[i0]
        if d > 0: sl, tp = e * (1 - s), e * (1 + tg)
        else:     sl, tp = e * (1 + s), e * (1 - tg)
        rolls = 0
        for i in range(i0, self.N):
            if i > i0 and self.roll[i]: rolls += 1
            if d > 0: hs = self.L[i] <= sl; ht = self.H[i] >= tp
            else:     hs = self.H[i] >= sl; ht = self.L[i] <= tp
            if hs and ht: return (rng.random() < s / (s + tg)), i, rolls   # unbiased tie-break
            if hs: return False, i, rolls
            if ht: return True, i, rolls
        return None, self.N, rolls

def calibrate(name, ms=(1, 1.5, 2, 3, 4, 6, 9), ks=(1, 2), n=8000, seed=1):
    mk = Market(name); rng = random.Random(seed)
    out = dict(name=name, sig_h=mk.sig_h, cost=mk.cost, fin=mk.fin, grid=[])
    for m in ms:
        s = m * mk.sig_h
        for k in ks:
            wins = 0; tot = 0; hours = []; rolls = []
            for _ in range(n):
                i = mk.entry_ok[rng.randrange(len(mk.entry_ok) - 300)]
                d = 1 if rng.random() < 0.5 else -1
                won, j, ro = mk.bracket(i, d, s, k * s, rng)
                if won is None: continue
                nxt = mk.next_entry(j + 1)
                if nxt is None: continue
                wins += won; tot += 1
                hours.append(mk.t[nxt] - mk.t[i]); rolls.append(ro)
            p = wins / tot; fair = 1 / (1 + k)
            kappa = mk.cost / s; phi = mk.fin * np.mean(rolls) / s
            e = p * (1 + k) - 1 - kappa - phi          # expected P&L per trade, units of risk
            out["grid"].append(dict(m=m, s=s, k=k, p=p, fair=fair, se=math.sqrt(p * (1 - p) / tot),
                                    hours=float(np.mean(hours)), hours_med=float(np.median(hours)),
                                    rolls=float(np.mean(rolls)), kappa=kappa, phi=phi, edge=e,
                                    dur=list(np.random.default_rng(seed).choice(hours, 400))))
            g = out["grid"][-1]
            print(f"{name:13s} m={m:<4} k={k} p={p:.4f} (fair {fair:.4f}) hrs={g['hours']:6.1f} "
                  f"kappa={kappa*100:5.2f}% fin={phi*100:5.2f}% edge/trade={e*100:+6.2f}%", flush=True)
    return out

if __name__ == "__main__":
    names = sys.argv[1:] or list(INSTR)
    for nm in names:
        json.dump(calibrate(nm), open(f"calib_{nm}.json", "w"), default=float)
