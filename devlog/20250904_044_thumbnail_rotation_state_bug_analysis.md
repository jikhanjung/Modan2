# 썸네일 회전 상태 버그 분석 (Thumbnail Rotation State Bug Analysis)

- **Date**: 2025-09-04
- **Author**: Gemini (분석 담당)
- **Related**: `20250903_043_Thumbnail_overlay_perf_and_rotation_debug.md`

## 1. 개요 (Summary)

3차원 데이터셋 분석 화면에서, 메인 3D 뷰를 회전시킬 때 그래프의 썸네일들이 함께 회전하는 기능에 버그가 존재한다. 첫 번째 드래그-릴리즈 동작에서는 썸네일이 정상적으로 회전하지만, 두 번째 드래그를 시작하는 순간 썸네일의 회전 상태가 초기화되어 원래 방향으로 돌아가는 문제가 발생한다.

## 2. 근본 원인 분석 (Root Cause Analysis)

문제의 근본 원인은 **`ObjectViewer3D.set_object()` 메소드가 뷰어의 회전 상태를 강제로 초기화**하기 때문이다. 이 메소드는 매 드래그 동작이 끝날 때마다 불필요하게 호출된다.

**버그 발생 순서:**

1.  **첫 번째 드래그 종료 시:**
    -   `DataExplorationDialog.sync_rotation_with_deltas()`가 호출되어 메인 뷰의 최종 회전 상태를 `self.rotation_matrix`에 저장한다.
    -   고화질 썸네일을 그리기 위해 `_draw_shape_grid_thumbnails(live=False)`가 호출된다.
    -   이 메소드 내부에서 각 썸네일 뷰어(`view`)에 대해 `view.set_object(obj)`가 호출된다.
    -   `ModanComponents.py`에 정의된 `ObjectViewer3D.set_object()`는 내부적으로 `self.rotate_x = self.rotate_y = 0` 코드를 실행하여 해당 뷰어의 회전 각도를 0으로 리셋한다.
    -   직후 `view.apply_rotation(self.rotation_matrix)`가 호출되어 객체의 정점(vertex) 좌표를 직접 변환하므로, 겉보기에는 회전이 유지된 것처럼 보인다.

2.  **두 번째 드래그 시작 시:**
    -   사용자가 다시 메인 뷰를 드래그하면 `sync_temp_rotation`이 호출되어 회전 변화량(`temp_rotate_x/y`)을 썸네일 뷰어에 전달한다.
    -   썸네일 뷰어의 `paintGL` 메소드는 `self.rotate_x + self.temp_rotate_x` 와 같은 방식으로 최종 회전 각도를 계산한다.
    -   하지만 `self.rotate_x`와 `self.rotate_y`는 이미 `set_object`에 의해 0으로 초기화되었으므로, 이전 회전 상태가 무시되고 새로운 변화량만으로 회전을 시작한다.
    -   결과적으로 썸네일은 회전이 없는 초기 상태에서 다시 회전하게 되어, 사용자가 보기에는 회전이 리셋된 것처럼 보인다.

## 3. 해결 방안 제안 (Proposed Solution)

사용자의 제안대로, **`set_object`의 불필요한 호출을 막고 회전 상태가 보존되도록 하는 것**이 핵심이다.

1.  **주요 해결책: `set_object` 호출 로직 제거**
    -   `ModanDialogs.py`의 `_draw_shape_grid_thumbnails` 메소드에서, 고화질 렌더링(`live=False`) 분기 내에 있는 `shape_to_object`, `view.set_object(obj)` 등의 객체 재생성 관련 코드를 제거한다.
    -   썸네일 객체는 처음 생성될 때 한 번만 설정하고, 회전과 같은 뷰 업데이트 시에는 객체를 재생성하지 않고 기존 객체의 트랜스폼 정보만 수정하도록 한다.

2.  **구현 상세:**
    -   `_draw_shape_grid_thumbnails` 메소드에서 `live=False` 일 때도 `live=True` 모드와 유사하게, 이미 존재하는 `view` 객체의 상태를 그대로 사용해야 한다.
    -   `set_object` 호출을 제거하면 `view`의 내부 회전 각도(`rotate_x`, `rotate_y`)가 더 이상 초기화되지 않으므로, `_base_rotation`과 `temp_rotate_x/y`를 이용한 기존 회전 로직이 의도대로 동작하여 회전 상태가 누적 보존될 것이다.
    -   최종적으로 `view.apply_rotation(self.rotation_matrix)`를 호출하여 고화질 렌더링 시 정점 위치를 정확하게 업데이트하는 로직은 유지한다.

## 4. 기대 효과 (Expected Outcome)

-   썸네일 회전이 드래그 동작 간에 초기화되는 버그가 해결된다.
-   불필요한 객체 재생성 및 설정 과정을 제거하여 애플리케이션의 반응성과 성능이 소폭 개선된다.
