# 2D 뷰어 픽스맵 보간을 SmoothTransformation으로 (R03 항목 3)

## 날짜
2026-07-21

## 배경

`ObjectViewer2D`가 화면에 그릴 픽스맵을 만들 때 `QPixmap.scaled()`에 보간
모드를 지정하지 않아 Qt 기본값인 `Qt.FastTransformation`(최근접 이웃)이
적용되고 있었다. 축소 시 픽셀을 그냥 버리므로 계단현상이 생기고, 미세한 구조
위에 랜드마크를 찍을 때 불리하다.

R03에서는 "Show Original 성능 피드백과 함께 조정"으로 미뤄 뒀는데, 실제로
측정해 보니 우려했던 비용 구조가 직관과 반대였다.

## 측정 (오프스크린, 호출당 평균)

| 상황 | Fast | Smooth | 배율 |
|---|---|---|---|
| 2560×1920 → 1200×900 (일반적인 맞춤 축소) | 4.0 ms | 5.5 ms | 1.4x |
| 6000×4000 원본 → 1200×800 (Show Original 축소) | 4.8 ms | 13.6 ms | 2.8x |
| 2560×1920 → 2배 확대 | 102 ms | **37 ms** | 0.4x |
| 6000×4000 → 8192px 상한 확대 | 354 ms | **117 ms** | 0.3x |

축소는 smooth가 1.4~2.8배 느리지만 절대값이 5~14ms라 휠 한 틱에서 체감되지
않는다. 반대로 **확대는 smooth가 3배 가까이 빠르다** — Qt의 smooth 경로가 더
최적화되어 있다. 품질이 가장 아쉬운 축소에서 비용이 미미하고, 비용이 클 것
같던 확대에서 오히려 이득이라 미룰 이유가 없었다.

## 수정

`components/viewers/object_viewer_2d.py`의 두 호출 지점:

- `adjust_scale`(줌): 기존이 2인자 형태라 암묵적으로 `IgnoreAspectRatio`였다.
  동작을 바꾸지 않도록 `Qt.IgnoreAspectRatio`를 명시하고
  `Qt.SmoothTransformation`을 추가했다. 목표 박스가 이미 원본의 종횡비를
  갖고 있어 실질적으로 늘어나지 않는다.
- `calculate_resize`(창 맞춤/이미지 로드): 기존 `Qt.KeepAspectRatio` 유지 +
  `Qt.SmoothTransformation`.

표시 품질만 바뀌며 좌표 수학(`image_canvas_ratio`, 랜드마크 매핑)과는 무관하다.

## 참고

`dialogs/object_dialog.py:1334`에도 `scaled(...)`가 있으나 주석 처리된 죽은
코드다.
