# mrdna Bead Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PPView loads the bead model and Brownian-dynamics trajectory written by the mrdna Rust engine (`X.model` + `X.traj`/`X.final` + optional `X.energy`) and draws it as beads and bonds.

**Architecture:** A new self-contained format, loaded like MGL: a binary parser recovers bead kinds and bond types from the model's structure, a dedicated load branch and frame branch feed the existing stores, and a new `MrdnaBeads` renderer (two `InstancedLayer`s) is chosen through the format registry. A floating `MrdnaPanel` controls what is drawn. Nothing in `../mrdna_project` is modified.

**Tech Stack:** React 18 (CRA 5, Jest 27 + jsdom 16), Three.js 0.168 / React Three Fiber, Zustand; Python 3 + numpy/scipy/numba and Cargo for generating fixtures only.

**Spec:** `docs/superpowers/specs/2026-10-10-mrdna-bead-render-design.md`

## Global Constraints

- Do not modify anything under `../mrdna_project` (reading, importing, and `cargo build` producing `rust/target/` are fine).
- Units: mrdna lengths are Å; convert with `OX2A = 8.518` (Å per oxDNA length unit) before anything reaches the store.
- `.model` magic number: u64 little-endian `0x4D52444E4131`. All binary data little-endian.
- Bead kinds: `ds`, `ss`, `or`, plus `bead` (unknown, only when a model has no `or` beads). Bond types: `helix`, `crossover`, `ss`, `junction`, `orient`, plus `bond` (unknown).
- Python tag → JS bond type: `ds→helix`, `xover→crossover`, `ss→ss`, `junction→junction`, `orient→orient`.
- Frames are centred, **never wrapped**.
- Follow `CLAUDE.md`: renderers use `InstancedLayer`, `useRegisterPickable`, `useClusterVisuals`; no new branches in `ParticleScene`; every control's store value must have a consumer; panels use `tokens.css` tokens, numeric readouts get `.num`.
- Work on branch `feat/mrdna-beads`. Commit at the end of each task **only if the user has approved commits for this work**; otherwise skip the commit step and leave the changes in the working tree.
- Commit messages end with the attribution line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A drop with several runs** (`a.model`, `a.traj`, `b.model`, `b.traj`): the `.traj` sharing the model's name stem must be used, not whichever came first. Pinned in Task 4.
2. **A `.traj` cut short by a blow-up** (size not a whole number of frames): the whole frames load and the tail is dropped with a warning, not a failure. Pinned in Task 2 and Task 4.
3. **A `.traj` dropped without its `.model`**: a message saying the model is missing, not "No topology file detected". Pinned in Task 4.
4. **A text oxDNA `trajectory.traj`** must still load as an oxDNA trajectory; only a binary head makes a `.traj` mrdna. Pinned in Task 3.
5. **Hiding orientation beads hides their orient bonds**, and clicking where a hidden bead is selects nothing. Pinned in Task 5.

---

## File Structure

| file | create/modify | responsibility |
|---|---|---|
| `visual-tests/make-mrdna-fixtures.py` | create | runs mrdna (read-only import) to write unit and visual fixtures plus expected values |
| `src/formats/parsers/__fixtures__/mrdna/` | create (generated) | `tetra_r5.*`, `tetra_r1.*` model/traj/energy/final/expected.json |
| `src/formats/parsers/__fixtures__/encodeMrdnaModel.js` | create | test-only writer of synthetic `.model` buffers |
| `src/formats/parsers/mrdna.js` | create | binary model parser, classification, frame and energy decoding, bead description |
| `src/formats/parsers/mrdna.test.js` | create | parser tests |
| `src/formats/detection/signatures.js` | modify | `isMrdnaModel`, `mrdnaFramesRole`, `isMrdnaEnergy` |
| `src/formats/detection/detectFileType.js` | modify | binary head check first, energy header before observables |
| `src/formats/detection/categorize.js` | modify | `mrdnaModels`, `mrdnaTrajectories`, `mrdnaFinals`, `mrdnaEnergies` roles |
| `src/loading/resolveFiles.js` | modify | `classifyDrop` counts mrdna files as a simulation |
| `src/formats/detection/detectFileType.test.js` | create | detection with fake files |
| `src/loading/mrdnaFrames.js` | create | box, centring, particles, companion picking, frame reading |
| `src/loading/loadMrdna.js` | create | the load branch |
| `src/loading/loadMrdna.test.js` | create | load-branch tests |
| `src/loading/loadSimulation.js` | modify | dispatch to `loadMrdna` |
| `src/loading/loadFrame.js` | modify | `mrdnaFrame` branch |
| `src/loading/loadFrame.test.js` | modify | mrdna frame test |
| `src/rendering/transforms.js` | modify | `cylinderBetweenPoints` |
| `src/components/MrdnaBeads/geometry.js` | create | colours, radii, orientation marker placement |
| `src/components/MrdnaBeads/geometry.test.js` | create | geometry tests |
| `src/components/MrdnaBeads/index.js` | create | the renderer |
| `src/formats/registry.js` | modify | `mrdna` entry |
| `src/store/uiStore.js` | modify | `showMrdnaPanel`, `mrdnaDisplay` and setters |
| `src/store/mrdnaDisplay.test.js` | create | store setter tests |
| `src/components/MrdnaPanel/index.js`, `MrdnaPanel.css`, `MrdnaPanel.test.js` | create | panel |
| `src/styles.css` | modify | import the panel css |
| `src/components/Icons/index.js` | modify | `BeadsIcon` |
| `src/components/ControlBar/index.js` | modify | Tools toggle for the panel |
| `src/components/SelectedParticlesDisplay/index.js` | modify | bead kind and nucleotide count |
| `src/App.js` | modify | mount `MrdnaPanel` |
| `visual-tests/scenarios.js`, `visual-tests/baseline.json` | modify | `mrdna` fixture and scenarios |
| `CLAUDE.md` | modify | format table and mrdna section |

---

### Task 1: Branch, toolchain and fixtures

**Files:**
- Create: `visual-tests/make-mrdna-fixtures.py`
- Create (generated): `src/formats/parsers/__fixtures__/mrdna/tetra_r5.{model,traj,energy,final,expected.json}`, `tetra_r1.{...}`, `visual-tests/fixtures/mrdna.{model,traj,energy}`

**Interfaces:**
- Produces: `tetra_rN.expected.json` with keys `res` (int), `n` (int), `frames` (int), `kind` (list of `'ds'|'ss'|'or'`), `parent` (list of int, -1 unless `or`), `bonds` (list of `[i, j, type]` with JS bond-type names, in file order), `first_pos` (Å, bead 0 in the model), `last_frame_first_pos` (Å, bead 0 in the last `.traj` frame), `energy_steps` (list of int).

- [ ] **Step 1: Create the branch and install dependencies**

```bash
cd /Users/m.matthies/Data/FasterRelax/ppview
git checkout -b feat/mrdna-beads
npm ci
CI=true npx react-scripts test --watchAll=false 2>&1 | tail -5
```
Expected: the existing suite passes (record the count of passing tests; later tasks must not reduce it).

- [ ] **Step 2: Build the mrdna Rust engine**

```bash
cd /Users/m.matthies/Data/FasterRelax/mrdna_project/rust && cargo build --release
ls -la target/release/mrdna_rs
```
Expected: the binary exists.

- [ ] **Step 3: Write the fixture generator**

`visual-tests/make-mrdna-fixtures.py`:

```python
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
```

- [ ] **Step 4: Run it**

```bash
cd /Users/m.matthies/Data/FasterRelax/ppview && python3 visual-tests/make-mrdna-fixtures.py
ls -la src/formats/parsers/__fixtures__/mrdna visual-tests/fixtures/mrdna.*
```
Expected output:
```
res 5: 360 beads, 378 bonds, 20 frames
res 1: 1440 beads, 1458 bonds, 5 frames
```
(The bead and bond counts were verified against the Python model while planning.) `tetra_r5.traj` must be `360*24*20 = 172800` bytes.

- [ ] **Step 5: Commit** (only if commits are approved)

```bash
git add visual-tests/make-mrdna-fixtures.py src/formats/parsers/__fixtures__/mrdna visual-tests/fixtures/mrdna.model visual-tests/fixtures/mrdna.traj visual-tests/fixtures/mrdna.energy
git commit -m "test: generate mrdna fixtures from a real Rust engine run

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Parser and classification

**Files:**
- Create: `src/formats/parsers/__fixtures__/encodeMrdnaModel.js`
- Create: `src/formats/parsers/mrdna.js`
- Test: `src/formats/parsers/mrdna.test.js`

**Interfaces:**
- Consumes: Task 1 fixtures.
- Produces (all exported from `src/formats/parsers/mrdna.js`):
  - `OX2A = 8.518`, `MRDNA_FRAME_BYTES_PER_BEAD = 24`
  - `KIND = { DS: 0, SS: 1, OR: 2, UNKNOWN: 3 }`, `KIND_NAMES = ['ds', 'ss', 'or', 'bead']`, `KIND_LABELS = ['Double-stranded', 'Single-stranded', 'Orientation', 'Bead']`
  - `BOND = { HELIX: 0, CROSSOVER: 1, SS: 2, JUNCTION: 3, ORIENT: 4, UNKNOWN: 5 }`, `BOND_NAMES = ['helix', 'crossover', 'ss', 'junction', 'orient', 'bond']`, `BOND_LABELS = ['Helix', 'Crossover', 'Single strand', 'Junction', 'Orientation', 'Bond']`
  - `class MrdnaFormatError extends Error` (`name === 'MrdnaFormatError'`)
  - `parseMrdnaModel(buffer: ArrayBuffer) → { n: number, pos: Float64Array(3n) /* Å */, nts: Float64Array(n), bonds: Int32Array(2B), dihedrals: Int32Array(4D) }`
  - `classifyMrdna({ n, nts, bonds, dihedrals }) → { kind: Uint8Array(n), bondType: Uint8Array(B), parent: Int32Array(n), counts: { beads: {ds, ss, or, bead}, bonds: {helix, crossover, ss, junction, orient, bond} } }`
  - `mrdnaFrameCount(byteLength: number, n: number) → { frames: number, remainder: number }`
  - `decodeMrdnaFrame(buffer: ArrayBuffer, n: number) → Float64Array(3n)` (throws `MrdnaFormatError` if `byteLength !== n*24`)
  - `parseMrdnaEnergy(text: string) → Array<{ step, total, bond, angle, dihedral, nonbonded }>`
  - `describeMrdnaBead(topData, index) → string | null`
- `encodeMrdnaModel({ pos, nts, bonds, dihedrals, angles, excl, nbAtoms }) → ArrayBuffer` (test helper; all arrays of index tuples; `pos` flat, length 3n).

- [ ] **Step 1: Write the test helper**

`src/formats/parsers/__fixtures__/encodeMrdnaModel.js`:

```js
/**
 * Writes a `.model` buffer in the layout of mrdna's rsbridge.export_model, for
 * tests that need a model the real fixtures do not contain — crossovers, which
 * the tetrahelix has none of, and the malformed files the parser must refuse.
 */
export function encodeMrdnaModel({
  pos, nts, bonds = [], angles = [], dihedrals = [], excl = [], nbAtoms = [],
}) {
  const n = nts.length;
  const size = 16 + 24 * n + 8 * n + 8 * n + 8 + 56 + 8
    + 8 + 8 * nbAtoms.length
    + 8 + 32 * bonds.length
    + 8 + 40 * angles.length
    + 8 + 64 * dihedrals.length
    + 8 + 16 * excl.length;
  const buffer = new ArrayBuffer(size);
  const view = new DataView(buffer);
  let o = 0;
  const u64 = (v) => {
    view.setUint32(o, v % 2 ** 32, true);
    view.setUint32(o + 4, Math.floor(v / 2 ** 32), true);
    o += 8;
  };
  const f64 = (v) => { view.setFloat64(o, v, true); o += 8; };

  u64(0x4D52444E4131);
  u64(n);
  pos.forEach(f64);
  for (let i = 0; i < n; i++) f64(1);          // diffusion constants
  nts.forEach(f64);
  f64(0.586);                                  // kT
  for (let k = 0; k < 7; k++) f64(0);          // nonbonded parameters
  u64(1);                                      // nonbonded flag
  u64(nbAtoms.length); nbAtoms.forEach(u64);
  u64(bonds.length);
  bonds.forEach(([i, j]) => { u64(i); u64(j); f64(1); f64(1); });
  u64(angles.length);
  angles.forEach(([i, j, l]) => { u64(i); u64(j); u64(l); f64(1); f64(Math.PI); });
  u64(dihedrals.length);
  dihedrals.forEach(([i, j, k, l]) => { u64(i); u64(j); u64(k); u64(l); f64(1); f64(0); f64(0); f64(0); });
  u64(excl.length);
  excl.forEach(([a, b]) => { u64(a); u64(b); });
  return buffer;
}
```

- [ ] **Step 2: Write the failing tests**

`src/formats/parsers/mrdna.test.js`:

```js
import fs from 'fs';
import path from 'path';
import {
  parseMrdnaModel, classifyMrdna, mrdnaFrameCount, decodeMrdnaFrame,
  parseMrdnaEnergy, describeMrdnaBead, MrdnaFormatError,
  KIND, KIND_NAMES, BOND, BOND_NAMES,
} from './mrdna';
import { encodeMrdnaModel } from './__fixtures__/encodeMrdnaModel';

const FIXTURES = path.join(__dirname, '__fixtures__', 'mrdna');
const bufferOf = (name) => {
  const b = fs.readFileSync(path.join(FIXTURES, name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
const expectedOf = (name) => JSON.parse(fs.readFileSync(path.join(FIXTURES, name), 'utf8'));

// Two helices of two ds beads each (with their orientation beads), joined by a
// crossover, and a two-bead single strand leaving the second helix.
//   0 ds  1 or(0)  2 ds  3 or(2)   helix A
//   4 ds  5 or(4)  6 ds  7 or(6)   helix B
//   8 ss  9 ss
const SYNTHETIC = {
  pos: Array.from({ length: 30 }, (_, i) => i),
  nts: [10, 0, 10, 0, 10, 0, 10, 0, 5, 5],
  bonds: [[0, 2], [0, 1], [2, 3], [4, 6], [4, 5], [6, 7], [2, 4], [6, 8], [8, 9]],
  dihedrals: [[1, 0, 2, 3], [5, 4, 6, 7], [0, 2, 4, 6]],
};

describe('parseMrdnaModel', () => {
  it.each(['tetra_r5', 'tetra_r1'])('reads %s as mrdna wrote it', (name) => {
    const expected = expectedOf(`${name}.expected.json`);
    const model = parseMrdnaModel(bufferOf(`${name}.model`));
    expect(model.n).toBe(expected.n);
    expect(model.bonds.length / 2).toBe(expected.bonds.length);
    expect(Array.from(model.pos.slice(0, 3))).toEqual(expected.first_pos);
    expected.bonds.forEach(([i, j], b) => {
      expect([model.bonds[2 * b], model.bonds[2 * b + 1]]).toEqual([i, j]);
    });
  });

  it('refuses a file that is not an mrdna model', () => {
    const buffer = encodeMrdnaModel(SYNTHETIC);
    new DataView(buffer).setUint32(0, 0, true);
    expect(() => parseMrdnaModel(buffer)).toThrow(MrdnaFormatError);
    expect(() => parseMrdnaModel(buffer)).toThrow(/not an mrdna model/);
  });

  it('refuses a truncated model rather than reading past its end', () => {
    const buffer = encodeMrdnaModel(SYNTHETIC).slice(0, 200);
    expect(() => parseMrdnaModel(buffer)).toThrow(/ends early/);
  });

  it('refuses a model with bytes left over', () => {
    const whole = new Uint8Array(encodeMrdnaModel(SYNTHETIC));
    const longer = new Uint8Array(whole.length + 8);
    longer.set(whole);
    expect(() => parseMrdnaModel(longer.buffer)).toThrow(/bytes after/);
  });

  it('refuses a bond to a bead that does not exist', () => {
    const buffer = encodeMrdnaModel({ ...SYNTHETIC, bonds: [[0, 99]] });
    expect(() => parseMrdnaModel(buffer)).toThrow(/bead 99/);
  });
});

describe('classifyMrdna', () => {
  it.each(['tetra_r5', 'tetra_r1'])('agrees with the Python model on every bead and bond of %s', (name) => {
    const expected = expectedOf(`${name}.expected.json`);
    const { kind, bondType, parent } = classifyMrdna(parseMrdnaModel(bufferOf(`${name}.model`)));
    expect(Array.from(kind, k => KIND_NAMES[k])).toEqual(expected.kind);
    expect(Array.from(parent)).toEqual(expected.parent);
    expect(Array.from(bondType, t => BOND_NAMES[t])).toEqual(expected.bonds.map(b => b[2]));
  });

  it('tells a crossover from a helix bond by the twist dihedral across it', () => {
    const { kind, bondType, parent, counts } = classifyMrdna(parseMrdnaModel(encodeMrdnaModel(SYNTHETIC)));
    expect(Array.from(kind, k => KIND_NAMES[k])).toEqual(
      ['ds', 'or', 'ds', 'or', 'ds', 'or', 'ds', 'or', 'ss', 'ss']);
    expect(Array.from(parent)).toEqual([-1, 0, -1, 2, -1, 4, -1, 6, -1, -1]);
    expect(Array.from(bondType, t => BOND_NAMES[t])).toEqual(
      ['helix', 'orient', 'orient', 'helix', 'orient', 'orient', 'crossover', 'junction', 'ss']);
    expect(counts.beads).toEqual({ ds: 4, ss: 2, or: 4, bead: 0 });
    expect(counts.bonds).toEqual({ helix: 2, crossover: 1, ss: 1, junction: 1, orient: 4, bond: 0 });
  });

  it('does not guess kinds for a model built without orientation beads', () => {
    const model = parseMrdnaModel(encodeMrdnaModel({
      pos: Array(9).fill(0), nts: [5, 5, 5], bonds: [[0, 1], [1, 2]],
    }));
    const { kind, bondType } = classifyMrdna(model);
    expect(Array.from(kind)).toEqual([KIND.UNKNOWN, KIND.UNKNOWN, KIND.UNKNOWN]);
    expect(Array.from(bondType)).toEqual([BOND.UNKNOWN, BOND.UNKNOWN]);
  });
});

describe('frames', () => {
  it('counts whole frames and reports a partial tail', () => {
    expect(mrdnaFrameCount(360 * 24 * 20, 360)).toEqual({ frames: 20, remainder: 0 });
    expect(mrdnaFrameCount(360 * 24 * 2 + 100, 360)).toEqual({ frames: 2, remainder: 100 });
    expect(mrdnaFrameCount(100, 360)).toEqual({ frames: 0, remainder: 100 });
  });

  it('decodes the last frame of the fixture trajectory', () => {
    const expected = expectedOf('tetra_r5.expected.json');
    const traj = bufferOf('tetra_r5.traj');
    const bytes = expected.n * 24;
    const last = decodeMrdnaFrame(traj.slice(traj.byteLength - bytes), expected.n);
    expect(Array.from(last.slice(0, 3))).toEqual(expected.last_frame_first_pos);
  });

  it('refuses a frame of the wrong size', () => {
    expect(() => decodeMrdnaFrame(new ArrayBuffer(48), 3)).toThrow(MrdnaFormatError);
  });
});

describe('parseMrdnaEnergy', () => {
  it('reads one row per trajectory frame', () => {
    const expected = expectedOf('tetra_r5.expected.json');
    const rows = parseMrdnaEnergy(fs.readFileSync(path.join(FIXTURES, 'tetra_r5.energy'), 'utf8'));
    expect(rows.map(r => r.step)).toEqual(expected.energy_steps);
    expect(Object.keys(rows[0])).toEqual(['step', 'total', 'bond', 'angle', 'dihedral', 'nonbonded']);
  });

  it('skips blank lines and the header', () => {
    expect(parseMrdnaEnergy('# step E_total E_bond E_angle E_dihedral E_nonbonded\n\n100 1 2 3 4 5\n'))
      .toEqual([{ step: 100, total: 1, bond: 2, angle: 3, dihedral: 4, nonbonded: 5 }]);
  });
});

describe('describeMrdnaBead', () => {
  const topData = { format: 'mrdna', kind: Uint8Array.from([0, 2, 1]), nts: Float64Array.from([10, 0, 2.5]), parent: Int32Array.from([-1, 0, -1]) };
  it('names the kind and the nucleotides a bead stands for', () => {
    expect(describeMrdnaBead(topData, 0)).toBe('ds bead · 10 nt');
    expect(describeMrdnaBead(topData, 1)).toBe('orientation bead of 0');
    expect(describeMrdnaBead(topData, 2)).toBe('ss bead · 2.5 nt');
  });
  it('says nothing for other formats', () => {
    expect(describeMrdnaBead({ format: 'lorenzo' }, 0)).toBeNull();
  });
});
```

- [ ] **Step 3: Run to see it fail**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/parsers/mrdna.test.js`
Expected: FAIL, `Cannot find module './mrdna'`.

- [ ] **Step 4: Implement the parser**

`src/formats/parsers/mrdna.js`:

```js
/**
 * The bead model written by the mrdna Rust engine (`mrdna_rs run`).
 *
 * `X.model` is the engine's input: positions, nucleotides per bead and every
 * bonded term, in the layout of `rsbridge.export_model`. It carries no labels —
 * the engine only needs numbers — so what each bead and bond *is* is recovered
 * from the model's structure (see `classifyMrdna`). `X.traj` and `X.final` are
 * bare f64 frames, N×3 each; `X.energy` is one text row per `.traj` frame.
 *
 * Lengths are Å throughout; conversion to oxDNA units happens on load.
 */

export const OX2A = 8.518;
export const MRDNA_FRAME_BYTES_PER_BEAD = 24;

export const KIND = { DS: 0, SS: 1, OR: 2, UNKNOWN: 3 };
export const KIND_NAMES = ['ds', 'ss', 'or', 'bead'];
export const KIND_LABELS = ['Double-stranded', 'Single-stranded', 'Orientation', 'Bead'];

export const BOND = { HELIX: 0, CROSSOVER: 1, SS: 2, JUNCTION: 3, ORIENT: 4, UNKNOWN: 5 };
export const BOND_NAMES = ['helix', 'crossover', 'ss', 'junction', 'orient', 'bond'];
export const BOND_LABELS = ['Helix', 'Crossover', 'Single strand', 'Junction', 'Orientation', 'Bond'];

const MAGIC_LO = 0x444E4131;
const MAGIC_HI = 0x4D52;

export class MrdnaFormatError extends Error {
  constructor(message) {
    super(message);
    this.name = 'MrdnaFormatError';
  }
}

/** True when the first eight bytes are the `.model` magic number. */
export function hasMrdnaMagic(bytes) {
  if (!bytes || bytes.length < 8) return false;
  const view = new DataView(bytes.buffer, bytes.byteOffset, 8);
  return view.getUint32(0, true) === MAGIC_LO && view.getUint32(4, true) === MAGIC_HI;
}

/** A cursor that refuses to read past the end, so a truncated file says so. */
function reader(buffer) {
  const view = new DataView(buffer);
  let o = 0;
  const need = (bytes) => {
    if (o + bytes > buffer.byteLength) {
      throw new MrdnaFormatError('The mrdna model file ends early; it may be truncated.');
    }
  };
  const u64 = () => {
    need(8);
    const lo = view.getUint32(o, true);
    const hi = view.getUint32(o + 4, true);
    o += 8;
    if (hi >= 0x200000) throw new MrdnaFormatError('The mrdna model file holds an impossible count.');
    return hi * 2 ** 32 + lo;
  };
  return {
    u64,
    f64s(count) {
      need(8 * count);
      const out = new Float64Array(count);
      for (let i = 0; i < count; i++) out[i] = view.getFloat64(o + 8 * i, true);
      o += 8 * count;
      return out;
    },
    skip(bytes) { need(bytes); o += bytes; },
    get offset() { return o; },
  };
}

export function parseMrdnaModel(buffer) {
  if (!hasMrdnaMagic(new Uint8Array(buffer, 0, Math.min(8, buffer.byteLength)))) {
    throw new MrdnaFormatError('This is not an mrdna model file (its magic number is wrong).');
  }
  const r = reader(buffer);
  r.skip(8);
  const n = r.u64();
  const pos = r.f64s(3 * n);
  r.skip(8 * n);                        // diffusion constants
  const nts = r.f64s(n);
  r.skip(8 + 56 + 8);                   // kT, nonbonded parameters, nonbonded flag
  r.skip(8 * r.u64());                  // nonbonded atom list

  const index = (v) => {
    if (v >= n) throw new MrdnaFormatError(`The mrdna model names bead ${v}, but has only ${n} beads.`);
    return v;
  };

  const nBonds = r.u64();
  const bonds = new Int32Array(2 * nBonds);
  for (let b = 0; b < nBonds; b++) {
    bonds[2 * b] = index(r.u64());
    bonds[2 * b + 1] = index(r.u64());
    r.skip(16);                         // k, r0
  }
  r.skip(40 * r.u64());                 // angles: i j l k θ0
  const nDih = r.u64();
  const dihedrals = new Int32Array(4 * nDih);
  for (let d = 0; d < nDih; d++) {
    for (let k = 0; k < 4; k++) dihedrals[4 * d + k] = index(r.u64());
    r.skip(32);                         // k, φ0, rcm, rcq
  }
  r.skip(16 * r.u64());                 // exclusions

  if (r.offset !== buffer.byteLength) {
    throw new MrdnaFormatError(
      `The mrdna model has ${buffer.byteLength - r.offset} bytes after its last section.`);
  }
  return { n, pos, nts, bonds, dihedrals };
}

/**
 * What each bead and bond is, from the model's structure alone.
 *
 * - orientation beads are the only ones carrying no nucleotides;
 * - a double-stranded bead is one bonded to an orientation bead;
 * - every other bead is single-stranded;
 * - a ds–ds bond with a twist dihedral (orientation bead at both ends) across
 *   it lies along a helix; any other ds–ds bond is a crossover.
 *
 * Checked bead for bead and bond for bond against the Python BeadModel at 5, 3
 * and 1 bp/bead. A model built without local twist has no orientation beads,
 * and then nothing tells ds from ss — so nothing is guessed.
 */
export function classifyMrdna({ n, nts, bonds, dihedrals }) {
  const nBonds = bonds.length / 2;
  const kind = new Uint8Array(n);
  const bondType = new Uint8Array(nBonds);
  const parent = new Int32Array(n).fill(-1);

  let anyOrient = false;
  for (let i = 0; i < n; i++) if (nts[i] === 0) { anyOrient = true; break; }

  if (!anyOrient) {
    kind.fill(KIND.UNKNOWN);
    bondType.fill(BOND.UNKNOWN);
  } else {
    for (let i = 0; i < n; i++) kind[i] = nts[i] === 0 ? KIND.OR : KIND.SS;
    for (let b = 0; b < nBonds; b++) {
      const i = bonds[2 * b];
      const j = bonds[2 * b + 1];
      if (kind[i] === KIND.OR && kind[j] !== KIND.OR) { kind[j] = KIND.DS; parent[i] = j; }
      if (kind[j] === KIND.OR && kind[i] !== KIND.OR) { kind[i] = KIND.DS; parent[j] = i; }
    }
    const twisted = new Set();
    for (let d = 0; d < dihedrals.length / 4; d++) {
      const a = dihedrals[4 * d];
      const b = dihedrals[4 * d + 1];
      const c = dihedrals[4 * d + 2];
      const e = dihedrals[4 * d + 3];
      if (kind[a] === KIND.OR && kind[e] === KIND.OR) twisted.add(Math.min(b, c) * n + Math.max(b, c));
    }
    for (let b = 0; b < nBonds; b++) {
      const i = bonds[2 * b];
      const j = bonds[2 * b + 1];
      const ki = kind[i];
      const kj = kind[j];
      if (ki === KIND.OR || kj === KIND.OR) bondType[b] = BOND.ORIENT;
      else if (ki === KIND.DS && kj === KIND.DS) {
        bondType[b] = twisted.has(Math.min(i, j) * n + Math.max(i, j)) ? BOND.HELIX : BOND.CROSSOVER;
      } else if (ki === KIND.SS && kj === KIND.SS) bondType[b] = BOND.SS;
      else bondType[b] = BOND.JUNCTION;
    }
  }

  const counts = {
    beads: Object.fromEntries(KIND_NAMES.map(k => [k, 0])),
    bonds: Object.fromEntries(BOND_NAMES.map(b => [b, 0])),
  };
  kind.forEach(k => { counts.beads[KIND_NAMES[k]] += 1; });
  bondType.forEach(t => { counts.bonds[BOND_NAMES[t]] += 1; });
  return { kind, bondType, parent, counts };
}

export function mrdnaFrameCount(byteLength, n) {
  const frameBytes = n * MRDNA_FRAME_BYTES_PER_BEAD;
  return { frames: Math.floor(byteLength / frameBytes), remainder: byteLength % frameBytes };
}

export function decodeMrdnaFrame(buffer, n) {
  if (buffer.byteLength !== n * MRDNA_FRAME_BYTES_PER_BEAD) {
    throw new MrdnaFormatError(
      `An mrdna frame of ${n} beads is ${n * MRDNA_FRAME_BYTES_PER_BEAD} bytes; this one is ${buffer.byteLength}.`);
  }
  const view = new DataView(buffer);
  const out = new Float64Array(3 * n);
  for (let k = 0; k < 3 * n; k++) out[k] = view.getFloat64(8 * k, true);
  return out;
}

export function parseMrdnaEnergy(text) {
  const rows = [];
  for (const line of text.split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const [step, total, bond, angle, dihedral, nonbonded] = t.split(/\s+/).map(Number);
    rows.push({ step, total, bond, angle, dihedral, nonbonded });
  }
  return rows;
}

/** One line for the selection panel, or null when the scene is not mrdna. */
export function describeMrdnaBead(topData, index) {
  if (topData?.format !== 'mrdna') return null;
  const k = topData.kind[index];
  if (k === KIND.OR) return `orientation bead of ${topData.parent[index]}`;
  return `${KIND_NAMES[k]} bead · ${Number(topData.nts[index].toFixed(2))} nt`;
}
```

- [ ] **Step 5: Run the tests**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/parsers/mrdna.test.js`
Expected: PASS, all tests.

- [ ] **Step 6: Commit** (only if commits are approved)

```bash
git add src/formats/parsers/mrdna.js src/formats/parsers/mrdna.test.js src/formats/parsers/__fixtures__/encodeMrdnaModel.js
git commit -m "feat: read the mrdna bead model and recover bead kinds and bond types

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Detection and categorisation

**Files:**
- Modify: `src/formats/detection/signatures.js` (append)
- Modify: `src/formats/detection/detectFileType.js:17-35`
- Modify: `src/formats/detection/categorize.js:5-19` and the switch
- Modify: `src/loading/resolveFiles.js` (`classifyDrop`)
- Test: `src/formats/detection/signatures.test.js` (append), `src/formats/detection/detectFileType.test.js` (create), `src/loading/resolveFiles.test.js` (append)

**Interfaces:**
- Consumes: `hasMrdnaMagic(bytes)` from Task 2.
- Produces:
  - `isMrdnaModel(bytes: Uint8Array) → boolean`, `mrdnaFramesRole(bytes: Uint8Array, name: string) → 'mrdna-trajectory' | 'mrdna-final' | null`, `isMrdnaEnergy(lines: string[]) → boolean` (in `signatures.js`)
  - detected types `'mrdna-model'`, `'mrdna-trajectory'`, `'mrdna-final'`, `'mrdna-energy'`
  - `categorized.mrdnaModels`, `.mrdnaTrajectories`, `.mrdnaFinals`, `.mrdnaEnergies`: arrays of File (always present, possibly empty)

- [ ] **Step 1: Write failing signature tests** (append to `src/formats/detection/signatures.test.js`; add the three names to its import from `./signatures`)

```js
describe('mrdna signatures', () => {
  const magic = () => {
    const b = new Uint8Array(16);
    new DataView(b.buffer).setUint32(0, 0x444E4131, true);
    new DataView(b.buffer).setUint32(4, 0x4D52, true);
    return b;
  };
  const binary = Float64Array.from([12.5, -3.25, 7.125]);
  const binaryBytes = new Uint8Array(binary.buffer);
  const textBytes = new TextEncoder().encode('t = 0\nb = 10 10 10\nE = 0 0 0\n');

  it('recognises a model by its magic number', () => {
    expect(isMrdnaModel(magic())).toBe(true);
    expect(isMrdnaModel(textBytes)).toBe(false);
    expect(isMrdnaModel(new Uint8Array(4))).toBe(false);
  });

  it('claims a .traj or .final only when its head is binary', () => {
    expect(mrdnaFramesRole(binaryBytes, 'run.traj')).toBe('mrdna-trajectory');
    expect(mrdnaFramesRole(binaryBytes, 'RUN.FINAL')).toBe('mrdna-final');
    // An oxDNA text trajectory named .traj stays an oxDNA trajectory.
    expect(mrdnaFramesRole(textBytes, 'trajectory.traj')).toBeNull();
    expect(mrdnaFramesRole(binaryBytes, 'run.dat')).toBeNull();
    expect(mrdnaFramesRole(new Uint8Array(0), 'run.traj')).toBeNull();
  });

  it('recognises the energy log by its header', () => {
    expect(isMrdnaEnergy(['# step E_total E_bond E_angle E_dihedral E_nonbonded', '100 1 2 3 4 5'])).toBe(true);
    expect(isMrdnaEnergy(['# step 100 N 40 n 2'])).toBe(false);
  });
});
```

- [ ] **Step 2: Run to see it fail**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/detection/signatures.test.js`
Expected: FAIL, `isMrdnaModel is not a function`.

- [ ] **Step 3: Implement the signatures** (append to `src/formats/detection/signatures.js`; add `import { hasMrdnaMagic } from '../parsers/mrdna';` at the top)

```js
/** The mrdna engine's `.model`: a binary file opening with its magic number. */
export function isMrdnaModel(bytes) {
  return hasMrdnaMagic(bytes);
}

// Text never holds a NUL or most control characters; packed doubles almost
// always do within a few values.
function looksBinary(bytes) {
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i];
    if (b === 0 || b === 127 || (b < 32 && b !== 9 && b !== 10 && b !== 13)) return true;
  }
  return false;
}

/**
 * The mrdna engine's frames: `.traj` (every frame) or `.final` (the last one),
 * raw doubles with no header. Named like oxDNA's text trajectories, so the
 * name alone is not enough — only a binary head makes one ours.
 */
export function mrdnaFramesRole(bytes, name) {
  if (!bytes || bytes.length === 0 || !looksBinary(bytes)) return null;
  const lower = name.toLowerCase();
  if (lower.endsWith('.traj')) return 'mrdna-trajectory';
  if (lower.endsWith('.final')) return 'mrdna-final';
  return null;
}

/** The engine's energy log: `# step E_total E_bond ...`. */
export function isMrdnaEnergy(lines) {
  return lines.length > 0 && /^#\s*step\s+E_total\b/.test(lines[0]);
}
```

- [ ] **Step 4: Run the signature tests**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/detection/signatures.test.js`
Expected: PASS.

- [ ] **Step 5: Write failing detection tests**

`src/formats/detection/detectFileType.test.js`:

```js
import { detectFileType } from './detectFileType';
import { categorizeFiles } from './categorize';

// jsdom 16's Blob has neither text() nor arrayBuffer(), so files are faked with
// the two calls detection makes.
const fakeFile = (name, bytes) => ({
  name,
  size: bytes.length,
  slice: (start = 0, end = bytes.length) => {
    const part = bytes.slice(start, end);
    return {
      arrayBuffer: async () => part.buffer.slice(part.byteOffset, part.byteOffset + part.byteLength),
      text: async () => new TextDecoder().decode(part),
    };
  },
});
const textFile = (name, text) => fakeFile(name, new TextEncoder().encode(text));

const modelBytes = () => {
  const b = new Uint8Array(64);
  new DataView(b.buffer).setUint32(0, 0x444E4131, true);
  new DataView(b.buffer).setUint32(4, 0x4D52, true);
  new DataView(b.buffer).setUint32(8, 3, true);
  return b;
};
const frameBytes = () => new Uint8Array(Float64Array.from([1.5, -2.25, 3, 4, 5, 6, 7, 8, 9]).buffer);

describe('detectFileType for mrdna', () => {
  it('names each file of an mrdna run', async () => {
    expect(await detectFileType(fakeFile('a.model', modelBytes()))).toBe('mrdna-model');
    expect(await detectFileType(fakeFile('a.traj', frameBytes()))).toBe('mrdna-trajectory');
    expect(await detectFileType(fakeFile('a.final', frameBytes()))).toBe('mrdna-final');
    expect(await detectFileType(textFile('a.energy',
      '# step E_total E_bond E_angle E_dihedral E_nonbonded\n100 1 2 3 4 5\n'))).toBe('mrdna-energy');
  });

  it('leaves an oxDNA text trajectory named .traj to oxDNA', async () => {
    const text = ['t = 0', 'b = 10 10 10', 'E = 0 0 0', '1 2 3 1 0 0 0 0 1'].join('\n');
    expect(await detectFileType(textFile('trajectory.traj', text))).toBe('trajectory');
  });

  it('sorts an mrdna drop into its roles', () => {
    const m = { name: 'a.model' };
    const t = { name: 'a.traj' };
    const f = { name: 'a.final' };
    const e = { name: 'a.energy' };
    const c = categorizeFiles([
      { file: m, type: 'mrdna-model' }, { file: t, type: 'mrdna-trajectory' },
      { file: f, type: 'mrdna-final' }, { file: e, type: 'mrdna-energy' },
    ]);
    expect(c.mrdnaModels).toEqual([m]);
    expect(c.mrdnaTrajectories).toEqual([t]);
    expect(c.mrdnaFinals).toEqual([f]);
    expect(c.mrdnaEnergies).toEqual([e]);
    expect(c.trajectory).toBeNull();
    expect(c.unknown).toEqual([]);
  });
});
```

Append to `src/loading/resolveFiles.test.js` (it already imports `classifyDrop`; if not, add it):

```js
describe('classifyDrop with mrdna files', () => {
  it('treats an mrdna model as a simulation, not an overlay drop', () => {
    const categorized = { mrdnaModels: [{ name: 'a.model' }], clusterFiles: [{ name: 'c.json' }], observableFiles: [] };
    expect(classifyDrop(categorized, { sceneIsLoaded: true })).toBe('simulation');
  });
  it('treats a lone mrdna trajectory as a simulation drop, so its error is reported', () => {
    const categorized = { mrdnaTrajectories: [{ name: 'a.traj' }], clusterFiles: [{ name: 'c.json' }], observableFiles: [] };
    expect(classifyDrop(categorized, { sceneIsLoaded: true })).toBe('simulation');
  });
});
```

- [ ] **Step 6: Run to see them fail**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/detection/detectFileType.test.js src/loading/resolveFiles.test.js`
Expected: FAIL (`'unknown'` instead of `'mrdna-model'`; `classifyDrop` returns `'overlays-only'`).

- [ ] **Step 7: Implement detection**

In `src/formats/detection/detectFileType.js`, add `isMrdnaModel, mrdnaFramesRole, isMrdnaEnergy` to the import from `./signatures`, then replace the start of the `try` block (from `// Read the first few KB` down to the `if (lines.length === 0)` check) with:

```js
    // Binary files first: decoding one as text yields garbage that a text
    // signature could match by accident, and `.traj` is also an oxDNA name.
    const headBlob = file.slice(0, Math.min(file.size, 64));
    if (typeof headBlob.arrayBuffer === 'function') {
      const head = new Uint8Array(await headBlob.arrayBuffer());
      if (isMrdnaModel(head)) return 'mrdna-model';
      const framesRole = mrdnaFramesRole(head, file.name);
      if (framesRole) return framesRole;
    }

    // Read the first few KB of the file to analyze structure
    const chunkSize = Math.min(file.size, 8192); // Read first 8KB
    const chunk = file.slice(0, chunkSize);
    const text = await chunk.text();
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);

    if (lines.length === 0) {
      return 'unknown';
    }

    // Before the observables: its `# step ...` header is the shape a
    // PatchyBonds header has.
    if (isMrdnaEnergy(lines)) {
      return 'mrdna-energy';
    }
```

In `src/formats/detection/categorize.js`, add to the `categorized` object:

```js
    mrdnaModels: [],
    mrdnaTrajectories: [],
    mrdnaFinals: [],
    mrdnaEnergies: [],
```

and to the switch, before `case 'input':`:

```js
      case 'mrdna-model':
        categorized.mrdnaModels.push(file);
        break;
      case 'mrdna-trajectory':
        categorized.mrdnaTrajectories.push(file);
        break;
      case 'mrdna-final':
        categorized.mrdnaFinals.push(file);
        break;
      case 'mrdna-energy':
        categorized.mrdnaEnergies.push(file);
        break;
```

In `src/loading/resolveFiles.js`, `classifyDrop`, extend `bringsSimulation`:

```js
  const bringsSimulation = !!(
    categorized.topology || categorized.trajectory
    || categorized.mglFile || categorized.mglTrajectory
    || categorized.mrdnaModels?.length || categorized.mrdnaTrajectories?.length
    || categorized.mrdnaFinals?.length
  );
```

- [ ] **Step 8: Run detection, categorisation and the whole suite**

Run: `CI=true npx react-scripts test --watchAll=false src/formats/detection src/loading/resolveFiles.test.js`
Expected: PASS.

- [ ] **Step 9: Commit** (only if commits are approved)

```bash
git add src/formats/detection src/loading/resolveFiles.js src/loading/resolveFiles.test.js
git commit -m "feat: detect the files of an mrdna run, before .traj is claimed as oxDNA

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Loading and frames

**Files:**
- Create: `src/loading/mrdnaFrames.js`
- Create: `src/loading/loadMrdna.js`
- Modify: `src/loading/loadSimulation.js` (dispatch, after `checkpoint(signal)` and before the MGL branch)
- Modify: `src/loading/loadFrame.js` (`loadFrame`, before the MGL branch)
- Test: `src/loading/loadMrdna.test.js` (create), `src/loading/loadFrame.test.js` (append)

**Interfaces:**
- Consumes: Task 2 parser exports; Task 3 categorised roles.
- Produces:
  - `mrdnaFrames.js`: `mrdnaBox(pos: Float64Array, n) → [L, L, L]`; `mrdnaParticles(pos: Float64Array, n, kind: Uint8Array, box) → Array<{x, y, z, typeIndex, particleType: null}>`; `pickCompanion(files: File[], modelName: string) → File | null`; `readMrdnaFrame(source, k) → Promise<Float64Array>`; `frameTime(source, k) → number`; `frameEnergy(source, k) → number[]`.
  - Frame source stored as `trajFile`: `{ mrdna: true, name, n, kind, modelPos: Float64Array, traj: File|null, final: File|null, frameCount, energy: Array<row>, box }`.
  - `loadMrdna(categorized, signal, scene, status) → Promise<void>`; throws `LoadError`.
  - `topData` for this format: `{ format: 'mrdna', count: n, kind, nts, parent, bonds, bondType, counts }`.

- [ ] **Step 1: Write the failing load tests**

`src/loading/loadMrdna.test.js`:

```js
import fs from 'fs';
import path from 'path';
import { loadSimulation } from './loadSimulation';
import { createLoadTokens, runLoad } from './staleness';
import { mrdnaBox, mrdnaParticles, pickCompanion, readMrdnaFrame } from './mrdnaFrames';
import { OX2A } from '../formats/parsers/mrdna';

const FIXTURES = path.join(__dirname, '..', 'formats', 'parsers', '__fixtures__', 'mrdna');
const bytesOf = (name) => {
  const b = fs.readFileSync(path.join(FIXTURES, name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
const binaryFile = (name, buffer) => ({
  name,
  size: buffer.byteLength,
  arrayBuffer: async () => buffer,
  slice: (a, b) => ({ arrayBuffer: async () => buffer.slice(a, b) }),
});
const textFile = (name, text) => ({ name, size: text.length, text: async () => text });
const expected = JSON.parse(fs.readFileSync(path.join(FIXTURES, 'tetra_r5.expected.json'), 'utf8'));

const sceneOf = () => {
  const calls = {};
  const record = (key) => (value) => { calls[key] = value; };
  return {
    calls,
    setTopData: record('topData'),
    setPositions: record('positions'),
    setCurrentBoxSize: record('boxSize'),
    setCurrentTime: record('time'),
    setCurrentEnergy: record('energy'),
    setConfigIndex: record('configIndex'),
    setConfigTimes: record('configTimes'),
    setTotalConfigs: record('totalConfigs'),
    setTrajFile: record('trajFile'),
    setFormatParticleRadius: record('formatRadius'),
  };
};

const categorizedOf = (overrides) => ({
  mrdnaModels: [], mrdnaTrajectories: [], mrdnaFinals: [], mrdnaEnergies: [],
  clusterFiles: [], observableFiles: [], unknown: [], ...overrides,
});

const load = (categorized, scene = sceneOf()) => runLoad(() => loadSimulation({
  files: [], categorized, signal: createLoadTokens().begin(), scene,
})).then(outcome => ({ outcome, scene }));

const MODEL = binaryFile('tetra_r5.model', bytesOf('tetra_r5.model'));
const TRAJ = binaryFile('tetra_r5.traj', bytesOf('tetra_r5.traj'));
const ENERGY = textFile('tetra_r5.energy', fs.readFileSync(path.join(FIXTURES, 'tetra_r5.energy'), 'utf8'));

describe('loadMrdna', () => {
  it('loads the model as frame 0 and the trajectory after it', async () => {
    const { outcome, scene } = await load(categorizedOf({
      mrdnaModels: [MODEL], mrdnaTrajectories: [TRAJ], mrdnaEnergies: [ENERGY],
    }));
    expect(outcome.ok).toBe(true);
    const { topData, positions, totalConfigs, configIndex, trajFile, configTimes } = scene.calls;
    expect(topData.format).toBe('mrdna');
    expect(topData.count).toBe(expected.n);
    expect(topData.counts.beads).toEqual({ ds: 162, ss: 36, or: 162, bead: 0 });
    expect(positions).toHaveLength(expected.n);
    expect(totalConfigs).toBe(expected.frames + 1);
    expect(configIndex).toEqual(Array.from({ length: expected.frames + 1 }, (_, i) => i));
    expect(configTimes).toEqual([0, ...expected.energy_steps]);
    expect(trajFile.mrdna).toBe(true);
  });

  it('works with only the final frame', async () => {
    const final = binaryFile('tetra_r5.final', bytesOf('tetra_r5.final'));
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaFinals: [final] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(2);
  });

  it('shows the model alone when no frames came with it', async () => {
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(1);
  });

  it('keeps the whole frames of a trajectory cut short', async () => {
    const frame = expected.n * 24;
    const cut = binaryFile('tetra_r5.traj', bytesOf('tetra_r5.traj').slice(0, 3 * frame + 100));
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaTrajectories: [cut] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(4);
    expect(warn).toHaveBeenCalledWith(expect.stringMatching(/100 bytes/));
    warn.mockRestore();
  });

  it('refuses a trajectory shorter than one frame of this model', async () => {
    const tiny = binaryFile('tetra_r5.traj', new ArrayBuffer(240));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaTrajectories: [tiny] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/360 beads/);
  });

  it('refuses a final frame of the wrong size', async () => {
    const wrong = binaryFile('tetra_r5.final', new ArrayBuffer(48));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaFinals: [wrong] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/final frame/);
  });

  it('asks for the model when only frames were dropped', async () => {
    const { outcome } = await load(categorizedOf({ mrdnaTrajectories: [TRAJ] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/\.model/);
  });

  it('turns a malformed model into a message', async () => {
    const broken = binaryFile('x.model', bytesOf('tetra_r5.model').slice(0, 300));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [broken] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/ends early/);
  });
});

describe('mrdnaFrames', () => {
  it('pairs a model with the trajectory sharing its name', () => {
    const files = [{ name: 'b.traj' }, { name: 'a.traj' }];
    expect(pickCompanion(files, 'a.model')).toBe(files[1]);
    expect(pickCompanion([{ name: 'other.traj' }], 'a.model')).toEqual({ name: 'other.traj' });
    expect(pickCompanion([], 'a.model')).toBeNull();
  });

  it('converts to oxDNA units and centres the beads in a box around them', () => {
    const pos = Float64Array.from([0, 0, 0, 2 * OX2A, 0, 0]);
    const box = mrdnaBox(pos, 2);
    expect(box[0]).toBeCloseTo(2 * 1.5 + 4);
    const particles = mrdnaParticles(pos, 2, Uint8Array.from([0, 1]), box);
    expect(particles[0].x).toBeCloseTo(box[0] / 2 - 1);
    expect(particles[1].x).toBeCloseTo(box[0] / 2 + 1);
    expect(particles[1].typeIndex).toBe(1);
  });

  it('reads frame k from the right slice of the trajectory', async () => {
    const source = { n: expected.n, modelPos: null, traj: TRAJ, final: null, frameCount: expected.frames + 1 };
    const last = await readMrdnaFrame(source, expected.frames);
    expect(Array.from(last.slice(0, 3))).toEqual(expected.last_frame_first_pos);
  });
});
```

Append to `src/loading/loadFrame.test.js`:

```js
describe('loadFrame for mrdna', () => {
  it('hands the requested frame to the scene in oxDNA units, with its step and energy', async () => {
    const n = 2;
    const frame1 = Float64Array.from([0, 0, 0, 8.518, 0, 0]);
    const traj = {
      size: frame1.byteLength,
      slice: (a, b) => ({ arrayBuffer: async () => frame1.buffer.slice(a, b) }),
    };
    const source = {
      mrdna: true, n, kind: Uint8Array.from([0, 1]),
      modelPos: Float64Array.from([0, 0, 0, 0, 0, 0]),
      traj, final: null, frameCount: 2,
      energy: [{ step: 500, total: -12.5, bond: 1, angle: 2, dihedral: 3, nonbonded: 4 }],
      box: [10, 10, 10],
    };
    const scene = sceneOf();
    await loadFrame({ file: source, index: [0, 1], frameNumber: 1, topData: { format: 'mrdna' }, scene });
    expect(scene.calls.time).toBe(500);
    expect(scene.calls.energy).toEqual([-12.5, 1, 2, 3, 4]);
    expect(scene.calls.boxSize).toEqual([10, 10, 10]);
    expect(scene.calls.positions[1].x - scene.calls.positions[0].x).toBeCloseTo(1);
  });
});
```

- [ ] **Step 2: Run to see them fail**

Run: `CI=true npx react-scripts test --watchAll=false src/loading/loadMrdna.test.js src/loading/loadFrame.test.js`
Expected: FAIL, `Cannot find module './mrdnaFrames'`.

- [ ] **Step 3: Implement the frame helpers**

`src/loading/mrdnaFrames.js`:

```js
import {
  OX2A, MRDNA_FRAME_BYTES_PER_BEAD, decodeMrdnaFrame,
} from '../formats/parsers/mrdna';

/**
 * Frames of an mrdna run, as the scene wants them.
 *
 * Frame 0 is the model itself — the bead mapping of the design, before the
 * engine minimised anything — and frame k is `.traj` frame k-1, or `.final`
 * when there is no `.traj`. Frames are bare doubles needing no parsing, so a
 * frame is read directly each time rather than cached.
 */

/**
 * A cube around frame 0, in oxDNA units. The model stores no box, and the beads
 * are not periodic, so this only has to hold the structure with room to move.
 */
export function mrdnaBox(pos, n) {
  let extent = 0;
  for (let axis = 0; axis < 3; axis++) {
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i < n; i++) {
      const v = pos[3 * i + axis];
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    extent = Math.max(extent, (hi - lo) / OX2A);
  }
  const side = extent * 1.5 + 4;
  return [side, side, side];
}

/**
 * Particles centred on the box by their centroid, as oxDNA frames are centred
 * on their centre of mass — which takes out drift — and never wrapped: wrapping
 * would cut every bond that crossed a wall.
 */
export function mrdnaParticles(pos, n, kind, box) {
  let cx = 0; let cy = 0; let cz = 0;
  for (let i = 0; i < n; i++) { cx += pos[3 * i]; cy += pos[3 * i + 1]; cz += pos[3 * i + 2]; }
  cx /= n; cy /= n; cz /= n;
  const out = new Array(n);
  for (let i = 0; i < n; i++) {
    out[i] = {
      x: (pos[3 * i] - cx) / OX2A + box[0] / 2,
      y: (pos[3 * i + 1] - cy) / OX2A + box[1] / 2,
      z: (pos[3 * i + 2] - cz) / OX2A + box[2] / 2,
      typeIndex: kind[i],
      particleType: null,
    };
  }
  return out;
}

const stem = (name) => name.replace(/\.[^.]*$/, '');

/** The file sharing the model's name stem, else the first, else null. */
export function pickCompanion(files, modelName) {
  if (!files?.length) return null;
  return files.find(f => stem(f.name) === stem(modelName)) ?? files[0];
}

export async function readMrdnaFrame(source, k) {
  if (k === 0) return source.modelPos;
  const bytes = source.n * MRDNA_FRAME_BYTES_PER_BEAD;
  const file = source.traj ?? source.final;
  const start = source.traj ? (k - 1) * bytes : 0;
  const buffer = await file.slice(start, start + bytes).arrayBuffer();
  return decodeMrdnaFrame(buffer, source.n);
}

/** The BD step a frame was written at: 0 for the model, else from `.energy`. */
export function frameTime(source, k) {
  if (k === 0) return 0;
  return source.energy[k - 1]?.step ?? k;
}

/** Total first, which is what the control bar's readout shows. */
export function frameEnergy(source, k) {
  const row = k > 0 ? source.energy[k - 1] : null;
  return row ? [row.total, row.bond, row.angle, row.dihedral, row.nonbonded] : [0];
}
```

- [ ] **Step 4: Implement the load branch**

`src/loading/loadMrdna.js`:

```js
import {
  parseMrdnaModel, classifyMrdna, parseMrdnaEnergy, mrdnaFrameCount,
  MrdnaFormatError, MRDNA_FRAME_BYTES_PER_BEAD,
} from '../formats/parsers/mrdna';
import {
  mrdnaBox, mrdnaParticles, pickCompanion, frameTime,
} from './mrdnaFrames';
import { step, LoadError } from './staleness';

/**
 * An mrdna run: a `.model`, and optionally its `.traj` or `.final` and its
 * `.energy`. Self-contained like MGL — no topology or oxDNA trajectory is
 * involved — so it sets the whole scene up here.
 */
export async function loadMrdna(categorized, signal, scene, status) {
  const modelFile = categorized.mrdnaModels[0];
  if (!modelFile) {
    throw new LoadError(
      'These are mrdna frames, but the run’s .model file was not dropped with them. Drop the .model too.');
  }

  status('Reading the mrdna model');
  let model;
  try {
    model = parseMrdnaModel(await step(signal, modelFile.arrayBuffer()));
  } catch (error) {
    if (error instanceof MrdnaFormatError) throw new LoadError(error.message);
    throw error;
  }
  const { n } = model;
  const classes = classifyMrdna(model);

  const traj = pickCompanion(categorized.mrdnaTrajectories, modelFile.name);
  const final = traj ? null : pickCompanion(categorized.mrdnaFinals, modelFile.name);
  const energyFile = pickCompanion(categorized.mrdnaEnergies, modelFile.name);
  const frameBytes = n * MRDNA_FRAME_BYTES_PER_BEAD;

  let recorded = 0;
  if (traj) {
    const { frames, remainder } = mrdnaFrameCount(traj.size, n);
    if (frames === 0) {
      throw new LoadError(
        `${traj.name} is shorter than one frame of this model (${n} beads, ${frameBytes} bytes a frame). `
        + 'It may belong to a different run.');
    }
    if (remainder) {
      console.warn(`${traj.name}: ignoring ${remainder} bytes after the last whole frame.`);
    }
    recorded = frames;
  } else if (final) {
    if (final.size !== frameBytes) {
      throw new LoadError(
        `${final.name} is not one final frame of this model (${n} beads, ${frameBytes} bytes).`);
    }
    recorded = 1;
  }

  let energy = [];
  if (energyFile) {
    energy = parseMrdnaEnergy(await step(signal, energyFile.text()));
    if (traj && energy.length !== recorded) {
      console.warn(`${energyFile.name} has ${energy.length} rows for ${recorded} frames; using what matches.`);
    }
    if (!traj) energy = [];       // a .final has no row of its own
  }

  const box = mrdnaBox(model.pos, n);
  const source = {
    mrdna: true,
    name: modelFile.name,
    n,
    kind: classes.kind,
    modelPos: model.pos,
    traj,
    final,
    frameCount: recorded + 1,
    energy,
    box,
  };

  scene.setTopData({
    format: 'mrdna',
    count: n,
    nts: model.nts,
    bonds: model.bonds,
    ...classes,
  });
  scene.setPositions(mrdnaParticles(model.pos, n, classes.kind, box));
  scene.setCurrentBoxSize(box);
  scene.setCurrentTime(0);
  scene.setCurrentEnergy([0]);
  const frames = Array.from({ length: source.frameCount }, (_, k) => k);
  scene.setTrajFile(source);
  scene.setConfigIndex(frames);
  scene.setConfigTimes(frames.map(k => frameTime(source, k)));
  scene.setTotalConfigs(source.frameCount);
}
```

- [ ] **Step 5: Dispatch from `loadSimulation` and `loadFrame`**

In `src/loading/loadSimulation.js` add `import { loadMrdna } from './loadMrdna';` and, right after the first `checkpoint(signal);`:

```js
  // mrdna is self-contained like MGL: its model is the topology and its frames
  // are bare doubles, not an oxDNA trajectory.
  if (categorized.mrdnaModels?.length || categorized.mrdnaTrajectories?.length
      || categorized.mrdnaFinals?.length) {
    await loadMrdna(categorized, signal, scene, status);
    return;
  }
```

In `src/loading/loadFrame.js` add `import { readMrdnaFrame, mrdnaParticles, frameTime, frameEnergy } from './mrdnaFrames';`, a function after `mglFrame`:

```js
/** mrdna frames are bare doubles: one slice, no parsing, no wrap. */
async function mrdnaFrame(source, frameNumber, scene) {
  const pos = await readMrdnaFrame(source, frameNumber);
  scene.setPositions(mrdnaParticles(pos, source.n, source.kind, source.box));
  scene.setCurrentBoxSize(source.box);
  scene.setCurrentTime(frameTime(source, frameNumber));
  scene.setCurrentEnergy(frameEnergy(source, frameNumber));
}
```

and in `loadFrame`, immediately before `if (file.mglTrajectoryData) {`:

```js
  if (file.mrdna) {
    await mrdnaFrame(file, frameNumber, scene);
    scene.setLoadedConfigIndex?.(frameNumber);
    return;
  }
```

- [ ] **Step 6: Run the tests**

Run: `CI=true npx react-scripts test --watchAll=false src/loading`
Expected: PASS, including the existing loader tests.

- [ ] **Step 7: Commit** (only if commits are approved)

```bash
git add src/loading
git commit -m "feat: load an mrdna run and step through its Brownian-dynamics frames

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Renderer, registry and display state

**Files:**
- Modify: `src/rendering/transforms.js` (add `cylinderBetweenPoints` after `cylinderBetween`)
- Create: `src/components/MrdnaBeads/geometry.js`, `src/components/MrdnaBeads/geometry.test.js`
- Create: `src/components/MrdnaBeads/index.js`
- Modify: `src/formats/registry.js` (import + `FORMATS` entry)
- Modify: `src/store/uiStore.js` (state and setters)
- Test: `src/store/mrdnaDisplay.test.js` (create), `src/formats/registry.test.js` (create)

**Interfaces:**
- Consumes: `KIND`, `BOND`, `BOND_NAMES` (Task 2); `topData` shape (Task 4).
- Produces:
  - `cylinderBetweenPoints(dummy, scratch, a: Vector3, b: Vector3, thickness) → boolean`
  - `geometry.js`: `MRDNA_COLORS = { kind: string[4], bond: string[6] }`, `beadRadius(kind, nts) → number`, `orientMarker(target: Vector3, parentCentre: Vector3, orCentre: Vector3, parentRadius: number) → Vector3`, `BOND_THICKNESS = 0.12`, `ORIENT_THICKNESS = 0.05`, `beadVisible(kind, appearance, display) → boolean`
  - uiStore: `showMrdnaPanel` (default `true`), `mrdnaDisplay` (default `{ showOrient: true, beadScale: 1, bondTypes: { helix: true, crossover: true, ss: true, junction: true, orient: true, bond: true } }`), `setShowMrdnaPanel(bool)`, `setMrdnaShowOrient(bool)`, `setMrdnaBeadScale(number)`, `setMrdnaBondType(name, bool)`
  - registry entry `{ id: 'mrdna', label: 'mrdna beads', matches: topData?.format === 'mrdna', renderer: MrdnaBeads }`

- [ ] **Step 1: Write the failing tests**

`src/components/MrdnaBeads/geometry.test.js`:

```js
import * as THREE from 'three';
import { beadRadius, orientMarker, beadVisible, MRDNA_COLORS } from './geometry';
import { KIND } from '../../formats/parsers/mrdna';

describe('mrdna bead geometry', () => {
  it('sizes a 5 bp double-stranded bead at about a helix radius', () => {
    expect(beadRadius(KIND.DS, 10)).toBeCloseTo(1.0);
    expect(beadRadius(KIND.DS, 2)).toBeCloseTo(Math.cbrt(0.2));
    expect(beadRadius(KIND.SS, 5)).toBeLessThan(beadRadius(KIND.DS, 10));
  });

  it('draws an orientation bead small, whatever it carries', () => {
    expect(beadRadius(KIND.OR, 0)).toBe(0.25);
  });

  it('puts the orientation marker on its ds bead surface, pointing the real way', () => {
    const parent = new THREE.Vector3(1, 1, 1);
    const real = new THREE.Vector3(1.18, 1, 1);    // 1.5 Å off the axis
    const marker = orientMarker(new THREE.Vector3(), parent, real, 0.9);
    expect(marker.x).toBeCloseTo(1.9);
    expect(marker.y).toBeCloseTo(1);
    expect(marker.z).toBeCloseTo(1);
  });

  it('hides orientation beads when they are switched off, and hidden beads always', () => {
    const shown = { hidden: false };
    expect(beadVisible(KIND.OR, shown, { showOrient: false })).toBe(false);
    expect(beadVisible(KIND.OR, shown, { showOrient: true })).toBe(true);
    expect(beadVisible(KIND.DS, { hidden: true }, { showOrient: true })).toBe(false);
  });

  it('has a colour for every kind and bond type', () => {
    expect(MRDNA_COLORS.kind).toHaveLength(4);
    expect(MRDNA_COLORS.bond).toHaveLength(6);
  });
});
```

`src/store/mrdnaDisplay.test.js`:

```js
import { useUIStore } from './uiStore';

describe('mrdna display state', () => {
  it('starts with everything shown at natural size', () => {
    const { mrdnaDisplay, showMrdnaPanel } = useUIStore.getState();
    expect(showMrdnaPanel).toBe(true);
    expect(mrdnaDisplay.showOrient).toBe(true);
    expect(mrdnaDisplay.beadScale).toBe(1);
    expect(Object.values(mrdnaDisplay.bondTypes).every(Boolean)).toBe(true);
  });

  it('changes one bond type without touching the others, as a new object', () => {
    const before = useUIStore.getState().mrdnaDisplay;
    useUIStore.getState().setMrdnaBondType('orient', false);
    const after = useUIStore.getState().mrdnaDisplay;
    expect(after).not.toBe(before);
    expect(after.bondTypes.orient).toBe(false);
    expect(after.bondTypes.helix).toBe(true);
    useUIStore.getState().setMrdnaBondType('orient', true);
  });

  it('sets bead size and orientation beads', () => {
    useUIStore.getState().setMrdnaBeadScale(0.4);
    useUIStore.getState().setMrdnaShowOrient(false);
    expect(useUIStore.getState().mrdnaDisplay).toMatchObject({ beadScale: 0.4, showOrient: false });
    useUIStore.getState().setMrdnaBeadScale(1);
    useUIStore.getState().setMrdnaShowOrient(true);
  });
});
```

`src/formats/registry.test.js`:

```js
import { rendererFor, getFormat } from './registry';
import MrdnaBeads from '../components/MrdnaBeads';

describe('registry', () => {
  it('draws an mrdna model with the bead renderer', () => {
    expect(rendererFor({ format: 'mrdna' })).toBe(MrdnaBeads);
    expect(getFormat('mrdna').label).toBe('mrdna beads');
  });
});
```

- [ ] **Step 2: Run to see them fail**

Run: `CI=true npx react-scripts test --watchAll=false src/components/MrdnaBeads src/store/mrdnaDisplay.test.js src/formats/registry.test.js`
Expected: FAIL (missing modules / undefined state).

- [ ] **Step 3: Implement geometry, transforms helper and store state**

`src/components/MrdnaBeads/geometry.js`:

```js
import { KIND } from '../../formats/parsers/mrdna';

/** Kind colours: ds, ss, or, unknown. Bond colours: helix, crossover, ss, junction, orient, unknown. */
export const MRDNA_COLORS = {
  kind: ['#4a7fb5', '#e8903a', '#9aa0a6', '#b0b0b0'],
  bond: ['#2c4f7c', '#d64545', '#e8903a', '#8e5bb5', '#c8c8c8', '#888888'],
};

// A 5 bp double-stranded bead carries 10 nucleotides and is drawn about a helix
// radius across (1 nm ≈ 1.17 oxDNA units). Volume follows the nucleotides, so
// the radius goes as their cube root.
const REFERENCE_NTS = 10;
const REFERENCE_RADIUS = 1.0;
const OR_RADIUS = 0.25;
export const BOND_THICKNESS = 0.12;
export const ORIENT_THICKNESS = 0.05;

export function beadRadius(kind, nts) {
  if (kind === KIND.OR) return OR_RADIUS;
  return REFERENCE_RADIUS * Math.cbrt(Math.max(nts, 0.5) / REFERENCE_NTS);
}

/**
 * Where an orientation bead is drawn. It really sits 1.5 Å off the helix axis —
 * inside its ds bead, where nothing would show it — so it is drawn on that
 * bead's surface in the direction it really points. That direction is the
 * information it carries: the local twist.
 */
export function orientMarker(target, parentCentre, orCentre, parentRadius) {
  target.copy(orCentre).sub(parentCentre);
  const length = target.length();
  if (length < 1e-9) return target.copy(orCentre);
  return target.multiplyScalar(parentRadius / length).add(parentCentre);
}

export function beadVisible(kind, appearance, display) {
  if (appearance?.hidden) return false;
  return kind !== KIND.OR || display.showOrient;
}
```

In `src/rendering/transforms.js`, after `cylinderBetween`:

```js
/**
 * A cylinder between two points already in scene space, with no periodic
 * filter — for structures that are not periodic, where a long bond is real.
 */
export function cylinderBetweenPoints(dummy, scratch, a, b, thickness) {
  scratch.delta.copy(b).sub(a);
  return layCylinder(dummy, scratch, a, scratch.delta, scratch.delta.length(), thickness);
}
```

In `src/store/uiStore.js`, add next to `showClusteringPane: false,`:

```js
  // The mrdna bead panel. Opens with an mrdna run: what it controls is the
  // first thing anyone looking at beads wants to change.
  showMrdnaPanel: true,
  mrdnaDisplay: {
    showOrient: true,
    beadScale: 1,
    bondTypes: { helix: true, crossover: true, ss: true, junction: true, orient: true, bond: true },
  },
```

and next to `setShowClusteringPane`:

```js
  setShowMrdnaPanel: (show) => set({ showMrdnaPanel: show }),
  setMrdnaShowOrient: (on) => set(state => ({ mrdnaDisplay: { ...state.mrdnaDisplay, showOrient: on } })),
  setMrdnaBeadScale: (scale) => set(state => ({ mrdnaDisplay: { ...state.mrdnaDisplay, beadScale: scale } })),
  setMrdnaBondType: (name, on) => set(state => ({
    mrdnaDisplay: {
      ...state.mrdnaDisplay,
      bondTypes: { ...state.mrdnaDisplay.bondTypes, [name]: on },
    },
  })),
```

- [ ] **Step 4: Implement the renderer**

`src/components/MrdnaBeads/index.js`:

```js
import React, { useCallback, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';
import InstancedLayer from '../../rendering/InstancedLayer';
import { useRegisterPickable } from '../../rendering/pickingService';
import { centreOnBox, cylinderScratch, cylinderBetweenPoints } from '../../rendering/transforms';
import useClusterVisuals from '../../rendering/useClusterVisuals';
import { KIND, BOND, BOND_NAMES } from '../../formats/parsers/mrdna';
import {
  MRDNA_COLORS, beadRadius, orientMarker, beadVisible, BOND_THICKNESS, ORIENT_THICKNESS,
} from './geometry';

/**
 * The mrdna bead model: one sphere per bead, one cylinder per bond.
 *
 * Bead colour and scale go through the shared cluster appearance, so selection
 * and clustering apply here as everywhere else. A bond is drawn only while both
 * of its beads are.
 */
function MrdnaBeads() {
  const positions = useParticleStore(state => state.positions);
  const boxSize = useParticleStore(state => state.currentBoxSize);
  const topData = useParticleStore(state => state.topData);
  const particleRadius = useParticleStore(state => state.particleRadius);
  const baseParticleRadius = useParticleStore(state => state.baseParticleRadius);
  const sphereSegments = useUIStore(state => state.sphereSegments);
  const display = useUIStore(state => state.mrdnaDisplay);
  const appearanceOf = useClusterVisuals();
  const beadMeshRef = useRef();

  const n = topData?.count ?? 0;
  const ready = topData?.format === 'mrdna' && n > 0 && positions.length === n;
  const bondCount = ready ? topData.bondType.length : 0;
  const radiusScale = particleRadius / (baseParticleRadius || 1);

  const kindColors = useMemo(() => MRDNA_COLORS.kind.map(c => new THREE.Color(c)), []);
  const bondColors = useMemo(() => MRDNA_COLORS.bond.map(c => new THREE.Color(c)), []);
  const beadGeometry = useMemo(
    () => new THREE.SphereGeometry(1, sphereSegments, sphereSegments), [sphereSegments]);
  const bondGeometry = useMemo(
    () => new THREE.CylinderGeometry(1, 1, 1, Math.max(6, Math.round(sphereSegments / 2))), [sphereSegments]);
  const material = useMemo(() => new THREE.MeshStandardMaterial({ metalness: 0.1, roughness: 0.7 }), []);
  const bondMaterial = useMemo(() => new THREE.MeshStandardMaterial({ metalness: 0.1, roughness: 0.6 }), []);

  const appearance = useMemo(() => {
    if (!ready) return [];
    return Array.from({ length: n }, (_, i) => appearanceOf(i, { baseColor: kindColors[topData.kind[i]] }));
  }, [ready, n, topData, appearanceOf, kindColors]);

  // Where each bead is drawn and how big, once per frame or display change.
  const layout = useMemo(() => {
    if (!ready) return null;
    const { kind, nts, parent } = topData;
    const centres = Array.from({ length: n }, (_, i) => centreOnBox(new THREE.Vector3(), positions[i], boxSize));
    const radii = new Float32Array(n);
    const visible = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      radii[i] = beadRadius(kind[i], nts[i]) * display.beadScale * radiusScale * appearance[i].scaleFactor;
      visible[i] = beadVisible(kind[i], appearance[i], display) ? 1 : 0;
    }
    const real = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      if (kind[i] !== KIND.OR || parent[i] < 0) continue;
      real.copy(centres[i]);
      orientMarker(centres[i], centres[parent[i]], real, radii[parent[i]]);
    }
    return { centres, radii, visible };
  }, [ready, n, topData, positions, boxSize, display, radiusScale, appearance]);

  const writeBead = useMemo(() => (i, dummy, setColor) => {
    if (!layout.visible[i]) return false;
    dummy.position.copy(layout.centres[i]);
    dummy.scale.setScalar(layout.radii[i]);
    setColor(appearance[i].color ?? kindColors[topData.kind[i]]);
    return true;
  }, [layout, appearance, kindColors, topData]);

  const scratch = useMemo(cylinderScratch, []);
  const writeBond = useMemo(() => (b, dummy, setColor) => {
    const type = topData.bondType[b];
    if (!display.bondTypes[BOND_NAMES[type]]) return false;
    const i = topData.bonds[2 * b];
    const j = topData.bonds[2 * b + 1];
    if (!layout.visible[i] || !layout.visible[j]) return false;
    const thin = Math.min(appearance[i].scaleFactor, appearance[j].scaleFactor);
    const thickness = (type === BOND.ORIENT ? ORIENT_THICKNESS : BOND_THICKNESS) * radiusScale * thin;
    if (!cylinderBetweenPoints(dummy, scratch, layout.centres[i], layout.centres[j], thickness)) return false;
    setColor(bondColors[type]);
    return true;
  }, [topData, display, layout, appearance, radiusScale, scratch, bondColors]);

  // A bead that is not drawn cannot be clicked.
  const resolveIndex = useCallback(
    (instanceId) => (layout?.visible[instanceId] ? instanceId : null), [layout]);
  useRegisterPickable('mrdna-beads', { meshRef: beadMeshRef, resolveIndex, enabled: ready });

  if (!ready) return null;
  return (
    <>
      <InstancedLayer
        ref={beadMeshRef}
        geometry={beadGeometry}
        material={material}
        count={n}
        write={writeBead}
        deps={[writeBead]}
      />
      <InstancedLayer
        geometry={bondGeometry}
        material={bondMaterial}
        count={bondCount}
        write={writeBond}
        deps={[writeBond]}
      />
    </>
  );
}

export default MrdnaBeads;
```

- [ ] **Step 5: Register the format**

In `src/formats/registry.js` add `import MrdnaBeads from '../components/MrdnaBeads';` and append to `FORMATS`:

```js
  {
    id: 'mrdna',
    label: 'mrdna beads',
    // Loaded by its own branch (loading/loadMrdna.js), never through
    // parseTopology: its topology is a binary model, not a text .top.
    parse: () => { throw new Error('mrdna models are loaded by loadMrdna'); },
    matches: (topData) => topData?.format === 'mrdna',
    renderer: MrdnaBeads,
  },
```

- [ ] **Step 6: Run the tests**

Run: `CI=true npx react-scripts test --watchAll=false src/components/MrdnaBeads src/store src/formats/registry.test.js`
Expected: PASS.

- [ ] **Step 7: Check it draws, in the browser**

```bash
npm start
```
Open http://localhost:3000/ppview, drop `visual-tests/fixtures/mrdna.model`, `mrdna.traj` and `mrdna.energy`. Expected: a tetrahedron of blue tubes with orange vertex beads and grey orientation markers; stepping frames (→) moves the beads; clicking a bead turns it yellow. Stop the server.

- [ ] **Step 8: Commit** (only if commits are approved)

```bash
git add src/rendering/transforms.js src/components/MrdnaBeads src/formats/registry.js src/formats/registry.test.js src/store/uiStore.js src/store/mrdnaDisplay.test.js
git commit -m "feat: draw the mrdna bead model as beads and bonds

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Panel, control-bar toggle and selection details

**Files:**
- Create: `src/components/MrdnaPanel/index.js`, `src/components/MrdnaPanel/MrdnaPanel.css`, `src/components/MrdnaPanel/MrdnaPanel.test.js`
- Modify: `src/styles.css` (add `@import` for the panel css after the other component imports)
- Modify: `src/components/Icons/index.js` (append `BeadsIcon`)
- Modify: `src/components/ControlBar/index.js` (Tools group)
- Modify: `src/components/SelectedParticlesDisplay/index.js` (type label)
- Modify: `src/App.js` (mount the panel next to `ClusteringPane`)

**Interfaces:**
- Consumes: Task 2 `KIND_NAMES`, `KIND_LABELS`, `BOND_NAMES`, `BOND_LABELS`, `KIND`, `describeMrdnaBead`; Task 5 store setters and `MRDNA_COLORS`.
- Produces: `MrdnaPanel` (default export), `BeadsIcon`.

- [ ] **Step 1: Write the failing panel test**

`src/components/MrdnaPanel/MrdnaPanel.test.js`:

```js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MrdnaPanel from '.';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';

const TOP_DATA = {
  format: 'mrdna',
  counts: {
    beads: { ds: 162, ss: 36, or: 162, bead: 0 },
    bonds: { helix: 144, crossover: 0, ss: 0, junction: 72, orient: 162, bond: 0 },
  },
};

beforeEach(() => {
  useParticleStore.setState({ topData: TOP_DATA });
  useUIStore.setState({ showMrdnaPanel: true });
});

describe('MrdnaPanel', () => {
  it('lists the kinds and bond types present, with their counts', () => {
    render(<MrdnaPanel />);
    expect(screen.getByText('Double-stranded')).toBeInTheDocument();
    // ds beads, orientation beads and orient bonds all number 162.
    expect(screen.getAllByText('162')).toHaveLength(3);
    expect(screen.getByText('Junction')).toBeInTheDocument();
    // Absent types are not offered.
    expect(screen.queryByText('Crossover')).toBeNull();
  });

  it('switches a bond type and orientation beads in the store', () => {
    render(<MrdnaPanel />);
    fireEvent.click(screen.getByRole('checkbox', { name: /Helix/ }));
    expect(useUIStore.getState().mrdnaDisplay.bondTypes.helix).toBe(false);
    fireEvent.click(screen.getByRole('checkbox', { name: /Orientation beads/ }));
    expect(useUIStore.getState().mrdnaDisplay.showOrient).toBe(false);
    useUIStore.getState().setMrdnaBondType('helix', true);
    useUIStore.getState().setMrdnaShowOrient(true);
  });

  it('sets the bead size', () => {
    render(<MrdnaPanel />);
    fireEvent.change(screen.getByRole('slider', { name: 'Bead size' }), { target: { value: '0.5' } });
    expect(useUIStore.getState().mrdnaDisplay.beadScale).toBe(0.5);
    useUIStore.getState().setMrdnaBeadScale(1);
  });

  it('renders nothing for other formats or when closed', () => {
    useParticleStore.setState({ topData: { format: 'lorenzo' } });
    const { container } = render(<MrdnaPanel />);
    expect(container).toBeEmptyDOMElement();
  });
});
```

- [ ] **Step 2: Run to see it fail**

Run: `CI=true npx react-scripts test --watchAll=false src/components/MrdnaPanel`
Expected: FAIL, `Cannot find module '.'`.

- [ ] **Step 3: Implement the panel**

`src/components/MrdnaPanel/index.js`:

```js
import React from 'react';
import DraggablePanel from '../DraggablePanel';
import { CloseIcon } from '../Icons';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';
import {
  KIND, KIND_NAMES, KIND_LABELS, BOND_NAMES, BOND_LABELS,
} from '../../formats/parsers/mrdna';
import { MRDNA_COLORS } from '../MrdnaBeads/geometry';

const Swatch = ({ color }) => <span className="mrdna-swatch" style={{ background: color }} aria-hidden="true" />;

/** What the mrdna renderer draws, with a legend that is also its controls. */
function MrdnaPanel() {
  const topData = useParticleStore(state => state.topData);
  const show = useUIStore(state => state.showMrdnaPanel);
  const setShow = useUIStore(state => state.setShowMrdnaPanel);
  const display = useUIStore(state => state.mrdnaDisplay);
  const setShowOrient = useUIStore(state => state.setMrdnaShowOrient);
  const setBeadScale = useUIStore(state => state.setMrdnaBeadScale);
  const setBondType = useUIStore(state => state.setMrdnaBondType);

  if (topData?.format !== 'mrdna' || !show) return null;
  const { beads, bonds } = topData.counts;

  return (
    <DraggablePanel initialX={20} initialY={20} className="pp-panel mrdna-panel" storageId="mrdna">
      <div className="panel-header drag-handle" tabIndex={0}>
        <h3 className="panel-title">mrdna beads</h3>
        <button className="icon-button" onClick={() => setShow(false)} title="Hide mrdna panel" aria-label="Hide mrdna panel">
          <CloseIcon size={15} />
        </button>
      </div>
      <div className="panel-body">
        <section className="panel-section" aria-label="Beads">
          <h4 className="mrdna-heading">Beads</h4>
          <ul className="mrdna-legend">
            {KIND_NAMES.map((name, k) => beads[name] > 0 && (
              <li key={name}>
                {k === KIND.OR ? (
                  <label>
                    <input type="checkbox" checked={display.showOrient} onChange={e => setShowOrient(e.target.checked)} />
                    <Swatch color={MRDNA_COLORS.kind[k]} />
                    <span>{KIND_LABELS[k]} beads</span>
                  </label>
                ) : (
                  <span className="mrdna-legend-label">
                    <Swatch color={MRDNA_COLORS.kind[k]} />
                    <span>{KIND_LABELS[k]}</span>
                  </span>
                )}
                <span className="num">{beads[name]}</span>
              </li>
            ))}
          </ul>
          <label className="mrdna-slider">
            <span>Bead size</span>
            <input
              type="range" min="0.1" max="2" step="0.05"
              value={display.beadScale}
              onChange={e => setBeadScale(parseFloat(e.target.value))}
              aria-label="Bead size"
            />
            <span className="num">{display.beadScale.toFixed(2)}×</span>
          </label>
          {beads.or > 0 && (
            <p className="section-hint">
              Orientation beads sit 1.5 Å off the helix axis, inside their bead. They are drawn
              on its surface, in the direction they point.
            </p>
          )}
        </section>
        <section className="panel-section" aria-label="Bonds">
          <h4 className="mrdna-heading">Bonds</h4>
          <ul className="mrdna-legend">
            {BOND_NAMES.map((name, t) => bonds[name] > 0 && (
              <li key={name}>
                <label>
                  <input type="checkbox" checked={display.bondTypes[name]} onChange={e => setBondType(name, e.target.checked)} />
                  <Swatch color={MRDNA_COLORS.bond[t]} />
                  <span>{BOND_LABELS[t]}</span>
                </label>
                <span className="num">{bonds[name]}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </DraggablePanel>
  );
}

export default MrdnaPanel;
```

`src/components/MrdnaPanel/MrdnaPanel.css`:

```css
.mrdna-panel {
    width: 260px;
}

.mrdna-heading {
    margin: 0 0 var(--space-2);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--ink-mute);
}

.mrdna-legend {
    margin: 0 0 var(--space-3);
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
}

.mrdna-legend li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: var(--ink);
}

.mrdna-legend label,
.mrdna-legend-label {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    cursor: pointer;
}

.mrdna-swatch {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex: none;
}

.mrdna-slider {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-2);
    font-size: var(--text-sm);
    color: var(--ink);
}
```

Before writing the css, confirm each token used exists: `grep -o -- '--[a-z0-9-]*' src/styles/tokens.css | sort -u`. Replace any missing one with the nearest existing token (for example `--space-2` with whatever spacing token the file defines).

Add to `src/styles.css`, after the last component `@import`: `@import './components/MrdnaPanel/MrdnaPanel.css';` (match the path style of the existing imports in that file).

- [ ] **Step 4: Wire it in**

`src/components/Icons/index.js`, append:

```js
export const BeadsIcon = ({ size = 24, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" aria-hidden="true">
    <circle cx="5" cy="12" r="3" />
    <circle cx="19" cy="12" r="3" />
    <circle cx="12" cy="5" r="2" />
    <path d="M8 12h8M7 10l3-3M17 10l-3-3" />
  </svg>
);
```

`src/components/ControlBar/index.js`: add `BeadsIcon` to the Icons import and `import { useUIStore } from '../../store/uiStore';`. Next to `const hasBonds = ...` add:

```js
  // Shown only for an mrdna run, like the bonds toggle: a control for a panel
  // that cannot appear is decoration.
  const isMrdna = useParticleStore(state => state.topData?.format === 'mrdna');
  const showMrdnaPanel = useUIStore(state => state.showMrdnaPanel);
  const setShowMrdnaPanel = useUIStore(state => state.setShowMrdnaPanel);
```

and in the Tools group, directly after the Clustering `ToggleBtn`:

```jsx
                {isMrdna && (
                  <ToggleBtn checked={showMrdnaPanel} onChange={setShowMrdnaPanel} icon={<BeadsIcon size={17} />} label="mrdna beads" />
                )}
```

`src/components/SelectedParticlesDisplay/index.js`: add `import { describeMrdnaBead } from "../../formats/parsers/mrdna";` and replace

```jsx
                <span className="particle-type">Type {info.typeIndex}</span>
```

with

```jsx
                <span className="particle-type">
                  {describeMrdnaBead(topData, info.index) ?? `Type ${info.typeIndex}`}
                </span>
```

`src/App.js`: add `import MrdnaPanel from "./components/MrdnaPanel";` and below the `ClusteringPane` line:

```jsx
      {particleCount > 0 && !isLoading && <MrdnaPanel />}
```

- [ ] **Step 5: Run the tests**

Run: `CI=true npx react-scripts test --watchAll=false`
Expected: the whole suite passes, with at least the Task 1 count plus the new tests.

- [ ] **Step 6: Check it in the browser**

`npm start`; drop the three `visual-tests/fixtures/mrdna.*` files. Expected: the panel lists Double-stranded 162, Single-stranded 36, Orientation beads 162; Helix 144, Junction 72, Orientation 162. Unticking *Orientation beads* removes the grey markers *and* their thin bonds; unticking *Helix* removes the helix bonds; the slider resizes beads; clicking a bead shows "ds bead · 10 nt" (or similar) in the selection panel; the *mrdna beads* toggle in Tools reopens the panel after closing it. Stop the server.

- [ ] **Step 7: Commit** (only if commits are approved)

```bash
git add src/components/MrdnaPanel src/components/Icons/index.js src/components/ControlBar/index.js src/components/SelectedParticlesDisplay/index.js src/App.js src/styles.css
git commit -m "feat: an mrdna panel to choose which beads and bonds are drawn

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Visual suite and documentation

**Files:**
- Modify: `visual-tests/scenarios.js` (`FORMATS`, `RENDERERS`, `PICKABLE`, `LOADERS`)
- Modify: `visual-tests/baseline.json` (re-recorded for mrdna jobs only)
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: Task 1 visual fixtures; everything above.

- [ ] **Step 1: Add the fixture and its scenarios**

In `visual-tests/scenarios.js`, add to `FORMATS` after the `srs` entry:

```js
  // The mrdna bead model: a binary model and binary frames, its own loader and
  // its own renderer (beads plus bond cylinders).
  { name: 'mrdna', files: F('mrdna.model', 'mrdna.traj', 'mrdna.energy') },
```

and extend the coverage lists, adding one row to the renderer table in the comment above them (`| mrdna | bead spheres + bond cylinders |`):

```js
const RENDERERS = ['raspberry', 'oxdna', 'srs', 'lorenzo', 'impostor', 'mrdna'];
const PICKABLE = ['raspberry', 'oxdna', 'lorenzo', 'impostor', 'mrdna', ...NEW_IMPOSTORS];
const LOADERS = ['mgl', 'oxdna', 'mrdna'];
```

(Keep `NEW_IMPOSTORS` declared before `PICKABLE`, as it is now.)

- [ ] **Step 2: Run the mrdna jobs and record their baseline**

Stop any dev server on the suite's port first.

```bash
npm run test:visual -- --only=mrdna
```
Expected: `load`, `playback`, `detail`, `clustering` and `selection` run against `mrdna`; any assertion failure is a real bug to fix before continuing (`playback` asserts a revisited frame renders identically, `selection` that a click selects). When they pass, record:

```bash
npm run test:visual -- --only=mrdna --update
```

Then run the whole suite to confirm no other baseline moved:

```bash
npm run test:visual
```
Expected: no changes reported outside `mrdna/*`.

- [ ] **Step 3: Document the format**

In `CLAUDE.md`:

1. File Format Support table, add the row:
```
| mrdna bead model | `.model` + `.traj`/`.final` (+ `.energy`) | `.model` by magic number `0x4D52444E4131`; `.traj`/`.final` by name **and** a binary head; `.energy` by its `# step E_total` header |
```
2. Change the Trajectory row's detection cell to: `content keywords; a binary `.traj` is mrdna's`.
3. Add a section after "SRS Springs Format":

```markdown
### mrdna bead model (`.model` + `.traj`)
Written by the Rust engine of the mrdna re-implementation in `../mrdna_project`
(`mrdna_rs run`, via `rsbridge.rs_run`). Lengths are Å and are divided by
`OX2A = 8.518` on load.

- **Loaded by its own branch** (`loading/loadMrdna.js`), like MGL: the model is
  binary, so it never passes through `parseTopology`. Frame 0 is the model's
  own positions (the mapped design, before minimisation); frame k is `.traj`
  frame k-1, or `.final`. `.energy` gives each frame its step and energies.
- **Kinds and bond types are recovered, not stored** (`classifyMrdna`):
  orientation beads carry 0 nucleotides, ds beads are bonded to one, the rest
  are ss; a ds–ds bond with a twist dihedral (orientation beads at both ends)
  across it is a helix bond, any other is a crossover. Verified bead for bead
  against the Python model at 5, 3 and 1 bp/bead; a model without
  orientation beads is labelled `bead`/`bond` rather than guessed.
- **Centred, never wrapped.** The model has no box; one is made around frame 0.
  Wrapping would cut bonds.
- **Orientation beads are drawn on their ds bead's surface**, in the direction
  they point: really they sit 1.5 Å off the axis, inside it. The selection
  panel reports the true position.
- `.traj` is also an oxDNA trajectory name, so detection reads 64 bytes first
  and only a binary head makes it mrdna.
- Fixtures: `python3 visual-tests/make-mrdna-fixtures.py` (needs
  `cargo build --release` in `mrdna_project/rust`). It records what the Python
  model says each bead and bond is, which `mrdna.test.js` checks against.
```

- [ ] **Step 4: Run the unit suite once more**

Run: `CI=true npx react-scripts test --watchAll=false`
Expected: PASS.

- [ ] **Step 5: Commit** (only if commits are approved)

```bash
git add visual-tests/scenarios.js visual-tests/baseline.json CLAUDE.md
git commit -m "test: cover the mrdna renderer in the visual suite, and document the format

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
