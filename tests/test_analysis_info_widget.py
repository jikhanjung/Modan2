"""
Test suite for AnalysisInfoWidget component

Tests cover:
- Widget initialization
- Tab management (PCA, CVA, MANOVA)
- Analysis display
- Grouping variable selection
- Settings persistence

Note: Full integration testing with matplotlib plots requires complex setup.
These tests focus on core widget functionality and state management.
"""

from unittest.mock import Mock, patch

from PyQt5.QtWidgets import QApplication

from components.widgets.analysis_info import AnalysisInfoWidget


class TestAnalysisInfoWidgetInitialization:
    """Test AnalysisInfoWidget initialization"""

    def test_widget_creation(self, qtbot):
        """Test that AnalysisInfoWidget can be created"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        assert widget is not None
        assert widget.parent == parent

    def test_has_required_widgets(self, qtbot):
        """Test that widget has all required child widgets"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Check basic widgets
        assert hasattr(widget, "edtAnalysisName")
        assert hasattr(widget, "edtSuperimposition")
        assert hasattr(widget, "analysis_tab")

        # Check tab views
        assert hasattr(widget, "PcaView")
        assert hasattr(widget, "CvaView")
        assert hasattr(widget, "ManovaView")

        # Check combo boxes
        assert hasattr(widget, "comboPcaGroupBy")
        assert hasattr(widget, "comboCvaGroupBy")
        assert hasattr(widget, "comboManovaGroupBy")

    def test_has_three_tabs(self, qtbot):
        """Test that analysis tab has PCA, CVA, and MANOVA tabs"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        assert widget.analysis_tab.count() == 3
        assert widget.analysis_tab.tabText(0) == "PCA"
        assert widget.analysis_tab.tabText(1) == "CVA"
        assert widget.analysis_tab.tabText(2) == "MANOVA"

    def test_initial_state(self, qtbot):
        """Test initial widget state"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Superimposition field should be disabled
        assert not widget.edtSuperimposition.isEnabled()

        # Combo boxes should be initially disabled
        assert not widget.comboPcaGroupBy.isEnabled()
        assert not widget.comboCvaGroupBy.isEnabled()
        assert not widget.comboManovaGroupBy.isEnabled()

        # ignore_change flag should start False
        assert widget.ignore_change is False


class TestAnalysisInfoWidgetTabManagement:
    """Test tab switching and management"""

    def test_tab_changed_signal(self, qtbot):
        """Test that tab changed signal is connected"""
        parent = Mock()
        parent.btnAnalysisDetail = Mock()
        parent.btnDataExploration = Mock()

        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Initially on PCA tab, switch away and back to trigger signal
        widget.analysis_tab.setCurrentIndex(1)  # Switch to CVA
        parent.btnAnalysisDetail.setEnabled.reset_mock()
        parent.btnDataExploration.setEnabled.reset_mock()

        # Now switch to PCA tab (index 0)
        widget.analysis_tab.setCurrentIndex(0)

        # PCA tab should enable parent buttons
        parent.btnAnalysisDetail.setEnabled.assert_called_with(True)
        parent.btnDataExploration.setEnabled.assert_called_with(True)

    def test_non_pca_tab_disables_buttons(self, qtbot):
        """Test that non-PCA tabs disable parent buttons"""
        parent = Mock()
        parent.btnAnalysisDetail = Mock()
        parent.btnDataExploration = Mock()

        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Switch to CVA tab (index 1)
        widget.analysis_tab.setCurrentIndex(1)

        # CVA tab should disable parent buttons
        parent.btnAnalysisDetail.setEnabled.assert_called_with(False)
        parent.btnDataExploration.setEnabled.assert_called_with(False)

    def test_manova_tab_disables_buttons(self, qtbot):
        """Test that MANOVA tab disables parent buttons"""
        parent = Mock()
        parent.btnAnalysisDetail = Mock()
        parent.btnDataExploration = Mock()

        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Switch to MANOVA tab (index 2)
        widget.analysis_tab.setCurrentIndex(2)

        # MANOVA tab should disable parent buttons
        parent.btnAnalysisDetail.setEnabled.assert_called_with(False)
        parent.btnDataExploration.setEnabled.assert_called_with(False)


class TestAnalysisInfoWidgetAnalysisDisplay:
    """Test analysis display functionality"""

    def test_set_analysis_basic(self, qtbot):
        """Test setting analysis object updates widget"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Create mock analysis with proper dataset
        analysis = Mock()
        analysis.analysis_name = "Test Analysis"
        analysis.superimposition_method = "Procrustes"
        analysis.cva_group_by = "None"
        analysis.manova_group_by = "None"

        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.get_grouping_variable_index_list.return_value = [0, 1]
        mock_dataset.get_variablename_list.return_value = ["Sex", "Age"]
        analysis.dataset = mock_dataset

        # Set analysis
        widget.set_analysis(analysis)

        # Check that fields are updated
        assert widget.edtAnalysisName.text() == "Test Analysis"
        assert widget.edtSuperimposition.text() == "Procrustes"
        assert widget.analysis == analysis

    def test_set_analysis_populates_combo_boxes(self, qtbot):
        """Test that setting analysis populates grouping variable combo boxes"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Create mock analysis with proper dataset
        analysis = Mock()
        analysis.analysis_name = "Test Analysis"
        analysis.superimposition_method = "Procrustes"
        analysis.cva_group_by = "None"
        analysis.manova_group_by = "None"

        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.get_grouping_variable_index_list.return_value = [0, 1, 2]
        mock_dataset.get_variablename_list.return_value = ["Sex", "Age", "Species"]
        analysis.dataset = mock_dataset

        # Set analysis
        widget.set_analysis(analysis)

        # Check that combo boxes are populated
        assert widget.comboPcaGroupBy.count() == 3
        assert widget.comboCvaGroupBy.count() == 3
        assert widget.comboManovaGroupBy.count() == 3

        # Check items are variable names
        assert widget.comboPcaGroupBy.itemText(0) == "Sex"
        assert widget.comboPcaGroupBy.itemText(1) == "Age"
        assert widget.comboPcaGroupBy.itemText(2) == "Species"

    def test_show_analysis_result_with_no_json(self, qtbot):
        """Test showing analysis with no JSON data (legacy support)"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Create mock analysis with no JSON
        analysis = Mock()
        analysis.analysis_name = "Legacy Analysis"
        analysis.superimposition_method = "Bookstein"
        analysis.object_info_json = None
        analysis.pca_analysis_result_json = None
        analysis.cva_analysis_result_json = None
        analysis.manova_analysis_result_json = None

        widget.analysis = analysis
        widget.show_analysis_result()

        # Should show basic info without errors
        assert widget.edtAnalysisName.text() == "Legacy Analysis"
        assert widget.edtSuperimposition.text() == "Bookstein"


class TestAnalysisInfoWidgetGroupingVariables:
    """Test grouping variable selection"""

    def test_pca_groupby_change_ignored_when_flag_set(self, qtbot):
        """Test that groupby changes are ignored when ignore_change flag is True"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Set ignore_change flag
        widget.ignore_change = True

        # Mock show_analysis_result
        widget.show_analysis_result = Mock()

        # Change combo box
        widget.comboPcaGroupBy_changed()

        # Should not call show_analysis_result
        widget.show_analysis_result.assert_not_called()

    def test_pca_groupby_change_triggers_update(self, qtbot):
        """Test that groupby changes trigger analysis update"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Clear ignore_change flag
        widget.ignore_change = False

        # Mock show_analysis_result
        widget.show_analysis_result = Mock()

        # Change combo box
        widget.comboPcaGroupBy_changed()

        # Should call show_analysis_result
        widget.show_analysis_result.assert_called_once()

    def test_cva_groupby_change_triggers_update(self, qtbot):
        """Test CVA groupby changes trigger analysis update"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        widget.ignore_change = False
        widget.show_analysis_result = Mock()

        widget.comboCvaGroupBy_changed()

        widget.show_analysis_result.assert_called_once()

    def test_manova_groupby_change_triggers_update(self, qtbot):
        """Test MANOVA groupby changes trigger analysis update"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        widget.ignore_change = False
        widget.show_analysis_result = Mock()

        widget.comboManovaGroupBy_changed()

        widget.show_analysis_result.assert_called_once()


class TestAnalysisInfoWidgetSettings:
    """Test settings reading"""

    @patch.object(QApplication, "instance")
    def test_read_settings(self, mock_app_instance, qtbot):
        """Test that read_settings reads from QSettings"""
        # Mock QApplication and settings
        mock_app = Mock()
        mock_settings = Mock()
        mock_settings.value = Mock(side_effect=lambda key, default: default)
        mock_app.settings = mock_settings
        mock_app_instance.return_value = mock_app

        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # read_settings is called in __init__, verify it was called
        assert mock_settings.value.called

    def test_color_list_initialization(self, qtbot):
        """Test that color list is initialized"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        assert hasattr(widget, "color_list")
        assert hasattr(widget, "default_color_list")
        assert len(widget.color_list) > 0

    def test_marker_list_initialization(self, qtbot):
        """Test that marker list is initialized"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        assert hasattr(widget, "marker_list")
        assert len(widget.marker_list) > 0


class TestAnalysisInfoWidgetManovaDisplay:
    """Test MANOVA result display"""

    def test_manova_table_cleared_on_show(self, qtbot):
        """Test that MANOVA table is cleared before showing results"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        # Set up analysis with no MANOVA data
        analysis = Mock()
        analysis.analysis_name = "Test"  # Provide string instead of Mock
        analysis.superimposition_method = "Procrustes"
        analysis.object_info_json = None
        analysis.pca_analysis_result_json = None
        analysis.cva_analysis_result_json = None
        analysis.manova_analysis_result_json = None

        widget.analysis = analysis
        widget.show_analysis_result()

        # Table should be cleared (row count = 0)
        assert widget.tabManovaResult.rowCount() == 0

    def test_manova_table_has_widget(self, qtbot):
        """Test that MANOVA results are displayed in a table widget"""
        parent = Mock()
        widget = AnalysisInfoWidget(parent)
        qtbot.addWidget(widget)

        assert hasattr(widget, "tabManovaResult")
        assert widget.tabManovaResult is not None
