"""Per-person portfolios: EV per month, fee outlay, and the spread of outcomes when slots move together or independently."""
import json, numpy as np
T = json.load(open("timeline_v3.json")); F = json.load(open("final_v3.json"))
H = ["1", "2", "3", "6", "9", "12"]
CFD7 = {"FTMO 2-Step": 4, "FundingPips 2-Step (bi-weekly 80%)": 4, "FundedNext Stellar 2-Step": 3,
        "The5ers High Stakes": 1, "Alpha Capital Pro 10%": 3, "FXIFY Two-Phase": 4, "GFT 2-Step Standard": 4}
PORTF = {
  "FTMO only: 4 x 100K": {"FTMO 2-Step": 4},
  "Five best-documented CFD firms: 15 slots": {k: CFD7[k] for k in ("FTMO 2-Step", "FundingPips 2-Step (bi-weekly 80%)", "FundedNext Stellar 2-Step", "The5ers High Stakes", "Alpha Capital Pro 10%")},
  "Seven CFD firms: 23 slots": CFD7,
  "Seven CFD firms + Topstep: 23 + 5": dict(CFD7, **{"Topstep 50K": 5}),
}
if __name__ == "__main__":
    rs = np.random.default_rng(9)
    A = {f: {h: np.array(T[f][h]) for h in H + ["worst"]} for f in T}
    order = {f: np.argsort(A[f]["12"]) for f in A}
    out = {}
    for pname, P in PORTF.items():
        r = dict(slots=P, n_slots=sum(P.values()))
        r["EV_month"] = sum(n * F[f]["synth"]["EV_month"] for f, n in P.items())
        r["EV_month_CI"] = float(np.sqrt(sum((n * F[f]["synth"]["EV_month_CI"]) ** 2 for f, n in P.items())))
        r["EV_month_real"] = sum(n * F[f]["real"]["EV_month"] for f, n in P.items())
        r["fees_month"] = sum(n * (F[f]["fee"] + F[f]["synth"]["P"] * F[f]["activation"]) * 30.44 / F[f]["synth"]["days"] for f, n in P.items())
        N = 20000
        path = np.zeros((N, len(H)))
        for f, n in P.items():
            for _ in range(n):
                idx = rs.integers(0, len(A[f]["12"]), N); path += np.stack([A[f][h][idx] for h in H], 1)
        trough_i = np.minimum(path.min(1), 0)
        u = rs.random(N); pt = np.zeros((N, len(H))); wt = np.zeros(N)
        for f, n in P.items():
            idx = order[f][(u * len(order[f])).astype(int)]
            pt += n * np.stack([A[f][h][idx] for h in H], 1); wt += n * A[f]["worst"][idx]
        for mode, M, tr in (("together", pt, wt), ("independent", path, trough_i)):
            for j, h in enumerate(H):
                r[f"{mode}_P_ahead_{h}"] = float(np.mean(M[:, j] > 0)); r[f"{mode}_median_{h}"] = float(np.median(M[:, j]))
                r[f"{mode}_p05_{h}"] = float(np.percentile(M[:, j], 5)); r[f"{mode}_p95_{h}"] = float(np.percentile(M[:, j], 95))
            r[f"{mode}_trough_median"] = float(np.median(tr)); r[f"{mode}_trough_p05"] = float(np.percentile(tr, 5))
        out[pname] = r
        print(f"{pname}: EV/mo {r['EV_month']:,.0f} ± {r['EV_month_CI']:,.0f} (real-path {r['EV_month_real']:,.0f}); fees/mo {r['fees_month']:,.0f}")
        for mode in ("together", "independent"):
            print("   ", mode, " ".join(f"{h}m:{r[f'{mode}_P_ahead_{h}']:.2f}" for h in H),
                  f"| med12 {r[f'{mode}_median_12']:,.0f} p05_12 {r[f'{mode}_p05_12']:,.0f} | trough med {r[f'{mode}_trough_median']:,.0f} p05 {r[f'{mode}_trough_p05']:,.0f}")
    json.dump(out, open("portfolio_v3.json", "w"), indent=1)
