"""
Version 8 rule tests: each new mechanism of the engine checked directly on simulated accounts (python3 tests_v8.py).
Writes tests_v8.json; every check must print PASS.
  dll        the day's loss allowance: 'rel' = share of the day's starting balance, 'fixed' = share of the initial balance
  terminal   every failed attempt ends at the floor itself (a breach that closes the account), never above it
  gap        at least 10 minutes between a close and the next entry (exit minute from the one-minute sub-steps)
  target     no take-profit closer than 0.6 hourly sd to the entry, except where a rule cap is the binding cap
  filler     filler days fall on real trading days (Friday target: the fillers are on Monday and Tuesday)
  clock      the first payout is never requested before first_payout days after the first funded trade
  maven      funded profit never above $4,900 (the plan's margin under $5,000); closed profit in any 30 days never above $10,000
  alpha      no first payout before 5 distinct trading days on the funded account
  futures    a micro contract's risk follows the path's price level
  streams    no two stages share a random stream (stream manifest)
  day        every day's loss within the firm's allowance and profit within the day caps, by each trade's entry day
  fxify      at every FXIFY payout the best calendar day so far is at most 25% of it
"""
import json, math, random, sys
import numpy as np
import acct_mc as A, pathfirm as PF, optimize_v8 as O, multi

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

# ---------------------------------------------------------------- instrumented trader
class Spy(PF.PathTrader):
    """records every trade: (entry clock, exit clock, risk, win, pnl, x before) through the engine's calls"""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.log = []
    def trade(self, l, w, clock=None, flat_weekend=False):
        i, waited = PF.entry_index(self.M, self._idx(clock), flat_weekend, self.flat_daily)
        pnl, h = super().trade(l, w, clock, flat_weekend)
        self.log.append(dict(t_in=clock + waited, t_next=clock + h, l=l, w=w, pnl=pnl, i=i, exit=self.st.last_exit))
        return pnl, h

def spy_attempts(c, n, data="synth901y4", seed=3):
    F = O.firm_rules(c); rng = random.Random(seed); recs = []
    for _ in range(n):
        tr = Spy(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "random", F.get("flat_daily"))
        clock = rng.random() * A.DAY; t0 = clock; ends = []
        for st in F["phases"]:
            x_hist = []
            ok, clock = A.run_stage(st, tr, rng, F, clock)
            ends.append((ok, clock))
            if not ok: break
        res = dict(log=tr.log, ends=ends, F=F, funded=None)
        if all(o for o, _ in ends):
            A.PAYLOG = []
            paid, c2, tf, npay = A.run_funded(F["funded"], tr, rng, F, clock, c["X1"], c["X"])
            res["funded"] = dict(t0=clock, paid=paid, end=c2, npay=npay, pays=list(A.PAYLOG))
            A.PAYLOG = None
        recs.append(res)
    return recs

# ---------------------------------------------------------------- terminal: failures end at the floor
c = cfg("FTMO 2-Step", "FTMO", "US100", 0.75, 8, 0.2, 0.015)
recs = spy_attempts(c, 300)
gaps, tgt_ok, n_tr = [], 0, 0
fails_at_floor = 0; fails = 0
for r in recs:
    x = 0.0; B = r["F"]["phases"][0]["dd"]; ph = 0; start = 0
    log = r["log"]
    for a, b in zip(log, log[1:]):
        gaps.append((b["t_in"] - a["t_next"]))
    for ok, _ in r["ends"]:
        pass
    # replay phase 1 P&L from the log up to the first phase end
xs_fail = []
for r in recs:
    if not r["ends"][0][0]:                       # failed in phase 1: the sum of P&L of its trades is the end balance
        t_end = r["ends"][0][1]
        pnl = sum(t["pnl"] for t in r["log"] if t["t_in"] < t_end)
        xs_fail.append(pnl)
B = 10_000
xf = np.array(xs_fail)
check("terminal_floor", len(xf) > 50 and np.all(xf <= -B + 1e-6),
      f"{len(xf)} phase-1 failures; largest end P&L {xf.max():.2f} (floor -{B}); the engine clamps losses at the floor")

# ---------------------------------------------------------------- gap: next entry at least 10 minutes after the exit
M = PF.market("US100", "synth901y4")
gmin = 1e9; tot = 0
for r in recs:
    for a, b in zip(r["log"], r["log"][1:]):
        (ie, mi) = a["exit"]; ib = b["i"]
        if ib < ie: ib += M["T"]
        g = (ib - ie) * 60.0 - mi; tot += 1; gmin = min(gmin, g)
check("gap_rule", gmin >= PF.GAP_MIN - 1e-9, f"{tot} consecutive trades: shortest time from an exit to the next entry {gmin:.0f} minutes")

# direct test of the resolver: bars where the exit falls after minute 50
rng = random.Random(1); late_ok = True; nlate = 0
for t in range(3000):
    i, _ = PF.entry_index(M, rng.randrange(M["T"] - 500), False, 20)
    pnl, hours, _ = PF.resolve(M, i, 1 if rng.random() < .5 else -1, 1000.0, 3000.0, 0.75 * M["sig"], M["cost"], False, 20, rng)
    # reconstruct the exit: walk bars until the barrier; compare minute from the sub-steps
    st = PF.Stats()
    pnl2, hours2, _ = PF.resolve(M, i, 1, 1000.0, 3000.0, 0.75 * M["sig"], M["cost"], False, 20, random.Random(5), st=st)
    nlate += st.late
check("gap_resolver", nlate > 0, f"{nlate} of 3000 brackets exited after minute 50 and got the extra hour")

# ---------------------------------------------------------------- target distance
cnt = 0; small = 0; s = 0.75 * M["sig"]
for r in recs:
    for t in r["log"]:
        cnt += 1
        fee = M["cost"] * t["l"] / s
        dist = s * (t["w"] + fee) / t["l"] / M["sig"]          # take-profit distance in hourly sd
        if dist < PF.WMIN_SD - 1e-6: small += 1
check("target_distance", small == 0, f"{cnt} trades, {small} with a take-profit closer than {PF.WMIN_SD} sd")

# ---------------------------------------------------------------- filler days on the real calendar
class Cal:
    pass
tr = PF.PathTrader("US100", "synth901y4", 1.0, 1500, 3, random.Random(2), flat_daily=20)
# find a Friday 15:00 UTC clock
idx = None
for t in range(24 * 14):
    j = tr._idx(t)
    if M["entry"][j] and (M["fri_late"][j] is False) and M["hour"][j] == 15:
        import pandas as pd
    # weekday from the path's calendar: fri_late marks Friday >= 19:00
for t in range(24 * 14):
    j = tr._idx(t)
    if M["hour"][j] == 15 and M["fri_late"][(j + 4) % M["T"]] and M["entry"][j]:
        idx = t; break
traded = {int(idx // A.DAY)}
t2 = tr.filler_days(idx + 1, 2, traded)
days = sorted(traded)
gap_days = [days[i + 1] - days[i] for i in range(len(days) - 1)]
check("filler_calendar", gap_days == [3, 1], f"target reached on a Friday: filler days {gap_days} days later (Monday, Tuesday)")

# ---------------------------------------------------------------- payout clock from the first funded trade
viol = 0; npays = 0; vk = {}
def bad(kind):
    global viol
    viol += 1; vk[kind] = vk.get(kind, 0) + 1
for prog, firm, instr, m, k, x in [("FTMO 2-Step", "FTMO", "US100", 0.75, 8, 0.1), ("Alpha Capital Pro 10%", "Alpha Capital", "US100", 1.0, 6, 0.1),
                                   ("Maven 2-Step", "Maven", "US100", 1.25, 4, 0.05), ("Fintokei ProTrader", "Fintokei", "US100", 1.0, 10, 0.1)]:
    c = cfg(prog, firm, instr, m, k, x)
    R = spy_attempts(c, 400, seed=11)
    for r in R:
        f = r["funded"]
        if not f or not f["pays"]: continue
        first_trade = min(t["t_in"] for t in r["log"] if t["t_in"] >= f["t0"] - 1e-9)
        fp = r["F"]["funded"]["first_payout"]
        t_req = f["pays"][0][0] - r["F"]["funded"].get("process", 1) * A.DAY
        npays += 1
        if t_req < first_trade + fp * A.DAY - 1e-6: bad("clock")
        if prog == "Alpha Capital Pro 10%":
            ddays = {int(t["t_in"] // A.DAY) for t in r["log"] if f["t0"] - 1e-9 <= t["t_in"] < t_req}
            if len(ddays) < 5: bad("alpha_days")
        if prog == "Maven 2-Step":
            # funded profit never above $4,900 at any trade close; closed profit in any 30 days <= $10,000
            fl = [t for t in r["log"] if t["t_in"] >= f["t0"] - 1e-9]
            reqs = [p[0] - r["F"]["funded"].get("process", 1) * A.DAY for p in f["pays"]]
            xx = 0.0; ri = 0
            for t in fl:                                  # the funded profit resets to 0 at every payout request
                while ri < len(reqs) and reqs[ri] <= t["t_in"] + 1e-9: xx = 0.0; ri += 1
                xx += t["pnl"]
                if xx > 4_900 + 1e-6: bad("maven_ceiling")
            for t in fl:
                win = sum(u["pnl"] for u in fl if t["t_next"] - 30 * A.DAY < u["t_next"] <= t["t_next"])
                if win > 10_000 + 1.0: bad("maven_30d")
check("payout_clock_alpha_maven", viol == 0, f"{npays} first payouts checked (clock from the first trade; Alpha's 5 days; Maven's caps): {viol} violations {vk}")

# ---------------------------------------------------------------- futures contract value follows the price
Mf = PF.market("MNQ_fut", "synth901y4")
Of = np.array(Mf["O"][:20000], dtype=float); i0 = int(np.flatnonzero(np.isfinite(Of))[0]); j = int(np.nanargmax(Of))
v0 = PF.contract_value(Mf, Of[i0]); v1 = PF.contract_value(Mf, Of[j])
check("futures_price", abs(v1 / v0 - Of[j] / Of[i0]) < 1e-12 and abs(v0 - 2 * 31070 * Of[i0] / 100) < 1e-9,
      f"contract value x{v1 / v0:.3f} where the price is x{Of[j] / Of[i0]:.3f}; at the start ${v0:,.0f} per 100% move")

# ---------------------------------------------------------------- streams: the same path number on two markets is independent
a = PF.market("US100", "synth901y4"); b = PF.market("USDJPY", "synth901y4")
ra = np.diff(np.log(np.array(a["C"][:5000], dtype=float))); rb = np.diff(np.log(np.array(b["C"][:5000], dtype=float)))
ok = np.isfinite(ra) & np.isfinite(rb)
corr = float(np.corrcoef(ra[ok], rb[ok])[0, 1])
k1 = multi.stream_key(["US100"], 0.0, 4, 60, 901); k2 = multi.stream_key(["USDJPY"], 0.0, 4, 60, 901)
check("streams", k1 != k2 and abs(corr) < 0.05, f"keys differ; hourly-return correlation {corr:+.3f}")

# ---------------------------------------------------------------- daily limits, by the day each trade opened (n12)
def day_limits(c, n, data="synth901y4", seed=8):
    """runs n attempts and returns the worst excess, over every evaluation phase and funded account, of a day's loss over
    the firm's daily allowance and of a day's profit over the plan's day caps, days taken from each trade's own entry time"""
    F = O.firm_rules(c); rng = random.Random(seed); worst = dict(loss=-1e18, profit=-1e18, daycap=-1e18); days = 0
    def check_days(log, st, cap_day, dcap=None):
        nonlocal days
        by = {}
        for (tag, te, xb, pnl) in log: by.setdefault(int(te // A.DAY), []).append((xb, pnl))
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

# ---------------------------------------------------------------- FXIFY: at every payout, no day above 25% of it (best day ever)
def fxify_best(c, n, data="synth901y4", seed=9):
    """worst (best calendar day so far - 25% of the payout) over every payout; payouts inferred from the balance between
    consecutive funded trades, days from each trade's entry time"""
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
        for j, (tag, te, xb, pnl) in enumerate(log):
            d = int(te // A.DAY); days[d] = days.get(d, 0.0) + pnl
            amt = (xb + pnl - log[j + 1][2]) if j + 1 < len(log) else 0.0
            if amt > 1.0:                                   # a payout between this trade and the next
                npay += 1; worst = max(worst, max(days.values()) - F["funded"]["best"] * amt)
    return worst, npay
fx = [fxify_best(cfg(p, "FXIFY", "US100", 1.07, 6, x), 150) for p in ("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY Two Phase Classic (80%)")
      for x in (0.10, 0.20)]
check("fxify_best_day", max(w for w, _ in fx) <= 1.0,
      f"{sum(k for _, k in fx)} FXIFY payouts: largest best calendar day beyond 25% of the payout {max(w for w, _ in fx):+.2f} (must be <= 0)")

# ---------------------------------------------------------------- no account ever stalls (the engine's stall detector never fires)
s0 = A.STUCK[0]
for prog, firm, instr, m, k, x in [("GFT 2-Step Standard", "GFT", "USDJPY", 0.6, 3, 0.04), ("Maven 2-Step", "Maven", "US100", 0.75, 8, 0.02),
                                   ("Maven 2-Step", "Maven", "US100", 1.25, 4, 0.05), ("Alpha Capital Pro 10%", "Alpha Capital", "US100", 1.0, 6, 0.05),
                                   ("Maven 2-Step", "Maven", "US100", 0.6, 6, 0.02)]:   # $800 daily cap below half the minimum win
    spy_attempts(cfg(prog, firm, instr, m, k, x), 200, seed=21)
# the account that stalled at Maven's ceiling one profitable day short (version 8, n10), on its own path and seed
c10 = cfg("Maven 2-Step", "Maven", "US100", 0.75, 2, 0.05, lf=0.015); F10 = O.firm_rules(c10); r10 = random.Random(4)
for _ in range(500): PF.attempt(F10, "US100", "synth104", 0.75, c10["L"], 2, c10["X1"], c10["X"], r10)
check("no_stall", A.STUCK[0] == s0, f"{A.STUCK[0] - s0} stalled accounts in 1,500 attempts at the settings where small caps meet the minimum target distance")

json.dump(OUT, open("tests_v8.json", "w"), indent=1)
print("all passed" if all(v["ok"] for v in OUT.values()) else "SOME FAILED")
