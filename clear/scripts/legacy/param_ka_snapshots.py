#!/usr/bin/env python3
"""param_ka: snapshot representative confs (start / last pre-splice sampled frame <=~1e8 steps / final last_conf) into
final_report/clusters/param_ka_<tag>.conf.dat (+ topology copy), label them with cluster_labels, write manifest."""
import sys, os, json, shutil, subprocess
sys.path.insert(0,'/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/legacy_scripts'); sys.path.insert(0,'/scratch/sroy85/Github/dna/large_crystal/hand5/final_report')
import param_ka_timeseries as T
R=T.R; FR='/scratch/sroy85/Github/dna/large_crystal/hand5/final_report'; CL=FR+'/clusters'
RUNS=[(0.10,100.,100.,150.),(0.10,300.,100.,150.),(0.05,100.,100.,100.),(0.05,300.,100.,100.),(0.03,100.,300.,10.),(0.03,300.,300.,10.),
      (0.12,100.,300.,100.),(0.12,300.,300.,100.),(0.10,100.,100.,1.),(0.05,300.,300.,150.)]
def nm(a,ka,kb,s): return f'alpha_{a:.2f}_Ka_{ka:.1f}_Kb_{kb:.1f}_str_{s:.1f}'
def short(a,ka,kb,s): return f'a{a:.2f}_Ka{ka:.0f}_Kb{kb:.0f}_s{s:.0f}'
man=[]
def add(tag,conf_text=None,conf_path=None,run=None,state=None,note=''):
    out=f'{CL}/param_ka_{tag}.conf.dat'
    if conf_text is not None: open(out,'w').write(conf_text)
    else: shutil.copy(conf_path,out)
    top=f'{CL}/param_ka_{tag}.topology.phb'; shutil.copy(R+'/'+run+'/input.phb',top)
    man.append(dict(tag=tag,run=run,state=state,note=note,conf=out,top=top))
tab={r['name']:r for r in json.load(open(FR+'/data/param_ka_table.json'))}
for a,ka,kb,s in RUNS:
    n=nm(a,ka,kb,s); d=R+'/'+n; r=tab[n]; sh=short(a,ka,kb,s)
    if not os.path.exists(CL+f'/param_ka_start__{sh}.conf.dat') and ka==100.:
        pass
    ts=json.load(open(f'{FR}/data/param_ka_ts/{n}.json'))['frames']
    lim=r.get('splice_t_before_steps') or 1e99
    pre=[f for f in ts if f['t']<=lim+1.5e6 and f['t']<=1.1e8]
    if pre:
        f=pre[-1]; fh=open(d+'/trajectory.dat','rb'); fh.seek(f['off']); b=fh.read(int(17.2e6*1.06)+2_000_000)
        ms=list(T.HDR.finditer(b,20)); txt=b[:(ms[0].start()+1) if ms else len(b)].decode()
        add(f'pre__{sh}',conf_text=txt,run=n,state='pre-splice',note=f"trajectory frame t={f['t']:.3g} steps")
    if os.path.exists(d+'/last_conf.dat'):
        add(f'final__{sh}',conf_path=d+'/last_conf.dat',run=n,state='final',note=f"last_conf.dat t={r.get('end_t'):.3g} steps")
# start refs (alpha-specific MC-relaxed starts)
add('start__a0.10_Ka100_Kb100_s150',conf_path=R+'/'+nm(0.10,100.,100.,150.)+'/mc_relaxed.dat',run=nm(0.10,100.,100.,150.),state='start',note='mc_relaxed.dat (MD input), alpha=0.10')
add('start__a0.01_Ka100_Kb100_s100',conf_path=R+'/'+nm(0.01,100.,100.,100.)+'/mc_relaxed.dat',run=nm(0.01,100.,100.,100.),state='start(alpha=0.01, MC never converged)',note='mc_relaxed.dat, E_MC=-100/N')
ref='/scratch/sroy85/Github/dna/large_crystal/large_crystal_min.dat'
add('start__large_crystal_min',conf_path=ref,run=nm(0.10,100.,100.,150.),state='start (shared large_crystal_min.dat t=10000)',note='shared MC-relaxed seed config of the sweep')
for m in man:
    base=m['conf'][:-len('.conf.dat')]
    subprocess.run(['python3',FR+'/cluster_labels.py','--top',m['top'],'--conf',m['conf'],'--out',base+'.labels.txt','--json',base+'.summary.json'],check=True,stdout=subprocess.DEVNULL)
    s=json.load(open(base+'.summary.json')); m.update(labels=base+'.labels.txt',summary=base+'.summary.json',lc=s['largest_cluster_fraction'],n_bonds=s['n_patch_bonds'],valence=s['mean_valence'],tetra=s['tetra_per_molecule'])
    print(m['tag'],round(m['lc'],3),m['n_bonds'],flush=True)
json.dump(man,open(CL+'/param_ka_manifest.json','w'),indent=1)
