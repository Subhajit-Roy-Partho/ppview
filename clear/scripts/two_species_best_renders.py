#!/usr/bin/env python3
"""Fresh latest-conf renders of the 4 strength designs: (a) val-6 molecules highlighted, (b) coloured by species.
Snapshots are copied first (runs are live).  Outputs renders/best/<variant>_T<T>_{val6,species}.png, clusters/best_*.labels.txt"""
import os, sys, json, shutil, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cluster_labels as CL
R = os.path.dirname(HERE)
SCR = "/tmp/claude-2438191/-scratch-sroy85-Github-dna/a7f7a000-064e-4224-9ff5-fe91f96309bd/scratchpad/best"
os.makedirs(SCR, exist_ok=True); os.makedirs(HERE + "/renders/best", exist_ok=True)
PP = "/scratch/sroy85/Github/ppview/render_phb.py"
out = {}
for T in ("0.140", "0.078"):
    for v in ("equal", "3H3L", "5H1L", "5L1H"):
        d = f"{R}/two_species_preconnected/{v}/Kb_300_T_{T}"
        top = os.path.realpath(d + "/topology.phb")
        snap = f"{SCR}/{v}_T{T}.dat"
        shutil.copyfile(d + "/final_conf.dat", snap)
        topo = CL.load_topology(top)
        res = CL.analyze_conf(topo, snap)
        val = res["valence"]; sp = topo["species"]
        lab6 = np.where(val == 6, 0, -1)[topo["mol"]]
        labsp = sp[topo["mol"]]
        for tag, lab in (("val6", lab6), ("species", labsp)):
            lf = f"{HERE}/clusters/best_{v}_T{T}_{tag}.labels.txt"
            np.savetxt(lf, lab, fmt="%d")
            png = f"{HERE}/renders/best/{v}_T{T}_{tag}.png"
            subprocess.run([sys.executable, PP, "--top", top, "--conf", snap, "--out", png, "--width", "2400", "--height", "1800",
                            "--scale", "2", "--background", "white", "--cluster-file", lf, "--min-cluster-mols", "1",
                            "--cores-only", "--quiet"] + (["--fade-unassigned", "0.5"] if tag == "val6" else []), check=True)
        out[f"{v}_T{T}"] = dict(n6=int((val == 6).sum()), meanval=float(val.mean()), species_counts=np.bincount(sp).tolist())
        print(v, T, out[f"{v}_T{T}"], flush=True)
json.dump(out, open(HERE + "/data/two_species_best_renders.json", "w"), indent=1)
