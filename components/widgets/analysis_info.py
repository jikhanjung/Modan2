"""
AnalysisInfoWidget - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import (
    QTranslator,
)
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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
import json
import os

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


class AnalysisInfoWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        # print("color_list", self.color_list)
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        # print("color_list", self.color_list)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.lblAnalysisName = QLabel(self.tr("Analysis Name"))
        self.edtAnalysisName = QLineEdit()
        self.lblSuperimposition = QLabel(self.tr("Superimposition"))
        self.edtSuperimposition = QLineEdit()
        self.edtSuperimposition.setEnabled(False)
        self.ignore_change = False
        self.PcaView = QWidget()
        self.pca_layout = QGridLayout()
        self.PcaView.setLayout(self.pca_layout)
        self.CvaView = QWidget()
        self.cva_layout = QGridLayout()
        self.CvaView.setLayout(self.cva_layout)
        self.ManovaView = QWidget()
        self.manova_layout = QGridLayout()
        self.ManovaView.setLayout(self.manova_layout)
        self.analysis_tab = QTabWidget()
        self.analysis_tab.addTab(self.PcaView, "PCA")
        self.analysis_tab.addTab(self.CvaView, "CVA")
        self.analysis_tab.addTab(self.ManovaView, "MANOVA")
        self.analysis_tab.currentChanged.connect(self.on_tab_changed)

        """ PCA 3D plot """
        self.lblPcaGroupBy = QLabel(self.tr("Grouping variable"))
        self.comboPcaGroupBy = QComboBox()
        self.comboPcaGroupBy.setEnabled(False)
        self.comboPcaGroupBy.currentIndexChanged.connect(self.comboPcaGroupBy_changed)
        self.pca_plot_widget3 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.pca_fig3 = self.pca_plot_widget3.figure
        self.pca_ax3 = self.pca_fig3.add_subplot(projection="3d")
        self.pca_toolbar3 = NavigationToolbar(self.pca_plot_widget3, self)
        i = 0
        self.pca_layout.addWidget(self.pca_toolbar3, i, 0)
        self.pca_layout.addWidget(self.lblPcaGroupBy, i, 1)
        self.pca_layout.addWidget(self.comboPcaGroupBy, i, 2)
        i += 1
        self.pca_layout.addWidget(self.pca_plot_widget3, i, 0, 1, 2)
        self.pca_layout.setRowStretch(i, 1)

        """ CVA 3D plot """
        self.lblCvaGroupBy = QLabel("Grouping variable")
        self.comboCvaGroupBy = QComboBox()
        self.comboCvaGroupBy.setEnabled(False)
        self.comboCvaGroupBy.currentIndexChanged.connect(self.comboCvaGroupBy_changed)
        self.cva_plot_widget3 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.cva_fig3 = self.cva_plot_widget3.figure
        self.cva_ax3 = self.cva_fig3.add_subplot(projection="3d")
        self.cva_toolbar3 = NavigationToolbar(self.cva_plot_widget3, self)
        i = 0
        self.cva_layout.addWidget(self.cva_toolbar3, i, 0)
        self.cva_layout.addWidget(self.lblCvaGroupBy, i, 1)
        self.cva_layout.addWidget(self.comboCvaGroupBy, i, 2)
        i += 1
        self.cva_layout.addWidget(self.cva_plot_widget3, i, 0, 1, 3)
        self.cva_layout.setRowStretch(i, 1)

        """ MANOVA info """
        self.lblManovaGroupBy = QLabel("Grouping variable")
        self.comboManovaGroupBy = QComboBox()
        self.comboManovaGroupBy.setEnabled(False)
        """ manova output table """
        self.tabManovaResult = QTableWidget()
        self.comboManovaGroupBy.currentIndexChanged.connect(self.comboManovaGroupBy_changed)
        i = 0
        self.manova_layout.addWidget(self.lblManovaGroupBy, i, 0)
        self.manova_layout.addWidget(self.comboManovaGroupBy, i, 1)
        i += 1
        self.manova_layout.addWidget(self.tabManovaResult, i, 0, 1, 2)

        i = 0
        self.layout.addWidget(self.lblAnalysisName, i, 0)
        self.layout.addWidget(self.edtAnalysisName, i, 1)
        i += 1
        self.layout.addWidget(self.lblSuperimposition, i, 0)
        self.layout.addWidget(self.edtSuperimposition, i, 1)
        i += 1
        self.layout.addWidget(self.analysis_tab, i, 0, 1, 2)
        self.read_settings()

    def read_settings(self):
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/" + str(i), self.marker_list[i])
        self.update_language()  # self.m_app.settings.value("Language", "en"))

    def update_language(self):
        if False:
            if self.m_app.translator is not None:
                self.m_app.removeTranslator(self.m_app.translator)
                self.m_app.translator = None

            translator = QTranslator()
            translator_path = mu.resource_path(f"translations/Modan2_{language}.qm")
            if os.path.exists(translator_path):
                translator.load(translator_path)
                self.m_app.installTranslator(translator)
                self.m_app.translator = translator

        self.lblAnalysisName.setText(self.tr("Analysis Name"))
        self.lblSuperimposition.setText(self.tr("Superimposition"))
        self.lblPcaGroupBy.setText(self.tr("Grouping variable"))

    def on_tab_changed(self, index):
        """Handle tab change event - enable buttons only for PCA tab"""
        # Enable Analysis Detail and Data Exploration buttons only for PCA tab (index 0)
        is_pca_tab = index == 0

        # Access parent's buttons (ModanMainWindow)
        if hasattr(self.parent, "btnAnalysisDetail"):
            self.parent.btnAnalysisDetail.setEnabled(is_pca_tab)
        if hasattr(self.parent, "btnDataExploration"):
            self.parent.btnDataExploration.setEnabled(is_pca_tab)

    def comboPcaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def comboCvaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def comboManovaGroupBy_changed(self):
        if self.ignore_change:
            return
        self.show_analysis_result()

    def set_analysis(self, analysis):
        self.ignore_change = True
        self.analysis = analysis
        self.edtAnalysisName.setText(analysis.analysis_name)
        self.edtSuperimposition.setText(analysis.superimposition_method)
        for combo in [self.comboPcaGroupBy, self.comboCvaGroupBy, self.comboManovaGroupBy]:
            combo.clear()

            valid_property_index_list = analysis.dataset.get_grouping_variable_index_list()
            variablename_list = analysis.dataset.get_variablename_list()
            for idx in valid_property_index_list:
                property = variablename_list[idx]
                combo.addItem(property, idx)

        self.comboPcaGroupBy.setEnabled(True)
        self.comboCvaGroupBy.setEnabled(False)
        self.comboManovaGroupBy.setEnabled(False)

        self.comboPcaGroupBy.setCurrentIndex(0)

        if analysis.cva_group_by in analysis.dataset.get_variablename_list():
            self.comboCvaGroupBy.setCurrentText(analysis.cva_group_by)
        else:
            self.comboCvaGroupBy.setCurrentIndex(0)

        if analysis.manova_group_by in analysis.dataset.get_variablename_list():
            self.comboManovaGroupBy.setCurrentText(analysis.manova_group_by)
        else:
            self.comboManovaGroupBy.setCurrentIndex(0)
        self.ignore_change = False

        # Set tab to PCA by default
        self.analysis_tab.setCurrentIndex(0)

        # Set initial button state - enable only for PCA tab
        self.on_tab_changed(0)

    def show_analysis_result(self):
        logger = logging.getLogger(__name__)
        logger.info(f"show_analysis_result called for: {self.analysis.analysis_name}")

        # Handle legacy analysis data - if JSON is missing, show basic info
        if not self.analysis.object_info_json:
            logger.warning("No JSON data found - showing basic analysis info")
            # Show analysis name and details in a simple format
            self.edtAnalysisName.setText(self.analysis.analysis_name)
            self.edtSuperimposition.setText(self.analysis.superimposition_method or "Unknown")
            return

        # Continue with full analysis display if JSON data exists
        logger.info("Loading object_info_json")
        object_info_list = json.loads(self.analysis.object_info_json)
        for obj in object_info_list:
            if "property_list" in obj.keys():
                obj["variable_list"] = obj["property_list"]

        # Initialize result variables
        pca_analysis_result_list = None
        cva_analysis_result_list = None
        manova_result = None

        if self.analysis.pca_analysis_result_json:
            logger.info("Loading pca_analysis_result_json")
            pca_analysis_result_list = json.loads(self.analysis.pca_analysis_result_json)
            logger.info(
                f"PCA result loaded: type={type(pca_analysis_result_list)}, len={len(pca_analysis_result_list) if pca_analysis_result_list else 'None'}"
            )

        logger.info(f"CVA JSON exists: {bool(self.analysis.cva_analysis_result_json)}")
        if self.analysis.cva_analysis_result_json:
            logger.info("Loading cva_analysis_result_json")
            cva_analysis_result_list = json.loads(self.analysis.cva_analysis_result_json)
            logger.info(
                f"CVA result loaded: type={type(cva_analysis_result_list)}, len={len(cva_analysis_result_list) if cva_analysis_result_list else 'None'}"
            )
        else:
            logger.warning("CVA analysis_result_json is empty or None")

        manova_result = None
        if self.analysis.manova_analysis_result_json:
            logger.info("Loading manova_analysis_result_json")
            logger.info(f"MANOVA JSON length: {len(self.analysis.manova_analysis_result_json)}")
            logger.info(f"MANOVA JSON preview: {self.analysis.manova_analysis_result_json[:200]}...")

            try:
                manova_result_raw = json.loads(self.analysis.manova_analysis_result_json)
                logger.info(f"MANOVA result loaded, type: {type(manova_result_raw)}")

                # Check if it's already in the expected format
                if isinstance(manova_result_raw, dict):
                    logger.info(f"MANOVA result keys: {manova_result_raw.keys()}")
                    if "stat_dict" in manova_result_raw:
                        # Already has stat_dict wrapper
                        manova_result = manova_result_raw
                        logger.info("MANOVA format: Already has stat_dict wrapper")
                    elif "column_names" in manova_result_raw:
                        # This IS the stat_dict, wrap it
                        manova_result = {"stat_dict": manova_result_raw}
                        logger.info("MANOVA format: Is stat_dict, wrapping it")
                    else:
                        # Unknown format, try to use as-is
                        manova_result = manova_result_raw
                        logger.warning("MANOVA format: Unknown, using as-is")
                else:
                    manova_result = manova_result_raw
                    logger.warning(f"MANOVA result is not a dict, type: {type(manova_result_raw)}")
            except Exception as e:
                logger.error(f"Failed to parse MANOVA JSON: {e}")
                manova_result = None
        else:
            logger.warning("No MANOVA analysis_result_json")

        # Handle MANOVA results
        self.tabManovaResult.clear()
        self.tabManovaResult.setRowCount(0)

        if manova_result:
            logger.info("Processing MANOVA result for display")
            logger.debug(f"MANOVA result structure: {manova_result}")

            # Set up proper MANOVA table format
            # Columns: Statistic, Value, Num DF, Den DF, F Value, Pr>F
            column_headers = ["Statistic", "Value", "Num DF", "Den DF", "F Value", "Pr>F"]
            self.tabManovaResult.setColumnCount(len(column_headers))
            self.tabManovaResult.setHorizontalHeaderLabels(column_headers)

            # Check if MANOVA result contains multiple statistics or single values
            if "stat_dict" in manova_result and isinstance(manova_result["stat_dict"], dict):
                # New stat_dict format (matches original Modan2)
                logger.info("MANOVA: Processing stat_dict format")
                stat_dict = manova_result["stat_dict"]
                stat_dict.get("column_names", column_headers)
                logger.info(f"MANOVA stat_dict has {len(stat_dict)} items")

                for stat_name, stat_values in stat_dict.items():
                    if stat_name == "column_names":
                        continue

                    logger.info(f"Processing MANOVA stat: {stat_name} = {stat_values}")
                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)

                    # Set statistic name
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))

                    # Set values from the list
                    if isinstance(stat_values, list) and len(stat_values) >= 5:
                        self.tabManovaResult.setItem(row, 1, QTableWidgetItem(f"{stat_values[0]:.6e}"))
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(int(stat_values[1]))))
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(int(stat_values[2]))))
                        self.tabManovaResult.setItem(row, 4, QTableWidgetItem(f"{stat_values[3]:.3f}"))
                        self.tabManovaResult.setItem(row, 5, QTableWidgetItem(f"{stat_values[4]:.3f}"))
                        logger.info(f"Added MANOVA row for {stat_name}")
                    else:
                        logger.warning(f"Invalid stat values for {stat_name}: {stat_values}")

            elif "statistics" in manova_result and isinstance(manova_result["statistics"], dict):
                # Multiple statistics format
                logger.info("MANOVA: Processing multiple statistics format")
                for stat_name, stat_data in manova_result["statistics"].items():
                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)

                    # Set statistic name
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))

                    # Set values if available
                    if isinstance(stat_data, dict):
                        self.tabManovaResult.setItem(row, 1, QTableWidgetItem(str(stat_data.get("value", "N/A"))))
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(stat_data.get("num_df", "N/A"))))
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(stat_data.get("den_df", "N/A"))))
                        self.tabManovaResult.setItem(row, 4, QTableWidgetItem(str(stat_data.get("f_statistic", "N/A"))))
                        self.tabManovaResult.setItem(row, 5, QTableWidgetItem(str(stat_data.get("p_value", "N/A"))))
            else:
                # Single statistics - convert current format to table rows
                logger.info("MANOVA: Processing single statistics format")

                # Map common MANOVA statistics to display names
                stat_mapping = {
                    "wilks_lambda": "Wilks' Lambda",
                    "pillais_trace": "Pillai's Trace",
                    "hotellings_trace": "Hotelling's Trace",
                    "roys_largest_root": "Roy's Largest Root",
                    "f_statistic": "F Statistic",
                    "p_value": "P Value",
                }

                for key, value in manova_result.items():
                    if key in ["analysis_type", "degrees_of_freedom"]:
                        continue  # Skip meta information

                    row = self.tabManovaResult.rowCount()
                    self.tabManovaResult.insertRow(row)

                    # Use mapped name if available, otherwise use key
                    display_name = stat_mapping.get(key, key.replace("_", " ").title())
                    self.tabManovaResult.setItem(row, 0, QTableWidgetItem(display_name))

                    # Set the value
                    self.tabManovaResult.setItem(row, 1, QTableWidgetItem(str(value)))

                    # For degrees of freedom, try to extract if available
                    if key == "degrees_of_freedom" and isinstance(value, (list, tuple)) and len(value) >= 2:
                        self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(value[0])))  # Num DF
                        self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(value[1])))  # Den DF
                    elif "degrees_of_freedom" in manova_result and isinstance(
                        manova_result["degrees_of_freedom"], (list, tuple)
                    ):
                        df = manova_result["degrees_of_freedom"]
                        if len(df) >= 2:
                            self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(df[0])))
                            self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(df[1])))

            logger.info(
                f"MANOVA table final size: {self.tabManovaResult.rowCount()}x{self.tabManovaResult.columnCount()}"
            )
        else:
            logger.warning("MANOVA result is empty or None")

        # Handle property names safely
        if self.analysis.propertyname_str:
            variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to dataset's variable names if analysis doesn't have them
            variablename_list = self.analysis.dataset.get_variablename_list()
            logger.info(f"Using dataset variable names: {variablename_list}")

        symbol_candidate = ["o", "s", "^", "x", "+", "d", "v", "<", ">", "p", "h"]
        symbol_candidate = self.marker_list[:]
        color_candidate = ["blue", "green", "black", "cyan", "magenta", "yellow", "gray", "red"]
        color_candidate = self.color_list[:]

        SCATTER_MEDIUM_SIZE = 50
        scatter_size = SCATTER_MEDIUM_SIZE

        self.pca_ax3.clear()
        self.cva_ax3.clear()

        axis_prefix_list = ["PC", "CV"]
        combo_list = [self.comboPcaGroupBy, self.comboCvaGroupBy]
        fig_list = [self.pca_fig3, self.cva_fig3]
        ax_list = [self.pca_ax3, self.cva_ax3]
        propertyname_index_list = [-1, -1]
        self.pca_scatter_data = {}
        self.cva_scatter_data = {}
        scatter_data_list = [self.pca_scatter_data, self.cva_scatter_data]
        self.pca_scatter_result = {}
        self.cva_scatter_result = {}
        scatter_result_list = [self.pca_scatter_result, self.cva_scatter_result]
        analysis_result_list_list = [pca_analysis_result_list, cva_analysis_result_list]

        # Debug logging for analysis results
        logger.info(f"Object count: {len(object_info_list)}")
        if pca_analysis_result_list:
            logger.info(f"PCA result count: {len(pca_analysis_result_list)}")
        else:
            logger.info("PCA result is None/empty")
        if cva_analysis_result_list:
            logger.info(f"CVA result count: {len(cva_analysis_result_list)}")
        else:
            logger.info("CVA result is None/empty")

        for idx, axis_prefix in enumerate(axis_prefix_list):
            logger.info(
                f"Processing analysis type idx={idx}, prefix='{axis_prefix}', has_data={analysis_result_list_list[idx] is not None}"
            )

            # Skip processing if no data available for this analysis type
            if not analysis_result_list_list[idx]:
                logger.info(f"Skipping {axis_prefix} processing - no data available")
                continue

            depth_shade = False
            axis1 = 0
            axis2 = 1
            axis3 = 2
            axis1_title = axis_prefix + str(axis1 + 1)
            axis2_title = axis_prefix + str(axis2 + 1)
            axis3_title = axis_prefix + str(axis3 + 1)
            propertyname = combo_list[idx].currentText()
            propertyname_index_list[idx] = (
                variablename_list.index(propertyname) if propertyname in variablename_list else -1
            )
            logger.info(
                f"Grouping for {axis_prefix}: propertyname='{propertyname}', index={propertyname_index_list[idx]}"
            )
            logger.info(f"Available variables: {variablename_list[:10]}")  # Show first 10 variables
            scatter_data_list[idx] = {}
            scatter_result_list[idx] = {}

            key_list = []
            key_list.append("__default__")
            scatter_data_list[idx]["__default__"] = {
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

            for idx2, obj in enumerate(object_info_list):
                key_name = "__default__"
                """ get propertyname """
                if idx2 < 3:  # Debug first 3 objects
                    logger.info(f"Object {idx2} keys: {list(obj.keys())}")
                    if "variable_list" in obj.keys():
                        logger.info(
                            f"Object {idx2} variable_list: {obj['variable_list'][:5] if len(obj['variable_list']) > 5 else obj['variable_list']}"
                        )

                if "variable_list" in obj.keys():
                    if propertyname_index_list[idx] > -1 and propertyname_index_list[idx] < len(obj["variable_list"]):
                        key_name = obj["variable_list"][propertyname_index_list[idx]]
                else:
                    if propertyname_index_list[idx] > -1 and propertyname_index_list[idx] < len(obj["property_list"]):
                        key_name = obj["property_list"][propertyname_index_list[idx]]

                if key_name not in scatter_data_list[idx].keys():
                    scatter_data_list[idx][key_name] = {
                        "x_val": [],
                        "y_val": [],
                        "z_val": [],
                        "data": [],
                        "property": key_name,
                        "symbol": "",
                        "color": "",
                        "size": scatter_size,
                    }
                    if idx2 < 5:  # Only log first few objects
                        logger.info(f"Created new group '{key_name}' for object {idx2}")

                # Safety check for analysis result data
                if (
                    analysis_result_list_list[idx]
                    and idx2 < len(analysis_result_list_list[idx])
                    and analysis_result_list_list[idx][idx2] is not None
                    and len(analysis_result_list_list[idx][idx2]) > max(axis1, axis2, axis3)
                ):
                    scatter_data_list[idx][key_name]["x_val"].append(analysis_result_list_list[idx][idx2][axis1])
                    scatter_data_list[idx][key_name]["y_val"].append(analysis_result_list_list[idx][idx2][axis2])
                    scatter_data_list[idx][key_name]["z_val"].append(analysis_result_list_list[idx][idx2][axis3])
                    scatter_data_list[idx][key_name]["data"].append(obj)
                else:
                    # Debug detailed failure reason
                    failure_reasons = []
                    if not analysis_result_list_list[idx]:
                        failure_reasons.append("no analysis data")
                    elif idx2 >= len(analysis_result_list_list[idx]):
                        failure_reasons.append(f"idx2({idx2}) >= data_len({len(analysis_result_list_list[idx])})")
                    elif analysis_result_list_list[idx][idx2] is None:
                        failure_reasons.append("result is None")
                    elif len(analysis_result_list_list[idx][idx2]) <= max(axis1, axis2, axis3):
                        failure_reasons.append(
                            f"result_len({len(analysis_result_list_list[idx][idx2])}) <= max_axis({max(axis1, axis2, axis3)})"
                        )

                    # Silently skip invalid analysis result data
                    # logger.warning(f"Skipping invalid analysis result data for object {idx2}: {', '.join(failure_reasons)}")
                    # Add default values to maintain consistency
                    scatter_data_list[idx][key_name]["x_val"].append(0.0)
                    scatter_data_list[idx][key_name]["y_val"].append(0.0)
                    scatter_data_list[idx][key_name]["z_val"].append(0.0)
                    scatter_data_list[idx][key_name]["data"].append(obj)

            """ remove empty group """
            if len(scatter_data_list[idx]["__default__"]["x_val"]) == 0:
                del scatter_data_list[idx]["__default__"]

            """ assign color and symbol """
            sc_idx = 0
            for key_name in scatter_data_list[idx].keys():
                if scatter_data_list[idx][key_name]["color"] == "":
                    scatter_data_list[idx][key_name]["color"] = color_candidate[sc_idx % len(color_candidate)]
                    scatter_data_list[idx][key_name]["symbol"] = symbol_candidate[sc_idx % len(symbol_candidate)]
                    sc_idx += 1

            if True:
                ax_list[idx].clear()
                for name in scatter_data_list[idx].keys():
                    group = scatter_data_list[idx][name]
                    if len(scatter_data_list[idx][name]["x_val"]) > 0:
                        scatter_result_list[idx][name] = ax_list[idx].scatter(
                            group["x_val"],
                            group["y_val"],
                            group["z_val"],
                            s=group["size"],
                            marker=group["symbol"],
                            color=group["color"],
                            data=group["data"],
                            depthshade=depth_shade,
                            picker=True,
                            pickradius=5,
                        )

                if True:
                    if "__default__" in scatter_result_list[idx].keys():
                        del scatter_result_list[idx]["__default__"]
                    ax_list[idx].legend(
                        scatter_result_list[idx].values(),
                        scatter_result_list[idx].keys(),
                        loc="upper right",
                        bbox_to_anchor=(1.05, 1),
                    )
                if True:
                    ax_list[idx].set_xlabel(axis1_title)
                    ax_list[idx].set_ylabel(axis2_title)
                    ax_list[idx].set_zlabel(axis3_title)
                fig_list[idx].tight_layout()
                fig_list[idx].canvas.draw()
                fig_list[idx].canvas.flush_events()
