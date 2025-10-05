"""Preferences Dialog for application settings."""

import logging
import os
from pathlib import Path

from PyQt5.QtCore import QPoint, QRect, Qt, QTranslator
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class PreferencesDialog(BaseDialog):
    """Dialog for managing application preferences.

    Features:
    - Window geometry memory settings
    - Toolbar icon size configuration
    - Plot size and color customization
    - Data point marker configuration
    - 2D/3D landmark, wireframe, and index appearance
    - Background color selection
    - Language selection (English/Korean)
    """

    def __init__(self, parent):
        """Initialize preferences dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent, title="Preferences")
        self.parent = parent
        self.m_app = QApplication.instance()

        # Initialize defaults
        self._init_defaults()

        # Create UI
        self._create_widgets()
        self._create_layout()
        self._connect_signals()

        # Load current settings
        self.read_settings()

    def _init_defaults(self):
        """Initialize default preference values."""
        self.m_app.remember_geometry = True
        self.toolbar_icon_small = False
        self.toolbar_icon_medium = False
        self.toolbar_icon_large = False
        self.m_app.plot_size = "medium"

        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.m_app.color_list = self.default_color_list[:]
        self.m_app.marker_list = mu.MARKER_LIST[:]

        self.m_app.landmark_pref = {"2D": {"size": 1, "color": "#0000FF"}, "3D": {"size": 1, "color": "#0000FF"}}
        self.m_app.wireframe_pref = {
            "2D": {"thickness": 1, "color": "#FFFF00"},
            "3D": {"thickness": 1, "color": "#FFFF00"},
        }
        self.m_app.index_pref = {"2D": {"size": 1, "color": "#FFFFFF"}, "3D": {"size": 1, "color": "#FFFFFF"}}
        self.m_app.bgcolor = "#AAAAAA"

    def _create_widgets(self):
        """Create UI widgets."""
        self._create_geometry_widgets()
        self._create_toolbar_widgets()
        self._create_landmark_widgets()
        self._create_wireframe_widgets()
        self._create_index_widgets()
        self._create_bgcolor_widgets()
        self._create_plot_widgets()
        self._create_language_widgets()
        self._create_button_widgets()

    def _create_geometry_widgets(self):
        """Create window geometry preference widgets."""
        self.rbRememberGeometryYes = QRadioButton(self.tr("Yes"))
        self.rbRememberGeometryYes.setChecked(self.m_app.remember_geometry)
        self.rbRememberGeometryNo = QRadioButton(self.tr("No"))
        self.rbRememberGeometryNo.setChecked(not self.m_app.remember_geometry)

        self.gbRememberGeomegry = QGroupBox()
        self.gbRememberGeomegry.setLayout(QHBoxLayout())
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryYes)
        self.gbRememberGeomegry.layout().addWidget(self.rbRememberGeometryNo)

    def _create_toolbar_widgets(self):
        """Create toolbar icon size widgets."""
        self.toolbar_icon_large = (
            self.m_app.toolbar_icon_size.lower() == "large" if hasattr(self.m_app, "toolbar_icon_size") else False
        )

        self.rbToolbarIconLarge = QRadioButton(self.tr("Large"))
        self.rbToolbarIconLarge.setChecked(self.toolbar_icon_large)
        self.rbToolbarIconSmall = QRadioButton(self.tr("Small"))
        self.rbToolbarIconSmall.setChecked(self.toolbar_icon_small)
        self.rbToolbarIconMedium = QRadioButton(self.tr("Medium"))
        self.rbToolbarIconMedium.setChecked(self.toolbar_icon_medium)

        self.gbToolbarIconSize = QGroupBox()
        self.gbToolbarIconSize.setLayout(QHBoxLayout())
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconSmall)
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconMedium)
        self.gbToolbarIconSize.layout().addWidget(self.rbToolbarIconLarge)

    def _create_landmark_widgets(self):
        """Create landmark preference widgets for 2D and 3D."""
        # 2D Landmark
        self.gb2DLandmarkPref = QGroupBox(self.tr("2D"))
        self.gb2DLandmarkPref.setLayout(QHBoxLayout())
        self.combo2DLandmarkSize = QComboBox()
        self.combo2DLandmarkSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo2DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref["2D"]["size"]))
        self.lbl2DLandmarkColor = QPushButton()
        self.lbl2DLandmarkColor.setMinimumSize(20, 20)
        self.lbl2DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref["2D"]["color"])
        self.lbl2DLandmarkColor.setToolTip(self.m_app.landmark_pref["2D"]["color"])
        self.lbl2DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.gb2DLandmarkPref.layout().addWidget(self.combo2DLandmarkSize)
        self.gb2DLandmarkPref.layout().addWidget(self.lbl2DLandmarkColor)

        # 3D Landmark
        self.gb3DLandmarkPref = QGroupBox(self.tr("3D"))
        self.gb3DLandmarkPref.setLayout(QHBoxLayout())
        self.combo3DLandmarkSize = QComboBox()
        self.combo3DLandmarkSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo3DLandmarkSize.setCurrentIndex(int(self.m_app.landmark_pref["3D"]["size"]))
        self.lbl3DLandmarkColor = QPushButton()
        self.lbl3DLandmarkColor.setMinimumSize(20, 20)
        self.lbl3DLandmarkColor.setStyleSheet("background-color: " + self.m_app.landmark_pref["3D"]["color"])
        self.lbl3DLandmarkColor.setToolTip(self.m_app.landmark_pref["3D"]["color"])
        self.lbl3DLandmarkColor.setCursor(Qt.PointingHandCursor)
        self.gb3DLandmarkPref.layout().addWidget(self.combo3DLandmarkSize)
        self.gb3DLandmarkPref.layout().addWidget(self.lbl3DLandmarkColor)

        # Container
        self.landmark_layout = QHBoxLayout()
        self.landmark_layout.addWidget(self.gb2DLandmarkPref)
        self.landmark_layout.addWidget(self.gb3DLandmarkPref)

    def _create_wireframe_widgets(self):
        """Create wireframe preference widgets for 2D and 3D."""
        # 2D Wireframe
        self.gb2DWireframePref = QGroupBox(self.tr("2D"))
        self.gb2DWireframePref.setLayout(QHBoxLayout())
        self.combo2DWireframeThickness = QComboBox()
        self.combo2DWireframeThickness.addItems([self.tr("Thin"), self.tr("Medium"), self.tr("Thick")])
        self.combo2DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref["2D"]["thickness"]))
        self.lbl2DWireframeColor = QPushButton()
        self.lbl2DWireframeColor.setMinimumSize(20, 20)
        self.lbl2DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref["2D"]["color"])
        self.lbl2DWireframeColor.setToolTip(self.m_app.wireframe_pref["2D"]["color"])
        self.lbl2DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.gb2DWireframePref.layout().addWidget(self.combo2DWireframeThickness)
        self.gb2DWireframePref.layout().addWidget(self.lbl2DWireframeColor)

        # 3D Wireframe
        self.gb3DWireframePref = QGroupBox(self.tr("3D"))
        self.gb3DWireframePref.setLayout(QHBoxLayout())
        self.combo3DWireframeThickness = QComboBox()
        self.combo3DWireframeThickness.addItems([self.tr("Thin"), self.tr("Medium"), self.tr("Thick")])
        self.combo3DWireframeThickness.setCurrentIndex(int(self.m_app.wireframe_pref["3D"]["thickness"]))
        self.lbl3DWireframeColor = QPushButton()
        self.lbl3DWireframeColor.setMinimumSize(20, 20)
        self.lbl3DWireframeColor.setStyleSheet("background-color: " + self.m_app.wireframe_pref["3D"]["color"])
        self.lbl3DWireframeColor.setToolTip(self.m_app.wireframe_pref["3D"]["color"])
        self.lbl3DWireframeColor.setCursor(Qt.PointingHandCursor)
        self.gb3DWireframePref.layout().addWidget(self.combo3DWireframeThickness)
        self.gb3DWireframePref.layout().addWidget(self.lbl3DWireframeColor)

        # Container
        self.wireframe_layout = QHBoxLayout()
        self.wireframe_layout.addWidget(self.gb2DWireframePref)
        self.wireframe_layout.addWidget(self.gb3DWireframePref)

    def _create_index_widgets(self):
        """Create landmark index preference widgets for 2D and 3D."""
        # 2D Index
        self.gb2DIndexPref = QGroupBox(self.tr("2D"))
        self.gb2DIndexPref.setLayout(QHBoxLayout())
        self.combo2DIndexSize = QComboBox()
        self.combo2DIndexSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo2DIndexSize.setCurrentIndex(int(self.m_app.index_pref["2D"]["size"]))
        self.lbl2DIndexColor = QPushButton()
        self.lbl2DIndexColor.setMinimumSize(20, 20)
        self.lbl2DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref["2D"]["color"])
        self.lbl2DIndexColor.setToolTip(self.m_app.index_pref["2D"]["color"])
        self.lbl2DIndexColor.setCursor(Qt.PointingHandCursor)
        self.gb2DIndexPref.layout().addWidget(self.combo2DIndexSize)
        self.gb2DIndexPref.layout().addWidget(self.lbl2DIndexColor)

        # 3D Index
        self.gb3DIndexPref = QGroupBox(self.tr("3D"))
        self.gb3DIndexPref.setLayout(QHBoxLayout())
        self.combo3DIndexSize = QComboBox()
        self.combo3DIndexSize.addItems([self.tr("Small"), self.tr("Medium"), self.tr("Large")])
        self.combo3DIndexSize.setCurrentIndex(int(self.m_app.index_pref["3D"]["size"]))
        self.lbl3DIndexColor = QPushButton()
        self.lbl3DIndexColor.setMinimumSize(20, 20)
        self.lbl3DIndexColor.setStyleSheet("background-color: " + self.m_app.index_pref["3D"]["color"])
        self.lbl3DIndexColor.setToolTip(self.m_app.index_pref["3D"]["color"])
        self.lbl3DIndexColor.setCursor(Qt.PointingHandCursor)
        self.gb3DIndexPref.layout().addWidget(self.combo3DIndexSize)
        self.gb3DIndexPref.layout().addWidget(self.lbl3DIndexColor)

        # Container
        self.index_layout = QHBoxLayout()
        self.index_layout.addWidget(self.gb2DIndexPref)
        self.index_layout.addWidget(self.gb3DIndexPref)

    def _create_bgcolor_widgets(self):
        """Create background color widget."""
        self.lblBgcolor = QPushButton()
        self.lblBgcolor.setMinimumSize(20, 20)
        self.lblBgcolor.setStyleSheet("background-color: " + self.m_app.bgcolor)
        self.lblBgcolor.setToolTip(self.m_app.bgcolor)
        self.lblBgcolor.setCursor(Qt.PointingHandCursor)

    def _create_plot_widgets(self):
        """Create plot customization widgets."""
        # Plot size
        self.rbPlotLarge = QRadioButton(self.tr("Large"))
        self.rbPlotLarge.setChecked(self.m_app.plot_size.lower() == "large")
        self.rbPlotSmall = QRadioButton(self.tr("Small"))
        self.rbPlotSmall.setChecked(self.m_app.plot_size.lower() == "small")
        self.rbPlotMedium = QRadioButton(self.tr("Medium"))
        self.rbPlotMedium.setChecked(self.m_app.plot_size.lower() == "medium")

        self.gbPlotSize = QGroupBox()
        self.gbPlotSize.setLayout(QHBoxLayout())
        self.gbPlotSize.layout().addWidget(self.rbPlotSmall)
        self.gbPlotSize.layout().addWidget(self.rbPlotMedium)
        self.gbPlotSize.layout().addWidget(self.rbPlotLarge)

        # Plot colors
        self.gbPlotColors = QGroupBox()
        self.gbPlotColors.setLayout(QGridLayout())

        self.btnResetVivid = QPushButton(self.tr("Vivid"))
        self.btnResetVivid.setMinimumSize(60, 20)
        self.btnResetVivid.setMaximumSize(100, 20)
        self.btnResetPastel = QPushButton(self.tr("Pastel"))
        self.btnResetPastel.setMinimumSize(60, 20)
        self.btnResetPastel.setMaximumSize(100, 20)

        self.lblColor_list = []
        for i in range(len(self.m_app.color_list)):
            lbl = QPushButton()
            lbl.setMinimumSize(20, 20)
            lbl.setStyleSheet("background-color: " + self.m_app.color_list[i])
            lbl.setToolTip(self.m_app.color_list[i])
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.setText(str(i + 1))
            self.lblColor_list.append(lbl)
            self.gbPlotColors.layout().addWidget(lbl, i // 10, i % 10)

        self.gbPlotColors.layout().addWidget(self.btnResetVivid, 0, 10)
        self.gbPlotColors.layout().addWidget(self.btnResetPastel, 1, 10)

        # Plot markers
        self.gbPlotMarkers = QGroupBox()
        self.gbPlotMarkers.setLayout(QHBoxLayout())

        self.btnResetMarkers = QPushButton(self.tr("Reset"))
        self.btnResetMarkers.setMinimumSize(60, 20)
        self.btnResetMarkers.setMaximumSize(100, 20)

        self.comboMarker_list = []
        for i in range(len(self.m_app.marker_list)):
            combo = QComboBox()
            combo.addItems(mu.MARKER_LIST)
            combo.setCurrentIndex(mu.MARKER_LIST.index(self.m_app.marker_list[i]))
            self.comboMarker_list.append(combo)
            self.gbPlotMarkers.layout().addWidget(combo)
        self.gbPlotMarkers.layout().addWidget(self.btnResetMarkers)

    def _create_language_widgets(self):
        """Create language selection widgets."""
        self.comboLang = QComboBox()
        self.comboLang.addItem(self.tr("English"))
        self.comboLang.addItem(self.tr("Korean"))
        if hasattr(self.m_app, "language"):
            if self.m_app.language == "en":
                self.comboLang.setCurrentIndex(0)
            elif self.m_app.language == "ko":
                self.comboLang.setCurrentIndex(1)

        self.lang_layout = QHBoxLayout()
        self.lang_layout.addWidget(self.comboLang)

    def _create_button_widgets(self):
        """Create action button widgets."""
        self.btnOkay = QPushButton(self.tr("Close"))
        self.btnCancel = QPushButton(self.tr("Cancel"))

    def _create_layout(self):
        """Create dialog layout."""
        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)

        # Labels
        self.lblGeometry = QLabel(self.tr("Remember Geometry"))
        self.lblToolbarIconSize = QLabel(self.tr("Toolbar Icon Size"))
        self.lblPlotSize = QLabel(self.tr("Data point size"))
        self.lblPlotColors = QLabel(self.tr("Data point colors"))
        self.lblPlotMarkers = QLabel(self.tr("Data point markers"))
        self.lblLandmark = QLabel(self.tr("Landmark"))
        self.lblWireframe = QLabel(self.tr("Wireframe"))
        self.lblIndex = QLabel(self.tr("Index"))
        self.lblBgcolorLabel = QLabel(self.tr("Background Color"))
        self.lblLang = QLabel(self.tr("Language"))

        # Add rows
        self.main_layout.addRow(self.lblGeometry, self.gbRememberGeomegry)
        self.main_layout.addRow(self.lblToolbarIconSize, self.gbToolbarIconSize)
        self.main_layout.addRow(self.lblPlotSize, self.gbPlotSize)
        self.main_layout.addRow(self.lblPlotColors, self.gbPlotColors)
        self.main_layout.addRow(self.lblPlotMarkers, self.gbPlotMarkers)

        # Create container widgets for landmark, wireframe, index
        from PyQt5.QtWidgets import QWidget

        landmark_widget = QWidget()
        landmark_widget.setLayout(self.landmark_layout)
        wireframe_widget = QWidget()
        wireframe_widget.setLayout(self.wireframe_layout)
        index_widget = QWidget()
        index_widget.setLayout(self.index_layout)
        lang_widget = QWidget()
        lang_widget.setLayout(self.lang_layout)

        self.main_layout.addRow(self.lblLandmark, landmark_widget)
        self.main_layout.addRow(self.lblWireframe, wireframe_widget)
        self.main_layout.addRow(self.lblIndex, index_widget)
        self.main_layout.addRow(self.lblBgcolorLabel, self.lblBgcolor)
        self.main_layout.addRow(self.lblLang, lang_widget)
        self.main_layout.addRow("", self.btnOkay)

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Geometry
        self.rbRememberGeometryYes.clicked.connect(self.on_rbRememberGeometryYes_clicked)
        self.rbRememberGeometryNo.clicked.connect(self.on_rbRememberGeometryNo_clicked)

        # Toolbar
        self.rbToolbarIconLarge.clicked.connect(self.on_rbToolbarIconLarge_clicked)
        self.rbToolbarIconSmall.clicked.connect(self.on_rbToolbarIconSmall_clicked)
        self.rbToolbarIconMedium.clicked.connect(self.on_rbToolbarIconMedium_clicked)

        # Plot
        self.rbPlotLarge.clicked.connect(self.on_rbPlotLarge_clicked)
        self.rbPlotSmall.clicked.connect(self.on_rbPlotSmall_clicked)
        self.rbPlotMedium.clicked.connect(self.on_rbPlotMedium_clicked)
        self.btnResetMarkers.clicked.connect(self.on_btnResetMarkers_clicked)
        self.btnResetVivid.clicked.connect(self.on_btnResetVivid_clicked)
        self.btnResetPastel.clicked.connect(self.on_btnResetPastel_clicked)

        # Landmark
        self.lbl2DLandmarkColor.mousePressEvent = lambda event: self.on_lblLmColor_clicked(event, "2D")
        self.lbl3DLandmarkColor.mousePressEvent = lambda event: self.on_lblLmColor_clicked(event, "3D")
        self.combo2DLandmarkSize.currentIndexChanged.connect(
            lambda event: self.on_comboLmSize_currentIndexChanged(event, "2D")
        )
        self.combo3DLandmarkSize.currentIndexChanged.connect(
            lambda event: self.on_comboLmSize_currentIndexChanged(event, "3D")
        )

        # Wireframe
        self.lbl2DWireframeColor.mousePressEvent = lambda event: self.on_lblWireframeColor_clicked(event, "2D")
        self.lbl3DWireframeColor.mousePressEvent = lambda event: self.on_lblWireframeColor_clicked(event, "3D")
        self.combo2DWireframeThickness.currentIndexChanged.connect(
            lambda event: self.on_comboWireframeThickness_currentIndexChanged(event, "2D")
        )
        self.combo3DWireframeThickness.currentIndexChanged.connect(
            lambda event: self.on_comboWireframeThickness_currentIndexChanged(event, "3D")
        )

        # Index
        self.lbl2DIndexColor.mousePressEvent = lambda event: self.on_lblIndexColor_clicked(event, "2D")
        self.lbl3DIndexColor.mousePressEvent = lambda event: self.on_lblIndexColor_clicked(event, "3D")
        self.combo2DIndexSize.currentIndexChanged.connect(
            lambda event: self.on_comboIndexSize_currentIndexChanged(event, "2D")
        )
        self.combo3DIndexSize.currentIndexChanged.connect(
            lambda event: self.on_comboIndexSize_currentIndexChanged(event, "3D")
        )

        # Background color
        self.lblBgcolor.mousePressEvent = lambda event: self.on_lblBgcolor_clicked(event)

        # Colors
        for i, lbl in enumerate(self.lblColor_list):
            lbl.mousePressEvent = lambda event, index=i: self.on_lblColor_clicked(event, index)

        # Markers
        for i, combo in enumerate(self.comboMarker_list):
            combo.currentIndexChanged.connect(
                lambda event, index=i: self.on_comboMarker_currentIndexChanged(event, index)
            )

        # Language
        self.comboLang.currentIndexChanged.connect(self.comboLangIndexChanged)

        # Buttons
        self.btnOkay.clicked.connect(self.Okay)
        self.btnCancel.clicked.connect(self.Cancel)

    # Event handlers - Geometry
    def on_rbRememberGeometryYes_clicked(self):
        """Handle remember geometry yes button click."""
        self.m_app.remember_geometry = True

    def on_rbRememberGeometryNo_clicked(self):
        """Handle remember geometry no button click."""
        self.m_app.remember_geometry = False

    # Event handlers - Toolbar
    def on_rbToolbarIconLarge_clicked(self):
        """Handle toolbar icon large button click."""
        self.toolbar_icon_large = True
        self.toolbar_icon_medium = False
        self.toolbar_icon_small = False
        self.m_app.toolbar_icon_size = "Large"
        self.parent.update_settings()

    def on_rbToolbarIconSmall_clicked(self):
        """Handle toolbar icon small button click."""
        self.toolbar_icon_small = True
        self.toolbar_icon_medium = False
        self.toolbar_icon_large = False
        self.m_app.toolbar_icon_size = "Small"
        self.parent.update_settings()

    def on_rbToolbarIconMedium_clicked(self):
        """Handle toolbar icon medium button click."""
        self.toolbar_icon_small = False
        self.toolbar_icon_medium = True
        self.toolbar_icon_large = False
        self.m_app.toolbar_icon_size = "Medium"
        self.parent.update_settings()

    # Event handlers - Plot
    def on_rbPlotLarge_clicked(self):
        """Handle plot size large button click."""
        self.m_app.plot_size = "Large"

    def on_rbPlotMedium_clicked(self):
        """Handle plot size medium button click."""
        self.m_app.plot_size = "Medium"

    def on_rbPlotSmall_clicked(self):
        """Handle plot size small button click."""
        self.m_app.plot_size = "Small"

    def on_btnResetMarkers_clicked(self):
        """Reset markers to default values."""
        self.m_app.marker_list = mu.MARKER_LIST[:]
        for i in range(len(self.m_app.marker_list)):
            self.comboMarker_list[i].setCurrentText(self.m_app.marker_list[i])

    def on_btnResetPastel_clicked(self):
        """Reset colors to pastel palette."""
        self.m_app.color_list = mu.PASTEL_COLOR_LIST[:]
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])

    def on_btnResetVivid_clicked(self):
        """Reset colors to vivid palette."""
        self.m_app.color_list = mu.VIVID_COLOR_LIST[:]
        for i in range(len(self.m_app.color_list)):
            self.lblColor_list[i].setStyleSheet("background-color: " + self.m_app.color_list[i])
            self.lblColor_list[i].setToolTip(self.m_app.color_list[i])

    def on_lblColor_clicked(self, event, index):
        """Handle color button click.

        Args:
            event: Mouse event
            index: Color index in list
        """
        current_lblColor = self.lblColor_list[index]
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(current_lblColor.toolTip()))
        if color is not None and color.isValid():
            current_lblColor.setStyleSheet("background-color: " + color.name())
            current_lblColor.setToolTip(color.name())
            self.m_app.color_list[index] = color.name()

    def on_comboMarker_currentIndexChanged(self, event, index):
        """Handle marker combo box change.

        Args:
            event: Index changed event
            index: Marker index in list
        """
        current_lblMarker = self.comboMarker_list[index]
        self.m_app.marker_list[index] = current_lblMarker.currentText()

    # Event handlers - Landmark
    def on_comboLmSize_currentIndexChanged(self, event, dim):
        """Handle landmark size change.

        Args:
            event: Index changed event
            dim: Dimension ('2D' or '3D')
        """
        current_comboLmSize = self.combo2DLandmarkSize if dim == "2D" else self.combo3DLandmarkSize
        self.m_app.landmark_pref[dim]["size"] = current_comboLmSize.currentIndex()
        self.parent.update_settings()

    def on_lblLmColor_clicked(self, event, dim):
        """Handle landmark color button click.

        Args:
            event: Mouse event
            dim: Dimension ('2D' or '3D')
        """
        current_lblLmColor = self.lbl2DLandmarkColor if dim == "2D" else self.lbl3DLandmarkColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(current_lblLmColor.toolTip()))
        if color is not None and color.isValid():
            current_lblLmColor.setStyleSheet("background-color: " + color.name())
            current_lblLmColor.setToolTip(color.name())
            self.m_app.landmark_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    # Event handlers - Wireframe
    def on_comboWireframeThickness_currentIndexChanged(self, event, dim):
        """Handle wireframe thickness change.

        Args:
            event: Index changed event
            dim: Dimension ('2D' or '3D')
        """
        current_comboWireframeThickness = (
            self.combo2DWireframeThickness if dim == "2D" else self.combo3DWireframeThickness
        )
        self.m_app.wireframe_pref[dim]["thickness"] = current_comboWireframeThickness.currentIndex()
        self.parent.update_settings()

    def on_lblWireframeColor_clicked(self, event, dim):
        """Handle wireframe color button click.

        Args:
            event: Mouse event
            dim: Dimension ('2D' or '3D')
        """
        current_lblWireframeColor = self.lbl2DWireframeColor if dim == "2D" else self.lbl3DWireframeColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(current_lblWireframeColor.toolTip()))
        if color is not None and color.isValid():
            current_lblWireframeColor.setStyleSheet("background-color: " + color.name())
            current_lblWireframeColor.setToolTip(color.name())
            self.m_app.wireframe_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    # Event handlers - Index
    def on_comboIndexSize_currentIndexChanged(self, event, dim):
        """Handle index size change.

        Args:
            event: Index changed event
            dim: Dimension ('2D' or '3D')
        """
        current_comboIndexSize = self.combo2DIndexSize if dim == "2D" else self.combo3DIndexSize
        self.m_app.index_pref[dim]["size"] = current_comboIndexSize.currentIndex()
        self.parent.update_settings()

    def on_lblIndexColor_clicked(self, event, dim):
        """Handle index color button click.

        Args:
            event: Mouse event
            dim: Dimension ('2D' or '3D')
        """
        current_lblIndexColor = self.lbl2DIndexColor if dim == "2D" else self.lbl3DIndexColor
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(current_lblIndexColor.toolTip()))
        if color is not None and color.isValid():
            current_lblIndexColor.setStyleSheet("background-color: " + color.name())
            current_lblIndexColor.setToolTip(color.name())
            self.m_app.index_pref[dim]["color"] = color.name()
        self.parent.update_settings()

    # Event handlers - Background color
    def on_lblBgcolor_clicked(self, event):
        """Handle background color button click.

        Args:
            event: Mouse event
        """
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.m_app.bgcolor))
        if color is not None and color.isValid():
            self.m_app.bgcolor = color.name()
            self.lblBgcolor.setStyleSheet("background-color: " + self.m_app.bgcolor)
            self.lblBgcolor.setToolTip(self.m_app.bgcolor)
        self.parent.update_settings()

    # Event handlers - Language
    def comboLangIndexChanged(self, index):
        """Handle language selection change.

        Args:
            index: Language combo box index (0=English, 1=Korean)
        """
        if index == 0:
            self.m_app.language = "en"
        elif index == 1:
            self.m_app.language = "ko"

        # Remove existing translator
        if hasattr(self.m_app, "translator") and self.m_app.translator is not None:
            self.m_app.removeTranslator(self.m_app.translator)
            self.m_app.translator = None

        # Load new translator
        translator = QTranslator()
        translator_path = mu.resource_path(f"translations/Modan2_{self.m_app.language}.qm")
        if os.path.exists(translator_path):
            translator.load(translator_path)
            self.m_app.installTranslator(translator)
            self.m_app.translator = translator

        self.update_language()

    def read_settings(self):
        """Read preferences from application settings."""
        # Window geometry
        self.m_app.remember_geometry = mu.value_to_bool(
            self.m_app.settings.value("WindowGeometry/RememberGeometry", True)
        )

        # Toolbar icon size
        self.m_app.toolbar_icon_size = self.m_app.settings.value("ToolbarIconSize", "Medium")
        if self.m_app.toolbar_icon_size.lower() == "small":
            self.toolbar_icon_small = True
            self.toolbar_icon_large = False
            self.toolbar_icon_medium = False
        elif self.m_app.toolbar_icon_size.lower() == "medium":
            self.toolbar_icon_small = False
            self.toolbar_icon_medium = True
            self.toolbar_icon_large = False
        elif self.m_app.toolbar_icon_size.lower() == "large":
            self.toolbar_icon_small = False
            self.toolbar_icon_medium = False
            self.toolbar_icon_large = True

        # Colors and markers
        for i in range(len(self.m_app.color_list)):
            self.m_app.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])

        for i in range(len(self.m_app.marker_list)):
            self.m_app.marker_list[i] = self.m_app.settings.value(
                "DataPointMarker/" + str(i), self.m_app.marker_list[i]
            )

        self.m_app.plot_size = self.m_app.settings.value("PlotSize", self.m_app.plot_size)

        # Landmark preferences
        self.m_app.landmark_pref["2D"]["size"] = self.m_app.settings.value(
            "LandmarkSize/2D", self.m_app.landmark_pref["2D"]["size"]
        )
        self.m_app.landmark_pref["2D"]["color"] = self.m_app.settings.value(
            "LandmarkColor/2D", self.m_app.landmark_pref["2D"]["color"]
        )
        self.m_app.landmark_pref["3D"]["size"] = self.m_app.settings.value(
            "LandmarkSize/3D", self.m_app.landmark_pref["3D"]["size"]
        )
        self.m_app.landmark_pref["3D"]["color"] = self.m_app.settings.value(
            "LandmarkColor/3D", self.m_app.landmark_pref["3D"]["color"]
        )

        # Wireframe preferences
        self.m_app.wireframe_pref["2D"]["thickness"] = self.m_app.settings.value(
            "WireframeThickness/2D", self.m_app.wireframe_pref["2D"]["thickness"]
        )
        self.m_app.wireframe_pref["2D"]["color"] = self.m_app.settings.value(
            "WireframeColor/2D", self.m_app.wireframe_pref["2D"]["color"]
        )
        self.m_app.wireframe_pref["3D"]["thickness"] = self.m_app.settings.value(
            "WireframeThickness/3D", self.m_app.wireframe_pref["3D"]["thickness"]
        )
        self.m_app.wireframe_pref["3D"]["color"] = self.m_app.settings.value(
            "WireframeColor/3D", self.m_app.wireframe_pref["3D"]["color"]
        )

        # Index preferences
        self.m_app.index_pref["2D"]["size"] = self.m_app.settings.value(
            "IndexSize/2D", self.m_app.index_pref["2D"]["size"]
        )
        self.m_app.index_pref["2D"]["color"] = self.m_app.settings.value(
            "IndexColor/2D", self.m_app.index_pref["2D"]["color"]
        )
        self.m_app.index_pref["3D"]["size"] = self.m_app.settings.value(
            "IndexSize/3D", self.m_app.index_pref["3D"]["size"]
        )
        self.m_app.index_pref["3D"]["color"] = self.m_app.settings.value(
            "IndexColor/3D", self.m_app.index_pref["3D"]["color"]
        )

        # Other preferences
        self.m_app.bgcolor = self.m_app.settings.value("BackgroundColor", self.m_app.bgcolor)
        self.m_app.language = self.m_app.settings.value("Language", "en")
        self.update_language()

        # Dialog geometry
        if self.m_app.remember_geometry:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/PreferencesDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(100, 100))

    def write_settings(self):
        """Save preferences to application settings."""
        self.m_app.settings.setValue("ToolbarIconSize", self.m_app.toolbar_icon_size)
        self.m_app.settings.setValue("PlotSize", self.m_app.plot_size)
        self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.m_app.remember_geometry)

        # Save markers and colors
        for i in range(len(self.m_app.marker_list)):
            self.m_app.settings.setValue("DataPointMarker/" + str(i), self.m_app.marker_list[i])

        for i in range(len(self.m_app.color_list)):
            self.m_app.settings.setValue("DataPointColor/" + str(i), self.m_app.color_list[i])

        # Save dialog geometry
        if self.m_app.remember_geometry:
            self.m_app.settings.setValue("WindowGeometry/PreferencesDialog", self.geometry())

        # Save landmark preferences
        self.m_app.settings.setValue("LandmarkSize/2D", self.m_app.landmark_pref["2D"]["size"])
        self.m_app.settings.setValue("LandmarkColor/2D", self.m_app.landmark_pref["2D"]["color"])
        self.m_app.settings.setValue("LandmarkSize/3D", self.m_app.landmark_pref["3D"]["size"])
        self.m_app.settings.setValue("LandmarkColor/3D", self.m_app.landmark_pref["3D"]["color"])

        # Save wireframe preferences
        self.m_app.settings.setValue("WireframeThickness/2D", self.m_app.wireframe_pref["2D"]["thickness"])
        self.m_app.settings.setValue("WireframeColor/2D", self.m_app.wireframe_pref["2D"]["color"])
        self.m_app.settings.setValue("WireframeThickness/3D", self.m_app.wireframe_pref["3D"]["thickness"])
        self.m_app.settings.setValue("WireframeColor/3D", self.m_app.wireframe_pref["3D"]["color"])

        # Save index preferences
        self.m_app.settings.setValue("IndexSize/2D", self.m_app.index_pref["2D"]["size"])
        self.m_app.settings.setValue("IndexColor/2D", self.m_app.index_pref["2D"]["color"])
        self.m_app.settings.setValue("IndexSize/3D", self.m_app.index_pref["3D"]["size"])
        self.m_app.settings.setValue("IndexColor/3D", self.m_app.index_pref["3D"]["color"])

        # Save other preferences
        self.m_app.settings.setValue("BackgroundColor", self.m_app.bgcolor)
        self.m_app.settings.setValue("Language", self.m_app.language)

    def update_language(self):
        """Update all UI text with current language translations."""
        self.lblGeometry.setText(self.tr("Remember Geometry"))
        self.lblToolbarIconSize.setText(self.tr("Toolbar Icon Size"))
        self.lblPlotSize.setText(self.tr("Data point size"))
        self.lblPlotColors.setText(self.tr("Data point colors"))
        self.lblPlotMarkers.setText(self.tr("Data point markers"))
        self.lblLandmark.setText(self.tr("Landmark"))
        self.lblWireframe.setText(self.tr("Wireframe"))
        self.lblIndex.setText(self.tr("Index"))
        self.lblBgcolorLabel.setText(self.tr("Background Color"))
        self.lblLang.setText(self.tr("Language"))

        self.rbRememberGeometryYes.setText(self.tr("Yes"))
        self.rbRememberGeometryNo.setText(self.tr("No"))
        self.rbToolbarIconLarge.setText(self.tr("Large"))
        self.rbToolbarIconSmall.setText(self.tr("Small"))
        self.rbToolbarIconMedium.setText(self.tr("Medium"))
        self.rbPlotLarge.setText(self.tr("Large"))
        self.rbPlotSmall.setText(self.tr("Small"))
        self.rbPlotMedium.setText(self.tr("Medium"))
        self.btnResetMarkers.setText(self.tr("Reset"))
        self.btnResetVivid.setText(self.tr("Vivid"))
        self.btnResetPastel.setText(self.tr("Pastel"))
        self.btnOkay.setText(self.tr("Okay"))
        self.btnCancel.setText(self.tr("Cancel"))

        # Update combo box items
        item_list = [(self.tr("Small"), "Small"), (self.tr("Medium"), "Medium"), (self.tr("Large"), "Large")]
        for item in item_list:
            self.combo2DLandmarkSize.addItem(item[0], item[1])
            self.combo3DLandmarkSize.addItem(item[0], item[1])
            self.combo2DIndexSize.addItem(item[0], item[1])
            self.combo3DIndexSize.addItem(item[0], item[1])

        item_list = [(self.tr("Thin"), "Thin"), (self.tr("Medium"), "Medium"), (self.tr("Thick"), "Thick")]
        for item in item_list:
            self.combo2DWireframeThickness.addItem(item[0], item[1])
            self.combo3DWireframeThickness.addItem(item[0], item[1])

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.write_settings()
        self.parent.update_settings()
        event.accept()

    def Okay(self):
        """Save settings and close dialog."""
        self.write_settings()
        self.close()

    def Cancel(self):
        """Close dialog without saving."""
        self.close()

    def select_folder(self):
        """Select data folder (legacy method).

        Note:
            This method appears unused but is kept for compatibility.
        """
        folder = str(QFileDialog.getExistingDirectory(self, "Select a folder", str(getattr(self, "data_folder", "."))))
        if folder:
            self.data_folder = Path(folder).resolve()
            if hasattr(self, "edtDataFolder"):
                self.edtDataFolder.setText(folder)
