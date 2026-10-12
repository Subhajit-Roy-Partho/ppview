# mrdna bead render — design

Date: 2026-10-10
Status: draft, awaiting review

## Goal

Let PPView draw the coarse-grained bead model produced by the MrDNA
re-implementation in `../mrdna_project`, and play back its Brownian-dynamics
relaxation, from the files the Rust engine already writes. Nothing in
`mrdna_project` is changed.

Out of scope for now: drawing nucleotides from `.oxview`, overlaying beads on
nucleotides, multi-resolution stage comparison. The design leaves room for them
(a bead keeps its index, so a later bead→nucleotide map can attach to it) but
builds none of it.

## Input files

All written by `mrdna_rs run MODEL OUT_PREFIX ...` (via `rsbridge.rs_run`).
Little-endian throughout. Lengths in Å.

| file | content | detection |
|---|---|---|
| `X.model` | header + bead model (layout below) | first 8 bytes = u64 `0x4D52444E4131` |
| `X.traj` | raw f64 frames, `N×3` each, no header, one per `out_every` BD steps | name ends `.traj` **and** the head is not text |
| `X.final` | one raw f64 frame | name ends `.final` and the head is not text |
| `X.energy` | text: `# step E_total E_bond E_angle E_dihedral E_nonbonded`, one line per `.traj` frame | first line starts with that header |

`.model` layout (from `rsbridge.export_model` / `main.rs#read_model`):

```
u64 magic, u64 N
f64[N*3] pos, f64[N] D, f64[N] nts
f64 kT, f64×7 nonbonded params, u64 nonbonded flag
u64 n_nb, i64[n_nb] nb_atoms
u64 n_bonds,  n_bonds  × (i64 i, i64 j, f64 k, f64 r0)
u64 n_angles, n_angles × (i64 i, i64 j, i64 l, f64 k, f64 θ0)
u64 n_dihs,   n_dihs   × (i64 i, i64 j, i64 k, i64 l, f64 k, f64 φ0, f64 rcm, f64 rcq)
u64 n_excl,   n_excl   × (i64 a, i64 b)
```

Only `pos`, `nts`, bonds and dihedral indices are used; the rest is read past.
A file whose length does not match the counts is rejected with a `LoadError`.

## Recovering bead kinds and bond types

The `.model` carries no labels, but they follow from its structure
(`cgmodel.build_bead_model`, `_add_bonded_terms`):

- **`or` (orientation)**: `nts == 0`. Only orientation beads carry no nucleotides.
- **`ds`**: bonded to an `or` bead.
- **`ss`**: everything else.

Bonds, in order of test:

- **orient**: one end is `or`.
- **helix**: `ds–ds` and some dihedral has this pair as its middle two atoms
  with `or` beads at both ends (the twist dihedral `o0-b0-b1-o1`).
- **crossover**: any other `ds–ds` bond.
- **ss**: `ss–ss`.
- **junction**: `ds–ss`.

A model built with `local_twist=False` has no `or` beads. Every bead is then
classified `ss`, which is wrong. That case is detected (no `or` beads at all)
and labelled `bead` / `bond` instead of guessing; the pipeline never builds one.

Classification is a pure function, `classifyMrdna(model) → { kind[], bondType[] }`,
tested against the Python `BeadModel` (see Testing).

## Frames

- Frame 0 is the `.model` positions: the mapped design, before minimisation.
- Frames 1..K are `.traj`, K = `size / (N*24)`. A size that is not a whole
  number of frames drops the partial tail and warns, because a run that blew up
  stops writing mid-run.
- If there is no `.traj` but there is a `.final`, frames are `[model, final]`.
- `.energy` row k gives frame k+1 its step (shown as the time readout) and its
  energy terms (shown as the energy readout). Frame 0 has step 0 and no energy.

Coordinates are converted to oxDNA length units (÷ 8.518, `OX2A` in
`topology.py`) so sizes match the rest of PPView. The `.model` stores no box, so
the box is the bounding box of frame 0 plus a margin, and every frame is
centred on it. Frames are **not** wrapped: beads are not periodic in this model,
and wrapping would cut bonds.

`.traj` is read lazily, one `N*24`-byte slice per frame. The WASM text parser
and the frame cache are not used: a frame is `N*24` bytes that need no
parsing, which is cheaper to re-read than to cache.

## Architecture

Following "Adding a format" in `CLAUDE.md`. No branches in `ParticleScene`.

| unit | responsibility |
|---|---|
| `formats/parsers/mrdna.js` | `parseMrdnaModel(ArrayBuffer)`, `classifyMrdna`, `readMrdnaFrame(ArrayBuffer, N)`, `parseMrdnaEnergy(text)`. Pure, no DOM |
| `formats/detection/signatures.js` | `isMrdnaModel(bytes)`, `isMrdnaBinaryFrames(bytes, name)`, `isMrdnaEnergy(lines)` |
| `formats/detection/detectFileType.js` | checks the binary signatures **before** reading the head as text, and the `.traj` check before the trajectory fallback |
| `formats/detection/categorize.js` | new roles `mrdnaModel`, `mrdnaTrajectory`, `mrdnaFinal`, `mrdnaEnergy` |
| `loading/loadSimulation.js` | `loadMrdna` branch, self-contained like `loadMgl`: sets `topData`, frame 0, box, frame count, `trajFile` wrapper |
| `loading/loadFrame.js` | `mrdnaFrame` branch, like `mglFrame`: slice, decode, convert, centre, hand to scene |
| `formats/registry.js` | entry `mrdna`; `matches: topData?.format === 'mrdna'`; renderer `MrdnaBeads` |
| `components/MrdnaBeads/` | the renderer (below) |
| `store/uiStore.js` | `showMrdnaPanel`, and `mrdnaDisplay`: `{ showOrient, beadScale, bondTypes: { helix, crossover, ss, junction, orient, bond } }` (plain booleans, so a toggle is a new object) |
| `components/MrdnaPanel/` | the panel (below) |
| `rendering/transforms.js` | `cylinderBetweenPoints`: a cylinder between two scene-space points with no periodic filter |

`topData` for this format:

```js
{ format: 'mrdna', count: N,
  kind: Uint8Array(N),          // 0 ds, 1 ss, 2 or, 3 unknown
  nts: Float64Array(N),
  bonds: Int32Array(2*B), bondType: Uint8Array(B),
  parent: Int32Array(N),        // or bead -> its ds bead, else -1
  counts: { beads: { ds, ss, or, bead }, bonds: { helix, crossover, ss, junction, orient, bond } } }
```

Particles are built as `{ x, y, z, typeIndex: kind }`, so selection, framing and
the existing readouts work unchanged.

## Rendering (`MrdnaBeads`)

Two `InstancedLayer`s, so picking and redraw come for free (impostors are per renderer and not enabled here):

- **Beads**: spheres. `ds` and `ss` radius ∝ `nts^(1/3)`, normalised so a 5 bp
  `ds` bead is about one helix radius (~1 nm ≈ 1.17 su). `or` beads are fixed
  and small (0.25 su). An `or` bead sits 1.5 Å (0.18 su) off the axis, inside
  its `ds` bead, so it is drawn just outside its `ds` bead, on a short stalk, in the direction it
  really points, and the panel says so. Its stored position, the one the
  selection panel reports, is not changed. Colour by kind: `ds` steel blue, `ss` orange, `or` grey,
  unknown neutral. Selected beads are yellow, as elsewhere.
- **Bonds**: cylinders between bead centres, colour by type: helix (dark
  blue), crossover (red), ss (orange), junction (purple), orient (light grey,
  thin). The `Springs` cylinder recipe is reused (unit cylinder, scaled,
  zero-scale when hidden), without its half-box length filter, which does not
  apply to a non-periodic model.
- Picking registers the bead mesh with `useRegisterPickable`; a hidden `or`
  bead resolves to `null`, so it cannot swallow a click.
- Bead colour and scale go through `getClusterAppearance`, so selection,
  DBSCAN clustering and cluster files apply to beads with no extra wiring.
  A bond follows its two beads: it is hidden if either is hidden.
- `sphereSegments` (Detail) drives bead and bond geometry. Bead radius and
  bond thickness scale by `particleRadius / baseParticleRadius`, as other
  renderers with intrinsic geometry do; the ratio is 1 at load because every load
  calls `resetParticleRadius()`. Every effect ends in `invalidate()` (the layer does it).

## UI

A floating `MrdnaPanel` (`DraggablePanel`, `.pp-panel` chrome), shown only when
this format is loaded and opened by default. A toggle in the control bar's Tools
group, also shown only for this format, reopens it. It contains:

- toggle: orientation beads
- toggles: helix, crossover, ss, junction, orient bonds
- bead size slider (multiplier on the computed radius)
- legend: colour swatch, label and count per kind and per bond type

`SelectedParticlesDisplay` shows the bead index, kind and `nts` for a bead.

## Error handling

A `LoadError` with a human-readable message is thrown for:

- a bad magic number
- a truncated `.model`
- `.traj`/`.final` without a `.model`
- a frame size that does not match N

A `.traj` shorter than one frame gets a `LoadError` naming the bead count it
expected. A longer one that is not a whole number of frames keeps its whole
frames and warns: a run that blew up stops mid-write, and a file from another
model cannot be told apart from that by size alone. A `.final` that is not
exactly one frame gets a `LoadError`. When a drop holds several of a kind, the
one sharing the `.model`'s name stem is used.

An `.energy` file whose row count differs from the frame count is used for as
many rows as both have, with a console warning.

## Testing

- **Fixtures**: `visual-tests/make-mrdna-fixtures.py`, kept in ppview, imports
  `../mrdna_project/python` read-only. It builds the tetrahelix bead model at 5
  and 1 bp/bead, calls `rsbridge.rs_run` with the prefix in
  `src/formats/parsers/__fixtures__/` (short runs, ~20 frames), and writes
  `X.expected.json`: N, the kind of every bead, and the tag of every bond from
  the Python `BeadModel`. This needs the Rust engine built once
  (`cargo build --release` in `mrdna_project/rust`).
- **Unit tests** (Jest):
  - parser round trip: N, positions and bond count match the expected JSON
  - `classifyMrdna` reproduces every Python kind and bond tag exactly, with
    tags mapped `ds→helix`, `xover→crossover`, `ss`, `junction`, `orient`
  - frame count and the partial-tail handling
  - detection: the model by magic number, `.traj` not claimed by the
    oxDNA trajectory fallback, `.energy` by its header
  - every error path above
- **Visual**: a fixture copy of the 5 bp/bead files under
  `visual-tests/fixtures/` and one `mrdna` scenario in `scenarios.js`.
  Re-record the baseline for that scenario only.

## Documentation

`CLAUDE.md` gets a row in the File Format Support table, a short "mrdna bead
model" section (the file set, kind and bond recovery, no wrapping), and a
correction to the Trajectory row: `.traj` is claimed by mrdna when the head is
binary.

## Open questions

None blocking. The colour choices are provisional and can be changed after the
first render.
