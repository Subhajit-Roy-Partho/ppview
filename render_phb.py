#!/usr/bin/env python3
"""
render_phb.py - headless high-resolution renderer for PHB crystal configurations.

Renders a PHB topology (.phb) plus an oxDNA configuration (.dat) to a PNG with a
small numpy z-buffer sphere rasteriser (no GPU, no display, no browser). It
mirrors how the ppview web viewer draws PHB systems:

  * icosahedral cores (type -3, radius 1) and helix-arm beads (type -4, radius
    0.1, drawn at a minimum relative radius so they stay visible);
  * patches are coloured by their interaction colour id. Two patches interact
    when colour_p + colour_q == 0, so a complementary pair (c, -c) gets exactly
    the same colour. Hue is keyed on |c| mod 500 (21 / 521 share a hue family),
    tone tells them apart (|c| >= 500 is the darker, more saturated variant).
    Patch cap size scales with patch strength.
  * or, with --cluster-file, every particle is coloured by its cluster label.

Dependencies: numpy and Pillow (matplotlib is only used, if present, to find a
nice font). Typical run on a 500-molecule (8000 particle) system at 3840x2160
takes well under a minute.

Examples
--------
  # patch colouring, 4K, isometric view
  python render_phb.py --top topology.phb --conf final_conf.dat --out img.png \\
      --width 3840 --height 2160

  # cluster colouring with legend, cores only, white background
  python render_phb.py --top topology.phb --conf final_conf.dat --out img.png \\
      --cluster-file final_conf.labels.txt --legend --cores-only --highlight-largest

  # a mid-height slab looking down z, with the periodic box drawn
  python render_phb.py --top t.phb --conf c.dat --out slab.png --view z \\
      --slab z 0.4 0.6 --box

Cluster file: one integer per particle (topology order). -1 = unassigned,
0 = largest cluster, 1 = second largest, ... Clusters with fewer than
--min-cluster-mols molecules (default 2) are drawn as unassigned (muted grey).

See also render_batch.py (renders every entry of a manifest.json).
"""

import argparse
import colorsys
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Constants shared with the web viewer (src/formats/parsers/phb.js)
# --------------------------------------------------------------------------- #

CORE_COLOR = "#c8ccd6"
ARM_COLOR = "#5f6f86"
# one body colour per core species (the core bead type), in order of bead-type id
SPECIES_PALETTE = ["#3b78c2", "#e8912d", "#3fa66a", "#8e5db8", "#d24d4d", "#2fb0b0", "#a07f4d", "#d96ea6"]


def species_colors(ptype, btype):
    """-> ([species bead types, sorted], {btype: hex}) of the core beads."""
    types = sorted(set(int(b) for b in btype[ptype == -3]))
    return types, {t: SPECIES_PALETTE[i % len(SPECIES_PALETTE)] for i, t in enumerate(types)}
MIN_RELATIVE_RADIUS = 0.25      # PHB_MIN_RELATIVE_RADIUS in phb.js
UNASSIGNED_COLOR = "#8a8f98"

# Qualitative palette for clusters (Okabe-Ito / Tableau-like, distinguishable on
# both white and dark backgrounds). Beyond this, hues come from the golden angle.
CLUSTER_PALETTE = [
    "#e4572e", "#2e86de", "#2fb344", "#f2a900", "#8e44ad", "#17bebb",
    "#d6336c", "#7f8c2a", "#0b5ea8", "#c0762d", "#5f3dc4", "#12a07a",
    "#e0457b", "#4c6ef5", "#99a31f", "#a23e48",
]


def hex_to_rgb(h: str) -> Tuple[float, float, float]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore


def rgb_to_hex(c) -> str:
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(1, v)) * 255)) for v in c)


NAMED_BG = {"white": "#ffffff", "black": "#000000", "dark": "#0f1218",
            "grey": "#808080", "gray": "#808080"}


def hsl_hex(h_deg: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360) / 360.0, l, s)
    return rgb_to_hex((r, g, b))


# --------------------------------------------------------------------------- #
# Patch colour mapping (same rule as phbPatchPalette in phb.js)
# --------------------------------------------------------------------------- #

def phb_patch_palette(colors) -> Tuple[Dict[int, str], List[Tuple[int, str]]]:
    """Return ({raw colour -> hex}, legend [(|c|, hex)]). c and -c map identically."""
    colors = [int(c) for c in colors]
    keys = sorted({abs(c) % 500 for c in colors})
    n = max(len(keys), 1)
    stride = max(1, round(n * 0.381966))
    while math.gcd(stride, n) != 1:
        stride += 1
    hue_of = {k: ((r * stride) % n) / n * 360.0 for r, k in enumerate(keys)}

    def color_of(c: int) -> str:
        a = abs(c)
        h = hue_of.get(a % 500, 0.0)
        return hsl_hex(h, 0.85, 0.42) if a >= 500 else hsl_hex(h, 0.80, 0.62)

    cmap = {c: color_of(c) for c in set(colors)}
    legend = [(a, color_of(a)) for a in sorted({abs(c) for c in colors})]
    return cmap, legend


# --------------------------------------------------------------------------- #
# Input parsing
# --------------------------------------------------------------------------- #

@dataclass
class Topology:
    n: int
    ptype: np.ndarray            # (N,) -3 core, -4 arm bead
    strand: np.ndarray           # (N,) strand id (one per arm, one per core)
    btype: np.ndarray            # (N,)
    radius: np.ndarray           # (N,)
    # btype -> (dirs (P,3) unit vectors in body frame, colors (P,), strengths (P,))
    patches: Dict[int, Tuple[np.ndarray, np.ndarray, np.ndarray]] = field(default_factory=dict)
    all_colors: List[int] = field(default_factory=list)


def parse_topology(path: str) -> Topology:
    patch_defs: Dict[int, Tuple[int, float, np.ndarray]] = {}
    color_defs: Dict[int, List[int]] = {}
    ptype, strand, btype, radius = [], [], [], []
    header = False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tok = line.split()
            if not header:
                header = True
                continue
            if tok[0] == "iP":
                v = np.array([float(tok[4]), float(tok[5]), float(tok[6])])
                nv = np.linalg.norm(v)
                patch_defs[int(tok[1])] = (int(tok[2]), float(tok[3]),
                                           v / nv if nv > 1e-9 else np.zeros(3))
            elif tok[0] == "iC":
                color_defs[int(tok[1])] = [int(t) for t in tok[2:]]
            elif tok[0][0] == "i":
                continue
            elif len(tok) >= 4:
                ptype.append(int(tok[0]))
                strand.append(int(tok[1]))
                btype.append(int(tok[2]))
                radius.append(float(tok[3]))
    patches = {}
    for bt, ids in color_defs.items():
        ids = [i for i in ids if i in patch_defs]
        if not ids:
            continue
        dirs = np.array([patch_defs[i][2] for i in ids])
        cols = np.array([patch_defs[i][0] for i in ids])
        st = np.array([patch_defs[i][1] for i in ids])
        patches[bt] = (dirs, cols, st)
    return Topology(len(ptype), np.array(ptype), np.array(strand), np.array(btype), np.array(radius),
                    patches, [p[0] for p in patch_defs.values()])


def parse_conf(path: str, n: int, frame: int = -1):
    """Read frame `frame` (default last) of an oxDNA configuration/trajectory."""
    with open(path) as f:
        lines = f.read().split("\n")
    starts = [i for i, l in enumerate(lines) if l.startswith("t ") or l.startswith("t=")]
    if not starts:
        raise SystemExit(f"{path}: no 't =' header found; not an oxDNA configuration")
    s = starts[frame]
    box = np.array([float(x) for x in lines[s + 1].split()[2:5]])
    rows = lines[s + 3:s + 3 + n]
    if len(rows) < n or not rows[-1].strip():
        raise SystemExit(f"{path}: expected {n} particles, found fewer in the chosen frame")
    arr = np.array([r.split()[:9] for r in rows], dtype=np.float64)
    return box, arr[:, 0:3], arr[:, 3:6], arr[:, 6:9]


def load_labels(path: str, n: int, n_cores: int) -> np.ndarray:
    vals = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                vals.append(int(float(line.split()[0])))
    lab = np.array(vals, dtype=np.int64)
    if len(lab) != n:
        raise SystemExit(f"{path}: {len(lab)} labels but the topology has {n} particles")
    return lab


# --------------------------------------------------------------------------- #
# Scene preparation
# --------------------------------------------------------------------------- #

def unit_ids(strand: np.ndarray) -> np.ndarray:
    """Rigid unit per particle: a strand (an arm's bead chain, or a lone core)."""
    _, inv = np.unique(strand, return_inverse=True)
    return inv


def min_image(d, box):
    return d - box * np.round(d / box)


def wrap_positions(pos, strand, box, mode):
    """Centre the box on the origin and wrap.

    mode 'strand' (default) wraps every strand as a rigid unit, so an arm's bead
    chain is never cut by the periodic boundary. In the PHB model arms and cores
    are separate strands (arms bind cores through patches), so they wrap
    independently. 'particle' wraps each bead; 'none' leaves coordinates alone.
    Returns (centred positions, unit id per particle).
    """
    unit = unit_ids(strand)
    if mode == "none":
        return pos - box / 2.0, unit
    if mode == "strand":
        _, first = np.unique(unit, return_index=True)
        ref = pos[first][unit]
        out = np.mod(ref, box) + min_image(pos - ref, box)
        return out - box / 2.0, unit
    return np.mod(pos, box) - box / 2.0, unit


@dataclass
class Camera:
    right: np.ndarray
    up: np.ndarray
    back: np.ndarray            # points from the scene towards the viewer


def make_camera(view: str, azim: Optional[float], elev: Optional[float]) -> Camera:
    if azim is not None or elev is not None or view == "iso":
        az = math.radians(35.0 if azim is None else azim)
        el = math.radians(25.0 if elev is None else elev)
        back = np.array([math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)])
        up_hint = np.array([0.0, 0.0, 1.0])
    elif view == "x":
        back, up_hint = np.array([1.0, 0, 0]), np.array([0.0, 0, 1])
    elif view == "y":
        back, up_hint = np.array([0.0, -1, 0]), np.array([0.0, 0, 1])
    elif view == "z":
        back, up_hint = np.array([0.0, 0, 1]), np.array([0.0, 1, 0])
    else:
        raise SystemExit(f"unknown --view {view}")
    back = back / np.linalg.norm(back)
    right = np.cross(up_hint, back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    return Camera(right, up, back)


# --------------------------------------------------------------------------- #
# Cluster colouring
# --------------------------------------------------------------------------- #

def cluster_color(rank: int) -> str:
    if rank < len(CLUSTER_PALETTE):
        return CLUSTER_PALETTE[rank]
    h = (rank * 137.508) % 360
    return hsl_hex(h, 0.65, 0.5 if rank % 2 else 0.6)


def build_cluster_colors(labels, ptype, min_mols, highlight_largest):
    """-> per-particle RGB (N,3), legend entries [(label, mols, hex)], unassigned mask."""
    n = len(labels)
    is_core = ptype == -3
    have_cores = is_core.any()
    unit = is_core if have_cores else np.ones(n, bool)
    ids = np.unique(labels[labels >= 0])
    sizes = {int(c): int(unit[labels == c].sum()) for c in ids}
    real = [c for c in sizes if sizes[c] >= min_mols]
    # Rank by size (label 0 is meant to be the largest, but do not rely on it).
    real.sort(key=lambda c: (-sizes[c], c))
    colors = np.tile(hex_to_rgb(UNASSIGNED_COLOR), (n, 1))
    legend = []
    for rank, c in enumerate(real):
        hx = cluster_color(rank)
        base = np.array(hex_to_rgb(hx))
        if highlight_largest and rank > 0:
            grey = np.array(hex_to_rgb(UNASSIGNED_COLOR))
            base = 0.45 * base + 0.55 * grey
        colors[labels == c] = base
        legend.append((int(c), sizes[c], rgb_to_hex(base)))
    unassigned = ~np.isin(labels, real)
    n_un = int(unit[unassigned].sum())
    return colors, legend, unassigned, n_un


# --------------------------------------------------------------------------- #
# Rasteriser
# --------------------------------------------------------------------------- #

def box_blur(a: np.ndarray, k: int) -> np.ndarray:
    """Separable moving average with window 2k+1 (edge-clamped), float32 in/out."""
    if k < 1:
        return a
    out = a.astype(np.float64)
    for axis in (0, 1):
        pad = [(0, 0)] * 2
        pad[axis] = (k + 1, k)
        c = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * k + 1, 2 * k + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * k + 1)
    return out.astype(np.float32)


def render_scene(args, pos, a1, a3, ptype, btype, radius, body_rgb, topo, patch_cmap,
                 box, fade_mask, log):
    W, H, S = args.width, args.height, args.scale
    Wi, Hi = W * S, H * S
    cam = make_camera(args.view, args.azim, args.elev)

    n = len(pos)
    # displayed radii
    rmax = radius.max() if n else 1.0
    disp_r = np.maximum(radius, args.min_radius_frac * rmax)

    # ---- fit camera ----
    sel = np.arange(n) if args._fit_mask is None else np.nonzero(args._fit_mask)[0]
    if len(sel) == 0:
        sel = np.arange(n)
    center = (pos[sel].min(0) + pos[sel].max(0)) / 2.0
    if args.center is not None:
        center = np.array(args.center, float)
    rel = pos - center
    xc = rel @ cam.right
    yc = rel @ cam.up
    zc = rel @ cam.back          # larger = closer to the viewer
    persp = args.perspective

    extent_pts = [np.stack([xc[sel], yc[sel], zc[sel]], 1)]
    radii_sel = disp_r[sel]
    box_corners = None
    if args.box:
        sgn = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) * (box / 2.0)
        bc = sgn - center
        box_corners = np.stack([bc @ cam.right, bc @ cam.up, bc @ cam.back], 1)
        if args.fit == "box" or (args.fit == "auto" and not args._fit_subset):
            extent_pts.append(box_corners)

    P = np.concatenate(extent_pts, 0)
    R_all = np.concatenate([radii_sel, np.zeros(len(P) - len(radii_sel))])
    scene_r = np.max(np.linalg.norm(P, axis=1) + R_all)
    if persp:
        fov = math.radians(args.fov)
        dist = scene_r / math.sin(fov / 2.0) * 1.0
    else:
        dist = scene_r * 4.0 + 10.0

    def depth_of(z):            # distance from the eye along the view direction
        return dist - z

    if persp:
        dz = depth_of(P[:, 2])
        px = P[:, 0] / dz
        py = P[:, 1] / dz
        rr = R_all / dz
    else:
        px, py, rr = P[:, 0], P[:, 1], R_all
    x_lo, x_hi = (px - rr).min(), (px + rr).max()
    y_lo, y_hi = (py - rr).min(), (py + rr).max()
    margin = 1.0 + args.margin
    fx = Wi / ((x_hi - x_lo) * margin)
    fy = Hi / ((y_hi - y_lo) * margin)
    f = min(fx, fy) * args.zoom
    mx = (x_hi + x_lo) / 2.0
    my = (y_hi + y_lo) / 2.0
    ox = Wi / 2.0 - f * mx
    oy = Hi / 2.0 + f * my

    def project(x, y, z):
        d = depth_of(z)
        if persp:
            return ox + f * x / d, oy - f * y / d, d
        return ox + f * x, oy - f * y, d

    sx, sy, sd = project(xc, yc, zc)
    sr = disp_r * (f / sd if persp else f)

    # ---- visibility ----
    vis = np.ones(n, bool)
    if fade_mask is not None and args.hide_unassigned:
        vis &= ~fade_mask
    if args.visible is not None:
        vis &= args.visible
    vis &= (sx + sr > 0) & (sx - sr < Wi) & (sy + sr > 0) & (sy - sr < Hi)
    order = np.nonzero(vis)[0]
    order = order[np.argsort(sd[order])]          # front to back
    log(f"  drawing {len(order)} of {n} particles at {Wi}x{Hi}")

    zref = order if getattr(args, "_zref", None) is None else np.nonzero(args._zref)[0]
    zmin_d = sd[zref].min() if len(zref) else 0.0
    zmax_d = sd[zref].max() if len(zref) else 1.0
    zspan = max(zmax_d - zmin_d, 1e-6)

    bg = np.array(hex_to_rgb(args._bg_hex))
    zbuf = np.full((Hi, Wi), np.inf, dtype=np.float32)
    ibuf = np.full((Hi, Wi), -1, dtype=np.int32)
    cbuf = np.empty((Hi, Wi, 3), dtype=np.uint8)
    cbuf[:] = np.round(bg * 255).astype(np.uint8)

    # lighting in camera space (x right, y up, z toward viewer)
    L1 = np.array([-0.45, 0.65, 0.62]); L1 /= np.linalg.norm(L1)
    L2 = np.array([0.75, -0.25, 0.45]); L2 /= np.linalg.norm(L2)
    Hh = L1 + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    amb, k1, k2, spec = args.ambient, 0.62, 0.22, 0.28

    # patch world directions per particle (only built lazily per particle)
    want_patches = args.patches
    smax = max([p[2].max() for p in topo.patches.values()] + [1e-9]) if topo.patches else 1.0
    cap0 = math.radians(args.patch_size)
    fade = args.fade_unassigned

    # camera axes as a matrix: world = nx*right + ny*up + nz*back
    CAM = np.stack([cam.right, cam.up, cam.back], 0)      # (3,3) rows

    t0 = time.time()
    for ii, i in enumerate(order):
        r = sr[i]
        r_eff = max(r, 0.6)
        cx, cy = sx[i], sy[i]
        x0 = max(int(math.floor(cx - r_eff)), 0)
        x1 = min(int(math.ceil(cx + r_eff)) + 1, Wi)
        y0 = max(int(math.floor(cy - r_eff)), 0)
        y1 = min(int(math.ceil(cy + r_eff)) + 1, Hi)
        if x1 <= x0 or y1 <= y0:
            continue
        dxs = (np.arange(x0, x1) + 0.5 - cx) / r_eff
        dys = (np.arange(y0, y1) + 0.5 - cy) / r_eff
        rho2 = dys[:, None] ** 2 + dxs[None, :] ** 2
        inside = rho2 <= 1.0
        nzs = np.sqrt(np.maximum(1.0 - rho2, 0.0))
        rw = disp_r[i]
        depth = sd[i] - rw * nzs      # nearer = smaller
        zwin = zbuf[y0:y1, x0:x1]
        ok = inside & (depth < zwin)
        if not ok.any():
            continue
        yy, xx = np.nonzero(ok)
        nxv = dxs[xx]
        nyv = -dys[yy]
        nzv = nzs[yy, xx]
        N = np.stack([nxv, nyv, nzv], 1)                         # camera-space normals
        diff = np.clip(N @ L1, 0, None) * k1 + np.clip(N @ L2, 0, None) * k2
        sp = np.clip(N @ Hh, 0, None) ** 36 * spec
        base = body_rgb[i]
        col = np.tile(base, (len(yy), 1))

        if want_patches and not fade_mask_is(fade_mask, i):
            bt = int(btype[i])
            tab = topo.patches.get(bt)
            if tab is not None:
                dirs_b, cols_raw, strength = tab
                Rm = np.stack([a1[i], np.cross(a3[i], a1[i]), a3[i]], 1)   # columns a1,a2,a3
                dirs_w = dirs_b @ Rm.T                                    # (P,3) world
                Nw = N @ CAM                                              # (n,3) world normals
                dots = Nw @ dirs_w.T                                      # (n,P)
                j = np.argmax(dots, 1)
                dbest = np.clip(dots[np.arange(len(yy)), j], -1, 1)
                ang = np.arccos(dbest)
                cap = cap0 * (0.7 + 0.3 * np.sqrt(np.clip(np.abs(strength[j]) / smax, 0, 1)))
                inside_cap = ang < cap
                if inside_cap.any():
                    pc = np.array([hex_to_rgb(patch_cmap[int(c)]) for c in cols_raw])
                    col = np.where(inside_cap[:, None], pc[j], col)
                    ring = inside_cap & (ang > cap * 0.82)
                    col[ring] *= 0.55
        lit = col * (amb + diff)[:, None] + sp[:, None]
        # depth cue toward the background
        if args.depth_cue > 0:
            t = np.clip((depth[yy, xx] - zmin_d) / zspan, 0, 1) * args.depth_cue
            lit = lit * (1 - t[:, None]) + bg * t[:, None]
        if fade_mask is not None and fade_mask[i] and fade < 1.0:
            lit = lit * fade + bg * (1 - fade)
        zwin[yy, xx] = depth[yy, xx]
        ibuf[y0:y1, x0:x1][yy, xx] = (i if args._gid is None else args._gid[i])
        cbuf[y0:y1, x0:x1][yy, xx] = np.clip(lit * 255.0 + 0.5, 0, 255).astype(np.uint8)
        if (ii + 1) % 4000 == 0:
            log(f"    {ii + 1}/{len(order)} ({time.time() - t0:.1f}s)")
    log(f"  rasterised in {time.time() - t0:.1f}s")

    obj = ibuf >= 0
    # ---- ambient occlusion from depth (computed at output resolution) ----
    if args.ao > 0 and obj.any():
        zfill = np.where(obj, zbuf, zmax_d + 1.0).astype(np.float32)
        zs = zfill.reshape(H, S, W, S).mean((1, 3)) if S > 1 else zfill
        core_px = float(np.median(sr[order][ptype[order] == -3])) if (ptype[order] == -3).any() \
            else float(np.median(sr[order]))
        k = int(max(2, min(60, 1.1 * core_px / S)))
        zb = box_blur(zs, k)
        zscale = float(np.median(disp_r[order])) * (1.0 if not (ptype[order] == -3).any() else 0.9)
        occ = np.clip((zs - zb) / max(zscale, 1e-6), 0, 1)
        occ = np.repeat(np.repeat(occ, S, 0), S, 1) if S > 1 else occ
        shade = (1.0 - args.ao * occ)[..., None]
        cbuf = np.where(obj[..., None], (cbuf * shade).astype(np.uint8), cbuf)

    # ---- silhouette outlines ----
    if args.outline > 0 and obj.any():
        edge = np.zeros((Hi, Wi), bool)
        eps = 0.06 * float(np.median(disp_r[order]))
        zinf = np.where(obj, zbuf, np.inf)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            idn = np.roll(ibuf, (dy, dx), (0, 1))
            zn = np.roll(zinf, (dy, dx), (0, 1))
            diffid = (idn != ibuf) & obj
            edge |= diffid & (np.isinf(zn) | (zn < zbuf - eps))
        t = max(1, int(round(args.outline * S * 0.5)))
        thick = edge.copy()
        for _ in range(t - 1):
            thick = thick | np.roll(thick, 1, 0) | np.roll(thick, 1, 1)
        thick &= obj
        dark = np.array(hex_to_rgb(args._edge_hex))
        cbuf[thick] = np.clip((cbuf[thick] * 0.25 + dark * 255 * 0.75), 0, 255).astype(np.uint8)

    # ---- periodic box, depth tested ----
    if args.box and box_corners is not None:
        bsx, bsy, bsd = project(box_corners[:, 0], box_corners[:, 1], box_corners[:, 2])
        corner_idx = [(sxi, syi, szi) for sxi in (0, 1) for syi in (0, 1) for szi in (0, 1)]
        cid = {c: k for k, c in enumerate(corner_idx)}
        edges = []
        for c in corner_idx:
            for ax in range(3):
                if c[ax] == 0:
                    d = list(c); d[ax] = 1
                    edges.append((cid[c], cid[tuple(d)]))
        line_rgb = np.array(hex_to_rgb(args._box_hex)) * 255
        th = max(1, int(round(S * args.box_width)))
        for a, b in edges:
            length = int(math.hypot(bsx[b] - bsx[a], bsy[b] - bsy[a])) + 2
            ts = np.linspace(0, 1, max(length, 2))
            ex = bsx[a] + (bsx[b] - bsx[a]) * ts
            ey = bsy[a] + (bsy[b] - bsy[a]) * ts
            ez = bsd[a] + (bsd[b] - bsd[a]) * ts
            for oy_ in range(-(th // 2), th - th // 2):
                for ox_ in range(-(th // 2), th - th // 2):
                    xi = np.round(ex).astype(int) + ox_
                    yi = np.round(ey).astype(int) + oy_
                    okp = (xi >= 0) & (xi < Wi) & (yi >= 0) & (yi < Hi)
                    xi, yi, zi = xi[okp], yi[okp], ez[okp]
                    front = zi < zbuf[yi, xi] + 1e-3
                    cbuf[yi[front], xi[front]] = line_rgb.astype(np.uint8)

    # ---- downsample ----
    if S > 1:
        img = np.zeros((H, W, 3), np.float32)
        for k in range(0, H, 256):                              # chunked: bounded memory
            blk = cbuf[k * S:(k + 256) * S].astype(np.float32)
            h = blk.shape[0] // S
            img[k:k + h] = blk.reshape(h, S, W, S, 3).mean((1, 3))
        cover = (ibuf >= 0).reshape(H, S, W, S).mean((1, 3)) if S > 1 else (ibuf >= 0).astype(np.float32)
    else:
        img = cbuf.astype(np.float32)
        cover = (ibuf >= 0).astype(np.float32)
    zimg = np.where(obj, zbuf, np.inf).astype(np.float32)
    zmin = zimg.reshape(H, S, W, S).min((1, 3)) if S > 1 else zimg
    return (np.clip(img + 0.5, 0, 255).astype(np.uint8), cover,
            dict(f=f / S, sd=sd, sx=sx / S, sy=sy / S, zmin=zmin))


def fade_mask_is(fade_mask, i):
    return fade_mask is not None and bool(fade_mask[i])


# --------------------------------------------------------------------------- #
# Annotations
# --------------------------------------------------------------------------- #

def find_font(size: int):
    cands = []
    try:
        import matplotlib
        cands.append(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf"))
        cands.append(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans-Bold.ttf"))
    except Exception:
        pass
    cands += ["/usr/share/fonts/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_legend(img: Image.Image, entries, title, fg, bg_rgb, corner="tr", footer=None, columns=1):
    """entries: [(hex, text)]. Draws a swatch list in a corner."""
    W, H = img.size
    unit = H / 1080.0
    fs = max(12, int(22 * unit))
    font = find_font(fs)
    tfont = find_font(int(fs * 1.12))
    d = ImageDraw.Draw(img, "RGBA")
    pad = int(14 * unit)
    sw = int(fs * 1.0)
    row_h = int(fs * 1.45)
    nrows = math.ceil(len(entries) / columns)
    tw = max([d.textlength(t, font=font) for _, t in entries] + [d.textlength(title, font=tfont)] + [1])
    col_w = sw + int(10 * unit) + int(tw) + int(18 * unit)
    if columns > 1:
        tw_cols = max(d.textlength(t, font=font) for _, t in entries)
        col_w = sw + int(10 * unit) + int(tw_cols) + int(18 * unit)
    box_w = max(col_w * columns, int(d.textlength(title, font=tfont)) + 2 * pad) + 2 * pad
    foot_h = row_h if footer else 0
    box_h = pad + int(fs * 1.7) + nrows * row_h + foot_h + pad
    m = int(24 * unit)
    x0 = W - box_w - m if "r" in corner else m
    y0 = m if "t" in corner else H - box_h - m
    panel = (*bg_rgb, 190)
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=int(10 * unit), fill=panel,
                        outline=(*fg, 70), width=max(1, int(unit)))
    d.text((x0 + pad, y0 + pad), title, font=tfont, fill=(*fg, 255))
    y = y0 + pad + int(fs * 1.7)
    for k, (hx, text) in enumerate(entries):
        c, r = divmod(k, nrows)
        xx = x0 + pad + c * col_w
        yy = y + r * row_h
        rgb = tuple(int(v * 255) for v in hex_to_rgb(hx))
        d.rounded_rectangle([xx, yy + 2, xx + sw, yy + 2 + sw], radius=int(3 * unit),
                            fill=(*rgb, 255), outline=(*fg, 90))
        d.text((xx + sw + int(10 * unit), yy), text, font=font, fill=(*fg, 255))
    if footer:
        d.text((x0 + pad, y + nrows * row_h + int(4 * unit)), footer, font=font, fill=(*fg, 200))


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render_phb.py",
        description="Headless high-resolution renderer for PHB topology (.phb) + oxDNA configuration (.dat).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples"+__doc__.split("Examples",1)[1])
    g = p.add_argument_group("input / output")
    g.add_argument("--top", required=True, help="PHB topology (.phb)")
    g.add_argument("--conf", required=True, help="oxDNA configuration or trajectory (.dat)")
    g.add_argument("--out", "-o", default="phb_render.png", help="output PNG (default phb_render.png)")
    g.add_argument("--frame", type=int, default=-1, help="frame of a trajectory file (default -1 = last)")
    g.add_argument("--width", type=int, default=3840)
    g.add_argument("--height", type=int, default=2160)
    g.add_argument("--scale", type=int, default=2,
                   help="supersampling factor (render at scale x size, then average; default 2)")
    g.add_argument("--background", default="white",
                   help="white | black | dark | #rrggbb | transparent (default white)")
    g.add_argument("--title", default=None, help="text drawn in the top-left corner")

    c = p.add_argument_group("camera")
    c.add_argument("--view", choices=["iso", "x", "y", "z"], default="iso")
    c.add_argument("--azim", type=float, default=None, help="custom azimuth in degrees (overrides --view)")
    c.add_argument("--elev", type=float, default=None, help="custom elevation in degrees (overrides --view)")
    c.add_argument("--zoom", type=float, default=1.0, help="zoom factor about the view centre (default 1)")
    c.add_argument("--perspective", action="store_true", help="perspective projection (default orthographic)")
    c.add_argument("--fov", type=float, default=30.0, help="perspective field of view in degrees")
    c.add_argument("--margin", type=float, default=0.04, help="blank border around the structure (fraction)")
    c.add_argument("--center", type=float, nargs=3, metavar=("X", "Y", "Z"), default=None,
                   help="look-at point in box-centred coordinates (default: middle of the structure)")
    c.add_argument("--fit", choices=["auto", "all", "box"], default="auto",
                   help="what the framing includes: particles only (all), particles and box (box), or "
                        "auto = the box if --box is drawn and the view is not a --slab/--fit-cluster subset")
    c.add_argument("--fit-cluster", type=int, default=None, metavar="LABEL",
                   help="frame only the particles of this cluster label (needs --cluster-file)")

    s = p.add_argument_group("what to draw")
    s.add_argument("--no-arms", "--cores-only", dest="no_arms", action="store_true",
                   help="hide helix-arm beads (type -4); readable 500-molecule overviews")
    s.add_argument("--slab", nargs=3, metavar=("AXIS", "LO", "HI"), default=None,
                   help="keep only strands with LO <= pos/box+0.5 <= HI along AXIS (x|y|z, box fractions 0..1)")
    s.add_argument("--box", action="store_true", help="draw the periodic box wireframe")
    s.add_argument("--box-width", type=float, default=1.6, help="box line width in output pixels")
    s.add_argument("--wrap", choices=["strand", "particle", "none"], default="strand",
                   help="periodic wrapping: whole strands (default; arm chains are never cut), per particle, or raw")
    s.add_argument("--min-radius-frac", type=float, default=MIN_RELATIVE_RADIUS,
                   help="smallest drawn radius as a fraction of the largest (keeps 0.1 beads visible; default 0.25)")
    s.add_argument("--model", choices=["ball", "ballstick"], default="ball",
                   help="ball (default, ppview model): cores and arm beads as spheres; "
                        "ballstick: cores as balls, each helix arm drawn as small joint balls joined by sticks")
    s.add_argument("--stick-radius", type=float, default=0.06, help="ballstick: stick radius (default 0.06)")
    s.add_argument("--joint-radius", type=float, default=0.13, help="ballstick: arm-bead (joint) radius (default 0.13)")
    s.add_argument("--species-colors", action="store_true",
                   help="colour each core body by its species (core bead type); patches keep their interaction colours")
    s.add_argument("--no-patches", dest="patches", action="store_false", default=None,
                   help="do not draw patches (default: drawn unless --cluster-file is given)")
    s.add_argument("--patches", dest="patches", action="store_true", default=None,
                   help="force patches on even when colouring by cluster")
    s.add_argument("--patch-size", type=float, default=24.0, help="patch cap half-angle in degrees (default 24)")

    k = p.add_argument_group("cluster colouring")
    k.add_argument("--cluster-file", default=None,
                   help="per-particle integer labels, one per line: -1 unassigned, 0 largest cluster, 1 second, ...")
    k.add_argument("--min-cluster-mols", type=int, default=2,
                   help="clusters with fewer molecules are drawn as unassigned (default 2)")
    k.add_argument("--highlight-largest", action="store_true",
                   help="largest cluster in a saturated colour, the others muted")
    k.add_argument("--fade-unassigned", type=float, default=1.0, metavar="A",
                   help="opacity-like fade of unassigned particles towards the background (0..1, default 1 = opaque)")
    k.add_argument("--hide-unassigned", action="store_true", help="do not draw unassigned particles at all")
    k.add_argument("--legend", action="store_true",
                   help="add a legend (cluster sizes with --cluster-file, patch colour pairs otherwise)")
    k.add_argument("--legend-top", type=int, default=8, help="clusters listed in the legend (default 8)")
    k.add_argument("--legend-corner", choices=["tr", "tl", "br", "bl"], default="tr")

    q = p.add_argument_group("shading")
    q.add_argument("--ambient", type=float, default=0.36)
    q.add_argument("--ao", type=float, default=0.4, help="depth-based ambient occlusion strength (0 = off)")
    q.add_argument("--outline", type=float, default=1.0, help="silhouette outline width in output pixels (0 = off)")
    q.add_argument("--depth-cue", type=float, default=0.18, help="fade towards the background with depth (0..1)")
    q.add_argument("--quiet", "-q", action="store_true")
    return p


def add_sticks(args, topo, pos, a1, a3, body_rgb, fade_mask):
    """Ball-and-stick model: arm beads become small joint balls and consecutive
    beads of an arm are joined by a stick, drawn as a dense row of small spheres
    (so the z-buffer rasteriser needs no cylinder primitive). Stick spheres are
    appended after the real particles with ptype -5 and share their arm bead's
    outline id so no seams appear along a stick."""
    n = topo.n
    arm = topo.ptype == -4
    idx = np.nonzero(arm)[0]
    a, b = idx[:-1], idx[1:]
    keep = topo.strand[a] == topo.strand[b]
    a, b = a[keep], b[keep]
    step = max(args.stick_radius * 0.4, 1e-3)
    seg = pos[b] - pos[a]
    length = np.linalg.norm(seg, axis=1)
    cnt = np.maximum(np.ceil(length / step).astype(int) - 1, 0)
    owner = np.repeat(a, cnt)
    t = np.concatenate([(np.arange(1, c + 1) / (c + 1.0)) for c in cnt]) if cnt.sum() else np.zeros(0)
    sp = pos[owner] + seg[np.repeat(np.arange(len(a)), cnt)] * t[:, None]
    m = len(sp)
    radius = topo.radius.copy()
    radius[arm] = args.joint_radius
    pos2 = np.concatenate([pos, sp])
    zeros = np.zeros((m, 3))
    ptype2 = np.concatenate([topo.ptype, np.full(m, -5)])
    btype2 = np.concatenate([topo.btype, np.full(m, -1)])
    radius2 = np.concatenate([radius, np.full(m, args.stick_radius)])
    rgb2 = np.concatenate([body_rgb, body_rgb[owner]])
    vis = args.visible
    args.visible = np.concatenate([vis, vis[owner]])
    args._fit_mask = np.concatenate([args._fit_mask, np.zeros(m, bool)])
    args._gid = np.concatenate([np.arange(n), owner])
    fm = None if fade_mask is None else np.concatenate([fade_mask, fade_mask[owner]])
    return pos2, np.concatenate([a1, zeros]), np.concatenate([a3, zeros]), ptype2, btype2, radius2, rgb2, fm


def render_ghosted(args, solid, pos_w, a1, a3, ptype_r, btype_r, radius_r, body_rgb, topo, cmap, box,
                   fade_mask, log):
    """Two passes with one camera: `solid` particles opaque, all others at args.ghost_opacity.
    A pixel shows whichever layer is nearer; a solid particle behind a ghost is seen through it."""
    solid_full = solid if args._gid is None else solid[args._gid]
    vis0 = args.visible.copy()
    args._zref = vis0
    args.visible = vis0 & solid_full
    ic, cc, info_c = render_scene(args, pos_w, a1, a3, ptype_r, btype_r, radius_r, body_rgb, topo, cmap,
                                  box, fade_mask, log)
    args.visible = vis0 & ~solid_full
    ig, cg, info_g = render_scene(args, pos_w, a1, a3, ptype_r, btype_r, radius_r, body_rgb, topo, cmap,
                                  box, fade_mask, log)
    args.visible = vis0
    bg = np.array(hex_to_rgb(args._bg_hex)) * 255.0

    def straight(img, cov):          # undo the blend with the background at antialiased edges
        c = np.clip(cov, 1e-4, 1)[..., None]
        return np.clip((img.astype(np.float32) - bg * (1 - c)) / c, 0, 255)

    C, G = straight(ic, cc)[...], straight(ig, cg)
    a = float(args.ghost_opacity)
    cc3, cg3 = cc[..., None], (cg * a)[..., None]
    solid_front = (info_c["zmin"] <= info_g["zmin"])[..., None]
    # ghost over background, then solid over that   /   solid over background, then ghost over that
    g_under = bg * (1 - cg3) + G * cg3
    c_over = g_under * (1 - cc3) + C * cc3
    c_under = bg * (1 - cc3) + C * cc3
    g_over = c_under * (1 - cg3) + G * cg3
    out = np.where(solid_front, c_over, g_over)
    cover = np.maximum(cc, cg * a)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8), cover


def render(args, log=print) -> str:
    t_start = time.time()
    topo = parse_topology(args.top)
    box, pos, a1, a3 = parse_conf(args.conf, topo.n, args.frame)
    n = topo.n
    log(f"{os.path.basename(args.top)}: {n} particles, {int((topo.ptype == -3).sum())} cores, box {box}")

    # background
    bg_name = args.background.lower()
    transparent = bg_name == "transparent"
    bg_hex = NAMED_BG.get(bg_name, bg_name)
    if transparent:
        bg_hex = "#ffffff"
    if not bg_hex.startswith("#"):
        bg_hex = "#" + bg_hex
    r_, g_, b_ = hex_to_rgb(bg_hex)
    lum = 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_
    dark_bg = lum < 0.5 and not transparent
    args._bg_hex = bg_hex
    args._edge_hex = "#000000" if not dark_bg else "#05070a"
    args._box_hex = "#7a8190" if not dark_bg else "#9aa3b2"
    fg = (20, 24, 32) if not dark_bg else (232, 236, 242)

    # wrap + molecules
    pos_w, unit = wrap_positions(pos, topo.strand, box, args.wrap)
    is_core = topo.ptype == -3
    have_cores = bool(is_core.any())

    # colours
    labels = None
    cluster_legend, n_unassigned_units, fade_mask = [], 0, None
    use_cluster = args.cluster_file is not None
    if args.patches is None:
        args.patches = not use_cluster
    cmap, patch_legend = phb_patch_palette(topo.all_colors)
    if use_cluster:
        labels = load_labels(args.cluster_file, n, int(is_core.sum()))
        rgb, cluster_legend, unassigned, n_unassigned_units = build_cluster_colors(
            labels, topo.ptype, args.min_cluster_mols, args.highlight_largest)
        body_rgb = rgb.copy()
        # arms slightly darker than cores so molecule structure still reads
        body_rgb[topo.ptype == -4] *= 0.82
        fade_mask = unassigned
    else:
        body_rgb = np.where((topo.ptype == -3)[:, None],
                            np.array(hex_to_rgb(CORE_COLOR)), np.array(hex_to_rgb(ARM_COLOR)))

    if args.species_colors:
        _types, _cmap = species_colors(topo.ptype, topo.btype)
        for _t, _hx in _cmap.items():
            body_rgb[(topo.ptype == -3) & (topo.btype == _t)] = hex_to_rgb(_hx)

    # visibility: arms, slab
    visible = np.ones(n, bool)
    if args.no_arms and have_cores:
        visible &= is_core
    if args.slab:
        ax = "xyz".index(args.slab[0].lower())
        lo, hi = float(args.slab[1]), float(args.slab[2])
        # each strand is kept or dropped whole, by its first bead
        _, first = np.unique(unit, return_index=True)
        key = pos_w[first][unit][:, ax]
        frac = key / box[ax] + 0.5
        visible &= (frac >= lo) & (frac <= hi)
    args.visible = visible

    args._fit_mask = None
    args._fit_subset = bool(args.slab) or args.fit_cluster is not None
    if args.fit_cluster is not None:
        if labels is None:
            raise SystemExit("--fit-cluster needs --cluster-file")
        args._fit_mask = (labels == args.fit_cluster) & visible
    else:
        args._fit_mask = visible

    ptype_r, btype_r, radius_r = topo.ptype, topo.btype, topo.radius
    args._gid = None
    if args.model == "ballstick":
        pos_w, a1, a3, ptype_r, btype_r, radius_r, body_rgb, fade_mask = add_sticks(
            args, topo, pos_w, a1, a3, body_rgb, fade_mask)
        args.min_radius_frac = 0.0          # radii are explicit in ballstick mode

    rlog = (lambda *a: None) if args.quiet else log
    solid = getattr(args, "solid", None)
    if solid is None:
        img, cover, _info = render_scene(args, pos_w, a1, a3, ptype_r, btype_r, radius_r,
                                         body_rgb, topo, cmap, box, fade_mask, rlog)
    else:
        img, cover = render_ghosted(args, solid, pos_w, a1, a3, ptype_r, btype_r, radius_r,
                                    body_rgb, topo, cmap, box, fade_mask, rlog)

    out = Image.fromarray(img, "RGB")
    if transparent:
        a = Image.fromarray((np.clip(cover, 0, 1) * 255).astype(np.uint8), "L")
        out = out.convert("RGBA")
        out.putalpha(a)
    pil = out.convert("RGBA")

    # annotations
    bg_rgb = tuple(int(v * 255) for v in (r_, g_, b_))
    if args.title:
        d = ImageDraw.Draw(pil, "RGBA")
        f_t = find_font(max(14, int(34 * args.height / 1080)))
        m = int(26 * args.height / 1080)
        d.text((m, m), args.title, font=f_t, fill=(*fg, 255))
    if args.legend:
        if use_cluster:
            entries = []
            total_units = int(is_core.sum()) if have_cores else n
            for label, size, hx in cluster_legend[:args.legend_top]:
                entries.append((hx, f"cluster {label}: {size} mol ({100.0 * size / max(total_units, 1):.1f}%)"))
            rest = cluster_legend[args.legend_top:]
            if rest:
                entries.append(("#b0b5bd", f"{len(rest)} smaller clusters: {sum(s for _, s, _ in rest)} mol"))
            entries.append((UNASSIGNED_COLOR, f"unassigned / singletons: {n_unassigned_units} mol"))
            unit = "mol" if have_cores else "particles"
            draw_legend(pil, entries, f"Clusters ({len(cluster_legend)}, sizes in {unit})", fg, bg_rgb,
                        args.legend_corner)
        else:
            # one swatch per |colour|; "c / -c" pairs share a colour
            entries = [(hx, f"{a} / -{a}") for a, hx in patch_legend]
            draw_legend(pil, entries, "Patch colour (c / -c bond)", fg, bg_rgb, args.legend_corner,
                        columns=2 if len(entries) > 12 else 1)

    final = pil if transparent else pil.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    final.save(args.out, optimize=False, compress_level=3)
    log(f"wrote {args.out} ({args.width}x{args.height}) in {time.time() - t_start:.1f}s")
    return args.out


def main(argv=None):
    args = build_parser().parse_args(argv)
    render(args, log=(lambda *a: None) if args.quiet else (lambda *a: print(*a, flush=True)))


if __name__ == "__main__":
    main()
