#!/usr/bin/env python3
"""Run the ORIGINAL analyze_phb_crystal.py (no PBC wrapping of stored coords) on the final_conf of dilute-start sweeps, to
quantify the artefact against the PBC-safe analysis in data/legacy_fresh_analysis.json."""
import json, os, subprocess, re
from multiprocessing import Pool
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'
fresh = json.load(open(f'{R}/final_report/data/legacy_fresh_analysis.json'))
runs = [r for r in fresh if r['run'].split('/')[0] in ('seeded_sweep','decisive_equalK','preconnected_seed_sweep','preconnected_K300_large','preconnected_strength_scan')]
def work(r):
    d = f"{R}/{r['run']}"
    try:
        out = subprocess.run(['python3', f'{R}/analyze_phb_crystal.py', '--top', os.path.realpath(d + '/topology.phb'), '--conf', d + '/final_conf.dat', '--json'],
                             capture_output=True, text=True, timeout=600).stdout
        j = json.loads(out[out.index('{\n  "n_mol"'):])
        # extent of stored coordinates in box lengths
        with open(d + '/final_conf.dat') as f:
            f.readline(); box = float(f.readline().split('=')[1].split()[0]); f.readline()
            import numpy as np
            a = np.loadtxt(f, usecols=(0,1,2), max_rows=r['N'])
        ext = float(((a.max(0) - a.min(0)) / box).max())
        return dict(run=r['run'], old_lc_frac=j['largest_cluster_fraction'], old_largest=j['largest_cluster'], old_nbonds=j['n_bonds_inter'], coord_extent_boxes=ext, pbc_lc_frac=r['lc_frac'])
    except Exception as e:
        return dict(run=r['run'], error=repr(e)[:200])
if __name__ == '__main__':
    os.nice(10)
    with Pool(4) as p: res = p.map(work, runs, chunksize=1)
    json.dump(res, open(f'{R}/final_report/data/legacy_oldscript_vs_pbc.json', 'w'))
    print(len(res), sum('error' in x for x in res))
