import acct_mc as A, random
# synthetic fair-coin calibration point: zero edge, zero cost, every trade lasts 24h
pt = dict(edge=0.0, kappa=0.0, phi=0.0, dur=[24.0])
F = A.firm_defs()
for name in ["FTMO 2-Step", "FTMO 1-Step", "FundingPips 2-Step (bi-weekly 80%)", "Breakout 2-Step (crypto)", "HyroTrader 2-Step (crypto)"]:
    r = A.evaluate(F[name], pt, L=1000, k=1, X1=1000, X=10000, n=3000)
    print(f"{name:36s} EV={r['EV']:7.0f}±{r['CI']:4.0f} Pf={r['Pf']:.3f} days={r['days']:6.0f} EV/mo={r['EV_month']:6.0f} first pay={r['t_first_pay']}")
FF = A.futures_defs()
for name in FF:
    r = A.evaluate(FF[name], pt, L=500, k=1, X1=0, X=0, n=3000)
    print(f"{name:36s} EV={r['EV']:7.0f}±{r['CI']:4.0f} Pf={r['Pf']:.3f} days={r['days']:6.0f} EV/mo={r['EV_month']:6.0f} first pay={r['t_first_pay']}")
