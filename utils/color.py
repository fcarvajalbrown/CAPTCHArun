"""
utils/color.py — Color manipulation helpers for CAPTCHArun.

Used primarily by renderer/cuboid.py to derive the top and right face
shades from a single base color, producing the isometric illusion without
hardcoding every face color manually.
"""

from typing import Tuple

RGBColor = Tuple[int, int, int]


def clamp(value: int, lo: int = 0, hi: int = 255) -> int:
    """Clamp an integer value to [lo, hi].

    Args:
        value: The integer to clamp.
        lo:    Lower bound (inclusive). Defaults to 0.
        hi:    Upper bound (inclusive). Defaults to 255.

    Returns:
        The clamped integer.
    """
    return max(lo, min(hi, value))


def lighter(color: RGBColor, amount: int = 40) -> RGBColor:
    """Return a lightened version of an RGB color.

    Used for the top face of a cuboid — top faces catch more light.

    Args:
        color:  Base RGB tuple, e.g. (74, 144, 217).
        amount: How much to add to each channel. Defaults to 40.

    Returns:
        A new RGB tuple with each channel increased by `amount`, clamped to 255.
    """
    r, g, b = color
    return (clamp(r + amount), clamp(g + amount), clamp(b + amount))


def darker(color: RGBColor, amount: int = 40) -> RGBColor:
    """Return a darkened version of an RGB color.

    Used for the right face of a cuboid — side faces are in shadow.

    Args:
        color:  Base RGB tuple, e.g. (74, 144, 217).
        amount: How much to subtract from each channel. Defaults to 40.

    Returns:
        A new RGB tuple with each channel decreased by `amount`, clamped to 0.
    """
    r, g, b = color
    return (clamp(r - amount), clamp(g - amount), clamp(b - amount))


def with_alpha(color: RGBColor, alpha: int) -> Tuple[int, int, int, int]:
    """Append an alpha channel to an RGB tuple.

    Useful when drawing to a Surface with per-pixel alpha (SRCALPHA).

    Args:
        color: Base RGB tuple.
        alpha: Alpha value 0–255 (0 = transparent, 255 = opaque).

    Returns:
        An RGBA tuple.
    """
    return (color[0], color[1], color[2], clamp(alpha))


def lerp_color(a: RGBColor, b: RGBColor, t: float) -> RGBColor:
    """Linearly interpolate between two RGB colors.

    Used for smooth flash transitions (pass/fail feedback).

    Args:
        a: Start color.
        b: End color.
        t: Interpolation factor in [0.0, 1.0]. 0 → a, 1 → b.

    Returns:
        Interpolated RGB tuple.
    """
    t = max(0.0, min(1.0, t))
    return (
        clamp(int(a[0] + (b[0] - a[0]) * t)),
        clamp(int(a[1] + (b[1] - a[1]) * t)),
        clamp(int(a[2] + (b[2] - a[2]) * t)),
    )