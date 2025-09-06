# 오버레이 타이틀 및 테이블 UI 개선

**작업일**: 2025-09-06  
**작업자**: Claude  
**관련 파일**: `Modan2.py`, `ModanComponents.py`

## 작업 요약

오버레이 위젯의 타이틀 표시 기능과 오브젝트 테이블의 사용성을 개선했습니다. 오브젝트 이름을 타이틀바에 표시하고, 컨텍스트 메뉴에 Edit object 기능을 추가했으며, 선택된 오브젝트 행을 시각적으로 강조하는 기능을 구현했습니다.

## 주요 변경 사항

### 1. 오버레이 타이틀 기능 구현

#### 1.1 타이틀 라벨 추가
- **위치**: 오버레이 헤더의 중앙
- **스타일**: 굵은 글씨체, 12px, 진회색 (#333333)
- **정렬**: 가운데 정렬 (`Qt.AlignCenter`)

```python
# Header layout with title and close button
header_layout = QHBoxLayout()
header_layout.setContentsMargins(8, 5, 5, 5)

# Title label for object name
self.overlay_title_label = QLabel("Object")
self.overlay_title_label.setStyleSheet("""
    QLabel {
        color: #333333;
        font-weight: bold;
        font-size: 12px;
    }
""")
self.overlay_title_label.setAlignment(Qt.AlignCenter)

header_layout.addStretch()  # Push title to center
header_layout.addWidget(self.overlay_title_label)
header_layout.addStretch()  # Push close button to the right
header_layout.addWidget(close_button)
```

#### 1.2 동적 타이틀 업데이트
- **오브젝트 선택 시**: 오브젝트 이름 표시
- **선택 해제 시**: 기본 "Object" 텍스트로 복원
- **접두사 제거**: "Object:" 접두사 없이 오브젝트 이름만 표시

```python
def show_object(self, obj):
    # ... 기존 코드 ...
    
    # Update overlay title with object name
    if hasattr(self, 'overlay_title_label') and obj:
        self.overlay_title_label.setText(obj.object_name)
```

### 2. 오브젝트 테이블 컨텍스트 메뉴 개선

#### 2.1 Edit Object 액션 추가
- **위치**: 컨텍스트 메뉴 최상단
- **조건**: 행이 선택되어 있을 때만 표시
- **구분**: 구분선으로 다른 액션들과 분리

```python
# MdTableView.__init__()
self.edit_object_action = QAction(self.tr("Edit object"), self)
self.edit_object_action.triggered.connect(self.edit_selected_object)

# show_context_menu()
menu = QMenu(self)

# Add Edit object option at the top if a row is selected
if selected_indices:
    menu.addAction(self.edit_object_action)
    menu.addSeparator()
```

#### 2.2 툴바 액션과 연결
- **기능**: 컨텍스트 메뉴의 "Edit object"가 툴바의 Edit Object 버튼과 동일한 동작 수행
- **구현**: 부모 윈도우를 탐색하여 `actionEditObject` 트리거

```python
def edit_selected_object(self):
    """Trigger the main window's edit object action"""
    parent = self.parent()
    while parent and not hasattr(parent, 'actionEditObject'):
        parent = parent.parent()
    
    if parent and hasattr(parent, 'actionEditObject'):
        parent.actionEditObject.trigger()
```

### 3. 선택된 오브젝트 행 시각적 강조

#### 3.1 Row 전체 테두리 강조
- **문제**: Cell mode에서도 선택된 오브젝트가 구별되지 않음
- **해결**: 선택된 오브젝트의 행 전체에 테두리 적용
- **스타일**: 3px 두께의 파란색 테두리 (#0078d4)

#### 3.2 Custom Paint 구현
```python
def paintEvent(self, event):
    """Override paint event to draw row border for selected object"""
    super().paintEvent(event)
    
    if self.selected_object_row >= 0 and self.model():
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get the row geometry
        row_rect = QRect()
        for col in range(self.model().columnCount()):
            if not self.isColumnHidden(col):
                cell_rect = self.visualRect(self.model().index(self.selected_object_row, col))
                if row_rect.isNull():
                    row_rect = cell_rect
                else:
                    row_rect = row_rect.united(cell_rect)
        
        if not row_rect.isNull():
            # Draw the border around the entire row
            painter.setPen(QPen(QColor(0, 120, 212), 3))  # Blue border, 3px thick
            painter.drawRect(row_rect.adjusted(1, 1, -1, -1))
```

#### 3.3 동적 행 하이라이트 관리
- **추적 변수**: `selected_object_row` 속성으로 현재 선택된 행 추적
- **업데이트 메서드**: `setSelectedObjectRow(row)` 메서드로 선택 상태 변경
- **자동 갱신**: `viewport().update()` 호출로 즉시 화면 갱신

```python
def setSelectedObjectRow(self, row):
    """Set the currently selected object row for highlighting"""
    if self.selected_object_row != row:
        self.selected_object_row = row
        self.viewport().update()  # Trigger repaint
```

### 4. 메인 윈도우 연동 개선

#### 4.1 오브젝트 선택 변경 시 행 하이라이트 업데이트
```python
def on_object_selection_changed(self, selected, deselected):
    # ... 기존 코드 ...
    
    # Highlight the selected object row in the table
    if hasattr(self, 'tableView') and self.tableView.selectionModel():
        selected_indexes = self.tableView.selectionModel().selectedIndexes()
        if selected_indexes:
            selected_row = selected_indexes[0].row()
            self.tableView.setSelectedObjectRow(selected_row)
```

#### 4.2 선택 해제 시 정리 작업
- 오버레이 타이틀 초기화
- 행 하이라이트 제거
- 오버레이 숨김

## 사용자 경험 개선

### 1. 명확한 정보 표시
- **오버레이 타이틀**: 현재 보고 있는 오브젝트가 무엇인지 즉시 확인 가능
- **중앙 정렬**: 시각적으로 균형잡힌 레이아웃

### 2. 직관적인 상호작용
- **컨텍스트 메뉴**: 우클릭으로 바로 Edit object 기능 접근
- **툴바 연동**: 일관된 사용자 경험 제공
- **시각적 구분**: 선택된 행이 명확히 구별됨

### 3. Cell Mode에서의 개선
- **문제 해결**: Cell mode에서도 현재 오브젝트 행이 구별됨
- **일관성**: Row mode와 Cell mode 모두에서 동일한 시각적 피드백

## 구현 세부사항

### 타이틀 레이아웃 구조
```
Header Layout
├── Stretch (좌측 여백)
├── Title Label (중앙)
├── Stretch (우측 여백)
└── Close Button (우측 끝)
```

### 컨텍스트 메뉴 구조
```
Context Menu
├── Edit object (선택된 행이 있을 때)
├── Separator
├── Copy
├── Paste (읽기전용 컬럼이 아닐 때)
├── Fill sequence (조건부)
├── Fill value
└── Clear
```

### 행 하이라이트 렌더링 순서
1. 기본 테이블 렌더링 (`super().paintEvent()`)
2. 선택된 행 확인 (`selected_object_row >= 0`)
3. 행 영역 계산 (모든 보이는 컬럼의 셀 영역 통합)
4. 파란색 테두리 그리기 (`QPen(QColor(0, 120, 212), 3)`)

## 테스트 확인 사항

1. **타이틀 표시**: 오브젝트 선택/해제 시 타이틀 정상 변경 ✅
2. **타이틀 정렬**: 중앙 정렬 및 닫기 버튼과의 균형 ✅
3. **컨텍스트 메뉴**: Edit object 옵션 표시 및 기능 동작 ✅
4. **행 하이라이트**: Cell mode에서 선택된 오브젝트 행 구별 ✅
5. **동적 업데이트**: 오브젝트 선택 변경 시 즉시 반영 ✅

## 향후 개선 가능 사항

1. **애니메이션 효과**: 행 하이라이트 전환 시 부드러운 애니메이션
2. **커스터마이즈**: 테두리 색상 및 두께 설정 가능
3. **키보드 내비게이션**: 키보드로 오브젝트 간 이동 시 행 하이라이트 연동
4. **다중 선택**: 여러 오브젝트 선택 시 모든 해당 행 하이라이트

## 코드 품질

- **재사용성**: `setSelectedObjectRow` 메서드로 외부에서 행 하이라이트 제어 가능
- **성능 최적화**: 행 변경 시에만 `viewport().update()` 호출
- **에러 처리**: 안전한 부모 윈도우 탐색 및 속성 확인
- **일관성**: 기존 코드 스타일과 일치하는 구현

## 영향 범위

- **UI/UX**: 사용자 인터페이스 개선으로 사용성 향상
- **성능**: 최소한의 추가 렌더링으로 성능 영향 미미
- **호환성**: 기존 기능에 영향 없이 새 기능 추가
- **유지보수**: 명확한 메서드 분리로 유지보수 용이