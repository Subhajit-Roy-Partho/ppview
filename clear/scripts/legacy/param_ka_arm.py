#!/usr/bin/env python3
"""param_ka: analyse tiny isolated 10-bead PHB arm MD runs (T=0.078, CPU oxDNA, runs in scratchpad) to measure
(a) frame-vs-backbone misalignment phi (Ka), (b) displacement of the patch positions (near-tip on bead0 at -0.1*a1,
far-tip on bead9 at +0.1*a1) from the ideal straight-rod geometry, vs the patch tolerance alpha. -> data/param_ka_arm.json"""
import sys, os, json, numpy as np
ARM = sys.argv[1]; OUT = sys.argv[2]
def load(path, N=10):
    fr = []
    with open(path) as f:
        lines = f.read().split('\n')
    i = 0
    while i + 3 + N <= len(lines):
        if not lines[i].startswith('t ='): break
        blk = np.array([[float(x) for x in l.split()[:9]] for l in lines[i+3:i+3+N]])
        fr.append(blk); i += 3 + N
    return np.array(fr)
res = {}
kT = 0.078
for d in sorted(os.listdir(ARM)):
    if not d.startswith('Ka'): continue
    ka = float(d.split('_')[0][2:]); kb = float(d.split('_')[1][2:])
    X = load(f'{ARM}/{d}/trajectory.dat'); X = X[len(X)//5:]
    pos, a1 = X[:, :, 0:3], X[:, :, 3:6]
    t = pos[:, 1:] - pos[:, :-1]; th = t / np.linalg.norm(t, axis=2, keepdims=True)
    phi = np.degrees(np.arccos(np.clip(np.sum(a1[:, :9] * th, axis=2), -1, 1)))     # beads 0..8 (Ka acts on these)
    cosphi = np.sum(a1[:, :9] * th, axis=2).mean()
    # bending between consecutive frames u_i.u_{i+1}
    cb = np.sum(a1[:, :-1] * a1[:, 1:], axis=2).mean()
    # patch displacement from ideal straight geometry
    p0 = pos[:, 0] - 0.1 * a1[:, 0]; p0i = pos[:, 0] - 0.1 * th[:, 0]            # near-tip: ideal along bond 0->1
    p9 = pos[:, 9] + 0.1 * a1[:, 9]; p9i = pos[:, 9] + 0.1 * th[:, 8]            # far-tip: ideal along bond 8->9
    d0 = np.linalg.norm(p0 - p0i, axis=1); d9 = np.linalg.norm(p9 - p9i, axis=1)
    # far-tip patch vs rigid straight arm clamped to bead-0 frame u0: p_ideal = r0 + u0*(9*0.2+0.1)
    pid = pos[:, 0] + a1[:, 0] * 1.9
    dclamp = np.linalg.norm(p9 - pid, axis=1)
    res[d] = dict(Ka=ka, Kb=kb, n_frames=int(len(X)), phi_rms_deg=float(np.sqrt((phi**2).mean())), phi_mean_deg=float(phi.mean()),
                  phi_theory_rms_deg=float(np.degrees(np.sqrt(2*kT/ka))), cosphi=float(cosphi), cosphi_theory=float(1/np.tanh(ka/kT)-kT/ka),
                  cos_bend=float(cb), cos_bend_theory=float(1/np.tanh(kb/kT)-kT/kb),
                  near_tip_dev_rms=float(np.sqrt((d0**2).mean())), near_tip_dev_p95=float(np.percentile(d0, 95)),
                  far_tip_dev_rms=float(np.sqrt((d9**2).mean())), far_tip_dev_p95=float(np.percentile(d9, 95)),
                  far_tip_clamp_rms=float(np.sqrt((dclamp**2).mean())), far_tip_clamp_p95=float(np.percentile(dclamp, 95)),
                  Lp_theory=float(0.2*kb/kT))
    r = res[d]; print(d, {k: round(v, 4) for k, v in r.items() if isinstance(v, float)})
json.dump(res, open(OUT, 'w'), indent=1)
