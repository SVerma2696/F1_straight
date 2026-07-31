"""Tests for the famous-track background system."""
import game as g


def test_pick_track_keeps_a_valid_name():
    assert g.pick_track("monza") == "monza"


def test_pick_track_picks_something_random_for_bad_input():
    for name in (None, "not_a_real_track", "MONZA"):
        assert g.pick_track(name) in g.TRACK_NAMES


def test_every_track_has_a_background():
    for name in g.TRACKS:
        assert len(g.TRACK_SKYLINES[name]) > 0


def test_all_three_shape_kinds_are_used():
    shapes = {cfg["shape"] for cfg in g.TRACKS.values()}
    assert shapes == {"tree", "rect", "hill"}
