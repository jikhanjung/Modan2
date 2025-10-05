#!/usr/bin/env python3
"""
Build both English and Korean documentation with separate output directories.

Usage:
    python build_all.py

Output:
    _build/html/en/  - English documentation
    _build/html/ko/  - Korean documentation
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and print status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n❌ Error: {description} failed")
        sys.exit(1)

    print(f"\n✅ Success: {description} completed")
    return result

def main():
    # Get the docs directory
    docs_dir = Path(__file__).parent.resolve()
    os.chdir(docs_dir)

    print("\n" + "="*60)
    print("  Building Modan2 Documentation (English + Korean)")
    print("="*60)

    # Clean previous builds
    build_dir = docs_dir / "_build" / "html"
    if build_dir.exists():
        print(f"\n🗑️  Cleaning previous build: {build_dir}")
        shutil.rmtree(build_dir)

    # Create output directories
    en_dir = build_dir / "en"
    ko_dir = build_dir / "ko"
    en_dir.mkdir(parents=True, exist_ok=True)
    ko_dir.mkdir(parents=True, exist_ok=True)

    # Build English documentation
    run_command(
        f'sphinx-build -b html -D language=en . {en_dir}',
        "Building English documentation"
    )

    # Build Korean documentation
    run_command(
        f'sphinx-build -b html -D language=ko . {ko_dir}',
        "Building Korean documentation"
    )

    # Create root index.html that redirects to English
    root_index = build_dir / "index.html"
    root_index.write_text("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=en/index.html">
    <title>Redirecting to Modan2 Documentation</title>
</head>
<body>
    <p>Redirecting to <a href="en/index.html">English documentation</a>...</p>
    <p>또는 <a href="ko/index.html">한국어 문서</a>로 이동</p>
</body>
</html>
""")

    # Copy .nojekyll file for GitHub Pages
    nojekyll_src = docs_dir / ".nojekyll"
    nojekyll_dst = build_dir / ".nojekyll"
    if nojekyll_src.exists():
        shutil.copy(nojekyll_src, nojekyll_dst)
        print("✅ Copied .nojekyll to build directory")

    print("\n" + "="*60)
    print("  ✅ Build Complete!")
    print("="*60)
    print(f"\nEnglish: {en_dir}/index.html")
    print(f"Korean:  {ko_dir}/index.html")
    print(f"Root:    {root_index}")
    print("\nTo view locally, open:")
    print(f"  file://{en_dir}/index.html")
    print(f"  file://{ko_dir}/index.html")
    print()

if __name__ == "__main__":
    main()
