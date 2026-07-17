"""Unit tests for the guard_slot decorator (silent-crash protection for Qt slots)."""

from unittest.mock import Mock

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from MdHelpers import guard_slot


class _FakeDialog:
    """Stand-in for a QWidget/QDialog self; guard_slot only uses it as msgbox parent."""

    def __init__(self):
        self.ran = False

    @guard_slot("Boom")
    def ok(self):
        self.ran = True
        return 42

    @guard_slot("Boom")
    def boom(self):
        raise ValueError("kaboom")

    @guard_slot("Set cursor then boom")
    def cursor_then_boom(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        raise RuntimeError("mid-work failure")

    @guard_slot("with arg")
    def takes_one(self, value):
        return value


def test_guard_slot_passes_through_on_success(qtbot, monkeypatch):
    import MdHelpers

    crit = Mock()
    monkeypatch.setattr(MdHelpers.QMessageBox, "critical", crit)
    d = _FakeDialog()
    assert d.ok() == 42
    assert d.ran is True
    crit.assert_not_called()


def test_guard_slot_catches_and_shows_dialog(qtbot, monkeypatch):
    import MdHelpers

    crit = Mock()
    monkeypatch.setattr(MdHelpers.QMessageBox, "critical", crit)
    d = _FakeDialog()

    result = d.boom()  # must not raise

    assert result is None
    crit.assert_called_once()


def test_guard_slot_truncates_extra_signal_args(qtbot, monkeypatch):
    """PyQt passes signal args (e.g. clicked(bool)) to the variadic wrapper; a slot
    with fewer params must still work, and one that wants the arg must receive it."""
    import MdHelpers

    monkeypatch.setattr(MdHelpers.QMessageBox, "critical", Mock())
    d = _FakeDialog()

    # no-arg slot called with an extra bool (as clicked/triggered would) -> truncated
    assert d.ok(True) == 42
    # one-arg slot still receives its value, and drops a second extra arg
    assert d.takes_one(5) == 5
    assert d.takes_one(5, "extra") == 5


def test_guard_slot_restores_override_cursor(qtbot, monkeypatch):
    import MdHelpers

    monkeypatch.setattr(MdHelpers.QMessageBox, "critical", Mock())
    d = _FakeDialog()

    d.cursor_then_boom()  # sets WaitCursor then raises

    # The stuck override cursor must have been popped.
    assert QApplication.overrideCursor() is None
