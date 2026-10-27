import os, subprocess, re
ROOT = '/mnt/Drive/PHB'
made, skipped = [], []
def need(sweep, out='plot.png'):
    return not os.path.exists(os.path.join(sweep, out))
def gnuplot(gp_path, lines):
    open(gp_path, 'w').write('\n'.join(lines) + '\n')
    subprocess.run(['gnuplot', os.path.basename(gp_path)], check=True, cwd=os.path.dirname(gp_path))
# 1. T-sweep .ign style: output/<T>/energy.ign|energy2.ign
ign_sweeps = ['PHBdegub/Ka100','PHBdegub/box300','PHBdegub/sh0ab100','PHBdegub/sh0alpha0.01',
 'PHBdegub/sh0alpha0.03','PHBdegub/sh0alpha0.05','PHBdegub/sh0alpha0.12','PHBdegub/small0.01',
 'PHBdegub/small0.01a0.01','PHBdegub/small0.01a0.05','PHBdegub/small0.01a0.15','PHBdegub/small0.1',
 'PHBdegub/small30','PHBcg/PHBlb/13p','PHBcg/PHBlb/100p']
for s in ign_sweeps:
    sw = os.path.join(ROOT, s)
    outdir = os.path.join(sw, 'output')
    if not os.path.isdir(outdir): skipped.append((s,'no output/')); continue
    series = []
    for t in sorted(os.listdir(outdir)):
        for fn in ('energy.ign','energy2.ign'):
            p = os.path.join(outdir, t, fn)
            if os.path.isfile(p) and os.path.getsize(p) > 0:
                series.append((t, os.path.join('output', t, fn))); break
    if not series: skipped.append((s,'no energy files')); continue
    if not need(sw): skipped.append((s,'has plot.png')); continue
    lines = ['set terminal png', 'set output "plot.png"', 'set xlabel "Time (SU)"',
             'set ylabel "Energy (SU)"', 'set logscale x', '']
    for k,(t,rel) in enumerate(series):
        cmd = 'plot' if k==0 else 'replot'
        lines.append(f'{cmd} "{rel}" u 1:4 w l t "T={t}"')
    lines += ['set output \'plot.png\'', 'replot']
    gnuplot(os.path.join(sw,'plot.gp'), lines)
    made.append(s)
# 2. replica energy.dat style: output/<i>/energy.dat
rep_sweeps = []
for base in ['50helix','60helix','560helix']:
    b = os.path.join(ROOT, base)
    if os.path.isdir(b):
        rep_sweeps += [os.path.join(b,d) for d in sorted(os.listdir(b)) if os.path.isdir(os.path.join(b,d,'output'))]
for base in ['PHB/50helix','PHB/60helix','PHB/560helix']:
    b = os.path.join(ROOT, base)
    if os.path.isdir(b):
        rep_sweeps += [os.path.join(b,d) for d in sorted(os.listdir(b)) if os.path.isdir(os.path.join(b,d,'output'))]
rep_sweeps += [os.path.join(ROOT,'Helix/Single'),
               os.path.join(ROOT,'PHBdna2/duplex/10T'), os.path.join(ROOT,'PHBdna2/duplex/15T'),
               os.path.join(ROOT,'PHBdna2/duplex/20T'), os.path.join(ROOT,'PHBdna2/simplex/15T'),
               os.path.join(ROOT,'PHBdna2/simplex/20T')]
for sw in rep_sweeps:
    outdir = os.path.join(sw,'output')
    series = []
    for i in sorted(os.listdir(outdir)):
        p = os.path.join(outdir, i, 'energy.dat')
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            series.append((i, os.path.join('output', i, 'energy.dat')))
    s = os.path.relpath(sw, ROOT)
    if not series: skipped.append((s,'no energy files')); continue
    if not need(sw): skipped.append((s,'has plot.png')); continue
    lines = ['set terminal png', 'set output "plot.png"', 'set xlabel "Time (SU)"',
             'set ylabel "Energy (SU)"', 'set logscale x', '']
    for k,(i,rel) in enumerate(series):
        cmd = 'plot' if k==0 else 'replot'
        lines.append(f'{cmd} "{rel}" u 1:4 w l t "{i}"')
    lines += ['set output \'plot.png\'', 'replot']
    gnuplot(os.path.join(sw,'plot.gp'), lines)
    made.append(s)
print('MADE:', len(made))
for s in made: print('  +', s)
print('SKIPPED:', len(skipped))
for s,why in skipped: print('  -', s, f'({why})')
