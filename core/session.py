"""
core/session.py — Player session state for CAPTCHArun.

Session tracks all mutable game data that persists across rounds:
    - Round number
    - Score and streak multiplier
    - Strike (suspicion) count
    - Flash feedback state (pass/fail overlay timing)

Session does NOT own the timer, the current challenge, or any rendering.
It is a pure data container with methods for state transitions.

game.py is the sole caller. It reads session state each frame and calls
the appropriate transition methods in response to game events.

Usage:
    session = Session()
    session.reset()                  # start a new game

    # on correct answer:
    session.register_pass()

    # on wrong answer or timeout:
    session.register_fail()

    # each frame:
    session.update_flash(dt)
    flash_color, flash_alpha = session.flash_state()
"""

from settings import MAX_STRIKES, COLOR

# Flash animation duration in seconds
_FLASH_DURATION = 0.45

# Score awarded per correct answer at base (multiplied by streak)
_BASE_SCORE = 100


class Session:
    """Mutable game state for one full playthrough.

    Attributes:
        round_num:     Current round number, 1-based. Increments on each pass.
        score:         Cumulative score across all rounds.
        streak:        Consecutive correct answers. Resets to 0 on any fail.
        strikes:       Number of wrong answers / timeouts. Game over at MAX_STRIKES.
        _flash_color:  RGB tuple of the active flash overlay color, or None.
        _flash_timer:  Seconds remaining in the current flash animation.
    """

    def __init__(self) -> None:
        """Initialise session with zeroed state. Call reset() before use."""
        self.round_num: int   = 1
        self.score:     int   = 0
        self.streak:    int   = 0
        self.strikes:   int   = 0
        self._flash_color: tuple | None = None
        self._flash_timer: float        = 0.0

    def reset(self) -> None:
        """Reset all state to begin a fresh game.

        Call this when the player starts a new game from the menu or
        after a game over.
        """
        self.round_num = 1
        self.score     = 0
        self.streak    = 0
        self.strikes   = 0
        self._flash_color = None
        self._flash_timer = 0.0

    # ── Round transitions ─────────────────────────────────────────────────────

    def register_pass(self) -> None:
        """Record a correct answer, update score and streak, advance round.

        Score per round = BASE_SCORE * (1 + streak). Streak increments
        after the score is computed so the first correct answer always
        awards BASE_SCORE (multiplier of 1).
        """
        multiplier   = 1 + self.streak
        self.score  += _BASE_SCORE * multiplier
        self.streak += 1
        self.round_num += 1
        self._start_flash(COLOR["pass"])

    def register_fail(self) -> None:
        """Record a wrong answer or timeout, increment strikes, reset streak.

        Does not advance the round — the player retries a new challenge
        at the same difficulty level.
        """
        self.strikes += 1
        self.streak   = 0
        self._start_flash(COLOR["fail"])

    def is_game_over(self) -> bool:
        """Return True if the player has exhausted all strikes.

        Returns:
            True if strikes >= MAX_STRIKES.
        """
        return self.strikes >= MAX_STRIKES

    # ── Flash overlay ─────────────────────────────────────────────────────────

    def _start_flash(self, color: tuple) -> None:
        """Begin a flash animation with the given color.

        Args:
            color: RGB tuple — COLOR["pass"] for green, COLOR["fail"] for red.
        """
        self._flash_color = color
        self._flash_timer = _FLASH_DURATION

    def update_flash(self, dt: float) -> None:
        """Tick the flash animation timer down by dt seconds.

        Call this every frame. The flash fades out linearly over
        _FLASH_DURATION seconds and clears itself when done.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self._flash_timer > 0.0:
            self._flash_timer = max(0.0, self._flash_timer - dt)
            if self._flash_timer == 0.0:
                self._flash_color = None

    def flash_state(self) -> tuple[tuple | None, float]:
        """Return the current flash color and normalised alpha.

        Alpha is 1.0 at the start of the flash and fades to 0.0 at the end.
        Returns (None, 0.0) when no flash is active.

        Returns:
            Tuple of (color_or_None, alpha_float).
            Pass directly to renderer/ui.py draw_flash().
        """
        if self._flash_color is None or _FLASH_DURATION == 0:
            return None, 0.0
        alpha = self._flash_timer / _FLASH_DURATION
        return self._flash_color, alpha

    # ── Convenience reads ─────────────────────────────────────────────────────

    def multiplier(self) -> int:
        """Return the current score multiplier (1 + streak).

        Returns:
            Integer multiplier. 1 on no streak, higher with consecutive passes.
        """
        return 1 + self.streak

    def strikes_remaining(self) -> int:
        """Return how many strikes the player has left before game over.

        Returns:
            Non-negative integer.
        """
        return max(0, MAX_STRIKES - self.strikes)