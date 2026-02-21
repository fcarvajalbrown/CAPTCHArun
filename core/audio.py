"""
core/audio.py — Audio manager for CAPTCHArun.

Generates all sounds programmatically using numpy + pygame.sndarray.
No audio files required — all sounds are synthesized bit/chiptune style
at runtime, fitting the corporate-glitch aesthetic of the game.

Sound design intent:
    - tile_select:   short blip (square wave, high pitch) — tactile click feedback
    - tile_deselect: same blip, slightly lower pitch — deselection feels lighter
    - verify:        ascending two-tone blip — submission feels deliberate
    - pass:          bright ascending arpeggio — rewarding, satisfying
    - fail:          descending buzz — punishing but not annoying
    - timeout:       flat alarm blip — distinct from fail, urgency
    - checkbox_flee: quick whoosh-like pitch drop — comedic
    - menu_hover:    very short soft tick — subtle affordance
    - menu_start:    boot-up ascending sweep — game is beginning

All sounds are generated in _generate_sounds() which is called once on
init(). If pygame.mixer is unavailable or numpy is missing, all methods
become silent no-ops — the game runs fine without audio.

Usage:
    audio = Audio()
    audio.init()

    # anywhere in game.py or challenge handlers:
    audio.play("tile_select")
    audio.play("pass")
"""

from __future__ import annotations
import pygame

# numpy is optional — audio degrades gracefully without it
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

# ── Synthesis constants ───────────────────────────────────────────────────────
_SAMPLE_RATE = 22050   # Hz — low rate reinforces chiptune feel
_CHANNELS    = 1       # mono
_BIT_DEPTH   = 16      # signed 16-bit


def _square_wave(freq: float, duration: float, volume: float = 0.3) -> "np.ndarray":
    """Generate a square wave buffer.

    Args:
        freq:     Frequency in Hz.
        duration: Duration in seconds.
        volume:   Amplitude scale in [0.0, 1.0].

    Returns:
        int16 numpy array ready for pygame.sndarray.make_sound().
    """
    n_samples = int(_SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    return (wave * volume * 32767).astype(np.int16)


def _sine_wave(freq: float, duration: float, volume: float = 0.3) -> "np.ndarray":
    """Generate a sine wave buffer.

    Args:
        freq:     Frequency in Hz.
        duration: Duration in seconds.
        volume:   Amplitude scale in [0.0, 1.0].

    Returns:
        int16 numpy array.
    """
    n_samples = int(_SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    return (wave * volume * 32767).astype(np.int16)


def _sweep(freq_start: float, freq_end: float, duration: float,
           volume: float = 0.3, wave: str = "square") -> "np.ndarray":
    """Generate a frequency sweep (glide) buffer.

    Args:
        freq_start: Starting frequency in Hz.
        freq_end:   Ending frequency in Hz.
        duration:   Duration in seconds.
        volume:     Amplitude scale in [0.0, 1.0].
        wave:       "square" or "sine".

    Returns:
        int16 numpy array.
    """
    n_samples = int(_SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    freqs = np.linspace(freq_start, freq_end, n_samples)
    phase = np.cumsum(2 * np.pi * freqs / _SAMPLE_RATE)
    raw = np.sign(np.sin(phase)) if wave == "square" else np.sin(phase)
    return (raw * volume * 32767).astype(np.int16)


def _concat(*buffers: "np.ndarray") -> "np.ndarray":
    """Concatenate multiple wave buffers into one.

    Args:
        *buffers: Any number of int16 arrays.

    Returns:
        Single concatenated int16 array.
    """
    return np.concatenate(buffers)


def _fade_out(buf: "np.ndarray", tail: float = 0.05) -> "np.ndarray":
    """Apply a linear fade-out to the last `tail` seconds of a buffer.

    Prevents clicks and pops at the end of short sounds.

    Args:
        buf:  int16 numpy array.
        tail: Seconds of fade at the end.

    Returns:
        Modified int16 array.
    """
    fade_samples = min(int(_SAMPLE_RATE * tail), len(buf))
    envelope = np.ones(len(buf))
    envelope[-fade_samples:] = np.linspace(1.0, 0.0, fade_samples)
    return (buf * envelope).astype(np.int16)


# ── Audio manager ─────────────────────────────────────────────────────────────

class Audio:
    """Manages all game audio. Generates sounds on init, plays on demand.

    All public methods are safe to call even if audio is unavailable —
    they silently no-op if mixer init failed or numpy is missing.

    Attributes:
        _sounds:    Dict mapping sound name → pygame.mixer.Sound.
        _available: True if pygame.mixer initialised successfully.
    """

    def __init__(self) -> None:
        """Create an uninitialised Audio manager. Call init() before use."""
        self._sounds:    dict[str, pygame.mixer.Sound] = {}
        self._available: bool = False

    def init(self) -> None:
        """Initialise pygame.mixer and generate all sounds.

        Safe to call multiple times — reinitialises cleanly.
        If numpy is unavailable, _available stays False and all
        play() calls become silent no-ops.
        """
        if not _NUMPY_AVAILABLE:
            return

        try:
            pygame.mixer.pre_init(_SAMPLE_RATE, -_BIT_DEPTH, _CHANNELS, 512)
            pygame.mixer.init()
            self._available = True
            self._generate_sounds()
        except pygame.error:
            self._available = False

    def _generate_sounds(self) -> None:
        """Synthesize all game sounds and store as pygame.mixer.Sound objects.

        Called once during init(). Each sound is a short programmatic
        synthesis — square waves, sweeps, and arpeggios in chiptune style.
        """
        def make(buf: "np.ndarray") -> pygame.mixer.Sound:
            """Wrap a numpy buffer as a pygame Sound."""
            # pygame.sndarray requires 2D for mono: shape (n, 1) or (n,)
            return pygame.sndarray.make_sound(buf)

        # tile_select — short high blip
        self._sounds["tile_select"] = make(
            _fade_out(_square_wave(880, 0.06, volume=0.25))
        )

        # tile_deselect — same blip, lower pitch
        self._sounds["tile_deselect"] = make(
            _fade_out(_square_wave(660, 0.06, volume=0.2))
        )

        # verify — two-tone ascending blip (deliberate submission feel)
        self._sounds["verify"] = make(
            _fade_out(_concat(
                _square_wave(440, 0.07, volume=0.28),
                _square_wave(660, 0.07, volume=0.28),
            ))
        )

        # pass — bright ascending arpeggio (C4 E4 G4 C5)
        self._sounds["pass"] = make(
            _fade_out(_concat(
                _square_wave(261, 0.07, volume=0.3),
                _square_wave(329, 0.07, volume=0.3),
                _square_wave(392, 0.07, volume=0.3),
                _square_wave(523, 0.12, volume=0.35),
            ))
        )

        # fail — descending buzz (E4 → C4 → low A3)
        self._sounds["fail"] = make(
            _fade_out(_concat(
                _square_wave(329, 0.08, volume=0.3),
                _square_wave(261, 0.08, volume=0.3),
                _square_wave(220, 0.14, volume=0.25),
            ))
        )

        # timeout — flat alarm pulse (two repeated beeps)
        alarm = _square_wave(440, 0.08, volume=0.3)
        silence = np.zeros(int(_SAMPLE_RATE * 0.04), dtype=np.int16)
        self._sounds["timeout"] = make(
            _fade_out(_concat(alarm, silence, alarm))
        )

        # checkbox_flee — comedic pitch drop sweep
        self._sounds["checkbox_flee"] = make(
            _fade_out(_sweep(800, 200, 0.15, volume=0.25, wave="square"))
        )

        # menu_hover — very soft tick
        self._sounds["menu_hover"] = make(
            _fade_out(_square_wave(1200, 0.03, volume=0.12))
        )

        # menu_start — ascending sweep into game
        self._sounds["menu_start"] = make(
            _fade_out(_sweep(200, 800, 0.25, volume=0.3, wave="sine"))
        )

    def play(self, name: str) -> None:
        """Play a sound by name. Silent no-op if unavailable or name unknown.

        Args:
            name: Sound identifier string. One of:
                  tile_select, tile_deselect, verify, pass, fail,
                  timeout, checkbox_flee, menu_hover, menu_start.
        """
        if not self._available:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.play()

    def set_volume(self, volume: float) -> None:
        """Set global volume for all sounds.

        Args:
            volume: Float in [0.0, 1.0].
        """
        if not self._available:
            return
        volume = max(0.0, min(1.0, volume))
        for sound in self._sounds.values():
            sound.set_volume(volume)

    def quit(self) -> None:
        """Shut down pygame.mixer cleanly on game exit."""
        if self._available:
            pygame.mixer.quit()