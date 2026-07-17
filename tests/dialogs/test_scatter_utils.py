"""Unit tests for the shared scatter-plot helpers."""

from dialogs.scatter_utils import build_scatter_group


def test_default_seed_group_has_meta_and_empty_lists():
    g = build_scatter_group(50, symbol="o", color="#0000FF", meta=True)
    assert g == {
        "x_val": [],
        "y_val": [],
        "z_val": [],
        "data": [],
        "hoverinfo": [],
        "text": [],
        "property": "",
        "symbol": "o",
        "color": "#0000FF",
        "size": 50,
    }


def test_average_default_seed_uses_scalar_zero():
    g = build_scatter_group(50, symbol="o", color="#0000FF", meta=True, empty=0)
    assert g["x_val"] == 0
    assert g["y_val"] == 0
    assert g["z_val"] == 0
    assert "hoverinfo" in g


def test_non_default_group_has_no_meta_and_named_property():
    g = build_scatter_group(30, property_name="Male")
    assert g == {
        "x_val": [],
        "y_val": [],
        "z_val": [],
        "data": [],
        "property": "Male",
        "symbol": "",
        "color": "",
        "size": 30,
    }


def test_axis_lists_are_independent_objects():
    g = build_scatter_group(50)
    g["x_val"].append(1)
    assert g["y_val"] == []  # y/z must not alias x
    assert g["z_val"] == []


def test_selected_group_shape():
    g = build_scatter_group(60, symbol="o", color="red", meta=True)
    assert g["color"] == "red"
    assert g["size"] == 60
    assert g["symbol"] == "o"
