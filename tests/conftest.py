"""
conftest.py -- pytest reads this file automatically, before any test
runs. This is where we do the setup EVERY test needs: making pygame run
"headless" (no real window, no real speakers needed) and making sure
Python can find game.py and launcher.py to import them.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame
pygame.init()
