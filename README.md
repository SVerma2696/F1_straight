A pixel-art F1 endless-runner racing game I built to learn game-loop
architecture, hardware-agnostic input design, and CustomTkinter/pygame
integration -- with an optional real 4-button ESP32 controller.

# The F1 Straight🏎️🚥
A pixel-art racing game where your car blasts down an endless straight
that keeps accelerating through the gears. It's split into a
**CustomTkinter** menu layer and a **pygame** real-time race engine,
connected through one function call, with an **`InputManager`**
abstraction clean enough that a real 4-button **ESP32** hardware
controller drops in without touching a single line of game logic. Runs
on **Windows, macOS, and Linux**, and can be packaged into a
double-click download for each with **PyInstaller**.

---

## 📥 Download the App (no Python needed)
Grab a ready-to-run download from the
[Releases page](https://github.com/SVerma2696/f1_straight/releases) --
pick the one for your computer:

| Your computer | Download | First-time setup |
|---|---|---|
| Windows | `F1Straight-windows.exe` | Just double-click it. Windows SmartScreen may warn about an unrecognized app the first time -- click "More info" then "Run anyway." |
| macOS | `F1Straight-macos` | Right-click (or Control-click) it and choose **Open** the first time, since it isn't signed by an Apple developer account -- macOS Gatekeeper blocks a plain double-click on unsigned apps. |
| Linux | `F1Straight-linux` | Make it runnable first: `chmod +x F1Straight-linux`, then run it with `./F1Straight-linux`. |

Every release is built fresh for all three from the same source code by
[.github/workflows/release.yml](.github/workflows/release.yml), so
they're always in sync with each other.

---

## 📂 Project Structure
```
f1_straight/
├── .github/
│   └── workflows/
│       └── release.yml                      # Builds + publishes the 3 downloads above
├── assets/
│   └── fonts/
│       ├── OFL.txt                          # License for the Orbitron font
│       └── Orbitron-Variable.ttf             # The scoreboard's font
├── firmware/
│   └── endless_straight_controller.ino       # Optional 4-button ESP32 controller sketch
├── .gitignore              # Ignore rules for caches, build junk, and generated files
├── build_app.py             # Packages the game into one downloadable app (see below)
├── game.py                   # The race engine: car, obstacles, input, scoreboard, main loop
├── launcher.py                 # The menu screen: team picker, theme picker, high score
├── LICENSE                       # MIT license
├── README.md                       # Project documentation
├── requirements.txt                  # Python dependencies (just to play from source)
└── requirements-dev.txt                # Adds PyInstaller (only needed to build the app)
```

---

## ⚙️ Features
* Play as any of the **11 current F1 teams**, each with a matching
  **procedurally-generated pixel-art car** livery (no image files --
  the car is built from a color grid at runtime).
* **DRS zones** — hold the boost button inside a scrolling green zone
  for a real speed boost, just like the activation zones on a real circuit.
* **Gravel traps** — sandy patches that slow you down for a bit before
  easing back up to speed; jump over one instead to dodge the penalty.
* **Four famous tracks** — Monza, Monaco, Silverstone, or Suzuka, each
  with its own background shape and color, or leave it on random for a
  surprise every race.
* **Unpredictable day/night cycles** — `AUTO` mode flips at a
  randomized point in your score (never the same gap twice), with the
  sun/moon **visually drifting** across the sky as the only hint a
  change is coming.
* **High score saved to disk** — remembered the next time you open the
  game, even after fully closing it.
* **Optional hardware controller support** — plug in a physical
  4-button pad built on an **ESP32**, talking to the game over a small
  custom USB-serial protocol, debounced on the firmware side and
  drained-to-newest-line on the Python side so input never lags.
* **Two-layer architecture**: a CustomTkinter menu shell hands off to a
  pygame real-time race loop through a single `run_race(...)` call, and
  gets a plain dict back when the race ends.
* A gradient sky, parallax city skyline, glowing sun/moon, tyre-dust and
  DRS-spark particles, a crash-impact flash, and a scoreboard HUD
  rendered with a bundled TTF font.
* Obstacles spawn at randomized distances apart, so the game never
  settles into a predictable rhythm.
* **Resizable, maximizable window** — drag an edge or hit maximize and
  the whole game scales up with you, always keeping its correct
  proportions (matching black borders fill in any leftover space rather
  than stretching or squashing the picture).
* Runs natively on **Windows, macOS, and Linux** -- see the
  cross-platform notes below.

---

## 🚀 Running From Source
### 1. Get the project
```
git clone https://github.com/SVerma2696/f1_straight.git
cd f1_straight
```

### 2. Install dependencies
Make sure you have Python 3.8+ installed, then run:
```
pip install -r requirements.txt
```

### 3. (Optional) Set up a real controller
Flash `firmware/endless_straight_controller.ino` onto an ESP32 with the
Arduino IDE, wire up 4 buttons, and note which USB port it shows up as
-- you'll type that into the launcher in the next step. Skip this
entirely to just use the keyboard.

### 4. Run it
```
python launcher.py
```
*(Pick a team, a day/night mode, and a track (or leave it on RANDOM),
optionally enter your controller's port, then click START RACE.)*

---

## 🖥️ Cross-Platform Notes
This project is developed and tested primarily on Windows, with these
platform differences specifically accounted for in the code:

* **Finding bundled files**: every file the game loads (like the
  Orbitron font) is located relative to `sys._MEIPASS` when running as
  a packaged app, or relative to the script folder otherwise -- both
  paths built with `os.path.join`, so there are no hardcoded `\` or `/`
  separators anywhere.
* **Controller port names**: the launcher shows a different example in
  the CONTROLLER PORT box depending on the detected OS -- `COM5`-style
  on Windows, `/dev/tty.usbserial-...` on macOS, `/dev/ttyUSB0` on Linux.
* **Font fallback**: if the bundled font ever fails to load, the
  fallback list includes a font that's actually likely to be installed
  on each OS (Consolas on Windows, Menlo on macOS, DejaVu Sans Mono on
  most Linux distros).
* **CustomTkinter's `"system"` appearance mode** (light/dark) reads the
  OS theme automatically on Windows and macOS; on some Linux desktop
  environments there's no theme setting for it to detect, so it may
  default to light mode there regardless of your system theme -- pick
  it manually with your desktop's usual dark-mode toggle if that
  matters to you, or override it in `launcher.py`'s
  `ctk.set_appearance_mode(...)` call.
* **The downloadable apps** are unsigned (no Apple/Microsoft developer
  certificate), so macOS and Windows both show a first-run warning --
  see the download table above for how to get past it.
* **High score save location**: running from source, it's saved right
  next to the game files (`high_score.json`). Running as a packaged
  app, it's saved to the same per-user settings folder every other app
  on your OS uses -- `%APPDATA%\TheF1Straight` on Windows,
  `~/Library/Application Support/TheF1Straight` on macOS, or
  `~/.local/share/TheF1Straight` (or `$XDG_DATA_HOME`) on Linux.

---

## 🛠️ Building the App Yourself
```
pip install -r requirements-dev.txt
python build_app.py
```
This uses PyInstaller to produce a single-file app in `dist/`. Build on
the same kind of computer you want the app to run on -- a Windows build
only runs on Windows, and so on; you can't cross-build. Pushing a
version tag (like `v1.0.0`) to GitHub runs this same script on all
three operating systems automatically and publishes the results to the
Releases page -- see `.github/workflows/release.yml`.

**Troubleshooting a failed release build:** if the Actions log shows
`Resource not accessible by integration` (a 403 error) on the last
step, it means this repo's GitHub Actions token defaulted to
read-only. That's fixed by the `permissions: contents: write` line
near the top of the workflow file -- if you ever see this error again,
that's the line to check first.

---

## 🔌 System Integrations (Data Flow)
### Input
```
Keyboard keys           -> InputManager._poll_keyboard -> is_active("jump", "duck", "boost", "home")
ESP32 serial CSV frame  -> InputManager._poll_serial    -> is_active("jump", "duck", "boost", "home")
```
**Note:** the serial reader always acts on only the newest complete
line and discards any that piled up behind it, so a busy frame can
never build up input lag.

### Menu ⇄ Race
```
launcher.py: Launcher._start()  -> game.run_race(team_color, theme_mode, high_score, serial_port)
game.py: run_race()             -> returns {"action": "home" | "quit", "high_score": int}
```
The menu hides itself, waits for that one function call to return, then
either shows itself again (`"home"`) or closes (`"quit"`). That's the
entire connection between the two layers.

---

## 📘 Concepts Demonstrated
* **Hardware-agnostic input abstraction** — the game loop only ever
  asks `is_active("jump")`; it never knows or cares whether the answer
  came from a keyboard or a physical controller over serial.
* **Two-process-in-one-app UI architecture** — a native GUI toolkit
  (CustomTkinter) and a real-time game loop (pygame) sharing one Python
  process, cleanly separated behind a single entry-point function.
* **Procedural sprite generation** — the car is drawn as a grid of
  colors at runtime and recolored per team, instead of loading image files.
* **Serial protocol design** — a compact, debounced, framed CSV
  protocol between microcontroller firmware and a desktop app, built to
  tolerate boot noise and dropped/garbled frames without crashing.
* **Finite-state game loop** — a small `RUNNING` / `GAME_OVER` state
  machine driving restart timers, crash flashes, and score-gated
  day/night transitions.
* **Embedded firmware basics** — debounced digital input, internal
  pull-up resistors, and a fixed-format serial output on an ESP32.
* **Cross-platform packaging** — one PyInstaller script and one GitHub
  Actions matrix build turning the same source into native downloads
  for three different operating systems.
* **Reusable procedural background system** — one scrolling-shape
  generator (rectangles, triangles, or rounded hills, each with its own
  color and sizing) drives all four track themes, instead of needing
  separate hand-drawn art per track.
* **Persistent local state** — the high score is read from and written
  to a small JSON file in a proper per-user data directory when running
  as a packaged app (never the app's own folder, which may not be
  writable, and never the temporary PyInstaller extraction folder,
  which is wiped after the app closes).

---

## 🔧 Requirements
* Python 3.8+ (only if running from source -- not needed for the downloads above)
* `pygame-ce`, `customtkinter`, `pillow` (installed via `requirements.txt`)
* `pyserial` -- only needed if you're using a real hardware controller
* An ESP32 board + 4 push buttons -- optional, only for the hardware controller
* Arduino IDE -- optional, only needed to flash the firmware
* `pyinstaller` (via `requirements-dev.txt`) -- only needed to build the app yourself

---

## 🎓 Credits & Attributions
This is a personal/educational project, not affiliated with or endorsed
by Formula 1, the FIA, or any of the named teams or circuits. Team and
track names referenced in-game are used only as labels for the
procedurally-generated colors/shapes, and are the trademarks of their
respective owners.

* **Font:** [Orbitron](https://github.com/google/fonts/tree/main/ofl/orbitron)
  by Matt McInerney, bundled under the [SIL Open Font License](assets/fonts/OFL.txt).
* **Car sprite and all other visuals:** generated procedurally in code
  -- no external art assets used.
