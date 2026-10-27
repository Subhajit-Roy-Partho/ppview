#!/usr/bin/env bash
# Render text-free final-state PNG per completed run dir. Idempotent (skips existing final.png).
dir="$1"
conf="$dir/last_conf.dat"
out="$dir/final.png"
[ -f "$conf" ] || exit 0
[ -f "$out" ] && exit 0
t=$(head -1 "$conf" | awk '{print $3}')
[ "$t" = "0" ] && exit 0
top=$(ls "$dir"/*.phb 2>/dev/null | sort | head -1)
[ -n "$top" ] || exit 0
if python3 /home/gila/Documents/Github/ppview/render_phb.py --top "$top" --conf "$conf" \
    --out "$out" --width 1920 --height 1080 --scale 1 --model ball \
    --background white --species-colors --quiet > /dev/null 2>&1; then
  echo "OK  $dir"
else
  rm -f "$out"
  echo "ERR $dir"
fi
