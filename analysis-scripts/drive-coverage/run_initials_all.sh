#!/usr/bin/env bash
# initial.png for EVERY completed output T-dir (main starting config). Idempotent.
dir="$1"
out="$dir/initial.png"
[ -f "$out" ] && exit 0
conf="$dir/last_conf.dat"
[ -f "$conf" ] || exit 0
t=$(head -1 "$conf" | awk '{print $3}')
[ "$t" = "0" ] && exit 0
sweep="${dir%/output/*}"
mdir="$sweep/main"
mconf="$mdir/last_conf.dat"
[ -f "$mconf" ] || mconf=$(ls "$mdir"/*.dat 2>/dev/null | sort | head -1)
[ -n "$mconf" ] || { echo "ERR(noconf) $dir" >> /tmp/initials_all.log; exit 0; }
top=$(ls "$mdir"/*.phb 2>/dev/null | sort | head -1)
[ -n "$top" ] || { echo "ERR(notop) $dir" >> /tmp/initials_all.log; exit 0; }
if python3 /home/gila/Documents/Github/ppview/render_phb.py --top "$top" --conf "$mconf" \
    --out "$out" --width 1920 --height 1080 --scale 1 --model ball \
    --background white --species-colors --quiet > /dev/null 2>&1; then
  echo "OK  $dir" >> /tmp/initials_all.log
else
  echo "ERR $dir" >> /tmp/initials_all.log
fi
