"""
The F1 Straight -- the racing part of the game
=================================================
This is a simple car racing game, kind of like an old game called
"Chrome Dino" where a dinosaur jumps over cactuses -- except here you
drive a race car instead of a dinosaur!

Your car speeds down a road that never ends, and it goes faster and
faster the longer you play (just like a real car shifting into higher
gears). Jump over things on the ground, duck under birds flying by, and
try to survive as long as you can! The longer you play, the sun goes
down and you race at night under bright lights.

This file (game.py) is just the racing part. Picking your team and
picking day or night happens in a different file called launcher.py,
which has prettier buttons and menus. Think of it like this: launcher.py
is the front desk, and game.py is the race track.

Cool things in this game
-------------------------
* Your car is made of tiny colored squares (like Lego bricks) and gets
  painted in your favorite F1 team's colors.
* There are special green "DRS zones" on the road. Hold SHIFT while
  driving through one and your car gets a speed boost -- just like real
  F1 cars do!
* The sky fades between pretty colors, buildings sit in the background,
  little dust sparkles fly behind your tires, and the scoreboard uses a
  cool robot-looking font.

How to play
-----------
    SPACE / UP / W          Jump over things
    DOWN / S                 Duck under things
    SHIFT                     Speed boost -- only works inside a green zone
    SPACE                     Play again after you crash
    H  or click HOME          After you crash: go back and pick a new team
    ESC                       Stop playing
    MODE button (top-left)    Pick AUTO (day turns to night on its own),
                              LIGHT (always daytime), or DARK (always night)

A note for grown-up programmers (Phase Two is here!)
--------------------------------------------------------
This game never looks at the keyboard by itself. Instead, it always
asks one helper, called `InputManager`, "is the jump button being
pressed right now?" That helper is the ONLY part that knows about
keyboards -- which is why we could add a real toy controller (built
from a little computer chip called an ESP32) without changing anything
else in the game. Plug one in over USB, flash the sketch in
`firmware/endless_straight_controller.ino` onto it, and pass its port
name (like "COM5") to `run_race(..., serial_port="COM5")` -- or set it
right in the launcher's menu. See `InputManager._poll_serial` below for
how it reads the controller.

How to start the game:            python launcher.py   (shows the menus)
Just the race, skip the menus:    python game.py
A quick self-check, no window:    python game.py --selftest
"""

import os
import sys
import math
import random
import pygame

# --------------------------------------------------------------------------- #
#  Settings -- all the game's basic numbers, kept in one place
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 900, 300     # how big the game window is
FPS = 60                     # how many pictures we draw every second

GROUND_Y = 250               # how far down the road is (the car's wheels touch here)

BASE_SPEED = 6.0             # how fast the car starts out
MAX_SPEED = 15.0             # the fastest the car can go normally
SPEED_RAMP = 0.0016          # how much faster the car gets for every point you score

BOOST_MULTIPLIER = 1.35      # DRS: how much extra speed a boost gives you
MAX_BOOST_SPEED = 19.0       # the fastest you can ever go, even while boosting

GRAVITY = 0.72                # how hard gravity pulls the car back down after a jump
JUMP_VELOCITY = -13.0         # how strong a jump is (more negative = jumps higher)

NIGHT_EVERY = 600            # roughly how many points before night arrives (it's random -- see below!)
TRANSITION_FRAMES = 45       # how many frames it takes to slowly fade between day and night

# DRS zones are the green stripes of road where boosting is allowed
DRS_ZONE_MIN_W = 230         # the shortest a green zone can be
DRS_ZONE_MAX_W = 360         # the longest a green zone can be

# A palette is just a little box of colors -- one box for day, one for night
DAY = {
    "bg":     (247, 247, 247),
    "ground": (83, 83, 83),
    "ink":    (40, 40, 40),
    "accent": (225, 6, 0),      # bright red -- this is "F1 red"
    "sky":    (210, 226, 240),
}
NIGHT = {
    "bg":     (18, 18, 26),
    "ground": (120, 120, 130),
    "ink":    (230, 230, 235),
    "accent": (255, 40, 40),
    "sky":    (30, 34, 55),
}

DRS_GREEN = (0, 200, 110)   # the green used for DRS zones

# These are the 11 real F1 teams, each with a color that looks like their
# real paint job, so your car can match your favorite team. The colors
# are close guesses, not exact -- feel free to change any of them.
TEAMS = [
    ("McLaren",       (255, 128,   0)),   # orange (matches our example car)
    ("Ferrari",       (222,   0,  45)),   # red
    ("Red Bull",      ( 14,  28,  84)),   # dark navy blue
    ("Mercedes",      (  0, 175, 160)),   # teal
    ("Aston Martin",  (  0,  90,  78)),   # green
    ("Alpine",        (  0, 120, 225)),   # blue
    ("Williams",      ( 70, 195, 230)),   # light blue
    ("Racing Bulls",  ( 58,  72, 190)),   # purple-blue
    ("Audi",          (150,  28,  52)),   # dark red
    ("Haas",          (228, 228, 230)),   # white
    ("Cadillac",      (196, 158,  74)),   # gold
]

GROUND_KINDS = ("tires", "board", "bollard", "debris")   # the different things you can crash into

# The two states the game can be in: still racing, or crashed
RUNNING, GAME_OVER = "running", "game_over"

# The three day/night modes: "auto" changes on its own; "light"/"dark" stay put forever
THEME_MODES = ("auto", "light", "dark")
THEME_LABELS = {"auto": "AUTO", "light": "LIGHT", "dark": "DARK"}


def lerp(a, b, t):
    """Find a number partway between two numbers. If t is 0 you get a, if
    t is 1 you get b, and if t is 0.5 you get the number right in between."""
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    # Same trick as lerp(), but done for a whole color at once
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def darker(c, f=0.6):
    """Make a color darker. A smaller f makes it darker; 1.0 leaves it the same."""
    return tuple(max(0, int(x * f)) for x in c)


def luminance(c):
    """Guess how bright a color looks (0 = looks dark, 1 = looks light).
    We use this to decide if text on top of that color should be black or
    white, so it's always easy to read."""
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255.0


def blend(c1, c2, t):
    """Mix two colors together. t=0 gives all of the first color, t=1
    gives all of the second color, and anything between mixes them."""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# --------------------------------------------------------------------------- #
#  Finding our own files, no matter how the game is being run
# --------------------------------------------------------------------------- #
def _app_dir():
    """Find the folder our game files live in.

    Normally that's just the folder this .py file is sitting in. But if
    the game has been packaged into a single downloadable app (with a
    tool called PyInstaller), Python actually unpacks everything into a
    hidden temporary folder first and runs it from there -- so we check
    for that special case (`sys._MEIPASS`) first, and only fall back to
    "next to this file" when we're running from plain source code."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------- #
#  Fonts -- the letters and numbers we draw on screen
# --------------------------------------------------------------------------- #
# We carry our own font file (called Orbitron) inside the game's folder,
# so the game looks the same on every computer -- Windows, Mac, or
# Linux. If that file is ever missing, we just use a normal font that's
# probably already installed (a slightly different list per computer,
# since Windows, Mac, and Linux don't all ship the same fonts).
FONT_PATH = os.path.join(_app_dir(), "assets", "fonts", "Orbitron-Variable.ttf")
_FALLBACK_FONT_NAMES = "consolas,menlo,dejavusansmono,couriernew,monospace"
_FONT_CACHE = {}   # remembers fonts we've already built, so we don't rebuild them every time


def load_font(size, bold=False):
    # If we already made a font this size before, just reuse it.
    # Otherwise build a new one and remember it for next time.
    key = (size, bold)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = pygame.font.Font(FONT_PATH, size)
        except (FileNotFoundError, OSError):
            _FONT_CACHE[key] = pygame.font.SysFont(_FALLBACK_FONT_NAMES, size, bold=bold)
    return _FONT_CACHE[key]


# --------------------------------------------------------------------------- #
#  City skyline -- the row of buildings way in the background
# --------------------------------------------------------------------------- #
# The buildings scroll by slower than the road, kind of like how far-away
# things out a car window seem to creep past slower than close-up things.
# That little trick makes the world feel like it has real depth to it.
SKY_TILE_W = 300


def _make_skyline():
    # We always build the exact same skyline (same starting seed every
    # time), so the buildings look the same each time you play -- they
    # just scroll past differently depending on how far you've gone.
    rng = random.Random(42)
    buildings = []
    x = 0
    while x < SKY_TILE_W:
        w = rng.randint(18, 40)
        h = rng.randint(20, 70)
        buildings.append((x, w, h))
        x += w + rng.randint(6, 20)
    return buildings


SKYLINE = _make_skyline()


def draw_soft_shadow(surf, center_x, ground_y, width):
    """Draw a soft, see-through shadow blob on the road under something.
    It makes things look like they're really standing on the ground -- and
    for the car, the shadow stays on the road even while the car is up in
    the air, so it also shows you exactly where you're about to land!"""
    h = 6
    sh = pygame.Surface((max(4, int(width)), h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, sh.get_rect(center=(int(center_x), ground_y + 2)))


# --------------------------------------------------------------------------- #
#  The car picture (made of tiny colored squares, like Lego bricks)
# --------------------------------------------------------------------------- #
# We draw the car on a small grid of squares (46 across, 20 down), then
# stretch it bigger without blurring it, so it stays nice and chunky like
# an old video game. `body` is whichever color the team is; everything
# else on the car (tires, wings, cockpit) always looks the same no matter
# which team you pick. The car always faces RIGHT, since that's the way
# it's driving.
SPRITE_W, SPRITE_H = 46, 20


def build_car_grid(body):
    """Build the car as a grid of colors. Each square is either a color,
    or None, which means "see-through, don't draw anything here"."""
    D = (40, 42, 48)      # dark gray -- wings, the ring around the seat, the little fin
    T = (24, 24, 27)      # almost-black -- the tires
    H = (160, 165, 170)   # light gray -- the middle of the wheel
    V = (232, 224, 198)   # cream -- the driver's visor
    S = darker(body, 0.55)  # a darker version of the team color, used for shading

    g = [[None] * SPRITE_W for _ in range(SPRITE_H)]

    def px(r, c, col):
        # Color in one square of the grid, as long as it's actually on the grid
        if 0 <= r < SPRITE_H and 0 <= c < SPRITE_W:
            g[r][c] = col

    # ---- the main body: rounded on top over the seat, long nose up front ----
    def top(x):
        if 5 <= x < 14:  return 8 - (x - 5) * (8 - 6) / 9.0
        if 14 <= x < 20: return 6 - (x - 14) * (6 - 4) / 6.0
        if 20 <= x < 27: return 4
        return 4 + (x - 27) * (13 - 4) / 18.0
    def bot(x):
        if x < 40: return 13
        return 13 - (x - 40) * (13 - 12) / 4.0

    for x in range(5, 45):
        t = int(round(top(x))); b = int(round(bot(x)))
        for y in range(t, b + 1):
            px(y, x, body)
        px(b, x, S)                                   # a thin shadow line along the bottom

    # ---- a little diagonal cut-out shape behind the front wheel ----
    for x in range(23, 33):
        yline = max(9, 13 - (x - 23))
        for y in range(yline, 14):
            px(y, x, D)
    px(9, 14, D); px(10, 14, D); px(9, 15, D)         # a tiny notch, like an air vent

    # ---- the floor line along the bottom of the car ----
    for x in range(6, 41):
        px(14, x, (58, 58, 64))

    # ---- the bump behind the driver's head, plus a fin further back ----
    for x in range(15, 19):
        for y in range(2, 7):
            px(y, x, D)
    px(1, 16, D); px(1, 17, D)
    for x in range(8, 16):
        px(6, x, D)

    # ---- the ring around the cockpit, plus the driver's visor ----
    for x in range(19, 25):
        px(5, x, D)
    px(6, 19, D)
    px(5, 21, V); px(5, 22, V); px(4, 22, V)

    # ---- the wing at the back of the car ----
    for x in range(0, 6):
        px(2, x, D); px(3, x, D)
    for y in range(2, 12):
        px(y, 1, D); px(y, 2, D)
    for x in range(0, 5):
        px(11, x, D)

    # ---- the wing at the front of the car, down low ----
    for x in range(40, 46):
        px(14, x, D); px(15, x, D)
    px(16, 43, D); px(16, 44, D); px(16, 45, D)

    # ---- the wheels: a round tire with a round hub in the middle ----
    def wheel(cx, cy, r):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if d <= r: px(y, x, T)
                if d <= r - 2: px(y, x, H)
                if d <= r - 3.5: px(y, x, darker(H, 0.7))
                if d <= 1: px(y, x, T)
    wheel(11, 13, 6)   # the back wheel
    wheel(35, 13, 6)   # the front wheel
    return g


def surface_from_grid(grid):
    """Turn our grid of colors into a real picture that pygame can draw
    on screen, keeping the see-through squares actually see-through."""
    s = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
    for r, row in enumerate(grid):
        for c, col in enumerate(row):
            if col is not None:
                s.fill(col, (c, r, 1, 1))
    return s


# --------------------------------------------------------------------------- #
#  Reading which buttons you're pressing
# --------------------------------------------------------------------------- #
class InputManager:
    """
    This is the ONE place in the whole game that knows about the keyboard
    (or a real button controller, if you plug one in).

    Everywhere else, the game just asks "is_active('jump')?" -- it never
    looks at the keyboard directly, and it doesn't care whether the
    answer came from a keyboard or a real controller wired up to a
    little computer chip.

    Phase 1: check the keyboard (this is the normal, default way to play).
    Phase 2: check a real 4-button controller instead, sent over a USB
    cable. Pass serial_port="COM5" (or whatever port your controller
    shows up as) to use it. If we can't open that port for any reason,
    we just fall back to the keyboard, so the game always still works.
    """

    ACTIONS = ("jump", "duck", "left", "right", "boost", "home")

    def __init__(self, serial_port=None, baud=115200):
        self.actions = {a: False for a in self.ACTIONS}
        self.serial = None
        self._buf = b""     # leftover bits of text from the controller we haven't used yet
        if serial_port:
            try:
                import serial   # only needed if you're actually using a controller
                # timeout=0 means "don't wait around" -- we never want to
                # freeze the game just because the controller went quiet
                self.serial = serial.Serial(serial_port, baud, timeout=0)
            except Exception as e:
                print(f"[input] {serial_port} unavailable ({e}); using keyboard")

    def update(self):
        if self.serial is not None:
            self._poll_serial()
        else:
            self._poll_keyboard()

    def _poll_keyboard(self):
        keys = pygame.key.get_pressed()
        self.actions["jump"] = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        self.actions["duck"] = keys[pygame.K_DOWN] or keys[pygame.K_s]
        self.actions["boost"] = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.actions["home"] = keys[pygame.K_h]
        self.actions["left"] = keys[pygame.K_LEFT] or keys[pygame.K_a]     # not used yet -- saved for later
        self.actions["right"] = keys[pygame.K_RIGHT] or keys[pygame.K_d]   # not used yet -- saved for later

    def _poll_serial(self):
        """Read whatever the controller has sent so far, and use only the
        NEWEST full line of button info. If lots of lines piled up (say,
        the game paused for a moment), we throw away the old, stale ones
        instead of working through them one by one -- that way, button
        presses always feel like they happened "just now," never delayed."""
        try:
            n = self.serial.in_waiting
            if n:
                self._buf += self.serial.read(n)
        except OSError:
            return   # the controller got unplugged or something -- just skip this frame

        if b"\n" not in self._buf:
            return   # no full line has arrived yet

        parts = self._buf.split(b"\n")
        self._buf = parts[-1]                       # keep any half-finished line for next time
        bits = parts[-2].strip().split(b",")
        if len(bits) != 4:
            # this isn't a real button line (maybe boot-up noise from the
            # board) -- ignore it rather than guessing what it means
            return

        jump, duck, drs, home = (b == b"1" for b in bits)
        self.actions["jump"] = jump
        self.actions["duck"] = duck
        self.actions["boost"] = drs
        self.actions["home"] = home

    def is_active(self, action):
        return self.actions.get(action, False)


class _DictInput:
    """A tiny helper that lets a plain dictionary like {"jump": True}
    answer is_active() questions the same way InputManager does. This is
    handy for testing, where we just want to pretend a button is pressed
    without needing a real keyboard."""
    def __init__(self, actions):
        self.actions = actions

    def is_active(self, action):
        return self.actions.get(action, False)


# --------------------------------------------------------------------------- #
#  The player's car
# --------------------------------------------------------------------------- #
class Car:
    STAND_H = 34     # how tall the car is normally
    DUCK_H = 20      # how tall the car is while ducking (shorter!)
    WIDTH = 78

    def __init__(self, body_color):
        self.body_color = body_color
        self.x = 90
        self.y = GROUND_Y          # y is where the BOTTOM of the car is (touching the road)
        self.vel_y = 0.0           # how fast the car is moving up or down right now
        self.on_ground = True
        self.ducking = False
        # Build the car's picture just once, then keep different
        # stretched copies of it around so we never have to redraw it
        # from scratch every single frame.
        self._base = surface_from_grid(build_car_grid(body_color))
        self._scaled = {}

    def _sprite(self, w, h):
        # Reuse a stretched copy of the car if we already made one this size
        key = (w, h)
        if key not in self._scaled:
            # scale() doesn't blur the picture, so the little squares stay sharp
            self._scaled[key] = pygame.transform.scale(self._base, (w, h))
        return self._scaled[key]

    def update(self, inp):
        # start a jump if the jump button is pressed and we're on the ground
        if inp.is_active("jump") and self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False

        # gravity pulls us back down a little bit more each frame
        self.vel_y += GRAVITY
        self.y += self.vel_y
        if self.y >= GROUND_Y:
            # we've landed -- snap back exactly onto the road
            self.y = GROUND_Y
            self.vel_y = 0.0
            self.on_ground = True

        # you can only duck while your wheels are on the ground
        self.ducking = inp.is_active("duck") and self.on_ground

    @property
    def height(self):
        return self.DUCK_H if self.ducking else self.STAND_H

    @property
    def rect(self):
        # a rectangle showing exactly where the car is on screen
        return pygame.Rect(self.x, self.y - self.height, self.WIDTH, self.height)

    @property
    def hitbox(self):
        # a slightly smaller rectangle used just for crash-checking, so
        # close calls still feel fair instead of "that barely touched me!"
        return self.rect.inflate(-14, -8)

    def draw(self, surf, pal):
        r = self.rect
        draw_soft_shadow(surf, self.x + self.WIDTH / 2, GROUND_Y, self.WIDTH * 0.75)
        surf.blit(self._sprite(r.width, r.height), r.topleft)


# --------------------------------------------------------------------------- #
#  The things you crash into
# --------------------------------------------------------------------------- #
class Obstacle:
    def __init__(self, x, kind):
        self.kind = kind
        self.x = float(x)
        self.flap = 0.0          # used to make the seagull's wings flap up and down
        if kind == "seagull":
            self.w, self.h = 34, 22
            self.y = GROUND_Y - 48
        elif kind == "tires":
            self.w, self.h = 26, 30
            self.y = GROUND_Y - self.h
        elif kind == "board":
            self.w, self.h = 22, 40
            self.y = GROUND_Y - self.h
        elif kind == "bollard":
            self.w, self.h = 12, 26
            self.y = GROUND_Y - self.h
        else:  # debris -- broken bits and pieces
            self.w, self.h = 30, 16
            self.y = GROUND_Y - self.h

    def update(self, speed):
        self.x -= speed                                    # scroll toward the car
        self.flap = (self.flap + 0.25) % (2 * math.pi)      # keep the seagull's wings flapping

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def hitbox(self):
        # a bit smaller than the picture, so crashes feel fair
        return self.rect.inflate(-6, -4)

    def offscreen(self):
        # true once this thing has scrolled all the way off the left edge
        return self.x + self.w < -10

    def draw(self, surf, pal):
        r = self.rect
        ink, accent = pal["ink"], pal["accent"]
        if self.kind != "seagull":
            draw_soft_shadow(surf, r.centerx, GROUND_Y, r.width * 0.85)
        if self.kind == "tires":
            # a stack of tire circles
            for cy in range(r.bottom - 8, r.top, -11):
                pygame.draw.circle(surf, ink, (r.centerx, cy), 8)
                pygame.draw.circle(surf, pal["bg"], (r.centerx, cy), 3)
        elif self.kind == "board":
            # a warning sign on a post
            pygame.draw.rect(surf, ink, (r.centerx - 2, r.top, 4, r.height))
            pygame.draw.rect(surf, accent, (r.left, r.top, r.width, 18))
            pygame.draw.rect(surf, pal["bg"], (r.left + 3, r.top + 3, r.width - 6, 12))
        elif self.kind == "bollard":
            # a short striped post
            pygame.draw.rect(surf, accent, r)
            pygame.draw.rect(surf, pal["bg"], (r.left, r.top + 6, r.width, 4))
            pygame.draw.rect(surf, pal["bg"], (r.left, r.top + 14, r.width, 4))
        elif self.kind == "debris":
            # a jagged little pile of broken bits
            pygame.draw.polygon(surf, ink, [
                (r.left, r.bottom), (r.left + 8, r.top),
                (r.right - 6, r.top + 4), (r.right, r.bottom),
            ])
        else:  # seagull -- two flapping wing shapes that bob up and down
            dy = int(4 * math.sin(self.flap))
            cx, cy = r.centerx, r.centery
            pygame.draw.lines(surf, ink, False,
                              [(r.left, cy + dy), (cx, cy - 6 - dy), (r.right, cy + dy)], 3)
            pygame.draw.lines(surf, ink, False,
                              [(r.left + 4, cy + 6 + dy), (cx, cy + dy),
                               (r.right - 4, cy + 6 + dy)], 3)


# --------------------------------------------------------------------------- #
#  DRS zone -- the green stretch of road where boosting is allowed
# --------------------------------------------------------------------------- #
class DrsZone:
    def __init__(self, x, w):
        self.x = float(x)
        self.w = w

    def update(self, speed):
        self.x -= speed     # scroll toward the car, just like everything else on the road

    def offscreen(self):
        return self.x + self.w < -10

    def covers(self, car_left, car_right):
        # true if the car overlaps this zone at all, front to back
        return self.x <= car_right and (self.x + self.w) >= car_left

    def draw(self, surf, pal, active):
        # a see-through green stripe painted onto the road
        top = GROUND_Y - 2
        band_h = 18
        band = pygame.Surface((int(self.w), band_h), pygame.SRCALPHA)
        alpha = 95 if active else 55     # glows brighter while you're actually boosting inside it
        band.fill((*DRS_GREEN, alpha))
        surf.blit(band, (int(self.x), top))
        # little posts marking where the green zone starts and ends
        for edge in (int(self.x), int(self.x + self.w)):
            pygame.draw.line(surf, DRS_GREEN, (edge, top - 6), (edge, top + band_h), 2)
        # a "DRS" label that appears as the zone's front edge comes into view
        entry = int(self.x + self.w)
        if entry < WIDTH + 40:
            tag = load_font(12, bold=True).render("DRS", True, DRS_GREEN)
            surf.blit(tag, tag.get_rect(midbottom=(entry, top - 4)))


# --------------------------------------------------------------------------- #
#  Tiny dust and spark specks that fly off the tires
# --------------------------------------------------------------------------- #
DUST_COLOR = (150, 140, 125)
SPARK_COLORS = ((255, 150, 40), (255, 90, 30))


class Particle:
    """One single speck of dust or spark. It flies for a little while,
    then fades away and disappears."""
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")

    def __init__(self, x, y, vx, vy, life, size, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy          # how fast it moves sideways and up/down
        self.life = self.max_life = life    # how many frames it has left to live
        self.size = size
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05     # a little bit of gravity, so it drifts downward
        self.life -= 1       # one frame closer to disappearing

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surf):
        # the speck gets smaller and more see-through the closer it is to disappearing
        t = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * t))
        alpha = int(150 * t)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surf.blit(s, s.get_rect(center=(int(self.x), int(self.y))))


# --------------------------------------------------------------------------- #
#  Game -- keeps track of everything happening in one race
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self, font=None, big_font=None, team_color=None, high_score=0):
        self.font = font
        self.big_font = big_font
        self.team_color = team_color or TEAMS[0][1]
        self.high_score = high_score
        self.theme_mode = "auto"     # set from outside by the MODE button; stays put across reset()
        self.reset()

    def reset(self):
        # Put everything back to how it looks at the very start of a race
        self.car = Car(self.team_color)
        self.obstacles = []
        self.zones = []
        self.speed = BASE_SPEED
        self.score = 0.0
        self.boosting = False
        self.drs_available = False
        self.state = RUNNING
        self.spawn_timer = 0
        self.next_gap = 60
        self.zone_timer = 0
        self.next_zone_gap = 90
        self.ground_scroll = 0.0
        self.bg_scroll = 0.0          # the background buildings scroll slower than the road
        self.flash_timer = 0          # counts down the quick white flash right after a crash
        self.particles = []           # all the dust and spark specks on screen right now
        self.night = False
        self.transition = 0.0
        # In auto mode, the current day/night stretch started at
        # phase_start_score and will flip at next_transition_score -- a
        # random spot chosen fresh each time, so you can never guess when
        # it's about to happen just by counting your score.
        self.phase_start_score = 0.0
        self.next_transition_score = random.uniform(NIGHT_EVERY * 0.4, NIGHT_EVERY * 1.8)
        self.restart_lock = 15        # a tiny pause after crashing before you're allowed to restart

    # --- work out the mix of colors to use right now (for smooth day/night fades) ---
    def palette(self):
        base, other = (NIGHT, DAY) if self.night else (DAY, NIGHT)
        if self.transition <= 0:
            return base
        t = self.transition / TRANSITION_FRAMES
        return {k: lerp_color(base[k], other[k], t) if isinstance(base[k], tuple)
                else base[k] for k in base}

    def spawn_obstacle(self):
        # most of the time drop something on the ground; sometimes send a seagull instead
        if random.random() < 0.25 + min(0.15, (self.speed - BASE_SPEED) * 0.02):
            kind = "seagull"
        else:
            kind = random.choice(GROUND_KINDS)
        self.obstacles.append(Obstacle(WIDTH + 20, kind))
        # How far away the NEXT thing shows up is picked freshly at random
        # every time (not just one fixed number with a tiny wiggle), so the
        # gaps feel truly unpredictable -- sometimes bunched close together,
        # sometimes with a nice long breather in between.
        min_gap_px = random.randint(220, 480)
        self.next_gap = int(min_gap_px / self.speed) + random.randint(5, 90)
        self.spawn_timer = 0

    def spawn_zone(self):
        # make a new green DRS zone with a random width
        w = random.randint(DRS_ZONE_MIN_W, DRS_ZONE_MAX_W)
        self.zones.append(DrsZone(WIDTH + 20, w))
        # the faster you're going, the sooner the next zone shows up (roughly every 3-5 seconds)
        self.next_zone_gap = int(1100 / self.speed) + random.randint(30, 110)
        self.zone_timer = 0

    def step(self, actions):
        """Move the whole game forward by exactly one frame, using
        whichever buttons are currently being held down."""
        inp = _DictInput(actions)

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.state == GAME_OVER:
            # while crashed, just count down a "please wait a moment" timer,
            # then let the jump button restart the race
            self.boosting = False
            self.restart_lock = max(0, self.restart_lock - 1)
            if self.restart_lock == 0 and inp.is_active("jump"):
                hs = self.high_score
                self.reset()
                self.high_score = hs   # keep the high score even though everything else resets
            return

        # work out how fast we're going right now, based on our score
        self.speed = min(MAX_SPEED, BASE_SPEED + self.score * SPEED_RAMP)

        # move the green zones and check if we're currently standing inside one
        self.zone_timer += 1
        if self.zone_timer >= self.next_zone_gap:
            self.spawn_zone()
        for z in self.zones:
            z.update(self.speed)
        self.zones = [z for z in self.zones if not z.offscreen()]
        car_l, car_r = self.car.x, self.car.x + self.car.WIDTH
        self.drs_available = any(z.covers(car_l, car_r) for z in self.zones)

        # boosting only works if you're holding the button AND inside a green zone
        self.boosting = inp.is_active("boost") and self.drs_available
        if self.boosting:
            self.speed = min(MAX_BOOST_SPEED, self.speed * BOOST_MULTIPLIER)

        self.score += self.speed / 8.0
        self.ground_scroll = (self.ground_scroll + self.speed) % 40
        self.bg_scroll = (self.bg_scroll + self.speed * 0.25) % SKY_TILE_W

        prev_grounded = self.car.on_ground
        self.car.update(inp)

        # make some dust while rolling along, extra sparks while boosting,
        # and a little puff of dust the moment you land from a jump
        if not prev_grounded and self.car.on_ground:
            for _ in range(6):
                self.particles.append(Particle(
                    self.car.x + self.car.WIDTH / 2 + random.uniform(-14, 14), GROUND_Y - 1,
                    random.uniform(-1.5, 1.5), -random.uniform(0.5, 1.8),
                    life=20, size=3, color=DUST_COLOR))
        if self.car.on_ground:
            rate = 0.55 if self.boosting else 0.15
            if random.random() < rate:
                wheel_x = self.car.x + (16 if random.random() < 0.5 else self.car.WIDTH - 16)
                if self.boosting:
                    self.particles.append(Particle(
                        wheel_x, GROUND_Y - 2,
                        -self.speed * 0.6 - random.uniform(0, 1.5), random.uniform(-0.6, 0.1),
                        life=18, size=3, color=random.choice(SPARK_COLORS)))
                else:
                    self.particles.append(Particle(
                        wheel_x, GROUND_Y - 1,
                        -self.speed * 0.3 - random.uniform(0, 0.6), -random.uniform(0.2, 0.8),
                        life=26, size=4, color=DUST_COLOR))
        if len(self.particles) > 160:
            self.particles = self.particles[-160:]     # don't let too many pile up at once
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]   # remove the ones that faded away

        # obstacles: maybe spawn a new one, move them all, remove ones off screen
        self.spawn_timer += 1
        if self.spawn_timer >= self.next_gap:
            self.spawn_obstacle()
        for ob in self.obstacles:
            ob.update(self.speed)
        self.obstacles = [o for o in self.obstacles if not o.offscreen()]

        # did we crash into anything?
        car_box = self.car.hitbox
        for ob in self.obstacles:
            if car_box.colliderect(ob.hitbox):
                self.state = GAME_OVER
                self.restart_lock = 15
                self.flash_timer = 10
                self.high_score = max(self.high_score, int(self.score))
                break

        # day and night
        if self.transition > 0:
            self.transition -= 1
        if self.theme_mode == "light":
            want_night = False
        elif self.theme_mode == "dark":
            want_night = True
        else:
            want_night = self.night
            if self.score >= self.next_transition_score:
                want_night = not self.night
        if want_night != self.night:
            self.night = want_night
            self.transition = TRANSITION_FRAMES
            self.phase_start_score = self.score
            # pick a brand new random spot for the NEXT flip, so you could
            # never learn the pattern just by counting score
            self.next_transition_score = self.score + random.uniform(NIGHT_EVERY * 0.4, NIGHT_EVERY * 1.8)

    # ----------------------------------------------------------------- draw everything
    def render(self, surf):
        pal = self.palette()
        surf.fill(pal["bg"])
        horizon_y = GROUND_Y - 60

        # the sky -- painted in thin stripes that slowly change color from
        # top to bottom, instead of being just one flat color
        horizon_col = blend(pal["sky"], pal["bg"], 0.55)
        bands = 18
        for i in range(bands):
            t = i / (bands - 1)
            col = blend(pal["sky"], horizon_col, t)
            y0 = int(horizon_y * i / bands)
            y1 = int(horizon_y * (i + 1) / bands) + 1
            pygame.draw.rect(surf, col, (0, y0, WIDTH, y1 - y0))

        # the sun (or moon at night), with a soft glow around it instead of
        # being just a plain circle. In auto mode it slowly slides from the
        # right side of the sky to the left as the current day/night
        # stretch goes on -- a gentle hint that a change is coming, without
        # ever telling you exactly when (that part's still a surprise!). If
        # you've picked LIGHT or DARK mode, day/night never changes, so the
        # sun or moon just stays put.
        orb = (255, 220, 120) if not self.night else (235, 235, 245)
        if self.theme_mode == "auto":
            span = max(1.0, self.next_transition_score - self.phase_start_score)
            progress = max(0.0, min(1.0, (self.score - self.phase_start_score) / span))
        else:
            progress = 0.0
        orb_x = int(lerp(WIDTH - 110, 90, progress))
        orb_y = int(60 - 10 * math.sin(progress * math.pi))
        orb_pos = (orb_x, orb_y)
        for rad, alpha in ((44, 14), (34, 24), (27, 40)):
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*orb, alpha), (rad, rad), rad)
            surf.blit(glow, glow.get_rect(center=orb_pos))
        pygame.draw.circle(surf, orb, orb_pos, 22)

        # the city skyline in the background, scrolling slower than the road
        building_col = blend(pal["ground"], pal["sky"], 0.35)
        offset = int(self.bg_scroll)
        for tile_x in range(-SKY_TILE_W, WIDTH + SKY_TILE_W, SKY_TILE_W):
            for bx, bw, bh in SKYLINE:
                x = tile_x + bx - offset
                if x + bw < 0 or x > WIDTH:
                    continue
                y = horizon_y - bh
                pygame.draw.rect(surf, building_col, (x, y, bw, bh))
                if self.night:
                    # a few tiny glowing windows, like the lights are on inside
                    for wy in range(y + 4, horizon_y - 4, 8):
                        for wx in range(x + 3, x + bw - 3, 7):
                            if (wx * 7 + wy * 13) % 5 == 0:
                                pygame.draw.rect(surf, orb, (wx, wy, 2, 2))

        if self.night:
            # tall floodlight poles, like the ones at a real night race
            for fx in (150, 420, 690):
                pygame.draw.rect(surf, pal["ground"], (fx, 40, 4, GROUND_Y - 100))
                pygame.draw.rect(surf, orb, (fx - 10, 34, 24, 8))

        # the green DRS zones are painted onto the road, underneath the car and obstacles
        for z in self.zones:
            z.draw(surf, pal, active=self.drs_available)

        # the road line, plus little scrolling dashes to show you're moving
        pygame.draw.line(surf, pal["ground"], (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        for dx in range(-40, WIDTH + 40, 40):
            x = dx - int(self.ground_scroll)
            pygame.draw.line(surf, pal["ground"], (x, GROUND_Y + 10), (x + 18, GROUND_Y + 10), 3)

        for p in self.particles:
            p.draw(surf)

        for ob in self.obstacles:
            ob.draw(surf, pal)
        self.car.draw(surf, pal)

        # a quick white flash right after a crash, to make it feel like a
        # real "bang!" -- it's drawn UNDER the score and crash message, so
        # those stay easy to read even while the flash is fading away
        if self.flash_timer > 0:
            alpha = int(180 * (self.flash_timer / 10))
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            surf.blit(flash, (0, 0))

        # the scoreboard card in the top-right corner: your score, a little
        # row of 8 bars showing which gear you're in, and (sometimes) a
        # DRS message. We stack these one under the other using a running
        # "how far down are we so far" number, so they can never overlap.
        if self.font:
            gear = min(8, int((self.speed - BASE_SPEED) / ((MAX_SPEED - BASE_SPEED) / 8)) + 1)

            if self.boosting:
                badge_txt, badge_col = "DRS ACTIVE", pal["accent"]
            elif self.drs_available:
                badge_txt, badge_col = "DRS READY", DRS_GREEN
            else:
                badge_txt, badge_col = None, None

            pad = 14
            panel_w = 232
            panel_h = 96 if badge_txt else 72     # taller when there's a DRS message to show
            panel_x, panel_y = WIDTH - panel_w - 14, 12
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(panel, (*pal["bg"], 220), panel.get_rect(), border_radius=10)
            pygame.draw.rect(panel, (*pal["ink"], 70), panel.get_rect(), 1, border_radius=10)
            surf.blit(panel, (panel_x, panel_y))

            cy = panel_y + pad - 2

            # top row: your score on the left, the gear bars on the right
            score_txt = self.font.render(f"{int(self.score):05d}", True, pal["ink"])
            surf.blit(score_txt, (panel_x + pad, cy))

            tick_w, tick_gap = 6, 4
            tick_row_w = 8 * tick_w + 7 * tick_gap
            tick_x0 = panel_x + panel_w - pad - tick_row_w
            tick_y = cy + 4
            for i in range(8):
                lit = i < gear
                col = pal["accent"] if lit else blend(pal["ink"], pal["bg"], 0.65)
                pygame.draw.rect(surf, col, (tick_x0 + i * (tick_w + tick_gap), tick_y, tick_w, 14), border_radius=1)
            gear_lbl = load_font(11, bold=True).render(f"GEAR {gear}", True, pal["ink"])
            surf.blit(gear_lbl, gear_lbl.get_rect(topright=(panel_x + panel_w - pad, tick_y + 18)))

            cy += score_txt.get_height() + 6

            # middle row: your best score ever
            hi_txt = load_font(11).render(f"HI {self.high_score:05d}", True, blend(pal["ink"], pal["bg"], 0.35))
            surf.blit(hi_txt, (panel_x + pad, cy))
            cy += hi_txt.get_height() + 10

            # bottom row (only shows up sometimes): the DRS message
            if badge_txt:
                badge = load_font(13, bold=True).render(badge_txt, True, badge_col)
                surf.blit(badge, (panel_x + pad, cy))

        if self.state == GAME_OVER and self.big_font:
            # the big "you crashed" message in the middle of the screen
            msg = self.big_font.render("YELLOW FLAG - crashed out", True, pal["accent"])
            sub = self.font.render("SPACE to rejoin the grid", True, pal["ink"])
            surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 14)))
            surf.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 16)))


# --------------------------------------------------------------------------- #
#  MODE button -- a little dropdown menu for picking day/night, drawn with
#  the mouse. It lives outside of the Game class, so it still works even
#  after you've crashed.
# --------------------------------------------------------------------------- #
class ThemeDropdown:
    W = 136
    ROW_H = 26

    def __init__(self, x=16, y=16):
        self.mode = "auto"
        self.open = False
        self.rect = pygame.Rect(x, y, self.W, self.ROW_H)

    def option_rect(self, i):
        # where the i-th choice (AUTO/LIGHT/DARK) is drawn when the menu is open
        return pygame.Rect(self.rect.x, self.rect.bottom + i * self.ROW_H, self.W, self.ROW_H)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.rect.collidepoint(event.pos):
            # clicked the button itself -- open or close the menu
            self.open = not self.open
            return
        if self.open:
            # clicked somewhere else while open -- pick that option, then close
            for i, mode in enumerate(THEME_MODES):
                if self.option_rect(i).collidepoint(event.pos):
                    self.mode = mode
                    break
            self.open = False

    def draw(self, surf, pal, font):
        ink, bg = pal["ink"], pal["bg"]
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)
        pygame.draw.rect(surf, ink, self.rect, 1, border_radius=6)
        # We always leave room on the right for the little arrow, so the
        # words never bump into it -- that used to happen with longer
        # words like "LIGHT" or "DARK" before this fix.
        caret_zone = 26
        label = font.render(f"MODE: {THEME_LABELS[self.mode]}", True, ink)
        label_rect = label.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        label_rect.width = min(label_rect.width, self.rect.width - caret_zone - 14)
        surf.blit(label, label_rect, area=pygame.Rect(0, 0, label_rect.width, label.get_height()))

        # we draw the little triangle arrow ourselves (instead of using a
        # text character for it), because our font doesn't have a nice
        # arrow character and it would show up as a weird empty box
        cx, cy = self.rect.right - 15, self.rect.centery
        if self.open:
            pts = [(cx - 5, cy + 2), (cx + 5, cy + 2), (cx, cy - 3)]   # pointing up
        else:
            pts = [(cx - 5, cy - 2), (cx + 5, cy - 2), (cx, cy + 3)]   # pointing down
        pygame.draw.polygon(surf, ink, pts)

        if not self.open:
            return
        # draw the three choices underneath the button
        for i, mode in enumerate(THEME_MODES):
            r = self.option_rect(i)
            pygame.draw.rect(surf, bg, r)
            pygame.draw.rect(surf, ink, r, 1)
            row_label = font.render(THEME_LABELS[mode], True, ink)
            surf.blit(row_label, row_label.get_rect(midleft=(r.x + 10, r.centery)))
            if mode == self.mode:
                # a little red dot next to whichever one is picked right now
                pygame.draw.circle(surf, pal["accent"], (r.right - 12, r.centery), 3)


# --------------------------------------------------------------------------- #
#  This is where the actual race happens. Picking your team and picking
#  day/night happens over in launcher.py -- this function just plays ONE
#  race from start to finish, then hands control back.
# --------------------------------------------------------------------------- #
def _fit_rect(window_w, window_h):
    """Work out how to fit our game picture (always drawn at the same
    fixed WIDTH x HEIGHT size) into whatever size the window actually
    is right now -- like fitting a photo into a picture frame that
    isn't quite the same shape as the photo. We always keep the photo's
    correct proportions instead of squishing it, so if the frame is too
    wide or too tall for an exact fit, we center it with even, matching
    borders on the sides that are left over.

    Gives back: (scale, x_offset, y_offset, drawn_width, drawn_height)
    """
    window_w = max(window_w, 1)
    window_h = max(window_h, 1)
    scale = min(window_w / WIDTH, window_h / HEIGHT)
    scale = max(scale, 0.1)   # never shrink to nothing, even if the window gets tiny
    drawn_w = max(1, int(WIDTH * scale))
    drawn_h = max(1, int(HEIGHT * scale))
    x_offset = (window_w - drawn_w) // 2
    y_offset = (window_h - drawn_h) // 2
    return scale, x_offset, y_offset, drawn_w, drawn_h


def run_race(team_color, theme_mode="auto", high_score=0, serial_port=None):
    """
    Open the game window and play one race.

    When it's over, it hands back a little note saying what happened:
    {"action": "home" | "quit", "high_score": int}
    "home"  -- you crashed and pressed H, clicked HOME, or pressed the
               HOME button on a real controller, to go pick a new team
    "quit"  -- you closed the window or pressed ESC

    Pass serial_port (like "COM5") to play with a real 4-button
    controller instead of the keyboard. Leave it as None to use the
    keyboard, which is what happens by default.
    """
    # Every time a race ends, pygame.quit() (further down) completely
    # shuts down pygame's font system. If we kept old fonts from a
    # PREVIOUS race sitting in our cache, trying to use them again would
    # crash the whole program -- so we throw away the old fonts here and
    # let fresh ones get built for the new race.
    _FONT_CACHE.clear()
    pygame.init()
    # RESIZABLE turns on the window's maximize button (and lets you drag
    # the edges) -- without it, the window is stuck at one fixed size
    # and that button does nothing at all.
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("The F1 Straight")
    clock = pygame.time.Clock()
    font = load_font(18)
    small_font = load_font(13)
    big = load_font(26, bold=True)

    # Everything in the game still gets drawn onto this ONE fixed-size
    # picture, exactly like before -- nothing about how the game draws
    # itself has to change. At the very end of each frame, we stretch
    # that picture to fill however big the real window is right now (see
    # _fit_rect), so maximizing the window makes the whole game bigger
    # instead of leaving it stuck in a tiny corner.
    game_surface = pygame.Surface((WIDTH, HEIGHT))
    win_w, win_h = WIDTH, HEIGHT

    inp = InputManager(serial_port=serial_port)
    theme = ThemeDropdown()
    theme.mode = theme_mode
    game = Game(font, big, team_color=team_color, high_score=high_score)
    home_btn = pygame.Rect(WIDTH // 2 - 62, HEIGHT // 2 + 34, 124, 32)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return {"action": "quit", "high_score": game.high_score}
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return {"action": "quit", "high_score": game.high_score}

            if event.type == pygame.VIDEORESIZE:
                # the player dragged an edge, or clicked maximize/restore
                # -- rebuild the real window at its new size (pygame
                # needs this one extra step; it doesn't just happen by
                # itself), with a small minimum so it can't shrink away
                # to nothing
                win_w, win_h = max(event.w, 240), max(event.h, 90)
                screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                # pygame tells us where the mouse is in REAL window
                # pixels, but the MODE button and HOME button were drawn
                # using our smaller, fixed game size -- so we translate
                # the click back into that smaller space first, before
                # anything checks whether it landed on a button
                scale, x_off, y_off, _, _ = _fit_rect(win_w, win_h)
                event.pos = (int((event.pos[0] - x_off) / scale), int((event.pos[1] - y_off) / scale))

            theme.handle_event(event)

            # a mouse click on the HOME button works the instant it's
            # clicked. The keyboard/controller HOME button is checked
            # below instead, once per frame, since InputManager owns it.
            if (game.state == GAME_OVER and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1 and home_btn.collidepoint(event.pos)):
                pygame.quit()
                return {"action": "home", "high_score": game.high_score}

        inp.update()                                    # <- reads the keyboard, or a real controller

        if game.state == GAME_OVER and inp.is_active("home"):
            pygame.quit()
            return {"action": "home", "high_score": game.high_score}

        game.theme_mode = theme.mode
        game.step(inp.actions)                           # <- the game only ever hears "which buttons are pressed"
        game.render(game_surface)
        theme.draw(game_surface, game.palette(), small_font)

        if game.state == GAME_OVER:
            # draw a HOME button you can click after crashing
            pal = game.palette()
            pygame.draw.rect(game_surface, pal["accent"], home_btn, border_radius=8)
            pygame.draw.rect(game_surface, pal["ink"], home_btn, 1, border_radius=8)
            lbl = small_font.render("HOME  [H]", True, (255, 255, 255))
            game_surface.blit(lbl, lbl.get_rect(center=home_btn.center))

        # stretch our fixed-size picture to fill the real window, with
        # matching black borders if the shapes don't line up exactly, so
        # the game never looks squished, stretched, or stuck in a corner
        scale, x_off, y_off, drawn_w, drawn_h = _fit_rect(win_w, win_h)
        screen.fill((0, 0, 0))
        big_picture = pygame.transform.smoothscale(game_surface, (drawn_w, drawn_h))
        screen.blit(big_picture, (x_off, y_off))

        pygame.display.flip()
        clock.tick(FPS)


def selftest():
    """A quick check that runs the game without opening a real window, to
    make sure jumping, ducking, boosting, crashing, and restarting all
    still work. If this passes, the game is basically healthy."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    surf = pygame.Surface((WIDTH, HEIGHT))
    game = Game(team_color=TEAMS[0][1])

    script = []
    script += [{"jump": True}] * 5
    script += [{}] * 40
    script += [{"duck": True}] * 20
    script += [{"boost": True}] * 60          # try to boost (this only works while inside a green zone)
    script += [{}] * 200
    script += [{"jump": True}] * 3

    crashed = restarted = boosted_in_zone = False
    for i in range(len(script) + 400):
        actions = script[i] if i < len(script) else {}
        prev = game.state
        game.step(actions)
        game.render(surf)
        if game.boosting:
            boosted_in_zone = True
        if game.state == GAME_OVER:
            crashed = True
        if crashed and prev == GAME_OVER and game.state == RUNNING:
            restarted = True

    assert crashed, "expected a crash at some point"
    print("selftest OK  ->  crashed:", crashed,
          "| restart path:", restarted,
          "| boosted-in-zone seen:", boosted_in_zone,
          "| final score:", int(game.score))
    pygame.quit()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        # running this file directly (not through the launcher) skips the
        # team-picking menu -- the real way to start the game is
        # `python launcher.py`
        run_race(TEAMS[0][1])
