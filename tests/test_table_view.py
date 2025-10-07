"""
Test suite for MdTableView and MdTableModel components

Tests cover:
- MdTableModel data management
- MdTableView basic functionality
- Selection modes (cells vs rows)
- Context menu actions

Note: Full integration testing with drag-and-drop and complex UI interactions
requires comprehensive setup. These tests focus on core functionality.
"""

from PyQt5.QtCore import Qt

from components.widgets.table_view import MdTableModel, MdTableView


class TestMdTableModel:
    """Test MdTableModel data model"""

    def test_model_creation(self):
        """Test that MdTableModel can be created"""
        model = MdTableModel()
        assert model is not None

    def test_model_with_data(self):
        """Test model with initial data"""
        data = [
            ["Row1Col1", "Row1Col2"],
            ["Row2Col1", "Row2Col2"],
        ]
        model = MdTableModel(data=data)

        assert model.rowCount() == 2
        assert model.columnCount() == 2

    def test_load_data(self):
        """Test loading data into model"""
        model = MdTableModel()
        data = [
            ["A", "B", "C"],
            ["D", "E", "F"],
            ["G", "H", "I"],
        ]
        model.load_data(data)

        assert model.rowCount() == 3
        assert model.columnCount() == 3

    def test_data_retrieval(self):
        """Test retrieving data from model"""
        data = [["Value1", "Value2"]]
        model = MdTableModel(data=data)

        index = model.index(0, 0)
        assert model.data(index, Qt.DisplayRole) == "Value1"

        index = model.index(0, 1)
        assert model.data(index, Qt.DisplayRole) == "Value2"

    def test_set_data(self):
        """Test setting data in model"""
        data = [["Original", "Data"]]
        model = MdTableModel(data=data)

        index = model.index(0, 0)
        model.setData(index, "Modified", Qt.EditRole)

        assert model.data(index, Qt.DisplayRole) == "Modified"

    def test_header_data(self):
        """Test header data retrieval"""
        model = MdTableModel()
        model._hheader_data = ["Col1", "Col2", "Col3"]

        assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Col1"
        assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "Col2"
        assert model.headerData(2, Qt.Horizontal, Qt.DisplayRole) == "Col3"

    def test_row_header_numbers(self):
        """Test row headers show row numbers"""
        data = [["A"], ["B"], ["C"]]
        model = MdTableModel(data=data)

        assert model.headerData(0, Qt.Vertical, Qt.DisplayRole) == "1"
        assert model.headerData(1, Qt.Vertical, Qt.DisplayRole) == "2"
        assert model.headerData(2, Qt.Vertical, Qt.DisplayRole) == "3"

    def test_flags_contains_item_flags(self):
        """Test that cells have proper item flags"""
        data = [["Test"]]
        model = MdTableModel(data=data)

        index = model.index(0, 0)
        flags = model.flags(index)

        # Should have at least ItemIsEnabled and ItemIsSelectable
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsSelectable

    def test_set_columns_uneditable(self):
        """Test making specific columns uneditable"""
        data = [["Col0", "Col1", "Col2"]]
        model = MdTableModel(data=data)

        model.set_columns_uneditable([0, 2])

        # Column 0 should be uneditable
        index0 = model.index(0, 0)
        assert not (model.flags(index0) & Qt.ItemIsEditable)

        # Column 1 should be editable
        index1 = model.index(0, 1)
        assert model.flags(index1) & Qt.ItemIsEditable

        # Column 2 should be uneditable
        index2 = model.index(0, 2)
        assert not (model.flags(index2) & Qt.ItemIsEditable)

    def test_uneditable_columns_initial(self):
        """Test that uneditable columns list is initialized"""
        model = MdTableModel()

        # Model has default uneditable columns
        assert hasattr(model, "_uneditable_columns")
        assert isinstance(model._uneditable_columns, list)


class TestMdTableView:
    """Test MdTableView widget"""

    def test_view_creation(self, qtbot):
        """Test that MdTableView can be created"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert view is not None

    def test_vertical_header_hidden(self, qtbot):
        """Test that vertical header is hidden by default"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert view.verticalHeader().isHidden()

    def test_has_context_menu_policy(self, qtbot):
        """Test that context menu policy is set"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert view.contextMenuPolicy() == Qt.CustomContextMenu

    def test_cells_selection_mode(self, qtbot):
        """Test setting cells selection mode"""
        view = MdTableView()
        qtbot.addWidget(view)

        view.set_cells_selection_mode()

        assert view.selection_mode == "Cells"
        assert not view.dragEnabled()
        assert view.selectionBehavior() == view.SelectItems

    def test_rows_selection_mode(self, qtbot):
        """Test setting rows selection mode"""
        view = MdTableView()
        qtbot.addWidget(view)

        view.set_rows_selection_mode()

        assert view.selection_mode == "Rows"
        assert view.dragEnabled()
        assert view.selectionBehavior() == view.SelectRows

    def test_has_copy_action(self, qtbot):
        """Test that copy action is available"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert hasattr(view, "copy_action")
        assert view.copy_action is not None

    def test_has_paste_action(self, qtbot):
        """Test that paste action is available"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert hasattr(view, "paste_action")
        assert view.paste_action is not None

    def test_has_fill_sequence_action(self, qtbot):
        """Test that fill sequence action is available"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert hasattr(view, "fill_sequence_action")
        assert view.fill_sequence_action is not None

    def test_has_fill_action(self, qtbot):
        """Test that fill value action is available"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert hasattr(view, "fill_action")
        assert view.fill_action is not None

    def test_has_clear_action(self, qtbot):
        """Test that clear cells action is available"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert hasattr(view, "clear_cells_action")
        assert view.clear_cells_action is not None

    def test_selected_object_row_initial(self, qtbot):
        """Test initial selected object row"""
        view = MdTableView()
        qtbot.addWidget(view)

        assert view.selected_object_row == -1

    def test_set_selected_object_row(self, qtbot):
        """Test setting selected object row"""
        view = MdTableView()
        qtbot.addWidget(view)

        view.setSelectedObjectRow(5)
        assert view.selected_object_row == 5

        view.setSelectedObjectRow(-1)
        assert view.selected_object_row == -1


class TestMdTableViewAndModel:
    """Test MdTableView and MdTableModel integration"""

    def test_view_with_model(self, qtbot):
        """Test connecting view with model"""
        view = MdTableView()
        qtbot.addWidget(view)

        data = [
            ["A1", "A2"],
            ["B1", "B2"],
        ]
        model = MdTableModel(data=data)
        model._hheader_data = ["Col1", "Col2"]  # Set headers to avoid IndexError
        view.setModel(model)

        assert view.model() == model
        assert view.model().rowCount() == 2
        assert view.model().columnCount() == 2

    def test_view_displays_model_data(self, qtbot):
        """Test that view displays model data"""
        view = MdTableView()
        qtbot.addWidget(view)

        data = [["Value"]]
        model = MdTableModel(data=data)
        model._hheader_data = ["Col1"]  # Set headers to avoid IndexError
        view.setModel(model)

        index = model.index(0, 0)
        assert model.data(index, Qt.DisplayRole) == "Value"
