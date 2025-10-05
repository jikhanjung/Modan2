# Readonly Columns Context Menu Implementation

**Date**: 2025-08-30
**Author**: Claude
**Type**: Feature Implementation

## Overview

Implemented conditional context menus for readonly columns in MdTableView. Columns with headers "name", "count", "csize" now display only the Copy option in their context menu, while other columns continue to show the full menu.

## Problem Statement

User requested that certain columns (name, count, csize) should be treated as readonly and only allow copying data, not editing operations like paste, fill value, or clear.

## Implementation Details

### Modified Files

#### ModanComponents.py - MdTableView.show_context_menu()

Added column header detection and conditional menu building:

```python
# Check if this is a read-only column (name, count, csize)
readonly_columns = ['name', 'count', 'csize']
column_header_lower = str(column_header).lower().strip()
is_readonly_column = column_header_lower in readonly_columns

# Log column type for debugging
if is_readonly_column:
    logging.info(f"Context menu for column '{column_header}' (read-only): Copy")
else:
    menu_items = ["Copy"]
    if not is_readonly_column:
        menu_items.extend(["Paste", "Fill value", "Clear"])
        if column == 1:  # Sequence column
            menu_items.insert(-2, "Fill sequence")  # Add before Fill value
    logging.info(f"Context menu for column '{column_header}' (editable): {', '.join(menu_items)}")

menu = QMenu(self)
menu.addAction(self.copy_action)

# Only add paste and other actions if not a read-only column
if not is_readonly_column:
    menu.addAction(self.paste_action)

    # Add Fill sequence for sequence column (column 1)
    if column == 1:
        if hasattr(self, 'fill_sequence_action'):
            menu.addAction(self.fill_sequence_action)

    menu.addAction(self.fill_value_action)
    menu.addAction(self.clear_action)
```

### Key Features

1. **Column Header Detection**: Extracts column header text and normalizes to lowercase for comparison
2. **Readonly Column List**: Maintains list of readonly columns: ['name', 'count', 'csize']
3. **Conditional Menu Building**: Only adds Copy action for readonly columns, full menu for others
4. **Sequence Column Support**: Preserves Fill sequence functionality for sequence column (column 1)
5. **Comprehensive Logging**: Logs menu type and available actions for debugging

### Test Implementation

Created `test_readonly_columns.py` to verify functionality:
- Tests context menus for ID, Sequence, Name, Count, CSize, and Other columns
- Includes manual test buttons and visual verification
- Comprehensive logging for debugging

## Testing Results

Verification confirmed correct behavior:
- **Name column**: "Context menu for column 'Name' (read-only): Copy" ✅
- **Count column**: "Context menu for column 'Count' (read-only): Copy" ✅
- **CSize column**: Should show same behavior (tested via UI)
- **Other columns**: "Context menu for column 'Other' (editable): Copy, Paste, Fill value, Clear" ✅

## Technical Notes

1. **Case Insensitive Matching**: Column headers are normalized to lowercase for robust comparison
2. **Whitespace Handling**: Headers are stripped of leading/trailing whitespace
3. **Backward Compatibility**: Non-readonly columns retain full functionality
4. **Sequence Column Preservation**: Fill sequence functionality preserved for sequence column

## Code Quality

- Added comprehensive logging for debugging and monitoring
- Maintained existing code structure and patterns
- Preserved all existing functionality for non-readonly columns
- Clean, readable implementation with clear variable names

## User Impact

Users can now safely interact with readonly columns (name, count, csize) without accidentally modifying critical data, while maintaining full editing capabilities for other columns.
