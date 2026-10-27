"""Yield of every final_conf.dat under large_crystal: largest cluster, six-valent fraction, tetrahedra per molecule
(ideal crystal 0.358). Writes yield.csv in the current directory. Run with a Python that has numpy/scipy."""
import sys, os, re, glob, csv
from multiprocessing import Pool
sys.path.insert(0, "/scratch/sroy85/Github/ppview/clear/scripts")
import cluster_labels as CL
ROOT = "/scratch/sroy85/Github/dna/large_crystal"

def temp(d):
    for n in ("input", "input_stage", "input_md_production", "input_chain"):
        p = os.path.join(d, n)
        if os.path.exists(p):
            for l in open(p):
                m = re.match(r"\s*T\s*=\s*([0-9.]+)", l)
                if m: return m.group(1)
    return ""

def one(conf):
    d = os.path.dirname(conf)
    tops = glob.glob(d + "/*.phb") or glob.glob(os.path.dirname(d) + "/*.phb")
    if not tops: return None
    try:
        topo = CL.load_topology(tops[0])
        if topo["n_mol"] >= 3000: return None
        t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
        res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
        n = topo["n_mol"]; val = res["valence"]
        cl = CL.clique_stats(topo, res["neighbors"])
        return (os.path.relpath(d, ROOT), temp(d), n, f"{t:.4g}", round((res["mol_label"] == 0).sum() / n, 3),
                round(float((val == 6).mean()), 3), round(cl["n_tetra"] / n, 3))
    except Exception as e:
        return (os.path.relpath(d, ROOT), "ERR", 0, str(e)[:40], 0, 0, 0)

if __name__ == "__main__":
    confs = sorted(c for c in glob.glob(ROOT + "/**/final_conf.dat", recursive=True) if "PHB_visuals" not in c)
    w = csv.writer(open("yield.csv", "w")); w.writerow("dir T N step largest six tetra".split())
    with Pool(2) as p:
        for i, r in enumerate(p.imap_unordered(one, confs, chunksize=4)):
            if r: w.writerow(r)
            if i % 50 == 0: sys.stderr.write(f"{i}/{len(confs)}\n")
