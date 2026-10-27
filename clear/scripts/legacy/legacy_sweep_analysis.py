#!/usr/bin/env python3
"""PBC-safe analysis of large_crystal/sweep (old alpha x Ka x Kb x strength sweep, 63,488-particle pre-formed crystal)."""
import sys, os, json, glob, re, subprocess
sys.path.insert(0, '/scratch/sroy85/hand5_analysis')
from multiprocessing import Pool
from phbtraj import Topology, analyse_conf, structure_of_conf
S = '/scratch/sroy85/Github/dna/large_crystal/sweep'
def work(d):
    name = os.path.basename(d); m = re.match(r'alpha_([\d.]+)_Ka_([\d.]+)_Kb_([\d.]+)_str_([\d.]+)', name)
    out = dict(run=name, alpha=float(m[1]), Ka=float(m[2]), Kb=float(m[3]), strength=float(m[4]))
    try:
        ef = d + '/energy.dat'
        nl = int(subprocess.check_output(['wc', '-l', ef], text=True).split()[0]) if os.path.exists(ef) else 0
        out['energy_lines'] = nl
        if nl:
            l = subprocess.check_output(['tail', '-n', '1', ef], text=True).split()
            out['t_last'] = float(l[0]); out['U_last'] = float(l[1])
            f = subprocess.check_output(['head', '-n', '1', ef], text=True).split()
            out['U_first'] = float(f[1])
        conf = d + '/last_conf.dat'
        if nl and os.path.exists(conf) and os.path.getsize(conf) > 1e6:
            top = Topology(d + '/input.phb')
            r = analyse_conf(top, conf); s = structure_of_conf(top, conf); nm = len(top.cores)
            out.update(nmol=nm, t_conf=r['t'], largest_cores=r['largest_cores'], lc_frac=r['largest_cores'] / nm,
                       n_clusters=r['n_clusters'], n_spacers=r['n_spacers'], mean_valence=r['mean_valence'],
                       frac_v6=r['frac_v6'], tetra_per_mol=s['n_tetra_4species'] / nm, clustering=s['clustering'])
    except Exception as e:
        out['error'] = repr(e)[:200]
    return out
if __name__ == '__main__':
    os.nice(10)
    ds = sorted(glob.glob(S + '/alpha_*'))
    with Pool(4) as p: res = p.map(work, ds, chunksize=1)
    json.dump(res, open('/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data/legacy_sweep_analysis.json', 'w'))
    print(len(res), sum('error' in r for r in res))
