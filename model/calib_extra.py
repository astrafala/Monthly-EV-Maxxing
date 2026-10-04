import json, sys
import calibrate as C
nm = sys.argv[1]
out = C.calibrate(nm, ms=(0.5, 0.75, 1, 1.5, 2), ks=(3,) if len(sys.argv) < 3 else (1, 2, 3), n=8000, seed=3)
json.dump(out, open(f"calibx_{nm}.json", "w"), default=float)
