# Reset Pose 버튼 문제 해결 계획

**작업일**: 2025-09-05
**작업자**: Gemini
**관련 문서**: `20250905_032_reset_pose_button_issues.md`

## 문제 분석 요약

`Reset Pose` 버튼 클릭 시, `ObjectViewer3D` 위젯의 상태 변수는 정상적으로 초기화되지만, 뷰가 즉시 갱신되지 않는 문제가 있다. 현재 구현은 외부 컨텍스트(Dialog)에서 `repaint()`를 호출하여 뷰 갱신을 시도하고 있으나, 이는 불안정하며 Qt의 이벤트 루프에 의해 즉시 처리되지 않는 것으로 보인다.

## 해결 전략

위젯 외부에서 강제로 렌더링을 지시하는 대신, **위젯 스스로가 자신의 상태 변경을 인지하고 뷰 갱신을 요청**하도록 책임을 위임한다. 이는 Qt 프레임워크의 표준 설계 원칙에 부합하며, 코드의 안정성과 캡슐화를 높인다.

## 수정 계획

### 1. `ModanComponents.py`의 `ObjectViewer3D` 클래스 수정

`reset_pose` 메서드가 내부 상태를 변경한 후, 스스로 뷰를 갱신하도록 `self.update()`를 호출한다.

- **파일**: `ModanComponents.py`
- **클래스**: `ObjectViewer3D`
- **메서드**: `reset_pose`
- **변경 사항**: 메서드 마지막에 `self.update()` 호출 추가

```python
# To-Be: ObjectViewer3D.reset_pose
def reset_pose(self):
    # ... 모든 pose 관련 변수 초기화 ...

    self.align_object()

    # GL display list가 있다면 무효화
    if hasattr(self, 'gl_list') and self.gl_list is not None:
        gl.glDeleteLists(self.gl_list, 1)
        self.gl_list = None

    # 위젯 스스로 뷰 갱신을 예약
    self.update()
```

### 2. `ModanDialogs.py`의 `DataExplorationDialog` 클래스 수정

`ObjectViewer3D`가 스스로 뷰를 갱신하므로, Dialog에서는 더 이상 `repaint()`를 호출할 필요가 없다. 해당 코드를 제거하여 책임을 명확히 분리한다.

- **파일**: `ModanDialogs.py`
- **클래스**: `DataExplorationDialog`
- **메서드**: `Reset Pose` 버튼의 클릭 핸들러
- **변경 사항**: `shape_view.repaint()` 및 `view.repaint()` 호출 제거

```python
# To-Be: DataExplorationDialog의 리셋 로직
# ...
for shape_view in self.shape_view_list:
    shape_view.reset_pose()  # repaint() 호출 제거

# ...
for key in self.shape_grid.keys():
    view = self.shape_grid[key]['view']
    if view:
        view.reset_pose()  # repaint() 호출 제거
```

## 기대 효과

1.  **안정적인 뷰 갱신**: Qt의 이벤트 루프를 통해 렌더링이 안정적으로 예약 및 실행된다.
2.  **코드 구조 개선**: 위젯의 상태와 뷰에 대한 책임이 `ObjectViewer3D` 클래스 내부로 캡슐화된다.
3.  **단순화**: 외부에서의 불필요한 렌더링 제어 코드가 제거되어 로직이 단순해진다.

## 다음 단계

Claude Code Assistant가 이 계획에 따라 코드를 수정한다.
