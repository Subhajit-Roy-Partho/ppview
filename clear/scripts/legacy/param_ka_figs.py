#!/usr/bin/env python3
"""param_ka: figures -> final_report/figs/param_ka_*.png (matplotlib, 200 dpi, Okabe-Ito colourblind-safe palette)."""
import json, os, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
FR='/scratch/sroy85/Github/dna/large_crystal/hand5/final_report'; D=FR+'/data'; O=FR+'/figs'
R='/scratch/sroy85/Github/dna/large_crystal/sweep'
rows=json.load(open(D+'/param_ka_table.json')); arm=json.load(open(D+'/param_ka_arm.json'))
for r in rows:
    r['ret_1e7']=r['bonds_1e7']/r['start_bonds'] if r.get('bonds_1e7') is not None else (r['bonds_1e6']/r['start_bonds'] if r.get('bonds_1e6') is not None else None)
    r['ret_1e6']=r['bonds_1e6']/r['start_bonds'] if r.get('bonds_1e6') is not None else None
C={100.0:'#0072B2',300.0:'#E69F00'}  # Okabe-Ito blue / orange
plt.rcParams.update({'figure.facecolor':'white','axes.facecolor':'white','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.25})
def get(a,ka,kb,s): 
    for r in rows:
        if (r['alpha'],r['Ka'],r['Kb'],r['strength'])==(a,ka,kb,s): return r
def energy(n):
    a=np.array([[float(x) for x in l.split()[:2]] for l in open(f'{R}/{n}/energy.dat') if len(l.split())>=3]); return a[:,0]*2000,a[:,1]
# ---- fig1: PE/N traces
fig,ax=plt.subplots(2,3,figsize=(13,6.5),sharex='col')
for j,a in enumerate((0.05,0.10,0.12)):
    for i,(kb,s) in enumerate(((100.0,100.0),(100.0,150.0))):
        A=ax[i,j]
        for ka in (100.0,300.0):
            r=get(a,ka,kb,s); st,pe=energy(r['name'])
            sp=r.get('splice_t_after_steps'); cut=len(st)
            if r.get('splice_t_before_steps'):
                cut=int(np.argmax(st>=r['splice_t_before_steps']))+1
            A.plot(st[:cut],pe[:cut],color=C[ka],lw=1.6,label=f'Ka={ka:.0f}')
            A.plot(st[cut:],pe[cut:],color=C[ka],lw=1,ls=':',alpha=.8)
            if sp: A.axvline(sp,color='0.4',lw=.7,ls='--')
        A.set_xscale('log'); A.set_title(f'alpha={a}, Kb={kb:.0f}, strength={s:.0f}',fontsize=9)
        if j==0: A.set_ylabel('PE / N')
        if i==1: A.set_xlabel('MD step')
        if i==0 and j==0: A.legend(frameon=False)
fig.suptitle('PE/N vs step, Ka=100 vs 300. Solid: before the step-counter splice; dotted: after (dissolved state). Dashed grey: splice target (2.2e8 steps)',fontsize=10)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig01_energy_traces.png',dpi=200); plt.close(fig)
# ---- heatmaps
alphas=[0.03,0.05,0.10,0.12]; strs=[1.0,10.0,90.0,100.0,150.0]
def hm(metric,fname,title,vmax=1.0,fmt='{:.2f}'):
    fig,ax=plt.subplots(1,4,figsize=(14,3.6),sharey=True)
    for k,(ka,kb) in enumerate(((100.0,100.0),(100.0,300.0),(300.0,100.0),(300.0,300.0))):
        M=np.full((len(alphas),len(strs)),np.nan)
        for i,a in enumerate(alphas):
            for j,s in enumerate(strs):
                r=get(a,ka,kb,s); v=r.get(metric) if r else None
                if v is not None: M[i,j]=v
        im=ax[k].imshow(M,origin='lower',cmap='Blues',vmin=0,vmax=vmax,aspect='auto')
        for i in range(len(alphas)):
            for j in range(len(strs)):
                if not np.isnan(M[i,j]): ax[k].text(j,i,fmt.format(M[i,j]),ha='center',va='center',fontsize=8,color='white' if M[i,j]>.55*vmax else 'black')
                else: ax[k].text(j,i,'n/a',ha='center',va='center',fontsize=8,color='0.5')
        ax[k].set_xticks(range(len(strs)),[f'{s:.0f}' for s in strs]); ax[k].set_yticks(range(len(alphas)),[str(a) for a in alphas])
        ax[k].set_title(f'Ka={ka:.0f}, Kb={kb:.0f}',fontsize=9); ax[k].set_xlabel('crystal-patch strength'); ax[k].grid(False)
    ax[0].set_ylabel('patchyAlpha'); fig.suptitle(title,fontsize=10); fig.colorbar(im,ax=ax,shrink=.8,pad=.01)
    fig.savefig(O+'/'+fname,dpi=200,bbox_inches='tight'); plt.close(fig)
hm('ret_1e7','param_ka_fig02_retention_presplice_heatmaps.png','Inter-molecular patch bonds retained at ~1e7 steps (before any splice), fraction of the start-configuration bond count (alpha=0.01: no MD data)',vmax=1.1)
hm('end_lc','param_ka_fig03_final_largest_cluster_heatmaps.png','Final-frame largest-cluster fraction (cutoff 0.3). Dominated by the step-counter splice, not by the parameters (alpha=0.12/Ka300/Kb300/str150: no final conf)',vmax=0.8)
# ---- fig4 paired scatter
fig,ax=plt.subplots(1,3,figsize=(13,4.2))
cm={0.03:'#CC79A7',0.05:'#009E73',0.10:'#0072B2',0.12:'#D55E00'}
for A,m,lab in ((ax[0],'ret_1e6','bond retention at 1e6 steps'),(ax[1],'ret_1e7','bond retention at ~1e7 steps (pre-splice)'),(ax[2],'end_lc','final largest-cluster fraction')):
    for a in alphas:
        xs=[];ys=[]
        for (al,kb,s) in {(r['alpha'],r['Kb'],r['strength']) for r in rows if r['alpha']==a}:
            p,q=get(al,100.0,kb,s),get(al,300.0,kb,s)
            if p and q and p.get(m) is not None and q.get(m) is not None: xs.append(p[m]);ys.append(q[m])
        A.scatter(xs,ys,s=34,color=cm[a],edgecolor='white',lw=.6,label=f'alpha={a}',zorder=3)
    A.plot([0,1.1],[0,1.1],color='0.3',lw=1); A.set_xlabel('Ka=100'); A.set_ylabel('Ka=300'); A.set_title(lab,fontsize=9); A.set_xlim(-.03,1.1); A.set_ylim(-.03,1.1)
ax[0].legend(frameon=False,fontsize=8); fig.suptitle('Paired comparison, each point = same (alpha, Kb, strength); y=x means no Ka effect',fontsize=10)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig04_paired_Ka_scatter.png',dpi=200); plt.close(fig)
# ---- fig5 alpha / strength / Kb response (pre-splice retention)
fig,ax=plt.subplots(1,3,figsize=(13,4))
for ka in (100.0,300.0):
    for kb,ls in ((100.0,'-'),(300.0,'--')):
        ys=[np.mean([r['ret_1e6'] for r in rows if r['alpha']==a and r['Ka']==ka and r['Kb']==kb and r['strength']>=10 and r['ret_1e6'] is not None]) for a in alphas]
        ax[0].plot(alphas,ys,marker='o',color=C[ka],ls=ls,label=f'Ka={ka:.0f}, Kb={kb:.0f}')
ax[0].set_xlabel('patchyAlpha'); ax[0].set_ylabel('bonds at 1e6 steps / start (strength>=10)'); ax[0].legend(frameon=False,fontsize=8); ax[0].set_title('alpha response')
for a in alphas:
    ys=[np.mean([r['ret_1e6'] for r in rows if r['alpha']==a and r['strength']==s and r['ret_1e6'] is not None]) for s in strs]
    ax[1].plot(range(len(strs)),ys,marker='o',color=cm[a],label=f'alpha={a}')
ax[1].set_xticks(range(len(strs)),[f'{s:.0f}' for s in strs]); ax[1].set_xlabel('crystal-patch strength'); ax[1].legend(frameon=False,fontsize=8); ax[1].set_title('strength response (mean over Ka,Kb)')
for ka in (100.0,300.0):
    for kb in (100.0,300.0): pass
x=np.arange(len(alphas)); w=.2
for k,(ka,kb) in enumerate(((100.0,100.0),(100.0,300.0),(300.0,100.0),(300.0,300.0))):
    ys=[np.mean([r['ret_1e7'] for r in rows if r['alpha']==a and r['Ka']==ka and r['Kb']==kb and r['strength']>=10 and r['ret_1e7'] is not None]) for a in alphas]
    ax[2].bar(x+(k-1.5)*w,ys,w,color=C[ka],alpha=1.0 if kb==100 else .55,label=f'Ka={ka:.0f}, Kb={kb:.0f}')
ax[2].set_xticks(x,[str(a) for a in alphas]); ax[2].set_xlabel('patchyAlpha'); ax[2].set_ylabel('bonds at ~1e7 steps / start'); ax[2].set_title('Kb (shade) and Ka (colour), strength>=10'); ax[2].legend(frameon=False,fontsize=7)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig05_alpha_strength_Kb_response.png',dpi=200); plt.close(fig)
# ---- fig6 theory vs MD
kT=0.078; fig,ax=plt.subplots(1,3,figsize=(13,4))
ka=np.logspace(0.8,2.8,100); ax[0].plot(ka,np.degrees(np.sqrt(2*kT/ka)),color='0.2',label='theory sqrt(2kT/Ka)')
for k,v in arm.items():
    if v['Kb']==100.0: ax[0].scatter(v['Ka'],v['phi_rms_deg'],color='#0072B2',zorder=3,s=36)
ax[0].scatter([],[],color='#0072B2',label='isolated-arm MD (10 beads, T=0.078)'); ax[0].axvline(100,color=C[100.0],lw=.8); ax[0].axvline(300,color=C[300.0],lw=.8)
ax[0].set_xscale('log'); ax[0].set_yscale('log'); ax[0].set_xlabel('Ka'); ax[0].set_ylabel('rms angle(bead axis, backbone) [deg]'); ax[0].legend(frameon=False,fontsize=8)
ax[0].set_title('Ka sets frame jitter: 2.3 deg (100) -> 1.3 deg (300)',fontsize=9)
al=np.array([0.01,0.03,0.05,0.10,0.12]); wd=.35
for k,(kaa) in enumerate((100.0,300.0)):
    v=arm[f'Ka{kaa:.0f}_Kb100']
    ax[1].bar(np.arange(5)+(k-.5)*wd,v['far_tip_dev_p95']/al,wd,color=C[kaa],label=f'Ka={kaa:.0f} far-tip patch, 95th pct')
ax[1].axhline(1,color='k',lw=.8); ax[1].set_xticks(range(5),[str(a) for a in al]); ax[1].set_yscale('log'); ax[1].set_ylim(.03,3); ax[1].set_xlabel('patchyAlpha'); ax[1].set_ylabel('patch displacement / alpha'); ax[1].legend(frameon=False,fontsize=8,loc='upper right')
ax[1].set_title('Frame-jitter displacement of the tip patch relative to alpha (Kb=100)',fontsize=9)
kbs=sorted({v['Kb'] for v in arm.values() if v['Ka']==300.0}); ax[2].plot(kbs,[arm[f'Ka300_Kb{k:.0f}']['far_tip_clamp_rms'] for k in kbs],marker='o',color='#009E73',label='far-tip patch, arm axis pinned at bead 0 (rms)')
ax[2].plot(kbs,[arm[f'Ka300_Kb{k:.0f}']['far_tip_dev_rms'] for k in kbs],marker='s',color='#CC79A7',label='far-tip patch vs local backbone (rms)')
for a in (0.03,0.10): ax[2].axhline(a,color='0.4',lw=.8,ls='--'); ax[2].text(1.05,a*1.07,f'alpha={a}',fontsize=7)
ax[2].set_xscale('log'); ax[2].set_yscale('log'); ax[2].set_xlabel('Kb (Ka=300)'); ax[2].set_ylabel('displacement [length units]'); ax[2].legend(frameon=False,fontsize=7); ax[2].set_title('Kb sets arm-tip wander (Lp = 0.2 Kb / kT)',fontsize=9)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig06_misalignment_theory_vs_MD.png',dpi=200); plt.close(fig)
# ---- fig7 splice evidence
fig,ax=plt.subplots(1,2,figsize=(12,4.2))
for r in rows:
    if r.get('splice_dpe') is not None and r['alpha']>=0.10 and r['splice_t_after_steps'] and 2.2e8<=r['splice_t_after_steps']<=2.24e8:
        ax[0].scatter(r['strength'],r['splice_dpe'],color=C[r['Ka']],s=30,alpha=.8)
xx=np.array([0,150]); ax[0].plot(xx,0.173*xx,color='0.3',lw=1,label='0.173 x strength')
ax[0].scatter([],[],color=C[100.0],label='Ka=100'); ax[0].scatter([],[],color=C[300.0],label='Ka=300'); ax[0].legend(frameon=False); ax[0].set_xlabel('crystal-patch strength'); ax[0].set_ylabel('PE/N jump at the splice'); ax[0].set_title('PE jump at the splice depends only on strength (alpha>=0.10)',fontsize=9)
for n,c,ls in (('alpha_0.10_Ka_100.0_Kb_100.0_str_150.0',C[100.0],'-'),('alpha_0.10_Ka_300.0_Kb_100.0_str_150.0',C[300.0],'-'),('alpha_0.12_Ka_100.0_Kb_100.0_str_100.0',C[100.0],'--'),('alpha_0.12_Ka_300.0_Kb_100.0_str_100.0',C[300.0],'--'),('alpha_0.05_Ka_300.0_Kb_300.0_str_150.0','#009E73','-')):
    ts=json.load(open(f'{D}/param_ka_ts/{n}.json'))['frames']
    ax[1].plot([f['t'] for f in ts],[f['c0.3']['n_bonds'] for f in ts],marker='.',color=c,ls=ls,label=n[6:])
ax[1].set_xscale('log'); ax[1].set_xlabel('step counter (as recorded)'); ax[1].set_ylabel('inter-molecular patch bonds'); ax[1].legend(frameon=False,fontsize=6.5); ax[1].set_title('Bond count in trajectory frames: stable, then abrupt loss at 2.2e8',fontsize=9)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig07_splice_evidence.png',dpi=200); plt.close(fig)
# ---- fig8 kinetics alpha=0.03 and 0.05 early
fig,ax=plt.subplots(1,3,figsize=(13,3.8))
for A,(a,kb,s) in zip(ax,((0.03,100.0,100.0),(0.03,300.0,10.0),(0.05,300.0,100.0))):
    for ka in (100.0,300.0):
        r=get(a,ka,kb,s); ts=r.get('ts') or []
        lim=r.get('splice_t_before_steps') or 1e99
        x=[f['t'] for f in ts if f['t']<=lim+1.5e6]; y=[f['bonds']/r['start_bonds'] for f in ts if f['t']<=lim+1.5e6]
        A.plot(x,y,marker='o',ms=3,color=C[ka],label=f'Ka={ka:.0f}')
    A.axhline(1.0,color='0.5',ls=':',lw=1); A.set_xscale('log'); A.set_xlabel('MD step (pre-splice only; dotted = start config)'); A.set_title(f'alpha={a}, Kb={kb:.0f}, strength={s:.0f}',fontsize=9); A.set_ylim(-.02,1.1)
ax[0].set_ylabel('bonds / start bonds'); ax[0].legend(frameon=False)
fig.tight_layout(); fig.savefig(O+'/param_ka_fig08_early_kinetics.png',dpi=200); plt.close(fig)
print('ok')
