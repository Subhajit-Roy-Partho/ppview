#!/usr/bin/env python3
"""Snapshot confs of representative legacy runs, run cluster_labels.py, append to clusters/legacy_manifest.json."""
import os, sys, json, shutil, subprocess, time
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'; F = f'{R}/final_report'
SEL = [
 ('seeded_sweep', 'seeded_sweep/weak_strong/Kb_300_T_0.078', 'plain 8-mol seed, K=101, arrested network (100% one cluster, tetra/mol~0.09)'),
 ('seeded_sweep', 'seeded_sweep/weak_weak/Kb_300_T_0.078', 'plain 8-mol seed, K=2, arrested network (paired with the weak_strong run)'),
 ('preconnected_K300_large', 'preconnected_K300_large/weak_weak/Kb_300_T_0.140', 'annealed ordered-ish state: K=2, T=0.14, 32-mol seed (tetra/mol 0.32)'),
 ('seeding_scan', 'seeding_scan/runs/S128_T0.140_r2', 'best finished seeded growth: 128-mol seed, T=0.14, ordered per monitor thresholds'),
 ('seeding_scan', 'seeding_scan/runs/S256_T0.140_r2', 'bigger seed (256 mol) T=0.14, still running (3.5e8 steps), highest tetra/mol so far'),
 ('seeding_scan', 'seeding_scan/runs/S8_T0.160', 'failed growth: 8-mol seed at T=0.16 (above melting) - stays small/melted'),
 ('preconnected_strength_scan', 'preconnected_strength_scan/S200/Kb_300_T_0.100', 'strongest equal strength S=200 (K=400), fully aggregated but arrested'),
 ('window_scan', 'window_scan/runs/H_a', 'ordered state heated to T=0.22: fully melted (hysteresis/melting example)'),
 ('stiffness_sweep', 'stiffness_sweep/weak_weak/Kb_1_T_0.100', 'pre-formed 2048-mol crystal, floppiest arms (Kb=1) at highest T=0.10: does not melt'),
]
man_path = f'{F}/clusters/legacy_manifest.json'
man = json.load(open(man_path)) if os.path.exists(man_path) else []
mine_runs = {x[1] for x in SEL}
man = [m for m in man if m.get('run') not in mine_runs]
mine = []
for system, rel, note in SEL:
    d = f'{R}/{rel}'; tag = rel.split('/', 1)[1].replace('/', '_') if system in ('window_scan', 'seeding_scan') else rel.split('/', 1)[1].replace('/', '_')
    tag = tag.replace('runs_', '')
    base = f'legacy_{system}__{tag}'
    top_src = os.path.realpath(d + '/topology.phb')
    conf_snap = f'{F}/clusters/{base}.conf.dat'
    shutil.copyfile(d + '/final_conf.dat', conf_snap)
    top_snap = f'{F}/clusters/{base}.topology.phb'
    shutil.copyfile(top_src, top_snap)
    lab = f'{F}/clusters/{base}.labels.txt'; js = f'{F}/clusters/{base}.summary.json'
    rc = subprocess.run([sys.executable, f'{F}/cluster_labels.py', '--top', top_snap, '--conf', conf_snap, '--out', lab, '--json', js], capture_output=True, text=True)
    ent = dict(system=system, run=rel, note=note, topology=top_snap, topology_source=top_src, conf_snapshot=conf_snap,
               conf_source=d + '/final_conf.dat', labels=lab, summary_json=js, snapshot_time=time.strftime('%Y-%m-%d %H:%M'),
               rc=rc.returncode, stderr=rc.stderr[-300:])
    if rc.returncode == 0:
        s = json.load(open(js)); ent['summary'] = {k: s[k] for k in ('n_particles','n_molecules','time','box','n_patch_bonds','n_clusters_ge2','largest_cluster','largest_cluster_fraction','second_cluster','n_singletons','top_cluster_sizes','mean_valence','fraction_valence6','fraction_bonded','physical_largest_cluster_cores','mean_bond_patch_distance') if k in s}
    mine.append(ent); print(base, rc.returncode, rc.stderr[-200:])
json.dump(man + mine, open(man_path, 'w'), indent=1)
