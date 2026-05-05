#!/usr/bin/env bash
# Waybar custom module: Cloudflare WARP status.
# Emits JSON {"text":..., "tooltip":..., "class":...} so styles can react
# to the current state (connected / disconnected / connecting / unknown).

set -u

if ! command -v warp-cli >/dev/null 2>&1; then
    jq -nc '{text:"", tooltip:"warp-cli not installed", class:"missing"}'
    exit 0
fi

raw="$(warp-cli status 2>&1)"
status_line="$(printf '%s\n' "$raw" | awk -F': ' '/Status update/{print $2; exit}')"

case "$status_line" in
    Connected)
        icon="󰦝"; class="connected" ;;
    Disconnected|"Disconnected. Reason: "*)
        icon="󰦞"; class="disconnected" ;;
    Connecting|"Connecting...")
        icon="󰔚"; class="connecting" ;;
    Disconnecting|"Disconnecting...")
        icon="󰔚"; class="connecting" ;;
    "Registration Missing"|"Unable to connect"*)
        icon="󰒃"; class="error" ;;
    *)
        icon="󰒃"; class="unknown" ;;
esac

# Tooltip: full warp-cli output, plus a hint line.
tooltip="<b>Cloudflare WARP</b>
${raw}

<i>Left-click: toggle  •  Right-click: stats</i>"

jq -nc --arg text "$icon" --arg tooltip "$tooltip" --arg class "$class" \
    '{text:$text, tooltip:$tooltip, class:$class}'
