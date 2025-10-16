# Object Preview Overlay Visibility Persistence

- **문서 번호:** 20251016_P01
- **작성일:** 2025-10-16
- **작성자:** Claude
- **관련 Issue:** [#14 Object preview widget visibility](https://github.com/jikhanjung/Modan2/issues/14)

## 1. 문제 설명

### 현재 동작
사용자가 메인 윈도우의 object list(table view)에서 객체를 선택하면, 화면 우측 하단에 object preview overlay가 자동으로 나타납니다. 사용자가 데이터를 편집할 때 이 preview를 방해가 되어 닫기 버튼(×)을 클릭하여 숨기지만, **다른 행(row)으로 커서를 이동하면 overlay가 자동으로 다시 나타나는** 문제가 있습니다.

### 사용자 불만
"make it invisible should be more persistent" - 사용자가 한 번 overlay를 숨기면, 그 설정이 세션 동안 유지되어야 합니다. 매번 행을 이동할 때마다 반복적으로 닫아야 하는 것은 불편한 UX입니다.

## 2. 원인 분석

### 코드 분석 결과

#### 2.1 관련 코드 위치
- **파일**: `Modan2.py`
- **핵심 메서드**:
  - `on_object_selection_changed()` (line 1014~1043): TableView에서 객체 선택 시 호출
  - `show_object()` (line 1045~1057): 선택된 객체를 overlay에 표시
  - `show_object_overlay()` (line 1077~1082): Overlay 표시
  - `hide_object_overlay()` (line 1084~1087): Overlay 숨김
  - `position_object_overlay()` (line 1064~1075): Overlay 위치 조정

#### 2.2 문제 발생 원인

**`on_object_selection_changed()` 메서드 (line 1014-1057)**:
```python
def on_object_selection_changed(self, selected, deselected):
    selected_object_list = self.get_selected_object_list()
    if selected_object_list is None or len(selected_object_list) != 1:
        # ... 객체가 선택되지 않았을 때
        self.hide_object_overlay()  # ← 여기서 숨김
        return

    # 객체가 선택되었을 때
    self.btnEditObject.setEnabled(True)
    # ...
    self.show_object(self.selected_object)  # ← show_object 호출
```

**`show_object()` 메서드 (line 1045-1057)**:
```python
def show_object(self, obj):
    self.object_view.clear_object()
    self.object_view.landmark_list = copy.deepcopy(obj.landmark_list)
    self.object_view.set_object(obj)
    self.object_view.read_only = True
    self.object_view.update()

    # Update overlay title with object name
    if hasattr(self, "overlay_title_label") and obj:
        self.overlay_title_label.setText(obj.object_name)

    # Show the overlay when an object is selected
    self.show_object_overlay()  # ← 항상 overlay를 표시함!
```

**문제의 핵심**:
- 객체 선택이 변경될 때마다 `show_object()` → `show_object_overlay()`가 **무조건 호출**됩니다
- 사용자가 이전에 overlay를 숨겼는지 여부를 **전혀 추적하지 않음**
- 사용자 설정(preference)을 **저장하거나 확인하는 로직이 없음**

#### 2.3 Close 버튼 동작

**Close 버튼 연결 (line 1102)**:
```python
close_button.clicked.connect(self.hide_object_overlay)
```

**`hide_object_overlay()` 메서드 (line 1084-1087)**:
```python
def hide_object_overlay(self):
    """Hide the object overlay"""
    if hasattr(self, "object_overlay"):
        self.object_overlay.hide()  # ← 단순히 숨기기만 함
```

- Close 버튼을 클릭하면 overlay를 숨기지만
- **사용자가 숨겼다는 사실을 기록하지 않음**
- 다음 `on_object_selection_changed()` 호출 시 다시 표시됨

## 3. 해결 방안

### 3.1 설계 원칙

1. **사용자 설정 우선**: 사용자가 명시적으로 overlay를 숨기면, 그 설정이 우선합니다
2. **세션 지속성**: 세션 동안 사용자의 visibility 선택이 유지되어야 합니다
3. **선택적 영구 저장**: (선택사항) 설정을 config에 저장하여 앱 재시작 후에도 유지

### 3.2 구현 계획

#### Phase 1: 기본 Persistence + 재활성화 기능 (필수)

**Step 1: 상태 변수 추가**
- `ModanMainWindow` 클래스에 인스턴스 변수 추가:
  ```python
  self.object_overlay_auto_show = True  # True: 자동 표시, False: 수동만
  ```

**Step 2: Close 버튼 개선 - 토글 기능으로 변경**
- Close 버튼을 "Show/Hide 토글 버튼"으로 변경:
  ```python
  # In initUI() - 기존 close button 부분 수정
  self.overlay_toggle_button = QPushButton("×")
  self.overlay_toggle_button.setFixedSize(20, 20)
  self.overlay_toggle_button.setStyleSheet("""
      QPushButton {
          background-color: #ff6b6b;
          color: white;
          border: none;
          border-radius: 10px;
          font-weight: bold;
          font-size: 14px;
      }
      QPushButton:hover {
          background-color: #ff5252;
      }
  """)
  self.overlay_toggle_button.clicked.connect(self.toggle_object_overlay_auto_show)
  ```

**Step 3: 토글 메서드 추가 (새로운 메서드)**
- 사용자가 버튼 클릭 시 자동 표시 on/off:
  ```python
  def toggle_object_overlay_auto_show(self):
      """Toggle auto-show behavior of object overlay"""
      self.object_overlay_auto_show = not self.object_overlay_auto_show

      if self.object_overlay_auto_show:
          # 자동 표시 모드로 전환 - 현재 선택된 객체가 있으면 즉시 표시
          if self.selected_object:
              self.show_object_overlay()
          # 버튼 아이콘을 × 로 변경 (숨기기 버튼)
          self.overlay_toggle_button.setText("×")
          self.overlay_toggle_button.setStyleSheet("""
              QPushButton {
                  background-color: #ff6b6b;
                  color: white;
                  border: none;
                  border-radius: 10px;
                  font-weight: bold;
                  font-size: 14px;
              }
              QPushButton:hover {
                  background-color: #ff5252;
              }
          """)
      else:
          # 수동 모드로 전환 - overlay 숨기기
          self.hide_object_overlay()
          # 버튼 아이콘을 👁 로 변경 (보기 버튼)
          self.overlay_toggle_button.setText("👁")
          self.overlay_toggle_button.setStyleSheet("""
              QPushButton {
                  background-color: #4CAF50;
                  color: white;
                  border: none;
                  border-radius: 10px;
                  font-weight: bold;
                  font-size: 12px;
              }
              QPushButton:hover {
                  background-color: #45a049;
              }
          """)
  ```

**Step 4: `hide_object_overlay()` - 플래그 설정 없이 단순 숨김만**
  ```python
  def hide_object_overlay(self):
      """Hide the object overlay"""
      if hasattr(self, "object_overlay"):
          self.object_overlay.hide()
  ```

**Step 5: `show_object()` 수정**
- `object_overlay_auto_show` 플래그 확인:
  ```python
  def show_object(self, obj):
      self.object_view.clear_object()
      self.object_view.landmark_list = copy.deepcopy(obj.landmark_list)
      self.object_view.set_object(obj)
      self.object_view.read_only = True
      self.object_view.update()

      # Update overlay title with object name
      if hasattr(self, "overlay_title_label") and obj:
          self.overlay_title_label.setText(obj.object_name)

      # Show the overlay only if auto-show is enabled
      if getattr(self, "object_overlay_auto_show", True):
          self.show_object_overlay()
  ```

**Step 6: 초기화**
- `initUI()` 메서드에서 초기화:
  ```python
  # In initUI, after creating overlay
  self.object_overlay_auto_show = True
  ```

**Step 7: (선택사항) Tooltip 추가로 사용자 안내**
  ```python
  # In initUI, after creating toggle button
  self.overlay_toggle_button.setToolTip(
      "Click to toggle automatic preview\n"
      "× = Auto-show ON (click to turn OFF)\n"
      "👁 = Auto-show OFF (click to turn ON)"
  )
  ```

#### Phase 2: 추가 개선 사항 (선택사항)

**Option A: Keyboard Shortcut 추가**
- `Ctrl+P` 같은 단축키로 빠르게 토글
  ```python
  # In __init__
  self.actionTogglePreview = QAction("Toggle Object Preview", self)
  self.actionTogglePreview.setShortcut(QKeySequence("Ctrl+P"))
  self.actionTogglePreview.triggered.connect(self.toggle_object_overlay_auto_show)
  ```

**Option B: Context Menu에도 추가**
- TableView 우클릭 메뉴에 "Show/Hide Preview" 옵션 추가

#### Phase 3: 영구 저장 (선택사항)

설정을 config.json에 저장하여 앱 재시작 후에도 유지:

**Step 1: SettingsWrapper에 key 추가**
```python
# In read_settings() SettingsWrapper 정의 부분
self.key_map["ObjectOverlay/AutoShow"] = ("ui", "object_overlay_auto_show")
```

**Step 2: 설정 읽기**
```python
def read_settings(self):
    # ... existing code ...
    if not self.init_done:
        self.object_overlay_auto_show = self.config.get("ui", {}).get("object_overlay_auto_show", True)
```

**Step 3: 설정 쓰기**
```python
def write_settings(self):
    # ... existing code ...
    if hasattr(self.m_app, "settings"):
        self.m_app.settings.setValue("ObjectOverlay/AutoShow", self.object_overlay_auto_show)
```

### 3.3 엣지 케이스 처리

1. **Dataset 변경 시**: 다른 dataset으로 전환해도 설정 유지
2. **첫 실행 시**: 기본값은 `False` (overlay 표시)
3. **Overlay가 없는 상태에서**: `hasattr` 체크로 안전하게 처리

## 4. 테스트 계획

### 4.1 수동 테스트 시나리오

1. **기본 동작 테스트**:
   - [ ] 앱 시작
   - [ ] Dataset 선택
   - [ ] 첫 번째 object 선택 → overlay 표시되는지 확인
   - [ ] Close 버튼 클릭 → overlay 숨겨지는지 확인
   - [ ] 다른 object 선택 → overlay가 **나타나지 않는지** 확인 ✅
   - [ ] 여러 object를 번갈아 선택 → 계속 숨겨진 상태 유지되는지 확인

2. **Dataset 전환 테스트**:
   - [ ] Overlay를 숨긴 상태에서 다른 dataset 선택
   - [ ] 새 dataset의 object 선택 → 여전히 숨겨져 있는지 확인

3. **영구 저장 테스트** (Phase 3 구현 시):
   - [ ] Overlay를 숨긴 상태에서 앱 종료
   - [ ] 앱 재시작
   - [ ] Object 선택 → 여전히 숨겨져 있는지 확인

### 4.2 자동화 테스트

```python
# tests/test_object_overlay_persistence.py
def test_object_overlay_persistence(qtbot, main_window, sample_dataset):
    """Test that object overlay visibility persists across object selection"""
    # Setup: Select dataset and first object
    main_window.selected_dataset = sample_dataset
    main_window.load_object()
    first_object = sample_dataset.object_list[0]

    # Simulate selecting first object
    main_window.selected_object = first_object
    main_window.show_object(first_object)

    # Verify overlay is shown initially
    assert main_window.object_overlay.isVisible()
    assert not main_window.object_overlay_user_hidden

    # User hides the overlay
    main_window.hide_object_overlay()
    assert not main_window.object_overlay.isVisible()
    assert main_window.object_overlay_user_hidden

    # Select second object
    second_object = sample_dataset.object_list[1]
    main_window.selected_object = second_object
    main_window.show_object(second_object)

    # Verify overlay stays hidden
    assert not main_window.object_overlay.isVisible()
    assert main_window.object_overlay_user_hidden
```

## 5. 구현 우선순위

1. **Phase 1** (필수, 즉시 구현): 기본 persistence + 토글 버튼으로 재활성화 기능
   - Close 버튼을 토글 버튼으로 변경
   - 버튼 아이콘: × (자동표시 ON) ↔ 👁 (자동표시 OFF)
   - `object_overlay_auto_show` 플래그로 상태 관리
2. **Phase 2** (선택, 추후 고려): 키보드 단축키 등 추가 편의 기능
3. **Phase 3** (선택, 낮은 우선순위): 영구 저장 - 사용자 요청이 있을 경우

## 6. 예상 영향

### 6.1 긍정적 영향
- 사용자 경험 크게 개선
- 반복 작업 시 효율성 증가
- 사용자 불만 해소

### 6.2 위험 요소
- **없음**: 기존 동작을 개선하는 것이므로 breaking change 없음
- Backward compatibility 완벽 유지

## 7. 관련 파일

### 수정 대상
- `Modan2.py`:
  - `__init__()` or `initUI()`: 상태 변수 초기화 (line ~225)
  - `hide_object_overlay()`: 사용자 선택 기록 (line 1084-1087)
  - `show_object()`: 조건부 표시 로직 (line 1045-1057)
  - `read_settings()`: 설정 읽기 (Phase 3, line 356-591)
  - `write_settings()`: 설정 쓰기 (Phase 3, line 592-623)

### 테스트 파일
- `tests/test_object_overlay_persistence.py` (신규 생성)
- `tests/test_main_window.py` (기존 테스트 업데이트)

## 8. 참고사항

- 이 issue는 UI/UX 개선 사항으로, 기능 추가가 아닌 개선입니다
- 사용자가 명시적으로 요청한 내용이므로 높은 우선순위로 처리 권장
- Phase 1만 구현해도 충분히 문제 해결 가능

---

## 9. 구현 완료 (2025-10-16)

### 9.1 구현된 기능

#### ✅ Phase 1: 기본 Persistence + 토글 기능
**상태**: 완료

**구현 내용**:
- `object_overlay_auto_show` 플래그 추가 (Modan2.py)
- overlay 위젯 내부 토글 버튼 구현
  - 자동 표시 ON: 빨간색 × 버튼
  - 자동 표시 OFF: 녹색 👁 버튼
- `toggle_object_overlay_auto_show()` 메서드 추가
- `show_object()` 메서드 수정: auto-show 플래그 확인

**파일**:
- `Modan2.py`: lines 827-878, 1879-1927

#### ✅ Phase 2: 키보드 단축키
**상태**: 완료

**구현 내용**:
- `Ctrl+P` 단축키로 preview 토글 기능 추가
- `actionTogglePreview` QAction 생성 (line 149-154)
- View 메뉴에 Preview 메뉴 항목 추가 (line 195)

**파일**:
- `Modan2.py`: lines 149-154, 195

#### ✅ Phase 3: 영구 저장
**상태**: 완료

**구현 내용**:
- SettingsWrapper에 키 매핑 추가:
  - `ObjectOverlay/AutoShow` → `("ui", "object_overlay_auto_show")`
  - `ObjectOverlay/Position` → `("ui", "object_overlay_position")`
- `read_settings()`에서 config 값 읽기 (lines 506-517)
- `write_settings()`에서 config 값 저장 (lines 642-648)
- 설정 파일 위치: `~/.modan2/config.json`

**파일**:
- `Modan2.py`: lines 420-421, 506-517, 642-648

### 9.2 추가 구현 기능

#### ✅ 툴바 Preview 토글 버튼
**상태**: 완료

**구현 내용**:
- 툴바에 Preview 토글 버튼 추가
- checkable QAction으로 구현
- 버튼 상태가 auto-show 상태와 동기화
- separator로 다른 버튼들과 구분
- 초기 상태를 저장된 config 값으로 설정 (lines 511-513)

**파일**:
- `Modan2.py`: lines 149-154, 166-168

#### ✅ Overlay 위치 저장 및 복원
**상태**: 완료

**구현 내용**:
- 사용자가 overlay를 드래그하면 위치 저장
- snap 기능: 드래그 완료 시 가장 가까운 코너로 자동 정렬
- `on_overlay_moved()` 콜백으로 위치 저장
- `position_object_overlay()`에서 저장된 위치 복원
- 위치 정보는 `[x, y]` 형식으로 config에 저장

**파일**:
- `Modan2.py`: lines 1841-1864, 1929-1944
- `components/widgets/overlay_widget.py`: lines 131-133, 188-210, 308-356

#### ✅ Overlay Parent 참조 수정
**상태**: 완료

**문제**: overlay의 parent가 `dataset_view` (QWidget)였기 때문에 `on_overlay_moved()` 콜백을 호출할 수 없었음

**해결**:
- `ResizableOverlayWidget.__init__()`에 `main_window` 파라미터 추가
- overlay 생성 시 main_window 참조 전달
- `mouseReleaseEvent()`에서 `main_window.on_overlay_moved()` 호출

**파일**:
- `components/widgets/overlay_widget.py`: lines 131-133, 203-205
- `Modan2.py`: line 822

### 9.3 테스트 파일 작성

#### ✅ 자동화 테스트
**상태**: 완료

**파일**: `tests/test_object_overlay_persistence.py`

**테스트 항목**:
1. `test_initial_state_defaults_to_true` - 초기 상태 확인
2. `test_toggle_changes_state` - 토글 버튼 동작 확인
3. `test_overlay_stays_hidden_when_disabled` - auto-show OFF 시 숨김 유지
4. `test_overlay_shows_when_enabled` - auto-show ON 시 표시
5. `test_keyboard_shortcut_toggles_overlay` - Ctrl+P 단축키 동작
6. `test_preference_persists_to_config` - config 저장 확인
7. `test_preference_loads_from_config` - config 로드 확인
8. `test_dataset_switch_preserves_preference` - dataset 전환 시 설정 유지
9. `test_overlay_position_persists_across_selections` - 위치 유지 확인
10. `test_overlay_position_saved_to_config` - 위치 저장 확인
11. `test_overlay_position_loaded_from_config` - 위치 로드 확인
12. `test_overlay_uses_default_position_on_first_run` - 첫 실행 시 기본 위치

### 9.4 구현 결과

#### 동작 방식
1. **첫 실행 시**:
   - Preview overlay auto-show: ON (기본값)
   - Toolbar 버튼: 체크됨
   - Overlay 위치: 우하단 (기본값)

2. **사용자가 토글 버튼 클릭 (OFF로 전환)**:
   - Overlay 즉시 숨김
   - 버튼 아이콘: × → 👁 (눈 모양)
   - 버튼 색상: 빨간색 → 녹색
   - 다른 object 선택 시에도 overlay 나타나지 않음
   - 설정 자동 저장

3. **사용자가 overlay 드래그**:
   - 드래그 중: 마우스 커서 따라 이동
   - 마우스 놓으면: 가장 가까운 코너로 snap
   - 위치 자동 저장
   - 다른 object 선택 시 저장된 위치에 표시

4. **애플리케이션 재시작**:
   - 저장된 auto-show 설정 복원
   - Toolbar 버튼 상태 복원
   - Overlay 위치 복원

#### Config 파일 예시
```json
{
  "ui": {
    "object_overlay_auto_show": false,
    "object_overlay_position": [0, 1027]
  }
}
```

### 9.5 해결된 이슈

1. ✅ **원래 요청사항**: "make it invisible should be more persistent"
   - overlay를 숨기면 세션 동안 유지됨
   - 매번 object 선택 시 다시 나타나지 않음

2. ✅ **추가 개선**:
   - 키보드 단축키로 빠른 토글
   - 툴바 버튼으로 접근성 향상
   - 설정 영구 저장으로 재시작 후에도 유지
   - Overlay 위치 저장으로 사용자 레이아웃 유지

### 9.6 남은 작업

없음. 모든 계획된 기능이 구현되고 테스트되었습니다.

### 9.7 관련 커밋

- 추후 커밋 시 해시 추가 예정
