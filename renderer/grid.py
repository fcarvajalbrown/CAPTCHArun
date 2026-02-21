"""
renderer/grid.py — Tile grid layout and hit detection for CAPTCHArun.

TileGrid manages the NxN grid of clickable tiles that most challenge types
use. It handles:
    - Computing tile positions from settings constants
    - Tracking which tiles are selected
    - Hit detection against native game coordinates
    - Rendering each tile as flat (unselected) or cuboid (selected)

Challenges that need a grid instantiate TileGrid directly and call
render() each frame. They read selected_indices to evaluate correctness.

The grid is always centered horizontally within the 360px game width,
and positioned vertically in the middle region between the header and
the bottom panel.
"""

import pygame
from typing import Set
from settings import (
    SCREEN_W, SCREEN_H,
    GRID_COLS, GRID_ROWS,
    GRID_TILE_W, GRID_TILE_H, GRID_PADDING,
    HEADER_H, TIMER_BAR_H, BOTTOM_PANEL_H,
    COLOR, CUBOID_DEPTH,
)
from renderer.cuboid import draw_cuboid, draw_flat_tile
from utils.color import RGBColor


class TileGrid:
    """A clickable NxN grid of tiles centered in the game viewport.

    Attributes:
        cols:             Number of columns.
        rows:             Number of rows.
        tile_w:           Width of each tile in pixels.
        tile_h:           Height of each tile in pixels.
        padding:          Gap between tiles in pixels.
        origin_x:         X pixel of the grid's top-left tile.
        origin_y:         Y pixel of the grid's top-left tile.
        selected:         Set of (col, row) tuples the player has toggled on.
        tile_color:       Base color for unselected tiles.
        selected_color:   Base color for selected (cuboid) tiles.
        icon_map:         Optional dict mapping (col, row) → callable(surface, rect)
                          for rendering vector icons inside tiles.
    """

    def __init__(
        self,
        cols: int = GRID_COLS,
        rows: int = GRID_ROWS,
        tile_w: int = GRID_TILE_W,
        tile_h: int = GRID_TILE_H,
        padding: int = GRID_PADDING,
        tile_color: RGBColor = COLOR["tile"],
        selected_color: RGBColor = COLOR["highlight"],
        icon_map: dict | None = None,
    ) -> None:
        """Initialise a TileGrid and compute its screen position.

        Grid is centered horizontally and placed in the vertical midpoint
        of the space between the header+timer and the bottom panel.

        Args:
            cols:           Number of tile columns.
            rows:           Number of tile rows.
            tile_w:         Tile width in pixels.
            tile_h:         Tile height in pixels.
            padding:        Gap between adjacent tiles in pixels.
            tile_color:     RGB fill for unselected tiles.
            selected_color: RGB fill for selected tiles (cuboid face color).
            icon_map:       Optional dict of (col, row) → draw callable.
                            Each callable receives (surface, pygame.Rect) and
                            should draw a vector icon inside the tile bounds.
        """
        self.cols = cols
        self.rows = rows
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.padding = padding
        self.tile_color = tile_color
        self.selected_color = selected_color
        self.icon_map = icon_map or {}
        self.selected: Set[tuple[int, int]] = set()

        self._compute_origin()

    def _compute_origin(self) -> None:
        """Calculate the pixel origin (top-left of the grid) to center it.

        The usable vertical region sits between the header+timer bar at the
        top and the bottom panel. The grid is centered within that region.
        """
        top_used = HEADER_H + TIMER_BAR_H
        bottom_used = BOTTOM_PANEL_H
        usable_h = SCREEN_H - top_used - bottom_used

        grid_w = self.cols * self.tile_w + (self.cols - 1) * self.padding
        grid_h = self.rows * self.tile_h + (self.rows - 1) * self.padding

        self.origin_x = (SCREEN_W - grid_w) // 2
        self.origin_y = top_used + (usable_h - grid_h) // 2

    def tile_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the pygame.Rect for a tile at grid position (col, row).

        Args:
            col: Column index (0-based, left to right).
            row: Row index (0-based, top to bottom).

        Returns:
            pygame.Rect in native game coordinates.
        """
        x = self.origin_x + col * (self.tile_w + self.padding)
        y = self.origin_y + row * (self.tile_h + self.padding)
        return pygame.Rect(x, y, self.tile_w, self.tile_h)

    def hit_test(self, gx: int, gy: int) -> tuple[int, int] | None:
        """Return the (col, row) of the tile under a game coordinate, or None.

        Always pass game-space coordinates (after Scaler.to_game()) — never
        raw window mouse coordinates.

        Args:
            gx: X coordinate in native game space (0–360).
            gy: Y coordinate in native game space (0–640).

        Returns:
            (col, row) tuple if the point is inside a tile, else None.
            Returns None if the point falls in the padding gap between tiles.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                if self.tile_rect(col, row).collidepoint(gx, gy):
                    return (col, row)
        return None

    def toggle(self, col: int, row: int) -> None:
        """Toggle the selected state of a tile.

        Selected tiles render as raised cuboids; unselected tiles are flat.

        Args:
            col: Column index.
            row: Row index.
        """
        key = (col, row)
        if key in self.selected:
            self.selected.discard(key)
        else:
            self.selected.add(key)

    def handle_click(self, gx: int, gy: int) -> tuple[int, int] | None:
        """Handle a mouse click in game coordinates, toggling the hit tile.

        Convenience method combining hit_test() and toggle().

        Args:
            gx: X in native game space.
            gy: Y in native game space.

        Returns:
            (col, row) of the toggled tile, or None if no tile was hit.
        """
        hit = self.hit_test(gx, gy)
        if hit is not None:
            self.toggle(*hit)
        return hit

    def reset(self) -> None:
        """Clear all selected tiles. Call between challenge rounds."""
        self.selected.clear()

    def render(self, surface: pygame.Surface) -> None:
        """Draw all tiles onto the surface.

        Selected tiles are drawn as cuboids (raised, colored).
        Unselected tiles are drawn flat (white with gray border).
        Vector icons from icon_map are drawn on top of each tile.

        Args:
            surface: pygame Surface in native 360x640 resolution.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                rect = self.tile_rect(col, row)
                is_selected = (col, row) in self.selected

                if is_selected:
                    draw_cuboid(
                        surface,
                        rect.x, rect.y,
                        rect.w, rect.h,
                        self.selected_color,
                        border_color=COLOR["chrome"],
                    )
                else:
                    draw_flat_tile(
                        surface,
                        rect.x, rect.y,
                        rect.w, rect.h,
                        self.tile_color,
                        border_color=COLOR["tile_border"],
                    )

                # Draw vector icon if one is registered for this tile
                icon_fn = self.icon_map.get((col, row))
                if icon_fn is not None:
                    icon_fn(surface, rect)