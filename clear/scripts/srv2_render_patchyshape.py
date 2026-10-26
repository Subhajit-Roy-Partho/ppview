#!/usr/bin/env python3
"""Matplotlib renders of the 2023 PatchyShape pyrochlore configurations (oxDNAcpp/example/crystal) -> renders/srv2/"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
EX = Path("/scratch/sroy85/Github/oxDNAcpp/example/crystal"); OUT = Path(__file__).resolve().parent / "renders/srv2"; OUT.mkdir(parents=True, exist_ok=True)
COL = ["#0072B2", "#E69F00", "#009E73", "#CC79A7"]
def load(f):
    L = open(f).read().split("\n"); box = np.array(L[1].split()[2:5], float)
    return box, np.array([l.split()[:3] for l in L[3:] if l.strip()], float)
types = np.array(open(EX / "125/output.top").read().split("\n")[1].split(), int)
fig = plt.figure(figsize=(12, 8))
for j, T in enumerate(("125", "150")):
    box, a = load(EX / T / "last_conf130.BIG.dat"); a = a % box
    ax = fig.add_subplot(2, 2, 1 + j, projection="3d")
    ax.scatter(*a.T, c=[COL[t] for t in types], s=6, depthshade=True, linewidths=0)
    ax.set_title(f"T = 0.{T}: all 2048 shells (box {box[0]:.0f})", fontsize=9); ax.set_box_aspect((1, 1, 1))
    for f in (ax.set_xticks, ax.set_yticks, ax.set_zticks): f([])
    m = a[:, 2] < 5
    ax2 = fig.add_subplot(2, 2, 3 + j)
    ax2.scatter(a[m, 0], a[m, 1], c=[COL[t] for t in types[m]], s=26, edgecolors="white", linewidths=.3); ax2.set_aspect("equal")
    ax2.set_title(f"T = 0.{T}: slab 0 < z < 5 ({m.sum()} shells)", fontsize=9); ax2.set_xticks([]); ax2.set_yticks([]); ax2.grid(False)
for t, c in zip("0123", COL): fig.text(0.02 + 0.06 * int(t), 0.02, f"species {t}", color=c, fontsize=8)
fig.suptitle("PatchyShape sat24 pyrochlore, 2048 particles (oxDNAcpp/example/crystal, 2023): final configurations", fontsize=10)
fig.tight_layout(rect=(0, 0.03, 1, 0.97)); fig.savefig(OUT / "srv2_patchyshape2048_T125_vs_T150.png", dpi=200); print("ok")
