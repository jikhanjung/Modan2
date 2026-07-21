"""Deleting datasets and objects must take their files with them.

Only ``delete_object_with_files`` (the object dialog's path) ever cleaned up.
``delete_dataset`` and ``delete_object`` removed rows only, so images, their
archived originals and 3D models stayed on disk for good — and for a dataset,
so did the whole ``<storage>/<dataset_id>/`` directory. See devlog 228.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel
from ModanController import ModanController


@pytest.fixture
def controller(mock_database):
    return ModanController()


def _write(path, text="data"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    return path


def _object_with_files(dataset, storage, name="O", with_original=True, with_model=False):
    """An object plus the on-disk files it owns."""
    obj = MdModel.MdObject.create(dataset=dataset, object_name=name, landmark_str="1\t2")
    paths = []
    if with_model:
        model = MdModel.MdThreeDModel.create(object=obj, original_path="scan.obj")
        paths.append(_write(model.get_file_path(storage)))
    else:
        image = MdModel.MdImage.create(object=obj, original_path="pic.jpg")
        paths.append(_write(image.get_file_path(storage)))
        if with_original:
            paths.append(_write(image.get_original_file_path(storage)))
    return obj, paths


def test_delete_dataset_removes_its_storage_directory(controller, tmp_path):
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=2)
    _, paths_a = _object_with_files(dataset, storage, "A")
    _, paths_b = _object_with_files(dataset, storage, "B")
    directory = os.path.join(storage, str(dataset.id))
    assert all(os.path.exists(p) for p in paths_a + paths_b)

    assert controller.delete_dataset(dataset.id, storage) is True

    assert not os.path.exists(directory)
    assert MdModel.MdDataset.select().where(MdModel.MdDataset.id == dataset.id).count() == 0


def test_delete_dataset_leaves_other_datasets_alone(controller, tmp_path):
    storage = str(tmp_path)
    doomed = MdModel.MdDataset.create(dataset_name="Doomed", dimension=2)
    keeper = MdModel.MdDataset.create(dataset_name="Keeper", dimension=2)
    _, doomed_paths = _object_with_files(doomed, storage, "A")
    _, keeper_paths = _object_with_files(keeper, storage, "B")

    assert controller.delete_dataset(doomed.id, storage) is True

    assert not any(os.path.exists(p) for p in doomed_paths)
    assert all(os.path.exists(p) for p in keeper_paths)


def test_delete_dataset_succeeds_when_it_has_no_files(controller, tmp_path):
    dataset = MdModel.MdDataset.create(dataset_name="Empty", dimension=2)
    MdModel.MdObject.create(dataset=dataset, object_name="O", landmark_str="1\t2")

    assert controller.delete_dataset(dataset.id, str(tmp_path)) is True


def test_delete_object_removes_image_and_archived_original(controller, tmp_path):
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=2)
    obj, paths = _object_with_files(dataset, storage)
    assert len(paths) == 2

    assert controller.delete_object(obj.id, storage) is True

    assert not any(os.path.exists(p) for p in paths)
    assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj.id).count() == 0


def test_delete_object_removes_three_d_model(controller, tmp_path):
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=3)
    obj, paths = _object_with_files(dataset, storage, with_model=True)

    assert controller.delete_object(obj.id, storage) is True

    assert not any(os.path.exists(p) for p in paths)


def test_delete_object_keeps_sibling_files(controller, tmp_path):
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=2)
    doomed, doomed_paths = _object_with_files(dataset, storage, "A")
    _, keeper_paths = _object_with_files(dataset, storage, "B")

    assert controller.delete_object(doomed.id, storage) is True

    assert not any(os.path.exists(p) for p in doomed_paths)
    assert all(os.path.exists(p) for p in keeper_paths)


def test_delete_object_with_files_also_removes_three_d_model(controller, tmp_path):
    """The dialog path handled images only; a 3D model was left behind."""
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=3)
    obj, paths = _object_with_files(dataset, storage, with_model=True)

    controller.delete_object_with_files(obj, storage)

    assert not any(os.path.exists(p) for p in paths)


def test_missing_files_do_not_fail_the_delete(controller, tmp_path):
    """Rows must go even when the files were already gone."""
    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=2)
    obj, paths = _object_with_files(dataset, storage)
    for path in paths:
        os.remove(path)

    assert controller.delete_object(obj.id, storage) is True
    assert MdModel.MdObject.select().where(MdModel.MdObject.id == obj.id).count() == 0


def test_dataset_dialog_delete_goes_through_the_controller(qtbot, tmp_path, monkeypatch, mock_database):
    """The dialog used to call delete_instance() directly, skipping cleanup."""
    from PyQt5.QtWidgets import QMessageBox

    from dialogs.dataset_dialog import DatasetDialog

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    storage = str(tmp_path)
    dataset = MdModel.MdDataset.create(dataset_name="DS", dimension=2)
    _, paths = _object_with_files(dataset, storage)

    dialog = DatasetDialog(None)
    qtbot.addWidget(dialog)
    # m_app is the shared QApplication singleton, so set this through
    # monkeypatch: left behind, it redirects storage for every later test
    # (mu._get_storage_dir prefers the app attribute over the default).
    monkeypatch.setattr(dialog.m_app, "storage_directory", storage, raising=False)
    dialog.dataset = dataset
    dialog.parent = type("P", (), {"selected_dataset": dataset})()

    dialog.Delete()

    assert not any(os.path.exists(p) for p in paths)
    assert MdModel.MdDataset.select().where(MdModel.MdDataset.id == dataset.id).count() == 0
