# PCA Scatterplot에 Variation Explained 표시 기능 구현

## 날짜
2025-09-18

## 작업자
Jikhan Jung

## 배경
- PCA(Principal Component Analysis) 결과를 시각화할 때, 각 PC(Principal Component) 축이 설명하는 분산의 비율을 함께 표시하면 데이터 해석에 유용함
- 기존에는 PC1, PC2 등의 축 이름만 표시되었으나, 각 축이 전체 분산의 몇 %를 설명하는지 직관적으로 알 수 없었음
- Data Exploration Dialog의 scatterplot에서 PC 축 라벨에 분산 설명력(variation explained)을 백분율로 표시하는 기능 추가 요구

## 구현 개요

### 1. 데이터 구조
- **저장 위치**: `MdAnalysis.pca_eigenvalues_json` 필드 (데이터베이스)
- **데이터 형식**: JSON 배열 `[[eigenvalue1, percentage1], [eigenvalue2, percentage2], ...]`
- **생성 시점**: PCA 분석 실행 시 `ModanController._run_pca()` 메서드에서 계산 및 저장

### 2. UI 컴포넌트 추가 (`ModanDialogs.py`)

#### 체크박스 추가 (Line 2128-2138)
```python
self.cbxShowVariance = QCheckBox()
self.cbxShowVariance.setText(self.tr("Show var. explained"))
self.cbxShowVariance.setChecked(False)  # 기본값: 비활성화
self.cbxShowVariance.toggled.connect(self.update_chart)
```
- Chart Basics 그룹박스 내에 "Show var. explained" 체크박스 추가
- 체크 상태 변경 시 `update_chart()` 메서드 호출하여 차트 즉시 업데이트

### 3. 데이터 로드 로직 (`ModanDialogs.py`)

#### PCA 결과 로드 시 eigenvalues 처리 (Line 3442-3451)
```python
if self.analysis_method == 'PCA':
    self.analysis_result_list = json.loads(self.analysis.pca_analysis_result_json)
    # Load eigenvalues for displaying variance explained
    if self.analysis.pca_eigenvalues_json:
        try:
            eigenvalues_data = json.loads(self.analysis.pca_eigenvalues_json)
            # eigenvalues_data is a list of [eigenvalue, percentage] pairs
            self.eigen_value_percentages = [item[1] for item in eigenvalues_data] if eigenvalues_data else []
        except:
            self.eigen_value_percentages = []
    else:
        self.eigen_value_percentages = []
```
- PCA 분석 결과 설정 시 eigenvalues JSON 데이터 파싱
- 백분율 값만 추출하여 `eigen_value_percentages` 리스트에 저장
- 에러 발생 시 빈 리스트로 초기화 (안전한 처리)

### 4. 차트 업데이트 로직 (`ModanDialogs.py`)

#### 축 라벨 업데이트 (Line 3845-3871)
```python
if show_variance and self.analysis_method == 'PCA':
    # Get axis indices from combo boxes
    axis1_idx = self.comboAxis1.currentIndex()
    axis2_idx = self.comboAxis2.currentIndex()

    # Try to get eigenvalues from analysis_result or from stored values
    var_explained = None
    if hasattr(self, 'analysis_result') and hasattr(self.analysis_result, 'eigen_value_percentages'):
        var_explained = self.analysis_result.eigen_value_percentages
    elif hasattr(self, 'eigen_value_percentages'):
        var_explained = self.eigen_value_percentages

    if var_explained:
        try:
            # Axis1: index 0 is CSize, so PC1 is at index 1, PC2 at index 2, etc.
            if axis1_idx > 0:  # Skip if CSize is selected (index 0)
                pc_idx_1 = axis1_idx - 1
                if pc_idx_1 >= 0 and pc_idx_1 < len(var_explained):
                    axis1_title += f" ({var_explained[pc_idx_1]*100:.1f}%)"

            # Axis2: PC1 is at index 0, PC2 at index 1, etc.
            if axis2_idx >= 0 and axis2_idx < len(var_explained):
                axis2_title += f" ({var_explained[axis2_idx]*100:.1f}%)"
        except:
            pass  # Silently continue if there's any issue
```

#### 축 인덱스 매핑
- **X축 (Axis1)**:
  - index 0 = Centroid Size (CSize)
  - index 1 = PC1
  - index 2 = PC2, ...
  - PC 인덱스 계산: `pc_idx = axis1_idx - 1`

- **Y축 (Axis2)**:
  - index 0 = PC1
  - index 1 = PC2, ...
  - PC 인덱스 직접 매핑: `pc_idx = axis2_idx`

### 5. 백엔드 데이터 생성 (`ModanController.py`)

#### PCA 실행 시 eigenvalues 저장 (Line 790-795)
```python
if hasattr(pca_result, 'raw_eigen_values') and hasattr(pca_result, 'eigen_value_percentages'):
    eigenvalues_list = []
    for val, variance_ratio in zip(pca_result.raw_eigen_values, pca_result.eigen_value_percentages):
        eigenvalues_list.append([val, variance_ratio])
    analysis.pca_eigenvalues_json = json.dumps(eigenvalues_list)
```

## 사용 방법

1. PCA 분석 실행
2. Data Exploration Dialog 열기
3. "Show var. explained" 체크박스 활성화
4. Scatterplot의 축 라벨에 분산 설명력 백분율 표시 확인

## 표시 예시

- 체크박스 비활성화 시:
  - X축: "PC1"
  - Y축: "PC2"

- 체크박스 활성화 시:
  - X축: "PC1 (45.2%)"
  - Y축: "PC2 (23.1%)"

## 특징 및 제한사항

### 특징
- PCA 분석에만 적용 (CVA, MANOVA는 미지원)
- 실시간 토글 가능 (체크박스로 즉시 on/off)
- 기존 축 제목 유지하면서 백분율 정보만 추가
- 에러 발생 시 조용히 무시하고 기본 라벨 표시 (사용자 경험 유지)

### 제한사항
- CVA(Canonical Variate Analysis)와 MANOVA는 eigenvalue의 의미가 다르므로 미지원
- Centroid Size가 X축으로 선택된 경우 백분율 표시 안 함 (PC가 아니므로)

## 테스트 시나리오

1. **정상 케이스**:
   - PCA 분석 실행 → Data Exploration → 체크박스 활성화 → 백분율 표시 확인

2. **엣지 케이스**:
   - eigenvalues 데이터가 없는 경우 → 체크박스 활성화해도 백분율 미표시
   - CSize를 X축으로 선택 → X축에는 백분율 미표시, Y축에만 표시
   - PC10 이상의 높은 차원 선택 → 해당 PC의 백분율 정확히 표시

3. **에러 처리**:
   - JSON 파싱 실패 → 기본 라벨만 표시
   - 인덱스 범위 초과 → 기본 라벨만 표시

## 관련 파일
- `ModanDialogs.py`: UI 및 표시 로직
- `ModanController.py`: eigenvalues 계산 및 저장
- `MdModel.py`: `pca_eigenvalues_json` 필드 정의
- `MdStatistics.py`: PCA 계산 로직 (eigenvalues 생성)

## 향후 개선 사항
1. CVA 분석에도 적절한 통계 정보 표시 방안 검토
2. 툴팁으로 누적 분산 설명력 표시 고려
3. 설정 저장하여 다음 세션에서도 체크 상태 유지
4. 3D scatterplot에도 동일 기능 적용
