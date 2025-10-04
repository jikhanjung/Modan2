"""Tests for ModanWidgets module - UI widgets."""
import pytest
from unittest.mock import Mock
from datetime import datetime
from PyQt5.QtCore import Qt

import ModanWidgets as mw
import MdModel

@pytest.fixture
def mock_dataset():
    dataset = Mock(spec=MdModel.MdDataset)
    dataset.dataset_name = "Test Dataset"
    dataset.dimension = 2
    dataset.created_at = datetime(2025, 1, 1, 12, 0, 0)
    dataset.object_list = Mock()
    dataset.object_list.count.return_value = 10
    dataset.object_list.first.return_value = None
    dataset.analyses = []
    return dataset

class TestDatasetTreeWidget:
    def test_init(self, qtbot):
        widget = mw.DatasetTreeWidget()
        qtbot.addWidget(widget)
        assert widget.columnCount() == 4
    
    def test_add_dataset(self, qtbot, mock_dataset):
        widget = mw.DatasetTreeWidget()
        qtbot.addWidget(widget)
        item = widget.add_dataset(mock_dataset)
        assert item.text(0) == "Test Dataset"
        assert item.text(2) == "2D"
