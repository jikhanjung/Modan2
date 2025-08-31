#!/usr/bin/env python3
"""
Simple test for fill_sequence functionality with logging
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Setup logging first
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add project path
sys.path.insert(0, '/home/jikhanjung/projects/Modan2')
from ModanComponents import MdTableView

class SimpleTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fill Sequence Debug Test")
        self.setGeometry(100, 100, 800, 600)
        
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
        
        # Add instruction label
        from PyQt5.QtWidgets import QLabel
        instruction = QLabel("""
        Instructions:
        1. Select multiple cells in the 'Sequence' column (column 2)
        2. Right-click to show context menu
        3. Select 'Fill sequence'
        4. Watch debug output in console
        """)
        layout.addWidget(instruction)
        
        # Add manual test button
        test_btn = QPushButton("Manual Test: Call fill_sequence() directly")
        test_btn.clicked.connect(self.manual_test)
        layout.addWidget(test_btn)
        
        print("=" * 60)
        print("Fill Sequence Debug Test")
        print("=" * 60)
        print("Watch console for debug messages when using context menu")
    
    def manual_test(self):
        """Manually trigger fill_sequence for testing"""
        print("\n" + "="*50)
        print("MANUAL TEST - Calling fill_sequence() directly")
        print("="*50)
        
        # Select some cells in column 1 first
        selection = self.table.selectionModel()
        model = self.table.model()
        
        # Select rows 0-2 in column 1 (sequence column)
        for row in range(3):
            index = model.index(row, 1)
            selection.select(index, selection.Select)
        
        print(f"Selected {len(self.table.selectionModel().selectedIndexes())} cells")
        
        # Now call fill_sequence
        self.table.fill_sequence()

def main():
    app = QApplication(sys.argv)
    
    # Enable all debug output
    print("Starting application with debug logging enabled...")
    
    window = SimpleTestWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())