#!/usr/bin/env python3
"""Time-resolved PBC-safe sampling (seek-based, phbtraj.sample_trajectory) of trajectories of the running/recent legacy runs."""
import sys, os, json, glob
sys.path.insert(0, '/scratch/sroy85/hand5_analysis')
import numpy as np
from multiprocessing import Pool
from phbtraj import Topology, sample_trajectory, DEFAULT_FRACS, structure_of_conf
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'
FR = sorted(set(DEFAULT_FRACS + [round(x, 4) for x in np.linspace(0, 0.99, 34)]))
def work(rel):
    d = f'{R}/{rel}'; out = dict(run=rel)
    try:
        top = Topology(os.path.realpath(d + '/topology.phb'))
        tr = d + '/trajectory.dat'
        fr = sample_trajectory(top, tr, FR)
        nm = len(top.cores)
        out['size'] = os.path.getsize(tr)
        out['frames'] = [dict(t=f['t'], step=f['t'], E=f['E'], largest=f['largest_cores'], n_clusters=f['n_clusters'], cryst=f['n_cryst_cores'],
                              val=f['mean_valence'], v6=f['frac_v6'], spacers=f['n_spacers'], clusters=f['clusters'][:3]) for f in fr]
        out['nmol'] = nm
    except Exception as e:
        out['error'] = repr(e)[:200]
    return out
if __name__ == '__main__':
    os.nice(15)
    rels = []
    for pat in ('preconnected_strength_scan/S*/Kb_*', 'seeding_scan/runs/*', 'window_scan/runs/*'):
        rels += [os.path.relpath(p, R) for p in sorted(glob.glob(f'{R}/{pat}')) if os.path.exists(p + '/trajectory.dat')]
    with Pool(3) as p: res = p.map(work, rels, chunksize=1)
    json.dump(res, open(f'{R}/final_report/data/legacy_timecourses.json', 'w'))
    print(len(res), sum('error' in r for r in res))
