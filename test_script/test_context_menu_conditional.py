#!/usr/bin/env python3
"""
Test context menu conditional fill sequence functionality
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QStandardItemModel, QStandardItem

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, '/home/jikhanjung/projects/Modan2')
from ModanComponents import MdTableView

class ConditionalContextMenuTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conditional Context Menu Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Add instructions
        instructions = QLabel("""
        Test Instructions:
        1. Select cells in different columns and right-click
        2. Fill Sequence should only appear when:
           - All selected cells are in column 1 (Sequence)
           - OR when right-clicking on column 1 with no selection
        3. Check console output for debug information
        """)
        layout.addWidget(instructions)
        
        # Create table view
        self.table = MdTableView()
        
        # Create model with test data
        model = QStandardItemModel(5, 4)
        model.setHorizontalHeaderLabels(["ID", "Sequence", "Name", "Other"])
        
        # Fill with test data
        for i in range(5):
            model.setItem(i, 0, QStandardItem(str(i+1)))
            model.setItem(i, 1, QStandardItem(""))  # Empty sequence column
            model.setItem(i, 2, QStandardItem(f"Object {i+1}"))
            model.setItem(i, 3, QStandardItem(f"Data {i+1}"))
        
        self.table.setModel(model)
        layout.addWidget(self.table)
        
        # Add test buttons
        btn1 = QPushButton("Test 1: Select sequence column cells")
        btn1.clicked.connect(self.test_sequence_column)
        layout.addWidget(btn1)
        
        btn2 = QPushButton("Test 2: Select mixed column cells") 
        btn2.clicked.connect(self.test_mixed_columns)
        layout.addWidget(btn2)
        
        btn3 = QPushButton("Test 3: Select ID column cells")
        btn3.clicked.connect(self.test_id_column)
        layout.addWidget(btn3)
        
        btn4 = QPushButton("Test 4: Context menu on sequence column")
        btn4.clicked.connect(self.test_context_sequence)
        layout.addWidget(btn4)
        
        btn5 = QPushButton("Test 5: Context menu on other column")
        btn5.clicked.connect(self.test_context_other)
        layout.addWidget(btn5)
    
    def test_sequence_column(self):
        """Select multiple cells in sequence column (should show Fill Sequence)"""
        print("\n" + "="*60)
        print("TEST 1: Selecting multiple cells in sequence column")
        print("Expected: Fill Sequence should be available")
        print("="*60)
        
        selection = self.table.selectionModel()
        selection.clear()
        model = self.table.model()
        
        for row in range(3):
            index = model.index(row, 1)  # Column 1 = Sequence
            selection.select(index, selection.Select)
        
        # Trigger context menu
        pos = QPoint(100, 50)  # Position in sequence column
        self.table.show_context_menu(pos)
    
    def test_mixed_columns(self):
        """Select cells across multiple columns (should NOT show Fill Sequence)"""
        print("\n" + "="*60)
        print("TEST 2: Selecting cells across multiple columns")
        print("Expected: Fill Sequence should NOT be available")
        print("="*60)
        
        selection = self.table.selectionModel()
        selection.clear()
        model = self.table.model()
        
        # Select cells in different columns
        selection.select(model.index(0, 0), selection.Select)  # ID column
        selection.select(model.index(0, 1), selection.Select)  # Sequence column
        selection.select(model.index(1, 2), selection.Select)  # Name column
        
        # Trigger context menu
        pos = QPoint(100, 50)
        self.table.show_context_menu(pos)
    
    def test_id_column(self):
        """Select cells in ID column (should NOT show Fill Sequence)"""
        print("\n" + "="*60)
        print("TEST 3: Selecting multiple cells in ID column")
        print("Expected: Fill Sequence should NOT be available")
        print("="*60)
        
        selection = self.table.selectionModel()
        selection.clear()
        model = self.table.model()
        
        for row in range(3):
            index = model.index(row, 0)  # Column 0 = ID
            selection.select(index, selection.Select)
        
        # Trigger context menu
        pos = QPoint(50, 50)  # Position in ID column
        self.table.show_context_menu(pos)
    
    def test_context_sequence(self):
        """Right-click on sequence column with no selection (should show Fill Sequence)"""
        print("\n" + "="*60)
        print("TEST 4: Right-click on sequence column (no selection)")
        print("Expected: Fill Sequence should be available")
        print("="*60)
        
        selection = self.table.selectionModel()
        selection.clear()
        
        # Simulate right-click on sequence column
        pos = QPoint(150, 50)  # Position in sequence column
        self.table.show_context_menu(pos)
    
    def test_context_other(self):
        """Right-click on other column with no selection (should NOT show Fill Sequence)"""
        print("\n" + "="*60)
        print("TEST 5: Right-click on other column (no selection)")
        print("Expected: Fill Sequence should NOT be available")
        print("="*60)
        
        selection = self.table.selectionModel()
        selection.clear()
        
        # Simulate right-click on name column
        pos = QPoint(250, 50)  # Position in name column
        self.table.show_context_menu(pos)

def main():
    app = QApplication(sys.argv)
    
    window = ConditionalContextMenuTest()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())