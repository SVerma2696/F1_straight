"""Tests for InputManager -- reading the keyboard, and reading a real
controller's messages over a fake, pretend serial connection."""
import game as g


class _FakeSerial:
    """Stands in for a real serial.Serial object, without needing an
    actual controller plugged in."""

    def __init__(self, data: bytes = b""):
        self._data = data
        self.in_waiting = len(data)
        self.written = []   # every message we "sent" to the pretend controller

    def read(self, n):
        chunk = self._data[:n]
        self._data = self._data[n:]
        self.in_waiting = len(self._data)
        return chunk

    def write(self, data):
        self.written.append(data)


def test_poll_serial_reads_the_newest_line():
    inp = g.InputManager()
    inp.serial = _FakeSerial(b"0,0,0,0\n1,0,1,0\n")
    inp._poll_serial()
    assert inp.actions["jump"] is True
    assert inp.actions["duck"] is False
    assert inp.actions["boost"] is True
    assert inp.actions["home"] is False


def test_poll_serial_ignores_garbage():
    inp = g.InputManager()
    inp.serial = _FakeSerial(b"boot message, not a real frame\n")
    inp._poll_serial()   # should not raise, and should leave actions untouched
    assert inp.actions["jump"] is False


def test_poll_serial_waits_for_a_full_line():
    inp = g.InputManager()
    inp.serial = _FakeSerial(b"1,0,0,0")   # no trailing newline yet
    inp._poll_serial()
    assert inp.actions["jump"] is False


def test_send_drs_ready_does_nothing_without_a_real_controller():
    inp = g.InputManager()   # no serial_port given -- this is keyboard mode
    inp.send_drs_ready(True)   # should not raise, and there's nothing to check it wrote to


def test_send_drs_ready_writes_the_led_message():
    inp = g.InputManager()
    inp.serial = _FakeSerial()
    inp.send_drs_ready(True)
    assert inp.serial.written == [b"LED,1\n"]
    inp.send_drs_ready(False)
    assert inp.serial.written == [b"LED,1\n", b"LED,0\n"]


def test_send_drs_ready_only_writes_when_it_actually_changes():
    inp = g.InputManager()
    inp.serial = _FakeSerial()
    inp.send_drs_ready(True)
    inp.send_drs_ready(True)   # still True -- should NOT send another message
    inp.send_drs_ready(True)
    assert inp.serial.written == [b"LED,1\n"]
