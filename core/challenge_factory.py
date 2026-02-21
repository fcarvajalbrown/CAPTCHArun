"""
core/challenge_factory.py — Random challenge selector for CAPTCHArun.

The factory is the only place that knows about the full set of challenge
types. It reads from challenges/registry.py and applies three rules when
selecting the next challenge:

    1. Round gating  — challenges whose min_round > current round are excluded.
    2. No-repeat     — the same challenge ID cannot appear twice in a row.
    3. Weighted pick — remaining eligible challenges are sampled by base_weight.

game.py calls next_challenge(round_num) once per round transition and
receives a freshly reset CaptchaChallenge instance ready to render.

Design note:
    Instances are not cached — a new instance is created each round.
    This keeps reset() logic simple and avoids stale state leaking
    between rounds. Challenge classes are lightweight so this is fine.
"""

from __future__ import annotations
import random
from challenges.base import CaptchaChallenge
from challenges.registry import CHALLENGE_REGISTRY


class ChallengeFactory:
    """Weighted random selector for CAPTCHA challenge types.

    Attributes:
        _last_id: The ID string of the most recently returned challenge.
                  Used to enforce the no-repeat rule. None on first call.
    """

    def __init__(self) -> None:
        """Initialise the factory with no history."""
        self._last_id: str | None = None

    def next_challenge(self, round_num: int) -> CaptchaChallenge:
        """Return a new challenge instance appropriate for the given round.

        Applies round gating, no-repeat filtering, and weighted random
        selection in that order. Falls back to the full eligible pool
        (ignoring no-repeat) if filtering would leave zero candidates —
        this prevents a deadlock when only one challenge type is unlocked.

        Args:
            round_num: Current round number (1-based). Used to gate
                       challenges by their min_round attribute.

        Returns:
            A freshly instantiated CaptchaChallenge subclass, reset()
            called to guarantee clean state.

        Raises:
            RuntimeError: If CHALLENGE_REGISTRY is empty or no challenge
                          passes the round gate. This should never happen
                          in a correctly configured registry.
        """
        # Step 1: filter by round gate
        eligible = {
            cid: (cls, weight)
            for cid, (cls, weight) in CHALLENGE_REGISTRY.items()
            if round_num >= cls.min_round
        }

        if not eligible:
            raise RuntimeError(
                f"No challenges available for round {round_num}. "
                "Check DIFFICULTY_THRESHOLDS and registry min_round values."
            )

        # Step 2: apply no-repeat filter — exclude last used ID
        no_repeat = {
            cid: pair
            for cid, pair in eligible.items()
            if cid != self._last_id
        }

        # Step 3: fall back to full eligible pool if no-repeat leaves nothing
        # (only happens when exactly one challenge type is unlocked)
        pool = no_repeat if no_repeat else eligible

        # Step 4: weighted random selection
        ids     = list(pool.keys())
        weights = [pool[cid][1] for cid in ids]
        chosen_id = random.choices(ids, weights=weights, k=1)[0]

        # Step 5: instantiate and reset
        chosen_cls = pool[chosen_id][0]
        instance   = chosen_cls()
        instance.reset()

        self._last_id = chosen_id
        return instance

    def reset_history(self) -> None:
        """Clear the no-repeat history.

        Call this when starting a new game so the first challenge of a
        new session is not constrained by the last challenge of a previous one.
        """
        self._last_id = None