"""
Test suite for format handler components

Tests cover:
- TPS format reading and parsing
- NTS format reading and parsing (header layouts, dimension, invertY, comments)
- X1Y1 format reading and parsing (2D/3D, landmark count, invertY, errors)
- Morphologika format reading and parsing
- Object name extraction
- Landmark data extraction
- Wireframe/edge list extraction
- Variable/property extraction
"""

import os
import tempfile

import pytest

from components.formats.morphologika import Morphologika
from components.formats.nts import NTS
from components.formats.tps import TPS
from components.formats.x1y1 import X1Y1


class TestTPSFormat:
    """Test TPS format handler"""

    def test_tps_basic_parsing(self):
        """Test basic TPS file parsing with 2D data"""
        tps_content = """LM=3
1.0 2.0
3.0 4.0
5.0 6.0
ID=Object1

LM=3
10.0 20.0
30.0 40.0
50.0 60.0
ID=Object2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "TestDataset")

            assert tps.nobjects == 2
            assert tps.nlandmarks == 3
            assert tps.dimension == 2
            assert len(tps.object_name_list) == 2
            assert tps.object_name_list[0] == "Object1"
            assert tps.object_name_list[1] == "Object2"

            # Check landmark data structure
            assert "Object1" in tps.landmark_data
            assert len(tps.landmark_data["Object1"]) == 3
            assert tps.landmark_data["Object1"][0] == [1.0, 2.0]
            assert tps.landmark_data["Object1"][1] == [3.0, 4.0]
            assert tps.landmark_data["Object1"][2] == [5.0, 6.0]

            assert "Object2" in tps.landmark_data
            assert len(tps.landmark_data["Object2"]) == 3
            assert tps.landmark_data["Object2"][0] == [10.0, 20.0]
        finally:
            os.unlink(tps_file)

    def test_tps_3d_data(self):
        """Test TPS file with 3D landmark data"""
        tps_content = """LM=2
1.0 2.0 3.0
4.0 5.0 6.0
ID=Object3D

LM=2
10.0 20.0 30.0
40.0 50.0 60.0
ID=Object3D_2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "TestDataset3D")

            assert tps.dimension == 3
            assert tps.nobjects == 2
            assert tps.nlandmarks == 2

            # Check 3D landmark data
            assert len(tps.landmark_data["Object3D"][0]) == 3
            assert tps.landmark_data["Object3D"][0] == [1.0, 2.0, 3.0]
            assert tps.landmark_data["Object3D"][1] == [4.0, 5.0, 6.0]
        finally:
            os.unlink(tps_file)

    def test_tps_with_image_path(self):
        """Test TPS file with IMAGE field"""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
IMAGE=specimen1.jpg
ID=Specimen1
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "TestDataset")

            assert tps.nobjects == 1
            assert "Specimen1" in tps.object_images
            assert tps.object_images["Specimen1"] == "specimen1.jpg"
        finally:
            os.unlink(tps_file)

    def test_tps_with_comment(self):
        """Test TPS file with COMMENT field"""
        tps_content = """LM=2
1.0 2.0
3.0 4.0
ID=TestObj
COMMENT=This is a test comment
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "TestDataset")

            assert tps.nobjects == 1
            assert "TestObj" in tps.object_comment
            assert "test comment" in tps.object_comment["TestObj"]
        finally:
            os.unlink(tps_file)

    def test_tps_without_id_uses_dataset_name(self):
        """Test TPS file without ID uses dataset name + counter"""
        tps_content = """LM=2
1.0 2.0
3.0 4.0

LM=2
5.0 6.0
7.0 8.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "MyDataset")

            assert tps.nobjects == 2
            assert "MyDataset_1" in tps.object_name_list
            assert "MyDataset_2" in tps.object_name_list
        finally:
            os.unlink(tps_file)

    def test_tps_inverty_flag(self):
        """Test TPS file with invertY flag for 2D data"""
        tps_content = """LM=2
10.0 20.0
30.0 40.0
ID=TestInvert
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tps", delete=False) as f:
            f.write(tps_content)
            f.flush()
            tps_file = f.name

        try:
            tps = TPS(tps_file, "TestDataset", invertY=True)

            assert tps.dimension == 2
            # Y coordinates should be inverted
            assert tps.landmark_data["TestInvert"][0][1] == -20.0
            assert tps.landmark_data["TestInvert"][1][1] == -40.0
            # X coordinates should remain the same
            assert tps.landmark_data["TestInvert"][0][0] == 10.0
            assert tps.landmark_data["TestInvert"][1][0] == 30.0
        finally:
            os.unlink(tps_file)


class TestNTSFormat:
    """Test NTS format handler.

    The header is positional, e.g. ``1 2L 6 0 dim=2``: a matrix marker, the
    object count with a row-name flag (``L`` = names on their own line, ``b``/
    ``e`` = at the row's start/end), the variable count, and the dimension.
    """

    @staticmethod
    def _write(tmp_path, content):
        path = tmp_path / "test.nts"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_nts_parses_header_and_rows(self, tmp_path):
        content = "1 2L 6 0 dim=2\nObjA ObjB\n1.0 2.0 3.0 4.0 5.0 6.0\n7.0 8.0 9.0 10.0 11.0 12.0\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.dimension == 2
        assert nts.nobjects == 2
        assert nts.object_name_list == ["ObjA", "ObjB"]
        assert nts.landmark_data["ObjA"] == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        assert nts.landmark_data["ObjB"] == [[7.0, 8.0], [9.0, 10.0], [11.0, 12.0]]

    def test_nts_reports_landmark_count(self, tmp_path):
        """nlandmarks is variables / dimension.

        Regression: the count was computed behind a guard that read a stale local
        `dimension` (only self.dimension was ever updated), so the guard was
        always false and nlandmarks stayed 0 for every NTS file.
        """
        content = "1 2L 6 0 dim=2\nObjA ObjB\n1.0 2.0 3.0 4.0 5.0 6.0\n7.0 8.0 9.0 10.0 11.0 12.0\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.nlandmarks == 3
        assert nts.nlandmarks == len(nts.landmark_data["ObjA"])

    def test_nts_row_names_at_beginning(self, tmp_path):
        """``b`` flag: each data row starts with its object name."""
        content = "1 2b 4 0 dim=2\nObjA 1.0 2.0 3.0 4.0\nObjB 5.0 6.0 7.0 8.0\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.object_name_list == ["ObjA", "ObjB"]
        assert nts.landmark_data["ObjA"] == [[1.0, 2.0], [3.0, 4.0]]
        assert nts.landmark_data["ObjB"] == [[5.0, 6.0], [7.0, 8.0]]

    def test_nts_row_names_at_ending(self, tmp_path):
        """``e`` flag: each data row ends with its object name."""
        content = "1 2e 4 0 dim=2\n1.0 2.0 3.0 4.0 ObjA\n5.0 6.0 7.0 8.0 ObjB\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.object_name_list == ["ObjA", "ObjB"]
        assert nts.landmark_data["ObjA"] == [[1.0, 2.0], [3.0, 4.0]]

    def test_nts_generates_names_when_none_supplied(self, tmp_path):
        """No row-name flag and no name line: names fall back to dataset_index."""
        content = "1 2 4 0 dim=2\n1.0 2.0 3.0 4.0\n5.0 6.0 7.0 8.0\n"
        nts = NTS(self._write(tmp_path, content), "MyDS")

        assert nts.object_name_list == ["MyDS_1", "MyDS_2"]
        assert nts.landmark_data["MyDS_1"] == [[1.0, 2.0], [3.0, 4.0]]

    def test_nts_3d_dimension(self, tmp_path):
        content = "1 1L 6 0 dim=3\nObjA\n1.0 2.0 3.0 4.0 5.0 6.0\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.dimension == 3
        assert nts.nlandmarks == 2
        assert nts.landmark_data["ObjA"] == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]

    def test_nts_invert_y_negates_y_for_2d(self, tmp_path):
        content = "1 1L 4 0 dim=2\nObjA\n1.0 2.0 3.0 4.0\n"
        nts = NTS(self._write(tmp_path, content), "ds", invertY=True)

        assert nts.landmark_data["ObjA"] == [[1.0, -2.0], [3.0, -4.0]]

    def test_nts_collects_quoted_comment_lines(self, tmp_path):
        content = '"a header comment"\n1 1L 4 0 dim=2\nObjA\n1.0 2.0 3.0 4.0\n'
        nts = NTS(self._write(tmp_path, content), "ds")

        assert "a header comment" in nts.description
        assert nts.object_name_list == ["ObjA"]

    def test_nts_empty_matrix_returns_no_objects(self, tmp_path):
        """A 0-object / 0-variable header short-circuits without objects."""
        content = "1 0 0 0 dim=2\n"
        nts = NTS(self._write(tmp_path, content), "ds")

        assert nts.nobjects == 0
        assert nts.landmark_data == {}


class TestX1Y1Format:
    """Test X1Y1 format handler.

    X1Y1 is a tab-separated table: a header row of column names (a name column
    followed by coordinate columns ``X1 Y1 X2 Y2 ...`` for 2D or ``X1 Y1 Z1 ...``
    for 3D), then one object per row. Dimension is inferred from the third
    coordinate column: for 2D it is ``X2`` (starts with ``x`` -> 2D); for 3D it
    is ``Z1`` (does not start with ``x`` -> 3D).
    """

    @staticmethod
    def _write(tmp_path, content):
        path = tmp_path / "test.x1y1"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_x1y1_basic_2d_parsing(self, tmp_path):
        content = "name\tX1\tY1\tX2\tY2\nObj1\t1.0\t2.0\t3.0\t4.0\nObj2\t5.0\t6.0\t7.0\t8.0\n"
        x = X1Y1(self._write(tmp_path, content), "ds")

        assert x.dimension == 2
        assert x.nobjects == 2
        assert x.object_name_list == ["Obj1", "Obj2"]
        assert x.landmark_data["Obj1"] == [[1.0, 2.0], [3.0, 4.0]]
        assert x.landmark_data["Obj2"] == [[5.0, 6.0], [7.0, 8.0]]

    def test_x1y1_reports_landmark_count(self, tmp_path):
        """nlandmarks is coordinate columns / dimension.

        Regression: the count was computed and discarded, so nlandmarks stayed 0
        for every X1Y1 file (the same latent bug fixed earlier in nts.py).
        ModanController.import_dataset feeds this value into build_curve_config.
        """
        content = "name\tX1\tY1\tX2\tY2\nObj1\t1.0\t2.0\t3.0\t4.0\n"
        x = X1Y1(self._write(tmp_path, content), "ds")

        assert x.nlandmarks == 2
        assert x.nlandmarks == len(x.landmark_data["Obj1"])

    def test_x1y1_3d_parsing(self, tmp_path):
        content = "name\tX1\tY1\tZ1\tX2\tY2\tZ2\nObj1\t1.0\t2.0\t3.0\t4.0\t5.0\t6.0\n"
        x = X1Y1(self._write(tmp_path, content), "ds")

        assert x.dimension == 3
        assert x.nlandmarks == 2
        assert x.landmark_data["Obj1"] == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]

    def test_x1y1_invert_y_negates_y_for_2d(self, tmp_path):
        content = "name\tX1\tY1\tX2\tY2\nObj1\t1.0\t2.0\t3.0\t4.0\n"
        x = X1Y1(self._write(tmp_path, content), "ds", invertY=True)

        assert x.landmark_data["Obj1"] == [[1.0, -2.0], [3.0, -4.0]]

    def test_x1y1_skips_comment_and_quoted_lines(self, tmp_path):
        content = "name\tX1\tY1\tX2\tY2\n# a comment\nObj1\t1.0\t2.0\t3.0\t4.0\n'quoted'\n"
        x = X1Y1(self._write(tmp_path, content), "ds")

        assert x.object_name_list == ["Obj1"]
        assert x.nobjects == 1

    def test_x1y1_empty_file_raises(self, tmp_path):
        with pytest.raises(ValueError):
            X1Y1(self._write(tmp_path, ""), "ds")

    def test_x1y1_malformed_header_raises(self, tmp_path):
        """A header with fewer than 3 coordinate columns is rejected."""
        content = "name\tX1\tY1\nObj1\t1.0\t2.0\n"
        with pytest.raises(ValueError):
            X1Y1(self._write(tmp_path, content), "ds")


class TestMorphologikaFormat:
    """Test Morphologika format handler"""

    def test_morphologika_basic_parsing(self):
        """Test basic Morphologika file parsing"""
        morph_content = """[Individuals]
2

[Landmarks]
3

[Dimensions]
2

[Names]
Object1
Object2

[Rawpoints]
1.0 2.0
3.0 4.0
5.0 6.0
10.0 20.0
30.0 40.0
50.0 60.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(morph_content)
            f.flush()
            morph_file = f.name

        try:
            morph = Morphologika(morph_file, "Test Dataset")

            assert morph.nobjects == 2
            assert morph.nlandmarks == 3
            assert morph.dimension == 2
            assert len(morph.object_name_list) == 2
            assert morph.object_name_list[0] == "Object1"
            assert morph.object_name_list[1] == "Object2"

            # Check landmark data
            assert "Object1" in morph.landmark_data
            assert len(morph.landmark_data["Object1"]) == 3
            assert morph.landmark_data["Object1"][0] == ["1.0", "2.0"]

            assert "Object2" in morph.landmark_data
            assert len(morph.landmark_data["Object2"]) == 3
        finally:
            os.unlink(morph_file)

    def test_morphologika_with_wireframe(self):
        """Test Morphologika file with wireframe"""
        morph_content = """[Individuals]
1

[Landmarks]
3

[Dimensions]
2

[Names]
Object1

[Rawpoints]
1.0 2.0
3.0 4.0
5.0 6.0

[Wireframe]
1 2
2 3
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(morph_content)
            f.flush()
            morph_file = f.name

        try:
            morph = Morphologika(morph_file, "Test Dataset")

            assert len(morph.edge_list) == 2
            assert [1, 2] in morph.edge_list
            assert [2, 3] in morph.edge_list
        finally:
            os.unlink(morph_file)

    def test_morphologika_with_labels(self):
        """Test Morphologika file with labels and label values"""
        morph_content = """[Individuals]
2

[Landmarks]
2

[Dimensions]
2

[Names]
Object1
Object2

[Rawpoints]
1.0 2.0
3.0 4.0
10.0 20.0
30.0 40.0

[Labels]
Sex Age

[Labelvalues]
Male 25
Female 30
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(morph_content)
            f.flush()
            morph_file = f.name

        try:
            morph = Morphologika(morph_file, "Test Dataset")

            assert len(morph.variablename_list) == 2
            assert "Sex" in morph.variablename_list
            assert "Age" in morph.variablename_list

            assert len(morph.property_list_list) == 2
            assert morph.property_list_list[0] == ["Male", "25"]
            assert morph.property_list_list[1] == ["Female", "30"]
        finally:
            os.unlink(morph_file)

    def test_morphologika_with_images(self):
        """Test Morphologika file with images"""
        morph_content = """[Individuals]
2

[Landmarks]
2

[Dimensions]
2

[Names]
Object1
Object2

[Rawpoints]
1.0 2.0
3.0 4.0
10.0 20.0
30.0 40.0

[Images]
image1.jpg
image2.jpg
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(morph_content)
            f.flush()
            morph_file = f.name

        try:
            morph = Morphologika(morph_file, "Test Dataset")

            assert len(morph.object_images) == 2
            assert morph.object_images["Object1"] == "image1.jpg"
            assert morph.object_images["Object2"] == "image2.jpg"
        finally:
            os.unlink(morph_file)
