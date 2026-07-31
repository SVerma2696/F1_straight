"""Tests for pausing mid-race -- freezing the race in place without
ending it. The P key and the controller pause-chord both just flip
Game.paused, so these tests check that flag directly."""
import game as g


def _fresh_game():
    font = g.load_font(18)
    big = g.load_font(26, bold=True)
    return g.Game(font=font, big_font=big, team_color=g.TEAMS[0][1], track="monza")


def test_pausing_freezes_the_score():
    gm = _fresh_game()
    for _ in range(20):
        gm.step({})
    score_before = gm.score
    gm.paused = True
    for _ in range(20):
        gm.step({})
    assert gm.score == score_before


def test_pausing_freezes_the_car_too():
    gm = _fresh_game()
    for _ in range(5):
        gm.step({})
    gm.paused = True
    gm.step({"jump": True})   # holding jump while paused should do nothing at all
    assert gm.car.on_ground is True


def test_unpausing_lets_the_race_continue():
    gm = _fresh_game()
    gm.paused = True
    gm.step({})
    score_while_paused = gm.score
    gm.paused = False
    for _ in range(20):
        gm.step({})
    assert gm.score > score_while_paused


def test_pausing_does_not_end_the_race():
    gm = _fresh_game()
    gm.paused = True
    gm.step({})
    assert gm.state == g.RUNNING
