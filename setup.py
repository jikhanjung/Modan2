import sys
import re
from cx_Freeze import setup, Executable

def get_version():
    """Extract version from version.py file"""
    try:
        # Try importing first
        from version import __version__
        return __version__
    except ImportError:
        # Fallback to regex extraction
        with open("version.py", "r") as f:
            content = f.read()
            match = re.search(r'__version__ = "(.*?)"', content)
            if match:
                return match.group(1)
        raise RuntimeError("Unable to find version string")

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "excludes": ["tkinter", "unittest"],
    "zip_include_packages": ["encodings", "PyQt5"],
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Modan2",
    version=get_version(),
    description="Modan2 - Morphometric Analysis Application",
    options={"build_exe": build_exe_options},
    executables=[Executable("Modan2.py", base=base)],
)