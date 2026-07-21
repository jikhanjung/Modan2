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
    assert "MIT License" in text
