#!/usr/bin/env python3
"""
Energy vs time plots for all hand5 PHB simulations.

Reads energy files from:
  - stiffness_sweep: energy_long.dat (primary, from input), fallback energy.dat
  - seeded_sweep:    energy.dat
  - preconnected:    energy.dat

Generates:
  - plots/energy_stiffness_weak_weak.png
  - plots/energy_stiffness_weak_strong.png
  - plots/energy_seeded_weak_weak.png
  - plots/energy_seeded_weak_strong.png
  - plots/energy_stiffness_grid.png       (6x6 grid per patch set)
  - plots/energy_seeded_grid.png
  - plots/energy_dashboard.html           (self-contained interactive)
"""
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
PLOTS = HERE / "plots"
PLOTS.mkdir(exist_ok=True)

LARGE_CRYSTAL = HERE.parent
HAND5 = LARGE_CRYSTAL / "hand5"

# Energy file columns: time | PE/N | KE/N | (PE+KE)/N
COL_TIME = 0
COL_PE = 1
COL_KE = 2
COL_TE = 3

KB_VALS  = [1, 3, 10, 30, 100, 300]
T_VALS   = [0.050, 0.060, 0.070, 0.078, 0.090, 0.100]
T_LABELS = ["0.05", "0.06", "0.07", "0.078", "0.09", "0.10"]
KB_LABELS = [str(k) for k in KB_VALS]

LINE_COLORS = ["#163290","#3158b3","#5c80cc","#8fa9e0",
               "#f59e0b","#b45309"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_energy_file(path):
    """Load energy file, return (time, PE, KE, TE) arrays."""
    if not path.exists():
        return None
    data = np.loadtxt(path, usecols=(COL_TIME, COL_PE, COL_KE, COL_TE))
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def get_energy_data(run_dir, sweep):
    """Get combined energy data for a run directory."""
    if sweep == "stiffness_sweep":
        # Primary: energy_long.dat (from input); fallback: energy.dat
        primary = load_energy_file(run_dir / "energy_long.dat")
        secondary = load_energy_file(run_dir / "energy.dat")
        if primary is not None and secondary is not None:
            # Merge: use primary if it has more data points, else combine
            if len(primary) >= len(secondary):
                return primary
            # Combine non-overlapping: take secondary up to primary's start
            t_start = primary[0, 0]
            sec_mask = secondary[:, 0] < t_start
            if sec_mask.any():
                combined = np.vstack([secondary[sec_mask], primary])
                return combined
            return primary
        elif primary is not None:
            return primary
        elif secondary is not None:
            return secondary
        return None
    else:
        return load_energy_file(run_dir / "energy.dat")


def discover_runs():
    """Return list of dicts with sweep, patch_set, Kb, T, run_dir."""
    runs = []
    for sweep in ("stiffness_sweep", "seeded_sweep"):
        for pset in ("weak_weak", "weak_strong"):
            base = HAND5 / sweep / pset
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                m = re.match(r"Kb_(\d+)_T_([0-9.]+)", d.name)
                if not m:
                    continue
                kb, T = int(m.group(1)), float(m.group(2))
                runs.append({
                    "sweep": sweep,
                    "patch_set": pset,
                    "Kb": kb,
                    "T": T,
                    "run_dir": d,
                })

    base = HAND5 / "preconnected_seed_sweep" / "four_species"
    if base.exists():
        for d in sorted(base.iterdir()):
            m = re.match(r"Kb_(\d+)_T_([0-9.]+)", d.name)
            if not m:
                continue
            kb, T = int(m.group(1)), float(m.group(2))
            runs.append({
                "sweep": "preconnected",
                "patch_set": "four_species",
                "Kb": kb,
                "T": T,
                "run_dir": d,
            })
    return runs


def plot_energy_lines(runs, sweep, pset, title, filename):
    """Plot PE/N vs time, one line per (Kb, T) combination."""
    subset = [r for r in runs if r["sweep"] == sweep and r["patch_set"] == pset]
    if not subset:
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True,
                             gridspec_kw={"hspace": 0.25, "wspace": 0.15})

    for ki, kb in enumerate(KB_VALS):
        ax = axes[ki // 3, ki % 3]
        kb_runs = [r for r in subset if r["Kb"] == kb]
        for r in kb_runs:
            data = get_energy_data(r["run_dir"], sweep)
            if data is None or len(data) < 2:
                continue
            t = data[:, 0]
            pe = data[:, 1]
            T = r["T"]
            ti_idx = T_VALS.index(T) if T in T_VALS else -1
            color = LINE_COLORS[ti_idx] if ti_idx >= 0 else "#999999"
            ax.plot(t, pe, color=color, linewidth=0.8, alpha=0.85,
                    label=f"T={T}")

        ax.set_ylabel("PE / N", fontsize=8)
        ax.set_title(f"K$_b$ = {kb}", fontsize=9, fontweight="bold")
        ax.grid(True, linewidth=0.3, alpha=0.4)
        ax.tick_params(labelsize=7)
        if ki == 0:
            ax.legend(fontsize=6, ncol=2, loc="best", framealpha=0.5)

    for ax in axes[1, :]:
        ax.set_xlabel("Time (sim. units)", fontsize=9)

    fig.suptitle(title, fontsize=12, fontweight="bold", y=0.98)
    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def plot_energy_grid(runs, sweep, pset, title, filename):
    """Plot PE/N vs time in a 6x6 grid (rows=Kb, cols=T)."""
    subset = [r for r in runs if r["sweep"] == sweep and r["patch_set"] == pset]
    if not subset:
        return

    fig, axes = plt.subplots(6, 6, figsize=(18, 16), sharex=True, sharey=False,
                             gridspec_kw={"hspace": 0.3, "wspace": 0.2})

    for ki, kb in enumerate(KB_VALS):
        for ti, T in enumerate(T_VALS):
            ax = axes[ki, ti]
            match = [r for r in subset if r["Kb"] == kb and r["T"] == T]
            if match:
                data = get_energy_data(match[0]["run_dir"], sweep)
                if data is not None and len(data) > 1:
                    t = data[:, 0]
                    pe = data[:, 1]
                    ax.plot(t, pe, color="#3158b3", linewidth=0.5, alpha=0.8)
                    # Mark initial and final
                    ax.axhline(pe[0], color="#9ca3af", linewidth=0.4,
                              linestyle="--", alpha=0.5)
            if ki == 0:
                ax.set_title(f"T={T}", fontsize=8, fontweight="bold")
            if ti == 0:
                ax.set_ylabel(f"Kb={kb}\nPE/N", fontsize=7)
            ax.tick_params(labelsize=6)
            ax.grid(True, linewidth=0.3, alpha=0.3)

    for ax in axes[-1, :]:
        ax.set_xlabel("Time", fontsize=7)

    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.995)
    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def plot_energy_summary_bars(runs, sweep, pset, title, filename):
    """Bar chart: final PE/N for each (Kb, T)."""
    subset = [r for r in runs if r["sweep"] == sweep and r["patch_set"] == pset]
    if not subset:
        return

    fig, ax = plt.subplots(figsize=(10, 5))

    bar_data = {}
    for r in subset:
        data = get_energy_data(r["run_dir"], sweep)
        if data is None or len(data) < 2:
            continue
        key = (r["Kb"], r["T"])
        bar_data[key] = data[-1, 1]  # final PE/N

    x_labels = []
    pe_vals = []
    colors = []
    for ki, kb in enumerate(KB_VALS):
        for ti, T in enumerate(T_VALS):
            val = bar_data.get((kb, T))
            if val is not None:
                x_labels.append(f"Kb{kb}\nT{T}")
                pe_vals.append(val)
                colors.append(LINE_COLORS[ti])

    if pe_vals:
        bars = ax.bar(range(len(pe_vals)), pe_vals, color=colors,
                      width=0.7, edgecolor="white", linewidth=0.3)
        ax.set_xticks(range(len(pe_vals)))
        ax.set_xticklabels(x_labels, fontsize=6, rotation=90)
        ax.set_ylabel("Final PE / N", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        # Add value labels for small grids
        if len(pe_vals) <= 36:
            for bar, val in zip(bars, pe_vals):
                ax.text(bar.get_x() + bar.get_width()/2, val,
                        f"{val:.1f}", ha="center", va="bottom",
                        fontsize=5.5, rotation=90)

    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def compute_stats(runs):
    """Compute energy stats for all runs."""
    stats = []
    for r in runs:
        data = get_energy_data(r["run_dir"], r["sweep"])
        if data is None or len(data) < 2:
            continue
        pe = data[:, 1]
        t = data[:, 0]
        stats.append({
            "sweep": r["sweep"],
            "patch_set": r["patch_set"],
            "Kb": r["Kb"],
            "T": r["T"],
            "n_points": len(data),
            "t_max": float(t[-1]),
            "pe_init": float(pe[0]),
            "pe_final": float(pe[-1]),
            "pe_min": float(pe.min()),
            "pe_max": float(pe.max()),
            "pe_mean": float(pe.mean()),
            "pe_std": float(pe.std()),
        })
    return stats


def plot_energy_all_on_one(runs, sweep, pset, title, filename):
    """All (Kb,T) curves on a single graph, colored by T, linestyle by Kb."""
    import matplotlib.cm as cm
    from matplotlib.colors import Normalize
    subset = [r for r in runs if r["sweep"] == sweep and r["patch_set"] == pset]
    if not subset:
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    cmap = cm.get_cmap("viridis")
    t_norm = Normalize(vmin=min(T_VALS), vmax=max(T_VALS))
    kb_styles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 1))]

    for r in subset:
        data = get_energy_data(r["run_dir"], sweep)
        if data is None or len(data) < 2:
            continue
        t = data[:, 0]
        pe = data[:, 1]
        ti_idx = T_VALS.index(r["T"]) if r["T"] in T_VALS else 0
        ki_idx = KB_VALS.index(r["Kb"]) if r["Kb"] in KB_VALS else 0
        color = cmap(t_norm(r["T"]))
        ls = kb_styles[ki_idx % len(kb_styles)]
        ax.plot(t, pe, color=color, linestyle=ls, linewidth=0.7, alpha=0.8,
                label=f"Kb={r['Kb']}, T={r['T']}")

    ax.set_xlabel("Time (sim. units)", fontsize=10)
    ax.set_ylabel("PE / N", fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, linewidth=0.3, alpha=0.3)
    ax.legend(fontsize=5.5, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.22),
              framealpha=0.5)
    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def plot_energy_preconnected(runs, filename):
    """Preconnected sweep: all 6 temps on one graph."""
    subset = [r for r in runs if r["sweep"] == "preconnected"]
    if not subset:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.plasma(np.linspace(0, 0.85, len(subset)))
    for i, r in enumerate(sorted(subset, key=lambda x: x["T"])):
        data = get_energy_data(r["run_dir"], "preconnected")
        if data is None or len(data) < 2:
            continue
        ax.plot(data[:, 0], data[:, 1], color=colors[i], linewidth=1.0, alpha=0.85,
                label=f"T={r['T']}")
    ax.set_xlabel("Time (sim. units)", fontsize=10)
    ax.set_ylabel("PE / N", fontsize=10)
    ax.set_title("Preconnected seed sweep — PE/N vs Time (Kb=300)", fontsize=12,
                 fontweight="bold")
    ax.grid(True, linewidth=0.3, alpha=0.3)
    ax.legend(fontsize=8)
    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def plot_energy_comparison(runs, pset, title, filename):
    """Compare stiffness vs seeded at same (Kb,T), overlaid."""
    stiff = [r for r in runs if r["sweep"] == "stiffness_sweep" and r["patch_set"] == pset]
    seed = [r for r in runs if r["sweep"] == "seeded_sweep" and r["patch_set"] == pset]
    if not stiff or not seed:
        return

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True,
                             gridspec_kw={"hspace": 0.25, "wspace": 0.15})
    for ki, kb in enumerate(KB_VALS):
        ax = axes[ki // 3, ki % 3]
        for r in [r for r in stiff if r["Kb"] == kb]:
            data = get_energy_data(r["run_dir"], "stiffness_sweep")
            if data is not None and len(data) > 1:
                ti_idx = T_VALS.index(r["T"]) if r["T"] in T_VALS else 0
                ax.plot(data[:, 0], data[:, 1], color=LINE_COLORS[ti_idx],
                        linewidth=0.7, alpha=0.6, label=f"stiff T={r['T']}")
        for r in [r for r in seed if r["Kb"] == kb]:
            data = get_energy_data(r["run_dir"], "seeded_sweep")
            if data is not None and len(data) > 1:
                ti_idx = T_VALS.index(r["T"]) if r["T"] in T_VALS else 0
                ax.plot(data[:, 0], data[:, 1], color=LINE_COLORS[ti_idx],
                        linewidth=0.7, alpha=0.6, linestyle="--",
                        label=f"seed T={r['T']}")
        ax.set_ylabel("PE / N", fontsize=8)
        ax.set_title(f"K$_b$ = {kb}", fontsize=9, fontweight="bold")
        ax.grid(True, linewidth=0.3, alpha=0.4)
        ax.tick_params(labelsize=7)
        if ki == 0:
            ax.legend(fontsize=5, ncol=2, loc="best", framealpha=0.5)
    for ax in axes[1, :]:
        ax.set_xlabel("Time (sim. units)", fontsize=9)
    fig.suptitle(title, fontsize=12, fontweight="bold", y=0.98)
    plt.savefig(PLOTS / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {filename}")


def main():
    print("Discovering simulation directories...")
    runs = discover_runs()
    print(f"Found {len(runs)} simulation directories")

    print("\nGenerating energy vs time line plots...")
    plot_energy_lines(runs, "stiffness_sweep", "weak_weak",
                      "Stiffness sweep — Weak-Weak: PE/N vs Time",
                      "energy_stiffness_weak_weak.png")
    plot_energy_lines(runs, "stiffness_sweep", "weak_strong",
                      "Stiffness sweep — Weak-Strong: PE/N vs Time",
                      "energy_stiffness_weak_strong.png")
    plot_energy_lines(runs, "seeded_sweep", "weak_weak",
                      "Seeded sweep — Weak-Weak: PE/N vs Time",
                      "energy_seeded_weak_weak.png")
    plot_energy_lines(runs, "seeded_sweep", "weak_strong",
                      "Seeded sweep — Weak-Strong: PE/N vs Time",
                      "energy_seeded_weak_strong.png")

    print("\nGenerating all-on-one-graph plots...")
    plot_energy_all_on_one(runs, "stiffness_sweep", "weak_weak",
                           "Stiffness sweep — Weak-Weak: All runs (color=T, style=Kb)",
                           "energy_stiffness_ww_all.png")
    plot_energy_all_on_one(runs, "stiffness_sweep", "weak_strong",
                           "Stiffness sweep — Weak-Strong: All runs (color=T, style=Kb)",
                           "energy_stiffness_ws_all.png")
    plot_energy_all_on_one(runs, "seeded_sweep", "weak_weak",
                           "Seeded sweep — Weak-Weak: All runs (color=T, style=Kb)",
                           "energy_seeded_ww_all.png")
    plot_energy_all_on_one(runs, "seeded_sweep", "weak_strong",
                           "Seeded sweep — Weak-Strong: All runs (color=T, style=Kb)",
                           "energy_seeded_ws_all.png")
    plot_energy_preconnected(runs, "energy_preconnected_all.png")

    print("\nGenerating stiffness vs seeded comparison plots...")
    plot_energy_comparison(runs, "weak_weak",
                           "Stiffness (solid) vs Seeded (dashed) — Weak-Weak",
                           "energy_comparison_ww.png")
    plot_energy_comparison(runs, "weak_strong",
                           "Stiffness (solid) vs Seeded (dashed) — Weak-Strong",
                           "energy_comparison_ws.png")

    print("\nGenerating energy grid plots...")
    plot_energy_grid(runs, "stiffness_sweep", "weak_weak",
                     "Stiffness sweep — Weak-Weak: PE/N vs Time (grid)",
                     "energy_stiffness_grid_ww.png")
    plot_energy_grid(runs, "stiffness_sweep", "weak_strong",
                     "Stiffness sweep — Weak-Strong: PE/N vs Time (grid)",
                     "energy_stiffness_grid_ws.png")
    plot_energy_grid(runs, "seeded_sweep", "weak_weak",
                     "Seeded sweep — Weak-Weak: PE/N vs Time (grid)",
                     "energy_seeded_grid_ww.png")
    plot_energy_grid(runs, "seeded_sweep", "weak_strong",
                     "Seeded sweep — Weak-Strong: PE/N vs Time (grid)",
                     "energy_seeded_grid_ws.png")

    print("\nGenerating energy summary bar charts...")
    plot_energy_summary_bars(runs, "stiffness_sweep", "weak_weak",
                             "Stiffness sweep — Weak-Weak: Final PE/N",
                             "energy_bars_stiffness_ww.png")
    plot_energy_summary_bars(runs, "stiffness_sweep", "weak_strong",
                             "Stiffness sweep — Weak-Strong: Final PE/N",
                             "energy_bars_stiffness_ws.png")
    plot_energy_summary_bars(runs, "seeded_sweep", "weak_weak",
                             "Seeded sweep — Weak-Weak: Final PE/N",
                             "energy_bars_seeded_ww.png")
    plot_energy_summary_bars(runs, "seeded_sweep", "weak_strong",
                             "Seeded sweep — Weak-Strong: Final PE/N",
                             "energy_bars_seeded_ws.png")

    print("\nComputing energy statistics...")
    stats = compute_stats(runs)
    stats_path = PLOTS / "energy_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  -> energy_stats.json ({len(stats)} runs)")

    # Print summary
    print("\n" + "=" * 80)
    print("  ENERGY SUMMARY")
    print("=" * 80)
    for sweep in ("stiffness_sweep", "seeded_sweep", "preconnected"):
        for pset in ("weak_weak", "weak_strong", "four_species"):
            subset = [s for s in stats if s["sweep"] == sweep and s["patch_set"] == pset]
            if not subset:
                continue
            pe_finals = [s["pe_final"] for s in subset]
            t_maxes = [s["t_max"] for s in subset]
            print(f"\n  {sweep} / {pset} ({len(subset)} runs):")
            print(f"    Final PE/N:  min={min(pe_finals):.3f}  max={max(pe_finals):.3f}  "
                  f"mean={np.mean(pe_finals):.3f}")
            print(f"    Max time:    {max(t_maxes):.0f} sim. units "
                  f"(avg={np.mean(t_maxes):.0f})")

    print("\n" + "=" * 80)
    print(f"\nAll output in {PLOTS}/")


if __name__ == "__main__":
    main()
