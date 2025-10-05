# Missing Landmark Implementation Phase 3-5 Detailed Plan

## Date: 2025-09-19
## Version: 0.1.5-alpha.1
## Author: Jikhan Jung / Claude

## Executive Summary
This document outlines the detailed implementation plan for Phases 3-5 of missing landmark support in Modan2. These phases focus on advanced imputation methods, statistical analysis integration, and UI/UX improvements.

---

## Phase 3: Advanced Imputation Methods

### 3.1 TPS (Thin-Plate Spline) Based Prediction

#### Rationale
- Preserves geometric relationships between landmarks
- Provides smooth, biologically plausible interpolations
- Industry standard in morphometrics (used by geomorph, Morpho)

#### Implementation Details

##### 3.1.1 Core TPS Functions (MdStatistics.py)
```python
def compute_tps_coefficients(source_landmarks, target_landmarks):
    """
    Compute TPS warping coefficients

    Args:
        source_landmarks: Reference landmarks (with no missing)
        target_landmarks: Target landmarks (with no missing)

    Returns:
        Dictionary containing:
        - affine_matrix: Affine transformation component
        - w_matrix: Non-affine warping weights
        - control_points: Source landmarks used as control points
    """
    # Implementation based on Bookstein (1989) formulation
    # 1. Build TPS kernel matrix K
    # 2. Solve linear system for coefficients
    # 3. Return warping parameters

def apply_tps_transform(coefficients, query_points):
    """
    Apply TPS transformation to estimate missing landmarks

    Args:
        coefficients: TPS coefficients from compute_tps_coefficients
        query_points: Positions where we need predictions

    Returns:
        Predicted landmark positions
    """
    # Apply affine + non-affine components
    # Return estimated positions
```

##### 3.1.2 Integration with MdDatasetOps (MdModel.py)
```python
def estimate_missing_landmarks_tps(self, obj_index, reference_indices=None):
    """
    Estimate missing landmarks using TPS from similar complete specimens

    Args:
        obj_index: Index of object with missing landmarks
        reference_indices: Indices of complete reference objects
                          (if None, use all complete objects)

    Algorithm:
    1. Find k most similar complete specimens (using Procrustes distance)
    2. For each reference:
       - Compute TPS mapping from reference to target (using valid landmarks)
       - Apply TPS to predict missing landmarks
    3. Average predictions (weighted by similarity)
    """

def find_similar_complete_specimens(self, obj_index, k=5):
    """
    Find k most similar specimens without missing landmarks

    Uses:
    - Procrustes distance on shared landmarks
    - Optional: Mahalanobis distance in shape space
    """
```

##### 3.1.3 Testing Requirements
- Test with synthetic missing patterns (10%, 20%, 30% missing)
- Compare TPS vs mean imputation accuracy
- Validate on known complete datasets with artificial missing
- Performance benchmarks (< 100ms per specimen)

#### Deliverables
- [ ] TPS coefficient computation function
- [ ] TPS application function
- [ ] Integration with existing imputation pipeline
- [ ] Unit tests for TPS functions
- [ ] Performance optimization for large datasets

### 3.2 Regression-Based Estimation

#### Rationale
- Utilizes statistical relationships between landmarks
- Can incorporate covariates (size, age, sex)
- Provides uncertainty estimates

#### Implementation Details

##### 3.2.1 Multiple Regression Approach (MdStatistics.py)
```python
def build_landmark_regression_model(self, complete_data):
    """
    Build regression models for each landmark using complete data

    Returns:
        Dictionary of sklearn regression models (one per landmark)

    Models to implement:
    - Linear regression (baseline)
    - PLS regression (for high correlation)
    - Random Forest (for non-linear relationships)
    """

def predict_missing_regression(self, obj_with_missing, regression_models):
    """
    Predict missing landmarks using regression

    Features:
    - Use all available landmarks as predictors
    - Apply appropriate model based on missing pattern
    - Return predictions with confidence intervals
    """
```

##### 3.2.2 PLS (Partial Least Squares) Implementation
```python
def pls_imputation(self, dataset_matrix, n_components=None):
    """
    Use PLS to impute missing landmarks

    Advantages:
    - Handles multicollinearity well
    - Works with high-dimensional data
    - Captures maximal covariance
    """
```

##### 3.2.3 Model Selection and Validation
```python
def select_best_imputation_method(self, obj_index):
    """
    Automatically select best method based on:
    - Missing pattern (random vs systematic)
    - Missing percentage
    - Available reference specimens
    - Cross-validation performance

    Returns:
        'mean' | 'tps' | 'regression' | 'hybrid'
    """
```

#### Deliverables
- [ ] Multiple regression implementation
- [ ] PLS regression implementation
- [ ] Model selection algorithm
- [ ] Cross-validation framework
- [ ] Confidence interval computation

### 3.3 Hybrid and Advanced Methods

#### 3.3.1 Iterative Refinement
```python
def iterative_imputation_em(self, max_iter=10, tol=1e-5):
    """
    EM algorithm for missing landmark imputation

    E-step: Estimate missing values
    M-step: Update parameters (mean, covariance)
    Iterate until convergence
    """
```

#### 3.3.2 Multiple Imputation
```python
def multiple_imputation(self, n_imputations=5):
    """
    Generate multiple plausible imputations

    Benefits:
    - Captures uncertainty in missing values
    - Enables proper statistical inference
    - Required for valid standard errors
    """
```

---

## Phase 4: Statistical Analysis Integration

### 4.1 PCA with Missing Data

#### 4.1.1 Modified PCA Implementation (MdStatistics.py)
```python
def perform_pca_with_missing(landmark_data, method='complete'):
    """
    PCA with missing landmark handling

    Args:
        landmark_data: Dataset with possible None values
        method: 'complete' | 'available' | 'imputed' | 'probabilistic'

    Methods:
    - complete: Use only complete cases (current)
    - available: Pairwise deletion for covariance
    - imputed: Single imputation then standard PCA
    - probabilistic: PPCA (Probabilistic PCA)

    Returns:
        Modified PCA results with:
        - PC scores (with uncertainty if applicable)
        - Variance explained (adjusted)
        - Missing data diagnostics
    """
```

#### 4.1.2 PPCA Implementation
```python
def probabilistic_pca(self, data_with_missing, n_components):
    """
    Probabilistic PCA for missing data

    Based on:
    - Tipping & Bishop (1999)
    - EM algorithm for parameter estimation
    - Provides uncertainty in PC scores
    """
```

#### 4.1.3 Variance Adjustment
```python
def adjust_variance_for_imputation(self, pca_result, imputation_method):
    """
    Adjust variance explained to account for imputation uncertainty

    Methods:
    - Bootstrap variance estimation
    - Analytical corrections (Little & Rubin)
    """
```

### 4.2 CVA with Missing Data

#### 4.2.1 Modified CVA Implementation
```python
def perform_cva_with_missing(groups, landmarks, method='imputed'):
    """
    CVA with missing landmark handling

    Approaches:
    1. Complete case CVA (restrictive)
    2. Impute then CVA (current plan)
    3. Modified CVA with weighted observations

    Returns:
        CVA results with missing data diagnostics
    """
```

#### 4.2.2 Group-wise Imputation
```python
def group_aware_imputation(self, groups, landmarks):
    """
    Impute missing values considering group structure

    Benefits:
    - Preserves between-group differences
    - More accurate for structured populations
    """
```

### 4.3 MANOVA Considerations

#### 4.3.1 Test Statistic Adjustment
```python
def manova_with_missing(self, groups, landmarks):
    """
    MANOVA with missing data

    Adjustments:
    - Degrees of freedom correction
    - Test statistic modification
    - Power analysis with missing data
    """
```

#### 4.3.2 Assumptions Checking
```python
def check_manova_assumptions_missing(self, data):
    """
    Verify MANOVA assumptions with missing data:
    - Multivariate normality (on available data)
    - Homogeneity of covariance (adjusted tests)
    - Missing data mechanism (MCAR test)
    """
```

### 4.4 Missing Data Diagnostics

#### 4.4.1 Missing Pattern Analysis
```python
def analyze_missing_pattern(self, dataset):
    """
    Comprehensive missing data diagnostics

    Returns:
        - Missing percentage per landmark
        - Missing pattern matrix (visual)
        - Little's MCAR test result
        - Recommended imputation strategy
    """
```

#### 4.4.2 Impact Assessment
```python
def assess_missing_impact(self, complete_analysis, imputed_analysis):
    """
    Compare results with/without missing data

    Metrics:
    - Change in PC loadings
    - Shift in group centroids
    - Variance explained difference
    - Statistical power loss
    """
```

---

## Phase 5: UI/UX Integration

### 5.1 Visual Indicators for Missing Landmarks

#### 5.1.1 2D Viewer Enhancements (ModanComponents.py)
```python
class ObjectViewer2D:
    def paintEvent(self, event):
        """
        Modified to show missing landmarks distinctly

        Visual indicators:
        - Dashed circle for imputed landmarks
        - Red 'X' for missing landmarks
        - Transparency gradient for uncertainty
        - Tooltip showing imputation method
        """

    def draw_missing_landmark_indicator(self, painter, x, y, uncertainty=None):
        """
        Draw special indicator for missing/imputed landmark

        Options:
        - Style: 'x', 'circle', 'question'
        - Color: Based on imputation confidence
        - Size: Proportional to uncertainty
        """
```

#### 5.1.2 3D Viewer Enhancements
```python
class ObjectViewer3D:
    def show_landmarks_with_missing(self):
        """
        3D rendering with missing landmark indicators

        Features:
        - Semi-transparent spheres for imputed
        - Different material for missing
        - Confidence visualization (size/opacity)
        """
```

#### 5.1.3 Landmark Table Improvements
```python
def setup_landmark_table_missing(self):
    """
    Enhanced table for missing landmark display

    Features:
    - Color coding (red=missing, yellow=imputed)
    - Confidence column (if imputed)
    - Right-click context menu:
      - Mark as missing
      - Impute value
      - Show imputation details
    """
```

### 5.2 Analysis Dialog Enhancements

#### 5.2.1 NewAnalysisDialog Modifications (ModanDialogs.py)
```python
class NewAnalysisDialog:
    def __init__(self):
        # Add missing data handling section
        self.add_missing_data_options()

    def add_missing_data_options(self):
        """
        Add UI controls for missing data handling

        Components:
        - Imputation method dropdown:
          * Mean substitution
          * TPS estimation
          * Regression
          * Multiple imputation
        - Missing threshold spinbox (max % allowed)
        - Show missing statistics button
        - Sensitivity analysis checkbox
        """

    def show_missing_statistics(self):
        """
        Display missing data summary dialog

        Shows:
        - Table of objects with missing data
        - Heatmap of missing patterns
        - Recommended methods
        - Impact preview
        """
```

#### 5.2.2 Progress Feedback
```python
def show_imputation_progress(self):
    """
    Progress dialog for imputation process

    Shows:
        - Current specimen being processed
        - Method being used
        - Convergence plot (for iterative methods)
        - Estimated time remaining
    """
```

### 5.3 Results and Reporting

#### 5.3.1 AnalysisResultDialog Enhancements
```python
class AnalysisResultDialog:
    def add_missing_data_tab(self):
        """
        New tab for missing data diagnostics

        Contents:
        - Imputation summary table
        - Before/after comparison plots
        - Uncertainty visualization
        - Sensitivity analysis results
        """

    def export_missing_report(self):
        """
        Generate comprehensive missing data report

        Includes:
        - Methods used
        - Validation metrics
        - Recommendations
        - Citations for methods
        """
```

#### 5.3.2 Visualization Improvements
```python
def plot_imputation_uncertainty(self):
    """
    Visualize uncertainty in imputed values

    Plots:
    - Confidence ellipses
    - Bootstrap distributions
    - Comparison with complete data (if available)
    """
```

### 5.4 Dataset Management

#### 5.4.1 Import/Export Enhancements
```python
class ImportDatasetDialog:
    def detect_missing_on_import(self):
        """
        Automatically detect missing landmarks during import

        Detections:
        - Common missing indicators (NA, NaN, -, empty)
        - Outlier detection for probable errors
        - Pattern recognition for systematic missing
        """

    def preview_missing_handling(self):
        """
        Show preview of how missing will be handled

        Options:
        - Interactive landmark assignment
        - Batch missing marking
        - Import with warnings
        """
```

#### 5.4.2 Export Options
```python
class ExportDatasetDialog:
    def add_missing_export_options(self):
        """
        Options for exporting datasets with missing

        Formats:
        - Include imputed values
        - Export only original values
        - Include confidence intervals
        - Multiple imputation sets
        """
```

---

## Implementation Timeline

### Phase 3: Advanced Imputation Methods (2-3 weeks)
- Week 1: TPS implementation and testing
- Week 2: Regression methods and model selection
- Week 3: Integration and optimization

### Phase 4: Statistical Analysis Integration (2 weeks)
- Week 1: PCA and CVA modifications
- Week 2: MANOVA adjustments and diagnostics

### Phase 5: UI/UX Integration (2 weeks)
- Week 1: Visual indicators and viewer enhancements
- Week 2: Dialog modifications and reporting

### Total Estimated Time: 6-7 weeks

---

## Testing Strategy

### Unit Tests
```python
# tests/test_missing_landmark_advanced.py
class TestTPSImputation:
    def test_tps_coefficient_computation(self)
    def test_tps_prediction_accuracy(self)
    def test_tps_with_noise(self)

class TestRegressionImputation:
    def test_linear_regression_imputation(self)
    def test_pls_imputation(self)
    def test_model_selection(self)

class TestStatisticalAnalysisMissing:
    def test_pca_with_missing(self)
    def test_cva_with_missing(self)
    def test_manova_assumptions(self)
```

### Integration Tests
```python
# tests/test_missing_landmark_integration.py
class TestMissingLandmarkWorkflow:
    def test_complete_analysis_workflow(self)
    def test_ui_interaction_flow(self)
    def test_import_export_cycle(self)
```

### Performance Tests
```python
# tests/test_missing_landmark_performance.py
class TestImputationPerformance:
    def test_tps_speed_scaling(self)
    def test_memory_usage(self)
    def test_convergence_speed(self)
```

### Validation Tests
Compare against:
- R geomorph package results
- PAST software outputs
- Published dataset results

---

## Risk Mitigation

### Technical Risks
1. **Performance degradation**
   - Mitigation: Implement caching, parallel processing
   - Fallback: Limit advanced methods to small datasets

2. **Numerical instability**
   - Mitigation: Use robust linear algebra libraries
   - Fallback: Provide warnings and use simpler methods

3. **Memory issues with large datasets**
   - Mitigation: Implement chunked processing
   - Fallback: Out-of-core computation options

### User Experience Risks
1. **Complexity overwhelming users**
   - Mitigation: Provide sensible defaults
   - Solution: "Simple" and "Advanced" mode toggle

2. **Misinterpretation of results**
   - Mitigation: Clear documentation and warnings
   - Solution: Interactive tutorials

3. **Backward compatibility**
   - Mitigation: Version dataset files
   - Solution: Migration utilities

---

## Dependencies

### Required Libraries
```python
# requirements.txt additions
scikit-learn>=1.0.0  # For regression methods
scipy>=1.7.0         # For TPS and advanced stats
statsmodels>=0.13.0  # For statistical tests
matplotlib>=3.5.0    # For diagnostic plots
```

### Optional Libraries
```python
# For advanced features
pymc3  # Bayesian imputation
mice   # Multiple imputation
```

---

## Documentation Requirements

### User Documentation
1. Missing Landmark Handling Guide
2. Method Selection Flowchart
3. Interpretation Guidelines
4. FAQ and Troubleshooting

### Developer Documentation
1. API Reference for new functions
2. Architecture diagrams
3. Testing guidelines
4. Performance optimization guide

### Academic Documentation
1. Mathematical formulations
2. Validation studies
3. Comparison with other software
4. Citation guidelines

---

## Success Metrics

### Functional Metrics
- All tests passing (>95% coverage)
- Support for 30%+ missing data
- <2x slowdown vs complete data

### User Metrics
- Successful analysis with real damaged specimens
- Positive feedback from beta testers
- Adoption by research groups

### Scientific Metrics
- Results comparable to published studies
- Validation against known datasets
- Peer review acceptance

---

## Future Enhancements (Beyond Phase 5)

1. **Machine Learning Methods**
   - Deep learning imputation
   - Generative models for shape completion

2. **Bayesian Framework**
   - Full Bayesian treatment of missing data
   - Hierarchical models

3. **Real-time Imputation**
   - Live preview during digitization
   - Guided landmark placement

4. **Cloud Integration**
   - Server-side imputation for large datasets
   - Shared imputation models

---

## References

1. Bookstein, F. L. (1989). Principal warps: Thin-plate splines and the decomposition of deformations. IEEE TPAMI.

2. Gunz, P., Mitteroecker, P., et al. (2009). Principles for the virtual reconstruction of hominin crania. J. Human Evolution.

3. Little, R. J., & Rubin, D. B. (2019). Statistical analysis with missing data (3rd ed.). Wiley.

4. Arbour, J. H., & Brown, C. M. (2014). Incomplete specimens in geometric morphometric analyses. Methods in Ecology and Evolution.

5. Tipping, M. E., & Bishop, C. M. (1999). Probabilistic principal component analysis. J. Royal Statistical Society.

6. Adams, D. C., Collyer, M. L., & Kaliontzopoulou, A. (2020). Geomorph: Software for geometric morphometric analyses.

---

## Appendix: Code Examples

### A. TPS Implementation Example
```python
import numpy as np
from scipy.spatial.distance import cdist

def tps_kernel(r):
    """TPS kernel function: r^2 * log(r) for r > 0"""
    return np.where(r > 0, r**2 * np.log(r + 1e-20), 0)

def compute_tps_coefficients(source, target):
    """
    Compute TPS coefficients for warping source to target

    Args:
        source: (n, d) array of source landmarks
        target: (n, d) array of target landmarks

    Returns:
        dict with affine and non-affine coefficients
    """
    n, d = source.shape

    # Build system matrix
    K = tps_kernel(cdist(source, source))
    P = np.hstack([np.ones((n, 1)), source])

    # Build block matrix
    L = np.zeros((n + d + 1, n + d + 1))
    L[:n, :n] = K
    L[:n, n:] = P
    L[n:, :n] = P.T

    # Solve for coefficients
    Y = np.vstack([target, np.zeros((d + 1, d))])
    coefficients = np.linalg.solve(L, Y)

    return {
        'weights': coefficients[:n],
        'affine': coefficients[n:],
        'source': source
    }

def apply_tps_transform(coeffs, points):
    """Apply TPS transform to new points"""
    K = tps_kernel(cdist(points, coeffs['source']))
    P = np.hstack([np.ones((len(points), 1)), points])

    # Apply transformation
    f = K @ coeffs['weights'] + P @ coeffs['affine']
    return f
```

### B. Multiple Imputation Example
```python
def multiple_imputation_analysis(dataset, n_imputations=5):
    """
    Perform analysis with multiple imputation

    Following Rubin's rules for combining results
    """
    results = []

    for i in range(n_imputations):
        # Generate imputation
        imputed_data = impute_missing_landmarks(
            dataset,
            method='tps',
            random_seed=i
        )

        # Perform analysis
        pca_result = perform_pca(imputed_data)
        results.append(pca_result)

    # Combine results using Rubin's rules
    combined_result = combine_mi_results(results)

    return combined_result

def combine_mi_results(results):
    """
    Combine multiple imputation results

    Rubin's rules:
    - Point estimate: average across imputations
    - Variance: within + between imputation variance
    """
    # Average point estimates
    point_estimate = np.mean([r.scores for r in results], axis=0)

    # Within-imputation variance
    within_var = np.mean([r.variance for r in results], axis=0)

    # Between-imputation variance
    between_var = np.var([r.scores for r in results], axis=0)

    # Total variance (Rubin's formula)
    total_var = within_var + (1 + 1/len(results)) * between_var

    return {
        'scores': point_estimate,
        'variance': total_var,
        'n_imputations': len(results)
    }
```

---

## Contact and Support

For questions or clarifications about this implementation plan:
- Technical Lead: Jikhan Jung
- Documentation: See project wiki
- Issues: GitHub issue tracker

Last Updated: 2025-09-19
Next Review: 2025-10-01
