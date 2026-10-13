"""Writes the mrdna fixtures PPView's tests read.

Runs mrdna-relax (the mrdna package in ../mrdna_project, OpenMM) on the tetrahelix, so the files
are exactly what a real mrdna run writes. Alongside each run it records what the bead model says
every bead and bond is, which is what the JavaScript classification is tested against.

usage: python3 visual-tests/make-mrdna-fixtures.py [OUTDIR]
needs: the mrdna package installed (pip install -e ../mrdna_project, conda env mrdna-openmm)
OUTDIR defaults to the fixture folders; give another to try the script without touching them.
The committed fixtures were made with the earlier Rust engine; the file formats are the same.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

from mrdna.relax.cli import load_state

HERE = os.path.dirname(os.path.abspath(__file__))
MRDNA = os.environ.get('MRDNA_PROJECT', os.path.join(HERE, '..', '..', 'mrdna_project'))
TETRA = os.path.join(MRDNA, 'data', 'tetrahelix.oxview')
UNIT = os.path.join(HERE, '..', 'src', 'formats', 'parsers', '__fixtures__', 'mrdna')
VISUAL = os.path.join(HERE, 'fixtures')
TAGS = {'ds': 'helix', 'xover': 'crossover', 'ss': 'ss', 'junction': 'junction', 'orient': 'orient'}
# bp/bead and the free-dynamics length (ns, one frame per 3 ns)
RUNS = [(5, 60), (1, 6)]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    unit, visual = (out, out) if out else (UNIT, VISUAL)
    os.makedirs(unit, exist_ok=True)
    for res, ns in RUNS:
        with tempfile.TemporaryDirectory() as run:
            subprocess.run(['mrdna-relax', TETRA, run, '--res', str(res), '--phases', f'free:{ns}',
                            '--seed', '7'], check=True, stdout=subprocess.DEVNULL)
            stage = glob.glob(os.path.join(run, f'tetrahelix_1_r{res}.model'))[0][:-len('.model')]
            M = load_state(stage + '_state.pkl')
            prefix = os.path.join(unit, f'tetra_r{res}')
            for ext in ('model', 'traj', 'energy', 'final'):
                shutil.copy(f'{stage}.{ext}', f'{prefix}.{ext}')
        n = len(M.pos)
        traj = np.fromfile(prefix + '.traj', '<f8').reshape(-1, n, 3)
        steps = [int(ln.split()[0]) for ln in open(prefix + '.energy') if not ln.startswith('#')]
        expected = dict(
            res=res,
            n=int(n),
            frames=int(len(traj)),
            kind=[str(k) for k in M.kind],
            parent=[int(p) for p in M.parent],
            bonds=[[int(i), int(j), TAGS[t]] for i, j, _, _, t in M.bonds],
            first_pos=[float(v) for v in M.pos[0]],
            last_frame_first_pos=[float(v) for v in traj[-1][0]],
            energy_steps=steps,
        )
        with open(prefix + '.expected.json', 'w') as f:
            json.dump(expected, f)
        print(f'res {res}: {expected["n"]} beads, {len(expected["bonds"])} bonds, {expected["frames"]} frames')
    os.makedirs(visual, exist_ok=True)
    for ext in ('model', 'traj', 'energy'):
        shutil.copy(os.path.join(unit, f'tetra_r5.{ext}'), os.path.join(visual, f'mrdna.{ext}'))


if __name__ == '__main__':
    main()
