#!/usr/bin/env python3
"""
make_plots.py — Generate crystal analysis plots from crystal_results.csv and preconn_results.csv.
Run after run_batch.py.
"""

import os
import csv
import math
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_pdf import PdfPages

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(OUT_DIR, "crystal_results.csv")
PRECONN_CSV = os.path.join(OUT_DIR, "preconn_results.csv")
PDF_PATH = os.path.join(OUT_DIR, "all_plots.pdf")

plt.rcParams.update({'font.size': 11, 'figure.dpi': 120})

# ── Load data ─────────────────────────────────────────────────────────────────

def load_csv(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def to_f(x, default=0.0):
    try: return float(x)
    except: return default

rows = load_csv(CSV_PATH)
preconn_rows = load_csv(PRECONN_CSV)

seeded_ws = [r for r in rows if r['group'] == 'seeded_s8' and r['set_name'] == 'weak_strong']
seeded_ww = [r for r in rows if r['group'] == 'seeded_s8' and r['set_name'] == 'weak_weak']
stiff_ws  = [r for r in rows if r['group'] == 'stiffness' and r['set_name'] == 'weak_strong']
stiff_ww  = [r for r in rows if r['group'] == 'stiffness' and r['set_name'] == 'weak_weak']

SEED_GROUPS = ['seeded_s8', 'seeded_s32', 'seeded_s48']
SEED_LABELS = {'seeded_s8': 's8 (8-mol seed)', 'seeded_s32': 's32 (32-mol seed)', 'seeded_s48': 's48 (48-mol seed)'}

# ── Pivot helper ──────────────────────────────────────────────────────────────

def pivot_heatmap(dataset, value_key):
    """Return Kbs, Ts, Z matrix for heatmap."""
    kbs = sorted(set(to_f(r['Kb']) for r in dataset))
    ts  = sorted(set(to_f(r['T']) for r in dataset))
    Z = np.full((len(kbs), len(ts)), np.nan)
    for r in dataset:
        ki = kbs.index(to_f(r['Kb']))
        ti = ts.index(to_f(r['T']))
        Z[ki, ti] = to_f(r[value_key])
    return kbs, ts, Z


def make_heatmap(ax, kbs, ts, Z, title, cmap='viridis', vmin=None, vmax=None, fmt='.0f'):
    im = ax.imshow(Z, aspect='auto', origin='lower',
                   vmin=vmin if vmin is not None else np.nanmin(Z),
                   vmax=vmax if vmax is not None else np.nanmax(Z),
                   cmap=cmap)
    ax.set_xticks(range(len(ts)));  ax.set_xticklabels([f'{t:.3f}' for t in ts], rotation=45, ha='right')
    ax.set_yticks(range(len(kbs))); ax.set_yticklabels([f'{k:.0f}' for k in kbs])
    ax.set_xlabel('T'); ax.set_ylabel('Kb')
    ax.set_title(title)
    # Annotate cells
    for i in range(len(kbs)):
        for j in range(len(ts)):
            v = Z[i, j]
            if np.isfinite(v):
                ax.text(j, i, format(v, fmt), ha='center', va='center', fontsize=7,
                        color='white' if v < (np.nanmax(Z) * 0.6) else 'black')
    return im

# ── Figure 1: seeded largest_cluster heatmaps ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Seeded Sweep — Largest Crystal Cluster Size', fontsize=13)
for ax, ds, title in zip(axes, [seeded_ws, seeded_ww], ['Weak-Strong', 'Weak-Weak']):
    kbs, ts, Z = pivot_heatmap(ds, 'largest_cluster')
    im = make_heatmap(ax, kbs, ts, Z, title, cmap='plasma')
    fig.colorbar(im, ax=ax, label='Molecules in largest cluster')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig1_seeded_largest_cluster.png'))
plt.close(fig)
print("fig1 done")

# ── Figure 2: seeded frac_bonded heatmaps ────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Seeded Sweep — Fraction of Molecules Bonded (v≥1)', fontsize=13)
for ax, ds, title in zip(axes, [seeded_ws, seeded_ww], ['Weak-Strong', 'Weak-Weak']):
    kbs, ts, Z = pivot_heatmap(ds, 'frac_bonded')
    im = make_heatmap(ax, kbs, ts, Z, title, cmap='YlOrRd', vmin=0, vmax=1, fmt='.2f')
    fig.colorbar(im, ax=ax, label='Frac bonded')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig2_seeded_frac_bonded.png'))
plt.close(fig)
print("fig2 done")

# ── Figure 3: seeded avg_valence heatmaps ────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Seeded Sweep — Average Valence per Molecule', fontsize=13)
for ax, ds, title in zip(axes, [seeded_ws, seeded_ww], ['Weak-Strong', 'Weak-Weak']):
    kbs, ts, Z = pivot_heatmap(ds, 'avg_valence')
    im = make_heatmap(ax, kbs, ts, Z, title, cmap='Blues', vmin=0, fmt='.2f')
    fig.colorbar(im, ax=ax, label='Avg valence')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig3_seeded_avg_valence.png'))
plt.close(fig)
print("fig3 done")

# ── Figure 4: stiffness largest_cluster heatmaps ─────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Stiffness Sweep — Largest Crystal Cluster Size', fontsize=13)
for ax, ds, title in zip(axes, [stiff_ws, stiff_ww], ['Weak-Strong', 'Weak-Weak']):
    kbs, ts, Z = pivot_heatmap(ds, 'largest_cluster')
    im = make_heatmap(ax, kbs, ts, Z, title, cmap='plasma')
    fig.colorbar(im, ax=ax, label='Molecules in largest cluster')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig4_stiffness_largest_cluster.png'))
plt.close(fig)
print("fig4 done")

# ── Figure 5: stiffness frac_bonded + avg_valence heatmaps ───────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Stiffness Sweep — Bonding Summary', fontsize=13)
for col, (ds, set_lbl) in enumerate([(stiff_ws, 'Weak-Strong'), (stiff_ww, 'Weak-Weak')]):
    kbs, ts, Zfb = pivot_heatmap(ds, 'frac_bonded')
    _, _, Zav    = pivot_heatmap(ds, 'avg_valence')
    im0 = make_heatmap(axes[0, col], kbs, ts, Zfb, f'{set_lbl} — Frac Bonded',
                       cmap='YlOrRd', vmin=0, vmax=1, fmt='.2f')
    im1 = make_heatmap(axes[1, col], kbs, ts, Zav, f'{set_lbl} — Avg Valence',
                       cmap='Blues', vmin=0, fmt='.2f')
    fig.colorbar(im0, ax=axes[0, col])
    fig.colorbar(im1, ax=axes[1, col])
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig5_stiffness_bonding.png'))
plt.close(fig)
print("fig5 done")

# ── Figure 6: Seeded vs Stiffness scatter — largest cluster ──────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Seeded vs Stiffness Sweep — Largest Cluster Comparison', fontsize=13)
for ax, set_name, lbl in zip(axes, ['weak_strong', 'weak_weak'], ['Weak-Strong', 'Weak-Weak']):
    s_rows = [r for r in rows if r['set_name'] == set_name and r['group'] == 'seeded_s8']
    st_rows = [r for r in rows if r['set_name'] == set_name and r['group'] == 'stiffness']
    # Build dict keyed by (Kb, T)
    s_dict  = {(to_f(r['Kb']), to_f(r['T'])): to_f(r['largest_cluster']) for r in s_rows}
    st_dict = {(to_f(r['Kb']), to_f(r['T'])): to_f(r['largest_cluster']) for r in st_rows}
    common  = set(s_dict) & set(st_dict)
    xs = [s_dict[k] for k in common]
    ys = [st_dict[k] for k in common]
    n_mol = 72  # approximate
    ax.scatter(xs, ys, alpha=0.7, c='steelblue', edgecolors='k', s=40)
    lim = max(max(xs, default=1), max(ys, default=1)) + 5
    ax.plot([0, lim], [0, lim], 'k--', lw=0.8, label='y=x')
    ax.set_xlabel('Seeded — largest cluster')
    ax.set_ylabel('Stiffness — largest cluster')
    ax.set_title(lbl)
    ax.legend()
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig6_seeded_vs_stiffness_scatter.png'))
plt.close(fig)
print("fig6 done")

# ── Figure 7: Preconn evolution — start → mc_relaxed → final ─────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Preconnected Seed Sweep — Crystal Evolution Across Stages', fontsize=13)

stages = ['start', 'mc_relaxed', 'final']
stage_labels = ['Start\n(preformed crystal)', 'After MC relax', 'After MD']
ts_preconn = sorted(set(to_f(r['T']) for r in preconn_rows))

for ax, metric, ylabel in zip(axes,
    ['largest_cluster', 'frac_bonded', 'avg_valence'],
    ['Largest cluster (molecules)', 'Fraction bonded', 'Avg valence']):
    for t_val in ts_preconn:
        yvals = []
        for stage in stages:
            match = next((r for r in preconn_rows if to_f(r['T']) == t_val and r['conf_stage'] == stage), None)
            yvals.append(to_f(match[metric]) if match else np.nan)
        ax.plot(range(3), yvals, marker='o', label=f'T={t_val:.3f}')
    ax.set_xticks(range(3))
    ax.set_xticklabels(stage_labels)
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel)
    ax.legend(fontsize=8)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig7_preconn_evolution.png'))
plt.close(fig)
print("fig7 done")

# ── Figure 8: Energy vs Crystal size correlation ──────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Energy vs Largest Cluster (Seeded Sweep)', fontsize=13)
for ax, ds, title in zip(axes, [seeded_ws, seeded_ww], ['Weak-Strong', 'Weak-Weak']):
    xs = [to_f(r['Epot_last']) for r in ds if r['Epot_last'] not in ('', 'nan')]
    ys = [to_f(r['largest_cluster']) for r in ds if r['Epot_last'] not in ('', 'nan')]
    ax.scatter(xs, ys, alpha=0.7, c='firebrick', edgecolors='k', s=40)
    ax.set_xlabel('Epot/particle (last frame)')
    ax.set_ylabel('Largest cluster (molecules)')
    ax.set_title(title)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig8_energy_vs_cluster.png'))
plt.close(fig)
print("fig8 done")

# ── Figure 9: Summary bar chart — top 15 conditions by cluster size ───────────
sorted_rows = sorted(rows, key=lambda r: -to_f(r['largest_cluster']))[:15]
labels = [f"{r['group'][:9]}\n{r['set_name'][:5]}\nKb{r['Kb']}\nT{r['T']}" for r in sorted_rows]
vals   = [to_f(r['largest_cluster']) for r in sorted_rows]
GROUP_COLORS = {'seeded_s8': 'steelblue', 'seeded_s32': 'mediumseagreen',
                'seeded_s48': 'mediumpurple', 'stiffness': 'darkorange'}
colors = [GROUP_COLORS.get(r['group'], 'gray') for r in sorted_rows]
n_mol  = to_f(sorted_rows[0]['n_mol']) if sorted_rows else 500

fig, ax = plt.subplots(figsize=(14, 5))
bars = ax.bar(range(len(vals)), vals, color=colors, edgecolor='k', linewidth=0.5)
ax.axhline(n_mol * 0.5, color='red', linestyle='--', linewidth=1, label='50% of system')
ax.axhline(n_mol, color='green', linestyle='--', linewidth=1, label='Total system')
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=7)
ax.set_ylabel('Molecules in largest cluster')
ax.set_title('Top 15 Conditions by Largest Crystal Cluster')
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=c, label=g) for g, c in GROUP_COLORS.items()]
ax.legend(handles=legend_elements + [
    plt.Line2D([0],[0], color='red', linestyle='--', label='50% threshold'),
    plt.Line2D([0],[0], color='green', linestyle='--', label='N_total'),
], fontsize=7)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig9_top15_bar.png'))
plt.close(fig)
print("fig9 done")

# ── Figure 10: Simulation progress (steps_M) heatmap for seeded ──────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Seeded Sweep — Simulation Progress (Million Steps)', fontsize=13)
for ax, ds, title in zip(axes, [seeded_ws, seeded_ww], ['Weak-Strong', 'Weak-Weak']):
    kbs, ts, Z = pivot_heatmap(ds, 'steps_M')
    im = make_heatmap(ax, kbs, ts, Z, title, cmap='Greens', vmin=0, fmt='.0f')
    fig.colorbar(im, ax=ax, label='Simulation steps (M)')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig10_steps_progress.png'))
plt.close(fig)
print("fig10 done")

# ── Figure 11: Seed-size comparison — largest cluster (s8 vs s32 vs s48) ─────
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Seed-Size Comparison — Largest Crystal Cluster Size', fontsize=13)
for row_idx, set_name in enumerate(['weak_strong', 'weak_weak']):
    for col_idx, group in enumerate(SEED_GROUPS):
        ax = axes[row_idx, col_idx]
        ds = [r for r in rows if r['group'] == group and r['set_name'] == set_name]
        if not ds:
            ax.set_visible(False)
            continue
        kbs, ts, Z = pivot_heatmap(ds, 'largest_cluster')
        im = make_heatmap(ax, kbs, ts, Z,
                          f"{SEED_LABELS[group]}\n{set_name.replace('_',' ').title()}",
                          cmap='plasma')
        fig.colorbar(im, ax=ax, label='Molecules', shrink=0.85)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig11_seed_size_largest_cluster.png'))
plt.close(fig)
print("fig11 done")

# ── Figure 12: Seed-size comparison — frac_bonded (s8 vs s32 vs s48) ─────────
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Seed-Size Comparison — Fraction of Molecules Bonded (v≥1)', fontsize=13)
for row_idx, set_name in enumerate(['weak_strong', 'weak_weak']):
    for col_idx, group in enumerate(SEED_GROUPS):
        ax = axes[row_idx, col_idx]
        ds = [r for r in rows if r['group'] == group and r['set_name'] == set_name]
        if not ds:
            ax.set_visible(False)
            continue
        kbs, ts, Z = pivot_heatmap(ds, 'frac_bonded')
        im = make_heatmap(ax, kbs, ts, Z,
                          f"{SEED_LABELS[group]}\n{set_name.replace('_',' ').title()}",
                          cmap='YlOrRd', vmin=0, vmax=1, fmt='.2f')
        fig.colorbar(im, ax=ax, label='Frac bonded', shrink=0.85)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig12_seed_size_frac_bonded.png'))
plt.close(fig)
print("fig12 done")

# ── Figure 13: Seed-size effect — line plot of cluster size vs seed n ────────
seed_ns = {'seeded_s8': 8, 'seeded_s32': 32, 'seeded_s48': 48}
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Seed-Size Effect — Largest Cluster vs Seed Size\nEach line = one Kb, at a fixed T', fontsize=13)
T_sel = ['0.050', '0.070', '0.090']
kbs_all = sorted(set(to_f(r['Kb']) for r in rows if r['group'] in SEED_GROUPS))
cmap_kb = plt.get_cmap('viridis')(np.linspace(0.1, 0.9, len(kbs_all)))
for col_idx, T_val in enumerate(T_sel):
    for row_idx, set_name in enumerate(['weak_strong', 'weak_weak']):
        ax = axes[row_idx, col_idx]
        for kb, color in zip(kbs_all, cmap_kb):
            ys = []
            for group in SEED_GROUPS:
                match = next((r for r in rows if r['group'] == group and r['set_name'] == set_name
                             and abs(to_f(r['Kb']) - kb) < 1e-6 and abs(to_f(r['T']) - to_f(T_val)) < 1e-6), None)
                ys.append(to_f(match['largest_cluster']) if match else 0)
            xs = [seed_ns[g] for g in SEED_GROUPS]
            ax.plot(xs, ys, 'o-', color=color, label=f'Kb={kb:.0f}', linewidth=1.5)
        ax.set_xticks(xs); ax.set_xticklabels([f'n={n}' for n in xs])
        ax.set_xlabel('Seed size (# molecules)')
        ax.set_ylabel('Largest cluster (molecules)')
        ax.set_title(f'{set_name.replace("_"," ").title()} | T={T_val}', fontsize=10)
        ax.legend(fontsize=6, ncol=2)
        ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig13_seed_size_line.png'))
plt.close(fig)
print("fig13 done")

# ── Combine all into PDF ──────────────────────────────────────────────────────
png_files = [
    'fig1_seeded_largest_cluster.png',
    'fig2_seeded_frac_bonded.png',
    'fig3_seeded_avg_valence.png',
    'fig4_stiffness_largest_cluster.png',
    'fig5_stiffness_bonding.png',
    'fig6_seeded_vs_stiffness_scatter.png',
    'fig7_preconn_evolution.png',
    'fig8_energy_vs_cluster.png',
    'fig9_top15_bar.png',
    'fig10_steps_progress.png',
    'fig11_seed_size_largest_cluster.png',
    'fig12_seed_size_frac_bonded.png',
    'fig13_seed_size_line.png',
]

with PdfPages(PDF_PATH) as pdf:
    for fname in png_files:
        fpath = os.path.join(OUT_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  WARN: {fname} not found, skipping")
            continue
        img = plt.imread(fpath)
        fig, ax = plt.subplots(figsize=(14, img.shape[0] / img.shape[1] * 14))
        ax.imshow(img)
        ax.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

print(f"\nAll plots written to {OUT_DIR}")
print(f"PDF: {PDF_PATH}")
