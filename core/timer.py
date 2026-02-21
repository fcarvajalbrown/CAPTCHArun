"""
core/timer.py — Countdown timer logic for CAPTCHArun.

Each round has a time limit that shrinks as the game progresses.
Timer owns only its own state — it does not touch session, score,
or suspicion. game.py polls is_expired() and reacts accordingly.

Usage:
    timer = Timer()
    timer.start(round_num=1)

    # each frame:
    timer.update(dt)
    fill = timer.fill()       # float 0.0–1.0 for the timer bar
    if timer.is_expired():
        # handle time-out in game.py
"""

from settings import TIMER_START_S, TIMER_MIN_S, TIMER_DECAY


class Timer:
    """Countdown timer with per-round speed scaling.

    The time limit for each round is computed as:
        limit = max(TIMER_MIN_S, TIMER_START_S - (round_num - 1) * TIMER_DECAY)

    Attributes:
        _limit:    Total seconds allowed for the current round.
        _elapsed:  Seconds elapsed since the timer was started.
        _running:  True if the timer is actively counting down.
    """

    def __init__(self) -> None:
        """Initialise a stopped timer with default values."""
        self._limit:   float = TIMER_START_S
        self._elapsed: float = 0.0
        self._running: bool  = False

    def start(self, round_num: int) -> None:
        """Start (or restart) the timer for a given round number.

        Computes the time limit for this round based on the decay curve
        defined in settings.py, then resets elapsed time and begins counting.

        Args:
            round_num: Current round number (1-based). Higher rounds get
                       shorter time limits down to TIMER_MIN_S.
        """
        decay = (round_num - 1) * TIMER_DECAY
        self._limit   = max(TIMER_MIN_S, TIMER_START_S - decay)
        self._elapsed = 0.0
        self._running = True

    def stop(self) -> None:
        """Stop the timer without resetting elapsed time.

        Call this when the player submits an answer so the timer freezes
        during the pass/fail flash animation.
        """
        self._running = False

    def update(self, dt: float) -> None:
        """Advance the timer by dt seconds.

        No-op if the timer is stopped or already expired.

        Args:
            dt: Delta time in seconds since the last frame. Typically
                sourced from pygame.Clock.tick() / 1000.
        """
        if self._running and self._elapsed < self._limit:
            self._elapsed = min(self._elapsed + dt, self._limit)

    def fill(self) -> float:
        """Return the remaining time as a fraction of the total limit.

        Used by renderer/ui.py to draw the timer bar width.

        Returns:
            Float in [0.0, 1.0]. 1.0 = full time remaining, 0.0 = expired.
        """
        if self._limit <= 0:
            return 0.0
        return max(0.0, 1.0 - self._elapsed / self._limit)

    def remaining(self) -> float:
        """Return remaining seconds as a float.

        Returns:
            Seconds remaining. 0.0 if expired.
        """
        return max(0.0, self._limit - self._elapsed)

    def is_expired(self) -> bool:
        """Return True if the time limit has been reached.

        Returns:
            True if elapsed >= limit, False otherwise.
        """
        return self._elapsed >= self._limit

    def limit(self) -> float:
        """Return the total time limit for the current round in seconds.

        Returns:
            The computed time limit in seconds.
        """
        return self._limit