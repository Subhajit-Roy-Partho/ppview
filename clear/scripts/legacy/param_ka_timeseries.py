#!/usr/bin/env python3
"""param_ka: sample ~16 frames from each large trajectory.dat (35-55 GB, ~17 MB/frame) of large_crystal/sweep using
byte-offset seeking (no full scan), analyse each with the PBC-safe cluster_labels code (cutoff 0.3).
Read-only. Resumable: results cached per dir in data/param_ka_ts/<name>.json. Output merged to data/param_ka_timeseries.json"""
import sys, os, re, json, glob, time
import numpy as np
sys.path.insert(0, '/scratch/sroy85/Github/dna/large_crystal/hand5/final_report')
import cluster_labels as cl
R = '/scratch/sroy85/Github/dna/large_crystal/sweep'
D = '/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/data'
os.makedirs(D + '/param_ka_ts', exist_ok=True)
HDR = re.compile(rb'(?:^|\n)t = ([0-9.eE+-]+)\n')
NPART = 63488

def find_header(f, est, size, fs):
    """first frame header at or after est-w, widening window. returns (offset, t) or None"""
    for w in (0.6e6, 3e6, 10e6, 40e6):
        lo = int(max(0, est - w)); f.seek(lo)
        buf = f.read(int(2 * w))
        m = HDR.search(buf)
        if m:
            off = lo + m.start() + (1 if buf[m.start():m.start() + 1] == b'\n' else 0)
            return off, float(m.group(1))
    return None

def read_frame(f, off, fs, size):
    f.seek(off)
    buf = f.read(int(fs * 1.06) + 2_000_000)
    ms = list(HDR.finditer(buf, 20))
    end = (ms[0].start() + 1) if ms else len(buf)
    txt = buf[:end].decode()
    lines = txt.split('\n')
    if len([l for l in lines[3:] if l.strip()]) != NPART:
        return None
    return cl.parse_frame_text(txt)

def sample_indices(nfr):
    log = np.unique(np.round(np.logspace(0, np.log10(max(nfr - 1, 2)), 18)).astype(int))
    lin = np.round(np.linspace(0, nfr - 1, 14)).astype(int)
    return sorted(set([0]) | set(log.tolist()) | set(lin.tolist()))

def run(d):
    n = os.path.basename(d); cache = f'{D}/param_ka_ts/{n}.json'
    if os.path.exists(cache): return
    tp = d + '/trajectory.dat'
    if not os.path.exists(tp) or os.path.getsize(tp) < 1e8: return
    size = os.path.getsize(tp)
    topo = cl.load_topology(d + '/input.phb')
    fs0 = os.path.getsize(d + '/last_conf.dat') if os.path.exists(d + '/last_conf.dat') else 17.2e6
    f = open(tp, 'rb')
    # last header (for frame count)
    f.seek(max(0, size - int(2.2 * fs0))); tail = f.read()
    ms = list(HDR.finditer(tail))
    t_last = float(ms[-1].group(1)) if ms else None
    off_last = size - len(tail) + ms[-1].start() + (1 if tail[ms[-1].start():ms[-1].start() + 1] == b'\n' else 0)
    nfr = int(round(size / fs0))
    fs_avg = off_last / max(nfr - 1, 1)
    res = []; last = (0, 0)  # (frame idx, offset)
    for j in sample_indices(nfr):
        if j == 0: f.seek(0); hit = (0, float(f.readline().split(b'=')[1]))
        else:
            fs_loc = fs_avg
            est = last[1] + (j - last[0]) * fs_loc if last[0] > 0 else j * fs_avg
            hit = find_header(f, est, size, fs_loc)
        if hit is None: continue
        off, t = hit
        if off > off_last + 1: continue
        fr = read_frame(f, off, fs_avg, size)
        if fr is None: continue
        rec = dict(frame=int(j), off=int(off), t=fr[0])
        for cut in (0.3, 0.1):
            r = cl.analyze_conf(topo, conf=fr, cutoff=cut)
            s = cl.summarize(topo, r, cut)
            rec[f'c{cut}'] = dict(n_bonds=s['n_patch_bonds'], lc=s['largest_cluster_fraction'], valence=s['mean_valence'],
                                  f_v6=s['fraction_valence6'], tetra=s['tetra_per_molecule'],
                                  anchors=s['anchors_intact'] / (3.0 * topo['n_mol']), n_clusters_ge2=s['n_clusters_ge2'])
        res.append(rec)
        if last[0] == 0 or j > last[0]:
            if j > 0 and len(res) >= 2: last = (j, off)
            elif j > 0: last = (j, off)
        print(n, j, off, fr[0], round(rec['c0.3']['lc'], 3), flush=True)
    json.dump(dict(name=n, nfr_est=nfr, fs_avg=fs_avg, frames=res), open(cache, 'w'))

if __name__ == '__main__':
    os.nice(10)
    ds = sorted(glob.glob(R + '/alpha_*'))
    if len(sys.argv) > 1: ds = [d for d in ds if any(a in d for a in sys.argv[1:])]
    for d in ds:
        t0 = time.time(); run(d); print('done', os.path.basename(d), round(time.time() - t0, 1), flush=True)
