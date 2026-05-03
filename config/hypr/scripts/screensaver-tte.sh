#!/usr/bin/env bash
# Cycle through random terminaltexteffects on the current time string.
# Requires `tte` (pipx install terminaltexteffects).

trap 'tput cnorm; tput sgr0; clear; exit 0' INT TERM EXIT
tput civis 2>/dev/null

effects=(beams binarypath blackhole bouncyballs bubbles burn colorshift
         crumble decrypt errorcorrect expand fireworks middleout
         orbittingvolley overflow pour print rain randomsequence
         rings scattered slide spotlights spray swarm synthgrid
         unstable vhstape waves wipe)

while :; do
    eff=${effects[$((RANDOM % ${#effects[@]}))]}
    cols=$(tput cols)
    rows=$(tput lines)
    msg=$(date '+%H:%M:%S')
    pad_rows=$(( rows / 2 - 1 ))
    {
        for ((i = 0; i < pad_rows; i++)); do printf '\n'; done
        printf '%s\n' "$msg"
    } | tte --no-color "$eff" 2>/dev/null || sleep 1
    sleep 0.5
    clear
done
