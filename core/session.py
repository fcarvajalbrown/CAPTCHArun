"""
core/session.py — Player session state for CAPTCHArun.

Session tracks all mutable game data that persists across rounds:
    - Round number
    - Score and streak multiplier
    - Strike (suspicion) count
    - Flash feedback state (pass/fail overlay timing)
    - Security level (every 5 rounds = new level)

game.py is the sole caller. It reads session state each frame and calls
the appropriate transition methods in response to game events.
"""

from settings import MAX_STRIKES, COLOR

_FLASH_DURATION   = 0.45
_BASE_SCORE       = 100
ROUNDS_PER_LEVEL  = 5     # rounds before a security level-up


class Session:
    """Mutable game state for one full playthrough.

    Attributes:
        round_num:      Current round number, 1-based.
        score:          Cumulative score across all rounds.
        streak:         Consecutive correct answers.
        strikes:        Wrong answers / timeouts. Game over at MAX_STRIKES.
        security_level: Current security level, starts at 1.
        level_up:       True if a level-up just occurred this round.
        _flash_color:   RGB tuple of active flash color, or None.
        _flash_timer:   Seconds remaining in flash animation.
    """

    def __init__(self) -> None:
        """Initialise session. Call reset() before use."""
        self.round_num:      int   = 1
        self.score:          int   = 0
        self.streak:         int   = 0
        self.strikes:        int   = 0
        self.security_level: int   = 1
        self.level_up:       bool  = False
        self._flash_color: tuple | None = None
        self._flash_timer: float        = 0.0

    def reset(self) -> None:
        """Reset all state for a fresh game."""
        self.round_num      = 1
        self.score          = 0
        self.streak         = 0
        self.strikes        = 0
        self.security_level = 1
        self.level_up       = False
        self._flash_color   = None
        self._flash_timer   = 0.0

    # ── Round transitions ─────────────────────────────────────────────────────

    def register_pass(self) -> None:
        """Record a correct answer, update score/streak, advance round.

        Sets level_up=True if this round completes a security level
        (every ROUNDS_PER_LEVEL rounds). game.py reads this flag to
        trigger the LEVELUP state.
        """
        multiplier   = 1 + self.streak
        self.score  += _BASE_SCORE * multiplier
        self.streak += 1
        self.round_num += 1
        self.level_up = False

        # Check level up — triggers when round_num crosses a level boundary
        new_level = ((self.round_num - 1) // ROUNDS_PER_LEVEL) + 1
        if new_level > self.security_level:
            self.security_level = new_level
            self.level_up = True

        self._start_flash(COLOR["pass"])

    def register_fail(self) -> None:
        """Record a wrong answer or timeout, increment strikes, reset streak."""
        self.strikes += 1
        self.streak   = 0
        self.level_up = False
        self._start_flash(COLOR["fail"])

    def is_game_over(self) -> bool:
        """Return True if the player has exhausted all strikes."""
        return self.strikes >= MAX_STRIKES

    # ── Flash overlay ─────────────────────────────────────────────────────────

    def _start_flash(self, color: tuple) -> None:
        """Begin a flash animation with the given color."""
        self._flash_color = color
        self._flash_timer = _FLASH_DURATION

    def update_flash(self, dt: float) -> None:
        """Tick the flash animation timer down by dt seconds."""
        if self._flash_timer > 0.0:
            self._flash_timer = max(0.0, self._flash_timer - dt)
            if self._flash_timer == 0.0:
                self._flash_color = None

    def flash_state(self) -> tuple[tuple | None, float]:
        """Return current flash color and normalised alpha (1.0→0.0)."""
        if self._flash_color is None or _FLASH_DURATION == 0:
            return None, 0.0
        alpha = self._flash_timer / _FLASH_DURATION
        return self._flash_color, alpha

    # ── Convenience reads ─────────────────────────────────────────────────────

    def multiplier(self) -> int:
        """Return current score multiplier (1 + streak)."""
        return 1 + self.streak

    def strikes_remaining(self) -> int:
        """Return strikes left before game over."""
        return max(0, MAX_STRIKES - self.strikes)

    def rounds_until_next_level(self) -> int:
        """Return how many rounds remain until the next security level.

        Returns:
            Integer 1–ROUNDS_PER_LEVEL.
        """
        return ROUNDS_PER_LEVEL - ((self.round_num - 1) % ROUNDS_PER_LEVEL)