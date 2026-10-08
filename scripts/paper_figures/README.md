# Screenshots of the Modan2 paper

`run_all.sh` takes Figures 2–6 of the paper from a Modan2 checkout, headless:
it builds a throwaway library, starts Modan2 on a private Xvfb display, and
drives the windows and dialogs the way a user would — selecting datasets,
filling in dialogs, running analyses, clicking specimens in morphospace,
tracing a curve — saving each view as a PNG.

```bash
python scripts/rovinsky2021_data.py                      # the cranial data, once
git worktree add /tmp/modan2-v0.2.0 v0.2.0               # the version shown
scripts/paper_figures/run_all.sh /tmp/modan2-v0.2.0 tardigrades.zip figures/
```

Requirements: Xvfb, and a Python environment with Modan2's dependencies
(`PYTHON=~/venv/Modan2/bin/python` to choose one).

## Data

- **Cranial data** (Figures 4–5): the 206 specimens of known diet of Rovinsky
  et al. (2021), from the files `scripts/rovinsky2021_data.py` downloads.
- **Tardigrade images** (Figures 2, 3, 6): not public. `run_all.sh` takes them
  as a Modan2 JSON+ZIP package, exported from the authors' library with
  Export ▸ JSON+ZIP or headless with
  `HOME=<library home> python export_dataset.py <checkout> <dataset id> tardigrades.zip`.
  The dataset is renamed *Milnesium grandicupula* in the figure library.

## What each script captures

| Script | Figures |
|---|---|
| `fig2_3.py` | 2a main window with an analysis in the tree and a specimen previewed; 2b and 3c the object dialog, on two specimens; 2c analysis panel (PCA); 2d Data Exploration; 3a new-dataset dialog (General tab); 3b imported objects; 3d editing a variable |
| `fig4_5.py` | 4a New Analysis dialog; 4b–d PCA, CVA and MANOVA tabs; 5a a specimen picked in morphospace; 5b shape grid with convex hulls |
| `fig6cd.py` | 6c the object list and 6d the object dialog for a specimen with a missing landmark |
| `fig6ab.py` | 6b a curve traced along the body outline with edge snapping off and on; 6a the resulting curve scheme |

## Things that differ from a desktop session

- **Modal dialogs** (`exec_()`) are driven from a timer started before they open.
- **The shape grid** in Data Exploration is a set of translucent top-level
  windows over the plot. Xvfb has no compositing manager, so on screen their
  transparent pixels are black; `composite_shape_grid` paints each view's
  framebuffer, alpha included, over a grab of the window instead.
- **Mouse moves** are sent to the viewer as events: `QTest.mouseMove` moves the
  real cursor, and under Xvfb that motion arrives after the following click.
- The look is Qt's default style on Linux, with its fonts.
