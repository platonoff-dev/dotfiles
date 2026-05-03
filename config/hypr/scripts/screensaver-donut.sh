#!/usr/bin/env bash
# Spinning ASCII donut — Andy Sloane's classic torus, pure-bash variant.
# Pure stdlib, no deps. Gruvbox-tinted ANSI.

trap 'tput cnorm; tput sgr0; clear; exit 0' INT TERM EXIT
tput civis 2>/dev/null

# Gruvbox orange foreground on default bg
printf '\033[38;2;254;128;25m'

A=0
B=0

while :; do
    # Build frame in awk for speed
    awk -v A="$A" -v B="$B" 'BEGIN {
        cols = 80
        rows = 24
        # Try terminal size from env
        if (ENVIRON["COLUMNS"] != "") cols = ENVIRON["COLUMNS"]
        if (ENVIRON["LINES"]   != "") rows = ENVIRON["LINES"]

        for (k = 0; k < cols * rows; k++) { b[k] = " "; z[k] = 0 }

        cA = cos(A); sA = sin(A)
        cB = cos(B); sB = sin(B)

        for (j = 0; j < 6.28; j += 0.07) {
            cj = cos(j); sj = sin(j)
            for (i = 0; i < 6.28; i += 0.02) {
                ci = cos(i); si = sin(i)
                h = cj + 2
                D = 1 / (si * h * sA + sj * cA + 5)
                t = si * h * cA - sj * sA

                x = int(cols/2  + (cols * 0.30) * D * (ci * h * cB - t * sB))
                y = int(rows/2  + (rows * 0.30) * D * (ci * h * sB + t * cA))
                o = x + cols * y
                N = int(8 * ((sj * sA - si * cj * cA) * cB - si * cj * sA - sj * cA - ci * cj * sB))

                if (y >= 0 && y < rows && x >= 0 && x < cols && D > z[o]) {
                    z[o] = D
                    chars = ".,-~:;=!*#$@"
                    idx = (N > 0) ? N : 0
                    if (idx > 11) idx = 11
                    b[o] = substr(chars, idx + 1, 1)
                }
            }
        }

        # Move cursor home, then dump
        printf "\033[H"
        for (k = 0; k < cols * rows; k++) {
            printf "%s", b[k]
            if ((k + 1) % cols == 0) printf "\n"
        }
    }'

    A=$(awk -v a="$A" 'BEGIN { print a + 0.05 }')
    B=$(awk -v b="$B" 'BEGIN { print b + 0.03 }')
    sleep 0.04
done
