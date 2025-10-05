# Procrustes Superimposition with Missing Landmark Support - Implementation Plan

## 날짜
2025-09-18

## 작업자
Jikhan Jung / Claude

## 현재 상황 분석

### Procrustes 구현 현황
1. **MdModel.MdDatasetOps.procrustes_superimposition()** (주로 사용)
   - 반복적 GPA (Generalized Procrustes Analysis) 구현
   - 모든 분석 전 전처리로 사용됨
   - Missing landmark 처리 없음

2. **MdStatistics.do_procrustes_analysis()** (거의 미사용)
   - SciPy procrustes 함수 래퍼
   - 별도 "PROCRUSTES" 분석 타입 선택 시만 사용
   - Missing landmark 처리 없음

### 문제점 식별

#### MdObjectOps 클래스 메서드들
1. **move()** (Line 904)
   - `lm[0] = lm[0] + x` → None + float 연산 에러
   - Missing landmark 이동 불가

2. **rescale()** (Line 921)
   - `lm = [x * factor for x in lm]` → None * float 연산 에러
   - Missing landmark 스케일링 불가

3. **apply_rotation_matrix()** (Line 935)
   - numpy 행렬 연산에 None 포함 시 에러
   - Missing landmark 회전 불가

#### MdDatasetOps 클래스 메서드들
4. **get_average_shape()** (Line 1207)
   - None 값 평균 계산 불가
   - Missing landmark 평균 형태 계산 필요

5. **rotate_gls_to_reference_shape()** (Line 1278)
   - numpy 배열 변환 시 None 처리 안 됨
   - rotation_matrix 계산 시 missing 처리 필요

## 구현 전략

### Option 1: Complete Case Analysis (단순, 제한적)
- Missing landmark가 있는 개체 전체 제외
- 장점: 구현 간단, 수학적으로 명확
- 단점: 데이터 손실 많음, 실용성 낮음

### Option 2: Pairwise Deletion (중간 복잡도)
- 각 landmark별로 유효한 개체만 사용
- 장점: 데이터 활용도 높음
- 단점: 형태 일관성 문제 가능

### Option 3: Iterative Imputation (권장) ⭐
- Missing landmark를 추정하면서 반복
- 장점: 모든 데이터 활용, 통계적으로 타당
- 단점: 구현 복잡, 계산 시간 증가

## 구현 계획 (Iterative Imputation)

### Phase 1: 기본 인프라 구축
**목표**: Missing landmark를 안전하게 처리할 수 있는 기반 마련

#### 1.1 MdObjectOps 메서드 수정
```python
def move(self, x, y, z=0):
    """Move object, preserving missing landmarks"""
    new_landmark_list = []
    for lm in self.landmark_list:
        if lm[0] is not None and lm[1] is not None:
            lm[0] = lm[0] + x
            lm[1] = lm[1] + y
            if len(lm) == 3 and lm[2] is not None:
                lm[2] = lm[2] + z
        new_landmark_list.append(lm)
    self.landmark_list = new_landmark_list

def rescale(self, factor):
    """Rescale object, preserving missing landmarks"""
    new_landmark_list = []
    for lm in self.landmark_list:
        new_lm = []
        for coord in lm:
            if coord is not None:
                new_lm.append(coord * factor)
            else:
                new_lm.append(None)
        new_landmark_list.append(new_lm)
    self.landmark_list = new_landmark_list
```

#### 1.2 회전 행렬 적용 수정
```python
def apply_rotation_matrix(self, rotation_matrix):
    """Apply rotation, handling missing landmarks"""
    # Missing landmark는 회전하지 않고 None 유지
    # Valid landmark만 회전
```

### Phase 2: Missing Landmark 추정 구현
**목표**: TPS (Thin Plate Spline) 기반 missing landmark 추정

#### 2.1 TPS 추정 함수 추가
```python
def estimate_missing_landmarks(self, reference_shape):
    """Estimate missing landmarks using TPS from reference"""
    # 1. Valid landmarks 식별
    # 2. TPS 변환 계산
    # 3. Missing landmarks 추정
    # 4. 임시 값으로 채우기
```

#### 2.2 가중 평균 계산
```python
def get_weighted_average_shape(self, weights=None):
    """Calculate average shape with missing landmark handling"""
    # Missing이 아닌 landmark만으로 평균
    # 각 landmark별 가중치 적용
```

### Phase 3: Iterative Procrustes 수정
**목표**: Missing landmark를 고려한 반복적 정렬

#### 3.1 수정된 Procrustes 알고리즘
```python
def procrustes_superimposition_with_missing(self):
    """Modified GPA with missing landmark support"""
    # 1. 초기 정렬 (valid landmarks만 사용)
    # 2. Missing landmarks 추정
    # 3. 전체 정렬
    # 4. 수렴까지 반복:
    #    a. 평균 형태 계산
    #    b. Missing 재추정
    #    c. 재정렬
```

#### 3.2 수렴 기준 수정
```python
def is_converged(self, shape1, shape2, tolerance=1e-10):
    """Check convergence excluding missing landmarks"""
    # Valid landmarks만으로 수렴 판단
```

### Phase 4: 통계 분석 연동
**목표**: PCA/CVA/MANOVA에서 missing landmark 처리

#### 4.1 분석 전 검증
```python
def validate_for_analysis(self):
    """Check if dataset is ready for statistical analysis"""
    # Missing landmark 비율 체크
    # 분석 가능 여부 판단
```

#### 4.2 Missing 처리 옵션
- Complete case analysis
- Mean imputation
- Regression imputation
- Multiple imputation

### Phase 5: UI 업데이트
**목표**: 사용자에게 missing landmark 처리 옵션 제공

#### 5.1 NewAnalysisDialog 수정
- Missing landmark 처리 방법 선택 콤보박스
- Missing landmark 통계 표시
- 경고 메시지 추가

#### 5.2 진행 상황 표시
- Missing landmark 추정 진행률
- 수렴 상태 표시

## 구현 우선순위

### 1단계 (긴급) - 기본 안정성
- [ ] move(), rescale() None 체크 추가
- [ ] apply_rotation_matrix() None 처리
- [ ] 에러 방지를 위한 최소한의 수정

### 2단계 (중요) - Complete Case 구현
- [ ] Missing이 있는 개체 식별
- [ ] Complete case로만 Procrustes 수행
- [ ] 사용자에게 제외된 개체 알림

### 3단계 (권장) - Iterative Imputation
- [ ] TPS 기반 추정 구현
- [ ] 반복적 정렬 알고리즘
- [ ] 수렴 검증

### 4단계 (선택) - 고급 기능
- [ ] Multiple imputation
- [ ] Bootstrap 신뢰구간
- [ ] Missing pattern 분석

## 테스트 계획

### 단위 테스트
1. move() with None values
2. rescale() with None values
3. apply_rotation_matrix() with missing
4. get_average_shape() with missing
5. TPS estimation accuracy

### 통합 테스트
1. 10% missing landmarks
2. 30% missing landmarks
3. Systematic missing (특정 landmark)
4. Random missing pattern
5. 수렴 속도 비교

### 검증 기준
- Original data (no missing) vs Imputed data 비교
- Procrustes distance 차이 < 5%
- PCA variance explained 차이 < 3%
- 계산 시간 증가 < 2배

## 예상 일정
- Phase 1: 2시간 (기본 인프라)
- Phase 2: 4시간 (추정 알고리즘)
- Phase 3: 3시간 (Iterative Procrustes)
- Phase 4: 2시간 (통계 분석 연동)
- Phase 5: 2시간 (UI 업데이트)
- 테스트: 3시간

총 예상: 16시간

## 참고 문헌
1. Bookstein, F. L. (1991). Morphometric Tools for Landmark Data
2. Dryden, I. L., & Mardia, K. V. (2016). Statistical Shape Analysis
3. Arbour, J. H., & Brown, C. M. (2014). Incomplete specimens in geometric morphometric analyses

## 위험 요소
1. **성능 저하**: Iterative imputation으로 인한 계산 시간 증가
2. **수렴 실패**: Missing 비율이 높을 때 불안정
3. **통계적 타당성**: Imputed data의 신뢰성 문제
4. **하위 호환성**: 기존 분석 결과와의 일관성

## 대안
Missing landmark 비율이 높은 경우:
1. 사용자에게 경고 후 분석 중단
2. Landmark 제외 후 재분석
3. 다른 정렬 방법 사용 (Resistant-fit 등)
