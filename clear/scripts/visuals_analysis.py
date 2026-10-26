#!/usr/bin/env python3
"""Figures/tables from PHB_visuals_2026-10-23 (video per-frame metrics + snapshot metrics). Writes OUT/analysis/*.png|json"""
import json, glob, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = "/scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23"; os.makedirs(OUT + "/analysis", exist_ok=True)
V = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(OUT + "/videos/*.json")}
M = {os.path.basename(f)[:-13]: json.load(open(f)) for f in glob.glob(OUT + "/images/*.metrics.json")}
def series(n, key):
    pf = V[n]["per_frame"]; return np.array([p["step"] for p in pf]), np.array([p[key] for p in pf])
def at(n, key, step):
    s, y = series(n, key); return float(np.interp(step, s, y))
res = {}
# Ka x alpha: time-matched at 0.8e9 steps (control S128_T0.14 r2 has 0.8e9 only)
rows = []
for n in sorted(k for k in V if k.startswith("Ka")):
    ka = float(n.split("_")[0][2:]); a = float(n.split("_a")[1])
    rows.append(dict(name=n, Ka=ka, alpha=a, six_08=at(n, "six", 8e8), valence_08=at(n, "valence", 8e8), cluster_08=at(n, "largest", 8e8),
                     six_final=M[n]["final"]["six_valent"], tet_final=M[n]["final"]["tetra_per_molecule"], final_step=M[n]["final"]["step"]))
ctrl = dict(six_08=at("seed_S128_T0.140_r2", "six", 8e8), valence_08=at("seed_S128_T0.140_r2", "valence", 8e8), tet=M["seed_S128_T0.140_r2"]["final"]["tetra_per_molecule"])
res["ka_alpha"] = rows; res["ka_control_Ka300_a0.10_r2"] = ctrl
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
cols = {10: "#1b9e77", 30: "#7570b3", 100: "#e6ab02", 300: "#d95f02", 1000: "#e7298a"}
for a, axx in ((0.10, ax[0]), (0.12, ax[1])):
    for r in rows:
        if r["alpha"] != a: continue
        s, y = series(r["name"], "six"); axx.plot(s / 1e9, 100 * y, color=cols[int(r["Ka"])], lw=2, label=f"Ka={int(r['Ka'])}")
    s, y = series("seed_S128_T0.140_r2", "six"); axx.plot(s / 1e9, 100 * y, "k--", lw=1.5, label="control Ka=300, a=0.10")
    axx.set_title(f"alpha = {a}"); axx.set_xlabel("steps (10$^9$)"); axx.set_ylabel("six-valent molecules (%)"); axx.legend(fontsize=8, frameon=False)
for a, mk in ((0.10, "o-"), (0.12, "s--")):
    rr = sorted([r for r in rows if r["alpha"] == a], key=lambda r: r["Ka"]); ax[2].plot([r["Ka"] for r in rr], [r["tet_final"] for r in rr], mk, label=f"alpha={a} (2x10$^9$ steps)", ms=7)
ax[2].set_xscale("log"); ax[2].set_xlabel("Ka"); ax[2].set_ylabel("tetrahedra / molecule (final)"); ax[2].axhline(0.358, color="gray", ls=":"); ax[2].text(10, 0.362, "ideal crystal 0.358", fontsize=8, color="gray"); ax[2].legend(fontsize=8, frameon=False)
ax[2].set_title("order reached vs Ka"); ax[2].set_ylim(0.2, 0.4)
fig.suptitle("Seeded growth (128-molecule seed, T = 0.14): Ka x alpha study", y=1.02); fig.tight_layout(); fig.savefig(OUT + "/analysis/ka_alpha.png", dpi=140, bbox_inches="tight"); plt.close(fig)
# high-T 2-species
Ts = [0.14, 0.15, 0.16, 0.17, 0.18]
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4)); tab = []
for v, c in (("3H3L", "#0ea5a4"), ("5L1H", "#e11d48")):
    ys = []
    for T in Ts:
        n = f"2sp_{v}_T0.140" if T == 0.14 else f"2sp_highT_{v}_T{T:.3f}"; f = M[n]["final"]; ys.append(f)
        tab.append(dict(variant=v, T=T, six=f["six_valent"], cluster=f["largest_cluster"], valence=f["mean_valence"], tet=f["tetra_per_molecule"], n_clusters=f["n_clusters"], step=f["step"]))
    for k, (key, lab) in enumerate((("six_valent", "six-valent molecules (%)"), ("largest_cluster", "largest cluster (%)"), ("mean_valence", "mean valence"))):
        ax[k].plot(Ts, [(100 if k < 2 else 1) * y[key] for y in ys], "o-", color=c, lw=2, ms=7, label=v); ax[k].set_xlabel("T"); ax[k].set_ylabel(lab)
ax[0].legend(frameon=False); fig.suptitle("2-species 3-3 (3H3L) and 1-5 (5L1H): final state vs temperature (K$_{weak}$/T: 14.3, 13.3, 12.5, 11.8, 11.1)", y=1.02)
fig.tight_layout(); fig.savefig(OUT + "/analysis/two_species_vs_T.png", dpi=140, bbox_inches="tight"); plt.close(fig); res["two_species_vs_T"] = tab
# headline time courses
heads = ["2sp_3H3L_T0.140", "2sp_5L1H_T0.140", "4sp_ww_T0.140", "4sp_ws_T0.140", "seed_S256_T0.140_r1", "seed_S128_T0.140_r2", "seed_S64_T0.140", "seed_S8_T0.140", "window_Q_T0.140", "2sp_highT_3H3L_T0.170"]
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8))
for n in heads:
    s, y = series(n, "six"); ax[0].plot(s / 1e9, 100 * y, lw=2, label=n)
    s, y = series(n, "largest"); ax[1].plot(s / 1e9, 100 * y, lw=2)
ax[0].set_ylabel("six-valent molecules (%)"); ax[1].set_ylabel("largest cluster (%)")
for a_ in ax: a_.set_xlabel("steps (10$^9$)")
ax[0].legend(fontsize=7, frameon=False, ncol=2); fig.tight_layout(); fig.savefig(OUT + "/analysis/timecourses_headline.png", dpi=140, bbox_inches="tight"); plt.close(fig)
json.dump(res, open(OUT + "/analysis/analysis.json", "w"), indent=1)
print("control", ctrl)
for r in rows: print(f"{r['name']:16s} Ka={r['Ka']:6.0f} a={r['alpha']} @0.8e9: six {100*r['six_08']:5.1f}% val {r['valence_08']:.2f} cl {100*r['cluster_08']:.0f}%  | final tet {r['tet_final']:.3f} six {100*r['six_final']:.1f}%")
for t in tab: print(t)
