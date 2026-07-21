"""Attach-time routine for oversized images.

``MdImage.add_file`` stores a downscaled working copy (landmarks are digitized
on it) and archives the pristine original under ``originals/``; small images
are stored verbatim with no archive. The archive follows dataset copies and is
removed with the object.
"""

import hashlib
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MdModel


def _write_jpeg(path, w, h):
    Image.new("RGB", (w, h), (128, 64, 32)).save(str(path), quality=95)
    return str(path)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture
def dataset(mock_database):
    return MdModel.MdDataset.create(dataset_name="ImgDS", dimension=2)


@pytest.fixture
def obj(dataset):
    return MdModel.MdObject.create(dataset=dataset, object_name="O1", sequence=1)


def _attach(obj, src, storage):
    image = MdModel.MdImage()
    image.object = obj
    image.add_file(src, base_path=str(storage))
    image.save()
    return image


def test_oversized_image_stores_downscaled_copy_and_archives_original(obj, tmp_path, monkeypatch):
    monkeypatch.setattr(MdModel, "IMAGE_MAX_DIM", 100)
    src = _write_jpeg(tmp_path / "big.jpg", 400, 200)
    storage = tmp_path / "storage"

    image = _attach(obj, src, storage)

    # working copy: downscaled to the cap, aspect kept
    working = image.get_file_path(str(storage))
    with Image.open(working) as img:
        assert img.size == (100, 50)

    # pristine original archived under originals/, byte-identical
    archived = image.get_original_file_path(str(storage))
    assert os.path.exists(archived)
    assert _md5(archived) == _md5(src)

    # DB records the ORIGINAL file's provenance (hash/size), not the copy's
    assert image.md5hash == _md5(src)
    assert image.size == os.path.getsize(src)


def test_small_image_stored_verbatim_without_archive(obj, tmp_path):
    src = _write_jpeg(tmp_path / "small.jpg", 200, 100)  # under the real 2560 cap
    storage = tmp_path / "storage"

    image = _attach(obj, src, storage)

    working = image.get_file_path(str(storage))
    assert _md5(working) == _md5(src)
    assert not os.path.exists(image.get_original_file_path(str(storage)))


def test_unreadable_image_falls_back_to_verbatim_copy(obj, tmp_path, monkeypatch):
    """A file PIL can't parse must still attach (stored verbatim, no archive)."""
    monkeypatch.setattr(MdModel, "IMAGE_MAX_DIM", 100)
    src = tmp_path / "garbage.jpg"
    src.write_bytes(b"not really a jpeg" * 100)
    storage = tmp_path / "storage"

    image = _attach(obj, str(src), storage)

    assert _md5(image.get_file_path(str(storage))) == _md5(str(src))
    assert not os.path.exists(image.get_original_file_path(str(storage)))


def test_copy_image_carries_archived_original(dataset, obj, tmp_path, monkeypatch):
    """Dataset/object copies must not silently drop the archived original."""
    monkeypatch.setattr(MdModel, "IMAGE_MAX_DIM", 100)
    storage = tmp_path / "storage"

    # copy_image resolves paths with the default storage dir; redirect both
    # path helpers to the test storage so nothing touches the real one.
    orig_gfp = MdModel.MdImage.get_file_path
    orig_gofp = MdModel.MdImage.get_original_file_path
    monkeypatch.setattr(MdModel.MdImage, "get_file_path", lambda self, base_path=None: orig_gfp(self, str(storage)))
    monkeypatch.setattr(
        MdModel.MdImage, "get_original_file_path", lambda self, base_path=None: orig_gofp(self, str(storage))
    )

    src = _write_jpeg(tmp_path / "big.jpg", 400, 200)
    image = _attach(obj, src, storage)

    obj2 = MdModel.MdObject.create(dataset=dataset, object_name="O2", sequence=2)
    copied = image.copy_image(obj2)
    copied.save()

    with Image.open(copied.get_file_path()) as img:
        assert img.size == (100, 50)  # working copy carried as-is (no re-downscale)
    assert _md5(copied.get_original_file_path()) == _md5(src)


def test_delete_object_with_files_removes_archive(obj, tmp_path, monkeypatch, controller):
    monkeypatch.setattr(MdModel, "IMAGE_MAX_DIM", 100)
    src = _write_jpeg(tmp_path / "big.jpg", 400, 200)
    storage = tmp_path / "storage"

    image = _attach(obj, src, storage)
    working = image.get_file_path(str(storage))
    archived = image.get_original_file_path(str(storage))
    assert os.path.exists(working) and os.path.exists(archived)

    controller.delete_object_with_files(obj, str(storage))

    assert not os.path.exists(working)
    assert not os.path.exists(archived)
