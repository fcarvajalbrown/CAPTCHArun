"""
renderer/cuboid.py — Pure vector cuboid drawing for CAPTCHArun.

All visual elements in the game are built from cuboids: grid tiles,
UI bars, the player cursor, and decorative elements on the main menu.

A cuboid is rendered as three filled polygons sharing edges:
    - Front face  (base color)
    - Top face    (lighter — catches light)
    - Right face  (darker  — in shadow)

The isometric illusion is produced by a single depth offset `d` applied
to the top-right corner. No matrices or camera transforms are used.

Coordinate system:
    (x, y) is the TOP-LEFT corner of the FRONT face.
    Width and height describe the front face dimensions.
    Depth `d` is the pixel offset for top/right faces (defaults to CUBOID_DEPTH).

Example:
    draw_cuboid(surface, x=50, y=100, w=80, h=80, color=(74, 144, 217))
"""

import pygame
from settings import COLOR, CUBOID_DEPTH
from utils.color import lighter, darker, RGBColor


def draw_cuboid(
    surface: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    color: RGBColor,
    d: int = CUBOID_DEPTH,
    border_color: RGBColor | None = None,
    border_width: int = 1,
) -> None:
    """Draw a filled isometric cuboid using three polygon faces.

    Args:
        surface:      pygame Surface to draw onto.
        x:            X coordinate of the front face top-left corner.
        y:            Y coordinate of the front face top-left corner.
        w:            Width of the front face in pixels.
        h:            Height of the front face in pixels.
        color:        RGB tuple for the front face. Top and right faces
                      are derived automatically via lighter() and darker().
        d:            Isometric depth offset in pixels. Controls how
                      pronounced the 3D effect appears. Defaults to CUBOID_DEPTH.
        border_color: Optional RGB tuple for edge outlines. Pass None to skip.
        border_width: Outline thickness in pixels. Defaults to 1.
    """
    front_color = color
    top_color   = lighter(color)
    right_color = darker(color)

    # ── Face vertices ─────────────────────────────────────────────────────────
    # Front face: simple rectangle in screen space
    front = [
        (x,     y    ),
        (x + w, y    ),
        (x + w, y + h),
        (x,     y + h),
    ]

    # Top face: parallelogram shifted up-right by (d, -d)
    top = [
        (x,         y    ),
        (x + w,     y    ),
        (x + w + d, y - d),
        (x     + d, y - d),
    ]

    # Right face: parallelogram shifted right by (d, -d) from front-right edge
    right = [
        (x + w,     y    ),
        (x + w + d, y - d),
        (x + w + d, y + h - d),
        (x + w,     y + h),
    ]

    # ── Draw faces ────────────────────────────────────────────────────────────
    pygame.draw.polygon(surface, top_color,   top)
    pygame.draw.polygon(surface, right_color, right)
    pygame.draw.polygon(surface, front_color, front)

    # ── Draw outlines ─────────────────────────────────────────────────────────
    if border_color is not None:
        pygame.draw.polygon(surface, border_color, front, border_width)
        pygame.draw.polygon(surface, border_color, top,   border_width)
        pygame.draw.polygon(surface, border_color, right, border_width)


def draw_flat_tile(
    surface: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    color: RGBColor,
    border_color: RGBColor | None = None,
    border_width: int = 1,
) -> None:
    """Draw a flat (2D) rectangle tile with an optional border.

    Used for grid tiles that are not yet selected. Visually flat to contrast
    with the raised cuboid appearance of selected/highlighted tiles.

    Args:
        surface:      pygame Surface to draw onto.
        x:            X coordinate of the top-left corner.
        y:            Y coordinate of the top-left corner.
        w:            Width in pixels.
        h:            Height in pixels.
        color:        RGB fill color.
        border_color: Optional RGB tuple for the border. Pass None to skip.
        border_width: Border thickness in pixels. Defaults to 1.
    """
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, color, rect)
    if border_color is not None:
        pygame.draw.rect(surface, border_color, rect, border_width)


def draw_cuboid_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    total_w: int,
    h: int,
    fill: float,
    fill_color: RGBColor,
    bg_color: RGBColor = COLOR["tile"],
    d: int = CUBOID_DEPTH // 2,
) -> None:
    """Draw a horizontal progress bar styled as a cuboid.

    Used for the timer bar and suspicion meter. The bar fills left-to-right
    based on `fill`. The filled portion is a cuboid; the empty portion is flat.

    Args:
        surface:     pygame Surface to draw onto.
        x:           X coordinate of the bar's top-left.
        y:           Y coordinate of the bar's top-left.
        total_w:     Total width of the bar in pixels.
        h:           Height of the bar in pixels.
        fill:        Fill ratio in [0.0, 1.0]. 1.0 = completely full.
        fill_color:  RGB color for the filled (cuboid) portion.
        bg_color:    RGB color for the empty background portion.
        d:           Isometric depth for the cuboid portion. Defaults to half CUBOID_DEPTH.
    """
    fill = max(0.0, min(1.0, fill))
    filled_w = int(total_w * fill)

    # Background (empty portion) — flat
    draw_flat_tile(surface, x, y, total_w, h, bg_color, COLOR["tile_border"])

    # Filled portion — cuboid
    if filled_w > 0:
        draw_cuboid(surface, x, y, filled_w, h, fill_color, d=d)