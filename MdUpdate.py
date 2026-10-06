"""Check GitHub for a newer Modan2 release.

The About box asks this module whether a newer version has been published and,
if so, links the installer for the running platform.

Which releases count as "newer":

* A **stable** release counts whenever it is higher than the running version.
* A **pre-release** counts only on the running version's own line -- same
  major.minor.patch -- and only when the running version is itself a
  pre-release. Someone on 0.2.0-beta.5 is offered 0.2.0-beta.6, 0.2.0-rc.1 and
  0.2.0, but not 0.3.0-alpha.1: an alpha of the next version is a test build,
  not an update. Someone on a stable version is offered stable versions only.

GitHub's ``/releases/latest`` cannot be used: it skips pre-releases, and every
0.2.0 build so far is one. The full list is fetched and filtered here instead.

No network access happens on import or at startup; only an explicit
:func:`fetch_releases` call contacts GitHub.
"""

import json
import logging
import ssl
import sys
import urllib.request

import semver

logger = logging.getLogger(__name__)

RELEASES_API_URL = "https://api.github.com/repos/jikhanjung/Modan2/releases"
RELEASES_PAGE_URL = "https://github.com/jikhanjung/Modan2/releases"
REQUEST_TIMEOUT = 10  # seconds


def parse_version(text):
    """A ``semver.Version`` from ``"v0.2.0-beta.5"`` or ``"0.2.0-beta.5"``,
    or ``None`` when the text is not a semantic version."""
    if not text:
        return None
    try:
        return semver.Version.parse(text[1:] if text[:1] in ("v", "V") else text)
    except (ValueError, TypeError):
        return None


def is_offered(candidate, current):
    """Whether release version ``candidate`` should be offered to someone
    running ``current`` (see the module docstring for the rule)."""
    if candidate <= current:
        return False
    if candidate.prerelease is None:
        return True
    same_line = (candidate.major, candidate.minor, candidate.patch) == (current.major, current.minor, current.patch)
    return same_line and current.prerelease is not None


def platform_asset(assets, platform=None):
    """The download for ``platform`` (``sys.platform`` by default) among a
    release's assets, as ``(name, url)``, or ``None`` if it has none.

    Matches the names the release workflow publishes:
    ``Modan2-Windows-Installer-*.zip``, ``Modan2-macOS-Installer-*.dmg`` and
    ``Modan2-Linux-*.AppImage``.
    """
    platform = platform or sys.platform
    if platform.startswith("win"):
        wanted = [
            lambda n: "Windows-Installer" in n and n.endswith(".zip"),
            lambda n: "Windows" in n and n.endswith(".zip"),
        ]
    elif platform == "darwin":
        wanted = [lambda n: n.endswith(".dmg")]
    else:
        wanted = [lambda n: n.endswith(".AppImage")]
    for match in wanted:
        for asset in assets or []:
            name = asset.get("name", "")
            if match(name) and asset.get("browser_download_url"):
                return name, asset["browser_download_url"]
    return None


def find_update(current_version, releases, platform=None):
    """The newest release offered to ``current_version``, or ``None``.

    Args:
        current_version: the running version string.
        releases: GitHub's release list (dicts with ``tag_name``, ``draft``,
            ``html_url`` and ``assets``).
        platform: ``sys.platform`` value to pick the download for.

    Returns:
        ``{"version", "tag", "page_url", "asset_name", "asset_url"}`` --
        ``asset_*`` are ``None`` when the release has no file for this
        platform, in which case the release page is the link to give. ``None``
        when nothing newer is offered or the running version cannot be parsed.
    """
    current = parse_version(current_version)
    if current is None:
        return None
    best = None
    for release in releases or []:
        if release.get("draft"):
            continue
        version = parse_version(release.get("tag_name", ""))
        if version is None or not is_offered(version, current):
            continue
        if best is None or version > best[0]:
            best = (version, release)
    if best is None:
        return None
    version, release = best
    asset = platform_asset(release.get("assets"), platform)
    return {
        "version": str(version),
        "tag": release.get("tag_name"),
        "page_url": release.get("html_url") or RELEASES_PAGE_URL,
        "asset_name": asset[0] if asset else None,
        "asset_url": asset[1] if asset else None,
    }


def _ssl_contexts():
    """TLS contexts to try, in order. Every one verifies certificates.

    1. **The operating system's own trust store** (``truststore``): the Windows
       certificate store, the macOS keychain, the distribution's CA files on
       Linux. This is the one that works on a network that inspects TLS -- an
       institute or company proxy that re-signs traffic with its own root
       certificate. IT installs that root in the OS store, where browsers find
       it; a bundled CA list cannot know about it.
    2. **certifi's bundled CA list**: for a frozen build whose OpenSSL cannot
       find the system certificates (PyInstaller on macOS, an AppImage on an
       unusual Linux layout) and has no native store to ask.
    3. Python's default context, if neither package is available.
    """
    contexts = []
    try:
        import truststore

        contexts.append(truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
    except ImportError:
        logger.debug("truststore not installed; the OS trust store is not consulted")
    try:
        import certifi

        contexts.append(ssl.create_default_context(cafile=certifi.where()))
    except ImportError:
        logger.debug("certifi not installed; no bundled CA list to fall back on")
    return contexts or [ssl.create_default_context()]


def _is_certificate_failure(error):
    reason = getattr(error, "reason", error)
    return isinstance(reason, ssl.SSLCertVerificationError)


def fetch_releases(timeout=REQUEST_TIMEOUT):
    """GitHub's release list for Modan2 (newest first, first page).

    Tries each context of :func:`_ssl_contexts` in turn, moving on only when
    the certificate could not be verified; any other failure (no network, a
    timeout, an HTTP error) is final. A proxy configured in the environment
    (``HTTPS_PROXY``) or, on Windows, in the system settings is used as urllib
    finds it.

    Raises:
        OSError: network, TLS or HTTP failure (``urllib.error.URLError`` is one).
        ValueError: the response is not the expected JSON list.
    """
    from MdUtils import PROGRAM_NAME, PROGRAM_VERSION

    # S310: the URL is the fixed https constant above, never user input.
    request = urllib.request.Request(  # noqa: S310
        RELEASES_API_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"{PROGRAM_NAME}/{PROGRAM_VERSION}"},
    )
    *fallbacks, last = _ssl_contexts()
    for i, context in enumerate(fallbacks, start=1):
        try:
            return _read_releases(request, timeout, context)
        except OSError as e:
            if not _is_certificate_failure(e):
                raise
            logger.info("Update check: certificate not verified with trust source %d, trying the next: %s", i, e)
    return _read_releases(request, timeout, last)


def _read_releases(request, timeout, context):
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:  # noqa: S310
        releases = json.loads(response.read().decode("utf-8"))
    if not isinstance(releases, list):
        raise ValueError("unexpected response from GitHub")
    return releases


def check_for_update(current_version, platform=None):
    """Fetch the releases and return :func:`find_update`'s answer.

    Raises what :func:`fetch_releases` raises; the caller reports it.
    """
    return find_update(current_version, fetch_releases(), platform)
