#!/usr/bin/env python3
"""param_ka: inventory + PBC-safe start/end analysis of large_crystal/sweep (old alpha x Ka x Kb x strength sweep).
Start = per-dir mc_relaxed.dat (MD input), end = last_conf.dat. Uses final_report/cluster_labels.py (PBC-safe).
Read-only on the sweep dir. Output: final_report/data/param_ka_endpoints.json"""
import sys, os, re, json, glob
import numpy as np
sys.path.insert(0, '/scratch/sroy85/Github/dna/large_crystal/hand5/final_report')
import cluster_labels as cl
R = '/scratch/sroy85/Github/dna/large_crystal/sweep'
OUT = '/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data/param_ka_endpoints.json'

def metrics(topo, conf_path, cut):
    r = cl.analyze_conf(topo, conf_path, cutoff=cut)
    s = cl.summarize(topo, r, cut)
    nm = topo['n_mol']
    return dict(t=s['time'], n_bonds=s['n_patch_bonds'], n_pairs=s['n_molecule_pairs_bonded'], lc=s['largest_cluster_fraction'],
                n_clusters_ge2=s['n_clusters_ge2'], n_singletons=s['n_singletons'], valence=s['mean_valence'],
                f_bonded=s['fraction_bonded'], f_v6=s['fraction_valence6'], tetra=s['tetra_per_molecule'],
                anchors=s['anchors_intact'] / (3.0 * nm), clustering=s['clustering'],
                mean_bond_d=s['mean_bond_patch_distance'])

def main():
    out = []
    for d in sorted(glob.glob(R + '/alpha_*')):
        n = os.path.basename(d)
        m = re.match(r'alpha_([\d.]+)_Ka_([\d.]+)_Kb_([\d.]+)_str_([\d.]+)', n)
        rec = dict(name=n, alpha=float(m[1]), Ka=float(m[2]), Kb=float(m[3]), strength=float(m[4]))
        topo = cl.load_topology(d + '/input.phb')
        for tag, f in (('start', 'mc_relaxed.dat'), ('end', 'last_conf.dat')):
            p = d + '/' + f
            if not os.path.exists(p) or os.path.getsize(p) < 1e6:
                continue
            for cut in (0.3, 0.1):
                try:
                    rec[f'{tag}_c{cut}'] = metrics(topo, p, cut)
                except Exception as e:
                    rec[f'{tag}_c{cut}'] = dict(error=repr(e)[:200])
        out.append(rec); print(n, rec.get('start_c0.3', {}).get('lc'), rec.get('end_c0.3', {}).get('lc'), flush=True)
    json.dump(out, open(OUT, 'w'), indent=1)

if __name__ == '__main__':
    os.nice(10); main()
