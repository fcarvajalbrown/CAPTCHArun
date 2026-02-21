"""
main.py — Entry point and game loop for CAPTCHArun.

Responsibilities:
    - Initialise pygame and create the window
    - Own the Scaler (window → game coordinate translation)
    - Run the main loop: handle events → update → render → flip
    - Translate all mouse positions to game coordinates before
      passing them to Game
    - Manage pygame.Clock and delta time
    - Handle VIDEORESIZE events for responsive desktop embedding
    - Wrap the loop in async for pygbag (WASM/itch.io export)

Architecture note:
    main.py is intentionally thin. It owns pygame lifecycle and the
    window — nothing else. All game logic lives in core/game.py.

pygbag compatibility:
    The game loop is wrapped in an async function and driven by
    asyncio.run(). pygbag replaces asyncio with its own event loop
    that yields to the browser each frame. No other changes needed.

Audio:
    Audio is imported and initialised here. audio.play() calls are
    currently TODO — wired in after core gameplay is verified.

Usage (local):
    python main.py

Usage (WASM export):
    pygbag main.py
"""

import asyncio
import pygame
from settings import SCREEN_W, SCREEN_H, FPS, TITLE, COLOR
from utils.scaler import Scaler
from core.game import Game, GameState

# ── Window configuration ──────────────────────────────────────────────────────
# Desktop window starts at 2x native for comfortable play.
# pygbag will override this with the canvas size.
_WINDOW_SCALE  = 2
_WINDOW_W      = SCREEN_W * _WINDOW_SCALE
_WINDOW_H      = SCREEN_H * _WINDOW_SCALE


async def main() -> None:
    """Async main loop — compatible with both CPython and pygbag WASM.

    Initialises pygame, creates all subsystems, then runs the game loop.
    Each iteration yields to the event loop via asyncio.sleep(0), which
    pygbag uses to hand control back to the browser.
    """
    pygame.init()

    # ── Window setup ──────────────────────────────────────────────────────────
    window = pygame.display.set_mode(
        (_WINDOW_W, _WINDOW_H),
        pygame.RESIZABLE,
    )
    pygame.display.set_caption(TITLE)

    # Native resolution surface — all game rendering targets this
    game_surface = pygame.Surface((SCREEN_W, SCREEN_H))

    # Scaler handles letterboxing into the window
    scaler = Scaler(_WINDOW_W, _WINDOW_H)

    # ── Subsystems ────────────────────────────────────────────────────────────
    clock = pygame.Clock()
    game  = Game()
    game.start_menu()

    # TODO: audio init and hookup
    # audio = Audio()
    # audio.init()

    # ── Main loop ─────────────────────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # seconds since last frame
        dt = min(dt, 0.05)              # clamp to 50ms — prevents spiral on tab switch

        # ── Event handling ────────────────────────────────────────────────────
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                scaler.update(event.w, event.h)

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                 pygame.MOUSEMOTION):
                # Translate mouse position to native game coordinates
                # before passing the event to game logic
                if scaler.in_bounds(*event.pos):
                    translated_pos = scaler.to_game(*event.pos)
                    # pygame events are immutable — rebuild with translated pos
                    translated = event.copy()
                    translated.pos = translated_pos
                    game.handle_event(translated)

            elif event.type == pygame.KEYDOWN:
                # Keyboard events have no position — pass directly
                game.handle_event(event)

        # ── Update ────────────────────────────────────────────────────────────
        mouse_window = pygame.mouse.get_pos()
        mouse_game   = scaler.to_game(*mouse_window)
        game.update(dt, mouse_game)

        # ── Render ────────────────────────────────────────────────────────────
        game.render(game_surface)
        scaler.blit(window, game_surface)
        pygame.display.flip()

        # ── Yield to browser (pygbag) ─────────────────────────────────────────
        await asyncio.sleep(0)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    # audio.quit()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())