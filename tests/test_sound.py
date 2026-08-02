"""Tests for the procedurally-generated sound effects -- built out of
math, not sound files. Runs with SDL_AUDIODRIVER=dummy (see conftest.py),
so these exercise the real code path without needing real speakers."""
import game as g


def test_init_audio_turns_sound_on():
    g.init_audio()
    assert g._AUDIO_OK is True


def test_playing_sounds_does_not_crash():
    g.init_audio()
    g.play_click()
    g.play_whoosh()
    g.play_thud()   # if any of these raise, the test fails on its own


def test_sounds_are_cached_after_first_use():
    g.init_audio()
    g.play_click()
    assert "click" in g._SOUND_CACHE


def test_engine_sound_switches_loops_when_gear_changes():
    g.init_audio()
    engine = g.EngineSound()
    engine.update(gear=1, boosting=False)
    assert engine.current_gear == 1
    engine.update(gear=4, boosting=False)
    assert engine.current_gear == 4
    engine.stop()
    assert engine.current_gear is None


def test_volume_is_clamped_between_zero_and_one():
    g.set_volume(1.5)
    assert g.get_volume() == 1.0
    g.set_volume(-0.5)
    assert g.get_volume() == 0.0


def test_muting_silences_the_effective_volume_without_forgetting_it():
    g.set_volume(0.7)
    g.set_muted(True)
    assert g.is_muted() is True
    assert g._effective_volume() == 0.0
    g.set_muted(False)
    assert g._effective_volume() == 0.7   # back to what it was before muting


class _FakeEngine:
    """Stands in for EngineSound, just remembering whether update() or
    stop() got called -- so we can check run_race()'s pause/engine
    wiring without needing a real window or a real sound card."""

    def __init__(self):
        self.updated = False
        self.stopped = False

    def update(self, gear, boosting):
        self.updated = True

    def stop(self):
        self.stopped = True


def _fresh_game():
    return g.Game(team_color=g.TEAMS[0][1], track="monza")


def test_pausing_stops_the_engine_sound():
    # this is the exact regression a reviewer flagged: pausing must
    # silence the engine hum, not just freeze the car
    gm = _fresh_game()
    gm.paused = True
    engine = _FakeEngine()
    g._drive_engine_sound(engine, gm)
    assert engine.stopped is True
    assert engine.updated is False


def test_engine_sound_runs_while_actively_racing():
    gm = _fresh_game()
    gm.paused = False
    engine = _FakeEngine()
    g._drive_engine_sound(engine, gm)
    assert engine.updated is True
    assert engine.stopped is False


def test_engine_sound_stops_after_a_crash():
    gm = _fresh_game()
    gm.state = g.GAME_OVER
    engine = _FakeEngine()
    g._drive_engine_sound(engine, gm)
    assert engine.stopped is True
    assert engine.updated is False
