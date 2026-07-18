"""Unit tests for the module-level ``SettingsWrapper`` (hoisted from
``ModanMainWindow.read_settings``)."""

import json

from PyQt5.QtCore import QRect

import Modan2
from Modan2 import SettingsWrapper


def test_value_reads_mapped_nested_key():
    sw = SettingsWrapper({"ui": {"plot_size": "large"}}, None)
    assert sw.value("PlotSize", "medium") == "large"


def test_value_returns_default_for_missing():
    sw = SettingsWrapper({"ui": {}}, None)
    assert sw.value("BackgroundColor", "default") == "default"


def test_value_returns_default_for_unmapped_key():
    sw = SettingsWrapper({}, None)
    assert sw.value("TotallyUnknownKey", "fallback") == "fallback"


def test_dynamic_datapoint_keys():
    sw = SettingsWrapper({"ui": {"data_point_colors": {"3": "#123456"}}}, None)
    assert sw.value("DataPointColor/3", "x") == "#123456"


def test_window_geometry_list_becomes_qrect():
    sw = SettingsWrapper({"ui": {"window_geometry": {"main_window": [1, 2, 3, 4]}}}, None)
    r = sw.value("WindowGeometry/MainWindow", QRect(0, 0, 10, 10))
    assert (r.x(), r.y(), r.width(), r.height()) == (1, 2, 3, 4)


def test_window_geometry_missing_returns_default_qrect():
    sw = SettingsWrapper({"ui": {}}, None)
    default = QRect(5, 6, 7, 8)
    r = sw.value("WindowGeometry/MainWindow", default)
    assert r is default


def test_remember_geometry_is_not_qrect_converted():
    sw = SettingsWrapper({"ui": {"remember_geometry": True}}, None)
    assert sw.value("WindowGeometry/RememberGeometry", False) is True


def test_setvalue_writes_nested_and_converts_qrect(monkeypatch):
    config = {}
    sw = SettingsWrapper(config, None)
    monkeypatch.setattr(sw, "save", lambda: None)  # don't touch ~/.modan2
    sw.setValue("WindowGeometry/MainWindow", QRect(10, 20, 30, 40))
    assert config["ui"]["window_geometry"]["main_window"] == [10, 20, 30, 40]


def test_setvalue_ignores_unmapped_key(monkeypatch):
    config = {}
    sw = SettingsWrapper(config, None)
    monkeypatch.setattr(sw, "save", lambda: None)
    sw.setValue("UnmappedKey", "v")
    assert config == {}


def test_save_writes_atomically_no_temp_leftover(tmp_path, monkeypatch):
    """save() persists the config and leaves no temp file behind."""
    monkeypatch.setattr(Modan2.Path, "home", staticmethod(lambda: tmp_path))
    sw = SettingsWrapper({"language": "en"}, None)
    sw.setValue("PlotSize", "Large")

    cfg = tmp_path / ".modan2" / "config.json"
    assert cfg.exists()
    assert json.loads(cfg.read_text())["ui"]["plot_size"] == "Large"
    # only config.json, no .config-*.tmp left around
    assert [p.name for p in (tmp_path / ".modan2").iterdir()] == ["config.json"]


def test_save_failure_preserves_existing_config(tmp_path, monkeypatch):
    """A failing write (non-serializable value) must NOT corrupt or delete the
    existing config.json — the whole point of the atomic temp+replace."""
    monkeypatch.setattr(Modan2.Path, "home", staticmethod(lambda: tmp_path))

    good = SettingsWrapper({"language": "en"}, None)
    good.setValue("PlotSize", "Large")
    cfg = tmp_path / ".modan2" / "config.json"
    before = cfg.read_text()

    # Inject a value json can't serialize, then attempt to save.
    bad = SettingsWrapper({"language": "en", "bad": {1, 2, 3}}, None)
    bad.save()  # logs error, must not raise, must not touch the good file

    assert cfg.read_text() == before  # untouched
    assert [p.name for p in (tmp_path / ".modan2").iterdir()] == ["config.json"]  # no temp leftover
