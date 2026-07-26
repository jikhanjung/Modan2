# Bookstein / Resistant Fit에 결측 랜드마크 임퓨테이션 통합

## 날짜
2026-07-26

## 배경

[[20260726_251_bookstein_superimposition_implementation]]와
[[20260726_253_resistant_fit_3d]]에서 Bookstein/Resistant Fit을 살렸지만,
둘 다 **결측 랜드마크는 명확한 오류로 거부**하고 Procrustes를 쓰라고 안내했다.
Procrustes는 이미 EM 임퓨테이션(`procrustes_superimposition_with_imputation`,
devlog 227)을 갖고 있어, 같은 인프라를 두 방식에도 붙인다.

## 접근

핵심: **필요 시 먼저 임퓨테이션으로 gap을 채워 완전한 형상을 만든 뒤, 그 위에서
Bookstein/RF를 돌린다.** 임퓨테이션 품질은 검증된 Procrustes EM(평균 형상을 각
객체의 관측 랜드마크에 맞춰 채우고 정렬이 안정될 때까지 refine)에서 오고, 최종
정합은 Bookstein/RF가 담당한다. gap 채운 값은 각 객체 프레임에서 내부적으로
일관되므로, Bookstein/RF의 per-object 유사변환이 그 위에서 올바르게 동작한다.

## 변경

### `MdDatasetOps._fill_missing_landmarks()` (신규 공유 헬퍼)
- 결측이 없으면 no-op.
- 있으면 `procrustes_superimposition_with_imputation()`로 in-place 채움.
- 채운 뒤에도 non-finite(None/NaN)가 남으면(= 모든 객체에서 빠진 랜드마크,
  임퓨테이션 불가) 명확한 `ValueError`. 실제 분석 경로에서는 컨트롤러의
  `find_unimputable_landmarks` 게이트가 이 경우를 먼저 걸러낸다.

### Bookstein / Resistant Fit
- 기존 "결측이면 raise" 블록을 `self._fill_missing_landmarks()` 호출로 교체.
- 완전 데이터 경로는 그대로(결측 없으면 헬퍼가 no-op라 추가 비용 없음).
- Bookstein은 baseline 존재 확인을 먼저 하고(설정 오류는 fail-fast), 그 다음 채움.

## 테스트

- `test_bookstein_imputes_missing_landmarks`: 한 객체가 비-baseline 랜드마크를
  빠뜨려도 임퓨테이션 후 성공하고 baseline이 표준 위치에 매핑되며 결과에 None/NaN
  없음.
- `test_resistant_fit_imputes_missing_landmarks`: 결측 객체가 채워져 (동일 형상
  3개가) 정렬 후 일치.
- 컨트롤러 dispatch 테스트를 spy 기반으로 갱신(결측 거부에 기대던 부분 제거).

## 결과

- 관련 스위트 432 passed, 2 skipped. `ruff`/`format` 클린, Sphinx 경고 없음.
- 이제 세 정합 방식 모두 결측 랜드마크를 동일한 EM 임퓨테이션으로 처리한다
  (2D/3D 공통). 남아있던 유일한 제약이 해소됐다.

## 정합 방식 최종 상태

| 방식 | 2D | 3D | 결측 랜드마크 |
|------|----|----|--------------|
| Procrustes | ✅ | ✅ | 임퓨테이션 |
| Bookstein | ✅ | ✅ | 임퓨테이션 (baseline 필요) |
| Resistant Fit | ✅ | ✅ | 임퓨테이션 |
