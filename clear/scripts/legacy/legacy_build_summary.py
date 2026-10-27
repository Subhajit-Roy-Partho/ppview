#!/usr/bin/env python3
import json, re, numpy as np
from scipy import stats
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'; D = R + '/final_report/data'
fresh = json.load(open(D + '/legacy_fresh_analysis.json')); tj = json.load(open('/scratch/sroy85/hand5_analysis/traj_results.json'))
inv = {r['run']: r for r in json.load(open('/tmp/claude-2438191/-scratch-sroy85-Github-dna/a7f7a000-064e-4224-9ff5-fe91f96309bd/scratchpad/inv.json'))}
sw = json.load(open(D + '/legacy_sweep_analysis.json')); old = json.load(open(D + '/legacy_oldscript_vs_pbc.json')); tcs = {r['run']: r for r in json.load(open(D + '/legacy_timecourses.json'))}
for r in fresh:
    p = r['run'].split('/'); r['sys'] = p[0]; r['var'] = p[1]
    m = re.search(r'Kb_([\d.]+)_T_([\d.]+)', r['run']); r['Kb'] = float(m[1]) if m else None; r['T'] = float(m[2]) if m else None
    r['steps_e8'] = (inv[r['run']]['t_last'] or 0) * 2000 / 1e8
def row(r, keys=('lc_frac', 'largest_cores', 'n_clusters', 'mean_valence', 'frac_v6', 'tetra_per_mol', 'clustering', 'E', 't_conf')):
    return {k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in keys if k in r} | {'run': r['run']}
out = {'generated': '2026-10-14', 'analysis': 'phbtraj.py (PBC-safe), contact cutoff 0.3; ordered = tetra/mol>=0.20 & six-valent>=0.25 & clustering>=0.30 (monitor_window_scan.py thresholds)',
       'references': {'preformed_crystal_tetra_per_mol': 0.358, 'preformed_relaxed_tetra_per_mol': 0.372, 'ideal_500core_cluster_tetra_per_mol': 0.378, 'ideal_500core_valence': 5.07, 'ideal_500core_v6': 0.61}}
# audit
g = {}
for r in old:
    if 'error' in r: continue
    g.setdefault(r['run'].split('/')[0], []).append(r)
out['analysis_artifact'] = {k: dict(n=len(v), old_lc_frac_mean=round(float(np.mean([x['old_lc_frac'] for x in v])), 4), old_lc_frac_range=[min(x['old_lc_frac'] for x in v), max(x['old_lc_frac'] for x in v)],
                                    pbc_lc_frac_mean=round(float(np.mean([x['pbc_lc_frac'] for x in v])), 4), coord_extent_boxes_median=round(float(np.median([x['coord_extent_boxes'] for x in v])), 1), coord_extent_boxes_max=round(max(x['coord_extent_boxes'] for x in v), 1)) for k, v in g.items()}
# stiffness
s = [r for r in fresh if r['sys'] == 'stiffness_sweep']; ws = {(r['Kb'], r['T']): r for r in s if r['var'] == 'weak_strong'}; ww = {(r['Kb'], r['T']): r for r in s if r['var'] == 'weak_weak'}
paired = {}
for key in ('lc_frac', 'tetra_per_mol', 'frac_v6', 'mean_valence'):
    a = np.array([ws[k][key] for k in ws]); b = np.array([ww[k][key] for k in ws]); paired[key] = dict(ws_mean=round(a.mean(), 4), ww_mean=round(b.mean(), 4), wilcoxon_p=round(float(stats.wilcoxon(a, b).pvalue), 3), ws_wins=int((a > b).sum()), ww_wins=int((b > a).sum()))
L = np.array([inv[r['run']]['energy_lines'] for r in s])
out['stiffness_sweep'] = dict(n=72, start='pre-formed 2048-mol crystal (large_crystal_min.dat), 71% of molecules in largest crystallite at t=0', status='stalled since 2026-08-26 (no job running; watchdog DB stale)', energy_lines=dict(min=int(L.min()), median=int(np.median(L)), max=int(L.max()), n_ge_15001=int((L >= 15001).sum()), n_lt_5000=int((L < 5000).sum())),
    lc_frac=dict(mean=round(float(np.mean([r['lc_frac'] for r in s])), 4), min=round(min(r['lc_frac'] for r in s), 4), max=round(max(r['lc_frac'] for r in s), 4)), tetra_per_mol=dict(min=round(min(r['tetra_per_mol'] for r in s), 4), max=round(max(r['tetra_per_mol'] for r in s), 4)),
    frac_v6_mean=round(float(np.mean([r['frac_v6'] for r in s])), 4), paired_ws_vs_ww=paired, verdict='no melting/degradation at any Kb in 1..300, T in 0.05..0.10, either strength set; minimum-Kb threshold NOT bracketed (Kb=1 -> Lp~2-4)')
# seeded
S = [r for r in fresh if r['sys'] == 'seeded_sweep']
for r in S:
    fr = tj[r['run']]['frames']; f = lambda th: next((x['t'] for x in fr if x['largest_cores'] >= th * 500), None)
    r['t50'] = f(.5); r['t95'] = f(.95); r['maxclus'] = max(x['n_clusters'] for x in fr)
sd = {}
for v in ('weak_strong', 'weak_weak'):
    q = [r for r in S if r['var'] == v]
    sd[v] = dict(n=len(q), lc_frac=1.0, t50_median_steps=float(np.median([r['t50'] for r in q])), t95_median_steps=float(np.median([r['t95'] for r in q])), max_crystallites_median=float(np.median([r['maxclus'] for r in q])),
                 mean_valence=round(float(np.mean([r['mean_valence'] for r in q])), 3), frac_v6=round(float(np.mean([r['frac_v6'] for r in q])), 4), tetra_per_mol=round(float(np.mean([r['tetra_per_mol'] for r in q])), 4), E_per_N=round(float(np.mean([r['E'] for r in q])), 2),
                 spearman_t95_vs_T=round(float(stats.spearmanr([r['T'] for r in q], [r['t95'] for r in q])[0]), 3), spearman_t95_vs_Kb=round(float(stats.spearmanr([r['Kb'] for r in q], [r['t95'] for r in q])[0]), 3))
a = {k: np.array([next(r[k] for r in S if r['var'] == 'weak_strong' and (r['Kb'], r['T']) == (r2['Kb'], r2['T'])) for r2 in S if r2['var'] == 'weak_weak']) for k in ('tetra_per_mol', 'frac_v6', 'mean_valence')}
b = {k: np.array([r2[k] for r2 in S if r2['var'] == 'weak_weak']) for k in a}
out['seeded_sweep'] = dict(n=72, start='8-mol seed + 492 dispersed pre-attached 4-species units, box 40^3 (production data since 2026-08-31 rerun; older docs say 50^3)', status='cancelled 2026-10-06 after 2.3e9-4.5e9 steps each (target 1.5e9)', per_regime=sd,
    ww_vs_ws_paired_wilcoxon=dict(tetra_p=float(stats.wilcoxon(a['tetra_per_mol'], b['tetra_per_mol']).pvalue), v6_p=float(stats.wilcoxon(a['frac_v6'], b['frac_v6']).pvalue), valence_p=float(stats.wilcoxon(a['mean_valence'], b['mean_valence']).pvalue)),
    t95_ws_vs_ww_mannwhitney_p=float(stats.mannwhitneyu([r['t95'] for r in S if r['var'] == 'weak_strong'], [r['t95'] for r in S if r['var'] == 'weak_weak']).pvalue), note='t95 is frame-limited (26 sampled frames) so an upper bound; earlier session quoted 2.8e8 / 3.8e8 medians')
for key, name in (('decisive_equalK', 'decisive_equalK'), ('preconnected_seed_sweep', 'preconnected_seed_sweep'), ('preconnected_K300_large', 'preconnected_K300_large'), ('preconnected_strength_scan', 'preconnected_strength_scan'), ('seeding_scan', 'seeding_scan'), ('window_scan', 'window_scan')):
    out[name] = [row(r) | {'T': r['T'], 'steps_e8': round(r['steps_e8'], 2)} for r in fresh if r['sys'] == key]
# classify
def cls(r):
    if r['lc_frac'] < .5: return 'melted'
    if r['tetra_per_mol'] < .12: return 'aggregate'
    if r['tetra_per_mol'] < .20: return 'partial'
    return 'ordered' if (r['frac_v6'] >= .25 and r['clustering'] >= .30) else 'ambiguous'
for k in ('seeding_scan', 'window_scan', 'preconnected_K300_large'):
    for r in out[k]:
        rr = next(x for x in fresh if x['run'] == r['run']); r['class'] = cls(rr)
oldsw = [r for r in sw if 'lc_frac' in r]
out['old_sweep'] = dict(n_dirs=100, n_with_energy=sum(r.get('energy_lines', 0) > 0 for r in sw), alpha_0p01_no_output=sum(1 for r in sw if r['alpha'] == .01 and r.get('energy_lines', 0) == 0), n_analysed=len(oldsw),
    start='1445/2048 cores connected at t=0 (mc_relaxed), T=0.078, topology with trailing-space iC lines (7-patch quirk)', lc_frac_end_mean=round(float(np.mean([r['lc_frac'] for r in oldsw])), 4), lc_frac_end_max=round(max(r['lc_frac'] for r in oldsw), 4), by_alpha_strength={f'{a}_{s}': round(float(np.mean([r['lc_frac'] for r in oldsw if r['alpha'] == a and r['strength'] == s] or [float('nan')])), 4) for a in (.03, .05, .1, .12) for s in (1, 10, 90, 100, 150)})
json.dump(out, open(D + '/legacy_systems.json', 'w'), indent=1)
for k in ('stiffness_sweep', 'seeded_sweep', 'analysis_artifact'): print(k, json.dumps(out[k])[:1500])
import collections
for k in ('seeding_scan', 'window_scan', 'preconnected_K300_large'): print(k, collections.Counter(r['class'] for r in out[k]))
