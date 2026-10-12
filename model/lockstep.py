"""
Lockstep simulation of one person running many accounts at once.

Every account follows its firm's rules (the same rule code as acct_mc, turned into generators), on ONE shared
hourly price path and ONE calendar. Every event - a trade's entry, a purchase, a wait - is processed in the order of its
time, so the shared-direction rule can be enforced exactly: a new position takes the direction of any position still
open on any account in the same market (by the positions' actual exit times; version 9: version 8 kept a position open
until the next entry was allowed, review of version 8, finding 11); if none is open, the written rule decides (5-hour
momentum). No two accounts ever hold opposite positions.

Each slot buys a new evaluation as soon as its previous attempt ends (failed phase or lost funded account). With a finite
budget a purchase is an event at its own time: it is paid from the cash that has arrived by then (starting cash, minus
earlier purchases, plus payouts received by that time), and waits a day at a time otherwise (version 9: version 8 let a
purchase made while processing a later event release a payout dated after an earlier purchase, review of version 8,
finding 1). Every fee, pass, failure and payout is written to a ledger with its date.
"""
import heapq, random, math, json, copy, inspect, sys
import numpy as np
import acct_mc as A, pathfirm as PF, firms_v5 as F5

# ---------------------------------------------------------------- generator versions of the rule engine
_ns = dict(A.__dict__)
_src_stage = inspect.getsource(A.run_stage).replace("def run_stage(", "def g_run_stage(")
_a = 'pnl, h = tr.trade(l, w, clock, fw, opts)'
assert _src_stage.count(_a) == 1
_src_stage = _src_stage.replace(_a, 'pnl, h = yield ("trade", clock, l, w, fw, opts)')
_src_fund = inspect.getsource(A.run_funded).replace("def run_funded(", "def g_run_funded(")
assert _src_fund.count(_a) == 1
_src_fund = _src_fund.replace(_a, 'pnl, h = yield ("trade", clock, l, w, fw, opts)')
_src_fund = _src_fund.replace("if PAYLOG is not None: PAYLOG.append(", 'if fd.get("_paylog") is not None: fd["_paylog"].append(')
exec(_src_stage, _ns); exec(_src_fund, _ns)
g_run_stage, g_run_funded = _ns["g_run_stage"], _ns["g_run_funded"]
DAY = A.DAY

class _T:      # what the rule engine reads from the trader; the market calendar comes from the life's shared path
    def __init__(self, L, k, rho=0.0, min_l=0.0, s=1.0, M=None, base=0, flat_daily=None, futures=False, m=1.0, cost=0.0):
        self.L = L; self.k = k; self.rho = rho; self.min_l = min_l; self.s = s; self.cost = cost
        self.M = M; self.base = base; self.flat_daily = flat_daily; self.futures = futures
        self.wmin_frac = max(0.0, PF.WMIN_SD / m - rho) if M is not None else 0.0
        self.last_entry = None; self.last_exit = None; self.last_info = None; self.block = None
        self.news = None                       # the current stage's news rule (set by the rule engine), news_v10
    @property
    def nb(self):
        return PF.news_bars(self.M, self.news) if self.M is not None else None
    def _idx(self, clock): return (self.base + int(clock)) % self.M["T"]
    def utc(self, clock):
        return PF.EPOCH + PF._dt.timedelta(hours=self._idx(clock) + (clock - math.floor(clock)))
    def lmin_at(self, clock, flat_weekend=False):
        """the risk of the smallest position (0.01 lot, one micro contract) at the next entry's price"""
        if self.M is None: return self.min_l
        i, _ = PF.entry_index(self.M, self._idx(PF.next_bar(clock)), flat_weekend, self.flat_daily, self.block, nb=self.nb)
        return PF.min_risk(self.M, self.M["O"][i], self.s)
    def plan_at(self, clock, l, w, opts=None, flat_weekend=False):
        """the position the next trade would place (pathfirm.plan) at the next entry's open price"""
        i, _ = PF.entry_index(self.M, self._idx(PF.next_bar(clock)), flat_weekend, self.flat_daily, self.block, nb=self.nb)
        o = dict(opts or {})
        if "keep_w" not in o: o["keep_w"] = l > 0 and w < self.k * l * (1 - 1e-9)
        return PF.plan(self.M, i, l, w, self.s, self.cost, o)
    def bdays(self, clock, n):
        if self.M is None: return clock + n * DAY * 7.0 / 5.0
        return PF.add_bdays(self.M, self._idx, clock, n)
    def next_entry(self, clock, flat_weekend=False):
        """the time the next trade would open on the life's market (news-blocked hours included), as _push computes it"""
        if self.M is None: return clock
        c0 = PF.next_bar(clock)
        _, waited = PF.entry_index(self.M, self._idx(c0), flat_weekend, self.flat_daily, self.block, nb=self.nb)
        return float(c0 + waited)

def g_slot(sid, firm, L, k, X1, X, rng, t_end, ledger, start=0.0, rho=0.0, min_l=0.0, s=1.0, wallet=None, gap_days=0.0,
           tr=None, ref=None, firm_name=None):
    """one account slot, attempts back to back from `start` until t_end (hours).
    Ledger rows: (time, slot, kind, bank cash, attempt number). Non-cash credits (The5ers) are rows of kind
    'credit_earned' / 'credit_used' with zero cash; a purchase pays only the part of the fee the slot's credit does not cover.
    wallet: a shared finite cash budget; a purchase waits (checked daily) until the wallet holds its cash.
    gap_days: the plan waits this long after a failed attempt before buying the next one (pacing)."""
    tr = tr or _T(L, k, rho, min_l, s); clock = float(start); att = 0; credit = 0.0
    if wallet is not None:
        assert not firm["monthly"] and not firm.get("activation"), "finite budgets: purchase fees only"
    while clock < t_end:
        use = min(credit, firm["fee"]); cash_fee = firm["fee"] - use
        if wallet is not None:                       # the purchase is an event at its own time (version 9)
            while not (yield ("buy", clock, cash_fee)):
                clock += 24.0
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
        fd = copy.deepcopy(firm["funded"]); fd["_paylog"] = _PayLog(ledger, sid, att, wallet, ref, firm_name)
        if fd.get("refund") and firm.get("refund_frac") is not None:
            # the refund is a share of the cash actually paid for this account; fee paid with credit is not refunded
            # (The5ers; version 10: version 9 refunded 70% of the listed fee, review of version 9, finding 17)
            fd["refund"] = firm["refund_frac"] * cash_fee
        f2 = dict(firm); f2["funded"] = fd
        paid, clock, tfirst, npay = yield from g_run_funded(fd, tr, rng, f2, clock, X1, X)
        ledger.append((clock, sid, "funded_end", 0.0, att))
        clock += gap_days * DAY
    if credit > 0: ledger.append((t_end, sid, "credit_left", 0.0, att))

class _PayLog(list):
    """every payout written to the ledger, and made available to a finite budget, when it is requested, dated when its cash
    arrives (version 8: version 7 wrote an account's payouts only when the account ended, so a budget received them late,
    and an account still open at the end of a life had to be traded to its end before they were recorded). Version 10: a
    payout cancelled by a breach before it was processed is taken back by a 'payout_cancelled' row on the same date; with
    refusal scenarios (ref), each request may be refused (Refusals)"""
    def __init__(self, ledger, sid, att, wallet, ref=None, firm=None):
        super().__init__(); self.ledger = ledger; self.sid = sid; self.att = att; self.wallet = wallet
        self.ref = ref; self.firm = firm; self.rows = {}
    def append(self, item):
        tc, cash = item[0], item[1]
        kind = item[3] if len(item) > 3 else "payout"
        t_req = item[2]; t_proc = item[4] if len(item) > 4 else tc
        if kind == "payout_cancelled":
            i = self.rows.pop((round(tc, 9), round(-cash, 9)), None)
            if i is not None and self.ref is not None and i in self.ref.voided:
                return                                   # already voided by a refusal: nothing to take back
            if i is not None and self.ref is not None: self.ref.cancelled.add(i)
        self.ledger.append((tc, self.sid, kind, cash, self.att))
        if self.wallet is not None: self.wallet.receive(tc, cash)
        if kind == "payout":
            i = len(self.ledger) - 1; self.rows[(round(tc, 9), round(cash, 9))] = i
            if self.ref is not None: self.ref.on_payout(self.firm, self.ledger, i, t_req, t_proc, tc, cash, self.wallet)

class Refusals:
    """payout refusals drawn inside the event engine (version 10: version 9 removed a refused firm's later cash rows from a
    finished all-paid ledger, so the firm's open positions still steered the shared direction of the others: review of
    version 9, finding 12). Each payout request of a firm is refused with the scenario's probability for the firm's tier.
    A refusal at time t ends the plan's use of the firm then: the refused payout and every payout of the firm not processed
    by t are not paid (their ledger rows are voided, and a finite budget never receives them), and none of the firm's
    accounts trades or buys again after t (run_life drops their events), so the other accounts go on with the positions
    actually open"""
    def __init__(self, q, seed, tier_of):
        self.q = q; self.rng = random.Random(seed); self.tier_of = tier_of
        self.t_ref = {}; self.rows = {}; self.voided = set(); self.cancelled = set(); self.n_refused = 0
    def _void(self, ledger, i, wallet):
        if i in self.voided or i in self.cancelled: return
        tc, sid, kind, cash, att = ledger[i]
        ledger[i] = (tc, sid, "payout_void", 0.0, att); self.voided.add(i)
        if wallet is not None: wallet.receive(tc, -cash)          # dated after the refusal: never spent before it
    def on_payout(self, firm, ledger, i, t_req, t_proc, t_cash, cash, wallet):
        self.rows.setdefault(firm, []).append((t_req, t_proc, i, wallet))
        t_r = self.t_ref.get(firm)
        if t_r is not None and t_proc > t_r:
            self._void(ledger, i, wallet); return
        if self.rng.random() < self.q.get(self.tier_of(firm), 0.05):
            self.n_refused += 1
            if t_r is None or t_req < t_r:
                self.t_ref[firm] = t_req
                for (tq, tp, j, wl) in self.rows[firm]:
                    if tp > t_req: self._void(ledger, j, wl)
            self._void(ledger, i, wallet)

class Wallet:
    """a finite cash budget shared by every slot; payouts become spendable when they arrive. take() is called by the event
    loop in the order of time (asserted), so a purchase can only use receipts dated at or before it"""
    def __init__(self, cash):
        self.cash = float(cash); self.pending = []; self.low = float(cash); self.t_last = -1e18
    def receive(self, t, cash): heapq.heappush(self.pending, (t, cash))
    def pay_now(self, cash): self.cash += cash; self.low = min(self.low, self.cash)
    def take(self, t, fee):
        assert t >= self.t_last - 1e-9, "wallet used out of time order"
        self.t_last = t
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
    def entry_index(self, i, flat_weekend, flat_daily, nb=None):
        return PF.entry_index(self.M, i, flat_weekend, flat_daily, self.block, nb=nb)
    def resolve(self, i, d, l, w, s, cost, flat_weekend, flat_daily, rng, st=None, opts=None, nb=None):
        """position opened at bar i's open in direction d; returns (pnl, hours until the next entry may be considered,
        info) (pathfirm.resolve: the same code as the single-account engine)"""
        return PF.resolve(self.M, i, d, l, w, s, cost, flat_weekend, flat_daily, rng, block=self.block, st=st, opts=opts,
                          nb=nb)
    def rule_direction(self, i, rng, rule):
        if rule == "random": return 1 if rng.random() < 0.5 else -1
        M = self.M; C = M["C"]; ok = M["ok"]; T = M["T"]; closes = []; j = i - 1
        while len(closes) < 6 and j > i - 400:
            if ok[j % T]: closes.append(C[j % T])
            j -= 1
        if len(closes) < 6: return 1 if rng.random() < 0.5 else -1
        return 1 if closes[0] > closes[-1] else -1

def run_life(slots, data="synth", months=12, seed=1, rule="trend5", m=0.75, stagger_days=0.0, cost_mult=1.0,
             news=False, budget=None, share=True, refuse=None, bound=False):
    """slots: list of dict(firm=name, kind=cfd|fut, L, k, X1, X, m, instr, [gap_days, start_day]). Returns the ledger and
    trade/overlap statistics. data: "synthN" (12-year path N shared by many lives), "synthNyY" (a Y-year path for this
    life alone; gold, euro and yen get their own independent random streams of path N) or "corrR_NyY" (all four markets on
    one joint path with pairwise correlation R/100)."""
    rng = random.Random(seed)
    corr = data.startswith("corr")
    mk = {"US100": Market("US100", data, news), "MNQ_fut": Market("MNQ_fut", data, news)}
    for instr in ("XAUUSD", "EURUSD", "USDJPY"):      # each market its own random stream of the same path number
        if any(sp.get("instr") == instr for sp in slots):
            assert data.startswith(("synth", "corr")), "gold, euro and yen slots are simulated on synthetic paths only"
            mk[instr] = Market(instr, data, news)
            assert mk[instr].M["T"] == mk["US100"].M["T"]
    GROUP = {"US100": "NQ", "MNQ_fut": "NQ", "XAUUSD": "XAU", "USDJPY": "JPY", "EURUSD": "EUR"}     # the price path of each market
    # the shared direction (version 10): one direction per market, and EURUSD and USDJPY together, so that no two accounts
    # ever hold opposite dollar positions in currency pairs. The engine's EURUSD price is the euro in dollars and its USDJPY
    # price the yen in dollars (X = 1/USDJPY), so the same engine direction is the same dollar exposure on both: a long
    # EURUSD goes with a short USDJPY (both short the dollar)
    DGROUP = {"US100": "NQ", "MNQ_fut": "NQ", "XAUUSD": "XAU", "USDJPY": "USD", "EURUSD": "USD"}
    T = mk["US100"].M["T"]
    # one calendar for everybody: clock 0 = 22:00 UTC on a random day early in the path
    h0 = mk["US100"].M["h0"]
    base = 24 * rng.randrange(T // 48 // 2) + (22 - h0) % 24
    assert mk["MNQ_fut"].M["T"] == T and mk["MNQ_fut"].M["h0"] == h0
    t_end = months * 30.44 * DAY
    assert base + t_end + 60 * DAY < T, "price path too short for this horizon"
    wallet = Wallet(budget) if budget is not None else None
    ref = Refusals(refuse, seed * 7 + 3, lambda f: F5.TIER.get(f, "B")) if refuse else None
    ledger = []; gens = {}; pend = {}; heap = []; info = {}
    intervals = {}                 # market group -> [(first sub-step, end sub-step, log upper barrier, log lower barrier)]
    for sid, sp in enumerate(slots):
        F = rules(sp)
        if sp.get("lev"): F["lev"] = sp["lev"]
        instr = sp.get("instr") or ("US100" if sp["kind"] == "cfd" else "MNQ_fut")
        srng = random.Random(seed * 1000 + sid)
        mm = sp.get("m") or m
        s = mm * mk[instr].M["sig"]; cost = mk[instr].M["cost"] * cost_mult
        fut = instr == "MNQ_fut"                                      # whole micro contracts at each entry's price
        tr = _T(sp["L"], sp["k"], cost / s, 0.0, s, M=mk[instr].M, base=base, flat_daily=F.get("flat_daily"),
                futures=fut, m=mm, cost=cost)
        tr.block = mk[instr].block                                    # the news proxy's blocked hours, if any
        g = g_slot(sid, F, sp["L"], sp["k"], sp["X1"], sp["X"], srng, t_end, ledger, sp.get("start_day", 0) * DAY,
                   wallet=wallet, gap_days=sp.get("gap_days", 0.0), tr=tr, ref=ref, firm_name=F5.firm_of(sp["firm"]))
        info[sid] = dict(F=F, instr=instr, rng=srng, s=s, cost=cost, flat_daily=F.get("flat_daily"), futures=fut, tr=tr,
                         firm=F5.firm_of(sp["firm"]))
        gens[sid] = g
        try:
            req = next(g)
        except StopIteration:
            continue
        _push(sid, req, heap, pend, mk, info, base)
    open_pos = []          # (entry time, exit time, direction, group), absolute hours on the path
    stats = PF.Stats()
    n_trades = 0; n_copy = 0; conflicts = 0; trade_log = []
    while heap:
        key, _, sid = heapq.heappop(heap)
        req, w_hours = pend.pop(sid)
        if key - base > t_end + 31 * DAY:
            continue          # past the life's horizon: the account is no longer simulated (version 8: a funded Topstep
                              # account with its floor locked could otherwise trade on, on the wrapped path, for ever)
        if ref is not None and ref.t_ref.get(info[sid]["firm"]) is not None and key - base >= ref.t_ref[info[sid]["firm"]]:
            continue          # the firm refused a payout before this event: the plan no longer uses it
        try:
            if req[0] == "buy":                          # a purchase at its own time, from the cash arrived by then
                req = gens[sid].send(wallet.take(req[1], req[2]))
                _push(sid, req, heap, pend, mk, info, base); continue
            if req[0] == "wait":
                req = gens[sid].send(None)
                _push(sid, req, heap, pend, mk, info, base); continue
        except StopIteration:
            continue
        _, clock, l, w, fw, opts = req
        e_abs = key
        inf = info[sid]; M = mk[inf["instr"]]
        open_pos = [p for p in open_pos if p[1] > e_abs]                 # positions still open at this entry
        grp = GROUP[inf["instr"]]; dg = DGROUP[inf["instr"]]
        dirs = set(p[2] for p in open_pos if p[0] <= e_abs and p[3] == dg)
        if len(dirs) > 1: conflicts += 1
        if dirs and share: d = next(iter(dirs)); n_copy += 1
        else: d = M.rule_direction(e_abs % T, inf["rng"], rule)      # (share=False: diagnostic only, not the plan)
        o = dict(opts or {}); tr_ = inf["tr"]
        if "keep_w" not in o: o["keep_w"] = l > 0 and w < tr_.k * l * (1 - 1e-9)
        pnl, bars, ex = M.resolve(e_abs % T, d, l, w, inf["s"], inf["cost"], fw, inf["flat_daily"], inf["rng"], st=stats, opts=o,
                                  nb=tr_.nb)
        if ex["why"] != "unaffordable":                                # (no position is opened then)
            open_pos.append((e_abs, e_abs + ex["exit"], d, dg)); n_trades += 1
            trade_log.append((e_abs - base, sid, d, e_abs - base + ex["exit"], bool(dirs) and share, dg))
            if bound and M.M.get("sub"):                                # the barriers the trade watches, by sub-step
                sb = M.M["sub"]; j0 = (e_abs % T) * sb; j1 = j0 + int(round(ex["exit"] * sb))
                up = math.log(ex["tp"]) if (d > 0 and ex.get("tp")) else (math.log(ex["lo_px"]) if d < 0 and ex["lo_px"] < math.inf else math.inf)
                lo = math.log(ex["lo_px"]) if (d > 0 and ex["lo_px"] > 0) else (math.log(ex["tp"]) if d < 0 and ex.get("tp") else -math.inf)
                if j1 > j0: intervals.setdefault(grp, []).append((j0, j1, up, lo))
        hours = float(e_abs - base - clock) + float(bars)          # from the clock to the next permitted consideration
        tr_.last_entry = float(e_abs - base); tr_.last_exit = float(e_abs - base) + ex["exit"]; tr_.last_info = ex
        try:
            req = gens[sid].send((pnl, hours))
            _push(sid, req, heap, pend, mk, info, base)
        except StopIteration:
            pass
    jb = None
    if bound:
        rep = {"NQ": "US100", "XAU": "XAUUSD", "EUR": "EURUSD", "JPY": "USDJPY"}
        jb = {g: PF.joint_bound(mk[rep[g]].M, iv) for g, iv in intervals.items()}
    return ledger, dict(trades=n_trades, copied=n_copy, conflicts=conflicts, trade_log=trade_log, stats=stats.as_dict(),
                        wallet_low=wallet.low if wallet else None, wallet_end=wallet.cash if wallet else None,
                        refusals=dict(ref.t_ref) if ref else None, n_refused=ref.n_refused if ref else 0, joint_bound=jb)

_SEQ = [0]
def _push(sid, req, heap, pend, mk, info, base):
    _SEQ[0] += 1
    if req[0] in ("wait", "buy"):
        pend[sid] = (req, 0); heapq.heappush(heap, (base + float(req[1]), _SEQ[0], sid)); return
    _, clock, l, w, fw, opts = req
    inf = info[sid]; M = mk[inf["instr"]]
    i_abs = base + PF.next_bar(clock)
    T = M.M["T"]
    e, waited = M.entry_index(i_abs % T, fw, inf["flat_daily"], nb=inf["tr"].nb)
    e_abs = i_abs + waited
    pend[sid] = (req, waited)
    heapq.heappush(heap, (e_abs, _SEQ[0], sid))

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
