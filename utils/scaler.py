"""
utils/scaler.py — Resolution scaling for CAPTCHArun.

The game is designed at 360x640 (9:16 vertical). This module handles
letterboxing that base resolution into any window size — desktop itch.io
embed, fullscreen desktop, or future mobile viewport — without stretching
or distorting the layout.

Usage:
    scaler = Scaler(window_w, window_h)
    game_surface = pygame.Surface((SCREEN_W, SCREEN_H))

    # draw everything onto game_surface at native resolution, then:
    scaler.blit(window_surface, game_surface)

    # convert a mouse position from window coords to game coords:
    game_x, game_y = scaler.to_game(mouse_x, mouse_y)
"""

import pygame
from settings import SCREEN_W, SCREEN_H


class Scaler:
    """Letterboxes the native game resolution into an arbitrary window.

    Attributes:
        window_w:   Actual window width in pixels.
        window_h:   Actual window height in pixels.
        scale:      Uniform scale factor applied to the game surface.
        offset_x:   Horizontal letterbox offset in window pixels.
        offset_y:   Vertical letterbox offset in window pixels.
        dest_rect:  pygame.Rect describing where the scaled game surface lands.
    """

    def __init__(self, window_w: int, window_h: int) -> None:
        """Compute scale and letterbox offsets for a given window size.

        Chooses the largest uniform scale factor that fits the native
        resolution inside the window without cropping.

        Args:
            window_w: Window width in pixels.
            window_h: Window height in pixels.
        """
        self.window_w = window_w
        self.window_h = window_h
        self._compute(window_w, window_h)

    def _compute(self, window_w: int, window_h: int) -> None:
        """Recalculate scale and offsets. Called on init and on resize.

        Args:
            window_w: Window width in pixels.
            window_h: Window height in pixels.
        """
        scale_x = window_w / SCREEN_W
        scale_y = window_h / SCREEN_H
        self.scale = min(scale_x, scale_y)

        scaled_w = int(SCREEN_W * self.scale)
        scaled_h = int(SCREEN_H * self.scale)

        self.offset_x = (window_w - scaled_w) // 2
        self.offset_y = (window_h - scaled_h) // 2

        self.dest_rect = pygame.Rect(self.offset_x, self.offset_y, scaled_w, scaled_h)

    def update(self, window_w: int, window_h: int) -> None:
        """Recompute scaling when the window is resized.

        Call this from the main loop whenever a VIDEORESIZE event fires.

        Args:
            window_w: New window width in pixels.
            window_h: New window height in pixels.
        """
        self.window_w = window_w
        self.window_h = window_h
        self._compute(window_w, window_h)

    def blit(self, window_surface: pygame.Surface, game_surface: pygame.Surface) -> None:
        """Scale and blit the game surface onto the window surface.

        Fills letterbox bars with black before blitting so they're always clean.

        Args:
            window_surface: The actual pygame display surface.
            game_surface:   The native-resolution surface all game rendering writes to.
        """
        window_surface.fill((0, 0, 0))
        scaled = pygame.transform.scale(game_surface, self.dest_rect.size)
        window_surface.blit(scaled, self.dest_rect.topleft)

    def to_game(self, window_x: int, window_y: int) -> tuple[int, int]:
        """Convert window pixel coordinates to native game coordinates.

        Use this to translate mouse positions before passing them to
        any game logic or hit detection.

        Args:
            window_x: Mouse X in window pixels.
            window_y: Mouse Y in window pixels.

        Returns:
            (game_x, game_y) in native 360x640 coordinate space.
            Values may be negative or exceed screen bounds if the cursor
            is inside a letterbox bar — callers should guard against this.
        """
        game_x = (window_x - self.offset_x) / self.scale
        game_y = (window_y - self.offset_y) / self.scale
        return int(game_x), int(game_y)

    def in_bounds(self, window_x: int, window_y: int) -> bool:
        """Return True if a window coordinate falls inside the game viewport.

        Useful for ignoring clicks that land in letterbox bars.

        Args:
            window_x: Mouse X in window pixels.
            window_y: Mouse Y in window pixels.

        Returns:
            True if the point is within the scaled game area.
        """
        return self.dest_rect.collidepoint(window_x, window_y)