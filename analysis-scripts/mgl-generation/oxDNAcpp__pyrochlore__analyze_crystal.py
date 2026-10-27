#!/usr/bin/env python3
"""
analyze_crystal.py — Pyrochlore crystal quality analysis for patchy-particle simulations.

Supports three topology formats:
  phb   Single .top/.phb file with inline iP/iC body lines (PatchyShape or PHB)
  psi   Separate BIG.top + CRYSTAL.particles.txt + sat24.patches.txt
  psp2  PSP2 .psp file (pyrochlore_psp2.psp or ico_cg.psp style)

Two binding-detection modes:
  distance    (default) — complementary-color patch pairs within --cutoff
  orientation — additionally requires patch-direction cosine alignment

PHB (Patchy Helix Bundle) format notes:
  Each PHB bundle = 1 HEAD bead (-3 line) + N ARM beads (-4 lines).
  - HEAD beads carry icosahedral patches at |pos|=1.0 and drive all inter-particle bonding.
  - ARM beads are WLC spacer-extenders enabling photonic crystal lattice spacing; they do
    NOT form inter-particle patchy bonds and are excluded from the particle list.
  - In the conf file, arm beads appear BEFORE the head bead for each bundle, so
    conf_idx for head bead k is (N_arm_beads_per_bundle * k) + (N_arm_beads_per_bundle).
    The parser tracks global_bead_idx over both -3 and -4 lines to get this right.
  Binding rule: abs(c_i) % 500 == abs(c_j) % 500 AND c_i * c_j < 0  (modulo-500 rule).
  This covers pure sat24 (22↔-22) and mixed PHB (522↔-22) color schemes.
  Recommended cutoff for PHB: --cutoff 0.20 (actual bonded patch distances are 0.05-0.10).

Usage examples:
  # PHB inline topology (Patchy Helix Bundle)
  python analyze_crystal.py --format phb \\
      --top /mnt/Drive/PHB/simulation/input.phb \\
      --conf /mnt/Drive/PHB/simulation/last_conf.dat \\
      --cutoff 0.20 --mgl --mgl-out clusters.mgl

  # PatchyShape inline topology
  python analyze_crystal.py --format phb --top patchy.top --conf last_conf.dat

  # Separate-files topology (generate.py style)
  python analyze_crystal.py --format psi \\
      --top BIG.top --particles CRYSTAL.particles.txt --patches sat24.patches.txt \\
      --conf last_conf.BIG.dat

  # PSP2 topology
  python analyze_crystal.py --format psp2 --top pyrochlore_psp2.psp --conf pyrochlore_init.dat

  # Enable orientation check and MGL output
  python analyze_crystal.py --format phb --top patchy.top --conf last_conf.dat \\
      --mode orientation --cos-threshold 0.85 --mgl --mgl-out clusters.mgl
"""

import argparse
import sys
import re
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
import numpy as np

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PatchDef:
    """A patch prototype: global id, color, body-frame position and a1 axis."""
    pid:   int
    color: int
    pos:   np.ndarray   # (3,) body-frame displacement from COM
    a1:    np.ndarray   # (3,) body-frame orientation axis (for cosine mode)

@dataclass
class ParticleData:
    """Per-particle topology data."""
    idx:       int
    ptype:     int         # particle type (0-3 for pyrochlore)
    patch_ids: List[int]   # ordered list of PatchDef.pid values on this particle
    conf_idx:  int = -1    # index into the conf file (may differ from idx in PHB format
                           # where -4 arm beads interleave with -3 head beads)

@dataclass
class Bond:
    """A detected patch-patch bond between two particles."""
    i:        int    # particle index
    j:        int    # particle index (j > i)
    pi:       int    # PatchDef pid on particle i
    pj:       int    # PatchDef pid on particle j
    color:    int    # |color| of the complementary pair
    dist:     float  # patch-centre-to-patch-centre distance
    cos_i:    float  # patch-direction cosine for particle i (1.0 if not computed)
    cos_j:    float  # patch-direction cosine for particle j
    intended: bool   # False when valence overflows or same-type bonding

@dataclass
class ClusterResult:
    """Full analysis result for one connected component."""
    cid:                    int
    particle_ids:           List[int]
    bonds:                  List[Bond]
    avg_valence:            float
    full_valence_fraction:  float   # fraction with valence == expected_valence
    type_counts:            Dict[int, int]
    is_crystal_like:        bool
    shell_sizes:            List[int]   # [shell-0 count, shell-1 count, ...]
    n_unit_cells:           float
    non_intended_bonds:     List[Bond]
    notes:                  List[str]

# ---------------------------------------------------------------------------
# Topology parsers
# ---------------------------------------------------------------------------

def _parse_iP_iC_body(lines: List[str]) -> Tuple[List[ParticleData], Dict[int, PatchDef]]:
    """
    Shared parser for PHB/PatchyShape inline topology.

    Expected sections (in any order):
      iP id color strength px py pz a1x a1y a1z [a2x a2y a2z]
      iC type_id patch_id0 patch_id1 ...
      -3 strand_id type_id radius          (PatchyShape body)
      -33 strand_id type_id radius ...     (PHB body variant, same type_id at pos 2)
    """
    patch_defs:      Dict[int, PatchDef] = {}
    type_to_patches: Dict[int, List[int]] = {}
    particles:       List[ParticleData]  = []
    particle_idx = 0
    global_bead_idx = 0  # tracks position in conf file (counts every -3 and -4 line)

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        tag = parts[0]

        if tag == 'iP':
            pid    = int(parts[1])
            color  = int(parts[2])
            # parts[3] = strength (ignored)
            px, py, pz = float(parts[4]), float(parts[5]), float(parts[6])
            if len(parts) >= 10:
                a1x, a1y, a1z = float(parts[7]), float(parts[8]), float(parts[9])
            else:
                # a1 not stored — use normalised patch position as proxy
                v = np.array([px, py, pz])
                n = np.linalg.norm(v)
                a1x, a1y, a1z = (v / n).tolist() if n > 0 else (0., 0., 1.)
            patch_defs[pid] = PatchDef(
                pid=pid, color=color,
                pos=np.array([px, py, pz]),
                a1=np.array([a1x, a1y, a1z]))

        elif tag == 'iC':
            tid  = int(parts[1])
            pids = [int(x) for x in parts[2:]]
            type_to_patches[tid] = pids

        elif tag in ('-3', '-33'):
            # Patchy head bead: -3 strand_id type_id radius ...
            ptype = int(parts[2])
            pids  = type_to_patches.get(ptype, [])
            particles.append(ParticleData(idx=particle_idx, ptype=ptype,
                                          patch_ids=list(pids),
                                          conf_idx=global_bead_idx))
            particle_idx += 1
            global_bead_idx += 1

        elif tag == '-4':
            # Helix arm bead: not a patchy particle, but occupies a conf slot
            global_bead_idx += 1

    return particles, patch_defs


def parse_phb_top(top_file: str) -> Tuple[List[ParticleData], Dict[int, PatchDef]]:
    """Parse a single-file PHB or PatchyShape topology."""
    with open(top_file) as f:
        lines = f.readlines()
    return _parse_iP_iC_body(lines)


def parse_psi_top(top_file: str, particles_file: str, patches_file: str
                  ) -> Tuple[List[ParticleData], Dict[int, PatchDef]]:
    """
    Parse PatchyShapeInteraction topology from three separate files:
      top_file      BIG.top  (N ntypes \\n type0 type1 ...)
      particles_file CRYSTAL.particles.txt
      patches_file  sat24.patches.txt
    """
    # --- patches file ---
    patch_defs: Dict[int, PatchDef] = {}
    with open(patches_file) as f:
        content = f.read()
    for blk in re.finditer(r'patch_\d+\s*=\s*\{([^}]*)\}', content, re.DOTALL):
        b = blk.group(1)
        pid   = int(re.search(r'id\s*=\s*(\d+)', b).group(1))
        color = int(re.search(r'color\s*=\s*(-?\d+)', b).group(1))
        pm = re.search(r'position\s*=\s*([\d.e+\-]+)\s*,\s*([\d.e+\-]+)\s*,\s*([\d.e+\-]+)', b)
        px, py, pz = float(pm.group(1)), float(pm.group(2)), float(pm.group(3))
        # a1 from file if present, else fall back to normalised position
        am = re.search(r'a1\s*=\s*([\d.e+\-]+)\s*,\s*([\d.e+\-]+)\s*,\s*([\d.e+\-]+)', b)
        if am:
            a1 = np.array([float(am.group(1)), float(am.group(2)), float(am.group(3))])
        else:
            v = np.array([px, py, pz])
            n = np.linalg.norm(v)
            a1 = v / n if n > 0 else np.array([0., 0., 1.])
        patch_defs[pid] = PatchDef(pid=pid, color=color, pos=np.array([px, py, pz]), a1=a1)

    # --- particles file ---
    type_to_patches: Dict[int, List[int]] = {}
    with open(particles_file) as f:
        content = f.read()
    for blk in re.finditer(r'particle_\d+\s*=\s*\{([^}]*)\}', content, re.DOTALL):
        b = blk.group(1)
        tid = int(re.search(r'type\s*=\s*(\d+)', b).group(1))
        ps  = re.search(r'patches\s*=\s*([\d,\s]+)', b).group(1)
        pids = [int(x.strip()) for x in ps.split(',') if x.strip()]
        type_to_patches[tid] = pids

    # --- topology file ---
    particles: List[ParticleData] = []
    with open(top_file) as f:
        raw = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    N = int(raw[0].split()[0])
    type_assignments = [int(x) for x in raw[1].split()]
    for idx, ptype in enumerate(type_assignments[:N]):
        particles.append(ParticleData(idx=idx, ptype=ptype,
                                      patch_ids=list(type_to_patches.get(ptype, [])),
                                      conf_idx=idx))
    return particles, patch_defs


def parse_psp2_top(psp_file: str) -> Tuple[List[ParticleData], Dict[int, PatchDef]]:
    """
    Parse PSP2 .psp topology.

    Header: N_particles  N_strands  max_patches  max_springs
    iP lines: iP id color strength px py pz
    iS lines: skipped (springs only affect geometry, not binding colour)
    Body:
      -5 strand_id radius mass num_patches [patch_ids] [neigh spring ...]
      -6 strand_id radius mass 0 [neigh spring ...]  (center bead, no patches)
    """
    patch_defs: Dict[int, PatchDef] = {}
    particles:  List[ParticleData]  = []
    particle_idx = 0

    with open(psp_file) as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        tag = parts[0]

        if tag == 'iP':
            pid    = int(parts[1])
            color  = int(parts[2])
            # parts[3] = strength
            px, py, pz = float(parts[4]), float(parts[5]), float(parts[6])
            v = np.array([px, py, pz])
            n = np.linalg.norm(v)
            a1 = v / n if n > 0 else np.array([0., 0., 1.])
            patch_defs[pid] = PatchDef(pid=pid, color=color, pos=v, a1=a1)

        elif tag == '-5':
            # -5 strand_id radius mass num_patches [pid0 pid1 ...] [neigh spr ...]
            num_p = int(parts[4])
            pids  = [int(parts[5 + k]) for k in range(num_p)]
            # Filter inactive (color 100) patches for type inference
            active_colors = [patch_defs[p].color for p in pids
                             if p in patch_defs and patch_defs[p].color != 100]
            ptype = _infer_type_psp2(active_colors)
            particles.append(ParticleData(idx=particle_idx, ptype=ptype,
                                          patch_ids=pids, conf_idx=particle_idx))
            particle_idx += 1

        elif tag == '-6':
            # Center bead: no patches
            particles.append(ParticleData(idx=particle_idx, ptype=-1,
                                          patch_ids=[], conf_idx=particle_idx))
            particle_idx += 1

    return particles, patch_defs


def _infer_type_psp2(active_colors: List[int]) -> int:
    """Guess particle type from PSP2 active colour set."""
    if not active_colors:
        return -1
    # sat24 colour ranges: ±21–32; PSP2 pyrochlore: ±10–15 / ±20–25
    pos = [c for c in active_colors if c > 0]
    neg = [c for c in active_colors if c < 0]
    if pos:
        mn = min(pos)
        if 10 <= mn <= 15:  return 0
        if 20 <= mn <= 25:  return 1
        if 21 <= mn <= 26:  return 0   # sat24 type 0
        if 27 <= mn <= 30:  return 1   # sat24 type 1
    if neg:
        mx = max(neg)   # least negative
        if -15 <= mx <= -10: return 2
        if -25 <= mx <= -20: return 3
        if -24 <= mx <= -21: return 2  # sat24 type 2
        if -32 <= mx <= -27: return 3  # sat24 type 3
    return 0

# ---------------------------------------------------------------------------
# Configuration parser
# ---------------------------------------------------------------------------

def parse_conf(dat_file: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Parse an oxDNA .dat configuration file.

    Returns: positions (N,3), a1_vecs (N,3), a3_vecs (N,3), box (3,)

    The frame convention (right-handed):
      a2 = cross(a3, a1)
      world_vec = px*a1 + py*a2 + pz*a3
    """
    positions, a1_vecs, a3_vecs = [], [], []
    box = np.array([1., 1., 1.])

    with open(dat_file) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith('t'):
                continue
            if line.startswith('b'):
                vals = line.split('=')[1].split()
                box = np.array([float(v) for v in vals[:3]])
                continue
            if line.startswith('E'):
                continue
            parts = line.split()
            if len(parts) >= 9:
                positions.append([float(parts[0]), float(parts[1]), float(parts[2])])
                a1_vecs.append( [float(parts[3]), float(parts[4]), float(parts[5])])
                a3_vecs.append( [float(parts[6]), float(parts[7]), float(parts[8])])

    return (np.array(positions), np.array(a1_vecs),
            np.array(a3_vecs),  box)

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _world_patch(pos: np.ndarray, a1: np.ndarray, a3: np.ndarray,
                 body_pos: np.ndarray) -> np.ndarray:
    """Transform body-frame patch displacement to world frame."""
    a2 = np.cross(a3, a1)
    return pos + body_pos[0]*a1 + body_pos[1]*a2 + body_pos[2]*a3


def _world_a1(a1_particle: np.ndarray, a3_particle: np.ndarray,
              a1_patch_body: np.ndarray) -> np.ndarray:
    """Transform patch body-frame a1 axis to world frame."""
    a2_particle = np.cross(a3_particle, a1_particle)
    return (a1_patch_body[0]*a1_particle
          + a1_patch_body[1]*a2_particle
          + a1_patch_body[2]*a3_particle)


def _min_image(dr: np.ndarray, box: np.ndarray) -> np.ndarray:
    return dr - box * np.round(dr / box)

# ---------------------------------------------------------------------------
# Bond detection
# ---------------------------------------------------------------------------

def find_bonds(particles:  List[ParticleData],
               patch_defs: Dict[int, PatchDef],
               positions:  np.ndarray,
               a1_vecs:    np.ndarray,
               a3_vecs:    np.ndarray,
               box:        np.ndarray,
               cutoff:     float,
               mode:       str = 'distance',
               cos_threshold: float = 0.85) -> List[Bond]:
    """
    Detect patch-patch bonds.

    mode='distance'    : require colour complementarity + patch-centre distance < cutoff
    mode='orientation' : additionally require patch-direction cosine alignment

    cos_threshold   : minimum cos(angle) between patch-offset unit vector and bond
                      direction (used only in orientation mode, default cos(32°)≈0.85)

    Returns a list of Bond objects, one per detected bond.
    """
    N = len(particles)

    # Pre-compute world-frame patch centres for every particle
    # wp[i][k] = world position of particle i's k-th patch
    wp: List[List[np.ndarray]] = []
    for i, p in enumerate(particles):
        row = []
        for pid in p.patch_ids:
            pd = patch_defs.get(pid)
            if pd is None:
                row.append(positions[i].copy())
            else:
                row.append(_world_patch(positions[i], a1_vecs[i], a3_vecs[i], pd.pos))
        wp.append(row)

    # Pre-compute world-frame patch a1 axes (needed for orientation mode)
    wa1: List[List[np.ndarray]] = []
    if mode == 'orientation':
        for i, p in enumerate(particles):
            row = []
            for pid in p.patch_ids:
                pd = patch_defs.get(pid)
                if pd is None:
                    row.append(a1_vecs[i].copy())
                else:
                    row.append(_world_a1(a1_vecs[i], a3_vecs[i], pd.a1))
            wa1.append(row)

    bonds: List[Bond] = []

    for i in range(N):
        pi_pids = particles[i].patch_ids
        for j in range(i + 1, N):
            # Early exit: if COM distance is too large no patches can be close
            dr_com = _min_image(positions[j] - positions[i], box)
            if np.linalg.norm(dr_com) > 4.0 + cutoff:
                continue

            pj_pids = particles[j].patch_ids

            for ki, pid_i in enumerate(pi_pids):
                pd_i = patch_defs.get(pid_i)
                if pd_i is None or pd_i.color == 100:
                    continue

                for kj, pid_j in enumerate(pj_pids):
                    pd_j = patch_defs.get(pid_j)
                    if pd_j is None or pd_j.color == 100:
                        continue
                    # PHB uses a modulo-500 complementarity scheme:
                    # color 22 binds -22 (standard) but also 522 binds -22 because
                    # abs(522) % 500 == abs(22) % 500 == 22 with opposite signs.
                    # This covers both the sat24 pure case (c+(-c)=0) and the
                    # mixed PHB case (522/-22, 524/-24, etc.).
                    ci, cj = pd_i.color, pd_j.color
                    if not (abs(ci) % 500 == abs(cj) % 500
                            and ci * cj < 0):
                        continue

                    # Distance check
                    dr_patch = _min_image(wp[j][kj] - wp[i][ki], box)
                    dist = float(np.linalg.norm(dr_patch))
                    if dist >= cutoff:
                        continue

                    cos_i = cos_j = 1.0

                    if mode == 'orientation':
                        # Bond unit vector (from i toward j, using COM positions)
                        r_hat = dr_com / (np.linalg.norm(dr_com) + 1e-30)

                        # Patch offset unit vector on each particle
                        off_i = wp[i][ki] - positions[i]
                        off_j = wp[j][kj] - positions[j]
                        n_off_i = np.linalg.norm(off_i)
                        n_off_j = np.linalg.norm(off_j)

                        if n_off_i > 1e-12 and n_off_j > 1e-12:
                            ph_i = off_i / n_off_i
                            ph_j = off_j / n_off_j
                            cos_i = float(np.dot(ph_i,  r_hat))
                            cos_j = float(np.dot(ph_j, -r_hat))
                        else:
                            # Fallback: use patch a1 axis
                            cos_i = float(np.dot(wa1[i][ki],  r_hat))
                            cos_j = float(np.dot(wa1[j][kj], -r_hat))

                        if cos_i < cos_threshold or cos_j < cos_threshold:
                            continue

                    bonds.append(Bond(
                        i=i, j=j, pi=pid_i, pj=pid_j,
                        color=abs(pd_i.color),
                        dist=dist, cos_i=cos_i, cos_j=cos_j,
                        intended=True))

    return bonds

# ---------------------------------------------------------------------------
# Graph / cluster analysis
# ---------------------------------------------------------------------------

def find_clusters(bonds: List[Bond], N: int) -> List[List[int]]:
    """Union-Find connected components; returns lists sorted by size (largest first)."""
    parent = list(range(N))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for b in bonds:
        union(b.i, b.j)

    groups: Dict[int, List[int]] = defaultdict(list)
    for i in range(N):
        groups[find(i)].append(i)
    return sorted(groups.values(), key=len, reverse=True)


def _bfs_shells(cluster_set: Set[int],
                adjacency: Dict[int, List[int]],
                seed: int) -> List[int]:
    """BFS from seed; returns list of per-shell particle counts."""
    visited = {seed}
    frontier = [seed]
    shells = [1]
    while frontier:
        nxt = []
        for node in frontier:
            for nb in adjacency.get(node, []):
                if nb in cluster_set and nb not in visited:
                    visited.add(nb)
                    nxt.append(nb)
        if not nxt:
            break
        shells.append(len(nxt))
        frontier = nxt
    return shells


def _build_expected_bonds(particles: List[ParticleData],
                           patch_defs: Dict[int, PatchDef]
                           ) -> Dict[int, Dict[int, int]]:
    """
    Auto-detect expected per-type partner-type bond counts from the topology.

    Returns {ptype: {partner_ptype: expected_count}}.
    """
    # colour → set of particle types that carry it
    color_to_types: Dict[int, Set[int]] = defaultdict(set)
    for p in particles:
        for pid in p.patch_ids:
            pd = patch_defs.get(pid)
            if pd and pd.color != 100:
                color_to_types[pd.color].add(p.ptype)

    # For each type, count expected bonds to each partner type
    expected: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    seen_ptypes: Set[int] = set()
    for p in particles:
        if p.ptype in seen_ptypes:
            continue
        seen_ptypes.add(p.ptype)
        for pid in p.patch_ids:
            pd = patch_defs.get(pid)
            if pd is None or pd.color == 100:
                continue
            partners = color_to_types.get(-pd.color, set())
            for partner_type in partners:
                expected[p.ptype][partner_type] += 1

    return {k: dict(v) for k, v in expected.items()}


def analyze_cluster(cluster_ids:     List[int],
                    bonds:           List[Bond],
                    particles:       List[ParticleData],
                    patch_defs:      Dict[int, PatchDef],
                    expected_valence: int = 6,
                    cid:             int = 0) -> ClusterResult:
    """Full analysis for one connected component."""
    cluster_set = set(cluster_ids)
    n = len(cluster_ids)
    cbonds = [b for b in bonds if b.i in cluster_set and b.j in cluster_set]

    # Valence map
    valence: Dict[int, int] = defaultdict(int)
    for b in cbonds:
        valence[b.i] += 1
        valence[b.j] += 1

    # Type distribution
    type_counts: Dict[int, int] = defaultdict(int)
    for pid in cluster_ids:
        t = particles[pid].ptype
        if t >= 0:
            type_counts[t] += 1

    avg_val = (sum(valence[pid] for pid in cluster_ids) / n) if n > 0 else 0.0
    frac = sum(1 for pid in cluster_ids
               if valence[pid] == expected_valence) / n if n > 0 else 0.0

    # Adjacency for BFS
    adj: Dict[int, List[int]] = defaultdict(list)
    for b in cbonds:
        adj[b.i].append(b.j)
        adj[b.j].append(b.i)

    # Seed = particle with highest valence
    seed = max(cluster_ids, key=lambda p: valence[p])
    shells = _bfs_shells(cluster_set, adj, seed)

    # Non-intended: valence overflow or same-type bond
    overflow = {pid for pid in cluster_ids if valence[pid] > expected_valence}
    same_type_bonds = {(min(b.i, b.j), max(b.i, b.j))
                       for b in cbonds if particles[b.i].ptype == particles[b.j].ptype}
    non_intended: List[Bond] = []
    marked = set()
    for b in cbonds:
        pair = (min(b.i, b.j), max(b.i, b.j))
        is_bad = (b.i in overflow or b.j in overflow or pair in same_type_bonds)
        if is_bad and pair not in marked:
            marked.add(pair)
            non_intended.append(Bond(b.i, b.j, b.pi, b.pj, b.color,
                                     b.dist, b.cos_i, b.cos_j, intended=False))

    # Crystal-like heuristics
    notes: List[str] = []
    is_crystal = True
    n_types = len([t for t in type_counts if t >= 0])

    if n_types < 4:
        is_crystal = False
        notes.append(f"Only {n_types}/4 particle types present")
    if avg_val < 3.0:
        is_crystal = False
        notes.append(f"Avg valence {avg_val:.2f} < 3.0 — too sparse")
    if frac < 0.3:
        is_crystal = False
        notes.append(f"Only {frac:.1%} particles have full valence ({expected_valence})")
    if n_types == 4:
        vals = list(type_counts.values())
        if max(vals) > 2 * min(vals):
            is_crystal = False
            notes.append(f"Unbalanced type counts {dict(sorted(type_counts.items()))}")
    if len(non_intended) > 0:
        notes.append(f"{len(non_intended)} non-intended bonds "
                     f"(overflow or same-type)")
    if is_crystal and not notes:
        notes.append("Crystal-like structure detected")

    return ClusterResult(
        cid=cid,
        particle_ids=cluster_ids,
        bonds=cbonds,
        avg_valence=avg_val,
        full_valence_fraction=frac,
        type_counts=dict(type_counts),
        is_crystal_like=is_crystal,
        shell_sizes=shells,
        n_unit_cells=n / 4.0,
        non_intended_bonds=non_intended,
        notes=notes,
    )

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results:      List[ClusterResult],
                 particles:    List[ParticleData],
                 expected_val: int,
                 min_size:     int,
                 mode:         str,
                 cos_thresh:   float,
                 verbose:      bool) -> None:
    N = len(particles)
    total_bonds = sum(len(cr.bonds) for cr in results)
    sig = [cr for cr in results if len(cr.particle_ids) >= min_size]
    crystals = [cr for cr in sig if cr.is_crystal_like]
    n_crystallized = sum(len(cr.particle_ids) for cr in crystals)
    crystallization_pct = 100.0 * n_crystallized / N if N > 0 else 0.0
    n_assembled = sum(len(cr.particle_ids) for cr in sig)
    assembled_pct = 100.0 * n_assembled / N if N > 0 else 0.0

    sep = "=" * 72
    thin = "─" * 72
    print(sep)
    print("  PYROCHLORE CRYSTAL ANALYSIS")
    print(sep)
    print(f"  Binding mode     : {mode}"
          + (f" (cos ≥ {cos_thresh:.3f})" if mode == 'orientation' else ""))
    print(f"  Total particles  : {N}")
    print(f"  Total bonds      : {total_bonds}")
    print(f"  Components       : {len(results)}")
    print(f"  Crystal clusters : {len(crystals)}  "
          f"(of {len(sig)} clusters ≥ {min_size} particles)")
    print(f"  Crystallization  : {crystallization_pct:.2f}%  "
          f"({n_crystallized}/{N} particles in crystal-like clusters)")
    print(f"  Assembled        : {assembled_pct:.2f}%  "
          f"({n_assembled}/{N} particles in any bonded cluster ≥ {min_size}, "
          f"strict or not)")
    print()

    if not sig:
        print(f"  No clusters with ≥ {min_size} particles found.")
        print(sep)
        return

    for cr in sig:
        label = "[ CRYSTAL ]" if cr.is_crystal_like else "[AGGREGATE]"
        print(thin)
        print(f"  Cluster {cr.cid:>3}  {label}   size={len(cr.particle_ids)}")
        print(thin)

        pids = cr.particle_ids
        pid_str = str(pids[:25]) + ("..." if len(pids) > 25 else "")
        print(f"  Particle IDs   : {pid_str}")
        print(f"  Type counts    : {dict(sorted(cr.type_counts.items()))}")
        print(f"  Bonds          : {len(cr.bonds)}")
        print(f"  Unit cells (~) : {cr.n_unit_cells:.1f}  (particles / 4)")
        print(f"  Avg valence    : {cr.avg_valence:.2f} / {expected_val}")
        print(f"  Full-val frac  : {cr.full_valence_fraction:.1%}")

        shells_str = str(cr.shell_sizes[:12])
        if len(cr.shell_sizes) > 12:
            shells_str += f"...  ({len(cr.shell_sizes)} shells total)"
        print(f"  Shells (BFS)   : {shells_str}")
        print(f"  Total shells   : {len(cr.shell_sizes)}")
        print(f"  Non-intended   : {len(cr.non_intended_bonds)}")

        for note in cr.notes:
            print(f"  Note  : {note}")

        if verbose:
            print(f"  {'─'*60}")
            print("  Bond list (i → j, colour, dist, cos_i, cos_j):")
            for b in cr.bonds:
                ti = particles[b.i].ptype
                tj = particles[b.j].ptype
                flag = " [NON-INTENDED]" if not b.intended else ""
                print(f"    p{b.i}(t{ti}) — p{b.j}(t{tj})  "
                      f"col±{b.color:3d}  d={b.dist:.4f}"
                      f"  cosI={b.cos_i:.3f}  cosJ={b.cos_j:.3f}{flag}")

    iso = [cr for cr in results if len(cr.particle_ids) < min_size]
    if iso:
        iso_n = sum(len(cr.particle_ids) for cr in iso)
        print(thin)
        print(f"  Isolated/small : {len(iso)} groups, {iso_n} particles")
    print(sep)

# ---------------------------------------------------------------------------
# MGL output  (cogli2-compatible sphere/cylinder format)
# ---------------------------------------------------------------------------

# Kept at moderate luminance (channel sum well under 2.0) on purpose: the
# ppview renderer's lighting blows bright/near-white colours (e.g. pure
# yellow (1.0, 0.88, 0.1)) out to indistinguishable white, so every colour
# here is deliberately mid-saturated rather than pastel/bright.
_CLUSTER_COLORS = [
    (0.15, 0.45, 0.85),   # blue
    (0.85, 0.35, 0.05),   # orange
    (0.15, 0.60, 0.20),   # green
    (0.70, 0.10, 0.65),   # magenta
    (0.80, 0.60, 0.05),   # gold
    (0.05, 0.60, 0.60),   # teal
    (0.45, 0.20, 0.75),   # purple
    (0.75, 0.30, 0.40),   # rose
]
_ISOLATED_COL   = (0.45, 0.45, 0.45)
_NON_INT_COL    = (0.85, 0.10, 0.10)


def _wrap_positions_by_cluster(positions: np.ndarray,
                               box: np.ndarray,
                               results: List[ClusterResult]) -> np.ndarray:
    """
    oxDNA .dat files store unwrapped absolute coordinates: after a long
    trajectory, particles can sit many box-lengths from the origin even
    though periodic boundary conditions make them adjacent to particles
    "on the other side". Naively plotting raw positions scatters bonded
    clusters across a huge span with only a few particles landing near
    the visible box.

    This rebuilds a display-friendly coordinate set: each connected
    component is walked bond-by-bond from an arbitrary anchor (wrapped
    into the primary cell), placing every other member via minimum-image
    displacement from its already-placed neighbour, so the whole cluster
    stays spatially contiguous. Anchors (and true singletons) are simply
    wrapped into [0, box).
    """
    wrapped = positions.copy()
    for cr in results:
        ids = cr.particle_ids
        anchor = ids[0]
        wrapped[anchor] = positions[anchor] - box * np.floor(positions[anchor] / box)
        if len(ids) == 1:
            continue

        adj: Dict[int, List[int]] = defaultdict(list)
        for b in cr.bonds:
            adj[b.i].append(b.j)
            adj[b.j].append(b.i)

        visited = {anchor}
        queue = deque([anchor])
        while queue:
            cur = queue.popleft()
            for nb in adj.get(cur, []):
                if nb in visited:
                    continue
                visited.add(nb)
                dr = positions[nb] - positions[cur]
                dr = dr - box * np.round(dr / box)  # minimum-image step
                wrapped[nb] = wrapped[cur] + dr
                queue.append(nb)

        for i in ids:
            if i not in visited:
                wrapped[i] = positions[i] - box * np.floor(positions[i] / box)
    return wrapped


def _declutter_clusters(positions: np.ndarray,
                        results:   List[ClusterResult],
                        min_size:  int,
                        render_radius: float,
                        margin:    float = 2.5) -> np.ndarray:
    """
    Push each significant cluster's members outward from the cluster's own
    centroid so neighbouring spheres clear the fixed render radius.

    This dataset's clusters can be collapsed/interpenetrating (PSP2 shells
    with a near-zero steric core, or genuinely jammed aggregates) with real
    nearest-neighbour spacing far below the ~0.5 render radius ppview uses
    for every sphere. Rendered at true scale that reads as one solid grey
    mass — a real bug report against ppview (per-instance colour silently
    fails to apply when many heavily-overlapping instances share a colour;
    confirmed via isolated reproduction, root cause not yet found in
    ppview's InstancedMesh color pipeline) compounds this into fully
    invisible cluster colouring. Exploding cluster geometry outward (while
    leaving true singletons/free particles untouched) sidesteps both
    problems and, as a side effect, makes cluster shape/connectivity far
    easier to read than the collapsed-blob true-scale view would be.
    """
    exploded = positions.copy()
    for cr in results:
        ids = cr.particle_ids
        if len(ids) < min_size:
            continue
        cluster_pos = positions[ids]
        # Estimate a per-cluster explosion factor from its own nearest-neighbour
        # spacing so tightly-collapsed clusters get pushed apart more than
        # already-loose ones.
        dists = []
        for a in range(len(ids)):
            d = np.linalg.norm(cluster_pos - cluster_pos[a], axis=1)
            d[a] = np.inf
            dists.append(d.min())
        nn_min = max(min(dists), 1e-6)
        factor = max(1.0, margin * 2 * render_radius / nn_min)
        centroid = cluster_pos.mean(axis=0)
        for i in ids:
            exploded[i] = centroid + (positions[i] - centroid) * factor
    return exploded


def write_mgl(out_path:    str,
              results:     List[ClusterResult],
              particles:   List[ParticleData],
              positions:   np.ndarray,
              box:         np.ndarray,
              min_size:    int = 4,
              declutter:   bool = True) -> None:
    """
    Write a cogli2-compatible MGL file.

    Format:
      .Box:Lx,Ly,Lz
      x y z @radius C[R,G,B]     — sphere
      C x1 y1 z1 x2 y2 z2 0.05 C[R,G,B] — cylinder (bond)

    Crystal clusters get distinct colours; isolated particles are grey.
    Non-intended bonds are drawn in red.

    Positions are re-wrapped per connected component (see
    _wrap_positions_by_cluster) before writing, since oxDNA .dat files store
    unwrapped absolute coordinates that would otherwise scatter a bonded
    cluster across many box-lengths in the output file. If declutter=True
    (default), significant clusters are then exploded outward from their
    own centroid (see _declutter_clusters) so overlapping spheres separate
    into a legible shape instead of a solid blob.
    """
    positions = _wrap_positions_by_cluster(positions, box, results)
    if declutter:
        positions = _declutter_clusters(positions, results, min_size, render_radius=0.5)

    # Assign colour per particle
    pcolor: Dict[int, Tuple] = {}
    crystal_idx = 0
    non_int_pairs: Set[Tuple[int, int]] = set()

    n_clusters_colored = 0
    for cr in results:
        # Every cluster at/above min_size gets its own colour, cycling through
        # the palette — this used to only apply to strict is_crystal_like
        # clusters, so on datasets with zero "true" crystals (common here)
        # every bonded aggregate collapsed onto one shared colour. Below
        # min_size (in particular true singletons / free particles) stays grey.
        if len(cr.particle_ids) >= min_size:
            col = _CLUSTER_COLORS[n_clusters_colored % len(_CLUSTER_COLORS)]
            n_clusters_colored += 1
        else:
            col = _ISOLATED_COL
        for pid in cr.particle_ids:
            pcolor[pid] = col
        for b in cr.non_intended_bonds:
            non_int_pairs.add((min(b.i, b.j), max(b.i, b.j)))
    crystal_idx = n_clusters_colored

    N = len(particles)
    r_sphere = 0.5   # visual radius

    with open(out_path, 'w') as f:
        # ppview/cogli2 only recognise a frame boundary via a line starting
        # with ".Box:" (comma-separated dims, no spaces) — anything else
        # (e.g. a bare N-count line, or a ".> t=0" header) is silently NOT
        # treated as a frame header, which was previously causing every
        # particle to fall back to default scheme colouring instead of the
        # explicit per-particle C[...] colour written below. No N-count line
        # is written; particle lines simply follow the .Box: line directly.
        f.write(f"# Coloured clusters (>= min_size, one distinct colour each): {crystal_idx}\n")
        f.write(f"# Non-intended bonds: {len(non_int_pairs)}\n")
        f.write(f".Box:{box[0]:.6f},{box[1]:.6f},{box[2]:.6f}\n")

        # Spheres
        for i in range(N):
            col = pcolor.get(i, _ISOLATED_COL)
            x, y, z = positions[i]
            R, G, B = col
            f.write(f"{x:.6f} {y:.6f} {z:.6f} @{r_sphere:.3f} C[{R:.3f},{G:.3f},{B:.3f}]\n")

        # Bond cylinders
        for cr in results:
            if len(cr.particle_ids) < min_size:
                continue
            col = pcolor.get(cr.particle_ids[0], _ISOLATED_COL)
            for b in cr.bonds:
                pair = (min(b.i, b.j), max(b.i, b.j))
                if pair in non_int_pairs:
                    bR, bG, bB = _NON_INT_COL
                    tag = "  # NON-INTENDED"
                else:
                    bR, bG, bB = col
                    tag = ""
                xi, yi, zi = positions[b.i]
                dr = _min_image(positions[b.j] - positions[b.i], box)
                xj, yj, zj = positions[b.i] + dr
                f.write(f"C {xi:.6f} {yi:.6f} {zi:.6f} "
                        f"{xj:.6f} {yj:.6f} {zj:.6f} "
                        f"0.06 C[{bR:.3f},{bG:.3f},{bB:.3f}]{tag}\n")

    print(f"  MGL written → {out_path}  "
          f"({crystal_idx} coloured cluster(s), {len(non_int_pairs)} non-intended bonds)")

# ---------------------------------------------------------------------------
# JSON summary
# ---------------------------------------------------------------------------

def write_json(out_path: str,
               results:  List[ClusterResult],
               N:        int,
               box:      np.ndarray,
               total_bonds: int,
               min_size: int) -> None:
    n_crystallized = sum(len(cr.particle_ids) for cr in results
                        if cr.is_crystal_like and len(cr.particle_ids) >= min_size)
    n_assembled = sum(len(cr.particle_ids) for cr in results
                      if len(cr.particle_ids) >= min_size)
    doc = {
        "n_particles": N,
        "n_bonds":     total_bonds,
        "box":         box.tolist(),
        "n_crystallized_particles": n_crystallized,
        "crystallization_percentage": round(100.0 * n_crystallized / N, 4) if N > 0 else 0.0,
        "n_assembled_particles": n_assembled,
        "assembled_percentage": round(100.0 * n_assembled / N, 4) if N > 0 else 0.0,
        "clusters": []
    }
    for cr in results:
        if len(cr.particle_ids) < min_size:
            continue
        doc["clusters"].append({
            "id":                    cr.cid,
            "size":                  len(cr.particle_ids),
            "particle_ids":          cr.particle_ids,
            "is_crystal":            cr.is_crystal_like,
            "avg_valence":           round(cr.avg_valence, 4),
            "full_valence_fraction": round(cr.full_valence_fraction, 4),
            "n_unit_cells":          cr.n_unit_cells,
            "shell_sizes":           cr.shell_sizes,
            "type_counts":           cr.type_counts,
            "n_non_intended":        len(cr.non_intended_bonds),
            "notes":                 cr.notes,
        })
    with open(out_path, 'w') as f:
        json.dump(doc, f, indent=2)
    print(f"  JSON written  → {out_path}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pyrochlore crystal analysis for patchy-particle simulations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)

    # Topology
    ap.add_argument('--format', choices=['phb', 'psi', 'psp2'], default='phb',
                    help="Topology format (default: phb)")
    ap.add_argument('--top', required=True,
                    help="Topology file (.top / .phb / .psp)")
    ap.add_argument('--conf', required=True,
                    help="Configuration file (.dat)")
    ap.add_argument('--particles', default='CRYSTAL.particles.txt',
                    help="[psi] Particle-type definitions file")
    ap.add_argument('--patches', default='sat24.patches.txt',
                    help="[psi] Patch definitions file")

    # Binding detection
    ap.add_argument('--mode', choices=['distance', 'orientation'], default='distance',
                    help="Binding detection mode (default: distance)")
    ap.add_argument('--cutoff', type=float, default=0.20,
                    help="Patch-centre-to-patch-centre distance cutoff "
                         "(default 0.20; use ~0.35 for PHB radius-1 patches)")
    ap.add_argument('--cos-threshold', type=float, default=0.85,
                    help="[orientation mode] Minimum patch-direction cosine "
                         "(default 0.85 ≈ cos 32°)")

    # Crystal criteria
    ap.add_argument('--expected-valence', type=int, default=6,
                    help="Expected bonds per particle in a perfect crystal (default 6)")
    ap.add_argument('--min-cluster', type=int, default=4,
                    help="Minimum cluster size to report (default 4)")

    # Output
    ap.add_argument('--mgl', action='store_true',
                    help="Generate colour MGL file")
    ap.add_argument('--mgl-out', default='crystal_clusters.mgl',
                    help="MGL output path (default crystal_clusters.mgl)")
    ap.add_argument('--json-out', default=None,
                    help="Write JSON summary to file")
    ap.add_argument('--verbose', action='store_true',
                    help="Print bond-by-bond details")

    args = ap.parse_args()

    # ---- Parse topology ----
    print(f"[1/4] Parsing topology ({args.format}): {args.top}")
    if args.format == 'phb':
        particles, patch_defs = parse_phb_top(args.top)
    elif args.format == 'psi':
        particles, patch_defs = parse_psi_top(args.top, args.particles, args.patches)
    else:
        particles, patch_defs = parse_psp2_top(args.top)
    print(f"      {len(particles)} particles  |  {len(patch_defs)} patch definitions")

    # ---- Parse configuration ----
    print(f"[2/4] Parsing configuration: {args.conf}")
    positions_all, a1_vecs_all, a3_vecs_all, box = parse_conf(args.conf)
    print(f"      N_conf={len(positions_all)}  box={box}")

    # Use conf_idx to pull the correct positions for each patchy particle.
    # In PHB format, arm beads (-4) interleave with head beads (-3) in the conf
    # file, so we must index by each particle's stored conf_idx rather than
    # slicing positions[:N].
    conf_indices = np.array([p.conf_idx if p.conf_idx >= 0 else i
                             for i, p in enumerate(particles)])
    bad = conf_indices[conf_indices >= len(positions_all)]
    if len(bad):
        print(f"      ERROR: {len(bad)} particles have conf_idx beyond conf size "
              f"({len(positions_all)}); topology/conf mismatch")
        sys.exit(1)

    N = len(particles)
    positions = positions_all[conf_indices]
    a1_vecs   = a1_vecs_all[conf_indices]
    a3_vecs   = a3_vecs_all[conf_indices]

    n_unique_conf = len(set(conf_indices.tolist()))
    if n_unique_conf != N:
        print(f"      WARNING: only {n_unique_conf}/{N} unique conf positions mapped "
              f"(possible topology/conf mismatch)")

    # ---- Find bonds ----
    print(f"[3/4] Finding bonds (mode={args.mode}, cutoff={args.cutoff}"
          + (f", cos≥{args.cos_threshold}" if args.mode == 'orientation' else "") + ")")
    bonds = find_bonds(particles, patch_defs, positions, a1_vecs, a3_vecs,
                       box, args.cutoff, args.mode, args.cos_threshold)
    print(f"      {len(bonds)} bonds found")

    # ---- Cluster analysis ----
    print("[4/4] Analysing clusters …")
    raw_clusters = find_clusters(bonds, N)
    results: List[ClusterResult] = []
    for cid, cluster_ids in enumerate(raw_clusters):
        cr = analyze_cluster(cluster_ids, bonds, particles, patch_defs,
                             args.expected_valence, cid)
        results.append(cr)
    print(f"      {len(results)} connected components")

    # ---- Report ----
    print()
    print_report(results, particles, args.expected_valence,
                 args.min_cluster, args.mode, args.cos_threshold, args.verbose)

    # ---- Optional outputs ----
    total_bonds = len(bonds)
    if args.mgl:
        write_mgl(args.mgl_out, results, particles, positions, box, args.min_cluster)
    if args.json_out:
        write_json(args.json_out, results, N, box, total_bonds, args.min_cluster)


if __name__ == '__main__':
    main()
