#!/usr/bin/env python3
"""Figures for final_report/findings/two_species.md (reads data/*.pkl, data/reference_crystal.json)."""
import json, pickle, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
FIG = HERE / "figs"; FIG.mkdir(exist_ok=True)
R = pickle.load(open(HERE / "data/two_species_runs.pkl", "rb"))
R4 = pickle.load(open(HERE / "data/four_species_compare.pkl", "rb"))
REF = json.load(open(HERE / "data/reference_crystal.json"))

VAR = ["equal", "3H3L", "5H1L", "5L1H"]
VCOL = {"equal": "#2a78d6", "3H3L": "#eb6834", "5H1L": "#1baf7a", "5L1H": "#4a3aa7"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "figure.dpi": 100,
                     "savefig.dpi": 200, "savefig.facecolor": "white", "legend.frameon": False})


def sel(system, variant=None):
    return sorted([r for r in R if r["system"] == system and (variant is None or r["variant"] == variant)],
                  key=lambda r: (VAR.index(r["variant"]), r["T"]))


def blues(n):
    return plt.cm.Blues(np.linspace(0.35, 0.95, n))


# ---------------------------------------------------------------- fig 1: assembly kinetics
fig, axs = plt.subplots(1, 4, figsize=(12, 3.0), sharey=True)
for ax, v in zip(axs, VAR):
    rs = sel("precon", v)
    for c, r in zip(blues(len(rs)), rs):
        ts = r["timeseries"]
        ax.plot(np.array(ts["step"]) + 1, ts["frac"], color=c, lw=1.4, label=f"T={r['T']:.3f}")
    ax.set_xscale("log"); ax.set_title(v, color=VCOL[v], fontweight="bold"); ax.set_xlabel("MD steps")
    ax.set_xlim(1e5, 2e9); ax.axhline(0.5, color=GRID, lw=0.8)
axs[0].set_ylabel("largest-cluster fraction\n(molecules, PBC-safe)")
axs[0].legend(fontsize=7, loc="upper left")
fig.suptitle("Fig 1  2-species preconnected: every variant and T percolates (>=99%) within ~5% of the run; "
             "assembly is not rate-limited by strength", fontsize=9, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(FIG / "ts1_assembly_kinetics.png"); plt.close(fig)

# ---------------------------------------------------------------- fig 2: heatmaps precon
Ts = sorted({r["T"] for r in sel("precon")})
def mat(key, fn=None, system="precon", Tlist=None):
    Tl = Tlist or Ts
    M = np.full((4, len(Tl)), np.nan)
    for i, v in enumerate(VAR):
        for j, T in enumerate(Tl):
            for r in sel(system, v):
                if abs(r["T"] - T) < 1e-9:
                    M[i, j] = fn(r) if fn else r["final"][key]
    return M
panels = [("mean valence (ideal 6)", mat("mean_valence"), "%.2f", "viridis", (3, 6)),
          ("fraction of molecules with valence 6", mat("fraction_valence6"), "%.3f", "viridis", (0, 0.65)),
          ("val-6 mean angle deviation from\npyrochlore {60,120,180} (deg)", mat(None, lambda r: r["final"]["order"]["val6_mean_dev_deg"]),
           "%.1f", "viridis_r", (0, 17)),
          ("steps to 90% connected (1e7)", mat(None, lambda r: (r["t90_steps"] or np.nan) / 1e7), "%.1f", "magma_r", (0, 25))]
fig, axs = plt.subplots(1, 4, figsize=(12.5, 2.9))
for ax, (t, M, fmt, cm, (lo, hi)) in zip(axs, panels):
    im = ax.imshow(M, cmap=cm, vmin=lo, vmax=hi, aspect="auto")
    ax.set_xticks(range(len(Ts))); ax.set_xticklabels([f"{T:.3f}" for T in Ts], fontsize=7.5)
    ax.set_yticks(range(4)); ax.set_yticklabels(VAR); ax.set_xlabel("T"); ax.set_title(t, fontsize=8.5)
    ax.grid(False)
    for i in range(4):
        for j in range(len(Ts)):
            if not np.isnan(M[i, j]):
                frac = (M[i, j] - lo) / (hi - lo)
                ax.text(j, i, fmt % M[i, j], ha="center", va="center", fontsize=8,
                        color="white" if (frac < 0.5 if "_r" not in cm else frac > 0.5) else INK)
fig.suptitle(f"Fig 2  2-species preconnected, final configuration: gel-like network (valence ~4, few val-6 sites). "
             f"Reference pyrochlore crystal: val-6 = {REF['fraction_valence6']:.2f} (of all, incl. surface), angle deviation {REF['val6_mean_dev_deg']:.1f} deg; random = {REF['random_val6_mean_dev_deg']:.1f} deg",
             fontsize=8.5, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(FIG / "ts2_final_heatmaps_preconnected.png"); plt.close(fig)

# ---------------------------------------------------------------- fig 3: old sweep artifact
T8 = sorted({r["T"] for r in sel("sweep")})
panels = [("molecule-ID cluster fraction\n(what a naive molecule-graph analysis reports)", mat(None, lambda r: r["final"]["largest_cluster_fraction"], "sweep", T8), "%.2f", "Blues", (0, 1)),
          ("arm anchors intact (of 1500)\n(arm still attached to its own core)", mat(None, lambda r: r["final"]["anchors_intact"], "sweep", T8), "%d", "Reds", (0, 1500)),
          ("mean core-core distance of 'bonded'\nmolecule pairs (precon ~2.8)", mat(None, lambda r: r["final"]["order"]["bond_core_dist_mean"], "sweep", T8), "%.1f", "Oranges", (0, 14))]
fig, axs = plt.subplots(1, 3, figsize=(12, 2.9))
for ax, (t, M, fmt, cm, (lo, hi)) in zip(axs, panels):
    ax.imshow(M, cmap=cm, vmin=lo, vmax=hi, aspect="auto"); ax.grid(False)
    ax.set_xticks(range(len(T8))); ax.set_xticklabels([f"{T:.3f}" for T in T8], fontsize=7, rotation=45)
    ax.set_yticks(range(4)); ax.set_yticklabels(VAR); ax.set_xlabel("T"); ax.set_title(t, fontsize=8.5)
    for i in range(4):
        for j in range(len(T8)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, fmt % M[i, j], ha="center", va="center", fontsize=7,
                        color="white" if (M[i, j] - lo) / (hi - lo) > 0.6 else INK)
fig.suptitle("Fig 3  Original two_species_sweep (32 runs, stopped 2026-10-09): colour-encoding bug detached the arms from the cores "
             "- 'connected' molecule IDs are NOT physical aggregates", fontsize=8.5, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(FIG / "ts3_old_sweep_artifact.png"); plt.close(fig)

# ---------------------------------------------------------------- fig 4: valence histograms
fig, axs = plt.subplots(1, 2, figsize=(10, 3.2))
ax = axs[0]
w = 0.16; x = np.arange(0, 7)
def vh(rs):
    H = np.zeros(7)
    for r in rs:
        h = r["final"]["valence_histogram"]
        for k, v in h.items():
            H[int(k)] += v
    return H / H.sum()
series = [("reference crystal", np.array([REF["valence_histogram"].get(str(k), 0) for k in range(7)], float), "#0b0b0b")]
series[0] = (series[0][0], series[0][1] / series[0][1].sum(), series[0][2])
for v in VAR:
    series.append((f"precon {v}", vh(sel("precon", v)), VCOL[v]))
for i, (lab, H, c) in enumerate(series):
    ax.bar(x + (i - 2) * w, H, w, color=c, label=lab, edgecolor="white", linewidth=0.4)
ax.set_xlabel("valence (distinct neighbouring molecules)"); ax.set_ylabel("fraction of molecules")
ax.set_title("valence distribution, final config (pooled over T)", fontsize=9); ax.legend(fontsize=7)
ax = axs[1]
th = np.linspace(0, 180, 36 + 1); mid = 0.5 * (th[1:] + th[:-1])
def ah(rs):
    H = np.zeros(36)
    for r in rs:
        h = r["final"]["order"]["angles_val6_hist"]
        if h: H += np.array(h)
    return H / H.sum() / 5.0
ax.plot(mid, np.array(REF["angles_val6_hist"]) / np.sum(REF["angles_val6_hist"]) / 5.0, color="#0b0b0b", lw=1.6, label="reference crystal")
ax.plot(mid, ah(sel("precon")), color="#2a78d6", lw=1.6, label="2-sp preconnected (val-6 sites)")
ax.plot(mid, ah(sel("sweep")), color="#999999", lw=1.2, ls="--", label="old sweep (val-6 sites; not physical)")
ax.plot(mid, np.sin(np.radians(mid)) / 2 * np.radians(5), color="#e87ba4", lw=1.2, ls=":", label="isotropic (random)")
for a in (60, 120, 180):
    ax.axvline(a, color=GRID, lw=1)
ax.set_xlabel("angle between two neighbour bond vectors (deg)"); ax.set_ylabel("probability / 5 deg bin")
ax.set_title("neighbour-bond angles at valence-6 sites", fontsize=9); ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
fig.suptitle("Fig 4  Preconnected networks are far from the ideal 6-coordinated crystal: valence ~4, angles near-isotropic", fontsize=9, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "ts4_valence_angles.png", bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- fig 5: energy traces
fig, axs = plt.subplots(1, 4, figsize=(12, 3.0))
for ax, v in zip(axs, VAR):
    rs = sel("precon", v)
    for c, r in zip(blues(len(rs)), rs):
        e = r["energy_trace"]
        ax.plot(np.array(e["step"]) / 1e9, e["pe"], color=c, lw=1.2, label=f"T={r['T']:.3f}")
    ax.set_title(v, color=VCOL[v], fontweight="bold"); ax.set_xlabel("steps (1e9)")
    ax.set_xscale("symlog", linthresh=0.05)
axs[0].set_ylabel("PE / particle"); axs[0].legend(fontsize=7)
fig.suptitle("Fig 5  Energy per particle (preconnected, live runs). Fast drop then slow creep (aging); no plateau jump signalling ordering",
             fontsize=9, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(FIG / "ts5_energy_traces.png"); plt.close(fig)

# ---------------------------------------------------------------- fig 6: channel occupancy
fig, axs = plt.subplots(1, 2, figsize=(11, 3.2), gridspec_kw=dict(width_ratios=[1.05, 1]))
ax = axs[0]
pn = ["P1 (1,5)", "P2 (2,12)", "P3 (3,8)", "P4 (4,7)", "P5 (6,11)", "P6 (9,10)"]
for i, v in enumerate(VAR):
    rs = sel("precon", v)
    m = [np.mean([r["final"]["bonds_per_channel"].get(f"P{k}", 0) for r in rs]) for k in range(1, 7)]
    ax.bar(np.arange(6) + (i - 1.5) * 0.2, m, 0.2, color=VCOL[v], label=v, edgecolor="white", linewidth=0.4)
ax.axhline(250, color=INK2, lw=0.8, ls=":"); ax.text(5.45, 258, "250 = all handles used", fontsize=7, ha="right", color=INK2)
ax.set_xticks(range(6)); ax.set_xticklabels(pn, fontsize=7.5); ax.set_ylabel("inter-molecule bonds\n(mean over T)")
ax.set_ylim(0, 330); ax.set_title("preconnected: bonds per channel at end of run\n(H = strength 100, K=200; L = strength 1, K=2)", fontsize=8.5); ax.legend(fontsize=7, ncol=4, loc="upper left")
ax = axs[1]
rs = sel("sweep", "5L1H")
Tv = [r["T"] for r in rs]
low = [np.mean([r["final"]["bonds_per_channel"].get(f"P{k}", 0) for k in range(1, 6)]) for r in rs]
hi = [r["final"]["bonds_per_channel"].get("P6", 0) for r in rs]
ax.plot(Tv, low, "o-", color=VCOL["5L1H"], label="5 low channels P1-P5 (K=2)")
ax.plot(Tv, hi, "s-", color="#eb6834", label="P6 (9,10) high (K=200)")
ax2 = ax.secondary_xaxis("top", functions=(lambda T: 2.0 / np.maximum(T, 1e-6), lambda k: 2.0 / np.maximum(k, 1e-6)))
ax2.set_xticks([10, 12, 15, 20, 25]); ax2.set_xlabel("K/T of a low bond (kT)", fontsize=8)
ax.set_xlabel("T"); ax.set_ylabel("bonds (250 handles / channel)")
ax.set_title("old 5L1H sweep: low-channel bonds melt at T~0.16-0.20\n(K/T ~ 10-12 kT) - bond thermodynamics only", fontsize=8.5, pad=24); ax.legend(fontsize=7)
fig.suptitle("Fig 6  Strength heterogeneity: in the 'L' channels K=2 means 14-26 kT at T=0.078-0.14, i.e. still effectively irreversible", fontsize=9, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "ts6_channel_occupancy.png", bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- fig 7: 2 vs 4 species
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.4))
groups = [("2-sp preconnected (alpha .12)", [r for r in R if r["system"] == "precon"], "#2a78d6", "o"),
          ("4-sp K300_large (alpha .10, kicked)", [r for r in R4 if r["system"] == "k300_large"], "#eb6834", "s"),
          ("4-sp strength scan S50-S200 (alpha .12)", [r for r in R4 if r["system"] == "strength_scan"], "#1baf7a", "^"),
          ("4-sp seed sweep (alpha .10)", [r for r in R4 if r["system"] == "pre_seed_4sp"], "#4a3aa7", "D")]
ax = axs[0]
for lab, rs, c, m in groups:
    ax.scatter([r["final"]["mean_valence"] for r in rs], [r["final"]["fraction_valence6"] for r in rs], s=28, color=c, marker=m, label=lab, edgecolor="white", linewidth=0.5)
ax.scatter([REF["mean_valence"]], [REF["fraction_valence6"]], s=90, marker="*", color="#0b0b0b", label="reference crystal")
ax.set_xlabel("mean valence"); ax.set_ylabel("fraction valence 6"); ax.legend(fontsize=7, loc="upper left")
ax.set_title("final state: all preconnected systems end as the same gel", fontsize=9)
ax = axs[1]
rng = np.random.default_rng(0)
for i, (lab, rs, c, m) in enumerate(groups):
    vals = [r["t90_steps"] / 1e7 for r in rs if r.get("t90_steps") and r["t90_steps"] > 1.5e5]
    ax.scatter(i + rng.uniform(-0.12, 0.12, len(vals)), vals, color=c, marker=m, s=28, edgecolor="white", linewidth=0.5)
    ax.plot([i - 0.25, i + 0.25], [np.median(vals)] * 2, color=INK, lw=1.2)
ax.set_xticks(range(4)); ax.set_xticklabels(["2-sp\nprecon", "4-sp\nK300_large*", "4-sp\nstrength\nscan", "4-sp\nseed sweep"], fontsize=8)
ax.set_ylabel("steps to 90% connected (1e7)"); ax.set_title("speed of aggregation (median bar)", fontsize=9)
fig.text(0.99, 0.01, "*K300_large trajectories begin after the 10M-step T=0.17 kick, t90 not available", fontsize=6.5, ha="right", color=INK2)
fig.suptitle("Fig 7  2-species vs 4-species: same gel, 2-species is not worse and needs half the designs", fontsize=9, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.02, 1, 0.93)); fig.savefig(FIG / "ts7_two_vs_four_species.png"); plt.close(fig)
print("figs written:", sorted(p.name for p in FIG.glob("ts*.png")))
