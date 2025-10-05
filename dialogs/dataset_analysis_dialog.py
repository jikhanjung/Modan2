"""Dataset Analysis Dialog for visualizing and analyzing morphometric datasets.

This module provides the DatasetAnalysisDialog class for displaying analysis results,
visualizing shapes, and managing dataset-level analysis options.
"""

import logging

import numpy as np
from PyQt5.QtCore import Qt, QRect, QSize, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from components.widgets import DatasetOpsViewer
from MdModel import MdDataset
from ModanComponents import ObjectViewer3D

logger = logging.getLogger(__name__)

class DatasetAnalysisDialog(QDialog):
    def __init__(self, parent, dataset):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Dataset Analysis"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.default_color_list = mu.VIVID_COLOR_LIST[:]
        self.color_list = self.default_color_list[:]
        self.marker_list = mu.MARKER_LIST[:]
        self.plot_size = "medium"
        self.read_settings()
        # self.setGeometry(QRect(100, 100, 1400, 800))
        self.ds_ops = None
        self.object_hash = {}
        self.shape_list = []
        self.shape_name_list = []

        self.main_hsplitter = QSplitter(Qt.Horizontal)

        # 2d shape
        self.lblShape2 = DatasetOpsViewer(self)
        self.lblShape2.setAlignment(Qt.AlignCenter)
        self.lblShape2.setMinimumWidth(400)
        self.lblShape2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 3d shape
        self.lblShape3 = ObjectViewer3D(self)
        self.lblShape3.setMinimumWidth(400)
        self.lblShape3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if dataset.dimension == 3:
            self.lblShape2.hide()
            self.lblShape = self.lblShape3
        else:
            self.lblShape3.hide()
            self.lblShape = self.lblShape2

        # checkboxes
        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText(self.tr("Index"))
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText(self.tr("Wireframe"))
        self.cbxShowWireframe.setChecked(False)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText(self.tr("Baseline"))
        self.cbxShowBaseline.setChecked(False)
        self.cbxShowAverage = QCheckBox()
        self.cbxShowAverage.setText(self.tr("Average"))
        self.cbxShowAverage.setChecked(True)
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText(self.tr("Rotate"))
        self.cbxAutoRotate.setChecked(False)

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)

        self.checkbox_layout = QHBoxLayout()
        self.checkbox_layout.addWidget(self.cbxShowIndex)
        self.checkbox_layout.addWidget(self.cbxShowWireframe)
        self.checkbox_layout.addWidget(self.cbxShowBaseline)
        self.checkbox_layout.addWidget(self.cbxShowAverage)
        self.checkbox_layout.addWidget(self.cbxAutoRotate)
        self.cbx_widget = QWidget()
        self.cbx_widget.setLayout(self.checkbox_layout)

        self.shape_vsplitter = QSplitter(Qt.Vertical)
        self.shape_vsplitter.addWidget(self.lblShape)
        self.shape_vsplitter.addWidget(self.cbx_widget)
        self.shape_vsplitter.setSizes([800, 20])
        self.shape_vsplitter.setStretchFactor(0, 1)
        self.shape_vsplitter.setStretchFactor(1, 0)

        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.table_widget.setLayout(self.table_layout)

        self.table_tab = QTabWidget()

        self.tableView1 = QTableView()
        self.tableView1.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView1.setSortingEnabled(True)

        self.tableView2 = QTableView()
        self.tableView2.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView2.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table_tab.addTab(self.tableView1, self.tr("Objects"))
        self.table_tab.addTab(self.tableView2, self.tr("Groups"))
        self.table_tab.setTabVisible(1, False)
        self.table_layout.addWidget(self.table_tab)

        self.table_control_widget = QWidget()
        self.table_control_layout = QHBoxLayout()
        self.table_control_widget.setLayout(self.table_control_layout)
        self.btnSelectAll = QPushButton()
        self.btnSelectAll.setText(self.tr("All"))
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnSelectNone = QPushButton()
        self.btnSelectNone.setText(self.tr("None"))
        self.btnSelectNone.clicked.connect(self.select_none)
        self.btnSelectInvert = QPushButton()
        self.btnSelectInvert.setText(self.tr("Invert"))
        self.btnSelectInvert.clicked.connect(self.select_invert)
        self.table_control_layout.addWidget(self.btnSelectAll)
        self.table_control_layout.addWidget(self.btnSelectNone)
        self.table_control_layout.addWidget(self.btnSelectInvert)
        self.table_control_layout.addStretch(1)

        self.table_layout.addWidget(self.table_control_widget)

        # plot widgets
        self.plot_widget2 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig2 = self.plot_widget2.figure
        self.ax2 = self.fig2.add_subplot()
        self.toolbar2 = NavigationToolbar(self.plot_widget2, self)
        self.plot_widget3 = FigureCanvas(Figure(figsize=(20, 16), dpi=100))
        self.fig3 = self.plot_widget3.figure
        self.ax3 = self.fig3.add_subplot(projection="3d")
        self.toolbar3 = NavigationToolbar(self.plot_widget3, self)

        self.plot_layout = QVBoxLayout()
        self.plot_control_layout1 = QHBoxLayout()
        self.plot_control_layout2 = QHBoxLayout()
        self.plot_control_widget1 = QWidget()
        self.plot_control_widget2 = QWidget()
        self.plot_control_widget1.setMaximumHeight(80)
        self.plot_control_widget1.setLayout(self.plot_control_layout1)
        self.plot_control_widget2.setMaximumHeight(80)
        self.plot_control_widget2.setLayout(self.plot_control_layout2)

        # chart options
        self.comboAxis1 = QComboBox()
        self.comboAxis2 = QComboBox()
        self.comboAxis3 = QComboBox()
        self.cbxFlipAxis1 = QCheckBox()
        self.cbxFlipAxis1.setText("Flip")
        self.cbxFlipAxis1.setChecked(False)
        self.cbxFlipAxis2 = QCheckBox()
        self.cbxFlipAxis2.setText("Flip")
        self.cbxFlipAxis2.setChecked(False)
        self.cbxFlipAxis3 = QCheckBox()
        self.cbxFlipAxis3.setText("Flip")
        self.cbxFlipAxis3.setChecked(False)
        self.gbAxis1 = QGroupBox()
        self.gbAxis1.setTitle("Axis 1")
        self.gbAxis1.setLayout(QHBoxLayout())
        self.gbAxis1.layout().addWidget(self.comboAxis1)
        self.gbAxis1.layout().addWidget(self.cbxFlipAxis1)
        self.gbAxis2 = QGroupBox()
        self.gbAxis2.setTitle("Axis 2")
        self.gbAxis2.setLayout(QHBoxLayout())
        self.gbAxis2.layout().addWidget(self.comboAxis2)
        self.gbAxis2.layout().addWidget(self.cbxFlipAxis2)
        self.gbAxis3 = QGroupBox()
        self.gbAxis3.setTitle("Axis 3")
        self.gbAxis3.setLayout(QHBoxLayout())
        self.gbAxis3.layout().addWidget(self.comboAxis3)
        self.gbAxis3.layout().addWidget(self.cbxFlipAxis3)
        self.plot_control_layout1.addWidget(self.gbAxis1)
        self.plot_control_layout1.addWidget(self.gbAxis2)
        self.plot_control_layout1.addWidget(self.gbAxis3)

        self.cbxFlipAxis1.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis2.stateChanged.connect(self.flip_axis_changed)
        self.cbxFlipAxis3.stateChanged.connect(self.flip_axis_changed)

        self.rb2DChartDim = QRadioButton("2D")
        self.rb3DChartDim = QRadioButton("3D")
        self.rb2DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.rb3DChartDim.toggled.connect(self.on_chart_dim_changed)
        self.cbxDepthShade = QCheckBox()
        self.cbxDepthShade.setText(self.tr("Depth Shade"))
        self.cbxDepthShade.setChecked(False)
        self.cbxDepthShade.toggled.connect(self.on_chart_dim_changed)
        self.cbxLegend = QCheckBox()
        self.cbxLegend.setText(self.tr("Legend"))
        self.cbxLegend.setChecked(False)
        self.cbxLegend.toggled.connect(self.on_chart_dim_changed)
        self.cbxAxisLabel = QCheckBox()
        self.cbxAxisLabel.setText(self.tr("Axis"))
        self.cbxAxisLabel.setChecked(True)
        self.cbxAxisLabel.toggled.connect(self.on_chart_dim_changed)
        self.gbChartDim = QGroupBox()
        self.gbChartDim.setTitle(self.tr("Chart"))
        self.gbChartDim.setLayout(QHBoxLayout())
        self.gbChartDim.layout().addWidget(self.rb2DChartDim)
        self.gbChartDim.layout().addWidget(self.rb3DChartDim)
        self.gbChartDim.layout().addWidget(self.cbxDepthShade)
        self.gbChartDim.layout().addWidget(self.cbxLegend)
        self.gbChartDim.layout().addWidget(self.cbxAxisLabel)
        self.gbGroupBy = QGroupBox()
        self.gbGroupBy.setTitle(self.tr("Grouping variable"))
        self.gbGroupBy.setLayout(QHBoxLayout())
        self.comboPropertyName = QComboBox()
        self.comboPropertyName.setCurrentIndex(-1)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        self.gbGroupBy.layout().addWidget(self.comboPropertyName)

        self.plot_control_layout2.addWidget(self.gbChartDim)
        self.plot_control_layout2.addWidget(self.gbGroupBy)

        self.btnChartOptions = QPushButton(self.tr("Chart Options"))
        self.btnChartOptions.clicked.connect(self.chart_options_clicked)

        self.plot_view = QWidget()
        self.plot_view.setLayout(QVBoxLayout())
        self.plot_view.layout().addWidget(self.toolbar2)
        self.plot_view.layout().addWidget(self.plot_widget2)
        self.plot_view.layout().addWidget(self.toolbar3)
        self.plot_view.layout().addWidget(self.plot_widget3)

        self.plot_tab = QTabWidget()
        self.plot_tab.addTab(self.plot_view, "Chart")
        self.plot_data = QTableWidget()
        self.plot_data.setColumnCount(10)
        self.rotation_matrix_data = QTableWidget()
        self.rotation_matrix_data.setColumnCount(10)
        self.eigenvalue_data = QTableWidget()
        self.eigenvalue_data.setColumnCount(2)
        self.shapes_data = QTableWidget()
        self.shapes_data.setColumnCount(10)

        self.plot_tab.addTab(self.plot_data, self.tr("Result table"))
        self.plot_tab.addTab(self.rotation_matrix_data, self.tr("Rotation matrix"))
        self.plot_tab.addTab(self.eigenvalue_data, self.tr("Eigenvalues"))
        self.plot_tab.addTab(self.shapes_data, self.tr("Shapes"))

        self.plot_layout.addWidget(self.plot_tab)
        # self.plot_layout.addWidget(self.toolbar2)
        # self.plot_layout.addWidget(self.plot_widget2)
        # self.plot_layout.addWidget(self.toolbar3)
        # self.plot_layout.addWidget(self.plot_widget3)
        self.plot_layout.addWidget(self.plot_control_widget1)
        self.plot_layout.addWidget(self.plot_control_widget2)
        self.plot_layout.addWidget(self.btnChartOptions)

        self.plot_all_widget = QWidget()
        self.plot_all_widget.setLayout(self.plot_layout)

        # set value 1 to 10 for axis
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

        self.main_hsplitter.addWidget(self.shape_vsplitter)
        self.main_hsplitter.addWidget(self.table_widget)
        self.main_hsplitter.addWidget(self.plot_all_widget)

        self.main_hsplitter.setSizes([400, 200, 400])
        self.main_hsplitter.setStretchFactor(0, 1)
        self.main_hsplitter.setStretchFactor(1, 0)
        self.main_hsplitter.setStretchFactor(2, 1)

        # bottom layout
        rbbox_height = 50

        self.left_bottom_layout = QVBoxLayout()
        self.middle_bottom_layout = QVBoxLayout()
        self.right_bottom_layout = QVBoxLayout()

        self.rbProcrustes = QRadioButton("Procrustes")
        self.rbBookstein = QRadioButton("Bookstein")
        self.rbResistantFit = QRadioButton("Resistant Fit")
        self.rbProcrustes.setChecked(True)
        self.rbBookstein.setEnabled(False)
        self.rbResistantFit.setEnabled(False)
        self.btnSuperimpose = QPushButton(self.tr("Superimpose"))
        self.btnSuperimpose.clicked.connect(self.on_btnSuperimpose_clicked)
        self.gbSuperimposition = QGroupBox()
        self.gbSuperimposition.setTitle(self.tr("Superimposition"))
        self.gbSuperimposition.setLayout(QHBoxLayout())
        self.gbSuperimposition.layout().addWidget(self.rbProcrustes)
        self.gbSuperimposition.layout().addWidget(self.rbBookstein)
        self.gbSuperimposition.layout().addWidget(self.rbResistantFit)
        self.gbSuperimposition.setMaximumHeight(rbbox_height)

        self.left_bottom_layout.addWidget(self.gbSuperimposition)
        self.left_bottom_layout.addWidget(self.btnSuperimpose)

        self.rbPCA = QRadioButton("PCA")
        self.rbPCA.setChecked(True)
        self.rbPCA.toggled.connect(self.on_analysis_type_changed)
        self.rbCVA = QRadioButton("CVA")
        self.rbCVA.setEnabled(False)
        self.rbCVA.toggled.connect(self.on_analysis_type_changed)
        self.gbAnalysis = QGroupBox()
        self.gbAnalysis.setTitle("Analysis")
        self.gbAnalysis.setLayout(QHBoxLayout())
        self.gbAnalysis.layout().addWidget(self.rbPCA)
        self.gbAnalysis.layout().addWidget(self.rbCVA)
        self.gbAnalysis.setMaximumHeight(rbbox_height)
        self.btnAnalyze = QPushButton(self.tr("Perform Analysis"))
        self.btnAnalyze.clicked.connect(self.on_btn_analysis_clicked)
        self.middle_bottom_layout.addWidget(self.gbAnalysis)
        self.middle_bottom_layout.addWidget(self.btnAnalyze)

        self.empty_widget = QWidget()
        self.btnSaveResults = QPushButton(self.tr("Save Results"))
        self.btnSaveResults.clicked.connect(self.on_btnSaveResults_clicked)
        self.rb1_layout = QVBoxLayout()
        self.rb1_layout.addWidget(self.empty_widget)
        self.rb1_widget = QWidget()
        self.rb1_widget.setMinimumHeight(rbbox_height)
        self.rb1_widget.setMaximumHeight(rbbox_height)
        self.rb1_widget.setLayout(self.rb1_layout)
        self.right_bottom_layout.addWidget(self.rb1_widget)
        self.right_bottom_layout.addWidget(self.btnSaveResults)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addLayout(self.left_bottom_layout)
        self.bottom_layout.addLayout(self.middle_bottom_layout)
        self.bottom_layout.addLayout(self.right_bottom_layout)

        self.status_bar = QStatusBar()
        self.status_bar.setMaximumHeight(20)

        # final layout done
        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()
        self.main_layout.addWidget(self.main_hsplitter)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.status_bar)
        self.setLayout(self.main_layout)

        # initialization
        self.pca_result = None
        self.selected_object_list = []
        self.selected_object_id_list = []
        self.scatter_result = {}
        self.scatter_data = {}

        self.show_chart_options = True
        self.selection_changed_off = False
        self.onpick_happened = False

        self.analysis_type = "PCA"
        self.analysis_done = False

        # data setting
        set_result = self.set_dataset(dataset)
        # print("set dataset result: ", set_result)
        if set_result is False:
            self.close()
            return
        elif set_result is None:
            self.close()
            return
        else:
            self.reset_tableView()
            self.load_object()
            self.chart_options_clicked()
            self.rb3DChartDim.setChecked(True)
            self.on_chart_dim_changed()
            self.on_btn_analysis_clicked()

            self.btnSaveResults.setFocus()

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        self.plot_size = self.m_app.settings.value("PlotSize", self.plot_size)
        for i in range(len(self.color_list)):
            self.color_list[i] = self.m_app.settings.value("DataPointColor/" + str(i), self.default_color_list[i])
        for i in range(len(self.marker_list)):
            self.marker_list[i] = self.m_app.settings.value("DataPointMarker/" + str(i), self.marker_list[i])

        if self.remember_geometry is True:
            self.setGeometry(
                self.m_app.settings.value("WindowGeometry/DatasetAnalysisWindow", QRect(100, 100, 1400, 800))
            )
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/DatasetAnalysisWindow", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def on_analysis_type_changed(self):
        self.analysis_done = False
        axis1 = self.comboAxis1.currentIndex()
        axis2 = self.comboAxis2.currentIndex()
        axis3 = self.comboAxis3.currentIndex()
        self.comboAxis1.clear()
        self.comboAxis2.clear()
        self.comboAxis3.clear()
        if self.rbPCA.isChecked():
            header = "PC"
        else:
            header = "CV"

        for i in range(1, 11):
            self.comboAxis1.addItem(header + str(i))
            self.comboAxis2.addItem(header + str(i))
            self.comboAxis3.addItem(header + str(i))
        self.comboAxis1.setCurrentIndex(axis1)
        self.comboAxis2.setCurrentIndex(axis2)
        self.comboAxis3.setCurrentIndex(axis3)
        # self.reset_tableView()
        # self.load_object()
        # self.on_btn_analysis_clicked()

    def select_all(self):
        pass

    def select_none(self):
        pass

    def select_invert(self):
        pass

    def chart_options_clicked(self):
        self.show_chart_options = not self.show_chart_options
        if self.show_chart_options:
            # self.gbChartOptions.show()
            self.plot_control_widget1.show()
            self.plot_control_widget2.show()
        else:
            # self.gbChartOptions.hide()
            self.plot_control_widget1.hide()
            self.plot_control_widget2.hide()

    def on_chart_dim_changed(self):
        if self.rb2DChartDim.isChecked():
            self.plot_widget3.hide()
            self.plot_widget2.show()
            self.toolbar2.show()
            self.toolbar3.hide()
            self.gbAxis3.hide()
            self.comboAxis3.hide()
            self.cbxFlipAxis3.hide()
            self.cbxDepthShade.hide()
        else:
            self.plot_widget2.hide()
            self.plot_widget3.show()
            self.toolbar2.hide()
            self.toolbar3.show()
            self.gbAxis3.show()
            self.comboAxis3.show()
            self.cbxFlipAxis3.show()
            self.cbxDepthShade.show()

        if self.ds_ops is not None:
            self.show_analysis_result()

    def set_dataset(self, dataset):
        # print("dataset:", dataset)
        self.dataset = dataset
        prev_lm_count = -1
        for obj in dataset.object_list:
            obj.unpack_landmark()
            obj.unpack_variable()
            # print("property:", obj.variable_list)
            lm_count = len(obj.landmark_list)
            # print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
            if prev_lm_count != lm_count and prev_lm_count != -1:
                # show messagebox and close the window
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(self.tr("Error: landmark count is not consistent"))
                msg.setWindowTitle("Error")
                msg.exec_()
                self.close()
                return False
            prev_lm_count = lm_count

        self.comboPropertyName.clear()
        self.comboPropertyName.addItem("Select Property")
        if len(self.dataset.variablename_list) > 0:
            for propertyname in self.dataset.variablename_list:
                self.comboPropertyName.addItem(propertyname)
                # self.comboAxis2.addItem(propertyname)
        self.comboPropertyName.setCurrentIndex(0)
        self.comboPropertyName.currentIndexChanged.connect(self.propertyname_changed)
        if self.dataset.dimension == 3:
            self.cbxAutoRotate.show()
        else:
            self.cbxAutoRotate.hide()

        self.show_index_state_changed()
        self.show_wireframe_state_changed()
        self.show_baseline_state_changed()
        self.show_average_state_changed()
        self.auto_rotate_state_changed
        # self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        # self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        # self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        # self.cbxShowAverage.stateChanged.connect(self.show_average_state_changed)
        # self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
        return True

    def propertyname_changed(self):
        perform_analysis = False
        if self.comboPropertyName.currentIndex() > 0:
            self.rbCVA.setEnabled(True)
            self.cbxLegend.setChecked(True)
            perform_analysis = True
        else:
            self.rbCVA.setEnabled(False)
            self.cbxLegend.setChecked(False)

        if self.ds_ops is not None:
            self.reset_tableView()
            self.load_object()
            if perform_analysis:
                self.on_btn_analysis_clicked()
            self.show_analysis_result()

    def axis_changed(self):
        if self.ds_ops is not None and self.analysis_done is True:
            self.show_analysis_result()

    def flip_axis_changed(self, int):
        if self.ds_ops is not None:
            self.show_analysis_result()

    def on_btnSuperimpose_clicked(self):
        logger = logging.getLogger(__name__)
        logger.debug("on_btnSuperimpose_clicked")

    def on_btnAnalyze_clicked(self):
        # print("on_btnAnalyze_clicked")
        self.selected_object_id_list = []
        self.ds_ops.selected_object_id_list = self.selected_object_id_list
        self.load_object()
        self.on_object_selection_changed([], [])
        self.show_analysis_result()
        self.show_object_shape()

    def on_btnSaveResults_clicked(self):
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d_%H%M%S")

        filename_candidate = f"{self.ds_ops.dataset_name}_analysis_{date_str}.xlsx"
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        # print("filepath:", filepath)
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save File As"), filepath, "Excel format (*.xlsx)")
        if filename:
            # print("filename:", filename)
            doc = xlsxwriter.Workbook(filename)

            # PCA result
            property_count = len(self.ds_ops.variablename_list)
            header = ["object_name", *self.ds_ops.variablename_list]
            header.extend(
                [
                    self.analysis_type[:2] + str(i + 1)
                    for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))
                ]
            )
            header.extend("CSize")
            worksheet = doc.add_worksheet("Result coordinates")
            row_index = 0
            column_index = 0

            for colname in header:
                worksheet.write(row_index, column_index, colname)
                column_index += 1

            new_coords = self.analysis_result.rotated_matrix.tolist()
            for i, obj in enumerate(self.ds_ops.object_list):
                worksheet.write(i + 1, 0, obj.object_name)
                # print(obj.variable_list)
                for j in range(property_count):
                    # for j, property in enumerate(obj.variable_list):
                    worksheet.write(i + 1, j + 1, obj.variable_list[j])

                for k, val in enumerate(new_coords[i]):
                    worksheet.write(i + 1, k + property_count + 1, val)
                    # self.plot_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
                obj = MdObject.get_by_id(obj.id)
                worksheet.write(i + 1, k + property_count + 2, obj.get_centroid_size(True))

            worksheet = doc.add_worksheet("Rotation matrix")
            row_index = 0
            column_index = 0
            rotation_matrix = self.analysis_result.rotation_matrix.tolist()
            # print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
            for i, row in enumerate(rotation_matrix):
                for j, val in enumerate(row):
                    worksheet.write(i, j, val)

            worksheet = doc.add_worksheet("Eigenvalues")
            for i, val in enumerate(self.analysis_result.raw_eigen_values):
                val2 = self.analysis_result.eigen_value_percentages[i]
                worksheet.write(i, 0, val)
                worksheet.write(i, 1, val2)

            # PCA result
            # header = [ "object_name", *self.ds_ops.variablename_list ]
            # header.extend( [self.analysis_type[:2]+str(i+1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))] )
            worksheet = doc.add_worksheet("Shapes")
            row_index = 0
            column_index = 0
            for i, colname in enumerate(self.shape_column_header_list):
                worksheet.write(row_index, i, colname)
                # column_index+=1

            for i, shape in enumerate(self.shape_list.tolist()):
                worksheet.write(i + 1, 0, self.shape_name_list[i])
                for j, val in enumerate(shape):
                    worksheet.write(i + 1, j + 1, val)
                    # self.shapes_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))

            doc.close()

        # print("on_btnSaveResults_clicked")

    def show_index_state_changed(self):
        if self.cbxShowIndex.isChecked():
            self.lblShape.show_index = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_index = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def show_average_state_changed(self):
        if self.cbxShowAverage.isChecked():
            self.lblShape.show_average = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_average = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def auto_rotate_state_changed(self):
        # print("auto_rotate_state_changed", self.cbxAutoRotate.isChecked())
        if self.cbxAutoRotate.isChecked():
            self.lblShape.auto_rotate = True
            # print("auto rotate CHECKED!")
        else:
            self.lblShape.auto_rotate = False
            # print("auto rotate UNCHECKED!")
        self.lblShape.update()

    def show_wireframe_state_changed(self):
        if self.cbxShowWireframe.isChecked():
            self.lblShape.show_wireframe = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_wireframe = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

    def show_baseline_state_changed(self):
        if self.cbxShowBaseline.isChecked():
            self.lblShape.show_baseline = True
            # print("show index CHECKED!")
        else:
            self.lblShape.show_baseline = False
            # print("show index UNCHECKED!")
        self.lblShape.update()

        # connect
        # self.lblShape.sigPain

    def show_object_shape(self):
        self.lblShape.set_ds_ops(self.ds_ops)
        self.lblShape.repaint()

    def on_btn_analysis_clicked(self):
        # print("pca button clicked")
        # set wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        self.ds_ops = MdDatasetOps(self.dataset)
        self.analysis_done = False
        if self.rbCVA.isChecked():
            self.analysis_type = "CVA"
        elif self.rbPCA.isChecked():
            self.analysis_type = "PCA"

        if not self.ds_ops.procrustes_superimposition():
            logger = logging.getLogger(__name__)
            logger.error("procrustes superimposition failed")
            return
        self.show_object_shape()

        if self.dataset.object_list is None or len(self.dataset.object_list) < 5:
            logger = logging.getLogger(__name__)
            logger.warning("too small number of objects for PCA analysis")
            return

        if self.analysis_type == "CVA":
            self.analysis_result = self.PerformCVA(self.ds_ops)

        elif self.analysis_type == "PCA":
            self.analysis_result = self.PerformPCA(self.ds_ops)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.analysis_result = new_coords[i]

        self.show_analysis_result()

        # end wait cursor
        self.analysis_done = True
        QApplication.restoreOverrideCursor()

        # print("pca_result.nVariable:",pca_result.nVariable)
        # with open('pca_result.txt', 'w') as f:
        #    for obj in ds_ops.object_list:
        #        f.write(obj.object_name + "\t" + "\t".join([str(x) for x in obj.pca_result]) + "\n")

    def show_analysis_result(self):
        # self.plot_widget.clear()

        self.show_result_table()
        # get axis1 and axis2 value from comboAxis1 and 2 index
        depth_shade = self.cbxDepthShade.isChecked()
        show_legend = self.cbxLegend.isChecked()
        show_axis_label = self.cbxAxisLabel.isChecked()
        axis1 = self.comboAxis1.currentIndex()
        axis2 = self.comboAxis2.currentIndex()
        axis3 = self.comboAxis3.currentIndex()
        axis1_title = self.comboAxis1.currentText()
        axis2_title = self.comboAxis2.currentText()
        axis3_title = self.comboAxis3.currentText()
        flip_axis1 = -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        flip_axis2 = -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        flip_axis3 = -1.0 if self.cbxFlipAxis3.isChecked() else 1.0

        symbol_candidate = ["o", "s", "^", "x", "+", "d", "v", "<", ">", "p", "h"]
        color_candidate = ["blue", "green", "black", "cyan", "magenta", "yellow", "gray", "red"]
        color_candidate = self.color_list[:]
        symbol_candidate = self.marker_list[:]
        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.scatter_data = {}
        self.scatter_result = {}
        SCATTER_SMALL_SIZE = 30
        SCATTER_MEDIUM_SIZE = 50
        SCATTER_LARGE_SIZE = 60
        if self.plot_size.lower() == "small":
            scatter_size = SCATTER_SMALL_SIZE
        elif self.plot_size.lower() == "medium":
            scatter_size = SCATTER_MEDIUM_SIZE
        elif self.plot_size.lower() == "large":
            scatter_size = SCATTER_LARGE_SIZE

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
        if len(self.selected_object_id_list) > 0:
            self.scatter_data["__selected__"] = {
                "x_val": [],
                "y_val": [],
                "z_val": [],
                "data": [],
                "hoverinfo": [],
                "text": [],
                "property": "",
                "symbol": "o",
                "color": "red",
                "size": SCATTER_LARGE_SIZE,
            }
            key_list.append("__selected__")

        for obj in self.ds_ops.object_list:
            key_name = "__default__"

            if obj.id in self.selected_object_id_list:
                key_name = "__selected__"
            elif self.propertyname_index > -1 and self.propertyname_index < len(obj.variable_list):
                key_name = obj.variable_list[self.propertyname_index]

            if key_name not in self.scatter_data.keys():
                self.scatter_data[key_name] = {
                    "x_val": [],
                    "y_val": [],
                    "z_val": [],
                    "data": [],
                    "property": key_name,
                    "symbol": "",
                    "color": "",
                    "size": scatter_size,
                }
            if axis1 == 10:
                mdobject = MdObject.get_by_id(obj.id)
                mdobject.get_centroid_size(True)
                # print("obj:", mdobject.id, "csize:", csize)
                self.scatter_data[key_name]["x_val"].append(flip_axis1 * mdobject.get_centroid_size(True))
            else:
                self.scatter_data[key_name]["x_val"].append(flip_axis1 * obj.analysis_result[axis1])
            self.scatter_data[key_name]["y_val"].append(flip_axis2 * obj.analysis_result[axis2])
            self.scatter_data[key_name]["z_val"].append(flip_axis3 * obj.analysis_result[axis3])
            self.scatter_data[key_name]["data"].append(obj)
            # group_hash[key_name]['text'].append(obj.object_name)
            # group_hash[key_name]['hoverinfo'].append(obj.id)

        # remove empty group
        if len(self.scatter_data["__default__"]["x_val"]) == 0:
            del self.scatter_data["__default__"]

        # assign color and symbol
        sc_idx = 0
        for key_name in self.scatter_data.keys():
            if self.scatter_data[key_name]["color"] == "":
                self.scatter_data[key_name]["color"] = color_candidate[sc_idx % len(color_candidate)]
                self.scatter_data[key_name]["symbol"] = symbol_candidate[sc_idx % len(symbol_candidate)]
                sc_idx += 1

        if self.rb2DChartDim.isChecked():
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
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    # print("key", key)
                    if key[0] == "_":
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax2.legend(values, keys, loc="upper right", bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax2.set_xlabel(axis1_title)
                self.ax2.set_ylabel(axis2_title)
            self.fig2.tight_layout()
            self.fig2.canvas.draw()
            self.fig2.canvas.flush_events()
            self.fig2.canvas.mpl_connect("pick_event", self.on_pick)
            self.fig2.canvas.mpl_connect("button_press_event", self.on_canvas_button_press)
            self.fig2.canvas.mpl_connect("button_release_event", self.on_canvas_button_release)
        else:
            self.ax3.clear()
            for name in self.scatter_data.keys():
                group = self.scatter_data[name]
                # print("name", name, "len(group_hash[name]['x_val'])", len(group['x_val']), group['symbol'])
                if len(self.scatter_data[name]["x_val"]) > 0:
                    self.scatter_result[name] = self.ax3.scatter(
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
                if name == "__selected__":
                    for idx, obj in enumerate(group["data"]):
                        self.ax3.text(group["x_val"][idx], group["y_val"][idx], group["z_val"][idx], obj.object_name)
                    # print("ret", ret)
            if show_legend:
                values = []
                keys = []
                for key in self.scatter_result.keys():
                    # print("key", key)
                    if key[0] == "_":
                        continue
                    else:
                        keys.append(key)
                        values.append(self.scatter_result[key])
                self.ax3.legend(values, keys, loc="upper left", bbox_to_anchor=(1.05, 1))
            # if show_legend:
            #    self.ax3.legend(self.scatter_result.values(), self.scatter_result.keys(), loc='upper left', bbox_to_anchor=(1.05, 1))
            if show_axis_label:
                self.ax3.set_xlabel(axis1_title)
                self.ax3.set_ylabel(axis2_title)
                self.ax3.set_zlabel(axis3_title)
            self.fig3.tight_layout()
            self.fig3.canvas.draw()
            self.fig3.canvas.flush_events()
            self.fig3.canvas.mpl_connect("pick_event", self.on_pick)
            self.fig3.canvas.mpl_connect("button_press_event", self.on_canvas_button_press)
            self.fig3.canvas.mpl_connect("button_release_event", self.on_canvas_button_release)

    def show_result_table(self):
        self.plot_data.clear()
        self.rotation_matrix_data.clear()

        # PCA data
        # set header as "PC1", "PC2", "PC3", ... "PCn
        if self.rbCVA.isChecked():
            header = ["CV" + str(i + 1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        else:
            header = ["PC" + str(i + 1) for i in range(len(self.analysis_result.rotated_matrix.tolist()[0]))]
        header.append("CSize")
        # print("header", header)
        self.plot_data.setColumnCount(len(header) + 1)
        self.plot_data.setHorizontalHeaderLabels(["Name"] + header)

        new_coords = self.analysis_result.rotated_matrix.tolist()
        self.plot_data.setColumnCount(len(new_coords[0]) + 2)
        for i, obj in enumerate(self.ds_ops.object_list):
            self.plot_data.insertRow(i)
            self.plot_data.setItem(i, 0, QTableWidgetItem(obj.object_name))
            for j, val in enumerate(new_coords[i]):
                self.plot_data.setItem(i, j + 1, QTableWidgetItem(str(int(val * 10000) / 10000.0)))
            mdobject = MdObject.get_by_id(obj.id)
            csize = mdobject.get_centroid_size(True)
            # print("obj:", mdobject.id, "csize:", csize)
            self.plot_data.setItem(i, len(new_coords[0]) + 1, QTableWidgetItem(str(int(csize * 10000) / 10000.0)))

        # rotation matrix
        rotation_matrix = self.analysis_result.rotation_matrix.tolist()
        # print("rotation_matrix[0][0]", [0][0], len(self.pca_result.rotation_matrix[0][0]))
        self.rotation_matrix_data.setColumnCount(len(rotation_matrix[0]))
        for i, row in enumerate(rotation_matrix):
            self.rotation_matrix_data.insertRow(i)
            for j, val in enumerate(row):
                self.rotation_matrix_data.setItem(i, j, QTableWidgetItem(str(int(val * 10000) / 10000.0)))

        # self.analysis_result.rotated_matrix

        # eigen values
        self.eigenvalue_data.setColumnCount(2)
        for i, val in enumerate(self.analysis_result.raw_eigen_values):
            val2 = self.analysis_result.eigen_value_percentages[i]
            self.eigenvalue_data.insertRow(i)
            self.eigenvalue_data.setItem(i, 0, QTableWidgetItem(str(int(val * 10000) / 10000.0)))
            self.eigenvalue_data.setItem(i, 1, QTableWidgetItem(str(int(val2 * 10000) / 10000.0)))

        # shapes tab
        min_vector = self.analysis_result.rotated_matrix.min(axis=0)
        max_vector = self.analysis_result.rotated_matrix.max(axis=0)
        avg_vector = self.analysis_result.rotated_matrix.mean(axis=0)
        # combine 3 vectors to 1 matrix
        np.vstack((min_vector, avg_vector, max_vector))
        self.shapes_data.clear()
        self.shapes_data.setColumnCount(len(new_coords[0]) + 1)
        self.comboAxis1.currentIndex()
        self.comboAxis2.currentIndex()
        self.comboAxis3.currentIndex()
        self.comboAxis1.currentText()
        self.comboAxis2.currentText()
        self.comboAxis3.currentText()
        -1.0 if self.cbxFlipAxis1.isChecked() else 1.0
        -1.0 if self.cbxFlipAxis2.isChecked() else 1.0
        -1.0 if self.cbxFlipAxis3.isChecked() else 1.0
        new_coords = self.analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(self.ds_ops.object_list):
            obj.analysis_result = new_coords[i]

        # print("shapes", shapes.shape)
        dimension = self.ds_ops.dimension
        vector_length = len(self.analysis_result.rotated_matrix.tolist()[0])
        if dimension == 2:
            axis_label = ["x", "y"]
        elif dimension == 3:
            axis_label = ["x", "y", "z"]

        column_header_list = ["name"]
        for i in range(vector_length):
            column_header_list.append(axis_label[i % dimension] + str(int(i / dimension) + 1))
        # column_header_list.append("CSize")

        """
        self.shapes_data.setHorizontalHeaderLabels(column_header_list)
        if self.rb2DChartDim.isChecked():
            dim = 2
            combination2 = [ "min", "avg", "max" ]
            shape_list = np.zeros((len(combination2)**dim,len(new_coords[0])))
            idx = 0
            for i1, m1 in enumerate(combination2):
                for i2, m2 in enumerate(combination2):
                    row_header_list.append(axis1_title + " " + m1 + " " + axis2_title + " " + m2)
                    row_idx1 = int(( i1 - 1 ) * flip_axis1 + 1)
                    row_idx2 = int(( i2 - 1 ) * flip_axis2 + 1)
                    #print("row_idx1", row_idx1, "row_idx2", row_idx2)
                    shape_list[idx,axis1] = flip_axis1 * shapes[ row_idx1, axis1]
                    shape_list[idx,axis2] = flip_axis2 * shapes[ row_idx2, axis2]
                    idx += 1

        elif self.rb3DChartDim.isChecked():
            dim = 3
            combination2 = [ "min", "avg", "max" ]
            shape_list = np.zeros((len(combination2)**dim,len(new_coords[0])))
            idx = 0
            for i1, m1 in enumerate(combination2):
                for i2, m2 in enumerate(combination2):
                    for i3, m3 in enumerate(combination2):
                        row_header_list.append(axis1_title + " " + m1 + " " + axis2_title + " " + m2 + axis3_title + " " + m3)
                        row_idx1 = int(( i1 - 1 ) * flip_axis1 + 1)
                        row_idx2 = int(( i2 - 1 ) * flip_axis2 + 1)
                        row_idx3 = int(( i3 - 1 ) * flip_axis3 + 1)
                        #print("row_idx1", row_idx1, "row_idx2", row_idx2, "row_idx3", row_idx3)

                        shape_list[idx,axis1] = flip_axis1 * shapes[ row_idx1, axis1]
                        shape_list[idx,axis2] = flip_axis2 * shapes[ row_idx2, axis2]
                        shape_list[idx,axis3] = flip_axis3 * shapes[ row_idx3, axis3]
                        idx += 1
        # add average shape to shape_list
        row_header_list.append("Average")
        average_shape = np.array(self.ds_ops.get_average_shape().landmark_list).reshape(1,-1)
        #print(average_shape)


        inverted_matrix = np.linalg.inv(self.analysis_result.rotation_matrix)
        #print("inverted_matrix", inverted_matrix)

        unrotated_shapes = np.dot(shape_list, inverted_matrix)
        unrotated_shapes += average_shape
        self.shape_list = unrotated_shapes
        self.shape_name_list = row_header_list
        self.shape_column_header_list = column_header_list

        for i, shape in enumerate(unrotated_shapes.tolist()):
            self.shapes_data.insertRow(i)
            self.shapes_data.setItem(i, 0, QTableWidgetItem(row_header_list[i]))
            for j, val in enumerate(shape):
                self.shapes_data.setItem(i, j+1, QTableWidgetItem(str(int(val*10000)/10000.0)))
        """

    def on_canvas_button_press(self, evt):
        # print("button_press", evt)
        self.canvas_down_xy = (evt.x, evt.y)
        # self.tableView.selectionModel().clearSelection()

    def on_canvas_button_release(self, evt):
        # print("button_release", evt)
        if self.onpick_happened:
            self.onpick_happened = False
            return
        self.canvas_up_xy = (evt.x, evt.y)
        if self.canvas_down_xy == self.canvas_up_xy:
            self.tableView1.selectionModel().clearSelection()

    def on_pick(self, evt):
        # print("onpick", evt)
        self.onpick_happened = True
        # print("evt", evt, evt.ind, evt.artist )
        selected_object_id_list = []
        for key_name in self.scatter_data.keys():
            if evt.artist == self.scatter_result[key_name]:
                # print("key_name", key_name)
                for idx in evt.ind:
                    obj = self.scatter_data[key_name]["data"][idx]
                    # print("obj", obj)
                    selected_object_id_list.append(obj.id)
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

    def on_mouse_clicked(self, event):
        # print("mouse clicked:",event)
        # if event.double():
        #    print("double clicked")
        # else:
        #    print("single clicked")
        p = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos())
        self.status_bar.showMessage("scene pos:" + str(event.scenePos()) + ", data pos:" + str(p))

    def on_mouse_moved(self, pos):
        p = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        # print("plot widget:",self.plot_widget, "plotItem:",self.plot_widget.plotItem, "vb:",self.plot_widget.plotItem.vb, "mapSceneToView:",self.plot_widget.plotItem.vb.mapSceneToView(pos))
        # print("pos:",pos, pos.x(), pos.y(), "p:",p, p.x(), p.y())

        self.status_bar.showMessage("x: %d, y: %d, x2: %f, y2: %f" % (pos.x(), pos.y(), p.x(), p.y()))

    def on_scatter_item_clicked(self, plot, points):
        # print("scatter item clicked:",plot,points)
        self.selected_object_id_list = []
        for pt in points:
            # print("points:",str(pt.data()))
            self.selected_object_id_list.append(pt.data().id)
        # select rows in tableView
        for obj_id in self.selected_object_id_list:
            for row in range(self.object_model.rowCount()):
                if int(self.object_model.item(row, 0).text()) == obj_id:
                    self.tableView1.selectRow(row)
                    # break

    def PerformCVA(self, dataset_ops):
        cva = MdCanonicalVariate()

        property_index = self.comboPropertyName.currentIndex() - 1
        # print("property_index:",property_index)
        if property_index < 0:
            QMessageBox.information(self, "Information", "Please select a property.")
            return
        datamatrix = []
        category_list = []
        # obj = dataset_ops.object_list[0]
        # print(obj, obj.variable_list, property_index)
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)
            category_list.append(obj.variable_list[property_index])

        cva.SetData(datamatrix)
        cva.SetCategory(category_list)
        cva.Analyze()

        min(cva.nObservation, cva.nVariable)

        return cva

    def PerformPCA(self, dataset_ops):
        pca = MdPrincipalComponent()
        datamatrix = []
        for obj in dataset_ops.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm)
            datamatrix.append(datum)

        pca.SetData(datamatrix)
        pca.Analyze()

        min(pca.nObservation, pca.nVariable)

        return pca

    def load_object(self):
        # load objects into tableView
        # for object in self.dataset.object_list:
        self.object_model.clear()
        self.property_model.clear()
        self.reset_tableView()
        if self.dataset is None:
            return
        # objects = self.selected_dataset.objects
        self.object_hash = {}

        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.propertyname = self.comboPropertyName.currentText()

        self.variable_list = []
        for obj in self.dataset.object_list:
            item0 = QStandardItem()
            item0.setCheckable(True)
            item0.setCheckState(Qt.Checked)
            item0.setData(obj.id, Qt.DisplayRole)

            item1 = QStandardItem()
            item1.setData(obj.id, Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            self.object_hash[obj.id] = item1
            if self.propertyname_index >= 0:
                obj.unpack_variable()
                # print(obj.variable_list)
                item3 = QStandardItem(obj.variable_list[self.propertyname_index])
                if obj.variable_list[self.propertyname_index] not in self.variable_list:
                    self.variable_list.append(obj.variable_list[self.propertyname_index])
                    p_item0 = QStandardItem()
                    p_item0.setCheckable(True)
                    p_item0.setCheckState(Qt.Checked)
                    p_item1 = QStandardItem()
                    p_item1.setCheckable(True)
                    p_item1.setCheckState(Qt.Checked)
                    self.property_model.appendRow(
                        [p_item0, p_item1, QStandardItem(obj.variable_list[self.propertyname_index])]
                    )
                # self.variable_list.append(obj.variable_list[self.propertyname_index])
                self.object_model.appendRow([item0, item1, item2, item3])
            else:
                self.object_model.appendRow([item0, item1, item2])

    def reset_tableView(self):
        self.property_model = QStandardItemModel()
        self.property_model.setColumnCount(3)
        self.property_model.setHorizontalHeaderLabels(["Show", "Avg", "Group"])
        self.tableView2.setModel(self.property_model)

        self.tableView2.setColumnWidth(0, 20)
        self.tableView2.setColumnWidth(1, 20)
        self.tableView2.setColumnWidth(1, 100)
        header2 = self.tableView2.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Fixed)
        header2.setSectionResizeMode(1, QHeaderView.Fixed)
        header2.setSectionResizeMode(2, QHeaderView.Stretch)

        self.object_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.propertyname_index = self.comboPropertyName.currentIndex() - 1
        self.propertyname = self.comboPropertyName.currentText()
        self.object_model.setColumnCount(3)
        self.object_model.setHorizontalHeaderLabels(["", "ID", "Name"])
        self.tableView1.setModel(self.proxy_model)
        # self.tableView.setModel(self.object_model)
        self.tableView1.setColumnWidth(0, 20)
        self.tableView1.setColumnWidth(1, 50)
        self.tableView1.setColumnWidth(2, 150)
        self.tableView1.verticalHeader().setDefaultSectionSize(20)
        self.tableView1.verticalHeader().setVisible(False)
        self.tableView1.setSelectionBehavior(QTableView.SelectRows)
        # self.tableView.clicked.connect(self.on_tableView_clicked)
        self.object_selection_model = self.tableView1.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.sortByColumn(0, Qt.AscendingOrder)
        self.object_model.setSortRole(Qt.UserRole)

        header = self.tableView1.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header2 = self.tableView2.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Fixed)
        header2.setSectionResizeMode(1, QHeaderView.Fixed)
        header2.setSectionResizeMode(2, QHeaderView.Stretch)

        if self.propertyname_index >= 0:
            self.object_model.setColumnCount(4)
            self.object_model.setHorizontalHeaderLabels(["", "ID", "Name", self.propertyname])
            self.tableView1.setColumnWidth(3, 150)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            self.property_model.setHorizontalHeaderLabels(["Show", "Avg", self.propertyname])

        self.tableView1.setStyleSheet(
            "QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};"
        )

    def on_object_selection_changed(self, selected, deselected):
        if self.selection_changed_off:
            pass
        else:
            self.selected_object_id_list = self.get_selected_object_id_list()
            self.show_analysis_result()
            self.ds_ops.selected_object_id_list = self.selected_object_id_list
            self.show_object_shape()

    def get_selected_object_id_list(self):
        selected_indexes = self.tableView1.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return []

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, "mapToSource"):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list

        selected_object_id_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            selected_object_id_list.append(object_id)

        return selected_object_id_list


