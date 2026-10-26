# Archive crystals (/mnt/Drive/PHB) — .mgl for cogli2, generated 2026-10-23

Final configurations (`last_conf.dat`) of the archive runs that formed crystals, converted with
`oxDNAcpp/main/src/build/terminal phbcluster -i <topology> -d <conf> -o <file>.mgl --patchRadius 0.3`.
Numbers in the table are the Python structural detector (phbtraj.py) on the same frame; the C++ tool reports slightly
smaller cores for archive topologies (e.g. 458 vs 482) because the archive .phb files have a trailing space on every
iC line that the C++ parser turns into duplicated patch groups (see PHB_complete_analysis, D2). Initial frame = first
frame of trajectory.dat (t = 1e6 steps; SmallSeed t = 7e6).

| file | run (under /mnt/Drive/PHB) | T_eff | cores in largest crystallite | tetra/mol | six-valent |
|---|---|---|---|---|---|
| Seeded_7longHand_T0.078 | Seeded/HandLength/7longHand/output/0.078 | 0.078 | 466 | 0.332 (best of the archive) | 0.53 |
| PHB5_square_a1_T0.075 | PHB5/square/a1/output/0.075 | 0.075 | 486 | 0.290 | 0.33 |
| PHB5_square_a1_T0.076 | PHB5/square/a1/output/0.076 | 0.076 | 482 | 0.294 | 0.36 |
| PHB5_square_a1_T0.078 | PHB5/square/a1/output/0.078 | 0.078 | 461 | 0.284 | 0.36 |
| PHB5_weakSquare_a1_T0.076 | PHB5/weakSquare/a1/output/0.076 | 0.076 | 480 | 0.270 | 0.30 |
| PHB5_equal_a1_T0.075 | PHB5/equal/a1/output/0.075 | 0.075 | 476 | 0.256 | 0.29 |
| PHB5_square_a07_T0.073 | PHB5/square/a07/output/0.073 (alpha 0.07) | 0.073 | 395 | 0.268 | 0.33 |
| SmallSeed_7longHand300_T0.080 | SmallSeed/7longHand-300/output/0.080 | 0.080 | 402 | 0.282 | 0.45 |
| PHB3_bigS_a1_T0.12 | PHB3/crystals/bigSa1/output/0.12 (200 molecules) | 0.120 | 197 / 200 | 0.245 | 0.29 |
| PHB3_weakbigS_a1_T0.16 | PHB3/weakCrystals/bigSa1/output/0.16 (200 molecules) | 0.160 | 200 / 200 | 0.225 | 0.28 |
| PHB5_square_a1_T0.084_melted | PHB5/square/a1/output/0.084 | 0.084 | 7 | 0.0 | 0 (contrast: melted above T_eff 0.082) |

Caveat for the PHB3 rows: they start from a 43 % pre-formed crystalline seed, so order there is inherited from the template.
