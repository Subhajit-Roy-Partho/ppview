# hcc: hclear runs with the core coloured by species (ball and ballstick)

Same 53 runs and image format as `hclear/`, but every core body is coloured by its species (core bead type, via
`render_phb.py --species-colors`); arms stay slate and patches keep their interaction colours. No legend in the images:
each run's README lists the species colours. Code: `render_clear.py`. Regenerate: `python hcc/render_clear.py run <run>` or `all -j N`.
