"""
Tests for object overlay persistence feature (Issue #14).

This test file verifies that the object preview overlay visibility
preference persists across object selections and application restarts.
"""
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from MdModel import MdDataset, MdObject


class TestObjectOverlayPersistence:
    """Test suite for object overlay visibility persistence"""

    def test_initial_state_defaults_to_true(self, qtbot, main_window):
        """Test that overlay auto-show defaults to True on first run"""
        assert main_window.object_overlay_auto_show is True
        assert main_window.overlay_toggle_button.text() == "×"

    def test_toggle_changes_state(self, qtbot, main_window):
        """Test that clicking toggle button changes the auto-show state"""
        # Initial state: auto-show ON
        assert main_window.object_overlay_auto_show is True

        # Click the toggle button
        QTest.mouseClick(main_window.overlay_toggle_button, Qt.LeftButton)
        qtbot.wait(50)

        # State should be OFF now
        assert main_window.object_overlay_auto_show is False
        assert main_window.overlay_toggle_button.text() == "👁"

        # Click again
        QTest.mouseClick(main_window.overlay_toggle_button, Qt.LeftButton)
        qtbot.wait(50)

        # State should be ON again
        assert main_window.object_overlay_auto_show is True
        assert main_window.overlay_toggle_button.text() == "×"

    def test_overlay_stays_hidden_when_disabled(self, qtbot, main_window, sample_dataset):
        """Test that overlay stays hidden across object selections when disabled"""
        # Setup: Select dataset and ensure we have at least 2 objects
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        if len(sample_dataset.object_list) < 2:
            pytest.skip("Test requires at least 2 objects in dataset")

        first_object = list(sample_dataset.object_list)[0]
        second_object = list(sample_dataset.object_list)[1]

        # Select first object - overlay should show
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)
        assert main_window.object_overlay.isVisible()

        # Disable auto-show
        QTest.mouseClick(main_window.overlay_toggle_button, Qt.LeftButton)
        qtbot.wait(50)
        assert not main_window.object_overlay_auto_show
        assert not main_window.object_overlay.isVisible()

        # Select second object - overlay should stay hidden
        main_window.selected_object = second_object
        main_window.show_object(second_object)
        qtbot.wait(50)
        assert not main_window.object_overlay.isVisible()

        # Select first object again - overlay should still be hidden
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)
        assert not main_window.object_overlay.isVisible()

    def test_overlay_shows_when_enabled(self, qtbot, main_window, sample_dataset):
        """Test that overlay shows when re-enabled"""
        # Setup: Disable auto-show first
        main_window.object_overlay_auto_show = False
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        if not sample_dataset.object_list:
            pytest.skip("Test requires at least 1 object in dataset")

        first_object = list(sample_dataset.object_list)[0]

        # Select object with auto-show disabled - overlay hidden
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)
        assert not main_window.object_overlay.isVisible()

        # Enable auto-show by clicking toggle
        QTest.mouseClick(main_window.overlay_toggle_button, Qt.LeftButton)
        qtbot.wait(50)

        # Overlay should now be visible
        assert main_window.object_overlay_auto_show is True
        assert main_window.object_overlay.isVisible()

    def test_keyboard_shortcut_toggles_overlay(self, qtbot, main_window, sample_dataset):
        """Test that Ctrl+P keyboard shortcut toggles the overlay"""
        # Setup
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        if not sample_dataset.object_list:
            pytest.skip("Test requires at least 1 object in dataset")

        first_object = list(sample_dataset.object_list)[0]
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)

        # Initial state: auto-show ON, overlay visible
        assert main_window.object_overlay_auto_show is True
        assert main_window.object_overlay.isVisible()

        # Press Ctrl+P to toggle OFF
        QTest.keyPress(main_window, Qt.Key_P, Qt.ControlModifier)
        qtbot.wait(50)
        assert main_window.object_overlay_auto_show is False
        assert not main_window.object_overlay.isVisible()

        # Press Ctrl+P again to toggle ON
        QTest.keyPress(main_window, Qt.Key_P, Qt.ControlModifier)
        qtbot.wait(50)
        assert main_window.object_overlay_auto_show is True
        assert main_window.object_overlay.isVisible()

    def test_preference_persists_to_config(self, qtbot, main_window):
        """Test that preference is saved to config file"""
        # Toggle to OFF
        main_window.object_overlay_auto_show = False
        main_window.toggle_object_overlay_auto_show()  # Toggles to ON and saves

        # Verify it was saved
        if hasattr(main_window.m_app, 'settings'):
            saved_value = main_window.m_app.settings.value("ObjectOverlay/AutoShow", True)
            assert saved_value is True

    def test_preference_loads_from_config(self, qtbot, main_window_factory):
        """Test that preference is loaded from config on startup"""
        # Create a config with auto-show disabled
        config = {
            "ui": {
                "object_overlay_auto_show": False,
                "remember_geometry": False
            }
        }

        # Create main window with this config
        window = main_window_factory(config)

        # Verify the preference was loaded
        assert window.object_overlay_auto_show is False
        assert window.overlay_toggle_button.text() == "👁"

    def test_overlay_hidden_on_no_selection(self, qtbot, main_window, sample_dataset):
        """Test that overlay is hidden when no object is selected"""
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        # Clear selection
        main_window.selected_object = None
        main_window.clear_object_view()
        qtbot.wait(50)

        # Overlay should be hidden
        assert not main_window.object_overlay.isVisible()

    def test_button_appearance_changes_with_state(self, qtbot, main_window):
        """Test that button appearance changes based on auto-show state"""
        # Initial state: auto-show ON, red × button
        assert main_window.object_overlay_auto_show is True
        assert main_window.overlay_toggle_button.text() == "×"
        # Check for red background color in stylesheet
        assert "#ff6b6b" in main_window.overlay_toggle_button.styleSheet()

        # Toggle to OFF
        QTest.mouseClick(main_window.overlay_toggle_button, Qt.LeftButton)
        qtbot.wait(50)

        # Button should now show green 👁
        assert main_window.overlay_toggle_button.text() == "👁"
        assert "#4CAF50" in main_window.overlay_toggle_button.styleSheet()

    def test_dataset_switch_preserves_preference(self, qtbot, main_window, sample_dataset):
        """Test that overlay preference persists when switching datasets"""
        # Create a second dataset
        dataset2 = MdDataset.create(
            dataset_name="Test Dataset 2",
            dimension=2
        )

        try:
            # Disable auto-show
            main_window.object_overlay_auto_show = False
            main_window.selected_dataset = sample_dataset
            main_window.load_object()

            # Switch to dataset2
            main_window.selected_dataset = dataset2
            main_window.load_object()
            qtbot.wait(50)

            # Preference should still be OFF
            assert main_window.object_overlay_auto_show is False

        finally:
            # Cleanup
            dataset2.delete_instance(recursive=True)

    def test_overlay_position_persists_across_selections(self, qtbot, main_window, sample_dataset):
        """Test that overlay position persists when switching between objects"""
        # Setup: Select dataset and ensure we have at least 2 objects
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        if len(sample_dataset.object_list) < 2:
            pytest.skip("Test requires at least 2 objects in dataset")

        first_object = list(sample_dataset.object_list)[0]
        second_object = list(sample_dataset.object_list)[1]

        # Select first object - overlay should show
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)

        # Move overlay to a custom position
        custom_x, custom_y = 100, 100
        main_window.object_overlay.move(custom_x, custom_y)
        qtbot.wait(10)

        # Trigger the save callback (simulating user drag completion)
        main_window.on_overlay_moved()
        qtbot.wait(10)

        # Verify position was saved
        assert main_window.object_overlay_position == [custom_x, custom_y]

        # Select second object
        main_window.selected_object = second_object
        main_window.show_object(second_object)
        qtbot.wait(50)

        # Verify overlay is at the same custom position
        pos = main_window.object_overlay.pos()
        assert pos.x() == custom_x
        assert pos.y() == custom_y

    def test_overlay_position_saved_to_config(self, qtbot, main_window):
        """Test that overlay position is saved to config file"""
        # Move overlay to a custom position
        custom_x, custom_y = 150, 200
        main_window.object_overlay.move(custom_x, custom_y)
        qtbot.wait(10)

        # Trigger the save by calling on_overlay_moved
        main_window.on_overlay_moved()
        qtbot.wait(10)

        # Verify position was saved to internal state
        assert main_window.object_overlay_position == [custom_x, custom_y]

        # Verify setValue was called on settings (mock will record this)
        if hasattr(main_window.m_app, "settings"):
            # Check that setValue was called with the correct arguments
            main_window.m_app.settings.setValue.assert_any_call("ObjectOverlay/Position", [custom_x, custom_y])

    def test_overlay_position_loaded_from_config(self, qtbot, main_window_factory, sample_dataset):
        """Test that overlay position is loaded from config on startup"""
        # Create a config with custom position
        custom_position = [250, 300]
        config = {
            "ui": {
                "object_overlay_auto_show": True,
                "object_overlay_position": custom_position,
                "remember_geometry": False
            }
        }

        # Create main window with this config
        window = main_window_factory(config)

        # Verify the position was loaded
        assert window.object_overlay_position == custom_position

        # Setup and show an object
        window.selected_dataset = sample_dataset
        window.load_object()

        if not sample_dataset.object_list:
            pytest.skip("Test requires at least 1 object in dataset")

        first_object = list(sample_dataset.object_list)[0]
        window.selected_object = first_object
        window.show_object(first_object)
        qtbot.wait(50)

        # Verify overlay is at the loaded position
        pos = window.object_overlay.pos()
        assert pos.x() == custom_position[0]
        assert pos.y() == custom_position[1]

    def test_overlay_uses_default_position_on_first_run(self, qtbot, main_window, sample_dataset):
        """Test that overlay uses default bottom-right position when no saved position exists"""
        # Ensure no saved position
        main_window.object_overlay_position = None

        # Setup and show an object
        main_window.selected_dataset = sample_dataset
        main_window.load_object()

        if not sample_dataset.object_list:
            pytest.skip("Test requires at least 1 object in dataset")

        first_object = list(sample_dataset.object_list)[0]
        main_window.selected_object = first_object
        main_window.show_object(first_object)
        qtbot.wait(50)

        # Verify overlay is in bottom-right corner (with margin)
        parent_size = main_window.dataset_view.size()
        overlay_size = main_window.object_overlay.size()
        margin = 10

        expected_x = parent_size.width() - overlay_size.width() - margin
        expected_y = parent_size.height() - overlay_size.height() - margin

        pos = main_window.object_overlay.pos()
        # Allow some tolerance for window manager differences
        assert abs(pos.x() - expected_x) < 20
        assert abs(pos.y() - expected_y) < 20

    def test_overlay_position_callback(self, qtbot, main_window):
        """Test that on_overlay_moved callback saves position"""
        # Move overlay to a position
        initial_x, initial_y = 50, 50
        main_window.object_overlay.move(initial_x, initial_y)
        qtbot.wait(10)

        # Manually call the callback as if user finished dragging
        main_window.on_overlay_moved()
        qtbot.wait(10)

        # Verify position was saved
        assert main_window.object_overlay_position == [initial_x, initial_y]

        # Move to new position
        new_x, new_y = 200, 250
        main_window.object_overlay.move(new_x, new_y)
        qtbot.wait(10)

        # Call callback again
        main_window.on_overlay_moved()
        qtbot.wait(10)

        # Verify new position was saved
        assert main_window.object_overlay_position == [new_x, new_y]
