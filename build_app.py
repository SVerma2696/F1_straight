"""
build_app.py -- turn this game into one downloadable app file
================================================================
This script uses a tool called PyInstaller to squish the whole game
(all the Python code, plus the Orbitron font) into a single file that
someone can download and just double-click to play -- they don't need
to install Python or any of our other dependencies first.

How to use it
-------------
1. Install the extra tool this script needs (only needed for BUILDING
   the app, not for playing it from source):
       pip install pyinstaller
2. Run this script on the SAME kind of computer you want the app to
   run on -- a Windows build only works on Windows, a Mac build only
   works on Mac, and a Linux build only works on Linux. You can't
   build a Windows app from a Mac, or the other way around.
       python build_app.py
3. Look inside the new "dist" folder for your finished app.

(If you just want to play the game from the source code, you don't
need this file at all -- just run `python launcher.py` like normal.)

Our GitHub Actions workflow (.github/workflows/release.yml) runs this
same script automatically on Windows, Mac, and Linux whenever we tag a
new version, so all three downloads are always kept up to date.
"""
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# "Windows", "Darwin" (that's the technical name for macOS), or "Linux"
SYSTEM = platform.system()

# What we'll call the finished app, so it's obvious which download is
# for which computer once all three sit together in a GitHub Release
APP_NAMES = {
    "Windows": "F1Straight-windows",
    "Darwin": "F1Straight-macos",
    "Linux": "F1Straight-linux",
}
APP_NAME = APP_NAMES.get(SYSTEM, "F1Straight")

# PyInstaller's --add-data option needs the "copy this" and "put it
# here" paths joined together, but with a DIFFERENT joining character
# depending on the computer: a semicolon on Windows, a colon everywhere
# else. Getting this wrong is a very common mistake, so we pick the
# right one automatically instead of making anyone remember it.
DATA_SEP = ";" if SYSTEM == "Windows" else ":"
font_folder = HERE / "assets" / "fonts"
add_data = f"{font_folder}{DATA_SEP}assets/fonts"

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",          # squish everything into just ONE file
    "--windowed",          # don't show a black console window behind the game
    "--noconfirm",         # don't stop and ask before overwriting an old build
    "--name", APP_NAME,
    "--collect-all", "customtkinter",   # CustomTkinter needs its own theme files bundled too
    "--add-data", add_data,
    str(HERE / "launcher.py"),
]

print("Building with:", " ".join(cmd))
result = subprocess.run(cmd, cwd=HERE)
if result.returncode != 0:
    print("\nSomething went wrong -- scroll up to see what PyInstaller said.")
    sys.exit(result.returncode)

print(f"\nAll done! Your app is in the 'dist' folder, named '{APP_NAME}'.")
