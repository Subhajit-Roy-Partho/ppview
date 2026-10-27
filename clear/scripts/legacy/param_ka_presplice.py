#!/usr/bin/env python3
"""param_ka: build the per-run table of PRE-splice (clean-history) observables + end-state, from
data/param_ka_endpoints.json, data/param_ka_ts/*.json, data/param_ka_splices.json and energy.dat. -> data/param_ka_table.json"""
import json, glob, os, numpy as np
F='/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data'
R='/scratch/sroy85/Github/dna/large_crystal/sweep'
ep={r['name']:r for r in json.load(open(F+'/param_ka_endpoints.json'))}
rows=[]
for n,r in sorted(ep.items()):
    row=dict(name=n,alpha=r['alpha'],Ka=r['Ka'],Kb=r['Kb'],strength=r['strength'])
    s=r.get('start_c0.3'); row['start_bonds']=s['n_bonds']; row['start_lc']=s['lc']; row['start_valence']=s['valence']
    row['start_tetra']=s['tetra']; row['start_mean_d']=s['mean_bond_d']
    e=r.get('end_c0.3')
    if e:
        row.update(end_bonds=e['n_bonds'],end_lc=e['lc'],end_valence=e['valence'],end_tetra=e['tetra'],end_anchors=e['anchors'],end_t=e['t'])
        row['end_bonds_c01']=r['end_c0.1']['n_bonds']
    ef=R+'/'+n+'/energy.dat'
    if os.path.exists(ef) and os.path.getsize(ef)>0:
        a=np.array([[float(x) for x in l.split()[:2]] for l in open(ef) if len(l.split())>=3]); t,pe=a[:,0],a[:,1]
        dt=np.diff(t); j=np.where((np.abs(dt-500)>1e-6)&(dt!=0))[0]
        row['splice_t_before_steps']=float(2000*t[j[0]]) if len(j) else None   # first forward jump (steps)
        row['splice_t_after_steps']=float(2000*t[j[0]+1]) if len(j) else None
        row['splice_dpe']=float(pe[j[0]+1]-pe[j[0]]) if len(j) else None
        pre=slice(0,(j[0]+1) if len(j) else len(t))
        tp,pp=t[pre],pe[pre]
        def at(x): 
            k=np.searchsorted(tp,x); return float(pp[min(k,len(pp)-1)]) if len(pp) and tp[min(k,len(tp)-1)]>=x*0.99 else None
        row['pe_1e6']=float(pp[0]); row['pe_5e6']=at(2500); row['pe_1e7']=at(5000); row['pe_pre_last']=float(pp[-1]); row['t_pre_last_steps']=float(2000*tp[-1])
    tsf=F+'/param_ka_ts/'+n+'.json'
    if os.path.exists(tsf):
        fr=json.load(open(tsf))['frames']
        lim=row.get('splice_t_before_steps') or 1e99
        pre=[f for f in fr if f['t']<=lim+1.5e6]
        row['ts']=[dict(t=f['t'],bonds=f['c0.3']['n_bonds'],lc=f['c0.3']['lc'],val=f['c0.3']['valence'],anch=f['c0.3']['anchors'],tet=f['c0.3']['tetra'],bonds01=f['c0.1']['n_bonds']) for f in fr]
        if pre:
            def near(x):
                return min(pre,key=lambda f:abs(f['t']-x))
            for tag,x in (('1e6',1e6),('1e7',1e7),('1e8',1e8)):
                f=near(x)
                if abs(f['t']-x)<=0.2*x+1e6 and f['t']<=lim+1.5e6: row['bonds_'+tag]=f['c0.3']['n_bonds']; row['lc_'+tag]=f['c0.3']['lc']; row['bonds01_'+tag]=f['c0.1']['n_bonds']; row['tet_'+tag]=f['c0.3']['tetra']
            row['pre_last_bonds']=pre[-1]['c0.3']['n_bonds']; row['pre_last_lc']=pre[-1]['c0.3']['lc']; row['pre_last_t']=pre[-1]['t']
    rows.append(row)
json.dump(rows,open(F+'/param_ka_table.json','w'),indent=1)
import csv
keys=[k for k in rows[2].keys() if k!='ts']
with open(F+'/param_ka_table.csv','w') as fh:
    w=csv.DictWriter(fh,fieldnames=sorted({k for r in rows for k in r if k!='ts'}),extrasaction='ignore'); w.writeheader(); [w.writerow(r) for r in rows]
for r in rows:
    if r['alpha']>=0.03: print(r['name'][6:],r.get('splice_t_before_steps'),r.get('splice_dpe') and round(r['splice_dpe'],1),r.get('bonds_1e6'),r.get('bonds_1e7'),r.get('bonds_1e8'),r.get('lc_1e8'),r.get('pre_last_t'),r.get('pre_last_bonds'),r.get('pre_last_lc'))
