#!/usr/bin/env python3
"""Fresh PBC-safe re-analysis (phbtraj.py, cutoff 0.3) of final_conf.dat for every legacy-system run.
Read-only on simulation dirs. Output: ../data/legacy_fresh_analysis.json"""
import sys, os, json, time, glob
sys.path.insert(0, '/scratch/sroy85/hand5_analysis')
import numpy as np
from multiprocessing import Pool
from phbtraj import Topology, analyse_conf, structure_of_conf
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'
INV = '/tmp/claude-2438191/-scratch-sroy85-Github-dna/a7f7a000-064e-4224-9ff5-fe91f96309bd/scratchpad/inv.json'
_top = {}
def work(rel):
    d = f'{R}/{rel}'
    out = dict(run=rel)
    try:
        tp = os.path.realpath(d + '/topology.phb')
        if tp not in _top: _top[tp] = Topology(tp)
        top = _top[tp]
        conf = d + '/final_conf.dat'
        out['conf_mtime'] = os.path.getmtime(conf)
        for attempt in range(3):
            try:
                r = analyse_conf(top, conf); s = structure_of_conf(top, conf); break
            except Exception as e:
                time.sleep(2); err = e
        else:
            raise err
        nm = len(top.cores)
        out.update(topology=tp, nmol=nm, N=top.N, t_conf=r['t'], E=r['E'], box=r['box'][0],
            largest_cores=r['largest_cores'], lc_frac=r['largest_cores'] / nm, n_cryst_cores=r['n_cryst_cores'],
            n_clusters=r['n_clusters'], clusters=r['clusters'][:5], n_spacers=r['n_spacers'],
            mean_valence=r['mean_valence'], frac_v6=r['frac_v6'], valence_hist=r['valence_hist'],
            anchored_arms=r['anchored_arms'], n_tetra4=s['n_tetra_4species'], tetra_per_mol=s['n_tetra_4species'] / nm,
            clustering=s['clustering'], geo_frac6=s['geo_frac6'], nn_median=s['nn_median'])
    except Exception as e:
        out['error'] = repr(e)[:200]
    return out
if __name__ == '__main__':
    os.nice(10)
    inv = json.load(open(INV))
    rels = [r['run'] for r in inv if r['has_final']]
    with Pool(4) as p:
        res = p.map(work, rels, chunksize=1)
    json.dump(res, open(f'{R}/final_report/data/legacy_fresh_analysis.json', 'w'))
    print(len(res), sum('error' in r for r in res), 'errors')
