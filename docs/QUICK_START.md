# Modan2 Quick Start Guide

**Get up and running with Modan2 in 10 minutes!**

---

## 1. Installation (2 minutes)

### Windows
1. Download `Modan2-Setup.exe`
2. Run installer
3. Launch from Start Menu

### macOS
1. Download `Modan2.dmg`
2. Drag to Applications
3. Open from Applications folder

### Linux
```bash
sudo apt-get install python3 python3-pip python3-pyqt5
git clone https://github.com/jikhanjung/Modan2.git
cd Modan2
pip install -r requirements.txt
python3 main.py
```

---

## 2. Create Your First Dataset (1 minute)

1. Click **"New Dataset"** button (or press `Ctrl+N`)
2. Fill in:
   - **Name**: `My_First_Dataset`
   - **Dimension**: `2D`
3. Click **OK**

Done! Your dataset appears in the left panel.

---

## 3. Import Data (2 minutes)

### Option A: Import Landmark File (TPS, NTS, X1Y1, Morphologika)

1. Click **Import** (`Ctrl+I`)
2. Select your file (the format is auto-detected)
3. Click **Import**

✅ Objects appear in the center table! (You can also drag files onto the table.)

### Option B: Import Images for Digitizing

1. Click **Import** (`Ctrl+I`) and select image files (`.jpg`, `.png`), or drag
   them onto the dataset
2. Click **Import**

✅ Images ready for digitizing!

---

## 4. Digitize Landmarks (3 minutes)

**If you imported images**:

1. **Double-click** the first object in the table
2. The object editor opens (Landmark mode is active by default)
3. **Click on the image** to place landmarks (numbered 1, 2, 3... sequentially)
4. **Zoom**: mouse wheel · **Pan**: right-drag on empty space
5. Right-click a landmark to delete it; drag it to move it
6. Click **Save** when done, and use **Next** / **Previous** to move between objects

> **Tip — semi-landmark curves**: click the **Curve** mode button to trace an
> outline; it snaps to image edges automatically and is resampled into evenly
> spaced points. See the full User Guide for details.

---

## 5. Run Analysis (2 minutes)

### Run the Analysis

One run computes **PCA, CVA, and MANOVA together**.

1. Select the dataset and click **Analyze** (`Ctrl+G`)
2. Set the **superimposition method** (Procrustes) and, if you have groups, the
   **CVA / MANOVA grouping variables**
3. Click **OK**

✅ Results appear in ~100ms (for typical datasets)!

### View Results

1. Double-click the completed analysis in the tree to open **Data Exploration**
2. An interactive plot appears:
   - **PC1 vs PC2** scatter plot
   - Objects colored by group
   - Zoom, pan, explore

---

## Quick Reference

### Essential Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New dataset |
| `Ctrl+Shift+N` | New object |
| `Ctrl+Shift+O` | Edit object |
| `Ctrl+I` | Import |
| `Ctrl+E` | Export |
| `Ctrl+G` | Analyze |
| `Ctrl+S` | Save changes |

### Typical Workflow

```
1. Create Dataset
   ↓
2. Import Data (landmarks or images)
   ↓
3. Digitize landmarks / trace curves (if using images)
   ↓
4. Add Variables (optional, for grouping)
   ↓
5. Run Analysis (Procrustes → PCA + CVA + MANOVA)
   ↓
6. View & Interpret Results
   ↓
7. Export (for publication)
```

### Performance Expectations

| Dataset Size | Load Time | Analysis (PCA) |
|--------------|-----------|----------------|
| 50 objects | < 50ms | < 5ms |
| 500 objects | < 200ms | < 50ms |
| 1000 objects | < 600ms | < 80ms |

✅ **Always responsive** - no freezing!

---

## Next Steps

**Learn More**:
- 📖 Full **User Guide**: `docs/USER_GUIDE.md`
- 🔧 **Performance Guide**: `docs/performance.md`
- 💻 **Developer Guide**: `docs/developer_guide.md`

**Try These**:
1. **Add Variables** for grouping (Species, Sex, Age)
2. **Run CVA** to separate groups
3. **Export Results** for publication
4. **Import 3D Models** for 3D analysis

**Get Help**:
- 🐛 Report issues: [GitHub Issues]
- 📧 Email support: [your email]
- 💬 Community: [forum link]

---

## Common First Tasks

### Add Variables for Analysis

1. Right-click the dataset → **Edit Dataset**
2. In the variables section:
   - Click **Add Variable**
   - Enter a name: `Species`
   - Repeat for `Sex`, `Age`, etc.
3. Click **OK**

### Set Object Properties

1. Double-click the object (or right-click → **Edit Object**)
2. Enter the variable values for the object
3. Click **Save**

### Run CVA (Group Comparison)

CVA is part of the standard analysis run:

1. Select the dataset and click **Analyze** (`Ctrl+G`)
2. Set the **CVA grouping variable** to `Species` (or your variable)
3. Click **OK**, then open the result in **Data Exploration**

### Export Results

**Export a dataset**: select it, choose **Export** (`Ctrl+E`), and pick a format
(TPS, X1Y1, Morphologika, or a JSON+ZIP package).

**Export a plot**: in the Data Exploration dialog, use its export/chart-image
control to save the plot for publication.

---

## Troubleshooting Quick Fixes

**Issue**: Can't see imported objects
- **Fix**: Click on dataset in left tree to refresh

**Issue**: Landmarks not placing
- **Fix**: Make sure you opened the object editor (double-click the object) and
  the **Landmark** mode button is selected (not Curve or Calibration)

**Issue**: Analysis fails
- **Fix**: Verify all objects have same number of landmarks

**Issue**: Slow performance
- **Fix**: Resize large images to 1024-2048px before import

**Issue**: Linux Qt error
- **Fix**: Run `python3 fix_qt_import.py` instead

---

## Example Dataset

**Bird Wing Study**:

```
1. Create dataset: "Bird_Wings_2024" (2D)

2. Import images: 50 bird wing photos

3. Digitize 10 landmarks per wing:
   - Wing tip
   - Primary feather attachments (7 points)
   - Wing base (2 points)

4. Add variables:
   - Species (Sparrow, Robin, Finch)
   - Sex (Male, Female)
   - Age (numeric)

5. Set properties for each object:
   - Object 1: Sparrow,Male,2.5
   - Object 2: Sparrow,Female,1.8
   - ...

6. Run Procrustes + PCA:
   - See main shape variation (wing size, shape)

7. Run CVA by Species:
   - See which species separate clearly
   - Check classification accuracy

8. Export results:
   - PC scores as CSV
   - CVA plot as PDF
   - Statistics table
```

**Time**: ~30 minutes for 50 specimens

---

## Performance Tips

✅ **DO**:
- Use 1024-2048px images (good balance)
- Close unused datasets
- Import in batches (10-50 at a time)
- Use keyboard shortcuts

❌ **DON'T**:
- Use huge images (> 5MB) - resize first
- Keep all datasets open - close when done
- Import one-by-one - use batch import

---

## You're Ready! 🎉

**You now know enough to**:
- Create datasets
- Import data
- Digitize landmarks
- Run basic analyses
- View results

**For advanced features**, see the full **User Guide**.

**Questions?** Check the User Guide or report an issue on GitHub.

**Happy analyzing!** 🔬📊

---

**Last Updated**: 2026-07-26
**For Modan2 Version**: 0.2.0-alpha.2
