# Object Dialog Missing Landmark Estimation Review

## Date: 2025-09-19
## Version: 0.1.5-alpha.1
## Author: Jikhan Jung / Claude

## Executive Summary

This document reviews and recommends the approach for displaying estimated positions of missing landmarks in the Object Dialog. The goal is to provide **quick, reasonable estimates** that help users understand the approximate position of missing landmarks without requiring intensive computation.

---

## 1. Context and Requirements

### 1.1 Object Dialog Purpose
- **Primary function**: Quick viewing and basic editing of individual objects
- **User expectations**: Fast response, intuitive interface
- **Accuracy needs**: Approximate positions sufficient (not precision editing)

### 1.2 Current Missing Landmark Support
- ✅ Backend: Procrustes with iterative imputation implemented
- ✅ UI: "Add Missing" button in Object Dialog
- ✅ Display: Missing landmarks shown as "MISSING" in red
- ❌ **Gap**: No visual estimation in Object Dialog

### 1.3 Performance Constraints
```
Acceptable response times:
- Object loading: < 100ms
- Tab switching: < 50ms
- Landmark update: < 200ms
- Dataset switching: < 500ms
```

---

## 2. Estimation Method Comparison

### 2.1 Methods Evaluated

| Method | Accuracy | Speed | Implementation | Memory | User Experience |
|--------|----------|-------|----------------|--------|-----------------|
| **No estimation** | N/A | Instant | Trivial | None | ❌ Confusing |
| **Raw mean** | ⭐ | ⚡⚡⚡ | Easy | Low | ❌ Very inaccurate |
| **Aligned mean** | ⭐⭐⭐ | ⚡⚡ | Moderate | Medium | ✅ Good balance |
| **Nearest neighbor** | ⭐⭐⭐ | ⚡⚡ | Moderate | Medium | ✅ Intuitive |
| **Local interpolation** | ⭐⭐ | ⚡⚡⚡ | Easy | Low | ⚠️ Limited use |
| **TPS (full)** | ⭐⭐⭐⭐⭐ | ⚡ | Complex | High | ❌ Overkill |
| **Regression** | ⭐⭐⭐⭐ | ⚡ | Complex | High | ❌ Overkill |

### 2.2 Critical Issue: Scale/Position Alignment

#### ❌ Problem with Raw Mean
```python
# Example: Same shape, different scales
small_triangle = [[1, 1], [2, 1], [1.5, 2]]      # Small
large_triangle = [[10, 10], [20, 10], [15, 20]]  # Large (10x)

# Raw mean → Completely wrong position!
raw_mean = [[5.5, 5.5], [11, 5.5], [8.25, 11]]  # Meaningless
```

#### ✅ Solution: Aligned Mean
Must account for:
- **Translation**: Different positions in space
- **Scale**: Different sizes
- **Rotation**: Different orientations

---

## 3. Recommended Approach

### 3.1 Primary Method: **Procrustes-Aligned Mean**

#### Rationale
1. **Accuracy**: Accounts for size/position/rotation differences
2. **Speed**: One-time computation per dataset
3. **Simplicity**: No complex algorithms needed
4. **Reliability**: Works for all missing patterns

#### Implementation Strategy
```python
class ObjectDialog:
    def __init__(self):
        # Cache computed once per dataset
        self._aligned_mean_cache = None
        self._cache_timestamp = None

    def compute_aligned_mean(self):
        """Compute Procrustes-aligned mean shape (once per dataset)"""
        if self._aligned_mean_cache is None:
            # 1. Collect complete objects
            complete = [obj for obj in dataset if not has_missing(obj)]

            # 2. Procrustes alignment (existing function)
            aligned = procrustes_superimposition(complete)

            # 3. Compute mean
            self._aligned_mean_cache = compute_mean(aligned)
            self._cache_timestamp = time.time()

        return self._aligned_mean_cache

    def estimate_missing(self, current_object):
        """Estimate missing landmarks for current object"""
        mean_shape = self.compute_aligned_mean()

        # Transform mean to match current object
        transform = compute_transform(
            mean_shape[valid_indices],
            current_object[valid_indices]
        )

        # Apply to missing landmarks
        return apply_transform(mean_shape[missing_indices], transform)
```

### 3.2 Simplified Alternative: **Scale+Position Alignment Only**

For faster performance with acceptable accuracy:

```python
def estimate_missing_simple(self, current_object):
    """Simpler estimation: scale and position only"""
    mean_shape = self.get_cached_mean()

    # 1. Compute centroids (valid landmarks only)
    current_centroid = compute_centroid(current_object[valid])
    mean_centroid = compute_centroid(mean_shape[valid])

    # 2. Compute scales
    current_scale = compute_centroid_size(current_object[valid])
    mean_scale = compute_centroid_size(mean_shape[valid])

    # 3. Transform missing landmarks
    scale_factor = current_scale / mean_scale
    translation = current_centroid - mean_centroid

    estimated = []
    for idx in missing_indices:
        point = mean_shape[idx]
        # Scale around mean centroid, then translate
        estimated_point = (point - mean_centroid) * scale_factor + current_centroid
        estimated.append(estimated_point)

    return estimated
```

---

## 4. UI/UX Design

### 4.1 Visual Representation

#### In 2D Viewer
```python
def paint_missing_landmarks(painter):
    for idx, landmark in enumerate(landmarks):
        if landmark.is_missing:
            if show_estimation:
                # Estimated position
                painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(estimated_pos, 3, 3)

                # Confidence indicator
                painter.setFont(QFont("Arial", 8))
                painter.setPen(Qt.gray)
                painter.drawText(estimated_pos + QPoint(5, -5), "?")
            else:
                # Missing indicator only
                painter.setPen(QPen(Qt.red, 2))
                painter.drawLine(pos - 3, pos + 3)  # X mark
```

#### In Landmark Table
```
| # | X        | Y        | Status   |
|---|----------|----------|----------|
| 1 | 10.52    | 20.13    | ✓        |
| 2 | ~15.20   | ~25.30   | ? (est.) |  <- Italic, gray
| 3 | MISSING  | MISSING  | ✗        |  <- Red
```

### 4.2 User Controls

```python
class ObjectDialog:
    def setup_missing_controls(self):
        # Group box for missing landmark options
        group = QGroupBox("Missing Landmarks")

        # Estimation toggle
        self.show_estimation = QCheckBox("Show estimated positions")
        self.show_estimation.setChecked(True)

        # Confidence indicator
        self.confidence_label = QLabel()
        self.update_confidence_display()

        # Accept estimation button
        self.accept_button = QPushButton("Accept Estimates")
        self.accept_button.clicked.connect(self.accept_estimations)

        layout.addWidget(self.show_estimation)
        layout.addWidget(self.confidence_label)
        layout.addWidget(self.accept_button)
```

---

## 5. Implementation Plan

### 5.1 Phase 1: Core Estimation (2-3 hours)
1. Add `_aligned_mean_cache` to ObjectDialog
2. Implement `compute_aligned_mean()` method
3. Implement `estimate_missing()` method
4. Add caching logic

### 5.2 Phase 2: UI Integration (2-3 hours)
1. Add estimation toggle checkbox
2. Modify landmark table display
3. Update 2D viewer painting
4. Add confidence indicators

### 5.3 Phase 3: Optimization (1-2 hours)
1. Implement cache invalidation
2. Add progress feedback for initial computation
3. Optimize transform calculations
4. Add error handling

---

## 6. Performance Optimization

### 6.1 Caching Strategy

```python
class EstimationCache:
    def __init__(self):
        self.mean_shape = None
        self.mean_timestamp = None
        self.transform_cache = {}  # Per-object transforms

    def get_estimation(self, object_id, valid_landmarks):
        # Check if mean needs recomputation
        if self.needs_recompute():
            self.compute_mean()

        # Check transform cache
        cache_key = hash(tuple(valid_landmarks))
        if cache_key not in self.transform_cache:
            self.transform_cache[cache_key] = compute_transform(...)

        return apply_transform(self.mean_shape, self.transform_cache[cache_key])

    def invalidate(self, reason='dataset_change'):
        if reason == 'dataset_change':
            self.mean_shape = None
            self.transform_cache.clear()
        elif reason == 'object_change':
            # Keep mean, clear transforms
            self.transform_cache.clear()
```

### 6.2 Progressive Loading

```python
def load_object_progressive(self, object):
    # Step 1: Show immediately with missing markers
    self.display_immediate(object)

    # Step 2: Quick estimation (if cached mean available)
    if self.has_cached_mean():
        self.display_with_estimation(object, quality='quick')

    # Step 3: Compute mean if needed (with progress)
    if not self.has_cached_mean():
        QTimer.singleShot(100, lambda: self.compute_mean_async())
```

---

## 7. Testing Requirements

### 7.1 Unit Tests
```python
def test_estimation_accuracy():
    """Test estimation accuracy with known data"""
    # Create dataset with artificial missing
    # Compare estimation vs actual
    # Assert error < threshold

def test_cache_performance():
    """Test caching improves performance"""
    # Time first estimation
    # Time second estimation (cached)
    # Assert cached < 10% of initial

def test_transform_correctness():
    """Test scale/rotation/translation transform"""
    # Apply known transform
    # Verify result matches expected
```

### 7.2 Integration Tests
- Load dataset with missing landmarks
- Switch between objects rapidly
- Verify estimations appear correctly
- Test cache invalidation on dataset change

### 7.3 User Acceptance Criteria
- [ ] Estimation appears within 200ms
- [ ] Visual indicators are clear
- [ ] Switching objects remains smooth
- [ ] Memory usage stays reasonable

---

## 8. Alternative Approaches (Not Recommended)

### 8.1 Why NOT Use TPS in Object Dialog

1. **Computational Cost**
   - TPS requires solving large linear systems
   - O(n³) complexity for n landmarks
   - 100+ ms for typical datasets

2. **Complexity**
   - Requires complete reference specimens
   - Needs similarity computation
   - Complex parameter tuning

3. **Marginal Benefit**
   - Object Dialog is for quick viewing
   - Precise positions not critical
   - Users won't edit estimated positions

### 8.2 Why NOT Use Regression

1. **Training Time**
   - Requires building models per landmark
   - Cross-validation needed
   - Slow initial computation

2. **Data Requirements**
   - Needs sufficient training data
   - Assumes linear relationships
   - May fail with sparse data

---

## 9. Decision Matrix

| Criterion | Weight | Aligned Mean | TPS | Regression |
|-----------|--------|--------------|-----|------------|
| Speed | 30% | 9/10 | 5/10 | 4/10 |
| Accuracy | 20% | 7/10 | 9/10 | 8/10 |
| Simplicity | 25% | 8/10 | 4/10 | 3/10 |
| Robustness | 25% | 9/10 | 7/10 | 6/10 |
| **Total** | 100% | **8.3/10** | 6.1/10 | 5.2/10 |

---

## 10. Conclusion and Recommendation

### Recommended Approach: **Procrustes-Aligned Mean with Caching**

**Rationale:**
1. **Sufficient accuracy** for Object Dialog purposes
2. **Fast performance** with proper caching
3. **Simple implementation** using existing Procrustes code
4. **Robust** across different datasets
5. **User-friendly** with immediate visual feedback

### Implementation Priority:
1. **High**: Basic aligned mean estimation
2. **Medium**: Visual indicators and controls
3. **Low**: Advanced caching optimizations

### Success Metrics:
- ✅ Estimation available < 200ms
- ✅ No noticeable lag when switching objects
- ✅ Memory usage < 50MB additional
- ✅ Estimation error < 10% of object size

---

## Appendix A: Code Examples

### A.1 Complete Implementation Example

```python
class ObjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.estimation_manager = EstimationManager()

    def set_dataset(self, dataset):
        """Called when dataset changes"""
        self.dataset = dataset
        self.estimation_manager.set_dataset(dataset)

    def set_object(self, object):
        """Called when displaying new object"""
        self.object = object
        self.show_object_with_estimation()

    def show_object_with_estimation(self):
        """Display object with estimated missing landmarks"""
        # Get estimation if missing landmarks exist
        if self.has_missing_landmarks():
            estimated = self.estimation_manager.estimate(self.object)
            self.display_landmarks(self.object, estimated)
        else:
            self.display_landmarks(self.object)

class EstimationManager:
    def __init__(self):
        self.dataset = None
        self.mean_shape_cache = None
        self.cache_time = 0

    def set_dataset(self, dataset):
        """Update dataset and invalidate cache"""
        if self.dataset != dataset:
            self.dataset = dataset
            self.mean_shape_cache = None

    def estimate(self, object):
        """Estimate missing landmarks"""
        # Ensure mean shape is computed
        if self.mean_shape_cache is None:
            self.compute_mean_shape()

        # Transform mean to match object
        return self.transform_mean_to_object(object)

    def compute_mean_shape(self):
        """Compute aligned mean shape from complete objects"""
        # Get complete objects
        complete = []
        for obj in self.dataset.object_list:
            if not self.has_missing(obj):
                complete.append(obj)

        if len(complete) >= 2:
            # Procrustes alignment
            aligned = procrustes_superimposition(complete)
            # Compute mean
            self.mean_shape_cache = compute_mean(aligned)
        elif len(complete) == 1:
            self.mean_shape_cache = complete[0]
        else:
            self.mean_shape_cache = None

    def transform_mean_to_object(self, object):
        """Transform mean shape to match current object"""
        if self.mean_shape_cache is None:
            return object.landmark_list

        # Get valid landmarks
        valid_indices = [i for i, lm in enumerate(object.landmark_list)
                        if lm[0] is not None]

        if len(valid_indices) < 3:
            return object.landmark_list

        # Compute transform
        transform = self.compute_similarity_transform(
            source=[self.mean_shape_cache[i] for i in valid_indices],
            target=[object.landmark_list[i] for i in valid_indices]
        )

        # Apply to missing
        result = copy.deepcopy(object.landmark_list)
        for i, lm in enumerate(result):
            if lm[0] is None:
                result[i] = self.apply_transform(
                    self.mean_shape_cache[i],
                    transform
                )

        return result
```

### A.2 Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.timings = defaultdict(list)

    def measure(self, operation):
        """Decorator to measure operation time"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                self.timings[operation].append(elapsed)

                # Log if too slow
                if elapsed > 0.2:
                    logger.warning(f"{operation} took {elapsed:.3f}s")

                return result
            return wrapper
        return decorator

    def report(self):
        """Generate performance report"""
        for op, times in self.timings.items():
            avg = sum(times) / len(times)
            max_time = max(times)
            print(f"{op}: avg={avg:.3f}s, max={max_time:.3f}s")
```

---

## Appendix B: User Interface Mockup

```
┌─────────────────────────────────────────────────┐
│ Object Dialog - Sample_Object_01                │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │              │  │ Landmarks               │ │
│  │   2D View    │  │ ┌───┬─────┬─────┬────┐ │ │
│  │              │  │ │ # │  X  │  Y  │ St │ │ │
│  │  ●     ●     │  │ ├───┼─────┼─────┼────┤ │ │
│  │      ◌       │  │ │ 1 │10.5 │20.1 │ ✓  │ │ │
│  │   ●     ?    │  │ │ 2 │~15.2│~25.3│ ?  │ │ │
│  │              │  │ │ 3 │23.1 │18.7 │ ✓  │ │ │
│  └──────────────┘  │ └───┴─────┴─────┴────┘ │ │
│                    │                         │ │
│  ┌──────────────────────────────────────────┐ │
│  │ Missing Landmarks                        │ │
│  │ ☑ Show estimated positions               │ │
│  │ Confidence: ●●●○○ (Moderate)            │ │
│  │ Method: Aligned mean                     │ │
│  │ [Accept Estimates] [Recompute]          │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  Status: 1 missing landmark, estimation ready  │
└─────────────────────────────────────────────────┘

Legend:
● = Actual landmark
◌ = Missing landmark (no estimation)
? = Estimated position
```

---

## Document History

- 2025-09-19: Initial review and recommendations
- Next review: After Phase 1 implementation

## Contact

For questions or clarifications:
- Technical Lead: Jikhan Jung
- Implementation: Object Dialog team