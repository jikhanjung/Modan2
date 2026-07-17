"""Tests for ModanController object persistence helpers moved out of ObjectDialog
(devlog 189/190)."""

import os

import MdModel
from ModanController import ModanController


def _dataset():
    return MdModel.MdDataset.create(dataset_name="D", dataset_desc="", dimension=2)


def test_save_object_creates_and_persists(mock_database):
    ds = _dataset()
    controller = ModanController()
    obj = controller.save_object(
        None,
        ds,
        object_name="Obj1",
        sequence=1,
        object_desc="desc",
        landmark_str="1.0\t2.0\n3.0\t4.0",
        property_str=None,
    )
    assert obj is not None
    assert obj.id is not None
    reloaded = MdModel.MdObject.get_by_id(obj.id)
    assert reloaded.object_name == "Obj1"
    assert reloaded.dataset_id == ds.id
    assert reloaded.landmark_str == "1.0\t2.0\n3.0\t4.0"


def test_save_object_property_str_none_leaves_field(mock_database):
    ds = _dataset()
    controller = ModanController()
    obj = MdModel.MdObject.create(dataset=ds, object_name="Pre", property_str="keep")
    controller.save_object(
        obj,
        ds,
        object_name="Pre",
        sequence=1,
        object_desc="",
        landmark_str="1\t2",
        property_str=None,
    )
    assert MdModel.MdObject.get_by_id(obj.id).property_str == "keep"


def test_delete_object_with_files_no_image(mock_database):
    ds = _dataset()
    controller = ModanController()
    obj = MdModel.MdObject.create(dataset=ds, object_name="O", landmark_str="1\t2")
    obj_id = obj.id
    controller.delete_object_with_files(obj, "/nonexistent/storage")
    assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj_id).count() == 0


def test_delete_object_with_files_removes_image_file(tmp_path, mock_database):
    ds = _dataset()
    controller = ModanController()
    obj = MdModel.MdObject.create(dataset=ds, object_name="O", landmark_str="1\t2")
    img = MdModel.MdImage.create(object=obj, original_path="pic.jpg")

    storage = str(tmp_path)
    file_path = img.get_file_path(storage)  # <storage>/<ds.id>/<obj.id>.jpg
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write("data")
    assert os.path.exists(file_path)

    obj_id = obj.id
    controller.delete_object_with_files(obj, storage)

    assert not os.path.exists(file_path)  # image file removed
    assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj_id).count() == 0
