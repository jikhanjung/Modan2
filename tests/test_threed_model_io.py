"""Error-handling test for MdThreeDModel.add_file (audit 198, batch 3, group G).

add_file now mirrors MdImage.add_file: it logs and raises on failure instead of
silently leaving a 3D-model row without its file.
"""

import pytest

import MdModel


def test_threedmodel_add_file_missing_source_raises(mock_database):
    ds = MdModel.MdDataset.create(dataset_name="D", dataset_desc="", dimension=3)
    obj = MdModel.MdObject.create(dataset=ds, object_name="O")

    mdl = MdModel.MdThreeDModel()
    mdl.object = obj

    # A missing source file must raise (surfaced), not silently succeed.
    with pytest.raises(Exception):
        mdl.add_file("/definitely/does/not/exist.obj")
