"""Build the library the paper's screenshots are taken from.

Two datasets, and nothing else, so the dataset tree in the figures shows only
what the figures are about:

* the tardigrade images, from a Modan2 JSON+ZIP package exported from the
  authors' library (the images are not public), renamed as given;
* the published cranial data of Rovinsky et al. (2021): the 206 specimens of
  known diet from ``benchmarks/data/rovinsky2021/neurocranium_222.txt`` (written
  by ``scripts/rovinsky2021_data.py``), with the variables the paper uses,
  imported the way the Import dialog imports a Morphologika file.

Usage: python build_library.py <checkout> <work dir> <tardigrades.zip> <name> <neurocranium_222.txt>
"""

import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)

from MdAppSetup import ApplicationSetup  # noqa: E402

ApplicationSetup(language="en", on_data_directory_problem=None).initialize()

import MdModel as mm  # noqa: E402
import MdUtils as mu  # noqa: E402
from components.formats.morphologika import Morphologika  # noqa: E402
from ModanController import ModanController  # noqa: E402

work, tardigrade_zip, tardigrade_name, neurocranium = Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
CRANIAL = "Rovinsky et al. 2021 neurocranium"
VARIABLES = {"Family": "Family", "Genus": "Genus", "Species": "Species", "Diet": "DietFine", "PreySize": "PreyCatg"}

if not mm.MdDataset.select().where(mm.MdDataset.dataset_name == tardigrade_name).exists():
    ds = mm.MdDataset.get_by_id(mu.import_dataset_from_zip(tardigrade_zip))
    ds.dataset_name = tardigrade_name
    ds.save()

if not mm.MdDataset.select().where(mm.MdDataset.dataset_name == CRANIAL).exists():
    src = Morphologika(neurocranium, CRANIAL)
    v = src.variablename_list
    rows = [i for i, p in enumerate(src.property_list_list) if p[v.index("DietFine")] != "NA"]
    names = [src.object_name_list[i] for i in rows]
    lines = ["[individuals]", str(len(names)), "[landmarks]", str(src.nlandmarks), "[dimensions]", "3", "[names]"]
    lines += [*names, "[labels]", "\t".join(VARIABLES), "[labelvalues]"]
    lines += ["\t".join(src.property_list_list[i][v.index(c)] for c in VARIABLES.values()) for i in rows]
    lines.append("[rawpoints]")
    for n in names:
        lines += [f"'{n}", *("\t".join(r) for r in src.landmark_data[n])]
    if src.edge_list:
        lines += ["[wireframe]", *(" ".join(str(x) for x in e) for e in src.edge_list)]
    filtered = work / "neurocranium_206.txt"
    filtered.write_text("\n".join(lines) + "\n")
    ModanController().import_dataset(Morphologika(str(filtered), CRANIAL), CRANIAL, mu.get_storage_directory())

for d in mm.MdDataset.select():
    print("library:", d.dataset_name, f"{d.dimension}D,", len(list(d.object_list)), "objects")
