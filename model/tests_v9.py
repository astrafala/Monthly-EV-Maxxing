"""
Version 9 rule tests: each mechanism of the engine checked directly (python3 tests_v9.py). Writes tests_v9.json; every
check must print PASS. Version 8's checks carried over (on the version 9 engine), and new ones for the corrections of the
review of version 8:
  dll            the day's loss allowance: 'rel', 'fixed', 'min'
  terminal       every failed phase ends exactly at the floor, through a breach of the floor barrier (no clipping)
  near_floor     the review's witness: one micro contract with $100 left above the floor, the price first $110 against
                 the position, then $255 for it: the account breaches (version 8 returned a $255 win)
  min_lot        a 0.01-lot trade whose stop is beyond the floor: the floor is the barrier; mean result 0 without costs
  lots           volumes are whole steps (0.01 lot, one contract), never above the planned risk on a normal trade
  bridge         the error bound G(r) of the path generator: closed form against numerical integration, the review's
                 counterexample, and the exact two-barrier law against the bound on random configurations
  filler         filler trades are real positions: 0.01 lot, 3 minutes, with their result in the balance
  no_filler      no filler trade at Fintokei or Alpha Capital
  hold           Blue Guardian: no trade shorter than 2 minutes (the bracket is placed after 3 minutes)
  brightfunded   every counted BrightFunded trading day has a trade held at least one minute
  alpha_rule     the duration rule's three conditions on constructed trade lists
  hola_window    the review's witness: profitable days 0, 22 and 23 never make a bi-weekly Hola Prime payout
  fintokei_clock the next Fintokei request comes at least 14 days after the previous payout was processed
  bdays          a three-working-day review that starts on a Friday ends on the next Wednesday
  wallet         finite budgets: the cash dated by every ledger row never falls below zero (the review's witness life)
  exposure       a copied direction always comes from a position still open (by its exit time), never a closed one
  gap            at least 10 minutes between an exit and the next entry
  target         no take-profit closer than 0.6 hourly sd to the entry
  clock          the first payout is never requested before first_payout days after the first funded trade
  maven          funded profit never above $4,900; closed profit (dated by the close) in any 30 days never above $10,000
  alpha_days     no first Alpha payout before 5 distinct trading days on the funded account
  futures        a micro contract's value follows the path's price level
  streams        two markets of the same path number are independent
  day            every day's loss within the firm's allowance and profit within the day caps, by each trade's entry day
  fxify          at every FXIFY payout the best calendar day so far is at most 25% of it
  no_stall       the engine's stall detector never fires
  t_quantile     the Student quantiles used by the intervals
"""
import json, math, random, sys, copy, collections
import numpy as np
import acct_mc as A, pathfirm as PF, optimize_v9 as O, multi, lockstep as LS, firms_v9 as F9

OUT = {}
def check(name, ok, info=""):
    OUT[name] = dict(ok=bool(ok), info=info)
    print(("PASS " if ok else "FAIL ") + name, info, flush=True)

def cfg(prog, firm, instr, m, k, x, lf=0.0175, size=100_000):
    return dict(prog=prog, firm=firm, instr=instr, m=m, k=k, X1=O.x1_of(firm, x, size), X=x * size, L=lf * size, size=size)

# ---------------------------------------------------------------- dll
check("dll_rel", abs(A._dll_at(4000, "rel", 100_000, -6000) - 3760) < 1e-9, "FundingPips at $94,000: allowance $3,760")
check("dll_fixed", abs(A._dll_at(4000, "fixed", 100_000, -6000) - 4000) < 1e-9, "Blue Guardian: $4,000 at any balance")
check("dll_min", abs(A._dll_at(5000, "min", 100_000, 8000) - 5000) < 1e-9 and abs(A._dll_at(5000, "min", 100_000, -8000) - 4600) < 1e-9,
      "FunderPro: the stricter of the two")

# ---------------------------------------------------------------- t quantiles
ref = {3: 3.182446305284, 15: 2.131449545560, 23: 2.068657610419, 25: 2.059538552753}
check("t_quantile", all(abs(O.tq(k) - v) < 1e-9 for k, v in ref.items()),
      "97.5% quantiles for 3, 15, 23, 25 degrees of freedom: " + ", ".join(f"{O.tq(k):.6f}" for k in ref))

# ---------------------------------------------------------------- bridge bound
def exact_both(a, b, W, v, K=60):
    """P(a Brownian bridge from a to b over variance v touches both 0 and W): the image series"""
    stay = 0.0
    for k in range(-K, K + 1):
        stay += math.exp(-2 * k * W * (k * W - (b - a)) / v) - math.exp(-2 * (a - k * W) * (b - k * W) / v)
    pl = math.exp(-2 * a * b / v); pu = math.exp(-2 * (W - a) * (W - b) / v)
    return pl + pu - (1 - stay), pl * pu
bt, pi = exact_both(0.01, 0.99, 1.0, 0.01)
def G_num(r):
    d = np.linspace(-r - 12, r + 12, 400001)
    g = np.where(np.abs(d) <= r, np.minimum(1.0, 3 * np.exp(-(r * r - d * d))), 1.0) * np.exp(-d * d / 2) / math.sqrt(2 * math.pi)
    return float(np.trapz(g, d)) if hasattr(np, "trapz") else float(np.trapezoid(g, d))
errs = [abs(PF.bridge_err(r) / G_num(r) - 1) for r in (2.0, 4.0, 6.0, 8.0)]
rng = random.Random(3); worst = 0.0
for _ in range(4000):
    v = 10 ** rng.uniform(-2.0, -0.3); a = rng.uniform(0.02, 0.98); b = rng.uniform(0.02, 0.98)
    bt_, pi_ = exact_both(a, b, 1.0, v)
    bound = math.exp(-2 * (a * b + 1.0 * (1.0 - b)) / v) + math.exp(-2 * ((1 - a) * (1 - b) + 1.0 * b) / v)
    worst = max(worst, bt_ - bound)
check("bridge", abs(bt - math.exp(-4)) < 1e-9 and abs(pi - 0.019063114291) < 1e-9 and max(errs) < 1e-4 and worst < 1e-12,
      f"review's counterexample: exact both-touch {bt:.10f}, independent {pi:.10f} (version 8's bound 3.7e-44); closed form "
      f"against integration: largest relative difference {max(errs):.1e}; exact law minus the strong-Markov bound on 4,000 "
      f"random bridges: at most {worst:.1e}")

# ---------------------------------------------------------------- controlled markets
def ctl_market(instr, lp, norm=True, sig=0.0027):
    """a market following the given log-price sub-step closes exactly (60 per hour, straight moves inside each minute),
    every hour open and a permitted entry, weekdays only"""
    sub = 60; lp = np.asarray(lp, float); n = (len(lp) - 1) // sub
    lp = lp[:n * sub + 1]
    a, b = lp[:-1], lp[1:]
    sH = 100.0 * np.exp(np.maximum(a, b)); sL = 100.0 * np.exp(np.minimum(a, b)); sC = 100.0 * np.exp(b)
    O_ = 100.0 * np.exp(lp[:-1][::sub]); C_ = 100.0 * np.exp(lp[sub::sub])
    H_ = sH.reshape(n, sub).max(1); L_ = sL.reshape(n, sub).min(1)
    return dict(O=O_.tolist(), H=H_.tolist(), L=L_.tolist(), C=C_.tolist(), ok=[True] * n, entry=[True] * n,
                roll=[False] * n, sig=sig, cost=0.0, fin=0.0, fri_late=[False] * n, fri_close=[False] * n, T=n, h0=0,
                hour=[h % 24 for h in range(n)], wd=[(h // 24) % 5 for h in range(n)], norm=norm, instr=instr,
                sH=sH, sL=sL, sC=sC, sub=sub)

# near-floor witness (review of version 8, reproduction details): one MNQ contract at 100 has notional 2 x 31,070
uv = 2 * 31070.0; lp = [0.0, math.log(1 - 110 / uv), math.log(1 + 255 / uv)] + [math.log(1 + 255 / uv)] * 200
Mn = ctl_market("MNQ_fut", lp)
s_ = 170.0 / uv
pnl, hrs, info = PF.resolve(Mn, 0, 1, 100.0, 255.0, s_, 0.0, False, None, random.Random(1),
                            opts=dict(breach=100.0, terminal=True, keep_w=True))
pnl8, _, info8 = PF.resolve(Mn, 0, 1, 170.0, 255.0, s_, 0.0, False, None, random.Random(1), opts=dict(keep_w=True))
check("near_floor", info["breach"] and abs(pnl + 100.0) < 1e-9 and abs(pnl8 - 255.0) < 1e-6,
      f"$100 above the floor, one contract (risk $170 at the plan's stop): result {pnl:+.2f} (breach), against {pnl8:+.2f} "
      f"without the floor barrier (version 8)")

# min-lot witness: room $0.50, a 0.01-lot trade whose plan stop risks more; no costs: mean result 0, breach at -$0.50
rng = random.Random(7); means = []; lows = []; nb = 0
for pth in ("synth902y4", "synth903y4", "synth904y4", "synth905y4"):
    d0 = PF.free_market("US100", pth); M0 = PF.market("US100", d0); res = []
    for t in range(10000):
        i, _ = PF.entry_index(M0, rng.randrange(M0["T"] - 2000), False, 20)
        p, h, inf = PF.resolve(M0, i, 1 if rng.random() < .5 else -1, 0.5, 8.0, 1.0 * M0["sig"], 0.0, False, 20, rng,
                               opts=dict(breach=0.5, terminal=True, keep_w=True))
        res.append(p); nb += inf["breach"]
    means.append(np.mean(res)); lows.append(min(res))
mm = float(np.mean(means)); se = float(np.std(means, ddof=1) / 2.0)
check("min_lot", abs(mm) < O.tq(3) * se + 1e-9 and min(lows) >= -0.5 - 1e-9 and nb > 0,
      f"40,000 trades on 4 paths: mean {mm:+.4f} (path-cluster s.e. {se:.4f}; version 8's clipped payoff: +0.44), lowest "
      f"{min(lows):+.2f}, {nb} breaches at exactly -$0.50")

# lots: whole steps, never above the planned risk
M1 = PF.market("XAUUSD", "synth902y4"); rng = random.Random(8); bad = 0; n_ = 0
for t in range(3000):
    i, _ = PF.entry_index(M1, rng.randrange(M1["T"] - 2000), False, 20)
    l = rng.uniform(5, 2000); s1 = 0.75 * M1["sig"]
    p, h, inf = PF.resolve(M1, i, 1, l, 3 * l, s1, M1["cost"], False, 20, rng, opts=dict(breach=1e9))
    v = inf["vol"]; n_ += 1
    if abs(v * 100 - round(v * 100)) > 1e-6 or (v > 0.01 + 1e-9 and inf["notional"] * s1 > l + 1e-6): bad += 1
check("lots", bad == 0, f"{n_} gold trades: volumes in 0.01-lot steps, risk at the stop never above the planned risk ({bad} exceptions)")

# ---------------------------------------------------------------- instrumented trader
class Spy(PF.PathTrader):
    """records every trade with the resolver's description of it"""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.log = []
    def trade(self, l, w, clock=None, flat_weekend=False, opts=None):
        i, waited = PF.entry_index(self.M, self._idx(PF.next_bar(clock)), flat_weekend, self.flat_daily)
        pnl, h = super().trade(l, w, clock, flat_weekend, opts)
        self.log.append(dict(t_in=self.last_entry, t_out=self.last_exit, t_next=clock + h, l=l, w=w, pnl=pnl, i=i,
                             exit_bar=self.st.last_exit, kind=(opts or {}).get("kind", "trade"), **self.last_info))
        return pnl, h

def spy_attempts(c, n, data="synth901y4", seed=3):
    F = O.firm_rules(c); rng = random.Random(seed); recs = []
    for _ in range(n):
        tr = Spy(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
        clock = rng.random() * A.DAY; ends = []
        A.TRADELOG = []
        for st in F["phases"]:
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            ends.append((ok, clock))
            if not ok: break
        res = dict(log=tr.log, ends=ends, F=F, funded=None)
        if all(o for o, _ in ends):
            A.PAYLOG = []
            paid, c2, tf, npay = A.run_funded(F["funded"], tr, rng, F, clock, c["X1"], c["X"])
            res["funded"] = dict(t0=clock, paid=paid, end=c2, npay=npay, pays=list(A.PAYLOG))
            A.PAYLOG = None
        res["tlog"] = A.TRADELOG; A.TRADELOG = None
        recs.append(res)
    return recs

# ---------------------------------------------------------------- terminal: failures end exactly at the floor
c = cfg("FTMO 2-Step", "FTMO", "US100", 0.75, 8, 0.2, 0.015)
recs = spy_attempts(c, 300)
xs_fail = []
for r in recs:
    if not r["ends"][0][0]:
        t_end = r["ends"][0][1]
        xs_fail.append(sum(t["pnl"] for t in r["log"] if t["t_in"] < t_end))
xf = np.array(xs_fail); B = 10_000
check("terminal_floor", len(xf) > 50 and np.all(np.abs(xf + B) < 1e-6),
      f"{len(xf)} phase-1 failures; end P&L between {xf.min():.6f} and {xf.max():.6f} (floor -{B}): each a breach of the floor "
      f"barrier, nothing clipped")

# ---------------------------------------------------------------- gap: next entry at least 10 minutes after the exit
M = PF.market("US100", "synth901y4")
gmin = 1e9; tot = 0
for r in recs:
    for a, b in zip(r["log"], r["log"][1:]):
        g = (b["t_in"] - a["t_out"]) * 60.0; tot += 1; gmin = min(gmin, g)
check("gap_rule", gmin >= PF.GAP_MIN - 1e-6, f"{tot} consecutive trades: shortest time from an exit to the next entry {gmin:.1f} minutes")

# ---------------------------------------------------------------- target distance
cnt = 0; small = 0
for r in recs:
    for t in r["log"]:
        if t["kind"] == "filler" or t.get("why") == "breach" and t.get("td") is None: continue
        cnt += 1
        if t["td"] < PF.WMIN_SD - 1e-6: small += 1
check("target_distance", small == 0, f"{cnt} trades, {small} with a take-profit closer than {PF.WMIN_SD} sd")

# ---------------------------------------------------------------- fillers are real trades
fl = [t for r in recs for t in r["log"] if t["kind"] == "filler"]
ok_f = all(abs(t["dur"] - 3.0) < 1e-9 or t["breach"] for t in fl) and all(abs(t["vol"] - 0.01) < 1e-12 for t in fl)
nz = sum(abs(t["pnl"]) > 0 for t in fl)
# the review's witness: 200 FTMO phase-1 attempts at the chosen settings on synth901y4 with Random(19017)
Fw = O.firm_rules(cfg("FTMO 2-Step", "FTMO", "US100", 0.75, 8, 0.2, 0.015)); rw = random.Random(19017); nfw = 0; pw = 0.0
for _ in range(200):
    tr = PF.PathTrader("US100", "synth901y4", 0.75, 1500, 8, rw, 1.0, "random", Fw.get("flat_daily"))
    A.run_stage(Fw["phases"][0], tr, rw, Fw, rw.random() * 24)
    nfw += tr.st.fillers; pw += tr.st.filler_pnl
check("filler_trades", len(fl) > 0 and ok_f and nz == len(fl) and nfw > 0,
      f"{len(fl)} filler trades: every one 0.01 lot held 3 minutes, {nz} with a result in the balance (total "
      f"{sum(t['pnl'] for t in fl):+.2f}); the review's witness (200 attempts, Random(19017)): {nfw} filler trades, "
      f"total result {pw:+.2f}")

# ---------------------------------------------------------------- no fillers at Fintokei and Alpha Capital
nf = 0; ntr = 0
for prog, firm in (("Fintokei ProTrader", "Fintokei"), ("Alpha Capital Pro 10%", "Alpha Capital")):
    R = spy_attempts(cfg(prog, firm, "US100", 1.0, 6, 0.1), 200, seed=12)
    nf += sum(t["kind"] == "filler" for r in R for t in r["log"]); ntr += sum(len(r["log"]) for r in R)
check("no_filler", nf == 0, f"{ntr} trades at Fintokei and Alpha Capital, {nf} filler trades")

# ---------------------------------------------------------------- Blue Guardian: nothing under 2 minutes
R = spy_attempts(cfg("Blue Guardian 2-Step", "Blue Guardian", "US100", 0.6, 3, 0.1), 300, seed=13)
tl = [t for r in R for t in r["log"]]
short = [t for t in tl if t["dur"] < 2.0 - 1e-9 and not t["breach"]]
holdc = sum(t["why"] == "hold" for t in tl)
check("hold_bg", len(short) == 0 and min(t["dur"] for t in tl if not t["breach"]) >= 3.0 - 1e-9,
      f"{len(tl)} Blue Guardian trades at a 0.6 sd stop: none under 2 minutes except breaches, shortest {min(t['dur'] for t in tl if not t['breach']):.0f} "
      f"minutes; {holdc} closed at the end of the 3-minute hold")

# ---------------------------------------------------------------- BrightFunded: counted days have a trade of >= 1 minute
R = spy_attempts(cfg("BrightFunded 2-Step Classic", "BrightFunded", "US100", 0.6, 3, 0.1), 300, seed=14)
viol = 0; npass = 0
for r in R:
    t0 = 0.0
    for j, (ok, t_end) in enumerate(r["ends"]):
        if not ok: break
        npass += 1
        days = {int(t["t_in"] // A.DAY) for t in r["log"] if t0 <= t["t_in"] < t_end and t["dur"] >= 1.0}
        if len(days) < 5: viol += 1
        t0 = t_end
check("brightfunded_day", npass > 50 and viol == 0, f"{npass} BrightFunded phase passes, {viol} with fewer than 5 days holding a trade >= 60 s")

# ---------------------------------------------------------------- Alpha's duration rule
ok1 = A._dur_ok(2.0, [(3, 10), (5, -5), (2.5, 20)])
ok2 = not A._dur_ok(2.0, [(1, 100), (1, 50), (10, 10)])          # most trades short
ok3 = not A._dur_ok(2.0, [(1, 100), (5, 10), (5, 10)])           # most profit from a short trade
ok4 = not A._dur_ok(2.0, [(0.5, 1), (0.5, 1), (5.5, 1)])        # average 2.17 but most trades short
check("alpha_rule", ok1 and ok2 and ok3 and ok4, "average, majority and half-of-gross-profit conditions on constructed trade lists")

# ---------------------------------------------------------------- Hola Prime: 3 profitable days within 14 days
class Planned:
    """a trader with one permitted trade per weekday at 01:00 (engine day), results planned by day"""
    def __init__(self, plan, stop_day, L=1750.0, k=3.0):
        self.plan = plan; self.stop_day = stop_day; self.L = L; self.k = k; self.rho = 0.0; self.wmin_frac = 0.0; self.s = 0.001
        self.done = set(); self.last_entry = None; self.last_exit = None; self.last_info = None; self.trades = 0
    def lmin_at(self, clock, fw=False): return 1.0
    def bdays(self, clock, n): return clock + n * 24.0
    def next_entry(self, clock, fw=False):
        d = int(clock // 24); h = clock - d * 24
        if h <= 1.0: return d * 24 + 1.0
        if h < 18.0: return clock
        return (d + 1) * 24 + 1.0
    def trade(self, l, w, clock, fw=False, opts=None):
        te = self.next_entry(clock); d = int(te // 24)
        if d >= self.stop_day: pnl = -1e9
        elif d in self.done: pnl = 0.0
        else: pnl = self.plan.get(d, 0.0); self.done.add(d)
        self.last_entry = te; self.last_exit = te + 1.0; self.last_info = dict(dur=60.0, breach=pnl <= -1e8)
        self.trades += 1
        return pnl, (te - clock) + 19.0
Fh = F9.rules_for("Hola Prime 2-Step Prime (bi-weekly 80%)")
A.PAYLOG = []
paid, c2, tf, npay = A.run_funded(Fh["funded"], Planned({0: 550.0, 22: 550.0, 23: 550.0}, 60), random.Random(1), Fh, 0.0, 15000, 15000)
pays_h = list(A.PAYLOG); A.PAYLOG = []
paid2, _, _, npay2 = A.run_funded(Fh["funded"], Planned({15: 550.0, 22: 550.0, 23: 550.0}, 60), random.Random(1), Fh, 0.0, 15000, 15000)
A.PAYLOG = None
check("hola_window", npay == 0 and npay2 >= 1,
      f"profitable days 0, 22, 23: {npay} payouts (version 8 paid $1,469.75 on day 23.8); days 15, 22, 23 (inside 14 days): {npay2}")

# ---------------------------------------------------------------- Fintokei: 14 days from the processed payout
c = cfg("Fintokei ProTrader", "Fintokei", "US100", 1.0, 6, 0.05)
R = spy_attempts(c, 400, seed=15)
gaps_f = []
for r in R:
    f = r["funded"]
    if not f or len(f["pays"]) < 2: continue
    for (tc0, _, tr0), (tc1, _, tr1) in zip(f["pays"], f["pays"][1:]):
        gaps_f.append(tr1 - tc0)
check("fintokei_clock", len(gaps_f) > 20 and min(gaps_f) >= 14 * 24 - 1e-6,
      f"{len(gaps_f)} later Fintokei requests: shortest time from the previous payout's processing {min(gaps_f) / 24:.2f} days")

# ---------------------------------------------------------------- working days
tr = PF.PathTrader("US100", "synth901y4", 1.0, 1500, 3, random.Random(2), flat_daily=20)
fri = next(t for t in range(24 * 14) if tr.M["wd"][tr._idx(t)] == 4 and tr.M["hour"][tr._idx(t)] == 15)
e3 = A._bdays(tr, fri, 3); e1 = A._bdays(tr, fri, 1)
check("bdays", tr.M["wd"][tr._idx(e3)] == 2 and abs(e3 - fri - 5 * 24) < 1e-9 and tr.M["wd"][tr._idx(e1)] == 0,
      f"3 working days after Friday 15:00 UTC: {(e3 - fri) / 24:.0f} calendar days later (Wednesday); 1 working day: Monday")

# ---------------------------------------------------------------- wallet: dated cash never negative
LS.RULES = F9
def slot(prog, instr, n, m, k, x, lf=0.015, size=100_000):
    firm = F9.firm_of(prog)
    return [dict(firm=prog, kind="cfd", size=size, L=lf * size, k=k, X1=O.x1_of(firm, x, size), X=x * size, m=m, instr=instr,
                 lev=O.lev_tuple(firm, instr)) for _ in range(n)]
SL = (slot("FTMO 2-Step", "US100", 4, 0.75, 8, 0.2) + slot("FundingPips 2-Step Flex (95%)", "USDJPY", 4, 1.0, 6, 0.1) +
      slot("The5ers High Stakes", "US100", 1, 1.0, 6, 0.1) + slot("Fintokei ProTrader", "US100", 5, 1.0, 6, 0.1) +
      slot("Blue Guardian 2-Step", "US100", 1, 1.0, 4, 0.08))
worst = 1e18; lows = []; nbuy = 0
for seed in (100016, 100031, 100125):
    for budget in (10_000, 30_000):
        led, st = LS.run_life(SL, data=f"synth{seed}y2", months=12, seed=seed, rule="trend5", budget=budget)
        led.sort(key=lambda r: r[0]); cash = float(budget); low = cash
        for row in led:
            if row[0] > 12 * 30.44 * 24: break
            cash += row[3]; low = min(low, cash)
        nbuy += sum(r[2] == "buy" for r in led)
        worst = min(worst, low); lows.append((low, st["wallet_low"]))
check("wallet", worst >= -1e-6 and all(abs(a - b) < 1e-6 or a >= b - 1e-6 for a, b in lows),
      f"6 lives with $10,000 and $30,000 budgets ({nbuy} purchases): lowest cash dated by the ledger ${worst:,.2f}")

# ---------------------------------------------------------------- exposure: copies only from open positions
led, st = LS.run_life(SL, data="synth100016y2", months=12, seed=100016, rule="trend5")
tlog = st["trade_log"]; bad = 0; ncopy = 0
opn = []
for (te, sid, d, tx, copied, grp) in tlog:
    opn = [p for p in opn if p[1] > te]
    same = [p for p in opn if p[3] == grp]
    if copied:
        ncopy += 1
        if not same or any(p[2] != d for p in same): bad += 1
    elif same: bad += 1
    opn.append((te, tx, d, grp))
check("exposure", bad == 0 and ncopy > 0 and st["conflicts"] == 0,
      f"{len(tlog)} trades in one life, {ncopy} copied a direction: every copy from a position still open at the entry, "
      f"every uncopied entry with nothing open ({bad} exceptions), {st['conflicts']} opposite positions")

# ---------------------------------------------------------------- payout clock, Alpha's days, Maven's caps
viol = 0; npays = 0; vk = {}
def bad_(kind):
    global viol
    viol += 1; vk[kind] = vk.get(kind, 0) + 1
for prog, firm, instr, m, k, x in [("FTMO 2-Step", "FTMO", "US100", 0.75, 8, 0.1), ("Alpha Capital Pro 10%", "Alpha Capital", "US100", 1.0, 6, 0.1),
                                   ("Maven 2-Step", "Maven", "US100", 1.25, 4, 0.049), ("Fintokei ProTrader", "Fintokei", "US100", 1.0, 10, 0.1)]:
    c = cfg(prog, firm, instr, m, k, x)
    R = spy_attempts(c, 400, seed=11)
    for r in R:
        f = r["funded"]
        if not f or not f["pays"]: continue
        first_trade = min(t["t_in"] for t in r["log"] if t["t_in"] >= f["t0"] - 1e-9)
        fp = r["F"]["funded"]["first_payout"]
        t_req = f["pays"][0][2]
        npays += 1
        if t_req < first_trade + fp * A.DAY - 1e-6: bad_("clock")
        if prog == "Alpha Capital Pro 10%":
            ddays = {int(t["t_in"] // A.DAY) for t in r["log"] if f["t0"] - 1e-9 <= t["t_in"] < t_req}
            if len(ddays) < 5: bad_("alpha_days")
        if prog == "Maven 2-Step":
            fl_ = [t for t in r["log"] if t["t_in"] >= f["t0"] - 1e-9]
            reqs = [p[2] for p in f["pays"]]
            xx = 0.0; ri = 0
            for t in fl_:
                while ri < len(reqs) and reqs[ri] <= t["t_in"] + 1e-9: xx = 0.0; ri += 1
                xx += t["pnl"]
                if xx > 4_900 + 1e-6: bad_("maven_ceiling")
            for t in fl_:
                win = sum(u["pnl"] for u in fl_ if t["t_out"] - 30 * A.DAY < u["t_out"] <= t["t_out"])
                if win > 10_000 + 1.0: bad_("maven_30d")
check("payout_clock_alpha_maven", viol == 0, f"{npays} first payouts checked (clock from the first trade; Alpha's 5 days; "
      f"Maven's ceiling and 30-day cap by close date): {viol} violations {vk}")

# ---------------------------------------------------------------- futures contract value follows the price
Mf = PF.market("MNQ_fut", "synth901y4")
Of = np.array(Mf["O"][:20000], dtype=float); i0 = int(np.flatnonzero(np.isfinite(Of))[0]); j = int(np.nanargmax(Of))
v0 = PF.unit_value(Mf, Of[i0]); v1 = PF.unit_value(Mf, Of[j])
check("futures_price", abs(v1 / v0 - Of[j] / Of[i0]) < 1e-12 and abs(v0 - 2 * 31070 * Of[i0] / 100) < 1e-9,
      f"contract value x{v1 / v0:.3f} where the price is x{Of[j] / Of[i0]:.3f}; at the start ${v0:,.0f} per 100% move")

# ---------------------------------------------------------------- streams
a = PF.market("US100", "synth901y4"); b = PF.market("USDJPY", "synth901y4")
ra = np.diff(np.log(np.array(a["C"][:5000], dtype=float))); rb = np.diff(np.log(np.array(b["C"][:5000], dtype=float)))
ok = np.isfinite(ra) & np.isfinite(rb)
corr = float(np.corrcoef(ra[ok], rb[ok])[0, 1])
k1 = multi.stream_key(["US100"], 0.0, 4, 60, 901); k2 = multi.stream_key(["USDJPY"], 0.0, 4, 60, 901)
check("streams", k1 != k2 and abs(corr) < 0.05, f"keys differ; hourly-return correlation {corr:+.3f}")

# ---------------------------------------------------------------- daily limits, by the day each trade opened
def day_limits(c, n, data="synth901y4", seed=8):
    F = O.firm_rules(c); rng = random.Random(seed); worst = dict(loss=-1e18, profit=-1e18, daycap=-1e18); days = 0
    def check_days(log, st, cap_day, dcap=None):
        nonlocal days
        by = {}
        for (tag, te, xb, pnl, tx, kind, dur) in log: by.setdefault(int(te // A.DAY), []).append((xb, pnl))
        for d, tl in by.items():
            days += 1; run = 0.0; low = 0.0
            for xb, pnl in tl: run += pnl; low = min(low, run)
            if st.get("dll") and not st.get("dll_trailing"):
                worst["loss"] = max(worst["loss"], -low - A._dll_at(st["dll"], A._mode(st), F["size"], tl[0][0]))
            if cap_day: worst["profit"] = max(worst["profit"], run - cap_day)
            if dcap: worst["daycap"] = max(worst["daycap"], run - dcap)
    for _ in range(n):
        tr = PF.PathTrader(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
        clock = rng.random() * A.DAY; ok = True
        for st in F["phases"]:
            A.TRADELOG = []
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            caps = [v for v in (st.get("best") and st["best"] * st["target"], st.get("conc") and st["conc"] * st["target"]) if v]
            check_days(A.TRADELOG, st, min(caps) if caps else None)
            if not ok: break
        if ok:
            A.TRADELOG = []
            A.run_funded(F["funded"], tr, rng, F, clock, c["X1"], c["X"])
            check_days(A.TRADELOG, F["funded"], None, F["funded"].get("day_profit_cap"))
        A.TRADELOG = None
    return worst, days
DL = {}
for prog, firm, markets, xs in O.PROGS:
    lf = 0.015 if firm == "FTMO" else 0.0175
    x = 0.04 if firm == "Maven" else (0.06 if firm == "GFT" else 0.10)
    m = max(O.m_grid(firm, markets[0], lf)[0], 1.0)
    w, nd = day_limits(cfg(prog, firm, markets[0], m, 6, x, lf), 120)
    DL[prog] = (w, nd)
wl = max(v[0]["loss"] for v in DL.values()); wp = max(v[0]["profit"] for v in DL.values()); wd = max(v[0]["daycap"] for v in DL.values())
nd = sum(v[1] for v in DL.values())
check("day_limits", wl <= 1e-6 and wp <= 1.0 and wd <= 1.0,
      f"{nd:,} account-days of {len(DL)} programmes, days from each trade's entry: largest day loss beyond the firm's allowance "
      f"{wl:+.2f}, largest day profit beyond the plan's 40% cap {wp:+.2f}, beyond GFT's day cap {wd:+.2f} (all must be <= 0)")

# ---------------------------------------------------------------- FXIFY best day at every payout
def fxify_best(c, n, data="synth901y4", seed=9):
    F = O.firm_rules(c); rng = random.Random(seed); worst = -1e18; npay = 0
    for _ in range(n):
        tr = PF.PathTrader(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
        clock = rng.random() * A.DAY; ok = True
        for st in F["phases"]:
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            if not ok: break
        if not ok: continue
        A.TRADELOG = []
        A.run_funded(F["funded"], tr, rng, F, clock, c["X1"], c["X"])
        log = A.TRADELOG; A.TRADELOG = None
        days = {}
        for j, (tag, te, xb, pnl, tx, kind, dur) in enumerate(log):
            d = int(te // A.DAY); days[d] = days.get(d, 0.0) + pnl
            amt = (xb + pnl - log[j + 1][2]) if j + 1 < len(log) else 0.0
            if amt > 1.0:
                npay += 1; worst = max(worst, max(days.values()) - F["funded"]["best"] * amt)
    return worst, npay
fx = [fxify_best(cfg(p, "FXIFY", "US100", 1.07, 6, x), 150) for p in ("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY Two Phase Classic (80%)")
      for x in (0.10, 0.20)]
check("fxify_best_day", max(w for w, _ in fx) <= 1.0,
      f"{sum(k for _, k in fx)} FXIFY payouts: largest best calendar day beyond 25% of the payout {max(w for w, _ in fx):+.2f} (must be <= 0)")

# ---------------------------------------------------------------- no stalls
s0 = A.STUCK[0]
for prog, firm, instr, m, k, x in [("GFT 2-Step Standard", "GFT", "USDJPY", 0.6, 3, 0.04), ("Maven 2-Step", "Maven", "US100", 0.75, 8, 0.02),
                                   ("Maven 2-Step", "Maven", "US100", 1.25, 4, 0.049), ("Alpha Capital Pro 10%", "Alpha Capital", "US100", 1.0, 6, 0.05),
                                   ("Maven 2-Step", "Maven", "US100", 0.6, 6, 0.02), ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", "XAUUSD", 1.0, 6, 0.05),
                                   ("Fintokei ProTrader", "Fintokei", "US100", 1.0, 3, 0.05)]:
    spy_attempts(cfg(prog, firm, instr, m, k, x), 200, seed=21)
c10 = cfg("Maven 2-Step", "Maven", "US100", 0.75, 2, 0.049, lf=0.015); F10 = O.firm_rules(c10); r10 = random.Random(4)
for _ in range(500): PF.attempt(F10, "US100", "synth104", 0.75, c10["L"], 2, c10["X1"], c10["X"], r10)
check("no_stall", A.STUCK[0] == s0, f"{A.STUCK[0] - s0} stalled accounts in 1,900 attempts at settings where small caps meet the minimum target distance")

json.dump(OUT, open("tests_v9.json", "w"), indent=1)
print("all passed" if all(v["ok"] for v in OUT.values()) else "SOME FAILED")
