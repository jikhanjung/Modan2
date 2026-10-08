"""Figures 4 and 5: an analysis of the cranial data grouped by diet, and its
Data Exploration window.

Writes fig4a (the New Analysis dialog), fig4b-d (the PCA, CVA and MANOVA tabs),
fig5a (a specimen picked in morphospace) and fig5b (the shape grid with convex
hulls of the dietary groups).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    composite_shape_grid,
    main_window,
    mm,
    open_exploration,
    pick_specimen,
    pump,
    run_analysis,
    shoot,
    show_analysis,
)

CRANIAL = "Rovinsky et al. 2021 neurocranium"
PICKED = "Canis_lupus"  # Figure 5a names the first specimen of this species

cranial = mm.MdDataset.get(mm.MdDataset.dataset_name == CRANIAL)
w = main_window()

analysis = run_analysis(w, cranial, "Diet", "Diet", shot="fig4a_new_analysis")
info = show_analysis(w, analysis, "Diet")
for tab, name in ((0, "fig4b_pca"), (1, "fig4c_cva"), (2, "fig4d_manova")):
    info.analysis_tab.setCurrentIndex(tab)
    pump()
    if tab == 2:
        # Widen the columns the way a reader would, so no value is elided.
        info.tabManovaResult.resizeColumnsToContents()
        pump()
    shoot(w, name)

ex = open_exploration(w)
pick_specimen(ex, PICKED)
shoot(ex, "fig5a_pick")

ex.cbxConvexHull.setChecked(True)
ex.cbxShapeGrid.setChecked(True)
pump()
ex.update_chart()
pump(120)
composite_shape_grid(ex, "fig5b_shape_grid")
