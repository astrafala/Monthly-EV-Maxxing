import random, math, json, numpy as np
import sim_compliant as C
def sizing_bold(x, target, rr=None, risk_cap=None, buffer=None):
    room = (x + C.B) * 0.97
    l = min(5000.0 * 0.97, room)
    if l < 25: l = max(x + C.B - 1.0, 1.0)
    w = (target - x + 50) if target is not None else 5000.0
    return max(w, 100.0), l
C.sizing = sizing_bold
# funded: first target 500, later cycles aim +5000 and wait
def funded(clock, rng, rr, cycle_days=14):
    x=0.0; paid=0.0; first=True; n=0; npay=0
    while x > -C.B + 1e-6 and n < 4000:
        n += 1
        if n % cycle_days == 0 and x > 0:
            paid += 0.8*x + (C.FEE if first else 0); first=False; x=0.0; npay+=1
        h = 500.0 if first else 5000.0
        if x >= h:
            clock.advance_to(C.S.next_entry(clock.i, rng) or C.S.next_entry(0, rng)); continue
        w, l = sizing_bold(x, h)
        x += C.trade(clock, w, l, rng); x = max(x, -C.B)
    return paid, n, npay
C.funded = funded
rng = random.Random(77); M = 3000
res = [C.attempt(rng, 1.0) for _ in range(M)]
ev = np.array([r["ev"] for r in res]); wk = np.array([r["weeks"] for r in res])
st = np.array([r["stage"] for r in res])
out = dict(EV=float(ev.mean()), CI=float(1.96*ev.std()/math.sqrt(M)), Pf=float(np.mean(st>=2)),
           weeks_mean=float(wk.mean()), weeks_med=float(np.median(wk)),
           weeks_funded=float(np.mean([r["wf"] for r in res if r["stage"]==2])))
print(out); json.dump(out, open("bold_time.json","w"))
