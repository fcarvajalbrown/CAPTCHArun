"""
challenges/crosswalk.py — "Click the crosswalk path" CAPTCHA challenge.

The player is shown a 3x3 grid. A subset of tiles forms a connected path
from one edge of the grid to another — the crosswalk. The player must
select exactly those tiles.

Path generation uses a simple random walk from a random left-column tile
to a random right-column tile, moving only right or up/down by one step.
This guarantees the path is always solvable and visually clear.

Decoy tiles show a road marking (dashed line) to blend in. Path tiles show
a crosswalk stripe pattern (horizontal white bars on dark asphalt).

Difficulty: medium — unlocks at round 5.
"""

from __future__ import annotations
import pygame
import random
from challenges.base import CaptchaChallenge
from renderer.grid import TileGrid
from settings import GRID_COLS, GRID_ROWS, COLOR


# ── Vector icon drawers ───────────────────────────────────────────────────────

def _draw_crosswalk_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a crosswalk stripe pattern inside a tile rect.

    Horizontal white bars on a dark asphalt background — the classic
    zebra crossing look, rendered with pure rects.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 8
    tx = rect.x + pad
    ty = rect.y + pad
    tw = rect.w - pad * 2
    th = rect.h - pad * 2

    # Asphalt background
    pygame.draw.rect(surface, (60, 60, 60), (tx, ty, tw, th), border_radius=3)

    # White horizontal stripes
    stripe_count = 4
    stripe_h = th // (stripe_count * 2)
    gap_h = stripe_h
    for i in range(stripe_count):
        sy = ty + i * (stripe_h + gap_h)
        pygame.draw.rect(surface, (240, 240, 240), (tx + 2, sy, tw - 4, stripe_h))


def _draw_road_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a plain road tile with a dashed centre line as a decoy.

    Args:
        surface: Game surface to draw onto.
        rect:    Bounding rect of the tile in native game coordinates.
    """
    pad = 8
    tx = rect.x + pad
    ty = rect.y + pad
    tw = rect.w - pad * 2
    th = rect.h - pad * 2

    # Asphalt background
    pygame.draw.rect(surface, (80, 80, 80), (tx, ty, tw, th), border_radius=3)

    # Dashed centre line — vertical dashes
    cx = tx + tw // 2
    dash_h = 8
    gap_h = 6
    y = ty + 4
    while y + dash_h < ty + th:
        pygame.draw.rect(surface, (220, 200, 60), (cx - 2, y, 4, dash_h))
        y += dash_h + gap_h


# ── Path generation ───────────────────────────────────────────────────────────

def _generate_path() -> set[tuple[int, int]]:
    """Generate a connected crosswalk path from the left to the right column.

    Uses a random walk that starts at a random row on col=0 and ends at
    col=GRID_COLS-1. At each step it moves right, or randomly up/down
    (if within bounds), biased toward moving right to keep paths short.

    Returns:
        Set of (col, row) tuples forming the path.
    """
    path: list[tuple[int, int]] = []
    col = 0
    row = random.randint(0, GRID_ROWS - 1)
    path.append((col, row))

    while col < GRID_COLS - 1:
        # Bias: 70% chance to move right, 30% chance to move up/down
        move_right = random.random() < 0.7

        if move_right:
            col += 1
        else:
            # Move up or down if possible, else force right
            direction = random.choice([-1, 1])
            new_row = row + direction
            if 0 <= new_row < GRID_ROWS:
                row = new_row
            else:
                col += 1  # can't go out of bounds, move right instead

        if (col, row) not in path:
            path.append((col, row))

    return set(path)


# ── Challenge class ───────────────────────────────────────────────────────────

class CrosswalkChallenge(CaptchaChallenge):
    """CAPTCHA challenge: select all tiles forming the crosswalk path.

    A connected path of crosswalk tiles runs left-to-right across the grid.
    The player must identify and select exactly those tiles.

    Attributes:
        difficulty:    "medium" — unlocks at round 5.
        prompt:        Instruction shown in the header.
        correct_tiles: Set of (col, row) tuples forming the crosswalk path.
        grid:          TileGrid instance managing layout and selection.
    """

    difficulty = "medium"

    def __init__(self) -> None:
        """Initialise the challenge with a randomly generated path."""
        super().__init__()
        self.prompt = "Select all crosswalk tiles"
        self.correct_tiles: set[tuple[int, int]] = set()
        self.grid = TileGrid()
        self._randomise()

    def _randomise(self) -> None:
        """Generate a new crosswalk path and assign icons to all tiles.

        Resets grid selection state after building the new icon map.
        """
        all_positions = [
            (col, row)
            for row in range(GRID_ROWS)
            for col in range(GRID_COLS)
        ]
        self.correct_tiles = _generate_path()

        icon_map: dict[tuple[int, int], callable] = {}
        for pos in all_positions:
            if pos in self.correct_tiles:
                icon_map[pos] = _draw_crosswalk_tile
            else:
                icon_map[pos] = _draw_road_tile

        self.grid.icon_map = icon_map
        self.grid.reset()

    def render(self, surface: pygame.Surface) -> None:
        """Draw the tile grid with crosswalk and road icons.

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
        """Return True if the player's selection exactly matches the path.

        Returns:
            True if selection == correct_tiles, False otherwise.
        """
        return self.grid.selected == self.correct_tiles

    def reset(self) -> None:
        """Re-randomise the path layout for reuse in a new round."""
        self._randomise()