"""
renderer/ui.py — Static UI chrome rendering for CAPTCHArun.

Draws all non-grid interface elements:
    - Header bar ("Verify you are human" + round/score)
    - Timer bar (shrinking cuboid bar below header)
    - Suspicion meter (strike indicators above verify button)
    - Verify button
    - Pass/fail flash overlay
    - Game over screen

All functions are stateless — they take explicit data arguments and draw
to the provided surface. No global state is read except constants from
settings.py.

Coordinate system: native 360x640 game space. Scaler handles the rest.
"""

import pygame
from settings import (
    SCREEN_W, SCREEN_H,
    HEADER_H, TIMER_BAR_H, VERIFY_BTN_H, SUSPICION_BAR_H, BOTTOM_PANEL_H,
    MAX_STRIKES,
    COLOR,
    FONT_FAMILY, FONT_SIZE_LG, FONT_SIZE_MD, FONT_SIZE_SM,
    CUBOID_DEPTH,
)
from renderer.cuboid import draw_cuboid, draw_flat_tile, draw_cuboid_bar
from utils.color import lerp_color, RGBColor


# ── Font cache ────────────────────────────────────────────────────────────────
# Fonts are loaded once and reused. pygame.font.SysFont falls back gracefully
# if "couriernew" is unavailable on the system.
_fonts: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    """Return a cached monospace font at the given size.

    Args:
        size: Point size.

    Returns:
        A pygame.font.Font instance.
    """
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(FONT_FAMILY, size)
    return _fonts[size]


# ── Header ────────────────────────────────────────────────────────────────────

def draw_header(
    surface: pygame.Surface,
    prompt: str,
    round_num: int,
    score: int,
) -> None:
    """Draw the top header bar with the CAPTCHA prompt and round/score info.

    The header mimics a real CAPTCHA widget header: flat gray background,
    left-aligned prompt text, right-aligned score indicator.

    Args:
        surface:   Native-resolution game surface.
        prompt:    Challenge instruction text, e.g. "Select all traffic lights".
        round_num: Current round number (1-based) shown in the top-right.
        score:     Current player score shown below the round number.
    """
    # Background
    draw_flat_tile(surface, 0, 0, SCREEN_W, HEADER_H, COLOR["chrome"])

    # Brand label — top left
    brand = _font(FONT_SIZE_SM).render("reCAPTCHA", True, COLOR["tile"])
    surface.blit(brand, (12, 10))

    # Prompt — main instruction, left-aligned, wraps if long
    prompt_font = _font(FONT_SIZE_MD)
    prompt_surf = prompt_font.render(prompt, True, COLOR["text_light"])
    surface.blit(prompt_surf, (12, 32))

    # Round + score — top right
    meta_font = _font(FONT_SIZE_SM)
    round_surf = meta_font.render(f"Round {round_num}", True, COLOR["tile"])
    score_surf = meta_font.render(f"Score {score}", True, COLOR["tile"])
    surface.blit(round_surf, (SCREEN_W - round_surf.get_width() - 12, 10))
    surface.blit(score_surf, (SCREEN_W - score_surf.get_width() - 12, 28))


# ── Timer bar ─────────────────────────────────────────────────────────────────

def draw_timer_bar(surface: pygame.Surface, fill: float) -> None:
    """Draw the timer progress bar immediately below the header.

    The bar depletes left-to-right as time runs out. Color is always
    COLOR["timer"] (red) to create urgency.

    Args:
        surface: Native-resolution game surface.
        fill:    Remaining time ratio in [0.0, 1.0]. 1.0 = full time left.
    """
    y = HEADER_H
    draw_cuboid_bar(
        surface,
        x=0, y=y,
        total_w=SCREEN_W,
        h=TIMER_BAR_H,
        fill=fill,
        fill_color=COLOR["timer"],
        bg_color=COLOR["tile_border"],
        d=CUBOID_DEPTH // 2,
    )


# ── Suspicion meter ───────────────────────────────────────────────────────────

def draw_suspicion_meter(surface: pygame.Surface, strikes: int) -> None:
    """Draw strike indicators as cuboid blocks above the verify button.

    Each strike is represented by a small cuboid. Active strikes are red;
    remaining strikes are shown as empty flat tiles.

    Args:
        surface: Native-resolution game surface.
        strikes: Number of strikes the player has accumulated (0–MAX_STRIKES).
    """
    block_w = 24
    block_h = SUSPICION_BAR_H
    block_gap = 6
    total_w = MAX_STRIKES * block_w + (MAX_STRIKES - 1) * block_gap

    y = SCREEN_H - BOTTOM_PANEL_H
    x_start = (SCREEN_W - total_w) // 2

    label = _font(FONT_SIZE_SM).render("SUSPICION", True, COLOR["chrome"])
    surface.blit(label, ((SCREEN_W - label.get_width()) // 2, y - 18))

    for i in range(MAX_STRIKES):
        bx = x_start + i * (block_w + block_gap)
        if i < strikes:
            draw_cuboid(surface, bx, y, block_w, block_h, COLOR["fail"])
        else:
            draw_flat_tile(surface, bx, y, block_w, block_h, COLOR["tile"], COLOR["tile_border"])


# ── Verify button ─────────────────────────────────────────────────────────────

def draw_verify_button(surface: pygame.Surface, hovered: bool = False) -> pygame.Rect:
    """Draw the VERIFY button and return its rect for hit detection.

    The button is a cuboid when hovered, flat when idle — matching the
    tile visual language of the rest of the game.

    Args:
        surface: Native-resolution game surface.
        hovered: True if the mouse cursor is over the button.

    Returns:
        pygame.Rect of the button in native game coordinates.
    """
    margin = 24
    btn_w = SCREEN_W - margin * 2
    btn_h = VERIFY_BTN_H
    btn_x = margin
    btn_y = SCREEN_H - btn_h - 12

    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    if hovered:
        draw_cuboid(surface, btn_x, btn_y, btn_w, btn_h, COLOR["highlight"])
        text_color = COLOR["text_light"]
    else:
        draw_flat_tile(surface, btn_x, btn_y, btn_w, btn_h, COLOR["tile"], COLOR["tile_border"])
        text_color = COLOR["text"]

    label = _font(FONT_SIZE_LG).render("VERIFY", True, text_color)
    lx = btn_x + (btn_w - label.get_width()) // 2
    ly = btn_y + (btn_h - label.get_height()) // 2
    surface.blit(label, (lx, ly))

    return btn_rect


# ── Pass / fail flash overlay ─────────────────────────────────────────────────

def draw_flash(surface: pygame.Surface, flash_color: RGBColor, alpha: float) -> None:
    """Draw a full-screen color tint overlay for pass/fail feedback.

    Uses lerp_color to blend from flash_color → background as alpha fades.
    The caller controls alpha over time (typically 0.0→1.0 over ~0.4s).

    Args:
        surface:     Native-resolution game surface.
        flash_color: The tint color (COLOR["pass"] or COLOR["fail"]).
        alpha:       Blend factor in [0.0, 1.0]. 1.0 = full tint, 0.0 = invisible.
    """
    if alpha <= 0.0:
        return
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    a = int(alpha * 120)  # max 120/255 opacity — tint not blackout
    overlay.fill((*flash_color, a))
    surface.blit(overlay, (0, 0))


# ── Game over screen ──────────────────────────────────────────────────────────

def draw_game_over(surface: pygame.Surface, score: int, round_num: int) -> pygame.Rect:
    """Draw the game over screen and return the restart button rect.

    Full-screen overlay with final score and a RETRY button styled as a cuboid.

    Args:
        surface:   Native-resolution game surface.
        score:     Final score to display.
        round_num: Round reached before game over.

    Returns:
        pygame.Rect of the RETRY button for hit detection in game coordinates.
    """
    # Dim background
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((33, 33, 33, 200))
    surface.blit(overlay, (0, 0))

    cx = SCREEN_W // 2
    f_lg = _font(FONT_SIZE_LG)
    f_md = _font(FONT_SIZE_MD)
    f_sm = _font(FONT_SIZE_SM)

    # "VERIFICATION FAILED"
    title = f_lg.render("VERIFICATION FAILED", True, COLOR["fail"])
    surface.blit(title, (cx - title.get_width() // 2, 180))

    # Score and round
    sc = f_md.render(f"Score: {score}", True, COLOR["tile"])
    rd = f_sm.render(f"You reached round {round_num}", True, COLOR["chrome"])
    surface.blit(sc, (cx - sc.get_width() // 2, 230))
    surface.blit(rd, (cx - rd.get_width() // 2, 258))

    # RETRY button
    btn_w, btn_h = 180, VERIFY_BTN_H
    btn_x = cx - btn_w // 2
    btn_y = 320
    draw_cuboid(surface, btn_x, btn_y, btn_w, btn_h, COLOR["highlight"])
    label = f_lg.render("TRY AGAIN", True, COLOR["text_light"])
    surface.blit(label, (btn_x + (btn_w - label.get_width()) // 2,
                         btn_y + (btn_h - label.get_height()) // 2))

    return pygame.Rect(btn_x, btn_y, btn_w, btn_h)


# ── Level up screen ───────────────────────────────────────────────────────────

def draw_level_up(surface: pygame.Surface, security_level: int, alpha: float) -> None:
    """Draw the security level-up congratulations screen.

    Full-screen overlay that auto-dismisses — no button needed. Fades in
    then out, driven by alpha from game.py's level-up timer.

    Visual: dark overlay, large "SECURITY LEVEL X" in cuboid style,
    congratulations subtext, animated cuboid grid decorations.

    Args:
        surface:        Native 360x640 game surface.
        security_level: The new security level just reached.
        alpha:          Fade factor in [0.0, 1.0]. game.py drives this
                        from 0→1→0 over the display duration.
    """
    if alpha <= 0.0:
        return

    cx = SCREEN_W // 2

    # Dark overlay — deepens with alpha
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((20, 20, 20, int(alpha * 220)))
    surface.blit(overlay, (0, 0))

    # Decorative cuboid row — three small cuboids above the text
    from renderer.cuboid import draw_cuboid
    cub_size = 20
    cub_gap  = 12
    total_cub_w = 3 * cub_size + 2 * cub_gap
    cub_y = 180
    cub_x = cx - total_cub_w // 2
    for i in range(3):
        draw_cuboid(surface, cub_x + i * (cub_size + cub_gap), cub_y,
                    cub_size, cub_size, COLOR["highlight"])

    # "SECURITY CLEARANCE" label
    f_sm = _font(FONT_SIZE_SM)
    label = f_sm.render("SECURITY CLEARANCE", True, COLOR["chrome"])
    surface.blit(label, (cx - label.get_width() // 2, 220))

    # "LEVEL X" — big, bold, highlighted
    f_level = pygame.font.SysFont(FONT_FAMILY, 42, bold=True)
    level_text = f_level.render(f"LEVEL  {security_level}", True, COLOR["highlight"])
    surface.blit(level_text, (cx - level_text.get_width() // 2, 245))

    # Underline
    ul_y = 245 + level_text.get_height() + 4
    pygame.draw.rect(surface, COLOR["highlight"], (cx - 80, ul_y, 160, 3))

    # Congrats subtext
    f_md = _font(FONT_SIZE_MD)
    congrats = f_md.render("You are cleared for deeper verification.", True, COLOR["tile"])
    surface.blit(congrats, (cx - congrats.get_width() // 2, ul_y + 20))

    # "Are you still human?" — the game's running joke
    f_sm2 = _font(FONT_SIZE_SM)
    joke = f_sm2.render("...are you sure you're not a robot?", True, COLOR["chrome"])
    surface.blit(joke, (cx - joke.get_width() // 2, ul_y + 48))