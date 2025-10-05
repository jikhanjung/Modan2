# Reset Pose 즉시 반영 및 기하 복원 개선

**작업일**: 2025-09-05
**작업자**: Codex CLI Assistant
**관련 문서**: `20250905_032_reset_pose_button_issues.md`, `20250905_033_reset_pose_fix_plan.md`

## 문제 요약

- Data Exploration Dialog에서 Reset Pose 버튼 클릭 시, 메인 3D 뷰와 썸네일(Shape Grid)에서 포즈가 즉시 원복되지 않음.
- 그래프에서 다른 점을 클릭하거나 특정 상호작용 이후에만 원복된 상태가 반영되는 지연 현상 발생.

## 원인 분석

1) 즉시 렌더링 미발생(QGLWidget 특성)
- `ObjectViewer3D`는 `QGLWidget` 기반이며, 뷰 갱신에는 `updateGL()` 호출이 보다 직접적임.
- 기존 수정안은 `reset_pose()` 내부에서 `self.update()`를 호출하도록 했으나, 이는 OpenGL 경로에서 즉시 `paintGL()`을 보장하지 못함.

2) 회전 누적이 실제 기하(landmark_list)에 반영됨
- 마우스 드래그 회전 동작은 `MdObjectOps.rotate_3d(...)` 및 `MdObjectOps.apply_rotation_matrix(...)`를 통해 객체의 `landmark_list`에 영구적(세션 내)으로 반영됨.
- `reset_pose()`에서 뷰 변수(`rotate_x/y`, `pan`, `dolly`)와 내부 `rotation_matrix`만 초기화할 경우, 이미 변형된 landmark 좌표는 그대로여서 화면이 초기 상태로 돌아오지 않음.

## 변경 사항

대상 파일: `ModanComponents.py`

- `ObjectViewer3D.reset_pose` 로직 보강:
  - 뷰 상태 변수 초기화: `rotate_*`, `temp_rotate_*`, `pan_*`, `temp_pan_*`, `dolly`, `temp_dolly` 초기화 유지.
  - 내부 회전 행렬 초기화: `rotation_matrix = I` 유지.
  - 기하 복원:
    - OBJECT_MODE이고 `self.object`가 존재하면 `self.set_object(self.object)` 호출로 `obj_ops` 및 그 파생 상태를 원본 `MdObject` 기준으로 재구성 → 누적 회전으로 변형된 좌표 복원.
    - 그 외(예: DATASET_MODE)는 `self.align_object()`로 기준선 정렬만 수행(필요시 추후 DS 복원 확장 고려).
  - GL 캐시 무효화: `gl_list` 삭제 후 None 설정 유지.
  - 즉시 리프레시: `self.update()` 대신 `self.updateGL()` 호출로 OpenGL 경로에서 즉시 재도화 유도.

핵심 패치 요지:

```python
# ModanComponents.py::ObjectViewer3D.reset_pose
# ... 상태변수/행렬 초기화 ...
if self.data_mode == OBJECT_MODE and getattr(self, 'object', None) is not None:
    self.set_object(self.object)  # 원본 MdObject로부터 ops 재구성 → 기하 복원
else:
    self.align_object()           # DS 모드 등에서는 기준선 정렬만 수행

# GL 리스트 무효화 후
self.updateGL()                   # 즉시 GL 리페인트 보장
```

## 기대 효과

- 메인 3D 뷰: Reset Pose 클릭 직후 즉시 원복된 포즈로 렌더링됨.
- Shape Grid 썸네일(3D): 각 뷰가 자체 `reset_pose()` 수행 시 기하 복원 + 즉시 리페인트가 이루어져 지연 없이 원복 표시.
- 외부 컨텍스트에서의 강제 `repaint()` 호출 필요 없음(위젯 자체가 책임 보유).

## 검증 방법

1) Exploration 모드에서 3D 뷰를 임의로 회전/이동/줌한 뒤, Reset Pose 버튼 클릭 → 즉시 초기 포즈로 복귀.
2) Shape Grid 표시 상태에서 동일 동작 수행 → 썸네일 또한 즉시 초기 포즈로 복귀.
3) 그래프에서 추가 클릭 등의 상호작용 없이도 결과가 즉시 반영되는지 확인.

## 한계 및 후속 과제

- DATASET_MODE에서는 현재 `align_object()`만 수행하므로, 세션 중 누적된 변형을 완전히 되돌리려면 `ds_ops`도 초기 상태에서 재구성하는 추가 루틴이 유용할 수 있음. 필요 시 `set_ds_ops(...)` 경로를 통한 DS 재빌드 옵션을 검토.
- 2D 뷰(`ObjectViewer2D`)는 회전 누적을 좌표에 반영하지 않으므로 기존 `calculate_resize()` 중심의 리셋으로 충분함.

## 변경 이력

- 파일: `ModanComponents.py`
- 메서드: `ObjectViewer3D.reset_pose`
- 주요 변경: 기하 복원(`set_object(self.object)`), GL 즉시 리페인트(`updateGL()`), 예외시 `align_object()` 폴백 유지, GL 캐시 무효화 유지.
