"""Tests for DRS zones -- the green stretches of road where holding the
boost button actually speeds you up."""
import game as g


def _fresh_game():
    font = g.load_font(18)
    big = g.load_font(26, bold=True)
    return g.Game(font=font, big_font=big, team_color=g.TEAMS[0][1], track="monza")


def test_boost_does_nothing_outside_a_zone():
    gm = _fresh_game()
    for _ in range(10):
        gm.step({"boost": True})
    assert gm.boosting is False


def test_boost_speeds_you_up_inside_a_zone():
    gm = _fresh_game()
    for _ in range(10):
        gm.step({})
    car_l = gm.car.x
    gm.zones.append(g.DrsZone(car_l - 10, 300))
    gm.step({})   # let drs_available notice the new zone first
    assert gm.drs_available is True
    speed_before = gm.speed
    gm.step({"boost": True})
    assert gm.boosting is True
    assert gm.speed > speed_before


def test_boost_stops_the_moment_you_leave_the_zone():
    gm = _fresh_game()
    for _ in range(10):
        gm.step({})
    gm.zones.append(g.DrsZone(gm.car.x - 10, 60))   # a short zone, so we drive out of it quickly
    for _ in range(20):
        gm.step({"boost": True})
    assert gm.boosting is False


def test_just_boosted_is_only_true_on_the_first_frame():
    gm = _fresh_game()
    for _ in range(10):
        gm.step({})
    gm.zones.append(g.DrsZone(gm.car.x - 10, 300))
    gm.step({})
    gm.step({"boost": True})
    assert gm.just_boosted is True
    gm.step({"boost": True})
    assert gm.just_boosted is False
