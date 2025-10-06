"""
ShapePreference - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
)
from PyQt5.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QWidget,
)

# GLUT import conditional - causes crashes on Windows builds
GLUT_AVAILABLE = False
GLUT_INITIALIZED = False
glut = None

try:
    from OpenGL import GLUT as glut

    GLUT_AVAILABLE = True
except ImportError as e:
    GLUT_AVAILABLE = False
    print(f"Warning: GLUT not available ({e}), using fallback rendering")
    glut = None

# Initialize GLUT once at module level if available
if GLUT_AVAILABLE and glut:
    try:
        glut.glutInit(sys.argv)
        GLUT_INITIALIZED = True
    except Exception as e:
        print(f"Warning: Failed to initialize GLUT ({e}), using fallback rendering")
        GLUT_AVAILABLE = False
        GLUT_INITIALIZED = False


import MdUtils as mu

logger = logging.getLogger(__name__)

MODE = {}
MODE["NONE"] = 0
MODE["PAN"] = 12
MODE["EDIT_LANDMARK"] = 1
MODE["WIREFRAME"] = 2
MODE["READY_MOVE_LANDMARK"] = 3
MODE["MOVE_LANDMARK"] = 4
MODE["PRE_WIRE_FROM"] = 5
MODE["CALIBRATION"] = 6
MODE["VIEW"] = 7


MODE_EXPLORATION = 0
MODE_REGRESSION = 1
MODE_GROWTH_TRAJECTORY = 2
MODE_AVERAGE = 3
MODE_COMPARISON = 4
MODE_COMPARISON2 = 5
# MODE_GRID = 6

BASE_LANDMARK_RADIUS = 2
DISTANCE_THRESHOLD = BASE_LANDMARK_RADIUS * 3
CENTROID_SIZE_VALUE = 99
CENTROID_SIZE_TEXT = "CSize"

# glview modes
OBJECT_MODE = 1
DATASET_MODE = 2
VIEW_MODE = 1
PAN_MODE = 2
ROTATE_MODE = 3
ZOOM_MODE = 4
LANDMARK_MODE = 1
WIREFRAME_MODE = 2
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
COLOR["SELECTED_SHAPE"] = COLOR["RED"]
COLOR["SELECTED_TEXT"] = COLOR["RED"]
COLOR["SELECTED_LANDMARK"] = COLOR["RED"]
COLOR["WIREFRAME"] = COLOR["YELLOW"]
COLOR["SELECTED_EDGE"] = COLOR["RED"]
COLOR["BACKGROUND"] = COLOR["DARK_GRAY"]

ICON = {}
ICON["landmark"] = mu.resource_path("icons/M2Landmark_2.png")
ICON["landmark_hover"] = mu.resource_path("icons/M2Landmark_2_hover.png")
ICON["landmark_down"] = mu.resource_path("icons/M2Landmark_2_down.png")
ICON["landmark_disabled"] = mu.resource_path("icons/M2Landmark_2_disabled.png")
ICON["wireframe"] = mu.resource_path("icons/M2Wireframe_2.png")
ICON["wireframe_hover"] = mu.resource_path("icons/M2Wireframe_2_hover.png")
ICON["wireframe_down"] = mu.resource_path("icons/M2Wireframe_2_down.png")
ICON["calibration"] = mu.resource_path("icons/M2Calibration_2.png")
ICON["calibration_hover"] = mu.resource_path("icons/M2Calibration_2_hover.png")
ICON["calibration_down"] = mu.resource_path("icons/M2Calibration_2_down.png")
ICON["calibration_disabled"] = mu.resource_path("icons/M2Calibration_2_disabled.png")

NEWLINE = "\n"


class ShapePreference(QWidget):
    shape_preference_changed = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.visible = True
        self.show_landmark = True
        self.show_wireframe = True
        self.show_polygon = True
        self.transparency = 0
        self.opacity = 1 - self.transparency
        self.ignore_change = False
        self.index = -1
        self.edge_color = "red"
        self.landmark_color = "red"
        self.polygon_color = "red"
        self.name = ""

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.lblTitle = QLabel("Name")
        self.edtTitle = QLineEdit()
        self.cbxShow = QCheckBox("Show")
        self.cbxShow.setChecked(self.visible)
        self.cbxShowLandmark = QCheckBox("")
        self.cbxShowLandmark.setChecked(self.show_landmark)
        self.cbxShowWireframe = QCheckBox("")
        self.cbxShowWireframe.setChecked(self.show_wireframe)
        self.cbxShowPolygon = QCheckBox("")
        self.cbxShowPolygon.setChecked(self.show_polygon)
        self.sliderTransparency = QSlider(Qt.Horizontal)
        self.sliderTransparency.setMinimum(0)
        self.sliderTransparency.setMaximum(100)
        self.sliderTransparency.setValue(0)

        self.btnLMColor = QPushButton("LM")
        self.btnLMColor.setMinimumSize(20, 20)
        self.btnLMColor.setStyleSheet("background-color: red")
        self.btnLMColor.setToolTip("red")
        self.btnLMColor.setCursor(Qt.PointingHandCursor)
        # self.btnLMColor.mousePressEvent = lambda event, type='LM': self.on_btnColor_clicked(event, 'LM')
        self.btnLMColor.clicked.connect(self.on_btnLMColor_clicked)

        self.btnEdgeColor = QPushButton("Edge")
        self.btnEdgeColor.setMinimumSize(20, 20)
        self.btnEdgeColor.setStyleSheet("background-color: red")
        self.btnEdgeColor.setToolTip("red")
        self.btnEdgeColor.setCursor(Qt.PointingHandCursor)
        self.btnEdgeColor.clicked.connect(self.on_btnEdgeColor_clicked)

        self.btnFaceColor = QPushButton("Face")
        self.btnFaceColor.setMinimumSize(20, 20)
        self.btnFaceColor.setStyleSheet("background-color: red")
        self.btnFaceColor.setToolTip("red")
        self.btnFaceColor.setCursor(Qt.PointingHandCursor)
        self.btnFaceColor.clicked.connect(self.on_btnFaceColor_clicked)

        self.layout.addWidget(self.lblTitle)
        self.layout.addWidget(self.edtTitle)
        self.layout.addWidget(self.cbxShow)
        self.layout.addWidget(self.cbxShowLandmark)
        self.layout.addWidget(self.btnLMColor)
        self.layout.addWidget(self.cbxShowWireframe)
        self.layout.addWidget(self.btnEdgeColor)
        self.layout.addWidget(self.cbxShowPolygon)
        self.layout.addWidget(self.btnFaceColor)
        self.layout.addWidget(self.sliderTransparency)

        self.cbxShow.stateChanged.connect(self.cbxShow_stateChanged)
        self.cbxShowLandmark.stateChanged.connect(self.cbxShowLandmark_stateChanged)
        self.cbxShowWireframe.stateChanged.connect(self.cbxShowWireframe_stateChanged)
        self.cbxShowPolygon.stateChanged.connect(self.cbxShowPolygon_stateChanged)
        self.edtTitle.textChanged.connect(self.edtTitle_textChanged)
        self.sliderTransparency.valueChanged.connect(self.sliderTransparency_valueChanged)

    def hide_title(self):
        self.lblTitle.hide()

    def hide_name(self):
        self.edtTitle.hide()

    def hide_cbxShow(self):
        self.cbxShow.hide()

    def on_btnLMColor_clicked(self, event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnLMColor.toolTip()))
        if color is not None:
            self.btnLMColor.setStyleSheet("background-color: " + color.name())
            self.btnLMColor.setToolTip(color.name())
            self.landmark_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def on_btnEdgeColor_clicked(self, event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnEdgeColor.toolTip()))
        if color is not None:
            self.btnEdgeColor.setStyleSheet("background-color: " + color.name())
            self.btnEdgeColor.setToolTip(color.name())
            self.edge_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def on_btnFaceColor_clicked(self, event):
        dialog = QColorDialog()
        color = dialog.getColor(initial=QColor(self.btnFaceColor.toolTip()))
        if color is not None:
            self.btnFaceColor.setStyleSheet("background-color: " + color.name())
            self.btnFaceColor.setToolTip(color.name())
            self.polygon_color = color.name()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def edtTitle_textChanged(self, text):
        self.name = text
        if self.ignore_change is False:
            self.emit_changed_signal()

    def emit_changed_signal(self):
        pref = {
            "name": self.name,
            "index": self.index,
            "visible": self.visible,
            "show_landmark": self.show_landmark,
            "show_wireframe": self.show_wireframe,
            "show_polygon": self.show_polygon,
            "opacity": self.opacity,
            "landmark_color": self.landmark_color,
            "edge_color": self.edge_color,
            "polygon_color": self.polygon_color,
        }
        self.shape_preference_changed.emit(pref)

    def get_preference(self):
        pref = {
            "name": self.name,
            "index": self.index,
            "visible": self.visible,
            "show_landmark": self.show_landmark,
            "show_wireframe": self.show_wireframe,
            "show_polygon": self.show_polygon,
            "opacity": self.opacity,
            "landmark_color": self.landmark_color,
            "edge_color": self.edge_color,
            "polygon_color": self.polygon_color,
        }
        return pref

    def set_color(self, color):
        self.btnLMColor.setStyleSheet("background-color: " + color)
        self.landmark_color = color
        self.btnEdgeColor.setStyleSheet("background-color: " + color)
        self.edge_color = color
        self.btnFaceColor.setStyleSheet("background-color: " + color)
        self.polygon_color = color

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.transparency = 1 - opacity
        self.sliderTransparency.setValue(int(self.transparency * 100))

    def set_title(self, title):
        self.lblTitle.setText(title)

    def set_name(self, name):
        self.name = name
        self.ignore_change = True
        self.edtTitle.setText(name)
        self.ignore_change = False

    def set_index(self, index):
        self.index = index

    def btnColor_clicked(self):
        pass

    def cbxShow_stateChanged(self, int):
        self.visible = self.cbxShow.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def cbxShowLandmark_stateChanged(self, int):
        self.show_landmark = self.cbxShowLandmark.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def cbxShowWireframe_stateChanged(self, int):
        self.show_wireframe = self.cbxShowWireframe.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def cbxShowPolygon_stateChanged(self, int):
        self.show_polygon = self.cbxShowPolygon.isChecked()
        if self.ignore_change is False:
            self.emit_changed_signal()

    def sliderTransparency_valueChanged(self, int):
        self.transparency = self.sliderTransparency.value() / 100.0
        self.opacity = 1 - self.transparency
        if self.ignore_change is False:
            self.emit_changed_signal()
