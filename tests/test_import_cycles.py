"""Each top-level module must import standalone, in a fresh interpreter.

The full suite can mask a circular import: once *any* test has imported
``dialogs``, a later ``import ModanComponents`` finds it cached and succeeds. Only
a clean interpreter per entry point catches the cycle — which is how a real
`ImportError: cannot import name 'DatasetOpsViewer' from partially initialized
module` reached main once already.
"""

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENTRY_POINTS = [
    "ModanComponents",
    "ModanController",
    "MdModel",
    "MdStatistics",
    "MdUtils",
    "components.widgets",
    "components.viewers",
    "dialogs",
    "Modan2",
]


@pytest.mark.parametrize("module", ENTRY_POINTS)
def test_module_imports_standalone(module):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=ROOT)
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"`import {module}` failed:\n{result.stderr}"
