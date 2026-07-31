"""Tests for _fit_rect -- the math that fits the game's picture into
whatever size the window has been resized to."""
import game as g


def test_native_size_is_a_no_op():
    scale, xo, yo, dw, dh = g._fit_rect(g.WIDTH, g.HEIGHT)
    assert (scale, xo, yo, dw, dh) == (1.0, 0, 0, g.WIDTH, g.HEIGHT)


def test_doubling_the_window_doubles_the_picture():
    scale, xo, yo, dw, dh = g._fit_rect(g.WIDTH * 2, g.HEIGHT * 2)
    assert scale == 2.0
    assert (xo, yo) == (0, 0)


def test_mismatched_shape_adds_matching_borders():
    scale, xo, yo, dw, dh = g._fit_rect(1800, 1800)
    assert dw == 1800
    assert dh == 600
    assert yo == 600   # equal-sized borders top and bottom


def test_tiny_window_never_shrinks_to_nothing():
    scale, xo, yo, dw, dh = g._fit_rect(1, 1)
    assert dw >= 1 and dh >= 1
