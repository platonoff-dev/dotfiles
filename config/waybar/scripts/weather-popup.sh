#!/usr/bin/env bash
# Toggle a TUI weather popup (wttr.in) pinned just below the waybar weather
# indicator. Click again — or press any key in the terminal — to dismiss.
#
# Robustness:
# • flock guards against fast double-clicks spawning duplicate popups.
# • close path loops until no matching windows remain (Hyprland's
#   closewindow only kills the first match per call).
set -u

CLASS="com.local.WeatherPopup"
LOCK="${XDG_RUNTIME_DIR:-/tmp}/weather-popup.lock"

# Serialize toggles. -w 1 lets a click that arrives mid-spawn wait briefly
# rather than dropping the second toggle entirely.
exec 9>"$LOCK"
if ! flock -w 1 9; then
    exit 0
fi

popup_count() {
    hyprctl clients -j 2>/dev/null \
        | jq --arg c "$CLASS" '[.[] | select(.class == $c)] | length'
}

# --- close path: any popups open? close them all and exit. -----------------
if [[ "$(popup_count)" -gt 0 ]]; then
    for _ in 1 2 3 4 5 6 7 8; do
        [[ "$(popup_count)" -eq 0 ]] && break
        hyprctl dispatch closewindow "class:^(com\\.local\\.WeatherPopup)$" >/dev/null
        sleep 0.05
    done
    exit 0
fi

# --- open path: spawn one ghostty, then anchor it. -------------------------
loc="${WTTR_LOCATION:-}"

# 9>&- prevents ghostty from inheriting our flock, which would otherwise hold
# the lock for the lifetime of the popup and block every subsequent toggle.
ghostty --class="$CLASS" --title=weather -e bash -c "
    if ! curl -s --max-time 8 'https://wttr.in/${loc}?Fn2' 2>/dev/null; then
        printf 'Weather unavailable.\n'
    fi
    printf '\n%s' 'Press any key to close...'
    read -rsn1
" 9>&- >/dev/null 2>&1 &
disown

# Position under the bar on the currently-focused monitor. center-floats
# beats any windowrule `move`, so we issue movewindowpixel here instead.
WIDTH=720
RIGHT_MARGIN=8        # waybar margin-right
TOP_OFFSET=42         # waybar margin-top (4) + height (32) + gap (6)

for _ in $(seq 1 40); do
    if [[ "$(popup_count)" -gt 0 ]]; then
        read -r mx mw <<<"$(hyprctl monitors -j | jq -r '.[] | select(.focused) | "\(.x) \(.width)"')"
        target_x=$(( mx + mw - WIDTH - RIGHT_MARGIN ))
        hyprctl dispatch movewindowpixel "exact $target_x $TOP_OFFSET,class:^(com\\.local\\.WeatherPopup)$" >/dev/null
        break
    fi
    sleep 0.05
done
