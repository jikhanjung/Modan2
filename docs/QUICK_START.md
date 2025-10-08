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
git clone https://github.com/yourusername/Modan2.git
cd Modan2
pip install -r requirements.txt
python3 Modan2.py
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

### Option A: Import Landmark File (TPS, NTS, etc.)

1. **File → Import → TPS** (or your format)
2. Select your `.tps` file
3. Choose dataset: `My_First_Dataset`
4. Click **Import**

✅ Objects appear in the center table!

### Option B: Import Images for Digitizing

1. **File → Import → Images**
2. Select image files (`.jpg`, `.png`)
3. Choose dataset: `My_First_Dataset`
4. Click **Import**

✅ Images ready for digitizing!

---

## 4. Digitize Landmarks (3 minutes)

**If you imported images**:

1. **Double-click** first object in table
2. Object editor opens with image
3. **Click on image** to place landmarks
   - Landmark 1, 2, 3... placed sequentially
4. **Zoom**: Mouse wheel
5. **Pan**: Right-click + drag
6. Click **OK** when done
7. Press **Space** to move to next object

**Keyboard Shortcuts**:
- `Space`: Next object
- `Delete`: Remove last landmark
- `Ctrl+Z`: Undo
- `Esc`: Cancel

---

## 5. Run Analysis (2 minutes)

### Run PCA

1. **Analysis → New Analysis**
2. Select dataset: `My_First_Dataset`
3. Configure:
   - **Superimposition**: Procrustes
   - **Analysis Type**: PCA
4. Click **Run Analysis**

✅ Results appear in ~100ms (for typical datasets)!

### View Results

1. **Analysis → View Analysis Results**
2. Select your PCA analysis
3. Interactive plot appears:
   - **PC1 vs PC2** scatter plot
   - Objects colored by group
   - Zoom, pan, explore

---

## Quick Reference

### Essential Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New dataset |
| `Ctrl+I` | Import |
| `Ctrl+S` | Save |
| `Space` | Next (digitizing) |
| `Delete` | Delete |
| `F2` | Edit |

### Typical Workflow

```
1. Create Dataset
   ↓
2. Import Data (landmarks or images)
   ↓
3. Digitize (if using images)
   ↓
4. Add Variables (optional, for grouping)
   ↓
5. Run Analysis (Procrustes → PCA/CVA)
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

1. Right-click dataset → **Edit Dataset**
2. In "Variable Names" section:
   - Click **Add**
   - Enter variable name: `Species`
   - Repeat for `Sex`, `Age`, etc.
3. Click **OK**

### Set Object Properties

1. Select object in table
2. Right-click → **Edit Object**
3. In "Properties" field, enter comma-separated values:
   - Example: `Sparrow,Male,2.5`
4. Click **OK**

### Run CVA (Group Comparison)

1. **Analysis → New Analysis**
2. Select dataset
3. Configure:
   - **Superimposition**: Procrustes
   - **Analysis Type**: CVA
   - **Grouping Variable**: `Species` (or your variable)
4. Click **Run**

### Export Results

**Export Plot**:
1. In results viewer, right-click plot
2. **Save as Image** → Choose PNG/PDF/SVG
3. Save for publication

**Export Data**:
1. Click **Export** button in results
2. Choose format (CSV, Excel)
3. Save scores/loadings/statistics

---

## Troubleshooting Quick Fixes

**Issue**: Can't see imported objects
- **Fix**: Click on dataset in left tree to refresh

**Issue**: Landmarks not placing
- **Fix**: Make sure you're in edit mode (double-click object)

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

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**For Modan2 Version**: 0.1.4+
