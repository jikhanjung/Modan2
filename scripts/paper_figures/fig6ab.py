"""Figure 6a-b: a semi-landmark curve, traced the way a user traces one.

On the fourth tardigrade, three clicks along the right body outline, finished
with Enter: once with edge snapping off (captured, then discarded) and once
with it on (captured and saved). The first trace of a dataset asks how many
semi-landmarks the curve carries, which defines the curve scheme; the scheme is
then named in the dataset dialog and its Curves tab captured.

Writes fig6b_left_snap_on and fig6b_right_snap_off (whole dialog, and _crop
around the curve) and fig6a_curve_scheme. Saves the curve to the library, so
it runs after the other figure scripts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, app, main_window, mm, pump, select_in_tree, shoot, with_modal  # noqa: E402
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt, QTimer  # noqa: E402
from PyQt5.QtGui import QMouseEvent  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QInputDialog  # noqa: E402

TARDIGRADES = "Milnesium grandicupula"
N_SEMI = 8
CURVE_NAME = "Body outline, right"
# Image coordinates of three points on the right body outline of the fourth
# specimen, each moved onto the darkest pixel of the line (Gaussian-smoothed
# image, sigma 1.5, searched along the row).
ANCHORS = [[1115, 120], [1061, 400], [875, 720]]

ds = mm.MdDataset.get(mm.MdDataset.dataset_name == TARDIGRADES)
target = ds.object_list.where(mm.MdObject.sequence == 4).get()
w = main_window()
select_in_tree(w, ds)
model = w.tableView.model()
row = next(r for r in range(model.rowCount()) if model.index(r, 2).data() == target.object_name)


def answer_count_prompt():
    """The first trace asks for the curve's number of semi-landmarks."""
    dlg = app.activeModalWidget()
    if isinstance(dlg, QInputDialog):
        dlg.setIntValue(N_SEMI)
        dlg.accept()
    else:
        QTimer.singleShot(100, answer_count_prompt)


def trace(dlg, snap):
    dlg.btnCurve_clicked()
    dlg.cbxSnapToCurve.setChecked(snap)
    pump()
    view = dlg.object_view
    view.setFocus()
    for x, y in ANCHORS:
        pos = QPoint(int(round(view._2canx(x))), int(round(view._2cany(y))))
        # QTest.mouseMove moves the real cursor, and under Xvfb that motion
        # arrives after the click; deliver the move to the viewer directly.
        app.sendEvent(view, QMouseEvent(QEvent.MouseMove, QPointF(pos), Qt.NoButton, Qt.NoButton, Qt.NoModifier))
        pump(5)
        QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, pos)
        pump(10)
    QTimer.singleShot(200, answer_count_prompt)
    QTest.keyClick(view, Qt.Key_Return)
    pump(60)
    dlg.btnLandmark_clicked()  # leave curve mode so the curve is drawn as stored
    pump(40)


def crop_curve(dlg, name, margin=60):
    """Save the part of the viewer around the traced curve."""
    view = dlg.object_view
    xs = [view._2canx(x) for x, _ in ANCHORS]
    ys = [view._2cany(y) for _, y in ANCHORS]
    origin = view.mapTo(dlg, QPoint(0, 0))
    left = int(min(xs)) - margin - 120 + origin.x()
    top = int(min(ys)) - margin + origin.y()
    width = int(max(xs) - min(xs)) + 2 * margin + 240
    height = int(max(ys) - min(ys)) + 2 * margin
    pix = dlg.grab().copy(left, top, width, height)
    pix.save(str(OUT / f"{name}.png"))
    print("saved", f"{name}.png", pix.width(), "x", pix.height())


def tracing(snap, name, save):
    def run():
        dlg = w.dlg
        dlg.resize(1800, 1040)
        pump(60)
        trace(dlg, snap)
        shoot(dlg, name)
        crop_curve(dlg, name + "_crop")
        if save:
            dlg.Okay()  # the Save button
            pump()
            if dlg.isVisible():
                dlg.accept()
        else:
            dlg.reject()

    return run


for snap, name, save in ((False, "fig6b_right_snap_off", False), (True, "fig6b_left_snap_on", True)):
    w.tableView.selectRow(row)
    pump()
    with_modal(w.on_tableView_doubleClicked, tracing(snap, name, save))

# Figure 6a: the curve scheme, named, on the dataset dialog's Curves tab.
select_in_tree(w, mm.MdDataset.get_by_id(ds.id))


def name_and_capture_scheme():
    dlg = w.dlg
    dlg.tabs.setCurrentIndex(2)
    dlg.curveTable.item(0, 1).setText(CURVE_NAME)
    pump()
    shoot(dlg, "fig6a_curve_scheme")
    dlg.Okay()  # the Save button
    pump()


with_modal(w.on_treeView_doubleClicked, name_and_capture_scheme)
print("curve scheme:", mm.MdDataset.get_by_id(ds.id).get_curve_config())
