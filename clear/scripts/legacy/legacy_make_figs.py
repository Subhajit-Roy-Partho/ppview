#!/usr/bin/env python3
import json, re, os, collections
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'; F = R + '/final_report'; D = F + '/data'; O = F + '/figs'
C = dict(blue='#2a78d6', orange='#eb6834', aqua='#1baf7a', yellow='#eda100', magenta='#e87ba4', green='#008300', violet='#4a3aa7', grey='#7a7a76')
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25, 'grid.linewidth': .5,
                     'figure.dpi': 100, 'savefig.dpi': 200, 'axes.titlesize': 10, 'axes.labelsize': 9, 'legend.fontsize': 8, 'legend.frameon': False})
fresh = json.load(open(D + '/legacy_fresh_analysis.json'))
for r in fresh:
    p = r['run'].split('/'); r['sys'] = p[0]; r['var'] = p[1]
    m = re.search(r'Kb_([\d.]+)_T_([\d.]+)', r['run']); r['Kb'] = float(m[1]) if m else None; r['T'] = float(m[2]) if m else None
tj = json.load(open('/scratch/sroy85/hand5_analysis/traj_results.json'))
tcs = {r['run']: r for r in json.load(open(D + '/legacy_timecourses.json')) if 'error' not in r}
ots = {r['run']: r for r in json.load(open(D + '/legacy_order_timecourse.json')) if 'error' not in r}
old = json.load(open(D + '/legacy_oldscript_vs_pbc.json'))
def save(fig, name): fig.savefig(f'{O}/{name}', bbox_inches='tight', facecolor='white'); plt.close(fig); print(name)

# ---------- fig 1 timeline
import datetime as dt
def D_(s): return dt.datetime.strptime('2026-' + s, '%Y-%m-%d')
rows = [  # name, start, end, state, colour, label
 ('large_crystal/sweep (old, alpha x Ka x Kb x str)', '07-08', '10-06', 'cancelled 10-06', 'grey', '100 dirs; pre-formed crystal dissolves'),
 ('stiffness_sweep (72, pre-formed 2048-mol)', '07-11', '08-26', 'stalled 08-26 (never restarted)', 'orange', 'crystal survives everywhere'),
 ('seeded_sweep s8 (72) [40^3 rerun from 08-31]', '07-13', '10-06', 'cancelled 10-06', 'blue', '72/72 -> 1 cluster, arrested'),
 ('seeded_sweep_s32 / s48 (192)', '08-19', '08-27', 'stopped; raw data wiped 08-28', 'violet', 'void: analysis bug + data lost'),
 ('preconnected_seed_sweep (6, T 0.11-0.20)', '07-14', '09-02', 'stalled 09-02', 'aqua', '99% connected, arrested'),
 ('decisive_equalK (8)', '08-27', '10-06', 'cancelled 10-06', 'magenta', 'all variants identical'),
 ('preconnected_K300_large (8, 32-mol seed)', '08-27', '10-14', 'RUNNING (4 jobs)', 'green', 'ww T=0.14 anneals (tet 0.32)'),
 ('preconnected_strength_scan (4, S 50-200)', '10-07', '10-11', 'finished/idle', 'yellow', 'all arrested'),
 ('window_scan (16, ww quench/ramps/heating)', '10-09', '10-11', 'finished', 'blue', 'ordered only T<=0.14; melts 0.17-0.18'),
 ('seeding_scan (23, seed 8-256 mol)', '10-10', '10-15', 'RUNNING (S192/S256)', 'green', 'larger seeds -> ordered, T=0.14'),
]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
for i, (n, a, b, st, c, lab) in enumerate(rows[::-1]):
    a_, b_ = D_(a), D_(b)
    ax.barh(i, (b_ - a_).days, left=matplotlib.dates.date2num(a_), color=C[c], height=.55, alpha=.9)
    ax.text(matplotlib.dates.date2num(a_) - 2, i, n, ha='right', va='center', fontsize=8)
    ax.text(matplotlib.dates.date2num(b_) + 2, i, f'{st}; {lab}', ha='left', va='center', fontsize=7.5, color='#333', bbox=dict(fc='white', ec='none', pad=1, alpha=.85), zorder=5)
ax.axvline(matplotlib.dates.date2num(D_('10-06')), color='#444', lw=.8, ls='--'); ax.text(matplotlib.dates.date2num(D_('10-06')), len(rows) - .35, ' 10-06 mass cancel + wrong "no growth" report', fontsize=7, va='bottom')
ax.axvline(matplotlib.dates.date2num(D_('10-09')), color='#444', lw=.8, ls=':'); ax.text(matplotlib.dates.date2num(D_('10-09')), -1.1, ' 10-09 PBC bug found', fontsize=7, va='top')
ax.xaxis_date(); ax.set_yticks([]); ax.set_xlim(matplotlib.dates.date2num(D_('07-01')), matplotlib.dates.date2num(D_('11-25'))); ax.set_ylim(-1.5, len(rows) + .3)
ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator()); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b')); ax.grid(axis='y', alpha=0)
ax.set_title('Legacy (4-species) PHB sweeps: timeline and status as of 2026-10-14')
ax.spines['left'].set_visible(False)
fig.subplots_adjust(left=.36, right=.72)
save(fig, 'legacy_fig01_timeline_status.png')

# ---------- fig 2 artefact audit
fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
names = ['seeded_sweep', 'decisive_equalK', 'preconnected_seed_sweep', 'preconnected_K300_large', 'preconnected_strength_scan']
short = ['seeded\n(72)', 'decisive\nequal-K (8)', 'precon. seed\n(6)', 'K300_large\n(8)', 'strength\nscan (4)']
cols = [C['blue'], C['magenta'], C['aqua'], C['green'], C['yellow']]
rng = np.random.default_rng(1)
for i, n in enumerate(names):
    rs = [r for r in old if r['run'].startswith(n) and 'error' not in r]
    x = i + rng.uniform(-.18, .18, len(rs))
    axs[0].scatter(x - .0, [r['old_lc_frac'] * 100 for r in rs], s=12, color=C['orange'], label='original script (no PBC wrap)' if i == 0 else None, alpha=.8)
    axs[0].scatter(x, [r['pbc_lc_frac'] * 100 for r in rs], s=12, color=C['blue'], marker='s', label='PBC-safe (phbtraj, 3 detectors agree)' if i == 0 else None, alpha=.8)
    axs[1].scatter(x, [r['coord_extent_boxes'] for r in rs], s=12, color=C['violet'], alpha=.8)
axs[0].set_xticks(range(5)); axs[0].set_xticklabels(short, fontsize=7.5); axs[0].set_ylabel('largest cluster, % of 500 molecules'); axs[0].legend(loc='center right', fontsize=7)
axs[0].set_title('Same final configurations, two analyses'); axs[0].set_ylim(-3, 108)
axs[1].set_xticks(range(5)); axs[1].set_xticklabels(short, fontsize=7.5); axs[1].set_ylabel('extent of stored coordinates / box length'); axs[1].set_yscale('log')
axs[1].axhline(1, color='k', lw=.8, ls='--'); axs[1].text(4.4, 1.15, 'box', fontsize=7, ha='right'); axs[1].set_title('Why: stored (unwrapped) coordinates drift 10-100 boxes')
save(fig, 'legacy_fig02_analysis_artifact.png')

# ---------- fig 3 seeded growth
fig, axs = plt.subplots(1, 3, figsize=(11, 3.4))
ncols = {'weak_strong': C['blue'], 'weak_weak': C['orange']}
for k, v in tj.items():
    if k.startswith('seeded_sweep/') and '#' not in k:
        var = k.split('/')[1]; fr = v['frames']
        t = [f['t'] / 1e8 for f in fr]; axs[0].plot(t, [f['largest_cores'] / 5 for f in fr], color=ncols[var], lw=.5, alpha=.35)
        axs[1].plot(t, [f['n_clusters'] for f in fr], color=ncols[var], lw=.5, alpha=.35)
for var, c in ncols.items(): axs[0].plot([], [], color=c, label=var.replace('_', '-') + (' (K=101)' if 'strong' in var else ' (K=2)'))
axs[0].legend(); axs[0].set_xlabel('MD steps (1e8)'); axs[0].set_ylabel('largest crystallite, % of cores'); axs[0].set_title('Plain 8-mol seed: all 72 runs reach 100%'); axs[0].set_xlim(0, 6)
axs[1].set_xlabel('MD steps (1e8)'); axs[1].set_ylabel('disconnected crystallites'); axs[1].set_title('Many nuclei (~95), then coalescence'); axs[1].set_xlim(0, 6)
sc = {'S50': C['aqua'], 'S100': C['blue'], 'S150': C['orange'], 'S200': C['violet']}
for s, c in sc.items():
    r = tcs[f'preconnected_strength_scan/{s}/Kb_300_T_0.100']; axs[2].plot([f['t'] / 1e8 for f in r['frames']], [f['largest'] / 5 for f in r['frames']], color=c, label=f'{s} (K={2*int(s[1:])})')
axs[2].legend(); axs[2].set_xlim(0, 6); axs[2].set_xlabel('MD steps (1e8)'); axs[2].set_ylabel('largest crystallite, % of cores'); axs[2].set_title('32-mol seed, equal strength (T=0.10)')
save(fig, 'legacy_fig03_seeded_growth.png')

# ---------- fig 4 seeding scan
fig, axs = plt.subplots(1, 3, figsize=(11.5, 3.5))
cm = {8: '#c6dbef', 16: '#9ecae1', 32: '#6baed6', 64: '#3182bd', 128: '#08519c', 192: C['orange'], 256: C['magenta']}
cm = {8: C['grey'], 16: C['aqua'], 32: C['yellow'], 64: C['orange'], 128: C['blue'], 192: C['violet'], 256: C['magenta']}
for k, r in tcs.items():
    m = re.search(r'S(\d+)_T0\.140', k)
    if m and k.startswith('seeding_scan'):
        n = int(m[1]); axs[0].plot([f['t'] / 1e8 for f in r['frames']], [f['largest'] / 5 for f in r['frames']], color=cm[n], lw=1 if '_r' in k else 1.3, alpha=.9)
for n, c in cm.items(): axs[0].plot([], [], color=c, label=f'{n}-mol seed')
axs[0].legend(ncol=2, fontsize=7, loc='lower right'); axs[0].set_xlabel('MD steps (1e8)'); axs[0].set_ylabel('largest crystallite, % of cores'); axs[0].set_title('T=0.14, K=2: growth vs seed size')
sc2 = [r for r in fresh if r['sys'] == 'seeding_scan']
for T, mk, c in ((0.14, 'o', C['blue']), (0.15, 's', C['orange']), (0.16, '^', C['violet'])):
    rs = sorted([r for r in sc2 if abs(r['T_run'] if 'T_run' in r else 0) < 0 or re.search(f'T{T:.3f}', r['run'])], key=lambda r: int(re.search(r'S(\d+)', r['run'])[1]))
    xs = [int(re.search(r'S(\d+)', r['run'])[1]) for r in rs]
    axs[1].plot(xs, [r['lc_frac'] * 100 for r in rs], marker=mk, color=c, label=f'T={T}', ls='' if T == 0.14 else '-')
    axs[2].plot(xs, [r['tetra_per_mol'] for r in rs], marker=mk, color=c, label=f'T={T}', ls='' if T == 0.14 else '-')
axs[1].set_xscale('log', base=2); axs[2].set_xscale('log', base=2); axs[1].set_xlabel('seed size (molecules)'); axs[2].set_xlabel('seed size (molecules)')
axs[1].set_ylabel('largest crystallite at end, % of cores'); axs[1].set_title('Final size (8e8 steps; S192/S256 at 3.5e8)'); axs[1].legend()
axs[2].set_ylabel('4-species tetrahedra / molecule'); axs[2].axhline(.2, color='k', ls='--', lw=.8); axs[2].text(8, .205, 'monitor "ordered" threshold 0.20', fontsize=7)
axs[2].set_title('Order grows with seed size at T=0.14'); axs[2].legend(loc='lower right')
save(fig, 'legacy_fig04_seeding_scan.png')

# ---------- fig 5 order vs time
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
for k, r in ots.items():
    fr = r['frames']
    if k.startswith('seeding_scan'):
        n = int(re.search(r'S(\d+)', k)[1]); axs[0].plot([f['t'] / 1e8 for f in fr], [f['tet'] for f in fr], color=cm[n], lw=1 if '_r' in k or 'T0.1' in k else 1.3, alpha=.9)
for n in (8, 16, 32, 64, 128, 192, 256): axs[0].plot([], [], color=cm[n], label=f'{n}')
axs[0].axhline(.2, color='k', ls='--', lw=.8); axs[0].axhline(.378, color=C['green'], ls=':', lw=1); axs[0].text(.1, .385, 'ideal compact 500-core cluster 0.378', fontsize=7, color=C['green'])
axs[0].legend(title='seed size', ncol=2, fontsize=7, loc='upper left', bbox_to_anchor=(0, .9)); axs[0].set_xlabel('MD steps (1e8)'); axs[0].set_ylabel('tetrahedra / molecule'); axs[0].set_title('seeding_scan, T=0.135-0.150 (all S128 replicates incl.)'); axs[0].set_ylim(0, .42)
for k, c, lab in (('window_scan/runs/Q_T0.140_a', C['blue'], 'quench T=0.14'), ('window_scan/runs/Q_T0.130_a', C['aqua'], 'quench T=0.13'), ('window_scan/runs/Q_T0.120_a', C['yellow'], 'quench T=0.12'), ('window_scan/runs/AS_a', C['orange'], 'slow ramp 0.17->0.12'), ('window_scan/runs/AF_a', C['magenta'], 'fast ramp 0.17->0.12'),
                  ('preconnected_strength_scan/S100/Kb_300_T_0.100', C['grey'], 'S100 (K=200), T=0.10')):
    fr = ots[k]['frames']; axs[1].plot([f['t'] / 1e8 for f in fr], [f['tet'] for f in fr], color=c, label=lab)
axs[1].axhline(.2, color='k', ls='--', lw=.8); axs[1].legend(fontsize=7); axs[1].set_xlabel('MD steps (1e8)'); axs[1].set_ylabel('tetrahedra / molecule'); axs[1].set_title('32-mol-cluster starts: partial order at best'); axs[1].set_ylim(0, .42)
save(fig, 'legacy_fig05_order_vs_time.png')

# ---------- fig 6 strength comparison
fig, axs = plt.subplots(2, 2, figsize=(10, 7))
S = [r for r in fresh if r['sys'] == 'seeded_sweep']
Ts = sorted(set(r['T'] for r in S)); w = .38
for j, (key, yl) in enumerate((('tetra_per_mol', 'tetrahedra / molecule'), ('mean_valence', 'mean valence of crystallized cores'))):
    ax = axs[0, j]
    for o, (var, c, lab) in enumerate((('weak_strong', C['blue'], 'weak_strong K=101'), ('weak_weak', C['orange'], 'weak_weak K=2'))):
        m = [np.mean([r[key] for r in S if r['var'] == var and r['T'] == T]) for T in Ts]; sd = [np.std([r[key] for r in S if r['var'] == var and r['T'] == T]) for T in Ts]
        ax.bar(np.arange(len(Ts)) + (o - .5) * w, m, w, yerr=sd, color=c, label=lab, capsize=2, error_kw=dict(lw=.7))
    ax.set_xticks(range(len(Ts))); ax.set_xticklabels([f'{T:g}' for T in Ts]); ax.set_xlabel('T'); ax.set_ylabel(yl); ax.set_title(f'seeded_sweep (n=6 Kb per bar): {yl.split(" of")[0]}'); ax.legend(fontsize=7)
    if j == 0: ax.set_ylim(0, .16)
    else: ax.set_ylim(3, 4.5)
ax = axs[1, 0]
labs = []; vals = []; cols = []
for sysn, var, lab, c in (('decisive_equalK', 'weak_weak', 'K=2\n(1+1)', C['orange']), ('decisive_equalK', 'rev_1_299', 'K=300\n(1+299)', C['violet']), ('decisive_equalK', 'sym_150_150', 'K=300\n(150+150)', C['aqua']), ('decisive_equalK', 'ws_asym', 'K=300\n(299+1)', C['blue']),
                          ('preconnected_strength_scan', 'S50', 'S50\nK=100', C['grey']), ('preconnected_strength_scan', 'S100', 'S100\nK=200', C['grey']), ('preconnected_strength_scan', 'S150', 'S150\nK=300', C['grey']), ('preconnected_strength_scan', 'S200', 'S200\nK=400', C['grey'])):
    rs = [r for r in fresh if r['sys'] == sysn and r['var'] == var]; labs.append(lab); vals.append(np.array([r['tetra_per_mol'] for r in rs])); cols.append(c)
ax.bar(range(len(vals)), [v.mean() for v in vals], color=cols, yerr=[[v.mean() - v.min() for v in vals], [v.max() - v.mean() for v in vals]], capsize=2, error_kw=dict(lw=.7))
ax.set_xticks(range(len(vals))); ax.set_xticklabels(labs, fontsize=7); ax.set_ylabel('tetrahedra / molecule'); ax.set_ylim(0, .16); ax.set_title('Equal-K control (T=0.078/0.090) and equal-strength scan (T=0.10)')
ax.axhline(.372, color=C['green'], ls=':', lw=1) if False else None
ax = axs[1, 1]
K3 = [r for r in fresh if r['sys'] == 'preconnected_K300_large']
for var, c, lab in (('weak_strong', C['blue'], 'weak_strong K=101'), ('weak_weak', C['orange'], 'weak_weak K=2')):
    rs = sorted([r for r in K3 if r['var'] == var], key=lambda r: r['T']); ax.plot([r['T'] for r in rs], [r['tetra_per_mol'] for r in rs], 'o-', color=c, label=lab)
ax.axhline(.2, color='k', ls='--', lw=.8); ax.set_xlabel('T'); ax.set_ylabel('tetrahedra / molecule'); ax.set_title('preconnected_K300_large: only K=2 at T=0.14 anneals'); ax.legend(); ax.set_ylim(0, .4)
fig.tight_layout(); save(fig, 'legacy_fig06_strength_comparison.png')

# ---------- fig 7 stiffness heatmaps
st = [r for r in fresh if r['sys'] == 'stiffness_sweep']; Kbs = [1, 3, 10, 30, 100, 300]; Tl = sorted(set(r['T'] for r in st))
fig, axs = plt.subplots(2, 2, figsize=(9, 6.3))
for i, var in enumerate(('weak_strong', 'weak_weak')):
    for j, (key, lab, vmin, vmax) in enumerate((('lc_frac', 'largest crystallite / 2048 molecules', .6, 1.0), ('tetra_per_mol', 'tetrahedra / molecule', .3, .4))):
        ax = axs[i, j]; M = np.array([[next(r for r in st if r['var'] == var and r['Kb'] == kb and r['T'] == T)[key] for T in Tl] for kb in Kbs])
        im = ax.imshow(M, origin='lower', cmap='Blues', vmin=vmin, vmax=vmax, aspect='auto')
        for a in range(6):
            for b in range(6): ax.text(b, a, f'{M[a,b]:.2f}' if key == 'lc_frac' else f'{M[a,b]:.3f}', ha='center', va='center', fontsize=7, color='white' if M[a, b] > (vmin + vmax) / 2 + .08 * (vmax - vmin) else '#111')
        ax.set_xticks(range(6)); ax.set_xticklabels([f'{t:g}' for t in Tl]); ax.set_yticks(range(6)); ax.set_yticklabels(Kbs); ax.set_xlabel('T'); ax.set_ylabel('Kb'); ax.grid(False)
        ax.set_title(f'{var} ({"K=101" if "strong" in var else "K=2"}): {lab}', fontsize=8.5); plt.colorbar(im, ax=ax, fraction=.046)
fig.suptitle('Stiffness sweep (pre-formed 2048-mol crystal; start: 71% connected, 0.358 tet/mol): nothing melts, nothing depends on Kb', fontsize=9.5)
fig.tight_layout(); save(fig, 'legacy_fig07_stiffness_heatmaps.png')

# ---------- fig 8 quality vs K/T
fig, ax = plt.subplots(figsize=(8, 4.8))
def Kfar(r):
    s, v = r['sys'], r['var']
    if s == 'seeded_sweep' or s == 'preconnected_seed_sweep' or s == 'preconnected_K300_large': return 101 if ('strong' in v or s == 'preconnected_seed_sweep') else 2
    if s == 'decisive_equalK': return 2 if v == 'weak_weak' else 300
    if s == 'preconnected_strength_scan': return 2 * int(v[1:])
    if s in ('seeding_scan', 'window_scan'): return 2
    return None
def Tof(r):
    if r['sys'] == 'seeding_scan': return float(re.search(r'T(0\.\d+)', r['run'])[1])
    if r['sys'] == 'window_scan':
        m = re.search(r'Q_T(0\.\d+)', r['run'])
        return float(m[1]) if m else (0.12 if 'A' in r['var'][:2] else 0.22)
    if r['sys'] == 'preconnected_strength_scan': return 0.10
    return r['T']
mk = {'seeded_sweep': ('o', C['blue'], 'seeded_sweep (8 seed)'), 'decisive_equalK': ('s', C['magenta'], 'decisive_equalK'), 'preconnected_seed_sweep': ('D', C['aqua'], 'preconnected_seed_sweep'), 'preconnected_K300_large': ('^', C['green'], 'preconnected_K300_large'),
      'preconnected_strength_scan': ('v', C['yellow'], 'strength_scan'), 'seeding_scan': ('P', C['violet'], 'seeding_scan'), 'window_scan': ('X', C['orange'], 'window_scan (final state)')}
for s, (m, c, lab) in mk.items():
    rs = [r for r in fresh if r['sys'] == s and 'tetra_per_mol' in r]
    ax.scatter([Kfar(r) / Tof(r) for r in rs], [r['tetra_per_mol'] for r in rs], marker=m, color=c, s=26, alpha=.8, label=lab, edgecolor='white', linewidth=.3)
ax.set_xscale('log'); ax.axhline(.2, color='k', ls='--', lw=.8); ax.text(2500, .205, 'ordered threshold', fontsize=7, ha='right'); ax.axhline(.378, color=C['green'], ls=':', lw=1); ax.text(2500, .383, 'ideal 500-core cluster', fontsize=7, ha='right', color=C['green'])
ax.axvspan(11.5, 14.5, color='#999', alpha=.15); ax.text(12.9, .005, 'K/T 12-14', fontsize=7, ha='center')
ax.set_xlabel('reduced inter-molecular bond depth  K_far / T'); ax.set_ylabel('tetrahedra / molecule (final state)'); ax.set_ylim(0, .42); ax.set_title('Connectivity everywhere, order only at small K/T (reversible bonds)')
ax.legend(fontsize=7, ncol=2, loc='center', bbox_to_anchor=(.62, .66))
save(fig, 'legacy_fig08_quality_vs_KT.png')

# ---------- fig 9 window scan
fig, axs = plt.subplots(1, 3, figsize=(11.5, 3.5))
Q = {}
for r in fresh:
    m = re.search(r'window_scan/runs/Q_T(0\.\d+)_([ab])', r['run'])
    if m: Q.setdefault(float(m[1]), []).append(r)
Tq = sorted(Q)
axs[0].plot(Tq, [np.mean([r['lc_frac'] * 100 for r in Q[T]]) for T in Tq], 'o-', color=C['blue'], label='quench: LC (%)'); ax2 = axs[0]
for T in Tq:
    for r in Q[T]: axs[0].scatter(T, r['lc_frac'] * 100, color=C['blue'], s=10, alpha=.5)
sc3 = [r for r in fresh if r['sys'] == 'seeding_scan' and re.search(r'S(8|16|32|64|128)_T', r['run'])]
for r in sc3:
    pass
axs[0].set_xlabel('hold temperature T'); axs[0].set_ylabel('largest crystallite, % of cores'); axs[0].set_title('Unseeded quench (from T=0.17 melt), 8e8 steps')
axs[1].plot(Tq, [np.mean([r['tetra_per_mol'] for r in Q[T]]) for T in Tq], 's-', color=C['orange']); [axs[1].scatter(T, r['tetra_per_mol'], color=C['orange'], s=10, alpha=.5) for T in Tq for r in Q[T]]
axs[1].axhline(.2, color='k', ls='--', lw=.8); axs[1].set_xlabel('hold temperature T'); axs[1].set_ylabel('tetrahedra / molecule'); axs[1].set_title('Order of the quenched state (2 replicates)')
st_ = [.15 + .01 * i for i in range(8)]
for run, c in (('H_a', C['blue']), ('H_b', C['orange'])):
    r = tcs['window_scan/runs/' + run]; t0 = int(open(f'{R}/window_scan/runs/{run}/t0.txt').read())
    x = [st_[min(7, max(0, int((f['t'] - t0) // 6e7)))] + ((f['t'] - t0) % 6e7) / 6e7 * .01 for f in r['frames']]
    axs[2].plot(x, [f['largest'] / 5 for f in r['frames']], color=c, label=f'{run}')
axs[2].set_xlabel('T during heating ramp (+0.01 per 6e7 steps)'); axs[2].set_ylabel('largest crystallite, % of cores'); axs[2].set_title('Heating the ordered K=2 state: melts at 0.17-0.18'); axs[2].legend()
fig.tight_layout(); save(fig, 'legacy_fig09_window_scan.png')

# ---------- fig 10 old sweep
sw = json.load(open(D + '/legacy_sweep_analysis.json'))
fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
al = [.03, .05, .1, .12]; strs = [1, 10, 90, 100, 150]
M = np.array([[np.mean([r['lc_frac'] * 100 for r in sw if r['alpha'] == a and r['strength'] == s and 'lc_frac' in r] or [np.nan]) for s in strs] for a in al])
im = axs[0].imshow(M, origin='lower', cmap='Blues', vmin=0, vmax=25, aspect='auto')
for i in range(4):
    for j in range(5): axs[0].text(j, i, f'{M[i,j]:.1f}', ha='center', va='center', fontsize=8)
axs[0].set_xticks(range(5)); axs[0].set_xticklabels(strs); axs[0].set_yticks(range(4)); axs[0].set_yticklabels(al); axs[0].set_xlabel('ico patch strength (far-tip 0)'); axs[0].set_ylabel('patchyAlpha'); axs[0].grid(False)
axs[0].set_title('Old sweep: largest crystallite at end, % (start 70%)'); plt.colorbar(im, ax=axs[0], fraction=.046)
for s, c in zip(strs, [C['grey'], C['aqua'], C['blue'], C['violet'], C['orange']]):
    rs = [r for r in sw if r['strength'] == s and 'lc_frac' in r and r['alpha'] >= .05]
    axs[1].scatter([r['tetra_per_mol'] for r in rs], [r['lc_frac'] * 100 for r in rs], s=14, color=c, label=f'str {s}')
axs[1].set_xlabel('tetrahedra / molecule'); axs[1].set_ylabel('largest crystallite, %'); axs[1].legend(fontsize=7); axs[1].set_title('alpha>=0.05 runs (n=60)')
fig.tight_layout(); save(fig, 'legacy_fig10_old_sweep.png')
