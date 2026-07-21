# Show estimate: 결측 랜드마크 추정에 회전 정합 추가

## 날짜
2026-07-21

## 문제

ObjectDialog의 "show estimate"(결측 랜드마크 추정 표시)가 실제 데이터에서
엉뚱한 위치에 추정점을 그렸다. 원인은 회전 미정합으로 확인됨.

`estimate_missing_for_object`는 두 단계로 동작한다:

1. 결측 없는 표본들로 Procrustes superimposition → 평균형(aligned mean) 계산.
   여기까지는 정상.
2. 그 평균형을 현재 객체에 맞춘 뒤 결측 위치를 가져오는데, 이 정합이
   **centroid 위치 + centroid size(스케일)만** 맞추고 **회전을 전혀 맞추지
   않았다**. 평균형은 Procrustes 정렬 좌표계의 방향을 갖고, 객체는 이미지
   좌표계(촬영된 방향 그대로)에 있으므로, 표본이 기울어져 찍혀 있으면
   추정점이 실제 위치에서 회전각만큼 어긋난 곳에 표시됐다.

부수 버그: 정합용 대응점 수집 시 `current_valid`는 객체 기준 유효 인덱스
전부, `mean_valid`는 "평균형도 유효한" 인덱스만 담아 두 배열이 어긋날 수
있었다(평균형에 결측/개수 차이가 있는 경우 centroid·scale이 오염됨).

## 수정 (`dialogs/object_dialog.py`)

- 대응점을 **객체와 평균형 모두 유효한 인덱스**에서 짝지어 수집 (index-aligned).
- 정합을 similarity transform (회전 + 스케일 + 이동)으로 확장:
  - 회전은 공유 유효 랜드마크에 대한 **Kabsch (orthogonal Procrustes)**,
    reflection 제외 (`det` 부호 보정).
  - 결측점 변환: `R @ (mean_lm - mean_centroid) * scale + current_centroid`.
- 로그에 회전각(deg) 추가.

분석 파이프라인(`MdModel.procrustes_superimposition_with_imputation` — 정렬
공간에서 반복적 평균형 대입)은 건드리지 않았다. 표시용 추정과 분석용 대입이
별개 구현이라는 점은 여전하며, 필요하면 추후 통일 검토.

## 테스트

`tests/test_estimate_missing_landmarks.py` (신규, 10개):

- 0°/30°/90°/-45°/180° 회전 + 스케일 + 이동을 가한 표본에서 결측 랜드마크가
  참값 위치로 복원되는지 (atol 1e-6) — 회전 미정합이면 즉시 실패하는 케이스.
- 평균형 쪽이 결측인 인덱스는 정합에서 제외되고 추정 대상도 아님 (짝 맞춤
  버그의 회귀 테스트).
- 유효점 부족 / 결측 없음 / None 객체의 기존 fallback 동작 유지.

관련 스위트(add_missing, unimputable, procrustes_missing, object_dialog_modes,
object_workflows) 63개 통과, 전체 스위트 통과 확인.
