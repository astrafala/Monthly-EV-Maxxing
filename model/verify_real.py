# re-run the real-data bold strategy and report each stage separately, to look for bugs
import random, math, numpy as np
import sim_real as S
rng = random.Random(99)
M = 4000
p1 = p2 = 0; paids = []; evs = []
for _ in range(M):
    i = S.ENTRY_OK[rng.randrange(len(S.ENTRY_OK) // 2)]
    ok, i, _ = S.phase(10_000, 10_000, 5000, i, rng, S.bold)
    if not ok: evs.append(-632); continue
    p1 += 1
    ok, i, _ = S.phase(5_000, 10_000, 5000, i, rng, S.bold)
    if not ok: evs.append(-632); continue
    p2 += 1
    paid, _ = S.funded(i, rng, "bold")
    paids.append(paid); evs.append(-632 + paid)
paids = np.array(paids)
print(f"P(pass1)={p1/M:.3f}  P(pass2|pass1)={p2/p1:.3f}  P(funded)={p2/M:.3f}")
print(f"E[paid|funded]={paids.mean():.0f} +- {1.96*paids.std()/math.sqrt(len(paids)):.0f}   "
      f"P(no payout|funded)={np.mean(paids==0):.3f}  max={paids.max():.0f}")
print(f"EV={np.mean(evs):.0f} +- {1.96*np.std(evs)/math.sqrt(M):.0f}")
