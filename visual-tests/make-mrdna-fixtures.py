"""Writes the mrdna fixtures PPView's tests read.

Imports ../mrdna_project/python read-only and runs its Rust engine through
rsbridge.rs_run, so the files are exactly what a real mrdna run writes. Alongside
each run it records what the Python BeadModel says every bead and bond is, which
is what the JavaScript classification is tested against.

usage: python3 visual-tests/make-mrdna-fixtures.py
needs: numpy scipy numba, and `cargo build --release` in mrdna_project/rust
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MRDNA = os.environ.get('MRDNA_PY', os.path.join(HERE, '..', '..', 'mrdna_project', 'python'))
sys.path.insert(0, MRDNA)

from topology import NucleotideSystem  # noqa: E402
from cgmodel import build_bead_model  # noqa: E402
from rsbridge import rs_run  # noqa: E402

UNIT = os.path.join(HERE, '..', 'src', 'formats', 'parsers', '__fixtures__', 'mrdna')
VISUAL = os.path.join(HERE, 'fixtures')
TAGS = {'ds': 'helix', 'xover': 'crossover', 'ss': 'ss', 'junction': 'junction', 'orient': 'orient'}
# res bp/bead, BD steps, out_every, dt in fs (the README's recommended steps)
RUNS = [(5, 2000, 100, 150.0), (1, 1000, 200, 20.0)]


def main():
    os.makedirs(UNIT, exist_ok=True)
    s = NucleotideSystem.from_oxview(os.path.join(MRDNA, '..', 'data', 'tetrahelix.oxview'))
    s.detect_pairs()
    for res, steps, every, dt in RUNS:
        M = build_bead_model(s, res, res, True)
        prefix = os.path.join(UNIT, f'tetra_r{res}')
        info, traj, E, final = rs_run(M, prefix, steps, dt, seed=7, out_every=every)
        assert info['status'] == 'ok', info
        expected = dict(
            res=res,
            n=int(len(M.pos)),
            frames=int(len(traj)),
            kind=[str(k) for k in M.kind],
            parent=[int(p) for p in M.parent],
            bonds=[[int(i), int(j), TAGS[t]] for i, j, _, _, t in M.bonds],
            first_pos=[float(v) for v in M.pos[0]],
            last_frame_first_pos=[float(v) for v in traj[-1][0]],
            energy_steps=[int(r[0]) for r in E],
        )
        with open(prefix + '.expected.json', 'w') as f:
            json.dump(expected, f)
        print(f'res {res}: {expected["n"]} beads, {len(expected["bonds"])} bonds, {expected["frames"]} frames')
    for ext in ('model', 'traj', 'energy'):
        shutil.copy(os.path.join(UNIT, f'tetra_r5.{ext}'), os.path.join(VISUAL, f'mrdna.{ext}'))


if __name__ == '__main__':
    main()
