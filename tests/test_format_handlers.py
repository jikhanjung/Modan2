"""
Test suite for format handler components (Morphologika)

Tests cover:
- Morphologika format reading and parsing
- Object name extraction
- Landmark data extraction
- Wireframe/edge list extraction
- Variable/property extraction

Note: TPS, NTS, and X1Y1 format handlers require more investigation
of their actual implementation and will be added in future updates.
"""

import os
import tempfile

from components.formats.morphologika import Morphologika


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
