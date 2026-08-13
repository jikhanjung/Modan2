"""The About box shows the project page as a clickable link."""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdUtils as mu


def _about(main_window):
    msg = main_window.build_about_message()
    msg.deleteLater()
    return msg


def test_homepage_is_an_anchor(qtbot, main_window):
    msg = _about(main_window)

    assert f'href="{mu.PROGRAM_HOMEPAGE}"' in msg.text()
    assert mu.PROGRAM_HOMEPAGE == "https://github.com/jikhanjung/Modan2"


def test_rendered_as_rich_text_so_the_anchor_is_live(qtbot, main_window):
    """Plain text would show the markup instead of a link."""
    msg = _about(main_window)

    assert msg.textFormat() == Qt.RichText


def test_link_opens_in_a_browser(qtbot, main_window):
    """The label must carry the link to the desktop browser, and accept clicks."""
    msg = _about(main_window)

    labels = [lb for lb in msg.findChildren(QLabel) if mu.PROGRAM_HOMEPAGE in lb.text()]
    assert labels, "no label carries the homepage link"
    label = labels[0]
    assert label.openExternalLinks()
    assert label.textInteractionFlags() & Qt.LinksAccessibleByMouse


def test_still_reports_name_version_and_copyright(qtbot, main_window):
    text = _about(main_window).text()

    assert mu.PROGRAM_NAME in text
    assert mu.PROGRAM_VERSION in text
    assert mu.PROGRAM_COPYRIGHT in text


def test_names_both_licences(qtbot, main_window):
    """The source is MIT and this build is GPL-3.0; the box must say both.

    It said only "MIT License", which is the licence of the source and not of
    the binary printing the message -- the released build includes PyQt5, which
    is GPL-or-commercial, so the whole is GPL-3.0. A reader of an installed copy
    was being told they had permissive terms they did not have.

    Asserting on MIT alone would still pass with the GPL line deleted, which is
    how the wrong version of this box would come back.
    """
    text = _about(main_window).text()

    assert "MIT" in text
    assert "General Public License" in text or "GPL" in text
