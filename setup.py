import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "excludes": ["tkinter", "unittest"],
    "zip_include_packages": ["encodings", "PyQt5"],
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Modan2",
    version="0.0.1",
    description="Modan GUI",
    options={"build_exe": build_exe_options},
    executables=[Executable("Modan2.py", base=base)],
)