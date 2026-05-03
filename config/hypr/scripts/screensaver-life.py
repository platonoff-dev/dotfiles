#!/usr/bin/env python3
"""Conway's Game of Life — gruvbox-tinted, age-coloured cells.

Pure stdlib. Reseeds when the population dies or stabilizes.
"""
import os
import random
import shutil
import signal
import sys
import time

PALETTE = [
    (250, 189, 47),   # yellow — newborn
    (254, 128, 25),   # orange
    (251, 73, 52),    # red
    (211, 134, 155),  # purple
    (131, 165, 152),  # blue
    (142, 192, 124),  # aqua
    (184, 187, 38),   # green
    (213, 196, 161),  # fg2 — oldest / stable
]
GLYPHS = ["•", "●", "●", "■", "■", "▣", "▣", "◉"]


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


def seed(w, h):
    grid = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if random.random() < 0.32:
                grid[y][x] = 1
    return grid


def step(grid, w, h):
    new = [[0] * w for _ in range(h)]
    for y in range(h):
        yp = (y - 1) % h
        yn = (y + 1) % h
        gy_p = grid[yp]
        gy_c = grid[y]
        gy_n = grid[yn]
        for x in range(w):
            xp = (x - 1) % w
            xn = (x + 1) % w
            n = (
                bool(gy_p[xp]) + bool(gy_p[x]) + bool(gy_p[xn])
                + bool(gy_c[xp]) +                  bool(gy_c[xn])
                + bool(gy_n[xp]) + bool(gy_n[x]) + bool(gy_n[xn])
            )
            cell = gy_c[x]
            if cell:
                # Living cell — survives at 2 or 3 neighbours, ages by +1
                if n == 2 or n == 3:
                    new[y][x] = min(cell + 1, len(PALETTE))
                else:
                    new[y][x] = 0
            else:
                # Dead cell — born at exactly 3
                if n == 3:
                    new[y][x] = 1
    return new


def grid_hash(grid):
    return hash(tuple(tuple(row) for row in grid))


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    hide_cursor()

    w, h = shutil.get_terminal_size((80, 24))
    grid = seed(w, h)
    history = []
    same_count = 0
    last_size = (w, h)
    clear()

    try:
        while True:
            tw, th = shutil.get_terminal_size((80, 24))
            if (tw, th) != last_size:
                w, h = tw, th
                grid = seed(w, h)
                history.clear()
                same_count = 0
                last_size = (w, h)
                clear()

            buf = [b"\033[H"]
            for y, row in enumerate(grid):
                line = [f"\033[{y + 1};1H".encode()]
                for x, cell in enumerate(row):
                    if cell:
                        idx = min(cell - 1, len(PALETTE) - 1)
                        r, g, b = PALETTE[idx]
                        glyph = GLYPHS[idx]
                        line.append(
                            f"\033[38;2;{r};{g};{b}m{glyph}".encode()
                        )
                    else:
                        line.append(b" ")
                buf.append(b"".join(line))
            buf.append(b"\033[0m")
            sys.stdout.buffer.write(b"".join(buf))
            sys.stdout.flush()

            grid = step(grid, w, h)

            # Detect stable / oscillating / dead state, then reseed
            h_now = grid_hash(grid)
            if h_now in history:
                same_count += 1
            else:
                same_count = 0
            history.append(h_now)
            if len(history) > 8:
                history.pop(0)

            living = sum(1 for row in grid for c in row if c)
            if living == 0 or same_count > 12:
                time.sleep(1.2)
                grid = seed(w, h)
                history.clear()
                same_count = 0
                clear()

            time.sleep(0.10)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
