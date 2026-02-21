"""
challenges/checkbox.py — "Click the checkbox" CAPTCHA challenge.

The simplest and most meta challenge. A single large checkbox is shown
center-screen. The player must click it. The twist: the checkbox moves
away from the cursor as it approaches, snapping to a random new position.

After the player successfully clicks it (or it escapes MAX_DODGES times
and the player is forced to catch it), pressing VERIFY evaluates the result.

This challenge intentionally has no grid — it overrides render() and
handle_event() directly without using TileGrid.

Difficulty: easy — but psychologically the most frustrating.
"""

from __future__ import annotations
import pygame
import random
from challenges.base import CaptchaChallenge
from settings import SCREEN_W, SCREEN_H, HEADER_H, TIMER_BAR_H, BOTTOM_PANEL_H, COLOR
from renderer.cuboid import draw_cuboid, draw_flat_tile


# ── Constants ─────────────────────────────────────────────────────────────────
BOX_SIZE    = 48          # checkbox width and height in px
FLEE_RADIUS = 90          # px — cursor within this distance triggers a dodge
MAX_DODGES  = 4           # after this many dodges, checkbox stops fleeing
CUBOID_D    = 8           # isometric depth for the checked cuboid


# ── Helper ────────────────────────────────────────────────────────────────────

def _random_position() -> tuple[int, int]:
    """Return a random (x, y) for the checkbox top-left, within safe bounds.

    Keeps the checkbox inside the playable vertical region (below header/timer,
    above bottom panel) and horizontally padded from screen edges.

    Returns:
        (x, y) tuple in native game coordinates.
    """
    usable_top = HEADER_H + TIMER_BAR_H + 20
    usable_bot = SCREEN_H - BOTTOM_PANEL_H - BOX_SIZE - 20
    usable_left = 24
    usable_right = SCREEN_W - BOX_SIZE - 24
    return (
        random.randint(usable_left, usable_right),
        random.randint(usable_top, usable_bot),
    )


# ── Challenge class ───────────────────────────────────────────────────────────

class CheckboxChallenge(CaptchaChallenge):
    """CAPTCHA challenge: click the checkbox before it runs away.

    The checkbox dodges the cursor up to MAX_DODGES times. After that it
    freezes and the player can click it. is_solved() returns True only if
    the player has clicked it at least once.

    Attributes:
        difficulty: "easy" — psychologically hard, mechanically simple.
        prompt:     Instruction shown in the header.
        box_x:      Current X of the checkbox top-left in game coords.
        box_y:      Current Y of the checkbox top-left in game coords.
        checked:    True if the player has successfully clicked the checkbox.
        dodges:     Number of times the checkbox has fled the cursor.
    """

    difficulty = "easy"

    def __init__(self) -> None:
        """Initialise with the checkbox at a random starting position."""
        super().__init__()
        self.prompt = "Click the checkbox"
        self.checked: bool = False
        self.dodges: int = 0
        self.box_x, self.box_y = _random_position()

    def _box_rect(self) -> pygame.Rect:
        """Return the current bounding rect of the checkbox.

        Returns:
            pygame.Rect in native game coordinates.
        """
        return pygame.Rect(self.box_x, self.box_y, BOX_SIZE, BOX_SIZE)

    def _try_flee(self, cursor_x: int, cursor_y: int) -> None:
        """Move the checkbox to a new random position if the cursor is close.

        Only flees if dodges < MAX_DODGES and the checkbox is not yet checked.
        Ensures the new position is different from the current one.

        Args:
            cursor_x: Cursor X in native game coordinates.
            cursor_y: Cursor Y in native game coordinates.
        """
        if self.checked or self.dodges >= MAX_DODGES:
            return

        cx = self.box_x + BOX_SIZE // 2
        cy = self.box_y + BOX_SIZE // 2
        dist_sq = (cursor_x - cx) ** 2 + (cursor_y - cy) ** 2

        if dist_sq < FLEE_RADIUS ** 2:
            new_x, new_y = _random_position()
            # Guarantee a visually distinct new position
            while abs(new_x - self.box_x) < BOX_SIZE * 2 and abs(new_y - self.box_y) < BOX_SIZE * 2:
                new_x, new_y = _random_position()
            self.box_x, self.box_y = new_x, new_y
            self.dodges += 1

    def render(self, surface: pygame.Surface) -> None:
        """Draw the checkbox — flat if unchecked, cuboid with checkmark if checked.

        Also renders a small dodge counter below the checkbox so the player
        knows how many escapes remain.

        Args:
            surface: Native 360x640 game surface.
        """
        rect = self._box_rect()

        if self.checked:
            # Raised cuboid — visually "pressed in"
            draw_cuboid(surface, rect.x, rect.y, rect.w, rect.h,
                        COLOR["highlight"], d=CUBOID_D,
                        border_color=COLOR["chrome"])
            # Checkmark — two lines forming a tick
            tick_color = COLOR["text_light"]
            p1 = (rect.x + 10, rect.y + rect.h // 2)
            p2 = (rect.x + rect.w // 2 - 2, rect.y + rect.h - 12)
            p3 = (rect.x + rect.w - 10, rect.y + 12)
            pygame.draw.line(surface, tick_color, p1, p2, 3)
            pygame.draw.line(surface, tick_color, p2, p3, 3)
        else:
            # Flat tile — unchecked
            draw_flat_tile(surface, rect.x, rect.y, rect.w, rect.h,
                           COLOR["tile"], COLOR["tile_border"])

        # Dodge counter hint
        remaining = max(0, MAX_DODGES - self.dodges)
        if remaining > 0 and not self.checked:
            font = pygame.font.SysFont("couriernew", 11)
            hint = font.render(f"escapes left: {remaining}", True, COLOR["chrome"])
            surface.blit(hint, (rect.x + rect.w // 2 - hint.get_width() // 2,
                                rect.y + rect.h + 8))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse movement (flee) and click (check).

        MOUSEMOTION triggers flee logic. MOUSEBUTTONDOWN registers a click
        if it lands on the checkbox rect.

        Args:
            event: A pygame event.
        """
        if event.type == pygame.MOUSEMOTION:
            self._try_flee(*event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._box_rect().collidepoint(event.pos):
                self.checked = True

    def is_solved(self) -> bool:
        """Return True if the player has clicked the checkbox.

        Returns:
            True if checked, False otherwise.
        """
        return self.checked

    def reset(self) -> None:
        """Reset checkbox state and reposition for a new round."""
        self.checked = False
        self.dodges = 0
        self.box_x, self.box_y = _random_position()