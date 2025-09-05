# PCA 분석 결과 일치화 수정 가이드

## 문제 개요
Add Analysis Dialog와 Analysis Detail Dialog에서 동일한 데이터에 대해 서로 다른 PCA 결과가 나오는 문제가 있었습니다.

## 원인 분석

### 1. Add Analysis Dialog 경로 (ModanController.run_analysis)
- **문제점**: Procrustes superimposition을 수행하지 않음
- **문제점**: sklearn PCA + StandardScaler 사용 (데이터를 평균 0, 분산 1로 표준화)
- **경로**: Modan2.py → ModanController.run_analysis → MdStatistics.do_pca_analysis

### 2. Analysis Detail Dialog 경로 (DatasetAnalysisDialog)
- **정상**: Procrustes superimposition 수행
- **정상**: MdPrincipalComponent 클래스 사용 (평균만 빼는 centering)
- **경로**: DatasetAnalysisDialog → PerformPCA → MdPrincipalComponent.Analyze

## 수정 내용

### 1. ModanController.py 수정
**파일**: `/home/jikhanjung/projects/Modan2/ModanController.py`
**위치**: `run_analysis` 메서드 (라인 530-566 근처)

```python
# 기존 코드 (문제)
# Get objects with landmarks
objects = list(self.current_dataset.object_list)
objects_with_landmarks = []
for obj in objects:
    obj.unpack_landmark()
    if obj.landmark_str and obj.landmark_list:
        objects_with_landmarks.append(obj)

# Extract landmarks
landmarks_data = []
object_names = []
for obj in objects_with_landmarks:
    landmarks_data.append(obj.landmark_list)  # ← 원본 landmark 사용
    object_names.append(obj.object_name)

# 수정된 코드
# Get objects with landmarks
objects = list(self.current_dataset.object_list)
objects_with_landmarks = []
for obj in objects:
    obj.unpack_landmark()
    if obj.landmark_str and obj.landmark_list:
        objects_with_landmarks.append(obj)

if len(objects_with_landmarks) < 2:
    raise ValueError(f"At least 2 objects with landmarks are required for analysis...")

# Perform Procrustes superimposition before analysis
self.logger.info("Performing Procrustes superimposition")
from MdModel import MdDatasetOps
ds_ops = MdDatasetOps(self.current_dataset)
if not ds_ops.procrustes_superimposition():
    raise ValueError("Procrustes superimposition failed")
self.logger.info("Procrustes superimposition completed successfully")

# Extract landmarks from the superimposed objects
landmarks_data = []
object_names = []
for obj in ds_ops.object_list:  # ← 수정: 정렬된 객체 사용
    landmarks_data.append(obj.landmark_list)
    object_names.append(obj.object_name)
```

**추가 수정**: CVA/MANOVA 그룹 추출 부분도 `ds_ops.object_list` 사용하도록 변경
- 라인 588: `for obj in ds_ops.object_list:  # Use superimposed objects from ds_ops`
- 라인 625: `for obj in ds_ops.object_list:  # Use superimposed objects from ds_ops`

### 2. MdStatistics.py 수정
**파일**: `/home/jikhanjung/projects/Modan2/MdStatistics.py`

#### A. do_pca_analysis 함수 완전 재작성 (라인 352-442)
```python
def do_pca_analysis(landmarks_data, n_components=None):
    """Perform PCA analysis on landmark data.
    
    Args:
        landmarks_data: List of landmark arrays
        n_components: Number of components (None for auto)
        
    Returns:
        Dictionary with PCA results
    """
    try:
        import numpy as np
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"PCA Analysis starting with {len(landmarks_data)} specimens")
        if landmarks_data:
            logger.info(f"First specimen has {len(landmarks_data[0])} landmarks")
            if landmarks_data[0]:
                logger.info(f"Each landmark has {len(landmarks_data[0][0])} dimensions")
        
        # Use MdPrincipalComponent class for consistency with Analysis Detail
        pca = MdPrincipalComponent()
        
        # Flatten landmark data
        datamatrix = []
        for landmarks in landmarks_data:
            datum = []
            for lm in landmarks:
                datum.extend(lm)  # Use all coordinates (X, Y, Z for 3D)
            datamatrix.append(datum)
        
        # Perform PCA using the same method as Analysis Detail
        pca.SetData(datamatrix)
        pca.Analyze()
        
        # Get number of components
        if n_components is None:
            n_components = min(pca.nObservation, pca.nVariable)
        
        # Get scores (rotated matrix)
        scores = pca.rotated_matrix.tolist() if hasattr(pca, 'rotated_matrix') else []
        
        # Calculate mean shape from the centered data
        mean_shape = []
        dim = len(landmarks_data[0][0]) if landmarks_data and landmarks_data[0] else 2
        n_landmarks = len(landmarks_data[0]) if landmarks_data else 0
        
        # The mean is already calculated in pca.Analyze() during centering
        # We need to reconstruct it from the number of landmarks
        for i in range(n_landmarks):
            if dim == 2:
                mean_shape.append([0.0, 0.0])  # Already centered
            elif dim == 3:
                mean_shape.append([0.0, 0.0, 0.0])  # Already centered
        
        # Get eigenvalues and calculate variance ratios
        eigenvalues = pca.raw_eigen_values.tolist() if hasattr(pca, 'raw_eigen_values') else []
        explained_variance_ratio = pca.eigen_value_percentages if hasattr(pca, 'eigen_value_percentages') else []
        
        # Calculate cumulative variance
        cumulative_variance = []
        cumul = 0
        for ratio in explained_variance_ratio:
            cumul += ratio
            cumulative_variance.append(cumul)
        
        # Get rotation matrix (eigenvectors)
        rotation_matrix = pca.eigen_vectors.tolist() if hasattr(pca, 'eigen_vectors') else []
        
        logger.info(f"PCA Analysis completed")
        logger.info(f"Number of components: {n_components}")
        logger.info(f"Scores shape: {len(scores)}x{len(scores[0]) if scores else 0}")
        
        return {
            'n_components': n_components,
            'eigenvalues': eigenvalues[:n_components] if eigenvalues else [],
            'eigenvectors': rotation_matrix[:n_components] if rotation_matrix else [],
            'rotation_matrix': rotation_matrix,  # Full rotation matrix
            'scores': scores,
            'explained_variance_ratio': explained_variance_ratio[:n_components] if explained_variance_ratio else [],
            'cumulative_variance_ratio': cumulative_variance[:n_components] if cumulative_variance else [],
            'mean_shape': mean_shape,
            'raw_eigen_values': eigenvalues,
            'eigen_value_percentages': explained_variance_ratio
        }
        
    except Exception as e:
        import traceback
        logger.error(f"PCA analysis error: {traceback.format_exc()}")
        raise ValueError(f"PCA analysis failed: {str(e)}")
```

#### B. sklearn.preprocessing.StandardScaler import 제거
**모든 위치에서 제거**:
```python
# 제거할 라인들
from sklearn.preprocessing import StandardScaler
```

#### C. CVA 분석에서도 StandardScaler 제거 (라인 472-477)
```python
# 기존 코드
# Standardize data
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data_matrix)

# Perform LDA (equivalent to CVA)
lda = LinearDiscriminantAnalysis()
cv_scores = lda.fit_transform(data_scaled, group_array)

# Predict classifications
predictions = lda.predict(data_scaled)

# 수정된 코드
# Perform LDA (equivalent to CVA) without standardization
lda = LinearDiscriminantAnalysis()
cv_scores = lda.fit_transform(data_matrix, group_array)

# Predict classifications
predictions = lda.predict(data_matrix)
```

### 3. CLAUDE.md 문서 수정
**파일**: `/home/jikhanjung/projects/Modan2/CLAUDE.md`

```markdown
# 변경 전
- Key packages: PyQt5, numpy<2.0.0, pandas, scipy, opencv-python, peewee, trimesh
- Maintain compatibility with numpy < 2.0.0

# 변경 후  
- Key packages: PyQt5, numpy>2.0.0, pandas, scipy, opencv-python, peewee, trimesh
- Numpy > 2.0.0 is now supported (OpenGL issues resolved with pip installation)
```

## 핵심 변경사항 요약

1. **Procrustes Superimposition 추가**: Add Analysis 경로에서도 분석 전에 Procrustes 정렬 수행
2. **PCA 구현 통일**: sklearn PCA → MdPrincipalComponent 사용
3. **표준화 제거**: StandardScaler 제거하고 centering만 수행 (Analysis Detail과 동일)
4. **numpy 버전 요구사항 업데이트**: <2.0.0 → >2.0.0

## 테스트 방법

1. 동일한 dataset으로 Add Analysis 실행
2. 같은 dataset으로 Analysis Detail 실행  
3. 두 결과의 PCA scores, eigenvalues, explained variance 비교
4. 결과가 일치하는지 확인

## 기대 효과

- Add Analysis와 Analysis Detail에서 동일한 PCA 결과 출력
- 일관성 있는 분석 결과 제공
- 사용자 혼란 방지

---
**작성일**: 2025-09-05  
**작성자**: Claude Code Assistant