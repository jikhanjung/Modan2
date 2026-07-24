"""
AnalysisInfoWidget - Extracted from ModanComponents.py
Part of modular refactoring effort.
"""

import logging
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
    from OpenGL import GLUT as glut  # type: ignore[no-redef]

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

    def _normalize_manova_result(self, raw):
        """Coerce stored MANOVA JSON into the shape the table expects.

        Accepts the current ``{'stat_dict': ...}`` wrapper, a bare stat_dict
        (identified by ``column_names``), or an unknown layout passed through.
        """
        logger = logging.getLogger(__name__)
        if not isinstance(raw, dict):
            logger.warning(f"MANOVA result is not a dict, type: {type(raw)}")
            return raw
        if "stat_dict" in raw:
            logger.info("MANOVA format: already has stat_dict wrapper")
            return raw
        if "column_names" in raw:
            logger.info("MANOVA format: is a stat_dict, wrapping it")
            return {"stat_dict": raw}
        logger.warning("MANOVA format: unknown, using as-is")
        return raw

    def _load_result_json(self):
        """Parse the analysis' stored JSON blobs.

        Returns ``(object_info_list, pca_result_list, cva_result_list,
        manova_result)``; the result lists are None when that analysis was not run.
        """
        logger = logging.getLogger(__name__)
        object_info_list = json.loads(self.analysis.object_info_json)
        for obj in object_info_list:
            if "property_list" in obj.keys():
                obj["variable_list"] = obj["property_list"]

        pca_result_list = None
        if self.analysis.pca_analysis_result_json:
            pca_result_list = json.loads(self.analysis.pca_analysis_result_json)

        cva_result_list = None
        if self.analysis.cva_analysis_result_json:
            cva_result_list = json.loads(self.analysis.cva_analysis_result_json)
        else:
            logger.warning("CVA analysis_result_json is empty or None")

        manova_result = None
        if self.analysis.manova_analysis_result_json:
            try:
                manova_result = self._normalize_manova_result(json.loads(self.analysis.manova_analysis_result_json))
            except Exception as e:
                logger.error(f"Failed to parse MANOVA JSON: {e}")
        else:
            logger.warning("No MANOVA analysis_result_json")

        return object_info_list, pca_result_list, cva_result_list, manova_result

    def _fill_manova_stat_dict(self, stat_dict):
        """Fill the table from the current stat_dict layout (one row per statistic)."""
        logger = logging.getLogger(__name__)
        for stat_name, stat_values in stat_dict.items():
            if stat_name == "column_names":
                continue
            row = self.tabManovaResult.rowCount()
            self.tabManovaResult.insertRow(row)
            self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))
            if isinstance(stat_values, list) and len(stat_values) >= 5:
                self.tabManovaResult.setItem(row, 1, QTableWidgetItem(f"{stat_values[0]:.6e}"))
                self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(int(stat_values[1]))))
                self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(int(stat_values[2]))))
                self.tabManovaResult.setItem(row, 4, QTableWidgetItem(f"{stat_values[3]:.3f}"))
                self.tabManovaResult.setItem(row, 5, QTableWidgetItem(f"{stat_values[4]:.3f}"))
            else:
                logger.warning(f"Invalid stat values for {stat_name}: {stat_values}")

    def _fill_manova_statistics(self, statistics):
        """Fill the table from the older per-statistic dict layout."""
        for stat_name, stat_data in statistics.items():
            row = self.tabManovaResult.rowCount()
            self.tabManovaResult.insertRow(row)
            self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_name))
            if isinstance(stat_data, dict):
                for col, key in enumerate(("value", "num_df", "den_df", "f_statistic", "p_value"), start=1):
                    self.tabManovaResult.setItem(row, col, QTableWidgetItem(str(stat_data.get(key, "N/A"))))

    def _fill_manova_flat(self, manova_result):
        """Fill the table from a flat {statistic: value} layout."""
        stat_mapping = {
            "wilks_lambda": "Wilks' Lambda",
            "pillais_trace": "Pillai's Trace",
            "hotellings_trace": "Hotelling's Trace",
            "roys_largest_root": "Roy's Largest Root",
            "f_statistic": "F Statistic",
            "p_value": "P Value",
        }
        degrees_of_freedom = manova_result.get("degrees_of_freedom")
        for key, value in manova_result.items():
            if key in ("analysis_type", "degrees_of_freedom"):
                continue  # meta information, not a statistic row
            row = self.tabManovaResult.rowCount()
            self.tabManovaResult.insertRow(row)
            self.tabManovaResult.setItem(row, 0, QTableWidgetItem(stat_mapping.get(key, key.replace("_", " ").title())))
            self.tabManovaResult.setItem(row, 1, QTableWidgetItem(str(value)))
            if isinstance(degrees_of_freedom, (list, tuple)) and len(degrees_of_freedom) >= 2:
                self.tabManovaResult.setItem(row, 2, QTableWidgetItem(str(degrees_of_freedom[0])))
                self.tabManovaResult.setItem(row, 3, QTableWidgetItem(str(degrees_of_freedom[1])))

    def _populate_manova_table(self, manova_result):
        """Reset and fill the MANOVA table, tolerating the stored layouts."""
        logger = logging.getLogger(__name__)
        self.tabManovaResult.clear()
        self.tabManovaResult.setRowCount(0)
        if not manova_result:
            logger.warning("MANOVA result is empty or None")
            return

        column_headers = ["Statistic", "Value", "Num DF", "Den DF", "F Value", "Pr>F"]
        self.tabManovaResult.setColumnCount(len(column_headers))
        self.tabManovaResult.setHorizontalHeaderLabels(column_headers)

        if isinstance(manova_result.get("stat_dict"), dict):
            self._fill_manova_stat_dict(manova_result["stat_dict"])
        elif isinstance(manova_result.get("statistics"), dict):
            self._fill_manova_statistics(manova_result["statistics"])
        else:
            self._fill_manova_flat(manova_result)

    def _plot_analysis_scatter(
        self, axis_prefix, analysis_result_list, object_info_list, variablename_list, combo, ax, fig, scatter_size
    ):
        """Group the objects by the selected variable and draw one analysis
        type's 3-axis scatter (PCA or CVA)."""
        logger = logging.getLogger(__name__)
        symbol_candidate = self.marker_list[:]
        color_candidate = self.color_list[:]
        axis1, axis2, axis3 = 0, 1, 2

        propertyname = combo.currentText()
        propertyname_index = variablename_list.index(propertyname) if propertyname in variablename_list else -1
        logger.info(f"Grouping for {axis_prefix}: propertyname='{propertyname}', index={propertyname_index}")

        scatter_data = {
            "__default__": {
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
        }

        for idx, obj in enumerate(object_info_list):
            source_list = obj["variable_list"] if "variable_list" in obj.keys() else obj["property_list"]
            key_name = source_list[propertyname_index] if -1 < propertyname_index < len(source_list) else "__default__"

            if key_name not in scatter_data:
                scatter_data[key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }

            group = scatter_data[key_name]
            row = analysis_result_list[idx] if idx < len(analysis_result_list) else None
            if row is not None and len(row) > max(axis1, axis2, axis3):
                group["x_val"].append(row[axis1])
                group["y_val"].append(row[axis2])
                group["z_val"].append(row[axis3])
            else:
                # Keep the group aligned with object_info_list even when the
                # result row is missing or too short.
                group["x_val"].append(0.0)
                group["y_val"].append(0.0)
                group["z_val"].append(0.0)
            group["data"].append(obj)

        if len(scatter_data["__default__"]["x_val"]) == 0:
            del scatter_data["__default__"]

        sc_idx = 0
        for group in scatter_data.values():
            if group["color"] == "":
                group["color"] = color_candidate[sc_idx % len(color_candidate)]
                group["symbol"] = symbol_candidate[sc_idx % len(symbol_candidate)]
                sc_idx += 1

        ax.clear()
        scatter_result = {}
        for name, group in scatter_data.items():
            if len(group["x_val"]) > 0:
                scatter_result[name] = ax.scatter(
                    group["x_val"],
                    group["y_val"],
                    group["z_val"],
                    s=group["size"],
                    marker=group["symbol"],
                    color=group["color"],
                    data=group["data"],
                    depthshade=False,
                    picker=True,
                    pickradius=5,
                )
        scatter_result.pop("__default__", None)

        # Imported lazily: `dialogs/__init__` pulls in this package, so a
        # module-level import here is a circular import.
        from dialogs.scatter_utils import apply_legend_italics, format_legend_label

        legend_keys = list(scatter_result.keys())
        legend = ax.legend(
            scatter_result.values(),
            [format_legend_label(key)[0] for key in legend_keys],
            loc="upper right",
            bbox_to_anchor=(1.05, 1),
        )
        apply_legend_italics(legend, legend_keys)

        ax.set_xlabel(f"{axis_prefix}{axis1 + 1}")
        ax.set_ylabel(f"{axis_prefix}{axis2 + 1}")
        ax.set_zlabel(f"{axis_prefix}{axis3 + 1}")
        fig.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()

    def show_analysis_result(self):
        """Populate the info fields, MANOVA table and PCA/CVA scatter plots."""
        logger = logging.getLogger(__name__)
        logger.info(f"show_analysis_result called for: {self.analysis.analysis_name}")

        # Legacy analyses have no JSON payload — show just the basics.
        if not self.analysis.object_info_json:
            logger.warning("No JSON data found - showing basic analysis info")
            self.edtAnalysisName.setText(self.analysis.analysis_name)
            self.edtSuperimposition.setText(self.analysis.superimposition_method or "Unknown")
            return

        object_info_list, pca_result_list, cva_result_list, manova_result = self._load_result_json()

        self._populate_manova_table(manova_result)

        if self.analysis.propertyname_str:
            variablename_list = self.analysis.propertyname_str.split(",")
        else:
            # Fallback to the dataset's variable names if the analysis lacks them.
            variablename_list = self.analysis.dataset.get_variablename_list()

        scatter_size = 50  # SCATTER_MEDIUM_SIZE
        self.pca_ax3.clear()
        self.cva_ax3.clear()

        for axis_prefix, result_list, combo, ax, fig in (
            ("PC", pca_result_list, self.comboPcaGroupBy, self.pca_ax3, self.pca_fig3),
            ("CV", cva_result_list, self.comboCvaGroupBy, self.cva_ax3, self.cva_fig3),
        ):
            if not result_list:
                logger.info(f"Skipping {axis_prefix} processing - no data available")
                continue
            self._plot_analysis_scatter(
                axis_prefix, result_list, object_info_list, variablename_list, combo, ax, fig, scatter_size
            )
