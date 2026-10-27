# clear2: assembled structure solid, the rest translucent

Clean ball-and-stick renders (no text, legend or box) of the starting and last configuration of every PHB run in
`clear/manifest.json`, one subfolder per run with the two PNGs and a README.

A molecule is drawn **opaque** if it belongs to at least one intact tetrahedron (four mutually bonded molecules,
the crystal motif); all other molecules are drawn at **12% opacity**. This shows the seed and the grown structure
against the unassembled background.

Code: `render_clear2.py` (driver, run from the repo root with a Python that has numpy/scipy/PIL),
`../render_phb.py` (rasteriser; `render_ghosted()` does the two-layer opacity compositing),
`../clear/scripts/cluster_labels.py` (bond detection). Regenerate: `python clear2/render_clear2.py run <run>` or `all -j N`.
