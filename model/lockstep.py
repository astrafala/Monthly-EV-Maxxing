"""
Lockstep simulation of one person running many accounts at once.

Every account follows its firm's rules (the same rule code as acct_mc, turned into generators), on ONE shared
hourly price path and ONE calendar. Trades are processed in the order of their entry bar, so the shared-direction
rule can be enforced exactly: a new position takes the direction of any position already open on any account;
if none is open, the written rule decides (5-hour momentum). No two accounts ever hold opposite positions.

Each slot buys a new evaluation as soon as its previous attempt ends (failed phase or lost funded account).
Every fee, pass, failure and payout is written to a ledger with its date.
"""
import heapq, random, math, json, copy, inspect, sys
import numpy as np
import acct_mc as A, pathfirm as PF, firms_v5 as F5

# ---------------------------------------------------------------- generator versions of the rule engine
_ns = dict(A.__dict__)
_src_stage = inspect.getsource(A.run_stage).replace("def run_stage(", "def g_run_stage(")
_a = 'pnl, h = tr.trade(l, w, clock, firm.get("flat_weekend_eval", False))'
assert _a in _src_stage
_src_stage = _src_stage.replace(_a, 'pnl, h = yield (clock, l, w, firm.get("flat_weekend_eval", False))')
_src_fund = inspect.getsource(A.run_funded).replace("def run_funded(", "def g_run_funded(")
_b = 'pnl, h = tr.trade(l, w, clock, fd.get("flat_weekend", False))'
assert _b in _src_fund
_src_fund = _src_fund.replace(_b, 'pnl, h = yield (clock, l, w, fd.get("flat_weekend", False))')
_src_fund = _src_fund.replace("if PAYLOG is not None: PAYLOG.append(", 'if fd.get("_paylog") is not None: fd["_paylog"].append(')
exec(_src_stage, _ns); exec(_src_fund, _ns)
g_run_stage, g_run_funded = _ns["g_run_stage"], _ns["g_run_funded"]
DAY = A.DAY

class _T:      # what the rule engine reads from the trader
    def __init__(self, L, k, rho=0.0, min_l=0.0, s=1.0):
        self.L = L; self.k = k; self.rho = rho; self.min_l = min_l; self.s = s

def g_slot(sid, firm, L, k, X1, X, rng, t_end, ledger, start=0.0, rho=0.0, min_l=0.0, s=1.0, wallet=None, gap_days=0.0):
    """one account slot, attempts back to back from `start` until t_end (hours).
    Ledger rows: (time, slot, kind, bank cash, attempt number). Non-cash credits (The5ers) are rows of kind
    'credit_earned' / 'credit_used' with zero cash; a purchase pays only the part of the fee the slot's credit does not cover.
    wallet: a shared finite cash budget; a purchase waits (checked daily) until the wallet holds its cash.
    gap_days: the plan waits this long after a failed attempt before buying the next one (pacing)."""
    tr = _T(L, k, rho, min_l, s); clock = float(start); att = 0; credit = 0.0
    while clock < t_end:
        use = min(credit, firm["fee"]); cash_fee = firm["fee"] - use
        if wallet is not None:
            while not wallet.take(clock, cash_fee):
                yield ("wait", clock + 24.0); clock += 24.0
                if clock >= t_end: return
        t0 = clock; att += 1
        ledger.append((clock, sid, "buy", -cash_fee, att))
        if use > 0: ledger.append((clock, sid, "credit_used", 0.0, att)); credit -= use
        ok_all = True
        for j, st in enumerate(firm["phases"]):
            ok, clock = yield from g_run_stage(st, tr, rng, firm, clock)
            ledger.append((clock, sid, f"phase{j+1}_" + ("pass" if ok else "fail"), 0.0, att))
            if ok and firm.get("phase_credit"):
                credit += firm["phase_credit"][j]; ledger.append((clock, sid, "credit_earned", 0.0, att))
            if not ok: ok_all = False; break
        if firm["monthly"]:
            months = max(1, math.ceil((clock - t0) / (30 * DAY)))
            for m in range(1, months):
                ledger.append((t0 + 30 * DAY * m, sid, "monthly_fee", -firm["fee"], att))
                if wallet is not None: wallet.pay_now(-firm["fee"])
        if not ok_all:
            clock += gap_days * DAY
            continue
        if firm.get("activation"):
            ledger.append((clock, sid, "activation", -firm["activation"], att))
            if wallet is not None: wallet.pay_now(-firm["activation"])
        fd = copy.deepcopy(firm["funded"]); fd["_paylog"] = []
        f2 = dict(firm); f2["funded"] = fd
        paid, clock, tfirst, npay = yield from g_run_funded(fd, tr, rng, f2, clock, X1, X)
        for (tc, cash) in fd["_paylog"]:
            ledger.append((tc, sid, "payout", cash, att))
            if wallet is not None: wallet.receive(tc, cash)
        ledger.append((clock, sid, "funded_end", 0.0, att))
        clock += gap_days * DAY
    if credit > 0: ledger.append((t_end, sid, "credit_left", 0.0, att))

class Wallet:
    """a finite cash budget shared by every slot; payouts become spendable when they arrive"""
    def __init__(self, cash):
        self.cash = float(cash); self.pending = []; self.low = float(cash)
    def receive(self, t, cash): heapq.heappush(self.pending, (t, cash))
    def pay_now(self, cash): self.cash += cash; self.low = min(self.low, self.cash)
    def take(self, t, fee):
        while self.pending and self.pending[0][0] <= t: self.cash += heapq.heappop(self.pending)[1]
        if self.cash + 1e-9 < fee: return False
        self.cash -= fee; self.low = min(self.low, self.cash); return True

RULES = None          # module that turns a slot into firm rules (firms_v7 when set, else firms_v5)
def rules(sp):
    mod = RULES or F5
    return mod.rules_for(sp["firm"], sp.get("size", 100_000), sp["kind"], sp.get("fee"), sp.get("override"))

NEWS_HOURS = {"US100": (12, 13), "MNQ_fut": (12, 13), "XAUUSD": (12, 13), "USDJPY": (12, 13), "EURUSD": (8, 12, 13)}

class Market:
    def __init__(self, instr, data, news=False):
        self.M = PF.market(instr, data)
        self.block = set(NEWS_HOURS[instr]) if news else set()   # news proxy: flat through these UTC hours every weekday
    def entry_index(self, i, flat_weekend, flat_daily):
        M = self.M; T = M["T"]; waited = 0; B = self.block
        while (not M["entry"][i] or (flat_weekend and M["fri_late"][i]) or
               (flat_daily is not None and M["hour"][i] >= flat_daily - 1) or
               (B and (M["hour"][i] in B or (M["hour"][i] + 1) in B))):
            i = (i + 1) % T; waited += 1
        return i, waited
    def resolve(self, i, d, l, w, s, cost, flat_weekend, flat_daily, rng, contract=None):
        """bracket opened at bar i's open in direction d; returns (pnl, bars until exit incl. exit bar)"""
        if contract:                                   # whole contracts, rounded down (as pathfirm.PathTrader.trade)
            n = max(1, math.floor(l / (contract * s) + 1e-9)); f = n * contract * s / l; l *= f; w *= f
        M = self.M; T = M["T"]; notional = l / s; e = M["O"][i]; fee = cost * notional; wg = w + fee
        sl = e * (1 - d * s); tp = e * (1 + d * s * wg / l)
        rolls = 0; bars = 0; first = True; last = e; exit_px = None
        while True:
            if M["ok"][i]:
                o = M["O"][i]
                if not first:
                    if M["roll"][i]: rolls += 1
                    if d * (o - sl) <= 0 or d * (o - tp) >= 0: exit_px = o; break
                    if flat_daily is not None and M["hour"][i] == flat_daily: exit_px = o; break
                    if self.block and M["hour"][i] in self.block: exit_px = o; break
                if d > 0: hs = M["L"][i] <= sl; ht = M["H"][i] >= tp
                else:     hs = M["H"][i] >= sl; ht = M["L"][i] <= tp
                if hs or ht:
                    won = ht if not (hs and ht) else PF.first_touch(M, i, d, sl, tp, l / (l + wg), rng)
                    exit_px = tp if won else sl; break
                last = M["C"][i]
                if flat_weekend and M["fri_close"][i]: exit_px = last; break
            first = False; bars += 1; i += 1
            if i >= T: exit_px = last; break
        pnl = notional * d * (exit_px - e) / e - fee - M["fin"] * notional * rolls
        return pnl, bars + 1
    def rule_direction(self, i, rng, rule):
        if rule == "random": return 1 if rng.random() < 0.5 else -1
        M = self.M; C = M["C"]; ok = M["ok"]; T = M["T"]; closes = []; j = i - 1
        while len(closes) < 6 and j > i - 400:
            if ok[j % T]: closes.append(C[j % T])
            j -= 1
        if len(closes) < 6: return 1 if rng.random() < 0.5 else -1
        return 1 if closes[0] > closes[-1] else -1

def run_life(slots, data="synth", months=12, seed=1, rule="trend5", m=0.75, stagger_days=0.0, cost_mult=1.0,
             news=False, budget=None, share=True):
    """slots: list of dict(firm=name, kind=cfd|fut, L, k, X1, X, m, instr, [gap_days, start_day]). Returns the ledger and
    trade/overlap statistics. data: "synthN" (12-year path N shared by many lives), "synthNyY" (a Y-year path for this
    life alone; gold, euro and yen get their own independent paths N+50, N+70, N+60) or "corrR_NyY" (all four markets on
    one joint path with pairwise correlation R/100)."""
    rng = random.Random(seed)
    corr = data.startswith("corr")
    mk = {"US100": Market("US100", data, news), "MNQ_fut": Market("MNQ_fut", data, news)}
    for instr, off in (("XAUUSD", 50), ("EURUSD", 70), ("USDJPY", 60)):
        if any(sp.get("instr") == instr for sp in slots):
            assert data.startswith(("synth", "corr")), "gold, euro and yen slots are simulated on synthetic paths only"
            mk[instr] = Market(instr, data if corr else PF.sibling(data, off), news)
            assert mk[instr].M["T"] == mk["US100"].M["T"]
    GROUP = {"US100": "NQ", "MNQ_fut": "NQ", "XAUUSD": "XAU", "USDJPY": "JPY", "EURUSD": "EUR"}
    T = mk["US100"].M["T"]
    # one calendar for everybody: clock 0 = 22:00 UTC on a random day early in the path
    h0 = mk["US100"].M["h0"]
    base = 24 * rng.randrange(T // 48 // 2) + (22 - h0) % 24
    assert mk["MNQ_fut"].M["T"] == T and mk["MNQ_fut"].M["h0"] == h0
    t_end = months * 30.44 * DAY
    assert base + t_end + 60 * DAY < T, "price path too short for this horizon"
    wallet = Wallet(budget) if budget is not None else None
    ledger = []; gens = {}; pend = {}; heap = []; info = {}
    for sid, sp in enumerate(slots):
        F = rules(sp)
        if sp.get("lev"): F["lev"] = sp["lev"]
        instr = sp.get("instr") or ("US100" if sp["kind"] == "cfd" else "MNQ_fut")
        srng = random.Random(seed * 1000 + sid)
        s = (sp.get("m") or m) * mk[instr].M["sig"]; cost = mk[instr].M["cost"] * cost_mult
        contract = 2.0 * 31070.0 if instr == "MNQ_fut" else None     # as pathfirm.PathTrader: whole micro contracts
        g = g_slot(sid, F, sp["L"], sp["k"], sp["X1"], sp["X"], srng, t_end, ledger, sp.get("start_day", 0) * DAY,
                   rho=cost / s, min_l=contract * s if contract else 0.0, s=s, wallet=wallet, gap_days=sp.get("gap_days", 0.0))
        info[sid] = dict(F=F, instr=instr, rng=srng, s=s, cost=cost, flat_daily=F.get("flat_daily"), contract=contract)
        gens[sid] = g
        try:
            req = next(g)
        except StopIteration:
            continue
        _push(sid, req, heap, pend, mk, info, base)
    open_pos = []          # (entry_bar_abs, exit_bar_abs, direction, group)
    n_trades = 0; n_copy = 0; conflicts = 0; trade_log = []
    while heap:
        e_abs, sid = heapq.heappop(heap)
        req, w_hours = pend.pop(sid)
        try:
            if req[0] == "wait":
                req = gens[sid].send(None)
                _push(sid, req, heap, pend, mk, info, base); continue
        except StopIteration:
            continue
        clock, l, w, fw = req
        inf = info[sid]; M = mk[inf["instr"]]
        open_pos = [p for p in open_pos if p[1] > e_abs]
        grp = GROUP[inf["instr"]]
        dirs = set(p[2] for p in open_pos if p[0] <= e_abs and p[3] == grp)
        if len(dirs) > 1: conflicts += 1
        if dirs and share: d = next(iter(dirs)); n_copy += 1
        else: d = M.rule_direction(e_abs % T, inf["rng"], rule)      # (share=False: diagnostic only, not the plan)
        pnl, bars = M.resolve(e_abs % T, d, l, w, inf["s"], inf["cost"], fw, inf["flat_daily"], inf["rng"], inf["contract"])
        open_pos.append((e_abs, e_abs + bars, d, grp)); n_trades += 1
        trade_log.append((e_abs - base, sid))
        hours = float(w_hours + bars)
        try:
            req = gens[sid].send((pnl, hours))
            _push(sid, req, heap, pend, mk, info, base)
        except StopIteration:
            pass
    return ledger, dict(trades=n_trades, copied=n_copy, conflicts=conflicts, trade_log=trade_log,
                        wallet_low=wallet.low if wallet else None, wallet_end=wallet.cash if wallet else None)

def _push(sid, req, heap, pend, mk, info, base):
    if req[0] == "wait":
        pend[sid] = (req, 0); heapq.heappush(heap, (base + int(req[1]), sid)); return
    clock, l, w, fw = req
    inf = info[sid]; M = mk[inf["instr"]]
    i_abs = base + int(clock)
    T = M.M["T"]
    e, waited = M.entry_index(i_abs % T, fw, inf["flat_daily"])
    e_abs = i_abs + waited
    pend[sid] = (req, waited)
    heapq.heappush(heap, (e_abs, sid))

def monthly(ledger, months=12):
    out = np.zeros(months)
    for row in ledger:
        t, cash = row[0], row[3]
        mth = int(t // (30.44 * DAY))
        if 0 <= mth < months: out[mth] += cash
    return out

if __name__ == "__main__":
    cfg = json.loads(sys.argv[1])
    ledger, st = run_life(**cfg)
    print(st, monthly(ledger).round(0))
