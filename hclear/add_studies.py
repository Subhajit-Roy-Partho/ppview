import csv, json, os, re, glob, subprocess, sys
ROOT = "/scratch/sroy85/Github/dna/large_crystal"; REPO = "/scratch/sroy85/Github/ppview"
PY = "/home/sroy85/miniconda3/bin/python3"
cur = json.load(open(f"{REPO}/hclear/manifest.json")); have = {r["dir"] for r in cur}; names = {r["name"] for r in cur}
def study(d):
    p = d.split("/")
    return "/".join(p[:2]) if p[0] == "hand5" else "/".join(p[:3])
best = {}; small = {}
for r in csv.DictReader(open("yield.csv")):
    d = r["dir"]
    if r["T"] == "ERR" or "archive" in d or d.startswith("phase_diagram/results/"): continue
    t = float(r["tetra"])
    if study(d) not in best or t > float(best[study(d)]["tetra"]): best[study(d)] = r
    m = re.search(r"replicates/R2/S(\d+)_T", d)
    if m and int(m.group(1)) <= 64 and (m.group(1) not in small or t > float(small[m.group(1)]["tetra"])): small[m.group(1)] = r
picks = [(r, f"best of study {s}") for s, r in best.items()] + [(r, f"small-seed replicate S{k}") for k, r in small.items()]
new = []
for r, grp in picks:
    d = f"{ROOT}/{r['dir']}"
    if d in have: continue
    top = (glob.glob(d + "/*.phb") or glob.glob(os.path.dirname(d) + "/*.phb") or [None])[0]
    init = next((f"{d}/{n}" for n in ("mc_relaxed.dat", "start_conf.dat") if os.path.exists(f"{d}/{n}")), None)
    if not top or not init: print("SKIP (no topology/start conf)", r["dir"]); continue
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", r["dir"].replace("hand5/", "").replace("phase_diagram/", "pd/"))
    if name in names: continue
    names.add(name); have.add(d)
    pre = " [pre-formed crystal start]" if r["N"] == "2048" else ""
    new.append(dict(name=name, group=grp, label=f"{r['dir']} (T={r['T']}){pre}", dir=d, topology=top, initial=init,
                    final=f"{d}/final_conf.dat", headline=False, initial_exists=True, final_exists=True,
                    tetra=float(r["tetra"]), six=float(r["six"]), largest=float(r["largest"]), T=r["T"], step=r["step"]))
    print(f"+ {r['tetra']:>6} {name}")
for h in ("hclear", "hclear2"):
    json.dump(cur + new, open(f"{REPO}/{h}/manifest.json", "w"), indent=1)
print(len(new), "added;", len(cur) + len(new), "total")
nm = [r["name"] for r in new]
for script, h in (("render_clear.py", "hclear"), ("render_clear2.py", "hclear2")):
    subprocess.Popen([PY, f"{REPO}/{h}/{script}", "run", *nm, "-j", "4"], stdout=open(f"{REPO}/{h}/render_add.log", "w"), stderr=subprocess.STDOUT)
