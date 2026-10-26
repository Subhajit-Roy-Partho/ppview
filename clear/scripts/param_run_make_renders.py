#!/usr/bin/env python3
"""param_run_make_renders.py - snapshot (copy) -> cluster labels (cluster_labels.py) -> ppview render, for the parameter-variation image set.
Read-only on simulation dirs (final_conf.dat is copied first; header/length validated).  Usage: param_run_make_renders.py [stage: labels|render|all] [name-filter ...]
Outputs: clusters/param_run_<name>.{labels.txt,summary.json}, renders/param_run/<name>.png, clusters/param_run_manifest.json
"""
import os, sys, json, shutil, subprocess, time, re
R = '/scratch/sroy85/Github/dna/large_crystal/hand5'
FR = R + '/final_report'
SCR = '/tmp/claude-2438191/-scratch-sroy85-Github-dna/a7f7a000-064e-4224-9ff5-fe91f96309bd/scratchpad/param/snap'
os.makedirs(SCR, exist_ok=True); os.makedirs(FR + '/renders/param_run', exist_ok=True)
PP = '/scratch/sroy85/Github/ppview/render_phb.py'
CL = FR + '/clusters'
ex = lambda s: (f'{CL}/' + s)

items = []   # (name, topology, conf, mode, title, extra args)
def add(name, run, mode='cluster', title=None, extra=(), conf=None, top=None):
    d = f'{R}/{run}'
    items.append(dict(name=name, top=top or os.path.realpath(d + '/topology.phb'), conf=conf or d + '/final_conf.dat', mode=mode, title=title or name, extra=list(extra), run=run))
# stiffness sweep (2048 mol): cores only
for v, vs in (('weak_weak', 'ww K=2'), ('weak_strong', 'ws K=101')):
    for kb in (1, 10, 300):
        add(f'stiff_{v}_Kb{kb}_T0.100', f'stiffness_sweep/{v}/Kb_{kb}_T_0.100', title=f'pre-formed crystal, {vs}, Kb={kb}, T=0.10', extra=['--cores-only'])
# seeded sweep ww
for kb in (1, 300):
    for T in ('0.050', '0.100'):
        add(f'seeded_ww_Kb{kb}_T{T}', f'seeded_sweep/weak_weak/Kb_{kb}_T_{T}', title=f'dilute 8-seed, ww K=2, Kb={kb}, T={T}')
# seeding scan
for s, T, run in ((8, '0.140', 'S8_T0.140'), (32, '0.140', 'S32_T0.140'), (128, '0.140', 'S128_T0.140_r2'), (256, '0.140', 'S256_T0.140_r2'), (8, '0.150', 'S8_T0.150'), (128, '0.150', 'S128_T0.150'), (128, '0.160', 'S128_T0.160')):
    add(f'seedscan_S{s}_T{T}', f'seeding_scan/runs/{run}', title=f'seeding scan, ww K=2, seed {s}, T={T}')
# preconnected seed sweep
for T in ('0.110', '0.200'):
    add(f'preseed_ws_T{T}', f'preconnected_seed_sweep/four_species/Kb_300_T_{T}', title=f'preconnected 8-seed, ws K=101, T={T}')
# strength scan
for S in (50, 200):
    add(f'strength_S{S}_T0.100', f'preconnected_strength_scan/S{S}/Kb_300_T_0.100', title=f'equal strength S={S} (K={2*S}), alpha 0.12, T=0.10')
# window scan quench holds
for T in ('0.120', '0.140', '0.160'):
    add(f'window_Q_T{T}', f'window_scan/runs/Q_T{T}_a', title=f'melt-quench hold, ww K=2, 32-seed, T={T}')
# decisive equal-K
add('decisive_ww_K2_T0.078', 'decisive_equalK/weak_weak/Kb_300_T_0.078', title='equal-K control: K=2 (1+1), T=0.078')
add('decisive_rev_1_299_K300_T0.078', 'decisive_equalK/rev_1_299/Kb_300_T_0.078', title='equal-K control: K=300 (core 1 + far-tip 299), T=0.078')
# two-species (existing snapshots)
man = json.load(open(CL + '/manifest.json'))['runs']
for r in man:
    if r['system'] == 'two_species_preconnected' and r['variant'] in ('3H3L', '5L1H') and r['T'] in (0.078, 0.14):
        items.append(dict(name=f"twosp_{r['variant']}_T{r['T']:.3f}", top=r['topology'], conf=r['conf_snapshot'], mode='cluster', title=f"2-species {r['variant']} (alpha 0.12), T={r['T']}", extra=[], run=r['source_conf'].replace(R + '/', ''), prelabeled=r['labels'], presummary=r['summary_json']))
# patch-colour renders, one per distinct strength scheme (not already in renders/patches)
add('patch_seeded_ws_K101', 'seeded_sweep/weak_strong/Kb_300_T_0.078', mode='patch', title='patch colours: weak_strong (core 100 / far-tip 1)', extra=['--cores-only'])
add('patch_seeded_ww_K2', 'seeded_sweep/weak_weak/Kb_300_T_0.078', mode='patch', title='patch colours: weak_weak (1/1)', extra=['--cores-only'])
add('patch_strength_S200', 'preconnected_strength_scan/S200/Kb_300_T_0.100', mode='patch', title='patch colours: equal strength 200', extra=['--cores-only'])
add('patch_decisive_rev_1_299', 'decisive_equalK/rev_1_299/Kb_300_T_0.078', mode='patch', title='patch colours: core 1 + far-tip 299', extra=['--cores-only'])
for r in man:
    if r['system'] == 'two_species_preconnected' and r['variant'] == '3H3L' and r['T'] == 0.078:
        items.append(dict(name='patch_twosp_3H3L', top=r['topology'], conf=r['conf_snapshot'], mode='patch', title='patch colours: 2-species 3H3L (3 strong / 3 weak channels)', extra=['--cores-only'], run=''))

def snapshot(it):
    src = it['conf']; dst = f"{SCR}/{it['name']}.dat"
    if src.startswith(R + '/final_report/') or not os.path.exists(dst):
        for attempt in range(4):
            shutil.copyfile(src, dst)
            with open(dst) as f:
                hdr = f.readline(); n = sum(1 for _ in f)
            N = int(open(it['top']).readline().split()[0])
            if n == N + 2 or n == N + 3 or n >= N + 2: break
            time.sleep(3)
    it['snap'] = dst
    return dst

def labels(it):
    out = f"{CL}/param_run_{it['name']}.labels.txt"; js = f"{CL}/param_run_{it['name']}.summary.json"
    if it.get('prelabeled'):
        shutil.copyfile(it['prelabeled'], out); shutil.copyfile(it['presummary'], js)
    else:
        subprocess.run([sys.executable, FR + '/cluster_labels.py', '--top', it['top'], '--conf', it['snap'], '--out', out, '--json', js], check=True, stdout=subprocess.DEVNULL)
    it['labels'] = out; it['summary'] = js
    s = json.load(open(js))
    it['summary_digest'] = {k: s[k] for k in s if k in ('n_molecules', 'largest_cluster', 'largest_cluster_fraction', 'n_clusters', 'n_clusters_ge2', 'n_singletons', 'mean_valence', 'fraction_valence6', 'cluster_sizes')}

def render(it, width=3200, height=1800):
    out = f"{FR}/renders/param_run/{it['name']}.png"
    cmd = [sys.executable, PP, '--top', it['top'], '--conf', it['snap'], '--out', out, '--width', str(width), '--height', str(height), '--scale', '2', '--background', 'white', '--title', it['title'], '--quiet']
    if it['mode'] == 'cluster': cmd += ['--cluster-file', it['labels'], '--legend', '--highlight-largest' if False else '--legend-top', '6']
    cmd += it['extra']
    t0 = time.time(); subprocess.run(cmd, check=True); it['render'] = out; it['render_s'] = round(time.time() - t0, 1)

if __name__ == '__main__':
    os.nice(10)
    stage = sys.argv[1] if len(sys.argv) > 1 else 'all'; filt = sys.argv[2:]
    sel = [it for it in items if not filt or any(re.search(x, it['name']) for x in filt)]
    mpath = CL + '/param_run_manifest.json'
    done = {m['name']: m for m in json.load(open(mpath))} if os.path.exists(mpath) else {}
    for it in sel:
        try:
            if stage in ('labels', 'all'):
                if it['mode'] == 'cluster' or it['name'] == 'x': pass
                snapshot(it)
                if it['mode'] == 'cluster': labels(it)
            if stage in ('render', 'all'):
                if 'snap' not in it: it['snap'] = f"{SCR}/{it['name']}.dat"
                if it['mode'] == 'cluster' and 'labels' not in it:
                    it['labels'] = f"{CL}/param_run_{it['name']}.labels.txt"
                if not os.path.exists(f"{FR}/renders/param_run/{it['name']}.png") or '--force' in sys.argv: render(it)
            done[it['name']] = it; print('ok', it['name'], it.get('render_s', ''), flush=True)
        except Exception as e:
            print('FAIL', it['name'], repr(e)[:200], flush=True)
        json.dump(list(done.values()), open(mpath, 'w'), indent=1)
