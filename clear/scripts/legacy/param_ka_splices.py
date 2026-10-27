#!/usr/bin/env python3
"""param_ka: find time discontinuities (splices from restarts / concurrent writers) in sweep energy.dat and
test whether PE jumps (crystal loss) coincide with them. Read-only. -> data/param_ka_splices.json"""
import glob, os, re, json, numpy as np
R='/scratch/sroy85/Github/dna/large_crystal/sweep'
out=[]
for d in sorted(glob.glob(R+'/alpha_*')):
    n=os.path.basename(d); e=d+'/energy.dat'
    if not os.path.exists(e) or os.path.getsize(e)==0: continue
    a=np.array([[float(x) for x in l.split()[:2]] for l in open(e) if len(l.split())>=3])
    t,pe=a[:,0],a[:,1]
    dt=np.diff(t); dpe=np.diff(pe)
    odd=np.where(np.abs(dt-500)>1e-6)[0]          # print interval is 500 time units (1e6 steps)
    big=np.where(np.abs(dpe)>3.0)[0]               # PE/N jump > 3 in one print interval
    rec=dict(name=n,n_lines=len(t),n_tdisc=int(len(odd)),n_tback=int((dt<0).sum()),n_tdup=int((dt==0).sum()),
             n_tforward_jump=int((dt>500+1e-6).sum()),
             big_pe_jumps=[dict(i=int(i),t_before=float(t[i]),t_after=float(t[i+1]),dpe=float(dpe[i]),tdisc=bool(i in set(odd.tolist()))) for i in big[:8]],
             n_big=int(len(big)), n_big_at_tdisc=int(sum(1 for i in big if i in set(odd.tolist()))))
    out.append(rec)
json.dump(out,open('/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data/param_ka_splices.json','w'),indent=1)
tot=sum(r['n_big'] for r in out); at=sum(r['n_big_at_tdisc'] for r in out)
print('dirs',len(out),'big PE jumps',tot,'of which at time discontinuity',at)
for r in out:
    if r['n_big']: print(r['name'][6:],r['n_tdisc'],r['n_tback'],[(round(j['t_before']),round(j['t_after']),round(j['dpe'],1)) for j in r['big_pe_jumps'][:3]])
