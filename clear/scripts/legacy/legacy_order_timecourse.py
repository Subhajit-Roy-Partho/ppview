#!/usr/bin/env python3
"""Tetrahedra-per-molecule (4-species intact tetrahedra) vs steps for selected seeding_scan / window_scan / strength_scan runs."""
import sys, os, json, re
sys.path.insert(0, '/scratch/sroy85/hand5_analysis')
import numpy as np
from multiprocessing import Pool
from phbtraj import Topology, read_frame_text, spacer_graph, analyse_frame
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'
def frames(path, fracs, S_hint=None):
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        head = f.read(40 << 20)
        marks = [m.start() for m in re.finditer(rb'(^|\n)t = ', head)]
        first = marks[0] + (1 if head[marks[0]:marks[0] + 1] == b'\n' else 0); S = marks[1] + 1 - first
        for fr in fracs:
            off = 0 if fr <= 0 else min(int(fr * size), max(0, size - 2 * S))
            f.seek(off); blk = f.read(3 * S + 4096)
            m = [x.start() for x in re.finditer(rb'(^|\n)t = ', blk)]
            if off == 0: a = 0
            else:
                if not m: continue
                a = m[0] + (1 if blk[m[0]:m[0] + 1] == b'\n' else 0)
            nxt = [x for x in m if x > a + 5]
            e = nxt[0] + 1 if nxt else len(blk)
            yield blk[a:e].decode().rstrip('\n')
def tet4(top, adj):
    sp = {int(c): int(top.color[c]) for c in top.cores}; n = 0
    for a in adj:
        na = adj[a]
        for b in na:
            if b <= a: continue
            com = na & adj[b]
            for c in com:
                if c <= b: continue
                for d in com & adj[c]:
                    if d > c and len({sp[a], sp[b], sp[c], sp[d]}) == 4: n += 1
    return n
def work(rel):
    d = f'{R}/{rel}'; out = dict(run=rel, frames=[])
    try:
        top = Topology(os.path.realpath(d + '/topology.phb')); nm = len(top.cores)
        fr = [round(x, 4) for x in np.linspace(0, 0.99, 40)]
        for txt in frames(d + '/trajectory.dat', fr):
            try: t, box, E, pos, a1, a3 = read_frame_text(txt, top.N)
            except Exception: continue
            adj = spacer_graph(top, box, pos, a1, a3)
            r = analyse_frame(top, box, pos, a1, a3)
            n4 = tet4(top, adj)
            out['frames'].append(dict(t=t, largest=r['largest_cores'], tet=n4 / nm, v6=r['frac_v6'], val=r['mean_valence']))
    except Exception as e:
        out['error'] = repr(e)[:200]
    return out
if __name__ == '__main__':
    os.nice(15)
    rels = ['seeding_scan/runs/' + x for x in ['S8_T0.140','S16_T0.140','S32_T0.140','S64_T0.140','S128_T0.140','S128_T0.140_r2','S128_T0.140_r3','S128_T0.135_r1','S128_T0.145_r1','S128_T0.150','S192_T0.140_r1','S192_T0.140_r2','S256_T0.140_r1','S256_T0.140_r2']]
    rels += ['window_scan/runs/' + x for x in ['Q_T0.120_a','Q_T0.130_a','Q_T0.140_a','Q_T0.140_b','AS_a','AF_a','H_a','H_b']]
    rels += ['preconnected_strength_scan/S50/Kb_300_T_0.100','preconnected_strength_scan/S100/Kb_300_T_0.100','preconnected_strength_scan/S200/Kb_300_T_0.100']
    with Pool(3) as p: res = p.map(work, rels, chunksize=1)
    json.dump(res, open(f'{R}/final_report/data/legacy_order_timecourse.json', 'w'))
    print(len(res), sum('error' in r for r in res))
