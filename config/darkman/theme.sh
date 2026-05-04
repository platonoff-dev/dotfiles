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

# GTK / GNOME apps. We swap three things in lockstep:
#   1. gsettings — picked up by GTK3/GTK4 apps that listen to dconf, and feeds
#      xdg-desktop-portal's appearance interface (which waybar reads).
#   2. settings.ini — fallback for apps that don't read gsettings.
#   3. ~/.config/gtk-4.0/{gtk.css,assets} symlinks — required for libadwaita
#      apps, which mostly ignore gtk-theme but do read this CSS.
# icon-theme also swaps so tray icons (nm-applet, blueman) stay readable —
# Papirus-Dark is white and disappears on a light bar.
case "$mode" in
  light)
    gtk_theme="Colloid-Light-Gruvbox"
    icon_theme="Papirus-Light"
    color_scheme="prefer-light"
    prefer_dark="false"
    ;;
  dark)
    gtk_theme="Colloid-Dark-Gruvbox"
    icon_theme="Papirus-Dark"
    color_scheme="prefer-dark"
    prefer_dark="true"
    ;;
esac

gsettings set org.gnome.desktop.interface color-scheme "$color_scheme" 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme   "$gtk_theme"    2>/dev/null || true
gsettings set org.gnome.desktop.interface icon-theme  "$icon_theme"   2>/dev/null || true
gsettings set org.gnome.desktop.interface cursor-theme "Bibata-Modern-Ice" 2>/dev/null || true

# Rewrite settings.ini for both GTK3 and GTK4. These are read by apps that
# don't speak dconf (e.g. GTK apps under non-GNOME sessions occasionally fall
# back to this).
write_gtk_settings() {
  target="$1"
  mkdir -p "$(dirname "$target")"
  cat > "$target" <<EOF
[Settings]
gtk-theme-name=$gtk_theme
gtk-icon-theme-name=$icon_theme
gtk-font-name=CaskaydiaCove Nerd Font 10
gtk-cursor-theme-name=Bibata-Modern-Ice
gtk-cursor-theme-size=24
gtk-application-prefer-dark-theme=$prefer_dark
EOF
}
write_gtk_settings "$HOME/.config/gtk-3.0/settings.ini"
write_gtk_settings "$HOME/.config/gtk-4.0/settings.ini"

# Re-link libadwaita CSS to the active Colloid variant.
gtk4_src="/usr/share/themes/$gtk_theme/gtk-4.0"
if [ -d "$gtk4_src" ]; then
  mkdir -p "$HOME/.config/gtk-4.0"
  ln -sfn "$gtk4_src/gtk.css" "$HOME/.config/gtk-4.0/gtk.css"
  ln -sfn "$gtk4_src/assets"  "$HOME/.config/gtk-4.0/assets"
  # gtk-dark.css is what apps with prefer-dark-theme read; keep it consistent.
  if [ -e "$gtk4_src/gtk-dark.css" ]; then
    ln -sfn "$gtk4_src/gtk-dark.css" "$HOME/.config/gtk-4.0/gtk-dark.css"
  else
    rm -f "$HOME/.config/gtk-4.0/gtk-dark.css"
  fi
fi

# Waybar usually reacts to the portal appearance signal on its own, but the
# bridge can be flaky — kick it directly so the right style-<mode>.css loads.
pkill -SIGUSR2 -x waybar 2>/dev/null || true

# swaync has no built-in light/dark switching: copy the right variant into the
# cache file that swaync was launched with, then ask it to reparse.
swaync_src="$HOME/.config/swaync/style-${mode}.css"
swaync_dst="${XDG_CACHE_HOME:-$HOME/.cache}/swaync/style.css"
if [ -r "$swaync_src" ]; then
  mkdir -p "$(dirname "$swaync_dst")"
  cp -f "$swaync_src" "$swaync_dst"
  swaync-client --reload-css 2>/dev/null || true
fi
