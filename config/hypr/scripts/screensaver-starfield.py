#!/usr/bin/env python3
"""3D star warp screensaver — stars stream toward the viewer.

Pure stdlib, ANSI 24-bit color (gruvbox). Adapts to terminal size.
"""
import os
import random
import shutil
import signal
import sys
import time

# Gruvbox-ish star palette (warm-to-cool, brighter = closer)
PALETTE = [
    (40, 40, 40),       # bg0_h-ish (faintest)
    (102, 92, 84),      # bg3
    (168, 153, 132),    # fg4
    (213, 196, 161),    # fg2
    (235, 219, 178),    # fg
    (250, 189, 47),     # yellow
    (254, 128, 25),     # orange
    (251, 241, 199),    # fg0 (closest -> hottest)
]
GLYPHS = [".", ".", "·", "·", "+", "*", "✦", "✺"]


def hide_cursor():
    sys.stdout.write("\033[?25l")


def show_cursor():
    sys.stdout.write("\033[?25h")


def clear():
    sys.stdout.write("\033[2J\033[H")


def cleanup(*_):
    show_cursor()
    sys.stdout.write("\033[0m")
    clear()
    sys.stdout.flush()
    sys.exit(0)


class Star:
    __slots__ = ("x", "y", "z")

    def __init__(self, w, h):
        self.respawn(w, h)

    def respawn(self, w, h):
        # Pick a random direction in normalized -1..1 space
        self.x = random.uniform(-1.0, 1.0) * (w / h) * 1.5
        self.y = random.uniform(-1.0, 1.0)
        self.z = 1.0  # furthest


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    hide_cursor()
    clear()

    w, h = shutil.get_terminal_size((80, 24))
    n_stars = max(120, (w * h) // 25)
    stars = [Star(w, h) for _ in range(n_stars)]
    speed = 0.022

    try:
        last_size_check = 0.0
        while True:
            now = time.monotonic()
            if now - last_size_check > 0.5:
                w, h = shutil.get_terminal_size((80, 24))
                last_size_check = now

            buf = [b"\033[H"]
            # Clear to draw fresh frame
            buf.append(b"\033[2J")

            cx, cy = w / 2, h / 2
            for s in stars:
                s.z -= speed
                if s.z <= 0.02:
                    s.respawn(w, h)
                    continue

                # Perspective project
                px = int(cx + (s.x / s.z) * cx * 0.6)
                py = int(cy + (s.y / s.z) * cy * 0.6)
                if not (0 <= px < w and 0 <= py < h):
                    s.respawn(w, h)
                    continue

                # Brightness scales with proximity (1 - z)
                idx = min(len(PALETTE) - 1, int((1 - s.z) * len(PALETTE)))
                r, g, b = PALETTE[idx]
                glyph = GLYPHS[idx]
                buf.append(
                    f"\033[{py + 1};{px + 1}H\033[38;2;{r};{g};{b}m{glyph}".encode()
                )

            buf.append(b"\033[0m")
            sys.stdout.buffer.write(b"".join(buf))
            sys.stdout.flush()
            time.sleep(0.03)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
