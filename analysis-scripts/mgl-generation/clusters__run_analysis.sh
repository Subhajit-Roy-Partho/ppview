#!/usr/bin/env bash
# Batch-analyze all PHB simulations and collect MGL/JSON output.
# Usage: bash run_analysis.sh [--dry-run]
# Output: /mnt/Drive/PHB/clusters/<label>.mgl and .json per simulation

SCRIPT=/home/gila/Documents/Github/oxDNAcpp/pyrochlore/analyze_crystal.py
OUTDIR=/mnt/Drive/PHB/clusters
DRY=${1:-}

mkdir -p "$OUTDIR"

N=0; DONE=0; SKIP=0; ERR=0

find /mnt/Drive/PHB -name "*.phb" \
    -not -path "*/Backup/*" \
    -not -path "*/PHB/PHB/*" \
    | sort | while read top; do

  dir=$(dirname "$top")
  conf="$dir/last_conf.dat"
  [ -f "$conf" ] || continue

  # Skip unrun configs (t=0)
  t=$(head -1 "$conf" | awk '{print $3}')
  [ "$t" = "0" ] && { SKIP=$((SKIP+1)); continue; }

  # Build label from path
  label=$(echo "$dir" | sed 's|/mnt/Drive/PHB/||;s|/|_|g')
  mgl="$OUTDIR/${label}.mgl"
  json="$OUTDIR/${label}.json"

  [ "$DRY" = "--dry-run" ] && { echo "WOULD: $dir"; continue; }

  # Skip if already done
  [ -f "$mgl" ] && [ -f "$json" ] && { SKIP=$((SKIP+1)); continue; }

  python3 "$SCRIPT" \
      --format phb \
      --top "$top" \
      --conf "$conf" \
      --cutoff 0.20 \
      --mgl --mgl-out "$mgl" \
      --json-out "$json" \
      2>&1 | grep -v "^\[" | grep -v "^  " | head -3 && \
  echo "OK  $label" && DONE=$((DONE+1)) || { echo "ERR $label"; ERR=$((ERR+1)); }
done

echo ""
echo "=== Batch complete: done=$DONE  skipped=$SKIP  errors=$ERR ==="
