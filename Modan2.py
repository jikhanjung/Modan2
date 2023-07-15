from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QStatusBar, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QInputDialog


from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent, QDrag
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray, QPoint, QModelIndex, \
                         pyqtSignal, QThread, QMimeData

import math
from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
import hashlib
from datetime import datetime, timezone
import requests
from PIL import Image
from PIL.ExifTags import TAGS
import time
import io
import shutil

from MdModel import *
from ModanDialogs import DatasetAnalysisDialog, ObjectDialog, ImportDatasetDialog, DatasetDialog, PreferencesDialog, LandmarkEditor, IMAGE_EXTENSION_LIST, MyGLWidget

#import matplotlib
#matplotlib.use('Qt5Agg')

PROGRAM_NAME = "Modan2"
PROGRAM_VERSION = "0.0.1"

BASE_DIRECTORY = "."
DEFAULT_STORAGE_DIRECTORY = os.path.join(BASE_DIRECTORY, "data/")


form_class = uic.loadUiType("Modan2.ui")[0]
class ModanMainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setupUi(self)
        self.setGeometry(QRect(100, 100, 1400, 900))
        self.setWindowIcon(QIcon('icon/modan.ico'))
        self.initUI()
        self.setWindowTitle(PROGRAM_NAME)
        #self.read_settings()
        self.selected_dataset = None
        self.selected_object = None
        self.check_db()
        self.reset_views()
        self.load_dataset()
        #QApplication.restoreOverrideCursor()
        self.m_app = QApplication.instance()
        self.read_settings()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.analysis_dialog = None

    def read_settings(self):
        self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,"DiploSoft", "Modan2")
        self.m_app.settings.beginGroup("Defaults")
        self.m_app.storage_directory = self.m_app.settings.value("Storage directory", os.path.abspath(DEFAULT_STORAGE_DIRECTORY))
        dir = self.m_app.storage_directory

        #print("storage directory:", self.m_app.storage_directory)
        #print(os.path.abspath(dir), Path(dir).absolute())

    def check_db(self):
        gDatabase.connect()
        tables = gDatabase.get_tables()
        if tables:
            return
            print(tables)
        else:
            gDatabase.create_tables([MdDataset, MdObject, MdImage, ])

    '''
    def read_settings(self):
        #return
        settings = QSettings("Modan2", "Modan2")
        self.server_address = settings.value("server_address", "localhost")
        self.server_port = settings.value("server_port", "8000")
        self.data_folder = Path(settings.value("data_folder", "C:/Modan2/data"))
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    def write_settings(self):
        settings = QSettings("Modan2", "Modan2")
        settings.setValue("server_address", self.server_address)
        settings.setValue("server_port", self.server_port)
        settings.setValue("data_folder", str(self.data_folder))
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    '''

    def closeEvent(self, event):
        #self.write_settings()
        if self.analysis_dialog is not None:
            self.analysis_dialog.close()
        event.accept()

    @pyqtSlot()
    def on_action_edit_preferences_triggered(self):
        print("edit preferences")
        #dlg = PreferencesDialog(self)  
        #dlg.exec_()
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    
    @pyqtSlot()
    def on_action_exit_triggered(self):
        self.close()

    @pyqtSlot() 
    def on_action_about_triggered(self):
        QMessageBox.about(self, "About", "Modan2")

    @pyqtSlot()
    def on_action_analyze_dataset_triggered(self):
        #QMessageBox.about(self, "About", "Modan2")
        #print("analyze dataset")
        if self.selected_dataset is None:
            QMessageBox.warning(self, "Warning", "No dataset selected")
            return
        self.analysis_dialog = DatasetAnalysisDialog(self,self.selected_dataset)
        self.analysis_dialog.show()

    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #widget = QWidget()
        self.object_view_2d = LandmarkEditor(self)
        self.object_view_3d = MyGLWidget(self)
        self.object_view = self.object_view_2d
        self.object_view_3d.hide()

        hsplitter = QSplitter(Qt.Horizontal)
        vsplitter = QSplitter(Qt.Vertical)

        vsplitter.addWidget(self.tableView)
        vsplitter.addWidget(self.object_view_2d)
        vsplitter.addWidget(self.object_view_3d)

        #self.treeView = MyTreeView()
        hsplitter.addWidget(self.treeView)
        hsplitter.addWidget(vsplitter)
        hsplitter.setSizes([300, 800])

        self.setCentralWidget(hsplitter)

        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_dataset_menu)
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.open_object_menu)

        #self.treeView.
    def open_object_menu(self, position):
        indexes = self.tableView.selectedIndexes()
        selected_object_list = self.get_selected_object_list()
        if len(selected_object_list) > 0:
            level = 0
            index = indexes[0]
            action_edit_object = QAction("Edit")
            action_edit_object.triggered.connect(self.on_tableView_doubleClicked)
            action_delete_object = QAction("Delete")
            action_delete_object.triggered.connect(self.on_action_delete_object_triggered)
            action_refresh_table = QAction("Reload")
            action_refresh_table.triggered.connect(self.load_object)
            action_edit_property_list = []
            if self.selected_dataset is not None and len(self.selected_dataset.propertyname_list)>0:
                
                for index, propertyname in enumerate(self.selected_dataset.propertyname_list):
                    action_edit_property_list.append(QAction("- Edit " + propertyname))
                    action_edit_property_list[-1].triggered.connect(lambda checked,index=index: self.on_edit_property(index))
                    #action.triggered.connect(lambda arg=my_argument: my_slot(arg))



            menu = QMenu()
            if len(selected_object_list) == 1:
                menu.addAction(action_edit_object)
            menu.addAction(action_delete_object)
            menu.addAction(action_refresh_table)
            if len(action_edit_property_list) > 0:
                menu.addSeparator()
                for action in action_edit_property_list:
                    menu.addAction(action)

            menu.exec_(self.tableView.viewport().mapToGlobal(position))

    def on_edit_property(self,idx):
        object_list = self.get_selected_object_list()
        if len(object_list) == 0:
            return

        for obj in object_list:
            obj.unpack_property()

        # get property from qmessagebox input
        propertyname = self.selected_dataset.propertyname_list[idx]
        #propertyvalue = object_list[0].get_property(propertyname)
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter new value for ' + propertyname, text="")
        if ok:
            for object in object_list:
                object.unpack_property()
                #print("1", object.object_name, "property_list:", object.property_list)
                if len(object.property_list) < idx+1:
                    # extend property_list to idx
                    while len(object.property_list) < idx+1:
                        object.property_list.append("")
                #print("2", object.object_name, "property_list:", object.property_list)

                object.property_list[idx] = text
                #print("3", object.object_name, "property_list:", object.property_list)
                object.pack_property()
                #print("3", object.object_name, "property_str:", object.property_str)
                object.save()
            self.load_object()


    @pyqtSlot()
    def on_action_delete_object_triggered(self):
        #print("delete object")
        ret = QMessageBox.warning(self, "Warning", "Are you sure to delete the selected object?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        
        selected_object_list = self.get_selected_object_list()
        if selected_object_list:
            for object in selected_object_list:
                object.delete_instance()
            dataset = self.selected_dataset
            self.reset_treeView()
            self.load_dataset()
            self.reset_tableView()
            self.select_dataset(dataset)

    def open_dataset_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            action_add_dataset = QAction("Add a child dataset")
            action_add_dataset.triggered.connect(self.on_action_new_dataset_triggered)
            action_add_object = QAction("Add an object")
            action_add_object.triggered.connect(self.on_action_new_object_triggered)
            action_refresh_tree = QAction("Reload")
            action_refresh_tree.triggered.connect(self.load_dataset)

            menu = QMenu()
            menu.addAction(action_add_dataset)
            menu.addAction(action_add_object)
            menu.addAction(action_refresh_tree)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))


    @pyqtSlot()
    def on_action_import_dataset_triggered(self):
        #print("import dataset")
        # open import dataset dialog
        self.dlg = ImportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()
        self.load_dataset()        

    @pyqtSlot()
    def on_action_export_dataset_triggered(self):
        print("export dataset")

    @pyqtSlot()
    def on_action_new_object_triggered(self):
        # open new object dialog
        #return
        if not self.selected_dataset:
            return
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.object = None
        self.dlg.set_dataset(self.selected_dataset)
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        ret = self.dlg.exec_()
        if ret == 0:
            return

        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        #print("new dataset dialog shown")
        # create new dataset

    @pyqtSlot()
    def on_action_new_dataset_triggered(self):
        # open new dataset dialog
        #return
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        if self.selected_dataset:
            #print("selected exists")
            self.dlg.set_parent_dataset( self.selected_dataset )
        else:
            #print("selected not exists")
            self.dlg.set_parent_dataset( None )

        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        ret = self.dlg.exec_()
        #print("dataset edit result:", ret)
        self.load_dataset()
        self.reset_tableView()
        #print("new dataset dialog shown")
        # create new dataset

    @pyqtSlot()
    def on_treeView_doubleClicked(self):
        #print("treeView double clicked")
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset( self.selected_dataset )
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        ret = self.dlg.exec_()
        if ret == 0:
            return
        elif ret == 1:
            if self.selected_dataset is None: #deleted
                self.load_dataset()
                self.reset_tableView()
            else:
                dataset = self.selected_dataset
                self.reset_treeView()
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)

        #print("dataset edit result:", ret, self.selected_dataset)
        #self.load_dataset()
        #self.reset_tableView()
    
    def select_dataset(self,dataset,node=None):
        #print("select dataset:", dataset)
        if dataset is None:
            #print("dataset is None")
            return
        if node is None:
            node = self.dataset_model.invisibleRootItem()
        #print("node:", node)
        for i in range(node.rowCount()):
            item = node.child(i,0)
            #print("item:", item, item.data(),dataset)

            if item.data() == dataset:
                self.treeView.setCurrentIndex(item.index())
                #print("selected:", item.data())
                break
            self.select_dataset(dataset,node.child(i,0))

    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        #print("treeView double clicked")
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.set_object( self.selected_object )
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        self.dlg.exec_()
        dataset = self.selected_dataset
        self.reset_treeView()
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        self.object_view.clear_object()

    def reset_treeView(self):
        self.dataset_model = QStandardItemModel()
        self.treeView.setModel(self.dataset_model)
        self.treeView.setHeaderHidden(True)
        self.dataset_selection_model = self.treeView.selectionModel()
        self.dataset_selection_model.selectionChanged.connect(self.on_dataset_selection_changed)
        #self.treeView
        header = self.treeView.header()
        #header.setStretchLastSection(False)
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)

        #'''
        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        #self.treeView.setDragDropMode(QAbstractItemView.InternalMove)
        #self.treeView.dropEvent = self.dropEvent
        #'''

        #self.treeView.setSortingEnabled(True)
        #header.setSectionResizeMode(0, QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QHeaderView.Fixed)
        #self.treeView.header().setSectionResizeMode(0, QHeaderView.Stretch)
        #self.treeView.header().setSectionResizeMode(1, QHeaderView.Fixed)
        #self.treeView.header().setSectionResizeMode(2, QHeaderView.Fixed)


        #connect treeView's drop event to some handler
        self.treeView.dropEvent = self.dropEvent
        #self.treeView.dragEnterEvent = self.tableView_drag_enter_event
        #self.treeView.dragMoveEvent = self.tableView_drag_move_event

        #self.tableView.mousePressEvent = self.mousePressEvent
        #connect treeView's dragenter event to some handler  
        #self.treeView.dragEnterEvent = self.dragEnterEvent

    '''
    def treeView_drag_enter_event(self, event):

        #event.acceptProposedAction()
        QTreeView.dragEnterEvent(self.treeView, event)
        #return

    def treeView_drag_move_event(self, event):
        #event.acceptProposedAction()
        QTreeView.dragMoveEvent(self.treeView, event)
        #return
    '''

    # accept drop event
    def dropEvent(self, event):
        # make dragged item a child of the drop target
        #print("drop event")
        if event.source() == self.treeView:
            #print("drop event from treeView")
            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()

            source_index = event.source().currentIndex()
            source_item = self.dataset_model.itemFromIndex(source_index)
            source_dataset = source_item.data()

            source_dataset.parent = target_dataset
            source_dataset.save()
            self.load_dataset()
            self.reset_tableView()

        elif event.source() == self.tableView:
            #print("drop event from tableView")
            shift_clicked = False
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                shift_clicked = True
                #print('Shift+Click')
            # default behavior is to copy and not move
            # when shift is pressed, move instead

            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()

            selected_object_list = self.get_selected_object_list()
            source_dataset = None

            for source_object in selected_object_list:
                if source_object.dataset.dimension == target_dataset.dimension:
                    # if shift is pressed, move instead of copy
                    if shift_clicked:
                        if source_object.image.count() > 0:
                            source_image_path = source_object.image[0].get_image_path(self.m_app.storage_directory)
                        source_dataset = source_object.dataset
                        source_object.dataset = target_dataset
                        source_object.save()
                        if source_object.image.count() > 0:
                            target_image = source_object.image[0]
                            target_image_path = target_image.get_image_path(self.m_app.storage_directory)
                            if os.path.exists(source_image_path):
                                if not os.path.exists(os.path.dirname(target_image_path)):
                                    os.makedirs(os.path.dirname(target_image_path))

                                if os.path.exists(target_image_path):
                                    os.remove(target_image_path)
                                os.rename(source_image_path, target_image_path)
                    else:
                        # copy object
                        source_dataset = source_object.dataset
                        new_object = MdObject()
                        new_object.object_name = source_object.object_name
                        new_object.object_desc = source_object.object_desc
                        new_object.scale = source_object.scale
                        new_object.landmark_str = source_object.landmark_str
                        new_object.property_list = source_object.property_list
                        new_object.dataset = target_dataset
                        new_object.save()
                        if source_object.image.count() > 0:
                            old_image = source_object.image[0]
                            source_image_path = old_image.get_image_path(self.m_app.storage_directory)
                            new_image = MdImage()
                            new_image.original_path = old_image.original_path
                            new_image.original_filename = old_image.original_filename
                            new_image.name = old_image.name
                            new_image.md5hash = old_image.md5hash
                            new_image.size = old_image.size
                            new_image.exifdatetime = old_image.exifdatetime
                            new_image.file_created = old_image.file_created
                            new_image.file_modified = old_image.file_modified
                            new_image.object = new_object
                            new_image.save()
                            new_image_path = new_image.get_image_path(self.m_app.storage_directory)
                            #print(source_image_path, new_image_path)
                            if os.path.exists(source_image_path):
                                if not os.path.exists(os.path.dirname(new_image_path)):
                                    os.makedirs(os.path.dirname(new_image_path))
                                if os.path.exists(new_image_path):
                                    os.remove(new_image_path)
                                shutil.copyfile(source_image_path, new_image_path)

                else:
                    #print("dimension mismatch")
                    QMessageBox.warning(self, "Warning", "Dimension mismatch")
                    break
            #self.selected_dataset = target_dataset
            #self.reset_tableView()
            #dataset = self.selected_dataset
            if source_dataset is not None:
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(source_dataset)
            

                #source_object.dataset = target_dataset
                #source_object.save()
        #show to which item we are dropping

        #print(event)
        #print(event.source())

            #self.object_model.clear()
            #self.reset_tableView()        
            #item1 =self.dataset_model.itemFromIndex(indexes[0])
            #item2 =self.dataset_model.itemFromIndex(indexes[1])
            #ds = item2.data()
            #self.selected_dataset = ds
            #self.load_object()

        #print(event.source().model().itemFromIndex(event.source().currentIndex()).data())
        #print(event.mimeData().text())
        #event.acceptProposedAction()
        #return
        #'''
        #print(event.source().model().itemFromIndex(event.source().currentIndex()).data())
        #print(event.source().model().itemFromIndex(event.source().currentIndex()).data(Qt.UserRole))
        #print(event.target())
        #print(event.target().model())
        #print(event.target().model().itemFromIndex(event.target().currentIndex()))
    
    """
    def mousePressEvent(self, event):
        print("mouse press event",event.pos(),event.button(),self.tableView.indexAt(event.pos()).isValid())
        if event.button() == Qt.LeftButton and self.tableView.indexAt(event.pos()).isValid():

            drag =  QDrag(self.tableView)
            mimeData =  QMimeData()

            mimeData.setText("drag data")
            drag.setMimeData(mimeData)

            #drag.setPixmap(iconPixmap)

            dropAction = drag.exec_()

    def dragEnterEvent(self, event):
        print("drag enter event")
        if event.mimeData().hasFormat('text/plain'):
            print("mimedata:",event.mimeData().text())
            event.accept()
        else:
            event.ignore()
    """

    def get_selected_object_list(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list
        
        selected_object_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            selected_object_list.append(object)

        return selected_object_list

    def reset_tableView(self):
        self.object_model = QStandardItemModel()
        header_labels = ["ID", "Name", "Count", "CSize"]
        if self.selected_dataset is not None:
            #print("selected_dataset:",self.selected_dataset.dataset_name)
            self.selected_dataset.unpack_propertyname_str()
            if self.selected_dataset.propertyname_list is not None and len( self.selected_dataset.propertyname_list ) > 0:
                #print("propertyname_list:",self.selected_dataset.propertyname_list,"propertyname_str:",self.selected_dataset.propertyname_str)
                header_labels.extend( self.selected_dataset.propertyname_list )
            if self.selected_dataset.dimension == 2:
                self.object_view = self.object_view_2d
                self.object_view_2d.show()
                self.object_view_3d.hide()
            else:
                self.object_view = self.object_view_3d
                self.object_view_2d.hide()
                self.object_view_3d.show()
        self.object_model.setColumnCount(len(header_labels))
        self.object_model.setHorizontalHeaderLabels( header_labels )
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.tableView.setModel(self.proxy_model)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 50)
        self.tableView.setColumnWidth(3, 50)
        header = self.tableView.horizontalHeader()    
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)

        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)
        #print("tableview accept drops:", self.tableView.acceptDrops())
        self.tableView.setDropIndicatorShown(True)
        self.tableView.dropEvent = self.tableView_drop_event
        self.tableView.dragEnterEvent = self.tableView_drag_enter_event
        self.tableView.dragMoveEvent = self.tableView_drag_move_event

        self.tableView.setSortingEnabled(True)
        self.tableView.sortByColumn(0, Qt.AscendingOrder)
        self.object_model.setSortRole(Qt.UserRole)
        self.clear_object_view()
    #table.setSortingEnabled(True)
    #table.sortByColumn(0, Qt.AscendingOrder)

    def tableView_drop_event(self, event):
        if self.selected_dataset is None:
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        #print("file name list:", file_name_list)
        if len(file_name_list) == 0:
            return
        #print("selected_dataset", self.selected_dataset)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for file_name in file_name_list:
            file_name = re.sub('file:///', '', file_name)
            #print("file name:", file_name)
            ext = file_name.split('.')[-1].lower()
            if ext in IMAGE_EXTENSION_LIST:
                if self.selected_dataset.dimension != 2:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch.")
                    #self.statusBar.showMessage("Dimension mismatch.",2000)
                    break
                #print("drop file:", file_name)
                object = MdObject()
                object.dataset = self.selected_dataset
                object.object_name = Path(file_name).stem
                object.save()
                img = MdImage()
                img.object = object
                img.load_file_info(file_name)
                new_filepath = img.get_image_path( self.m_app.storage_directory)
                if not os.path.exists(os.path.dirname(new_filepath)):
                    os.makedirs(os.path.dirname(new_filepath))
                #print("save object new filepath:", new_filepath)
                shutil.copyfile(file_name, new_filepath)
                img.save()
            # see if file_name is directory
            elif os.path.isdir(file_name):
                self.statusBar.showMessage("Cannot process directory...",2000)
                #pass
                #print("drop directory:", file_name)
                #for root, dirs, files in os.walk(file_name):
                #    for file in files:
                #        file_name = os.path.join(root, file)
                #        ext = file_name.split('.')[-1].lower()
                #        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
                #            print("drop file:", file_name)
            else:
                self.statusBar.showMessage("Nothing to import.",2000)
                #pass
                #print("not image, not dir:", file_name)
            self.load_object()
        #print("selected_dataset", self.selected_dataset)
        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        QApplication.restoreOverrideCursor()

    def tableView_drag_enter_event(self, event):
        event.accept()
        return
        print("drag enter",event.mimeData().text())
        file_name_list = event.mimeData().text().strip().split("\n")
        print("file name list:", file_name_list)
        ext = file_name_list[0].split('.')[-1].lower()
        print("ext:", ext)
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            print("image file")
            print("source:", event.source())
            print("proposed action:", event.proposedAction())
            print("drop action:", event.dropAction())
            print("possible action:", int(event.possibleActions()))
            print("kinds of drop actions:", Qt.CopyAction, Qt.MoveAction, Qt.LinkAction, Qt.ActionMask, Qt.TargetMoveAction)
            #event.acceptProposedAction()
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()


    def tableView_drag_move_event(self, event):
        event.accept()
        return
        print("drag move",event.mimeData().text())
        file_name_list = event.mimeData().text().strip().split("\n")
        print("file name list:", file_name_list)
        ext = file_name_list[0].split('.')[-1].lower()
        print("ext:", ext)
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            print("image file")
            print("source:", event.source())
            print("proposed action:", event.proposedAction())
            print("drop action:", event.dropAction())
            print("possible action:", int(event.possibleActions()))
            print("kinds of drop actions:", Qt.CopyAction, Qt.MoveAction, Qt.LinkAction, Qt.ActionMask, Qt.TargetMoveAction)
            #event.acceptProposedAction()
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()


    def reset_views(self):
        self.reset_treeView()
        self.reset_tableView()
    
    def load_dataset(self):
        self.dataset_model.clear()
        self.selected_dataset = None
        all_record = MdDataset.filter(parent=None)
        for rec in all_record:
            rec.unpack_wireframe()
            #print("wireframe:", rec.wireframe, rec.edge_list)
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon("icon/icons8-xlarge-icons-50.png"))
            else:
                item1.setIcon(QIcon("icon/icons8-3d-50.png"))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            #item3 = QStandardItem(str(rec.dimension))
            #print("dataset id:",item2.text())
            #item2 = QStandardItem(rec.objects.count())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            
            self.dataset_model.appendRow([item1,item2])#,item2,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)
        #self.treeView.hideColumn(2)

            #item.appendRow([sub_item1,sub_item2])
    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            rec.unpack_wireframe()
            #print("wireframe:", rec.wireframe, rec.edge_list)
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon("icon/icons8-xlarge-icons-50.png")) #  https://icons8.com
            else:
                item1.setIcon(QIcon("icon/icons8-3d-50.png"))
            #item1 = QStandardItem(rec.dataset_name)
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            #item3 = QStandardItem(str(rec.dimension))
            #print("dataset id:",item2.text())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            parent_item.appendRow([item1,item2])#,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())

            #item.appendRow([sub_item1,sub_item2]

    def on_dataset_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        #print(indexes)
        if indexes:
            self.object_model.clear()
            #self.reset_tableView()
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            #item2 =self.dataset_model.itemFromIndex(indexes[1])
            ds = item1.data()
            self.selected_dataset = ds
            self.load_object()

    def load_object(self):
        self.object_model.clear()
        self.reset_tableView()
        if self.selected_dataset is None:
            return
        #objects = self.selected_dataset.objects
        for obj in self.selected_dataset.object_list:
            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            lm_count = obj.count_landmarks()
            item3 = QStandardItem()
            item3.setData(lm_count,Qt.DisplayRole)
            item4 = QStandardItem()
            item4.setData('',Qt.DisplayRole)
            item_list = [item1,item2,item3,item4]
            if len(self.selected_dataset.propertyname_list) > 0:
                property_list = obj.unpack_property()
                #print("obj",obj.object_name,"property list:",property_list)
                for idx,prop in enumerate(self.selected_dataset.propertyname_list):
                    item = QStandardItem()
                    if idx < len(property_list):
                        item.setData(property_list[idx],Qt.DisplayRole)
                    else:
                        item.setData('',Qt.DisplayRole)
                    item_list.append(item)
            self.object_model.appendRow(item_list)


    def on_object_selection_changed(self, selected, deselected):
        selected_object_list = self.get_selected_object_list()
        if selected_object_list is None or len(selected_object_list) != 1:
            return
        #print("object_id:",object_id, type(object_id))
        object_id = selected_object_list[0].id

        self.selected_object = MdObject.get_by_id(object_id)
        #print("selected_object:",self.selected_object)
        self.show_object(self.selected_object)
        #print(selected_object,selected_object.object_name)
        #filepath = item_text_list[1]
        #filename = item_text_list[0]
        #return filepath, filename

    def show_object(self, obj):
        #print("show_object:",obj)
        #print("object:", obj)
        self.object_view.clear_object()
        self.object_view.set_object(obj)
        #return
    def clear_object_view(self):
        #print("clear object view")
        self.object_view.clear_object()

    def _on_object_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        print(indexes)
        item1 = self.proxy_model.itemFromIndex(indexes[0])
        print(item1)

        indexes = self.object_selection_model.selection().indexes()
        print(indexes)
        item1 = self.proxy_model.itemFromIndex(indexes[0])
        print(item1)
        #item2 = self.dir_model.itemFromIndex(index_list[1])

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('Modan2.ico'))
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = ModanMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()


''' 
How to make an exe file
pyinstaller --onefile --noconsole --icon="icon/modan.ico" Modan2.py
'''