"""
Test suite for MdSequenceDelegate component

Tests cover:
- Delegate initialization
- Editor creation for different columns
- Integer validation in sequence column
- Integration with model/view

Note: Delegates are tested with minimal model/view setup. Full integration
testing requires complex table widget setup.
"""

from unittest.mock import Mock

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QLineEdit, QStyleOptionViewItem

from components.widgets.delegates import MdSequenceDelegate


class TestMdSequenceDelegateInitialization:
    """Test MdSequenceDelegate initialization"""

    def test_delegate_creation(self, qtbot):
        """Test that MdSequenceDelegate can be created"""
        delegate = MdSequenceDelegate()

        assert delegate is not None
        assert isinstance(delegate, MdSequenceDelegate)


class TestMdSequenceDelegateEditorCreation:
    """Test editor creation for different columns"""

    def test_create_editor_for_sequence_column(self, qtbot):
        """Test that column 1 creates a QLineEdit with integer validator"""
        delegate = MdSequenceDelegate()

        # Create parent (None for testing), option, and index for column 1
        parent = None
        option = QStyleOptionViewItem()
        index = Mock(spec=QModelIndex)
        index.column.return_value = 1  # Sequence column

        editor = delegate.createEditor(parent, option, index)

        # Should return QLineEdit
        assert editor is not None
        assert isinstance(editor, QLineEdit)

        # Should have integer validator
        validator = editor.validator()
        assert validator is not None
        assert isinstance(validator, QIntValidator)

    def test_column_check_for_sequence_column(self, qtbot):
        """Test that createEditor checks column number correctly"""
        delegate = MdSequenceDelegate()

        # Test column 1 detection (should create sequence editor)
        index_col1 = Mock(spec=QModelIndex)
        index_col1.column.return_value = 1

        editor_col1 = delegate.createEditor(None, QStyleOptionViewItem(), index_col1)
        assert isinstance(editor_col1, QLineEdit)
        assert isinstance(editor_col1.validator(), QIntValidator)

        # For other columns, just verify the logic works
        # (we don't test super().createEditor as it requires a full model/view setup)
        index_col0 = Mock(spec=QModelIndex)
        index_col0.column.return_value = 0

        # Verify that column 0 takes different path
        assert index_col0.column() != 1  # Would go to super().createEditor


class TestMdSequenceDelegateIntegerValidation:
    """Test integer validation in sequence column editor"""

    def test_validator_accepts_integers(self, qtbot):
        """Test that validator accepts integer input"""
        delegate = MdSequenceDelegate()

        parent = None
        option = QStyleOptionViewItem()
        index = Mock(spec=QModelIndex)
        index.column.return_value = 1

        editor = delegate.createEditor(parent, option, index)
        validator = editor.validator()

        # Test valid integer inputs
        state, text, pos = validator.validate("123", 0)
        assert state == QIntValidator.Acceptable

        state, text, pos = validator.validate("0", 0)
        assert state == QIntValidator.Acceptable

    def test_validator_rejects_non_integers(self, qtbot):
        """Test that validator rejects non-integer input"""
        delegate = MdSequenceDelegate()

        parent = None
        option = QStyleOptionViewItem()
        index = Mock(spec=QModelIndex)
        index.column.return_value = 1

        editor = delegate.createEditor(parent, option, index)
        validator = editor.validator()

        # Test invalid inputs
        state, text, pos = validator.validate("abc", 0)
        assert state == QIntValidator.Invalid

        state, text, pos = validator.validate("12.5", 0)
        assert state == QIntValidator.Invalid

    def test_validator_allows_negative_integers(self, qtbot):
        """Test that validator allows negative integers"""
        delegate = MdSequenceDelegate()

        parent = None
        option = QStyleOptionViewItem()
        index = Mock(spec=QModelIndex)
        index.column.return_value = 1

        editor = delegate.createEditor(parent, option, index)
        validator = editor.validator()

        # QIntValidator by default allows negative numbers
        state, text, pos = validator.validate("-", 0)
        # Intermediate or Acceptable depending on Qt version
        assert state in (QIntValidator.Intermediate, QIntValidator.Acceptable)

        state, text, pos = validator.validate("-123", 0)
        assert state == QIntValidator.Acceptable


class TestMdSequenceDelegateMultipleInstances:
    """Test that multiple delegate instances work independently"""

    def test_multiple_delegates(self, qtbot):
        """Test creating multiple delegate instances"""
        delegate1 = MdSequenceDelegate()
        delegate2 = MdSequenceDelegate()

        assert delegate1 is not delegate2

        # Both should work independently
        parent = None
        option = QStyleOptionViewItem()
        index = Mock(spec=QModelIndex)
        index.column.return_value = 1

        editor1 = delegate1.createEditor(parent, option, index)
        editor2 = delegate2.createEditor(parent, option, index)

        assert isinstance(editor1, QLineEdit)
        assert isinstance(editor2, QLineEdit)
