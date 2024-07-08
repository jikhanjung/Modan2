import subprocess
import os
from datetime import date
import MdUtils as mu

def run_pyinstaller(args):
    """Runs PyInstaller with the specified arguments."""
    pyinstaller_cmd = ["pyinstaller"] + args
    subprocess.run(pyinstaller_cmd, check=True)

def run_inno_setup(iss_file, version):
    """Runs Inno Setup Compiler with the specified ISS file and version."""
    with open(iss_file, 'r') as f:
        content = f.read()
        content = content.replace("#define AppVersion \"0.1.3\"", f"#define AppVersion \"{version}\"")
    with open(iss_file, 'w') as f:
        f.write(content)

    inno_setup_cmd = [r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", iss_file]
    subprocess.run(inno_setup_cmd, check=True)

# --- Configuration ---
NAME = mu.PROGRAM_NAME
VERSION = mu.PROGRAM_VERSION
#DATE = "20240708"
today = date.today()
DATE = today.strftime("%Y%m%d")
#print(DATE) # Output: YYYY-MM-DD (e.g., 2024-07-08)

OUTPUT_DIR = "dist"
ICON = "icons/Modan2_2.png"
# --- End Configuration ---

# 1. Run PyInstaller (One-File Executable)
onefile_args = [
    f"--name={NAME}_v{VERSION}_{DATE}.exe",
    "--onefile",
    "--noconsole",
    "--add-data=icons/*.png;icons",
    "--add-data=translations/*.qm;translations",
    "--add-data=migrations/*;migrations",
    f"--icon={ICON}",
    "Modan2.py",
]
run_pyinstaller(onefile_args)

# 2. Run PyInstaller (One-Directory Bundle)
onedir_args = [
    "--onedir",
    "--noconsole",
    "--add-data=icons/*.png;icons",
    "--add-data=translations/*.qm;translations",
    "--add-data=migrations/*;migrations",
    f"--icon={ICON}",
    "--noconfirm",
    "Modan2.py",
]
run_pyinstaller(onedir_args)

# 3. Run Inno Setup Compiler (Optional)
iss_file = "InnoSetup/Modan2.iss"
run_inno_setup(iss_file, mu.PROGRAM_VERSION)