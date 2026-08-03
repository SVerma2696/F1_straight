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
import customtkinter as ctk
from PIL import Image
import pygame

try:
    import serial.tools.list_ports   # only used to look up connected controllers
except ImportError:
    serial = None   # pyserial isn't installed -- we just won't find any controllers, that's all

import game as g

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

TEAM_COLS = 4     # how many team buttons fit in one row

NO_CONTROLLER = "No controller found -- using keyboard"


def _detect_ports():
    """Ask the computer which serial devices are plugged in right now --
    this is how we find a real controller automatically instead of
    making you type its port name yourself."""
    if serial is None:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


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
        "P" + " " * 19 + "Pause / un-pause\n"
        "M" + " " * 19 + "Mute / unmute\n"
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
        "swooping seagulls, and beat your high score. Your high score,\n"
        "your best 5 races, and your last team/track/mode are all saved\n"
        "to disk and remembered even after you close the game."
    )),
    ("Leaderboard", (
        "Click LEADERBOARD on the menu to see your best 5 races ever --\n"
        "each one remembers the score, the team, and the track."
    )),
    ("Gamepad (optional)", (
        "Plug in an Xbox, PlayStation, or Nintendo Switch Pro controller\n"
        "and it just works, right alongside the keyboard -- no menu, no\n"
        "setup. Bottom face button = jump, left face button (or D-pad\n"
        "down) = duck, right shoulder button = DRS boost, start/options\n"
        "= home."
    )),
    ("Custom controller (optional)", (
        "You can also plug in a real 4-button controller you built\n"
        "yourself, on top of the keyboard/gamepad (never instead of --\n"
        "they all work together). The CONTROLLER PORT menu automatically\n"
        "lists any connected devices -- just pick yours from the list\n"
        "(hit the small refresh button if you plug it in after opening\n"
        "the menu). No controller found just means the keyboard/gamepad\n"
        "will be used on their own."
    )),
]


class InstructionsWindow(ctk.CTkToplevel):
    """The little pop-up window that shows up when you click "HOW TO PLAY"."""

    def __init__(self, master):
        super().__init__(master)
        self.title("How to play")
        self.geometry("460x1080")
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
                      command=self._close).pack(pady=18)

    def _close(self):
        g.play_click()
        self.destroy()


def _track_label(track_key):
    # turn a saved track key like "monza" back into its pretty display
    # name, or "Random" if that race didn't use a fixed track
    cfg = g.TRACKS.get(track_key)
    return cfg["label"] if cfg else "Random"


class LeaderboardWindow(ctk.CTkToplevel):
    """The little pop-up window showing your best 5 races ever, with a
    way to filter down to just one team or track, and to sort by
    whichever column you care about."""

    SORT_CHOICES = ["SCORE (best first)", "TEAM (A-Z)", "TRACK (A-Z)"]

    def __init__(self, master):
        super().__init__(master)
        self.title("Leaderboard")
        self.geometry("440x520")
        self.resizable(True, True)
        self.minsize(360, 360)
        self.transient(master)
        self.grab_set()

        self.board = g.load_leaderboard()   # the raw top-5, loaded once when this window opens

        ctk.CTkLabel(self, text="TOP 5 RACES",
                     font=("Segoe UI", 20, "bold")).pack(pady=(20, 10))

        # filter + sort controls -- only worth showing if there's
        # actually more than one team/track to tell apart
        teams_seen = sorted({e.get("team", "?") for e in self.board})
        tracks_seen = sorted({_track_label(e.get("track")) for e in self.board})
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(pady=(0, 8))
        ctk.CTkLabel(controls, text="TEAM", font=("Segoe UI", 10), text_color="gray60").grid(row=0, column=0)
        self.team_filter = ctk.CTkOptionMenu(controls, values=["ALL"] + teams_seen,
                                              command=self._on_filter_change, width=110)
        self.team_filter.set("ALL")
        self.team_filter.grid(row=1, column=0, padx=4)
        ctk.CTkLabel(controls, text="TRACK", font=("Segoe UI", 10), text_color="gray60").grid(row=0, column=1)
        self.track_filter = ctk.CTkOptionMenu(controls, values=["ALL"] + tracks_seen,
                                               command=self._on_filter_change, width=110)
        self.track_filter.set("ALL")
        self.track_filter.grid(row=1, column=1, padx=4)
        ctk.CTkLabel(controls, text="SORT BY", font=("Segoe UI", 10), text_color="gray60").grid(row=0, column=2)
        self.sort_menu = ctk.CTkOptionMenu(controls, values=self.SORT_CHOICES,
                                            command=self._on_filter_change, width=150)
        self.sort_menu.set(self.SORT_CHOICES[0])
        self.sort_menu.grid(row=1, column=2, padx=4)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=24)
        self._render_rows()

        ctk.CTkButton(self, text="CLOSE", width=140, height=36, corner_radius=8,
                      command=self._close).pack(pady=14)

    def _on_filter_change(self, _value):
        g.play_click()
        self._render_rows()

    def _render_rows(self):
        # wipe out whatever rows are showing now, then draw fresh ones
        # that match the current filter + sort choice
        for child in self.body.winfo_children():
            child.destroy()

        rows = list(self.board)
        if self.team_filter.get() != "ALL":
            rows = [e for e in rows if e.get("team", "?") == self.team_filter.get()]
        if self.track_filter.get() != "ALL":
            rows = [e for e in rows if _track_label(e.get("track")) == self.track_filter.get()]

        sort_choice = self.sort_menu.get()
        if sort_choice.startswith("TEAM"):
            rows.sort(key=lambda e: e.get("team", "?"))
        elif sort_choice.startswith("TRACK"):
            rows.sort(key=lambda e: _track_label(e.get("track")))
        else:
            rows.sort(key=lambda e: e.get("score", 0), reverse=True)

        if not rows:
            msg = "No races finished yet -- go set a record!" if not self.board \
                else "No races match that filter."
            ctk.CTkLabel(self.body, text=msg, font=("Segoe UI", 12),
                         text_color="gray60").pack(pady=20)
            return

        for i, entry in enumerate(rows, start=1):
            row = ctk.CTkFrame(self.body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"#{i}", font=("Segoe UI", 13, "bold"),
                         text_color="#E10600", width=32, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{entry.get('score', 0):05d}", font=("Consolas", 13, "bold"),
                         anchor="w", width=80).pack(side="left")
            ctk.CTkLabel(row, text=f"{entry.get('team', '?')} -- {_track_label(entry.get('track'))}",
                         font=("Segoe UI", 12), text_color="gray70", anchor="w").pack(side="left")

    def _close(self):
        g.play_click()
        self.destroy()


class Launcher(ctk.CTk):
    """The main menu window: pick a team, pick a theme, then race."""

    def __init__(self):
        super().__init__()
        self.title("The F1 Straight")
        self.geometry("640x830")
        # lets you maximize (or just drag bigger) the menu window too --
        # the layout stays anchored at the top instead of stretching,
        # but the maximize button now actually does something
        self.resizable(True, True)
        self.minsize(640, 830)

        g.init_audio()   # turn sound on for menu clicks (a race will also do this itself when it starts)

        # bring back whatever volume/mute setting you left it on last time
        sound_setup = g.load_sound_settings()
        g.set_volume(sound_setup["volume"])
        g.set_muted(sound_setup["muted"])

        # load whatever high score, last team/track/mode were saved from
        # last time you played, so nothing resets just because you
        # closed the app
        self.high_score = g.load_high_score()
        setup = g.load_last_setup()
        self.theme_mode = setup["mode"] if setup["mode"] in g.THEME_MODES else "auto"
        self.last_track = setup["track"] if setup["track"] in g.TRACKS else None
        last_team_i = next((i for i, (name, _) in enumerate(g.TEAMS) if name == setup["team"]), 0)

        self.selected = 0          # which team is picked right now (0 = first team)
        self.team_buttons = []
        self._preview_cache = {}   # remembers car pictures we've already built

        self._build_ui()
        self._select(last_team_i)

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
                command=lambda i=i: self._pick_team(i),
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
        self.mode_menu.set(g.THEME_LABELS[self.theme_mode])
        self.mode_menu.pack()

        # which famous track's background to race at -- RANDOM means "let
        # the game surprise me," which is also what happens if you never
        # touch this menu at all
        ctk.CTkLabel(mode_frame, text="TRACK", font=("Segoe UI", 11),
                     text_color="gray60").pack(anchor="e", pady=(10, 0))
        track_values = ["RANDOM"] + [cfg["label"].upper() for cfg in g.TRACKS.values()]
        self.track_menu = ctk.CTkOptionMenu(mode_frame, values=track_values,
                                             command=self._on_track, width=120)
        self.track_menu.set(g.TRACKS[self.last_track]["label"].upper() if self.last_track else "RANDOM")
        self.track_menu.pack()

        # a real 4-button controller is optional -- pick its port from the
        # list of devices actually plugged in right now, or leave it on
        # "no controller found" to just use the keyboard, which is what
        # happens by default
        ctk.CTkLabel(mode_frame, text="CONTROLLER PORT (optional)", font=("Segoe UI", 10),
                     text_color="gray60").pack(anchor="e", pady=(10, 0))
        port_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        port_row.pack()
        ports = _detect_ports()
        self.port_menu = ctk.CTkOptionMenu(port_row, values=ports or [NO_CONTROLLER],
                                            command=lambda _v: g.play_click(), width=142)
        self.port_menu.set(ports[0] if ports else NO_CONTROLLER)
        self.port_menu.pack(side="left")
        ctk.CTkButton(port_row, text="⟳", width=28, command=self._refresh_ports).pack(side="left", padx=(4, 0))

        # a mute button plus a slider for how loud everything is -- both
        # apply right away and are remembered for next time
        ctk.CTkLabel(mode_frame, text="VOLUME", font=("Segoe UI", 11),
                     text_color="gray60").pack(anchor="e", pady=(10, 0))
        vol_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        vol_row.pack()
        self.mute_btn = ctk.CTkButton(vol_row, text=self._speaker_icon(), width=28,
                                       command=self._toggle_mute)
        self.mute_btn.pack(side="left")
        self.volume_slider = ctk.CTkSlider(vol_row, from_=0, to=100, width=110,
                                            command=self._on_volume)
        self.volume_slider.set(g.get_volume() * 100)
        self.volume_slider.pack(side="left", padx=(4, 0))

        self.hi_label = ctk.CTkLabel(self, text=f"High score: {self.high_score:05d}",
                                      font=("Segoe UI", 12), text_color="gray60")
        self.hi_label.pack(pady=(10, 0))

        ctk.CTkButton(self, text="START RACE", width=240, height=48,
                      corner_radius=10, fg_color="#E10600", hover_color="#a80400",
                      font=("Segoe UI", 16, "bold"),
                      command=self._start).pack(pady=(20, 10))

        # a solid, readable background instead of "transparent" -- a see-
        # through button blended into plain white in light mode, making
        # its border and text nearly invisible. (gray85, gray20) means
        # "light gray in light mode, dark gray in dark mode," so it
        # stays easy to read either way.
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, 16))
        ctk.CTkButton(btn_row, text="?  HOW TO PLAY", width=170, height=32,
                      corner_radius=8, fg_color=("gray85", "gray20"),
                      text_color=("gray10", "gray90"), border_width=1,
                      border_color=("gray70", "gray40"), font=("Segoe UI", 12),
                      command=self._open_instructions).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="\U0001F3C6  LEADERBOARD", width=170, height=32,
                      corner_radius=8, fg_color=("gray85", "gray20"),
                      text_color=("gray10", "gray90"), border_width=1,
                      border_color=("gray70", "gray40"), font=("Segoe UI", 12),
                      command=self._open_leaderboard).pack(side="left", padx=4)

    # ------------------------------------------------------------ what happens when you click things
    def _pick_team(self, i):
        g.play_click()
        self._select(i)

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
        g.play_click()
        self.theme_mode = value.lower()

    def _on_track(self, value):
        g.play_click()

    def _speaker_icon(self):
        # a little speaker (or muted-speaker) picture for the mute button
        return "\U0001F507" if g.is_muted() else "\U0001F50A"

    def _toggle_mute(self):
        g.set_muted(not g.is_muted())
        g.save_sound_settings(g.get_volume(), g.is_muted())
        self.mute_btn.configure(text=self._speaker_icon())
        if not g.is_muted():
            g.play_click()   # only actually audible once we've just un-muted

    def _on_volume(self, value):
        g.set_volume(value / 100)
        g.save_sound_settings(g.get_volume(), g.is_muted())

    def _refresh_ports(self):
        # look again for connected controllers -- handy if you plugged
        # one in after the menu was already open
        g.play_click()
        ports = _detect_ports()
        values = ports or [NO_CONTROLLER]
        self.port_menu.configure(values=values)
        self.port_menu.set(values[0])

    def _open_instructions(self):
        g.play_click()
        InstructionsWindow(self)

    def _open_leaderboard(self):
        g.play_click()
        LeaderboardWindow(self)

    def _start(self):
        g.play_click()
        # hide the menu, run one whole race, then decide what to do once it's over
        team_name, color = g.TEAMS[self.selected]
        port_pick = self.port_menu.get()
        port = None if port_pick == NO_CONTROLLER else port_pick
        # "RANDOM" means "let the game pick one" -- game.py already knows
        # how to turn None into a random choice, so we just pass it along
        track_pick = self.track_menu.get()
        track = None if track_pick == "RANDOM" else track_pick.lower()
        self.withdraw()
        result = g.run_race(color, theme_mode=self.theme_mode, high_score=self.high_score,
                             serial_port=port, track=track)
        g.init_audio()   # run_race() just shut sound down when it closed -- bring it back for the menu

        self.high_score = max(self.high_score, result.get("high_score", 0))
        self.hi_label.configure(text=f"High score: {self.high_score:05d}")
        # remember this race for the leaderboard, and remember this setup
        # (team/track/mode) so next time the app opens right back here
        g.add_leaderboard_entry(result.get("score", 0), team_name, track)
        g.save_last_setup(team_name, track, self.theme_mode)

        if result.get("action") == "quit":
            # they closed the game window -- close the menu too
            self.destroy()
            return
        # they pressed HOME after crashing -- show the menu again
        self.deiconify()


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
