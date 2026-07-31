"""
The F1 Straight -- launcher (the menu screen)
================================================
This file is the pretty menu you see before you race: pick your team,
pick day or night, then click START RACE. It's built with a toolkit
called CustomTkinter, which is really good at making buttons and menus
look nice.

Once you click START RACE, this file hands things over to game.py, which
runs the actual race. Each file does the job it's best at: this one is
good at menus, game.py is good at fast-moving pictures.

Run it:  python launcher.py
"""
import platform

import customtkinter as ctk
from PIL import Image
import pygame

import game as g

# A real controller's "port name" looks different on each kind of
# computer, so we show a matching example depending on what this
# computer is -- Windows, Mac, or Linux.
_OS_NAME = platform.system()
if _OS_NAME == "Windows":
    _PORT_EXAMPLE = "e.g. COM5"
elif _OS_NAME == "Darwin":   # "Darwin" is the technical name for macOS
    _PORT_EXAMPLE = "e.g. /dev/tty.usbserial-0001"
else:   # Linux and anything else
    _PORT_EXAMPLE = "e.g. /dev/ttyUSB0"

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

TEAM_COLS = 4     # how many team buttons fit in one row


def _hex(color):
    # turn a color like (225, 6, 0) into text like "#e10600" that
    # CustomTkinter understands
    return "#{:02x}{:02x}{:02x}".format(*color)


def _team_preview_image(color, scale=4):
    """Draw the little car picture (borrowed from game.py) and turn it
    into a normal picture file that CustomTkinter can show on a button."""
    pygame.init()
    surf = g.surface_from_grid(g.build_car_grid(color))
    surf = pygame.transform.scale(surf, (g.SPRITE_W * scale, g.SPRITE_H * scale))
    raw = pygame.image.tostring(surf, "RGBA")
    return Image.frombytes("RGBA", surf.get_size(), raw)


# All the text shown on the "HOW TO PLAY" page, one heading + paragraph at a time
INSTRUCTIONS = [
    ("Controls", (
        "SPACE / UP / W" + " " * 4 + "Bunny-hop (jump)\n"
        "DOWN / S" + " " * 10 + "Aero tuck (duck)\n"
        "SHIFT" + " " * 14 + "DRS boost -- only inside a green DRS zone\n"
        "SPACE" + " " * 14 + "Restart after a crash\n"
        "H" + " " * 19 + "After a crash: back to this menu\n"
        "ESC" + " " * 16 + "Quit the race"
    )),
    ("DRS zones", (
        "Scrolling green bands on the track. SHIFT only boosts your speed\n"
        "while the car is inside one -- just like the real activation\n"
        "zones on an F1 circuit. The BOOST/DRS status shows in the HUD."
    )),
    ("Gravel traps", (
        "Sandy-brown patches on the track. Drive through one and you'll\n"
        "slow down for a little while before easing back up to speed --\n"
        "jump over a patch instead to dodge the penalty completely."
    )),
    ("Tracks", (
        "Pick a famous real track from the TRACK menu -- Monza, Monaco,\n"
        "Silverstone, or Suzuka, each with its own background -- or leave\n"
        "it on RANDOM and let the game surprise you."
    )),
    ("Day / night", (
        "In AUTO mode the track flips between day and night at a random\n"
        "point -- never the same gap twice -- so you can't predict it by\n"
        "counting. The sun/moon drifts right-to-left over the course of a\n"
        "phase as a soft visual cue that a change is coming. LIGHT and\n"
        "DARK pin the time of day and stop the drift. The MODE dropdown\n"
        "is also live in the top-left corner during the race."
    )),
    ("Goal", (
        "Survive as long as possible -- hop the ground hazards, duck the\n"
        "swooping seagulls, and beat your high score, which is saved to\n"
        "disk and remembered even after you close the game."
    )),
    ("Controller (optional)", (
        "You can plug in a real 4-button controller instead of using the\n"
        "keyboard. Type its port into the CONTROLLER PORT box on the menu\n"
        "before starting (Windows looks like COM5; Mac and Linux look\n"
        "like a path such as /dev/tty.usbserial-0001 or /dev/ttyUSB0).\n"
        "Leave it blank to just use the keyboard."
    )),
]


class InstructionsWindow(ctk.CTkToplevel):
    """The little pop-up window that shows up when you click "HOW TO PLAY"."""

    def __init__(self, master):
        super().__init__(master)
        self.title("How to play")
        self.geometry("460x920")
        # letting this resize (and its maximize button work) means a
        # bigger window just gives the instructions more breathing room
        # -- nothing breaks, since the text area above already grows to
        # fill whatever space it's given (see "body" below)
        self.resizable(True, True)
        self.minsize(360, 400)
        self.transient(master)   # keeps this window in front of the main menu
        self.grab_set()          # you have to close this before clicking the menu again

        ctk.CTkLabel(self, text="HOW TO PLAY",
                     font=("Segoe UI", 20, "bold")).pack(pady=(20, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        for heading, text in INSTRUCTIONS:
            ctk.CTkLabel(body, text=heading, font=("Segoe UI", 13, "bold"),
                         text_color="#E10600", anchor="w").pack(fill="x", pady=(10, 2))
            ctk.CTkLabel(body, text=text, font=("Consolas", 11), justify="left",
                         anchor="w").pack(fill="x")

        ctk.CTkButton(self, text="CLOSE", width=140, height=36, corner_radius=8,
                      command=self.destroy).pack(pady=18)


class Launcher(ctk.CTk):
    """The main menu window: pick a team, pick a theme, then race."""

    def __init__(self):
        super().__init__()
        self.title("The F1 Straight")
        self.geometry("640x760")
        # lets you maximize (or just drag bigger) the menu window too --
        # the layout stays anchored at the top instead of stretching,
        # but the maximize button now actually does something
        self.resizable(True, True)
        self.minsize(640, 760)

        self.selected = 0          # which team is picked right now (0 = first team)
        self.theme_mode = "auto"
        # load whatever high score was saved from last time you played,
        # so it doesn't reset to zero just because you closed the app
        self.high_score = g.load_high_score()
        self.team_buttons = []
        self._preview_cache = {}   # remembers car pictures we've already built

        self._build_ui()
        self._select(0)

    # ------------------------------------------------------------ building the screen
    def _build_ui(self):
        ctk.CTkLabel(self, text="THE F1 STRAIGHT",
                     font=("Segoe UI", 28, "bold")).pack(pady=(24, 2))
        ctk.CTkLabel(self, text="CHOOSE YOUR TEAM", text_color="#E10600",
                     font=("Segoe UI", 13, "bold")).pack(pady=(0, 16))

        # one button per F1 team, colored to match that team
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=24)
        for i, (name, color) in enumerate(g.TEAMS):
            btn = ctk.CTkButton(
                grid, text=name, width=136, height=44, corner_radius=8,
                fg_color=_hex(color), hover_color=_hex(g.darker(color, 0.75)),
                text_color=("#141414" if g.luminance(color) > 0.6 else "#f5f5f5"),
                border_width=0, border_color="#ffffff",
                command=lambda i=i: self._select(i),
            )
            btn.grid(row=i // TEAM_COLS, column=i % TEAM_COLS, padx=6, pady=6)
            self.team_buttons.append(btn)

        # a row showing a picture of the car you picked, plus the day/night menu
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="x", padx=28, pady=(20, 6))

        preview_frame = ctk.CTkFrame(mid, fg_color="transparent")
        preview_frame.pack(side="left")
        self._preview_label = ctk.CTkLabel(preview_frame, text="")
        self._preview_label.pack(side="left")
        self._name_label = ctk.CTkLabel(preview_frame, text="",
                                         font=("Segoe UI", 17, "bold"))
        self._name_label.pack(side="left", padx=14)

        mode_frame = ctk.CTkFrame(mid, fg_color="transparent")
        mode_frame.pack(side="right")
        ctk.CTkLabel(mode_frame, text="MODE", font=("Segoe UI", 11),
                     text_color="gray60").pack(anchor="e")
        self.mode_menu = ctk.CTkOptionMenu(mode_frame, values=["AUTO", "LIGHT", "DARK"],
                                            command=self._on_mode, width=120)
        self.mode_menu.set("AUTO")
        self.mode_menu.pack()

        # which famous track's background to race at -- RANDOM means "let
        # the game surprise me," which is also what happens if you never
        # touch this menu at all
        ctk.CTkLabel(mode_frame, text="TRACK", font=("Segoe UI", 11),
                     text_color="gray60").pack(anchor="e", pady=(10, 0))
        track_values = ["RANDOM"] + [cfg["label"].upper() for cfg in g.TRACKS.values()]
        self.track_menu = ctk.CTkOptionMenu(mode_frame, values=track_values, width=120)
        self.track_menu.set("RANDOM")
        self.track_menu.pack()

        # a real 4-button controller is optional -- type its port here to
        # use one, or leave it blank to just use the keyboard, which is
        # what happens by default. The example shown changes depending
        # on whether this is Windows, Mac, or Linux, since each names
        # ports differently.
        ctk.CTkLabel(mode_frame, text="CONTROLLER PORT (optional)", font=("Segoe UI", 10),
                     text_color="gray60").pack(anchor="e", pady=(10, 0))
        self.port_entry = ctk.CTkEntry(mode_frame, placeholder_text=_PORT_EXAMPLE, width=170)
        self.port_entry.pack()

        self.hi_label = ctk.CTkLabel(self, text=f"High score: {self.high_score:05d}",
                                      font=("Segoe UI", 12), text_color="gray60")
        self.hi_label.pack(pady=(10, 0))

        ctk.CTkButton(self, text="START RACE", width=240, height=48,
                      corner_radius=10, fg_color="#E10600", hover_color="#a80400",
                      font=("Segoe UI", 16, "bold"),
                      command=self._start).pack(pady=(20, 10))

        ctk.CTkButton(self, text="?  HOW TO PLAY", width=180, height=32,
                      corner_radius=8, fg_color="transparent", border_width=1,
                      font=("Segoe UI", 12),
                      command=self._open_instructions).pack(pady=(0, 16))

    # ------------------------------------------------------------ what happens when you click things
    def _select(self, i):
        # remember which team is picked, and put a bright border around its button
        self.selected = i
        for j, btn in enumerate(self.team_buttons):
            btn.configure(border_width=3 if j == i else 0)

        # show that team's car picture and name
        name, color = g.TEAMS[i]
        if color not in self._preview_cache:
            img = _team_preview_image(color)
            self._preview_cache[color] = ctk.CTkImage(
                light_image=img, dark_image=img,
                size=(g.SPRITE_W * 3, g.SPRITE_H * 3),
            )
        self._preview_label.configure(image=self._preview_cache[color])
        self._name_label.configure(text=name)

    def _on_mode(self, value):
        self.theme_mode = value.lower()

    def _open_instructions(self):
        InstructionsWindow(self)

    def _start(self):
        # hide the menu, run one whole race, then decide what to do once it's over
        color = g.TEAMS[self.selected][1]
        # an empty box means "no controller" -- just use the keyboard
        port = self.port_entry.get().strip() or None
        # "RANDOM" means "let the game pick one" -- game.py already knows
        # how to turn None into a random choice, so we just pass it along
        track_pick = self.track_menu.get()
        track = None if track_pick == "RANDOM" else track_pick.lower()
        self.withdraw()
        result = g.run_race(color, theme_mode=self.theme_mode, high_score=self.high_score,
                             serial_port=port, track=track)
        self.high_score = max(self.high_score, result.get("high_score", 0))
        self.hi_label.configure(text=f"High score: {self.high_score:05d}")
        g.save_high_score(self.high_score)   # so it's still here next time you open the game

        if result.get("action") == "quit":
            # they closed the game window -- close the menu too
            self.destroy()
            return
        # they pressed HOME after crashing -- show the menu again
        self.deiconify()


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
