#!/usr/bin/env python3
"""Fetch and rotate wallpapers for hyprpaper.

All sources are free and require no API key:
  - bing        Bing Daily Wallpaper archive
  - apod        NASA Astronomy Picture of the Day (uses DEMO_KEY; set
                NASA_API_KEY from https://api.nasa.gov for a higher rate
                limit, but the demo key is enough for this script)
  - nasa        NASA Image and Video Library (no key, no rate limit)
  - wikimedia   Wikipedia "today's featured image" (last 7 days)
  - wallhaven   Wallhaven toplist, SFW general (no key required)
  - reddit      Top images of the week from curated SFW subreddits

Usage:
  wallpaper.py fetch [--sources bing apod ...]   download into pool
  wallpaper.py rotate                            pick a random pool entry
  wallpaper.py set PATH                          set a specific image
  wallpaper.py list                              list pool entries
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

POOL_DIR = Path.home() / "Pictures" / "wallpapers" / "pool"
USER_AGENT = "wallpaper.py/1.0 (Hyprland dotfiles)"
TIMEOUT = 30
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

REDDIT_SUBS = [
    "EarthPorn",
    "spaceporn",
    "ImaginaryLandscapes",
    "wallpapers",
    "MostBeautiful",
    "SkyPorn",
]

NASA_QUERIES = [
    "galaxy", "nebula", "earth from space", "aurora",
    "mars", "jupiter", "saturn", "hubble",
]


def http_open(url, headers=None):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def http_json(url, headers=None):
    with http_open(url, headers) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url, dest_dir, ext_hint=None):
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(url.encode()).hexdigest()[:16]
    ext = ext_hint or os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
    if ext not in IMAGE_EXTS:
        ext = ".jpg"
    dest = dest_dir / f"{name}{ext}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest, False
    try:
        with http_open(url) as resp:
            data = resp.read()
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"  ! download failed: {url} ({e})", file=sys.stderr)
        return None, False
    if len(data) < 4096:
        return None, False
    dest.write_bytes(data)
    return dest, True


# ---------- sources ----------

def fetch_bing():
    url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=en-US"
    data = http_json(url)
    out = []
    for img in data.get("images", []):
        rel = img.get("url", "")
        if not rel:
            continue
        full = "https://www.bing.com" + rel.replace("1920x1080", "UHD")
        out.append(full)
    return out


def fetch_nasa_apod():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=10"
    data = http_json(url)
    out = []
    for item in data:
        if item.get("media_type") != "image":
            continue
        out.append(item.get("hdurl") or item.get("url"))
    return [u for u in out if u]


def fetch_wikimedia():
    out = []
    today = datetime.now(timezone.utc)
    for delta in range(7):
        day = today - timedelta(days=delta)
        url = (
            "https://api.wikimedia.org/feed/v1/wikipedia/en/featured/"
            f"{day:%Y/%m/%d}"
        )
        try:
            data = http_json(url)
        except Exception:
            continue
        img = data.get("image") or {}
        src = (img.get("image") or {}).get("source")
        if src:
            out.append(src)
    return out


def fetch_nasa_library():
    """NASA Image and Video Library — no API key required."""
    out = []
    for q in random.sample(NASA_QUERIES, k=3):
        url = (
            "https://images-api.nasa.gov/search"
            f"?q={urllib.parse.quote(q)}&media_type=image"
        )
        try:
            data = http_json(url)
        except Exception as e:
            print(f"  ! nasa/{q}: {e}", file=sys.stderr)
            continue
        items = data.get("collection", {}).get("items", [])
        random.shuffle(items)
        for item in items[:8]:
            collection_url = item.get("href")
            if not collection_url:
                continue
            try:
                assets = http_json(collection_url)
            except Exception:
                continue
            # Prefer ~orig, then ~large
            best = None
            for asset in assets:
                if not isinstance(asset, str):
                    continue
                low = asset.lower()
                if "~orig" in low and any(
                    low.split("?")[0].endswith(e) for e in IMAGE_EXTS
                ):
                    best = asset
                    break
                if "~large" in low and not best:
                    best = asset
            if best:
                out.append(best)
    return out


def fetch_wallhaven():
    """Wallhaven SFW toplist — no API key required for SFW content."""
    url = (
        "https://wallhaven.cc/api/v1/search"
        "?categories=100&purity=100&sorting=toplist&topRange=1M"
        "&atleast=1920x1080"
    )
    try:
        data = http_json(url)
    except Exception as e:
        print(f"  ! wallhaven: {e}", file=sys.stderr)
        return []
    return [item["path"] for item in data.get("data", []) if item.get("path")]


def fetch_reddit():
    out = []
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=25"
        try:
            data = http_json(url)
        except Exception as e:
            print(f"  ! reddit/{sub}: {e}", file=sys.stderr)
            continue
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("over_18"):
                continue
            link = post.get("url_overridden_by_dest") or post.get("url") or ""
            low = link.lower().split("?")[0]
            if not any(low.endswith(e) for e in IMAGE_EXTS):
                continue
            out.append(link)
    return out


SOURCES = {
    "bing": fetch_bing,
    "apod": fetch_nasa_apod,
    "nasa": fetch_nasa_library,
    "wikimedia": fetch_wikimedia,
    "wallhaven": fetch_wallhaven,
    "reddit": fetch_reddit,
}


# ---------- commands ----------

def pool_files():
    if not POOL_DIR.exists():
        return []
    return [
        p for p in POOL_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def cmd_fetch(sources):
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    new = 0
    for name in sources:
        fn = SOURCES.get(name)
        if not fn:
            print(f"unknown source: {name}", file=sys.stderr)
            continue
        print(f"==> {name}")
        try:
            urls = fn()
        except Exception as e:
            print(f"  ! fetch failed: {e}", file=sys.stderr)
            continue
        dest = POOL_DIR / name
        for url in urls:
            path, fresh = download(url, dest)
            if path and fresh:
                new += 1
                print(f"  + {path.relative_to(POOL_DIR)}")
    print(f"\nFetched {new} new wallpapers (pool: {len(pool_files())} total).")


def hyprctl(*args):
    return subprocess.run(
        ["hyprctl", "hyprpaper", *args],
        capture_output=True, text=True, check=False,
    )


def cmd_set(target):
    print(f"setting wallpaper: {target}")
    hyprctl("preload", str(target))
    hyprctl("wallpaper", f",{target}")
    # Free memory of any preloads no longer on screen.
    hyprctl("unload", "unused")


def cmd_rotate():
    pool = pool_files()
    if not pool:
        print("Wallpaper pool is empty. Run `wallpaper.py fetch` first.",
              file=sys.stderr)
        sys.exit(1)
    cmd_set(random.choice(pool))


def cmd_list():
    for p in sorted(pool_files()):
        print(p)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="Download new wallpapers")
    f.add_argument("--sources", nargs="*", default=list(SOURCES.keys()))
    s = sub.add_parser("set", help="Set a specific wallpaper")
    s.add_argument("path")
    sub.add_parser("rotate", help="Pick a random pool entry and set it")
    sub.add_parser("list", help="List pool entries")
    args = parser.parse_args()
    if args.cmd == "fetch":
        cmd_fetch(args.sources)
    elif args.cmd == "set":
        cmd_set(Path(args.path).expanduser())
    elif args.cmd == "rotate":
        cmd_rotate()
    elif args.cmd == "list":
        cmd_list()


if __name__ == "__main__":
    main()
