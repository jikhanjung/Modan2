#!/usr/bin/env python3
"""
Test context menu functionality
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, '/home/jikhanjung/projects/Modan2')
from ModanComponents import MdTableView

class ContextMenuTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Context Menu Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Create table view
        self.table = MdTableView()
        
        # Create model with test data
        model = QStandardItemModel(5, 3)
        model.setHorizontalHeaderLabels(["ID", "Sequence", "Name"])
        
        # Fill with test data
        for i in range(5):
            model.setItem(i, 0, QStandardItem(str(i+1)))
            model.setItem(i, 1, QStandardItem(""))  # Empty sequence column
            model.setItem(i, 2, QStandardItem(f"Object {i+1}"))
        
        self.table.setModel(model)
        layout.addWidget(self.table)
        
        # Select some cells in the sequence column (column 1) programmatically
        selection = self.table.selectionModel()
        for row in range(3):
            index = model.index(row, 1)  # Column 1 is sequence
            selection.select(index, selection.Select)
        
        print("Selected cells in sequence column")
        print("Right-click on the table to show context menu")
        
        # Test programmatic context menu
        from PyQt5.QtWidgets import QPushButton
        test_btn = QPushButton("Test Context Menu Programmatically")
        test_btn.clicked.connect(self.test_context_menu)
        layout.addWidget(test_btn)
    
    def test_context_menu(self):
        """Test context menu programmatically"""
        print("\n" + "="*50)
        print("TESTING CONTEXT MENU PROGRAMMATICALLY")
        print("="*50)
        
        # Simulate right-click at position (50, 50) in the table
        pos = QPoint(50, 50)
        print(f"Simulating right-click at position: {pos}")
        
        # Call show_context_menu directly
        self.table.show_context_menu(pos)

def main():
    app = QApplication(sys.argv)
    
    window = ContextMenuTest()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())