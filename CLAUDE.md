# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Personal dotfiles for an Arch/CachyOS + Hyprland (Wayland) workstation. No tests, no lint, no build — changes are validated by re-running the setup script and observing the live system.

## Common commands

```sh
python3 setup.py                  # install packages + symlink configs + run post-install scripts
python3 setup.py --symlinks-only  # just (re)link configs after edits in this repo
python3 setup.py --packages-only  # just install packages from config.json
python3 setup.py --no-scripts     # skip the post-install scripts list
```

`setup.py` is idempotent: existing files are backed up to `<path>.backup` (overwriting any previous backup) before being replaced with a symlink. Running `--symlinks-only` after editing this repo does NOT require backups since the destination already points back here.

To validate a theme change end-to-end without waiting for darkman's schedule:

```sh
darkman set light    # or: darkman set dark / darkman toggle
darkman get          # query current mode
```

## Architecture

### One declarative manifest, three deploy paths

`config.json` lists `packages` (pacman + AUR with `aur:` prefix; `paru` is bootstrapped if missing) and `scripts` (post-install Python scripts run from `scripts/`). `setup.py` reads it and fans out to:

- `home/<name>` → `~/.<name>` (e.g. `home/zshrc` → `~/.zshrc`)
- `config/<name>` → `~/.config/<name>` (whole-directory symlink)
- `systemd-user/<unit-or-dropin>` → `~/.config/systemd/user/<...>` (placed *inside* the existing systemd user dir, not replacing it)
- `system/` is **not** wired into `setup.py` — it stages root-owned overlays (udev rules, `/usr/local/bin` scripts) that are installed manually with `sudo cp`.

Special case: darkman 2.x reads hook scripts from `$XDG_DATA_HOME/darkman/` but its config from `$XDG_CONFIG_HOME/darkman/`. `setup.py` symlinks the same `config/darkman/` directory to **both** XDG paths so `config.yaml` and `theme.sh` live next to each other in the repo.

### Light/dark theming pipeline

`darkman` is the source of truth for color mode. On every transition it execs `config/darkman/theme.sh light|dark`, which is the single fan-out point. Each themed app has its own coupling style — read `theme.sh` first when adding a new app:

- **gsettings** (`color-scheme`, `gtk-theme`, `icon-theme`, `cursor-theme`) — picked up by GTK3/4 apps via dconf and republished to xdg-desktop-portal, which is what most Wayland apps listen on. **Mozilla apps (Firefox, Thunderbird) auto-switch off this signal — no extra hook needed.**
- **GTK settings.ini + libadwaita CSS symlinks** in `~/.config/gtk-{3,4}.0/` — fallback for apps that ignore dconf and required to keep libadwaita apps in lockstep.
- **Per-app dual stylesheets** — `style-light.css` + `style.css` (dark) for waybar; `style-light.css` + `style-dark.css` for swaync. The hook either pokes the daemon to reload (`pkill -SIGUSR2 waybar`) or copies the right variant into a cache file the daemon was launched with (`swaync-client --reload-css`).
- **D-Bus reload** for Ghostty (`org.gtk.Actions.Activate reload-config`), since it only re-reads its config on demand.
- **Custom IPC** — neovim listens for `SIGUSR1` and re-reads `~/.cache/theme-mode`.

The `~/.cache/theme-mode` sentinel file (written by `theme.sh`) is the canonical "what mode am I in" source for any consumer.

### swaync needs the systemd drop-in

swaync's package-shipped service auto-starts on D-Bus activation, so the Hyprland `exec-once` line isn't enough. `systemd-user/swaync.service.d/override.conf` resets `ExecStart` to launch swaync with `--style %h/.cache/swaync/style.css` and seeds that cache file on first launch. Edits to swaync styling go in `config/swaync/style-{light,dark}.css`; `theme.sh` copies the active one over the cache and reloads.

### Thunderbird auto-theme (the gotcha)

Thunderbird gets its Gruvbox light/dark switching from a single combined "Gruvbox Auto" XPI installed by `scripts/install-thunderbird-theme.py`. The XPI source lives at `config/thunderbird/gruvbox-auto/manifest.json` and uses Mozilla's `theme` (light) + `dark_theme` (dark) sibling keys — Mozilla apps auto-swap variants live whenever `prefers-color-scheme` flips, which is already happening via the `gsettings color-scheme` line in `theme.sh`. So `theme.sh` does NOT need a Thunderbird-specific hook.

The installer only works because the user runs **Thunderbird ESR**, which honors `xpinstall.signatures.required = false` (release-channel TB ignores this). It also patches `extensions.json` directly to enable the sideloaded theme — sideloaded extensions in `<profile>/extensions/` are auto-disabled by Mozilla's security model and `extensions.autoDisableScopes = 0` only affects future scans, not the entry that already got created. The script refuses to patch `extensions.json` while Thunderbird is running because TB clobbers it on shutdown — quit TB and re-run the script.

The script also covers both native (`~/.thunderbird`) and Flatpak (`~/.var/app/org.mozilla.Thunderbird/.thunderbird`) install paths.
