# Missing Landmark Support Implementation Plan

## 날짜
2025-09-18

## 작업자
Jikhan Jung

## 배경
- 현재 Modan2는 모든 object가 동일한 수의 landmark를 가져야 한다고 가정함
- 실제 연구에서는 일부 landmark가 손상되거나 관찰 불가능한 경우가 있음
- Missing landmark를 지원하면 더 많은 데이터를 분석에 포함시킬 수 있음
- 통계 분석 시 missing value를 적절히 처리하는 방법론 필요

## 구현 목표
1. Object Dialog에서 missing landmark를 추가할 수 있는 UI 제공
2. Missing landmark를 데이터베이스에 저장하고 로드할 수 있도록 지원
3. 시각화 시 missing landmark를 구분하여 표시
4. 분석 시 missing landmark를 적절히 처리 (제외 또는 imputation)

## 기술적 접근 방식

### 1. Missing Value 표현 방법
**Option A: Special Numeric Value (-99999)**
- 장점: 기존 데이터 구조 유지, 숫자 배열로 처리 가능
- 단점: 실제 좌표값과 혼동 가능성, magic number 사용

**Option B: Text Marker ("MISSING" or "NA")**
- 장점: 명시적이고 직관적
- 단점: 데이터 타입 변경 필요, 파싱 로직 복잡

**Option C: None/null value**
- 장점: Python의 표준 방식, 명확한 의미
- 단점: 데이터베이스 저장 시 처리 필요

**선택: Option C (None) + Database에는 특수 문자열로 저장**
- Python 내부: None 사용
- Database 저장: "NA" 또는 빈 문자열로 표현
- 장점: Python 코드에서 자연스럽고, DB 호환성도 유지

### 2. UI 구현 계획

#### Object Dialog 수정 (ModanDialogs.py)
```python
# Line 934 근처, btnAddFile 다음에 추가
self.btnAddMissing = QPushButton()
self.btnAddMissing.setText(self.tr("Add Missing"))
self.btnAddMissing.clicked.connect(self.btnAddMissing_clicked)
self.right_middle_layout.addWidget(self.btnAddMissing)
```

#### 새로운 메서드 추가
```python
def btnAddMissing_clicked(self):
    """Add a missing landmark placeholder"""
    if self.dataset.dimension == 2:
        self.landmark_list.append([None, None])
    elif self.dataset.dimension == 3:
        self.landmark_list.append([None, None, None])
    self.show_landmarks()

def add_landmark(self, x, y, z=None):
    """Modified to handle None values"""
    if x is None or y is None:
        # Handle missing landmark
        if self.dataset.dimension == 2:
            self.landmark_list.append([None, None])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([None, None, None if z is None else None])
    else:
        # Existing logic for normal landmarks
        if self.dataset.dimension == 2:
            self.landmark_list.append([float(x), float(y)])
        elif self.dataset.dimension == 3:
            self.landmark_list.append([float(x), float(y), float(z)])
    self.show_landmarks()
```

### 3. 데이터 저장/로드 수정 (MdModel.py)

#### Landmark 문자열 포맷 변경
```python
# 현재: "x1,y1;x2,y2;x3,y3"
# 제안: "x1,y1;NA,NA;x3,y3" (missing landmark는 NA로 표현)

def pack_landmark(self):
    """Convert landmark list to string for database storage"""
    landmark_strs = []
    for lm in self.landmark_list:
        if lm[0] is None or lm[1] is None:
            landmark_strs.append("NA,NA" if self.dataset.dimension == 2 else "NA,NA,NA")
        else:
            coords = [str(x) for x in lm[:self.dataset.dimension]]
            landmark_strs.append(LANDMARK_SEPARATOR.join(coords))
    self.landmark_str = LINE_SEPARATOR.join(landmark_strs)

def unpack_landmark(self):
    """Parse landmark string from database"""
    self.landmark_list = []
    if self.landmark_str is None or self.landmark_str == '':
        return self.landmark_list

    lm_list = self.landmark_str.split(LINE_SEPARATOR)
    for lm in lm_list:
        if lm != "":
            coords = lm.split(LANDMARK_SEPARATOR)
            landmark = []
            for coord in coords:
                if coord == "NA" or coord == "":
                    landmark.append(None)
                else:
                    landmark.append(float(coord))
            self.landmark_list.append(landmark)
    return self.landmark_list
```

### 4. 시각화 수정

#### ObjectViewer2D (ModanComponents.py)
```python
def show_landmarks(self):
    """Modified to handle missing landmarks"""
    for idx, lm in enumerate(self.landmark_list):
        if lm[0] is None or lm[1] is None:
            # Draw missing landmark indicator (e.g., X mark or different color)
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            # Draw an X or ? at expected position or skip
            continue
        else:
            # Existing drawing logic
            painter.setPen(QPen(landmark_color, landmark_size))
            painter.drawEllipse(QPointF(lm[0], lm[1]), radius, radius)
```

#### ObjectViewer3D (ModanComponents.py)
```python
def show_landmarks(self):
    """Modified to handle missing landmarks in 3D"""
    for idx, lm in enumerate(self.landmark_list):
        if lm[0] is None or lm[1] is None or (len(lm) > 2 and lm[2] is None):
            # Skip or draw special indicator for missing landmarks
            continue
        else:
            # Existing 3D rendering logic
            pass
```

### 5. 테이블 표시 수정

#### show_landmarks in ObjectDialog
```python
def show_landmarks(self):
    """Update landmark table to show missing values"""
    self.edtLandmarkStr.setRowCount(len(self.landmark_list))

    for idx, lm in enumerate(self.landmark_list):
        # Index column
        self.edtLandmarkStr.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))

        # Coordinate columns
        if lm[0] is None:
            self.edtLandmarkStr.setItem(idx, 1, QTableWidgetItem("MISSING"))
            self.edtLandmarkStr.item(idx, 1).setForeground(Qt.red)
        else:
            self.edtLandmarkStr.setItem(idx, 1, QTableWidgetItem(str(round(lm[0], 4))))

        if lm[1] is None:
            self.edtLandmarkStr.setItem(idx, 2, QTableWidgetItem("MISSING"))
            self.edtLandmarkStr.item(idx, 2).setForeground(Qt.red)
        else:
            self.edtLandmarkStr.setItem(idx, 2, QTableWidgetItem(str(round(lm[1], 4))))

        # Z coordinate for 3D
        if self.dataset.dimension == 3:
            if len(lm) > 2 and lm[2] is not None:
                self.edtLandmarkStr.setItem(idx, 3, QTableWidgetItem(str(round(lm[2], 4))))
            else:
                self.edtLandmarkStr.setItem(idx, 3, QTableWidgetItem("MISSING"))
                self.edtLandmarkStr.item(idx, 3).setForeground(Qt.red)
```

### 6. 분석 처리 (MdStatistics.py)

#### Procrustes Analysis 수정
```python
def procrustes_with_missing(landmark_data):
    """Handle missing landmarks in Procrustes analysis"""
    # Option 1: Complete case analysis (제외)
    # Option 2: Pairwise deletion
    # Option 3: Imputation (평균값 또는 예측값으로 대체)

    # 구현 예시: Complete case 방식
    valid_indices = []
    for i in range(len(landmark_data[0])):
        if all(obj[i][0] is not None for obj in landmark_data):
            valid_indices.append(i)

    # Filter to valid landmarks only
    filtered_data = []
    for obj in landmark_data:
        filtered_obj = [obj[i] for i in valid_indices]
        filtered_data.append(filtered_obj)

    return filtered_data, valid_indices
```

## 구현 순서

1. **Phase 1: UI 추가 (1일)**
   - Object Dialog에 "Add Missing" 버튼 추가
   - 버튼 클릭 시 missing landmark 추가 기능
   - 테이블에 missing 표시

2. **Phase 2: 데이터 모델 수정 (1일)**
   - pack_landmark/unpack_landmark 수정
   - None 값 처리 로직 추가
   - 데이터베이스 저장/로드 테스트

3. **Phase 3: 시각화 업데이트 (0.5일)**
   - 2D/3D viewer에서 missing landmark 표시
   - 색상 또는 기호로 구분

4. **Phase 4: 분석 지원 (2일)**
   - Procrustes 분석 시 missing 처리
   - PCA/CVA 분석 시 missing 처리
   - 통계 결과에 missing 정보 포함

5. **Phase 5: 테스트 및 문서화 (0.5일)**
   - 단위 테스트 작성
   - 사용자 가이드 업데이트

## 예상 파일 변경

1. **ModanDialogs.py**
   - ObjectDialog 클래스: UI 버튼 추가, 이벤트 핸들러
   - show_landmarks(): missing 표시 로직

2. **MdModel.py**
   - MdObject 클래스: pack/unpack_landmark 메서드
   - 데이터 검증 로직

3. **ModanComponents.py**
   - ObjectViewer2D/3D: missing landmark 렌더링

4. **MdStatistics.py**
   - 각종 분석 함수: missing value 처리

5. **MdUtils.py** (필요시)
   - 유틸리티 함수 추가

## 테스트 계획

1. **단위 테스트**
   - Missing landmark 추가/삭제
   - 저장/로드 정확성
   - None 값 처리

2. **통합 테스트**
   - Missing landmark가 있는 dataset 분석
   - 시각화 정확성
   - 통계 결과 검증

3. **사용자 시나리오**
   - 부분적으로 손상된 표본 입력
   - Missing landmark가 혼재된 dataset 분석
   - 결과 export/import

## 위험 요소 및 대응

1. **기존 데이터 호환성**
   - 위험: 기존 dataset이 로드되지 않을 수 있음
   - 대응: backward compatibility 유지, 마이그레이션 스크립트

2. **분석 정확성**
   - 위험: Missing value로 인한 분석 결과 왜곡
   - 대응: 적절한 imputation 방법 선택, 경고 메시지

3. **성능 저하**
   - 위험: None 체크로 인한 처리 속도 감소
   - 대응: 벡터화된 연산 유지, 조건부 처리 최소화

## 향후 개선 사항

1. **고급 Imputation 방법**
   - Multiple imputation
   - Machine learning 기반 예측
   - Spatial interpolation

2. **Missing Pattern 분석**
   - Missing 패턴 시각화
   - MCAR/MAR/MNAR 테스트

3. **사용자 옵션**
   - Missing 처리 방법 선택 UI
   - Threshold 설정 (최대 허용 missing 비율)

## 참고 자료
- Little, R. J., & Rubin, D. B. (2019). Statistical analysis with missing data.
- Morphometrics missing data handling in R: geomorph package
- PAST software missing landmark handling documentation