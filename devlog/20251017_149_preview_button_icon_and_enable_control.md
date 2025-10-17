# Preview 버튼 아이콘 추가 및 활성화 제어

- **문서 번호:** 20251017_148
- **작성일:** 2025-10-17
- **작성자:** Claude
- **관련 문서:** [20251016_P01 Object Preview Overlay Persistence](./20251016_P01_object_preview_overlay_persistence.md)
- **관련 커밋:** `d8af1c7`

## 1. 작업 개요

어제(10/16) 구현한 Preview overlay 기능의 후속 작업으로, Preview 툴바 버튼에 아이콘을 추가하고 버튼 활성화 제어 로직을 개선했습니다.

## 2. 작업 내용

### 2.1 Preview 아이콘 추가

**문제점:**
- Preview 툴바 버튼이 빈 아이콘(`QIcon()`)으로 표시되어 시각적으로 불명확
- 다른 툴바 버튼들은 모두 아이콘이 있지만 Preview만 없어 일관성 부족

**해결 방법:**
1. `icons/Preview.png` 파일 추가 (99,354 bytes)
2. `MdConstants.py`의 `ICONS` 딕셔너리에 preview 아이콘 등록
3. `Modan2.py`에서 Preview 버튼이 아이콘 사용

**변경 사항:**

```python
# MdConstants.py (line 62-63)
ICONS = {
    # ... existing icons ...
    # Preview
    "preview": str(ICONS_DIR / "Preview.png"),
}
```

```python
# Modan2.py (line 149)
# Before:
self.actionTogglePreview = QAction(QIcon(), self.tr("Preview"), self)

# After:
self.actionTogglePreview = QAction(QIcon(ICON_CONSTANTS["preview"]), self.tr("Preview"), self)
```

### 2.2 Preview 버튼 활성화 제어

**문제점:**
- Preview 버튼이 항상 활성화되어 있어서, dataset이 선택되지 않았을 때도 클릭 가능
- 다른 dataset 관련 버튼들(New Object, Export, Analyze 등)은 dataset 선택 시에만 활성화되는데 Preview만 예외
- Analysis가 선택되었을 때도 Preview 버튼이 활성화되어 있어 일관성 부족

**해결 방법:**
Preview 버튼을 다른 dataset 관련 버튼들과 동일하게 취급하여, dataset 선택 시에만 활성화되도록 수정

**변경된 위치:**

1. **초기화 시** (line 224):
```python
# Initialize button states - disabled until dataset/object is selected
self.actionNewObject.setEnabled(False)
self.actionEditObject.setEnabled(False)
self.actionExport.setEnabled(False)
self.actionAnalyze.setEnabled(False)
self.actionCellSelection.setEnabled(False)
self.actionRowSelection.setEnabled(False)
self.actionAddVariable.setEnabled(False)
self.actionTogglePreview.setEnabled(False)  # ← 추가
```

2. **Dataset 선택 시** (line 303, 1721):
```python
# Enable column mode buttons for dataset
self.actionCellSelection.setEnabled(True)
self.actionRowSelection.setEnabled(True)
self.actionAddVariable.setEnabled(True)
self.actionTogglePreview.setEnabled(True)  # ← 추가
```

3. **Analysis 선택 시** (line 317, 1734):
```python
# Disable all dataset-related buttons when analysis is selected
self.actionCellSelection.setEnabled(False)
self.actionRowSelection.setEnabled(False)
self.actionAddVariable.setEnabled(False)
self.actionTogglePreview.setEnabled(False)  # ← 추가
```

4. **선택 없을 때** (line 1763):
```python
# Disable all dataset/analysis related buttons
self.actionAnalyze.setEnabled(False)
self.actionNewObject.setEnabled(False)
self.actionEditObject.setEnabled(False)
self.actionExport.setEnabled(False)
self.actionCellSelection.setEnabled(False)
self.actionRowSelection.setEnabled(False)
self.actionAddVariable.setEnabled(False)
self.actionTogglePreview.setEnabled(False)  # ← 추가
```

5. **on_dataset_selected_from_tree 헬퍼 메서드** (line 294, 303):
```python
def on_dataset_selected_from_tree(self, dataset):
    if dataset is None:
        # ... disable buttons ...
        self.actionTogglePreview.setEnabled(False)  # ← 추가
    else:
        # ... enable buttons ...
        self.actionTogglePreview.setEnabled(True)  # ← 추가
```

6. **on_analysis_selected_from_tree 헬퍼 메서드** (line 317):
```python
def on_analysis_selected_from_tree(self, analysis):
    if analysis:
        # Disable all dataset-related buttons when analysis is selected
        self.actionTogglePreview.setEnabled(False)  # ← 추가
```

## 3. 구현 결과

### 3.1 Preview 버튼 상태 변화

| 상황 | Preview 버튼 상태 | 다른 Dataset 버튼 상태 |
|------|------------------|---------------------|
| 앱 시작 (선택 없음) | ❌ Disabled | ❌ Disabled |
| Dataset 선택 | ✅ Enabled | ✅ Enabled |
| Analysis 선택 | ❌ Disabled | ❌ Disabled |
| Dataset 선택 해제 | ❌ Disabled | ❌ Disabled |

### 3.2 UI 일관성 개선

**Before:**
- Preview 버튼: 항상 활성화 (불일치)
- New Object, Export, Analyze: Dataset 선택 시에만 활성화

**After:**
- 모든 dataset 관련 버튼이 동일한 규칙으로 활성화/비활성화
- UI 동작이 직관적이고 예측 가능

### 3.3 사용자 경험 개선

1. **명확한 컨텍스트:**
   - Dataset이 없을 때 Preview 버튼이 비활성화되어 있어서, 사용자가 먼저 dataset을 선택해야 한다는 것을 시각적으로 알 수 있음

2. **실수 방지:**
   - Dataset이 선택되지 않은 상태에서 Preview 버튼을 클릭하는 실수 방지

3. **일관된 UX:**
   - 다른 dataset 관련 기능들과 동일한 활성화 패턴으로 학습 곡선 감소

## 4. 수정된 파일

### 4.1 MdConstants.py
```diff
@@ -59,6 +59,8 @@ ICONS = {
     # Selection types
     "cell_selection": str(ICONS_DIR / "cell_selection.png"),
     "row_selection": str(ICONS_DIR / "row_selection.png"),
+    # Preview
+    "preview": str(ICONS_DIR / "Preview.png"),
 }
```

### 4.2 Modan2.py
- Line 149: Preview 버튼 아이콘 적용
- Line 224: 초기화 시 disabled
- Line 294, 303: on_dataset_selected_from_tree에서 enable/disable
- Line 317: on_analysis_selected_from_tree에서 disable
- Line 1721: Dataset 선택 시 enable
- Line 1734: Analysis 선택 시 disable
- Line 1763: 선택 없을 때 disable

### 4.3 icons/Preview.png
- 새 파일 추가 (99,354 bytes)
- PNG 형식 아이콘

## 5. 테스트 결과

### 5.1 수동 테스트

| 테스트 케이스 | 결과 |
|-------------|------|
| 앱 시작 시 Preview 버튼 상태 | ✅ Disabled |
| Dataset 선택 후 Preview 버튼 상태 | ✅ Enabled |
| Analysis 선택 후 Preview 버튼 상태 | ✅ Disabled |
| Preview 버튼 클릭 시 동작 (Dataset 선택됨) | ✅ 정상 토글 |
| Preview 버튼 아이콘 표시 | ✅ 정상 표시 |

### 5.2 엣지 케이스

| 케이스 | 동작 | 결과 |
|-------|------|------|
| Dataset 선택 → Analysis 선택 | Preview 버튼 비활성화 | ✅ Pass |
| Analysis 선택 → Dataset 선택 | Preview 버튼 활성화 | ✅ Pass |
| Dataset 삭제 후 | Preview 버튼 비활성화 | ✅ Pass |

## 6. 관련 이슈 및 커밋

### 6.1 이슈
- GitHub Issue #14: Object preview widget visibility
- 이전 작업(10/16): Preview overlay persistence 기능 구현 (20251016_P01)

### 6.2 커밋
```
commit d8af1c762ef6368960579dfe44dbb436f2ddda38
Author: Jikhan Jung <honestjung@gmail.com>
Date:   Fri Oct 17 12:08:04 2025 +0900

    feat: Add Preview icon and enable only when dataset is selected

    - Add Preview icon (icons/Preview.png) to icon constants
    - Apply Preview icon to Preview toolbar button
    - Enable Preview button only when dataset is selected
    - Disable Preview button when analysis is selected or no selection

    This improves UI consistency by treating Preview button like other
    dataset-related buttons (New Object, Export, Analyze, etc.)
```

## 7. 향후 개선 사항

### 7.1 단기 (Optional)
- Preview 버튼 tooltip에 상태 정보 추가 ("No dataset selected" 등)
- Preview 버튼 아이콘 hover 상태 디자인 개선

### 7.2 장기 (Future Enhancement)
- Analysis 선택 시에도 analysis 결과를 미리보기할 수 있도록 확장
- Preview 버튼에 드롭다운 메뉴 추가 (2D/3D 전환 등)

## 8. 참고사항

### 8.1 디자인 결정
- Preview 버튼을 dataset 관련 버튼으로 분류한 이유:
  - Preview 기능이 dataset의 object를 표시하는 기능이므로 dataset 컨텍스트가 필요
  - 다른 dataset 관련 버튼들과 동일한 활성화 패턴을 따르는 것이 UI 일관성 측면에서 바람직

### 8.2 영향 범위
- 기존 기능에 영향 없음 (Backward compatible)
- UI 일관성 개선으로 사용자 경험 향상
- 추가 테스트 케이스 불필요 (기존 테스트로 커버됨)

## 9. 결론

Preview 버튼에 아이콘을 추가하고 활성화 제어 로직을 개선하여:
1. 시각적 일관성 확보
2. UI 동작의 예측 가능성 향상
3. 사용자 실수 방지
4. 전체적인 UX 품질 개선

이 작업은 어제(10/16) 구현한 Preview overlay persistence 기능의 완성도를 높이는 후속 작업으로, 두 작업을 통해 Preview 기능이 완전하고 일관된 사용자 경험을 제공하게 되었습니다.
