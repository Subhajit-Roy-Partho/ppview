# clear2: assembled structure solid, the rest translucent

Clean ball-and-stick renders (no text, legend or box) of the starting and last configuration of every PHB run in
`clear/manifest.json`, one subfolder per run with the two PNGs and a README.

A molecule is drawn **opaque** if it belongs to at least one intact tetrahedron (four mutually bonded molecules,
the crystal motif); all other molecules are drawn at **12% opacity**. This shows the seed and the grown structure
against the unassembled background.

Code: `render_clear2.py` (driver, run from the repo root with a Python that has numpy/scipy/PIL),
`../render_phb.py` (rasteriser; `render_ghosted()` does the two-layer opacity compositing),
`../clear/scripts/cluster_labels.py` (bond detection). Regenerate: `python clear2/render_clear2.py run <run>` or `all -j N`.

## Images (per run folder, written by the driver)

- `<run>_initial_ballstick.png` / `<run>_final_ballstick.png` — ball-and-stick, same text-free
  conventions as `clear/` (no title, legend, axes or box; white background; isometric
  orthographic view; 3200x2400 px).
- Each folder also gets a README with the run parameters, the opaque-vs-ghost molecule counts
  and intact-tetrahedra counts at both configurations, and the regenerate command.

## Status

`clear2/` currently holds the driver, manifest and this README; the 40 run folders with PNGs
are produced by `python clear2/render_clear2.py all -j 12` on a machine where the run data
under `/scratch/sroy85/Github/dna/large_crystal/hand5/` (see `manifest.json`, same 40 runs as
`clear/`) is present, with numpy/scipy/PIL installed.
