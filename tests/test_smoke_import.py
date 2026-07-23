"""Import smoke test — the cheapest guard against platform/runtime breakage.

Importing every application module catches the class of bugs that only bite on a
particular OS or Python version and never appear in a unit test:

- a runtime-version-only stdlib symbol (e.g. ``from datetime import UTC`` is
  Python 3.11+; it crashed the app on a 3.10 environment),
- a broken/missing native extension (``PyQt5.sip``, ``PIL._imaging``),
- an import-time syntax/name error introduced by a refactor.

Run this on the cross-platform CI matrix (Windows/macOS/Linux × min/max Python)
so those failures show up as a red build instead of a user's crash report.

See docs/CODE_QUALITY_GUIDE.md §5.
"""

import importlib

import pytest

# Root modules. Importing Modan2 / main transitively pulls in most of the app,
# but listing the leaf modules explicitly gives a precise failure location.
ROOT_MODULES = [
    "version",
    "MdConstants",
    "MdUtils",
    "MdHelpers",
    "MdStatistics",
    "MdModel",
    "ModanController",
    "MdAppSetup",
    "MdSplashScreen",
    "Modan2",
    "main",
]

DIALOG_MODULES = [
    "dialogs.object_dialog",
    "dialogs.data_exploration_dialog",
    "dialogs.analysis_dialog",
    "dialogs.dataset_dialog",
    "dialogs.dataset_analysis_dialog",
    "dialogs.import_dialog",
    "dialogs.export_dialog",
    "dialogs.preferences_dialog",
    "dialogs.calibration_dialog",
    "dialogs.base_dialog",
]

COMPONENT_MODULES = [
    "components.formats",
    "components.formats.tps",
    "components.formats.nts",
    "components.formats.x1y1",
    "components.formats.morphologika",
    "components.viewers",
    "components.widgets",
]


@pytest.mark.parametrize("module_name", ROOT_MODULES + DIALOG_MODULES + COMPONENT_MODULES)
def test_module_imports(module_name):
    """Every application module imports without error on this OS / Python."""
    importlib.import_module(module_name)
