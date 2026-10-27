#!/bin/bash
# param_ka: render every clusters/param_ka_*.conf.dat three ways (clusters, z-slab clusters, patch colours)
FR=/scratch/sroy85/Github/dna/large_crystal/hand5/final_report; P=/scratch/sroy85/Github/ppview/render_phb.py
for c in $FR/clusters/param_ka_*.conf.dat; do
  b=$(basename $c .conf.dat); t=$FR/clusters/$b.topology.phb; l=$FR/clusters/$b.labels.txt; o=$FR/renders/param_ka/$b
  common="--top $t --conf $c --width 3840 --height 2160 --scale 2 --background white --cores-only"
  nice python3 $P $common --out $o.clusters.png --cluster-file $l --legend --title "$b" --quiet
  nice python3 $P $common --out $o.slab.png --cluster-file $l --slab z 0.4 0.6 --legend --title "$b (z slab 0.4-0.6)" --quiet
  nice python3 $P $common --out $o.patches.png --patches --title "$b (patch colours)" --quiet
done
echo ALLDONE
