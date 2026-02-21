# CAPTCHArun — Product Requirements Document

**Version:** 0.1  
**Status:** Pre-production  
**Target platforms:** itch.io (web/pygame-wasm), Mobile app (future)

---

## 1. Concept

A meta-arcade game where the player is trapped inside a CAPTCHA verification loop. Each level is a different challenge type drawn with pure vector graphics (cuboids, rects, polygons — no sprites). The game is self-aware: it mocks corporate UX patterns while being genuinely fun and mechanically simple.

**Elevator pitch:** *"You are not a robot. Prove it. Again. Forever."*

---

## 2. Goals

| Goal | Description |
|---|---|
| **Portfolio** | Showcase pygame + vector rendering skills on itch.io |
| **Viral potential** | Meta-humor + CAPTCHA familiarity = shareable |
| **Mobile-ready** | Vertical layout from day one for future app port |
| **Scope control** | Flappy Bird complexity — no physics engine, no sprites |

---

## 3. Target Audience

- Casual players on itch.io (browser, free)
- Fans of meta/surreal games (e.g. CaptchaWare, The Stanley Parable)
- Mobile casual audience (future)

---

## 4. Core Gameplay Loop

```
[CAPTCHA Screen] → Player solves challenge → [Pass/Fail judgment]
     ↑                                               |
     └──────── Next challenge (harder) ──────────────┘
                         |
                   [Game Over] on 3 fails or timer = 0
```

Each "verification attempt" is one challenge. The game tracks:
- **Streak** (correct in a row → score multiplier)
- **Suspicion meter** (wrong answers fill it → game over)
- **Speed** (timer shrinks each round)

---

## 5. Challenge Types (MVP)

| ID | Name | Mechanic |
|---|---|---|
| `traffic_light` | Select all traffic lights | Click cuboid tiles matching the target |
| `bus` | Select all buses | Same as above, different icon set (pure vectors) |
| `crosswalk` | Click the correct path | Highlight a walkable tile sequence |
| `shuffle` | Type the distorted text | Keyboard input on a scrambled letter display |
| `checkbox` | Just click the checkbox | A trolley problem — checkbox moves |

All tile grids are 3×3 or 4×4 cuboid blocks. No images.

---

## 6. Visual Design

### Color Palette
| Element | Hex |
|---|---|
| Background | `#F0F0F0` |
| Grid tiles (default) | `#FFFFFF` with `#CCCCCC` border |
| Correct tile highlight | `#2A5DB0` |
| Cuboid front face | `#4A90D9` |
| Cuboid top face | `#6AAFE6` |
| Cuboid right face | `#2E6DA4` |
| Timer bar | `#E53935` |
| UI chrome | `#757575` |
| Text | `#212121` |

### Rendering Rules
- **No sprites.** Everything is `pygame.draw.polygon`, `pygame.draw.rect`, `pygame.draw.line`.
- Cuboid = 3 polygons (front, top, right) with hardcoded isometric offset `d = 10px`.
- Font: monospace only (courier-style) to reinforce the sterile corporate feel.

### Layout — Vertical First
```
┌──────────────────────┐
│   [CAPTCHA HEADER]   │  ← "Verify you are human"
│   [TIMER BAR]        │
│                      │
│   ┌───┬───┬───┐      │
│   │   │ ✓ │   │      │  ← 3×3 grid of cuboid tiles
│   ├───┼───┼───┤      │
│   │ ✓ │   │ ✓ │      │
│   ├───┼───┼───┤      │
│   │   │   │ ✓ │      │
│   └───┴───┴───┘      │
│                      │
│   [VERIFY BUTTON]    │
│   [Suspicion meter]  │
└──────────────────────┘
```
Target resolution: **360×640** (9:16). Scales up for desktop.

---

## 7. Architecture

```
captcharun/
├── main.py                  # Entry point, game loop
├── settings.py              # Constants: colors, screen size, timing
│
├── core/
│   ├── game.py              # Game state machine (MENU, PLAYING, FAIL, WIN)
│   ├── session.py           # Tracks score, streak, suspicion, round count
│   └── timer.py             # Countdown logic, speed scaling per round
│
├── challenges/
│   ├── base.py              # Abstract CaptchaChallenge: render(), handle_event(), is_solved()
│   ├── traffic_light.py
│   ├── bus.py
│   ├── crosswalk.py
│   ├── shuffle_text.py
│   └── checkbox.py
│
├── renderer/
│   ├── cuboid.py            # draw_cuboid(surface, x, y, w, h, d, color)
│   ├── ui.py                # draw_header(), draw_timer_bar(), draw_suspicion_meter()
│   └── grid.py              # TileGrid: manages NxN layout, hit detection
│
└── utils/
    ├── color.py             # lighter(), darker() helpers for cuboid shading
    └── scaler.py            # Resolution scaling for vertical → desktop
```

### Key Design Decisions

**State machine over spaghetti flags.** `game.py` owns a single `state: GameState` enum. All transitions go through it — nothing else mutates global state.

**Challenge factory pattern.** `session.py` picks the next challenge via a weighted random selector. Adding a new challenge type = drop a new file in `/challenges`, register it in one dict. No other changes.

**Renderer is stateless.** All draw functions take explicit arguments. No renderer holds game state. This makes the mobile port clean — swap pygame surface for a different backend without touching game logic.

**Vertical layout from day 1.** `settings.py` defines `SCREEN_W = 360, SCREEN_H = 640`. The scaler in `utils/scaler.py` letterboxes this into any window size (desktop itch.io embed or fullscreen mobile).

---

## 8. Platforms & Export

| Phase | Platform | Method |
|---|---|---|
| **v1** | itch.io (browser) | pygame-ce + pygbag (WASM export) |
| **v2** | Windows/Mac download | PyInstaller `.exe` / `.app` |
| **v3** | Mobile | Kivy port or rewrite in Godot 4 using same design doc |

---

## 9. MVP Scope

**In:**
- 3 challenge types (`traffic_light`, `bus`, `checkbox`)
- Suspicion meter + 3-strike system
- Timer that speeds up each round
- Score/streak display
- Game over + restart screen
- Full vector rendering, no assets

**Out (post-MVP):**
- Sound / SFX
- Leaderboard
- More challenge types
- Animations between challenges
- Mobile build

---

## 10. Success Metrics (itch.io)

- 65%+ browser play-through rate (industry avg ~65% per itch data)
- Featured in "New & Popular" within first week
- Shareable by nature: the concept is self-explanatory in a screenshot

---

## 11. Open Questions

- Should the "robot" player character be visible on screen, or is the player the cursor itself?
- Does the suspicion meter fill visually as a cuboid bar (on-brand) or a standard rect?
- Pygbag WASM build tested on pygame-ce? Confirm compatibility before committing.