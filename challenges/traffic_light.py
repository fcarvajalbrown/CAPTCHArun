"""
challenges/traffic_light.py — "Select all traffic lights" CAPTCHA challenge.

The player is shown a 3x3 grid of tiles. Some tiles contain a vector
traffic light icon, others contain a decoy icon (a street sign). The
player must select all tiles with traffic lights and press VERIFY.

Correct tiles are randomised on each instantiation and reset() call,
so the same challenge object can be safely reused across rounds.

Visual language:
    - Unselected tile: flat white rectangle with a vector icon
    - Selected tile:   raised cuboid (blue) with the same icon on top
    - Traffic light:   three stacked circles (red/yellow/green) in a rect
    - Decoy (sign):    diamond shape with an exclamation mark
"""

from __future__ import annotations
import pygame
import random
from challenges.base import CaptchaChallenge
from renderer.grid import TileGrid
from settings import COLOR, GRID_COLS, GRID_ROWS
from utils.color import RGBColor


# ── Vector icon drawers ───────────────────────────────────────────────────────

def _draw_traffic_light(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a vector traffic light icon centered inside a tile rect.

    Three vertically stacked circles (red, yellow, green) inside a
    dark rounded housing. Pure pygame.draw calls, no images.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 14
    housing_w = rect.w - pad * 2
    housing_h = rect.h - pad * 2
    hx = rect.x + pad
    hy = rect.y + pad

    # Housing background
    pygame.draw.rect(surface, (40, 40, 40), (hx, hy, housing_w, housing_h), border_radius=6)

    # Three lights stacked vertically
    light_r = housing_w // 2 - 4
    light_cx = hx + housing_w // 2
    section_h = housing_h // 3

    lights: list[tuple[int, RGBColor]] = [
        (0, (220,  50,  50)),   # red    — top
        (1, (220, 180,  50)),   # yellow — middle
        (2, ( 50, 200,  80)),   # green  — bottom
    ]
    for idx, color in lights:
        cy = hy + section_h * idx + section_h // 2
        pygame.draw.circle(surface, color, (light_cx, cy), light_r)


def _draw_decoy_sign(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a vector warning sign (diamond with exclamation) as a decoy icon.

    Players should NOT select these tiles.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 16
    cx = rect.x + rect.w // 2
    cy = rect.y + rect.h // 2
    half = rect.w // 2 - pad

    # Diamond shape
    diamond = [
        (cx,          cy - half),   # top
        (cx + half,   cy        ),  # right
        (cx,          cy + half),   # bottom
        (cx - half,   cy        ),  # left
    ]
    pygame.draw.polygon(surface, (220, 180, 50), diamond)
    pygame.draw.polygon(surface, (40, 40, 40), diamond, 2)

    # Exclamation mark
    font = pygame.font.Font(None, 29)
    mark = font.render("!", True, (40, 40, 40))
    surface.blit(mark, (cx - mark.get_width() // 2, cy - mark.get_height() // 2))


# ── Challenge class ───────────────────────────────────────────────────────────

class TrafficLightChallenge(CaptchaChallenge):
    """CAPTCHA challenge: select all tiles containing a traffic light.

    Attributes:
        difficulty:      "easy" — available from round 1.
        prompt:          Instruction shown in the header.
        correct_tiles:   Set of (col, row) tuples that contain traffic lights.
        grid:            TileGrid instance managing tile layout and selection.
    """

    difficulty = "easy"

    def __init__(self) -> None:
        """Initialise the challenge with a randomised tile layout."""
        super().__init__()
        self.prompt = "Select all traffic lights"
        self.correct_tiles: set[tuple[int, int]] = set()
        self.grid = TileGrid()
        self._randomise()

    def _randomise(self) -> None:
        """Randomly assign traffic light and decoy tiles.

        Guarantees at least 2 and at most 5 traffic light tiles so the
        challenge is neither trivially easy (1 tile) nor a process of
        elimination (all tiles). Resets grid selection state.
        """
        all_positions = [
            (col, row)
            for row in range(GRID_ROWS)
            for col in range(GRID_COLS)
        ]
        count = random.randint(2, 5)
        self.correct_tiles = set(random.sample(all_positions, count))

        # Build icon map: correct tiles get traffic light, rest get decoy
        icon_map: dict[tuple[int, int], callable] = {}
        for pos in all_positions:
            if pos in self.correct_tiles:
                icon_map[pos] = _draw_traffic_light
            else:
                icon_map[pos] = _draw_decoy_sign

        self.grid.icon_map = icon_map
        self.grid.reset()

    def render(self, surface: pygame.Surface) -> None:
        """Draw the tile grid with traffic light and decoy icons.

        Args:
            surface: Native 360x640 game surface.
        """
        self.grid.render(surface)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Toggle tile selection on left mouse click.

        Converts window mouse position to game coordinates via the event's
        pos attribute — note: pos is already in game space because game.py
        passes events after coordinate translation.

        Args:
            event: A pygame event. Only MOUSEBUTTONDOWN with button=1 is handled.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.grid.handle_click(*event.pos)

    def is_solved(self) -> bool:
        """Return True if the player's selection exactly matches correct_tiles.

        Requires an exact match — no missing tiles, no extra tiles selected.

        Returns:
            True if selected == correct_tiles, False otherwise.
        """
        return self.grid.selected == self.correct_tiles

    def reset(self) -> None:
        """Re-randomise the layout for reuse in a new round."""
        self._randomise()