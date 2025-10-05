"""Object Dialog for managing individual objects and their landmarks.

This module provides the ObjectDialog class for creating, editing, and viewing
morphometric objects with their associated landmarks and metadata.
"""

import copy
import logging
import os
from pathlib import Path

import numpy as np
from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSlot
from PyQt5.QtGui import (
    QFont,
    QIntValidator,
    QKeySequence,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from components.widgets import PicButton
from dialogs.calibration_dialog import CalibrationDialog
from MdConstants import ICONS as ICON
from MdModel import MdDataset, MdObject, MdObjectOps
from ModanComponents import ObjectViewer2D, ObjectViewer3D

logger = logging.getLogger(__name__)

# Mode constants used by ObjectDialog
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


class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Object Information"))
        self.parent = parent
        # print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        # self.move(self.parent.pos()+QPoint(50,50))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.status_bar = QStatusBar()
        self.landmark_list = []

        # Missing landmark estimation support
        self.original_landmark_list = []
        self.estimated_landmark_list = None
        self._aligned_mean_cache = None
        self.show_estimated = True

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        # self.vsplitter.addWidget(self.tableView)
        # self.vsplitter.addWidget(self.tableWidget)

        # self.hsplitter.addWidget(self.treeView)
        # self.hsplitter.addWidget(self.vsplitter)

        # Create two-row layout for coordinate input
        self.inputWidget = QWidget()
        self.inputMainLayout = QVBoxLayout()
        self.inputWidget.setLayout(self.inputMainLayout)
        self.inputMainLayout.setContentsMargins(0, 0, 0, 0)
        self.inputMainLayout.setSpacing(2)

        # First row: coordinate inputs
        self.inputCoordsLayout = QHBoxLayout()
        self.inputX = QLineEdit()
        self.inputY = QLineEdit()
        self.inputZ = QLineEdit()
        self.inputX.setPlaceholderText("X")
        self.inputY.setPlaceholderText("Y")
        self.inputZ.setPlaceholderText("Z")

        self.inputCoordsLayout.addWidget(self.inputX)
        self.inputCoordsLayout.addWidget(self.inputY)
        self.inputCoordsLayout.addWidget(self.inputZ)

        # Second row: buttons
        self.inputButtonLayout = QHBoxLayout()
        self.btnAddInput = QPushButton()
        self.btnAddInput.setText(self.tr("Add"))
        self.btnUpdateInput = QPushButton()
        self.btnUpdateInput.setText(self.tr("Update"))
        self.btnUpdateInput.setEnabled(False)
        self.btnDeleteInput = QPushButton()
        self.btnDeleteInput.setText(self.tr("Delete"))
        self.btnDeleteInput.setEnabled(False)

        self.inputButtonLayout.addWidget(self.btnAddInput)
        self.inputButtonLayout.addWidget(self.btnUpdateInput)
        self.inputButtonLayout.addWidget(self.btnDeleteInput)

        self.inputMainLayout.addLayout(self.inputCoordsLayout)
        self.inputMainLayout.addLayout(self.inputButtonLayout)

        # Keep track of selected landmark
        self.selected_landmark_index = -1

        self.inputX.returnPressed.connect(self.input_coords_process)
        self.inputY.returnPressed.connect(self.input_coords_process)
        self.inputZ.returnPressed.connect(self.input_coords_process)
        self.inputX.textChanged[str].connect(self.x_changed)
        self.btnAddInput.clicked.connect(self.btnAddInput_clicked)
        self.btnUpdateInput.clicked.connect(self.btnUpdateInput_clicked)
        self.btnDeleteInput.clicked.connect(self.btnDeleteInput_clicked)

        self.edtObjectName = QLineEdit()
        self.edtSequence = QLineEdit()
        self.edtSequence.setValidator(QIntValidator())
        self.edtObjectDesc = QTextEdit()
        self.edtObjectDesc.setMaximumHeight(100)
        self.edtLandmarkStr = QTableWidget()
        self.lblDataset = QLabel()

        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.object_view = None

        self.object_view_3d = ObjectViewer3D(self)
        self.object_view_3d.setMinimumWidth(300)
        self.object_view_3d.setMinimumHeight(300)
        self.object_view_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.object_view_3d.object_dialog = self
        self.object_view_3d.setMouseTracking(True)
        self.object_view_3d.show_index = True  # Enable landmark index display in ObjectDialog

        self.object_view_2d = ObjectViewer2D(self)
        self.object_view_2d.object_dialog = self
        self.object_view_2d.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.image_label.clicked.connect(self.on_image_clicked)

        self.pixmap = QPixmap(1024, 768)
        self.object_view_2d.setPixmap(self.pixmap)

        self.form_layout = QFormLayout()
        self.lblDatasetName = QLabel(self.tr("Dataset Name"))
        self.lblObjectName = QLabel(self.tr("Object Name"))
        self.lblSequence = QLabel(self.tr("Sequence"))
        self.lblObjectDesc = QLabel(self.tr("Description"))
        self.lblLandmarkStr = QLabel(self.tr("Landmarks"))
        self.form_layout.addRow(self.lblDatasetName, self.lblDataset)
        self.form_layout.addRow(self.lblObjectName, self.edtObjectName)
        self.form_layout.addRow(self.lblSequence, self.edtSequence)
        self.form_layout.addRow(self.lblObjectDesc, self.edtObjectDesc)
        self.form_layout.addRow(self.lblLandmarkStr, self.edtLandmarkStr)
        self.form_layout.addRow("", self.inputWidget)

        self.btnGroup = QButtonGroup()
        self.btnLandmark = PicButton(
            QPixmap(ICON["landmark"]),
            QPixmap(ICON["landmark_hover"]),
            QPixmap(ICON["landmark_down"]),
            QPixmap(ICON["landmark_disabled"]),
        )
        self.btnWireframe = PicButton(
            QPixmap(ICON["wireframe"]), QPixmap(ICON["wireframe_hover"]), QPixmap(ICON["wireframe_down"])
        )
        self.btnCalibration = PicButton(
            QPixmap(ICON["calibration"]),
            QPixmap(ICON["calibration_hover"]),
            QPixmap(ICON["calibration_down"]),
            QPixmap(ICON["calibration_disabled"]),
        )
        self.btnGroup.addButton(self.btnLandmark)
        self.btnGroup.addButton(self.btnWireframe)
        self.btnGroup.addButton(self.btnCalibration)
        self.btnLandmark.setCheckable(True)
        self.btnWireframe.setCheckable(True)
        self.btnCalibration.setCheckable(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setChecked(False)
        self.btnLandmark.setAutoExclusive(True)
        self.btnWireframe.setAutoExclusive(True)
        self.btnCalibration.setAutoExclusive(True)
        self.btnLandmark.clicked.connect(self.btnLandmark_clicked)
        self.btnWireframe.clicked.connect(self.btnWireframe_clicked)
        self.btnCalibration.clicked.connect(self.btnCalibration_clicked)
        BUTTON_SIZE = 48
        self.btnLandmark.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btnWireframe.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btnCalibration.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btn_layout2 = QGridLayout()
        self.btn_layout2.addWidget(self.btnLandmark, 0, 0)
        self.btn_layout2.addWidget(self.btnWireframe, 0, 1)
        self.btn_layout2.addWidget(self.btnCalibration, 1, 0)

        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText(self.tr("Index"))
        self.cbxShowIndex.setChecked(True)
        self.cbxShowWireframe = QCheckBox()
        self.cbxShowWireframe.setText(self.tr("Wireframe"))
        self.cbxShowWireframe.setChecked(True)
        self.cbxShowPolygon = QCheckBox()
        self.cbxShowPolygon.setText(self.tr("Polygon"))
        self.cbxShowPolygon.setChecked(True)
        self.cbxShowEstimated = QCheckBox()
        self.cbxShowEstimated.setText(self.tr("Show Estimated"))
        self.cbxShowEstimated.setChecked(True)
        self.cbxShowEstimated.stateChanged.connect(self.toggle_estimation)
        self.cbxShowBaseline = QCheckBox()
        self.cbxShowBaseline.setText(self.tr("Baseline"))
        self.cbxShowBaseline.setChecked(True)
        self.cbxShowBaseline.hide()
        self.cbxAutoRotate = QCheckBox()
        self.cbxAutoRotate.setText(self.tr("Rotate"))
        self.cbxAutoRotate.setChecked(False)
        self.cbxShowModel = QCheckBox()
        self.cbxShowModel.setText(self.tr("3D Model"))
        self.cbxShowModel.setChecked(False)
        self.btnAddFile = QPushButton()
        self.btnAddFile.setText(self.tr("Load Image"))
        self.btnAddFile.clicked.connect(self.btnAddFile_clicked)

        # self.btnFBO = QPushButton()
        # self.btnFBO.setText("FBO")
        # self.btnFBO.clicked.connect(self.btnFBO_clicked)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.form_layout)

        self.right_top_widget = QWidget()
        self.right_top_widget.setLayout(self.btn_layout2)
        self.right_middle_widget = QWidget()
        self.right_middle_layout = QVBoxLayout()
        self.right_middle_layout.addWidget(self.cbxShowIndex)
        self.right_middle_layout.addWidget(self.cbxShowWireframe)
        self.right_middle_layout.addWidget(self.cbxShowPolygon)
        self.right_middle_layout.addWidget(self.cbxShowEstimated)
        self.right_middle_layout.addWidget(self.cbxShowBaseline)
        self.right_middle_layout.addWidget(self.cbxShowModel)
        self.right_middle_layout.addWidget(self.cbxAutoRotate)
        self.right_middle_layout.addWidget(self.btnAddFile)
        self.btnAddMissing = QPushButton()
        self.btnAddMissing.setText(self.tr("Add Missing"))
        self.btnAddMissing.clicked.connect(self.btnAddMissing_clicked)
        self.right_middle_layout.addWidget(self.btnAddMissing)
        # self.right_middle_layout.addWidget(self.btnFBO)
        self.right_middle_widget.setLayout(self.right_middle_layout)
        self.right_bottom_widget = QWidget()
        self.vsplitter.addWidget(self.right_top_widget)
        self.vsplitter.addWidget(self.right_middle_widget)
        self.vsplitter.addWidget(self.right_bottom_widget)
        self.vsplitter.setSizes([50, 50, 400])
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 0)
        self.vsplitter.setStretchFactor(2, 1)

        self.object_view_layout = QVBoxLayout()
        self.object_view_layout.addWidget(self.object_view_2d)
        self.object_view_layout.addWidget(self.object_view_3d)
        self.object_view_widget = QWidget()
        self.object_view_widget.setLayout(self.object_view_layout)

        self.hsplitter.addWidget(self.left_widget)
        self.hsplitter.addWidget(self.object_view_widget)
        # self.hsplitter.addWidget(self.object_view_3d)
        self.hsplitter.addWidget(self.vsplitter)
        # self.hsplitter.addWidget(self.right_widget)
        self.hsplitter.setSizes([200, 800, 100])
        self.hsplitter.setStretchFactor(0, 0)
        self.hsplitter.setStretchFactor(1, 1)
        self.hsplitter.setStretchFactor(2, 0)

        self.btnPrevious = QPushButton()
        self.btnPrevious.setText(self.tr("Previous"))
        self.btnPrevious.clicked.connect(self.Previous)
        self.btnNext = QPushButton()
        self.btnNext.setText(self.tr("Next"))
        self.btnNext.clicked.connect(self.Next)

        self.btnOkay = QPushButton()
        self.btnOkay.setText(self.tr("Save"))
        self.btnOkay.clicked.connect(self.Okay)
        self.btnDelete = QPushButton()
        self.btnDelete.setText(self.tr("Delete"))
        self.btnDelete.clicked.connect(self.Delete)
        self.btnCancel = QPushButton()
        self.btnCancel.setText(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnPrevious)
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnNext)

        self.status_bar.setMaximumHeight(20)
        # self.main_layout.addLayout(self.sub_layout)
        self.main_layout.addWidget(self.hsplitter)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.status_bar)

        self.dataset = None
        self.object = None
        self.edtPropertyList = []
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.cbxShowIndex.stateChanged.connect(self.show_index_state_changed)
        self.cbxShowWireframe.stateChanged.connect(self.show_wireframe_state_changed)
        self.cbxShowPolygon.stateChanged.connect(self.show_polygon_state_changed)
        self.cbxShowBaseline.stateChanged.connect(self.show_baseline_state_changed)
        self.cbxAutoRotate.stateChanged.connect(self.auto_rotate_state_changed)
        self.cbxShowModel.stateChanged.connect(self.show_model_state_changed)
        self.object_deleted = False

        # self.show_index_state_changed()

    def read_settings(self):
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ObjectDialog", QRect(100, 100, 1400, 800)))
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))
            self.move(self.parent.pos() + QPoint(100, 100))

    def write_settings(self):
        if self.remember_geometry is True:
            self.m_app.settings.setValue("WindowGeometry/ObjectDialog", self.geometry())

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def btnAddFile_clicked(self):
        # open file dialog
        # print("btnAddFile_clicked")
        if self.dataset is None:
            return
        # print("btnAddFile_clicked")

        if self.dataset.dimension == 2:
            extension = " ".join(["*." + x for x in mu.IMAGE_EXTENSION_LIST])
            file_path, _ = QFileDialog.getOpenFileName(
                self, self.tr("Open File"), mu.USER_PROFILE_DIRECTORY, "Image Files (" + extension + ")"
            )
            if file_path == "":
                return
            self.object_view.set_image(file_path)
            self.object_view.calculate_resize()
            self.set_object_name(Path(file_path).stem)
            self.enable_landmark_edit()

        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, self.tr("Open File"), mu.USER_PROFILE_DIRECTORY, "3D Files (*.obj *.stl *.ply)"
            )
            if file_path == "":
                return
            # print("file_path 1:", file_path)
            file_path = mu.process_3d_file(file_path)
            # print("file_path 2:", file_path)

            self.object_view.set_threed_model(file_path)
            self.object_view.calculate_resize()
            self.set_object_name(Path(file_path).stem)
            self.enable_landmark_edit()

    def set_object_calibration(self, pixels, calibration_length, calibration_unit):
        self.object.pixels_per_mm = pixels * 1.0 / calibration_length
        if calibration_unit == "mm":
            self.object.pixels_per_mm /= 1.0
        elif calibration_unit == "cm":
            self.object.pixels_per_mm /= 10.0
        elif calibration_unit == "m":
            self.object.pixels_per_mm /= 1000.0
        elif calibration_unit == "um":
            self.object.pixels_per_mm /= 0.001
        elif calibration_unit == "nm":
            self.object.pixels_per_mm /= 0.000001
        self.object_view_2d.pixels_per_mm = self.object.pixels_per_mm
        # print(pixels, calibration_length, calibration_unit, self.object.pixels_per_mm)
        # self.object.save()

    # def btnFBO_clicked(self):
    #    self.object_view_3d.show_picker_buffer()

    def btnAddMissing_clicked(self):
        """Add a missing landmark placeholder to the current object"""
        if self.dataset is None:
            return

        if self.dataset.dimension == 2:
            self.landmark_list.append([None, None])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([None, None, None])

        self.show_landmarks()

        # Update the viewers
        if self.object_view_2d:
            self.object_view_2d.landmark_list = self.landmark_list
            self.object_view_2d.update()
        if self.object_view_3d:
            self.object_view_3d.landmark_list = self.landmark_list
            self.object_view_3d.update()

    def show_index_state_changed(self):
        self.object_view.show_index = self.cbxShowIndex.isChecked()
        self.object_view.update()

    def show_model_state_changed(self, int):
        self.object_view.show_model = self.cbxShowModel.isChecked()
        self.object_view.update()

    def show_baseline_state_changed(self, int):
        self.object_view.show_baseline = self.cbxShowBaseline.isChecked()
        self.object_view.update()

    def auto_rotate_state_changed(self, int):
        self.object_view.auto_rotate = self.cbxAutoRotate.isChecked()

    def show_wireframe_state_changed(self, int):
        self.object_view.show_wireframe = self.cbxShowWireframe.isChecked()
        self.object_view.update()

    def toggle_estimation(self, state):
        """Toggle display of estimated missing landmarks"""
        self.show_estimated = state == Qt.Checked

        # Re-process the current object to update estimation
        if self.object is not None:
            self.set_object(self.object)
            self.show_landmarks()
            self.object_view.update()

    def show_polygon_state_changed(self, int):
        self.object_view.show_polygon = self.cbxShowPolygon.isChecked()
        self.object_view.update()

    def btnLandmark_clicked(self):
        # self.edit_mode = MODE_ADD_LANDMARK
        # if self.object.image.count() == 0:
        #    return
        self.object_view.set_mode(MODE["EDIT_LANDMARK"])
        self.object_view.update()
        self.btnLandmark.setDown(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)

    def btnCalibration_clicked(self):
        # self.edit_mode = MODE_ADD_LANDMARK
        self.object_view.set_mode(MODE["CALIBRATION"])
        self.object_view.update()
        self.btnCalibration.setDown(True)
        self.btnCalibration.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)

    def calibrate(self, dist):
        logger = logging.getLogger(__name__)
        logger.debug(f"calibrate start - edit_mode: {self.object_view.edit_mode}, CALIBRATION: {MODE['CALIBRATION']}")
        self.calibrate_dlg = CalibrationDialog(self, dist)
        logger.debug(f"calibrate dialog created - edit_mode: {self.object_view.edit_mode}")
        self.calibrate_dlg.setModal(True)
        logger.debug(f"calibrate before exec - edit_mode: {self.object_view.edit_mode}")
        self.calibrate_dlg.exec_()
        logger.debug(f"calibrate after exec - edit_mode: {self.object_view.edit_mode}")

    def btnWireframe_clicked(self):
        # self.edit_mode = MODE_ADD_LANDMARK
        self.object_view.set_mode(MODE["WIREFRAME"])
        self.object_view.update()
        self.btnWireframe.setDown(True)
        self.btnWireframe.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)

    def set_object_name(self, name):
        # print("set_object_name", self.edtObjectName.text(), name)

        if self.edtObjectName.text() == "":
            self.edtObjectName.setText(name)

    def compute_aligned_mean(self):
        """Compute aligned mean shape from complete specimens.

        Returns:
            MdObjectOps with average shape, or None if insufficient data
        """
        if self._aligned_mean_cache is not None:
            return self._aligned_mean_cache

        if self.dataset is None:
            return None

        # Collect complete objects (no missing landmarks)
        complete_objects = []
        for obj in self.dataset.object_list:
            obj.unpack_landmark()
            has_missing = any(lm[0] is None or lm[1] is None for lm in obj.landmark_list)
            if not has_missing:
                complete_objects.append(obj)

        if len(complete_objects) < 2:
            return None

        # Create temporary MdDatasetOps for Procrustes
        from MdModel import MdDatasetOps

        temp_dataset = MdDataset()
        temp_dataset.dimension = self.dataset.dimension
        temp_dataset.id = self.dataset.id

        temp_ds_ops = MdDatasetOps(temp_dataset)
        temp_ds_ops.object_list = [MdObjectOps(obj) for obj in complete_objects]
        temp_ds_ops.dimension = self.dataset.dimension

        # Run Procrustes (no missing landmarks, should be fast)
        if not temp_ds_ops.procrustes_superimposition():
            return None

        # Get average shape
        self._aligned_mean_cache = temp_ds_ops.get_average_shape()
        return self._aligned_mean_cache

    def estimate_missing_for_object(self, obj):
        """Estimate missing landmarks for given object using aligned mean shape.

        The mean shape is computed from Procrustes-aligned complete specimens,
        then transformed to match the scale and position of the current object.

        Args:
            obj: MdObject with potential missing landmarks

        Returns:
            List of landmarks with missing values estimated, or original if estimation fails
        """
        import logging

        logger = logging.getLogger(__name__)

        if obj is None:
            return []

        obj.unpack_landmark()

        # Check if there are missing landmarks
        has_missing = any(lm[0] is None or lm[1] is None for lm in obj.landmark_list)

        if not has_missing:
            return obj.landmark_list

        # Get aligned mean shape (Procrustes-normalized, unit size)
        mean_shape = self.compute_aligned_mean()
        if mean_shape is None:
            # Cannot estimate, return original
            logger.warning("Cannot compute aligned mean - insufficient complete specimens")
            return obj.landmark_list

        # Extract valid (non-missing) landmarks from current object
        valid_indices = []
        current_valid = []
        mean_valid = []

        for lm_idx in range(len(obj.landmark_list)):
            lm = obj.landmark_list[lm_idx]
            if lm[0] is not None and lm[1] is not None:
                valid_indices.append(lm_idx)
                current_valid.append([lm[0], lm[1]])
                if lm_idx < len(mean_shape.landmark_list):
                    mean_lm = mean_shape.landmark_list[lm_idx]
                    if mean_lm[0] is not None and mean_lm[1] is not None:
                        mean_valid.append([mean_lm[0], mean_lm[1]])

        if len(valid_indices) < 2:
            logger.warning(f"Not enough valid landmarks to estimate scale/position ({len(valid_indices)} found)")
            return obj.landmark_list

        # Calculate transformation: mean shape → current object
        current_valid = np.array(current_valid)
        mean_valid = np.array(mean_valid)

        # Compute centroids
        current_centroid = np.mean(current_valid, axis=0)
        mean_centroid = np.mean(mean_valid, axis=0)

        # Compute centroid sizes (scale)
        current_centered = current_valid - current_centroid
        mean_centered = mean_valid - mean_centroid

        current_size = np.sqrt(np.sum(current_centered**2))
        mean_size = np.sqrt(np.sum(mean_centered**2))

        scale_factor = current_size / mean_size if mean_size > 0 else 1.0

        logger.info(f"Transformation: scale={scale_factor:.4f}, centroid_shift={current_centroid - mean_centroid}")

        # Create result with estimated missing landmarks
        import copy

        result_landmarks = copy.deepcopy(obj.landmark_list)
        imputed_count = 0

        for lm_idx in range(len(result_landmarks)):
            lm = result_landmarks[lm_idx]
            if lm[0] is None or lm[1] is None:
                # Get mean shape landmark
                if lm_idx < len(mean_shape.landmark_list):
                    mean_lm = mean_shape.landmark_list[lm_idx]
                    if mean_lm[0] is not None and mean_lm[1] is not None:
                        # Transform: (mean_lm - mean_centroid) * scale + current_centroid
                        mean_point = np.array([mean_lm[0], mean_lm[1]])
                        transformed = (mean_point - mean_centroid) * scale_factor + current_centroid

                        result_landmarks[lm_idx] = [float(transformed[0]), float(transformed[1])]
                        imputed_count += 1

        logger.info(f"Imputed {imputed_count} missing landmarks for object {obj.object_name}")
        return result_landmarks

    def set_dataset(self, dataset):
        # print("object dialog set_dataset", dataset.dataset_name)
        if dataset is None:
            self.dataset = None
            self.lblDataset.setText("No dataset selected")
            return
        self.dataset = dataset
        self.lblDataset.setText(dataset.dataset_name)

        # Invalidate cache when dataset changes
        self._aligned_mean_cache = None

        header = self.edtLandmarkStr.horizontalHeader()
        if self.dataset.dimension == 2:
            self.edtLandmarkStr.setColumnCount(2)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X", "Y"])
            # self.edtLandmarkStr.setColumnWidth(0, 80)
            # self.edtLandmarkStr.setColumnWidth(1, 80)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            self.cbxAutoRotate.hide()
            self.cbxShowModel.hide()
            # self.btnCalibration.show()
            self.inputZ.hide()
            self.object_view_3d.hide()
            self.object_view = self.object_view_2d
        elif self.dataset.dimension == 3:
            self.edtLandmarkStr.setColumnCount(3)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X", "Y", "Z"])
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            self.cbxAutoRotate.show()
            self.cbxShowModel.show()
            # self.btnCalibration.hide()
            self.inputZ.show()
            self.object_view_2d.hide()
            self.object_view = self.object_view_3d
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.edtPropertyList = []
            self.dataset.unpack_variablename_str()
            for variablename in self.dataset.variablename_list:
                self.edtPropertyList.append(QLineEdit())
                self.form_layout.addRow(variablename, self.edtPropertyList[-1])
        # self.inputX.setFixedWidth(input_width)
        # self.inputY.setFixedWidth(input_width)
        # self.inputZ.setFixedWidth(input_width)
        # self.btnAddInput.setFixedWidth(input_width)

    def set_object(self, object):
        # print("set_object", object.object_name, object.dataset.dimension)
        if object is not None:
            self.object = object
            self.edtObjectName.setText(object.object_name)
            self.edtSequence.setText(str(object.sequence or 1))
            self.edtObjectDesc.setText(object.object_desc)
            # self.edtLandmarkStr.setText(object.landmark_str)
            object.unpack_landmark()

            # Store original landmark list
            self.original_landmark_list = copy.deepcopy(object.landmark_list)

            # Check if object has missing landmarks
            has_missing = any(lm[0] is None or lm[1] is None for lm in object.landmark_list)

            # Estimate missing landmarks if needed and enabled
            if has_missing and self.show_estimated:
                self.estimated_landmark_list = self.estimate_missing_for_object(object)
            else:
                self.estimated_landmark_list = None

            # Always use original for table display (keep "MISSING" text)
            # Estimated values are only used for visualization in viewer
            self.landmark_list = self.original_landmark_list
            # Use object's dataset if self.dataset is None
            dataset_to_use = self.dataset if self.dataset is not None else object.dataset
            if dataset_to_use is not None:
                self.edge_list = dataset_to_use.unpack_wireframe()
            else:
                self.edge_list = []
            # for lm in self.landmark_list:
            #    self.show_landmark(*lm)
            # self.show_landmarks()

        # Use object's dataset if self.dataset is None
        dataset_to_use = self.dataset if self.dataset is not None else (object.dataset if object is not None else None)
        if dataset_to_use is not None and dataset_to_use.dimension == 3:
            # print("set_object 3d 1")
            self.object_view = self.object_view_3d
            self.object_view.auto_rotate = False
            # obj_ops = MdObjectOps(object)
            # self.object_view.set_dataset(object.dataset)
            # self.btnLandmark.setDisabled(True)
            # print("set_object 3d 2")
            self.btnCalibration.setDisabled(True)
            self.cbxAutoRotate.show()
            self.cbxShowModel.show()
            self.cbxShowPolygon.show()
            # self.cbxShowModel.setEnabled(True)
            self.btnAddFile.setText(self.tr("Load 3D Model"))
            # print("set_object 3d 3")
            if object is not None:
                # print("object dialog self.landmark_list in set object 3d", self.landmark_list)
                self.object_view.set_object(object)
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()
                if object.threed_model is not None and len(object.threed_model) > 0:
                    self.enable_landmark_edit()
                    # self.cbxShowModel.show()
                    self.cbxShowModel.setEnabled(True)
                    self.cbxShowModel.setChecked(True)
                else:
                    self.disable_landmark_edit()
                    self.cbxShowModel.setEnabled(False)
                # self.object_view.landmark_list = self.landmark_list
        else:
            # print("set_object 2d")
            self.object_view = self.object_view_2d
            self.cbxAutoRotate.hide()
            self.cbxShowModel.hide()
            self.cbxShowPolygon.hide()
            # self.cbxShowModel.setEnabled(True)
            self.btnAddFile.setText(self.tr("Load Image"))

            if object is not None:
                if object.image is not None and len(object.image) > 0:
                    # img = object.image[0]
                    # image_path = img.get_file_path(self.m_app.storage_directory)
                    ##check if image_path exists
                    # if os.path.exists(image_path):
                    #    self.object_view.set_image(image_path)
                    self.btnCalibration.setEnabled(True)
                    self.enable_landmark_edit()
                    if object.pixels_per_mm is None:
                        self.btnCalibration_clicked()
                        # self.btnCalibration.setDisabled(False)
                else:
                    self.btnCalibration.setDisabled(True)
                    self.disable_landmark_edit()
                # elif len(self.landmark_list) > 0:
                # print("objectdialog self.landmark_list in set object 2d", self.landmark_list)
                self.object_view.clear_object()
                self.object_view.set_object(object)
                self.object_view.image_changed = False
                self.object_view.landmark_list = self.landmark_list
                self.object_view.update_landmark_list()
                self.object_view.calculate_resize()

        if len(self.dataset.variablename_list) > 0:
            self.object.unpack_variable()
            self.dataset.unpack_variablename_str()
            for idx, _propertyname in enumerate(self.dataset.variablename_list):
                if idx < len(object.variable_list):
                    self.edtPropertyList[idx].setText(object.variable_list[idx])

            # self.object_view_3d.landmark_list = self.landmark_list
        # self.set_dataset(object.dataset)
        self.show_index_state_changed()
        self.object_view.align_object()
        self.show_landmarks()

    def enable_landmark_edit(self):
        self.btnLandmark.setEnabled(True)
        self.btnLandmark.setDown(True)
        self.object_view.set_mode(MODE["EDIT_LANDMARK"])

    def disable_landmark_edit(self):
        self.btnLandmark.setDisabled(True)
        self.btnLandmark.setDown(False)
        self.object_view.set_mode(MODE["VIEW"])

    @pyqtSlot(str)
    def x_changed(self, text):
        # if text is multiline and tab separated, add to table
        # print("x_changed called with", text)

        # Update button states based on whether we're in selection mode
        if self.selected_landmark_index >= 0:
            self.btnUpdateInput.setEnabled(True)
            self.btnAddInput.setEnabled(False)
        else:
            self.btnUpdateInput.setEnabled(False)
            self.btnAddInput.setEnabled(True)
        if "\n" in text:
            lines = text.split("\n")
            for line in lines:
                # print(line)
                if "\t" in line:
                    coords = line.split("\t")
                    # add landmarks using add_landmark method
                    if self.dataset.dimension == 2 and len(coords) == 2:
                        self.add_landmark(coords[0], coords[1])
                    elif self.dataset.dimension == 3 and len(coords) == 3:
                        self.add_landmark(coords[0], coords[1], coords[2])
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")

    def update_landmark(self, idx, x, y, z=None):
        if self.dataset.dimension == 2:
            self.landmark_list[idx] = [x, y]
        elif self.dataset.dimension == 3:
            self.landmark_list[idx] = [x, y, z]
        self.show_landmarks()

    def add_landmark(self, x, y, z=None):
        # print("adding landmark", x, y, z, self.landmark_list)
        if self.dataset.dimension == 2:
            self.landmark_list.append([float(x), float(y)])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([float(x), float(y), float(z)])
        self.show_landmarks()
        # self.object_view.calculate_resize()

    def delete_landmark(self, idx):
        # print("delete_landmark", idx)
        self.landmark_list.pop(idx)
        self.show_landmarks()

    def on_landmark_selected(self):
        """Handle landmark selection in table"""
        selected_items = self.edtLandmarkStr.selectedItems()
        if selected_items:
            row = self.edtLandmarkStr.row(selected_items[0])
            self.selected_landmark_index = row

            # Load coordinates into input fields
            if row < len(self.landmark_list):
                lm = self.landmark_list[row]

                # X coordinate
                if lm[0] is None:
                    self.inputX.setText("")
                else:
                    self.inputX.setText(str(lm[0]))

                # Y coordinate
                if lm[1] is None:
                    self.inputY.setText("")
                else:
                    self.inputY.setText(str(lm[1]))

                # Z coordinate
                if self.dataset.dimension == 3 and len(lm) > 2:
                    if lm[2] is None:
                        self.inputZ.setText("")
                    else:
                        self.inputZ.setText(str(lm[2]))

                # Enable update and delete buttons
                self.btnUpdateInput.setEnabled(True)
                self.btnDeleteInput.setEnabled(True)
                self.btnAddInput.setEnabled(False)
        else:
            self.selected_landmark_index = -1
            self.btnUpdateInput.setEnabled(False)
            self.btnDeleteInput.setEnabled(False)
            self.btnAddInput.setEnabled(True)

    def btnAddInput_clicked(self):
        """Handle Add button click"""
        self.input_coords_process()

    def btnUpdateInput_clicked(self):
        """Handle Update button click"""
        if self.selected_landmark_index >= 0:
            x_str = self.inputX.text()
            y_str = self.inputY.text()
            z_str = self.inputZ.text()

            if x_str == "" or y_str == "":
                # Update to missing landmark
                self.update_landmark(
                    self.selected_landmark_index, None, None, None if self.dataset.dimension == 3 else None
                )
            else:
                if self.dataset.dimension == 2:
                    self.update_landmark(self.selected_landmark_index, float(x_str), float(y_str))
                elif self.dataset.dimension == 3:
                    if z_str == "":
                        z_str = "0"
                    self.update_landmark(self.selected_landmark_index, float(x_str), float(y_str), float(z_str))

            # Clear selection after update
            self.edtLandmarkStr.clearSelection()
            self.selected_landmark_index = -1
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")
            self.btnUpdateInput.setEnabled(False)
            self.btnDeleteInput.setEnabled(False)
            self.btnAddInput.setEnabled(True)

            self.object_view.update_landmark_list()
            self.object_view.calculate_resize()

    def btnDeleteInput_clicked(self):
        """Handle Delete button click"""
        if self.selected_landmark_index >= 0:
            self.delete_landmark(self.selected_landmark_index)

            # Clear selection after delete
            self.edtLandmarkStr.clearSelection()
            self.selected_landmark_index = -1
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")
            self.btnUpdateInput.setEnabled(False)
            self.btnDeleteInput.setEnabled(False)
            self.btnAddInput.setEnabled(True)

            self.object_view.update_landmark_list()
            self.object_view.calculate_resize()

    def input_coords_process(self):
        """Process coordinate input for Add action"""
        if self.selected_landmark_index >= 0:
            # If a landmark is selected, act as Update
            self.btnUpdateInput_clicked()
            return

        x_str = self.inputX.text()
        y_str = self.inputY.text()
        z_str = self.inputZ.text()
        if self.dataset.dimension == 2:
            if x_str == "" or y_str == "":
                return
            # add landmark to table using add_landmark method
            self.add_landmark(x_str, y_str)

        elif self.dataset.dimension == 3:
            if x_str == "" or y_str == "" or z_str == "":
                return
            self.add_landmark(x_str, y_str, z_str)
        self.inputX.setText("")
        self.inputY.setText("")
        self.inputZ.setText("")
        self.inputX.setFocus()
        self.object_view.update_landmark_list()
        self.object_view.calculate_resize()

    def show_landmarks(self):
        # Configure table
        self.edtLandmarkStr.setRowCount(len(self.landmark_list))
        self.edtLandmarkStr.setSelectionBehavior(QTableWidget.SelectRows)
        self.edtLandmarkStr.setSelectionMode(QTableWidget.SingleSelection)

        # Connect selection handler
        try:
            self.edtLandmarkStr.itemSelectionChanged.disconnect()
        except TypeError:
            # No connections exist yet
            pass
        self.edtLandmarkStr.itemSelectionChanged.connect(self.on_landmark_selected)

        for idx, lm in enumerate(self.landmark_list):
            # print(idx, lm)

            # Handle X coordinate
            if lm[0] is None:
                item_x = QTableWidgetItem("MISSING")
                item_x.setForeground(Qt.red)
                font = QFont()
                font.setBold(True)
                item_x.setFont(font)
            else:
                item_x = QTableWidgetItem(str(float(lm[0]) * 1.0))
            item_x.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 0, item_x)

            # Handle Y coordinate
            if lm[1] is None:
                item_y = QTableWidgetItem("MISSING")
                item_y.setForeground(Qt.red)
                font = QFont()
                font.setBold(True)
                item_y.setFont(font)
            else:
                item_y = QTableWidgetItem(str(float(lm[1]) * 1.0))
            item_y.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.edtLandmarkStr.setItem(idx, 1, item_y)

            # Handle Z coordinate for 3D
            if self.dataset.dimension == 3:
                if len(lm) > 2 and lm[2] is not None:
                    item_z = QTableWidgetItem(str(float(lm[2]) * 1.0))
                else:
                    item_z = QTableWidgetItem("MISSING")
                    item_z.setForeground(Qt.red)
                    font = QFont()
                    font.setBold(True)
                    item_z.setFont(font)
                item_z.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.edtLandmarkStr.setItem(idx, 2, item_z)

    def save_object(self):
        # print("save object")

        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.sequence = int(self.edtSequence.text())
        self.object.object_desc = self.edtObjectDesc.toPlainText()
        # self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.landmark_str = self.make_landmark_str()
        # print("scale:", self.object.pixels_per_mm)
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            self.object.property_str = ",".join([edt.text() for edt in self.edtPropertyList])

        self.object.save()
        # print("object_view_2d.fullpath in save_object:", self.object_view_2d.fullpath, "has image", self.object.has_image(), "image changed", self.object_view_2d.image_changed)
        if self.object_view_2d.fullpath is not None:
            if not self.object.has_image():
                img = self.object.add_image(self.object_view_2d.fullpath)
                img.save()
            elif self.object_view_2d.image_changed is True:
                img = self.object.update_image(self.object_view_2d.fullpath)
                img.save()
            # print("img:", img)

        elif self.object_view_3d.fullpath is not None and not self.object.has_threed_model():
            mdl = self.object.add_threed_model(self.object_view_3d.fullpath)
            mdl.save()

    def make_landmark_str(self):
        # from table, make landmark_str
        # Modified to handle MISSING values - store as "Missing" text
        landmark_str = ""
        for row in range(self.edtLandmarkStr.rowCount()):
            for col in range(self.edtLandmarkStr.columnCount()):
                cell_text = self.edtLandmarkStr.item(row, col).text()
                # Keep "MISSING" as "Missing" for storage
                if cell_text == "MISSING":
                    landmark_str += "Missing"
                else:
                    landmark_str += cell_text
                if col < self.edtLandmarkStr.columnCount() - 1:
                    landmark_str += "\t"
            if row < self.edtLandmarkStr.rowCount() - 1:
                landmark_str += "\n"
        return landmark_str

    def set_tableview(self, tableview):
        self.tableView = tableview

    def Delete(self):
        ret = QMessageBox.question(
            self, "", self.tr("Are you sure to delete this object?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            if self.object.image.count() > 0:
                image_path = self.object.image[0].get_file_path(self.m_app.storage_directory)
                if os.path.exists(image_path):
                    os.remove(image_path)
            self.object.delete_instance()
        # self.delete_dataset()
        self.object_deleted = True
        self.accept()

    def get_selected_object_list(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, "mapToSource"):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list

        selected_object_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            selected_object_list.append(object)

        return selected_object_list

    def Previous(self):
        # get all items from tableView
        model = self.tableView.model()
        object_id_list = []
        proxy_index_list = []
        for row in range(model.rowCount()):
            proxy_index = self.tableView.model().index(row, 0)
            proxy_index_list.append(proxy_index)
            index = self.tableView.model().mapToSource(proxy_index)

            object_id = self.parent.object_model._data[index.row()][0]["value"]
            object_id = int(object_id)
            object_id_list.append(object_id)

        new_index = -1
        if object_id_list.index(self.object.id) > 0:
            new_index = object_id_list.index(self.object.id) - 1
            new_object_id = object_id_list[new_index]
            new_object = MdObject.get_by_id(new_object_id)

        if new_index >= 0:
            # enable or disable prev and next button
            if new_index == 0:
                self.btnPrevious.setEnabled(False)
            else:
                self.btnPrevious.setEnabled(True)
            if new_index == len(object_id_list) - 1:
                self.btnNext.setEnabled(False)
            else:
                self.btnNext.setEnabled(True)

            self.save_object()
            self.set_object(new_object)
            # select new object in tableView
            new_proxy_index = proxy_index_list[new_index]
            # new_index = self.object_model.indexFromId(new_object_id)
            self.tableView.selectRow(new_proxy_index.row())

            # self.accept()

    def Next(self):
        # get all items from tableView
        model = self.tableView.model()
        object_id_list = []
        proxy_index_list = []
        for row in range(model.rowCount()):
            proxy_index = self.tableView.model().index(row, 0)
            proxy_index_list.append(proxy_index)
            index = self.tableView.model().mapToSource(proxy_index)

            object_id = self.parent.object_model._data[index.row()][0]["value"]
            object_id = int(object_id)
            object_id_list.append(object_id)

        new_index = -1
        if object_id_list.index(self.object.id) < len(object_id_list) - 1:
            new_index = object_id_list.index(self.object.id) + 1
            new_object_id = object_id_list[new_index]
            new_object = MdObject.get_by_id(new_object_id)

        if new_index >= 0:
            # enable or disable prev and next button
            if new_index == 0:
                self.btnPrevious.setEnabled(False)
            else:
                self.btnPrevious.setEnabled(True)
            if new_index == len(object_id_list) - 1:
                self.btnNext.setEnabled(False)
            else:
                self.btnNext.setEnabled(True)

            self.save_object()
            self.set_object(new_object)
            new_proxy_index = proxy_index_list[new_index]
            # new_index = self.object_model.indexFromId(new_object_id)
            self.tableView.selectRow(new_proxy_index.row())
            # self.accept()

    def Okay(self):
        self.save_object()
        self.object_deleted = False
        self.accept()

    def Cancel(self):
        self.reject()

    def resizeEvent(self, event):
        # print("Window has been resized",self.image_label.width(), self.image_label.height())
        # self.pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        # self.edtObjectDesc.resize(self.edtObjectDesc.height(),300)
        # self.image_label.setPixmap(self.pixmap)
        QDialog.resizeEvent(self, event)
