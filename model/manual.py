import json, calibrate as CB, acct_mc as A
f, c, fin, hrs = CB.INSTR["US100"]
CB.INSTR["US100_manual"] = (f, c, fin, (13, 19))     # enter only 13:00-19:59 UTC (US session)
out = CB.calibrate("US100_manual", ms=(0.75, 1, 1.5), ks=(2, 3), n=6000, seed=4)
cost = c/100; fn = fin/100
res = []
for g in out["grid"]:
    g["kappa"] = cost/g["s"]; g["phi"] = fn*g["rolls"]/g["s"]
    pt = dict(edge=-g["kappa"]-g["phi"], kappa=g["kappa"], phi=g["phi"], dur=g["dur"])
    r = A.evaluate(A.firm_defs()["FTMO 2-Step"], pt, L=1500, k=g["k"], X1=1000, X=10000, n=3000, seed=3)
    r.update(m=g["m"], k=g["k"], hours=g["hours"]); res.append(r)
    print(g["m"], g["k"], round(g["hours"],1), round(r["EV"]), round(r["days"]), round(r["EV_month"]), r["t_first_pay"])
json.dump(res, open("manual.json","w"), default=float)
