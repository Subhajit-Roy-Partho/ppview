import csv, json, os, re, glob
ROOT = "/scratch/sroy85/Github/dna/large_crystal"
rows = [r for r in csv.DictReader(open("yield.csv")) if r["T"] != "ERR" and r["N"] != "2048"]
def started_from_prior(d):
    p = f"{ROOT}/{d}/meta.json"
    if os.path.exists(p):
        try:
            c = json.load(open(p)).get("conf", "")
            return c.endswith("final_conf.dat")
        except Exception: pass
    return False
def key(d):
    parent, base = d.rsplit("/", 1)
    b = re.sub(r"_?T_?\d\.\d+", "", base)           # drop temperature
    b = re.sub(r"_(r|rep)\d+$", "", b)               # drop replicate id
    b = re.sub(r"_[a-z]$", "", b)
    return parent + "/" + b
skip = lambda d: ("archive" in d or d.startswith("phase_diagram/results/") or "/unattached/" in d
                  or started_from_prior(d) or "/melting/" in d or "/anneal/" in d)
best = {}
for r in rows:
    if skip(r["dir"]): continue
    k = key(r["dir"])
    if k not in best or float(r["tetra"]) > float(best[k]["tetra"]): best[k] = r
sel = sorted((r for r in best.values() if float(r["tetra"]) >= 0.10), key=lambda r: -float(r["tetra"]))
out = []
for r in sel:
    d = f"{ROOT}/{r['dir']}"
    top = (glob.glob(d + "/*.phb") or glob.glob(os.path.dirname(d) + "/*.phb"))[0]
    init = next((f"{d}/{n}" for n in ("mc_relaxed.dat", "start_conf.dat") if os.path.exists(f"{d}/{n}")), None)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", r["dir"].replace("hand5/", "").replace("phase_diagram/", "pd/"))
    out.append(dict(name=name, group="Best temperature of its system", label=f"{r['dir']} (T={r['T']})", dir=d,
                    topology=top, initial=init, final=f"{d}/final_conf.dat", headline=False,
                    initial_exists=bool(init), final_exists=True, tetra=float(r["tetra"]), six=float(r["six"]),
                    largest=float(r["largest"]), T=r["T"], step=r["step"]))
    print(f"{r['tetra']} six={r['six']} T={r['T']:6} init={'ok' if init else 'MISSING'}  {r['dir']}")
json.dump(out, open("hmanifest.json", "w"), indent=1)
print(len(out))
