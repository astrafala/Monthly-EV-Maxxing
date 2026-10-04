import sys, json, multiprocessing as mp
import multi

def job(cfg):
    out = cfg.pop("out")
    r = multi.run(**cfg)
    with open(out, "a") as f: f.write(json.dumps(r) + "\n")
    return r

if __name__ == "__main__":
    cfgs = json.load(open(sys.argv[1]))
    with mp.Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4) as p:
        for r in p.imap_unordered(job, cfgs):
            print(r["tag"], r["data"], round(r["EV"]), "+-", round(r["CI"]), "days", round(r["days"], 1),
                  "EV/mo", round(r["EV_month"]), "pass", [round(x, 3) for x in r["pass_by_phase"]], flush=True)
