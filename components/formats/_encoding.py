"""Robust text decoding for the landmark file readers.

Landmark files (TPS/NTS/X1Y1/Morphologika) are almost entirely ASCII -- numbers
and keywords -- so only a specimen name can carry non-ASCII bytes. The bare
``open(path)`` used by the readers decodes with the platform's locale encoding,
so a UTF-8 file whose names contain non-ASCII characters fails to import on a
non-UTF-8 Windows box (cp949 in Korea), and a legacy-encoded file fails on a
UTF-8 box. This is the same class of failure as the 0.1.9 startup bug
(devlog 234). ``open_text`` tries UTF-8 first, then the platform preferred
encoding, then latin-1 (which decodes any byte), so a mildly mis-encoded name
degrades to replacement text instead of aborting the whole import.
"""

import io
import locale


def open_text(path):
    """Open a landmark text file tolerant of UTF-8 or a legacy locale encoding.

    Returns a text stream (``io.StringIO``) supporting ``read()`` /
    ``readlines()`` / iteration, so callers can keep using it like a file opened
    in text mode.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    tried = []
    for enc in ("utf-8-sig", locale.getpreferredencoding(False), "latin-1"):
        if not enc or enc.lower() in tried:
            continue
        tried.append(enc.lower())
        try:
            return io.StringIO(raw.decode(enc))
        except (UnicodeDecodeError, LookupError):
            continue
    # latin-1 decodes any byte sequence, so a return above always fires; this is
    # only a defensive last resort.
    return io.StringIO(raw.decode("latin-1", errors="replace"))
