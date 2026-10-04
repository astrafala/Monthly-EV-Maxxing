import json, math, sys
from engine import (eval_pass_prob, intraday_trailing_pass_prob, funded_value_static,
                    funded_value_trail_lock)
from firms import F

def phase_prob(ph, kappa, compliant=False, size=100_000, market="CFD"):
    A, D, typ, dll, cap = ph
    mlb = mwb = None
    if compliant:
        mlb = 0.01 * size if market == "CFD" else 0.25 * D
        mwb = 2 * mlb
    if typ == "intraday":
        p = intraday_trailing_pass_prob(A, D, kappa)
        return p
    g = D / (40 if typ == "static" else 20)
    if compliant:
        g = min(g, mlb / 2)
        if typ == "eod":
            g = max(g, D / 20)
    p, _ = eval_pass_prob(A, D, trailing=(typ == "eod"), dll=dll, daily_cap=cap,
                          kappa=kappa, g=g, max_loss_bet=mlb, max_win_bet=mwb)
    return float(p)

def funded(fd, kappa, size, compliant=False):
    if fd["kind"] == "static":
        k_eff = kappa
        if compliant:
            # small bets: cost fraction ~ kappa * D / L instead of 2 kappa
            L = 0.01 * size
            k_eff = kappa * fd["D"] / L / 2
        v, q = funded_value_static(fd["D"], fd["split"], k_eff, fd.get("refund", 0),
                                   fd.get("refund_after", 1), first_payout=0.005 * size)
        return v
    k_eff = kappa * (2.0 if compliant else 1.0)
    return funded_value_trail_lock(fd["D"], fd["split"], k_eff, c=fd.get("c", 100.0),
                                   total_cap=fd.get("cap"), intraday=fd.get("intraday", False))

def evaluate(row, kappa, compliant=False):
    ps = [phase_prob(ph, kappa, compliant, row["size"], row["market"]) for ph in row["phases"]]
    P = 1.0
    for p in ps:
        P *= p
    vf = funded(row["funded"], kappa, row["size"], compliant)
    ev = -row["fee"] + P * (vf - row["activation"])
    return dict(ps=ps, P=P, VF=vf, EV=ev)

def upper_bound(row):
    """Rigorous zero-edge, frictionless bound: product of B/(A+B) (or exp(-A/D) for
    intraday trailing) times split*D (+ refund)."""
    P = 1.0
    for (A, D, typ, dll, cap) in row["phases"]:
        P *= math.exp(-A / D) if typ == "intraday" else D / (A + D)
    fd = row["funded"]
    vf = fd["split"] * fd["D"] + fd.get("refund", 0)
    return -row["fee"] + P * (vf - row["activation"])

if __name__ == "__main__":
    out = []
    for row in F:
        r = dict(firm=row["firm"], prog=row["prog"], market=row["market"], size=row["size"],
                 fee=round(row["fee"], 2), activation=row["activation"], conf=row["conf"],
                 note=row["note"], monthly=row["monthly"],
                 D_funded=row["funded"]["D"], split=row["funded"]["split"],
                 phases=row["phases"], funded_kind=row["funded"]["kind"])
        r["UB"] = upper_bound(row)
        for tag, k, comp in [("k0", 0.0, False), ("k1", 0.01, False), ("k2", 0.02, False),
                             ("c1", 0.01, True)]:
            e = evaluate(row, k, comp)
            r[tag] = e
        out.append(r)
        print(f"{row['firm']:18s} {row['prog']:28s} fee {row['fee']:7.0f}  UB {r['UB']:8.0f} | "
              f"k0 P={r['k0']['P']:.3f} VF={r['k0']['VF']:7.0f} EV={r['k0']['EV']:7.0f} | "
              f"k1 P={r['k1']['P']:.3f} EV={r['k1']['EV']:7.0f} | k2 EV={r['k2']['EV']:7.0f} | "
              f"compliant EV={r['c1']['EV']:7.0f}", flush=True)
    json.dump(out, open("results.json", "w"), indent=1, default=float)
