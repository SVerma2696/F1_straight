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
