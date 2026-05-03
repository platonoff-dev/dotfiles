#!/usr/bin/env python3
"""ASCII fireworks screensaver. Pure stdlib, gruvbox palette."""
import math
import os
import random
import shutil
import signal
import sys
import time

# Gruvbox bright-color set used per firework burst
COLORS = [
    (251, 73, 52),    # red
    (184, 187, 38),   # green
    (250, 189, 47),   # yellow
    (131, 165, 152),  # blue
    (211, 134, 155),  # purple
    (142, 192, 124),  # aqua
    (254, 128, 25),   # orange
]
SPARK = "*"
FADE = ["@", "*", "+", "·", "."]


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


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "maxlife", "color")

    def __init__(self, x, y, vx, vy, life, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.maxlife = life
        self.color = color


class Rocket:
    __slots__ = ("x", "y", "vy", "explode_y", "color", "trail")

    def __init__(self, w, h):
        self.x = random.uniform(w * 0.1, w * 0.9)
        self.y = h - 1
        self.vy = -random.uniform(0.65, 0.95)
        self.explode_y = random.uniform(h * 0.10, h * 0.45)
        self.color = random.choice(COLORS)
        self.trail = []


def explode(rocket):
    n = random.randint(30, 60)
    parts = []
    for _ in range(n):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.25, 0.85)
        # Squash vertically a bit so circles read as circles in 2:1 cell aspect
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed * 0.55
        life = random.randint(18, 32)
        parts.append(Particle(rocket.x, rocket.y, vx, vy, life, rocket.color))
    return parts


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    hide_cursor()
    clear()

    w, h = shutil.get_terminal_size((80, 24))
    rockets = []
    particles = []
    last_launch = 0.0
    last_size_check = 0.0

    try:
        while True:
            now = time.monotonic()
            if now - last_size_check > 0.5:
                w, h = shutil.get_terminal_size((80, 24))
                last_size_check = now

            # Launch a new rocket sometimes
            if now - last_launch > random.uniform(0.4, 1.4) and len(rockets) < 4:
                rockets.append(Rocket(w, h))
                last_launch = now

            # Update rockets
            still_flying = []
            for r in rockets:
                r.y += r.vy
                r.trail.append((r.x, r.y))
                if len(r.trail) > 4:
                    r.trail.pop(0)
                if r.y <= r.explode_y:
                    particles.extend(explode(r))
                else:
                    still_flying.append(r)
            rockets = still_flying

            # Update particles
            alive = []
            for p in particles:
                p.x += p.vx
                p.y += p.vy
                p.vy += 0.04  # gravity
                p.life -= 1
                if p.life > 0 and 0 <= p.x < w and 0 <= p.y < h:
                    alive.append(p)
            particles = alive

            # Draw
            buf = [b"\033[H\033[2J"]

            for r in rockets:
                cr, cg, cb = r.color
                for tx, ty in r.trail:
                    px, py = int(tx), int(ty)
                    if 0 <= px < w and 0 <= py < h:
                        buf.append(
                            f"\033[{py + 1};{px + 1}H"
                            f"\033[38;2;{cr};{cg};{cb}m|".encode()
                        )

            for p in particles:
                px, py = int(p.x), int(p.y)
                if 0 <= px < w and 0 <= py < h:
                    cr, cg, cb = p.color
                    # Fade brightness with remaining life
                    fade = p.life / p.maxlife
                    fr = int(cr * fade)
                    fg = int(cg * fade)
                    fb = int(cb * fade)
                    glyph = FADE[min(len(FADE) - 1, int((1 - fade) * len(FADE)))]
                    buf.append(
                        f"\033[{py + 1};{px + 1}H"
                        f"\033[38;2;{fr};{fg};{fb}m{glyph}".encode()
                    )

            buf.append(b"\033[0m")
            sys.stdout.buffer.write(b"".join(buf))
            sys.stdout.flush()
            time.sleep(0.05)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
