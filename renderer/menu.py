"""
renderer/menu.py — Main menu screen for CAPTCHArun.

Pure vector graphics. No sprites, no images. Everything drawn with
pygame.draw primitives and the cuboid renderer.

Design intent:
    The menu IS a CAPTCHA. A giant checkbox dominates the screen.
    Below it: "I am not a robot." The player clicks the checkbox to start.
    This is both the tutorial and the hook — players immediately understand
    the game without reading a word of instructions.

    Visual language:
        - Oversized reCAPTCHA widget filling most of the screen
        - Animated floating cuboids in the background (parallax depth)
        - Pulsing checkbox that breathes to invite interaction
        - Corporate sterile palette broken by the glowing blue highlight
        - Scanline overlay for texture without images

The menu stores animation state in module-level variables so it
persists across render calls without needing an object. game.py
calls draw_menu() every frame.
"""

import pygame
import math
import random
from settings import (
    SCREEN_W, SCREEN_H,
    COLOR, CUBOID_DEPTH,
    FONT_FAMILY, FONT_SIZE_LG, FONT_SIZE_MD, FONT_SIZE_SM,
)
from renderer.cuboid import draw_cuboid, draw_flat_tile
from utils.color import lighter, darker

# ── Animation state (module-level, initialised once) ─────────────────────────
_time:        float = 0.0          # accumulated seconds since menu first rendered
_initialized: bool  = False

# Floating background cuboids — each is (x, y, size, speed, phase_offset)
_bg_cuboids: list[tuple[float, float, int, float, float]] = []
_BG_CUBOID_COUNT = 10

# Checkbox pulse animation
_CHECKBOX_SIZE  = 100              # px — giant checkbox
_CHECKBOX_X     = (SCREEN_W - _CHECKBOX_SIZE) // 2
_CHECKBOX_Y     = 210

# Hover state
_checkbox_hovered: bool = False


def _init_bg_cuboids() -> None:
    """Generate random floating background cuboid data.

    Called once on first render. Each cuboid has a fixed (x, y) start,
    a size, a vertical drift speed, and a phase offset for the sine wave.
    """
    global _bg_cuboids
    random.seed(42)   # fixed seed = deterministic layout, looks intentional
    _bg_cuboids = [
        (
            random.randint(10, SCREEN_W - 40),   # x
            random.randint(-20, SCREEN_H),        # y start
            random.randint(12, 32),               # size
            random.uniform(8.0, 22.0),            # drift speed (px/s)
            random.uniform(0.0, math.tau),        # sine phase offset
        )
        for _ in range(_BG_CUBOID_COUNT)
    ]
    random.seed()  # restore true randomness for gameplay


# ── Sub-renderers ─────────────────────────────────────────────────────────────

def _draw_background(surface: pygame.Surface) -> None:
    """Draw the background: solid fill + floating translucent cuboids.

    Cuboids drift upward and oscillate horizontally. They wrap at the top
    and reappear at the bottom, creating a continuous parallax effect.

    Args:
        surface: Native game surface.
    """
    surface.fill(COLOR["background"])

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

    for i, (ox, oy, size, speed, phase) in enumerate(_bg_cuboids):
        # Vertical drift — wraps at top
        y = (oy - _time * speed) % (SCREEN_H + 60) - 30
        # Horizontal sine sway
        x = ox + math.sin(_time * 0.4 + phase) * 12

        alpha = 35 + int(20 * math.sin(_time * 0.6 + phase))
        face_color = (*COLOR["cuboid_front"], alpha)
        top_color  = (*lighter(COLOR["cuboid_front"], 30), alpha)
        right_color = (*darker(COLOR["cuboid_front"], 30), alpha)

        d = CUBOID_DEPTH // 2

        front = [(x, y), (x+size, y), (x+size, y+size), (x, y+size)]
        top   = [(x, y), (x+size, y), (x+size+d, y-d), (x+d, y-d)]
        right = [(x+size, y), (x+size+d, y-d), (x+size+d, y+size-d), (x+size, y+size)]

        pygame.draw.polygon(overlay, top_color,   top)
        pygame.draw.polygon(overlay, right_color, right)
        pygame.draw.polygon(overlay, face_color,  front)

    surface.blit(overlay, (0, 0))


def _draw_scanlines(surface: pygame.Surface) -> None:
    """Draw subtle horizontal scanlines over the whole screen for texture.

    Adds visual noise and depth without any image assets. Every 3rd row
    gets a very low-alpha dark line.

    Args:
        surface: Native game surface.
    """
    scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for y in range(0, SCREEN_H, 3):
        pygame.draw.line(scan, (0, 0, 0, 18), (0, y), (SCREEN_W, y))
    surface.blit(scan, (0, 0))


def _draw_widget_frame(surface: pygame.Surface) -> None:
    """Draw the outer reCAPTCHA widget border and header.

    A large rounded rect styled like a real CAPTCHA widget chrome —
    gray border, white interior, reCAPTCHA branding at the bottom right.

    Args:
        surface: Native game surface.
    """
    margin = 24
    wx = margin
    wy = 150
    ww = SCREEN_W - margin * 2
    wh = 280

    # Widget shadow
    shadow = pygame.Surface((ww + 6, wh + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 40), (0, 0, ww + 6, wh + 6), border_radius=8)
    surface.blit(shadow, (wx + 2, wy + 2))

    # Widget background
    pygame.draw.rect(surface, COLOR["tile"], (wx, wy, ww, wh), border_radius=6)
    pygame.draw.rect(surface, COLOR["tile_border"], (wx, wy, ww, wh), 2, border_radius=6)

    # Bottom branding bar
    bar_h = 36
    bar_y = wy + wh - bar_h
    pygame.draw.rect(surface, COLOR["chrome"], (wx, bar_y, ww, bar_h),
                     border_radius=6)  # rounded bottom only, close enough

    f_sm = pygame.font.Font(None, int(FONT_SIZE_SM * 1.35))
    brand = f_sm.render("reCAPTCHA", True, COLOR["tile"])
    privacy = f_sm.render("Privacy  -  Terms", True, (180, 180, 180))
    surface.blit(brand, (wx + ww - brand.get_width() - 10, bar_y + (bar_h - brand.get_height()) // 2))
    surface.blit(privacy, (wx + 10, bar_y + (bar_h - privacy.get_height()) // 2))


def _draw_giant_checkbox(surface: pygame.Surface, hovered: bool) -> pygame.Rect:
    """Draw the large interactive checkbox — the game's start button.

    Pulses gently when idle. Glows blue when hovered. The checkbox is a
    cuboid when hovered (inviting a click) and flat when idle.

    Args:
        surface: Native game surface.
        hovered: True if the mouse is currently over the checkbox.

    Returns:
        pygame.Rect of the checkbox for hit detection.
    """
    pulse = math.sin(_time * 2.2) * 0.12 + 0.88   # 0.76 → 1.0 oscillation
    size  = int(_CHECKBOX_SIZE * pulse) if not hovered else _CHECKBOX_SIZE
    cx    = SCREEN_W // 2
    cy    = _CHECKBOX_Y + _CHECKBOX_SIZE // 2
    x     = cx - size // 2
    y     = cy - size // 2

    if hovered:
        draw_cuboid(surface, x, y, size, size, COLOR["highlight"],
                    d=CUBOID_DEPTH, border_color=COLOR["chrome"])
        # Checkmark
        p1 = (x + size // 5,       y + size // 2)
        p2 = (x + size * 2 // 5,   y + size * 3 // 4)
        p3 = (x + size * 4 // 5,   y + size // 4)
        pygame.draw.line(surface, COLOR["text_light"], p1, p2, 5)
        pygame.draw.line(surface, COLOR["text_light"], p2, p3, 5)
    else:
        draw_flat_tile(surface, x, y, size, size,
                       COLOR["tile"], COLOR["tile_border"])
        # Inner square hint — suggests interactivity
        inner = 8
        pygame.draw.rect(surface, COLOR["tile_border"],
                         (x + inner, y + inner, size - inner*2, size - inner*2), 2)

    return pygame.Rect(_CHECKBOX_X, _CHECKBOX_Y, _CHECKBOX_SIZE, _CHECKBOX_SIZE)


def _draw_label_and_instructions(surface: pygame.Surface) -> None:
    """Draw 'I am not a robot' label and instructional subtext.

    Args:
        surface: Native game surface.
    """
    f_lg = pygame.font.Font(None, int(int(FONT_SIZE_LG * 1.35 * 1.35)))
    f_md = pygame.font.Font(None, int(FONT_SIZE_MD * 1.35))
    f_sm = pygame.font.Font(None, int(FONT_SIZE_SM * 1.35))

    label = f_lg.render("I am not a robot.", True, COLOR["text"])
    cx = SCREEN_W // 2
    label_y = _CHECKBOX_Y + _CHECKBOX_SIZE // 2 - label.get_height() // 2
    surface.blit(label, (cx - label.get_width() // 2 + _CHECKBOX_SIZE // 2 + 12, label_y))

    sub = f_sm.render("(are you sure?)", True, COLOR["chrome"])
    surface.blit(sub, (cx - sub.get_width() // 2 + _CHECKBOX_SIZE // 2 + 12,
                       label_y + label.get_height() + 4))


def _draw_title(surface: pygame.Surface) -> None:
    """Draw the game title and tagline above the widget.

    Args:
        surface: Native game surface.
    """
    f_title = pygame.font.Font(None, int(int(28 * 1.35 * 1.35)))
    f_tag   = pygame.font.Font(None, int(FONT_SIZE_SM * 1.35))

    cx = SCREEN_W // 2

    title = f_title.render("CAPTCHArun", True, COLOR["text"])
    surface.blit(title, (cx - title.get_width() // 2, 72))

    # Blinking tagline
    if int(_time * 1.5) % 2 == 0:
        tag = f_tag.render("you are not a robot. prove it. forever.", True, COLOR["chrome"])
        surface.blit(tag, (cx - tag.get_width() // 2, 110))


def _draw_hint(surface: pygame.Surface) -> None:
    """Draw 'Click the checkbox to begin' hint below the widget.

    Fades in after 1 second so it doesn't overwhelm on first load.

    Args:
        surface: Native game surface.
    """
    if _time < 1.0:
        return

    alpha = min(255, int((_time - 1.0) * 300))
    f = pygame.font.Font(None, int(FONT_SIZE_SM * 1.35))
    hint = f.render("click the checkbox to begin", True, COLOR["chrome"])

    surf = pygame.Surface((hint.get_width(), hint.get_height()), pygame.SRCALPHA)
    surf.blit(hint, (0, 0))
    surf.set_alpha(alpha)
    cx = SCREEN_W // 2
    surface.blit(surf, (cx - surf.get_width() // 2, 460))


# ── Public entry point ────────────────────────────────────────────────────────

def draw_menu(surface: pygame.Surface, dt: float = 1/60) -> pygame.Rect:
    """Draw the full main menu and return the start button rect.

    Called every frame by game.py._render_menu(). Advances internal
    animation time by dt seconds.

    Args:
        surface: Native 360x640 game surface.
        dt:      Delta time in seconds. Defaults to 1/60 if not provided.
                 game.py should pass the real dt for smooth animation.

    Returns:
        pygame.Rect of the checkbox (start button) in game coordinates.
    """
    global _time, _initialized, _checkbox_hovered

    if not _initialized:
        _init_bg_cuboids()
        _initialized = True

    _time += dt

    # Mouse hover check
    mouse_pos = pygame.mouse.get_pos()   # raw — game.py hasn't translated yet
    # Note: game.py translates event.pos but not mouse.get_pos().
    # Menu self-checks hover since it owns the checkbox rect.
    checkbox_rect = pygame.Rect(_CHECKBOX_X, _CHECKBOX_Y, _CHECKBOX_SIZE, _CHECKBOX_SIZE)

    _draw_background(surface)
    _draw_scanlines(surface)
    _draw_title(surface)
    _draw_widget_frame(surface)

    hovered = checkbox_rect.collidepoint(mouse_pos)
    btn_rect = _draw_giant_checkbox(surface, hovered)
    _draw_label_and_instructions(surface)
    _draw_hint(surface)

    return btn_rect