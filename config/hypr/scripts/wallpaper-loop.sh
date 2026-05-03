#!/usr/bin/env bash
# Periodic wallpaper rotation. Refetches sources every REFETCH_EVERY rotations.
#   WALLPAPER_INTERVAL  seconds between rotations (default 600)
#   REFETCH_EVERY       rotations between source refetches (default 24)

set -u

INTERVAL="${WALLPAPER_INTERVAL:-600}"
REFETCH_EVERY="${REFETCH_EVERY:-24}"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
WALLPAPER="$SCRIPT_DIR/wallpaper.py"

# Wait for hyprpaper IPC to come up
sleep 3

# Initial pool fill (best-effort, network may be cold)
"$WALLPAPER" fetch >/dev/null 2>&1 || true

i=0
while true; do
    "$WALLPAPER" rotate >/dev/null 2>&1 || true
    i=$((i + 1))
    if (( i % REFETCH_EVERY == 0 )); then
        "$WALLPAPER" fetch >/dev/null 2>&1 || true
    fi
    sleep "$INTERVAL"
done
