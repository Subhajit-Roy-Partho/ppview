#!/usr/bin/env python3
"""param_ka: paired statistics (Ka 100 vs 300 etc.) on data/param_ka_table.json -> data/param_ka_stats.json"""
import json, numpy as np
from scipy import stats
F='/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data'
rows=json.load(open(F+'/param_ka_table.json'))
for r in rows:
    for tag in ('1e6','1e7'):
        b=r.get('bonds_'+tag)
        r['ret_'+tag]=b/r['start_bonds'] if b is not None else None
    r['ret_end']=r['end_bonds']/r['start_bonds'] if 'end_bonds' in r else None
    r['ret_prelast']=r['pre_last_bonds']/r['start_bonds'] if r.get('pre_last_bonds') is not None else None
key=lambda r:(r['alpha'],r['Kb'],r['strength'])
by={}
for r in rows: by.setdefault(key(r),{})[r['Ka']]=r
def paired(metric,sel=lambda k:True,fa=100.0,fb=300.0,var='Ka'):
    d=[];pairs=[]
    for k,v in by.items():
        if not sel(k): continue
        if fa in v and fb in v and v[fa].get(metric) is not None and v[fb].get(metric) is not None:
            d.append(v[fb][metric]-v[fa][metric]); pairs.append((k,v[fa][metric],v[fb][metric]))
    d=np.array(d)
    if len(d)==0: return None
    out=dict(n=len(d),median_diff=float(np.median(d)),mean_diff=float(d.mean()),sd_diff=float(d.std(ddof=1)) if len(d)>1 else None,
             n_ka300_higher=int((d>0).sum()),n_ka100_higher=int((d<0).sum()),n_tie=int((d==0).sum()))
    nz=d[d!=0]
    if len(nz)>=1:
        out['sign_p']=float(stats.binomtest(int((nz>0).sum()),len(nz),0.5).pvalue)
    if len(nz)>=6:
        try: out['wilcoxon_p']=float(stats.wilcoxon(nz).pvalue)
        except Exception as e: out['wilcoxon_p']=None
    if len(d)>1 and d.std(ddof=1)>0: out['cohen_dz']=float(d.mean()/d.std(ddof=1))
    # Hodges-Lehmann (median of Walsh averages)
    w=[(d[i]+d[j])/2 for i in range(len(d)) for j in range(i,len(d))]; out['hodges_lehmann']=float(np.median(w))
    return out
def Kbpaired(metric,sel):
    out=[]
    for (a,kb,s),v in by.items():
        pass
S={}
sets={'all_alpha>=0.03':lambda k:k[0]>=0.03,'alpha>=0.05_str>=10':lambda k:k[0]>=0.05 and k[2]>=10,
      'alpha>=0.10_str>=10':lambda k:k[0]>=0.10 and k[2]>=10,'alpha=0.03':lambda k:k[0]==0.03,'alpha=0.03_str>=10':lambda k:k[0]==0.03 and k[2]>=10,'alpha=0.03_str>=90':lambda k:k[0]==0.03 and k[2]>=90,
      'alpha=0.05':lambda k:k[0]==0.05,'alpha=0.10':lambda k:k[0]==0.10,'alpha=0.12':lambda k:k[0]==0.12,'strength=1':lambda k:k[2]==1}
for m in ('ret_1e6','ret_1e7','pre_last_lc','pe_1e6','pe_5e6','ret_end','end_lc','end_bonds','end_tetra'):
    S[m]={sn:paired(m,sf) for sn,sf in sets.items()}
# Ka effect on first-frame bond count after normalising by start
# Kb effect (100 vs 300) pooled over Ka
def pair_other(metric,var,va,vb,sel):
    d=[]
    idx={}
    for r in rows:
        k=(r['alpha'],r['Ka'],r['Kb'],r['strength']); idx[k]=r
    for (a,ka,kb,s),r in idx.items():
        if var=='Kb' and kb==va and (a,ka,vb,s) in idx and sel((a,kb,s)):
            x,y=r.get(metric),idx[(a,ka,vb,s)].get(metric)
            if x is not None and y is not None: d.append(y-x)
        if var=='strength' and s==va and (a,ka,kb,vb) in idx and sel((a,kb,s)):
            x,y=r.get(metric),idx[(a,ka,kb,vb)].get(metric)
            if x is not None and y is not None: d.append(y-x)
    d=np.array(d)
    if not len(d): return None
    nz=d[d!=0]
    o=dict(n=len(d),median_diff=float(np.median(d)),mean_diff=float(d.mean()),n_pos=int((d>0).sum()),n_neg=int((d<0).sum()))
    if len(nz): o['sign_p']=float(stats.binomtest(int((nz>0).sum()),len(nz),0.5).pvalue)
    if len(nz)>=6:
        try: o['wilcoxon_p']=float(stats.wilcoxon(nz).pvalue)
        except: pass
    return o
S['Kb_300_minus_100']={m:pair_other(m,'Kb',100.0,300.0,lambda k:k[0]>=0.05 and k[2]>=10) for m in ('ret_1e6','ret_1e7','pre_last_lc','pe_5e6','end_lc')}
S['Kb_300_minus_100_alpha0.03']={m:pair_other(m,'Kb',100.0,300.0,lambda k:k[0]==0.03 and k[2]>=10) for m in ('ret_1e6','ret_1e7')}
# marginal means
marg={}
for var in ('alpha','Ka','Kb','strength'):
    marg[var]={}
    for v in sorted({r[var] for r in rows}):
        for m in ('ret_1e6','ret_1e7','end_lc','pe_5e6'):
            xs=[r[m] for r in rows if r[var]==v and r.get(m) is not None]
            marg[var].setdefault(str(v),{})[m]=dict(mean=float(np.mean(xs)) if xs else None,n=len(xs))
# splice summary
sp=[r for r in rows if r.get('splice_t_before_steps')]
spl=dict(n_with_splice=len(sp),n_no_splice=len([r for r in rows if r['alpha']>=0.03])-len(sp),
         no_splice=[r['name'] for r in rows if r['alpha']>=0.03 and not r.get('splice_t_before_steps')],
         after_steps_values=sorted({r['splice_t_after_steps'] for r in sp}))
# dPE at splice vs strength for alpha>=0.10
x=np.array([r['strength'] for r in sp if r['alpha']>=0.10 and r['splice_dpe'] is not None and r['splice_t_after_steps']>2.2e8-1e6 and r['splice_t_after_steps']<2.3e8]);y=np.array([r['splice_dpe'] for r in sp if r['alpha']>=0.10 and r['splice_dpe'] is not None and r['splice_t_after_steps']>2.2e8-1e6 and r['splice_t_after_steps']<2.3e8])
if len(x)>2:
    sl=np.polyfit(x,y,1); spl['dpe_vs_strength_fit']=dict(slope=float(sl[0]),intercept=float(sl[1]),n=int(len(x)),r=float(np.corrcoef(x,y)[0,1]))
# retained runs
ret=[r['name'] for r in rows if r.get('end_lc') and r['end_lc']>0.3]
json.dump(dict(paired_Ka=S,marginals=marg,splice=spl,retained_end_lc_gt_0p3=ret),open(F+'/param_ka_stats.json','w'),indent=1)
for m in ('ret_1e6','ret_1e7','pre_last_lc','pe_5e6','end_lc','ret_end'):
    print('==',m)
    for sn,v in S[m].items():
        if v: print(f"  {sn:24s} n={v['n']:2d} med={v['median_diff']:+.4f} mean={v['mean_diff']:+.4f} Ka300>:{v['n_ka300_higher']} Ka100>:{v['n_ka100_higher']} tie:{v['n_tie']} sign_p={v.get('sign_p')} wil_p={v.get('wilcoxon_p')} dz={v.get('cohen_dz')}")
print(S['Kb_300_minus_100']); print(S['Kb_300_minus_100_alpha0.03']); print(spl); print(ret)
