import sys
sys.path.insert(0, '/home/gila/Documents/Github/ppview')
sys.path.insert(0, '/home/gila/Documents/Github/ppview/clear/scripts')
import render_phb as RP
import cluster_labels as CL
import numpy as np
from pathlib import Path
GHOST = 0.12
def tetra_members(nb):
    mem, n = set(), 0
    for a in nb:
        na = nb[a]
        for b in na:
            if b <= a: continue
            common = na & nb[b]
            for c in common:
                if c <= b: continue
                for d in common & nb[c]:
                    if d > c:
                        n += 1
                        mem.update((a, b, c, d))
    return mem, n
def main(d):
    d = Path(d)
    top = sorted(d.glob('*.phb'))[0]
    conf = d / 'last_conf.dat'
    out = d / 'final_ghost.png'
    topo = CL.load_topology(str(top))
    t, box, pos, a1, a3 = CL.load_conf(str(conf), topo['N'])
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    mem, ntet = tetra_members(res['neighbors'])
    mol = np.asarray(topo['mol'])
    mask = np.isin(mol, np.fromiter(mem, int, len(mem))) if mem else np.zeros(len(mol), bool)
    import argparse
    args = RP.build_parser().parse_args(['--top', str(top), '--conf', str(conf), '--out', str(out),
        '--width','1920','--height','1080','--scale','1','--model','ballstick',
        '--background','white','--species-colors','--quiet'])
    args.title = None; args.legend = False; args.box = False
    args.solid = mask; args.ghost_opacity = GHOST
    RP.render(args, log=lambda *a: None)
    print(f'{d} assembled={len(mem)}/{topo["n_mol"]} tet={ntet}')
main(sys.argv[1])
