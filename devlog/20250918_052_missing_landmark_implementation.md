# Missing Landmark Support - Implementation Complete (Phases 1-3)

## 날짜
2025-09-18

## 작업자
Jikhan Jung / Claude

## 완료된 작업

### Phase 1: UI 추가 ✓
**ModanDialogs.py**
- Object Dialog에 "Add Missing" 버튼 추가 (Line 935-938)
- `btnAddMissing_clicked()` 메서드 구현 (Line 1080-1098)
- 버튼 클릭 시 None 값을 가진 랜드마크 추가
- 2D/3D 차원에 따라 적절히 처리

### Phase 2: 데이터 모델 수정 ✓

**ModanDialogs.py**
- `show_landmarks()` 수정: Missing 랜드마크를 "MISSING" 텍스트로 표시, 빨간색으로 강조 (Line 1392-1423)
- `make_landmark_str()` 수정: "MISSING" 텍스트를 빈 문자열로 변환하여 저장 (Line 1456-1472)

**MdModel.py**
- `pack_landmark()` 수정: None 값을 빈 문자열로 저장 (Line 327-338)
- `unpack_landmark()`: 이미 None 값 처리 지원 (Line 340-349)
- `get_centroid_coord()` 수정: None 값을 제외하고 centroid 계산 (Line 437-474)
- `get_centroid_size()` 수정: None 값을 가진 랜드마크 제외하고 크기 계산 (Line 390-415)

### Phase 3: 시각화 업데이트 ✓

**ModanComponents.py**

#### ObjectViewer2D
- `draw_object()` 수정: Missing 랜드마크 체크 및 특별 표시 (Line 719-739)
- `draw_missing_landmark()` 추가: X 마크를 빨간 점선으로 표시 (Line 762-783)
- `paintEvent()` 수정: Missing 랜드마크 스킵 처리 (Line 838-842)
- Wireframe 렌더링: Missing 랜드마크가 포함된 edge 스킵 (Line 810-818)

#### ObjectViewer3D
- 랜드마크 렌더링: Missing 랜드마크 스킵 (Line 1978-1981, 2028-2032)
- Wireframe 렌더링: Missing 랜드마크가 포함된 edge 검증 후 렌더링 (Line 1944-1959)

## 구현 특징

### 데이터 표현
- **Python 내부**: None 사용
- **Database 저장**: "Missing" 텍스트로 저장
- **UI 표시**: "MISSING" 텍스트로 표시 (빨간색)

### 시각화
- **2D View**: 빨간색 점선 X 마크로 표시
- **3D View**: 렌더링에서 제외 (표시하지 않음)
- **Table**: "MISSING" 텍스트, 빨간색 강조

### 계산 처리
- Centroid 계산: None 값 제외하고 평균 계산
- Centroid size: 유효한 랜드마크만으로 계산
- Wireframe: Missing 포함된 edge는 렌더링 스킵

## 테스트 결과

### 데이터 형식 예시
```
396.0    196.0
901.0    179.0
Missing    Missing
901.0    482.0
750.0    658.0
```

### 저장/로드 사이클
```python
# Python 리스트: [[396.0, 196.0], [901.0, 179.0], [None, None], [901.0, 482.0], [750.0, 658.0]]
# DB 저장: '396.0\t196.0\n901.0\t179.0\nMissing\tMissing\n901.0\t482.0\n750.0\t658.0'
# 로드 후: [[396.0, 196.0], [901.0, 179.0], [None, None], [901.0, 482.0], [750.0, 658.0]]
```
✓ Missing 값이 "Missing" 텍스트로 저장되고 정확히 복원됨

## 남은 작업 (Phase 4-5)

### Phase 4: 분석 지원 (미완료)
- Procrustes 분석 시 missing landmark 처리
- PCA/CVA 분석 시 missing value 처리 옵션
- Complete case analysis vs Imputation 선택

### Phase 5: 테스트 및 문서화 (미완료)
- 자동화된 단위 테스트 작성
- 사용자 가이드 업데이트
- 다양한 시나리오 통합 테스트

## 사용 방법

1. Object Dialog 열기
2. "Add Missing" 버튼 클릭
3. Missing landmark가 테이블에 "MISSING"으로 표시됨
4. 2D view에서 빨간 X 마크로 표시
5. 저장 시 자동으로 처리되어 DB에 저장

## 기술적 결정

1. **None vs Special Value**: Python의 표준 None 사용으로 코드 가독성 향상
2. **빈 문자열 저장**: 기존 DB 스키마 유지하면서 호환성 보장
3. **시각적 구분**: 빨간색과 점선으로 명확한 구분
4. **계산 제외**: Missing value는 통계 계산에서 자동 제외

## 향후 개선 사항

1. Missing landmark 위치 추정 알고리즘
2. Imputation 방법 선택 UI
3. Missing pattern 분석 도구
4. 3D view에서도 missing 표시 (반투명 등)
