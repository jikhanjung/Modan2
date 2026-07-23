"""Object Dialog for managing individual objects and their landmarks.

This module provides the ObjectDialog class for creating, editing, and viewing
morphometric objects with their associated landmarks and metadata.
"""

import copy
import logging
from pathlib import Path

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
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

import MdUtils as mu
from components.widgets import PicButton
from dialogs.calibration_dialog import CalibrationDialog
from MdConstants import ICONS as ICON
from MdHelpers import guard_slot
from MdModel import MdDataset, MdObject, MdObjectOps, impute_missing_landmarks
from ModanComponents import ObjectViewer2D, ObjectViewer3D

logger = logging.getLogger(__name__)

# Mode constants used by ObjectDialog
from MdConstants import MODE

# Marker shown in the landmark table for a coordinate that has no value. Also the
# literal a user may type to mark one missing by hand.
MISSING_TEXT = "MISSING"


class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(self.tr("Modan2 - Object Information"))
        self.parent = parent
        # print(self.parent.pos())
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        # Controller for DB/file persistence (delegated out of the dialog). Falls
        # back to a standalone controller when constructed without a real parent
        # window (e.g. tests using a Mock parent), so persistence still targets the
        # active database. isinstance guards against Mock parents whose .controller
        # auto-creates a truthy Mock attribute.
        from ModanController import ModanController

        parent_controller = getattr(parent, "controller", None)
        self.controller = parent_controller if isinstance(parent_controller, ModanController) else ModanController()
        self.read_settings()
        # self.move(self.parent.pos()+QPoint(50,50))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.status_bar = QStatusBar()
        self.landmark_list = []
        # Semi-landmark curves are edited in memory and written to the database
        # only on Save (like the landmarks). curve_config is the dataset-wide
        # scheme [{id, n, method, start}]; curve_raw_map is this object's raw
        # traces {id: [[x, y], ...]}. This dialog is their single source of truth
        # while open, so the viewer reads them from here (avoids a stale copy on a
        # separately-fetched dataset instance).
        self.curve_config = []
        self.curve_raw_map = {}
        # Sparse click anchors for edge-snapped curves {id: [[x, y], ...]}. Only
        # present for snap-traced curves; editing an anchor re-snaps to rebuild
        # the dense curve_raw_map entry. Hand-traced curves have no anchors and
        # are edited point-by-point directly.
        self.curve_anchor_map = {}
        self._orig_curve_config = []
        self._orig_curve_raw = {}
        self._orig_curve_anchor = {}
        # Snapshot of the full savable state (name/sequence/desc/landmarks/
        # variables/curves) taken once the object is loaded, so Cancel can detect
        # any unsaved edit, not just curve edits.
        self._saved_snapshot = None
        # Set while show_landmarks() repopulates the table, so the cell validator
        # ignores the itemChanged storm that causes.
        self._populating_landmark_table = False

        # Missing landmark estimation support
        self.original_landmark_list = []
        self.estimated_landmark_list = None
        self._aligned_mean_cache = None
        self.show_estimated = True
        # Expected positions of not-yet-placed landmarks on a new specimen.
        self.expected_landmark_list = None
        self.show_expected = False
        self._expected_reference_cache = None

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        # self.vsplitter.addWidget(self.tableView)
        # self.vsplitter.addWidget(self.tableWidget)

        # self.hsplitter.addWidget(self.treeView)
        # self.hsplitter.addWidget(self.vsplitter)

        self._init_coord_input()

        self.edtObjectName = QLineEdit()
        self.edtSequence = QLineEdit()
        self.edtSequence.setValidator(QIntValidator())
        self.edtObjectDesc = QTextEdit()
        self.edtObjectDesc.setMaximumHeight(100)
        self.edtLandmarkStr = QTableWidget()
        # Semi-landmark curves for this object: id, editable name, traced
        # start/end point, and the dataset-wide semi-landmark count N (editable).
        self.curveTable = QTableWidget()
        self.curveTable.setColumnCount(3)
        self.curveTable.setHorizontalHeaderLabels([self.tr("Name"), self.tr("N"), self.tr("Traced")])
        # Name takes the free space; N and Traced only as wide as their contents.
        _curve_header = self.curveTable.horizontalHeader()
        _curve_header.setSectionResizeMode(0, QHeaderView.Stretch)
        _curve_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        _curve_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.curveTable.setMaximumHeight(150)
        self._populating_curve_table = False
        self.curveTable.itemChanged.connect(self.on_curve_cell_changed)
        self.curveTable.itemSelectionChanged.connect(self.on_curve_selected)
        self.curveTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.curveTable.customContextMenuRequested.connect(self.on_curve_table_context_menu)
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
        self.lblCurves = QLabel(self.tr("Curves"))
        self.form_layout.addRow(self.lblDatasetName, self.lblDataset)
        self.form_layout.addRow(self.lblObjectName, self.edtObjectName)
        self.form_layout.addRow(self.lblSequence, self.edtSequence)
        self.form_layout.addRow(self.lblObjectDesc, self.edtObjectDesc)
        self.form_layout.addRow(self.lblLandmarkStr, self.edtLandmarkStr)
        # Landmark coordinate input + Add/Update/Delete sit between the landmark
        # and curve tables.
        self.form_layout.addRow("", self.inputWidget)
        self.form_layout.addRow(self.lblCurves, self.curveTable)

        self._init_tool_buttons()

        self._init_option_checkboxes()

        # self.btnFBO = QPushButton()
        # self.btnFBO.setText("FBO")
        # self.btnFBO.clicked.connect(self.btnFBO_clicked)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.form_layout)

        self.right_top_widget = QWidget()
        self.right_top_widget.setLayout(self.btn_layout2)
        self.right_middle_widget = QWidget()
        self.right_middle_layout = QVBoxLayout()
        label_mode_layout = QHBoxLayout()
        label_mode_layout.addWidget(self.cbxShowIndex)
        label_mode_layout.addWidget(self.rbShowIndex)
        label_mode_layout.addWidget(self.rbShowName)
        label_mode_layout.addStretch()
        self.right_middle_layout.addLayout(label_mode_layout)
        self.right_middle_layout.addWidget(self.cbxShowWireframe)
        self.right_middle_layout.addWidget(self.cbxShowPolygon)
        self.right_middle_layout.addWidget(self.cbxShowEstimated)
        self.right_middle_layout.addWidget(self.cbxShowExpected)
        self.right_middle_layout.addWidget(self.cbxShowBaseline)
        self.right_middle_layout.addWidget(self.cbxShowModel)
        self.right_middle_layout.addWidget(self.cbxShowCurve)
        self.right_middle_layout.addWidget(self.cbxShowSemiLandmark)
        self.right_middle_layout.addWidget(self.cbxSnapToCurve)
        self.right_middle_layout.addWidget(self.cbxSmoothCurve)
        self.right_middle_layout.addWidget(self.cbxAutoRotate)
        self.right_middle_layout.addWidget(self.btnAddFile)
        self.right_middle_layout.addWidget(self.cbxUseOriginal)
        self.btnAddMissing = QPushButton()
        self.btnAddMissing.setText(self.tr("Add Missing"))
        self.btnAddMissing.clicked.connect(self.btnAddMissing_clicked)
        self.right_middle_layout.addWidget(self.btnAddMissing)
        self.right_middle_layout.addWidget(self.btnEditLandmarkNames)
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

        self._init_action_buttons()

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
        self.cbxShowCurve.stateChanged.connect(self.show_curve_state_changed)
        self.cbxShowSemiLandmark.stateChanged.connect(self.show_semi_landmark_state_changed)
        self.object_deleted = False

        # self.show_index_state_changed()

    def _init_coord_input(self):
        """Build the two-row coordinate-input panel (X/Y/Z + Add/Update/Delete)."""
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

    def _init_tool_buttons(self):
        """Build the landmark / wireframe / calibration exclusive tool-button group."""
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
        # Curve (semi-landmark) tracing. No dedicated icon yet, so a short text
        # button; it joins the same exclusive group as the other tools.
        self.btnCurve = QPushButton(self.tr("Curve"))
        self.btnCurve.setToolTip(self.tr("Trace a curve (semi-landmarks)"))
        # Flat by default so its background matches the flat icon tool buttons; a
        # subtle fill shows when it is the active tool.
        self.btnCurve.setFlat(True)
        self.btnCurve.setStyleSheet(
            "QPushButton { border: none; background: transparent; }"
            "QPushButton:hover { background: #e6f3ff; border: 1px solid #3399ff; border-radius: 4px; }"
            "QPushButton:checked { background: #cce6ff; border: 1px solid #3399ff; border-radius: 4px; }"
        )
        self.btnGroup.addButton(self.btnLandmark)
        self.btnGroup.addButton(self.btnWireframe)
        self.btnGroup.addButton(self.btnCalibration)
        self.btnGroup.addButton(self.btnCurve)
        # Exclusive group: exactly one of landmark/wireframe/calibration is always
        # selected (clicking the active one can't deselect it), and Landmark is the
        # default below.
        self.btnGroup.setExclusive(True)
        self.btnLandmark.setCheckable(True)
        self.btnWireframe.setCheckable(True)
        self.btnCalibration.setCheckable(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setChecked(False)
        self.btnCurve.setCheckable(True)
        self.btnCurve.setChecked(False)
        self.btnLandmark.setAutoExclusive(True)
        self.btnWireframe.setAutoExclusive(True)
        self.btnCalibration.setAutoExclusive(True)
        self.btnCurve.setAutoExclusive(True)
        self.btnLandmark.clicked.connect(self.btnLandmark_clicked)
        self.btnWireframe.clicked.connect(self.btnWireframe_clicked)
        self.btnCalibration.clicked.connect(self.btnCalibration_clicked)
        self.btnCurve.clicked.connect(self.btnCurve_clicked)
        BUTTON_SIZE = 48
        self.btnLandmark.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btnWireframe.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btnCalibration.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btnCurve.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.btn_layout2 = QGridLayout()
        self.btn_layout2.addWidget(self.btnLandmark, 0, 0)
        self.btn_layout2.addWidget(self.btnWireframe, 0, 1)
        self.btn_layout2.addWidget(self.btnCalibration, 1, 0)
        self.btn_layout2.addWidget(self.btnCurve, 1, 1)

    def _init_option_checkboxes(self):
        """Build the view-option checkboxes (index/wireframe/polygon/estimated/…)
        and the Load-Image button."""
        # "Show" toggles landmark labels; the Index/Name radios pick which label.
        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText(self.tr("Show"))
        self.cbxShowIndex.setChecked(True)
        self.rbShowIndex = QRadioButton(self.tr("Index"))
        self.rbShowIndex.setChecked(True)
        self.rbShowName = QRadioButton(self.tr("Name"))
        self.labelModeGroup = QButtonGroup(self)
        self.labelModeGroup.addButton(self.rbShowIndex)
        self.labelModeGroup.addButton(self.rbShowName)
        self.rbShowName.toggled.connect(self.show_name_state_changed)
        # Opens the dataset-wide landmark name/description editor.
        self.btnEditLandmarkNames = QPushButton(self.tr("Landmark Names"))
        self.btnEditLandmarkNames.clicked.connect(self.btnEditLandmarkNames_clicked)
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
        # 2D digitizing aid: once a few landmarks are placed on a new specimen,
        # show where the remaining ones are expected (mean shape fitted onto the
        # placed landmarks), drawn like estimated/missing landmarks.
        self.cbxShowExpected = QCheckBox()
        self.cbxShowExpected.setText(self.tr("Show Expected"))
        self.cbxShowExpected.setChecked(False)
        self.cbxShowExpected.stateChanged.connect(self.show_expected_state_changed)
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
        # Show the raw traced curves and/or the derived semi-landmarks. Both are
        # display-only (merge-at-analysis model); toggling neither stores nor
        # loses anything.
        self.cbxShowCurve = QCheckBox()
        self.cbxShowCurve.setText(self.tr("Curve"))
        self.cbxShowCurve.setChecked(True)
        self.cbxShowSemiLandmark = QCheckBox()
        self.cbxShowSemiLandmark.setText(self.tr("Semi-LM"))
        self.cbxShowSemiLandmark.setChecked(True)
        # Snap curve tracing to the strongest image edge (live-wire auto-detect).
        # Only meaningful while tracing, so it is enabled just in curve mode. On
        # by default -- entering curve mode applies this state to the viewer.
        self.cbxSnapToCurve = QCheckBox()
        self.cbxSnapToCurve.setText(self.tr("Snap to curve"))
        self.cbxSnapToCurve.setToolTip(self.tr("Snap curve tracing to image edges (live-wire)"))
        self.cbxSnapToCurve.setChecked(True)
        self.cbxSnapToCurve.setEnabled(False)
        self.cbxSnapToCurve.stateChanged.connect(self.snap_to_curve_state_changed)
        # Smooth the snapped trace (drop the pixel staircase) before it becomes
        # semi-landmarks. Like snapping, only meaningful/enabled in curve mode.
        self.cbxSmoothCurve = QCheckBox()
        self.cbxSmoothCurve.setText(self.tr("Smooth curve"))
        self.cbxSmoothCurve.setToolTip(self.tr("Smooth the traced curve (keeps the clicked anchors)"))
        self.cbxSmoothCurve.setChecked(True)
        self.cbxSmoothCurve.setEnabled(False)
        self.cbxSmoothCurve.stateChanged.connect(self.smooth_curve_state_changed)
        self.btnAddFile = QPushButton()
        self.btnAddFile.setText(self.tr("Load Image"))
        self.btnAddFile.clicked.connect(self.btnAddFile_clicked)
        # Shown only when the attached image has an archived pristine original
        # (oversized attachments are stored as a downscaled working copy).
        # Checking it renders the viewer from the original for extra detail
        # while digitizing; coordinates stay in working-copy pixels.
        self.cbxUseOriginal = QCheckBox()
        self.cbxUseOriginal.setText(self.tr("Show Original"))
        self.cbxUseOriginal.setChecked(False)
        self.cbxUseOriginal.stateChanged.connect(self.cbxUseOriginal_state_changed)
        self.cbxUseOriginal.hide()

    def _init_action_buttons(self):
        """Build the Previous/Save/Delete/Cancel/Next row and assemble the main layout."""
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

    @guard_slot("Failed to load file")
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

    def _update_missing_button_text(self):
        """Say which of the two things the button will do.

        The action depends on whether a row is selected, and "Add Missing" reads
        as append-only — so the label follows the selection instead of leaving
        the insert behaviour undiscoverable.
        """
        if 0 <= self.selected_landmark_index < len(self.landmark_list):
            self.btnAddMissing.setText(self.tr("Insert Missing"))
            self.btnAddMissing.setToolTip(self.tr("Insert a missing landmark before the selected row"))
        else:
            self.btnAddMissing.setText(self.tr("Add Missing"))
            self.btnAddMissing.setToolTip(self.tr("Append a missing landmark (select a row to insert instead)"))

    @guard_slot("Failed to add missing landmark")
    def btnAddMissing_clicked(self):
        """Insert a missing-landmark placeholder at the selected row.

        Landmark identity is positional — landmark 3 of a file is row 3 here — so
        a placeholder is only useful if it can go *where* the gap is. Inserts
        before the selected row (spreadsheet convention, so the new row takes the
        selected row's number) and appends when nothing is selected.
        """
        if self.dataset is None:
            return

        blank = [None] * (3 if self.dataset.dimension == 3 else 2)

        index = self.selected_landmark_index
        if 0 <= index < len(self.landmark_list):
            self.landmark_list.insert(index, blank)
        else:
            self.landmark_list.append(blank)
            index = len(self.landmark_list) - 1

        self.show_landmarks()
        self._refresh_landmark_views()

        # Keep the new row selected: consecutive clicks then stack placeholders
        # in order rather than walking backwards through the list.
        self.selected_landmark_index = index
        self.edtLandmarkStr.selectRow(index)
        # selectRow is a no-op signal-wise when that row was already selected, so
        # the coordinate inputs would keep showing the *previous* landmark's
        # values — and Update would then write them into the new blank row. Sync
        # them explicitly.
        self.on_landmark_selected()

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

    def show_curve_state_changed(self, int):
        self.object_view.show_curve = self.cbxShowCurve.isChecked()
        self.object_view.update()

    def show_semi_landmark_state_changed(self, int):
        self.object_view.show_semi_landmark = self.cbxShowSemiLandmark.isChecked()
        self.object_view.update()

    def toggle_estimation(self, state):
        """Toggle display of estimated missing landmarks"""
        self.show_estimated = state == Qt.Checked

        # Re-process the current object to update estimation
        if self.object is not None:
            self.set_object(self.object)
            self.show_landmarks()
            self.object_view.update()

    def show_name_state_changed(self, checked):
        """Label mode radio: draw the landmark name (checked) or the index."""
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.show_landmark_name = checked
        if self.object_view is not None:
            self.object_view.update()

    def btnEditLandmarkNames_clicked(self):
        """Open the dataset-wide landmark name/description editor."""
        from dialogs.landmark_name_dialog import LandmarkNameDialog

        dialog = LandmarkNameDialog(self, self.dataset, len(self.landmark_list))
        if dialog.exec_() and self.object_view is not None:
            self.object_view.update()

    def show_expected_state_changed(self, state):
        """Toggle the expected-landmark digitizing aid (2D)."""
        self.show_expected = state == Qt.Checked
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.show_expected = self.show_expected
        self.update_expected_landmarks()
        if self.object_view is not None:
            self.object_view.update()

    def update_expected_landmarks(self):
        """Estimate where the not-yet-placed landmarks are expected to go.

        Once at least two landmarks are placed on a new (incomplete) 2D specimen,
        fit the dataset mean shape onto them and take the remaining positions from
        the fitted mean -- the same imputation used for missing landmarks. Result
        is a full-length list; the viewer draws only the entries beyond the placed
        ones. ``None`` when the aid is off or cannot be computed.
        """
        self.expected_landmark_list = None
        if not self.show_expected or self.dataset is None or self.dataset.dimension != 2:
            return
        placed = [lm for lm in self.landmark_list if lm and lm[0] is not None and lm[1] is not None]
        if len(placed) < 2:
            return
        reference = self._expected_reference()
        if reference is None or len(placed) >= len(reference.landmark_list):
            return
        padded = [list(p) for p in placed] + [[None, None]] * (len(reference.landmark_list) - len(placed))
        self.expected_landmark_list = impute_missing_landmarks(padded, reference.landmark_list)

    def show_polygon_state_changed(self, int):
        self.object_view.show_polygon = self.cbxShowPolygon.isChecked()
        self.object_view.update()

    def cbxUseOriginal_state_changed(self, state):
        """Render the 2D image from the archived full-resolution original.

        Display only: the working copy stays the landmark coordinate space, so
        this just gives the viewer more detail to resample from while
        digitizing.
        """
        if self.object is None or self.object.image.count() == 0:
            return
        if state == Qt.Checked:
            storage_dir = getattr(self.m_app, "storage_directory", mu.DEFAULT_STORAGE_DIRECTORY)
            self.object_view_2d.set_fullres_source(self.object.image[0].get_original_file_path(storage_dir))
        else:
            self.object_view_2d.set_fullres_source(None)

    def _set_snap_available(self, available):
        """Enable the Snap/Smooth curve checkboxes only in curve mode; apply state.

        Both are only used while tracing, so they are greyed out in the other
        modes. Entering curve mode pushes their current state to the viewer so
        re-entering restores the last choice.
        """
        if not hasattr(self, "cbxSnapToCurve"):
            return
        self.cbxSnapToCurve.setEnabled(available)
        self.cbxSmoothCurve.setEnabled(available)
        if available:
            self._apply_snap()
            self._apply_smooth()

    def _apply_snap(self):
        """Forward the Snap checkbox state to the 2D viewer's live-wire."""
        if hasattr(self.object_view, "set_livewire_enabled"):
            self.object_view.set_livewire_enabled(self.cbxSnapToCurve.isChecked())

    def _apply_smooth(self):
        """Forward the Smooth checkbox state to the 2D viewer."""
        if hasattr(self.object_view, "set_smooth_curves"):
            self.object_view.set_smooth_curves(self.cbxSmoothCurve.isChecked())

    def snap_to_curve_state_changed(self, _state):
        self._apply_snap()

    def smooth_curve_state_changed(self, _state):
        self._apply_smooth()

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
        self.btnCurve.setDown(False)
        self.btnCurve.setChecked(False)
        self._set_snap_available(False)

    def btnCurve_clicked(self):
        # Entering trace mode: no curve selected, so a new curve is drawn.
        self.object_view.selected_curve_id = None
        self.object_view.set_mode(MODE["EDIT_CURVE"])
        self.object_view.update()
        self.btnCurve.setDown(True)
        self.btnCurve.setChecked(True)
        self.btnLandmark.setDown(False)
        self.btnLandmark.setChecked(False)
        self.btnWireframe.setDown(False)
        self.btnWireframe.setChecked(False)
        self.btnCalibration.setDown(False)
        self.btnCalibration.setChecked(False)
        self._set_snap_available(True)

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
        self.btnCurve.setDown(False)
        self.btnCurve.setChecked(False)
        self._set_snap_available(False)

    def calibrate(self, dist):
        logger = logging.getLogger(__name__)
        logger.debug(f"calibrate start - edit_mode: {self.object_view.edit_mode}, CALIBRATION: {MODE['CALIBRATION']}")
        self.calibrate_dlg = CalibrationDialog(self, dist)
        logger.debug(f"calibrate dialog created - edit_mode: {self.object_view.edit_mode}")
        self.calibrate_dlg.setModal(True)
        logger.debug(f"calibrate before exec - edit_mode: {self.object_view.edit_mode}")
        result = self.calibrate_dlg.exec_()
        logger.debug(f"calibrate after exec - edit_mode: {self.object_view.edit_mode}")
        # After a confirmed calibration, drop straight into landmark input mode so
        # the user can start digitizing without an extra click.
        if result == QDialog.Accepted:
            self.btnLandmark_clicked()

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
        self.btnCurve.setDown(False)
        self.btnCurve.setChecked(False)
        self._set_snap_available(False)

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

        # One shared implementation with Procrustes imputation: fit the mean
        # onto the observed landmarks (rotation + scale + translation) and take
        # the gaps from the fitted mean. Without the rotation term, a specimen
        # photographed at an angle got its estimates rotated away from the
        # right spot.
        # The mean shape carries its own dimensionality, so no dataset lookup.
        return impute_missing_landmarks(obj.landmark_list, mean_shape.landmark_list)

    def _expected_reference(self):
        """Mean shape of the dataset's longest complete specimens (other than the
        current one), used to predict landmarks the current specimen does not yet
        have. Its length is the maximum landmark count, so it can carry a
        landmark (e.g. a new 7th) that shorter specimens lack. None if there is
        no usable reference.
        """
        if getattr(self, "_expected_reference_cache", None) is not None:
            return self._expected_reference_cache
        if self.dataset is None:
            return None

        candidates = []
        max_count = 0
        for obj in self.dataset.object_list:
            if self.object is not None and getattr(obj, "id", None) == getattr(self.object, "id", None):
                continue  # skip the specimen being digitized
            obj.unpack_landmark()
            if not obj.landmark_list or any(lm[0] is None or lm[1] is None for lm in obj.landmark_list):
                continue
            count = len(obj.landmark_list)
            if count > max_count:
                max_count, candidates = count, [obj]
            elif count == max_count:
                candidates.append(obj)

        if not candidates or max_count == 0:
            return None

        from MdModel import MdDatasetOps

        temp_dataset = MdDataset()
        temp_dataset.dimension = self.dataset.dimension
        temp_dataset.id = self.dataset.id
        temp_ds_ops = MdDatasetOps(temp_dataset)
        temp_ds_ops.object_list = [MdObjectOps(obj) for obj in candidates]
        temp_ds_ops.dimension = self.dataset.dimension
        if not temp_ds_ops.procrustes_superimposition():
            return None
        self._expected_reference_cache = temp_ds_ops.get_average_shape()
        return self._expected_reference_cache

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
            # Load the curve scheme (dataset) and this object's raw traces into the
            # dialog's working copies; snapshot them to detect unsaved edits.
            self.curve_config = self.dataset.get_curve_config() if self.dataset is not None else []
            self.curve_raw_map = object.get_curve_raw()
            self.curve_anchor_map = object.get_curve_anchors()
            self._orig_curve_config = copy.deepcopy(self.curve_config)
            self._orig_curve_raw = copy.deepcopy(self.curve_raw_map)
            self._orig_curve_anchor = copy.deepcopy(self.curve_anchor_map)
            self.show_curves()
            # Expected-landmark digitizing aid (2D): mirror the flag onto the
            # viewers and recompute for this object (reference excludes it).
            self._expected_reference_cache = None
            for view in (self.object_view_2d, self.object_view_3d):
                if view is not None:
                    view.show_expected = self.show_expected
            self.update_expected_landmarks()
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
            self.cbxUseOriginal.hide()
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
                # Offer "Show Original" only when this image has an archived
                # pristine original. Reset to the working copy on every object
                # switch (set_image drops the full-res source anyway).
                has_original = (
                    object.image is not None
                    and len(object.image) > 0
                    and object.image[0].has_archived_original(
                        getattr(self.m_app, "storage_directory", mu.DEFAULT_STORAGE_DIRECTORY)
                    )
                )
                self.cbxUseOriginal.setChecked(False)
                self.cbxUseOriginal.setVisible(has_original)
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
        # Baseline for Cancel's unsaved-change check (table + property fields are
        # now populated).
        self._saved_snapshot = self._snapshot_state()

    def enable_landmark_edit(self):
        self.btnLandmark.setEnabled(True)
        self.btnLandmark.setDown(True)
        self.object_view.set_mode(MODE["EDIT_LANDMARK"])

    def disable_landmark_edit(self):
        self.btnLandmark.setDisabled(True)
        self.btnLandmark.setDown(False)
        self.object_view.set_mode(MODE["VIEW"])

    @pyqtSlot(str)
    @guard_slot("Failed to parse pasted landmarks")
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
                    # add landmarks using add_landmark method; skip non-numeric rows
                    # (e.g. a pasted header line) rather than aborting the whole paste.
                    try:
                        if self.dataset.dimension == 2 and len(coords) == 2:
                            self.add_landmark(coords[0], coords[1])
                        elif self.dataset.dimension == 3 and len(coords) == 3:
                            self.add_landmark(coords[0], coords[1], coords[2])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping unparseable landmark line '{line}': {e}")
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")

    def update_landmark(self, idx, x, y, z=None):
        if self.dataset.dimension == 2:
            self.landmark_list[idx] = [x, y]
        elif self.dataset.dimension == 3:
            self.landmark_list[idx] = [x, y, z]
        self.show_landmarks()
        self._refresh_expected()

    def add_landmark(self, x, y, z=None):
        # print("adding landmark", x, y, z, self.landmark_list)
        if self.dataset.dimension == 2:
            self.landmark_list.append([float(x), float(y)])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([float(x), float(y), float(z)])
        self.show_landmarks()
        self._refresh_expected()
        # self.object_view.calculate_resize()

    def delete_landmark(self, idx):
        # print("delete_landmark", idx)
        self.landmark_list.pop(idx)
        self.show_landmarks()
        self._refresh_expected()

    def _refresh_expected(self):
        """Recompute the expected landmarks and repaint (no-op when the aid is off)."""
        if not self.show_expected:
            return
        self.update_expected_landmarks()
        if self.object_view is not None:
            self.object_view.update()

    def finish_curve(self, raw_points, anchors=None):
        """Store a traced curve as its raw polyline (plus snap anchors, if any).

        Merge-at-analysis model: the semi-landmarks are NOT written into the
        landmark list. Only the raw trace is kept on the object; the dataset's
        curve scheme says how many semi-landmarks it resamples to, and display
        and analysis derive them on demand. The trace fills the next un-traced
        curve in the dataset scheme, in order. 2D only (the 2D viewer traces).

        ``anchors`` are the sparse points the user clicked when edge-snapping;
        stored so the curve can later be edited by its clicks and re-snapped.
        ``None`` (hand-traced) leaves the raw points themselves editable.
        """
        if raw_points is None or len(raw_points) < 2:
            return
        config = self.curve_config
        # Fill the next un-traced curve in the scheme; if every defined curve is
        # already traced (or none are defined), grow the scheme by one curve.
        # Held in memory until Save; N defaults to the previous curve's (editable
        # in the table).
        target = next((c for c in config if c.get("id") not in self.curve_raw_map), None)
        if target is None:
            # A brand-new curve: ask how many semi-landmarks it carries (this
            # count is dataset-wide and can be changed later in the curve table).
            if config:
                fixed_count = config[0].get("start", len(self.landmark_list))
                counts = [c.get("n", 0) for c in config]
                default_n = counts[-1] if counts else 10
            else:
                fixed_count = len(self.landmark_list)
                counts = []
                default_n = 10
            n, ok = QInputDialog.getInt(
                self,
                self.tr("Semi-landmarks"),
                self.tr("Number of semi-landmarks on this curve:"),
                default_n,
                2,
                1000,
            )
            if not ok:
                return
            counts.append(n)
            self.curve_config = mu.build_curve_config(fixed_count, counts)
            target = self.curve_config[-1]
        self.curve_raw_map[target["id"]] = [list(p) for p in raw_points]
        if anchors and len(anchors) >= 2:
            self.curve_anchor_map[target["id"]] = [list(p) for p in anchors]
        else:
            # Hand-traced (or a re-trace without snap): no sparse anchors, so the
            # raw points stay the editable points.
            self.curve_anchor_map.pop(target["id"], None)
        self.curve_trace_changed()
        # The N prompt ran a nested event loop; force an immediate repaint so the
        # new curve shows without waiting for the next event.
        if self.object_view is not None:
            self.object_view.repaint()

    def curve_trace_changed(self):
        """A curve's raw trace changed: refresh the table and repaint. Curves are
        held in memory and written to the database only on Save."""
        self.show_curves()
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.update()

    def show_curves(self):
        """Populate the curve table from the in-memory scheme and traces."""
        config = self.curve_config
        self._populating_curve_table = True
        try:
            self.curveTable.setRowCount(len(config))
            for row, curve in enumerate(config):
                traced = curve.get("id") in self.curve_raw_map
                # Name (0) and N (1) are editable; Traced (2) is a read-only mark.
                self.curveTable.setItem(row, 0, QTableWidgetItem(curve.get("name", "")))
                self.curveTable.setItem(row, 1, QTableWidgetItem(str(curve.get("n", 0))))
                traced_item = QTableWidgetItem("✓" if traced else "")
                traced_item.setFlags(traced_item.flags() & ~Qt.ItemIsEditable)
                self.curveTable.setItem(row, 2, traced_item)
        finally:
            self._populating_curve_table = False

    def select_curve_row(self, curve_id):
        """Select the curve's row in the table (which enables editing it)."""
        for row, curve in enumerate(self.curve_config):
            if curve.get("id") == curve_id:
                self.curveTable.selectRow(row)
                return

    def enter_curve_mode(self, curve_id):
        """Switch to curve mode and select a curve (e.g. clicked in landmark mode)."""
        self.btnCurve_clicked()
        self.select_curve_row(curve_id)

    def delete_curve(self, curve_id):
        """Clear this object's trace for a curve, held in memory until Save.

        The curve stays in the dataset scheme (its semi-landmark count is
        dataset-wide and the curve numbering is shared with every specimen), so
        the slot simply becomes empty and re-tracing re-fills it without asking
        for the count again. Removing a curve from the dataset entirely is a
        separate, dataset-level operation.
        """
        if curve_id not in self.curve_raw_map:
            return
        del self.curve_raw_map[curve_id]
        self.curve_anchor_map.pop(curve_id, None)
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.selected_curve_id = None
                view.hover_curve_id = None
        self.show_curves()
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.update()

    def on_curve_table_context_menu(self, pos):
        """Right-click a curve row to delete it from the whole dataset."""
        row = self.curveTable.rowAt(pos.y())
        if row < 0 or row >= len(self.curve_config):
            return
        menu = QMenu(self)
        del_action = menu.addAction(self.tr("Delete Curve (all specimens)"))
        if menu.exec_(self.curveTable.viewport().mapToGlobal(pos)) is del_action:
            self.delete_curve_dataset_wide(row)

    def delete_curve_dataset_wide(self, row):
        """Remove a curve from the whole dataset (every specimen).

        Restructures the dataset in the database, so the current object's curve
        edits are committed first; the rest are renumbered and every object's raw
        traces remapped by delete_curve_from_dataset.
        """
        from MdModel import delete_curve_from_dataset

        if self.dataset is None or row < 0 or row >= len(self.curve_config):
            return
        self.dataset.set_curve_config(self.curve_config)
        self.dataset.save()
        if self.object is not None:
            self.object.set_curve_raw(self.curve_raw_map)
            self.object.set_curve_anchors(self.curve_anchor_map)
            self.object.save()
        delete_curve_from_dataset(self.dataset, row)
        # Re-sync in-memory copies from the updated database.
        self.curve_config = self.dataset.get_curve_config()
        if self.object is not None:
            fresh = MdObject.get_by_id(self.object.id)
            self.object.curve_raw_json = fresh.curve_raw_json
            self.object.curve_anchor_json = fresh.curve_anchor_json
            self.curve_raw_map = self.object.get_curve_raw()
            self.curve_anchor_map = self.object.get_curve_anchors()
        self._orig_curve_config = copy.deepcopy(self.curve_config)
        self._orig_curve_raw = copy.deepcopy(self.curve_raw_map)
        self._orig_curve_anchor = copy.deepcopy(self.curve_anchor_map)
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.selected_curve_id = None
                view.hover_curve_id = None
        self.show_curves()
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.update()

    def on_curve_selected(self):
        """Selecting a curve row makes its traced points editable in the viewer."""
        if self._populating_curve_table or self.dataset is None:
            return
        items = self.curveTable.selectedItems()
        if not items:
            return
        row = self.curveTable.row(items[0])
        config = self.curve_config
        if row >= len(config):
            return
        view = self.object_view if self.object_view is not None else self.object_view_2d
        if view is not None:
            view.set_mode(MODE["EDIT_CURVE"])
            view.selected_curve_id = config[row]["id"]
            view.update()

    def on_curve_cell_changed(self, item):
        """Editing the Name (col 0) or the count N (col 1); held in memory."""
        if self._populating_curve_table or self.dataset is None:
            return
        config = self.curve_config
        row = item.row()
        if row >= len(config):
            return

        if item.column() == 0:  # curve name
            config[row]["name"] = item.text().strip()
            return
        if item.column() != 1:
            return
        try:
            new_n = int(item.text())
        except (ValueError, TypeError):
            self.show_curves()  # revert the bad edit
            return
        if new_n < 2:
            self.show_curves()
            return
        # Rebuild the scheme with the new count; start indices shift for every
        # following curve. This is a dataset-level change (all specimens share it),
        # applied to the database on Save. Names/descriptions are preserved.
        fixed_count = config[0].get("start", 0)
        curves = [{"n": c.get("n", 0), "name": c.get("name", ""), "desc": c.get("desc", "")} for c in config]
        curves[row]["n"] = new_n
        self.curve_config = mu.build_curve_config(fixed_count, curves)
        self.show_curves()
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.update()

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

        self._update_missing_button_text()

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

        try:
            self.edtLandmarkStr.itemChanged.disconnect()
        except TypeError:
            # No connections exist yet
            pass
        self.edtLandmarkStr.itemChanged.connect(self.on_landmark_cell_changed)

        column_count = 3 if self.dataset.dimension == 3 else 2
        # Repopulating emits itemChanged for every cell; suppress the validator so
        # it only reacts to genuine user edits.
        self._populating_landmark_table = True
        try:
            for idx, lm in enumerate(self.landmark_list):
                for col in range(column_count):
                    value = lm[col] if col < len(lm) else None
                    self.edtLandmarkStr.setItem(idx, col, self._make_landmark_item(value))
        finally:
            self._populating_landmark_table = False

    def _make_landmark_item(self, value):
        """Build one landmark cell: a number, or a red bold ``MISSING`` marker."""
        if value is None:
            item = QTableWidgetItem(MISSING_TEXT)
            item.setForeground(Qt.red)
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        else:
            item = QTableWidgetItem(str(float(value) * 1.0))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item

    def _set_landmark_cell(self, row, col, value):
        """Replace a cell without tripping the validator."""
        self._populating_landmark_table = True
        try:
            self.edtLandmarkStr.setItem(row, col, self._make_landmark_item(value))
        finally:
            self._populating_landmark_table = False

    @guard_slot("Failed to update landmark")
    def on_landmark_cell_changed(self, item):
        """Validate a hand-edited landmark cell when the edit is committed.

        Accepts a number, or ``MISSING`` (any case; a blank cell counts as
        missing since clearing one reads as "no value"). Anything else is
        reverted to the stored value and reported via a tooltip.

        Without this, ``unpack_landmark`` maps *every* non-numeric token to
        ``None``, so a typo like ``12.5o`` would silently turn the landmark into
        a missing one — no error, no warning, just a hole in the data.
        """
        if self._populating_landmark_table:
            return

        row, col = item.row(), item.column()
        if row >= len(self.landmark_list):
            return
        lm = self.landmark_list[row]
        if col >= len(lm):
            return

        text = item.text().strip()
        if text == "" or text.upper() == MISSING_TEXT:
            new_value = None
        else:
            try:
                new_value = float(text)
            except ValueError:
                self._reject_landmark_edit(item, lm[col], text)
                return

        lm[col] = new_value
        # Re-render so MISSING picks up its styling and a number its canonical
        # formatting.
        self._set_landmark_cell(row, col, new_value)
        self._refresh_landmark_views()

    def _reject_landmark_edit(self, item, previous_value, rejected_text):
        """Restore ``previous_value`` and tell the user why the edit bounced."""
        row, col = item.row(), item.column()
        # Resolve the position before replacing the item: Qt deletes the old one,
        # and visualItemRect on a dead item is a crash.
        pos = self.edtLandmarkStr.viewport().mapToGlobal(self.edtLandmarkStr.visualItemRect(item).center())
        logger.warning("Rejected landmark cell edit at (%d, %d): %r is not a number", row, col, rejected_text)
        self._set_landmark_cell(row, col, previous_value)
        QToolTip.showText(
            pos,
            self.tr("'{}' is not a number. Enter a number or {}.").format(rejected_text, MISSING_TEXT),
            self.edtLandmarkStr,
        )

    def _refresh_landmark_views(self):
        """Push the edited landmark list back into both viewers."""
        for view in (self.object_view_2d, self.object_view_3d):
            if view is not None:
                view.landmark_list = self.landmark_list
                view.update()

    def save_object(self):
        # Gather UI values here; the controller performs the DB/file persistence.
        property_str = None
        if self.dataset.propertyname_str is not None and self.dataset.propertyname_str != "":
            property_str = ",".join([edt.text() for edt in self.edtPropertyList])

        self.object = self.controller.save_object(
            self.object,
            self.dataset,
            object_name=self.edtObjectName.text(),
            sequence=int(self.edtSequence.text()),
            object_desc=self.edtObjectDesc.toPlainText(),
            landmark_str=self.make_landmark_str(),
            property_str=property_str,
            image_path=self.object_view_2d.fullpath,
            image_changed=self.object_view_2d.image_changed,
            model_path=self.object_view_3d.fullpath,
        )
        # Persist the semi-landmark curves, held in memory until now: the scheme
        # goes on the dataset (dataset-wide) and the raw traces on the object.
        if self.dataset is not None:
            self.dataset.set_curve_config(self.curve_config)
            self.dataset.save()
        if self.object is not None:
            self.object.set_curve_raw(self.curve_raw_map)
            self.object.set_curve_anchors(self.curve_anchor_map)
            self.object.save()
        self._orig_curve_config = copy.deepcopy(self.curve_config)
        self._orig_curve_raw = copy.deepcopy(self.curve_raw_map)
        self._orig_curve_anchor = copy.deepcopy(self.curve_anchor_map)
        self._saved_snapshot = self._snapshot_state()

        # Refresh this object's row in the main window's list (landmark count may
        # have changed) without disturbing its selection.
        if self.parent is not None and hasattr(self.parent, "update_object_in_table"):
            self.parent.update_object_in_table(self.object)

    def make_landmark_str(self):
        # from table, make landmark_str
        # Modified to handle MISSING values - store as "Missing" text
        landmark_str = ""
        for row in range(self.edtLandmarkStr.rowCount()):
            for col in range(self.edtLandmarkStr.columnCount()):
                cell = self.edtLandmarkStr.item(row, col)
                # An unpopulated cell has no item at all; treat it as missing
                # rather than raising AttributeError on None.
                cell_text = cell.text() if cell is not None else MISSING_TEXT
                # Keep "MISSING" as "Missing" for storage
                if cell_text == MISSING_TEXT:
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
            self.controller.delete_object_with_files(self.object, self.m_app.storage_directory)
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

    def _has_unsaved_curve_changes(self):
        return (
            self.curve_config != self._orig_curve_config
            or self.curve_raw_map != self._orig_curve_raw
            or self.curve_anchor_map != self._orig_curve_anchor
        )

    def _snapshot_state(self):
        # Everything save_object() would persist, so Cancel can tell whether any
        # real data (name/sequence/description/landmarks/variables/curves) changed.
        return {
            "name": self.edtObjectName.text(),
            "sequence": self.edtSequence.text(),
            "desc": self.edtObjectDesc.toPlainText(),
            "landmarks": self.make_landmark_str(),
            "variables": [edt.text() for edt in self.edtPropertyList],
            "curve_config": copy.deepcopy(self.curve_config),
            "curve_raw": copy.deepcopy(self.curve_raw_map),
            "curve_anchor": copy.deepcopy(self.curve_anchor_map),
        }

    def _has_unsaved_changes(self):
        if self._saved_snapshot is None:
            return self._has_unsaved_curve_changes()
        return self._snapshot_state() != self._saved_snapshot

    def Cancel(self):
        if self._has_unsaved_changes():
            answer = QMessageBox.question(
                self,
                self.tr("Unsaved changes"),
                self.tr("You have unsaved changes. Save them before closing?"),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer == QMessageBox.Cancel:
                return  # stay in the dialog
            if answer == QMessageBox.Save:
                self.Okay()
                return
            # Discard: fall through and close without saving.
        self.reject()

    def resizeEvent(self, event):
        # print("Window has been resized",self.image_label.width(), self.image_label.height())
        # self.pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        # self.edtObjectDesc.resize(self.edtObjectDesc.height(),300)
        # self.image_label.setPixmap(self.pixmap)
        QDialog.resizeEvent(self, event)
