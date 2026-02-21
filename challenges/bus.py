"""
challenges/bus.py — "Select all buses" CAPTCHA challenge.

Structurally identical to traffic_light.py — a 3x3 grid where the player
must identify and select all tiles containing a bus icon. Decoy tiles show
a car icon instead.

Visual language:
    - Bus:  wide rectangular body, two wheels, windows row, destination sign
    - Car:  lower profile body, two wheels, windshield trapezoid
    - Both drawn entirely with pygame.draw primitives
"""

from __future__ import annotations
import pygame
import random
from challenges.base import CaptchaChallenge
from renderer.grid import TileGrid
from settings import GRID_COLS, GRID_ROWS


# ── Vector icon drawers ───────────────────────────────────────────────────────

def _draw_bus(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a vector bus icon centered inside a tile rect.

    A tall rectangular body with a destination sign on top, a row of
    windows, and two circular wheels at the bottom.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 12
    bx = rect.x + pad
    by = rect.y + pad + 8
    bw = rect.w - pad * 2
    bh = rect.h - pad * 2 - 8

    body_color   = (52, 120, 210)
    wheel_color  = (40, 40, 40)
    window_color = (180, 220, 255)
    sign_color   = (240, 200, 60)

    # Destination sign above the body
    sign_h = 10
    pygame.draw.rect(surface, sign_color, (bx + 4, by - sign_h - 2, bw - 8, sign_h), border_radius=2)

    # Main body
    pygame.draw.rect(surface, body_color, (bx, by, bw, bh), border_radius=4)

    # Windows row — three small rectangles
    win_w = (bw - 16) // 3 - 4
    win_h = bh // 3
    win_y = by + 6
    for i in range(3):
        wx = bx + 8 + i * (win_w + 4)
        pygame.draw.rect(surface, window_color, (wx, win_y, win_w, win_h), border_radius=2)

    # Wheels — two circles at the bottom
    wheel_r = 7
    wheel_y = by + bh - 2
    pygame.draw.circle(surface, wheel_color, (bx + 14, wheel_y), wheel_r)
    pygame.draw.circle(surface, wheel_color, (bx + bw - 14, wheel_y), wheel_r)


def _draw_car(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a vector car icon as a decoy inside a tile rect.

    A lower-profile body with a trapezoidal cabin on top and two wheels.
    Visually distinct from the bus — smaller, rounder, no destination sign.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 14
    bx = rect.x + pad
    by = rect.y + rect.h // 2
    bw = rect.w - pad * 2
    bh = rect.h // 3

    body_color   = (180, 60, 60)
    wheel_color  = (40, 40, 40)
    cabin_color  = (210, 120, 120)
    window_color = (180, 220, 255)

    # Main body
    pygame.draw.rect(surface, body_color, (bx, by, bw, bh), border_radius=5)

    # Cabin — trapezoid sitting on top of the body
    cabin_inset = 10
    cabin_h = bh - 4
    cabin = [
        (bx + cabin_inset,      by              ),   # top-left
        (bx + bw - cabin_inset, by              ),   # top-right
        (bx + bw - 4,           by - cabin_h    ),   # bottom-right
        (bx + 4,                by - cabin_h    ),   # bottom-left
    ]
    pygame.draw.polygon(surface, cabin_color, cabin)

    # Windshield window inside cabin
    win_inset = 4
    window = [
        (bx + cabin_inset + win_inset,      by - 2          ),
        (bx + bw - cabin_inset - win_inset, by - 2          ),
        (bx + bw - 8,                       by - cabin_h + 4),
        (bx + 8,                            by - cabin_h + 4),
    ]
    pygame.draw.polygon(surface, window_color, window)

    # Wheels
    wheel_r = 6
    wheel_y = by + bh
    pygame.draw.circle(surface, wheel_color, (bx + 14, wheel_y), wheel_r)
    pygame.draw.circle(surface, wheel_color, (bx + bw - 14, wheel_y), wheel_r)


# ── Challenge class ───────────────────────────────────────────────────────────

class BusChallenge(CaptchaChallenge):
    """CAPTCHA challenge: select all tiles containing a bus.

    Attributes:
        difficulty:    "easy" — available from round 1.
        prompt:        Instruction shown in the header.
        correct_tiles: Set of (col, row) tuples containing bus icons.
        grid:          TileGrid instance managing layout and selection.
    """

    difficulty = "easy"

    def __init__(self) -> None:
        """Initialise the challenge with a randomised tile layout."""
        super().__init__()
        self.prompt = "Select all buses"
        self.correct_tiles: set[tuple[int, int]] = set()
        self.grid = TileGrid()
        self._randomise()

    def _randomise(self) -> None:
        """Randomly assign bus and car tiles.

        Guarantees 2–5 bus tiles so the challenge is neither trivial
        nor a pure process of elimination. Resets grid selection state.
        """
        all_positions = [
            (col, row)
            for row in range(GRID_ROWS)
            for col in range(GRID_COLS)
        ]
        count = random.randint(2, 5)
        self.correct_tiles = set(random.sample(all_positions, count))

        icon_map: dict[tuple[int, int], callable] = {}
        for pos in all_positions:
            if pos in self.correct_tiles:
                icon_map[pos] = _draw_bus
            else:
                icon_map[pos] = _draw_car

        self.grid.icon_map = icon_map
        self.grid.reset()

    def render(self, surface: pygame.Surface) -> None:
        """Draw the tile grid with bus and car icons.

        Args:
            surface: Native 360x640 game surface.
        """
        self.grid.render(surface)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Toggle tile selection on left mouse click.

        Args:
            event: A pygame event. Only MOUSEBUTTONDOWN with button=1 is handled.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.grid.handle_click(*event.pos)

    def is_solved(self) -> bool:
        """Return True if selected tiles exactly match the bus tiles.

        Returns:
            True if selection == correct_tiles, False otherwise.
        """
        return self.grid.selected == self.correct_tiles

    def reset(self) -> None:
        """Re-randomise the layout for reuse in a new round."""
        self._randomise()