# hcc2: hclear2 runs with the core coloured by species (assembled structure solid, rest translucent)

Same 53 runs and image format as `hclear2/` (opaque = molecules in an intact tetrahedron, 12% opacity otherwise), with each
core body coloured by its species (`render_phb.py --species-colors`). Code: `render_clear2.py`.
Regenerate: `python hcc2/render_clear2.py run <run>` or `all -j N`.
