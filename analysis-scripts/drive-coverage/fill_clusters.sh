#!/usr/bin/env bash
# Parallel fill of clusters/*.mgl + *.json for completed runs lacking them.
SCRIPT=/home/gila/Documents/Github/oxDNAcpp/pyrochlore/analyze_crystal.py
OUTDIR=/mnt/Drive/PHB/clusters
top="$1"
dir=$(dirname "$top")
conf="$dir/last_conf.dat"
[ -f "$conf" ] || exit 0
t=$(head -1 "$conf" | awk '{print $3}')
[ "$t" = "0" ] && exit 0
label=$(echo "$dir" | sed 's|/mnt/Drive/PHB/||;s|/|_|g')
mgl="$OUTDIR/${label}.mgl"
json="$OUTDIR/${label}.json"
[ -f "$mgl" ] && [ -f "$json" ] && exit 0
if python3 "$SCRIPT" --format phb --top "$top" --conf "$conf" --cutoff 0.20 \
    --mgl --mgl-out "$mgl" --json-out "$json" > /dev/null 2>&1; then
  echo "OK  $label"
else
  echo "ERR $label"
fi
