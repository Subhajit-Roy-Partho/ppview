#!/usr/bin/env bash
# Render initial.png (sweep main/last_conf.dat) into hero T-dir. Idempotent.
sweep="$1"; t="$2"
mdir="/mnt/Drive/PHB/$sweep/main"
out="/mnt/Drive/PHB/$sweep/output/$t/initial.png"
[ -f "$out" ] && exit 0
conf="$mdir/last_conf.dat"
[ -f "$conf" ] || { echo "ERR(noconf) $sweep"; exit 0; }
top=$(ls "$mdir"/*.phb 2>/dev/null | sort | head -1)
[ -n "$top" ] || { echo "ERR(notop) $sweep"; exit 0; }
if python3 /home/gila/Documents/Github/ppview/render_phb.py --top "$top" --conf "$conf" \
    --out "$out" --width 1920 --height 1080 --scale 1 --model ball \
    --background white --species-colors --quiet > /dev/null 2>&1; then
  echo "OK  $sweep T=$t" >> /tmp/initials.log
else
  echo "ERR $sweep T=$t" >> /tmp/initials.log
fi
