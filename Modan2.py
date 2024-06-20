from PyQt5.QtWidgets import QMainWindow, QHeaderView, QApplication, QAbstractItemView, \
                            QMessageBox, QTreeView, QTableView, QSplitter, QAction, QMenu, \
                            QStatusBar, QInputDialog, QToolBar, QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout, \
                            QPushButton
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QSize, QTranslator, QItemSelectionModel

from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
from PIL.ExifTags import TAGS
import shutil
import copy
from datetime import datetime

from MdModel import *
import MdUtils as mu
from peewee_migrate import Router

from ModanDialogs import DatasetAnalysisDialog, ObjectDialog, ImportDatasetDialog, DatasetDialog, PreferencesDialog, \
    MODE, ObjectViewer3D, ExportDatasetDialog, ObjectViewer2D, ProgressDialog, NewAnalysisDialog, DataExplorationDialog
from ModanComponents import MdTableModel, MdTableView, MdSequenceDelegate, AnalysisInfoWidget
from MdStatistics import PerformCVA, PerformPCA, PerformManova

import matplotlib.pyplot as plt

import json
from MdLogger import setup_logger
logger = setup_logger(mu.PROGRAM_NAME)


ICON = {}
ICON['new_dataset'] = mu.resource_path('icons/M2NewDataset_1.png')
ICON['new_object'] = mu.resource_path('icons/M2NewObject_2.png')
ICON['import'] = mu.resource_path('icons/M2Import_1.png')
ICON['export'] = mu.resource_path('icons/M2Export_1.png')
ICON['analyze'] = mu.resource_path('icons/M2Analysis_1.png')
ICON['preferences'] = mu.resource_path('icons/M2Preferences_1.png')
ICON['about'] = mu.resource_path('icons/M2About_1.png')
ICON['exit'] = mu.resource_path('icons/exit.png')
ICON['Modan2'] = mu.resource_path('icons/Modan2_2.png')
ICON['dataset_2d'] = mu.resource_path('icons/M2Dataset2D_3.png')
ICON['dataset_3d'] = mu.resource_path('icons/M2Dataset3D_4.png')

class ModanMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(mu.resource_path('icons/Modan2_2.png')))
        self.setWindowTitle("{} v{}".format(self.tr("Modan2"), mu.PROGRAM_VERSION))

        self.tableView = MdTableView()
        self.tableView.setItemDelegateForColumn(1, MdSequenceDelegate())
        self.treeView = QTreeView()

        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(32,32))
        #self.toolbar.addAction(QIcon(mu.resource_path('icons/open.png')), "Open", self.on_action_open_db_triggered)
        #self.toolbar.addAction(QIcon(mu.resource_path('icons/newdb.png')), "New", self.on_action_new_db_triggered)
        #self.toolbar.addAction(QIcon(mu.resource_path('icons/saveas.png')), "Save As", self.on_action_save_as_triggered)
        self.actionNewDataset = QAction(QIcon(mu.resource_path(ICON['new_dataset'])), self.tr("New Dataset\tCtrl+N"), self)
        self.actionNewDataset.triggered.connect(self.on_action_new_dataset_triggered)
        self.actionNewDataset.setShortcut(QKeySequence("Ctrl+N"))
        self.actionNewObject = QAction(QIcon(mu.resource_path(ICON['new_object'])), "New Object\tCtrl+Shift+N", self)
        self.actionNewObject.triggered.connect(self.on_action_new_object_triggered)
        self.actionNewObject.setShortcut(QKeySequence("Ctrl+Shift+N"))
        #self.actionNewObject.setEnabled(False)
        self.actionImport = QAction(QIcon(mu.resource_path(ICON['import'])), "Import\tCtrl+I", self)
        self.actionImport.triggered.connect(self.on_action_import_dataset_triggered)
        self.actionImport.setShortcut(QKeySequence("Ctrl+I"))
        self.actionExport = QAction(QIcon(mu.resource_path(ICON['export'])), "Export\tCtrl+E", self)
        self.actionExport.triggered.connect(self.on_action_export_dataset_triggered)
        self.actionExport.setShortcut(QKeySequence("Ctrl+E"))
        #self.actionExport.setEnabled(False)
        self.actionAnalyze = QAction(QIcon(mu.resource_path(ICON['analyze'])), "Analyze\tCtrl+G", self)
        self.actionAnalyze.triggered.connect(self.on_action_analyze_dataset_triggered)
        self.actionAnalyze.setShortcut(QKeySequence("Ctrl+G"))
        #self.actionAnalyze.setEnabled(False)
        self.actionPreferences = QAction(QIcon(mu.resource_path(ICON['preferences'])), "Preferences", self)
        self.actionPreferences.triggered.connect(self.on_action_edit_preferences_triggered)
        self.actionExit = QAction(QIcon(mu.resource_path(ICON['exit'])), "Exit\tCtrl+W", self)
        self.actionExit.triggered.connect(self.on_action_exit_triggered)
        self.actionExit.setShortcut(QKeySequence("Ctrl+W"))
        self.actionAbout = QAction(QIcon(mu.resource_path(ICON['about'])), "About\tF1", self)
        self.actionAbout.triggered.connect(self.on_action_about_triggered)
        self.actionAbout.setShortcut(QKeySequence("F1"))
        self.toolbar.addAction(self.actionNewDataset)
        self.toolbar.addAction(self.actionNewObject)
        self.toolbar.addAction(self.actionImport)
        self.toolbar.addAction(self.actionExport)
        self.toolbar.addAction(self.actionAnalyze)
        self.toolbar.addAction(self.actionPreferences)
        self.toolbar.addAction(self.actionAbout)
        self.addToolBar(self.toolbar)

        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu("File")
        self.file_menu.addAction(self.actionExit)
        self.edit_menu = self.main_menu.addMenu("Edit")
        self.edit_menu.addAction(self.actionPreferences)
        self.data_menu = self.main_menu.addMenu("Data")
        self.data_menu.addAction(self.actionNewDataset)
        self.data_menu.addAction(self.actionNewObject)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionAnalyze)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionImport)
        self.data_menu.addAction(self.actionExport)
        self.help_menu = self.main_menu.addMenu("Help")
        self.help_menu.addAction(self.actionAbout)

        self.m_app = QApplication.instance()
        self.m_app.toolbar_icon_size = "Small"
        self.read_settings()

        self.initUI()
        
        self.selected_dataset = None
        self.selected_object = None
        self.prepare_database()
        self.reset_views()
        self.load_dataset()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.analysis_dialog = None
        self.data_changed = False

        # read preferences and set window size, toolbar icon size, etc.
        self.remember_geometry = True

        self.set_toolbar_icon_size(self.m_app.toolbar_icon_size)

    def update_settings(self):
        #print("update settings bgcolor",self.preferences_dialog.bgcolor)

        size = self.m_app.toolbar_icon_size
        self.set_toolbar_icon_size(size)
        self.object_view_2d.read_settings()#set_landmark_pref(landmark_pref['2D'],wireframe_pref['2D'],bgcolor)
        self.object_view_3d.read_settings()#.set_landmark_pref(landmark_pref['3D'],wireframe_pref['3D'],bgcolor)

    def set_toolbar_icon_size(self, size):
        if size.lower() == 'small':
            self.toolbar.setIconSize(QSize(24,24))
        elif size.lower() == 'medium':
            self.toolbar.setIconSize(QSize(32,32))
        else:
            self.toolbar.setIconSize(QSize(48,48))

    def on_action_open_db_triggered(self):
        pass

    def on_action_new_db_triggered(self):
        pass

    def on_action_save_as_triggered(self):
        pass

    def read_settings(self):
        #self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,mu.COMPANY_NAME, mu.PROGRAM_NAME)
        self.m_app.storage_directory = os.path.abspath(mu.DEFAULT_STORAGE_DIRECTORY)
        self.m_app.toolbar_icon_size = self.m_app.settings.value("ToolbarIconSize", "Medium")
        self.m_app.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.m_app.remember_geometry is True:
            #print('loading geometry', self.remember_geometry)
            self.setGeometry(self.m_app.settings.value("WindowGeometry/MainWindow", QRect(100, 100, 1400, 800)))
            is_maximized = mu.value_to_bool(self.m_app.settings.value("IsMaximized/MainWindow", False))
            if is_maximized == True:
                #print("maximized true")
                self.showMaximized()
            else:
                #print("maximized false")
                self.showNormal()
                #pass
        else:
            self.setGeometry(QRect(100, 100, 1400, 800))

        plt.rcParams["font.family"] = "serif" 
        plt.rcParams["font.serif"] = ["Times New Roman"] 
        plt.rcParams['mathtext.fontset'] = 'stix' 
        plt.rcParams['font.size'] = 12


    def write_settings(self):
        self.m_app.remember_geometry = mu.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.m_app.remember_geometry is True:
            #print("maximized:", self.isMaximized(), "geometry:", self.geometry())
            if self.isMaximized():
                self.m_app.settings.setValue("IsMaximized/MainWindow", True)
            else:
                self.m_app.settings.setValue("IsMaximized/MainWindow", False)
                self.m_app.settings.setValue("WindowGeometry/MainWindow", self.geometry())
                #print("save maximized false")

    def prepare_database(self):
        migrations_path = mu.resource_path("migrations")
        logger.info("migrations path: %s", migrations_path)
        logger.info("database path: %s", database_path)
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")

        # backup database file to backup directory
        backup_path = os.path.join( mu.DB_BACKUP_DIRECTORY, DATABASE_FILENAME + '.' + date_str )
        if not os.path.exists(backup_path) and os.path.exists(database_path):
            shutil.copy2(database_path, backup_path)
            logger.info("backup database to %s", backup_path)
            # read backup directory and delete old backups
            backup_list = os.listdir(mu.DB_BACKUP_DIRECTORY)
            # filter out non-backup files
            backup_list = [f for f in backup_list if f.startswith(DATABASE_FILENAME)]
            backup_list.sort()
            if len(backup_list) > 10:
                for i in range(len(backup_list) - 10):
                    os.remove(os.path.join(mu.DB_BACKUP_DIRECTORY, backup_list[i]))                    
        
        #logger.info("database name: %s", mu.DEFAULT_DATABASE_NAME)
        #print("migrations path:", migrations_path)
        gDatabase.connect()
        router = Router(gDatabase, migrate_dir=migrations_path)

        # Auto-discover and run migrations
        router.run()        
        return

        gDatabase.connect()
        tables = gDatabase.get_tables()
        if tables:
            return
            print(tables)
        else:
            gDatabase.create_tables([MdDataset, MdObject, MdImage, MdThreeDModel,])

    def closeEvent(self, event):
        self.write_settings()
        if self.analysis_dialog is not None:
            self.analysis_dialog.close()
        event.accept()

    @pyqtSlot()
    def on_action_edit_preferences_triggered(self):
        #print("edit preferences")
        self.preferences_dialog = PreferencesDialog(self)
        #self.preferences_dialog.setWindowModality(Qt.ApplicationModal)
        self.preferences_dialog.show()
    
    @pyqtSlot()
    def on_action_exit_triggered(self):
        self.close()

    @pyqtSlot() 
    def on_action_about_triggered(self):
        text = mu.PROGRAM_NAME + " v" + mu.PROGRAM_VERSION + "\n\n"
        text += "Morphometrics made easy\n\n"
        text += "This software is distributed under the terms of the MIT License.\n\n"
        text += "© 2023-2024 Jikhan Jung\n"

        QMessageBox.about(self, "About", text)

        license_text = """
Modan2
Copyright 2023-2024 Jikhan Jung

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

    @pyqtSlot()
    def on_action_analyze_dataset_triggered(self):
        if self.selected_dataset is None:
            QMessageBox.warning(self, "Warning", "No dataset selected")
            return
        prev_lm_count = -1
        if self.selected_dataset.object_list is None or len(self.selected_dataset.object_list) < 5:
            error_message = "Error: number of objects is too small for analysis."
            logger.error(error_message)
            mu.show_error_message(error_message)
            return

        for obj in self.selected_dataset.object_list:
            obj.unpack_landmark()
            lm_count = len(obj.landmark_list)
            #print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
            if prev_lm_count != lm_count and prev_lm_count != -1:
                # show messagebox and close the window
                error_message = "Error: landmark count is not consistent."
                logger.error(error_message)
                mu.show_error_message(error_message)
                return
            prev_lm_count = lm_count
        
        if True:
            valid_property_index_list = self.selected_dataset.get_valid_property_index_list()
            if len(valid_property_index_list) == 0:
                # alert no valid property
                variable_names = ', '.join(self.selected_dataset.get_propertyname_list())

                error_message = f"Error: No categorical (grouping) variables found in the dataset. \n\n"
                logger.error(error_message)
                error_message += f"All variables seem to be continuous measurements. The dataset contains the following variables: [{variable_names}]. "
                error_message += f"Please ensure that your dataset includes at least one categorical variable for grouping. "
                error_message += f"If you believe a variable should be considered categorical, check its data and format."
                #error_message = "Error: No grouping variable found in the dataset."
                mu.show_error_message(error_message)
                return

            self.analysis_dialog = NewAnalysisDialog(self,self.selected_dataset)
            ret = self.analysis_dialog.exec_()
            logger.info( "new analysis dialog return value %s", ret)
            if ret == 0:

                return
            elif ret == 1:
                superimposition_method = self.analysis_dialog.comboSuperimposition.currentText()
                cva_group_by = self.analysis_dialog.comboCvaGroupBy.currentData()
                manova_group_by = self.analysis_dialog.comboManovaGroupBy.currentData()
                analysis_name = self.analysis_dialog.edtAnalysisName.text()
                self.run_analysis(superimposition_method, cva_group_by, manova_group_by, analysis_name, self.selected_dataset )
                #logger.info("calling run analysis %s %s %s %s %s", superimposition_method, ordination_method, group_by, analysis_name, self.selected_dataset.dataset_name)
                #logger.info("call run analysis", superimposition_method, ordination_method, group_by, self.selected_dataset)
                self.reset_treeView()
                self.load_dataset()
        else:
            self.analysis_dialog = DatasetAnalysisDialog(self,self.selected_dataset)
            self.analysis_dialog.show()

    def run_analysis(self, superimposition_method, cva_group_by, manova_group_by, analysis_name, dataset):
        logger.info("run analysis %s %s %s %s %s", superimposition_method, cva_group_by, manova_group_by, analysis_name, dataset.dataset_name)
        #print("pca button clicked")
        # set wait cursor
        
        #QApplication.processEvents()

        ds_ops = MdDatasetOps(dataset)
        #if dataset.dimension == 2:
        #    for obj in dataset.object_list:
        #        if
        #        obj.apply_scale()
        #for obj_ops in ds_ops.object_list:
        #    if 
        analysis_done = False
        #analysis_type = analysis_method

        QApplication.setOverrideCursor(Qt.WaitCursor)
        if not ds_ops.procrustes_superimposition():
            error_message = "Procrustes superimposition failed"
            logger.error(error_message)
            mu.show_error_message(error_message)
            return
        #self.show_object_shape()

        cva_analysis_result = PerformCVA(ds_ops, cva_group_by)
        if cva_analysis_result is None:
            error_message = "CVA analysis failed"
            logger.error(error_message)
            mu.show_error_message(error_message)
            return
        pca_analysis_result = PerformPCA(ds_ops)
        if pca_analysis_result is None:
            error_message = "PCA analysis failed"
            logger.error(error_message)
            mu.show_error_message(error_message)
            return

        manova_analysis_result = PerformPCA(ds_ops)

        eigenvalues_list = []
        eigenvalues_cumulative_percentage = 0
        #print("raw eigenvalues:",pca_analysis_result.raw_eigen_values)
        #print("eigenvalues:",pca_analysis_result.eigen_value_percentages)
        for i, val in enumerate(pca_analysis_result.raw_eigen_values):
            val2 = pca_analysis_result.eigen_value_percentages[i]
            eigenvalues_list.append( val )
            eigenvalues_cumulative_percentage += val2
            #print("eigenvalues:",eigenvalues_list)
            if eigenvalues_cumulative_percentage > 0.9:
                break
        effective_eigenvalues = len(eigenvalues_list)
        #print("eigen_value list",eigenvalues_list)
        #print("effective eigenvalues:",effective_eigenvalues)
        manova_datamatrix = [ pc_score_list[:effective_eigenvalues] for pc_score_list in pca_analysis_result.rotated_matrix.tolist() ] 
            #analysis.eigenvalues_json = json.dumps(eigenvalues_list)

        manova_analysis_result = PerformManova(ds_ops, manova_datamatrix, manova_group_by)

        pca_new_coords = pca_analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(ds_ops.object_list):
            obj.analysis_result = pca_new_coords[i]

        cva_new_coords = pca_analysis_result.rotated_matrix.tolist()
        for i, obj in enumerate(ds_ops.object_list):
            obj.analysis_result = cva_new_coords[i]

        analysis = MdAnalysis()
        analysis.dataset = dataset
        analysis.analysis_name = analysis_name
        #analysis.analysis_type = analysis_type
        analysis.superimposition_method = superimposition_method
        analysis.dimension = dataset.dimension
        analysis.wireframe = dataset.wireframe
        analysis.baseline = dataset.baseline
        analysis.polygons = dataset.polygons
        analysis.propertyname_str = dataset.propertyname_str

        cva_group_by_name = dataset.propertyname_list[cva_group_by]
        manova_group_by_name = dataset.propertyname_list[manova_group_by]

        ''' manova results'''
        #print("MANOVA result:",manova_analysis_result.results)
        #print("group by:", manova_group_by, manova_group_by_name)
        stat_text = str(manova_analysis_result.results[manova_group_by_name]['stat'])
        column_names = ["", "Value", "Num DF", "Den DF", "F Value", "Pr > F"]
        lines = stat_text.strip().splitlines()

        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        stat_dict = {}
        for line in lines[1:]:
            data = line.split()
            stat_name = ""  # Initialize stat_name as an empty string
            stat_values = []
            for entry in data:
                if mu.is_numeric(entry):  # Check if entry is numeric
                    stat_values.append(float(entry))
                else:
                    stat_name += entry + " "  # Append entry with whitespace
            stat_name = stat_name.strip()  # Remove trailing whitespace from stat_name
            stat_dict[stat_name] = stat_values
            #print(column_names, stat_values)
            #for idx, colname in enumerate(column_names):
            #    stat_dict[stat_name][colname] = stat_values[idx]
            #    analysis.manova_analysis_result_json = json.dumps()
        stat_dict['column_names'] = column_names
        analysis.manova_analysis_result_json = json.dumps(stat_dict)

        object_info_list = []
        raw_landmark_list = []
        property_len = len(dataset.get_propertyname_list()) or 0
        object_list = dataset.object_list.order_by(MdObject.sequence)
        for obj in object_list:
            raw_landmark_list.append( obj.get_landmark_list() )
            object_info_list.append( { "id": obj.id, "name": obj.object_name, "sequence": obj.sequence, "csize": obj.get_centroid_size(), "property_list": obj.get_property_list()[:property_len] })
        analysis.raw_landmark_json = json.dumps(raw_landmark_list)
        analysis.object_info_json = json.dumps(object_info_list)

        superimposed_landmark_list = []
        for obj_ops in ds_ops.object_list:
            superimposed_landmark_list.append( obj_ops.landmark_list )
        analysis.superimposed_landmark_json = json.dumps(superimposed_landmark_list)


        pca_new_coords = pca_analysis_result.rotated_matrix.tolist()
        analysis.pca_analysis_result_json = json.dumps(pca_new_coords)
        rotation_matrix = pca_analysis_result.rotation_matrix.tolist()
        analysis.pca_rotation_matrix_json = json.dumps(rotation_matrix)

        cva_new_coords = cva_analysis_result.rotated_matrix.tolist()
        analysis.cva_analysis_result_json = json.dumps(cva_new_coords)
        rotation_matrix = cva_analysis_result.rotation_matrix.tolist()
        analysis.cva_rotation_matrix_json = json.dumps(rotation_matrix)

        analysis.cva_group_by = dataset.get_propertyname_list()[cva_group_by]
        analysis.manova_group_by = dataset.get_propertyname_list()[manova_group_by]
            
        eigenvalues_list = []
        for i, val in enumerate(pca_analysis_result.raw_eigen_values):
            val2 = pca_analysis_result.eigen_value_percentages[i]
            eigenvalues_list.append( [val, val2] )
        analysis.pca_eigenvalues_json = json.dumps(eigenvalues_list)

        eigenvalues_list = []
        for i, val in enumerate(cva_analysis_result.raw_eigen_values):
            val2 = cva_analysis_result.eigen_value_percentages[i]
            eigenvalues_list.append( [val, val2] )
        analysis.cva_eigenvalues_json = json.dumps(eigenvalues_list)

        analysis.save()

        #print("result:",new_coords)
        #self.show_analysis_result()

        # end wait cursor
        #self.analysis_done = True
        QApplication.restoreOverrideCursor()

    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #self.object_view_2d = LandmarkEditor(self)
        self.object_view_2d = ObjectViewer2D(self)
        self.object_view_2d.set_mode(MODE['VIEW'])
        self.object_view_3d = ObjectViewer3D(self)
        self.object_view = self.object_view_2d
        self.object_view_3d.hide()

        self.tableview_widget = QWidget()
        self.tableview_layout = QVBoxLayout()
        self.object_button_widget = QWidget()
        self.object_button_layout = QHBoxLayout()
        self.object_button_widget.setLayout(self.object_button_layout)

        self.btnSaveObjectInfo = QPushButton("Save Changes")
        self.btnEditObject = QPushButton("Edit Object")
        self.btnAddObject = QPushButton("Add Object")
        self.btnAddProperty = QPushButton("Add Variable")
        self.object_button_layout.addWidget(self.btnAddObject)
        self.object_button_layout.addWidget(self.btnEditObject)
        self.object_button_layout.addWidget(self.btnAddProperty)
        self.object_button_layout.addWidget(self.btnSaveObjectInfo)

        self.tableview_layout.addWidget(self.tableView)
        self.tableview_layout.addWidget(self.object_button_widget)
        self.tableview_widget.setLayout(self.tableview_layout)
        self.btnSaveObjectInfo.clicked.connect(self.on_btnSaveObjectInfo_clicked)
        self.btnAddObject.clicked.connect(self.on_action_new_object_triggered)
        self.btnEditObject.clicked.connect(self.on_tableView_doubleClicked)
        self.btnAddProperty.clicked.connect(self.on_action_new_property_triggered)



        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        self.vsplitter.addWidget(self.tableview_widget)
        self.vsplitter.addWidget(self.object_view_2d)
        self.vsplitter.addWidget(self.object_view_3d)

        #self.treeView = MyTreeView()
        self.hsplitter.addWidget(self.treeView)
        self.hsplitter.addWidget(self.vsplitter)
        self.hsplitter.setSizes([300, 800])
        self.analysis_view = QWidget()
        self.analysis_view_layout = QVBoxLayout()
        self.analysis_view.setLayout(self.analysis_view_layout)
        self.analysis_info_widget = AnalysisInfoWidget(self)
        self.analysis_view_layout.addWidget(self.analysis_info_widget)

        self.btnSaveAnalysis = QPushButton("Save")
        self.btnSaveAnalysis.clicked.connect(self.btnSaveAnalysis_clicked)
        self.btnAnalysisDetail = QPushButton("Analysis Details")
        self.btnAnalysisDetail.clicked.connect(self.btnAnalysisDetail_clicked)
        self.btnDataExploration = QPushButton("Data Exploration")
        self.btnDataExploration.clicked.connect(self.btnDataExploration_clicked)
        self.analysis_button_layout = QHBoxLayout()
        self.analysis_button_layout.addWidget(self.btnSaveAnalysis)
        self.analysis_button_layout.addWidget(self.btnAnalysisDetail)
        self.analysis_button_layout.addWidget(self.btnDataExploration)
        self.analysis_button_widget = QWidget()
        self.analysis_button_widget.setLayout(self.analysis_button_layout)
        self.analysis_view_layout.addWidget(self.analysis_button_widget)



        self.setCentralWidget(self.hsplitter)

        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)

        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.treeView.customContextMenuRequested.connect(self.open_treeview_menu)


    def btnAnalysisDetail_clicked(self):
        #self.detail_dialog = DatasetAnalysisDialog(self.parent)
        self.analysis_dialog = DatasetAnalysisDialog(self,self.analysis_info_widget.analysis.dataset)
        self.analysis_dialog.show()


    def btnSaveAnalysis_clicked(self):
        pass

    def btnDataExploration_clicked(self):
        #print("btnExplore_clicked")
        self.exploration_dialog = DataExplorationDialog(self)
        #print("exploration dialog created")
        # get tab text
        tab_text = self.analysis_info_widget.analysis_tab.tabText(self.analysis_info_widget.analysis_tab.currentIndex())
        if tab_text == "PCA":
            group_by = self.analysis_info_widget.comboPcaGroupBy.currentText()
        elif tab_text == "CVA":
            group_by = self.analysis_info_widget.comboCvaGroupBy.currentText()
        elif tab_text == "MANOVA":
            group_by = self.analysis_info_widget.comboManovaGroupBy.currentText()

        #group_by = self.comboCvaGroupBy
        #print("going to call set_analysis")
        self.exploration_dialog.set_analysis(self.analysis_info_widget.analysis, tab_text, group_by)
        #print("going to update chart")
        #print("going to show")
        self.exploration_dialog.show()
        self.exploration_dialog.update_chart()
        #self.exploration_dialog.activateWindow()

    def on_action_new_property_triggered(self):
        if self.selected_dataset is None:
            return
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter new property name', text="")
        if ok:
            self.selected_dataset.add_propertyname(text)
            ds = self.selected_dataset
            self.load_dataset()
            # select current dataset
            self.select_dataset(ds)
            self.load_object()

    def on_btnSaveObjectInfo_clicked(self):
        # save object info
        # get object info from tableview
        self.object_model.save_object_info()
        self.object_model.resetColors()
        self.data_changed = False
        self.btnSaveObjectInfo.setEnabled(False)
        #indexes = self.tableView.selectedIndexes()

    @pyqtSlot()
    def on_action_delete_object_triggered(self):
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

    def open_treeview_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            action_add_dataset = QAction("Add child dataset")
            action_add_dataset.triggered.connect(self.on_action_new_dataset_triggered)
            action_add_object = QAction("Add object")
            action_add_object.triggered.connect(self.on_action_new_object_triggered)
            action_add_analysis = QAction("Add analysis")
            action_add_analysis.triggered.connect(self.on_action_analyze_dataset_triggered)
            action_explore_data = QAction("Explore data")
            action_explore_data.triggered.connect(self.on_action_explore_data_triggered)
            action_delete_analysis = QAction("Delete analysis")
            action_delete_analysis.triggered.connect(self.on_action_delete_analysis_triggered)
            action_refresh_tree = QAction("Reload")
            action_refresh_tree.triggered.connect(self.load_dataset)

            # get item
            item = self.dataset_model.itemFromIndex(index)
            obj = item.data()

            menu = QMenu()
            if isinstance(obj, MdDataset):
                self.selected_dataset = obj
                menu.addAction(action_add_dataset)
                menu.addAction(action_add_object)
                menu.addAction(action_add_analysis)
                menu.addAction(self.actionExport)
                menu.addAction(action_refresh_tree)
            elif isinstance(obj, MdAnalysis):                
                #menu.addAction(action_explore_data)
                menu.addAction(action_delete_analysis)
                menu.addAction(action_refresh_tree)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    #def on_action_new_analysis_triggered(self):


    def on_action_delete_analysis_triggered(self):
        ret = QMessageBox.warning(self, "Warning", "Are you sure to delete the selected analysis?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        selected_indexes = self.treeView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return
        item = self.dataset_model.itemFromIndex(selected_indexes[0])
        analysis = item.data()
        analysis.delete_instance()
        self.load_dataset()

    def on_action_explore_data_triggered(self):
        print("data exploration")
        self.exploration_dialog = DataExplorationDialog(self)
        print("about to set analysis")
        self.exploration_dialog.set_analysis(self.selected_analysis)
        self.exploration_dialog.show()
        #self.load_dataset()

    @pyqtSlot()
    def on_action_import_dataset_triggered(self):
        self.dlg = ImportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()
        self.load_dataset()        

    @pyqtSlot()
    def on_action_export_dataset_triggered(self):
        if self.selected_dataset is None:
            return
        self.dlg = ExportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()

    @pyqtSlot()
    def on_action_new_dataset_triggered(self):
        # open new dataset dialog
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        if self.selected_dataset:
            self.dlg.set_parent_dataset( self.selected_dataset )
        else:
            self.dlg.set_parent_dataset( None )

        ret = self.dlg.exec_()
        self.load_dataset()
        self.reset_tableView()


    def get_selected_dataset(self):
        selected_indexes = self.treeView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None
        else:
            selected_dataset_list = []
            for index in selected_indexes:
                item = self.dataset_model.itemFromIndex(index)
                dataset = item.data()
                selected_dataset_list.append(dataset)
            return selected_dataset_list[0]

    @pyqtSlot()
    def on_treeView_clicked(self,event):
        #print("clicked")
        event.accept()
        self.selected_dataset = self.get_selected_dataset()
        if self.selected_dataset is None:
            #print("no dataset selected")
            self.actionNewObject.setEnabled(False)
            self.actionExport.setEnabled(False)
            self.actionAnalyze.setEnabled(False)
        else:
            self.actionNewObject.setEnabled(True)
            self.actionExport.setEnabled(True)
            self.actionAnalyze.setEnabled(True)
            self.load_object()
        #self.dlg = DatasetDialog(self)


    @pyqtSlot()
    def on_treeView_doubleClicked(self):
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset( self.selected_dataset )
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

    def select_dataset(self,dataset,node=None):
        if dataset is None:
            return
        if node is None:
            node = self.dataset_model.invisibleRootItem()   

        for i in range(node.rowCount()):
            item = node.child(i,0)
            if item.data() == dataset:
                self.treeView.setCurrentIndex(item.index())
                break
            self.select_dataset(dataset,node.child(i,0))

    @pyqtSlot()
    def on_action_new_object_triggered(self):
        # open new object dialog
        if not self.selected_dataset:
            return
        self.dlg = ObjectDialog(self)
        self.dlg.set_dataset(self.selected_dataset)
        object = MdObject()
        object.dataset = self.selected_dataset
        object.sequence = self.selected_dataset.object_list.count() + 1
        self.dlg.set_object(object)
        ret = self.dlg.exec_()
        if ret == 0:
            return

        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()

    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        if self.selected_object is None:
            print("no object selected")
            return
        self.dlg = ObjectDialog(self)
        #print("object dialog created")
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        #print("object dialog set dataset")
        self.dlg.set_object( self.selected_object )
        self.dlg.set_tableview(self.tableView)
        #print("object dialog set object")
        ret = self.dlg.exec_()
        if ret == 0:
            return
        elif ret == 1:
            if self.dlg.object_deleted:
                dataset = self.selected_dataset
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)
                self.load_object()
            return
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
        header = self.treeView.header()
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)

        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        self.treeView.dropEvent = self.dropEvent
        self.treeView.dragEnterEvent = self.treeView_drag_enter_event
        self.treeView.dragMoveEvent = self.treeView_drag_move_event

    def treeView_drag_enter_event(self, event):
        event.accept()
    def treeView_drag_move_event(self, event):
        event.accept()

    # accept drop event
    def dropEvent(self, event):
        if event.source() == self.treeView:
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
            shift_clicked = False
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                shift_clicked = True

            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()
            #print("target_dataset",target_dataset)

            selected_object_list = self.get_selected_object_list()
            source_dataset = None
            #print("selected_object_list",selected_object_list)

            total_count = len(selected_object_list)
            current_count = 0

            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.setModal(True)
            if shift_clicked:
                label_text = "Moving {} objects...".format(total_count)
            else:
                label_text = "Copying {} objects...".format(total_count)
            self.progress_dialog.lbl_text.setText(label_text)
            self.progress_dialog.pb_progress.setValue(0)
            self.progress_dialog.show()


            for source_object in selected_object_list:
                source_dataset = source_object.dataset
                current_count += 1
                self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
                self.progress_dialog.update()
                QApplication.processEvents()
                if self.progress_dialog.stop_progress:
                    break

                if source_object.dataset.dimension == target_dataset.dimension:
                    # if shift is pressed, move instead of copy
                    if shift_clicked:
                        source_object.change_dataset(target_dataset)
                        source_object.save()
                    else:
                        # copy object
                        new_object = source_object.copy_object(target_dataset)
                        new_object.save()
                        if source_object.has_image():
                            new_image = source_object.get_image().copy_image(new_object)
                            new_image.save()
                        elif source_object.has_threed_model():
                            new_model = source_object.get_threed_model().copy_threed_model(new_object)
                            new_model.save()
                            
                else:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch")
                    break
            self.progress_dialog.close()

            if source_dataset is not None:
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(source_dataset)
        elif event.mimeData().hasUrls():
            #print("file drop")
            file_path = event.mimeData().text()
            #file_path = re.sub('file:///', '', file_path)
            file_path = mu.process_dropped_file_name(file_path)
            #print("file path:", file_path)
            self.import_dialog = ImportDatasetDialog(self)
            self.import_dialog.setModal(True)
            self.import_dialog.setWindowModality(Qt.ApplicationModal)
            self.import_dialog.open_file2(file_path)
            self.import_dialog.exec_()
            self.load_dataset()



    def get_selected_object_list(self):
        #print("get selected object")
        selected_indexes = self.tableView.selectionModel().selectedIndexes()
        #print("selected indexes:", selected_indexes)
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
            #print("index:", index.row())

            # Directly access data using MdTableModel's internal structure
            object_id = self.object_model._data[index.row()][0]["value"]

            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            if object is not None and object not in selected_object_list:
                selected_object_list.append(object)

        return selected_object_list

    def on_object_data_changed(self):
        self.data_changed = True
        self.btnSaveObjectInfo.setEnabled(True)

    def reset_tableView(self):
        #print("reset tableview")
        #self.object_model = QStandardItemModel()
        self.btnSaveObjectInfo.setEnabled(False)
        self.btnAddObject.setEnabled(False)
        self.btnAddProperty.setEnabled(False)
        self.btnEditObject.setEnabled(False)
        self.object_model = MdTableModel()
        self.object_model.dataChangedCustomSignal.connect(self.on_object_data_changed)
        #print("mdtablemodel set")
        header_labels = ["ID", "Seq.", "Name", "Count", "CSize"]
        if self.selected_dataset is not None:
            self.selected_dataset.unpack_propertyname_str()
            if self.selected_dataset.propertyname_list is not None and len( self.selected_dataset.propertyname_list ) > 0:
                header_labels.extend( self.selected_dataset.propertyname_list )
            if self.selected_dataset.dimension == 2:
                self.object_view = self.object_view_2d
                self.object_view_2d.show()
                self.object_view_3d.hide()
            else:
                #self.object_view_3d.deleteLater()
                #self.object_view_3d = MyGLWidget(self)
                self.object_view = self.object_view_3d
                #self.vsplitter.addWidget(self.object_view_3d)
                self.object_view_2d.hide()
                self.object_view_3d.show()
        #self.object_model.setColumnCount(len(header_labels))
        #self.object_model.setHorizontalHeaderLabels( header_labels )
        #print("horizontal header:", header_labels)
        self.object_model.setHorizontalHeader( header_labels )
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        #print("-1")
        self.tableView.setModel(self.proxy_model)        

        #self.tableView.setColumnWidth(0, 50)
        #self.tableView.setColumnWidth(1, 200)
        #self.tableView.setColumnWidth(2, 50)
        #self.tableView.setColumnWidth(3, 50)
        
        #print("0")
        header = self.tableView.horizontalHeader()    
        #print("0.2")
        header.resizeSection(1,200)
        header.setDefaultSectionSize(15)
        #header.setSectionResizeMode(1,QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(1, QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QHeaderView.Stretch)
        #print("0.3")
        #self.tableView.verticalHeader().setDefaultSectionSize(20)
        #print("0.5")
        #self.tableView.verticalHeader().setVisible(False)
        #self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)
        #print("1")

        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)
        #print("tableview accept drops:", self.tableView.acceptDrops())
        self.tableView.setDropIndicatorShown(True)
        self.tableView.dropEvent = self.tableView_drop_event
        self.tableView.dragEnterEvent = self.tableView_drag_enter_event
        self.tableView.dragMoveEvent = self.tableView_drag_move_event
        #print("2")

        self.tableView.setSortingEnabled(True)
        self.tableView.sortByColumn(1, Qt.AscendingOrder)
        #print("3")
        #self.object_model.setSortRole(Qt.UserRole)
        #print("4")
        self.clear_object_view()
        #print("5")

    def tableView_drop_event(self, event):
        if self.selected_dataset is None:
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        if len(file_name_list) == 0:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        total_count = len(file_name_list)
        current_count = 0
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.setModal(True)
        if self.selected_dataset.dimension == 3:
            label_text = "Importing 3d model files..."
        else:
            label_text = "Importing image files..."
        self.progress_dialog.lbl_text.setText(label_text)
        self.progress_dialog.pb_progress.setValue(0)
        self.progress_dialog.show()

        for file_name in file_name_list:
            current_count += 1
            self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
            self.progress_dialog.update()
            QApplication.processEvents()

            file_name = mu.process_dropped_file_name(file_name)

            ext = file_name.split('.')[-1].lower()
            if ext in mu.IMAGE_EXTENSION_LIST:
                if self.selected_dataset.dimension != 2:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch.")
                    break
                obj = self.selected_dataset.add_object(object_name=Path(file_name).stem)
                obj.save()
                img = obj.add_image(file_name)
                img.save()

            elif ext in mu.MODEL_EXTENSION_LIST:
                if self.selected_dataset.dimension != 3:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch.")
                    break
                obj = self.selected_dataset.add_object(object_name=Path(file_name).stem)
                obj.save()
                mdl = obj.add_threed_model(file_name)
                mdl.save()

            elif os.path.isdir(file_name):
                self.statusBar.showMessage("Cannot process directory...",2000)

            else:
                self.statusBar.showMessage("Nothing to import.",2000)

            self.load_object()

        self.progress_dialog.close()

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
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon(mu.resource_path(ICON['dataset_2d'])))
            else:
                item1.setIcon(QIcon(mu.resource_path(ICON['dataset_3d'])))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            
            self.dataset_model.appendRow([item1,item2])#,item2,item3] )
            if rec.analyses.count() > 0:
                self.load_analysis(item1,rec)
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)
        #self.treeView.setIconSize(QSize(16,16))

    def load_analysis(self, parent_item, dataset):
        all_record = MdAnalysis.filter(dataset=dataset)
        for rec in all_record:
            item1 = QStandardItem(rec.analysis_name)
            item1.setIcon(QIcon(mu.resource_path(ICON['analyze'])))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            parent_item.appendRow([item1,item2])

    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            rec.unpack_wireframe()
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon(mu.resource_path(ICON['dataset_2d']))) 
            else:
                item1.setIcon(QIcon(mu.resource_path(ICON['dataset_3d'])))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            parent_item.appendRow([item1,item2])#,item3] )
            if rec.analyses.count() > 0:
                self.load_analysis(item1,rec)
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())

    def on_dataset_selection_changed(self, selected, deselected):
        if self.data_changed:
            ret = QMessageBox.warning(self, "Warning", "Data has been changed. Do you want to save?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                self.on_btnSaveObjectInfo_clicked()
            elif ret == QMessageBox.Cancel:
                # cancel selection change by selecting deselected
                self.treeView.selectionModel().selectionChanged.disconnect(self.on_dataset_selection_changed)
                self.treeView.selectionModel().clearSelection()
                self.treeView.selectionModel().select(deselected, QItemSelectionModel.Select)
                self.treeView.selectionModel().selectionChanged.connect(self.on_dataset_selection_changed)
                return
            else:
                self.data_changed = False
            
        #print("dataset selection changed")
        indexes = selected.indexes()
        #print(indexes)
        if indexes:
            self.object_model.clear()
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            obj = item1.data()
            if isinstance(obj, MdDataset):
                self.selected_dataset = obj
                self.load_object()
                if self.hsplitter.widget(1) != self.vsplitter:
                    self.hsplitter.replaceWidget(1,self.vsplitter)                
                self.actionAnalyze.setEnabled(True)
                self.actionNewObject.setEnabled(True)
                self.actionExport.setEnabled(True)
            elif isinstance(obj, MdAnalysis):
                self.selected_analysis = obj
                if self.hsplitter.widget(1) != self.analysis_view:
                    self.hsplitter.replaceWidget(1,self.analysis_view)
                self.analysis_info_widget.set_analysis(self.selected_analysis)
                self.analysis_info_widget.show_analysis_result()

                #self.actionAnalyze.setEnabled(False)
                #self.actionNewObject.setEnabled(False)
                #self.actionExport.setEnabled(False)
        else:
            self.actionAnalyze.setEnabled(False)
            self.actionNewObject.setEnabled(False)
            self.actionExport.setEnabled(False)

    def load_object(self):
        #print("load_object")
        self.object_model.clear()
        self.reset_tableView()
        self.clear_object_view()
        if self.selected_dataset is None:
            return

        self.btnEditObject.setEnabled(False)
        self.btnAddProperty.setEnabled(True)
        self.btnAddObject.setEnabled(True)
        self.btnSaveObjectInfo.setEnabled(False)

        object_list = self.selected_dataset.object_list.order_by(MdObject.sequence,MdObject.id)

        for idx, obj in enumerate(self.selected_dataset.object_list):
            seq = obj.sequence
            if seq is None:
                seq = idx + 1
                obj.sequence = seq
                obj.save()
            row_data = [ obj.id, seq, obj.object_name, obj.count_landmarks(), obj.get_centroid_size()]
            '''
            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            lm_count = obj.count_landmarks()
            item3 = QStandardItem()
            item3.setData(lm_count,Qt.DisplayRole)
            item4 = QStandardItem()
            if len(obj.landmark_list) == 0 and obj.landmark_str is not None and len(obj.landmark_str) > 0:
                obj.unpack_landmark()
            csize = obj.get_centroid_size()
            csize = round(csize,2)
            csize_str = str(csize)
            if csize < 0:
                csize_str = ""
            item4.setData(csize_str,Qt.DisplayRole)

            item_list = [item1,item2,item3,item4]
            '''
            if len(self.selected_dataset.propertyname_list) > 0:
                property_list = obj.unpack_property()

                for idx,prop in enumerate(self.selected_dataset.propertyname_list):
                    
                    #item = QStandardItem()
                    if idx < len(property_list):
                        #item.setData(property_list[idx],Qt.DisplayRole)
                        item = property_list[idx]
                    else:
                        #item.setData('',Qt.DisplayRole)
                        item = ''
                    #row_data.append(item)
                    
                    row_data.append(item)

            self.object_model.appendRows([row_data])

    def on_object_selection_changed(self, selected, deselected):
        #print("object selection changed 1")
        selected_object_list = self.get_selected_object_list()
        if selected_object_list is None or len(selected_object_list) != 1:
            self.btnEditObject.setEnabled(False)
            return
        #print("object selection changed 2")

        self.btnEditObject.setEnabled(True)
        object_id = selected_object_list[0].id
        self.selected_object = MdObject.get_by_id(object_id)
        self.selected_object.unpack_landmark()
        self.show_object(self.selected_object)

    def show_object(self, obj):
        #print("show object")
        self.object_view.clear_object()
        #print("cleared object view")
        self.object_view.landmark_list = copy.deepcopy(obj.landmark_list)
        #print("landmark list copied")
        self.object_view.set_object(obj)
        #print("set object", obj)
        self.object_view.read_only = True
        #print("object_view:", self.object_view)
        self.object_view.update()

    def clear_object_view(self):
        self.object_view.clear_object()

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    #with open('log.txt', 'w') as f:
    #    f.write("hello\n")
    #    # current directory
    #    f.write("current directory 1:" + os.getcwd() + "\n")
    #    f.write("current directory 2:" + os.path.abspath(".") + "\n")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(mu.resource_path('icons/Modan2_2.png')))
    app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,mu.COMPANY_NAME, mu.PROGRAM_NAME)

    translator = QTranslator()
    app.language = app.settings.value("language", "en")
    translator.load(mu.resource_path("translations/Modan2_{}.qm".format(app.language)))
    app.installTranslator(translator)

    #app.settings = 
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = ModanMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()
    #myWindow.activateWindow()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()


''' 
How to make an exe file

pyinstaller --name "Modan2_v0.1.3_20240617.exe" --onefile --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Modan2_2.png" Modan2.py
pyinstaller --onedir --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Modan2_2.png" --noconfirm Modan2.py
#--upx-dir=/path/to/upx

for MacOS
pyinstaller --onefile --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Modan2_2.png" Modan2.py
pyinstaller --onedir --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Modan2_2.png" --noconfirm Modan2.py

pylupdate5 Modan2.py -ts translations/Modan2_en.ts
pylupdate5 Modan2.py -ts translations/Modan2_ko.ts
pylupdate5 Modan2.py -ts translations/Modan2_ja.ts

linguist


'''