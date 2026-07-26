# Bookstein 정합 구현 + 분석 경로 연결 (Resistant Fit은 재작성 과제로 남김)

## 날짜
2026-07-26

## 배경

[[20260726_250_disable_bookstein_resistant_fit_superimposition]]에서 분석
다이얼로그의 Bookstein/Resistant Fit을 비활성화했다("고르면 조용히 Procrustes가
도는" 문제 차단). 후속으로 "연결하면 바로 동작하냐"를 확인한 결과, 두 함수 모두
"연결만 하면 되는" 상태가 아니었다.

**Resistant Fit(`MdDatasetOps.resistant_fit_superimposition`)은 사실상 망가짐:**
- `rotate_resistant_fit_to_reference_shape` 끝에서 `lm = [...]`로 루프 변수만
  재바인딩 → 회전 결과가 `landmark_list`에 **반영 안 됨**(rescale만 적용되는 no-op).
- `cos_val = np.vdot(...) / norm(t) * norm(r)` — 연산자 우선순위상 정규화가 틀려
  `math.acos` 도메인 에러 소지.
- `[i][2]` 무조건 접근 → **3D 전용**(2D 크래시), 반환값 없음, 결측 미지원.
- 유일한 테스트가 3D + "수렴 여부"만 봐서 이 결함들을 못 잡고 통과.

**Bookstein은 데이터셋 단위 함수 자체가 없었다** — `bookstein_registration`은
`MdObjectOps`의 개별 객체 메서드(3D 인덱싱)뿐.

사용자 결정: **Bookstein 먼저** 깔끔히 구현하고, Resistant Fit은 별도 재작성
과제로 남긴다(계속 비활성).

## 계획

1. `MdDatasetOps.bookstein_superimposition()` 신규 — 폐형식(closed-form)
   변환으로 2D/3D 모두, **차원 보존**(2D는 2원소 유지), 결측 랜드마크 거부.
2. 컨트롤러 `_prepare_landmarks`에 `superimposition_method` 스레딩 + dispatch.
3. 분석 다이얼로그에서 Bookstein 재활성(Resistant Fit만 비활성 유지).
4. 테스트(MdModel 단위 + 컨트롤러 dispatch + 다이얼로그 상태).
5. 문서 동기화.

기존 레거시 `bookstein_registration`(MdObjectOps)은 건드리지 않았다 — `[2]`
하드코딩 + `rotate_2d`가 2D를 3원소로 승격시키는 등 얽혀 있어, 패치보다 폐형식
신규 구현이 안전하고 검증도 쉽다. 기존 함수의 테스트도 그대로 둔다.

## 구현

### `MdModel.MdDatasetOps.bookstein_superimposition()`
- 데이터셋 baseline(`baseline_point_list`, 1-based)에서 2D는 2점, 3D는 3점 사용.
  없거나 부족하면 명확한 `ValueError`.
- 어떤 객체든 랜드마크에 `None`이 있으면 `ValueError`("Procrustes를 쓰라").
- **2D**(`_bookstein_coords_2d`): baseline 끝점을 `(-0.5,0)`,`(0.5,0)`으로 보내는
  표준 Bookstein 좌표 폐형식. 2원소 유지.
- **3D**(`_bookstein_coords_3d`): 중점 원점 이동 → baseline 길이 1로 스케일 →
  `e1=(B-A)`, 세 번째 점의 baseline 직교 성분으로 `e2`, `e3=e1×e2` 정규직교 기저에
  투영. 결과: 끝점 `(±0.5,0,0)`, 세 번째 점은 xy평면(z=0) +y쪽. collinear면
  `ValueError`.
- 성공 시 `True` 반환(Procrustes와 계약 일치).

### 컨트롤러 dispatch (`_prepare_landmarks`)
- `_prepare_landmarks(superimposition_method="Procrustes")`로 시그니처 확장,
  `run_analysis`가 자신의 `superimposition_method`를 전달.
- `method == "bookstein"`이면 `ds_ops.bookstein_superimposition()`(실패는 구체적
  `ValueError`로 자체 발생), 그 외는 기존대로 `procrustes_superimposition()`.
  Bookstein 외 값은 모두 Procrustes로 폴백(회귀 방지).

### UI
- `analysis_dialog.py`: `item(2)`(Resistant Fit)만 비활성. Bookstein은 선택 가능.

## 테스트

- `tests/test_mdmodel.py::TestBooksteinSuperimposition` (5): 2D 표준 위치 + 유사
  변환 불변성(닮은 두 도형이 동일 Bookstein 좌표), 3D 표준 위치, baseline 필수,
  결측 거부, 일치 baseline 거부.
- `tests/test_controller.py::...test_prepare_landmarks_dispatches_to_bookstein`:
  `"Bookstein"`이 baseline을 `(±0.5,0)`에 고정, `"Procrustes"`는 안 함.
- `tests/dialogs/test_analysis_dialog.py`: Procrustes/Bookstein enabled,
  Resistant Fit disabled.

## 결과

- 관련 스위트 426 passed, 2 skipped. `ruff`/`format` 클린, Sphinx 경고 없음.
- 사용자는 이제 baseline이 정의된 데이터셋에서 Bookstein 정합을 실제로 쓸 수 있다.
- 문서(`user_guide.rst`, `USER_GUIDE.md`) 갱신: Procrustes/Bookstein 동작,
  Bookstein은 baseline + 완전 랜드마크 필요, Resistant Fit은 비활성.

## 남은 것

- **Resistant Fit 재작성**: 회전 미반영·정규화 버그·3D전용·무반환을 고쳐 제대로
  된 repeated-median resistant fit으로 재구현하고 2D/3D·결측·정답 검증 테스트를
  붙여야 함. 그때 `analysis_dialog.py`의 `item(2)` 비활성만 풀면 dispatch는 이미
  들어갈 자리가 있다(현재는 Procrustes 폴백).
- Bookstein 결측 랜드마크 지원(현재는 거부) — 필요하면 Procrustes식 임퓨테이션
  통합을 후속으로.
