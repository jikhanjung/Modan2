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
import MdUtils as mu


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

    # copy_image resolves paths itself, so point the resolver at the test
    # storage to keep the real one untouched.
    _redirect_storage(monkeypatch, storage)

    src = _write_jpeg(tmp_path / "big.jpg", 400, 200)
    image = _attach(obj, src, storage)

    obj2 = MdModel.MdObject.create(dataset=dataset, object_name="O2", sequence=2)
    copied = image.copy_image(obj2)
    copied.save()

    with Image.open(copied.get_file_path()) as img:
        assert img.size == (100, 50)  # working copy carried as-is (no re-downscale)
    assert _md5(copied.get_original_file_path()) == _md5(src)


def _redirect_storage(monkeypatch, storage):
    """Point attachment storage at a tmp directory.

    Patching the single resolver is enough. This used to have to replace
    ``get_file_path`` and ``get_original_file_path`` wholesale, because
    ``base_path`` defaulted to the storage directory and default arguments are
    bound at import -- see ``MdUtils.get_storage_directory``.
    """
    monkeypatch.setattr(mu, "get_storage_directory", lambda: str(storage))


def test_update_image_removes_replaced_files(obj, tmp_path, monkeypatch):
    """Replacing an image with a different extension must not orphan the old
    working copy or its archived original on disk."""
    monkeypatch.setattr(MdModel, "IMAGE_MAX_DIM", 100)
    storage = tmp_path / "storage"
    _redirect_storage(monkeypatch, storage)

    old = obj.add_image(_write_jpeg(tmp_path / "big.jpg", 400, 200))
    old.save()
    old_working = old.get_file_path()
    old_archive = old.get_original_file_path()
    assert os.path.exists(old_working) and os.path.exists(old_archive)

    src = tmp_path / "small.png"
    Image.new("RGB", (50, 30), (10, 20, 30)).save(str(src))
    new = obj.update_image(str(src))
    new.save()

    assert not os.path.exists(old_working)
    assert not os.path.exists(old_archive)
    new_working = new.get_file_path()
    assert new_working.endswith(".png") and os.path.exists(new_working)
    assert not os.path.exists(new.get_original_file_path())  # small: no archive


def test_update_image_same_extension_overwrites(obj, tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    _redirect_storage(monkeypatch, storage)

    first = obj.add_image(_write_jpeg(tmp_path / "a.jpg", 60, 40))
    first.save()
    second = obj.update_image(_write_jpeg(tmp_path / "b.jpg", 80, 20))
    second.save()

    with Image.open(second.get_file_path()) as img:
        assert img.size == (80, 20)
    assert MdModel.MdImage.select().where(MdModel.MdImage.object == obj).count() == 1


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
