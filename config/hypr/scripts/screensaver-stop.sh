#!/usr/bin/env bash
# Tear down every screensaver kitty across all monitors and exit the dismiss
# submap. Idempotent — safe to call when nothing's running.

hyprctl dispatch submap reset >/dev/null 2>&1

for _ in 1 2 3 4; do
    hyprctl clients -j 2>/dev/null \
        | jq -e 'any(.[]; .class == "hypr-screensaver")' >/dev/null 2>&1 \
        || break
    hyprctl dispatch closewindow class:hypr-screensaver >/dev/null 2>&1 || true
done

# Catch survivors that haven't fully registered with hyprctl yet
pkill -TERM -f 'kitty .*hypr-screensaver' 2>/dev/null || true
