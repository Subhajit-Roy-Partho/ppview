# PHB crystal .mgl files (cogli2) — generated 2026-10-23

Made with `~/Documents/Github/oxDNAcpp/main/src/build/terminal phbcluster -i <topology.phb> -d <final_conf.dat> -o <out>.mgl --patchRadius 0.3`
(each file uses its OWN run topology). Open: `~/Documents/Software/cogli2/build/bin/cogli2 file.mgl`. Particles are coloured by
disconnected crystallite (largest = first colour), small/unbonded pieces grey. Tetra/mol, six-valent fraction: from the
Python structural detector (phbtraj.py) at the same frame; "LC" = cores in the largest crystallite (C++ and Python agree).

| file | what | LC (cores of 500) | tetra/mol | v6 |
|---|---|---|---|---|
| seed256_T0.140_r1_ordered | 256-molecule seed, T=0.14, 1.5e9 steps | 491 | 0.344 | 0.49 |
| seed256_T0.140_r2_ordered | same, independent gas placement | 484 | 0.348 | 0.51 |
| seed192_T0.140_r1_ordered | 192 seed | 468 | 0.292 | 0.39 |
| seed192_T0.140_r2_ordered | 192 seed, placement 2 | 477 | 0.298 | 0.40 |
| seed128_T0.140_ordered / _r2 / _r3 | 128 seed, 3 placements, 8e8 steps | 411 / 452 / 450 | 0.244 / 0.252 / 0.234 | 0.29 / 0.30 / 0.26 |
| seed128_T0.145_r1_ordered | 128 seed, T=0.145 | 342 | 0.226 | 0.30 |
| seed128_T0.150_partial | 128 seed, T=0.15 | 304 | 0.188 | 0.26 |
| seed8_T0.140_grown_partial | 8-molecule seed grown at T=0.14 | 434 | 0.184 | 0.13 |
| quench_T0.140_a_partial | unseeded quench, T=0.14 | 445 | 0.180 | 0.15 |
| quench_T0.120_a_aggregate | unseeded quench, T=0.12: lowest energy, NO order (contrast case) | 499 | 0.114 | 0.09 |
| k300_ww_T0.140_kicked_ordered | K300 weak_weak kick-and-quench state (still running) | ~480 | ~0.30 | ~0.40 |
| reference_preformed_crystal | 2048-molecule pyrochlore reference (0.358, 63 % v6) | 1443 in largest of 2048 | 0.358 | 0.63 |

Best crystals to look at: seed256_*_ordered (closest to the reference); compare with quench_T0.120_a_aggregate (dense but disordered).
