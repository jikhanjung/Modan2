import subprocess
import os
import sys
import platform
import re
import tempfile
import shutil
from datetime import date
from pathlib import Path

# Import version from centralized version file
try:
    from version import __version__ as VERSION
except ImportError:
    # Fallback: extract from version.py file
    def get_version_from_file():
        with open("version.py", "r") as f:
            content = f.read()
            match = re.search(r'__version__ = "(.*?)"', content)
            if match:
                return match.group(1)
        raise RuntimeError("Unable to find version string")
    VERSION = get_version_from_file()

import MdUtils as mu

def run_pyinstaller(args):
    """Runs PyInstaller with the specified arguments."""
    pyinstaller_cmd = ["pyinstaller"] + args
    try:
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully")
        
        # Check if the executable was created
        # Extract the actual name from PyInstaller args
        actual_name = "Modan2"  # default
        for i, arg in enumerate(args):
            if arg.startswith("--name="):
                actual_name = arg.split("=", 1)[1]
                break
        
        # For onedir, the main executable is in a subdirectory and might need .exe extension
        if "--onedir" in args:
            # For onedir mode, check if we need to add .exe extension
            base_exe_name = "Modan2"  # onedir always uses the script name as exe name
            exe_extension = get_platform_executable_extension()
            exe_path = Path(f"dist/{actual_name}/{base_exe_name}{exe_extension}")
        else:
            exe_path = Path(f"dist/{actual_name}")
            
        if not exe_path.exists():
            # List actual files in dist directory for debugging
            dist_path = Path("dist")
            if dist_path.exists():
                print(f"Contents of dist directory:")
                for item in dist_path.iterdir():
                    print(f"  {item}")
                if (dist_path / "Modan2").exists():
                    print(f"Contents of dist/Modan2 directory:")
                    for item in (dist_path / "Modan2").iterdir():
                        print(f"  {item}")
            raise FileNotFoundError(f"Expected executable not found: {exe_path}")
        else:
            print(f"Executable created: {exe_path}")
            
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        raise

def prepare_inno_setup_template(template_path, version):
    """Prepare Inno Setup script from template with version replacement."""
    temp_dir = Path(tempfile.mkdtemp())
    temp_iss = temp_dir / "Modan2_build.iss"
    
    # Read template or original file
    template_file = Path(template_path)
    if template_file.with_suffix('.iss.template').exists():
        # Use template if it exists
        template_file = template_file.with_suffix('.iss.template')
    
    content = template_file.read_text()
    
    # Replace version placeholder or hardcoded version
    content = re.sub(r'#define AppVersion ".*?"', f'#define AppVersion "{version}"', content)
    content = content.replace('{{VERSION}}', version)  # Also support template syntax
    
    # Write temporary ISS file
    temp_iss.write_text(content)
    return temp_iss

def run_inno_setup(iss_file, version, build_number):
    """Runs Inno Setup Compiler with the specified ISS file, version, and build number."""
    if platform.system() != "Windows":
        print("Inno Setup is Windows-only, skipping...")
        return
    
    # Prepare ISS file from template
    temp_iss = prepare_inno_setup_template(iss_file, version)
    
    inno_setup_cmd = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", 
        f"/DBuildNumber={build_number}",
        str(temp_iss)
    ]
    try:
        result = subprocess.run(inno_setup_cmd, check=True, capture_output=True, text=True)
        print(f"Installer created with version {version}")
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        print("Skipping installer creation...")
    except FileNotFoundError:
        print("Inno Setup not found, skipping installer creation...")
    finally:
        # Cleanup temp directory
        if temp_iss.parent.exists():
            shutil.rmtree(temp_iss.parent)

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
# Use centralized version
BUILD_NUMBER = os.environ.get('BUILD_NUMBER', 'local')
today = date.today()
DATE = today.strftime("%Y%m%d")

print(f"Building {NAME} version {VERSION}")
print(f"Build number: {BUILD_NUMBER}")
print(f"Build date: {DATE}")

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
    "main.py",
]
run_pyinstaller(onefile_args)

# 2. Run PyInstaller (One-Directory Bundle)
onedir_args = [
    "--name=Modan2",  # Explicitly set output name
    "--onedir",
    "--noconsole",
    f"--add-data=icons/*.png{data_separator}icons",
    f"--add-data=translations/*.qm{data_separator}translations",
    f"--add-data=migrations/*{data_separator}migrations",
    f"--icon={ICON}",
    "--noconfirm",
    "main.py",
]
run_pyinstaller(onedir_args)

# 3. Run Inno Setup Compiler (Optional)
iss_file = "InnoSetup/Modan2.iss"
run_inno_setup(iss_file, VERSION, BUILD_NUMBER)

print(f"\nBuild completed for version {VERSION}")