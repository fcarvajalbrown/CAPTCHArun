"""
core/audio.py — Audio manager for CAPTCHArun.

Generates all sounds programmatically using pure Python math — no numpy,
no audio files. Compatible with both CPython and pygbag WASM (itch.io).

All sounds are in C major (C4=261Hz, E4=329Hz, G4=392Hz, A4=440Hz, C5=523Hz).
Wave generation uses struct.pack to build raw PCM bytes that pygame.mixer.Sound
accepts directly via the buffer protocol.

Sound design:
    tile_select   — A5 square blip (880Hz)        — tactile click
    tile_deselect — E5 square blip (659Hz)         — lighter deselect
    verify        — A4→E5 two-tone (440→659Hz)     — deliberate submission
    pass          — C4 E4 G4 C5 arpeggio           — rewarding C major chord
    fail          — E4→C4→A3 descent (329→261→220) — punishing but musical
    timeout       — A4 double alarm (440Hz)         — urgent, distinct
    checkbox_flee — 800→200Hz pitch drop sweep      — comedic
    menu_hover    — C6 soft tick (1047Hz)           — subtle affordance
    menu_start    — 200→800Hz sine sweep            — game is beginning

Usage:
    audio = Audio()
    audio.init()
    audio.play("tile_select")
"""

from __future__ import annotations
import math
import struct
import pygame

# ── Synthesis constants ───────────────────────────────────────────────────────
_SAMPLE_RATE = 22050
_MAX_AMP     = 32767   # int16 max


def _pack(samples: list[float]) -> bytes:
    """Pack a list of float samples [-1.0, 1.0] into signed 16-bit stereo PCM bytes.

    Duplicates mono into L+R channels so pygame stereo mixer accepts it.

    Args:
        samples: List of float values in [-1.0, 1.0].

    Returns:
        Raw PCM bytes: interleaved L R L R ... int16 stereo.
    """
    buf = []
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * _MAX_AMP)
        buf.append(struct.pack("<hh", v, v))   # L + R
    return b"".join(buf)


def _square(freq: float, duration: float, volume: float = 0.3) -> list[float]:
    """Generate a square wave as a list of float samples.

    Args:
        freq:     Frequency in Hz.
        duration: Duration in seconds.
        volume:   Amplitude in [0.0, 1.0].

    Returns:
        List of float samples.
    """
    n = int(_SAMPLE_RATE * duration)
    period = _SAMPLE_RATE / freq
    return [volume * (1.0 if (i % period) < (period / 2) else -1.0) for i in range(n)]


def _sine(freq: float, duration: float, volume: float = 0.3) -> list[float]:
    """Generate a sine wave as a list of float samples.

    Args:
        freq:     Frequency in Hz.
        duration: Duration in seconds.
        volume:   Amplitude in [0.0, 1.0].

    Returns:
        List of float samples.
    """
    n = int(_SAMPLE_RATE * duration)
    return [volume * math.sin(2 * math.pi * freq * i / _SAMPLE_RATE) for i in range(n)]


def _sweep(f_start: float, f_end: float, duration: float,
           volume: float = 0.3, wave: str = "square") -> list[float]:
    """Generate a frequency sweep (glide) between two frequencies.

    Args:
        f_start:  Starting frequency in Hz.
        f_end:    Ending frequency in Hz.
        duration: Duration in seconds.
        volume:   Amplitude in [0.0, 1.0].
        wave:     "square" or "sine".

    Returns:
        List of float samples.
    """
    n = int(_SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = f_start + (f_end - f_start) * t
        phase += 2 * math.pi * freq / _SAMPLE_RATE
        if wave == "square":
            samples.append(volume * (1.0 if math.sin(phase) >= 0 else -1.0))
        else:
            samples.append(volume * math.sin(phase))
    return samples


def _concat(*parts: list[float]) -> list[float]:
    """Concatenate multiple sample lists into one.

    Args:
        *parts: Any number of float sample lists.

    Returns:
        Single concatenated list.
    """
    result = []
    for p in parts:
        result.extend(p)
    return result


def _fade_out(samples: list[float], tail: float = 0.05) -> list[float]:
    """Apply a linear fade-out to the last `tail` seconds of a sample list.

    Prevents clicks and pops at the end of short sounds.

    Args:
        samples: Float sample list.
        tail:    Seconds of fade at the end.

    Returns:
        Modified sample list.
    """
    fade_n = min(int(_SAMPLE_RATE * tail), len(samples))
    result = list(samples)
    for i in range(fade_n):
        idx = len(result) - fade_n + i
        result[idx] *= i / fade_n
    return result


def _silence(duration: float) -> list[float]:
    """Generate silence.

    Args:
        duration: Duration in seconds.

    Returns:
        List of zero-value float samples.
    """
    return [0.0] * int(_SAMPLE_RATE * duration)


def _make_sound(samples: list[float]) -> pygame.mixer.Sound:
    """Convert a float sample list to a pygame.mixer.Sound.

    Args:
        samples: Float sample list in [-1.0, 1.0].

    Returns:
        pygame.mixer.Sound ready to play.
    """
    return pygame.mixer.Sound(buffer=_pack(samples))


# ── Audio manager ─────────────────────────────────────────────────────────────

class Audio:
    """Manages all game audio. Pure Python synthesis, no numpy required.

    Works identically in CPython and pygbag WASM. All sounds are in C major.

    Attributes:
        _sounds:    Dict mapping sound name → pygame.mixer.Sound.
        _available: True if pygame.mixer initialised successfully.
    """

    def __init__(self) -> None:
        """Create an uninitialised Audio manager. Call init() before use."""
        self._sounds:    dict[str, pygame.mixer.Sound] = {}
        self._available: bool = False

    def init(self) -> None:
        """Initialise pygame.mixer and synthesize all sounds.

        Safe to call multiple times. Silent no-op if mixer init fails.
        """
        try:
            pygame.mixer.pre_init(_SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init()
            self._available = True
            self._generate_sounds()
        except pygame.error:
            self._available = False

    def _generate_sounds(self) -> None:
        """Synthesize all sounds and cache as pygame.mixer.Sound objects.

        All frequencies chosen from C major scale for harmonic consistency.
        """
        # tile_select — A5 square blip (880Hz) — sharp tactile click
        self._sounds["tile_select"] = _make_sound(
            _fade_out(_square(880, 0.06, volume=0.25))
        )

        # tile_deselect — E5 square blip (659Hz) — lighter than select
        self._sounds["tile_deselect"] = _make_sound(
            _fade_out(_square(659, 0.06, volume=0.20))
        )

        # verify — A4→E5 two-tone (440→659Hz) — deliberate, musical
        self._sounds["verify"] = _make_sound(
            _fade_out(_concat(
                _square(440, 0.07, volume=0.28),
                _square(659, 0.07, volume=0.28),
            ))
        )

        # pass — C4 E4 G4 C5 ascending arpeggio — C major chord, rewarding
        self._sounds["pass"] = _make_sound(
            _fade_out(_concat(
                _square(261, 0.07, volume=0.30),
                _square(329, 0.07, volume=0.30),
                _square(392, 0.07, volume=0.30),
                _square(523, 0.12, volume=0.35),
            ))
        )

        # fail — E4→C4→A3 descent — punishing but stays in C major
        self._sounds["fail"] = _make_sound(
            _fade_out(_concat(
                _square(329, 0.08, volume=0.30),
                _square(261, 0.08, volume=0.30),
                _square(220, 0.14, volume=0.25),
            ))
        )

        # timeout — A4 double alarm — urgent, distinct from fail
        self._sounds["timeout"] = _make_sound(
            _fade_out(_concat(
                _square(440, 0.08, volume=0.30),
                _silence(0.04),
                _square(440, 0.08, volume=0.30),
            ))
        )

        # checkbox_flee — 800→200Hz sweep — comedic pitch drop
        self._sounds["checkbox_flee"] = _make_sound(
            _fade_out(_sweep(800, 200, 0.15, volume=0.25, wave="square"))
        )

        # menu_hover — C6 soft tick (1047Hz) — subtle affordance
        self._sounds["menu_hover"] = _make_sound(
            _fade_out(_square(1047, 0.03, volume=0.12))
        )

        # menu_start — 200→800Hz sine sweep — ascending game start feel
        self._sounds["menu_start"] = _make_sound(
            _fade_out(_sweep(200, 800, 0.25, volume=0.30, wave="sine"))
        )

    def play(self, name: str) -> None:
        """Play a sound by name. Silent no-op if unavailable or unknown.

        Args:
            name: One of: tile_select, tile_deselect, verify, pass, fail,
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
        for sound in self._sounds.values():
            sound.set_volume(max(0.0, min(1.0, volume)))

    def quit(self) -> None:
        """Shut down pygame.mixer cleanly on game exit."""
        if self._available:
            pygame.mixer.quit()