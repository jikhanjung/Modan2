"""Shared helpers for the paper's screenshots: drive Modan2 headless under Xvfb.

Every script in this folder is run by ``run_all.sh`` as
``python <script> <modan2 checkout> <output dir>``, with the checkout as the
working directory (Modan2 resolves its resources against it), ``HOME`` pointing
at a throwaway library built by ``build_library.py``, and ``DISPLAY`` at Xvfb.
Importing this module starts the application against that library.
"""

import sys
from pathlib import Path

WT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
sys.path.insert(0, str(WT))
OUT.mkdir(parents=True, exist_ok=True)

from PyQt5.QtCore import QItemSelectionModel, QPoint, Qt, QTimer  # noqa: E402
from PyQt5.QtGui import QPainter  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)

from MdAppSetup import ApplicationSetup  # noqa: E402

setup = ApplicationSetup(language="en", on_data_directory_problem=None)
setup.initialize()

import MdModel as mm  # noqa: E402


def pump(n=40):
    for _ in range(n):
        app.processEvents()


def shoot(widget, name):
    """Save what this window shows on screen (OpenGL views included)."""
    pump()
    pix = app.primaryScreen().grabWindow(widget.winId()) if widget.isWindow() else widget.grab()
    if pix.isNull():
        pix = widget.grab()
    pix.save(str(OUT / f"{name}.png"))
    print("saved", f"{name}.png", pix.width(), "x", pix.height())


def main_window(width=1500, height=900):
    from Modan2 import ModanMainWindow

    w = ModanMainWindow(setup.get_config(), config_path=setup.config_path)
    w.resize(width, height)
    w.show()
    pump()
    return w


def select_in_tree(w, target):
    model = w.dataset_model

    def walk(parent):
        for row in range(model.rowCount(parent)):
            index = model.index(row, 0, parent)
            obj = model.itemFromIndex(index).data()
            if type(obj) is type(target) and obj.id == target.id:
                return index
            found = walk(index)
            if found is not None:
                return found
        return None

    index = walk(w.treeView.rootIndex())
    w.treeView.expandAll()
    w.treeView.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
    w.treeView.scrollTo(index)
    pump()
    # Selecting twice in a row left the object table empty; make sure it is filled.
    if isinstance(target, mm.MdDataset) and w.object_model.rowCount() == 0:
        w.load_object()
        pump()


def with_modal(open_dialog, drive, delay=500):
    """Call open_dialog(), which runs a modal exec_(); drive() runs inside it."""
    QTimer.singleShot(delay, drive)
    open_dialog()
    pump()


def run_analysis(w, dataset, name, group_by, shot=None):
    """Run an analysis through the New Analysis dialog, as a user would."""
    select_in_tree(w, dataset)

    def drive():
        dlg = w.analysis_dialog
        dlg.edtAnalysisName.setText(name)
        for combo in (dlg.comboCvaGroupBy, dlg.comboManovaGroupBy):
            combo.setCurrentIndex(combo.findText(group_by))
        pump()
        if shot:
            shoot(dlg, shot)
        dlg.btnOK_clicked()
        pump(80)
        if dlg.isVisible():
            dlg.accept()

    with_modal(w.on_action_analyze_dataset_triggered, drive)
    analysis = mm.MdAnalysis.select().where(mm.MdAnalysis.dataset == dataset).order_by(mm.MdAnalysis.id.desc()).get()
    w.load_dataset()
    pump()
    return analysis


def show_analysis(w, analysis, pca_group_by):
    select_in_tree(w, analysis)
    info = w.analysis_info_widget
    info.comboPcaGroupBy.setCurrentIndex(info.comboPcaGroupBy.findText(pca_group_by))
    pump()
    return info


def open_exploration(w, size=(1500, 900)):
    w.analysis_info_widget.analysis_tab.setCurrentIndex(0)
    pump()
    w.btnDataExploration_clicked()
    ex = w.exploration_dialog
    ex.resize(*size)
    pump(80)
    return ex


def pick_specimen(ex, prefix):
    """Click the plotted point of the first specimen whose name starts with prefix."""
    for group in ex.scatter_data.values():
        for x, y, d in zip(group["x_val"], group["y_val"], group.get("data", [])):
            label = d.get("name") if isinstance(d, dict) else getattr(d, "object_name", "")
            if label and label.startswith(prefix):
                ex.is_picking_shape = True
                ex.pick_idx = 0
                ex.pick_shape(x, y)
                ex.fig2.canvas.draw()
                pump(80)
                return label
    return None


def composite_shape_grid(dialog, name):
    """Grid views are translucent top-level windows; Xvfb has no compositor, so
    paint their framebuffers, alpha included, over a grab of the dialog."""
    base = dialog.grab().toImage()
    painter = QPainter(base)
    origin = dialog.mapToGlobal(QPoint(0, 0))
    for entry in dialog.shape_grid.values():
        view = entry.get("view")
        if view is None or not view.isVisible():
            continue
        if hasattr(view, "grabFrameBuffer"):
            view.makeCurrent()
            frame = view.grabFrameBuffer(withAlpha=True)
        else:
            frame = view.grab().toImage()
        painter.drawImage(view.mapToGlobal(QPoint(0, 0)) - origin, frame)
    painter.end()
    base.save(str(OUT / f"{name}.png"))
    print("saved", f"{name}.png", base.width(), "x", base.height())
