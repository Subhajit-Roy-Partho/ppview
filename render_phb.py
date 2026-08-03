#!/usr/bin/env python3
"""
render_phb.py — CLI renderer for PHB patchy-particle configurations.

Generates publication-quality images showing crystal vs gas-phase particles.

Usage:
    # Render a single configuration
    python render_phb.py --top topology.phb --conf final_conf.dat -o out.png

    # Render the 4 most important seeded-sweep configurations
    python render_phb.py --sweep /path/to/seeded_sweep

    # Custom view
    python render_phb.py --top topology.phb --conf final_conf.dat \
        --elev 25 --azim 45 --title "Kb=100 T=0.050" -o out.png

Color scheme (crystal coloring):
    Gray     (#aaaaaa) — Free gas monomers (no inter-molecular bonds)
    Cyan     (#00bcd4) — Weakly bonded (1 bond)
    Gold     (#ffa726) — Moderately bonded (2–3 bonds)
    Red      (#f44336) — Fully bonded / crystal-like (4+ bonds)
    Dark blue (seed)   — The original seed cluster (largest initial cluster)

Requirements: numpy, matplotlib
Optional: scipy (for better 3D rendering)
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass, field
from collections import defaultdict

# ── Patch/topology parsing (adapted from analyze_phb_crystal.py) ──────────

@dataclass
class Patch:
    pid: int
    color: int
    body_pos: np.ndarray


@dataclass
class Bead:
    idx: int
    ptype: int   # -3 = ico core, -4 = helix
    btype: int   # color/btype index
    strand: int
    patches: List[Patch] = field(default_factory=list)
    radius: float = 0.5


def parse_topology(top_file: str):
    """Parse PHB topology. Molecules = contiguous block of -4 beads + trailing -3 ico bead."""
    patch_defs = {}
    color_to_patches = {}
    beads = []
    header_read = False
    bead_idx = 0

    with open(top_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if not header_read:
                header_read = True
                continue
            if parts[0] == 'iP':
                pid = int(parts[1])
                color = int(parts[2])
                pos = np.array([float(parts[4]), float(parts[5]), float(parts[6])])
                patch_defs[pid] = Patch(pid=pid, color=color, body_pos=pos)
            elif parts[0] == 'iC':
                cid = int(parts[1])
                color_to_patches[cid] = [int(x) for x in parts[2:]]
            elif parts[0] in ('-3', '-4'):
                ptype = int(parts[0])
                strand = int(parts[1])
                btype = int(parts[2])
                radius = float(parts[3]) if len(parts) > 3 else 0.5
                pids = color_to_patches.get(btype, [])
                # Exclude color=100 (backbone springs, not interaction patches)
                patches = [patch_defs[p] for p in pids
                           if p in patch_defs and patch_defs[p].color != 100]
                b = Bead(idx=bead_idx, ptype=ptype, btype=btype,
                         strand=strand, patches=patches, radius=radius)
                beads.append(b)
                bead_idx += 1

    # Assign molecules: contiguous helix (-4) beads followed by ico (-3) bead
    mol_of_bead = {}
    ico_of_mol = {}
    pending = []
    mol_id = 0
    for b in beads:
        if b.ptype == -4:
            pending.append(b.idx)
        elif b.ptype == -3:
            for h in pending:
                mol_of_bead[h] = mol_id
            mol_of_bead[b.idx] = mol_id
            ico_of_mol[mol_id] = b.idx
            pending = []
            mol_id += 1

    return beads, mol_of_bead, ico_of_mol


def parse_conf(conf_file: str, N: int):
    positions = np.zeros((N, 3))
    a1_vecs = np.zeros((N, 3))
    a3_vecs = np.zeros((N, 3))
    box = np.array([50., 50., 50.])

    with open(conf_file) as f:
        f.readline()
        bline = f.readline().split()
        box = np.array([float(bline[2]), float(bline[3]), float(bline[4])])
        f.readline()
        for i in range(N):
            line = f.readline()
            if not line:
                break
            vals = line.split()
            positions[i] = [float(vals[0]), float(vals[1]), float(vals[2])]
            if len(vals) >= 6:
                a1_vecs[i] = [float(vals[3]), float(vals[4]), float(vals[5])]
            if len(vals) >= 9:
                a3_vecs[i] = [float(vals[6]), float(vals[7]), float(vals[8])]

    return box, positions, a1_vecs, a3_vecs


def world_patch(pos, a1, a3, body_pos):
    a2 = np.cross(a3, a1)
    n = np.linalg.norm(a2)
    if n > 1e-10:
        a2 = a2 / n
    R = np.column_stack([a1, a2, a3])
    return pos + R @ body_pos


def min_image(dr, box):
    return dr - box * np.round(dr / box)


def find_bonds(beads, positions, a1_vecs, a3_vecs, box, mol_of_bead, ico_of_mol, cutoff=0.25):
    """Find inter-molecular crystal bonds (ico↔helix-tip). Vectorised."""
    # Pre-compute world patch positions for ALL beads that have patches
    ico_patch_wpos = []   # (world_pos, color, mol_id)
    helix_patch_wpos = []

    for b in beads:
        if not b.patches:
            continue
        pos = positions[b.idx]
        a1 = a1_vecs[b.idx]
        a3 = a3_vecs[b.idx]
        a2 = np.cross(a3, a1)
        n = np.linalg.norm(a2)
        if n > 1e-10:
            a2 /= n
        R = np.column_stack([a1, a2, a3])
        mol = mol_of_bead[b.idx]
        for p in b.patches:
            wp = pos + R @ p.body_pos
            if b.ptype == -3:
                ico_patch_wpos.append((wp, p.color, mol))
            else:
                helix_patch_wpos.append((wp, p.color, mol))

    if not ico_patch_wpos or not helix_patch_wpos:
        return []

    ico_pos_arr = np.array([x[0] for x in ico_patch_wpos])   # (Ni, 3)
    ico_col_arr = np.array([x[1] for x in ico_patch_wpos])   # (Ni,)
    ico_mol_arr = np.array([x[2] for x in ico_patch_wpos])   # (Ni,)
    hel_pos_arr = np.array([x[0] for x in helix_patch_wpos]) # (Nh, 3)
    hel_col_arr = np.array([x[1] for x in helix_patch_wpos]) # (Nh,)
    hel_mol_arr = np.array([x[2] for x in helix_patch_wpos]) # (Nh,)

    bond_set = set()
    # Use spatial binning: divide box into cells of size cutoff
    cell = cutoff * 1.5
    hel_cell = np.floor(hel_pos_arr / cell).astype(int)
    hel_dict = defaultdict(list)
    for j, cj in enumerate(hel_cell):
        hel_dict[tuple(cj)].append(j)

    offsets = list(range(-1, 2))
    for i in range(len(ico_patch_wpos)):
        ci = np.floor(ico_pos_arr[i] / cell).astype(int)
        for dx in offsets:
            for dy in offsets:
                for dz in offsets:
                    key = (ci[0]+dx, ci[1]+dy, ci[2]+dz)
                    for j in hel_dict.get(key, []):
                        if ico_mol_arr[i] == hel_mol_arr[j]:
                            continue
                        if (ico_col_arr[i] + hel_col_arr[j]) != 0:
                            continue
                        dr = min_image(ico_pos_arr[i] - hel_pos_arr[j], box)
                        if np.dot(dr, dr) < cutoff * cutoff:
                            m1, m2 = int(ico_mol_arr[i]), int(hel_mol_arr[j])
                            bond_set.add((min(m1, m2), max(m1, m2)))

    return list(bond_set)


def find_clusters(bonds, n_mols):
    """Find connected components (clusters) from bond list."""
    parent = list(range(n_mols))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for m1, m2 in bonds:
        union(m1, m2)

    clusters = defaultdict(list)
    for i in range(n_mols):
        clusters[find(i)].append(i)
    return list(clusters.values())


# ── Crystal coloring ──────────────────────────────────────────────────────

COLORS = {
    "free":       "#9e9e9e",  # gray     — no bonds
    "bonded1":    "#29b6f6",  # cyan     — 1 bond
    "bonded2_3":  "#ffa726",  # orange   — 2–3 bonds
    "bonded4p":   "#ef5350",  # red      — 4+ bonds (crystal-like)
    "seed":       "#1565c0",  # dark blue — original seed cluster
    "helix_free": "#e0e0e0",  # light gray for helix beads (free)
    "helix_bond": "#81d4fa",  # light blue for helix beads (bonded mol)
}


def get_crystal_colors(mol_ids, valences, seed_mols):
    """Return color per molecule based on crystal bonding status."""
    colors = []
    for mol in mol_ids:
        if mol in seed_mols:
            colors.append(COLORS["seed"])
        elif valences.get(mol, 0) >= 4:
            colors.append(COLORS["bonded4p"])
        elif valences.get(mol, 0) >= 2:
            colors.append(COLORS["bonded2_3"])
        elif valences.get(mol, 0) == 1:
            colors.append(COLORS["bonded1"])
        else:
            colors.append(COLORS["free"])
    return colors


# ── Main rendering function ───────────────────────────────────────────────

def render_configuration(
    top_file: str,
    conf_file: str,
    output: str,
    title: str = "",
    elev: float = 25,
    azim: float = 45,
    show_helix: bool = True,
    cutoff: float = 0.25,
    alpha_free: float = 0.15,
    alpha_bonded: float = 0.85,
    dpi: int = 200,
):
    """Render a PHB configuration with crystal coloring."""
    beads, mol_of_bead, ico_of_mol = parse_topology(top_file)
    N = len(beads)
    box, positions, a1_vecs, a3_vecs = parse_conf(conf_file, N)

    n_mols = len(ico_of_mol)

    # Find bonds and valences
    bonds = find_bonds(beads, positions, a1_vecs, a3_vecs, box, mol_of_bead, ico_of_mol, cutoff)
    valences = defaultdict(int)
    for m1, m2 in bonds:
        valences[m1] += 1
        valences[m2] += 1

    # Find clusters
    clusters = find_clusters(bonds, n_mols)
    largest = max(clusters, key=len)
    seed_mols = set(largest)  # approximate seed = largest cluster

    # Color each molecule
    mol_ids = list(range(n_mols))
    mol_colors = get_crystal_colors(mol_ids, valences, seed_mols)

    # Ico positions
    ico_positions = np.array([positions[ico_of_mol[m]] for m in mol_ids])
    ico_radii = np.array([beads[ico_of_mol[m]].radius for m in mol_ids])

    # Shift to center the box
    ico_positions = ico_positions - box / 2.0

    # ── Figure ────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot ico spheres grouped by color for legend
    color_groups = {
        "seed": (COLORS["seed"], "Seed cluster", "^", 1.0),
        "bonded4p": (COLORS["bonded4p"], "Crystal (≥4 bonds)", "o", alpha_bonded),
        "bonded2_3": (COLORS["bonded2_3"], "Assembling (2–3 bonds)", "o", alpha_bonded),
        "bonded1": (COLORS["bonded1"], "Weakly bonded (1 bond)", "o", 0.7),
        "free": (COLORS["free"], "Free gas", "o", alpha_free),
    }

    val_labels = {COLORS["seed"]: "seed", COLORS["bonded4p"]: "bonded4p",
                  COLORS["bonded2_3"]: "bonded2_3", COLORS["bonded1"]: "bonded1",
                  COLORS["free"]: "free"}

    for group_key, (color, label, marker, alpha) in color_groups.items():
        mask = np.array([val_labels.get(c, "free") == group_key for c in mol_colors])
        if not mask.any():
            continue
        pts = ico_positions[mask]
        r = ico_radii[mask]
        size = (r * 200).clip(20, 400)  # map radius → marker size
        ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
                   c=color, s=size, marker=marker, alpha=alpha,
                   edgecolors='none', label=f"{label} ({mask.sum()})", depthshade=True)

    # Draw bond lines
    for m1, m2 in bonds[:500]:  # cap at 500 for performance
        p1 = positions[ico_of_mol[m1]] - box / 2
        p2 = positions[ico_of_mol[m2]] - box / 2
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                c='#555555', lw=0.5, alpha=0.3)

    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect([1, 1, 1])
    half = box[0] / 2
    ax.set_xlim([-half, half])
    ax.set_ylim([-half, half])
    ax.set_zlim([-half, half])
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")

    # Stats text
    n_bonded = sum(1 for m in mol_ids if valences.get(m, 0) >= 1)
    n_crystal = sum(1 for m in mol_ids if valences.get(m, 0) >= 4)
    stats = (f"Bonds: {len(bonds)}   Bonded: {n_bonded}/{n_mols} ({100*n_bonded/max(n_mols,1):.0f}%)\n"
             f"Crystal-like (≥4 bonds): {n_crystal}  |  Seed: {len(seed_mols)} mol")
    ax.text2D(0.02, 0.98, stats, transform=ax.transAxes,
              fontsize=8, va='top', fontfamily='monospace',
              bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    ax.legend(loc='lower right', fontsize=8, framealpha=0.8)
    ax.set_title(title or Path(conf_file).parent.name, fontsize=12, fontweight='bold')

    fig.tight_layout()
    fig.savefig(output, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {output}")
    print(f"  Bonds: {len(bonds)}  |  Bonded: {n_bonded}/{n_mols}  |  Crystal-like: {n_crystal}")


# ── Batch rendering for the sweep ─────────────────────────────────────────

def render_sweep(sweep_dir: str, output_dir: str, top_systems: list = None, **kwargs):
    """Render multiple systems from a seeded sweep directory."""
    sweep = Path(sweep_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if top_systems is None:
        # Default: render the 4 most important weak_strong systems
        top_systems = [
            ("weak_strong", "Kb_100", "T_0.050", "ws Kb=100 T=0.050 (highest ΔE)"),
            ("weak_strong", "Kb_1",   "T_0.090", "ws Kb=1   T=0.090 (highest rate)"),
            ("weak_strong", "Kb_3",   "T_0.050", "ws Kb=3   T=0.050 (3rd highest ΔE)"),
            ("weak_strong", "Kb_1",   "T_0.078", "ws Kb=1   T=0.078 (stable assembler)"),
        ]

    for strength, kb, temp, label in top_systems:
        # Handle both Kb_X_T_Y and separate kb/temp tokens
        if "_" in kb and "_" in temp:
            run_dir = sweep / strength / f"{kb}_{temp}"
        else:
            run_dir = sweep / strength / f"{kb}_{temp}"

        top_f = run_dir / "topology.phb"
        conf_f = run_dir / "final_conf.dat"

        if not top_f.exists() or not conf_f.exists():
            print(f"  SKIP (missing files): {run_dir}")
            continue

        name = f"{strength}_{kb}_{temp}".replace(" ", "_")
        out_file = out / f"{name}.png"
        print(f"\nRendering {label} ...")
        render_configuration(str(top_f), str(conf_f), str(out_file),
                             title=label, **kwargs)


# ── Panel figure: 4-up comparison ─────────────────────────────────────────

def render_4panel(sweep_dir: str, output: str, **kwargs):
    """Render 4 key systems in a 2×2 panel figure."""
    systems = [
        ("weak_strong", "Kb_100_T_0.050", "ws Kb=100, T=0.050\n(Largest ΔE)"),
        ("weak_strong", "Kb_1_T_0.090",   "ws Kb=1,   T=0.090\n(Fastest rate)"),
        ("weak_strong", "Kb_3_T_0.050",   "ws Kb=3,   T=0.050\n(3rd ΔE)"),
        ("weak_strong", "Kb_1_T_0.078",   "ws Kb=1,   T=0.078\n(Broad assembler)"),
    ]

    fig = plt.figure(figsize=(16, 14))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25)
    fig.suptitle("PHB Seeded-Growth — Crystal Status of Top-4 Assemblers\n"
                 "Blue=seed  Red=crystal-like(≥4 bonds)  Orange=assembling  Cyan=weakly bonded  Gray=free gas",
                 fontsize=12, fontweight="bold")

    sweep = Path(sweep_dir)
    color_legend_done = False

    for panel_idx, (strength, run_name, label) in enumerate(systems):
        run_dir = sweep / strength / run_name
        top_f = run_dir / "topology.phb"
        conf_f = run_dir / "final_conf.dat"

        ax = fig.add_subplot(gs[panel_idx // 2, panel_idx % 2], projection='3d')

        if not top_f.exists() or not conf_f.exists():
            ax.text(0.5, 0.5, 0.5, "Data not found", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(label, fontsize=10, fontweight='bold')
            continue

        beads, mol_of_bead, ico_of_mol = parse_topology(str(top_f))
        N = len(beads)
        box, positions, a1_vecs, a3_vecs = parse_conf(str(conf_f), N)

        n_mols = len(ico_of_mol)
        bonds = find_bonds(beads, positions, a1_vecs, a3_vecs, box, mol_of_bead, ico_of_mol)
        valences = defaultdict(int)
        for m1, m2 in bonds:
            valences[m1] += 1
            valences[m2] += 1

        clusters = find_clusters(bonds, n_mols)
        seed_mols = set(max(clusters, key=len)) if clusters else set()

        mol_ids = list(range(n_mols))
        mol_colors = get_crystal_colors(mol_ids, valences, seed_mols)
        ico_positions = np.array([positions[ico_of_mol[m]] for m in mol_ids]) - box / 2
        ico_radii = np.array([beads[ico_of_mol[m]].radius for m in mol_ids])

        color_groups = {
            "seed": (COLORS["seed"], "Seed", "^", 1.0),
            "bonded4p": (COLORS["bonded4p"], "Crystal-like", "o", 0.9),
            "bonded2_3": (COLORS["bonded2_3"], "Assembling", "o", 0.8),
            "bonded1": (COLORS["bonded1"], "Weakly bonded", "o", 0.6),
            "free": (COLORS["free"], "Free gas", "o", 0.12),
        }
        val_labels = {COLORS["seed"]: "seed", COLORS["bonded4p"]: "bonded4p",
                      COLORS["bonded2_3"]: "bonded2_3", COLORS["bonded1"]: "bonded1",
                      COLORS["free"]: "free"}

        for group_key, (color, lbl, marker, alpha) in color_groups.items():
            mask = np.array([val_labels.get(c, "free") == group_key for c in mol_colors])
            if not mask.any():
                continue
            pts = ico_positions[mask]
            r = ico_radii[mask]
            size = (r * 150).clip(15, 300)
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
                       c=color, s=size, marker=marker, alpha=alpha,
                       edgecolors='none', depthshade=True)

        for m1, m2 in bonds[:300]:
            p1 = positions[ico_of_mol[m1]] - box / 2
            p2 = positions[ico_of_mol[m2]] - box / 2
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    c='#555555', lw=0.4, alpha=0.25)

        ax.view_init(elev=25, azim=45)
        ax.set_box_aspect([1, 1, 1])
        half = box[0] / 2
        ax.set_xlim([-half, half]); ax.set_ylim([-half, half]); ax.set_zlim([-half, half])

        n_bonded = sum(1 for m in mol_ids if valences.get(m, 0) >= 1)
        n_crystal = sum(1 for m in mol_ids if valences.get(m, 0) >= 4)
        stats = f"bonds={len(bonds)}  bonded={n_bonded}/{n_mols}  crystal={n_crystal}"
        ax.text2D(0.02, 0.02, stats, transform=ax.transAxes, fontsize=7,
                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        ax.set_title(label, fontsize=10, fontweight='bold')
        ax.set_xlabel("x", fontsize=8); ax.set_ylabel("y", fontsize=8)

    # Colorbar legend as text box
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["seed"],     label="Seed cluster"),
        Patch(facecolor=COLORS["bonded4p"], label="Crystal-like (≥4 bonds)"),
        Patch(facecolor=COLORS["bonded2_3"],label="Assembling (2–3 bonds)"),
        Patch(facecolor=COLORS["bonded1"],  label="Weakly bonded (1 bond)"),
        Patch(facecolor=COLORS["free"],     label="Free gas"),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=5,
               fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

    fig.savefig(output, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved 4-panel: {output}")


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Render PHB patchy-particle configurations with crystal coloring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="command")

    # Single render
    p_single = sub.add_parser("render", help="Render a single configuration")
    p_single.add_argument("--top", required=True, help="PHB topology file")
    p_single.add_argument("--conf", required=True, help="Configuration/trajectory file")
    p_single.add_argument("-o", "--output", default="phb_render.png", help="Output PNG path")
    p_single.add_argument("--title", default="", help="Figure title")
    p_single.add_argument("--elev", type=float, default=25, help="Elevation angle")
    p_single.add_argument("--azim", type=float, default=45, help="Azimuth angle")
    p_single.add_argument("--cutoff", type=float, default=0.25, help="Bond detection cutoff")
    p_single.add_argument("--dpi", type=int, default=200, help="Output DPI")

    # Sweep batch render
    p_sweep = sub.add_parser("sweep", help="Render top systems from a sweep directory")
    p_sweep.add_argument("--sweep", required=True, help="Path to seeded_sweep directory")
    p_sweep.add_argument("--outdir", default="phb_renders", help="Output directory")
    p_sweep.add_argument("--dpi", type=int, default=180, help="Output DPI")

    # 4-panel render
    p_panel = sub.add_parser("panel", help="Render 4 key systems in a 2×2 panel")
    p_panel.add_argument("--sweep", required=True, help="Path to seeded_sweep directory")
    p_panel.add_argument("-o", "--output", default="phb_4panel.png", help="Output PNG path")

    args = parser.parse_args()

    if args.command == "render":
        render_configuration(args.top, args.conf, args.output,
                             title=args.title, elev=args.elev, azim=args.azim,
                             cutoff=args.cutoff, dpi=args.dpi)

    elif args.command == "sweep":
        render_sweep(args.sweep, args.outdir, dpi=args.dpi)

    elif args.command == "panel":
        render_4panel(args.sweep, args.output)

    else:
        # Default: render the 4 key systems if a sweep dir is available
        sweep_default = Path(__file__).parent.parent / "dna/large_crystal/hand5/seeded_sweep"
        if sweep_default.exists():
            print(f"Auto-detecting sweep directory: {sweep_default}")
            render_4panel(str(sweep_default), "phb_4panel.png")
        else:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
