"""
core/game.py — Central game state machine for CAPTCHArun.

Game owns the top-level state enum and orchestrates all subsystems:
    - Session  (score, strikes, flash)
    - Timer    (countdown per round)
    - ChallengeFactory (random challenge selection)
    - Current challenge (render + event delegation)
    - Audio    (chiptune feedback, C major key)

States:
    MENU      — main menu screen (vector graphics, start prompt)
    PLAYING   — active CAPTCHA challenge
    FLASH     — brief pass/fail overlay before next round loads
    GAMEOVER  — game over screen

Transitions:
    MENU      → PLAYING   : player clicks start
    PLAYING   → FLASH     : player clicks VERIFY or timer expires
    FLASH     → PLAYING   : flash animation ends (session handles timing)
    FLASH     → GAMEOVER  : flash ends and session.is_game_over()
    GAMEOVER  → MENU      : player clicks TRY AGAIN

Audio hookup:
    All sound triggers live in game.py. Challenges call back via
    self._play() which is a silent no-op if audio is not set.
    Challenge-level sounds (tile clicks) are triggered here by
    intercepting MOUSEBUTTONDOWN before delegating to the challenge.

game.py does NOT call pygame.display.flip() or manage the window.
That is main.py's responsibility. Game writes to the game_surface
passed into update() and render().
"""

from __future__ import annotations
import pygame
from enum import Enum, auto

from core.session import Session
from core.timer import Timer
from core.challenge_factory import ChallengeFactory
from challenges.base import CaptchaChallenge
from renderer import ui
from settings import COLOR


class GameState(Enum):
    """Top-level state machine states."""
    MENU     = auto()
    PLAYING  = auto()
    FLASH    = auto()
    GAMEOVER = auto()


class Game:
    """Orchestrates all game subsystems via a state machine.

    Attributes:
        state:     Current GameState enum value.
        session:   Session instance tracking score/strikes/flash.
        timer:     Timer instance for the current round countdown.
        factory:   ChallengeFactory for random challenge selection.
        challenge: The currently active CaptchaChallenge instance.
        _audio:    Audio instance injected via set_audio(). None until set.
        _btn_rect: Cached rect of the verify or retry button for hit detection.
        _hover:    True if the mouse is currently over the action button.
    """

    def __init__(self) -> None:
        """Initialise all subsystems. Call start_menu() before first update."""
        self.state:     GameState             = GameState.MENU
        self.session:   Session               = Session()
        self.timer:     Timer                 = Timer()
        self.factory:   ChallengeFactory      = ChallengeFactory()
        self.challenge: CaptchaChallenge|None = None
        self._audio                           = None
        self._btn_rect: pygame.Rect|None      = None
        self._hover:    bool                  = False

    # ── Audio ─────────────────────────────────────────────────────────────────

    def set_audio(self, audio) -> None:
        """Inject the Audio instance after construction.

        Called by main.py after audio.init() succeeds. Keeping audio out
        of __init__ avoids pygame.mixer being initialised before pygame.init().

        Args:
            audio: Initialised Audio instance from core/audio.py.
        """
        self._audio = audio

    def _play(self, name: str) -> None:
        """Play a sound by name. Silent no-op if audio not set.

        Args:
            name: Sound identifier matching core/audio.py keys.
        """
        if self._audio:
            self._audio.play(name)

    # ── State transitions ─────────────────────────────────────────────────────

    def start_menu(self) -> None:
        """Transition to the MENU state and reset all session data."""
        self.session.reset()
        self.factory.reset_history()
        self.challenge = None
        self.state = GameState.MENU

    def start_game(self) -> None:
        """Transition from MENU to PLAYING, loading the first challenge."""
        self.session.reset()
        self.factory.reset_history()
        self._load_next_challenge()
        self._play("menu_start")
        self.state = GameState.PLAYING

    def _load_next_challenge(self) -> None:
        """Ask the factory for the next challenge and start the timer.

        Called on the transition into each new round.
        """
        self.challenge = self.factory.next_challenge(self.session.round_num)
        self.timer.start(self.session.round_num)
        self._hover = False

    def _submit(self) -> None:
        """Evaluate the current challenge and transition to FLASH.

        Stops the timer, plays verify sound, registers pass or fail with
        session, plays result sound, then moves to FLASH state.
        """
        self.timer.stop()
        self._play("verify")

        if self.challenge and self.challenge.is_solved():
            self.session.register_pass()
            self._play("pass")
        else:
            self.session.register_fail()
            self._play("fail")

        self.state = GameState.FLASH

    def _handle_timeout(self) -> None:
        """Handle timer expiry — distinct sound from a wrong answer.

        Plays the timeout alarm before submitting as a fail.
        """
        self._play("timeout")
        self.timer.stop()
        self.session.register_fail()
        self._play("fail")
        self.state = GameState.FLASH

    # ── Per-frame update ──────────────────────────────────────────────────────

    def update(self, dt: float, game_mouse_pos: tuple[int, int]) -> None:
        """Advance game logic by one frame.

        Args:
            dt:             Delta time in seconds since last frame.
            game_mouse_pos: Mouse position in native game coordinates
                            (already translated by Scaler.to_game()).
        """
        if self.state == GameState.PLAYING:
            self.timer.update(dt)
            self.session.update_flash(dt)

            if self._btn_rect:
                self._hover = self._btn_rect.collidepoint(game_mouse_pos)

            if self.timer.is_expired():
                self._handle_timeout()

        elif self.state == GameState.FLASH:
            self.session.update_flash(dt)

            _, alpha = self.session.flash_state()
            if alpha <= 0.0:
                if self.session.is_game_over():
                    self.state = GameState.GAMEOVER
                else:
                    self._load_next_challenge()
                    self.state = GameState.PLAYING

        elif self.state in (GameState.MENU, GameState.GAMEOVER):
            if self._btn_rect:
                self._hover = self._btn_rect.collidepoint(game_mouse_pos)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route a pygame event to the appropriate handler for the current state.

        Mouse positions in events are expected to already be in game coordinates.
        main.py must translate event.pos via Scaler.to_game() before calling this.

        Args:
            event: A pygame event with pos already in game coordinates.
        """
        if self.state == GameState.MENU:
            self._handle_menu_event(event)

        elif self.state == GameState.PLAYING:
            self._handle_playing_event(event)

        elif self.state == GameState.GAMEOVER:
            self._handle_gameover_event(event)

        # FLASH state consumes no input — player must wait

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """Handle input on the main menu.

        Args:
            event: pygame event in game coordinates.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self.start_game()

    def _handle_playing_event(self, event: pygame.event.Event) -> None:
        """Handle input during an active challenge.

        Intercepts VERIFY button clicks. For tile clicks, plays the
        appropriate sound based on whether the tile is being selected
        or deselected, then delegates to the challenge.

        Args:
            event: pygame event in game coordinates.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # VERIFY button — submit and return
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self._submit()
                return

            # Tile click — select vs deselect sound
            if self.challenge and hasattr(self.challenge, "grid"):
                hit = self.challenge.grid.hit_test(*event.pos)
                if hit is not None:
                    if hit in self.challenge.grid.selected:
                        self._play("tile_deselect")
                    else:
                        self._play("tile_select")

            # Checkbox challenge — click sound
            from challenges.checkbox import CheckboxChallenge
            if isinstance(self.challenge, CheckboxChallenge):
                if self.challenge._box_rect().collidepoint(event.pos):
                    self._play("tile_select")

        # Checkbox flee sound on mouse motion
        if event.type == pygame.MOUSEMOTION:
            from challenges.checkbox import CheckboxChallenge
            if isinstance(self.challenge, CheckboxChallenge):
                prev_pos = (self.challenge.box_x, self.challenge.box_y)
                self.challenge.handle_event(event)
                if (self.challenge.box_x, self.challenge.box_y) != prev_pos:
                    self._play("checkbox_flee")
                return

        # Delegate all other events to the active challenge
        if self.challenge:
            self.challenge.handle_event(event)

    def _handle_gameover_event(self, event: pygame.event.Event) -> None:
        """Handle input on the game over screen.

        Args:
            event: pygame event in game coordinates.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self._play("menu_start")
                self.start_menu()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the current state onto the game surface.

        Args:
            surface: Native 360x640 pygame Surface. Written to each frame.
        """
        surface.fill(COLOR["background"])

        if self.state == GameState.MENU:
            self._render_menu(surface)

        elif self.state in (GameState.PLAYING, GameState.FLASH):
            self._render_playing(surface)

        elif self.state == GameState.GAMEOVER:
            self._render_gameover(surface)

    def _render_menu(self, surface: pygame.Surface) -> None:
        """Draw the main menu screen.

        Args:
            surface: Native game surface.
        """
        from renderer.menu import draw_menu
        self._btn_rect = draw_menu(surface)

    def _render_playing(self, surface: pygame.Surface) -> None:
        """Draw the active challenge, UI chrome, and optional flash overlay.

        Args:
            surface: Native game surface.
        """
        if self.challenge:
            self.challenge.render(surface)

        ui.draw_header(
            surface,
            prompt=self.challenge.prompt if self.challenge else "",
            round_num=self.session.round_num,
            score=self.session.score,
        )
        ui.draw_timer_bar(surface, fill=self.timer.fill())
        ui.draw_suspicion_meter(surface, strikes=self.session.strikes)
        self._btn_rect = ui.draw_verify_button(surface, hovered=self._hover)

        flash_color, flash_alpha = self.session.flash_state()
        if flash_color and flash_alpha > 0.0:
            ui.draw_flash(surface, flash_color, flash_alpha)

    def _render_gameover(self, surface: pygame.Surface) -> None:
        """Draw the game over screen.

        Args:
            surface: Native game surface.
        """
        self._btn_rect = ui.draw_game_over(
            surface,
            score=self.session.score,
            round_num=self.session.round_num,
        )