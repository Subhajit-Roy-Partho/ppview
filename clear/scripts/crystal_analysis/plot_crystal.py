#!/usr/bin/env python3
"""
PHB crystal analysis plots.
Reads crystal_analysis/results.json and generates:
  - plots/stiffness_heatmaps.png
  - plots/seeded_heatmaps.png
  - plots/comparison.png
  - plots/crystal_dashboard.html  (self-contained interactive)
"""
import base64
import io
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

HERE = Path(__file__).parent
PLOTS = HERE / "plots"
PLOTS.mkdir(exist_ok=True)

# ── Load & deduplicate results ────────────────────────────────────────────────

with open(HERE / "results.json") as f:
    raw = json.load(f)

# deduplicate by (sweep, patch_set, Kb, T); prefer ok=True entries
seen: dict = {}
for r in raw:
    key = (r["sweep"], r["patch_set"], round(r["Kb"]), round(r["T"], 3))
    if key not in seen or r.get("ok"):
        seen[key] = r
results = [r for r in seen.values() if r.get("ok")]

print(f"Loaded {len(results)} valid results")

# ── Parameter grids ───────────────────────────────────────────────────────────

KB_VALS  = [1, 3, 10, 30, 100, 300]
T_VALS   = [0.050, 0.060, 0.070, 0.078, 0.090, 0.100]
T_LABELS = ["0.05", "0.06", "0.07", "0.078", "0.09", "0.10"]
KB_LABELS = [str(k) for k in KB_VALS]

ENERGY_STEPS = {
    "stiffness_sweep": 1_500_000_000,
    "seeded_sweep":    1_500_000_000,
    "preconnected":    1_500_000_000,
}
PRINT_EVERY = {
    "stiffness_sweep": 100_000,
    "seeded_sweep":    100_000,
    "preconnected":    100_000,
}

def kb_round(v):
    return int(round(v))

def t_round(v):
    return round(float(v), 3)

def make_matrix(sweep, patch_set, metric):
    mat = np.full((len(KB_VALS), len(T_VALS)), np.nan)
    for r in results:
        if r["sweep"] != sweep or r["patch_set"] != patch_set:
            continue
        kb = kb_round(r["Kb"])
        T  = t_round(r["T"])
        if kb in KB_VALS and T in T_VALS:
            ki = KB_VALS.index(kb)
            ti = T_VALS.index(T)
            val = r["crystal"].get(metric, np.nan)
            mat[ki, ti] = val
    return mat

# ── Color helpers ─────────────────────────────────────────────────────────────
# Sequential: light slate → deep indigo (single hue, validated contrast)
SEQ_COLORS = ["#eef2fa", "#c7d4f0", "#8fa9e0", "#5c80cc", "#3158b3", "#163290"]
SEQ_CMAP   = LinearSegmentedColormap.from_list("phb_seq", SEQ_COLORS, N=256)

# For seeded (low values): green sequential
SEQ_GREEN  = ["#f0faf4", "#b8e8c5", "#70cc8a", "#2dad55", "#147a35", "#0a4d22"]
SEQ_GREEN_CMAP = LinearSegmentedColormap.from_list("phb_green", SEQ_GREEN, N=256)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ── Helper: draw one heatmap panel ───────────────────────────────────────────

def heatmap_panel(ax, mat, title, vmin, vmax, cmap, fmt="{:.0f}%",
                  scale=100, fontsize=8):
    im = ax.imshow(mat * scale, aspect="auto", origin="lower",
                   vmin=vmin, vmax=vmax, cmap=cmap,
                   extent=[-0.5, len(T_VALS)-0.5, -0.5, len(KB_VALS)-0.5])
    ax.set_xticks(range(len(T_VALS)))
    ax.set_xticklabels(T_LABELS, fontsize=7)
    ax.set_yticks(range(len(KB_VALS)))
    ax.set_yticklabels(KB_LABELS, fontsize=7)
    ax.set_xlabel("Temperature  T", fontsize=8)
    ax.set_ylabel("Bending stiffness  K$_b$", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold", pad=6)
    # draw grid
    for x in np.arange(-0.5, len(T_VALS), 1):
        ax.axvline(x, color="white", linewidth=0.4, alpha=0.6)
    for y in np.arange(-0.5, len(KB_VALS), 1):
        ax.axhline(y, color="white", linewidth=0.4, alpha=0.6)
    # annotate cells
    for ki in range(len(KB_VALS)):
        for ti in range(len(T_VALS)):
            v = mat[ki, ti]
            if np.isnan(v):
                continue
            frac = (v * scale - vmin) / max(vmax - vmin, 1e-9)
            text_color = "white" if frac > 0.55 else "#1a1a2e"
            ax.text(ti, ki, fmt.format(v * scale),
                    ha="center", va="center",
                    fontsize=fontsize, color=text_color, fontweight="bold")
    return im

# ── Figure 1: Stiffness sweep heatmaps ───────────────────────────────────────
print("Generating stiffness sweep heatmap...")
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5),
                         gridspec_kw={"wspace": 0.35})

for ax, pset, label in zip(axes,
                            ["weak_weak", "weak_strong"],
                            ["Weak–Weak patches", "Weak–Strong patches"]):
    mat = make_matrix("stiffness_sweep", pset, "largest_cluster_fraction")
    im = heatmap_panel(ax, mat,
                       f"Stiffness sweep — {label}\nLargest cluster fraction",
                       vmin=40, vmax=100, cmap=SEQ_CMAP)

fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Largest cluster  (%)")
fig.suptitle("Stiffness sweep: Crystal maintenance  (starting from pre-formed crystal)",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "stiffness_heatmaps.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → stiffness_heatmaps.png")

# ── Figure 2: Stiffness — avg valence ────────────────────────────────────────
print("Generating avg valence heatmaps...")
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5),
                         gridspec_kw={"wspace": 0.35})
VAL_COLORS = ["#fefaf0", "#fde68a", "#f59e0b", "#b45309", "#78350f", "#3d1c04"]
val_cmap = LinearSegmentedColormap.from_list("val", VAL_COLORS, N=256)

for ax, pset, label in zip(axes,
                            ["weak_weak", "weak_strong"],
                            ["Weak–Weak", "Weak–Strong"]):
    mat = make_matrix("stiffness_sweep", pset, "avg_valence")
    im = heatmap_panel(ax, mat,
                       f"Avg bonds / molecule — {label}",
                       vmin=0, vmax=6, cmap=val_cmap,
                       fmt="{:.2f}", scale=1, fontsize=7)
fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Avg inter-mol bonds (max 6)")
fig.suptitle("Stiffness sweep: Average molecular valence",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "stiffness_valence.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → stiffness_valence.png")

# ── Figure 3: Seeded sweep (early stage) ─────────────────────────────────────
print("Generating seeded sweep heatmaps...")
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5),
                         gridspec_kw={"wspace": 0.35})
for ax, pset, label in zip(axes,
                            ["weak_weak", "weak_strong"],
                            ["Weak–Weak", "Weak–Strong"]):
    mat = make_matrix("seeded_sweep", pset, "largest_cluster_fraction")
    im = heatmap_panel(ax, mat,
                       f"Seeded sweep — {label}\nLargest cluster fraction",
                       vmin=0, vmax=5, cmap=SEQ_GREEN_CMAP,
                       fmt="{:.1f}%")

fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Largest cluster  (%)")
note = ("Note: seeded sweep runs are early-stage (≤0.5% of target steps completed).\n"
        "Values of ~1–2% reflect the seed cluster only; crystal growth is ongoing.")
fig.text(0.5, -0.04, note, ha="center", fontsize=8, color="#6b7280",
         style="italic")
fig.suptitle("Seeded sweep: Crystal nucleation progress  (starting from dispersed monomers + seed)",
             fontsize=10, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "seeded_heatmaps.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → seeded_heatmaps.png")

# ── Figure 4: Preconnected ───────────────────────────────────────────────────
print("Generating preconnected bar chart...")
pre_data = [(r["T"], r["crystal"]["largest_cluster_fraction"],
             r["crystal"]["avg_valence"])
            for r in results if r["sweep"] == "preconnected"]
pre_data.sort()
T_pre  = [d[0] for d in pre_data]
LC_pre = [d[1]*100 for d in pre_data]
AV_pre = [d[2] for d in pre_data]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5),
                                gridspec_kw={"wspace": 0.4})
bar_color = "#5c80cc"
ax1.bar([str(t) for t in T_pre], LC_pre, color=bar_color, width=0.5,
        edgecolor="white", linewidth=0.4)
ax1.set_ylim(0, max(LC_pre)*1.4 + 1)
ax1.set_xlabel("Temperature  T", fontsize=9)
ax1.set_ylabel("Largest cluster  (%)", fontsize=9)
ax1.set_title("Largest cluster fraction\n(K$_b$=300, four-species)", fontsize=9, fontweight="bold")
for i, v in enumerate(LC_pre):
    ax1.text(i, v + 0.05, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)

ax2.bar([str(t) for t in T_pre], AV_pre, color="#f59e0b", width=0.5,
        edgecolor="white", linewidth=0.4)
ax2.set_ylim(0, 6.5)
ax2.set_xlabel("Temperature  T", fontsize=9)
ax2.set_ylabel("Avg inter-mol bonds", fontsize=9)
ax2.set_title("Average valence\n(K$_b$=300, four-species)", fontsize=9, fontweight="bold")
ax2.axhline(6, color="#9ca3af", linewidth=0.8, linestyle="--", label="max (6)")
ax2.legend(fontsize=8)
for i, v in enumerate(AV_pre):
    ax2.text(i, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=8)

fig.suptitle("Preconnected seed sweep — Kb=300, four species",
             fontsize=11, fontweight="bold", y=1.02)
plt.savefig(PLOTS / "preconnected.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → preconnected.png")

# ── Figure 5: Comparison — LC vs T per Kb level (stiffness_sweep only) ───────
print("Generating comparison line plot...")
fig, axes = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"wspace": 0.35})
LINE_COLORS = ["#163290","#3158b3","#5c80cc","#8fa9e0",
               "#f59e0b","#b45309"]

for ax, pset, label in zip(axes,
                            ["weak_weak", "weak_strong"],
                            ["Weak–Weak", "Weak–Strong"]):
    for ki, (kb, lc) in enumerate(zip(KB_VALS, LINE_COLORS)):
        mat = make_matrix("stiffness_sweep", pset, "largest_cluster_fraction")
        row = mat[ki, :]
        mask = ~np.isnan(row)
        ax.plot(np.array(T_VALS)[mask], row[mask]*100,
                "-o", color=lc, markersize=5, linewidth=1.8,
                label=f"K$_b$={kb}", markeredgecolor="white",
                markeredgewidth=0.6)
    ax.set_ylim(30, 100)
    ax.set_xlabel("Temperature  T", fontsize=9)
    ax.set_ylabel("Largest cluster  (%)", fontsize=9)
    ax.set_title(f"Stiffness sweep — {label}", fontsize=9, fontweight="bold")
    ax.legend(fontsize=7.5, ncol=2, framealpha=0.5)
    ax.grid(axis="y", linewidth=0.4, alpha=0.5)
    ax.set_xticks(T_VALS)
    ax.set_xticklabels(T_LABELS, fontsize=8)

fig.suptitle("Crystal maintenance vs temperature — stiffness sweep",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "comparison_lines.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → comparison_lines.png")

# ── Figure 5b: Absolute largest cluster (molecule count) heatmaps ───────────
print("Generating absolute molecule count heatmaps...")

def make_matrix_abs(sweep, patch_set, metric="largest_cluster"):
    mat = np.full((len(KB_VALS), len(T_VALS)), np.nan)
    for r in results:
        if r["sweep"] != sweep or r["patch_set"] != patch_set:
            continue
        kb = kb_round(r["Kb"])
        T  = t_round(r["T"])
        if kb in KB_VALS and T in T_VALS:
            ki = KB_VALS.index(kb)
            ti = T_VALS.index(T)
            val = r["crystal"].get(metric, np.nan)
            mat[ki, ti] = val
    return mat

# Stiffness: absolute mol count (out of 2048)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={"wspace": 0.35})
for ax, pset, label in zip(axes, ["weak_weak", "weak_strong"],
                           ["Weak–Weak", "Weak–Strong"]):
    mat = make_matrix_abs("stiffness_sweep", pset, "largest_cluster")
    im = heatmap_panel(ax, mat,
                       f"Stiffness — {label}\nLargest cluster (molecules, out of 2048)",
                       vmin=0, vmax=2048, cmap=SEQ_CMAP,
                       fmt="{:.0f}", scale=1, fontsize=7)
fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Molecules in largest cluster")
fig.suptitle("Stiffness sweep: Largest crystal size (absolute molecule count)",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "stiffness_molcount_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → stiffness_molcount_heatmap.png")

# Seeded: absolute mol count (out of 500)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={"wspace": 0.35})
for ax, pset, label in zip(axes, ["weak_weak", "weak_strong"],
                           ["Weak–Weak", "Weak–Strong"]):
    mat = make_matrix_abs("seeded_sweep", pset, "largest_cluster")
    im = heatmap_panel(ax, mat,
                       f"Seeded — {label}\nLargest cluster (molecules, out of 500)",
                       vmin=0, vmax=20, cmap=SEQ_GREEN_CMAP,
                       fmt="{:.0f}", scale=1, fontsize=7)
fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Molecules in largest cluster")
fig.suptitle("Seeded sweep: Largest crystal size (absolute molecule count)",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "seeded_molcount_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → seeded_molcount_heatmap.png")

# ── Figure 5c: Combined overview — all 4 grids in one figure ─────────────────
print("Generating combined overview figure...")
fig, axes = plt.subplots(2, 2, figsize=(12, 10),
                         gridspec_kw={"hspace": 0.4, "wspace": 0.35})

# (0,0) Stiffness WW — LC%
mat = make_matrix("stiffness_sweep", "weak_weak", "largest_cluster_fraction")
im0 = heatmap_panel(axes[0,0], mat, "Stiffness — Weak-Weak\nLargest cluster (%)",
                    vmin=40, vmax=100, cmap=SEQ_CMAP)

# (0,1) Stiffness WS — LC%
mat = make_matrix("stiffness_sweep", "weak_strong", "largest_cluster_fraction")
im1 = heatmap_panel(axes[0,1], mat, "Stiffness — Weak-Strong\nLargest cluster (%)",
                    vmin=40, vmax=100, cmap=SEQ_CMAP)

# (1,0) Seeded WW — LC%
mat = make_matrix("seeded_sweep", "weak_weak", "largest_cluster_fraction")
im2 = heatmap_panel(axes[1,0], mat, "Seeded — Weak-Weak\nLargest cluster (%)",
                    vmin=0, vmax=5, cmap=SEQ_GREEN_CMAP, fmt="{:.1f}%")

# (1,1) Seeded WS — LC%
mat = make_matrix("seeded_sweep", "weak_strong", "largest_cluster_fraction")
im3 = heatmap_panel(axes[1,1], mat, "Seeded — Weak-Strong\nLargest cluster (%)",
                    vmin=0, vmax=5, cmap=SEQ_GREEN_CMAP, fmt="{:.1f}%")

fig.colorbar(im0, ax=axes[0,:], shrink=0.7, pad=0.02, label="Largest cluster (%)")
fig.colorbar(im2, ax=axes[1,:], shrink=0.7, pad=0.02, label="Largest cluster (%)")
fig.suptitle("PHB Crystal Formation — Color Gradient Heatmaps\n"
             "Rows: Bending stiffness Kb | Columns: Temperature T",
             fontsize=13, fontweight="bold", y=1.01)
plt.savefig(PLOTS / "crystal_heatmap_overview.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → crystal_heatmap_overview.png")

# ── Build HTML dashboard ──────────────────────────────────────────────────────
print("Building HTML dashboard...")

def png_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

imgs = {
    "stiffness_lc":  png_to_b64(PLOTS / "stiffness_heatmaps.png"),
    "stiffness_val": png_to_b64(PLOTS / "stiffness_valence.png"),
    "seeded_lc":     png_to_b64(PLOTS / "seeded_heatmaps.png"),
    "preconnected":  png_to_b64(PLOTS / "preconnected.png"),
    "lines":         png_to_b64(PLOTS / "comparison_lines.png"),
}

# Summary stats
def summary_stats():
    rows = []
    for sweep in ("stiffness_sweep", "seeded_sweep", "preconnected"):
        for pset in ("weak_weak", "weak_strong", "four_species"):
            subset = [r for r in results
                      if r["sweep"] == sweep and r["patch_set"] == pset]
            if not subset:
                continue
            lc_vals = [r["crystal"]["largest_cluster_fraction"]*100 for r in subset]
            av_vals = [r["crystal"]["avg_valence"] for r in subset]
            rows.append({
                "sweep": sweep.replace("_", " "),
                "patch_set": pset.replace("_", "–"),
                "n": len(subset),
                "lc_mean": np.mean(lc_vals),
                "lc_min": np.min(lc_vals),
                "lc_max": np.max(lc_vals),
                "av_mean": np.mean(av_vals),
            })
    return rows

stats = summary_stats()
stats_json = json.dumps(stats)

html = f"""<title>PHB Crystal Analysis Dashboard</title>
<style>
  :root {{
    --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0;
    --text: #1e293b; --muted: #64748b; --accent: #3158b3;
    --tag-bg: #eff6ff; --tag-text: #1d4ed8;
  }}
  [data-theme="dark"] {{
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #f1f5f9; --muted: #94a3b8; --accent: #8fa9e0;
    --tag-bg: #1e3a5f; --tag-text: #93c5fd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; font-size: 14px; line-height: 1.5; }}
  .header {{ background: var(--card); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
  .header h1 {{ font-size: 18px; font-weight: 700; color: var(--accent); }}
  .header .sub {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}
  .toggle-btn {{ background: var(--tag-bg); color: var(--tag-text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 12px; font-weight: 600; }}
  .main {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 15px; font-weight: 700; margin-bottom: 4px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); display: inline-block; }}
  .section-desc {{ font-size: 12px; color: var(--muted); margin-bottom: 14px; margin-top: 4px; }}
  .plot-img {{ width: 100%; border-radius: 8px; border: 1px solid var(--border); background: var(--card); display: block; }}
  .tabs {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
  .tab {{ padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--card); color: var(--muted); transition: all .15s; }}
  .tab.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 12px; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }}
  .stat-card .sc-sweep {{ font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }}
  .stat-card .sc-pset {{ font-size: 12px; color: var(--muted); margin-bottom: 8px; }}
  .stat-row {{ display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid var(--border); font-size: 13px; }}
  .stat-row:last-child {{ border: none; }}
  .stat-val {{ font-weight: 700; color: var(--text); }}
  .note {{ background: var(--tag-bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; font-size: 12px; color: var(--muted); margin-top: 10px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; background: var(--tag-bg); color: var(--tag-text); margin-left: 6px; }}
</style>

<div class="header">
  <div>
    <h1>PHB Crystal Analysis Dashboard</h1>
    <div class="sub">hand5 simulations — largest cluster fraction &amp; valence analysis</div>
  </div>
  <button class="toggle-btn" onclick="toggleDark()">Toggle dark mode</button>
</div>

<div class="main">

  <!-- Summary stats -->
  <div class="section">
    <div class="section-title">Summary</div>
    <div class="section-desc">Key metrics across all 148 analyzed configurations (final_conf.dat checkpoint).</div>
    <div class="stats-grid" id="stats-grid"></div>
  </div>

  <!-- Tabbed plots -->
  <div class="section">
    <div class="section-title">Crystal Quality Heatmaps</div>
    <div class="section-desc">Color = metric value; rows = K<sub>b</sub> (bending stiffness); columns = temperature T.</div>
    <div class="tabs">
      <div class="tab active" onclick="showTab('lc')">Largest cluster fraction</div>
      <div class="tab" onclick="showTab('val')">Avg valence</div>
      <div class="tab" onclick="showTab('seeded')">Seeded sweep (early stage)</div>
    </div>
    <div id="tab-lc" class="tab-content active">
      <img src="data:image/png;base64,{imgs['stiffness_lc']}" class="plot-img" alt="Stiffness sweep largest cluster fraction heatmaps">
    </div>
    <div id="tab-val" class="tab-content">
      <img src="data:image/png;base64,{imgs['stiffness_val']}" class="plot-img" alt="Stiffness sweep avg valence heatmaps">
    </div>
    <div id="tab-seeded" class="tab-content">
      <img src="data:image/png;base64,{imgs['seeded_lc']}" class="plot-img" alt="Seeded sweep heatmaps">
      <div class="note">⚠ Seeded simulations are at ≈0.5% completion (≈6.8M / 1.5B target steps). Values of 1–2% reflect the seed cluster only. Crystal growth is diffusion-limited and ongoing.</div>
    </div>
  </div>

  <!-- Comparison lines -->
  <div class="section">
    <div class="section-title">LC fraction vs Temperature  <span class="badge">Stiffness sweep</span></div>
    <div class="section-desc">Each line = one K<sub>b</sub> value. Shows how crystal maintenance depends on temperature and patch stiffness.</div>
    <img src="data:image/png;base64,{imgs['lines']}" class="plot-img" alt="LC vs T line plots">
  </div>

  <!-- Preconnected -->
  <div class="section">
    <div class="section-title">Preconnected seed sweep  <span class="badge">K<sub>b</sub>=300 · four species</span></div>
    <div class="section-desc">4 temperature points at fixed K<sub>b</sub>=300 with four-species preconnected seed topology. Early stage.</div>
    <img src="data:image/png;base64,{imgs['preconnected']}" class="plot-img" alt="Preconnected results">
  </div>

</div>

<script>
var stats = {stats_json};

function toggleDark() {{
  var el = document.documentElement;
  el.setAttribute('data-theme', el.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}}

function showTab(id) {{
  document.querySelectorAll('.tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
  document.querySelectorAll('.tab').forEach(function(el) {{ el.classList.remove('active'); }});
  document.getElementById('tab-' + id).classList.add('active');
  event.target.classList.add('active');
}}

function sweepLabel(s) {{
  return {{stiffness_sweep:'Stiffness sweep',seeded_sweep:'Seeded sweep',preconnected:'Preconnected'}}[s] || s;
}}

var grid = document.getElementById('stats-grid');
stats.forEach(function(s) {{
  var div = document.createElement('div');
  div.className = 'stat-card';
  div.innerHTML =
    '<div class="sc-sweep">' + sweepLabel(s.sweep) + '</div>' +
    '<div class="sc-pset">' + s.patch_set + '  (' + s.n + ' sims)</div>' +
    '<div class="stat-row"><span>Largest cluster</span><span class="stat-val">' + s.lc_mean.toFixed(1) + '% <small style="font-weight:normal;color:var(--muted)">(' + s.lc_min.toFixed(1) + '–' + s.lc_max.toFixed(1) + '%)</small></span></div>' +
    '<div class="stat-row"><span>Avg valence</span><span class="stat-val">' + s.av_mean.toFixed(2) + ' / 6</span></div>';
  grid.appendChild(div);
}});
</script>
"""

html_path = PLOTS / "crystal_dashboard.html"
html_path.write_text(html)
print(f"  → crystal_dashboard.html")
print(f"\nAll output in {PLOTS}/")
