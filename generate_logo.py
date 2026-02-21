"""
generate_logo.py — CAPTCHArun logo generator.

Renders a 630x500 PNG logo using pure pygame vector graphics.
Run once to produce captcharun_logo.png for itch.io.

Design:
    - Dark background (#1a1a1a) — breaks from the in-game gray, more striking
    - Large reCAPTCHA-style widget frame dominating the canvas
    - Giant checkbox on the left, checked with a bold blue cuboid
    - "CAPTCHArun" title in monospace, large and bold
    - Tagline: "you are not a robot. prove it. forever."
    - Floating cuboids in background for depth
    - Scanline texture overlay
    - Bottom strip in game-palette blue with "Free on itch.io"

Usage:
    python generate_logo.py
    → captcharun_logo.png
"""

import pygame
import math
import random
import sys
import os

# ── Add project root to path so we can import from the game ──────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from settings import COLOR, CUBOID_DEPTH
from renderer.cuboid import draw_cuboid, draw_flat_tile
from utils.color import lighter, darker

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 630, 500

# ── Colors (extend palette for logo) ─────────────────────────────────────────
BG          = (18, 18, 18)
WIDGET_BG   = (240, 240, 240)
WIDGET_BORDER = (180, 180, 180)
BLUE        = COLOR["highlight"]       # #2A5DB0
BLUE_LIGHT  = lighter(BLUE, 30)
CHROME      = COLOR["chrome"]
TEXT_DARK   = COLOR["text"]
TEXT_LIGHT  = (255, 255, 255)
TEXT_MUTED  = (140, 140, 140)


def draw_bg_cuboids(surface: pygame.Surface) -> None:
    """Draw floating translucent cuboids in the dark background for depth."""
    random.seed(7)
    for _ in range(14):
        x    = random.randint(-10, W)
        y    = random.randint(-10, H)
        size = random.randint(14, 42)
        alpha = random.randint(18, 50)
        d = 8

        front = [(x,y),(x+size,y),(x+size,y+size),(x,y+size)]
        top   = [(x,y),(x+size,y),(x+size+d,y-d),(x+d,y-d)]
        right = [(x+size,y),(x+size+d,y-d),(x+size+d,y+size-d),(x+size,y+size)]

        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(ov, (*lighter(BLUE, 20), alpha), top)
        pygame.draw.polygon(ov, (*darker(BLUE, 20), alpha),  right)
        pygame.draw.polygon(ov, (*BLUE, alpha),               front)
        surface.blit(ov, (0, 0))
    random.seed()


def draw_scanlines(surface: pygame.Surface) -> None:
    """Draw subtle scanline texture over the whole canvas."""
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 3):
        pygame.draw.line(ov, (0, 0, 0, 22), (0, y), (W, y))
    surface.blit(ov, (0, 0))


def draw_widget_frame(surface: pygame.Surface) -> None:
    """Draw the reCAPTCHA widget chrome — the visual anchor of the logo."""
    mx, my = 28, 120
    mw, mh = W - 56, 240

    # Shadow
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(ov, (0,0,0,60), (mx+4, my+4, mw, mh), border_radius=8)
    surface.blit(ov, (0,0))

    # Widget body
    pygame.draw.rect(surface, WIDGET_BG, (mx, my, mw, mh), border_radius=6)
    pygame.draw.rect(surface, WIDGET_BORDER, (mx, my, mw, mh), 2, border_radius=6)

    # Bottom chrome bar
    bar_h = 42
    bar_y = my + mh - bar_h
    pygame.draw.rect(surface, CHROME, (mx, bar_y, mw, bar_h))
    pygame.draw.rect(surface, WIDGET_BORDER, (mx, my, mw, mh), 2, border_radius=6)

    f = pygame.font.SysFont("couriernew", 13)
    brand  = f.render("reCAPTCHA", True, WIDGET_BG)
    policy = f.render("Privacy  -  Terms", True, (180,180,180))
    surface.blit(brand,  (mx + mw - brand.get_width()  - 14, bar_y + (bar_h - brand.get_height())  // 2))
    surface.blit(policy, (mx + 14,                           bar_y + (bar_h - policy.get_height()) // 2))


def draw_checked_checkbox(surface: pygame.Surface) -> None:
    """Draw a large checked cuboid checkbox inside the widget."""
    size = 80
    x    = 60
    y    = 152

    # Raised cuboid — checked state
    draw_cuboid(surface, x, y, size, size, BLUE, d=12, border_color=(30,30,30))

    # Bold checkmark
    p1 = (x + 14,      y + size//2)
    p2 = (x + size//2 - 4, y + size - 16)
    p3 = (x + size - 14,   y + 16)
    pygame.draw.line(surface, TEXT_LIGHT, p1, p2, 6)
    pygame.draw.line(surface, TEXT_LIGHT, p2, p3, 6)


def draw_label(surface: pygame.Surface) -> None:
    """Draw 'I am not a robot' label next to the checkbox."""
    f_lg = pygame.font.SysFont("couriernew", 22, bold=True)
    f_sm = pygame.font.SysFont("couriernew", 13)

    label = f_lg.render("I am not a robot.", True, TEXT_DARK)
    sub   = f_sm.render("(are you sure?)",   True, CHROME)

    lx = 168
    surface.blit(label, (lx, 172))
    surface.blit(sub,   (lx, 172 + label.get_height() + 4))


def draw_title(surface: pygame.Surface) -> None:
    """Draw the game title and tagline above the widget."""
    f_title = pygame.font.SysFont("couriernew", 52, bold=True)
    f_tag   = pygame.font.SysFont("couriernew", 14)

    title = f_title.render("CAPTCHArun", True, TEXT_LIGHT)
    tag   = f_tag.render("you are not a robot.  prove it.  forever.", True, TEXT_MUTED)

    cx = W // 2
    surface.blit(title, (cx - title.get_width() // 2, 32))

    # Blue underline accent under title
    ul_y = 32 + title.get_height() + 2
    pygame.draw.rect(surface, BLUE, (cx - 140, ul_y, 280, 3))

    surface.blit(tag, (cx - tag.get_width() // 2, ul_y + 10))


def draw_bottom_strip(surface: pygame.Surface) -> None:
    """Draw a bold blue bottom strip with 'Free on itch.io' CTA."""
    strip_h = 44
    strip_y = H - strip_h
    pygame.draw.rect(surface, BLUE, (0, strip_y, W, strip_h))

    # Cuboid accent blocks on the left
    for i in range(4):
        draw_cuboid(surface, 10 + i * 18, strip_y + 10, 12, 24,
                    lighter(BLUE, 30), d=4)

    f = pygame.font.SysFont("couriernew", 16, bold=True)
    cta = f.render("FREE  ·  itch.io  ·  BROWSER + DOWNLOAD", True, TEXT_LIGHT)
    surface.blit(cta, (W // 2 - cta.get_width() // 2, strip_y + (strip_h - cta.get_height()) // 2))


def draw_corner_cuboids(surface: pygame.Surface) -> None:
    """Draw small decorative cuboid clusters in the top corners."""
    # Top-right cluster
    for i, (ox, oy, sz) in enumerate([(W-55,8,18),(W-34,14,12),(W-68,18,10)]):
        draw_cuboid(surface, ox, oy, sz, sz, BLUE, d=5)

    # Top-left cluster
    for i, (ox, oy, sz) in enumerate([(8,8,14),(24,16,10),(6,26,8)]):
        draw_cuboid(surface, ox, oy, sz, sz, lighter(BLUE, 20), d=4)


def main() -> None:
    """Generate and save the logo PNG."""
    pygame.init()

    # Offscreen surface — no window needed
    surface = pygame.Surface((W, H))

    # ── Render layers ──────────────────────────────────────────────────────────
    surface.fill(BG)
    draw_bg_cuboids(surface)
    draw_corner_cuboids(surface)
    draw_title(surface)
    draw_widget_frame(surface)
    draw_checked_checkbox(surface)
    draw_label(surface)
    draw_bottom_strip(surface)
    draw_scanlines(surface)

    # ── Save ──────────────────────────────────────────────────────────────────
    output = "captcharun_logo.png"
    pygame.image.save(surface, output)
    print(f"Saved → {output}  ({W}x{H}px)")

    pygame.quit()


if __name__ == "__main__":
    main()