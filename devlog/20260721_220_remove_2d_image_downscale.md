# 2D 뷰어 이미지 다운스케일링 기능 제거 (revert)

## 날짜
2026-07-21

## 결정
`f6c684c` (perf: Downscale oversized images in the 2D viewer)와
`252cad6` (perf: Load full-resolution image lazily when zooming in the 2D viewer)
두 커밋을 revert하여 ObjectViewer2D의 오버사이즈 이미지 다운스케일링 기능과
해당 테스트(`tests/test_object_viewer_2d_image_scaling.py`)를 제거했다.

## 배경: WSL에서 pytest가 OOM으로 죽던 문제

WSL(RAM 7.8GB)에서 전체 테스트 스위트를 돌리면 커널 OOM killer가 python을
죽였다. 조사 결과:

- 테스트별 RSS를 기록해 보면 전체 스위트는 약 780MB 수준에서 안정적이었다.
  (다이얼로그 계열 테스트가 테스트당 15~46MB씩 누적하는 별도 문제는 있음 —
  `tests/dialogs/test_data_exploration_scatter.py` +110MB,
  `test_export_dialog.py` +69MB 등. 이건 OOM의 직접 원인은 아니었다.)
- 실제 OOM은 `test_object_viewer_2d_image_scaling.py::test_zoom_in_loads_full_resolution`
  한 개 테스트에서 발생했다. 커널 로그: `Out of memory: Killed process (python)
  total-vm:16357988kB, anon-rss:6666552kB`.

### OOM 메커니즘

`test_zoom_in_loads_full_resolution`은 `adjust_scale(0.2, recurse=False)`를
60회 반복 호출한다. `adjust_scale`은 `scale > 1`이면
`scale += floor(scale) * 0.2`로 커져 사실상 지수적으로 증가하고
(60회 반복 시 scale이 수만 배), 매 호출마다

```python
self.curr_pixmap = self.orig_pixmap.scaled(
    int(self.orig_width * self.scale / self.image_canvas_ratio), ...)
```

로 scale에 비례하는 QPixmap을 새로 할당한다. scale이 폭주하면 수 GB짜리
픽스맵 할당을 시도하다 프로세스가 OOM으로 죽는다.

참고: `scale`에 비례해 `curr_pixmap`을 할당하는 코드는 이 기능 이전부터
있었다(줌 상한 없음). 이 기능이 새로 만든 문제라기보다는, 60회 연속 줌인하는
새 테스트가 기존의 "줌 스케일 무제한 + 스케일 비례 픽스맵 할당" 문제를
증폭시켜 드러낸 것이다. 나중에 어떤 형태로든 줌 상한(예: scale clamp)을
넣는 것이 근본 해결책이다.

## 다시 넣을 때 참고

- 기능 복원: `git revert <이번 revert 커밋>` 또는 `f6c684c`, `252cad6`의
  diff를 참조해 재적용.
- 원래 기능 설계 기록: `devlog/20260718_209_large_image_downscale.md`
  (그리고 252cad6 커밋 메시지) — MAX_RENDER_DIM=2560,
  QImageReader.setScaledSize 기반 다운스케일 디코드, TRUE 픽셀 좌표 유지,
  줌인 시 full-resolution 지연 로드.
- 재도입 시 반드시 함께 할 것:
  1. `adjust_scale`에 scale 상한(clamp) 추가 — 픽스맵 할당 크기가 뷰포트
     기준 상수 배를 넘지 않도록.
  2. 줌 테스트는 고정 횟수 반복 대신 목표 scale을 직접 설정하는 방식으로
     작성해 거대 할당을 유발하지 않게 할 것.
