"""Data Exploration Dialog for interactive data analysis and visualization.

This module provides the DataExplorationDialog class for exploring morphometric
analysis results through interactive plots and 3D shape visualization.
"""

import glob
import json
import logging
import math
import sys
import tempfile

import cv2
import matplotlib
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import QEvent, QItemSelectionModel, QPoint, QRect, QSize, Qt, QTimer
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QShortcut,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from scipy import stats
from scipy.spatial import ConvexHull

import MdUtils as mu
from MdModel import MdDataset, MdObject
from ModanComponents import ObjectViewer2D, ObjectViewer3D, ShapePreference

logger = logging.getLogger(__name__)

# Centroid size constants
CENTROID_SIZE_VALUE = 9999
CENTROID_SIZE_TEXT = "CSize"

# Mode constants
MODE_EXPLORATION = 0
MODE_REGRESSION = 1
MODE_AVERAGE = 2
MODE_COMPARISON = 3
MODE_COMPARISON2 = 4


def safe_remove_artist(artist, ax=None):
    """Safely remove matplotlib artist from plot"""
    if artist is None:
        return
    try:
        artist.remove()
    except NotImplementedError:
        # For scatter plots and other collections
        if ax is not None:
            if hasattr(ax, "collections") and artist in ax.collections:
                ax.collections.remove(artist)
            elif hasattr(ax, "texts") and artist in ax.texts:
                ax.texts.remove(artist)
            elif hasattr(ax, "lines") and artist in ax.lines:
                ax.lines.remove(artist)
    except Exception:
        pass  # Silently ignore if already removed or other issues


# Color constants
COLOR = {
    "RED": (1, 0, 0),
    "GREEN": (0, 1, 0),
    "BLUE": (0, 0, 1),
    "YELLOW": (1, 1, 0),
    "CYAN": (0, 1, 1),
    "MAGENTA": (1, 0, 1),
    "WHITE": (1, 1, 1),
    "LIGHT_GRAY": (0.8, 0.8, 0.8),
    "GRAY": (0.5, 0.5, 0.5),
    "DARK_GRAY": (0.3, 0.3, 0.3),
    "BLACK": (0, 0, 0),
}

COLOR["SINGLE_SHAPE"] = COLOR["GREEN"]
COLOR["AVERAGE_SHAPE"] = COLOR["LIGHT_GRAY"]
COLOR["NORMAL_SHAPE"] = COLOR["BLUE"]
COLOR["NORMAL_TEXT"] = COLOR["WHITE"]


class DataExplorationDialog(QDialog):
    def __init__(self, parent):
        self.initialized = False
        super().__init__()
        # print("DataExplorationDialog init")
        self.parent = parent
        self.setWindowTitle(self.tr("Modan2 - Data Exploration"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # self.setWindowFlags(Qt.FramelessWindowHint)  # Removes window decoration
        # self.setAttribute(Qt.WA_TranslucentBackground)  # Enables transparency
        # self.setAttribute(Qt.WA_NoSystemBackground, True)  # Avoids system background paint

        # self.windowActivated.connect(self.handle_window_focus)
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.m_app = QApplication.instance()
        self.fig2 = None
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        # print("color_list", self.color_list)
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        self.remember_geometry = True
        self.on_pick_happened = False
        self.bgcolor = "#AAAAAA"

        self.curve_list = []
        self.shape_view_list = []
        self.shape_label_list = []
        self.shape_preference_list = []
        self.custom_shape_hash = {}
        self.shape_grid = {}
        self.shape_grid_pref_dict = {}
        self.shape_button_list = []
        # self.shape_combo_list = []
        self.vertical_line_xval = None
        # self.ds_ops = None
        self.vertical_line_style = "dashed"
        self.axvline = None
        self.temp_rotate_x = 0
        self.temp_rotate_y = 0
        self.shape_view_pan_x = 0
        self.shape_view_pan_y = 0
        self.shape_view_dolly = 0
        self.is_picking_shape = False
        self.pick_idx = -1
        self.animation_counter = 0
        self.show_arrow = True
        self.arrow_color = "red"
        self.object_info_list = []
        # self.shape_mode = MODE_REGRESSION
        self.rotation_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

        self.read_settings()
        self.mode = MODE_EXPLORATION
        self.ignore_change = False
        self.init_UI()

    def init_UI(self):
        """Initialize the UI for data exploration dialog"""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self._setup_title_row()
        self._setup_plot_canvases()
        self._setup_chart_basic_options()
        self._setup_overlay_settings()
        self._setup_regression_controls()
        self._setup_plot_layout()
        self._setup_shape_view_controls()
        self._assemble_final_layout()

        self.on_chart_dim_changed()
        self.initialized = True

    def _setup_title_row(self):
        """Setup the title row with analysis info fields"""
        self.lblAnalysisName = QLabel(self.tr("Analysis name"))
        self.lblAnalysisName.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.edtAnalysisName = QLineEdit()
        self.edtAnalysisName.setEnabled(False)
        self.lblSuperimposition = QLabel(self.tr("Superimposition method"))
        self.lblSuperimposition.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.edtSuperimposition = QLineEdit()
        self.edtSuperimposition.setEnabled(False)
        self.lblOrdination = QLabel(self.tr("Ordination method"))
        self.lblOrdination.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.edtOrdination = QLineEdit()
        self.edtOrdination.setEnabled(False)
        self.lblVisualization = QLabel(self.tr("Shape view"))
        self.lblVisualization.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.comboVisualization = QComboBox()
        self.comboVisualization.addItem(self.tr("Exploration"), MODE_EXPLORATION)
        self.comboVisualization.addItem(self.tr("Regression"), MODE_REGRESSION)
        self.comboVisualization.addItem(self.tr("Average"), MODE_AVERAGE)
        self.comboVisualization.addItem(self.tr("Comparison"), MODE_COMPARISON)
        self.comboVisualization.addItem(self.tr("Comparison (overlap)"), MODE_COMPARISON2)
        self.comboVisualization.currentIndexChanged.connect(self.comboVisualizationMethod_changed)
        self.comboVisualization.setCurrentIndex(0)

        self.title_row_widget = QWidget()
        self.title_row_layout = QHBoxLayout()
        self.title_row_widget.setLayout(self.title_row_layout)
        self.title_row_layout.addWidget(self.lblAnalysisName, 1)
        self.title_row_layout.addWidget(self.edtAnalysisName, 2)
        self.title_row_layout.addWidget(self.lblSuperimposition, 1)
        self.title_row_layout.addWidget(self.edtSuperimposition, 2)
        self.title_row_layout.addWidget(self.lblOrdination, 1)
        self.title_row_layout.addWidget(self.edtOrdination, 2)
        self.layout.addWidget(self.title_row_widget)

    def _setup_plot_canvases(self):
        """Setup matplotlib plot canvases for 2D and 3D visualization"""
        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.ax2.set_xlabel("X-axis Label")
        self.ax2.set_ylabel("Y-axis Label")
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        # self.fig2.canvas.mpl_connect('pick_event',self.on_pick)
        self.fig2.canvas.mpl_connect("button_press_event", self.on_canvas_button_press)
        self.fig2.canvas.mpl_connect("button_release_event", self.on_canvas_button_release)
        self.fig2.canvas.mpl_connect("motion_notify_event", self.on_canvas_move)
        self.fig2.canvas.mpl_connect("resize_event", self.resizeEvent)
        # self.fig2.canvas.mpl_connect('motion_notify_event', self.on_hover_enter)
        # self.fig2.canvas.mpl_connect('motion_notify_event', self.on_hover_leave)

        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection="3d")
        self.toolbar3 = NavigationToolbar(self.plot_widget3, self)

        self.plot_setting_widget = QWidget()
        self.plot_setting_layout = QVBoxLayout()
        self.plot_setting_widget.setLayout(self.plot_setting_layout)
        self.plot_setting_widget.hide()

    def _setup_chart_basic_options(self):
        """Setup basic chart options like grouping, dimensions, and axes"""
        self.axis_option_widget = QWidget()
        self.axis_option_layout = QHBoxLayout()
        self.axis_option_widget.setLayout(self.axis_option_layout)

        # basic chart options
        self.gbChartBasics = QWidget()
        # self.gbChartBasics.setTitle(self.tr("Basic settings"))
        self.gbChartBasics.setLayout(QHBoxLayout())

        spacer1 = QWidget()
        spacer1.setMinimumWidth(20)
        spacer2 = QWidget()
        spacer2.setMinimumWidth(20)

        self.lblGroupBy = QLabel(self.tr("Grouping variable"))
        self.lblGroupBy.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.comboGroupBy = QComboBox()
        self.comboGroupBy.setEnabled(False)
        self.comboGroupBy.currentIndexChanged.connect(self.comboGroupBy_changed)
        self.lblChartDim = QLabel(self.tr("Chart dimension:"))
        self.rb2DChartDim = QRadioButton("2D")
        self.rb3DChartDim = QRadioButton("3D")
        self.grpRadioButton1 = QButtonGroup()
        self.grpRadioButton1.addButton(self.rb2DChartDim)
        self.grpRadioButton1.addButton(self.rb3DChartDim)
        self.rb3DChartDim.setEnabled(False)
        self.rb2DChartDim.setChecked(True)
        self.rb2DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.rb3DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.cbxLegend = QCheckBox()
        self.cbxLegend.setText(self.tr("Show legend"))
        self.cbxLegend.setChecked(True)
        self.cbxLegend.toggled.connect(self.update_chart)
        self.cbxShowVariance = QCheckBox()
        self.cbxShowVariance.setText(self.tr("Show var. explained"))
        self.cbxShowVariance.setChecked(False)
        self.cbxShowVariance.toggled.connect(self.update_chart)
        self.gbChartBasics.layout().addWidget(self.lblGroupBy)
        self.gbChartBasics.layout().addWidget(self.comboGroupBy)
        self.gbChartBasics.layout().addWidget(spacer1)
        # self.gbChartBasics.layout().addWidget(self.lblChartDim)
        # self.gbChartBasics.layout().addWidget(self.rb2DChartDim)
        # self.gbChartBasics.layout().addWidget(self.rb3DChartDim)
        self.gbChartBasics.layout().addWidget(self.cbxLegend)
        self.gbChartBasics.layout().addWidget(self.cbxShowVariance)
        self.gbChartBasics.layout().addWidget(spacer2)
        # self.axis_option_layout.addWidget(self.gbChartBasics)

        self.lblAxis1 = QLabel("Axis 1")
        self.lblAxis2 = QLabel("Axis 2")
        self.lblAxis3 = QLabel("Axis 3")
        self.comboAxis1 = QComboBox()
        self.comboAxis2 = QComboBox()
        self.comboAxis3 = QComboBox()
        self.cbxFlipAxis1 = QCheckBox()
        self.cbxFlipAxis1.setText(self.tr("Flip"))
        self.cbxFlipAxis1.setChecked(False)
        self.cbxFlipAxis2 = QCheckBox()
        self.cbxFlipAxis2.setText(self.tr("Flip"))
        self.cbxFlipAxis2.setChecked(False)
        self.cbxFlipAxis3 = QCheckBox()
        self.cbxFlipAxis3.setText(self.tr("Flip"))
        self.cbxFlipAxis3.setChecked(False)

        self.cbxFlipAxis1.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis2.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis3.stateChanged.connect(self.flip_axis_changed)

        for i in range(1, 11):
            self.comboAxis1.addItem("PC" + str(i))
            self.comboAxis2.addItem("PC" + str(i))
            self.comboAxis3.addItem("PC" + str(i))
        self.comboAxis1.addItem("CSize")
        self.comboAxis1.setCurrentIndex(0)
        self.comboAxis2.setCurrentIndex(1)
        self.comboAxis3.setCurrentIndex(2)
        self.comboAxis1.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis2.currentIndexChanged.connect(self.axis_changed)
        self.comboAxis3.currentIndexChanged.connect(self.axis_changed)

        # self.gbAxis= QGroupBox()
        # self.gbAxis.setTitle(self.tr("Axes settings"))
        # self.gbAxis.setLayout(QHBoxLayout())
        self.gbChartBasics.layout().addWidget(self.lblAxis1, 0)
        self.gbChartBasics.layout().addWidget(self.comboAxis1, 1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis1, 0)
        self.gbChartBasics.layout().addWidget(self.lblAxis2, 0)
        self.gbChartBasics.layout().addWidget(self.comboAxis2, 1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis2, 0)
        self.gbChartBasics.layout().addWidget(self.lblAxis3, 0)
        self.gbChartBasics.layout().addWidget(self.comboAxis3, 1)
        self.gbChartBasics.layout().addWidget(self.cbxFlipAxis3, 0)

    def _setup_overlay_settings(self):
        """Setup overlay visualization settings"""
        self.overlay_setting_widget = QWidget()
        self.overlay_setting_layout = QHBoxLayout()
        self.overlay_setting_widget.setLayout(self.overlay_setting_layout)

        self.gbOverlay = QGroupBox()
        self.gbOverlay.setTitle(self.tr("Overlay settings"))
        self.gbOverlay.setLayout(QHBoxLayout())

        self.cbxDepthShade = QCheckBox()
        self.cbxDepthShade.setText(self.tr("Depth shade"))
        self.cbxDepthShade.setChecked(False)
        self.cbxDepthShade.toggled.connect(self.update_chart)

        self.cbxAverage = QCheckBox()
        self.cbxAverage.setText(self.tr("Group average"))
        self.cbxAverage.setChecked(False)
        self.cbxAverage.stateChanged.connect(self.update_chart)
        self.cbxConvexHull = QCheckBox()
        self.cbxConvexHull.setText(self.tr("Convex hull"))
        self.cbxConvexHull.setChecked(False)
        self.cbxConvexHull.stateChanged.connect(self.update_chart)
        self.cbxConfidenceEllipse = QCheckBox()
        self.cbxConfidenceEllipse.setText(self.tr("Confidence ellipse"))
        self.cbxConfidenceEllipse.setChecked(False)
        self.cbxConfidenceEllipse.stateChanged.connect(self.update_chart)
        self.cbxShapeGrid = QCheckBox()
        self.cbxShapeGrid.setText(self.tr("Shape grid"))
        self.cbxShapeGrid.setChecked(False)
        self.cbxShapeGrid.stateChanged.connect(self.cbxShapeGrid_state_changed)
        self.sgpWidget = ShapePreference(self)
        self.sgpWidget.set_title("")
        self.sgpWidget.hide_name()
        self.sgpWidget.hide_title()
        self.sgpWidget.hide_cbxShow()
        self.sgpWidget.set_color("gray")
        self.sgpWidget.set_opacity(0.8)
        self.sgpWidget.hide()
        self.cbxArrow = QCheckBox(self.tr("Show arrow"))
        self.cbxArrow.setChecked(True)
        self.cbxArrow.stateChanged.connect(self.arrow_preference_changed)
        self.btnArrowColor = QPushButton(self.tr("Arrow color"))
        self.btnArrowColor.setMinimumSize(20, 20)
        self.btnArrowColor.setStyleSheet("background-color: yellow")
        self.btnArrowColor.setToolTip("yellow")
        self.btnArrowColor.setCursor(Qt.PointingHandCursor)
        self.btnArrowColor.clicked.connect(self.on_btnArrowColor_clicked)
        self.sgpWidget.shape_preference_changed.connect(self.shape_grid_preference_changed)

        self.gbOverlay.layout().addWidget(self.cbxDepthShade, 1)
        self.gbOverlay.layout().addWidget(self.cbxAverage, 1)
        self.gbOverlay.layout().addWidget(self.cbxConvexHull, 1)
        self.gbOverlay.layout().addWidget(self.cbxConfidenceEllipse, 1)
        self.gbOverlay.layout().addWidget(self.cbxShapeGrid, 1)
        self.gbOverlay.layout().addWidget(self.sgpWidget, 2)
        self.plot_setting_layout.addWidget(self.gbOverlay)

    def _setup_regression_controls(self):
        """Setup regression-related controls"""
        self.cbxRegression = QCheckBox()
        self.cbxRegression.setText(self.tr("Show regression"))
        self.cbxRegression.setChecked(False)
        self.cbxRegression.stateChanged.connect(self.update_chart)
        self.lblRegressionBasedon = QLabel(self.tr("Group by"))
        self.comboRegressionBasedOn = QComboBox()
        self.comboRegressionBasedOn.currentIndexChanged.connect(self.comboRegressionBasedOn_changed)

        self.comboRegressionBy = QComboBox()
        self.comboRegressionBy.addItem("All")
        self.comboRegressionBy.addItem("By group")
        self.comboRegressionBy.addItem("Select group")
        self.comboRegressionBy.setCurrentIndex(1)
        self.comboRegressionBy.currentIndexChanged.connect(self.comboRegressionBy_changed)
        self.comboSelectGroup = QComboBox()
        self.comboSelectGroup.currentIndexChanged.connect(self.comboSelectGroup_changed)
        self.comboSelectGroup.hide()
        model = self.comboSelectGroup.model()
        model.itemChanged.connect(self.comboSelectGroup_itemChanged)
        self.cbxExtrapolate = QCheckBox(self.tr("Extrapolate"))
        self.cbxExtrapolate.setChecked(True)
        self.cbxExtrapolate.stateChanged.connect(self.update_chart)
        self.lblDegree = QLabel(self.tr("Degree"))
        self.sbxDegree = QSpinBox()
        self.sbxDegree.setValue(1)
        self.sbxDegree.textChanged.connect(self.update_chart)
        self.cbxAnnotation = QCheckBox()
        self.cbxAnnotation.setText(self.tr("Annotation"))
        self.cbxAnnotation.stateChanged.connect(self.update_chart)
        self.cbxAnnotation.setChecked(False)

        self.gbRegression = QGroupBox()
        self.gbRegression.setTitle(self.tr("Regression settings"))
        self.gbRegression.setLayout(QHBoxLayout())

        self.gbRegression.layout().addWidget(self.cbxRegression, 1)
        self.gbRegression.layout().addWidget(self.lblRegressionBasedon, 0)
        self.gbRegression.layout().addWidget(self.comboRegressionBasedOn, 1)
        # self.gbRegression.layout().addWidget(self.comboRegressionBy, 1)
        self.gbRegression.layout().addWidget(self.comboSelectGroup, 1)
        self.gbRegression.layout().addWidget(self.cbxExtrapolate, 1)
        self.gbRegression.layout().addWidget(self.lblDegree, 0)
        self.gbRegression.layout().addWidget(self.sbxDegree, 1)
        self.gbRegression.layout().addWidget(self.cbxAnnotation, 1)
        self.plot_setting_layout.addWidget(self.gbRegression)

    def _setup_plot_layout(self):
        """Setup the main plot layout with toolbar and canvases"""
        self.visualization_layout = QGridLayout()
        self.visualization_widget = QWidget()
        self.visualization_widget.setLayout(self.visualization_layout)
        self.plot_layout = QVBoxLayout()
        self.plot_widget = QWidget()
        self.plot_widget.setLayout(self.plot_layout)
        # self.plot_layout.addWidget(self.plot_control_widget)
        # self.plot_layout.addWidget(self.regression_widget)
        self.plot_preference_button = QPushButton(QIcon(mu.resource_path("icons/M2Preferences_1.png")), "")
        self.plot_preference_button.setStyleSheet("border: none; padding: 0px;")
        self.plot_preference_button.setIconSize(QSize(32, 32))
        self.plot_preference_button.clicked.connect(self.show_plot_preference)
        self.plot_preference_button.setAutoDefault(False)
        self.btn_save_plot = QPushButton(self.tr("Export Chart"))
        self.btn_save_plot.clicked.connect(self.export_chart)

        self.toolbar_widget = QWidget()
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_widget.setLayout(self.toolbar_layout)
        self.toolbar_layout.addWidget(self.toolbar2)
        self.toolbar_layout.addWidget(self.toolbar3)
        self.toolbar_layout.addWidget(self.gbChartBasics)
        self.toolbar_layout.addWidget(self.btn_save_plot)
        self.toolbar_layout.addWidget(self.plot_preference_button)

        self.plot_layout.addWidget(self.toolbar_widget)
        self.plot_layout.addWidget(self.plot_setting_widget)
        self.plot_layout.addWidget(self.plot_widget2)
        self.plot_layout.addWidget(self.plot_widget3)

    def _setup_shape_view_controls(self):
        """Setup shape view controls and animation options"""
        self.view_layout = QVBoxLayout()
        self.view_widget = QWidget()
        self.view_widget.setLayout(self.view_layout)
        self.shape_view_layout = QVBoxLayout()

        self.btnResetPose = QPushButton(self.tr("Reset Pose"))
        self.btnResetPose.clicked.connect(self.reset_shape_pose)
        self.btnAnimate = QPushButton(self.tr("Animate"))
        self.btnAnimate.clicked.connect(self.animate_shape)
        self.cbxRecordAnimation = QCheckBox()
        self.cbxRecordAnimation.setText(self.tr("Record"))
        self.cbxRecordAnimation.setChecked(False)
        self.cbxRecordAnimation.stateChanged.connect(self.record_animation_changed)
        self.edtNumFrames = QLineEdit()
        self.total_frame = 120
        self.pause_frame = 0
        self.edtNumFrames.setText(str(self.total_frame))
        self.edtNumFrames.setFixedWidth(40)
        self.record_animation = False
        self.animation_frame_list = []

        self.animate_option_widget = QWidget()
        self.animate_option_layout = QHBoxLayout()
        self.animate_option_widget.setLayout(self.animate_option_layout)
        self.animate_option_layout.addWidget(self.btnAnimate)
        self.animate_option_layout.addWidget(self.cbxRecordAnimation)
        self.animate_option_layout.addWidget(self.edtNumFrames)

        self.shape_preference_button = QPushButton(QIcon(mu.resource_path("icons/M2Preferences_1.png")), "")
        self.shape_preference_button.setStyleSheet("border: none; padding: 0px;")
        self.shape_preference_button.setIconSize(QSize(32, 32))
        self.shape_preference_button.clicked.connect(self.shape_preference_button_clicked)
        self.shape_preference_button.setAutoDefault(False)

        self.shape_option_widget = QWidget()
        self.shape_option_layout = QHBoxLayout()
        self.shape_option_widget.setLayout(self.shape_option_layout)
        self.shape_option_layout.addWidget(self.lblVisualization, 0)
        self.shape_option_layout.addWidget(self.comboVisualization, 1)

        self.shape_option_layout.addWidget(self.animate_option_widget, 1)
        self.shape_option_layout.addWidget(self.btnResetPose, 0)
        self.shape_option_layout.addWidget(self.shape_preference_button, 0)
        self.view_layout.addWidget(self.shape_option_widget, 0)

        self.shape_preference_widget = QWidget()
        self.shape_preference_layout = QVBoxLayout()
        self.shape_preference_widget.setLayout(self.shape_preference_layout)
        self.shape_preference_widget.hide()
        self.view_layout.addWidget(self.shape_preference_widget, 0)

        self.arrow_widget = QWidget()
        self.arrow_layout = QHBoxLayout()
        self.arrow_widget.setLayout(self.arrow_layout)
        self.arrow_layout.addWidget(self.cbxArrow)
        self.arrow_layout.addWidget(self.btnArrowColor)
        self.view_layout.addWidget(self.arrow_widget, 0)

    def _assemble_final_layout(self):
        """Assemble all components into the final layout"""
        self.shape_view_widget = QWidget()
        self.shape_view_widget.setLayout(self.shape_view_layout)
        self.shape_view_scroll_area = QScrollArea()
        self.shape_view_scroll_area.setWidgetResizable(True)
        self.shape_view_scroll_area.setWidget(self.shape_view_widget)
        self.view_layout.addWidget(self.shape_view_scroll_area)

        self.visualization_splitter = QSplitter(Qt.Horizontal)
        self.visualization_splitter.addWidget(self.plot_widget)
        self.visualization_splitter.addWidget(self.view_widget)
        self.visualization_splitter.setSizes([800, 300])
        self.visualization_splitter.splitterMoved.connect(self.on_splitter_moved)

        self.layout.addWidget(self.visualization_splitter)

    def comboSelectGroup_changed(self):
        # print("comboSelectGroup_changed")
        # self.update_chart()
        return

    def comboSelectGroup_itemChanged(self, item):
        # print("comboSelectGroup_itemChanged", self.ignore_change)
        if self.ignore_change:
            return

        self.update_chart()

    def comboRegressionBy_changed(self):
        self.comboSelectGroup.hide()
        if self.comboRegressionBy.currentText() == "By group":
            for shape_view in self.shape_view_list:
                shape_view.show()
        else:
            if self.comboRegressionBy.currentText() == "Select group":
                self.comboSelectGroup.show()
            for idx, shape_view in enumerate(self.shape_view_list):
                if idx == 0:
                    shape_view.show()
                else:
                    shape_view.hide()

        self.update_chart()

    def comboRegressionBasedOn_changed(self):
        if len(self.object_info_list) == 0:
            return
        self.update_chart()
        # pass
        # self.update_chart()

    def cbxShapeGrid_state_changed(self):
        # print("cbxShape_state_changed")
        # Set wait cursor while processing shape grid
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if self.cbxShapeGrid.isChecked():
                self.sgpWidget.show()
                self.update_chart()
            else:
                self.sgpWidget.hide()
                self.update_chart()
        finally:
            # Restore normal cursor after processing
            QApplication.restoreOverrideCursor()

    def export_chart(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter("PNG (*.png);;JPG (*.jpg);;PDF (*.pdf);;SVG (*.svg);;All files (*.*)")
        dialog.setDefaultSuffix("png")
        # dialog.setDirectory(self.m_app.last_opened_dir)
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            # self.m_app.last_opened_dir = dialog.directory().absolutePath()
            if filename:
                if self.cbxShapeGrid.isChecked():
                    self.save_composite_plot(filename)
                else:
                    self.fig2.savefig(filename)

    def save_composite_plot(self, filename):
        # def export_composite_image(chart_widget, shape_widgets, filename, format="PNG"):
        # 1. Create the combined canvas (QPixmap)
        canvas_width = self.plot_widget2.width()
        canvas_height = self.plot_widget2.height()
        # chart_aspect_ratio = canvas_width / canvas_height
        # target_width = 2048
        # canvas_width = target_width
        # size_ratio = target_width / canvas_width
        # canvas_height = int(target_width / chart_aspect_ratio)  # Maintain aspect ratio
        canvas = QPixmap(canvas_width, canvas_height)

        # canvas = QPixmap(canvas_width, canvas_height)
        # fig = self.plot_widget2.figure  # Assuming your chart widget has a 'figure' attribute
        # fig.set_size_inches(canvas_width / fig.dpi, canvas_height / fig.dpi)
        # chart_widget.render(painter)

        # 2. Initialize QPainter for drawing on the canvas
        painter = QPainter(canvas)

        # 3. Draw the Matplotlib chart onto the canvas
        self.plot_widget2.render(painter)

        # 4. Overlay the shape images
        for keyname in self.shape_grid.keys():
            view = self.shape_grid[keyname]["view"]
            if view:
                # print("keyname", keyname, "x_val", self.shape_grid[keyname]['x_val'], "y_val", self.shape_grid[keyname]['y_val'])
                transform = self.ax2.transData
                display_coords = transform.transform(
                    (self.shape_grid[keyname]["x_val"], self.shape_grid[keyname]["y_val"])
                )
                x_pixel, y_pixel = display_coords
                if sys.platform == "darwin":
                    x_pixel = x_pixel / 2
                    y_pixel = y_pixel / 2
                # print("display_coords", display_coords, "x_pixel", x_pixel, "y_pixel", y_pixel)
                fig_height = self.fig2.canvas.height()
                fig_width = self.fig2.canvas.width()
                view_height = int(fig_height / 4)
                view_width = int(fig_width / 4)
                x_pos = int(x_pixel)
                y_pos = int(fig_height - y_pixel)
                w, h = view.width(), view.height()
                w, h = 120, 90
                w = max(w, view_width)
                h = max(h, view_height)
                # print("view size", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height, "view pos 2", x_pos, y_pos)
                """
                self.shape_grid[keyname]['x_pos'] = x_pixel
                self.shape_grid[keyname]['y_pos'] = y_pixel
                #print("view size 2  ", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)

                view.setGeometry(self.shape_grid[keyname]['x_pos']-int(w/2), self.shape_grid[keyname]['y_pos']-int(h/2), w, h)
                """

                # for shape_widget, (x, y) in zip(shape_widgets, pca_coordinates):
                # Convert PCA coordinates to pixel positions on the canvas
                # x_pixel, y_pixel = map_coordinates_to_pixels(x, y, canvas_width, canvas_height)

                # Draw the shape image onto the canvas
                view.update()
                if isinstance(view, ObjectViewer3D):
                    buffer = QPixmap(view.grabFrameBuffer(True))
                else:
                    buffer = QPixmap(view.grab())
                # print(buffer)
                painter.drawPixmap(x_pos - int(w / 2), y_pos - int(h / 2), buffer)

        # 5. End painting
        painter.end()

        # 6. Save the composite image
        canvas.save(filename, "PNG")

    def on_btnArrowColor_clicked(self, event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnArrowColor.toolTip()))
        if color is not None:
            self.btnArrowColor.setStyleSheet("background-color: " + color.name())
            self.btnArrowColor.setToolTip(color.name())
            self.arrow_color = color.name()
            # self.m_app.landmark_pref[dim]['color'] = color.name()
        self.arrow_preference_changed()

    def shape_grid_preference_changed(self, pref):
        self.shape_grid_pref_dict = pref
        if self.cbxShapeGrid.isChecked():
            for key in self.shape_grid:
                if self.shape_grid[key]["view"] is not None:
                    self.shape_grid[key]["view"].set_shape_preference(self.shape_grid_pref_dict)
                    self.shape_grid[key]["view"].update()

    def event(self, event):
        if event.type() in [QEvent.WindowActivate, QEvent.WindowStateChange] and self.initialized:
            # print("Window has been activated")
            self.handle_window_focus()
        return super().event(event)

    def handle_window_focus(self):
        # print("handle_window_focus")
        if self.cbxShapeGrid.isChecked():
            for key in self.shape_grid:
                if self.shape_grid[key]["view"] is not None:
                    self.shape_grid[key]["view"].raise_()
                    self.shape_grid[key]["view"].update()

    def shape_preference_button_clicked(self):
        # print("shape preference button clicked")
        if self.shape_preference_widget.isVisible():
            self.shape_preference_widget.hide()
            self.arrow_widget.hide()
        else:
            self.shape_preference_widget.show()
            if self.mode == MODE_COMPARISON2:
                self.arrow_widget.show()
            # self.chart_option_widget.hide()

    def record_animation_changed(self):
        self.record_animation = self.cbxRecordAnimation.isChecked()

    def chart_animation(self):
        # print("chart_animation", self.animation_counter)
        idx = 0
        if self.animation_counter < self.pause_frame:
            idx = 0
        elif self.animation_counter >= self.pause_frame and self.animation_counter < self.half_frame + self.pause_frame:
            # 0 -> half frame
            idx = self.animation_counter - self.pause_frame
        elif (
            self.animation_counter >= self.half_frame + self.pause_frame
            and self.animation_counter < self.half_frame + 2 * self.pause_frame
        ):
            idx = self.half_frame - 1
        elif (
            self.animation_counter >= self.half_frame + 2 * self.pause_frame
            and self.animation_counter < self.total_frame + 2 * self.pause_frame
        ):
            # half_frame -> 0
            idx = self.total_frame - self.animation_counter + 2 * self.pause_frame - 1
        elif (
            self.animation_counter >= self.total_frame + 2 * self.pause_frame
            and self.animation_counter < self.total_frame + 3 * self.pause_frame
        ):
            idx = 0
        elif self.animation_counter == self.total_frame + 3 * self.pause_frame:
            safe_remove_artist(self.animation_shape["point"], self.ax2)
            self.animation_shape["point"] = None
            self.timer.stop()
            self.fig2.canvas.draw()
            # wait cursor
            if self.record_animation:
                self.create_video_from_frames()
            QApplication.restoreOverrideCursor()
            self.toolbar_widget.show()
            self.shape_option_widget.show()
            return
        # print("chart_animation", self.animation_counter, idx, self.pause_frame, self.half_frame, self.total_frame)

        x = self.animation_x_range[idx]
        y = self.animation_y_range[idx]
        # print("chart_animation", x, y, self.animation_counter)
        # self.animation_shape['point']
        self.animation_shape["point"].set_offsets([x, y])
        self.fig2.canvas.draw()
        self.animation_counter += 1

        """ show shape """
        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        shape_to_visualize = np.zeros((1, len(self.analysis_result_list[0])))
        x_value = flip_axis1 * x
        y_value = flip_axis2 * y
        if axis1 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis1] = x_value
        shape_to_visualize[0][axis2] = y_value
        unrotated_shape = self.unrotate_shape(shape_to_visualize)

        # print("0-4:",datetime.datetime.now())
        self.show_shape(unrotated_shape[0], 0)

        if self.record_animation:
            screen = QApplication.primaryScreen()
            x, y, width, height = self.geometry().getRect()
            # print("x,y,width,height", x, y, width, height)
            pixmap = screen.grabWindow(self.winId(), 0, 0, width, height)
            self.animation_frame_list.append(pixmap)
            # print("frame added", len(self.animation_frame_list))

        # print("chart_animation done")

    def create_video_from_frames(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for idx, frame in enumerate(self.animation_frame_list):
                # padding 3 digits
                filename = f"{temp_dir}/frame{idx:03}.png"
                # print("saving frame", filename)
                frame.save(filename)
            # Specify the path to your image files
            # image_folder = 'd:/'
            # video_name = 'output_video.avi'

            images = sorted(glob.glob(f"{temp_dir}/frame*.png"))
            if len(images) == 0:
                logger = logging.getLogger(__name__)
                logger.warning("No frame found")
                return
            frame = cv2.imread(images[0])
            height, width, layers = frame.shape

            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*"DIVX")  # or use 'XVID'

            # ask user for video directory
            # options = QFileDialog.Options()
            # options |= QFileDialog.DontUseNativeDialog
            video_name, _ = QFileDialog.getSaveFileName(self, "Save video file", "", "Video Files (*.avi)")
            if video_name == "":
                return
            # print("video_name", video_name)

            video = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))

            for image in images:
                video.write(cv2.imread(image))

            cv2.destroyAllWindows()
            video.release()

    def animate_shape(self):
        if self.mode not in [
            MODE_COMPARISON,
        ]:  # or self.comboRegressionBy.currentText() == "By group":
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.pause_frame = 15
        self.toolbar_widget.hide()
        self.shape_option_widget.hide()
        self.total_frame = int(self.edtNumFrames.text())
        self.half_frame = int(self.total_frame / 2)

        if self.mode in [MODE_COMPARISON]:
            from_shape = self.custom_shape_hash[0]
            to_shape = self.custom_shape_hash[1]
            x_from, y_from = from_shape["coords"]
            x_to, y_to = to_shape["coords"]
            # print("animate_shape", x_from, y_from, x_to, y_to)

            self.animation_x_range = np.linspace(x_from, x_to, self.half_frame)
            self.animation_y_range = np.linspace(y_from, y_to, self.half_frame)
            self.animation_shape = {"coords": [x_from, y_from], "point": None}

        elif self.mode in []:
            x_from = min(self.regression_data["x_val"])
            x_to = max(self.regression_data["x_val"])

            self.animation_x_range = np.linspace(x_from, x_to, self.half_frame)
            self.animation_y_range = np.zeros(self.half_frame)
            self.cbxExtrapolate.isChecked()
            curve = self.curve_list[0]
            # print("curve", curve)
            model = curve["model"]
            # if show_extrapolate:
            #    model = curve['curve2']
            # else:
            #    model = curve['curve']
            # print("model", model)
            for idx, x in enumerate(self.animation_x_range):
                self.animation_y_range[idx] = np.polyval(model, x)
            y_from = self.animation_y_range[0]
            self.animation_shape = {"coords": [x_from, y_from], "point": None}

        self.animation_counter = 0
        self.animation_frame_list = []
        self.animation_shape["point"] = self.ax2.scatter(x_from, y_from, s=100, c="red", marker="o")
        self.fig2.canvas.draw()

        self.timer = QTimer()
        self.timer.timeout.connect(self.chart_animation)
        self.timer.start(100)

    def reset_shape_pose(self):
        logger = logging.getLogger(__name__)
        logger.info("Reset shape pose initiated")
        self.rotation_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        logger.info(f"Resetting {len(self.shape_view_list)} shape views")
        for shape_view in self.shape_view_list:
            shape_view.reset_pose()  # Widget handles its own update

        logger.info(f"Resetting {len(self.shape_grid.keys())} shape grid views")
        for key in self.shape_grid.keys():
            view = self.shape_grid[key]["view"]
            if view:
                view.reset_pose()  # Widget handles its own update
        logger.info("Shape pose reset completed")

    def on_chart_dim_changed(self):
        # print("on chart dim changed")
        if self.rb2DChartDim.isChecked():
            self.toolbar3.hide()
            self.toolbar2.show()
            self.plot_widget3.hide()
            self.plot_widget2.show()
            self.toolbar2.show()
            self.toolbar3.hide()
            self.lblAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.cbxDepthShade.hide()
        else:
            self.toolbar3.show()
            self.toolbar2.hide()
            self.plot_widget2.hide()
            self.plot_widget3.show()
            self.toolbar2.hide()
            self.toolbar3.show()
            self.lblAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.cbxDepthShade.show()

    def show_plot_preference(self):
        if self.plot_setting_widget.isVisible():
            self.plot_setting_widget.hide()
        else:
            self.plot_setting_widget.show()

    def on_splitter_moved(self):
        self.resizeEvent(None)

    def showEvent(self, event):
        # print("show event")
        self.resizeEvent(None)

    def comboVisualizationMethod_changed(self):
        new_mode = self.comboVisualization.currentIndex()
        # print("before set_mode")
        self.set_mode(new_mode)
        # print("after set_mode")

    def set_growth_trajectory_mode(self):
        # self.mode = MODE_GROWTH_TRAJECTORY
        # self.comboGroupBy.setEnabled(False)
        # self.comboGroupBy.hide()
        # self.lblGroupBy.hide()
        # self.show_analysis_result()

        self.comboAxis1.setCurrentText(CENTROID_SIZE_TEXT)
        self.comboAxis2.setCurrentIndex(0)
        self.update_chart()

    def set_mode(self, mode):
        # print("set mode", mode)
        self.mode = mode

        self.ignore_change = True
        if False:  # mode == MODE_GROWTH_TRAJECTORY:
            self.comboAxis1.setCurrentText(CENTROID_SIZE_TEXT)
            self.comboAxis2.setCurrentIndex(0)
            self.comboAxis3.setCurrentIndex(1)
        else:
            # elif mode == MODE_CUSTOM:
            self.comboAxis1.setCurrentIndex(1)
            self.comboAxis2.setCurrentIndex(1)
            self.comboAxis3.setCurrentIndex(2)
        # print("inside set_mode 1")
        self.cbxRegression.setChecked(False)
        if mode in [MODE_REGRESSION]:
            self.cbxRegression.setChecked(True)

        # print("inside set_mode 1.5")
        self.cbxAverage.setChecked(False)
        if mode == MODE_AVERAGE:
            self.cbxAverage.setChecked(True)
        self.ignore_change = False

        if mode in [MODE_COMPARISON, MODE_REGRESSION]:
            self.animate_option_widget.show()
        else:
            self.animate_option_widget.hide()

        if mode == MODE_COMPARISON2:
            self.arrow_widget.show()
        else:
            self.arrow_widget.hide()

        self.prepare_shape_view()
        self.resizeEvent(None)

        # print("inside set_mode 3")
        if mode == MODE_EXPLORATION:
            self.pick_idx = 0
            self.is_picking_shape = True
            self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.is_picking_shape = False
            self.pick_idx = -1
            self.plot_widget2.setCursor(QCursor(Qt.ArrowCursor))

    def prepare_shape_view(self):
        for shape_label in self.shape_label_list:
            shape_label.deleteLater()
        for shape_button in self.shape_button_list:
            shape_button.deleteLater()
        for shape_preference in self.shape_preference_list:
            shape_preference.deleteLater()
        for shape_view in self.shape_view_list:
            self.shape_view_layout.removeWidget(shape_view)
            shape_view.deleteLater()
        for key in self.custom_shape_hash.keys():
            self.custom_shape_hash[key]["coords"] = []
            if self.custom_shape_hash[key]["point"] is not None:
                safe_remove_artist(self.custom_shape_hash[key]["point"], self.ax2)
            self.custom_shape_hash[key]["point"] = None
            if self.custom_shape_hash[key]["label"] is not None:
                safe_remove_artist(self.custom_shape_hash[key]["label"], self.ax2)
            self.custom_shape_hash[key]["label"] = None
        self.arrow_widget.hide()

        # self.custom_shape_list = []
        self.shape_view_list = []
        self.shape_label_list = []
        self.shape_button_list = []
        self.shape_preference_list = []
        self.custom_shape_hash = {}
        self.grid_view_list = []

        if self.mode in [MODE_REGRESSION, MODE_AVERAGE]:
            keyname_list = self.scatter_data.keys()
        elif self.mode == MODE_COMPARISON:
            keyname_list = ["A", "B"]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {
                    "name": keyname,
                    "coords": [],
                    "point": None,
                    "color": None,
                    "label": None,
                }
        elif self.mode == MODE_COMPARISON2:
            keyname_list = ["A", "B"]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {
                    "name": keyname,
                    "coords": [],
                    "point": None,
                    "color": None,
                    "label": None,
                }
        elif self.mode == MODE_EXPLORATION:
            keyname_list = [""]
            for idx, keyname in enumerate(keyname_list):
                self.custom_shape_hash[idx] = {
                    "name": keyname,
                    "coords": [],
                    "point": None,
                    "color": None,
                    "label": None,
                }

        for idx, keyname in enumerate(keyname_list):
            if self.analysis.dimension == 2:
                shape_view = ObjectViewer2D(self)
                shape_view.show_index = False
            else:
                shape_view = ObjectViewer3D(self)
            self.shape_view_list.append(shape_view)

            if self.mode in [MODE_COMPARISON, MODE_COMPARISON2]:
                shape_button = QPushButton(QIcon(mu.resource_path("icons/M2Landmark_2.png")), "")
                # send idx to lambda function
                shape_button.clicked.connect(lambda checked, idx=idx: self.shape_button_clicked(idx))

                shape_button.setParent(shape_view)
                self.shape_button_list.append(shape_button)
                shape_button.setAutoDefault(False)

                # print("shape_preference", idx)
                shape_preference = ShapePreference(self)
                if idx == 0:
                    shape_preference.set_title(self.tr("Source shape"))
                    shape_preference.set_color("red")
                    shape_preference.set_opacity(1.0)
                else:
                    shape_preference.set_title(self.tr("Target shape"))
                    shape_preference.set_color("blue")
                    shape_preference.set_opacity(0.5)
                shape_preference.set_name(keyname)
                shape_preference.set_index(idx)
                # shape_preference.set_color(self.color_list[idx])
                # connect shape_preference signal to self.shape_preference_changed
                shape_preference.shape_preference_changed.connect(self.shape_preference_changed)

                self.shape_preference_list.append(shape_preference)
                self.shape_preference_layout.addWidget(shape_preference)
            else:
                shape_preference = ShapePreference(self)
                shape_preference.hide_title()
                shape_preference.hide_name()
                shape_preference.hide_cbxShow()
                shape_preference.set_name(keyname)
                shape_preference.set_index(idx)

                shape_preference.set_color(self.color_list[idx])
                self.shape_preference_list.append(shape_preference)
                self.shape_preference_layout.addWidget(shape_preference)
                shape_preference.shape_preference_changed.connect(self.shape_preference_changed)

            shape_label = QLabel(keyname)
            shape_label.setParent(shape_view)
            shape_label.setStyleSheet("background-color: " + self.bgcolor + "; color: white")

            self.shape_label_list.append(shape_label)
            if keyname == "__default__":
                shape_label.hide()

            self.shape_view_layout.addWidget(shape_view, 1)
            shape_view.set_object_name(keyname)
            shape_view.show()
        if self.mode == MODE_AVERAGE:
            self.show_average_shapes()
            # pass
        if self.mode == MODE_COMPARISON2:
            # self.arrow_widget.hi()
            self.shape_label_list[1].setParent(self.shape_view_list[0])
            self.shape_button_list[1].setParent(self.shape_view_list[0])
            self.shape_label_list[1].show()
            self.shape_button_list[1].show()
            self.shape_view_list[1].hide()
            # self.shape_view_list[0].set_source_shape_color(QColor(255,0,0))
            # self.shape_view_list[0].set_target_shape_color(QColor(0,0,255))
            self.shape_view_list[0].show_arrow = True

    def arrow_preference_changed(self):
        self.shape_view_list[0].show_arrow = self.cbxArrow.isChecked()
        self.shape_view_list[0].arrow_color = self.arrow_color
        self.shape_view_list[0].update()

    def shape_preference_changed(self, pref_dict):
        # print("shape_preference_changed", pref_dict)
        idx = pref_dict["index"]
        name = pref_dict["name"]
        # color = pref_dict['color']
        # self.custom_shape_hash[idx]['color'] = color
        shape_label = self.shape_label_list[idx]
        shape_label.setText(name)
        # label = QLabel("Your sample text")
        font_metrics = QFontMetrics(shape_label.font())
        text_rect = font_metrics.boundingRect(shape_label.text())

        width = text_rect.width() + 10  # Add some padding for visual comfort
        height = shape_label.height()
        x, y = shape_label.pos().x(), shape_label.pos().y()  # Get current position
        shape_label.setGeometry(x, y, width, height)

        # shape_label.adjustSize()

        # rendered_width = text_rect.width()
        # print("Rendered width:", rendered_width)

        if self.mode == MODE_COMPARISON2:
            self.custom_shape_hash[idx]["name"] = name
            shape_view = self.shape_view_list[0]
            idx = pref_dict["index"]
            if idx == 0:
                shape_view.set_source_shape_preference(pref_dict)
            else:
                shape_view.set_target_shape_preference(pref_dict)
            shape_view.update()
        else:
            shape_view = self.shape_view_list[idx]
            shape_view.set_shape_preference(pref_dict)
            shape_view.update()

        # self.custom_shape_hash[idx]['point'].set_color(color)
        # self.custom_shape_hash[idx]['label'].set_color(color)
        # self.custom_shape_hash[idx]['label'].setText(name)

    def show_average_shapes(self):
        keyname_list = self.scatter_data.keys()
        # print("show_average_shapes", keyname_list, self.average_shape)
        for idx, keyname in enumerate(keyname_list):
            # shape_view = ObjectViewer3D(self)
            # for idx, shape_view in enumerate(self.shape_view_list):
            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()

            x_average = self.average_shape[keyname]["x_val"]
            y_average = self.average_shape[keyname]["y_val"]
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
            x_value = flip_axis1 * x_average
            y_value = flip_axis2 * y_average
            shape_to_visualize = np.zeros((1, len(self.analysis_result_list[0])))

            if axis1 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis1] = x_value
            shape_to_visualize[0][axis2] = y_value
            unrotated_shape = self.unrotate_shape(shape_to_visualize)
            self.show_shape(unrotated_shape[0], idx)

            # shape_view.show()

    def shape_regression(self, evt):
        # print("shape regression", evt.xdata)
        for idx, _shape_view in enumerate(self.shape_view_list):
            # print("0-1:",datetime.datetime.now())
            # shape_view.clear_object()

            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
            shape_to_visualize = np.zeros((1, len(self.analysis_result_list[0])))
            # if axis1 == 10:
            # fit regression line
            y_value = 0
            curve = self.curve_list[idx]
            # print("0-2:",datetime.datetime.now(), evt.xdata, min(curve['size_range2']), max(curve['size_range2']))
            if evt.xdata >= min(curve["size_range2"]) and evt.xdata <= max(curve["size_range2"]):
                y_value = np.polyval(curve["model"], evt.xdata)
            else:
                continue
            x_value = flip_axis1 * evt.xdata
            # y_value = flip_axis2 * y_value

            if axis1 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis1] = x_value

            shape_to_visualize[0][axis2] = flip_axis2 * y_value
            # print("0-3:",datetime.datetime.now())
            unrotated_shape = self.unrotate_shape(shape_to_visualize)
            # print("0-4:",datetime.datetime.now())
            self.show_shape(unrotated_shape[0], idx)

    def shape_button_clicked(self, idx):
        # print("shape_button_clicked", idx)
        self.is_picking_shape = True
        self.pick_idx = idx
        self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))

        # self.shape_view_list[idx].show()

    def update_chart(self):
        # if self.ds_ops is not None and self.analysis_done is True:
        self.prepare_scatter_data()
        self.calculate_fit()
        # print("update chart", self.curve_list)
        self.show_analysis_result()

    def axis_changed(self):
        # if self.ds_ops is not None and self.analysis_done is True:
        if self.ignore_change:
            return

        self.update_chart()

    def flip_axis_changed(self, int):
        # if self.ds_ops is not None:
        self.update_chart()

    def read_settings(self):
        # self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/" + str(i), self.marker_list[i])
        self.bgcolor = self.m_app.settings.value("BackgroundColor", self.bgcolor)
        if self.m_app.remember_geometry is True:
            # print('loading geometry', self.remember_geometry)

            is_maximized = mu.value_to_bool(self.m_app.settings.value("IsMaximized/DataExplorationWindow", False))
            if is_maximized:
                # print("maximized true. restoring maximized state")
                # self.showMaximized()
                self.setWindowState(Qt.WindowMaximized)
            else:
                self.setGeometry(
                    self.m_app.settings.value("WindowGeometry/DataExplorationWindow", QRect(100, 100, 1400, 800))
                )
                # self.setGeometry(self.m_app.settings.value("WindowGeometry/DataExplorationWindow", QRect(100, 100, 1400, 800)))
                # print("maximized false")
                # self.showNormal()
                # pass
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        self.m_app.remember_geometry = mu.value_to_bool(
            self.m_app.settings.value("WindowGeometry/RememberGeometry", True)
        )
        if self.m_app.remember_geometry is True:
            # print("maximized:", self.isMaximized(), "geometry:", self.geometry())

            if self.isMaximized():
                self.m_app.settings.setValue("IsMaximized/DataExplorationWindow", True)
            else:
                self.m_app.settings.setValue("IsMaximized/DataExplorationWindow", False)
                self.m_app.settings.setValue("WindowGeometry/DataExplorationWindow", self.geometry())
                # print("save maximized false")

    def closeEvent(self, event):
        self.write_settings()
        # for shape_view in self.shape_view_list:
        #    shape_view.close()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]["view"]:
                self.shape_grid[key]["view"].close()
        # if self.analysis_dialog is not None:
        #    self.analysis_dialog.close()
        event.accept()

    def store_rotation(self, x_rad, y_rad):
        # print("store_rotation", x_rad, y_rad)
        rotationXMatrix = np.array(
            [[1, 0, 0, 0], [0, np.cos(y_rad), -np.sin(y_rad), 0], [0, np.sin(y_rad), np.cos(y_rad), 0], [0, 0, 0, 1]]
        )

        rotationYMatrix = np.array(
            [[np.cos(x_rad), 0, np.sin(x_rad), 0], [0, 1, 0, 0], [-np.sin(x_rad), 0, np.cos(x_rad), 0], [0, 0, 0, 1]]
        )
        # print(rotationXMatrix)
        # print(rotationYMatrix)
        # print("rotation matrix before\n",self.rotation_matrix)
        new_rotation_matrix = np.dot(rotationXMatrix, rotationYMatrix)
        self.rotation_matrix = np.dot(new_rotation_matrix, self.rotation_matrix)
        # print("rotation matrix after\n",self.rotation_matrix)

    def sync_rotation(self):
        if len(self.shape_view_list) > 0:
            temp_rotate_x = math.radians(self.shape_view_list[0].temp_rotate_x)
            temp_rotate_y = math.radians(self.shape_view_list[0].temp_rotate_y)
            # (math.radians(self.rotate_x),math.radians(self.rotate_y),apply_rotation_to_vertex)
            self.store_rotation(temp_rotate_x, temp_rotate_y)
        for key in self.shape_grid.keys():
            if self.shape_grid[key]["view"]:
                self.shape_grid[key]["view"].sync_rotation()
                self.shape_grid[key]["view"].update()

        for sv in self.shape_view_list:
            # self.temp_rotate_x = sv.temp_rotate_x
            # self.temp_rotate_y = sv.temp_rotate_y
            # sv.rotate_x = sv.temp_rotate_x
            # sv.rotate_y = sv.temp_rotate_y
            sv.sync_rotation()
            sv.update()

    def sync_temp_pan(self, shape_view, temp_pan_x, temp_pan_y):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_pan_x = temp_pan_x
                sv.temp_pan_y = temp_pan_y
                # sv.sync_zoom()
                sv.update()

    def sync_pan(self, shape_view, pan_x, pan_y):
        if len(self.shape_view_list) > 0:
            self.shape_view_pan_x = self.shape_view_list[0].pan_x
            self.shape_view_pan_y = self.shape_view_list[0].pan_y
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.pan_x = pan_x
                sv.pan_y = pan_y
                # sv.sync_zoom()
                sv.update()

    def sync_zoom(self, shape_view, zoom_factor):
        # print("sync_zoom", shape_view, zoom_factor)
        is_2D = False
        if isinstance(shape_view, ObjectViewer2D):
            is_2D = True

        if len(self.shape_view_list) > 0:
            if is_2D:
                pass
                # self.shape_view_dolly = self.shape_view_list[0].scale
            else:
                self.shape_view_dolly = self.shape_view_list[0].dolly

        for sv in self.shape_view_list:
            if sv != shape_view:
                if is_2D:
                    sv.adjust_scale(zoom_factor, recurse=False)
                else:
                    sv.dolly = zoom_factor
                # sv.sync_zoom()
                sv.update()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]["view"]:
                if is_2D:
                    self.shape_grid[key]["view"].adjust_scale(zoom_factor)
                else:
                    self.shape_grid[key]["view"].dolly = zoom_factor
                self.shape_grid[key]["view"].update()

    def sync_temp_zoom(self, shape_view, temp_dolly):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_dolly = temp_dolly
                # sv.sync_zoom()
                sv.update()
        for key in self.shape_grid.keys():
            if self.shape_grid[key]["view"]:
                self.shape_grid[key]["view"].temp_dolly = temp_dolly
                self.shape_grid[key]["view"].update()

    def sync_temp_rotation(self, shape_view, temp_rotate_x, temp_rotate_y):
        for sv in self.shape_view_list:
            if sv != shape_view:
                sv.temp_rotate_x = temp_rotate_x
                sv.temp_rotate_y = temp_rotate_y
                # sv.sync_rotation()
                sv.update()
        for key in self.shape_grid.keys():
            view = self.shape_grid[key]["view"]
            if view:
                view.temp_rotate_x = temp_rotate_x
                view.temp_rotate_y = temp_rotate_y
                view.update()

        # self.object_view_3d.sync_rotation(rotation_x, rotation_y)

    def moveEvent(self, event):
        self.reposition_shape_grid()

    def resizeEvent(self, event):
        for idx, shape_view in enumerate(self.shape_view_list):
            width = int(shape_view.width())
            int(width / 2)
            y_pos = 0
            x_pos = 0
            if self.mode == MODE_COMPARISON2:
                y_pos = (idx) * 32
                x_pos = 32
            if self.mode == MODE_COMPARISON:
                x_pos = 32
            # else:
            shape_label = self.shape_label_list[idx]
            font_metrics = QFontMetrics(shape_label.font())
            text_rect = font_metrics.boundingRect(shape_label.text())

            width = text_rect.width() + 10  # Add some padding for visual comfort
            height = shape_label.height()
            # x, y = shape_label.pos().x(), shape_label.pos().y()  # Get current position
            # shape_label.setGeometry(x, y, width, height)

            self.shape_label_list[idx].setGeometry(x_pos, y_pos, width, height)
        for idx, button in enumerate(self.shape_button_list):
            # button = self.shape_button_list[idx]
            y_pos = 0
            if self.mode == MODE_COMPARISON2:
                y_pos = (idx) * 32
            button.setGeometry(0, y_pos, 32, 32)
        self.reposition_shape_grid()

    def load_comboSelectgroup(self):
        # print("load_comboSelectgroup", self.ignore_change)
        # if self.comboRegressionBy.
        propertyname_index = self.comboGroupBy.currentData()
        self.comboSelectGroup.clear()
        unique_groupname_list = []
        for _idx, obj in enumerate(self.object_info_list):
            if "variable_list" in obj.keys():
                if propertyname_index > -1 and propertyname_index < len(obj["variable_list"]):
                    key_name = obj["variable_list"][self.scatter_variable_index]
                    if key_name not in unique_groupname_list:
                        unique_groupname_list.append(key_name)
                        self.comboSelectGroup.addItem(key_name)
            else:
                if propertyname_index > -1 and propertyname_index < len(obj["property_list"]):
                    key_name = obj["property_list"][self.scatter_variable_index]
                    if key_name not in unique_groupname_list:
                        unique_groupname_list.append(key_name)
                        self.comboSelectGroup.addItem(key_name)
        model = self.comboSelectGroup.model()
        # Make all items checkable
        for i in range(model.rowCount()):
            item = model.item(i)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)  # Initially unchecked

    def comboGroupBy_changed(self):
        if self.ignore_change:
            return
        self.load_comboSelectgroup()
        self.update_chart()
        self.prepare_shape_view()
        self.resizeEvent(None)
        # shape_combo.setGeometry(150,0,150,20)
        # self.prepare_scatter_data()
        # self.calculate_fit()
        # self.show_analysis_result()

    def comboShapeview_changed(self):
        logger = logging.getLogger(__name__)
        logger.debug("shape_combo_changed")
        # shape_view_index = self.shape_combo_list.index(combo)
        # shape_view = self.shape_view_list[shape_view_index]

        return

    def set_analysis(self, analysis, analysis_method, group_by):
        self.ignore_change = True
        # print("set_analysis", analysis, analysis_method, group_by, self.ignore_change)
        self.analysis = analysis
        self.analysis_method = analysis_method
        self.edtAnalysisName.setText(analysis.analysis_name)
        self.edtSuperimposition.setText(analysis.superimposition_method)
        self.edtOrdination.setText(self.analysis_method)
        # self.edtGroupBy.setText(analysis.group_by)
        self.comboGroupBy.clear()
        self.comboGroupBy.addItem("Select property", -1)
        self.comboRegressionBasedOn.clear()
        self.comboRegressionBasedOn.addItem("Select property", -1)

        valid_property_index_list = analysis.dataset.get_grouping_variable_index_list()
        variablename_list = analysis.dataset.get_variablename_list()
        for idx in valid_property_index_list:
            property = variablename_list[idx]
            self.comboGroupBy.addItem(property, idx)
            self.comboRegressionBasedOn.addItem(property, idx)

        # print("set_analysis 2", analysis, analysis_method, group_by, self.ignore_change)
        if analysis_method == "PCA":
            # self.lblGroupBy.hide()
            self.comboGroupBy.setEnabled(True)
            self.comboRegressionBasedOn.setEnabled(True)
        else:
            # self.lblGroupBy.show()
            self.comboGroupBy.setEnabled(False)
            self.comboRegressionBasedOn.setEnabled(False)

        if group_by in analysis.dataset.get_variablename_list():
            self.comboGroupBy.setCurrentText(group_by)
            self.comboRegressionBasedOn.setCurrentText(group_by)
        else:
            self.comboGroupBy.setCurrentIndex(0)
            self.comboRegressionBasedOn.setCurrentIndex(0)
        # print("going to set mode")

        obj = self.analysis.dataset.object_list[0]
        lm_list = obj.get_landmark_list()
        dim = self.analysis.dataset.dimension
        analysis_dim = len(lm_list) * dim
        # print("set_analysis 3", analysis, analysis_method, group_by, self.ignore_change)

        self.comboAxis1.clear()
        self.comboAxis2.clear()
        self.comboAxis3.clear()

        self.comboAxis1.addItem(CENTROID_SIZE_TEXT, CENTROID_SIZE_VALUE)
        for i in range(analysis_dim):
            self.comboAxis1.addItem("PC" + str(i + 1), i)
            self.comboAxis2.addItem("PC" + str(i + 1), i)
            self.comboAxis3.addItem("PC" + str(i + 1), i)
        # print("set_analysis 4", analysis, analysis_method, group_by, self.ignore_change)

        # print("set_analysis 5", analysis, analysis_method, group_by, self.ignore_change)
        self.object_info_list = json.loads(self.analysis.object_info_json)
        for obj in self.object_info_list:
            if "property_list" in obj.keys():
                obj["variable_list"] = obj["property_list"]
        if self.analysis_method == "PCA":
            self.analysis_result_list = json.loads(self.analysis.pca_analysis_result_json)
            # Load eigenvalues for displaying variance explained
            if self.analysis.pca_eigenvalues_json:
                try:
                    eigenvalues_data = json.loads(self.analysis.pca_eigenvalues_json)
                    # eigenvalues_data is a list of [eigenvalue, percentage] pairs
                    self.eigen_value_percentages = [item[1] for item in eigenvalues_data] if eigenvalues_data else []
                except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
                    logger.warning(f"Failed to parse eigenvalues JSON: {e}")
                    self.eigen_value_percentages = []
            else:
                self.eigen_value_percentages = []
        elif self.analysis_method == "CVA":
            self.analysis_result_list = json.loads(self.analysis.cva_analysis_result_json)

        # print("set_analysis 6", analysis, analysis_method, group_by, self.ignore_change)

        scatter_variable_name = self.comboGroupBy.currentText()
        regression_variable_name = self.comboRegressionBasedOn.currentText()
        if self.analysis.propertyname_str:
            self.variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            self.variablename_list = self.analysis.dataset.get_variablename_list()
        self.scatter_variable_index = (
            self.variablename_list.index(scatter_variable_name)
            if scatter_variable_name in self.variablename_list
            else -1
        )
        self.regression_variable_index = (
            self.variablename_list.index(regression_variable_name)
            if regression_variable_name in self.variablename_list
            else -1
        )
        # self.scatter_variable_index = self.variablename_list.index(propertyname) if propertyname in self.variablename_list else -1
        # print("set analysis load_comboselect", self.ignore_change)
        self.load_comboSelectgroup()
        self.set_mode(MODE_EXPLORATION)
        self.ignore_change = False

    def prepare_scatter_data(self):
        show_shape_grid = self.cbxShapeGrid.isChecked()
        show_convex_hull = self.cbxConvexHull.isChecked()
        show_confidence_ellipse = self.cbxConfidenceEllipse.isChecked()
        self.comboRegressionBasedOn.currentText()
        # regression_by = self.comboRegressionBy.currentText()
        self.cbxRegression.isChecked()

        select_group_list = []
        for i in range(self.comboSelectGroup.count()):
            item = self.comboSelectGroup.model().item(i)
            if item.checkState() == Qt.Checked:
                select_group_list.append(item.text())
        # print("select_group_list", select_group_list)

        # regression_by_group = self.rbByGroup.isChecked()
        # regression_all_at_once = self.rbAllAtOnce.isChecked()

        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        axis3 = self.comboAxis3.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() else 1.0

        if self.analysis.propertyname_str:
            self.variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            self.variablename_list = self.analysis.dataset.get_variablename_list()
        symbol_candidate = ["o", "s", "^", "x", "+", "d", "v", "<", ">", "p", "h"]
        symbol_candidate = self.marker_list[:]
        color_candidate = ["blue", "green", "black", "cyan", "magenta", "yellow", "gray", "red"]
        color_candidate = self.color_list[:]
        # print("color list:", self.color_list, "marker list:", self.marker_list)
        # print("color candidate:", color_candidate, "symbol candidate:", symbol_candidate)

        scatter_variable_name = self.comboGroupBy.currentText()
        regression_variable_name = self.comboRegressionBasedOn.currentText()

        self.scatter_variable_index = (
            self.variablename_list.index(scatter_variable_name)
            if scatter_variable_name in self.variablename_list
            else -1
        )
        self.regression_variable_index = (
            self.variablename_list.index(regression_variable_name)
            if regression_variable_name in self.variablename_list
            else -1
        )
        self.scatter_data = {}
        self.scatter_result = {}
        self.average_shape = {}
        self.regression_data = {}
        # self.regression_data = { 'x_val':[], 'y_val':[], 'z_val':[] }
        # self.shape_grid = {}
        self.data_range = {
            "x_min": 99999,
            "x_max": -99999,
            "y_min": 99999,
            "y_max": -99999,
            "z_min": 99999,
            "z_max": -99999,
            "x_sum": 0,
            "y_sum": 0,
            "z_sum": 0,
            "x_avg": 0,
            "y_avg": 0,
            "z_avg": 0,
        }
        SCATTER_MEDIUM_SIZE = 50
        scatter_size = SCATTER_MEDIUM_SIZE
        # if self.plot_size.lower() == 'small':
        #    scatter_size = SCATTER_SMALL_SIZE
        # elif self.plot_size.lower() == 'medium':
        #    scatter_size = SCATTER_MEDIUM_SIZE
        # elif self.plot_size.lower() == 'large':
        #    scatter_size = SCATTER_LARGE_SIZE

        # print("removing shape grid")
        for scatter_key_name in self.shape_grid.keys():
            # print("removing shape grid", key_name)
            if self.shape_grid[scatter_key_name]["view"] is not None:
                self.shape_grid[scatter_key_name]["view"].hide()
                self.shape_grid[scatter_key_name]["view"].deleteLater()
                self.shape_grid[scatter_key_name]["view"] = None

        key_list = []
        key_list.append("__default__")
        self.scatter_data["__default__"] = {
            "x_val": [],
            "y_val": [],
            "z_val": [],
            "data": [],
            "hoverinfo": [],
            "text": [],
            "property": "",
            "symbol": "o",
            "color": color_candidate[0],
            "size": scatter_size,
        }
        self.average_shape["__default__"] = {
            "x_val": 0,
            "y_val": 0,
            "z_val": 0,
            "data": [],
            "hoverinfo": [],
            "text": [],
            "property": "",
            "symbol": "o",
            "color": color_candidate[0],
            "size": scatter_size,
        }
        self.regression_data["__default__"] = {
            "x_val": [],
            "y_val": [],
            "z_val": [],
            "data": [],
            "hoverinfo": [],
            "text": [],
            "property": "",
            "symbol": "o",
            "color": color_candidate[0],
            "size": scatter_size,
        }
        # regression_key_name = ''
        # scatter_key_name = ''

        for idx, obj in enumerate(self.object_info_list):
            scatter_key_name = "__default__"
            regression_key_name = "__default__"

            if "variable_list" in obj.keys():
                if self.scatter_variable_index > -1 and self.scatter_variable_index < len(obj["variable_list"]):
                    scatter_key_name = obj["variable_list"][self.scatter_variable_index]
                if self.regression_variable_index > -1 and self.regression_variable_index < len(obj["variable_list"]):
                    regression_key_name = obj["variable_list"][self.regression_variable_index]
            else:
                if self.scatter_variable_index > -1 and self.scatter_variable_index < len(obj["property_list"]):
                    scatter_key_name = obj["property_list"][self.scatter_variable_index]

            if scatter_key_name not in self.scatter_data.keys():
                self.scatter_data[scatter_key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": scatter_key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }
                self.average_shape[scatter_key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": scatter_key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }

            if regression_key_name not in self.regression_data.keys():
                self.regression_data[regression_key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": regression_key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }

            if axis1 == CENTROID_SIZE_VALUE:
                # print("obj:", obj)
                self.scatter_data[scatter_key_name]["x_val"].append(obj["csize"])
                self.regression_data[regression_key_name]["x_val"].append(obj["csize"])
                # if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
                #    self.regression_data['x_val'].append(obj['csize'])
            else:
                self.scatter_data[scatter_key_name]["x_val"].append(flip_axis1 * self.analysis_result_list[idx][axis1])
                self.regression_data[regression_key_name]["x_val"].append(
                    flip_axis1 * self.analysis_result_list[idx][axis1]
                )
                # if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
                #    self.regression_data['x_val'].append(flip_axis1 * self.analysis_result_list[idx][axis1])
            self.scatter_data[scatter_key_name]["y_val"].append(flip_axis2 * self.analysis_result_list[idx][axis2])
            self.regression_data[regression_key_name]["y_val"].append(
                flip_axis2 * self.analysis_result_list[idx][axis2]
            )
            # if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
            #    self.regression_data['y_val'].append(flip_axis2 * self.analysis_result_list[idx][axis2])
            self.scatter_data[scatter_key_name]["z_val"].append(flip_axis3 * self.analysis_result_list[idx][axis3])
            self.regression_data[regression_key_name]["z_val"].append(
                flip_axis3 * self.analysis_result_list[idx][axis3]
            )
            # if regression_by == 'All' or ( regression_by == 'Select group' and scatter_key_name in select_group_list ):
            #    self.regression_data['z_val'].append(flip_axis3 * self.analysis_result_list[idx][axis3])

            self.scatter_data[scatter_key_name]["data"].append(obj)
            self.regression_data[regression_key_name]["data"].append(obj)

            self.data_range["x_max"] = max(self.data_range["x_max"], self.scatter_data[scatter_key_name]["x_val"][-1])
            self.data_range["x_min"] = min(self.data_range["x_min"], self.scatter_data[scatter_key_name]["x_val"][-1])
            self.data_range["x_sum"] += self.scatter_data[scatter_key_name]["x_val"][-1]
            self.data_range["y_max"] = max(self.data_range["y_max"], self.scatter_data[scatter_key_name]["y_val"][-1])
            self.data_range["y_min"] = min(self.data_range["y_min"], self.scatter_data[scatter_key_name]["y_val"][-1])
            self.data_range["y_sum"] += self.scatter_data[scatter_key_name]["y_val"][-1]
            self.data_range["z_max"] = max(self.data_range["z_max"], self.scatter_data[scatter_key_name]["z_val"][-1])
            self.data_range["z_min"] = min(self.data_range["z_min"], self.scatter_data[scatter_key_name]["z_val"][-1])
            self.data_range["z_sum"] += self.scatter_data[scatter_key_name]["z_val"][-1]

        if show_shape_grid:
            self.data_range["x_avg"] = self.data_range["x_sum"] / len(self.object_info_list)
            self.data_range["y_avg"] = self.data_range["y_sum"] / len(self.object_info_list)
            x_key_list = ["x_min", "x_avg", "x_max"]
            y_key_list = ["y_min", "y_avg", "y_max"]
            for x_key in x_key_list:
                for y_key in y_key_list:
                    scatter_key_name = x_key + "_" + y_key
                    self.shape_grid[scatter_key_name] = {
                        "x_val": self.data_range[x_key],
                        "y_val": self.data_range[y_key],
                    }
                    if self.analysis.dataset.dimension == 3:
                        self.shape_grid[scatter_key_name]["view"] = ObjectViewer3D(parent=None, transparent=True)
                    else:
                        self.shape_grid[scatter_key_name]["view"] = ObjectViewer2D(parent=None, transparent=True)
                        self.shape_grid[scatter_key_name]["view"].show_index = False
                    self.shape_grid[scatter_key_name]["view"].set_object_name(scatter_key_name)

        # remove empty group
        if len(self.scatter_data["__default__"]["x_val"]) == 0:
            del self.scatter_data["__default__"]
            del self.average_shape["__default__"]
            del self.regression_data["__default__"]

        for scatter_key_name in self.scatter_data.keys():
            self.average_shape[scatter_key_name]["x_val"] = np.mean(self.scatter_data[scatter_key_name]["x_val"])
            self.average_shape[scatter_key_name]["y_val"] = np.mean(self.scatter_data[scatter_key_name]["y_val"])
            self.average_shape[scatter_key_name]["z_val"] = np.mean(self.scatter_data[scatter_key_name]["z_val"])
            # group_hash[key_name]['text'].append(obj.object_name)
            # group_hash[key_name]['hoverinfo'].append(obj.id)

        if show_convex_hull:
            for scatter_key_name in self.scatter_data.keys():
                if len(self.scatter_data[scatter_key_name]["x_val"]) > 1:
                    self.scatter_data[scatter_key_name]["points"] = np.array(
                        [self.scatter_data[scatter_key_name]["x_val"], self.scatter_data[scatter_key_name]["y_val"]]
                    ).T
                    hull = ConvexHull(self.scatter_data[scatter_key_name]["points"])
                    self.scatter_data[scatter_key_name]["hull"] = hull

        if show_confidence_ellipse:
            for scatter_key_name in self.scatter_data.keys():
                if len(self.scatter_data[scatter_key_name]["x_val"]) > 1:
                    covariance = np.cov(
                        [self.scatter_data[scatter_key_name]["x_val"], self.scatter_data[scatter_key_name]["y_val"]]
                    )
                    confidence_level = 0.90  # For 95% confidence ellipse
                    alpha = 1 - confidence_level
                    n_std = stats.chi2.ppf(1 - alpha, df=2)  # Degrees of freedom = 2 for 2D ellipse
                    width, height, angle = mu.get_ellipse_params(covariance, n_std)
                    self.scatter_data[scatter_key_name]["ellipse"] = (width, height, angle)

        if len(self.scatter_data.keys()) == 0:
            return

        # assign color and symbol
        # sc_idx = 0
        for sc_idx, scatter_key_name in enumerate(self.scatter_data.keys()):
            if self.scatter_data[scatter_key_name]["color"] == "":
                self.scatter_data[scatter_key_name]["color"] = color_candidate[sc_idx % len(color_candidate)]
                self.scatter_data[scatter_key_name]["symbol"] = symbol_candidate[sc_idx % len(symbol_candidate)]
                # sc_idx += 1

        # rg_idx = 0
        for rg_idx, regression_key_name in enumerate(self.regression_data.keys()):
            if self.regression_data[regression_key_name]["color"] == "":
                self.regression_data[regression_key_name]["color"] = color_candidate[rg_idx % len(color_candidate)]
                self.regression_data[regression_key_name]["symbol"] = symbol_candidate[rg_idx % len(symbol_candidate)]
                # sc_idx += 1

    def calculate_fit(self):
        # self.scatter_data[key_name]['y_val']
        show_regression = self.cbxRegression.isChecked()
        if not show_regression:
            return
        regression_by = "By group"  # self.comboRegressionBy.currentText()

        key_list = self.regression_data.keys()
        # print("key list:", key_list)
        self.curve_list = []
        # data_range = self.data_range
        degree_text = self.sbxDegree.text()
        if degree_text == "":
            return

        degree = int(degree_text)
        if regression_by == "By group":
            for _idx, key in enumerate(key_list):
                x_vals = np.array(self.regression_data[key]["x_val"])
                y_vals = np.array(self.regression_data[key]["y_val"])

                if len(x_vals) < 2:
                    self.curve_list.append(None)
                    # self.shape_view_list[idx].hide()
                else:
                    # self.shape_view_list[idx].show()
                    model = np.polyfit(x_vals, y_vals, degree)
                    # model_list.append(model)
                    r_squared = self.calculate_r_squared(model, x_vals, y_vals)
                    # print(key, model, r_squared)
                    size_range = np.linspace(
                        min(self.regression_data[key]["x_val"]), max(self.regression_data[key]["x_val"]), 100
                    )
                    size_range2 = np.linspace(self.data_range["x_min"], self.data_range["x_max"], 100)
                    curve = np.polyval(model, size_range)
                    curve2 = np.polyval(model, size_range2)
                    self.curve_list.append(
                        {
                            "key": key,
                            "model": model,
                            "size_range": size_range,
                            "size_range2": size_range2,
                            "curve": curve,
                            "curve2": curve2,
                            "r_squared": r_squared,
                            "color": self.regression_data[key]["color"],
                        }
                    )
        else:
            color_candidate = ["blue", "green", "black", "cyan", "magenta", "yellow", "gray", "red"]
            color_candidate = self.color_list[:]
            color = color_candidate[len(self.scatter_data.keys())]

            x_vals = np.array(self.regression_data["x_val"])
            y_vals = np.array(self.regression_data["y_val"])
            if len(x_vals) < 2:
                self.curve_list.append(None)
                # self.shape_view_list[idx].hide()
            else:
                # self.shape_view_list[idx].show()
                model = np.polyfit(x_vals, y_vals, degree)
                r_squared = self.calculate_r_squared(model, x_vals, y_vals)
                size_range = np.linspace(min(self.regression_data["x_val"]), max(self.regression_data["x_val"]), 100)
                size_range2 = np.linspace(self.data_range["x_min"], self.data_range["x_max"], 100)
                curve = np.polyval(model, size_range)
                curve2 = np.polyval(model, size_range2)
                self.curve_list.append(
                    {
                        "key": "All",
                        "model": model,
                        "size_range": size_range,
                        "size_range2": size_range2,
                        "curve": curve,
                        "curve2": curve2,
                        "r_squared": r_squared,
                        "color": color,
                    }
                )

    def calculate_r_squared(self, model, x_vals, y_vals):
        y_mean = np.mean(y_vals)
        ss_total = np.sum((y_vals - y_mean) ** 2)
        ss_res = np.sum((y_vals - np.polyval(model, x_vals)) ** 2)
        r_squared = 1 - (ss_res / ss_total)
        return r_squared

    def show_analysis_result(self):
        # print("show analysis result", datetime.datetime.now())
        # self.plot_widget.clear()
        self.ax2.clear()

        # get axis1 and axis2 value from comboAxis1 and 2 index
        # depth_shade = False
        show_average_shape = self.cbxAverage.isChecked()
        show_regression = self.cbxRegression.isChecked()
        show_annotation = self.cbxAnnotation.isChecked()
        show_legend = self.cbxLegend.isChecked()
        show_variance = self.cbxShowVariance.isChecked() if hasattr(self, "cbxShowVariance") else False
        show_convex_hull = self.cbxConvexHull.isChecked()
        show_confidence_ellipse = self.cbxConfidenceEllipse.isChecked()
        show_axis_label = True
        show_extraplolate = self.cbxExtrapolate.isChecked()

        axis1_title = self.comboAxis1.currentText()
        axis2_title = self.comboAxis2.currentText()
        self.comboAxis3.currentText()

        if True:
            self.ax2.clear()
            for name in self.scatter_data.keys():
                # print("name", name, "len(group_hash[name]['x_val'])", len(group_hash[name]['x_val']), group_hash[name]['symbol'])
                group = self.scatter_data[name]
                if len(group["x_val"]) > 0:
                    self.scatter_result[name] = self.ax2.scatter(
                        group["x_val"],
                        group["y_val"],
                        s=group["size"],
                        marker=group["symbol"],
                        color=group["color"],
                        data=group["data"],
                        picker=True,
                        pickradius=5,
                    )
                    # print("ret", ret)
                if name == "__selected__":
                    for idx, obj in enumerate(group["data"]):
                        self.ax2.annotate(obj.object_name, (group["x_val"][idx], group["y_val"][idx]))

                if show_average_shape:
                    self.ax2.scatter(
                        self.average_shape[name]["x_val"],
                        self.average_shape[name]["y_val"],
                        s=group["size"] * 3,
                        marker=group["symbol"],
                        color=group["color"],
                    )

            if show_regression:
                if self.curve_list is not None and len(self.curve_list) > 0:
                    for curve in self.curve_list:
                        if curve is None:
                            continue
                        self.ax2.plot(curve["size_range"], curve["curve"], label=curve["key"], color=curve["color"])
                        if show_extraplolate:
                            self.ax2.plot(
                                curve["size_range2"],
                                curve["curve2"],
                                label=curve["key"],
                                color=curve["color"],
                                linestyle="dashed",
                            )
                        degree = len(curve["model"]) - 1
                        model_text = "Y="
                        # superscript_list = ["⁰","¹","²","³","⁴","⁵","⁶","⁷","⁸","⁹"]
                        for i in range(degree + 1):
                            coeff = round(curve["model"][i] * 1000) / 1000
                            if coeff == 0.0:
                                continue
                            model_text += str(coeff)

                            if degree != i:
                                model_text += "X"
                                model_text += "^" + str(degree - i) if degree - i > 1 else ""
                                # model_text += str(superscript_list[degree-i]) if degree-i > 1 else ""
                            if i < degree:
                                model_text += " + "
                        r_squared_text = "R^2=" + str(round(curve["r_squared"] * 1000) / 1000)

                        # self.ax2.annotate(str(curve['model'])+" "+str(curve['r_squared']), (curve['size_range'][50], curve['curve'][50]))
                        if show_annotation:
                            annotation1 = self.ax2.annotate(
                                rf"${model_text}$",
                                (curve["size_range"][10], curve["curve"][10]),
                                fontname="Times New Roman",
                            )
                            annotation2 = self.ax2.annotate(
                                rf"${r_squared_text}$",
                                (curve["size_range"][90], curve["curve"][90]),
                                fontname="Times New Roman",
                            )
                            annotation1.set_bbox(
                                {"boxstyle": "round", "facecolor": "white", "edgecolor": "none", "alpha": 0.7}
                            )
                            annotation2.set_bbox(
                                {"boxstyle": "round", "facecolor": "white", "edgecolor": "none", "alpha": 0.7}
                            )

                # self.ax2.plot(size_range, group_a_curve, label='Group A')
            # print("show_legend:", show_legend)
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    # print("key", key)
                    if key[0] == "_" or key == "":
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                scatter_legend = self.ax2.legend(values, keys, loc="upper right", bbox_to_anchor=(1.05, 1))
                self.ax2.add_artist(scatter_legend)
                bbox = scatter_legend.get_window_extent()
                # Convert to axis coordinates
                bbox.transformed(self.ax2.transAxes.inverted())
                # Calculate the height of first legend in axis coordinates

                if show_regression and self.regression_variable_index != self.scatter_variable_index:
                    values = []
                    keys = []
                    for curve in self.curve_list:
                        # print("curve", curve)
                        if curve:
                            keys.append(curve["key"])
                            values.append(curve)
                    regression_legend = self.ax2.legend(values, keys, loc="lower right", bbox_to_anchor=(1.05, 0))
                    self.ax2.add_artist(regression_legend)

            # print("show axis label:", show_axis_label)
            if show_axis_label:
                # print("show axis label true")
                # Add variance explained to axis titles if enabled and analysis is PCA
                if show_variance and self.analysis_method == "PCA":
                    # Get axis indices from combo boxes
                    axis1_idx = self.comboAxis1.currentIndex()
                    axis2_idx = self.comboAxis2.currentIndex()

                    # Try to get eigenvalues from analysis_result or from stored values
                    var_explained = None
                    if hasattr(self, "analysis_result") and hasattr(self.analysis_result, "eigen_value_percentages"):
                        var_explained = self.analysis_result.eigen_value_percentages
                    elif hasattr(self, "eigen_value_percentages"):
                        var_explained = self.eigen_value_percentages

                    if var_explained:
                        try:
                            # Axis1: index 0 is CSize, so PC1 is at index 1, PC2 at index 2, etc.
                            # So we need to subtract 1 to get the PC number (0-based)
                            if axis1_idx > 0:  # Skip if CSize is selected (index 0)
                                pc_idx_1 = axis1_idx - 1
                                if pc_idx_1 >= 0 and pc_idx_1 < len(var_explained):
                                    axis1_title += f" ({var_explained[pc_idx_1] * 100:.1f}%)"

                            # Axis2: PC1 is at index 0, PC2 at index 1, etc.
                            # So the index directly corresponds to the PC number (0-based)
                            if axis2_idx >= 0 and axis2_idx < len(var_explained):
                                axis2_title += f" ({var_explained[axis2_idx] * 100:.1f}%)"
                        except (IndexError, TypeError, ValueError) as e:
                            logger.debug(f"Could not add variance explained to axis labels: {e}")
                            pass  # Silently continue if there's any issue
                self.ax2.set_xlabel(axis1_title)
                # print("ret_x", ret_x)

                self.ax2.set_ylabel(axis2_title)
                # print("ret_y", ret_y)

            # if self.vertical_line_xval is not None:
            # self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)

            if show_convex_hull:
                # print("showing convex hull")
                for key_name in self.scatter_data.keys():
                    if "hull" in self.scatter_data[key_name].keys():
                        hull = self.scatter_data[key_name]["hull"]
                        for simplex in hull.simplices:
                            self.ax2.plot(
                                self.scatter_data[key_name]["points"][simplex, 0],
                                self.scatter_data[key_name]["points"][simplex, 1],
                                color=self.scatter_data[key_name]["color"],
                            )

                        hull_vertices_x = self.scatter_data[key_name]["points"][hull.vertices, 0]
                        hull_vertices_y = self.scatter_data[key_name]["points"][hull.vertices, 1]
                        hull_vertices_x = np.append(hull_vertices_x, hull_vertices_x[0])
                        hull_vertices_y = np.append(hull_vertices_y, hull_vertices_y[0])
                        self.ax2.fill(
                            hull_vertices_x, hull_vertices_y, color=self.scatter_data[key_name]["color"], alpha=0.5
                        )

            if show_confidence_ellipse:
                for key_name in self.scatter_data.keys():
                    if "ellipse" in self.scatter_data[key_name].keys():
                        width, height, angle = self.scatter_data[key_name]["ellipse"]
                        ellipse = matplotlib.patches.Ellipse(
                            xy=(self.average_shape[key_name]["x_val"], self.average_shape[key_name]["y_val"]),
                            width=width,
                            height=height,
                            angle=angle,
                            color=self.scatter_data[key_name]["color"],
                            lw=2,
                            alpha=0.3,
                            fill=True,
                        )
                        self.ax2.add_patch(ellipse)

            # self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()

            """ overlay shapes """
            # shape grid
            show_shape_grid = self.cbxShapeGrid.isChecked()
            # get widget position
            # print("fig_pos", fig_pos)
            if show_shape_grid:
                for keyname in self.shape_grid.keys():
                    shape = self.raw_chart_coords_to_shape(
                        self.shape_grid[keyname]["x_val"], self.shape_grid[keyname]["y_val"]
                    )
                    obj = self.shape_to_object(shape)

                    view = self.shape_grid[keyname]["view"]
                    view.show()
                    view.set_object(obj)
                    view.apply_rotation(self.rotation_matrix)
                    view.set_shape_preference(self.sgpWidget.get_preference())
                self.reposition_shape_grid()

    def reposition_shape_grid(self):
        # check if self has fig2
        if self.fig2 is None:
            return

        pos_x = self.fig2.canvas.mapToGlobal(QPoint(0, 0)).x()
        pos_y = self.fig2.canvas.mapToGlobal(QPoint(0, 0)).y()
        # print("pos_x", pos_x, "pos_y", pos_y)
        for keyname in self.shape_grid.keys():
            view = self.shape_grid[keyname]["view"]
            if view:
                # print("keyname", keyname, "x_val", self.shape_grid[keyname]['x_val'], "y_val", self.shape_grid[keyname]['y_val'])
                transform = self.ax2.transData
                display_coords = transform.transform(
                    (self.shape_grid[keyname]["x_val"], self.shape_grid[keyname]["y_val"])
                )
                x_pixel, y_pixel = display_coords
                if sys.platform == "darwin":
                    x_pixel = x_pixel / 2
                    y_pixel = y_pixel / 2
                # print("display_coords", display_coords, "x_pixel", x_pixel, "y_pixel", y_pixel)
                fig_height = self.fig2.canvas.height()
                fig_width = self.fig2.canvas.width()
                view_height = int(fig_height / 4)
                view_width = int(fig_width / 4)
                x_pixel = int(x_pixel + pos_x)
                y_pixel = int(fig_height - y_pixel + pos_y)
                self.shape_grid[keyname]["x_pos"] = x_pixel
                self.shape_grid[keyname]["y_pos"] = y_pixel
                w, h = view.width(), view.height()
                # print("view size", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)
                w, h = 120, 90
                w = max(w, view_width)
                h = max(h, view_height)
                # print("view size 2  ", w, h, "view pos", x_pixel, y_pixel, "fig_size", fig_width, fig_height)

                view.setGeometry(
                    self.shape_grid[keyname]["x_pos"] - int(w / 2), self.shape_grid[keyname]["y_pos"] - int(h / 2), w, h
                )

    def on_hover_enter(self, event):
        return
        if event.inaxes == self.ax2:  # Check if mouse is over the axes
            self.fig2.canvas.setCursor(QCursor(Qt.CrossCursor))

    def on_hover_leave(self, event):
        return
        self.fig2.canvas.setCursor(QCursor(Qt.ArrowCursor))

    def on_canvas_move(self, evt):
        if evt.xdata is None or evt.ydata is None or self.mode == MODE_AVERAGE:
            return

        x_val = evt.xdata
        y_val = evt.ydata
        if self.comboRegressionBy.currentText() == "By group":
            if x_val > self.data_range["x_max"]:
                x_val = self.data_range["x_max"]
            if x_val < self.data_range["x_min"]:
                x_val = self.data_range["x_min"]
            if y_val > self.data_range["y_max"]:
                y_val = self.data_range["y_max"]
            if y_val < self.data_range["y_min"]:
                y_val = self.data_range["y_min"]
        else:
            if x_val > max(self.regression_data["x_val"]):
                x_val = max(self.regression_data["x_val"])
            if x_val < min(self.regression_data["x_val"]):
                x_val = min(self.regression_data["x_val"])
            if y_val > max(self.regression_data["y_val"]):
                y_val = max(self.regression_data["y_val"])
            if y_val < min(self.regression_data["y_val"]):
                y_val = min(self.regression_data["y_val"])

        if self.axvline is not None:
            # print("remove axvline",self.axvline)
            safe_remove_artist(self.axvline, self.ax2)
            self.axvline = None

        # print(evt.button, evt.xdata, evt.ydata)
        if self.mode in [MODE_REGRESSION]:
            if evt.button is None:
                self.vertical_line_xval = x_val
                self.vertical_line_style = "dashed"
                self.axvline = self.ax2.axvline(
                    x=self.vertical_line_xval, color="gray", linestyle=self.vertical_line_style
                )
                self.fig2.canvas.draw()
                # self.ax2.axvline(x=evt.xdata, color='gray', linestyle='dashed')
                # self.show_analysis_result()
            elif evt.button == 1:
                self.vertical_line_xval = x_val
                self.vertical_line_style = "solid"
                # print("2-0:",datetime.datetime.now())
                # self.show_analysis_result()
                if self.axvline is not None:
                    safe_remove_artist(self.axvline, self.ax2)
                    self.axvline = None
                self.axvline = self.ax2.axvline(
                    x=self.vertical_line_xval, color="gray", linestyle=self.vertical_line_style
                )
                self.fig2.canvas.draw()
                # print("2-1:",datetime.datetime.now())
                # self.ax2.axvline(x=evt.xdata, color='gray', linestyle='solid')
                # print("evt:", evt)
                # self.vertical_line_xval = evt.xdata
                # self.ax2.axvline(x=evt.xdata, color='gray', linestyle='solid')
                self.shape_regression(evt)
        elif self.mode in [MODE_COMPARISON, MODE_EXPLORATION, MODE_COMPARISON2]:
            if evt.button == 1 and self.is_picking_shape:
                self.pick_shape(x_val, y_val)
                self.fig2.canvas.draw()
        return

    def on_canvas_button_release(self, evt):
        if self.mode == MODE_AVERAGE:
            return

        if evt.button == 1:
            if self.is_picking_shape:
                # set cursor to crosshair
                if self.mode == MODE_COMPARISON:
                    self.plot_widget2.setCursor(QCursor(Qt.ArrowCursor))
                    self.is_picking_shape = False
                    self.pick_idx = -1
                elif self.mode == MODE_EXPLORATION:
                    self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
                    self.is_picking_shape = True
                    self.pick_idx = 0
            else:
                self.vertical_line_xval = evt.xdata
                self.vertical_line_style = "dashed"
        return
        # print("button_release", evt)
        if self.onpick_happened:
            self.onpick_happened = False
            return
        self.canvas_up_xy = (evt.x, evt.y)
        if self.canvas_down_xy == self.canvas_up_xy:
            self.tableView1.selectionModel().clearSelection()

    def shape_to_object(self, shape):
        obj = MdObject()
        obj.dataset = self.analysis.dataset
        # print("ds 1:", obj.dataset)
        # ds = MdDataset()
        # print("ds id", self.analysis.dataset_id)
        ds = MdDataset.get(MdDataset.id == self.analysis.dataset_id)
        # print("ds 2:", ds)
        obj.dataset = ds
        # print("dataset:", obj.dataset, obj.dataset_id, obj.dataset.polygon_list, obj.dataset.edge_list)
        obj.landmark_list = []
        for i in range(0, len(shape), self.analysis.dimension):
            landmark = shape[i : i + self.analysis.dimension]
            obj.landmark_list.append(landmark)
        obj.pack_landmark()
        obj.unpack_landmark()
        return obj

    def show_shape(self, shape, idx):
        obj = self.shape_to_object(shape)

        shape_view = self.shape_view_list[idx]

        if self.mode == MODE_COMPARISON2:
            shape_view = self.shape_view_list[0]
            shape_view.show_average = False
            shape_view.show_polygon = True
            shape_view.show_wireframe = True
            shape_view.dataset = obj.dataset
            shape_view.polygon_list = obj.dataset.get_polygon_list()
            shape_view.edge_list = obj.dataset.get_edge_list()
            # print("edge_list", obj.dataset.edge_list, "polygon_list:", obj.dataset.polygon_list, "show average:", shape_view.show_average, "show polygon:", shape_view.show_polygon, "show wireframe:", shape_view.show_wireframe)

            if idx == 0:
                shape_view.set_source_shape(obj)
                shape_view.generate_reference_shape()
                shape_view.set_source_shape_preference(self.shape_preference_list[idx].get_preference())
            elif idx == 1:
                shape_view.set_target_shape(obj)
                shape_view.generate_reference_shape()
                shape_view.set_target_shape_preference(self.shape_preference_list[idx].get_preference())
        else:
            shape_view.set_object(obj)
            shape_view.set_shape_preference(self.shape_preference_list[idx].get_preference())

        shape_view.apply_rotation(self.rotation_matrix)
        if self.analysis.dimension == 3:
            shape_view.pan_x = self.shape_view_pan_x
            shape_view.pan_y = self.shape_view_pan_y
            shape_view.dolly = self.shape_view_dolly
        shape_view.update()

    def on_canvas_button_press(self, evt):
        # print("button_press", evt)

        if self.mode == MODE_AVERAGE:
            return

        x_val = evt.xdata
        y_val = evt.ydata
        if x_val is None or y_val is None:
            return
        if x_val > self.data_range["x_max"]:
            x_val = self.data_range["x_max"]
        if x_val < self.data_range["x_min"]:
            x_val = self.data_range["x_min"]
        if y_val > self.data_range["y_max"]:
            y_val = self.data_range["y_max"]
        if y_val < self.data_range["y_min"]:
            y_val = self.data_range["y_min"]

        if self.mode in [MODE_REGRESSION]:
            if evt.button == 1:
                self.vertical_line_xval = x_val
                self.vertical_line_style = "solid"
                # print("2-0:",datetime.datetime.now())
                # self.show_analysis_result()
                if self.axvline is not None:
                    safe_remove_artist(self.axvline, self.ax2)
                    self.axvline = None
                if evt.xdata is not None:
                    # print("xdata", evt.xdata)
                    self.axvline = self.ax2.axvline(
                        x=self.vertical_line_xval, color="gray", linestyle=self.vertical_line_style
                    )
                    self.fig2.canvas.draw()
                    self.shape_regression(evt)
        elif self.mode in [MODE_COMPARISON, MODE_EXPLORATION, MODE_COMPARISON2]:
            if evt.button == 1 and self.is_picking_shape:
                self.plot_widget2.setCursor(QCursor(Qt.CrossCursor))
                self.pick_shape(x_val, y_val)
                self.fig2.canvas.draw()

        return
        self.canvas_down_xy = (evt.x, evt.y)
        # self.tableView.selectionModel().clearSelection()

    def pick_shape(self, x_val, y_val):
        if self.pick_idx == -1:
            return

        # Set wait cursor while processing shape display
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # print("pick_shape", evt.xdata, evt.ydata, self.pick_idx)
            scatter_data_len = len(self.scatter_data.keys())
            marker_list = self.marker_list
            while scatter_data_len + 2 > len(marker_list):
                marker_list += self.marker_list
            # print("scatter_data_len", scatter_data_len, self.marker_list, marker_list)
            symbol_candidate = marker_list[scatter_data_len : scatter_data_len + 2]
            color_list = self.color_list
            while scatter_data_len + 2 > len(color_list):
                color_list += self.color_list
            color_candidate = color_list[scatter_data_len : scatter_data_len + 2]
            # print("pick_shape", evt.xdata, evt.ydata, self.pick_idx, scatter_data_len, symbol_candidate, color_candidate)
            shape = self.custom_shape_hash[self.pick_idx]

            if shape["point"] is not None:
                try:
                    shape["point"].remove()
                except NotImplementedError:
                    # For scatter plots, we need to remove from the axes collection
                    if shape["point"] in self.ax2.collections:
                        self.ax2.collections.remove(shape["point"])
                shape["point"] = None
            if shape["label"] is not None:
                try:
                    shape["label"].remove()
                except NotImplementedError:
                    # For annotations, try removing from axes
                    if shape["label"] in self.ax2.texts:
                        self.ax2.texts.remove(shape["label"])
                shape["label"] = None

            """ need to improve speed by using offset, not creating new annotation every time """
            # print("shape['name']", shape['name'], x_val, y_val, self.pick_idx, symbol_candidate, color_candidate)
            shape["coords"] = [x_val, y_val]
            shape["point"] = self.ax2.scatter(
                [x_val], [y_val], s=150, marker=symbol_candidate[self.pick_idx], color=color_candidate[self.pick_idx]
            )
            # print("shape['name']", shape['name'])
            if shape["name"] != "":
                shape["label"] = self.ax2.annotate(
                    shape["name"],
                    (x_val, y_val),
                    xycoords="data",
                    textcoords="offset pixels",
                    xytext=(15, 15),
                    ha="center",
                    fontsize=12,
                    color="black",
                )
            # print("point:", self.custom_shape_hash[self.pick_idx]['point'])
            # self.ax2.scatter(self.average_shape[name]['x_val'], self.average_shape[name]['y_val'], s=150, marker=group['symbol'], color=group['color'])

            axis1 = self.comboAxis1.currentData()
            axis2 = self.comboAxis2.currentData()
            flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
            flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
            shape_to_visualize = np.zeros((1, len(self.analysis_result_list[0])))
            x_value = flip_axis1 * x_val
            y_value = flip_axis2 * y_val
            if axis1 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis1] = x_value
            if axis2 != CENTROID_SIZE_VALUE:
                shape_to_visualize[0][axis2] = y_value
            unrotated_shape = self.unrotate_shape(shape_to_visualize)
            # print("0-4:",datetime.datetime.now())
            self.show_shape(unrotated_shape[0], self.pick_idx)

            # self.axvline = self.ax2.axvline(x=self.vertical_line_xval, color='gray', linestyle=self.vertical_line_style)
        finally:
            # Restore normal cursor after shape display
            QApplication.restoreOverrideCursor()

    def raw_chart_coords_to_shape(self, x_val, y_val):
        axis1 = self.comboAxis1.currentData()
        axis2 = self.comboAxis2.currentData()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0

        x_value = flip_axis1 * x_val
        y_value = flip_axis2 * y_val

        shape_to_visualize = np.zeros((1, len(self.analysis_result_list[0])))
        if axis1 != CENTROID_SIZE_VALUE:
            shape_to_visualize[0][axis1] = x_value
        shape_to_visualize[0][axis2] = y_value
        unrotated_shape = self.unrotate_shape(shape_to_visualize)

        return unrotated_shape[0]

    def on_pick(self, evt):
        # print("onpick", evt)
        return
        self.onpick_happened = True
        # print("evt", evt, evt.ind, evt.artist )
        selected_object_id_list = []
        for key_name in self.scatter_data.keys():
            if evt.artist == self.scatter_result[key_name]:
                # print("key_name", key_name)
                for idx in evt.ind:
                    obj = self.scatter_data[key_name]["data"][idx]
                    # print("obj", obj)
                    selected_object_id_list.append(obj["id"])
                    # self.ds_ops.select_object(obj.id)

        # print("selected_object_id_list", selected_object_id_list)
        # select rows in tableView
        # self.tableView.clearSelection()
        # selectionModel = self.tableView.selectionModel()

        # print("selected_object_id_list", selected_object_id_list)
        self.selection_changed_off = True
        for id in selected_object_id_list:
            # item = self.object_model.findItems(str(id), Qt.MatchExactly, 0)
            item = self.object_hash[id]
            self.tableView1.selectionModel().select(item.index(), QItemSelectionModel.Rows | QItemSelectionModel.Select)
        self.selection_changed_off = False
        self.on_object_selection_changed([], [])

        # for row in range(self.object_model.rowCount()):
        #    if int(self.object_model.item(row,0).text()) in selected_object_id_list:
        #        self.tableView.selectionModel().select(self.object_model.item(row,0).index(),QItemSelectionModel.Rows | QItemSelectionModel.Select)

    def unrotate_shape(self, shape):
        if self.analysis_method == "PCA":
            rotation_matrix = json.loads(self.analysis.pca_rotation_matrix_json)
        elif self.analysis_method == "CVA":
            rotation_matrix = json.loads(self.analysis.cva_rotation_matrix_json)
        # rotation_matrix = json.loads(self.analysis.rotation_matrix_json)

        inverted_matrix = np.linalg.inv(rotation_matrix)
        # print("inverted_matrix", inverted_matrix)

        unrotated_shape = np.dot(shape, inverted_matrix)

        all_shapes = np.array(json.loads(self.analysis.superimposed_landmark_json))
        # get average of all_shapes
        average_shape = np.mean(all_shapes, axis=0)
        average_shape = average_shape.reshape(1, -1)

        # For PCA/CVA space (144D) to original 3D space (216D) conversion
        if average_shape.shape[1] != unrotated_shape.shape[1]:
            # Instead of complex transformation, use the picked point from original space
            # The 'shape' parameter should correspond to original landmark data
            final_shape = average_shape  # For now, just return average shape
            print(
                f"Note: Using average shape due to dimension mismatch ({unrotated_shape.shape[1]}D vs {average_shape.shape[1]}D)"
            )
        else:
            final_shape = average_shape + unrotated_shape
        # print("final shape", final_shape.shape,final_shape)

        return final_shape
