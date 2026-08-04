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
│   ├── dependabot.yml                        # Weekly automated dependency-update checks
│   └── workflows/
│       ├── codeql.yml                        # Automated code-scanning for security issues
│       └── release.yml                       # Builds + publishes the 3 downloads above
├── assets/
│   └── fonts/
│       ├── OFL.txt                          # License for the Orbitron font
│       └── Orbitron-Variable.ttf             # The scoreboard's font
├── firmware/
│   └── endless_straight_controller.ino       # Optional 4-button ESP32 controller sketch
├── tests/
│   ├── conftest.py                           # Shared pytest setup (headless pygame, import path)
│   ├── test_controller.py                    # InputManager: keyboard + fake-serial parsing
│   ├── test_drs.py                           # DRS zones and boosting
│   ├── test_gravel.py                        # Gravel traps: slowdown, recovery, jump-dodge
│   ├── test_pause.py                         # Pausing mid-race
│   ├── test_persistence.py                   # High score, last setup, leaderboard save/load
│   ├── test_resize.py                        # Fitting the game picture into a resized window
│   ├── test_sound.py                         # Procedural sound effects
│   └── test_tracks.py                        # Famous-track background generation
├── .gitignore              # Ignore rules for caches, build junk, and generated files
├── build_app.py             # Packages the game into one downloadable app (see below)
├── game.py                   # The race engine: car, obstacles, input, sound, scoreboard, main loop
├── launcher.py                 # The menu screen: team picker, theme picker, leaderboard
├── LICENSE                       # MIT license
├── pytest.ini                     # Tells pytest where to find the tests/ folder
├── README.md                       # Project documentation
├── requirements.txt                  # Python dependencies (just to play from source)
├── requirements-dev.txt                # Adds PyInstaller and pytest (only needed to build/test)
└── SECURITY.md                           # How to report a security problem
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
* **Procedurally-generated sound** — an engine hum that gets
  higher-pitched as you shift up through the gears, a whoosh when DRS
  kicks in, and a thud on crashing, all built out of math with
  `pygame.mixer` — no sound files, same idea as the car sprite.
* **Pause anytime** — press `P` mid-race (or hold JUMP + HOME together
  on a controller) to freeze the race, dim the screen, and show PAUSED.
* **Mute or turn the volume down** — press `M` any time to mute, or set
  a volume slider in the launcher; your setting is saved for next time.
* **Game-over stats** — crashing shows how many DRS zones you used, how
  many gravel patches you hit, and how long you survived, alongside your score.
* **Standard gamepad support** — plug in an Xbox, PlayStation, or
  Nintendo Switch Pro controller and it just works, right alongside the
  keyboard, no setup needed. (Still separate from the optional
  hand-built ESP32 controller below.)
* **High score, top-5 leaderboard, and your last team/track/mode are
  all saved to disk** — remembered the next time you open the game,
  even after fully closing it.
* **Leaderboard filtering and sorting** — the LEADERBOARD window can
  filter your top 5 races down to one team or track, and sort by score,
  team, or track.
* **Optional hardware controller support** — plug in a physical
  4-button pad built on an **ESP32**, talking to the game over a small
  custom USB-serial protocol, debounced on the firmware side and
  drained-to-newest-line on the Python side so input never lags. The
  launcher **auto-detects** which serial port it's on, instead of
  making you type it in. The game also talks back: an optional LED on
  the controller lights up whenever DRS is ready to use.
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
Skip this entirely to just use the keyboard (or a plugged-in Xbox,
PlayStation, or Switch gamepad, which needs no setup at all).

**Wiring** (4 push buttons + 1 optional LED, on a breadboard with an
ESP32 dev board, like the one in an ELEGOO Super Starter Kit):
* Each button: one leg to GND (the breadboard's ground rail), the
  other leg to GPIO 32 (jump), 33 (duck), 25 (DRS), or 26 (home). No
  resistor needed -- the firmware turns on the pin's internal pull-up.
* Optional DRS-ready LED: GPIO 27 -> a 220Ω resistor -> the LED's long
  leg (anode). The LED's short leg (cathode) -> GND. The resistor here
  IS required, or the LED burns out.
* Don't forget one last wire from the ground rail back to a GND pin on
  the ESP32 itself -- without it, nothing reads correctly.

**Flashing the firmware:**
1. Install the Arduino IDE, then add the ESP32 board package: File ->
   Preferences -> Additional Boards Manager URLs ->
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`,
   then Tools -> Board -> Boards Manager -> search "esp32" -> install.
2. Plug the board in over USB, pick Tools -> Board -> esp32 -> "ESP32
   Dev Module", and Tools -> Port -> the port that shows up (install
   the CP210x USB driver if none appears).
3. Open `firmware/endless_straight_controller.ino` and click Upload.
   If it hangs at "Connecting...", hold the board's BOOT button until
   uploading actually starts -- a common ESP32 quirk, not a problem.
4. Test it: Tools -> Serial Monitor, set the speed to 115200. You
   should see a `0,0,0,0`-style line -- press each button and watch
   its number flip to 1. To test the LED on its own, set the line
   ending to "Newline", type `LED,1` and send it -- the LED should
   light up.

You don't need to know the port's name to actually play -- the
launcher lists connected devices for you automatically.

### 4. Run it
```
python launcher.py
```
*(Pick a team, a day/night mode, and a track (or leave it on RANDOM),
optionally pick your controller's port from the dropdown, then click
START RACE. Your picks are remembered for next time.)*

---

## 🧪 Running the Tests
```
pip install -r requirements-dev.txt
pytest
```
Each mechanic (DRS, gravel, pausing, persistence, sound, the resize
math, controller input, track generation) has its own test file in
`tests/`, running headless (no real window or speakers needed) so it
works the same on any machine, including in CI. This sits alongside
`python game.py --selftest`, which is a quick end-to-end smoke test
rather than a set of isolated, named assertions.

---

## 🖥️ Cross-Platform Notes
This project is developed and tested primarily on Windows, with these
platform differences specifically accounted for in the code:

* **Finding bundled files**: every file the game loads (like the
  Orbitron font) is located relative to `sys._MEIPASS` when running as
  a packaged app, or relative to the script folder otherwise -- both
  paths built with `os.path.join`, so there are no hardcoded `\` or `/`
  separators anywhere.
* **Controller port names**: the launcher auto-detects connected serial
  devices with `serial.tools.list_ports`, so it doesn't matter that
  Windows, macOS, and Linux all name ports differently (`COM5` vs.
  `/dev/tty.usbserial-...` vs. `/dev/ttyUSB0`) -- you just pick one
  from the list.
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
* **Save file location**: running from source, your high score, top-5
  leaderboard, last-used team/track/mode, and volume/mute setting are
  all saved right next to the game files (`high_score.json`, one file,
  several keys).
  Running as a packaged app, it's saved to the same per-user settings
  folder every other app on your OS uses -- `%APPDATA%\TheF1Straight`
  on Windows, `~/Library/Application Support/TheF1Straight` on macOS,
  or `~/.local/share/TheF1Straight` (or `$XDG_DATA_HOME`) on Linux.

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

## 🔒 Security
* **Reporting a problem:** see [SECURITY.md](SECURITY.md) for how to
  report a security issue privately.
* **Code scanning:** [.github/workflows/codeql.yml](.github/workflows/codeql.yml)
  runs CodeQL on every push to `main`, every pull request, and once a
  week on its own, to catch common unsafe coding patterns automatically.
* **Dependency updates:** [.github/dependabot.yml](.github/dependabot.yml)
  checks our Python dependencies and GitHub Actions weekly and opens a
  pull request by itself when a newer version is available.
* **Dependabot alerts** and **private vulnerability reporting** are
  turned on for this repo under Settings -> Code security and
  analysis -- those are one-time toggles in GitHub's own settings
  page, not something a file in this repo can turn on by itself.

---

## 🔌 System Integrations (Data Flow)
### Input
```
Keyboard keys              -> InputManager._poll_keyboard -> is_active("jump", "duck", "boost", "home")
Xbox/PlayStation/Switch pad -> InputManager._poll_gamepad  -> is_active("jump", "duck", "boost", "home")
ESP32 serial CSV frame     -> InputManager._poll_serial    -> is_active("jump", "duck", "boost", "home")
```
**Note:** the serial reader always acts on only the newest complete
line and discards any that piled up behind it, so a busy frame can
never build up input lag. All three input sources are always checked
together and merged (any one of them can trigger an action) --
**nothing ever turns the keyboard off**, even when a serial controller
is connected. That matters because the launcher auto-picks the first
serial port it finds, which might not actually be a game controller;
if connecting to some unrelated device ever silenced the keyboard, the
whole game would look "broken" with no error message at all.

### Output (game -> controller)
```
game.py: Game.drs_available  -> InputManager.send_drs_ready(ready) -> "LED,1\n" / "LED,0\n" over serial
firmware: readFeedbackFromGame() -> lights (or turns off) the optional DRS-ready LED
```
The serial link is two-way: the controller tells the game which
buttons are pressed, and the game tells the controller whether DRS is
ready right now, so an optional LED can echo the on-screen badge.
`send_drs_ready` only actually writes a message when the ready/not-ready
state just changed, so it doesn't spam the USB cable every frame.
**Both directions are non-blocking** (`timeout=0` for reads,
`write_timeout=0` for writes) -- without the write side of that, picking
an unrelated real serial port (a modem, a Bluetooth COM port, anything
that isn't actually our controller) could freeze the whole game
waiting forever for that device to acknowledge a write it was never
going to answer.

### Menu ⇄ Race
```
launcher.py: Launcher._start()  -> game.run_race(team_color, theme_mode, high_score, serial_port, track)
game.py: run_race()             -> returns {"action": "home" | "quit", "high_score": int, "score": int}
```
The menu hides itself, waits for that one function call to return, then
either shows itself again (`"home"`) or closes (`"quit"`). That's the
entire connection between the two layers. The returned `"score"` (this
race's own result, separate from `"high_score"`, your best ever) is
what the launcher hands to `add_leaderboard_entry()` afterward.

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
  tolerate boot noise and dropped/garbled frames without crashing, now
  **bidirectional**: the desktop app also sends short text commands
  back to the firmware to drive an LED, parsed without ever blocking
  the firmware's own button-reading loop.
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
* **Persistent local state** — the high score, top-5 leaderboard,
  last-used team/track/mode, and volume/mute setting are all read from
  and written to a small JSON file in a proper per-user data directory
  when running as a packaged app (never the app's own folder, which may
  not be writable, and never the temporary PyInstaller extraction
  folder, which is wiped after the app closes).
* **Procedural audio synthesis** — every sound effect is a raw PCM
  waveform built sample-by-sample with `math.sin` and friends, wrapped
  in a `pygame.mixer.Sound(buffer=...)`, instead of loaded from a file
  -- the same "generate it, don't ship it" philosophy as the car sprite.
* **Automated test suite** — `pytest` tests in `tests/`, each isolating
  and asserting on one mechanic at a time (DRS, gravel, pausing,
  persistence, sound, resize math, controller parsing, track
  generation), run headlessly so they pass the same way locally and in CI.
* **Cross-brand gamepad support** — one set of button numbers works for
  Xbox, PlayStation, and Nintendo Switch Pro controllers alike, since
  `pygame.joystick` lines them up consistently through SDL's built-in
  controller database instead of needing per-brand code.

---

## 🔧 Requirements
* Python 3.8+ (only if running from source -- not needed for the downloads above)
* `pygame-ce`, `customtkinter`, `pillow` (installed via `requirements.txt`)
* `pyserial` -- only needed if you're using a real hardware controller
* An ESP32 board + 4 push buttons -- optional, only for the hardware controller
* Arduino IDE -- optional, only needed to flash the firmware
* `pyinstaller` (via `requirements-dev.txt`) -- only needed to build the app yourself
* `pytest` (via `requirements-dev.txt`) -- only needed to run the automated tests

---

## 🎓 Credits & Attributions
This is a personal/educational project, not affiliated with or endorsed
by Formula 1, the FIA, or any of the named teams or circuits. Team and
track names referenced in-game are used only as labels for the
procedurally-generated colors/shapes, and are the trademarks of their
respective owners.

* **Font:** [Orbitron](https://github.com/google/fonts/tree/main/ofl/orbitron)
  by Matt McInerney, bundled under the [SIL Open Font License](assets/fonts/OFL.txt).
* **Car sprite, all other visuals, and every sound effect:** generated
  procedurally in code -- no external art or audio assets used.
