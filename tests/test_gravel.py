"""Tests for gravel traps -- the sandy patches that slow you down for a
little while, unless you jump over them."""
import game as g


def _fresh_game(track="suzuka"):
    font = g.load_font(18)
    big = g.load_font(26, bold=True)
    return g.Game(font=font, big_font=big, team_color=g.TEAMS[0][1], track=track)


def test_driving_through_gravel_slows_you_down():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    speed_before = gm.speed
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 200))
    gm.step({})
    assert gm.in_gravel is True
    assert gm.speed < speed_before


def test_speed_eases_back_up_after_leaving_gravel():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 200))
    gm.step({})
    slowed = gm.speed
    gm.gravel_zones.clear()
    gm.step({})
    assert gm.in_gravel is False
    assert gm.gravel_recovery > 0
    assert gm.speed > slowed


def test_recovery_eventually_finishes():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 200))
    gm.step({})
    gm.gravel_zones.clear()
    for _ in range(g.GRAVEL_RECOVERY_FRAMES + 5):
        gm.step({})
    assert gm.gravel_recovery == 0


def test_jumping_over_gravel_avoids_the_penalty():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 200))
    gm.step({"jump": True})
    for _ in range(3):
        gm.step({})
    assert gm.car.on_ground is False
    assert gm.in_gravel is False


def test_gear_never_goes_negative_while_slowed():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 200))
    gm.step({})
    assert gm.gear >= 1


def test_gravel_hits_counts_each_fresh_patch():
    gm = _fresh_game()
    for _ in range(30):
        gm.step({})
    assert gm.gravel_hits == 0
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 40))   # a short patch
    for _ in range(20):   # long enough to drive all the way through and out the other side
        gm.step({})
    assert gm.gravel_hits == 1
    gm.gravel_zones.append(g.GravelTrap(gm.car.x - 10, 40))   # a second, separate patch
    for _ in range(20):
        gm.step({})
    assert gm.gravel_hits == 2
