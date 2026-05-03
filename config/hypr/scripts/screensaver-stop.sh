#!/usr/bin/env bash
# Tear down the screensaver kitty window (and any orphan terminal-tools).

PIDFILE="/run/user/$(id -u)/hypr-screensaver.pid"

if [[ -f "$PIDFILE" ]]; then
    pid=$(cat "$PIDFILE")
    [[ -n "$pid" ]] && kill -TERM "$pid" 2>/dev/null
    rm -f "$PIDFILE"
fi

# Catch any survivors started under the dedicated class
hyprctl dispatch closewindow class:hypr-screensaver >/dev/null 2>&1 || true
pkill -TERM -f 'kitty .*hypr-screensaver' 2>/dev/null || true
