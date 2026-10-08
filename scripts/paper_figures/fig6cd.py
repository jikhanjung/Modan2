"""Figure 6c-d: a missing landmark in the object list and the object dialog, with
its estimated position drawn as a hollow circle.

Uses the tardigrade that has a landmark recorded as missing in the authors' data.
Writes fig6c_object_list_missing and fig6cd_object_dialog_missing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import main_window, mm, pump, select_in_tree, shoot, with_modal  # noqa: E402

TARDIGRADES = "Milnesium grandicupula"

ds = mm.MdDataset.get(mm.MdDataset.dataset_name == TARDIGRADES)
target = next(o for o in ds.object_list.order_by(mm.MdObject.sequence) if "Missing" in (o.landmark_str or ""))
w = main_window()
select_in_tree(w, ds)
model = w.tableView.model()
row = next(r for r in range(model.rowCount()) if model.index(r, 2).data() == target.object_name)
w.tableView.selectRow(row)
w.tableView.scrollTo(model.index(row, 0))
pump(60)
shoot(w, "fig6c_object_list_missing")


def capture_object_dialog():
    dlg = w.dlg
    dlg.resize(1300, 850)
    pump(80)
    shoot(dlg, "fig6cd_object_dialog_missing")
    dlg.reject()


with_modal(w.on_tableView_doubleClicked, capture_object_dialog)
