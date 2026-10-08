"""Figures 2 and 3: the main window, the dataset and object dialogs, and an analysis
of the tardigrades.

Writes fig2a-d and fig3a-d. Figure 2b and 3c both show the object dialog, on
different specimens; Figure 2a is taken once the analysis exists, so the tree
shows datasets and an analysis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    main_window,
    mm,
    open_exploration,
    pick_specimen,
    pump,
    run_analysis,
    select_in_tree,
    shoot,
    show_analysis,
    with_modal,
)
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtWidgets import QListWidgetItem  # noqa: E402

TARDIGRADES = "Milnesium grandicupula"
SPECIMEN_ROW = 3  # the fourth specimen, used throughout
OVERVIEW_ROW = 0  # the first specimen, for the object dialog of Figure 2b

tardigrades = mm.MdDataset.get(mm.MdDataset.dataset_name == TARDIGRADES)
w = main_window()

# Figure 3a: creating the dataset -- name and dimension, on the General tab.
w.selected_dataset = None
w.treeView.clearSelection()
pump()


def fill_new_dataset_dialog():
    dlg = w.dlg
    dlg.edtDatasetName.setText(TARDIGRADES)
    dlg.rbtn2D.setChecked(True)
    for name in tardigrades.propertyname_str.split(","):
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        dlg.lstVariableName.addItem(item)
    dlg.tabs.setCurrentIndex(0)
    pump()
    shoot(dlg, "fig3a_dataset_dialog")
    dlg.reject()


with_modal(w.on_action_new_dataset_triggered, fill_new_dataset_dialog)

# Figure 3b: the imported images as objects.
select_in_tree(w, tardigrades)
shoot(w, "fig3b_objects_imported")

# Figure 3d: a variable edited in the table.
model = w.tableView.model()
headers = [str(model.headerData(c, Qt.Horizontal)) for c in range(model.columnCount())]
index = model.index(SPECIMEN_ROW, headers.index("Tube_shape"))
w.tableView.setCurrentIndex(index)
w.tableView.edit(index)
pump()
shoot(w, "fig3d_variables_edit")


# Figures 3c and 2b: the object dialog, with landmarks and wireframe on the image.
def object_dialog_capture(name):
    def capture():
        dlg = w.dlg
        dlg.resize(1300, 850)
        pump(80)
        shoot(dlg, name)
        dlg.reject()

    return capture


for row, name in ((SPECIMEN_ROW, "fig3c_object_dialog"), (OVERVIEW_ROW, "fig2b_object_dialog")):
    w.tableView.selectRow(row)
    pump()
    with_modal(w.on_tableView_doubleClicked, object_dialog_capture(name))

# Figures 2c and 2d: an analysis grouped by tube shape, and its exploration window.
analysis = run_analysis(w, tardigrades, "Tube shape", "Tube_shape")
info = show_analysis(w, analysis, "Tube_shape")
info.analysis_tab.setCurrentIndex(0)
pump()
shoot(w, "fig2c_analysis_panel_pca")

# Figure 2a: the main window with datasets and an analysis in the tree, a specimen
# selected and its preview shown. Before the exploration window opens, which
# would otherwise overlap it on screen.
select_in_tree(w, tardigrades)
w.treeView.expandAll()
w.tableView.selectRow(SPECIMEN_ROW)
pump(60)
shoot(w, "fig2a_main_window_with_preview")
show_analysis(w, analysis, "Tube_shape")

ex = open_exploration(w)
first = tardigrades.object_list.order_by(mm.MdObject.sequence).first().object_name
pick_specimen(ex, first)
shoot(ex, "fig2d_exploration")
