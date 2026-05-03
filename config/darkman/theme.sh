#!/bin/sh
# darkman 2.x hook: receives "light" or "dark" as $1.
# Lives at $XDG_DATA_HOME/darkman/theme.sh (symlinked from dotfiles/config/darkman/).

mode="$1"
echo "$mode" > "$HOME/.cache/theme-mode"

# Wake any running nvim instances so they re-read the sentinel and swap colorscheme.
pkill -USR1 -x nvim 2>/dev/null || true

# Ghostty reads the system theme only on config (re)load, so poke it via D-Bus.
gdbus call --session --dest com.mitchellh.ghostty \
  --object-path /com/mitchellh/ghostty \
  --method org.gtk.Actions.Activate \
  reload-config '@av []' '@a{sv} {}' >/dev/null 2>&1 || true

# GTK / GNOME apps (also feeds xdg-desktop-portal-gtk's appearance interface).
case "$mode" in
  light)
    gsettings set org.gnome.desktop.interface color-scheme prefer-light 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme Adwaita 2>/dev/null || true
    ;;
  dark)
    gsettings set org.gnome.desktop.interface color-scheme prefer-dark 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme Adwaita-dark 2>/dev/null || true
    ;;
esac
