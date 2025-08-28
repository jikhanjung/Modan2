import subprocess
import os
import sys
import platform
from datetime import date
import MdUtils as mu

def run_pyinstaller(args):
    """Runs PyInstaller with the specified arguments."""
    pyinstaller_cmd = ["pyinstaller"] + args
    subprocess.run(pyinstaller_cmd, check=True)

def run_inno_setup(iss_file, version):
    """Runs Inno Setup Compiler with the specified ISS file and version."""
    if platform.system() != "Windows":
        print("Inno Setup is Windows-only, skipping...")
        return
        
    with open(iss_file, 'r') as f:
        content = f.read()
        content = content.replace("#define AppVersion \"0.1.4\"", f"#define AppVersion \"{version}\"")
    with open(iss_file, 'w') as f:
        f.write(content)

    inno_setup_cmd = [r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", iss_file]
    try:
        subprocess.run(inno_setup_cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Inno Setup not found or failed, skipping installer creation...")

def get_platform_executable_extension():
    """Get the appropriate executable extension for the current platform."""
    if platform.system() == "Windows":
        return ".exe"
    return ""

def get_platform_separator():
    """Get the appropriate path separator for PyInstaller add-data."""
    if platform.system() == "Windows":
        return ";"
    return ":"

# --- Configuration ---
NAME = mu.PROGRAM_NAME
VERSION = mu.PROGRAM_VERSION
BUILD_NUMBER = os.environ.get('BUILD_NUMBER', 'local')
#DATE = "20240708"
today = date.today()
DATE = today.strftime("%Y%m%d")
#print(DATE) # Output: YYYY-MM-DD (e.g., 2024-07-08)

OUTPUT_DIR = "dist"
ICON = "icons/Modan2_2.png"
# --- End Configuration ---

# 1. Run PyInstaller (One-File Executable)
exe_extension = get_platform_executable_extension()
data_separator = get_platform_separator()

# Add platform suffix to filename
platform_suffix = ""
if platform.system() == "Linux":
    platform_suffix = "_linux"
elif platform.system() == "Darwin":  # macOS
    platform_suffix = "_macos"
elif platform.system() == "Windows":
    platform_suffix = ""  # Windows already has .exe extension

onefile_args = [
    f"--name={NAME}_v{VERSION}_build{BUILD_NUMBER}{platform_suffix}{exe_extension}",
    "--onefile",
    "--noconsole",
    f"--add-data=icons/*.png{data_separator}icons",
    f"--add-data=translations/*.qm{data_separator}translations",
    f"--add-data=migrations/*{data_separator}migrations",
    f"--icon={ICON}",
    "Modan2.py",
]
run_pyinstaller(onefile_args)

# 2. Run PyInstaller (One-Directory Bundle)
onedir_args = [
    "--onedir",
    "--noconsole",
    f"--add-data=icons/*.png{data_separator}icons",
    f"--add-data=translations/*.qm{data_separator}translations",
    f"--add-data=migrations/*{data_separator}migrations",
    f"--icon={ICON}",
    "--noconfirm",
    "Modan2.py",
]
run_pyinstaller(onedir_args)

# 3. Run Inno Setup Compiler (Optional)
iss_file = "InnoSetup/Modan2.iss"
run_inno_setup(iss_file, mu.PROGRAM_VERSION)