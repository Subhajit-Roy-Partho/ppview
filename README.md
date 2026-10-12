# PPView - Patchy Particle Viewer

A React-based visualization tool for molecular dynamics simulations, specifically designed for oxDNA systems and patchy particle models. This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Features

### Core Visualization
- Interactive 3D visualization using Three.js and React Three Fiber
- Trajectory playback: play/pause, frame stepping, scrubbing and playback speed
- Customizable color schemes for particle types and patches
- Simulation box, backdrop planes and coordinate axes, each switchable
- Lighting presets built for reading data rather than for looks (Depth, Publication, Studio, Relief, Flat), with neutral white lights, faithful tone mapping and ambient occlusion
- Light or dark scene background
- Screenshot (`P`) and GLTF export
- Large systems: spheres switch to GPU impostors above 50,000 drawn spheres (force with `?impostors=1`, disable with `?impostors=0`); frames are parsed by a WebAssembly core and cached for fast replay

### Particle Types
- **Standard spherical particles** — rendered as instanced spheres
- **Raspberry particles** — multi-bead particles with an inner core and outer repulsion beads; only the outer beads are visible and selectable
- **SRS Springs particles** — spring-bonded particle chains with directional binding patches
- **oxDNA nucleotides** — full nucleotide representation with backbone beads, nucleoside ellipsoids, and connector cylinders
- **mrdna bead model** — the coarse-grained DNA beads and bonds written by the mrdna engine, with playback of its Brownian-dynamics relaxation

### Patch Visualization
- Patches rendered as outward-pointing cones on the particle surface
- Cone size proportional to particle radius (scales correctly for all formats)
- Color-coded by patch ID using the active color scheme
- Rotation matrix applied from trajectory orientation vectors

### Spring Bond Visualization
- Spring bonds between particles rendered as instanced cylinders
- Springs longer than half the minimum box dimension are hidden (periodic boundary artifact filter)
- Spring radius proportional to particle radius

### Clustering Analysis
- **DBSCAN clustering** over periodic (minimum-image) distances, with two parameters:
  - **Epsilon**: the neighbour distance, capped at half the shortest box side
  - **Neighbours needed**: the density a particle needs to be a core point (counting itself)
- **Size band**: keep only clusters between a smallest and a largest size; applies to every cluster source
- **Cluster files**: load clusters computed elsewhere from a `.json` file (drop it with the simulation, or use *Load clusters from file*)
- **Cluster/bond observables**: `PLClusterTopology`, `PatchyBonds` and `RaspberryPatchyBonds` output is streamed (multi-GB files work), matched to trajectory frames by step number, and its bonds are drawn patch to patch
- **Statistics and a size histogram**; clicking a bar selects the clusters of that size
- **Highlighting**: select clusters to enlarge them in their cluster colour; *Show only selected clusters* hides the rest, optionally leaving faint grey markers
- **Per-cluster visibility**: an eye control per cluster (or `"visible": false` in a cluster file)
- **Time view**: clusters over the whole trajectory as bands whose height is their size, showing growth, merges and splits; follow one cluster's particles to see where they went
- **View control**: choose what colours the scene (particle type, computed clusters or a loaded cluster file) independently of which clusters are being worked with

### oxDNA Nucleotide Visualization
When a standard oxDNA topology (`.top`) is loaded, PPView automatically switches to the nucleotide representation matching the oxdna-viewer style:
- **Backbone bead** (sphere r=0.2) — colored by strand, individually selectable
- **Nucleoside** (ellipsoid r=0.3, flattened along the helix axis) — colored by base type: A=blue, G=yellow, C=green, T/U=red
- **ns↔bb connector** (cylinder r=0.1) — colored by strand
- **Backbone connector** (tapered cylinder r=0.1→0.02) — follows the sugar-phosphate backbone along the strand, hidden at periodic boundaries

Strand colors cycle through four distinct colors to match standard DNA duplex conventions. Click a backbone bead to select and inspect it; Ctrl/Cmd+click for multi-selection; double-click to frame that nucleotide.

### mrdna Bead Model Visualization
The bead model of mrdna, a re-implementation of MrDNA (a multi-resolution coarse-grained DNA model used to relax oxDNA designs quickly):
- **Beads** sized by the nucleotides they stand for: double-stranded (blue), single-stranded (orange), and grey orientation markers on short stalks showing the local twist
- **Bonds** as cylinders coloured by type: helix, crossover, single strand, junction and orientation
- **Playback**: frame 0 is the bead mapping of the design, then the Brownian-dynamics frames, with the step and the energy of each frame in the readout
- **mrdna panel**: a legend with counts that doubles as the controls — switch orientation beads and each bond type on or off, and resize the beads
- Selection, clustering, the Detail and radius controls and the shift keys work on beads as on any particle; the selection panel shows each bead's kind and nucleotide count

### File Format Support
- Standard oxDNA nucleotide topology (`.top` with `strandId base n3 n5` body lines)
- Lorenzo's topology format (`.top` files)
- Flavio's topology format with `particles.txt` and `patches.txt`
- Raspberry topology format (`.top` with `iP`/`iR`/`iC` keywords)
- SRS Springs topology format (`.psp` with `iP`/`iS` keywords)
- oxDNA trajectory files (`.dat`, `.traj`, `.conf`, etc.)
- MGL format (`.mgl`), single configurations and trajectories
- mrdna bead model (`.model` + `.traj`/`.final`, optionally `.energy`)
- Cluster files (`.json`) and cluster/bond observables (`.txt`/`.dat`), plus `observables.json` and the oxDNA input file for lining observables up with frames
- Content-based file type detection; files can be dropped all at once

### User Interface
- Floating control bar: transport and readout, the scrubber, then display options grouped as Scene · Legends · Tools
- Draggable panels (clustering, mrdna, selection) that stay on screen and remember their position
- Particle and patch legends
- Selected particle display
- Drop more files at any time: cluster files and observables add to the open scene, a new simulation replaces it
- Embeddable in an iframe with a `postMessage` interface (see [IFRAME_MESSAGING.md](IFRAME_MESSAGING.md))

## Usage

### Getting Started
1. Start the application using `npm start`
2. Drag and drop your simulation files (topology + trajectory), or press `Ctrl`/`Cmd`+`O`
3. Use the controls or the keyboard to navigate through the trajectory
4. Open clustering analysis with the chart icon in the Tools group

### File Formats

#### Standard oxDNA nucleotide topology
Drop a standard oxDNA `.top` file alongside a `.dat` trajectory. The topology format is:
```
<numNucleotides> <numStrands>
<strandId> <base> <n3> <n5>   # one line per nucleotide; n3/n5 = -1 at chain ends
...
```
PPView automatically detects this format and renders the full nucleotide representation. Backbone beads are clickable and show position and orientation in the selection panel.

#### Lorenzo / Flavio topology
Standard oxDNA `.top` file + `.dat` trajectory, used for patchy particle simulations.

For Flavio format, PPView also reads a particles file and a patches file. Filenames are matched flexibly:
- **Particles**: any file whose name contains `particles` and ends in `.txt` (e.g. `CRYSTAL.particles.txt`, `CRYSTAL.particles (1).txt`)
- **Patches**: any file whose name ends in `.patch.txt` (e.g. `sat3.patch.txt`)

If you also drop an oxDNA **input file** (any file with `input` in its name, e.g. `input_sims`), PPView reads `PATCHY_radius` to set the particle display radius, and uses `particle_file`/`patchy_file` fields to locate the companion files by name.

#### Raspberry particles
Drop a `.top` file using `iP`/`iR`/`iC` keywords alongside a `.dat` trajectory. The inner center particle is hidden; the outer repulsion-site beads are rendered and are individually selectable.

#### SRS Springs (Bullview `.psp`)
Drop a `.psp` topology alongside a `.dat` trajectory. Format:
```
<numParticles> <numStrands> <maxSpringsPerParticle> <repeatedPatchesPerParticle>
iP <id> <color> <strength> <x> <y> <z>   # patch definition
iS <id> <k> <r0> <x> <y> <z>             # spring definition
<particleType> <strand> <radius> <mass> <numPatches> [patchIds...] [neighborIdx springIdx]...
```
Springs between particles are visualized as cylinders. Patches are shown as cones on the particle surface.

#### mrdna bead model
Drop the files of one mrdna run together:
- `X.model` — the bead model (binary, recognised by its magic number)
- `X.traj` — the Brownian-dynamics frames, or `X.final` for the last frame only
- `X.energy` — optional; gives each frame its step and energy terms

Without a trajectory the model alone is shown. Lengths are converted from Å to oxDNA units, and frames are centred but never wrapped into the box. See [docs/MRDNA_FORMAT_SUPPORT.md](docs/MRDNA_FORMAT_SUPPORT.md) for details.

#### Cluster files and observables
A cluster `.json` lists clusters as `{ "name", "color", "visible", "particles": [...] }` (or as a bare array; `indices`/`ids` also work). Cluster/bond observables from oxDNA's patchy plugins are recognised by content and lined up with the trajectory by step number, using `print_every` from `observables.json` or the input file when the observable writes no steps.

### Clustering Analysis
1. **Open clustering**: click the chart icon in the Tools group
2. **Choose the cluster source**: computed (DBSCAN) or any loaded cluster file or observable
3. **Adjust parameters**: epsilon and neighbours needed (DBSCAN), and the size band (any source)
4. **Inspect**: statistics, the size histogram and the cluster list
5. **Highlight**: select clusters, use *Show only selected clusters*, hide individual clusters with their eye control, and use *Clear clustering* to get back to the plain scene
6. **Over time**: open the time view to see clusters grow, merge and split across the trajectory

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Space` | Frame the selected particles, or play/pause when nothing is selected |
| `←` / `→` | Step one frame (`Shift` for 10) |
| `Home` / `End` | First / last frame |
| `Ctrl`/`Cmd`+`O` | Open files |
| `P` | Screenshot |
| `Q/A`, `W/S`, `E/D` | Shift particles along X, Y, Z |

Shortcuts are ignored while typing in a form field. Double-click a particle to frame it.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run test:visual`

Visual regression tests: headless Chrome drives the real app over every fixture format and compares pixel measurements and assertions against `visual-tests/baseline.json`. Use `-- --only=<format>` to run one format and `-- --update` to re-record the baseline. `npm run fixtures` regenerates the synthetic fixtures; `python3 visual-tests/make-mrdna-fixtures.py` regenerates the mrdna ones from a real mrdna run.

### WebAssembly core

Frame parsing, DBSCAN and observable indexing are compiled from Rust (`wasm/`) to WebAssembly. `npm start` and `npm run build` rebuild it first (`npm run build:wasm`), so a Rust toolchain with the `wasm32-unknown-unknown` target is required.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run deploy`

Deploys to GitHub Pages at `https://m-matthies.github.io/ppview`.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).
