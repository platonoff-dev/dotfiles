#!/usr/bin/env bash
# Pick and run a random ASCII screensaver. Always exec'd inside a fullscreen
# kitty terminal opened by screensaver-start.sh.

set -e
SCRIPTS="$HOME/.config/hypr/scripts"

savers=()

# ---- Custom Python animations (always available) ----
savers+=("python3 $SCRIPTS/screensaver-starfield.py")
savers+=("python3 $SCRIPTS/screensaver-fireworks.py")
savers+=("python3 $SCRIPTS/screensaver-life.py")
savers+=("$SCRIPTS/screensaver-donut.sh")

# ---- Tools from official Arch repos ----
if command -v cmatrix >/dev/null 2>&1; then
    savers+=("cmatrix -ab -u 4 -C cyan")
    savers+=("cmatrix -ab -u 6 -C green")
fi
if command -v asciiquarium >/dev/null 2>&1; then
    savers+=("asciiquarium")
fi
if command -v nyancat >/dev/null 2>&1; then
    savers+=("nyancat")
fi

# ---- AUR optional packages ----
if command -v cbonsai >/dev/null 2>&1; then
    savers+=("cbonsai -li -t 0.6 -L 32 -M 4")
fi
if command -v pipes.sh >/dev/null 2>&1; then
    savers+=("pipes.sh -t 1 -p 3 -r 4000")
elif command -v pipes-rs >/dev/null 2>&1; then
    savers+=("pipes-rs")
fi
if command -v unimatrix >/dev/null 2>&1; then
    savers+=("unimatrix -a -s 96 -l 'oOcCFKkM'")
fi
if command -v rsclock >/dev/null 2>&1; then
    savers+=("rsclock")
fi
if command -v tte >/dev/null 2>&1; then
    savers+=("$SCRIPTS/screensaver-tte.sh")
fi

idx=$((RANDOM % ${#savers[@]}))
exec ${savers[$idx]}
