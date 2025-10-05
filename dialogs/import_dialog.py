"""Import Dataset Dialog for importing datasets from various formats."""

import logging
import os
import shutil
from pathlib import Path

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QWidget,
)

import MdUtils as mu
from dialogs.base_dialog import BaseDialog
from MdModel import MdDataset, MdImage, MdObject
from ModanComponents import NTS, TPS, X1Y1, Morphologika

logger = logging.getLogger(__name__)


class ImportDatasetDialog(BaseDialog):
    """Dialog for importing datasets from various file formats.

    Supported formats:
    - TPS (landmark data)
    - NTS (landmark data)
    - X1Y1 (landmark data)
    - Morphologika (with metadata)
    - JSON+ZIP (complete dataset package)

    Features:
    - Automatic file type detection
    - Progress tracking
    - Dataset name suggestion
    """

    def __init__(self, parent):
        """Initialize import dialog.

        Args:
            parent: Parent window with load_dataset method
        """
        super().__init__(parent, title="Modan2 - Import")
        self.setWindowTitle(self.tr("Modan2 - Import"))
        self.parent = parent
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        """Create UI widgets."""
        # File selection
        self.filename_layout = QHBoxLayout()
        self.filename_widget = QWidget()
        self.btnOpenFile = QPushButton(self.tr("Open File"))
        self.btnOpenFile.clicked.connect(self.open_file)
        self.edtFilename = QLineEdit()
        self.edtFilename.setReadOnly(True)
        self.edtFilename.setPlaceholderText(self.tr("Select a file to import"))
        self.edtFilename.setMinimumWidth(400)
        self.edtFilename.setMaximumWidth(400)
        self.edtFilename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filename_layout.addWidget(self.edtFilename)
        self.filename_layout.addWidget(self.btnOpenFile)
        self.filename_widget.setLayout(self.filename_layout)

        # File type selection
        self.chkFileType = QButtonGroup()
        self.rbnTPS = QRadioButton("TPS")
        self.rbnNTS = QRadioButton("NTS")
        self.rbnX1Y1 = QRadioButton("X1Y1")
        self.rbnMorphologika = QRadioButton("Morphologika")
        self.rbnJSONZip = QRadioButton("JSON+ZIP")
        self.chkFileType.addButton(self.rbnTPS)
        self.chkFileType.addButton(self.rbnNTS)
        self.chkFileType.addButton(self.rbnX1Y1)
        self.chkFileType.addButton(self.rbnMorphologika)
        self.chkFileType.addButton(self.rbnJSONZip)
        self.chkFileType.buttonClicked.connect(self.file_type_changed)
        self.chkFileType.setExclusive(True)

        self.gbxFileType = QGroupBox()
        self.gbxFileType.setLayout(QHBoxLayout())
        self.gbxFileType.layout().addWidget(self.rbnTPS)
        self.gbxFileType.layout().addWidget(self.rbnNTS)
        self.gbxFileType.layout().addWidget(self.rbnX1Y1)
        self.gbxFileType.layout().addWidget(self.rbnMorphologika)
        self.gbxFileType.layout().addWidget(self.rbnJSONZip)
        self.gbxFileType.layout().addStretch(1)
        self.gbxFileType.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gbxFileType.setMaximumHeight(50)
        self.gbxFileType.setMinimumHeight(50)

        # Dimension selection
        self.rb2D = QRadioButton("2D")
        self.rb3D = QRadioButton("3D")
        self.gbxDimension = QGroupBox()
        self.gbxDimension.setLayout(QHBoxLayout())
        self.gbxDimension.layout().addWidget(self.rb2D)
        self.gbxDimension.layout().addWidget(self.rb3D)

        self.cbxInvertY = QCheckBox(self.tr("Inverted"))

        # Dataset info
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setPlaceholderText(self.tr("Dataset Name"))
        self.edtDatasetName.setMinimumWidth(400)
        self.edtDatasetName.setMaximumWidth(400)
        self.edtDatasetName.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.edtObjectCount = QLineEdit()
        self.edtObjectCount.setReadOnly(True)
        self.edtObjectCount.setPlaceholderText(self.tr("Object Count"))
        self.edtObjectCount.setMinimumWidth(100)
        self.edtObjectCount.setMaximumWidth(100)
        self.edtObjectCount.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Import button
        self.btnImport = QPushButton(self.tr("Execute Import"))
        self.btnImport.clicked.connect(self.import_file)
        self.btnImport.setEnabled(False)

        # Progress bar
        self.prgImport = QProgressBar()
        self.prgImport.setMinimum(0)
        self.prgImport.setMaximum(100)
        self.prgImport.setValue(0)
        self.prgImport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _create_layout(self):
        """Create dialog layout."""
        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow(self.tr("File"), self.filename_widget)
        self.main_layout.addRow(self.tr("File Type"), self.gbxFileType)
        self.main_layout.addRow(self.tr("Dataset Name"), self.edtDatasetName)
        self.main_layout.addRow(self.tr("Object Count"), self.edtObjectCount)
        self.main_layout.addRow(self.tr("Y coordinate"), self.cbxInvertY)
        self.main_layout.addRow(self.tr("Dimension"), self.gbxDimension)
        self.main_layout.addRow(self.tr("Progress"), self.prgImport)
        self.main_layout.addRow("", self.btnImport)

    def read_settings(self):
        """Read window geometry from settings."""
        self.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/ImportDialog", QRect(100, 100, 500, 220)))
        else:
            self.setGeometry(QRect(100, 100, 500, 220))
            self.move(self.parent.pos() + QPoint(50, 50))

    def write_settings(self):
        """Save window geometry to settings."""
        if self.remember_geometry:
            self.m_app.settings.setValue("WindowGeometry/ImportDialog", self.geometry())

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent
        """
        self.write_settings()
        event.accept()

    def open_file2(self, filename):
        """Process selected file and auto-detect format.

        Args:
            filename: Path to file to import
        """
        self.edtFilename.setText(filename)
        self.btnImport.setEnabled(True)
        self.edtDatasetName.setText(self.suggest_unique_dataset_name(Path(filename).stem))
        self.edtObjectCount.setText("")
        self.prgImport.setValue(0)

        self.file_ext = Path(filename).suffix
        import_data = None

        # Auto-detect file type
        if self.file_ext.lower() == ".tps":
            self.rbnTPS.setChecked(True)
            self.file_type_changed()
            import_data = TPS(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".nts":
            self.rbnNTS.setChecked(True)
            self.file_type_changed()
            import_data = NTS(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".x1y1":
            self.rbnX1Y1.setChecked(True)
            self.file_type_changed()
            import_data = X1Y1(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".txt":
            self.rbnMorphologika.setChecked(True)
            self.file_type_changed()
            import_data = Morphologika(filename, self.edtDatasetName.text(), self.cbxInvertY.isChecked())
        elif self.file_ext.lower() == ".zip":
            self._handle_zip_file(filename)
            return
        else:
            self._handle_unsupported_file()
            return

        if import_data and len(import_data.object_name_list) > 0:
            self.edtObjectCount.setText(str(import_data.nobjects))
            if import_data.dimension == 2:
                self.rb2D.setChecked(True)
            else:
                self.rb3D.setChecked(True)

    def _handle_zip_file(self, filename):
        """Handle JSON+ZIP file import.

        Args:
            filename: Path to ZIP file
        """
        self.rbnJSONZip.setChecked(True)
        self.file_type_changed()
        try:
            data = mu.read_json_from_zip(filename)
            ds_meta = data.get("dataset", {})
            objs = data.get("objects", [])
            base_name = ds_meta.get("name") or self.tr("Imported Dataset")
            self.edtDatasetName.setText(self.suggest_unique_dataset_name(base_name))
            self.edtObjectCount.setText(str(len(objs)))
            if int(ds_meta.get("dimension", 2)) == 2:
                self.rb2D.setChecked(True)
            else:
                self.rb3D.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Import"), self.tr("Failed to read package: ") + str(e))

    def _handle_unsupported_file(self):
        """Handle unsupported file type."""
        self.rbnTPS.setChecked(False)
        self.rbnNTS.setChecked(False)
        self.rbnX1Y1.setChecked(False)
        self.rbnMorphologika.setChecked(False)
        if hasattr(self, "rbnJSONZip"):
            self.rbnJSONZip.setChecked(False)
        self.btnImport.setEnabled(False)
        self.edtObjectCount.setText("")
        self.prgImport.setValue(0)
        self.edtDatasetName.setText("")
        self.edtFilename.setText("")
        QMessageBox.warning(self, self.tr("Warning"), self.tr("File type not supported."))

    def open_file(self):
        """Show file selection dialog."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", mu.USER_PROFILE_DIRECTORY, "All Files (*.*)")
        if filename:
            self.open_file2(filename)

    def file_type_changed(self):
        """Handle file type selection change."""
        pass

    def suggest_unique_dataset_name(self, base_name: str) -> str:
        """Generate unique dataset name by appending number if needed.

        Args:
            base_name: Base name for dataset

        Returns:
            Unique dataset name
        """
        try:
            candidate = base_name
            suffix = 1
            while MdDataset.select().where(MdDataset.dataset_name == candidate).exists():
                candidate = f"{base_name} ({suffix})"
                suffix += 1
            return candidate
        except Exception:
            return base_name

    def import_file(self):
        """Import dataset from selected file."""
        filename = self.edtFilename.text()
        filetype = self.chkFileType.checkedButton().text()
        datasetname = self.suggest_unique_dataset_name(self.edtDatasetName.text())
        invertY = self.cbxInvertY.isChecked()

        # Handle JSON+ZIP separately
        if filetype == "JSON+ZIP":
            self._import_json_zip(filename)
            return

        # Handle other formats
        import_data = self._get_import_data(filetype, filename, datasetname, invertY)
        if import_data is None:
            return

        self._execute_import(import_data, datasetname, filetype)

    def _get_import_data(self, filetype, filename, datasetname, invertY):
        """Get import data object based on file type.

        Args:
            filetype: Type of file (TPS, NTS, etc.)
            filename: Path to file
            datasetname: Name for new dataset
            invertY: Whether to invert Y coordinates

        Returns:
            Import data object or None
        """
        if filetype == "TPS":
            return TPS(filename, datasetname, invertY)
        elif filetype == "NTS":
            return NTS(filename, datasetname, invertY)
        elif filetype == "X1Y1":
            return X1Y1(filename, datasetname, invertY)
        elif filetype == "Morphologika":
            return Morphologika(filename, datasetname, invertY)
        return None

    def _import_json_zip(self, filename):
        """Import dataset from JSON+ZIP package.

        Args:
            filename: Path to ZIP file
        """
        self.prgImport.setValue(0)

        def progress_callback(curr, total):
            """Update progress bar."""
            try:
                val = int((curr / float(total)) * 100) if total else 0
            except Exception:
                val = 0
            self.prgImport.setValue(val)
            self.prgImport.update()

        try:
            new_ds_id = mu.import_dataset_from_zip(filename, progress_callback=progress_callback)
            self.prgImport.setValue(100)
            QMessageBox.information(
                self, self.tr("Import"), self.tr("Import completed (Dataset ID: ") + str(new_ds_id) + ")"
            )
            if hasattr(self.parent, "load_dataset"):
                self.parent.load_dataset()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Import"), self.tr("Import failed: ") + str(e))

    def _execute_import(self, import_data, datasetname, filetype):
        """Execute import from parsed data.

        Args:
            import_data: Parsed import data object
            datasetname: Name for new dataset
            filetype: Type of file being imported
        """
        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat(self.tr("Importing..."))
        self.update_progress(0)

        self.edtObjectCount.setText(str(import_data.nobjects))

        # Create dataset
        dataset = MdDataset()
        dataset.dataset_name = datasetname
        dataset.dimension = import_data.dimension
        if len(import_data.variablename_list) > 0:
            dataset.variablename_list = import_data.variablename_list
            dataset.pack_variablename_str()
        if len(import_data.edge_list) > 0:
            dataset.edge_list = import_data.edge_list
            dataset.wireframe = dataset.pack_wireframe()
        dataset.save()

        # Add objects
        for i in range(import_data.nobjects):
            self._import_object(import_data, dataset, i)
            self.update_progress(int(float(i + 1) * 100.0 / float(import_data.nobjects)))

        # Show completion message
        QMessageBox.information(self, self.tr("Import"), self.tr(f"Finished importing a {filetype} file."))
        if hasattr(self.parent, "load_dataset"):
            self.parent.load_dataset()
        self.close()

    def _import_object(self, import_data, dataset, index):
        """Import single object.

        Args:
            import_data: Parsed import data
            dataset: Target dataset
            index: Object index in import data
        """
        obj = MdObject()
        obj.object_name = import_data.object_name_list[index]

        # Set pixels per mm if available
        if hasattr(import_data, "ppmm_list") and len(import_data.ppmm_list) > 0:
            if mu.is_numeric(import_data.ppmm_list[index]):
                obj.pixels_per_mm = float(import_data.ppmm_list[index])

        obj.dataset = dataset

        # Set landmarks
        landmark_list = []
        for landmark in import_data.landmark_data[obj.object_name]:
            landmark_list.append("\t".join([str(x) for x in landmark]))
        obj.landmark_str = "\n".join(landmark_list)

        # Set variables
        if len(import_data.variablename_list) > 0:
            obj.variable_list = import_data.property_list_list[index]
            obj.pack_variable()

        # Set description
        if obj.object_name in import_data.object_comment.keys():
            obj.object_desc = import_data.object_comment[import_data.object_name_list[index]]

        obj.save()

        # Import image if available
        if obj.object_name in import_data.object_images.keys():
            self._import_object_image(obj, import_data)

    def _import_object_image(self, obj, import_data):
        """Import image for object.

        Args:
            obj: MdObject to attach image to
            import_data: Import data containing image info
        """
        file_name = import_data.object_images[obj.object_name]
        if not os.path.exists(file_name):
            file_name = os.path.join(import_data.dirname, file_name)
        if not os.path.exists(file_name):
            logger.error(f"File not found: {file_name}")
            return

        new_image = MdImage()
        new_image.object = obj
        new_image.load_file_info(file_name)
        new_filepath = new_image.get_file_path(self.m_app.storage_directory)
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        shutil.copyfile(file_name, new_filepath)
        new_image.save()

    def update_progress(self, value):
        """Update progress bar.

        Args:
            value: Progress value (0-100)
        """
        self.prgImport.setValue(value)
        self.prgImport.setFormat(self.tr(f"Importing...{value}%"))
        self.prgImport.update()
        self.prgImport.repaint()
        QApplication.processEvents()
