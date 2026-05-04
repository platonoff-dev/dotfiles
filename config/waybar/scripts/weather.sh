#!/usr/bin/env bash
# Waybar custom module: current weather via wttr.in.
# Outputs a single JSON line {"text":..., "tooltip":..., "alt":...}.
#
# Location auto-detects from public IP. Override with $WTTR_LOCATION
# (e.g. "Berlin", "Lviv", "EWR" for an airport code).
#
# Cached for 15 minutes in $XDG_CACHE_HOME to avoid hammering wttr.in
# when waybar restarts or the interval is short.

set -u

cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/waybar"
cache_file="$cache_dir/weather.json"
mkdir -p "$cache_dir"

location="${WTTR_LOCATION:-}"
url="https://wttr.in/${location}?format=j1"

# Reuse cache if it's fresh (< 900s) and non-empty.
if [ -s "$cache_file" ] && [ "$(( $(date +%s) - $(stat -c %Y "$cache_file") ))" -lt 900 ]; then
  raw="$(cat "$cache_file")"
else
  raw="$(curl --max-time 6 -fsSL "$url" 2>/dev/null || true)"
  if [ -n "$raw" ] && printf '%s' "$raw" | jq -e . >/dev/null 2>&1; then
    printf '%s' "$raw" > "$cache_file"
  elif [ -s "$cache_file" ]; then
    raw="$(cat "$cache_file")"
  fi
fi

if [ -z "${raw:-}" ]; then
  printf '{"text":"󰼯 ?","tooltip":"Weather unavailable","alt":"offline","class":"offline"}\n'
  exit 0
fi

# Map wttr.in weatherCode → nerd-font icon. Codes from
# https://github.com/chubin/wttr.in/blob/master/lib/constants.py
icon_for_code() {
  case "$1" in
    113) printf '󰖙' ;;                # Sunny / Clear
    116) printf '󰖕' ;;                # Partly cloudy
    119|122) printf '󰖐' ;;            # Cloudy / Overcast
    143|248|260) printf '󰖑' ;;        # Mist / Fog
    176|263|266|293|296|299|302|353) printf '󰖗' ;;  # Light rain / drizzle
    179|227|320|323|326|368) printf '󰖘' ;;          # Light snow
    182|185|281|284|311|314|317|350|374|377) printf '󰙿' ;;  # Freezing rain / sleet
    200|386|389|392|395) printf '󰖓' ;;             # Thunder
    230|329|332|335|338|371) printf '󰼶' ;;         # Heavy snow / blizzard
    305|308|356|359) printf '' ;;                # Heavy rain
    *) printf '󰖙' ;;
  esac
}

read -r code temp feels desc humidity wind area <<EOF
$(printf '%s' "$raw" | jq -r '
  .current_condition[0] as $c
  | .nearest_area[0] as $a
  | [$c.weatherCode, $c.temp_C, $c.FeelsLikeC, ($c.weatherDesc[0].value),
     $c.humidity, $c.windspeedKmph,
     ($a.areaName[0].value + ", " + ($a.country[0].value // ""))]
  | @tsv
' 2>/dev/null)
EOF

if [ -z "${code:-}" ]; then
  printf '{"text":"󰼯 ?","tooltip":"Weather parse failed","alt":"error","class":"error"}\n'
  exit 0
fi

icon="$(icon_for_code "$code")"
text="$icon ${temp}°"

# Build a multi-line tooltip with today's high/low and next few hours.
tooltip="$(printf '%s' "$raw" | jq -r --arg desc "$desc" --arg area "$area" \
  --arg feels "$feels" --arg hum "$humidity" --arg wind "$wind" '
  .weather[0] as $today
  | "<b>" + $area + "</b>\n"
    + $desc + "  •  feels " + $feels + "°\n"
    + "High " + $today.maxtempC + "°  /  Low " + $today.mintempC + "°\n"
    + "Humidity " + $hum + "%  •  Wind " + $wind + " km/h\n"
    + "Sunrise " + $today.astronomy[0].sunrise
    + "  •  Sunset " + $today.astronomy[0].sunset
    + "\n\n<b>Today</b>\n"
    + ([$today.hourly[] | "  " + (((.time|tonumber)/100|floor|tostring)) + ":00  "
        + .tempC + "°  " + .weatherDesc[0].value] | join("\n"))
')"

jq -nc --arg text "$text" --arg tooltip "$tooltip" --arg alt "code$code" \
  '{text:$text, tooltip:$tooltip, alt:$alt, class:$alt}'
