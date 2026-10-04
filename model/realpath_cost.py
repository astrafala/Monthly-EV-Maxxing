import sys, json, realpath as RP, calibrate as CB
mult = float(sys.argv[1])
nm = "US100"
f, c, fin, hrs = CB.INSTR[nm]
CB.INSTR[nm] = (f, c * mult, fin * mult, hrs)
r = RP.run(nm, 0.75, 3, 1500, 1000, 10000, 1500, seed=9)
r["cost_mult"] = mult
print(json.dumps(r)); json.dump(r, open(f"real_cost_{mult}.json", "w"))
