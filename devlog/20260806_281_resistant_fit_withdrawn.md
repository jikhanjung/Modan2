# Resistant Fit 철회 — 수렴하지 않고 발산한다

## 날짜
2026-08-06

## 한 일

1. 분석 다이얼로그의 중첩(superimposition) 선택지에서 Resistant Fit 제거.
   남은 것은 Procrustes, Bookstein 둘.
2. `_prepare_landmarks` 는 요청받으면 **거부한다.** Procrustes 로 대체하지
   않는다 — 부른 이름과 다른 중첩을 돌려주는 셈이기 때문이다.
3. 구현체 자체는 `MdModel` 에 남긴다. 한계를 docstring 에 적었고 모델 수준
   테스트도 그대로 둔다. 고칠 사람을 위한 것이다.
4. 매뉴얼 네 곳(`advanced_features` / `faq` / `troubleshooting` / `user_guide`)
   정정. 낡은 매뉴얼은 0.2.0-beta.1 한 릴리스를 통째로 쓴 문제다.

## 왜 — 반복이 수렴하지 않는다

시험한 모든 데이터셋 크기에서 100회 상한을 다 쓰고 끝났다. 그리고 **상한을
올리면 답이 가까워지는 게 아니라 멀어졌다.** 랜드마크 10개짜리 표본 5개 기준,
상한을 5→10 으로 올렸을 때 좌표가 1.96, 10→20 에서 3.94, 20→40 에서 10.41
움직였다. 수렴한 유일한 경우는 테스트가 쓰는 삼각형 두 개짜리 사례인데,
한 형상이 다른 형상의 정확한 닮음 변환이라 애초에 반복할 것이 없다.

코드에서 보이는 원인은 둘이다. 형상을 단위 크기로 정규화하지 않아
`convergence_threshold` 가 원자료 단위와 비교되므로 사실상 도달할 수 없고,
반복 중앙값 기반의 크기·각도 추정이 극한 순환(limit cycle)에 빠지는 것으로
보인다.

비용만으로도 독립적으로 탈락한다. `_resistant_scale` 과
`_repeated_median_angle` 은 모든 랜드마크 쌍을 도는 순수 파이썬 O(n²) 루프이고,
이것을 매 반복마다 모든 형상에 대해 돌린다. 3D 회전은 그 안에 최대 100회를 더
중첩한다. 222표본 × 72랜드마크 데이터셋은 시간 단위로 외삽되고, 직접 재보려던
두 번의 시도를 22분·19분에서 포기했다.

## 뒤늦게 고친 것 — dialog 테스트가 같이 안 바뀌었다

위 작업 커밋(`2578707`)이 `tests/test_controller.py` 는 갱신했지만
`tests/dialogs/test_analysis_dialog.py` 를 빠뜨려 **main 이 3개 실패로
빨간불이었다** (러너 세 개 전부).

- `test_superimposition_methods` — 콤보 항목 수 기대값 3 → 2
- `test_all_methods_enabled_for_{2d,3d}_dataset` — `model.item(2)`(Resistant
  Fit)가 `None` 이 되어 `AttributeError`. 해당 단언 제거, 3D 쪽에는
  "제공되지 않는다" 를 명시적으로 확인하는 `count() == 2` 를 대신 넣었다.

이 두 테스트는 원래 *"Resistant Fit 이 2D·3D 양쪽에서 선택 가능하다"* 를
지키려고 있던 것이라, 지킬 대상이 사라진 자리에 남은 두 방법의 활성 여부
확인만 남겼다.

## 남아 있는 문자열 참조 (통과하지만 알아 둘 것)

- `tests/test_multi_analysis_workflow.py:369` — `"Resistant Fit"` 을
  `MdAnalysis.superimposition_method` 에 **라벨로만** 저장한다. 중첩을 실행하지
  않으므로(원자료로 바로 PCA) 통과한다.
- `dialogs/export_dialog.py:141` `rbRFTRA` — 라디오 버튼이 있지만
  `setEnabled(False)` 다. `rbBookstein` 도 마찬가지로 비활성이며, 둘 다 이번
  변경 이전부터 그랬다.
