"""Tests for saving/loading the high score, your last team/track/mode,
and the top-5 leaderboard.

Every test here points the save file at a temporary, throwaway folder
instead of your real one (using monkeypatch on _data_dir), so running
the tests never touches your actual saved progress.
"""
import game as g


def _use_temp_save_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(g, "_data_dir", lambda: str(tmp_path))


def test_high_score_starts_at_zero(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    assert g.load_high_score() == 0


def test_high_score_round_trips(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    g.save_high_score(4242)
    assert g.load_high_score() == 4242


def test_last_setup_has_sensible_defaults(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    setup = g.load_last_setup()
    assert setup == {"team": None, "track": None, "mode": "auto"}


def test_last_setup_round_trips(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    g.save_last_setup("Ferrari", "monza", "dark")
    assert g.load_last_setup() == {"team": "Ferrari", "track": "monza", "mode": "dark"}


def test_leaderboard_keeps_only_the_best_five(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    for score in (100, 500, 300, 900, 200, 700, 50):
        g.add_leaderboard_entry(score, "McLaren", "monza")
    board = g.load_leaderboard()
    assert len(board) == 5
    assert [e["score"] for e in board] == [900, 700, 500, 300, 200]


def test_leaderboard_updates_high_score_too(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    g.add_leaderboard_entry(777, "Mercedes", "suzuka")
    assert g.load_high_score() == 777


def test_saving_high_score_does_not_erase_last_setup(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    g.save_last_setup("Audi", "silverstone", "light")
    g.save_high_score(123)
    assert g.load_last_setup()["team"] == "Audi"


def test_saving_last_setup_does_not_erase_the_leaderboard(monkeypatch, tmp_path):
    _use_temp_save_folder(monkeypatch, tmp_path)
    g.add_leaderboard_entry(999, "Haas", "monaco")
    g.save_last_setup("Williams", "monza", "auto")
    assert g.load_leaderboard()[0]["score"] == 999
