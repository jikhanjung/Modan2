from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu

from PyQt5 import uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray, QPoint, QModelIndex
from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
import hashlib
from datetime import datetime, timezone
import requests
from PIL import Image
from PIL.ExifTags import TAGS
#import imagesize
from datetime import datetime
import time
import io

PROGRAM_NAME = "Modan2"
PROGRAM_VERSION = "0.0.1"

from MdModel import *

class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

        self.cbxParent = QComboBox()
        self.edtDatasetName = QLineEdit()
        self.edtDatasetDesc = QLineEdit()

        self.rbtn2D = QRadioButton("2D")
        self.rbtn2D.setChecked(True)
        self.rbtn3D = QRadioButton("3D")
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(self.rbtn2D)
        dim_layout.addWidget(self.rbtn3D)

        self.edtWireframe = QTextEdit()
        self.edtBaseline = QLineEdit()
        self.edtPolygons = QTextEdit()
        self.edtPropertyNameList = QTextEdit()

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Parent", self.cbxParent)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Description", self.edtDatasetDesc)
        self.main_layout.addRow("Dimension", dim_layout)
        self.main_layout.addRow("Wireframe", self.edtWireframe)
        self.main_layout.addRow("Baseline", self.edtBaseline)
        self.main_layout.addRow("Polygons", self.edtPolygons)
        self.main_layout.addRow("Property Name List", self.edtPropertyNameList)


        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnDelete = QPushButton()
        self.btnDelete.setText("Delete")
        self.btnDelete.clicked.connect(self.Delete)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        self.main_layout.addRow(btn_layout)


        self.dataset = None
        self.load_parent_dataset()

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    def load_parent_dataset(self,curr_dataset_id = None):
        self.cbxParent.clear()
        datasets = MdDataset.select()
        for dataset in datasets:
            if curr_dataset_id is None or dataset.id != curr_dataset_id:
                self.cbxParent.addItem(dataset.dataset_name, dataset.id)

    def read_dataset(self, dataset_id):
        try:
            dataset = MdDataset.get(dataset.id == dataset_id)
        except:
            dataset = None
        self.dataset = dataset
        #self
        #return dataset

    def set_dataset(self, dataset):
        if dataset is None:
            self.dataset = None
            self.cbxParent.setCurrentIndex(-1)
            return

        self.dataset = dataset
        self.load_parent_dataset(dataset.id)
        self.cbxParent.setCurrentIndex(self.cbxParent.findData(dataset.parent_id))

        self.edtDatasetName.setText(dataset.dataset_name)
        self.edtDatasetDesc.setText(dataset.dataset_desc)
        if dataset.dimension == 2:
            self.rbtn2D.setChecked(True)
        elif dataset.dimension == 3:
            self.rbtn3D.setChecked(True)
        self.edtWireframe.setText(dataset.wireframe)
        self.edtBaseline.setText(dataset.baseline)
        self.edtPolygons.setText(dataset.polygons)
        self.edtPropertyNameList.setText(dataset.propertyname_list)

    
    def set_parent_dataset(self, parent_dataset_id):
        #print("parent:", parent_dataset_id, "dataset:", self.dataset)
        if parent_dataset_id is None:
            self.cbxParent.setCurrentIndex(-1)
        else:
            self.cbxParent.setCurrentIndex(self.cbxParent.findData(parent_dataset_id))
        

    def Okay(self):
        if self.dataset is None:
            self.dataset = MdDataset()
        self.dataset.parent_id = self.cbxParent.currentData()
        self.dataset.dataset_name = self.edtDatasetName.text()
        self.dataset.dataset_desc = self.edtDatasetDesc.text()
        if self.rbtn2D.isChecked():
            self.dataset.dimension = 2
        elif self.rbtn3D.isChecked():
            self.dataset.dimension = 3
        self.dataset.wireframe = self.edtWireframe.toPlainText()
        self.dataset.baseline = self.edtBaseline.text()
        self.dataset.polygons = self.edtPolygons.toPlainText()
        self.dataset.propertyname_list = self.edtPropertyNameList.toPlainText()

        #self.data
        #print(self.dataset.dataset_desc, self.dataset.dataset_name)
        self.dataset.save()
        self.close()

    def Delete(self):
        QMessageBox.question(self, "", "Are you sure to delete this dataset?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if QMessageBox.Yes:
            self.dataset.delete_instance()
        #self.delete_dataset()
        self.close()

    def Cancel(self):
        self.close()

class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Object")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 400, 300))
        self.move(self.parent.pos()+QPoint(100,100))

        self.edtObjectName = QLineEdit()
        self.edtObjectDesc = QLineEdit()
        self.edtLandmarkStr = QLineEdit()
        self.lblDataset = QLabel()

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Dataset Name", self.lblDataset)
        self.main_layout.addRow("Object Name", self.edtObjectName)
        self.main_layout.addRow("Object Desc", self.edtObjectDesc)
        self.main_layout.addRow("Landmarks", self.edtLandmarkStr)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnCancel)
        self.main_layout.addRow(btn_layout)

        self.dataset = None

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    def set_dataset(self, dataset):
        self.dataset = dataset
        self.lblDataset.setText(dataset.dataset_name)

    def set_object(self, object):
        self.object = object
        self.edtObjectName.setText(object.object_name)
        self.edtObjectDesc.setText(object.object_desc)
        self.edtLandmarkStr.setText(object.landmark_str)
        self.set_dataset(object.dataset)

    def save_object(self):
        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.object_desc = self.edtObjectDesc.text()
        self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.save()

    def Okay(self):
        self.save_object()
        self.close()

    def Cancel(self):
        self.close()

class PreferencesDialog(QDialog):
    '''
    PreferencesDialog shows preferences.

    Args:
        None

    Attributes:
        well..
    '''
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.setGeometry(QRect(0, 0, 400, 300))
        self.setWindowTitle("설정")
        #self.lbl_main_view.setMinimumSize(400, 300)

        self.lblServerAddress = QLabel()
        self.edtServerAddress = QLineEdit()
        self.edtServerPort = QLineEdit()
        self.lblDataFolder = QLabel()
        self.edtDataFolder = QLineEdit()

        self.edtServerPort.setFixedWidth(50)

        self.btnDataFolder = QPushButton()
        self.btnDataFolder.setText("선택")
        self.btnDataFolder.clicked.connect(self.select_folder)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("확인")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("취소")
        self.btnCancel.clicked.connect(self.Cancel)


        self.layout = QVBoxLayout()
        self.layout1 = QHBoxLayout()
        self.layout1.addWidget(self.lblServerAddress)
        self.layout1.addWidget(self.edtServerAddress)
        self.layout1.addWidget(self.edtServerPort)
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.lblDataFolder)
        self.layout3.addWidget(self.edtDataFolder)
        self.layout3.addWidget(self.btnDataFolder)
        self.layout4 = QHBoxLayout()
        self.layout4.addWidget(self.btnOkay)
        self.layout4.addWidget(self.btnCancel)
        self.layout.addLayout(self.layout1)
        #self.layout.addLayout(self.layout2)
        self.layout.addLayout(self.layout3)
        self.layout.addLayout(self.layout4)
        self.setLayout(self.layout)
        self.server_address = ''
        self.server_port = ''
        self.data_folder = ''
        #print("pref dlg data_folder:", self.data_folder)
        self.read_settings()
        #print("pref dlg data_folder:", self.data_folder)
        self.lblServerAddress.setText("서버 주소")
        #self.lblServerPort.setText("Server Port")
        self.lblDataFolder.setText("사진 위치")

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        self.edtServerAddress.setText(self.server_address)
        self.edtServerPort.setText(self.server_port)

    def write_settings(self):
        self.parent.server_address = self.edtServerAddress.text()
        self.parent.server_port = self.edtServerPort.text()
        self.parent.data_folder = Path(self.edtDataFolder.text())
        #print( self.parent.server_address,self.parent.server_port, self.parent.data_folder)

    def read_settings(self):
        self.server_address = self.parent.server_address
        self.server_port = self.parent.server_port
        self.data_folder = self.parent.data_folder.resolve()
        #print("pref dlg data folder:", self.data_folder)
        #print("pref dlg server address:", self.server_address)

    def Okay(self):
        self.write_settings()
        self.close()

    def Cancel(self):
        self.close()

    def select_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "폴더 선택", str(self.data_folder)))
        if folder:
            self.data_folder = Path(folder).resolve()
            self.edtDataFolder.setText(folder)



form_class = uic.loadUiType("Modan2.ui")[0]
class ModanMainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setGeometry(QRect(100, 100, 1280, 800))
        self.setupUi(self)
        self.initUI()
        self.setWindowTitle(PROGRAM_NAME)
        #self.read_settings()
        self.check_db()
        self.reset_views()
        self.load_dataset()
        #QApplication.restoreOverrideCursor()
        self.selected_dataset = None
        self.selected_object = None

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
        event.accept()

    def on_actionPreferences_triggered(self):
        dlg = PreferencesDialog(self)
        dlg.exec_()
        self.server_address = dlg.server_address
        self.server_port = dlg.server_port
        self.data_folder = dlg.data_folder
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    
    def on_actionExit_triggered(self):
        self.close()

    def on_actionAbout_triggered(self):
        QMessageBox.about(self, "About", "Modan2")

    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #widget = QWidget()
        hsplitter = QSplitter(Qt.Horizontal)
        vsplitter = QSplitter(Qt.Vertical)

        vsplitter.addWidget(self.tableView)
        vsplitter.addWidget(self.tableWidget)

        hsplitter.addWidget(self.treeView)
        hsplitter.addWidget(vsplitter)
        hsplitter.setSizes([300, 800])

        self.setCentralWidget(hsplitter)

        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)

        #self.treeView.

    def open_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            action_add_dataset = QAction("Add Dataset")
            action_add_dataset.triggered.connect(self.on_action_new_dataset_triggered)
            action_add_object = QAction("Add Object")
            action_add_object.triggered.connect(self.on_action_new_object_triggered)
            action_refresh_tree = QAction("Refresh Tree")
            action_refresh_tree.triggered.connect(self.load_dataset)

            menu = QMenu()
            menu.addAction(action_add_dataset)
            menu.addAction(action_add_object)
            menu.addAction(action_refresh_tree)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

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
        self.dlg.exec_()
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
            print("selected exists")
            self.dlg.set_parent_dataset( self.selected_dataset.id )
        else:
            print("selected not exists")
            self.dlg.set_parent_dataset( None )

        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        self.dlg.exec_()
        self.load_dataset()
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
        self.dlg.exec_()
        self.load_dataset()

    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        #print("treeView double clicked")
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_object( self.selected_object )
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        self.dlg.exec_()
        self.load_object()

    def reset_treeView(self):
        self.dataset_model = QStandardItemModel()
        self.treeView.setModel(self.dataset_model)
        self.treeView.setHeaderHidden(True)
        self.dataset_selection_model = self.treeView.selectionModel()
        self.dataset_selection_model.selectionChanged.connect(self.on_dataset_selection_changed)

    def reset_tableView(self):
        self.object_model = QStandardItemModel()
        self.object_model.setColumnCount(4)
        self.object_model.setHorizontalHeaderLabels(["ID", "Name", "Count", "CSize"])
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.tableView.setModel(self.proxy_model)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 200)
        self.tableView.setColumnWidth(3, 200)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)

    def reset_views(self):
        self.reset_treeView()
        self.reset_tableView()
    
    def load_dataset(self):
        self.dataset_model.clear()
        self.selected_dataset = None
        all_record = MdDataset.filter(parent=None)
        for rec in all_record:
            item1 = QStandardItem(rec.dataset_name)
            item2 = QStandardItem(str(rec.id))
            item2.setData(rec)
            #print("dataset id:",item2.text())
            #item2 = QStandardItem(rec.objects.count())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            
            self.dataset_model.appendRow([item1,item2] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item2.data())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)

            #item.appendRow([sub_item1,sub_item2])
    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            item1 = QStandardItem(rec.dataset_name)
            item2 = QStandardItem(str(rec.id))
            item2.setData(rec)
            #print("dataset id:",item2.text())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            parent_item.appendRow([item1,item2] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item2.data())

            #item.appendRow([sub_item1,sub_item2]

    def on_dataset_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        #print(indexes)
        if indexes:
            self.object_model.clear()
            self.reset_tableView()        
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            item2 =self.dataset_model.itemFromIndex(indexes[1])
            ds = item2.data()
            self.selected_dataset = ds
            self.load_object()

    def load_object(self):
        self.object_model.clear()
        self.reset_tableView()
        if self.selected_dataset is None:
            return
        #objects = self.selected_dataset.objects
        for obj in self.selected_dataset.objects:
            item1 = QStandardItem(str(obj.id))
            item2 = QStandardItem(obj.object_name)
            item1.setData(obj)
            self.object_model.appendRow([item1,item2] )


    def on_object_selection_changed(self, selected, deselected):
        selected_index_list = self.object_selection_model.selection().indexes()
        if len(selected_index_list) == 0:
            return
        #print("selected_index",selected_index_list)

        new_index_list = []
        model = selected_index_list[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_index_list:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
        #print("new_index_list",new_index_list)
        item_text_list = []
        for index in new_index_list:
            item = self.object_model.itemFromIndex(index)
            #print("item_text:",item.text())
            item_text_list.append(item)
        self.selected_object = item_text_list[0].data()
        #print(selected_object,selected_object.object_name)
        #filepath = item_text_list[1]
        #filename = item_text_list[0]
        #return filepath, filename



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

    #WindowClass의 인스턴스 생성
    myWindow = ModanMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
