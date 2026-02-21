"""
challenges/registry.py — Central registry of all available challenge types.

This is the ONLY file that needs to change when adding a new challenge.
Drop a new file in challenges/, subclass CaptchaChallenge, then add one
line to CHALLENGE_REGISTRY below.

Registry format:
    {
        "challenge_id": (ChallengeClass, base_weight),
        ...
    }

    challenge_id:  Unique string key, used by challenge_factory.py
                   for the no-repeat guard and logging.
    ChallengeClass: The subclass of CaptchaChallenge to instantiate.
    base_weight:   Relative probability weight for random selection.
                   Higher = more likely to appear. Weights are relative
                   to each other, not absolute percentages.

Difficulty gating:
    challenge_factory.py reads each class's `difficulty` attribute and
    filters the pool by DIFFICULTY_THRESHOLDS before sampling. Challenges
    whose min_round exceeds the current round are excluded automatically.
    You do not need to handle gating here — just set `difficulty` on
    the class.

Weight tuning guide:
    - Equal weights (10/10/10) → uniform random selection
    - Higher weight on easy types keeps early rounds approachable
    - Reduce weight on a type if playtesters find it appears too often
"""

from challenges.traffic_light import TrafficLightChallenge
from challenges.bus import BusChallenge
from challenges.checkbox import CheckboxChallenge
from challenges.crosswalk import CrosswalkChallenge
from challenges.shuffle_text import ShuffleTextChallenge
from challenges.base import CaptchaChallenge
from settings import DIFFICULTY_THRESHOLDS

# ── Registry ──────────────────────────────────────────────────────────────────
# Format: "id": (Class, base_weight)
CHALLENGE_REGISTRY: dict[str, tuple[type[CaptchaChallenge], int]] = {
    "traffic_light": (TrafficLightChallenge, 10),
    "bus":           (BusChallenge,          10),
    "checkbox":      (CheckboxChallenge,     10),
    "crosswalk":     (CrosswalkChallenge,     7),
    "shuffle":       (ShuffleTextChallenge,   5),
}


def _resolve_min_round(difficulty: str) -> int:
    """Map a difficulty string to its minimum round threshold.

    Args:
        difficulty: One of "easy", "medium", "hard".

    Returns:
        The minimum round number at which this challenge can appear.
        Defaults to 0 if the difficulty string is unrecognised.
    """
    return DIFFICULTY_THRESHOLDS.get(difficulty, 0)


# ── Stamp min_round onto each class at import time ────────────────────────────
# This means challenge_factory.py can read cls.min_round without knowing
# anything about the difficulty → round mapping logic.
for _cls, _ in CHALLENGE_REGISTRY.values():
    _cls.min_round = _resolve_min_round(_cls.difficulty)