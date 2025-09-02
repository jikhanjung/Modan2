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
        
        # Check for critical Qt files in the build output (platform-specific)
        if "--onedir" in args:
            base_dir = Path(f"dist/{actual_name}")
            print(f"Checking Qt files in: {base_dir}")
            
            if platform.system() == "Windows":
                qt_plugin_paths = [
                    base_dir / "PyQt5" / "Qt" / "plugins" / "platforms",
                    base_dir / "PyQt5" / "Qt" / "plugins" / "imageformats",
                    base_dir / "PyQt5" / "Qt" / "plugins" / "styles"
                ]
                
                for plugin_path in qt_plugin_paths:
                    if plugin_path.exists():
                        plugin_count = len(list(plugin_path.glob("*.dll")))
                        print(f"[OK] Found {plugin_count} plugins in {plugin_path}")
                    else:
                        print(f"[WARN] Missing plugin directory: {plugin_path}")
                
                # Check for critical OpenGL DLLs on Windows
                opengl_dlls = ["d3dcompiler_47.dll", "libEGL.dll", "libGLESv2.dll", "opengl32sw.dll"]
                for dll in opengl_dlls:
                    dll_path = base_dir / dll
                    if dll_path.exists():
                        print(f"[OK] Found OpenGL DLL: {dll}")
                    else:
                        print(f"[WARN] Missing OpenGL DLL: {dll}")
                        
            elif platform.system() == "Darwin":  # macOS
                # Check for PyQt5 frameworks/dylibs
                qt_lib_paths = [
                    base_dir / "_internal" / "PyQt5",
                    base_dir / "PyQt5"
                ]
                
                for qt_path in qt_lib_paths:
                    if qt_path.exists():
                        dylib_count = len(list(qt_path.rglob("*.dylib")))
                        so_count = len(list(qt_path.rglob("*.so")))
                        print(f"[OK] Found {dylib_count} dylibs and {so_count} shared objects in {qt_path}")
                        break
                else:
                    print(f"[WARN] Missing PyQt5 libraries in macOS bundle")
                    
            else:  # Linux  
                # Check for PyQt5 shared libraries
                qt_lib_paths = [
                    base_dir / "_internal" / "PyQt5",
                    base_dir / "PyQt5"
                ]
                
                for qt_path in qt_lib_paths:
                    if qt_path.exists():
                        so_count = len(list(qt_path.rglob("*.so*")))
                        print(f"[OK] Found {so_count} shared objects in {qt_path}")
                        break
                else:
                    print(f"[WARN] Missing PyQt5 libraries in Linux bundle")
            
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

# Create build info file for runtime access
build_info = {
    "version": VERSION,
    "build_number": BUILD_NUMBER,
    "build_date": DATE,
    "platform": platform.system().lower()
}

# Write build info to JSON file
import json
with open("build_info.json", "w") as f:
    json.dump(build_info, f, indent=2)
print(f"Build info saved to build_info.json")

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
    f"--add-data=build_info.json{data_separator}.",
    f"--icon={ICON}",
    "main.py",  # Use main.py instead of Modan2.py for better error handling
]
run_pyinstaller(onefile_args)

# 2. Run PyInstaller (One-Directory Bundle)
# Check if spec file exists and use it for more precise control
spec_file = Path("Modan2.spec")
if spec_file.exists() and platform.system() == "Windows":
    print("Using Modan2.spec file for Windows build...")
    onedir_args = [
        "--noconfirm",
        "--clean",
        str(spec_file)
    ]
else:
    # Fallback to command-line arguments
    onedir_args = [
        "--name=Modan2",  # Set executable name to Modan2.exe
        "--onedir",
        "--noconsole",
        f"--add-data=icons/*.png{data_separator}icons",
        f"--add-data=translations/*.qm{data_separator}translations",
        f"--add-data=migrations/*{data_separator}migrations",
        f"--add-data=build_info.json{data_separator}.",
        f"--icon={ICON}",
        "--noconfirm",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui", 
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtOpenGL",
        "main.py",  # Use main.py instead of Modan2.py for better error handling
    ]
    
    # Platform-specific PyQt5 collection (Windows needs more aggressive collection)
    if platform.system() == "Windows":
        onedir_args.extend([
            # Critical Qt plugins and OpenGL DLL inclusion for Windows stability
            "--collect-all=PyQt5",
            "--collect-binaries=PyQt5",
            "--collect-data=PyQt5",
            # Explicitly include OpenGL support libraries
            "--hidden-import=OpenGL",
            "--hidden-import=OpenGL.GL",
            "--hidden-import=OpenGL.GLU",
            # Ensure PyQt5 plugins are included
            "--copy-metadata=PyQt5",
            # Include numpy and other scientific libs
            "--hidden-import=numpy",
            "--hidden-import=scipy",
            "--hidden-import=pandas",
            "--hidden-import=cv2",
        ])
    elif platform.system() == "Darwin":  # macOS
        onedir_args.extend([
            # More selective collection for macOS to avoid framework conflicts
            "--collect-binaries=PyQt5.QtCore",
            "--collect-binaries=PyQt5.QtGui", 
            "--collect-binaries=PyQt5.QtWidgets",
            "--collect-binaries=PyQt5.QtOpenGL",
        ])
    else:  # Linux
        onedir_args.extend([
            # Moderate collection for Linux
            "--collect-binaries=PyQt5",
        ])

run_pyinstaller(onedir_args)

# Verify critical DLLs are included (Windows only)
if platform.system() == "Windows":
    print("\n=== Verifying Critical DLLs ===")
    from pathlib import Path
    
    dist_dir = Path("dist/Modan2")
    
    # Check for Qt platform plugins
    qt_plugins = {
        "platforms/qwindows.dll": "Qt Windows platform plugin",
        "platforms/qminimal.dll": "Qt minimal platform plugin",
        "platforms/qoffscreen.dll": "Qt offscreen platform plugin",
        "styles/qwindowsvistastyle.dll": "Qt Windows Vista style",
        "imageformats/qico.dll": "Qt ICO image format",
        "imageformats/qjpeg.dll": "Qt JPEG image format",
        "imageformats/qpng.dll": "Qt PNG image format",
    }
    
    # Check PyQt5/Qt/plugins directory
    qt_plugin_base = dist_dir / "PyQt5" / "Qt" / "plugins"
    if qt_plugin_base.exists():
        print(f"[OK] Qt plugins directory found: {qt_plugin_base}")
        for plugin_path, description in qt_plugins.items():
            full_path = qt_plugin_base / plugin_path
            if full_path.exists():
                print(f"  [OK] {description}: {plugin_path}")
            else:
                print(f"  [MISSING] {description}: {plugin_path}")
    else:
        # Alternative location
        qt_plugin_base = dist_dir / "PyQt5" / "Qt5" / "plugins"
        if qt_plugin_base.exists():
            print(f"[OK] Qt plugins directory found (Qt5): {qt_plugin_base}")
        else:
            print(f"[WARNING] Qt plugins directory not found at expected locations")
    
    # Check for OpenGL DLLs
    opengl_dlls = {
        "opengl32sw.dll": "Software OpenGL renderer",
        "d3dcompiler_47.dll": "Direct3D compiler",
        "libEGL.dll": "EGL library",
        "libGLESv2.dll": "OpenGL ES 2.0 library",
    }
    
    print("\n=== OpenGL DLL Status ===")
    for dll_name, description in opengl_dlls.items():
        # Check in main dist directory
        dll_path = dist_dir / dll_name
        if dll_path.exists():
            print(f"[OK] {description}: {dll_name}")
        else:
            # Check in PyQt5 directory
            alt_path = dist_dir / "PyQt5" / "Qt" / "bin" / dll_name
            if alt_path.exists():
                print(f"[OK] {description}: PyQt5/Qt/bin/{dll_name}")
            else:
                print(f"[WARNING] {description} not found: {dll_name}")
    
    # Check for VC++ runtime DLLs
    vcruntime_dlls = [
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "msvcp140.dll",
        "api-ms-win-crt-runtime-l1-1-0.dll",
    ]
    
    print("\n=== VC++ Runtime DLL Status ===")
    for dll_name in vcruntime_dlls:
        dll_path = dist_dir / dll_name
        if dll_path.exists():
            print(f"[OK] {dll_name}")
        else:
            print(f"[INFO] {dll_name} not included (may use system version)")
    
    # Check for database support
    print("\n=== Database Support ===")
    sqlite_dll = dist_dir / "sqlite3.dll"
    if sqlite_dll.exists():
        print(f"[OK] SQLite3 DLL found")
    else:
        # Check alternative location
        sqlite_dll = dist_dir / "_sqlite3.pyd"
        if sqlite_dll.exists():
            print(f"[OK] SQLite3 Python extension found")
        else:
            print(f"[WARNING] SQLite3 support files not found")
    
    print("\n=== Build Verification Complete ===")

# 3. Run Inno Setup Compiler (Optional)
iss_file = "InnoSetup/Modan2.iss"
run_inno_setup(iss_file, VERSION, BUILD_NUMBER)

print(f"\nBuild completed for version {VERSION}")