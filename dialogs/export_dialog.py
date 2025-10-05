"""Export Dataset Dialog for exporting datasets to various formats."""

import datetime
import os
import shutil

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog
from dialogs.progress_dialog import ProgressDialog
from MdModel import MdDatasetOps, MdObject

NEWLINE = "\n"


class ExportDatasetDialog(BaseDialog):
    """Dialog for exporting datasets to various file formats.

    Supported formats:
    - TPS (landmark data)
    - Morphologika (with images and metadata)
    - JSON+ZIP (complete dataset package)

    Features:
    - Object selection for export
    - Optional Procrustes superimposition
    - File size estimation for ZIP exports
    """

    def __init__(self, parent):
        """Initialize export dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent, title="Modan2 - Export")
        self.setWindowTitle(self.tr("Modan2 - Export"))
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        """Create UI widgets."""
        # Dataset name
        self.lblDatasetName = QLabel(self.tr("Dataset Name"))
        self.lblDatasetName.setMaximumHeight(20)
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setMaximumHeight(20)

        # Object lists
        self.lblObjectList = QLabel(self.tr("Object List"))
        self.lblExportList = QLabel(self.tr("Export List"))
        self.lblObjectList.setMaximumHeight(20)
        self.lblExportList.setMaximumHeight(20)
        self.lstObjectList = QListWidget()
        self.lstExportList = QListWidget()
        self.lstObjectList.setMinimumHeight(400)
        self.lstExportList.setMinimumHeight(400)

        # Buttons
        self.btnExport = QPushButton(self.tr("Export"))
        self.btnExport.clicked.connect(self.export_dataset)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.close)
        self.btnMoveRight = QPushButton(">")
        self.btnMoveRight.clicked.connect(self.move_right)
        self.btnMoveLeft = QPushButton("<")
        self.btnMoveLeft.clicked.connect(self.move_left)

        # Export format options
        self.lblExport = QLabel(self.tr("Export Format"))
        self.rbTPS = QRadioButton("TPS")
        self.rbTPS.setChecked(True)
        self.rbTPS.clicked.connect(self.on_rbTPS_clicked)
        self.rbX1Y1 = QRadioButton("X1Y1")
        self.rbX1Y1.clicked.connect(self.on_rbX1Y1_clicked)
        self.rbMorphologika = QRadioButton("Morphologika")
        self.rbMorphologika.clicked.connect(self.on_rbMorphologika_clicked)

        # JSON+ZIP option
        self.rbJSONZip = QRadioButton("JSON+ZIP")
        self.rbJSONZip.clicked.connect(self.on_rbJSONZip_clicked)
        self.chkIncludeFiles = QCheckBox(self.tr("Include image and model files"))
        self.chkIncludeFiles.setChecked(True)
        self.chkIncludeFiles.setEnabled(False)
        self.chkIncludeFiles.toggled.connect(self.update_estimated_size)
        self.lblEstimatedSize = QLabel(self.tr("Estimated size: -"))

        # Superimposition options
        self.lblSuperimposition = QLabel(self.tr("Superimposition"))
        self.rbProcrustes = QRadioButton(self.tr("Procrustes"))
        self.rbProcrustes.clicked.connect(self.on_rbProcrustes_clicked)
        self.rbProcrustes.setChecked(True)
        self.rbBookstein = QRadioButton(self.tr("Bookstein"))
        self.rbBookstein.clicked.connect(self.on_rbBookstein_clicked)
        self.rbBookstein.setEnabled(False)
        self.rbRFTRA = QRadioButton(self.tr("Resistant fit"))
        self.rbRFTRA.clicked.connect(self.on_rbRFTRA_clicked)
        self.rbRFTRA.setEnabled(False)
        self.rbNone = QRadioButton(self.tr("None"))
        self.rbNone.clicked.connect(self.on_rbNone_clicked)

    def _create_layout(self):
        """Create dialog layout."""
        # Form layout
        self.form_layout = QGridLayout()
        self.form_layout.addWidget(self.lblDatasetName, 0, 0)
        self.form_layout.addWidget(self.edtDatasetName, 0, 1, 1, 2)
        self.form_layout.addWidget(self.lblObjectList, 1, 0)
        self.form_layout.addWidget(self.lstObjectList, 2, 0, 2, 1)
        self.form_layout.addWidget(self.btnMoveRight, 2, 1)
        self.form_layout.addWidget(self.btnMoveLeft, 3, 1)
        self.form_layout.addWidget(self.lblExportList, 1, 2)
        self.form_layout.addWidget(self.lstExportList, 2, 2, 2, 1)

        # Button layouts
        self.button_layout1 = QHBoxLayout()
        self.button_layout1.addWidget(self.btnExport)
        self.button_layout1.addWidget(self.btnCancel)

        # Export format button group
        self.button_layout2 = QHBoxLayout()
        self.button_layout2.addWidget(self.lblExport)
        self.button_layout2.addWidget(self.rbTPS)
        self.button_layout2.addWidget(self.rbX1Y1)
        self.button_layout2.addWidget(self.rbMorphologika)
        self.button_layout2.addWidget(self.rbJSONZip)
        self.button_layout2.addWidget(self.chkIncludeFiles)
        self.button_layout2.addWidget(self.lblEstimatedSize)
        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.rbTPS)
        self.button_group2.addButton(self.rbX1Y1)
        self.button_group2.addButton(self.rbMorphologika)
        self.button_group2.addButton(self.rbJSONZip)

        # Superimposition button group
        self.button_layout3 = QHBoxLayout()
        self.button_layout3.addWidget(self.lblSuperimposition)
        self.button_layout3.addWidget(self.rbNone)
        self.button_layout3.addWidget(self.rbProcrustes)
        self.button_layout3.addWidget(self.rbBookstein)
        self.button_layout3.addWidget(self.rbRFTRA)
        self.button_group3 = QButtonGroup()
        self.button_group3.addButton(self.rbNone)
        self.button_group3.addButton(self.rbProcrustes)
        self.button_group3.addButton(self.rbBookstein)
        self.button_group3.addButton(self.rbRFTRA)

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.button_layout2)
        self.layout.addLayout(self.button_layout3)
        self.layout.addLayout(self.button_layout1)

        self.setLayout(self.layout)

    def read_settings(self):
        """Read window geometry from settings."""
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ExportDialog", QRect(100, 100, 600, 400)))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        """Save window geometry to settings."""
        if self.remember_geometry:
            self.m_app.settings.setValue("WindowGeometry/ExportDialog", self.geometry())

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.write_settings()
        event.accept()

    def set_dataset(self, dataset):
        """Set the dataset to export.

        Args:
            dataset: MdDataset to export
        """
        self.dataset = dataset
        self.ds_ops = MdDatasetOps(dataset)
        self.edtDatasetName.setText(self.dataset.dataset_name)
        for obj in self.dataset.object_list:
            self.lstExportList.addItem(obj.object_name)

    # Radio button handlers
    def on_rbProcrustes_clicked(self):
        """Handle Procrustes radio button click."""
        pass

    def on_rbBookstein_clicked(self):
        """Handle Bookstein radio button click."""
        pass

    def on_rbRFTRA_clicked(self):
        """Handle Resistant fit radio button click."""
        pass

    def on_rbNone_clicked(self):
        """Handle None radio button click."""
        pass

    def on_rbTPS_clicked(self):
        """Handle TPS radio button click."""
        pass

    def on_rbNTS_clicked(self):
        """Handle NTS radio button click."""
        pass

    def on_rbX1Y1_clicked(self):
        """Handle X1Y1 radio button click."""
        pass

    def on_rbMorphologika_clicked(self):
        """Handle Morphologika radio button click."""
        pass

    def on_rbJSONZip_clicked(self):
        """Handle JSON+ZIP radio button click - enable file inclusion."""
        self.chkIncludeFiles.setEnabled(True)
        self.update_estimated_size()

    def update_estimated_size(self):
        """Update estimated package size for ZIP export."""
        try:
            include_files = self.chkIncludeFiles.isChecked()
            size_bytes = mu.estimate_package_size(self.ds_ops.id, include_files=include_files)

            def fmt(sz):
                """Format bytes to human-readable size."""
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if sz < 1024.0:
                        return f"{sz:3.1f} {unit}"
                    sz /= 1024.0
                return f"{sz:.1f} PB"

            self.lblEstimatedSize.setText(self.tr("Estimated size: ") + fmt(size_bytes))
        except Exception:
            self.lblEstimatedSize.setText(self.tr("Estimated size: -"))

    def move_right(self):
        """Move selected objects from object list to export list."""
        selected_items = self.lstObjectList.selectedItems()
        for item in selected_items:
            self.lstObjectList.takeItem(self.lstObjectList.row(item))
            self.lstExportList.addItem(item)

    def move_left(self):
        """Move selected objects from export list to object list."""
        selected_items = self.lstExportList.selectedItems()
        for item in selected_items:
            self.lstExportList.takeItem(self.lstExportList.row(item))
            self.lstObjectList.addItem(item)

    def export_dataset(self):
        """Export dataset to selected format."""
        # Apply superimposition if selected
        if self.rbProcrustes.isChecked():
            self.ds_ops.procrustes_superimposition()

        object_list = self.ds_ops.object_list
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d_%H%M%S")

        if self.rbTPS.isChecked():
            self._export_tps(date_str, object_list)
        elif self.rbMorphologika.isChecked():
            self._export_morphologika(date_str, object_list)
        elif hasattr(self, "rbJSONZip") and self.rbJSONZip.isChecked():
            self._export_json_zip(date_str)

        self.close()

    def _export_tps(self, date_str, object_list):
        """Export dataset to TPS format.

        Args:
            date_str: Timestamp string for filename
            object_list: List of objects to export
        """
        filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.tps"
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "TPS format (*.tps)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                for obj in object_list:
                    f.write(f"LM={len(obj.landmark_list)}\n")
                    for lm in obj.landmark_list:
                        if self.ds_ops.dimension == 2:
                            f.write("{}\t{}\n".format(*lm))
                        else:
                            f.write("{}\t{}\t{}\n".format(*lm))
                    f.write(f"ID={obj.object_name}\n")

    def _export_morphologika(self, date_str, object_list):
        """Export dataset to Morphologika format.

        Args:
            date_str: Timestamp string for filename
            object_list: List of objects to export
        """
        filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.txt"
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "Morphologika format (*.txt)")
        if not filename:
            return

        result_str = ""
        result_str += "[individuals]" + NEWLINE + str(len(self.ds_ops.object_list)) + NEWLINE
        result_str += "[landmarks]" + NEWLINE + str(len(self.ds_ops.object_list[0].landmark_list)) + NEWLINE
        result_str += "[dimensions]" + NEWLINE + str(self.ds_ops.dimension) + NEWLINE
        label_values = "[labels]" + NEWLINE + "\t".join(self.dataset.variablename_list) + NEWLINE
        label_values += "[labelvalues]" + NEWLINE
        rawpoint_values = "[rawpoints]" + NEWLINE
        image_values = "[images]" + NEWLINE
        ppmm_values = "[pixelspermm]" + NEWLINE
        name_values = "[names]" + NEWLINE

        for mo in self.ds_ops.object_list:
            label_values += "\t".join(mo.variable_list).strip() + NEWLINE
            name_values += mo.object_name + NEWLINE
            rawpoint_values += "'#" + mo.object_name + NEWLINE
            for lm in mo.landmark_list:
                rawpoint_values += "\t".join([str(c) for c in lm])
                rawpoint_values += NEWLINE

        result_str += name_values + label_values + rawpoint_values

        if len(self.dataset.edge_list) > 0:
            result_str += "[wireframe]" + NEWLINE
            self.dataset.unpack_wireframe()
            for edge in self.dataset.edge_list:
                result_str += "\t".join([str(v) for v in edge]) + NEWLINE

        if len(self.dataset.polygon_list) > 0:
            result_str += "[polygons]" + NEWLINE
            self.dataset.unpack_polygons()
            for polygon in self.dataset.polygon_list:
                result_str += "\t".join([str(v) for v in polygon]) + NEWLINE

        for obj_ops in self.ds_ops.object_list:
            obj = MdObject.get_by_id(obj_ops.id)
            if obj.has_image():
                img = obj.get_image()
                image_values += obj.get_name() + "." + img.get_file_path().split(".")[-1] + NEWLINE
                old_filepath = img.get_file_path()
                new_image_path = os.path.join(
                    os.path.dirname(filename), obj.get_name() + "." + img.get_file_path().split(".")[-1]
                )
                shutil.copyfile(old_filepath, new_image_path)
            else:
                image_values = "" + NEWLINE

            if obj.pixels_per_mm is not None and obj.pixels_per_mm > 0:
                ppmm_values += str(obj.pixels_per_mm) + NEWLINE
            else:
                ppmm_values = "" + NEWLINE

        result_str += image_values
        result_str += ppmm_values

        with open(filename, "w", encoding="utf-8") as f:
            f.write(result_str)

    def _export_json_zip(self, date_str):
        """Export dataset to JSON+ZIP format.

        Args:
            date_str: Timestamp string for filename
        """
        filename_candidate = f"{self.ds_ops.dataset_name}_{date_str}.zip"
        filepath = os.path.join(mu.USER_PROFILE_DIRECTORY, filename_candidate)
        filename, _ = QFileDialog.getSaveFileName(self, "Save File As", filepath, "ZIP archive (*.zip)")
        if not filename:
            return

        try:
            # Show progress dialog
            progress = ProgressDialog(self)
            progress.set_progress_text(self.tr("Exporting {}/{}..."))
            progress.set_max_value(100)
            progress.show()

            def progress_callback(curr, total):
                """Update progress bar."""
                try:
                    val = int((curr / float(total)) * 100) if total else 0
                except Exception:
                    val = 0
                progress.set_curr_value(val)

            include_files = self.chkIncludeFiles.isChecked()
            mu.create_zip_package(
                self.ds_ops.id, filename, include_files=include_files, progress_callback=progress_callback
            )
            progress.close()
            QMessageBox.information(self, self.tr("Export"), self.tr("Export completed."))
        except Exception as e:
            try:
                progress.close()
            except Exception:
                pass
            QMessageBox.critical(self, self.tr("Export"), self.tr("Export failed: ") + str(e))
