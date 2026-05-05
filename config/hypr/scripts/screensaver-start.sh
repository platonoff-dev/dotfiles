#!/usr/bin/env bash
# Launch a fullscreen kitty running a random ASCII screensaver on every
# monitor. Enter the `screensaver` Hyprland submap so any of its dismiss keys
# (escape / space / return) tears down all instances at once via stop.sh.

# Already running? Nothing to do.
if hyprctl clients -j 2>/dev/null \
    | jq -e 'any(.[]; .class == "hypr-screensaver")' >/dev/null 2>&1; then
    exit 0
fi

focused=$(hyprctl activeworkspace -j 2>/dev/null | jq -r '.monitor // empty')

# Spawn one fullscreen, frameless kitty per monitor. The hyprctl exec dispatch
# sends each spawn to whichever monitor we just focused.
for m in $(hyprctl monitors -j | jq -r '.[].name'); do
    hyprctl dispatch focusmonitor "$m" >/dev/null
    hyprctl dispatch exec -- kitty \
        --class hypr-screensaver \
        --title "screensaver" \
        -o background_opacity=1 \
        -o window_padding_width=0 \
        -o hide_window_decorations=yes \
        -o confirm_os_window_close=0 \
        -o foreground='#ebdbb2' \
        -o background='#1d2021' \
        "$HOME/.config/hypr/scripts/screensaver-pick.sh" >/dev/null
done

[[ -n "$focused" ]] && hyprctl dispatch focusmonitor "$focused" >/dev/null

# Hand the keyboard to the dismiss submap so any window's focus is irrelevant.
hyprctl dispatch submap screensaver >/dev/null
