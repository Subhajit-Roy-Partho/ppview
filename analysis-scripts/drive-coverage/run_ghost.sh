#!/usr/bin/env bash
[ -f "$1/final_ghost.png" ] && exit 0
if python3 "$(dirname "$0")/render_ghost.py" "$1" >> /tmp/ghost_render.log 2>&1; then
  echo "OK  $1" >> /tmp/ghost_render.log
else
  echo "ERR $1" >> /tmp/ghost_render.log
fi
