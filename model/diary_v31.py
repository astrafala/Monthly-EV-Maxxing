"""Sign-up diary: the median life of the staged full-caps portfolio, week by week."""
import json, collections, numpy as np
import lockstep as LS, lockstep_portfolio as LP
DAY = 24.0
slots = LP.PORTFOLIOS["Full caps, staged start"]
firm_of = [s["firm"] for s in slots]
cands = []
for j in range(60):
    sd = 21 + j % 8
    ledger, st = LS.run_life(slots, data=f"synth{sd}", seed=7000 + j, rule="trend5")
    ledger.sort()
    tot12 = sum(c for (t, sid, k, c) in ledger if t <= 12 * 30.44 * DAY)
    cands.append((tot12, j, sd, ledger, st))
cands.sort(key=lambda x: x[0])
tot12, j, sd, ledger, st = cands[len(cands) // 2]
print("median life: 12-month cash", round(tot12), "seed", 7000 + j, "path", sd, "| lives' 12m p10/p50/p90:",
      [round(cands[int(q * (len(cands) - 1))][0]) for q in (0.1, 0.5, 0.9)])
rows = []
cum = 0.0; active_funded = set()
def week_of(t): return int(t // (7 * DAY))
by_week = collections.defaultdict(list)
for e in ledger:
    if e[0] <= 13 * 7 * DAY: by_week[week_of(e[0])].append(e)
low = 0.0
for w in range(13):
    ev = by_week.get(w, [])
    buys = [e for e in ev if e[2] == "buy"]; fees = -sum(e[3] for e in ev if e[3] < 0)
    p1 = sum(1 for e in ev if e[2] == "phase1_pass"); f1 = sum(1 for e in ev if e[2] == "phase1_fail")
    funded = sum(1 for e in ev if e[2] == f"phase{2}_pass" or (e[2] == "phase1_pass" and False))
    fail2 = sum(1 for e in ev if e[2] == "phase2_fail"); lost = sum(1 for e in ev if e[2] == "funded_end")
    pays = [e for e in ev if e[2] == "payout"]; cash_in = sum(e[3] for e in pays)
    for e in sorted(ev):
        cum += e[3]; low = min(low, cum)
    firms_new = sorted(set(firm_of[e[1]].split(" ")[0] for e in buys))
    rows.append(dict(week=w + 1, buys=len(buys), fees=round(fees), p1_pass=p1, p1_fail=f1, funded=funded, p2_fail=fail2,
                     funded_lost=lost, payouts=len(pays), cash_in=round(cash_in), cum=round(cum), firms=firms_new))
    print(rows[-1])
mon = LS.monthly(ledger)
print("monthly cash months 1-12:", mon.round(0).tolist(), " cum:", mon.cumsum().round(0).tolist(), " low point:", round(low))
json.dump(dict(rows=rows, monthly=mon.tolist(), tot12=tot12, low13w=low, ledger_sample=[(round(t / DAY, 2), firm_of[s], k, round(c)) for (t, s, k, c) in ledger if t <= 30 * DAY]),
          open("diary_v31.json", "w"), indent=0)
