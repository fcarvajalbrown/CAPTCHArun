"""
settings.py — Global constants for CAPTCHArun.

All magic numbers live here. No other module should hardcode colors,
dimensions, or timing values. Import what you need with:
    from settings import COLOR, SCREEN_W, ...
"""

# ── Screen ────────────────────────────────────────────────────────────────────
SCREEN_W = 360
SCREEN_H = 640
FPS = 60
TITLE = "CAPTCHArun"

# ── Colors ────────────────────────────────────────────────────────────────────
COLOR = {
    "background":   (240, 240, 240),   # #F0F0F0
    "tile":         (255, 255, 255),   # #FFFFFF
    "tile_border":  (204, 204, 204),   # #CCCCCC
    "highlight":    ( 42,  93, 176),   # #2A5DB0 — selected tile
    "cuboid_front": ( 74, 144, 217),   # #4A90D9
    "cuboid_top":   (106, 175, 230),   # #6AAFE6
    "cuboid_right": ( 46, 109, 164),   # #2E6DA4
    "timer":        (229,  57,  53),   # #E53935
    "chrome":       (117, 117, 117),   # #757575
    "text":         ( 33,  33,  33),   # #212121
    "text_light":   (255, 255, 255),   # white text on dark tiles
    "pass":         ( 52, 168,  83),   # green flash on correct
    "fail":         (234,  67,  53),   # red flash on wrong
}

# ── Cuboid ────────────────────────────────────────────────────────────────────
CUBOID_DEPTH = 10   # px offset for top/right faces (isometric illusion)

# ── Grid ──────────────────────────────────────────────────────────────────────
GRID_COLS     = 3
GRID_ROWS     = 3
GRID_TILE_W   = 96    # px
GRID_TILE_H   = 96    # px
GRID_PADDING  = 8     # gap between tiles

# ── Timer ─────────────────────────────────────────────────────────────────────
TIMER_START_S      = 12.0   # seconds for round 1
TIMER_MIN_S        = 4.0    # floor — never goes below this
TIMER_DECAY        = 0.4    # seconds subtracted per round

# ── Suspicion (lives) ─────────────────────────────────────────────────────────
MAX_STRIKES = 3

# ── Difficulty gating ─────────────────────────────────────────────────────────
# challenge_factory.py uses these to unlock harder types progressively
DIFFICULTY_THRESHOLDS = {
    "easy":   0,    # available from round 1
    "medium": 5,    # unlocks at round 5
    "hard":   8,    # unlocks at round 8
}

# ── UI Layout (relative to 360×640) ──────────────────────────────────────────
HEADER_H        = 80    # px — top bar with "Verify you are human"
TIMER_BAR_H     = 8     # px — thin bar below header
VERIFY_BTN_H    = 48    # px — bottom verify button
SUSPICION_BAR_H = 16    # px — suspicion meter above verify button
BOTTOM_PANEL_H  = VERIFY_BTN_H + SUSPICION_BAR_H + 24  # total bottom region

# ── Fonts ─────────────────────────────────────────────────────────────────────
# pygame.font.SysFont name — monospace enforces the sterile corporate feel
FONT_FAMILY = "couriernew"
FONT_SIZE_LG = 18
FONT_SIZE_MD = 14
FONT_SIZE_SM = 11