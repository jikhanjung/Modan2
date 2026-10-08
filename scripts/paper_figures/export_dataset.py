"""Export one dataset of a Modan2 library as a JSON+ZIP package, images included.

The headless equivalent of Export ▸ JSON+ZIP, for producing the tardigrade
package ``build_library.py`` reads. Run with ``HOME`` (or the data folder in
the preferences) pointing at the library that holds the dataset.

Usage: python export_dataset.py <checkout> <dataset id> <package.zip>
"""

import sys

sys.path.insert(0, sys.argv[1])

from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)

from MdAppSetup import ApplicationSetup  # noqa: E402

ApplicationSetup(language="en", on_data_directory_problem=None).initialize()

import MdModel as mm  # noqa: E402
import MdUtils as mu  # noqa: E402

ds = mm.MdDataset.get_by_id(int(sys.argv[2]))
print("exporting", ds.dataset_name, len(list(ds.object_list)), "objects")
if not mu.create_zip_package(ds.id, sys.argv[3], include_files=True):
    sys.exit("export failed")
