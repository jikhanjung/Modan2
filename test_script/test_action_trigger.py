#!/usr/bin/env python3
"""
Test action triggering directly
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, '/home/jikhanjung/projects/Modan2')

def test_action_connection():
    """Test if fill_sequence_action is properly connected"""
    
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QStandardItemModel, QStandardItem
    from ModanComponents import MdTableView
    
    app = QApplication(sys.argv)
    
    print("Creating MdTableView...")
    table = MdTableView()
    
    # Create model
    model = QStandardItemModel(3, 3)
    model.setHorizontalHeaderLabels(["ID", "Sequence", "Name"])
    
    for i in range(3):
        model.setItem(i, 0, QStandardItem(str(i+1)))
        model.setItem(i, 1, QStandardItem(""))
        model.setItem(i, 2, QStandardItem(f"Object {i+1}"))
    
    table.setModel(model)
    
    # Select some cells in sequence column
    selection = table.selectionModel()
    for row in range(3):
        index = model.index(row, 1)
        selection.select(index, selection.Select)
    
    print(f"Selected {len(table.selectionModel().selectedIndexes())} cells in sequence column")
    
    # Check if action exists
    print(f"fill_sequence_action exists: {hasattr(table, 'fill_sequence_action')}")
    print(f"fill_sequence method exists: {hasattr(table, 'fill_sequence')}")
    
    if hasattr(table, 'fill_sequence_action'):
        print(f"Action text: {table.fill_sequence_action.text()}")
        print(f"Action enabled: {table.fill_sequence_action.isEnabled()}")
        
        # Try to trigger the action directly
        print("Triggering action directly...")
        table.fill_sequence_action.trigger()
        
    print("Test completed")

if __name__ == "__main__":
    test_action_connection()