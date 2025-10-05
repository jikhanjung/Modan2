"""Calibration Dialog for setting scale measurements."""

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
)

from dialogs.base_dialog import BaseDialog


class CalibrationDialog(BaseDialog):
    """Dialog for calibrating pixel measurements to metric units.

    Allows users to:
    - Enter known length in metric units
    - Select unit (nm, um, mm, cm, m)
    - Calculate calibration factor from pixel distance
    """

    def __init__(self, parent, dist):
        """Initialize calibration dialog.

        Args:
            parent: Parent widget with set_object_calibration method
            dist: Pixel distance to calibrate (optional)
        """
        super().__init__(parent, title="Calibration")
        self.parent = parent
        self.last_calibration_unit = "mm"
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos() + QPoint(100, 100))
        self.m_app = QApplication.instance()
        self.read_settings()

        self.status_bar = QStatusBar()
        self.lblText1 = QLabel("Calibration", self)
        self.lblText2 = QLabel("Calibration", self)
        self.edtLength = QLineEdit(self)
        self.edtLength.setValidator(QDoubleValidator())
        self.edtLength.setText("1.0")
        self.edtLength.setFixedWidth(100)
        self.edtLength.setFixedHeight(30)
        self.comboUnit = QComboBox(self)
        self.comboUnit.addItem("nm")
        self.comboUnit.addItem("um")
        self.comboUnit.addItem("mm")
        self.comboUnit.addItem("cm")
        self.comboUnit.addItem("m")
        self.comboUnit.setFixedWidth(100)
        self.comboUnit.setFixedHeight(30)
        self.comboUnit.setCurrentText("mm")
        self.btnOK = QPushButton("OK", self)
        self.btnOK.setFixedWidth(100)
        self.btnOK.setFixedHeight(30)
        self.btnCancel = QPushButton("Cancel", self)
        self.btnCancel.setFixedWidth(100)
        self.btnCancel.setFixedHeight(30)
        self.btnOK.clicked.connect(self.btnOK_clicked)
        self.btnCancel.clicked.connect(self.btnCancel_clicked)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.edtLength)
        self.hbox.addWidget(self.comboUnit)
        self.hbox.addWidget(self.btnOK)
        self.hbox.addWidget(self.btnCancel)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.lblText1)
        self.vbox.addWidget(self.lblText2)
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)
        self.comboUnit.setCurrentText(self.last_calibration_unit)

        if dist is not None:
            self.set_pixel_number(dist)

    def read_settings(self):
        """Read last calibration unit from settings."""
        self.last_calibration_unit = self.m_app.settings.value("Calibration/Unit", self.last_calibration_unit)

    def write_settings(self):
        """Save calibration unit to settings."""
        self.m_app.settings.setValue("Calibration/Unit", self.last_calibration_unit)

    def set_pixel_number(self, pixel_number):
        """Set the pixel distance to be calibrated.

        Args:
            pixel_number: Number of pixels in the measured distance
        """
        self.pixel_number = pixel_number
        self.lblText1.setText("Enter the unit length in metric scale.")
        self.lblText2.setText(f"{self.pixel_number:.2f} pixels are equivalent to:")
        self.edtLength.selectAll()

    def btnOK_clicked(self):
        """Handle OK button click - apply calibration."""
        self.parent.set_object_calibration(
            self.pixel_number, float(self.edtLength.text()), self.comboUnit.currentText()
        )
        self.last_calibration_unit = self.comboUnit.currentText()
        self.write_settings()
        self.close()

    def btnCancel_clicked(self):
        """Handle Cancel button click."""
        self.close()
