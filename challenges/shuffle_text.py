"""
challenges/shuffle_text.py — "Type the distorted text" CAPTCHA challenge.

The classic text CAPTCHA. A short word (4–6 characters) is displayed in
a distorted, noisy style using vector rendering — no image assets. Each
character is drawn at a slightly randomised angle, offset, and size to
mimic the visual noise of real text CAPTCHAs.

The player types the word using the keyboard. Backspace is supported.
Matching is case-insensitive.

This challenge intentionally has no grid — it owns its own render and
input handling entirely.

Difficulty: hard — unlocks at round 8.
"""

from __future__ import annotations
import pygame
import random
import math
from challenges.base import CaptchaChallenge
from settings import (
    SCREEN_W, SCREEN_H,
    HEADER_H, TIMER_BAR_H, BOTTOM_PANEL_H,
    COLOR, FONT_FAMILY,
)
from renderer.cuboid import draw_flat_tile, draw_cuboid


# ── Word bank ─────────────────────────────────────────────────────────────────
# Short, unambiguous words. Avoid characters that look alike (0/O, 1/I/l).
_WORD_BANK = [
    "CRANE", "BRICK", "TOWER", "FRAME", "TRUSS",
    "CABLE", "VAULT", "SHAFT", "REBAR", "GROUT",
    "RIVET", "SHARD", "PLUMB", "CHORD", "FLANGE",
]

# ── Layout constants ──────────────────────────────────────────────────────────
_DISPLAY_Y_RATIO = 0.38   # vertical center of distorted text as fraction of usable height
_INPUT_BOX_H     = 44
_INPUT_BOX_W     = SCREEN_W - 48
_CHAR_BASE_SIZE  = 32     # base font size for distorted characters
_MAX_ANGLE_DEG   = 18     # max rotation per character in degrees
_MAX_OFFSET_PX   = 6      # max vertical jitter per character in pixels
_NOISE_LINE_COUNT = 12    # number of random noise lines drawn over the text


# ── Distorted character renderer ──────────────────────────────────────────────

def _render_distorted_text(
    surface: pygame.Surface,
    word: str,
    cx: int,
    cy: int,
    char_offsets: list[dict],
) -> None:
    """Draw a word with per-character rotation, offset, and size variation.

    Each character is rendered onto a small surface, rotated, then blitted
    at a jittered position. Noise lines are drawn over the whole text region
    to add visual complexity.

    Args:
        surface:      Native game surface.
        word:         The word to display (uppercase).
        cx:           Horizontal center of the text block in game coords.
        cy:           Vertical center of the text block in game coords.
        char_offsets: List of dicts (one per char) with keys:
                          "angle"  — rotation in degrees
                          "dy"     — vertical offset in pixels
                          "size"   — font point size
                      Pre-generated in _randomise() so offsets are stable
                      across frames (not re-randomised each render call).
    """
    char_spacing = 28
    total_w = len(word) * char_spacing
    start_x = cx - total_w // 2

    # Draw noise lines behind characters
    noise_color = (*COLOR["chrome"], 80)
    noise_surf = pygame.Surface((total_w + 40, 80), pygame.SRCALPHA)
    for _ in range(_NOISE_LINE_COUNT):
        x1 = random.randint(0, total_w + 40)
        y1 = random.randint(0, 80)
        x2 = random.randint(0, total_w + 40)
        y2 = random.randint(0, 80)
        pygame.draw.line(noise_surf, noise_color, (x1, y1), (x2, y2), 1)
    surface.blit(noise_surf, (start_x - 20, cy - 40))

    # Draw each character
    for i, char in enumerate(word):
        meta = char_offsets[i]
        font = pygame.font.Font(None, int(meta["size"] * 1.35))
        char_surf = font.render(char, True, COLOR["text"])

        # Rotate
        rotated = pygame.transform.rotate(char_surf, meta["angle"])

        # Position
        bx = start_x + i * char_spacing + char_spacing // 2 - rotated.get_width() // 2
        by = cy + meta["dy"] - rotated.get_height() // 2
        surface.blit(rotated, (bx, by))


# ── Challenge class ───────────────────────────────────────────────────────────

class ShuffleTextChallenge(CaptchaChallenge):
    """CAPTCHA challenge: type the distorted word shown on screen.

    A word from _WORD_BANK is displayed with per-character visual distortion.
    The player types the answer; matching is case-insensitive. Backspace works.

    Attributes:
        difficulty:    "hard" — unlocks at round 8.
        prompt:        Instruction shown in the header.
        word:          The target word the player must type.
        typed:         The string the player has typed so far.
        char_offsets:  Stable per-character randomisation data for rendering.
        input_rect:    pygame.Rect of the text input box in game coordinates.
        solved:        True once the player's typed input matches the word.
    """

    difficulty = "hard"

    def __init__(self) -> None:
        """Initialise with a random word and stable character offsets."""
        super().__init__()
        self.prompt = "Type the text shown below"
        self.word: str = ""
        self.typed: str = ""
        self.char_offsets: list[dict] = []
        self.solved: bool = False

        usable_top = HEADER_H + TIMER_BAR_H
        usable_h = SCREEN_H - usable_top - BOTTOM_PANEL_H
        self._text_cy = usable_top + int(usable_h * _DISPLAY_Y_RATIO)
        self._text_cx = SCREEN_W // 2

        input_x = (SCREEN_W - _INPUT_BOX_W) // 2
        input_y = self._text_cy + 60
        self.input_rect = pygame.Rect(input_x, input_y, _INPUT_BOX_W, _INPUT_BOX_H)

        self._randomise()

    def _randomise(self) -> None:
        """Pick a new word and generate stable per-character distortion data.

        Character offsets are generated once per round so the display is
        stable across frames — characters do not jitter while the player reads.
        Resets typed input and solved state.
        """
        self.word = random.choice(_WORD_BANK)
        self.typed = ""
        self.solved = False
        self.char_offsets = [
            {
                "angle": random.uniform(-_MAX_ANGLE_DEG, _MAX_ANGLE_DEG),
                "dy":    random.randint(-_MAX_OFFSET_PX, _MAX_OFFSET_PX),
                "size":  random.randint(_CHAR_BASE_SIZE - 4, _CHAR_BASE_SIZE + 6),
            }
            for _ in self.word
        ]

    def render(self, surface: pygame.Surface) -> None:
        """Draw the distorted word and the player's typed input box.

        Args:
            surface: Native 360x640 game surface.
        """
        # Distorted word display area background
        display_rect = pygame.Rect(
            self._text_cx - 100, self._text_cy - 44,
            200, 88,
        )
        draw_flat_tile(surface, display_rect.x, display_rect.y,
                       display_rect.w, display_rect.h,
                       (230, 230, 230), COLOR["tile_border"])

        _render_distorted_text(
            surface, self.word,
            self._text_cx, self._text_cy,
            self.char_offsets,
        )

        # Input box — cuboid if focused (always focused in this challenge)
        draw_cuboid(
            surface,
            self.input_rect.x, self.input_rect.y,
            self.input_rect.w, self.input_rect.h,
            COLOR["tile"], d=6,
            border_color=COLOR["highlight"],
        )

        # Typed text inside input box
        font = pygame.font.Font(None, 27)
        display_typed = self.typed + ("_" if len(self.typed) < len(self.word) else "")
        typed_surf = font.render(display_typed.upper(), True, COLOR["text"])
        tx = self.input_rect.x + 12
        ty = self.input_rect.y + (_INPUT_BOX_H - typed_surf.get_height()) // 2
        surface.blit(typed_surf, (tx, ty))

        # Character count hint
        hint_font = pygame.font.Font(None, 14)
        hint = hint_font.render(
            f"{len(self.typed)}/{len(self.word)} characters",
            True, COLOR["chrome"],
        )
        surface.blit(hint, (
            self.input_rect.x + self.input_rect.w - hint.get_width() - 8,
            self.input_rect.y + self.input_rect.h + 6,
        ))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle keyboard input — printable characters and backspace.

        Input is capped at the length of the target word. The player
        cannot type more characters than the word requires.

        Args:
            event: A pygame event. Only KEYDOWN events are handled.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif len(self.typed) < len(self.word):
            char = event.unicode.upper()
            if char.isalpha():
                self.typed += char

    def is_solved(self) -> bool:
        """Return True if the typed input matches the target word.

        Matching is case-insensitive and requires the full word.

        Returns:
            True if typed == word (case-insensitive), False otherwise.
        """
        return self.typed.upper() == self.word.upper()

    def reset(self) -> None:
        """Pick a new word and reset all input state for a new round."""
        self._randomise()