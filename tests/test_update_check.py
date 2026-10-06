"""Update check in the About box (MdUpdate + ModanMainWindow).

The network is never touched: conftest makes ``fetch_releases`` fail, and the
tests here feed release lists or a fake ``urlopen`` directly.
"""

import io
import json
import ssl
import urllib.error

import pytest

import MdUpdate as mu_update


def _release(tag, draft=False, prerelease=None, assets=None):
    if assets is None:
        version = tag.lstrip("v")
        assets = [
            {
                "name": f"Modan2-Windows-Installer-v{version}-build1.zip",
                "browser_download_url": f"https://dl/{tag}/win.zip",
            },
            {
                "name": f"Modan2-macOS-Installer-v{version}-build1.dmg",
                "browser_download_url": f"https://dl/{tag}/mac.dmg",
            },
            {
                "name": f"Modan2-Linux-v{version}-build1.AppImage",
                "browser_download_url": f"https://dl/{tag}/linux.AppImage",
            },
            {"name": "SHA256SUMS.txt", "browser_download_url": f"https://dl/{tag}/sums"},
        ]
    return {
        "tag_name": tag,
        "draft": draft,
        "prerelease": "-" in tag if prerelease is None else prerelease,
        "html_url": f"https://github.com/jikhanjung/Modan2/releases/tag/{tag}",
        "assets": assets,
    }


class TestWhatIsOffered:
    @pytest.mark.parametrize(
        ("current", "candidate", "offered"),
        [
            ("0.2.0-beta.5", "0.2.0-beta.6", True),  # next pre-release on the same line
            ("0.2.0-beta.5", "0.2.0-rc.1", True),
            ("0.2.0-beta.5", "0.2.0", True),  # the stable it leads to
            ("0.2.0-beta.5", "0.2.1", True),  # any newer stable
            ("0.2.0-beta.5", "0.3.0-alpha.1", False),  # test build of the next version
            ("0.2.0-beta.5", "0.2.0-beta.5", False),
            ("0.2.0-beta.5", "0.2.0-beta.4", False),
            ("0.2.0", "0.2.1-beta.1", False),  # stable users get stable only
            ("0.2.0", "0.2.1", True),
            ("0.3.0-alpha.1", "0.3.0-alpha.2", True),
            ("0.3.0-alpha.1", "0.2.0-beta.6", False),
        ],
    )
    def test_rule(self, current, candidate, offered):
        assert mu_update.is_offered(mu_update.parse_version(candidate), mu_update.parse_version(current)) is offered

    def test_parse_accepts_v_prefix_and_rejects_junk(self):
        assert str(mu_update.parse_version("v0.2.0-beta.5")) == "0.2.0-beta.5"
        assert mu_update.parse_version("nightly") is None
        assert mu_update.parse_version("") is None


class TestFindUpdate:
    RELEASES = (
        _release("v0.3.0-alpha.1"),
        _release("v0.2.0-beta.7", draft=True),
        _release("v0.2.0-beta.6"),
        _release("v0.2.0-beta.5"),
        _release("not-a-version"),
        _release("v0.1.12"),
    )

    def test_newest_offered_with_this_platforms_installer(self):
        info = mu_update.find_update("0.2.0-beta.5", self.RELEASES, "win32")
        assert info["version"] == "0.2.0-beta.6"  # not the draft, not the alpha
        assert info["asset_url"] == "https://dl/v0.2.0-beta.6/win.zip"
        assert info["page_url"].endswith("/tag/v0.2.0-beta.6")

    @pytest.mark.parametrize(
        ("platform", "suffix"), [("win32", "win.zip"), ("darwin", "mac.dmg"), ("linux", "linux.AppImage")]
    )
    def test_asset_per_platform(self, platform, suffix):
        info = mu_update.find_update("0.2.0-beta.5", self.RELEASES, platform)
        assert info["asset_url"].endswith(suffix)

    def test_up_to_date(self):
        assert mu_update.find_update("0.2.0-beta.6", self.RELEASES, "linux") is None

    def test_unparseable_running_version_checks_nothing(self):
        assert mu_update.find_update("dev", self.RELEASES, "linux") is None

    def test_release_without_this_platforms_file_links_its_page(self):
        releases = [_release("v0.2.0-beta.6", assets=[{"name": "SHA256SUMS.txt", "browser_download_url": "x"}])]
        info = mu_update.find_update("0.2.0-beta.5", releases, "darwin")
        assert info["asset_url"] is None
        assert info["page_url"].endswith("/tag/v0.2.0-beta.6")

    def test_windows_prefers_the_installer(self):
        assets = [
            {"name": "Modan2-Windows-Portable-v0.2.0-build1.zip", "browser_download_url": "portable"},
            {"name": "Modan2-Windows-Installer-v0.2.0-build1.zip", "browser_download_url": "installer"},
        ]
        assert mu_update.platform_asset(assets, "win32") == ("Modan2-Windows-Installer-v0.2.0-build1.zip", "installer")


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestFetch:
    """``fetch_releases`` itself, with ``urlopen`` faked (conftest's offline
    stub is undone by restoring the real function)."""

    @pytest.fixture(autouse=True)
    def _real_fetch(self, monkeypatch):
        import importlib

        real = importlib.reload(mu_update).fetch_releases
        monkeypatch.setattr(mu_update, "fetch_releases", real)

    def test_returns_the_list(self, monkeypatch):
        seen = {}

        def fake_urlopen(request, timeout, context):
            seen["url"] = request.full_url
            seen["agent"] = request.get_header("User-agent")
            return _Response(json.dumps([_release("v0.2.0-beta.6")]).encode())

        monkeypatch.setattr(mu_update.urllib.request, "urlopen", fake_urlopen)
        releases = mu_update.fetch_releases()
        assert releases[0]["tag_name"] == "v0.2.0-beta.6"
        assert seen["url"] == mu_update.RELEASES_API_URL
        assert seen["agent"].startswith("Modan2/")

    def test_certificate_failure_falls_back_to_the_next_trust_source(self, monkeypatch):
        """An OS store that cannot verify GitHub (or a bundle that cannot verify
        an inspecting proxy) is not the end: the next source is tried."""
        contexts = [object(), object()]
        monkeypatch.setattr(mu_update, "_ssl_contexts", lambda: contexts)
        tried = []

        def fake_urlopen(request, timeout, context):
            tried.append(context)
            if context is contexts[0]:
                raise urllib.error.URLError(ssl.SSLCertVerificationError("unable to get local issuer certificate"))
            return _Response(b"[]")

        monkeypatch.setattr(mu_update.urllib.request, "urlopen", fake_urlopen)
        assert mu_update.fetch_releases() == []
        assert tried == contexts

    def test_other_failures_are_not_retried(self, monkeypatch):
        contexts = [object(), object()]
        monkeypatch.setattr(mu_update, "_ssl_contexts", lambda: contexts)
        tried = []

        def fake_urlopen(request, timeout, context):
            tried.append(context)
            raise urllib.error.URLError("timed out")

        monkeypatch.setattr(mu_update.urllib.request, "urlopen", fake_urlopen)
        with pytest.raises(OSError):
            mu_update.fetch_releases()
        assert len(tried) == 1

    def test_every_context_verifies(self):
        for context in mu_update._ssl_contexts():
            assert context.verify_mode == ssl.CERT_REQUIRED
            assert context.check_hostname is True


class TestAboutBox:
    def test_status_lines(self, qtbot, main_window):
        info = mu_update.find_update("0.2.0-beta.5", [_release("v0.2.0-beta.6")], "linux")
        update = main_window.update_status_html(("update", info))
        assert "0.2.0-beta.6" in update
        assert 'href="https://dl/v0.2.0-beta.6/linux.AppImage"' in update
        assert 'href="https://github.com/jikhanjung/Modan2/releases/tag/v0.2.0-beta.6"' in update
        assert main_window.update_status_html(None)  # "checking"
        assert main_window.update_status_html(("current", None))
        error = main_window.update_status_html(("error", "offline"))
        assert f'href="{mu_update.RELEASES_PAGE_URL}"' in error

    def test_open_box_is_updated_when_the_answer_arrives(self, qtbot, main_window):
        msg = main_window.build_about_message(main_window.update_status_html(None))
        main_window._about_box = msg
        info = mu_update.find_update("0.2.0-beta.5", [_release("v0.2.0-beta.6")], "linux")
        main_window._on_update_check_done(("update", info))
        assert "0.2.0-beta.6" in msg.text()
        assert main_window._update_result[0] == "update"
        main_window._about_box = None
        msg.deleteLater()

    def test_checked_once_per_session(self, qtbot, main_window, monkeypatch):
        calls = []
        monkeypatch.setattr(mu_update, "check_for_update", lambda v: calls.append(v))
        main_window._update_result = ("current", None)
        main_window._start_update_check()
        assert calls == []

    def test_offline_is_reported_not_raised(self, qtbot, main_window):
        main_window._update_result = None
        main_window._update_checking = False
        with qtbot.waitSignal(main_window_signals(main_window), timeout=5000):
            main_window._start_update_check()
        assert main_window._update_result[0] == "error"

    def test_box_without_a_status_has_no_update_line(self, qtbot, main_window):
        msg = main_window.build_about_message()
        assert "Checking" not in msg.text()
        msg.deleteLater()


def main_window_signals(main_window):
    """The signal the worker thread reports on (created on first use)."""
    from Modan2 import _UpdateCheckSignals

    if getattr(main_window, "_update_signals", None) is None:
        main_window._update_signals = _UpdateCheckSignals()
        main_window._update_signals.done.connect(main_window._on_update_check_done)
    return main_window._update_signals.done
