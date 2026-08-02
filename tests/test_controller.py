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


class _FakeGamepad:
    """Stands in for a pygame.joystick.Joystick, without needing a real
    Xbox/PlayStation/Switch controller plugged in."""

    def __init__(self, pressed_buttons=(), hat=(0, 0)):
        self._pressed = set(pressed_buttons)
        self._hat = hat

    def get_numbuttons(self):
        return 16

    def get_button(self, i):
        return i in self._pressed

    def get_numhats(self):
        return 1

    def get_hat(self, i):
        return self._hat


def test_gamepad_bottom_face_button_jumps():
    inp = g.InputManager()
    inp.gamepad = _FakeGamepad(pressed_buttons=[0])   # Xbox A / PS Cross / Switch B
    inp._poll_gamepad()
    assert inp.actions["jump"] is True


def test_gamepad_dpad_down_also_ducks():
    inp = g.InputManager()
    inp.gamepad = _FakeGamepad(hat=(0, -1))   # D-pad pressed down
    inp._poll_gamepad()
    assert inp.actions["duck"] is True


def test_gamepad_buttons_do_not_turn_off_keyboard_presses():
    # the gamepad should only ever ADD to what the keyboard already
    # said, never take a "True" back to "False"
    inp = g.InputManager()
    inp.actions["jump"] = True   # pretend the keyboard already said jump
    inp.gamepad = _FakeGamepad(pressed_buttons=[])   # nothing held on the pad
    inp._poll_gamepad()
    assert inp.actions["jump"] is True


def test_gamepad_start_button_triggers_home():
    inp = g.InputManager()
    inp.gamepad = _FakeGamepad(pressed_buttons=[7])
    inp._poll_gamepad()
    assert inp.actions["home"] is True
