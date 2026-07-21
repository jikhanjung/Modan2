# 2D 뷰어 줌 스케일 클램프 (OOM 근본 수정)

## 날짜
2026-07-21

## 문제

`ObjectViewer2D.adjust_scale`은 `scale > 1`일 때 `scale += floor(scale) * ratio`
로 커져 반복 줌인 시 사실상 지수적으로 증가하고, 매 호출마다 scale에 비례하는
크기의 `curr_pixmap`을 새로 할당한다. 상한이 없어서 휠 줌 연타만으로 수 GB
할당을 시도할 수 있었다 — WSL 테스트 스위트를 죽인 OOM(devlog 220)의 근본
원인이 바로 이 패턴이었다.

## 수정

`MAX_SCALED_PIXMAP_DIM = 8192`: 렌더 픽스맵의 긴 변 상한 (RGBA 최악
~256MB). `adjust_scale`에서 scale 갱신 직후, 결과 픽스맵의 긴 변이 상한을
넘지 않도록 scale을 클램프한다:

```python
max_scale = MAX_SCALED_PIXMAP_DIM * self.image_canvas_ratio / longer_side
max_scale = max(1.0, math.floor(max_scale * 10) / 10)  # 0.1 격자 유지, fit 미만 금지
```

- 상한 아래의 일반 줌 동작은 완전히 동일.
- 상한 도달 시 scale이 고정될 뿐 다른 부작용 없음 (pan 보정은 실제 적용된
  scale로 계산되므로 일관).

## 테스트

`tests/test_viewer_zoom_clamp.py`: OOM 시나리오였던 60연속 줌인이 상한에서
멈추는지(픽스맵 치수·scale 모두), 상한 아래 줌은 기존과 동일한지, 상한이
fit 크기보다 작아도 fit 미만으로 줄지 않는지.

devlog 220에서 "재도입 시 반드시 scale clamp"라고 적었던 항목의 이행이며,
downscale 기능 재도입 여부와 무관하게 유효한 수정이다.
