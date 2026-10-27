"""make_figures.py — CALIBRATION.md figures.

Recomputes snapshot detail curves from scratch copies of run confs
(read-only wrt live run dirs) + MSD series from calout/*.json.
Usage: python make_figures.py  (writes figs/*.png)
"""
import json
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(HERE, "calout")
FIG = os.path.join(HERE, "figs")
SCR = "/tmp/opencode/pk/figs"

REPS = {
    "crystal": "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S128_T0.140_r2",
    "gel": "/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected/equal/Kb_300_T_0.140",
    "melt": "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S128_T0.160",
    "partial": "/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.140_a",
}

LABELS = {"crystal": "seeded crystal S128_T0.140_r2", "gel": "2sp gel equal_T0.140",
          "melt": "melt S128_T0.160", "partial": "partial Q_T0.140_a"}


def load_detail(key, rundir):
    from phasekit import api as A, io as _io
    os.makedirs(SCR, exist_ok=True)
    top = os.path.join(rundir, "topology.phb")
    for c in ("final_conf.dat", "last_conf.dat", "mc_relaxed.dat"):
        p = os.path.join(rundir, c)
        if os.path.exists(p):
            conf = p
            break
    ts, cs = os.path.join(SCR, f"{key}.phb"), os.path.join(SCR, f"{key}.dat")
    shutil.copy(top, ts)
    shutil.copy(conf, cs)
    topo = _io.load_topology(ts)
    ct = _io.load_conf(cs, topo["N"])
    th = A.load_thresholds()
    ref = A.load_reference()
    flat, nested = A.snapshot_metrics(topo, ct, th, ref)
    return flat, nested


def main():
    os.makedirs(FIG, exist_ok=True)
    det = {}
    for key, rd in REPS.items():
        print("computing", key, flush=True)
        det[key] = load_detail(key, rd)

    # 1. g(r) overlay
    plt.figure()
    for key in REPS:
        g = det[key][1]["gr"]
        plt.plot(g["r"], g["g"], label=LABELS[key])
    plt.xlim(0, 15)
    plt.ylim(0, 12)
    plt.xlabel("r"); plt.ylabel("g(r)")
    plt.legend(fontsize=8); plt.title("core g(r)")
    plt.savefig(f"{FIG}/gr.png", dpi=120)
    plt.close()

    # 2. S(q) iso overlay (log y)
    plt.figure()
    for key in REPS:
        s = det[key][1]["sq_iso"]
        q, Sq = np.array(s["q"]), np.array(s["Sq"])
        plt.plot(q, Sq, label=LABELS[key])
    plt.xlabel("q"); plt.ylabel("S(q)")
    plt.ylim(0, 60)
    plt.legend(fontsize=8); plt.title("isotropic S(q) of cores")
    plt.savefig(f"{FIG}/sq.png", dpi=120)
    plt.close()

    # 3. q6bar histograms (sample vs reference median vs gas median)
    plt.figure()
    for key in REPS:
        o = det[key][1]["order"]["q6bar"]
        e = np.array(o["edges"])
        plt.stairs(o["hist"], e, label=LABELS[key])
    plt.xlabel("q6bar"); plt.ylabel("count")
    plt.legend(fontsize=8); plt.title("q6bar distribution of cores")
    plt.savefig(f"{FIG}/q6hist.png", dpi=120)
    plt.close()

    # 4. q4bar histograms
    plt.figure()
    for key in REPS:
        o = det[key][1]["order"]["q4bar"]
        e = np.array(o["edges"])
        plt.stairs(o["hist"], e, label=LABELS[key])
    plt.xlabel("q4bar"); plt.ylabel("count")
    plt.legend(fontsize=8); plt.title("q4bar distribution of cores")
    plt.savefig(f"{FIG}/q4hist.png", dpi=120)
    plt.close()

    # 5. MSD: gel vs crystal vs melt (from run JSON series)
    plt.figure()
    for key in REPS:
        name = {"crystal": "runs_S128_T0.140_r2", "gel": "equal",
                "melt": "runs_S128_T0.160",
                "partial": "runs_Q_T0.140_a"}[key]
        jp = None
        for f in os.listdir(CAL):
            if f.startswith(name):
                jp = os.path.join(CAL, f)
                break
        if jp is None:
            continue
        d = json.load(open(jp))
        s = d.get("series")
        if not s:
            continue
        t = np.array(s["steps"])
        plt.loglog(t[1:] - t[0], np.array(s["msd"])[1:] + 1e-12, label=LABELS[key])
    plt.xlabel("t - t0"); plt.ylabel("MSD")
    plt.legend(fontsize=8); plt.title("core MSD (run trajectories)")
    plt.savefig(f"{FIG}/msd.png", dpi=120)
    plt.close()
    print("wrote figs")


if __name__ == "__main__":
    main()
