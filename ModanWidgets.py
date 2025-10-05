"""
Custom widgets for Modan2 application.
Reusable UI components separated from the main window.
"""
import logging
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import MdModel


class DatasetTreeWidget(QTreeWidget):
    """Enhanced tree widget for displaying datasets and analyses."""
    
    # Signals
    dataset_selected = pyqtSignal(object)       # MdDataset
    analysis_selected = pyqtSignal(object)      # MdAnalysis
    dataset_context_menu = pyqtSignal(object, QPoint)  # MdDataset, position
    analysis_context_menu = pyqtSignal(object, QPoint) # MdAnalysis, position
    
    def __init__(self, parent=None):
        """Initialize dataset tree widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup tree widget UI."""
        self.setHeaderLabels(['Name', 'Objects', 'Type', 'Created'])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        # Column widths
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def add_dataset(self, dataset: MdModel.MdDataset) -> QTreeWidgetItem:
        """Add dataset to tree.
        
        Args:
            dataset: Dataset to add
            
        Returns:
            Created tree item
        """
        item = QTreeWidgetItem(self)
        item.setText(0, dataset.dataset_name)
        item.setText(1, str(dataset.object_list.count()))
        item.setText(2, f"{dataset.dimension}D")
        item.setText(3, dataset.created_at.strftime("%Y-%m-%d"))
        item.setData(0, Qt.UserRole, dataset)
        item.setData(0, Qt.UserRole + 1, 'dataset')  # Type indicator
        
        # Set icon
        icon_name = 'M2Dataset2D_3.png' if dataset.dimension == 2 else 'M2Dataset3D_4.png'
        icon_path = Path(__file__).parent / 'icons' / icon_name
        if icon_path.exists():
            item.setIcon(0, QIcon(str(icon_path)))
        
        # Set tooltip
        first_obj = dataset.object_list.first()
        landmark_count = len(first_obj.landmark_list) if first_obj and first_obj.landmark_list else 0
        tooltip = f"Dataset: {dataset.dataset_name}\\nDimension: {dataset.dimension}D\\n" \
                 f"Landmarks: {landmark_count}\\nObjects: {dataset.object_list.count()}"
        item.setToolTip(0, tooltip)
        
        # Add analyses as children
        for analysis in dataset.analyses:
            self.add_analysis(item, analysis)
        
        return item
    
    def add_analysis(self, parent_item: QTreeWidgetItem, analysis: MdModel.MdAnalysis) -> QTreeWidgetItem:
        """Add analysis result to tree.
        
        Args:
            parent_item: Parent dataset item
            analysis: Analysis to add
            
        Returns:
            Created tree item
        """
        item = QTreeWidgetItem(parent_item)
        item.setText(0, analysis.analysis_name)
        item.setText(1, "-")
        item.setText(2, "Analysis")
        item.setText(3, analysis.created_at.strftime("%Y-%m-%d %H:%M"))
        item.setData(0, Qt.UserRole, analysis)
        item.setData(0, Qt.UserRole + 1, 'analysis')  # Type indicator
        
        # Set icon
        icon_path = Path(__file__).parent / 'icons' / 'M2Analysis_1.png'
        if icon_path.exists():
            item.setIcon(0, QIcon(str(icon_path)))
        
        # Set tooltip
        tooltip = f"Analysis: {analysis.analysis_name}\\nCreated: {analysis.created_at}"
        item.setToolTip(0, tooltip)
        
        return item
    
    def remove_dataset(self, dataset_id: int):
        """Remove dataset from tree.
        
        Args:
            dataset_id: ID of dataset to remove
        """
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            dataset = item.data(0, Qt.UserRole)
            
            if dataset and dataset.id == dataset_id:
                self.takeTopLevelItem(i)
                break
    
    def refresh_dataset(self, dataset: MdModel.MdDataset):
        """Refresh dataset item in tree.
        
        Args:
            dataset: Dataset to refresh
        """
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item_dataset = item.data(0, Qt.UserRole)
            
            if item_dataset and item_dataset.id == dataset.id:
                # Update object count
                item.setText(1, str(dataset.object_list.count()))
                
                # Refresh analyses
                item.takeChildren()
                for analysis in dataset.analyses:
                    self.add_analysis(item, analysis)
                break
    
    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.selectedItems()
        if items:
            item = items[0]
            data = item.data(0, Qt.UserRole)
            item_type = item.data(0, Qt.UserRole + 1)
            
            self.logger.info(f"Selection changed: item_type={item_type}, data={data}")
            
            if item_type == 'dataset' and isinstance(data, MdModel.MdDataset):
                self.logger.info(f"Emitting dataset_selected signal for: {data.dataset_name}")
                self.dataset_selected.emit(data)
            elif item_type == 'analysis' and isinstance(data, MdModel.MdAnalysis):
                self.logger.info(f"Emitting analysis_selected signal for: {data.analysis_name}")
                self.analysis_selected.emit(data)
    
    def _show_context_menu(self, position: QPoint):
        """Show context menu at position.
        
        Args:
            position: Mouse position for menu
        """
        item = self.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        item_type = item.data(0, Qt.UserRole + 1)
        
        if item_type == 'dataset':
            self.dataset_context_menu.emit(data, self.mapToGlobal(position))
        elif item_type == 'analysis':
            self.analysis_context_menu.emit(data, self.mapToGlobal(position))
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double click.
        
        Args:
            item: Clicked item
            column: Clicked column
        """
        data = item.data(0, Qt.UserRole)
        item_type = item.data(0, Qt.UserRole + 1)
        
        if item_type == 'analysis':
            # Double-click on analysis shows results
            self.analysis_selected.emit(data)


class ObjectTableWidget(QTableWidget):
    """Enhanced table widget for displaying objects."""
    
    # Signals
    object_selected = pyqtSignal(object)        # MdObject
    objects_dropped = pyqtSignal(list)          # List of file paths
    object_context_menu = pyqtSignal(object, QPoint)  # MdObject, position
    
    def __init__(self, parent=None):
        """Initialize object table widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._setup_drag_drop()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup table widget UI."""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setGridStyle(Qt.SolidLine)
        
        # Column setup
        self.setColumnCount(6)
        headers = ['Name', 'Type', 'Landmarks', 'Size', 'Modified', 'Status']
        self.setHorizontalHeaderLabels(headers)
        
        # Column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality."""
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setDefaultDropAction(Qt.CopyAction)
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)
    
    def add_object(self, obj: MdModel.MdObject):
        """Add object to table.
        
        Args:
            obj: Object to add
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(obj.object_name)
        name_item.setData(Qt.UserRole, obj)
        self.setItem(row, 0, name_item)
        
        # Type
        obj_type = self._get_object_type(obj)
        type_item = QTableWidgetItem(obj_type)
        self.setItem(row, 1, type_item)
        
        # Landmarks
        landmark_count = len(obj.landmarks) if obj.landmarks else 0
        landmarks_item = QTableWidgetItem(str(landmark_count))
        landmarks_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 2, landmarks_item)
        
        # Size
        size_text = self._get_object_size(obj)
        size_item = QTableWidgetItem(size_text)
        size_item.setTextAlignment(Qt.AlignRight)
        self.setItem(row, 3, size_item)
        
        # Modified time
        modified_item = QTableWidgetItem(obj.modified_at.strftime("%Y-%m-%d %H:%M"))
        modified_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 4, modified_item)
        
        # Status
        status_text = self._get_object_status(obj)
        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 5, status_item)
        
        # Set row colors based on status
        self._set_row_color(row, obj)
    
    def _get_object_type(self, obj: MdModel.MdObject) -> str:
        """Get object type string.
        
        Args:
            obj: Object to analyze
            
        Returns:
            Type string
        """
        if obj.image:
            return "Image"
        elif obj.model_3d:
            return "3D Model"
        elif obj.landmarks:
            return "Landmarks"
        else:
            return "Empty"
    
    def _get_object_size(self, obj: MdModel.MdObject) -> str:
        """Get object size string.
        
        Args:
            obj: Object to analyze
            
        Returns:
            Size string
        """
        if obj.image:
            return f"{obj.image.width}×{obj.image.height}"
        elif obj.model_3d:
            return f"{obj.model_3d.vertex_count} vertices"
        elif obj.landmarks:
            return f"{len(obj.landmarks)} points"
        else:
            return "-"
    
    def _get_object_status(self, obj: MdModel.MdObject) -> str:
        """Get object status string.
        
        Args:
            obj: Object to analyze
            
        Returns:
            Status string
        """
        if obj.landmarks and len(obj.landmarks) > 0:
            return "✓ Ready"
        elif obj.image or obj.model_3d:
            return "⚠ No landmarks"
        else:
            return "✗ Empty"
    
    def _set_row_color(self, row: int, obj: MdModel.MdObject):
        """Set row background color based on object status.
        
        Args:
            row: Table row index
            obj: Object for color determination
        """
        if obj.landmarks and len(obj.landmarks) > 0:
            # Green tint for ready objects
            color = QColor(240, 255, 240)
        elif obj.image or obj.model_3d:
            # Yellow tint for objects without landmarks
            color = QColor(255, 255, 240)
        else:
            # Red tint for empty objects
            color = QColor(255, 240, 240)
        
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(color)
    
    def update_object(self, obj: MdModel.MdObject):
        """Update object in table.
        
        Args:
            obj: Updated object
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.data(Qt.UserRole) == obj:
                # Update all columns
                item.setText(obj.object_name)
                self.item(row, 1).setText(self._get_object_type(obj))
                self.item(row, 2).setText(str(len(obj.landmarks) if obj.landmarks else 0))
                self.item(row, 3).setText(self._get_object_size(obj))
                self.item(row, 4).setText(obj.modified_at.strftime("%Y-%m-%d %H:%M"))
                self.item(row, 5).setText(self._get_object_status(obj))
                
                # Update row color
                self._set_row_color(row, obj)
                break
    
    def remove_object(self, object_id: int):
        """Remove object from table.
        
        Args:
            object_id: ID of object to remove
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            obj = item.data(Qt.UserRole) if item else None
            
            if obj and obj.id == object_id:
                self.removeRow(row)
                break
    
    def clear_objects(self):
        """Clear all objects from table."""
        self.setRowCount(0)
    
    def get_selected_object(self) -> MdModel.MdObject | None:
        """Get currently selected object.
        
        Returns:
            Selected object or None
        """
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.item(current_row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None
    
    def _on_selection_changed(self):
        """Handle selection change."""
        obj = self.get_selected_object()
        if obj:
            self.object_selected.emit(obj)
    
    def _show_context_menu(self, position: QPoint):
        """Show context menu at position.
        
        Args:
            position: Mouse position for menu
        """
        item = self.itemAt(position)
        if item:
            obj = item.data(Qt.UserRole)
            if obj:
                self.object_context_menu.emit(obj, self.mapToGlobal(position))
    
    def _on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double click.
        
        Args:
            row: Clicked row
            column: Clicked column
        """
        if column == 0:  # Name column
            item = self.item(row, 0)
            if item:
                obj = item.data(Qt.UserRole)
                if obj:
                    self.object_selected.emit(obj)
    
    # Drag and Drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if files are supported
            urls = event.mimeData().urls()
            supported_files = []
            
            for url in urls:
                file_path = url.toLocalFile()
                ext = Path(file_path).suffix.lower()
                
                if ext in ['.tps', '.nts', '.txt', '.jpg', '.jpeg', '.png', 
                          '.bmp', '.tiff', '.obj', '.ply', '.stl']:
                    supported_files.append(file_path)
            
            if supported_files:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if Path(file_path).exists():
                    file_paths.append(file_path)
            
            if file_paths:
                self.objects_dropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()


class LandmarkViewer2D(QWidget):
    """2D landmark viewer widget."""
    
    # Signals
    landmark_clicked = pyqtSignal(int)          # landmark_index
    landmark_moved = pyqtSignal(int, QPointF)   # landmark_index, new_position
    
    def __init__(self, parent=None):
        """Initialize 2D viewer."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.landmarks = []
        self.wireframe = []
        self.image = None
        
        self.landmark_size = 3
        self.landmark_color = QColor(255, 0, 0)
        self.wireframe_color = QColor(0, 0, 255)
        self.selection_color = QColor(0, 255, 0)
        
        self.selected_landmark = -1
        self.dragging = False
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
    
    def set_object(self, obj: MdModel.MdObject):
        """Set object to display.
        
        Args:
            obj: Object to display
        """
        self.landmarks = obj.landmarks if obj.landmarks else []
        self.image = obj.image
        self.selected_landmark = -1
        self.update()
    
    def set_landmark_style(self, size: int = 3, color: QColor = None):
        """Set landmark display style.
        
        Args:
            size: Landmark point size
            color: Landmark color
        """
        self.landmark_size = size
        if color:
            self.landmark_color = color
        self.update()
    
    def set_wireframe(self, wireframe_data: list[tuple[int, int]]):
        """Set wireframe connections.
        
        Args:
            wireframe_data: List of (point1_idx, point2_idx) tuples
        """
        self.wireframe = wireframe_data
        self.update()
    
    def paintEvent(self, event):
        """Paint the viewer content."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.landmarks:
            # Draw "No data" message
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(
                self.rect(), 
                Qt.AlignCenter, 
                "No landmarks to display\\nDrop files here to import"
            )
            return
        
        # Calculate scaling to fit landmarks
        self._calculate_transform(painter)
        
        # Draw wireframe
        if self.wireframe:
            self._draw_wireframe(painter)
        
        # Draw landmarks
        self._draw_landmarks(painter)
        
        # Draw landmark numbers if enabled
        self._draw_landmark_numbers(painter)
    
    def _calculate_transform(self, painter):
        """Calculate transformation to fit landmarks in widget."""
        if not self.landmarks:
            return
        
        # Get bounding box
        min_x = min(pt[0] for pt in self.landmarks)
        max_x = max(pt[0] for pt in self.landmarks)
        min_y = min(pt[1] for pt in self.landmarks)
        max_y = max(pt[1] for pt in self.landmarks)
        
        # Add margins
        margin = 20
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        # Calculate scale
        data_width = max_x - min_x
        data_height = max_y - min_y
        
        if data_width > 0 and data_height > 0:
            scale_x = width / data_width
            scale_y = height / data_height
            self.scale = min(scale_x, scale_y)
        else:
            self.scale = 1.0
        
        # Calculate offset
        self.offset_x = margin + (width - data_width * self.scale) / 2 - min_x * self.scale
        self.offset_y = margin + (height - data_height * self.scale) / 2 - min_y * self.scale
    
    def _transform_point(self, point) -> QPointF:
        """Transform landmark point to widget coordinates."""
        x = point[0] * self.scale + self.offset_x
        y = point[1] * self.scale + self.offset_y
        return QPointF(x, y)
    
    def _draw_wireframe(self, painter):
        """Draw wireframe connections."""
        if not self.wireframe or len(self.landmarks) < 2:
            return
        
        painter.setPen(QPen(self.wireframe_color, 1))
        
        for pt1_idx, pt2_idx in self.wireframe:
            if 0 <= pt1_idx < len(self.landmarks) and 0 <= pt2_idx < len(self.landmarks):
                pt1 = self._transform_point(self.landmarks[pt1_idx])
                pt2 = self._transform_point(self.landmarks[pt2_idx])
                painter.drawLine(pt1, pt2)
    
    def _draw_landmarks(self, painter):
        """Draw landmark points."""
        for i, landmark in enumerate(self.landmarks):
            pt = self._transform_point(landmark)
            
            # Choose color
            if i == self.selected_landmark:
                color = self.selection_color
                size = self.landmark_size + 2
            else:
                color = self.landmark_color
                size = self.landmark_size
            
            # Draw point
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt, size, size)
    
    def _draw_landmark_numbers(self, painter):
        """Draw landmark numbers."""
        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        for i, landmark in enumerate(self.landmarks):
            pt = self._transform_point(landmark)
            
            # Draw number slightly offset from point
            text_rect = QRectF(pt.x() + 5, pt.y() - 15, 20, 15)
            painter.drawText(text_rect, Qt.AlignCenter, str(i + 1))
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            # Find closest landmark
            pos = event.pos()
            closest_idx = self._find_closest_landmark(pos)
            
            if closest_idx >= 0:
                self.selected_landmark = closest_idx
                self.landmark_clicked.emit(closest_idx)
                self.dragging = True
                self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if self.dragging and self.selected_landmark >= 0:
            # Update landmark position
            new_pos = self._untransform_point(event.pos())
            if 0 <= self.selected_landmark < len(self.landmarks):
                self.landmarks[self.selected_landmark] = [new_pos.x(), new_pos.y()]
                self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if self.dragging and self.selected_landmark >= 0:
            new_pos = self._untransform_point(event.pos())
            self.landmark_moved.emit(self.selected_landmark, new_pos)
        
        self.dragging = False
    
    def _find_closest_landmark(self, pos: QPoint) -> int:
        """Find closest landmark to mouse position.
        
        Args:
            pos: Mouse position
            
        Returns:
            Index of closest landmark or -1 if none close enough
        """
        min_distance = float('inf')
        closest_idx = -1
        
        for i, landmark in enumerate(self.landmarks):
            pt = self._transform_point(landmark)
            distance = ((pos.x() - pt.x()) ** 2 + (pos.y() - pt.y()) ** 2) ** 0.5
            
            if distance < 10 and distance < min_distance:  # 10 pixel threshold
                min_distance = distance
                closest_idx = i
        
        return closest_idx
    
    def _untransform_point(self, widget_point: QPoint) -> QPointF:
        """Transform widget coordinates back to landmark coordinates."""
        x = (widget_point.x() - self.offset_x) / self.scale
        y = (widget_point.y() - self.offset_y) / self.scale
        return QPointF(x, y)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        selected_items = self.selectedItems()
        if selected_items:
            # Get object from first selected item
            row = selected_items[0].row()
            item = self.item(row, 0)
            if item:
                obj = item.data(Qt.UserRole)
                if obj:
                    self.object_selected.emit(obj)
    
    def _show_context_menu(self, position: QPoint):
        """Show context menu.
        
        Args:
            position: Menu position
        """
        item = self.itemAt(position)
        if item:
            obj = item.data(Qt.UserRole)
            if obj:
                self.object_context_menu.emit(obj, self.mapToGlobal(position))


class AnalysisResultWidget(QWidget):
    """Widget for displaying analysis results."""
    
    def __init__(self, parent=None):
        """Initialize analysis result widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.analysis = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup result widget UI."""
        layout = QVBoxLayout(self)
        
        # Title label
        self.title_label = QLabel("Analysis Results")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.title_label)
        
        # Tab widget for different result views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Summary tab
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.tab_widget.addTab(self.summary_text, "Summary")
        
        # Data table tab
        self.data_table = QTableWidget()
        self.tab_widget.addTab(self.data_table, "Data")
        
        # Visualization tab (placeholder)
        self.viz_widget = QWidget()
        self.tab_widget.addTab(self.viz_widget, "Visualization")
    
    def set_analysis(self, analysis: MdModel.MdAnalysis):
        """Set analysis to display.
        
        Args:
            analysis: Analysis result to display
        """
        self.analysis = analysis
        
        self.title_label.setText(f"{analysis.analysis_type} Analysis Results")
        
        # Update summary
        self._update_summary()
        
        # Update data table
        self._update_data_table()
        
        # Update visualization
        self._update_visualization()
    
    def _update_summary(self):
        """Update summary tab."""
        if not self.analysis:
            return
        
        summary = f"""
<h3>{self.analysis.analysis_type} Analysis</h3>
<p><b>Dataset:</b> {self.analysis.dataset.dataset_name}</p>
<p><b>Created:</b> {self.analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><b>Objects analyzed:</b> {len(self.analysis.object_names or [])}</p>

<h4>Parameters</h4>
<ul>
"""
        
        for key, value in (self.analysis.parameters or {}).items():
            summary += f"<li><b>{key}:</b> {value}</li>\\n"
        
        summary += "</ul>\\n<h4>Results</h4>\\n"
        
        # Add analysis-specific summary
        if self.analysis.analysis_type == 'PCA':
            summary += self._get_pca_summary()
        elif self.analysis.analysis_type == 'CVA':
            summary += self._get_cva_summary()
        elif self.analysis.analysis_type == 'MANOVA':
            summary += self._get_manova_summary()
        
        self.summary_text.setHtml(summary)
    
    def _get_pca_summary(self) -> str:
        """Get PCA-specific summary."""
        results = self.analysis.results or {}
        
        eigenvalues = results.get('eigenvalues', [])
        explained_var = results.get('explained_variance_ratio', [])
        
        summary = "<ul>\\n"
        summary += f"<li><b>Components:</b> {len(eigenvalues)}</li>\\n"
        
        if explained_var:
            total_var = sum(explained_var[:3]) * 100  # First 3 components
            summary += f"<li><b>Variance explained (PC1-3):</b> {total_var:.1f}%</li>\\n"
        
        summary += "</ul>\\n"
        return summary
    
    def _get_cva_summary(self) -> str:
        """Get CVA-specific summary."""
        results = self.analysis.results or {}
        accuracy = results.get('accuracy', 0.0)
        
        return f"<ul>\\n<li><b>Classification accuracy:</b> {accuracy:.1f}%</li>\\n</ul>\\n"
    
    def _get_manova_summary(self) -> str:
        """Get MANOVA-specific summary."""
        results = self.analysis.results or {}
        
        p_value = results.get('p_value', 0.0)
        f_stat = results.get('f_statistic', 0.0)
        
        significance = "Significant" if p_value < 0.05 else "Not significant"
        
        return f"""<ul>
<li><b>F-statistic:</b> {f_stat:.4f}</li>
<li><b>P-value:</b> {p_value:.4f}</li>
<li><b>Result:</b> {significance}</li>
</ul>
"""
    
    def _update_data_table(self):
        """Update data table tab."""
        if not self.analysis or not self.analysis.results:
            return
        
        results = self.analysis.results
        
        if self.analysis.analysis_type == 'PCA':
            self._populate_pca_table(results)
        elif self.analysis.analysis_type == 'CVA':
            self._populate_cva_table(results)
    
    def _populate_pca_table(self, results: dict[str, Any]):
        """Populate table with PCA results."""
        scores = results.get('scores', [])
        if not scores:
            return
        
        n_objects = len(scores)
        n_components = len(scores[0]) if scores else 0
        
        self.data_table.setRowCount(n_objects)
        self.data_table.setColumnCount(n_components + 1)
        
        # Headers
        headers = ['Object'] + [f'PC{i+1}' for i in range(n_components)]
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # Data
        object_names = self.analysis.object_names or [f"Object_{i+1}" for i in range(n_objects)]
        
        for i, (name, score_row) in enumerate(zip(object_names, scores)):
            self.data_table.setItem(i, 0, QTableWidgetItem(name))
            
            for j, score in enumerate(score_row):
                item = QTableWidgetItem(f"{score:.4f}")
                item.setTextAlignment(Qt.AlignRight)
                self.data_table.setItem(i, j + 1, item)
    
    def _populate_cva_table(self, results: dict[str, Any]):
        """Populate table with CVA results."""
        # Similar to PCA but with canonical variables
        cv_scores = results.get('canonical_variables', [])
        if not cv_scores:
            return
        
        n_objects = len(cv_scores)
        n_cvs = len(cv_scores[0]) if cv_scores else 0
        
        self.data_table.setRowCount(n_objects)
        self.data_table.setColumnCount(n_cvs + 1)
        
        # Headers
        headers = ['Object'] + [f'CV{i+1}' for i in range(n_cvs)]
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # Data
        object_names = self.analysis.object_names or [f"Object_{i+1}" for i in range(n_objects)]
        
        for i, (name, cv_row) in enumerate(zip(object_names, cv_scores)):
            self.data_table.setItem(i, 0, QTableWidgetItem(name))
            
            for j, cv_value in enumerate(cv_row):
                item = QTableWidgetItem(f"{cv_value:.4f}")
                item.setTextAlignment(Qt.AlignRight)
                self.data_table.setItem(i, j + 1, item)
    
    def _update_visualization(self):
        """Update visualization tab."""
        # Placeholder for future matplotlib integration
        pass


class ProgressIndicator(QWidget):
    """Custom progress indicator widget."""
    
    def __init__(self, parent=None):
        """Initialize progress indicator."""
        super().__init__(parent)
        self.setFixedSize(100, 20)
        
        self.progress = 0
        self.text = ""
        self.active = False
    
    def set_progress(self, value: int, text: str = ""):
        """Set progress value and text.
        
        Args:
            value: Progress value (0-100)
            text: Progress text
        """
        self.progress = max(0, min(100, value))
        self.text = text
        self.active = True
        self.update()
    
    def hide_progress(self):
        """Hide progress indicator."""
        self.active = False
        self.update()
    
    def paintEvent(self, event):
        """Paint progress indicator."""
        if not self.active:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(self.rect())
        
        # Progress bar
        if self.progress > 0:
            progress_width = int(self.width() * self.progress / 100)
            progress_rect = QRect(0, 0, progress_width, self.height())
            painter.fillRect(progress_rect, QColor(100, 150, 255))
        
        # Text
        if self.text:
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, self.text)