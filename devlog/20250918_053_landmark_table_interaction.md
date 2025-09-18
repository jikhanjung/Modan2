# Landmark Table Interaction Enhancement

## 날짜
2025-09-18

## 작업자
Jikhan Jung / Claude

## 구현 내용

### 1. UI 레이아웃 개선
**변경 전**: 좌표 입력 필드와 Add 버튼이 한 줄에 배치
**변경 후**: 2줄 레이아웃
- 첫 번째 줄: X, Y, Z 좌표 입력 필드
- 두 번째 줄: Add, Update, Delete 버튼

### 2. 테이블 상호작용 추가
- 랜드마크 테이블에서 행 선택 가능
- 선택 시 해당 좌표가 입력 필드에 자동으로 표시
- Missing 랜드마크 선택 시 빈 필드로 표시

### 3. 버튼 상태 관리
**선택하지 않은 상태**:
- Add 버튼: 활성화
- Update 버튼: 비활성화
- Delete 버튼: 비활성화

**랜드마크 선택 상태**:
- Add 버튼: 비활성화
- Update 버튼: 활성화
- Delete 버튼: 활성화

### 4. 새로운 메서드들

#### `on_landmark_selected(self)`
- 테이블에서 랜드마크 선택 시 호출
- 선택된 랜드마크의 좌표를 입력 필드에 로드
- 버튼 상태 업데이트

#### `btnAddInput_clicked(self)`
- Add 버튼 클릭 핸들러
- 새 랜드마크 추가

#### `btnUpdateInput_clicked(self)`
- Update 버튼 클릭 핸들러
- 선택된 랜드마크 좌표 수정
- 빈 값 입력 시 Missing 랜드마크로 변경 가능

#### `btnDeleteInput_clicked(self)`
- Delete 버튼 클릭 핸들러
- 선택된 랜드마크 삭제

### 5. 개선된 워크플로우

#### 새 랜드마크 추가
1. 좌표 입력 필드에 값 입력
2. Add 버튼 클릭 또는 Enter 키
3. 테이블에 추가됨

#### 기존 랜드마크 수정
1. 테이블에서 랜드마크 클릭
2. 좌표가 입력 필드에 표시됨
3. 값 수정
4. Update 버튼 클릭 또는 Enter 키
5. 테이블 업데이트됨

#### 랜드마크 삭제
1. 테이블에서 랜드마크 클릭
2. Delete 버튼 클릭
3. 테이블에서 제거됨

## 구현 상세

### ModanDialogs.py 변경사항

#### Line 801-848: 입력 위젯 재구성
```python
# Create two-row layout for coordinate input
self.inputWidget = QWidget()
self.inputMainLayout = QVBoxLayout()
# ... coordinate inputs in first row
# ... buttons in second row
```

#### Line 1420-1431: 테이블 설정
```python
def show_landmarks(self):
    # Configure table
    self.edtLandmarkStr.setSelectionBehavior(QTableWidget.SelectRows)
    self.edtLandmarkStr.setSelectionMode(QTableWidget.SingleSelection)
    # Connect selection handler
    self.edtLandmarkStr.itemSelectionChanged.connect(self.on_landmark_selected)
```

#### Line 1398-1489: 이벤트 핸들러
- `on_landmark_selected()`: 테이블 선택 처리
- `btnAddInput_clicked()`: Add 버튼 처리
- `btnUpdateInput_clicked()`: Update 버튼 처리
- `btnDeleteInput_clicked()`: Delete 버튼 처리

## 사용자 경험 개선

### 장점
1. **직관적인 편집**: 테이블에서 클릭하면 즉시 편집 가능
2. **명확한 액션**: Add/Update/Delete 버튼으로 의도가 명확
3. **Missing 지원**: Missing 랜드마크도 수정/삭제 가능
4. **자동 상태 관리**: 컨텍스트에 따라 버튼 자동 활성화/비활성화

### 키보드 단축키
- Enter 키: 선택 상태에 따라 Add 또는 Update 수행
- 좌표 필드 간 Tab 이동 지원

## 테스트 시나리오

1. **추가 테스트**
   - 좌표 입력 → Add → 테이블에 추가 확인

2. **수정 테스트**
   - 테이블 클릭 → 좌표 표시 확인
   - 값 변경 → Update → 테이블 업데이트 확인

3. **삭제 테스트**
   - 테이블 클릭 → Delete → 테이블에서 제거 확인

4. **Missing 랜드마크 테스트**
   - Missing 선택 → 빈 필드 표시 확인
   - 값 입력 → Update → Normal 랜드마크로 변경 확인
   - 값 삭제 → Update → Missing으로 변경 확인

## 향후 개선 사항

1. **다중 선택**: 여러 랜드마크 동시 삭제
2. **Undo/Redo**: 편집 작업 취소/재실행
3. **키보드 단축키**: Delete 키로 삭제, Ctrl+D 복제 등
4. **드래그 앤 드롭**: 테이블에서 순서 변경
5. **복사/붙여넣기**: 랜드마크 좌표 복사/붙여넣기