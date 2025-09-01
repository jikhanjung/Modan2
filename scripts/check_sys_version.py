#!/usr/bin/env python
"""
Script to check sys.version string in the packaged executable
Run this after unpacking the .exe to see what Python version string is embedded
"""
import sys
import platform

print("=== Python Version Information ===")
print(f"sys.version: {sys.version}")
print(f"sys.version_info: {sys.version_info}")
print(f"platform.python_version(): {platform.python_version()}")
print(f"platform.python_implementation(): {platform.python_implementation()}")
print(f"platform.python_compiler(): {platform.python_compiler()}")
print(f"sys.executable: {sys.executable}")

# Check for Anaconda
if '| packaged by Anaconda' in sys.version:
    print("\n⚠️  Anaconda Python detected in sys.version!")
else:
    print("\n✓ Standard Python (no Anaconda string found)")

# Try to import pandas and check its build info
try:
    import pandas as pd
    print(f"\npandas version: {pd.__version__}")
    import numpy as np
    print(f"numpy version: {np.__version__}")
    print(f"numpy build info: {np.__config__.show()}")
except ImportError as e:
    print(f"\nCould not import pandas/numpy: {e}")