#!/usr/bin/env bash
# Launch a fullscreen kitty window running a random ASCII screensaver.
# A pidfile lets the resume hook tear it down on user activity.

PIDFILE="/run/user/$(id -u)/hypr-screensaver.pid"

# Already running? Nothing to do.
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    exit 0
fi

# Spawn a fullscreen, frameless, single-window kitty in the dedicated workspace.
# `--class` makes Hyprland window rules match it for full-screen + no-border.
setsid kitty \
    --class hypr-screensaver \
    --title "screensaver" \
    -o background_opacity=1 \
    -o window_padding_width=0 \
    -o hide_window_decorations=yes \
    -o confirm_os_window_close=0 \
    -o foreground='#ebdbb2' \
    -o background='#1d2021' \
    "$HOME/.config/hypr/scripts/screensaver-pick.sh" \
    </dev/null >/dev/null 2>&1 &

KPID=$!
echo "$KPID" > "$PIDFILE"
disown
