#!/usr/bin/env bash
# Waybar custom module: clock + agenda tooltip.
# Outputs a single JSON line {"text":..., "tooltip":...}.
#
# Tooltip layout:
#   Today, <date>
#     <events>
#   Tomorrow, <date>
#     <events>
#   <ASCII month calendar>
#
# Events come from gcalcli (Google Calendar). If gcalcli is missing or
# unauthenticated, the tooltip degrades gracefully to just the calendar
# plus a hint about how to enable events.

set -u

# --- header text ----------------------------------------------------------
text="󰥔 $(date +'%a %d %b  %H:%M')"

# --- agenda --------------------------------------------------------------
today="$(date +%Y-%m-%d)"
tomorrow="$(date -d 'tomorrow' +%Y-%m-%d)"
day_after="$(date -d 'tomorrow + 1 day' +%Y-%m-%d)"

today_label="Today, $(date +'%a %d %b')"
tomorrow_label="Tomorrow, $(date -d tomorrow +'%a %d %b')"

# Format a gcalcli --tsv block: each line is start_date\tstart_time\tend_date\tend_time\turl\ttitle
# We only care about start_time and title, and we want all-day events to render as "all day".
format_block() {
  awk -F'\t' '
    NF == 0 { next }
    {
      start_time = $2
      title = $6
      # gcalcli emits "00:00" for both ends of all-day events.
      if (start_time == "00:00" && $4 == "00:00") start_time = "all day"
      printf "  %s   %s\n", start_time, title
    }
  '
}

agenda_section=""
if command -v gcalcli >/dev/null 2>&1; then
  if gcalcli_out_today=$(gcalcli agenda --tsv --military --nocolor "$today 00:00" "$tomorrow 00:00" 2>/dev/null) \
     && gcalcli_out_tomorrow=$(gcalcli agenda --tsv --military --nocolor "$tomorrow 00:00" "$day_after 00:00" 2>/dev/null); then

    today_block="$(printf '%s\n' "$gcalcli_out_today"   | format_block)"
    tmrw_block="$(printf '%s\n'  "$gcalcli_out_tomorrow" | format_block)"

    agenda_section+="<b>${today_label}</b>"$'\n'
    agenda_section+="${today_block:-  no events}"$'\n\n'
    agenda_section+="<b>${tomorrow_label}</b>"$'\n'
    agenda_section+="${tmrw_block:-  no events}"$'\n\n'
  else
    agenda_section+="<i>gcalcli not authenticated — run: gcalcli init</i>"$'\n\n'
  fi
else
  agenda_section+="<i>install gcalcli + run: gcalcli init</i>"$'\n\n'
fi

# --- ASCII month calendar ------------------------------------------------
# Monday-first, current day highlighted (cal already underlines today on most systems).
cal_block="$(cal -m 2>/dev/null || cal)"

# --- compose tooltip -----------------------------------------------------
tooltip="${agenda_section}<tt>${cal_block}</tt>"

# Escape characters that break JSON, then emit JSON via jq for safety.
jq -nc --arg text "$text" --arg tooltip "$tooltip" \
  '{text:$text, tooltip:$tooltip}'
