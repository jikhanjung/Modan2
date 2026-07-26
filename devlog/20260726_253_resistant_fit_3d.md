# Resistant Fit 3D 확장 — 좌표평면 repeated-median 회전

## 날짜
2026-07-26

## 배경

[[20260726_252_resistant_fit_rewrite_2d]]에서 2D RFTRA를 구현하고 3D는 "회전
추정이 복잡하다"며 범위에서 제외했다(3D 데이터셋 거부, UI 비활성). 후속으로 3D를
마저 살린다.

3D의 어려움은 **회전**이다: 2D 회전은 스칼라 각도라 pairwise 각도차의 repeated
median이 곧 회전이지만, 3D 회전은 단일 "median 각도"가 없다. 스케일(거리비)과
평행이동(좌표별 median)은 차원 무관하게 그대로 쓸 수 있다.

## 접근

**좌표평면 분해 + 좌표하강(coordinate descent).** 3D 회전을 Z→Y→X 축 회전의
반복으로 추정한다:

- 각 축에 대해, 그 축에 수직인 평면으로 pairwise edge를 사영하고 2D와 동일한
  repeated-median 각도를 구해 그 축으로 회전.
- Z, Y, X를 한 번씩 도는 sweep을 각도 합이 0에 수렴할 때까지 반복. 형상이 완전히
  정렬되면 모든 평면 각도가 0 → 고정점이므로, 반복이 그 정렬로 수렴한다.

2D는 이 틀의 특수 경우(Z 축 1회)라, `_resistant_align`으로 2D/3D를 통합했다.
스케일은 `_resistant_scale`, 평면 각도는 `_repeated_median_angle(u, w)`, 축 회전은
`_axis_rotation_3d`로 분리.

## 검증 (핵심)

구현 전/후로 순수 수학을 직접 검증했다(무작위 시드 고정):

- **3D 정확 복원**: 임의의 (회전·스케일·평행이동) 유사변환을 가한 형상을 정렬 →
  최대 잔차 **~2e-14**(기계정밀도). 무작위 변환 20개에서도 worst **~4e-14**. 즉
  좌표평면 좌표하강이 임의의 3D 유사변환을 정확히 복원한다.
- **3D outlier 저항성**: 한 랜드마크를 크게 어긋나게 하면, 나머지 랜드마크 잔차
  **0.0**, outlier 잔차 ~58 — 정확히 resistant-fit의 정의적 성질.

이 강한 검증(임의 3D 변환의 기계정밀도 복원 + outlier 저항)을 통과했기에 3D를
과학 도구에 넣어도 된다고 판단했다. (통과 못 했으면 넣지 않을 계획이었다.)

## 변경

- `resistant_fit_superimposition`: 2D 전용 → **2D/3D 통합**, 3D 거부 제거.
- 신규 헬퍼: `_resistant_align`(통합), `_resistant_scale`, `_repeated_median_angle`,
  `_axis_rotation_2d`, `_resistant_rotate_3d`(Z/Y/X 좌표하강),
  `_axis_rotation_3d`(행벡터 축 회전, `_repeated_median_angle`의 (u,w) 규약과 일치).
- `analysis_dialog.py`: 3D 비활성 가드 제거(2D/3D 모두 세 방식 선택 가능).
- 컨트롤러는 변경 불필요(dispatch는 이미 `resistant_fit_superimposition` 호출).

## 테스트

- `TestResistantFitSuperimposition`: 기존 2D(정렬/outlier/결측)에 더해 **3D 유사변환
  정렬**과 **3D outlier 저항** 추가.
- 컨트롤러 dispatch 테스트를 2D 성공 경로 + 결측 거부로 갱신(3D 거부 가드가 사라짐).
- 다이얼로그: 3D에서도 세 방식 enabled.

## 결과

- 관련 스위트 460 passed, 2 skipped. `ruff`/`format` 클린, Sphinx 경고 없음.
- Procrustes/Bookstein/Resistant Fit 세 방식이 **2D와 3D 모두** 동작.
- 문서 갱신(2D-only 문구 제거).

## 남은 것

- Bookstein/Resistant Fit의 결측 랜드마크 지원(현재 거부; 필요 시 임퓨테이션 통합).
