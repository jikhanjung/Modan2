#!/usr/bin/env python3
"""
Test script to verify the fill_sequence functionality
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem

# Add project path
sys.path.insert(0, '/home/jikhanjung/projects/Modan2')
from ModanComponents import MdTableView

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fill Sequence Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Create table view
        self.table = MdTableView()
        
        # Create model with test data
        model = QStandardItemModel(10, 3)
        model.setHorizontalHeaderLabels(["ID", "Sequence", "Name"])
        
        # Fill with test data
        for i in range(10):
            model.setItem(i, 0, QStandardItem(str(i+1)))
            model.setItem(i, 1, QStandardItem(""))  # Empty sequence column
            model.setItem(i, 2, QStandardItem(f"Object {i+1}"))
        
        self.table.setModel(model)
        layout.addWidget(self.table)
        
        # Add test button
        test_btn = QPushButton("Test Fill Sequence (Select cells in Sequence column first)")
        test_btn.clicked.connect(self.test_fill_sequence)
        layout.addWidget(test_btn)
        
        print("=" * 50)
        print("Fill Sequence Test Window")
        print("=" * 50)
        print("Instructions:")
        print("1. Select multiple cells in the 'Sequence' column (column 2)")
        print("2. Right-click to open context menu")
        print("3. Choose 'Fill sequence' option")
        print("4. Enter starting number and increment")
        print("5. Check if sequence is filled correctly")
        print("=" * 50)
    
    def test_fill_sequence(self):
        """Programmatically test fill_sequence"""
        # Select cells in column 1 (sequence column)
        selection = self.table.selectionModel()
        model = self.table.model()
        
        # Select rows 2-5 in column 1
        for row in range(2, 6):
            index = model.index(row, 1)
            selection.select(index, selection.Select)
        
        print("\nProgrammatically selected rows 3-6 in Sequence column")
        print("Now calling fill_sequence()...")
        
        # Note: This will show input dialogs
        # User needs to enter values manually
        self.table.fill_sequence()

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())