#!/usr/bin/env python3
"""
Test readonly columns context menu functionality
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, '/home/jikhanjung/projects/Modan2')
from ModanComponents import MdTableView

class ReadOnlyColumnsTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Read-Only Columns Context Menu Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Add instructions
        instructions = QLabel("""
        Test Instructions:
        1. Right-click on different columns to test context menu
        2. Read-only columns (name, count, csize) should only show "Copy"
        3. Other columns should show full context menu (Copy, Paste, Fill value, Clear)
        4. Sequence column should also show "Fill sequence" when selected
        5. Check console output for detailed logging
        """)
        layout.addWidget(instructions)
        
        # Create table view
        self.table = MdTableView()
        
        # Create model with test data including readonly columns
        model = QStandardItemModel(6, 7)
        headers = ["ID", "Sequence", "Name", "Count", "CSize", "Other", "Data"]
        model.setHorizontalHeaderLabels(headers)
        
        # Fill with test data
        for i in range(6):
            model.setItem(i, 0, QStandardItem(str(i+1)))              # ID
            model.setItem(i, 1, QStandardItem(""))                    # Sequence (empty)
            model.setItem(i, 2, QStandardItem(f"Object_{i+1}"))       # Name (readonly)
            model.setItem(i, 3, QStandardItem(str(i+10)))             # Count (readonly)
            model.setItem(i, 4, QStandardItem(f"{i*1.5:.2f}"))        # CSize (readonly)
            model.setItem(i, 5, QStandardItem(f"Other_{i+1}"))        # Other (editable)
            model.setItem(i, 6, QStandardItem(f"Data_{i+1}"))         # Data (editable)
        
        self.table.setModel(model)
        layout.addWidget(self.table)
        
        # Add test buttons for each column type
        btn1 = QPushButton("Test 1: Right-click on ID column")
        btn1.clicked.connect(self.test_id_column)
        layout.addWidget(btn1)
        
        btn2 = QPushButton("Test 2: Right-click on Sequence column")
        btn2.clicked.connect(self.test_sequence_column)
        layout.addWidget(btn2)
        
        btn3 = QPushButton("Test 3: Right-click on Name column (read-only)")
        btn3.clicked.connect(self.test_name_column)
        layout.addWidget(btn3)
        
        btn4 = QPushButton("Test 4: Right-click on Count column (read-only)")
        btn4.clicked.connect(self.test_count_column)
        layout.addWidget(btn4)
        
        btn5 = QPushButton("Test 5: Right-click on CSize column (read-only)")
        btn5.clicked.connect(self.test_csize_column)
        layout.addWidget(btn5)
        
        btn6 = QPushButton("Test 6: Right-click on Other column (editable)")
        btn6.clicked.connect(self.test_other_column)
        layout.addWidget(btn6)
    
    def test_id_column(self):
        """Test context menu on ID column (should be full menu)"""
        print("\\n" + "="*60)
        print("TEST 1: Right-clicking on ID column")
        print("Expected: Full context menu (Copy, Paste, Fill value, Clear)")
        print("="*60)
        
        # Calculate approximate position for ID column
        pos = QPoint(50, 50)
        self.table.show_context_menu(pos)
    
    def test_sequence_column(self):
        """Test context menu on Sequence column (should include Fill sequence)"""
        print("\\n" + "="*60)
        print("TEST 2: Right-clicking on Sequence column")
        print("Expected: Full menu with Fill sequence (Copy, Paste, Fill sequence, Fill value, Clear)")
        print("="*60)
        
        # Calculate approximate position for Sequence column
        pos = QPoint(120, 50)
        self.table.show_context_menu(pos)
    
    def test_name_column(self):
        """Test context menu on Name column (read-only, should be copy only)"""
        print("\\n" + "="*60)
        print("TEST 3: Right-clicking on Name column (READ-ONLY)")
        print("Expected: Copy only")
        print("="*60)
        
        # Calculate approximate position for Name column
        pos = QPoint(200, 50)
        self.table.show_context_menu(pos)
    
    def test_count_column(self):
        """Test context menu on Count column (read-only, should be copy only)"""
        print("\\n" + "="*60)
        print("TEST 4: Right-clicking on Count column (READ-ONLY)")
        print("Expected: Copy only")
        print("="*60)
        
        # Calculate approximate position for Count column  
        pos = QPoint(280, 50)
        self.table.show_context_menu(pos)
    
    def test_csize_column(self):
        """Test context menu on CSize column (read-only, should be copy only)"""
        print("\\n" + "="*60)
        print("TEST 5: Right-clicking on CSize column (READ-ONLY)")
        print("Expected: Copy only")
        print("="*60)
        
        # Calculate approximate position for CSize column
        pos = QPoint(360, 50)
        self.table.show_context_menu(pos)
    
    def test_other_column(self):
        """Test context menu on Other column (should be full menu)"""
        print("\\n" + "="*60)
        print("TEST 6: Right-clicking on Other column (editable)")
        print("Expected: Full context menu (Copy, Paste, Fill value, Clear)")
        print("="*60)
        
        # Calculate approximate position for Other column
        pos = QPoint(440, 50)
        self.table.show_context_menu(pos)

def main():
    app = QApplication(sys.argv)
    
    print("Starting Read-Only Columns Context Menu Test")
    print("Watch console for detailed logging information")
    
    window = ReadOnlyColumnsTest()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())