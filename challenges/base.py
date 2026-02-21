"""
challenges/base.py — Abstract base class for all CAPTCHA challenge types.

Every challenge in CAPTCHArun inherits from CaptchaChallenge and implements
three methods: render(), handle_event(), and is_solved().

The challenge lifecycle is:
    1. challenge_factory.py instantiates a challenge subclass
    2. game.py calls handle_event() each frame for input
    3. game.py calls render() each frame to draw the challenge
    4. When the player hits VERIFY, game.py calls is_solved() to judge

Challenges are self-contained — they own their grid, icon map, and any
internal state. They do NOT touch score, suspicion, or timer. Those live
in session.py and are managed by game.py.

Adding a new challenge type:
    1. Create a new file in challenges/
    2. Subclass CaptchaChallenge
    3. Implement the three abstract methods
    4. Register it in challenges/registry.py
"""

from __future__ import annotations
import pygame
from abc import ABC, abstractmethod


class CaptchaChallenge(ABC):
    """Abstract base for all CAPTCHA challenge types.

    Attributes:
        difficulty: Tier string — "easy", "medium", or "hard".
                    Used by challenge_factory.py for round-based gating.
        min_round:  Earliest round this challenge type can appear.
                    Derived from difficulty and DIFFICULTY_THRESHOLDS in settings.py.
        prompt:     Instruction string shown in the UI header, e.g.
                    "Select all traffic lights".
    """

    difficulty: str = "easy"   # subclasses override this
    min_round:  int = 0        # set automatically by registry at import time

    def __init__(self) -> None:
        """Initialise the challenge.

        Subclasses must call super().__init__() and then set up their
        own grid, icon_map, correct_tiles, and any internal state.
        """
        self.prompt: str = "Verify you are human"

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Draw the challenge onto the game surface.

        Called every frame while the challenge is active. Should draw
        the tile grid, any vector icons, and any challenge-specific UI.
        Does NOT draw the header, timer bar, or verify button — those
        are handled by renderer/ui.py in game.py.

        Args:
            surface: Native 360x640 pygame Surface.
        """
        ...

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event for this challenge.

        Called by game.py for every event in the event queue while the
        challenge is active. Typically handles MOUSEBUTTONDOWN to toggle
        tile selection, or KEYDOWN for text-input challenges.

        Args:
            event: A pygame event object.
        """
        ...

    @abstractmethod
    def is_solved(self) -> bool:
        """Return True if the player's current selection is correct.

        Called by game.py when the player presses VERIFY. Should compare
        the player's selected tiles (or input) against the challenge's
        correct answer without mutating any state — game.py may call this
        more than once.

        Returns:
            True if the challenge is correctly solved, False otherwise.
        """
        ...

    def reset(self) -> None:
        """Reset challenge state for reuse or retry.

        Optional override. Default implementation does nothing.
        Subclasses that generate randomised layouts should re-randomise
        here so the same challenge instance can be reused cleanly.
        """
        pass