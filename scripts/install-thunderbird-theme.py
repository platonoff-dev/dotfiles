#!/usr/bin/env python3
"""
Install the bundled Gruvbox Auto theme into every Thunderbird profile we find.

Why this exists: Mozilla's WebExtension theme API supports two color sets per
manifest (`theme` for light, `dark_theme` for dark) and Thunderbird picks the
right one live based on the system color scheme — exactly the signal darkman
already toggles via `org.gnome.desktop.interface color-scheme`. The two ATN
themes the user had installed previously each define only one variant, so they
can't auto-switch; this combined theme can.

Caveats:
- Self-built/unsigned themes only install when xpinstall.signatures.required is
  false. That pref is honored on ESR/Dev/Nightly builds (which the user runs);
  release-channel Thunderbird ignores it.
- Sideloaded extensions in <profile>/extensions/ are auto-disabled by Mozilla's
  security model (the "extensions.autoDisableScopes" default disables them on
  first scan). We patch extensions.json to flip our theme to enabled+active and
  delete addonStartup.json.lz4 so Thunderbird reseeds the cache on next launch.
- Patching the on-disk JSON only sticks if Thunderbird is closed when we write
  it; a running Thunderbird will overwrite it on shutdown. The script refuses
  to patch a live profile and prints what to do instead.
- Theme.id is pinned via user.js so Thunderbird re-applies it on every launch
  even if prefs.js gets out of sync.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from configparser import ConfigParser
from pathlib import Path

THEME_SRC = Path(__file__).resolve().parent.parent / "config/thunderbird/gruvbox-auto"
THEME_ID = "gruvbox-auto@platonoff.dotfiles"

# Candidate roots for Thunderbird profiles (native + Flatpak, in priority order).
PROFILE_ROOTS = [
    Path.home() / ".thunderbird",
    Path.home() / ".var/app/org.mozilla.Thunderbird/.thunderbird",
]

# user.js prefs we want to ensure on every profile we touch.
USER_JS_PREFS = {
    "xpinstall.signatures.required": False,
    "extensions.autoDisableScopes": 0,
    "extensions.activeThemeID": THEME_ID,
}

USER_JS_MARKER_BEGIN = "// >>> dotfiles: gruvbox-auto theme >>>"
USER_JS_MARKER_END = "// <<< dotfiles: gruvbox-auto theme <<<"


def find_profiles(root: Path) -> list[Path]:
    """Return every profile dir listed in <root>/profiles.ini."""
    ini_path = root / "profiles.ini"
    if not ini_path.exists():
        return []
    cfg = ConfigParser()
    cfg.read(ini_path)
    profiles = []
    for section in cfg.sections():
        if not section.startswith("Profile"):
            continue
        path = cfg.get(section, "Path", fallback=None)
        if not path:
            continue
        is_relative = cfg.get(section, "IsRelative", fallback="1") == "1"
        profile_dir = root / path if is_relative else Path(path)
        if profile_dir.is_dir():
            profiles.append(profile_dir)
    return profiles


def build_xpi(dest: Path) -> None:
    """Zip the theme source into a Thunderbird-installable XPI at dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in sorted(THEME_SRC.rglob("*")):
            if entry.is_file():
                zf.write(entry, entry.relative_to(THEME_SRC).as_posix())


def install_xpi(profile: Path, xpi_src: Path) -> Path:
    """Drop the XPI into <profile>/extensions/<id>.xpi and return the path."""
    ext_dir = profile / "extensions"
    ext_dir.mkdir(exist_ok=True)
    target = ext_dir / f"{THEME_ID}.xpi"
    shutil.copy2(xpi_src, target)
    return target


def thunderbird_running() -> bool:
    """True if a Thunderbird process is currently active."""
    try:
        subprocess.run(
            ["pgrep", "-x", "thunderbird"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    # Flatpak wraps thunderbird with bwrap, so the binary name differs.
    try:
        result = subprocess.run(
            ["pgrep", "-af", "org.mozilla.Thunderbird"],
            check=False,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def patch_extensions_json(profile: Path) -> bool:
    """Force-enable our theme + force-disable any other active themes.

    Sideloaded extensions get userDisabled=true on first scan because of
    extensions.autoDisableScopes. Setting that pref to 0 only affects future
    scans; the existing entry stays disabled until we flip it manually.
    Returns True if anything changed.
    """
    ext_json = profile / "extensions.json"
    if not ext_json.exists():
        return False
    data = json.loads(ext_json.read_text())
    changed = False
    for addon in data.get("addons", []):
        if addon.get("type") != "theme":
            continue
        if addon.get("id") == THEME_ID:
            if addon.get("userDisabled") or not addon.get("active"):
                addon["userDisabled"] = False
                addon["active"] = True
                addon["appDisabled"] = False
                changed = True
        else:
            if addon.get("active"):
                addon["active"] = False
                addon["userDisabled"] = True
                changed = True
    if changed:
        tmp = ext_json.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(ext_json)
        # Drop the binary startup cache; Thunderbird rebuilds it from
        # extensions.json on next launch.
        for cache in ("addonStartup.json.lz4", "extensions.ini"):
            (profile / cache).unlink(missing_ok=True)
    return changed


def write_user_js(profile: Path) -> None:
    """Append (or replace) our marked block in <profile>/user.js."""
    user_js = profile / "user.js"
    existing = user_js.read_text() if user_js.exists() else ""

    # Strip any prior block we wrote so re-runs don't accumulate duplicates.
    if USER_JS_MARKER_BEGIN in existing and USER_JS_MARKER_END in existing:
        before, _, rest = existing.partition(USER_JS_MARKER_BEGIN)
        _, _, after = rest.partition(USER_JS_MARKER_END)
        existing = (before.rstrip() + "\n" + after.lstrip()).strip() + "\n"

    block_lines = [USER_JS_MARKER_BEGIN]
    for key, value in USER_JS_PREFS.items():
        block_lines.append(f'user_pref("{key}", {json.dumps(value)});')
    block_lines.append(USER_JS_MARKER_END)
    block = "\n".join(block_lines) + "\n"

    if existing and not existing.endswith("\n"):
        existing += "\n"
    user_js.write_text(existing + block)


def main() -> int:
    if not THEME_SRC.is_dir():
        print(f"theme source missing: {THEME_SRC}", file=sys.stderr)
        return 1

    xpi_path = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    xpi_path = xpi_path / "dotfiles" / f"{THEME_ID}.xpi"
    build_xpi(xpi_path)
    print(f"built: {xpi_path}")

    tb_live = thunderbird_running()
    if tb_live:
        print(
            "Thunderbird is running. The XPI and user.js will be staged, but "
            "extensions.json patching is skipped — it would be clobbered on "
            "exit. Quit Thunderbird and re-run this script to finish.",
            file=sys.stderr,
        )

    touched = 0
    patched = 0
    for root in PROFILE_ROOTS:
        for profile in find_profiles(root):
            print(f"installing into: {profile}")
            install_xpi(profile, xpi_path)
            write_user_js(profile)
            if not tb_live and patch_extensions_json(profile):
                patched += 1
            touched += 1

    if touched == 0:
        print(
            "no Thunderbird profiles found; launch Thunderbird once to create "
            "one, then re-run this script.",
            file=sys.stderr,
        )
        return 1

    print(f"\ndone. staged into {touched} profile(s); patched {patched}.")
    if tb_live:
        print("Quit Thunderbird (`flatpak kill org.mozilla.Thunderbird`) "
              "and re-run this script.")
        return 2
    print("Launch Thunderbird; the theme will follow the system color scheme.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
