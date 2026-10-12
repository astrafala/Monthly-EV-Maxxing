"""
Version 10 rule tests, part 2: one check per correction made for the review of version 9 (findings 1-25) and for the
errors found while making them, each written from the firm's rule or the mathematical statement, not from the engine's
code (run through tests_v10.py). Ordinary replays use the review's own settings and seeds where it gave them; controlled
witnesses feed exact outcomes to the unchanged rule functions.
  lock          (1) Alpha Capital, FundingPips, FXIFY: no entry between a payout request and its processing
  req_wait      (2) every request at least 15 minutes after the last close, with the account flat
  usdjpy        (3) the engine's USDJPY result equals the dollar result of the opposite USDJPY position on the yen's
                dollar price X = 1/USDJPY, exactly; and the review's 1% example
  alpha_lots    (4) every funded Alpha position at most 40 lots per $100K; the review's 82.31-lot case capped at 80
  maven_rr      (5) every Maven position, smallest positions and terminal trades included, has a take-profit at least
                1.5 times as far as its stop; the review's witnesses
  bg_shield     (6) a floating loss of 2% during the hold closes the position at 2%; the first time the split becomes
                50%, the second time the account is breached
  hold_minutes  (7) the hold covers at least 3 minutes at 12, 60 and 240 sub-steps per hour
  unaffordable  (8) a position whose cost alone reaches the breach room is not opened; the account is abandoned
  joint_bound   (9) the joint bound against the review's counterexample and against the exact two-barrier law
  gft_cash      (10) the chain's cash per cycle never above the capped payout plus the refund
  refusals      (12) after a refusal the firm never trades, buys or pays again; its unprocessed payouts are not paid
  apex_expiry   (13) a target reached after 6 p.m. New York time on day 30 is not a pass
  the5ers_cap   (16) every High Stakes payout at most $4,000 with the refund inside it; $500 of profit at every request
  the5ers_refund(17) each account's refund is 70% of the cash paid for it
  topstep_session (18) at least five completed winning sessions (Chicago time) after the previous request's session
  topstep_min   (19) every Topstep payout at least $125 after the split; the review's controlled witness
  apex_pending  (20) nothing traded while an Apex request is pending; every request at a balance of $52,600 or more
  apex_today    (21) the review's controlled sequence: today's $900 makes the best day 64% of the cycle: no payout
  filler_target (25) with no filler executed, the no-filler variant equals the baseline attempt by attempt
  news          (n22) no position open in any bar that overlaps a restricted news window, on restricted stages
  gft_void      a GFT funded win held under a minute counts minus its cost
  cancel        a payout is cancelled exactly when the account breaches before it is processed
  min_payout    every payout's share for the trader (the cash less the fee refund paid with it) at least the firm's
                published minimum, FTMO's $20 included (found by comparing the inventory with the rule sets), at eleven
                firms; Alpha Capital's and FunderPro's $100 of profit before the split at every request ($80 of share)
  usd_direction no two positions in EURUSD and USDJPY open at the same time with opposite dollar exposure (the shared
                direction covers the two currency pairs together; version 9 gave each pair its own direction)
  gft_rules     GFT's rewards page (9 October 2026): every request's best trade larger than its worst loss, over the cycle
                and over the account; every payout 97% of the 80% split (the 3% processing fee) and no fee refund
  no_terminal_no_filler  (12 October 2026) no last trade to the floor at GFT and Alpha Capital, no filler at Fintokei,
                Alpha Capital, FunderPro and Hola Prime; FTMO, which has both, as the control
  payout_fees   the pages read on 12 October 2026: each payout's cash is the firm's fee applied to the split share plus
                the refund due with that request (GFT 3%; Hola Prime 2.5%, at least $5, the fee refunded with the 4th
                payout; Maven $20 a payout, the fee refunded with the 3rd); no refund at Fintokei, GFT or Alpha Capital
"""
import json, math, random, collections, datetime as _dt, zoneinfo
import numpy as np
import acct_mc as A, pathfirm as PF, optimize_v10 as O, lockstep as LS, firms_v10 as F10, news_v10 as NW

CHI = zoneinfo.ZoneInfo("America/Chicago")

def funded_replay(c, n, data, seed, spy):
    """n accounts started directly in the funded stage (the review's method), each on a new trader; returns the records"""
    F = O.firm_rules(c); rng = random.Random(seed); out = []
    for _ in range(n):
        tr = spy(c["instr"], data, c["m"], c["L"], c["k"], rng, 1.0, "trend5", F.get("flat_daily"))
        A.PAYLOG = []; A.TRADELOG = []
        t0 = rng.random() * A.DAY
        paid, c2, tf, npay = A.run_funded(F["funded"], tr, rng, F, t0, c["X1"], c["X"])
        out.append(dict(log=tr.log, pays=list(A.PAYLOG), tlog=list(A.TRADELOG), paid=paid, end=c2, npay=npay, tr=tr, F=F, t0=t0))
        A.PAYLOG = None; A.TRADELOG = None
    return out

def chosen(prog, instr):
    fin = json.load(open("opt_v9_final.json"))
    r = [r for r in fin if r["prog"] == prog and r["instr"] == instr and r["tag"] == "chosen"][0]
    return {k: r[k] for k in O.FINAL_KEYS if k in r}

def run(check, cfg, spy_attempts, Spy, ctl_market, Planned):
    # ---------------------------------------------------------------- 1. processing locks
    viol = 0; npay = 0; firms = []
    for prog, firm, instr in (("Alpha Capital Pro 10%", "Alpha Capital", "US100"), ("FundingPips 2-Step Flex (95%)", "FundingPips", "USDJPY"),
                              ("FXIFY Two Phase Classic (80%)", "FXIFY", "US100")):
        c = cfg(prog, firm, instr, 1.0, 4, 0.05)
        R = funded_replay(c, 300, "synth903y4", 177, Spy)
        for r in R:
            for p in r["pays"]:
                if p[3] != "payout": continue
                npay += 1
                if any(p[2] - 1e-9 <= t["t_in"] < p[4] - 1e-9 for t in r["log"]): viol += 1
        firms.append(firm)
    check("lock", npay > 100 and viol == 0, f"{npay} payouts at {', '.join(firms)} (300 funded accounts each, synth903y4, "
          f"Random(177), the review's replay): {viol} entries between a request and its processing (version 9: 219 of 219 at Alpha)")

    # ---------------------------------------------------------------- 2. 15 minutes after the last close
    c = cfg("FundingPips 2-Step Flex (95%)", "FundingPips", "USDJPY", 1.0, 6, 0.05)
    R = funded_replay(c, 300, "synth903y4", 177, Spy)
    gaps = []
    for r in R:
        for p in r["pays"]:
            if p[3] != "payout": continue
            prev = [t["t_out"] for t in r["log"] if t["t_out"] <= p[2] + 1e-9]
            if prev: gaps.append((p[2] - max(prev)) * 60.0)
            if any(t["t_in"] < p[2] - 1e-9 < t["t_out"] - 1e-9 for t in r["log"]): gaps.append(-1.0)   # not flat
    check("req_wait", len(gaps) > 50 and min(gaps) >= 15.0 - 1e-6,
          f"{len(gaps)} FundingPips requests: shortest time after the last close {min(gaps):.1f} minutes, every one flat "
          f"(version 9: 7 of 329 under 15 minutes)")

    # ---------------------------------------------------------------- 3. USDJPY in dollars
    M = PF.market("USDJPY", "synth904y4"); rng = random.Random(5); worst = 0.0; n_ = 0
    for t in range(4000):
        i, _ = PF.entry_index(M, rng.randrange(M["T"] - 3000), False, 20)
        d = 1 if rng.random() < .5 else -1; l = rng.uniform(50, 3000); s = rng.choice((0.6, 1.0, 1.25)) * M["sig"]
        Mf = PF.market("USDJPY", PF.free_market("USDJPY", "synth904y4"))
        pnl, h, info = PF.resolve(Mf, i, d, l, 3 * l, s, 0.0, False, 20, rng, opts=dict(breach=1e12))
        if info["why"] == "unaffordable": continue
        X_e = info["e"]; Q = info["notional"]                 # dollars of USDJPY (lots x 100,000)
        # the exit price of X, read from the path: the barrier hit, or the bar's open of a timed exit
        if info["why"] == "target": X_x = info["tp"]
        elif info["why"] in ("stop", "breach"): X_x = info["lo_px"]
        elif info["why"] in ("flat", "news", "gap", "block"): X_x = Mf["O"][i + int(round(info["exit"]))]
        else: continue
        P_e, P_x = 1.0 / X_e, 1.0 / X_x                      # USDJPY = 1/X (up to a constant, which cancels)
        usd = Q * (-d) * (P_x - P_e) / P_x                     # the opposite USDJPY position, converted at the exit rate
        worst = max(worst, abs(pnl - usd)); n_ += 1
    Q = 100_000.0; ex_long = Q * 0.01 / 1.01; ex_short = Q * 0.01 / 0.99
    check("usdjpy", worst < 1e-6 and n_ > 2000,
          f"{n_} USDJPY trades: engine result minus the exact dollar result of the opposite USDJPY position at the exit rate, "
          f"largest {worst:.2e}; the review's 1% move: a USDJPY long earns ${ex_long:,.4f}, a short ${ex_short:,.4f}, and the "
          f"engine's position on X = 1/USDJPY that is that long (an X short) earns Q(1 - X_x/X_e) = ${Q * (1 - 1 / 1.01):,.4f}")

    # ---------------------------------------------------------------- 4. Alpha's lot limit
    c = cfg("Alpha Capital Pro 10%", "Alpha Capital", "US100", 1.0, 6, 0.10, size=200_000)
    c["L"] = 3500.0
    R = funded_replay(c, 300, "synth903y4", 177, Spy)
    vmax = max(t["vol"] for r in R for t in r["log"])
    ncap = sum(t["capped"] for r in R for t in r["log"])
    Mx = PF.market("US100", "synth903y4")
    sig = Mx["sig"]; price = 15535.0 / PF.REF_NQ * 100.0
    Mc = dict(Mx); Mc["O"] = [price] * 3
    P = PF.plan(Mc, 0, 3500.0, 3500.0, 1.0 * sig, 0.0, dict(max_lots=80.0))
    P0 = PF.plan(Mc, 0, 3500.0, 3500.0, 1.0 * sig, 0.0, {})
    check("alpha_lots", vmax <= 80.0 + 1e-9 and abs(P["vol"] - 80.0) < 1e-9 and P0["vol"] > 80,
          f"300 funded $200K Alpha accounts: largest position {vmax:.2f} lots ({ncap} positions cut to the limit); the review's "
          f"case (index at 15,535, $3,500 at 1 sd): {P0['vol']:.2f} lots uncapped, {P['vol']:.2f} with the limit")

    # ---------------------------------------------------------------- 5. Maven's reward:risk on the actual position
    c = cfg("Maven 2-Step", "Maven", "US100", 1.25, 2, 0.049)
    R = spy_attempts(c, 2000, data="synth902y4", seed=88)
    trades = [t for r in R for t in r["log"] if t["kind"] != "filler"]
    rr = [t["td_rel"] / t["sd_rel"] for t in trades]
    low = min(rr); nmin = sum(t["vol"] <= 0.01 + 1e-12 for t in trades); nterm = sum(bool(t["opts"].get("terminal")) for t in trades)
    # the review's controlled case: target $1 at risk $1/1.5 on the smallest position
    Mx = PF.market("US100", "synth902y4"); i, _ = PF.entry_index(Mx, 5000, False, 20)
    class T1:            # the plan's check on that one position
        def __init__(s): s.s = 1.25 * Mx["sig"]; s.cost = Mx["cost"]; s.k = 2.0
        def plan_at(s, clock, l, w, o, fw):
            o = dict(o)
            if "keep_w" not in o: o["keep_w"] = w < s.k * l * (1 - 1e-9)      # as the trader sets it
            return PF.plan(Mx, i, l, w, s.s, s.cost, o)
    r1 = A._rr_fix(T1(), 0.0, False, 1.0 / 1.5, 1.0, dict(breach=4000.0), 1.5, 1.0, 1.0)       # rule cap $1: must wait
    r2 = A._rr_fix(T1(), 0.0, False, 1.0 / 1.5, 1.0, dict(breach=4000.0), 1.5, 1e9, 1.0)       # no cap: the win is raised
    P2 = PF.plan(Mx, i, r2[0], r2[1], 1.25 * Mx["sig"], Mx["cost"], dict(keep_w=True)) if r2 else None
    check("maven_rr", low >= 1.5 * (1 - 1e-9) and r1 is None and P2 is not None and P2["td"] >= 1.5 * P2["sd"] * (1 - 1e-12),
          f"{len(trades)} Maven positions (2,000 attempts, k=2, m=1.25, synth902y4, Random(88), the review's replay; {nmin} at "
          f"the smallest position, {nterm} terminal): smallest take-profit/stop distance ratio {low:.4f} (version 9: 1.266); "
          f"the review's $1-target case: waits when the cap is $1, else the win is raised to ${r2[1]:.4f} (ratio "
          f"{P2['td'] / P2['sd']:.4f})")

    # ---------------------------------------------------------------- 6. Guardian Shield
    sig = 0.0027; uvq = PF.REF_NQ                       # one US100 lot: $31,070 per 100% move at the reference
    def path_minutes(moves):                            # log price, minute by minute
        lp = [0.0]
        for mv in moves: lp.append(lp[-1] + mv)
        return lp + [lp[-1]] * (120 * 60)
    vol = 1750.0 / (uvq * 1.25 * sig); vol = math.floor(vol * 100 + 1e-9) / 100
    q = vol * uvq                                      # dollars per 100% move
    lp = path_minutes([-2200.0 / q, 0.0, +2200.0 / q])  # down $2,200 in the first minute, back by the third
    Mb = ctl_market("US100", lp)
    pnl, h, inf = PF.resolve(Mb, 0, 1, 1750.0, 1750.0 * 12, 1.25 * sig, 0.0, False, None, random.Random(1),
                             opts=dict(breach=8000.0, hold=3, shield=2000.0))
    pnl9, _, inf9 = PF.resolve(Mb, 0, 1, 1750.0, 1750.0 * 12, 1.25 * sig, 0.0, False, None, random.Random(1),
                               opts=dict(breach=8000.0, hold=3))
    # the consequences, on the unchanged funded function, with planned outcomes: two shields
    class Sh(Planned):
        def trade(s, l, w, clock, fw=False, opts=None):
            pnl_, h_ = super().trade(l, w, clock, fw, opts)
            d_ = int(s.last_entry // 24)
            if d_ in (2, 5) and not getattr(s, "sh_" + str(d_), False):
                setattr(s, "sh_" + str(d_), True)
                s.last_info = dict(dur=1.0, breach=False, shield=True, why="shield"); pnl_ = -2000.0
            return pnl_, h_
    Fb = F10.rules_for("Blue Guardian 2-Step"); Fb["funded"]["profit_days"] = None
    A.PAYLOG = []
    paid, c2, tf, npy = A.run_funded(Fb["funded"], Sh({0: 600.0, 1: 600.0, 3: 600.0, 4: 600.0}, 60), random.Random(1), Fb, 0.0, 1e9, 1e9)
    A.PAYLOG = None
    hits = dict(A.RULE_HITS)
    check("bg_shield", inf["why"] == "shield" and abs(pnl + 2000.0) < 1e-6 and abs(pnl9) < 1e-6 and c2 < 6 * 24 + 1e-9,
          f"a $2,200 floating loss in the first minute of the hold, recovered by the third: closed by the Shield at "
          f"{pnl:+,.2f} (version 9: {pnl9:+,.2f}); planned shields on days 2 and 5: the account ends on day {int(c2 // 24)} "
          f"(the second shield breaches it)")

    # ---------------------------------------------------------------- 7. holding time in minutes
    hs = {sb: PF.hold_steps(3, sb) * 60.0 / sb for sb in (12, 60, 240)}
    durs = {}
    for sb in (12, 60, 240):
        Ms = PF.market("US100", f"synth1501y2s{sb}"); rr_ = random.Random(3); dmin = 1e9
        for _ in range(300):
            i, _ = PF.entry_index(Ms, rr_.randrange(Ms["T"] - 2000), False, 20)
            p_, h_, inf_ = PF.resolve(Ms, i, 1, 100.0, 300.0, 0.6 * Ms["sig"], 0.0, False, 20, rr_, opts=dict(kind="filler", breach=1e9))
            dmin = min(dmin, inf_["dur"])
        durs[sb] = dmin
    check("hold_minutes", all(v >= 3.0 - 1e-9 for v in hs.values()) and all(v >= 3.0 - 1e-9 for v in durs.values()),
          "3-minute hold at 12, 60, 240 sub-steps per hour: " + ", ".join(f"{hs[s]:.2f}" for s in (12, 60, 240)) +
          " minutes (version 9: 15, 3, 0.75); filler trades held at least " + ", ".join(f"{durs[s]:.2f}" for s in (12, 60, 240)))

    # ---------------------------------------------------------------- 8. unaffordable position
    Mf = PF.market("MNQ_fut", "synth902y4"); i, _ = PF.entry_index(Mf, 4000, False, 20)
    cost = 2.0 / PF.contract_value(Mf, Mf["O"][i])        # $2 round trip on one contract
    pnl, h, inf = PF.resolve(Mf, i, 1, 50.0, 100.0, 0.6 * Mf["sig"], cost, False, 20, random.Random(1), opts=dict(breach=0.5))
    check("unaffordable", inf["why"] == "unaffordable" and pnl == 0.0,
          f"one micro contract, $2 round trip, $0.50 of room: not opened (result {pnl:+.2f}; version 9 returned -0.50, "
          f"a clipped cost)")

    # ---------------------------------------------------------------- 9. joint bound
    def exact_both(a, b, l, u, v, K=200):
        W = u - l; stay = 0.0
        for k in range(-K, K + 1):
            stay += math.exp(-2 * k * W * (k * W + (a - b)) / v) - math.exp(-2 * (k * W + a - u) * (k * W + b - u) / v)
        pu = math.exp(-2 * (u - a) * (u - b) / v); pl = math.exp(-2 * (a - l) * (b - l) / v)
        return pu + pl - (1 - stay), pu * pl
    e, g = exact_both(0.5, 0.5, 0.0, 1.0, 1.0)
    rng = random.Random(9); worst = 0.0
    for _ in range(3000):
        v = 10 ** rng.uniform(-2.5, 0.0); l = 0.0; u = 1.0
        a = rng.uniform(0.01, 0.99); b = rng.uniform(0.01, 0.99)
        e_, g_ = exact_both(a, b, l, u, v)
        worst = max(worst, e_ - 2 * g_)
    Mq = dict(sub=1, sig=1.0, sC=[math.exp(0.5), math.exp(0.5)])
    jb = PF.joint_bound(Mq, [(1, 2, math.log(math.exp(10.5)), 0.0), (1, 2, 1.0, -9.5)])
    check("joint_bound", abs(e - 0.2491160758) < 1e-9 and abs(g - 0.3678794412) < 1e-9 and worst <= 1e-12 and jb >= abs(g - e),
          f"the review's case (bridge 0.5 to 0.5, nearby barriers 0 and 1 of two accounts): exact {e:.10f}, independent "
          f"{g:.10f}; the joint bound for that sub-step is {jb:.3f} (no certificate), where the per-bracket bounds sum to "
          f"3e-25; P_exact(both) - 2 P_ind on 3,000 random bridges at most {worst:.1e}")

    # ---------------------------------------------------------------- 10. GFT capped cash in the chain
    import analytic_v10 as AN
    F = F10.rules_for("GFT 2-Step Standard"); fd = F["funded"]
    worst = -1e9
    for X in (6000.0, 8000.0, 10000.0):
        a = AN.programme("GFT 2-Step Standard", "US100", 1.07, 3.0, X, X, L=1750.0, size=100_000, F=F)
        for j, cc in enumerate(a["cash_cycle"][:2]):
            worst = max(worst, cc - (fd["split"] * fd["caps"][j] + (fd["refund"] if j == 0 else 0.0)))
    check("gft_cash", worst <= 1e-9, f"GFT chain: cash of each of the first two paid cycles at most the capped payout plus the "
          f"refund (largest excess {worst:+.2f}; version 9's table: $5,400 against at most $5,324)")

    # ---------------------------------------------------------------- 12. refusals inside the event engine
    LS.RULES = F10
    def slot(prog, instr, n, m, k, x, lf=0.015, size=100_000):
        firm = F10.firm_of(prog)
        return [dict(firm=prog, kind="cfd", size=size, L=lf * size, k=k, X1=O.x1_of(firm, x, size), X=x * size, m=m, instr=instr,
                     lev=O.lev_tuple(firm, instr)) for _ in range(n)]
    SL = (slot("FTMO 2-Step", "US100", 4, 0.75, 8, 0.1) + slot("Fintokei ProTrader", "US100", 5, 1.0, 6, 0.1) +
          slot("Blue Guardian 2-Step", "US100", 1, 1.0, 4, 0.08) + slot("GFT 2-Step Standard", "US100", 1, 1.0, 4, 0.06))
    bad = 0; nref = 0; nvoid = 0
    for seed in (100016, 100031, 100125, 100200):
        led, st = LS.run_life(SL, data=f"synth{seed}y2", months=12, seed=seed, rule="trend5",
                              refuse={"A": 0.3, "B": 0.3, "D": 0.5})
        names = [F10.firm_of(s_["firm"]) for s_ in SL]
        for f, t_r in (st["refusals"] or {}).items():
            nref += 1
            for (t, sid, kind, cash, att) in led:
                if names[sid] != f: continue
                if kind == "payout" and cash > 0:
                    pass
                if kind in ("buy",) and t > t_r + 1e-9: bad += 1
            for (te, sid, d, tx, cp, g) in st["trade_log"]:
                if names[sid] == f and te > t_r + 1e-9: bad += 1
        nvoid += sum(r[2] == "payout_void" for r in led)
    check("refusals", bad == 0 and nref > 0,
          f"4 lives with high refusal rates: {nref} refusals, {nvoid} payouts voided; {bad} trades or purchases of a firm after its refusal")

    # ---------------------------------------------------------------- 13. Apex expiry
    Fa = F10.rules_for("Apex 50K EOD", 50_000, "fut")
    st0 = Fa["phases"][0]
    class Late(Planned):
        """flat results every hour until hour 718, then a trade opened at 718 that gains $3,500 by hour 720"""
        def __init__(s, t_last): super().__init__({}, 1e9); s.t_last = t_last
        def utc(s, clock): return PF.EPOCH + _dt.timedelta(hours=clock)
        def next_entry(s, clock, fw=False): return clock
        def trade(s, l, w, clock, fw=False, opts=None):
            s.last_entry = clock; s.trades += 1
            if clock < 718.0 - 1e-9: s.last_exit = clock + 1.0; s.last_info = dict(dur=60.0, breach=False); return 0.0, 1.0
            s.last_exit = clock + s.t_last; s.last_info = dict(dur=60.0 * s.t_last, breach=False); return 3500.0, s.t_last
    # bought at 12:00 UTC on 1 January (7 a.m. in New York, day 1): the deadline is 6 p.m. New York on 30 January,
    # 23:00 UTC, hour 719 (bought at 00:00 UTC it would still be 31 December in New York, and day 30 would end a day sooner)
    exp = A._expiry(Late(2.0), 12.0, st0)
    ok, cl = A.run_stage(st0, Late(2.0), random.Random(1), Fa, 12.0)         # target reached at 720, after the deadline
    ok2, cl2 = A.run_stage(st0, Late(0.5), random.Random(1), Fa, 12.0)       # reached at 718.5, before it
    loc = (PF.EPOCH + _dt.timedelta(hours=exp)).astimezone(zoneinfo.ZoneInfo("America/New_York"))
    check("apex_expiry", not ok and ok2 and loc.hour == 18 and loc.minute == 0 and abs(exp - 719.0) < 1e-9,
          f"deadline {loc:%d %b %H:%M} New York, hour {exp:.0f} (bought at 12:00 UTC on 1 Jan: day 30 at 6 p.m.); a trade "
          f"opened at hour 718 that reaches the target at hour 720: {'pass' if ok else 'no pass'} (version 9: pass); at "
          f"718.5: {'pass' if ok2 else 'no pass'}")

    # ---------------------------------------------------------------- 16. The5ers payout cap and profit gate
    c = dict(chosen("The5ers High Stakes", "US100")); c.update(X1=8000.0, X=8000.0)
    R = funded_replay(c, 300, "synth912y4", 7767, Spy)
    F = O.firm_rules(c); fd = F["funded"]; worst = -1e9; low = 1e9; nreq = 0; low_net = 1e9
    for r in R:
        first = True
        for p in r["pays"]:
            if p[3] != "payout": continue
            ref_ = fd["refund"] if first else 0.0; first = False
            g = 1.0 - fd.get("fee_pct", 0.0)                 # The5ers' 3.5% commission on the whole withdrawal
            amt = (p[1] / g - ref_) / fd["split"]
            worst = max(worst, amt + ref_ - 4000.0); low_net = min(low_net, g * fd["split"] * amt); nreq += 1
            xb = [t for t in r["tlog"] if t[4] <= p[2] + 1e-9]
            prof = (xb[-1][2] + xb[-1][3]) if xb else 0.0
            low = min(low, prof)
    check("the5ers_cap", nreq > 50 and worst <= 1e-6 and low >= 500.0 - 1e-6 and low_net >= 150.0 - 1e-6,
          f"{nreq} High Stakes requests (300 funded $100K accounts, synth912y4, Random(7767), the review's replay): largest "
          f"withdrawal with the refund minus $4,000 {worst:+.2f}; lowest profit at a request ${low:,.2f} (>= $500); lowest "
          f"share ${low_net:,.2f} (>= $150) (version 9: 124 of 154 above the cap, 2 on $399)")

    # ---------------------------------------------------------------- 17. The5ers refund on cash paid
    rec = []
    orig = LS.g_run_funded
    def spyfund(fd, tr, rng, firm, clock, X1, X):
        rec.append(fd.get("refund"))
        return (yield from orig(fd, tr, rng, firm, clock, X1, X))
    LS.g_run_funded = spyfund
    try:
        led, st = LS.run_life(slot("The5ers High Stakes", "US100", 1, 0.75, 12, 0.05, lf=0.0175), data="synth913y4", months=36,
                              seed=8761, rule="trend5")
    finally:
        LS.g_run_funded = orig
    buys = {att: -cash for (t, sid, kind, cash, att) in led if kind == "buy"}
    funded_atts = sorted({att for (t, sid, kind, cash, att) in led if kind == "funded_end"})
    pairs = list(zip(funded_atts, rec))
    errs = [abs(refd - 0.7 * buys[att]) for att, refd in pairs]
    ncred = sum(1 for att, _ in pairs if buys[att] < F10.rules_for("The5ers High Stakes")["fee"] - 1e-9)
    check("the5ers_refund", len(pairs) > 0 and max(errs) < 1e-9 and ncred > 0,
          f"{len(pairs)} funded The5ers accounts in a 36-month slot (synth913y4, seed 8761, the review's replay), {ncred} bought "
          f"partly with credit: refund minus 70% of the cash paid, largest {max(errs):.1e} (version 9: $343.70 on $343.70 paid)")

    # ---------------------------------------------------------------- 18-19. Topstep sessions and minimum
    c = chosen("Topstep 50K", "MNQ_fut")
    R = funded_replay(c, 1500, "synth911y4", 7741, Spy)
    def session(tr, t):                                   # the Chicago trading day a time belongs to (5 p.m. boundary)
        ct = tr.utc(t).astimezone(CHI)
        return (ct + _dt.timedelta(hours=7)).date()
    def locked_before(tr, sx, t):                          # the session's results locked (4 p.m. Chicago) before time t
        lock = _dt.datetime(sx.year, sx.month, sx.day, 16, 0, tzinfo=CHI)
        return lock <= tr.utc(t).astimezone(CHI)
    short = 0; nreq = 0; low_net = 1e9; wrapped = 0
    for r in R:
        pays = [p for p in r["pays"] if p[3] == "payout"]
        low_net = min([low_net] + [p[1] for p in pays])
        for p0, p1 in zip(pays, pays[1:]):
            s0, s1 = session(r["tr"], p0[2]), session(r["tr"], p1[2])
            if r["tr"]._idx(p1[2]) < r["tr"]._idx(p0[2]):          # the account outlived its path, which wrapped round
                wrapped += 1; continue                               # between the requests: dates are not comparable
            by = collections.defaultdict(float)
            for t in r["log"]:
                sx = session(r["tr"], t["t_out"])
                if s0 < sx <= s1 and locked_before(r["tr"], sx, p1[2]): by[sx] += t["pnl"]
            nreq += 1
            if sum(1 for v in by.values() if v >= 150.0) < 5: short += 1
            if p1[2] >= 0 and r["tr"].utc(p1[2]).astimezone(CHI).weekday() == 4 and r["tr"].utc(p1[2]).astimezone(CHI).hour >= 17: short += 1
            if r["tr"].utc(p1[2]).astimezone(CHI).weekday() == 5: short += 1                  # outside the payout window
    Ft = F10.rules_for("Topstep 50K", 50_000, "fut")
    A.PAYLOG = []
    plan = {0: 150, 1: -140, 2: 150, 3: -140, 4: 150, 5: -140, 6: 150, 7: -130, 8: 150}
    paid, c2, tf, npy = A.run_funded(Ft["funded"], Planned({k: float(v) for k, v in plan.items()}, 12), random.Random(1), Ft, 0.0, 0, 0)
    pw = [p for p in A.PAYLOG if p[3] == "payout"]; A.PAYLOG = None
    check("topstep_session", nreq > 100 and short == 0,
          f"{nreq} later Topstep requests (1,500 funded accounts, synth911y4, Random(7741), the review's replay): {short} with "
          f"fewer than five winning Chicago sessions locked between the previous request's session and the request, or "
          f"outside the payout window ({wrapped} pairs across the end of a wrapped path not compared; version 9: 238 of 1,204)")
    check("topstep_min", low_net >= 125.0 - 1e-9 and not pw,
          f"lowest Topstep payout after the split ${low_net:,.2f}; the review's witness (five +$150 days between losses, $200 "
          f"of profit): {len(pw)} payouts (version 9: $90)")

    # ---------------------------------------------------------------- 20. Apex: pause while pending
    c = chosen("Apex 50K EOD", "MNQ_fut")
    R = funded_replay(c, 1500, "synth911y4", 7741, Spy)
    trade_in = 0; nreq = 0; lowbal = 1e9
    for r in R:
        for p in r["pays"]:
            if p[3] != "payout": continue
            nreq += 1
            if any(p[2] - 1e-9 <= t["t_in"] < p[4] - 1e-9 for t in r["log"]): trade_in += 1
            xb = [t for t in r["tlog"] if t[4] <= p[2] + 1e-9]
            lowbal = min(lowbal, 50_000 + ((xb[-1][2] + xb[-1][3]) if xb else 0.0))
    check("apex_pending", nreq > 100 and trade_in == 0 and lowbal >= 52_600 - 1e-6,
          f"{nreq} Apex requests (1,500 funded accounts, synth911y4, Random(7741)): {trade_in} with a trade while pending "
          f"(version 9: 912 of 982); lowest balance at a request ${lowbal:,.2f}")

    # ---------------------------------------------------------------- 21. Apex: today's profit in the consistency rule
    Fa = F10.rules_for("Apex 50K EOD", 50_000, "fut"); fa = Fa["funded"]
    fa.update(review_bd=0, pause_pending=False, protected=True, buffer=0.0, min_payout=0.0)
    seqp = {d_: 300.0 for d_ in range(5)}                      # a valid first payout on day 5 ($1,500, the first cap)
    for j, v in enumerate([500, -500, 500, -500, 500, -500, 500, -500, 500]): seqp[6 + j] = float(v)
    seqp[15] = 900.0                                           # then today's +$900
    A.PAYLOG = []
    paid, c2, tf, npy = A.run_funded(fa, Planned(seqp, 20), random.Random(1), Fa, 0.0, 0, 0)
    pp = [p for p in A.PAYLOG if p[3] == "payout"]; A.PAYLOG = None
    first = [p for p in pp if p[2] < 6 * 24.0]; late = [p for p in pp if p[2] >= 6 * 24.0]
    check("apex_today", len(first) == 1 and not late,
          f"a first payout of ${first[0][1] if first else 0:,.0f} on day 5, then five +$500 and four -$500 days and +$900 "
          f"today (best day 64% of the cycle's $1,400): {len(late)} later payouts (version 9: $1,400)")

    # ---------------------------------------------------------------- 25. filler variant keeps the target
    c = chosen("Hola Prime 2-Step Prime (bi-weekly 80%)", "XAUUSD")
    F = O.firm_rules(c)
    def att(Fx, seed):
        rng = random.Random(seed); out = []
        for _ in range(300):
            r = PF.attempt(Fx, c["instr"], "synth931y4", c["m"], c["L"], c["k"], c["X1"], c["X"], rng)
            out.append((round(r["v"], 6), round(r["days"], 6), r["st"]["fillers"]))
        return out
    base = att(F, 873); F2 = dict(F); F2["no_fillers"] = True; nof = att(F2, 873)
    nfill = sum(x[2] for x in base) + sum(x[2] for x in nof)
    same = sum(1 for a_, b_ in zip(base, nof) if a_[:2] == b_[:2])
    check("filler_target", nfill > 0 or same == 300,
          f"Hola gold, 300 attempts, synth931y4, Random(873) (the review's replay): {same} of 300 attempts identical with "
          f"and without fillers, {nfill} fillers executed (version 9: 281 differed with none executed)")

    # ---------------------------------------------------------------- news: flat in restricted bars
    viol = 0; ntr = 0; nnews = 0
    for prog, firm, instr in (("FTMO 2-Step", "FTMO", "US100"), ("Maven 2-Step", "Maven", "US100"),
                              ("FundedNext Stellar 2-Step", "FundedNext", "EURUSD"), ("FXIFY Two Phase Classic (80%)", "FXIFY", "USDJPY")):
        R = spy_attempts(cfg(prog, firm, instr, 1.0, 6, 0.05), 200, data="synth904y4", seed=31)
        for r in R:
            for t in r["log"]:
                if not t["news"]: continue
                ntr += 1; nb = PF.news_bars(PF.market(instr, "synth904y4"), t["news"])
                i0 = t["i"]; nh = int(math.ceil(t["exit"] - 1e-9))
                T_ = len(nb)
                if nb[i0 % T_] or nb[(i0 + 1) % T_]: viol += 1
                for b in range(1, nh):
                    if nb[(i0 + b) % T_]: viol += 1
                nnews += t["why"] == "news"
    check("news", viol == 0 and nnews > 0,
          f"{ntr} trades on stages with a news rule (FTMO funded, Maven, FundedNext funded, FXIFY): {viol} open during a bar "
          f"overlapping a release's window; {nnews} closed at the open of such a bar")

    # ---------------------------------------------------------------- GFT: wins under a minute
    c = cfg("GFT 2-Step Standard", "GFT", "US100", 0.6, 1.5, 0.06)
    R = funded_replay(c, 300, "synth905y4", 41, Spy)
    tl = [t for r in R for t in r["log"]]
    bad = sum(1 for t in tl if t["dur"] < 1.0 - 1e-9 and t["pnl"] > 1e-9)
    nv = sum(t["voided"] for t in tl)
    check("gft_void", bad == 0, f"{len(tl)} GFT funded trades: {bad} wins held under a minute counted ({nv} voided)")

    # ---------------------------------------------------------------- pending payouts cancelled by a breach
    c = cfg("FTMO 2-Step", "FTMO", "US100", 0.6, 1.5, 0.02)
    R = funded_replay(c, 600, "synth905y4", 43, Spy)
    bad = 0; ncan = 0
    for r in R:
        pays = [p for p in r["pays"] if p[3] == "payout"]; cans = [p for p in r["pays"] if p[3] == "payout_cancelled"]
        ncan += len(cans)
        br = [t["t_out"] for t in r["log"] if t["breach"]]
        tb = br[0] if br else None
        for p in pays:
            cancelled = any(abs(cn[0] - p[0]) < 1e-9 and abs(cn[1] + p[1]) < 1e-9 for cn in cans)
            should = tb is not None and p[2] <= tb < p[4]
            if cancelled != should: bad += 1
    check("cancel", bad == 0, f"{sum(len(r['pays']) for r in R)} payout rows of 600 funded FTMO accounts at a tight setting: "
          f"{ncan} cancelled, each by a breach between its request and its processing ({bad} mismatches)")

    # ---------------------------------------------------------------- minimum payouts, on the trader's share
    MINS = {"FTMO": 20.0, "FundingPips": 1_000.0, "FXIFY": 50.0, "Fintokei": 100.0, "Alpha Capital": 80.0, "GFT": 100.0,
            "FunderPro": 80.0, "Blue Guardian": 100.0, "The5ers": 150.0, "Hola Prime": 50.0, "FundedNext": 20.0}
    # Alpha Capital and FunderPro: $100 of profit before the split, $80 of share after it (12 October 2026)
    def refund_with(fd, j):
        """the fee refund paid with the j-th request (0-based): with the refund_after-th payout, or in equal parts with
        the first refund_split payouts (Hola Prime)"""
        if not fd.get("refund"): return 0.0
        g = 1.0 - fd.get("fee_pct", 0.0)               # the refund is paid net of a withdrawal fee too
        if fd.get("refund_split"): return g * fd["refund"] / fd["refund_split"] if j < fd["refund_split"] else 0.0
        return g * fd["refund"] if j == fd.get("refund_after", 1) - 1 else 0.0
    low = {}; low_prof = {}; nreq = 0; small = 0; w0 = A.RULE_HITS.get("min_net_wait", 0)
    for prog, firm, instr in (("FTMO 2-Step", "FTMO", "US100"), ("FundingPips 2-Step Flex (80%)", "FundingPips", "USDJPY"),
                              ("FXIFY Two Phase Classic (80%)", "FXIFY", "US100"), ("Fintokei ProTrader", "Fintokei", "US100"),
                              ("Alpha Capital Pro 10%", "Alpha Capital", "US100"), ("GFT 2-Step Standard", "GFT", "US100"),
                              ("FunderPro Classic", "FunderPro", "US100"), ("Blue Guardian 2-Step", "Blue Guardian", "US100"),
                              ("The5ers High Stakes", "The5ers", "US100"),
                              ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", "EURUSD"),
                              ("FundedNext Stellar 2-Step", "FundedNext", "EURUSD")):
        c = cfg(prog, firm, instr, 1.0, 2, 0.10)              # a target of 10%: most requests come at a payout date, below it
        R = funded_replay(c, 150, "synth906y4", 51, Spy)
        for r in R:
            fd = r["F"]["funded"]
            for j, p in enumerate([p for p in r["pays"] if p[3] == "payout"]):
                net = p[1] - refund_with(fd, j); nreq += 1
                if fd.get("min_payout"):                     # the profit gate before the split (Alpha Capital, FunderPro: $100)
                    xb = [t for t in r["tlog"] if t[4] <= p[2] + 1e-9]
                    prof = (xb[-1][2] + xb[-1][3]) if xb else 0.0
                    low_prof[firm] = min(low_prof.get(firm, 1e18), prof - fd["min_payout"])
                low[firm] = min(low.get(firm, 1e18), net)
                if net < 2 * MINS[firm]: small += 1
    worst = {f: round(v - MINS[f], 2) for f, v in low.items()}
    check("min_payout", nreq > 500 and all(v >= -1e-6 for v in worst.values()) and all(v >= -1e-6 for v in low_prof.values())
          and A.RULE_HITS.get("min_net_wait", 0) > w0,
          f"{nreq} requests at {len(low)} firms (150 funded accounts each, payout target 10%, synth906y4): smallest trader's share "
          f"less the firm's minimum {worst}; {small} requests under twice the minimum; "
          f"{A.RULE_HITS.get('min_net_wait', 0) - w0} requests deferred because the share was under the minimum; smallest profit "
          f"before the split less the firm's profit minimum {({f: round(v, 2) for f, v in low_prof.items()})}")
    payout_fees(check, cfg, Spy)
    no_terminal_no_filler(check, cfg, Spy, spy_attempts)
    keepalive(check, cfg, Spy)

    # ---------------------------------------------------------------- one dollar direction across EURUSD and USDJPY
    def sl_(prog, instr, n, m, k, x, lf=0.015):
        firm = F10.firm_of(prog)
        return [dict(firm=prog, kind="cfd", size=100_000, L=lf * 100_000, k=k, X1=O.x1_of(firm, x, 100_000), X=x * 100_000, m=m,
                     instr=instr, lev=O.lev_tuple(firm, instr)) for _ in range(n)]
    SLx = (sl_("FundingPips 2-Step Flex (95%)", "USDJPY", 2, 1.0, 4, 0.05) + sl_("FundedNext Stellar 2-Step", "EURUSD", 1, 1.0, 4, 0.05)
           + sl_("Hola Prime 2-Step Prime (bi-weekly 80%)", "EURUSD", 1, 1.0, 4, 0.05) + sl_("FTMO 2-Step", "US100", 1, 0.75, 4, 0.05))
    LS.RULES = F10
    opp = 0; both = 0; conf = 0; ntr = 0
    for seed in (100016, 100031):
        led, st = LS.run_life(SLx, data=f"synth{seed}y2", months=12, seed=seed, rule="trend5")
        conf += st["conflicts"]; tl = st["trade_log"]; ntr += len(tl)
        fx = [(te, tx, d, SLx[sid]["instr"]) for (te, sid, d, tx, cp, g) in tl if SLx[sid]["instr"] in ("EURUSD", "USDJPY")]
        for a in fx:
            for b in fx:
                if a[3] == "USDJPY" and b[3] == "EURUSD" and a[0] < b[1] and b[0] < a[1]:
                    both += 1; opp += a[2] != b[2]
    check("usd_direction", opp == 0 and both > 0 and conf == 0,
          f"2 lives, {ntr} trades: {both} pairs of overlapping USDJPY and EURUSD positions, {opp} with opposite dollar exposure "
          f"(the engine's prices are the euro and the yen in dollars: the same engine direction is the same dollar exposure); "
          f"{conf} opposite positions")

    # ---------------------------------------------------------------- GFT: best trade against worst loss; processing fee
    c = cfg("GFT 2-Step Standard", "GFT", "US100", 1.0, 1.5, 0.06)
    R = funded_replay(c, 150, "synth907y4", 61, Spy)
    nreq = 0; badbw = 0; worst_share = 0.0
    for r in R:
        fd = r["F"]["funded"]; prev = -1e18; xs = r["tlog"]
        for p in [p for p in r["pays"] if p[3] == "payout"]:
            cyc = [t["pnl"] for t in r["log"] if prev - 1e-9 <= t["t_out"] <= p[2] + 1e-9]
            life = [t["pnl"] for t in r["log"] if t["t_out"] <= p[2] + 1e-9]
            okc = max(cyc + [0.0]) > max([-v for v in cyc] + [0.0]); oke = max(life + [0.0]) > max([-v for v in life] + [0.0])
            nreq += 1; badbw += not (okc and oke); prev = p[2]
            worst_share = max(worst_share, abs(fd["split"] * (1 - fd.get("fee_pct", 0.0)) - 0.8 * 0.97))
    check("gft_rules", nreq > 100 and badbw == 0 and worst_share < 1e-12 and R[0]["F"]["funded"]["refund"] == 0,
          f"{nreq} GFT requests (150 funded accounts, synth907y4): {badbw} with the best trade not larger than the worst loss "
          f"(over the cycle and over the account); trader's share {R[0]['F']['funded']['split'] * (1 - R[0]['F']['funded']['fee_pct']):.3f} "
          f"of the profit (80% less the 3% processing fee); fee refund {R[0]['F']['funded']['refund']:.0f}")
    return {}

def payout_fees(check, cfg, Spy):
    """the firms' payout fees and refund timing as read on 12 October 2026: GFT 3% of every reward; Hola Prime 2.5% of every
    payout, at least $5, and the whole fee refunded with the 4th payout; Maven $20 from every payout (Rise) and the fee
    refunded with the 3rd; no refund at Fintokei, GFT or Alpha Capital. Each payout's cash is checked against the amount
    the balance fell by at the request (from the trade log), the split, the refund due with that request and the fee."""
    fdx = {p: F10.rules_for(p)["funded"] for p in ("GFT 2-Step Standard", "Hola Prime 2-Step Prime (bi-weekly 80%)", "Maven 2-Step",
                                                    "FTMO 2-Step", "Fintokei ProTrader", "Alpha Capital Pro 10%")}
    unit = [A.payout_net(fdx["GFT 2-Step Standard"], 1000.0), A.payout_net(fdx["Hola Prime 2-Step Prime (bi-weekly 80%)"], 100.0),
            A.payout_net(fdx["Hola Prime 2-Step Prime (bi-weekly 80%)"], 1000.0), A.payout_net(fdx["Maven 2-Step"], 1000.0),
            A.payout_net(fdx["FTMO 2-Step"], 1000.0)]
    ok_unit = all(abs(a - b) < 1e-9 for a, b in zip(unit, (970.0, 95.0, 975.0, 980.0, 1000.0)))
    norefund = all(not fdx[p].get("refund") for p in ("GFT 2-Step Standard", "Fintokei ProTrader", "Alpha Capital Pro 10%"))
    bad = 0; nchk = 0; nref = collections.Counter(); mism = collections.Counter()
    for prog, firm, instr, r_at in (("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", "EURUSD", 4),
                                    ("Maven 2-Step", "Maven", "US100", 3), ("Fintokei ProTrader", "Fintokei", "US100", None),
                                    ("GFT 2-Step Standard", "GFT", "US100", None), ("Alpha Capital Pro 10%", "Alpha Capital", "US100", None)):
        c = cfg(prog, firm, instr, 1.0, 2, 0.03 if firm == "Maven" else 0.04)
        R = funded_replay(c, 250, "synth908y4", 71, Spy)
        for r in R:
            fd = r["F"]["funded"]; tl = r["tlog"]
            for j, p in enumerate([p for p in r["pays"] if p[3] == "payout"]):
                before = [t for t in tl if t[4] <= p[2] + 1e-9]; after = [t for t in tl if t[1] >= p[2] - 1e-9]
                if not before or not after: continue          # the balance after the request is not observed
                amt = before[-1][2] + before[-1][3] - after[0][2]
                ref = (fd.get("refund") or 0.0) if (r_at is not None and j == r_at - 1) else 0.0
                gross = fd["split"] * amt + ref + (fd.get("eval_share", 0.0) * sum(s["target"] for s in r["F"]["phases"]) if j == 0 else 0.0)
                nchk += 1; nref[firm] += ref > 0
                if abs(p[1] - A.payout_net(fd, gross)) > 1e-6: bad += 1; mism[firm] += 1
    check("payout_fees", ok_unit and norefund and bad == 0 and nchk > 500 and nref["Hola Prime"] >= 5 and nref["Maven"] >= 5,
          f"payout_net: GFT $1,000 -> {unit[0]:.2f}; Hola Prime $100 -> {unit[1]:.2f} (the $5 minimum), $1,000 -> {unit[2]:.2f}; "
          f"Maven $1,000 -> {unit[3]:.2f} ($20); FTMO $1,000 -> {unit[4]:.2f}; no refund at GFT, Fintokei, Alpha Capital: {norefund}; "
          f"{nchk} payouts at five firms (250 funded accounts each, synth908y4) whose cash equals the fee applied to the split "
          f"share plus the refund due with that request ({bad} mismatches {dict(mism)}); refunds paid with the 4th payout at "
          f"Hola Prime {nref['Hola Prime']}, with the 3rd at Maven {nref['Maven']}")

def no_terminal_no_filler(check, cfg, Spy, spy_attempts):
    """the readings of 12 October 2026: GFT ('All-Or-Nothing Trading, where you can lose the account in one trade') and Alpha
    Capital ('all or nothing' strategies) get no last trade to the floor, the account being left as it is; Fintokei and
    Alpha Capital (minimal trades), FunderPro (abrupt lot-size changes) and Hola Prime (unexplained deviations in position
    size) get no filler trades. FTMO, which has both, is the control that shows the counts can be non-zero."""
    out = {}
    for prog, firm, instr in (("GFT 2-Step Standard", "GFT", "US100"), ("Alpha Capital Pro 10%", "Alpha Capital", "US100"),
                              ("FunderPro Classic", "FunderPro", "US100"), ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", "EURUSD"),
                              ("Fintokei ProTrader", "Fintokei", "US100"), ("FTMO 2-Step", "FTMO", "US100")):
        c = cfg(prog, firm, instr, 1.0, 2, 0.06)
        h0 = A.RULE_HITS["left_at_floor"]
        recs = spy_attempts(c, 300, data="synth909y4", seed=13)
        R = funded_replay(c, 200, "synth909y4", 17, Spy)
        logs = [t for r in recs for t in r["log"]] + [t for r in R for t in r["log"]]
        out[firm] = dict(terminal=sum(1 for t in logs if (t.get("opts") or {}).get("terminal")),
                         fillers=sum(1 for t in logs if t.get("kind") == "filler"), left=A.RULE_HITS["left_at_floor"] - h0,
                         trades=len(logs))
    ok = (all(out[f]["terminal"] == 0 and out[f]["left"] > 0 for f in ("GFT", "Alpha Capital"))
          and all(out[f]["fillers"] == 0 for f in ("Fintokei", "Alpha Capital", "FunderPro", "Hola Prime"))
          and out["FTMO"]["terminal"] > 0 and out["FTMO"]["fillers"] > 0 and out["FTMO"]["left"] == 0)
    check("no_terminal_no_filler", ok, "300 attempts and 200 funded accounts per firm (synth909y4): " +
          "; ".join(f"{f}: {v['trades']} trades, {v['terminal']} last trades to the floor, {v['left']} accounts left near it, "
                    f"{v['fillers']} fillers" for f, v in out.items()))

def keepalive(check, cfg, Spy):
    """the plan's 25-day rule (n47): the longest time from one entry to the next, or from the funded account's start to its
    first entry, on 200 funded accounts per firm. FXIFY's 30-day cycle with its read-only review and Maven's $10,000 per
    rolling 30 days are the waits that need a keep-alive position (version 10's first engine left up to 30.0 and 28.0 days);
    the four firms without fillers get none and never come near; Maven's 30-day windows stay under $10,000, a keep-alive's
    gain above it voided"""
    out = {}
    for prog, firm, instr, x in (("FXIFY Two Phase Classic (100%, 30 days)", "FXIFY", "US100", 0.05), ("Maven 2-Step", "Maven", "US100", 0.049),
                                 ("Hola Prime 2-Step Prime (bi-weekly 80%)", "Hola Prime", "EURUSD", 0.05),
                                 ("Alpha Capital Pro 10%", "Alpha Capital", "US100", 0.05), ("Fintokei ProTrader", "Fintokei", "US100", 0.05),
                                 ("FunderPro Classic", "FunderPro", "US100", 0.05)):
        c = cfg(prog, firm, instr, 1.0, 2 if firm == "Maven" else 3, x)
        h0 = dict(A.RULE_HITS)
        R = funded_replay(c, 200, "synth909y4", 21, Spy)
        gap = 0.0; over = -1e18
        for r in R:
            ins = sorted(t["t_in"] for t in r["log"])
            if not ins: continue
            gap = max(gap, (ins[0] - r["t0"]) / A.DAY, max([b - a for a, b in zip(ins, ins[1:])] or [0.0]) / A.DAY)
            if firm == "Maven":                      # every 30-day window of closes, as the audit measures it
                cs = sorted((tx, pnl) for (_, te, xb, pnl, tx, k_, dur) in r["tlog"])
                for b in range(len(cs)):
                    run = 0.0
                    for a in range(b, -1, -1):
                        if cs[b][0] - cs[a][0] >= 30 * A.DAY: break
                        run += cs[a][1]; over = max(over, run - 10_000.0)
        out[firm] = dict(gap=gap, ka=A.RULE_HITS["keepalive"] - h0["keepalive"], idle=A.RULE_HITS["idle_over_25"] - h0["idle_over_25"],
                         voided=A.RULE_HITS["filler_voided"] - h0["filler_voided"], over=over,
                         fillers=sum(1 for r in R for t in r["log"] if t.get("kind") == "filler"))
    ok = (all(v["gap"] <= 25.0 and v["idle"] == 0 for v in out.values()) and out["FXIFY"]["ka"] > 0 and out["Maven"]["ka"] > 0
          and all(out[f]["fillers"] == 0 and out[f]["ka"] == 0 for f in ("Hola Prime", "Alpha Capital", "Fintokei", "FunderPro"))
          and out["Maven"]["over"] <= 1e-6)
    check("keepalive", ok, "200 funded accounts per firm (synth909y4), longest time from one entry to the next: " +
          "; ".join(f"{f} {v['gap']:.2f} days ({v['ka']} keep-alive positions)" for f, v in out.items()) +
          f"; entries more than 25 days apart: {sum(v['idle'] for v in out.values())}; Maven: {out['Maven']['voided']} keep-alive gains voided above its "
          f"30-day cap, largest 30-day closed profit less $10,000 {out['Maven']['over']:+,.2f} (version 10's first engine: FXIFY 30.00 days, Maven 28.00)")

