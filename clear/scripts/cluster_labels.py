#!/usr/bin/env python3
"""
cluster_labels.py - per-particle cluster labels for PHB (patchy helix bundle) configurations.

WHAT IT DOES
  1. Parses a PHB topology (.phb: iP patch catalogue, iC colour->patch lists, particle lines).
  2. Parses an oxDNA configuration (.dat) (first 3 lines = t / b / E header, then one
     line per particle: pos(3) a1(3) a3(3) v(3) L(3)).
  3. Detects INTER-MOLECULE patch bonds with the same criterion as analyze_phb_crystal.py
     (which mirrors C++ Analysis::identifyPHBCrystalFormation / PHBInteraction.cpp):
        - a bond is a pair of patches on two different molecules whose colours are
          complementary and whose "patch distance"
              | min_image(pos_q - pos_p) + (ic_q - ic_p) |  <  cutoff     (default 0.3)
          where ic = R(a1,a2,a3) @ body_patch_position and a2 = a3 x a1.
        - colour complementarity follows the simulation rule (PHBInteraction.cpp):
              colour 100 never binds; if |c_p|<10 and |c_q|<10: bond iff c_p == c_q;
              otherwise bond iff c_p + c_q == 0.
          (--rule sumzero uses the strict c_p + c_q == 0 rule of analyze_phb_crystal.py;
          both are identical for the inter-molecular channels |c| >= 500.)
  4. Groups particles into molecules: a molecule is a contiguous block of helix beads
     (type -4) terminated by the icosahedral core (type -3), as in analyze_phb_crystal.py.
  5. Builds the molecule graph (edge = >=1 bond), finds connected components, ranks them by
     size (rank 0 = largest) and writes ONE INTEGER PER PARTICLE (topology order):
        label >= 0 : rank of the cluster the molecule belongs to (0 = largest)
        label  -1  : molecule is in a cluster smaller than --min-size (default 2, i.e.
                     singletons / unbonded molecules)
     Every particle (core and all arm beads) takes the label of its molecule.
  6. Optionally writes a JSON summary (cluster sizes, valence histogram, bond counts per
     channel, species mixing, ...).

USAGE
  python cluster_labels.py --top X.phb --conf Y.dat --out labels.txt [--json summary.json]
         [--cutoff 0.3] [--min-size 2] [--rule sim|sumzero] [--exclusive]

  --min-size K   clusters with fewer than K molecules are labelled -1 (default 2: singletons
                 only).  Use e.g. --min-size 8 to also hide small oligomers.
  --exclusive    one-to-one greedy patch matching by increasing distance (as the C++ code
                 does); default is off, matching analyze_phb_crystal.py.

AS A MODULE
  from cluster_labels import analyze
  res = analyze(top_path, conf_path)       # dict with arrays: mol_of_bead, labels, valence, ...
  The topology parse can be reused across many configurations:
      topo = load_topology(top_path); res = analyze_conf(topo, conf_path)

Notes
  * "Channel" in the summary is |colour|-500 for far-tip/core bonds with |colour| in 501..506
    (for the 2-species design this is pair P1..P6 = (1,5),(2,12),(3,8),(4,7),(6,11),(9,10)).
    Bonds involving other colours (e.g. anchor colours 21..26) are tagged "anchor".
  * Species of a molecule = btype of its core bead (0 / 1 in the 2-species systems,
    0..3 in the 4-species ones).
  * Periodic boundaries are handled with minimum image; positions need not be wrapped.
  * Needs numpy and scipy.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


# ----------------------------------------------------------------------------- topology
def load_topology(path):
    """Parse a .phb file. Returns dict with per-bead arrays and the patch catalogue."""
    ip = {}      # pid -> (color, strength, body_pos)
    ic = {}      # cid -> [pids]
    ptype, strand, btype = [], [], []
    with open(path) as f:
        header = f.readline().split()
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == "iP":
                ip[int(p[1])] = (int(p[2]), float(p[3]), np.array([float(p[4]), float(p[5]), float(p[6])]))
            elif p[0] == "iC":
                ic[int(p[1])] = [int(x) for x in p[2:]]
            else:
                ptype.append(int(p[0])); strand.append(int(p[1])); btype.append(int(p[2]))
    ptype = np.array(ptype); strand = np.array(strand); btype = np.array(btype)
    N = len(ptype)
    if int(header[0]) != N:
        raise ValueError(f"topology header says {header[0]} particles but {N} particle lines found")

    # molecules: contiguous -4 beads terminated by a -3 core
    mol = np.full(N, -1, dtype=int)
    cores = []
    pending = []
    m = 0
    for i in range(N):
        if ptype[i] == -4:
            pending.append(i)
        elif ptype[i] == -3:
            for h in pending:
                mol[h] = m
            mol[i] = m
            cores.append(i)
            pending = []
            m += 1
    if pending or (mol < 0).any():
        raise ValueError("could not assign every particle to a molecule (unexpected bead ordering)")
    n_mol = m
    cores = np.array(cores)

    # per-bead patch lists (skipping colour 100 = inert)
    site_bead, site_color, site_body = [], [], []
    for i in range(N):
        for pid in ic.get(int(btype[i]), []):
            c, s, body = ip[pid]
            if c == 100:
                continue
            site_bead.append(i); site_color.append(c); site_body.append(body)
    site_bead = np.array(site_bead, dtype=int)
    site_color = np.array(site_color, dtype=int)
    site_body = np.array(site_body, dtype=float).reshape(-1, 3)
    return dict(N=N, n_mol=n_mol, ptype=ptype, strand=strand, btype=btype, mol=mol, cores=cores,
                species=btype[cores], site_bead=site_bead, site_color=site_color, site_body=site_body,
                ip=ip, ic=ic, path=str(path))


# ----------------------------------------------------------------------------- configuration
def load_conf(path, N=None):
    """Return (t, box(3), pos(N,3), a1(N,3), a3(N,3))."""
    with open(path) as f:
        t = float(f.readline().split("=")[1])
        box = np.array([float(x) for x in f.readline().split("=")[1].split()])
        f.readline()
        data = np.loadtxt(f, ndmin=2, usecols=range(9))
    if N is not None and data.shape[0] != N:
        raise ValueError(f"conf has {data.shape[0]} particles, topology has {N}")
    return t, box, data[:, 0:3], data[:, 3:6], data[:, 6:9]


def parse_frame_text(text):
    """Parse one trajectory frame given as text (t/b/E header + particle lines)."""
    lines = text.splitlines()
    t = float(lines[0].split("=")[1])
    box = np.array([float(x) for x in lines[1].split("=")[1].split()])
    data = np.array([l.split()[:9] for l in lines[3:] if l.strip()], dtype=float)
    return t, box, data[:, 0:3], data[:, 3:6], data[:, 6:9]


# ----------------------------------------------------------------------------- bonds
def _compatible(ca, cb, rule):
    """Vectorised colour complementarity for arrays ca, cb."""
    if rule == "sumzero":
        return (ca + cb) == 0
    small = (np.abs(ca) < 10) & (np.abs(cb) < 10)
    return np.where(small, ca == cb, (ca + cb) == 0)


def detect_bonds(topo, box, pos, a1, a3, cutoff=0.3, rule="sim", exclusive=False, scope="inter"):
    """Patch bonds. scope="inter": only pairs on different molecules (the crystal bonds);
    scope="intra": only pairs on the same molecule but different strands (arm anchors to
    their own core); scope="all": both.  Returns dict of arrays (bead_a, bead_b, mol_a,
    mol_b, color_a, color_b, dist, ...)."""
    sb, sc, sbody = topo["site_bead"], topo["site_color"], topo["site_body"]
    a2 = np.cross(a3, a1)
    a2 /= np.maximum(np.linalg.norm(a2, axis=1, keepdims=True), 1e-12)
    # world offset of each patch from its bead centre: R @ body, R columns (a1, a2, a3)
    ic = (a1[sb] * sbody[:, 0:1] + a2[sb] * sbody[:, 1:2] + a3[sb] * sbody[:, 2:3])
    wp = pos[sb] + ic
    wrapped = np.mod(wp, box)
    wrapped[wrapped >= box] = 0.0
    tree = cKDTree(wrapped, boxsize=box)
    pairs = tree.query_pairs(cutoff + 0.05, output_type="ndarray")
    empty = dict(bead_a=np.zeros(0, int), bead_b=np.zeros(0, int), mol_a=np.zeros(0, int),
                 mol_b=np.zeros(0, int), color_a=np.zeros(0, int), color_b=np.zeros(0, int),
                 dist=np.zeros(0), site_a=np.zeros(0, int), site_b=np.zeros(0, int))
    if len(pairs) == 0:
        return empty
    i, j = pairs[:, 0], pairs[:, 1]
    mol = topo["mol"]
    same = mol[sb[i]] == mol[sb[j]]
    if scope == "inter":
        keep = ~same
    elif scope == "intra":
        keep = same & (topo["strand"][sb[i]] != topo["strand"][sb[j]])
    else:
        keep = topo["strand"][sb[i]] != topo["strand"][sb[j]]
    keep &= _compatible(sc[i], sc[j], rule)
    i, j = i[keep], j[keep]
    if len(i) == 0:
        return empty
    # exact PHBInteraction patch distance
    dr = pos[sb[j]] - pos[sb[i]]
    dr -= box * np.round(dr / box)
    d = np.linalg.norm(dr + ic[j] - ic[i], axis=1)
    ok = d < cutoff
    i, j, d = i[ok], j[ok], d[ok]
    if exclusive and len(i):
        order = np.argsort(d)
        used = set(); sel = []
        for k in order:
            if int(i[k]) in used or int(j[k]) in used:
                continue
            used.add(int(i[k])); used.add(int(j[k])); sel.append(k)
        sel = np.array(sel, dtype=int)
        i, j, d = i[sel], j[sel], d[sel]
    # drop duplicate bead pairs (keep first)
    seen = set(); sel = []
    for k in range(len(i)):
        key = (min(sb[i[k]], sb[j[k]]), max(sb[i[k]], sb[j[k]]), sc[i[k]], sc[j[k]])
        if key in seen:
            continue
        seen.add(key); sel.append(k)
    sel = np.array(sel, dtype=int)
    i, j, d = i[sel], j[sel], d[sel]
    return dict(bead_a=sb[i], bead_b=sb[j], mol_a=mol[sb[i]], mol_b=mol[sb[j]],
                color_a=sc[i], color_b=sc[j], dist=d, site_a=i, site_b=j)


# ----------------------------------------------------------------------------- clustering
def cluster_molecules(n_mol, mol_a, mol_b):
    """Connected components of the molecule graph. Returns (comp_id per molecule, sizes by comp)."""
    if len(mol_a) == 0:
        return np.arange(n_mol), np.ones(n_mol, dtype=int)
    g = coo_matrix((np.ones(len(mol_a)), (mol_a, mol_b)), shape=(n_mol, n_mol))
    ncomp, comp = connected_components(g, directed=False)
    sizes = np.bincount(comp, minlength=ncomp)
    return comp, sizes


def rank_labels(comp, sizes, min_size=2):
    """Map components to ranks (0 = largest). Components smaller than min_size -> -1."""
    order = np.argsort(-sizes, kind="stable")
    rank_of_comp = np.full(len(sizes), -1, dtype=int)
    r = 0
    for c in order:
        if sizes[c] >= min_size:
            rank_of_comp[c] = r; r += 1
    return rank_of_comp[comp]


def molecule_valence(n_mol, mol_a, mol_b):
    """Number of DISTINCT neighbouring molecules (as analyze_phb_crystal.py)."""
    nb = defaultdict(set)
    for a, b in zip(mol_a, mol_b):
        nb[int(a)].add(int(b)); nb[int(b)].add(int(a))
    val = np.array([len(nb[m]) for m in range(n_mol)], dtype=int)
    return val, nb


def analyze_conf(topo, conf_path=None, conf=None, cutoff=0.3, rule="sim", exclusive=False, min_size=2):
    """Full analysis of one configuration. Pass either conf_path or conf=(t, box, pos, a1, a3)."""
    if conf is None:
        conf = load_conf(conf_path, topo["N"])
    t, box, pos, a1, a3 = conf
    b = detect_bonds(topo, box, pos, a1, a3, cutoff, rule, exclusive)
    n_mol = topo["n_mol"]
    comp, sizes = cluster_molecules(n_mol, b["mol_a"], b["mol_b"])
    mol_label = rank_labels(comp, sizes, min_size)
    labels = mol_label[topo["mol"]]
    val, nb = molecule_valence(n_mol, b["mol_a"], b["mol_b"])
    # physical (strand-level) graph: nodes = strands (each arm and each core), edges = ALL
    # complementary patch bonds, including an arm's anchor to its own core.  If every arm
    # is still attached to its core this equals the molecule graph; if arms have detached
    # (bad anchor colours) the two differ.
    ba = detect_bonds(topo, box, pos, a1, a3, cutoff, rule, exclusive, scope="all")
    strand = topo["strand"]
    uniq, sinv = np.unique(strand, return_inverse=True)
    ns = len(uniq)
    if len(ba["bead_a"]):
        g = coo_matrix((np.ones(len(ba["bead_a"])), (sinv[ba["bead_a"]], sinv[ba["bead_b"]])), shape=(ns, ns))
        _, scomp = connected_components(g, directed=False)
    else:
        scomp = np.arange(ns)
    core_strand = sinv[topo["cores"]]
    ccount = np.bincount(scomp[core_strand], minlength=scomp.max() + 1)
    anchors = detect_bonds(topo, box, pos, a1, a3, cutoff, rule, exclusive, scope="intra")
    return dict(t=t, box=box, pos=pos, a1=a1, a3=a3, bonds=b, comp=comp, comp_sizes=sizes,
                mol_label=mol_label, labels=labels, valence=val, neighbors=nb,
                physical_core_counts=np.sort(ccount[ccount > 0])[::-1], anchors=anchors)


def clique_stats(topo, nb):
    """Triangles, 4-cliques ("tetrahedra") and clustering coefficient of the molecule graph.
    n_tetra_4species counts 4-cliques whose cores are of 4 distinct species (4-species designs).
    tetra_per_mol is comparable with the legacy-systems numbers (ideal crystal ~0.378)."""
    sp = topo["species"]
    tri = tet = tet4 = 0
    for a in nb:
        na = nb[a]
        for b in na:
            if b <= a:
                continue
            common = na & nb[b]
            for c in common:
                if c <= b:
                    continue
                tri += 1
                for d in common & nb[c]:
                    if d <= c:
                        continue
                    tet += 1
                    if len({int(sp[a]), int(sp[b]), int(sp[c]), int(sp[d])}) == 4:
                        tet4 += 1
    wedge = sum(len(v) * (len(v) - 1) / 2 for v in nb.values())
    return dict(n_triangles=tri, n_tetra=tet, n_tetra_4species=tet4,
                clustering=float(3 * tri / wedge) if wedge > 0 else 0.0)


def channel_name(ca, cb):
    m = max(abs(int(ca)), abs(int(cb)))
    if 501 <= m <= 506:
        return f"P{m-500}"
    return "anchor"


def summarize(topo, res, cutoff=0.3, rule="sim"):
    n_mol = topo["n_mol"]
    sizes = np.sort(res["comp_sizes"])[::-1]
    val = res["valence"]
    vc = Counter(val.tolist())
    b = res["bonds"]
    ch = Counter(channel_name(x, y) for x, y in zip(b["color_a"], b["color_b"]))
    sp = topo["species"]
    mix = Counter()
    pair_mols = set()
    for a, c in zip(b["mol_a"], b["mol_b"]):
        key = (int(min(a, c)), int(max(a, c)))
        if key in pair_mols:
            continue
        pair_mols.add(key)
        sa, sc_ = sorted((int(sp[a]), int(sp[c])))
        mix[f"{sa}-{sc_}"] += 1
    _cq = clique_stats(topo, res["neighbors"])
    return {
        "topology": topo["path"], "n_particles": topo["N"], "n_molecules": n_mol,
        "time": res["t"], "box": res["box"].tolist(), "cutoff": cutoff, "rule": rule,
        "n_patch_bonds": int(len(b["mol_a"])), "n_molecule_pairs_bonded": len(pair_mols),
        "n_clusters_total": int(len(sizes)),
        "n_clusters_ge2": int((sizes >= 2).sum()),
        "largest_cluster": int(sizes[0]), "largest_cluster_fraction": float(sizes[0] / n_mol),
        "second_cluster": int(sizes[1]) if len(sizes) > 1 else 0,
        "n_singletons": int((sizes == 1).sum()),
        "top_cluster_sizes": [int(s) for s in sizes[:20]],
        "cluster_size_histogram": {str(k): int(v) for k, v in sorted(Counter(sizes.tolist()).items())},
        "mean_valence": float(val.mean()),
        "valence_histogram": {str(k): int(vc.get(k, 0)) for k in range(0, int(val.max()) + 1)},
        "fraction_valence6": float((val == 6).mean()),
        "fraction_bonded": float((val >= 1).mean()),
        "bonds_per_channel": dict(ch),
        "bonded_pairs_by_species": dict(mix),
        "n_nearbead_anchor_bonds": int(ch.get("anchor", 0)),
        "anchors_intact": int(len(res["anchors"]["bead_a"])),
        "anchors_expected": int(3 * n_mol),
        "physical_largest_cluster_cores": int(res["physical_core_counts"][0]),
        "physical_largest_cluster_fraction": float(res["physical_core_counts"][0] / n_mol),
        **_cq,
        "tetra_per_molecule": _cq["n_tetra"] / n_mol,
        "tetra_4species_per_molecule": _cq["n_tetra_4species"] / n_mol,
        "mean_bond_patch_distance": float(b["dist"].mean()) if len(b["dist"]) else None,
    }


def analyze(top_path, conf_path, cutoff=0.3, rule="sim", exclusive=False, min_size=2):
    topo = load_topology(top_path)
    res = analyze_conf(topo, conf_path, cutoff=cutoff, rule=rule, exclusive=exclusive, min_size=min_size)
    res["topo"] = topo
    res["summary"] = summarize(topo, res, cutoff, rule)
    return res


# ----------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", required=True, help="PHB topology (.phb)")
    ap.add_argument("--conf", required=True, help="oxDNA configuration (.dat)")
    ap.add_argument("--out", required=True, help="output per-particle label file (one int per line)")
    ap.add_argument("--json", help="optional JSON summary output")
    ap.add_argument("--cutoff", type=float, default=0.3, help="patch distance cutoff (default 0.3)")
    ap.add_argument("--min-size", type=int, default=2,
                    help="clusters smaller than this get label -1 (default 2 => only singletons)")
    ap.add_argument("--rule", choices=["sim", "sumzero"], default="sim",
                    help="colour complementarity rule (default: simulation rule)")
    ap.add_argument("--exclusive", action="store_true", help="one-to-one greedy patch matching")
    a = ap.parse_args(argv)

    res = analyze(a.top, a.conf, a.cutoff, a.rule, a.exclusive, a.min_size)
    with open(a.out, "w") as f:
        f.write("\n".join(str(int(x)) for x in res["labels"]) + "\n")
    s = res["summary"]
    s["labels_file"] = a.out
    s["min_size"] = a.min_size
    if a.json:
        with open(a.json, "w") as f:
            json.dump(s, f, indent=2)
    print(f"{s['n_molecules']} molecules, {s['n_patch_bonds']} inter-molecule patch bonds, "
          f"{s['n_clusters_ge2']} clusters (>=2), largest {s['largest_cluster']} "
          f"({100*s['largest_cluster_fraction']:.1f}%), mean valence {s['mean_valence']:.2f}, "
          f"valence-6 {100*s['fraction_valence6']:.1f}%  -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
