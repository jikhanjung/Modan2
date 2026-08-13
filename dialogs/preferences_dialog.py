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
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog
from MdHelpers import guard_slot

logger = logging.getLogger(__name__)

# Marker selectors per row. Named because the dialog's width used to depend on
# it: a single row of all eleven was the widest row in the form. Six splits them
# evenly over two rows; fewer per row buys nothing, because below about six the
# colour swatches above become the widest row instead and the dialog stops
# getting narrower -- 547px at four or five per row against 557px at six, for a
# ragged third row. See _create_plot_widgets.
MARKERS_PER_ROW = 6


def _format_size(num_bytes):
    """A size a person can read, for telling them what a move involves.

    Decimal units, matching what file managers and disk vendors show, so the
    number agrees with the one the user sees elsewhere.
    """
    for unit in ("bytes", "KB", "MB", "GB"):
        if num_bytes < 1000 or unit == "GB":
            return f"{num_bytes:.0f} {unit}" if unit == "bytes" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1000.0
    return f"{num_bytes:.1f} GB"


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

        # Open at a size that fits the screen; anything taller scrolls (important on
        # low-resolution monitors where the full form would otherwise be clipped).
        screen = self.m_app.primaryScreen() if hasattr(self.m_app, "primaryScreen") else None
        available = screen.availableGeometry() if screen is not None else None
        avail_h = available.height() if available is not None else 900
        avail_w = available.width() if available is not None else 1200

        # Width is taken from the form rather than fixed, because a fixed one was
        # wrong: 560 was narrower than the form's own requirement even here, and
        # that requirement follows the platform's font -- 744px on this machine,
        # 997px on a Windows CI runner. Measuring is the only way that survives
        # a new row or a different font. The minimum matters as much as the
        # opening size, since otherwise the same clipping is one drag of the
        # window edge away.
        #
        # Clamped to the screen: a dialog wider than the display is worse than a
        # scrollbar, and the scroll area shows one when this clamp binds.
        height = min(760, int(avail_h * 0.9))
        needed_w = min(self._width_the_form_needs(), avail_w)
        self.setMinimumWidth(needed_w)
        self.resize(needed_w, height)

        # Then check the estimate against what the viewport actually got, and
        # top it up. Predicting the chrome cannot be done portably: macOS uses
        # overlay scrollbars, whose PM_ScrollBarExtent is not what the viewport
        # loses, and the estimate came out 5px short there while being exact on
        # Linux and Windows. Measuring is not an approximation of the arithmetic,
        # it is the answer the arithmetic was trying to guess.
        self.layout().activate()
        shortfall = self.scroll_area.widget().minimumSizeHint().width() - self.scroll_area.viewport().width()
        if shortfall > 0:
            needed_w = min(needed_w + shortfall, avail_w)
            self.setMinimumWidth(needed_w)
            self.resize(needed_w, height)

    def _width_the_form_needs(self):
        """An estimate of the dialog width at which no preference row is clipped.

        minimumSizeHint, not sizeHint: the latter is what the form would like if
        space were free, and here that is half again as wide (1129px against
        509px on this machine) because the twenty colour swatches would rather
        spread out. What is being prevented is clipping, so the question is the
        narrowest width that still fits everything.

        An estimate because the scrollbar and frame widths come from the style
        rather than from the laid-out widget; __init__ corrects it afterwards
        against the real viewport.
        """
        margins = self.layout().contentsMargins()
        return (
            self.scroll_area.widget().minimumSizeHint().width()
            + 2 * self.scroll_area.frameWidth()
            # The vertical scrollbar is present whenever the form is taller than
            # the screen, and it takes its width out of the form's.
            + self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
            + margins.left()
            + margins.right()
        )

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
        self._create_data_folder_widgets()
        self._create_button_widgets()

    def _create_data_folder_widgets(self):
        """Create the data-folder chooser.

        This row existed only as a dangling ``select_folder`` handler for a
        widget nothing ever built, so a chosen folder lived on the dialog
        instance and died with it. It is real now: it writes to
        ``preferences.json`` and every path in ``MdUtils`` derives from it.

        The whole library follows this setting -- database, attachments,
        backups and logs -- because splitting it would leave either half
        useless on its own. ``--db`` is the one exception: it names a file
        outright and is independent of the data directory by design.
        """
        self.edtDataFolder = QLineEdit()
        self.edtDataFolder.setReadOnly(True)
        self.btnDataFolder = QPushButton(self.tr("Browse..."))
        self.btnResetDataFolder = QPushButton(self.tr("Reset"))

        self.data_folder_layout = QHBoxLayout()
        self.data_folder_layout.setContentsMargins(0, 0, 0, 0)
        self.data_folder_layout.addWidget(self.edtDataFolder, 1)
        self.data_folder_layout.addWidget(self.btnDataFolder)
        self.data_folder_layout.addWidget(self.btnResetDataFolder)

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
        for i, color in enumerate(self.m_app.color_list):
            lbl = QPushButton()
            lbl.setMinimumSize(20, 20)
            lbl.setStyleSheet("background-color: " + color)
            lbl.setToolTip(color)
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.setText(str(i + 1))
            self.lblColor_list.append(lbl)
            self.gbPlotColors.layout().addWidget(lbl, i // 10, i % 10)

        self.gbPlotColors.layout().addWidget(self.btnResetVivid, 0, 10)
        self.gbPlotColors.layout().addWidget(self.btnResetPastel, 1, 10)

        # Plot markers, wrapped like the colours above rather than strung out in
        # one line. Ten combo boxes side by side made this the widest row in the
        # dialog by a distance -- 579px of the 744 the form demanded here, and
        # the reason the whole thing wanted 997px under Windows' font. Wrapping
        # brings the form to 509px, which is an ordinary size for a preferences
        # dialog and fits on any screen it is likely to meet.
        #
        # Five per row, not the colours' ten: these are combo boxes, several
        # times the width of a colour swatch, so ten of them is what caused the
        # problem in the first place.
        self.gbPlotMarkers = QGroupBox()
        self.gbPlotMarkers.setLayout(QGridLayout())

        self.btnResetMarkers = QPushButton(self.tr("Reset"))
        self.btnResetMarkers.setMinimumSize(60, 20)
        self.btnResetMarkers.setMaximumSize(100, 20)

        self.comboMarker_list = []
        for marker in self.m_app.marker_list:
            combo = QComboBox()
            combo.addItems(mu.MARKER_LIST)
            combo.setCurrentIndex(mu.MARKER_LIST.index(marker))
            self.comboMarker_list.append(combo)
        for i, combo in enumerate(self.comboMarker_list):
            self.gbPlotMarkers.layout().addWidget(combo, i // MARKERS_PER_ROW, i % MARKERS_PER_ROW)
        # Spans however many rows there turn out to be, so it sits beside the
        # block rather than in it -- and stays correct if a marker is added.
        marker_rows = -(-len(self.comboMarker_list) // MARKERS_PER_ROW)
        self.gbPlotMarkers.layout().addWidget(self.btnResetMarkers, 0, MARKERS_PER_ROW, marker_rows, 1)

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
        """Create dialog layout.

        The preference rows live inside a QScrollArea so the dialog stays usable on
        low-resolution monitors (the content scrolls instead of being clipped); the
        Save button is pinned below the scroll area so it's always reachable.
        """
        self.main_layout = QFormLayout()

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
        self.lblDataFolder = QLabel(self.tr("Data folder"))

        # Add rows
        self.main_layout.addRow(self.lblGeometry, self.gbRememberGeomegry)
        self.main_layout.addRow(self.lblToolbarIconSize, self.gbToolbarIconSize)
        self.main_layout.addRow(self.lblPlotSize, self.gbPlotSize)
        self.main_layout.addRow(self.lblPlotColors, self.gbPlotColors)
        self.main_layout.addRow(self.lblPlotMarkers, self.gbPlotMarkers)

        # Create container widgets for landmark, wireframe, index
        landmark_widget = QWidget()
        landmark_widget.setLayout(self.landmark_layout)
        wireframe_widget = QWidget()
        wireframe_widget.setLayout(self.wireframe_layout)
        index_widget = QWidget()
        index_widget.setLayout(self.index_layout)
        lang_widget = QWidget()
        lang_widget.setLayout(self.lang_layout)
        data_folder_widget = QWidget()
        data_folder_widget.setLayout(self.data_folder_layout)

        self.main_layout.addRow(self.lblLandmark, landmark_widget)
        self.main_layout.addRow(self.lblWireframe, wireframe_widget)
        self.main_layout.addRow(self.lblIndex, index_widget)
        self.main_layout.addRow(self.lblBgcolorLabel, self.lblBgcolor)
        self.main_layout.addRow(self.lblLang, lang_widget)
        self.main_layout.addRow(self.lblDataFolder, data_folder_widget)

        # Wrap the form in a scroll area (usable on low-res monitors); pin the Save
        # button below it so it's always visible.
        form_widget = QWidget()
        form_widget.setLayout(self.main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(form_widget)
        # As-needed, not always-off. The dialog opens wide enough for the form
        # whenever the screen allows, but it cannot when the screen is narrower
        # than the form -- and the form is wider than it looks: 997px on a
        # Windows CI runner against 744px here, because the width follows the
        # platform's font. With the bar off, that case put the right-hand column
        # of every row somewhere the user could not reach at all. A scrollbar
        # that appears only when it is needed costs nothing the rest of the time.
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.scroll_area)
        outer_layout.addWidget(self.btnOkay)
        self.setLayout(outer_layout)

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Geometry
        self.rbRememberGeometryYes.clicked.connect(self.on_rbRememberGeometryYes_clicked)
        self.rbRememberGeometryNo.clicked.connect(self.on_rbRememberGeometryNo_clicked)

        # Data folder
        self.btnDataFolder.clicked.connect(self.select_folder)
        self.btnResetDataFolder.clicked.connect(self.reset_data_folder)

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
        for i, marker in enumerate(self.m_app.marker_list):
            self.comboMarker_list[i].setCurrentText(marker)

    def on_btnResetPastel_clicked(self):
        """Reset colors to pastel palette."""
        self.m_app.color_list = mu.PASTEL_COLOR_LIST[:]
        for i, color in enumerate(self.m_app.color_list):
            self.lblColor_list[i].setStyleSheet("background-color: " + color)
            self.lblColor_list[i].setToolTip(color)

    def on_btnResetVivid_clicked(self):
        """Reset colors to vivid palette."""
        self.m_app.color_list = mu.VIVID_COLOR_LIST[:]
        for i, color in enumerate(self.m_app.color_list):
            self.lblColor_list[i].setStyleSheet("background-color: " + color)
            self.lblColor_list[i].setToolTip(color)

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
        for i, _ in enumerate(self.m_app.color_list):
            self.m_app.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])

        for i, marker in enumerate(self.m_app.marker_list):
            self.m_app.marker_list[i] = self.m_app.settings.value("DataPointMarker/" + str(i), marker)

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

        # Data folder. Shown resolved even when unset, so the field always names
        # a real place -- "" would read as "nowhere" rather than "the default".
        configured = self.m_app.settings.value("Data/Directory", "") or ""
        self.edtDataFolder.setText(os.path.abspath(configured or mu.DEFAULT_DB_DIRECTORY))
        self.data_folder = Path(self.edtDataFolder.text())

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
        for i, marker in enumerate(self.m_app.marker_list):
            self.m_app.settings.setValue("DataPointMarker/" + str(i), marker)

        for i, color in enumerate(self.m_app.color_list):
            self.m_app.settings.setValue("DataPointColor/" + str(i), color)

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
        self.lblDataFolder.setText(self.tr("Data folder"))
        self.btnDataFolder.setText(self.tr("Browse..."))
        self.btnResetDataFolder.setText(self.tr("Reset"))
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

    @guard_slot("Failed to save preferences")
    def Okay(self):
        """Save settings and close dialog."""
        self.write_settings()
        self.close()

    def Cancel(self):
        """Close dialog without saving."""
        self.close()

    @guard_slot("Failed to change the data folder")
    def select_folder(self):
        """Choose where the database, attachments and backups are kept.

        Two separate things happen here, and keeping them separate is the point:
        recording *where* the library should live, and moving the library there.
        The second is offered, never assumed -- relocating gigabytes has to be
        something the user asked for.

        Declining the move is a legitimate answer with a real use (pointing
        Modan2 at a library that is already in the new folder), so the message
        for that case says what will actually be found there rather than
        assuming it will be empty.
        """
        current = self.edtDataFolder.text() or mu.get_data_directory()
        folder = str(QFileDialog.getExistingDirectory(self, self.tr("Select a folder"), current))
        if not folder:
            return

        folder = str(Path(folder).resolve())
        if os.path.abspath(folder) == os.path.abspath(self.edtDataFolder.text() or ""):
            return

        if not self._accept_location_risk(folder):
            return

        # The library to move is the one in use, which is not necessarily what
        # the field shows: a folder chosen earlier in this session is pending
        # until the next launch, while the data is still where it always was.
        source = mu.get_data_directory()
        moved = False

        if mu.describe_move_problem(source, folder) is None:
            choice = self._ask_about_moving(source, folder)
            if choice == "cancel":
                return
            if choice == "move" and not self._move_library(source, folder):
                return
            moved = choice == "move"
        elif not self._confirm_without_moving(folder):
            return

        self.data_folder = Path(folder)
        self.edtDataFolder.setText(folder)
        self._apply_data_folder(folder, restart_required=not moved)

    def _accept_location_risk(self, destination):
        """Warn about a cloud-synced or network folder. True to go ahead.

        A warning rather than a refusal: the folder is the user's, and there are
        reasons to accept the risk. But both failure modes it describes are
        silent ones -- a database that syncs itself into two divergent copies,
        or locking that fails over SMB -- so nobody finds them on their own, and
        by the time they do the damage is not attributable.

        The safe answer is the default button, and the risky one has to be
        chosen deliberately.
        """
        risk = mu.describe_location_risk(destination)
        if not risk:
            return True

        logger.warning("Risky data folder chosen: %s", destination)
        box = QMessageBox(self)
        box.setWindowTitle(self.tr("This folder is not a good place for your data"))
        box.setIcon(QMessageBox.Warning)
        # Not wrapped in tr(): the text is assembled in MdUtils and tr() on a
        # runtime string looks up nothing. Translating it means moving the
        # wording here, which would put it out of reach of the non-GUI callers.
        box.setText(risk)
        use_anyway = box.addButton(self.tr("Use it anyway"), QMessageBox.DestructiveRole)
        choose_another = box.addButton(self.tr("Choose another folder"), QMessageBox.RejectRole)
        box.setDefaultButton(choose_another)
        box.exec_()
        return box.clickedButton() is use_anyway

    def _ask_about_moving(self, source, destination):
        """Offer the move. Returns "move", "setting-only" or "cancel"."""
        count, size = mu.library_size(source)
        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Change data folder"))
        box.setIcon(QMessageBox.Question)
        box.setText(self.tr("Modan2 will keep your data in:\n{}").format(destination))
        box.setInformativeText(
            self.tr(
                "Move your existing library there now? It is {} files, {}.\n\n"
                "Nothing is deleted until the copy has been checked, and you can "
                "stop partway -- your data stays where it is if you do."
            ).format(count, _format_size(size))
        )
        move_button = box.addButton(self.tr("Move now"), QMessageBox.AcceptRole)
        setting_button = box.addButton(self.tr("Change the setting only"), QMessageBox.DestructiveRole)
        box.addButton(QMessageBox.Cancel)
        box.setDefaultButton(move_button)
        box.exec_()

        clicked = box.clickedButton()
        if clicked is move_button:
            return "move"
        if clicked is setting_button:
            return "setting-only"
        return "cancel"

    def _confirm_without_moving(self, destination):
        """Confirm a change of setting with no move. True to go ahead.

        Used when moving is not on offer -- most often because the chosen folder
        already holds a library, which is the case where saying "Modan2 will
        start with an empty library there" would be plain wrong.
        """
        if mu.library_members(destination):
            detail = self.tr("Modan2 will open the library that is already in that folder.")
        else:
            detail = self.tr(
                "Your database, images and 3D models are not moved. Until you move "
                "them yourself, Modan2 will start with an empty library there."
            )

        answer = QMessageBox.question(
            self,
            self.tr("Change data folder"),
            self.tr("Modan2 will use this folder the next time it starts:\n{}\n\n{}\n\nContinue?").format(
                destination, detail
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def _move_library(self, source, destination):
        """Move the library and switch to it. True if it worked.

        The database is closed first -- an open file cannot be renamed on
        Windows -- and so is the log file, which follows the data directory and
        would otherwise be the one thing keeping the old folder locked.

        On any unhappy ending the database is reopened where it was. That is the
        whole recovery: ``move_data_directory`` guarantees the source is intact
        unless the move completed, so there is nothing else to undo.

        Recovery is the default and success is what switches it off, rather than
        something each failure path remembers to do. Listing the failures had
        already missed one: only DataDirectoryMoveError was caught, so any other
        exception left the database closed. It did not crash -- the caller is a
        guard_slot, which logs it and shows a dialog -- and that is worse, since
        the window survives with every later operation failing against a closed
        database. A move is not the place to enumerate what can go wrong.
        """
        import MdModel

        # --db names a file outright and is independent of the data directory,
        # so a database chosen that way is not part of this library and must not
        # be redirected into the new folder.
        db_in_library = os.path.dirname(os.path.abspath(MdModel.database_path)) == os.path.abspath(source)

        progress = QProgressDialog(self.tr("Moving your data..."), self.tr("Stop"), 0, 100, self)
        progress.setWindowTitle(self.tr("Change data folder"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def report(done, total, member):
            progress.setLabelText(self.tr("Moving {}...").format(member))
            progress.setValue(int(done * 100 / total) if total else 100)
            QApplication.processEvents()

        detached = mu.detach_log_file()
        if db_in_library:
            MdModel.gDatabase.close()

        moved = False
        failure = None
        try:
            result = mu.move_data_directory(source, destination, progress=report, should_cancel=progress.wasCanceled)
            moved = not result.cancelled
        except mu.DataDirectoryMoveError as e:
            # Reported after the restoration below, so the modal dialog is not
            # sitting in front of a closed database.
            failure = str(e)
        finally:
            progress.close()
            if not moved:
                self._restore_after_failed_move(MdModel, db_in_library, detached)

        if failure is not None:
            QMessageBox.critical(self, self.tr("Could not move the data"), failure)
        if not moved:
            return False

        mu.set_data_directory(destination)
        mu.ensure_directories()
        if db_in_library:
            MdModel.set_database_path(mu.get_database_path())
        mu.attach_log_file(detached)
        # The mirror on the application object, kept in step with MdUtils rather
        # than left pointing into a folder that no longer exists.
        self.m_app.storage_directory = mu.get_storage_directory()
        logger.info("Library moved to %s", destination)
        return True

    @staticmethod
    def _restore_after_failed_move(MdModel, db_in_library, detached):  # noqa: N803 - module, not a Qt argument
        """Put the database and the log file back the way they were."""
        if db_in_library:
            MdModel.set_database_path(MdModel.database_path)
        mu.attach_log_file(detached)

    @guard_slot("Failed to reset the data folder")
    def reset_data_folder(self):
        """Go back to the default location, from the next launch."""
        if not self.m_app.settings.value("Data/Directory", ""):
            return
        self.edtDataFolder.setText(os.path.abspath(mu.DEFAULT_DB_DIRECTORY))
        self._apply_data_folder("")

    def _apply_data_folder(self, folder, restart_required=True):
        """Record the choice, and say whether it is already in effect.

        ``folder`` is "" for the default. The empty string is what gets stored:
        recording a resolved path would pin a user who never made a choice to
        whatever the default was on the day they first launched.

        A move that just succeeded has already switched every path over, so
        telling the user to restart would be asking for something that is not
        needed -- and would suggest the move had not finished.
        """
        self.m_app.settings.setValue("Data/Directory", folder)
        if restart_required:
            QMessageBox.information(
                self,
                self.tr("Restart required"),
                self.tr("Restart Modan2 for the new data folder to take effect."),
            )
        else:
            QMessageBox.information(
                self,
                self.tr("Data folder changed"),
                self.tr("Your data is now in:\n{}").format(folder),
            )
