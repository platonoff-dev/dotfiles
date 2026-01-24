#!/usr/bin/env python3
"""
Dotfiles setup script for CachyOS/Arch Linux systems.
Handles package installation and dotfile symlinking.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


DOTFILES_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = DOTFILES_DIR / "config.json"


def run_cmd(
    cmd: list[str],
    check: bool = True,
    capture: bool = False,
    sudo: bool = False,
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    if sudo:
        cmd = ["sudo"] + cmd
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
    )


def is_arch_based() -> bool:
    """Check if running on Arch-based system."""
    return shutil.which("pacman") is not None


def load_config() -> dict:
    """Load configuration from config.json."""
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} not found")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)


def install_packages(packages: list[str], aur_helper: str = "paru") -> None:
    """Install packages using pacman or AUR helper."""
    if not packages:
        print("No packages to install")
        return

    print(f"\n{'='*50}")
    print("Installing packages...")
    print(f"{'='*50}")

    # Separate official and AUR packages
    official = []
    aur = []

    for pkg in packages:
        if pkg.startswith("aur:"):
            aur.append(pkg[4:])
        else:
            official.append(pkg)

    # Install official packages
    if official:
        print(f"\nInstalling official packages: {', '.join(official)}")
        run_cmd(["pacman", "-S", "--needed", "--noconfirm"] + official, sudo=True)

    # Install AUR packages
    if aur:
        if not shutil.which(aur_helper):
            print(f"\nAUR helper '{aur_helper}' not found. Installing...")
            install_aur_helper(aur_helper)
        print(f"\nInstalling AUR packages: {', '.join(aur)}")
        run_cmd([aur_helper, "-S", "--needed", "--noconfirm"] + aur)


def install_aur_helper(helper: str = "paru") -> None:
    """Install an AUR helper."""
    if helper == "paru":
        run_cmd(["pacman", "-S", "--needed", "--noconfirm", "base-devel", "git"], sudo=True)
        tmp_dir = Path("/tmp/paru-install")
        tmp_dir.mkdir(exist_ok=True)
        run_cmd(["git", "clone", "https://aur.archlinux.org/paru.git", str(tmp_dir)])
        run_cmd(["makepkg", "-si", "--noconfirm"], check=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        print(f"Unknown AUR helper: {helper}")
        sys.exit(1)


def create_symlink(source: Path, target: Path, backup: bool = True) -> None:
    """Create a symlink, optionally backing up existing files."""
    if target.exists() or target.is_symlink():
        if target.is_symlink() and target.resolve() == source:
            print(f"  [skip] {target} -> already linked")
            return
        if backup:
            backup_path = target.with_suffix(target.suffix + ".backup")
            print(f"  [backup] {target} -> {backup_path}")
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            target.rename(backup_path)
        else:
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source)
    print(f"  [link] {target} -> {source}")


def setup_symlinks(config: dict) -> None:
    """Create symlinks for dotfiles."""
    print(f"\n{'='*50}")
    print("Setting up symlinks...")
    print(f"{'='*50}")

    home = Path.home()
    config_dir = home / ".config"

    # Link files from home/ to ~/
    home_dir = DOTFILES_DIR / "home"
    if home_dir.exists():
        print("\nLinking home files:")
        for item in home_dir.iterdir():
            target = home / f".{item.name}"
            create_symlink(item, target)

    # Link directories from config/ to ~/.config/
    conf_dir = DOTFILES_DIR / "config"
    if conf_dir.exists():
        print("\nLinking config directories:")
        for item in conf_dir.iterdir():
            target = config_dir / item.name
            create_symlink(item, target)


def run_scripts(scripts: list[str]) -> None:
    """Run post-install scripts."""
    if not scripts:
        return

    print(f"\n{'='*50}")
    print("Running post-install scripts...")
    print(f"{'='*50}")

    scripts_dir = DOTFILES_DIR / "scripts"
    for script_name in scripts:
        script_path = scripts_dir / script_name
        if script_path.exists():
            print(f"\nRunning {script_name}...")
            run_cmd([sys.executable, str(script_path)])
        else:
            print(f"Warning: Script not found: {script_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup dotfiles and install packages")
    parser.add_argument(
        "--packages-only",
        action="store_true",
        help="Only install packages, skip symlinks",
    )
    parser.add_argument(
        "--symlinks-only",
        action="store_true",
        help="Only create symlinks, skip package installation",
    )
    parser.add_argument(
        "--no-scripts",
        action="store_true",
        help="Skip running post-install scripts",
    )
    parser.add_argument(
        "--aur-helper",
        default="paru",
        help="AUR helper to use (default: paru)",
    )
    args = parser.parse_args()

    print(f"Dotfiles directory: {DOTFILES_DIR}")

    if not is_arch_based():
        print("Warning: This script is designed for Arch-based systems")
        response = input("Continue anyway? [y/N] ")
        if response.lower() != "y":
            sys.exit(0)

    config = load_config()

    if not args.symlinks_only:
        install_packages(config.get("packages", []), args.aur_helper)

    if not args.packages_only:
        setup_symlinks(config)

    if not args.no_scripts:
        run_scripts(config.get("scripts", []))

    print(f"\n{'='*50}")
    print("Setup complete!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
