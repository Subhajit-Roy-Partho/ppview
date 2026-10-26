#!/usr/bin/env python3
"""Species- and cluster-aware PHB renders (helix bundles shown), built on ppview's render_phb.py.

Colour scheme (per molecule = core + 3 arms):
  hue          = species (core btype): 2 species -> orange / blue ; 4 species -> orange / blue / green / violet
  arms         = lighter tint of the hue (so the helix bundle reads against the core)
  core shade   = DARK saturated if the molecule is six-valent (crystal-like), normal otherwise
  cluster      = molecules in the LARGEST cluster keep full colour; other clusters (>=2 mol) are washed 55% towards grey,
                 free molecules / singletons 80% (so a growing cluster stands out against what it has not yet captured)
Usage (library):  render_conf(top, conf, out_png, width=1920, height=1080, view='iso', slab=None, title='', legend=True, ...)
CLI:  render_species.py --top T --conf C --out O.png [--view iso|x|y|z] [--slab z 0.4 0.6] [--cores-only] [--width W --height H] [--title S]
"""
import argparse, os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/scratch/sroy85/Github/ppview")
import cluster_labels as CL
import render_phb as RP

SPECIES_HUES = ["#e4572e", "#2e86de", "#2fb344", "#8e44ad"]
SPECIES_NAMES = ["species I", "species II", "species III", "species IV"]
_hex = lambda h: np.array(RP.hex_to_rgb(h))
_state = {}

def _patched_build(labels, ptype, min_mols, highlight_largest):
    return _state["rgb"].copy(), [], np.zeros(len(labels), bool), 0

def particle_colours(topo, res, nspecies):
    mol = topo["mol"]; n = topo["n_mol"]; sp = topo["species"]
    val = res["valence"]; big = (res["mol_label"] == 0)
    csize = np.bincount(res["mol_label"][res["mol_label"] >= 0]) if (res["mol_label"] >= 0).any() else np.array([])
    base = np.array([_hex(SPECIES_HUES[min(s, 3)]) for s in sp])           # per molecule
    core_m = base.copy(); arm_m = base * 0.55 + 0.45
    six = (val == 6)
    core_m[six] *= 0.62
    wash = np.zeros(n)
    wash[(res["mol_label"] > 0)] = 0.55
    wash[(res["mol_label"] < 0)] = 0.80
    grey = np.array([0.80, 0.81, 0.83])
    core_m = core_m * (1 - wash[:, None]) + grey * wash[:, None]
    arm_m = arm_m * (1 - wash[:, None]) + grey * wash[:, None]
    rgb = np.where((topo["ptype"] == -3)[:, None], core_m[mol], arm_m[mol])
    return rgb

def min_image(d, box):
    return d - box * np.round(d / box)

def wrap_molecules(topo, pos, box, detach=3.5):
    """Wrap each molecule rigidly into [0, L): the core is the reference and arm beads follow by minimum image.
    An arm strand whose first bead is farther than `detach` from its own core (anchor broken) is wrapped on its own."""
    mol = topo["mol"]; core = topo["cores"]; strand = topo["strand"]
    ref = pos[core][mol]
    out = np.mod(ref, box) + min_image(pos - ref, box)
    arm = np.where(topo["ptype"] == -4)[0]
    if len(arm):
        _, first_idx, inv = np.unique(strand[arm], return_index=True, return_inverse=True)
        firstbead = arm[first_idx]                                   # first bead of every arm strand
        dist = np.linalg.norm(min_image(pos[firstbead] - ref[firstbead], box), axis=1)
        far = dist > detach
        if far.any():
            ref_s = pos[firstbead]
            own = np.mod(ref_s[inv], box) + min_image(pos[arm] - ref_s[inv], box)
            sel = far[inv]
            out[arm[sel]] = own[sel]
    return out

def write_conf(path, t, box, pos, a1, a3):
    with open(path, "w") as f:
        f.write(f"t = {int(t)}\nb = {box[0]:.10g} {box[1]:.10g} {box[2]:.10g}\nE = 0 0 0\n")
        np.savetxt(f, np.hstack([pos, a1, a3, np.zeros((len(pos), 6))]), fmt="%.10g")

def draw_legend(img, items, title, corner="bl", scale=1.0):
    d = ImageDraw.Draw(img, "RGBA"); W, H = img.size
    fs = max(13, int(26 * H / 1080 * scale)); f = RP.find_font(fs); ft = RP.find_font(int(fs * 1.1))
    pad = int(fs * 0.7); row = int(fs * 1.5); sw = int(fs * 1.0)
    wmax = max(d.textlength(t, font=f) for _, t in items + [(None, title)])
    bw = int(wmax + sw + pad * 3); bh = int(pad * 2 + row * (len(items) + 1))
    x0 = pad if "l" in corner else W - bw - pad; y0 = H - bh - pad if "b" in corner else pad
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=pad, fill=(255, 255, 255, 215), outline=(150, 155, 165, 255))
    d.text((x0 + pad, y0 + pad * 0.8), title, font=ft, fill=(20, 24, 32, 255))
    for i, (c, t) in enumerate(items):
        y = y0 + pad + row * (i + 1)
        if c is not None:
            d.ellipse([x0 + pad, y, x0 + pad + sw, y + sw], fill=tuple(int(v * 255) for v in c) + (255,), outline=(40, 40, 40, 255))
        d.text((x0 + pad * 2 + sw, y - 2), t, font=f, fill=(20, 24, 32, 255))

def render_conf(top, conf, out, width=1920, height=1080, view="iso", slab=None, title="", legend=True, cores_only=False,
                zoom=1.0, box=True, fit="box", scale=1, azim=None, elev=None, background="white", topo=None, res=None, fit_cluster=None):
    topo = topo or CL.load_topology(top)
    t_, box_, pos_, a1_, a3_ = CL.load_conf(conf, topo["N"])
    if res is None:
        res = CL.analyze_conf(topo, conf=(t_, box_, pos_, a1_, a3_))
    wconf = tempfile.NamedTemporaryFile("w", suffix=".dat", delete=False); wconf.close()
    write_conf(wconf.name, t_, box_, wrap_molecules(topo, pos_, box_), a1_, a3_)
    nsp = int(topo["species"].max()) + 1
    _state["rgb"] = particle_colours(topo, res, nsp)
    RP.build_cluster_colors = _patched_build
    dummy = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    np.savetxt(dummy, res["labels"], fmt="%d"); dummy.close()
    argv = ["--top", top, "--conf", wconf.name, "--wrap", "none", "--out", out, "--width", str(width), "--height", str(height), "--scale", str(scale),
            "--background", background, "--cluster-file", dummy.name, "--min-cluster-mols", "1", "--view", view, "--fit", fit, "--zoom", str(zoom), "--quiet"]
    if fit_cluster is not None: argv += ["--fit-cluster", str(fit_cluster)]
    if cores_only: argv.append("--cores-only")
    if slab: argv += ["--slab", slab[0], str(slab[1]), str(slab[2])]
    if box: argv.append("--box")
    if azim is not None: argv += ["--azim", str(azim)]
    if elev is not None: argv += ["--elev", str(elev)]
    RP.main(argv)
    os.unlink(dummy.name); os.unlink(wconf.name)
    img = Image.open(out).convert("RGBA")
    img = img.convert('RGBA'); d = ImageDraw.Draw(img, 'RGBA')
    if title:
        f = RP.find_font(max(14, int(30 * height / 1080)))
        x0, y0 = int(18 * height / 1080), int(14 * height / 1080)
        tw = d.textlength(title, font=f)
        d.rounded_rectangle([x0 - 6, y0 - 4, x0 + tw + 10, y0 + int(40 * height / 1080)], radius=8, fill=(255, 255, 255, 230))
        d.text((x0 + 2, y0), title, font=f, fill=(20, 24, 32, 255))
    if legend:
        items = [(_hex(SPECIES_HUES[s]), f"{SPECIES_NAMES[s]} core / arms (light)") for s in range(min(nsp, 4))]
        items.append((_hex(SPECIES_HUES[0]) * 0.62, "dark core = six-valent molecule"))
        items.append((np.array([0.80, 0.81, 0.83]), "washed = outside the largest cluster"))
        draw_legend(img, items, "Particles", "bl")
    img.convert("RGB").save(out)
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", required=True); ap.add_argument("--conf", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--view", default="iso"); ap.add_argument("--slab", nargs=3, default=None)
    ap.add_argument("--cores-only", action="store_true"); ap.add_argument("--title", default="")
    ap.add_argument("--zoom", type=float, default=1.0); ap.add_argument("--fit", default="box")
    a = ap.parse_args()
    render_conf(a.top, a.conf, a.out, a.width, a.height, a.view, a.slab, a.title, True, a.cores_only, a.zoom, fit=a.fit)
