# Resistant Fit(RFTRA) 재작성 — 2D repeated-median, 분석 경로 연결

## 날짜
2026-07-26

## 배경

[[20260726_251_bookstein_superimposition_implementation]]에서 Bookstein을 살리고
Resistant Fit은 "재작성 필요"로 남겨 뒀다. 기존 `resistant_fit_superimposition`
(및 헬퍼들)은 연결만 하면 되는 상태가 아니라 근본적으로 망가져 있었다:

- `rotate_resistant_fit_to_reference_shape` 끝에서 `lm = [...]`로 루프 변수만
  재바인딩 → **회전이 `landmark_list`에 반영 안 됨**(rescale만 되는 no-op).
- `cos_val = np.vdot(...) / norm(t) * norm(r)` — 연산자 우선순위상 정규화가 틀려
  `math.acos` 도메인 에러 소지.
- `[i][2]` 무조건 접근 → 3D 전용(2D 크래시), 반환값 없음, 결측 미지원.
- 유일한 테스트가 3D + "수렴 여부"만 봐서 이 결함들을 못 잡고 통과.

## 결정 / 범위

- **2D RFTRA(Rohlf & Slice 1990)를 새로 구현.** repeated median으로 스케일·회전을,
  좌표별 median으로 평행이동을 추정 → 소수의 outlier 랜드마크가 전체 정합을
  끌어당기지 못한다(최소제곱 Procrustes와의 핵심 차이).
- **3D는 미구현**: 견고한 3D resistant fit(generalized resistant fit)은 회전
  추정이 훨씬 복잡하고 검증 부담이 커서 이번 범위에서 제외. 3D 데이터셋은 명확한
  `ValueError`로 거부하고 UI에서도 3D면 비활성.
- 결측 랜드마크 미지원(거부).

## 구현

### `MdModel.MdDatasetOps.resistant_fit_superimposition()` (재작성)
- 3D/결측이면 명확한 `ValueError`.
- 각 shape를 중심화 후 numpy(N×2)로 처리. 초기 reference = 첫 shape.
- 반복: 모든 shape를 `_resistant_align_2d`로 현재 **median consensus**에 정렬 →
  새 consensus 재계산 → 이동량이 임계값 미만이면 종료(최대 100회). median consensus
  덕에 한 shape의 outlier가 다른 shape들의 정렬 타깃을 오염시키지 않는다.
- 정렬 결과를 객체에 write-back하고 `self.reference_shape`를 평균 형상으로 설정
  (기존 호출/테스트 계약 유지). `True` 반환.

### `_resistant_align_2d(target, reference)` (신규 static)
1. **스케일**: 각 i에 대해 j에 걸친 거리비(ref/target) median → 그 median들의
   median(repeated median).
2. **회전**: 각 i에 대해 pairwise 각도차(정규화 (-π,π]) median → 그 median들의
   median. 행벡터 CCW 회전행렬 적용.
3. **평행이동**: `median(reference - rotated, axis=0)`.

### 죽은 코드 제거
`_resistant_align_2d`가 대체하므로, 깨진 데다 테스트도 없는
`rotate_resistant_fit_to_reference_shape` / `get_vector_rotation_matrix` /
`get_median_index`(254줄) 삭제. 범용 유틸 `rotate_vector_2d` / `rotate_vector_3d`는
자체 테스트가 있어 유지.

### 연결 / UI
- `ModanController._prepare_landmarks`: `"resistant fit"` → `resistant_fit_
  superimposition()` dispatch 추가(3D/결측은 자체 `ValueError`로 사용자에게 노출).
- `analysis_dialog.py`: Resistant Fit는 2D 전용이라 **3D 데이터셋에서만 비활성**
  (2D면 세 방식 모두 선택 가능).

## 테스트

- `TestResistantFitSuperimposition`(재작성): 3D 거부, 결측 거부, 유사변환 형상들이
  정렬 후 일치, **outlier 랜드마크 저항성**(오염된 한 점을 제외한 나머지는 정확히
  정렬되고 outlier는 멀리 남음) — RFTRA의 핵심 성질 검증.
- 컨트롤러 dispatch: `"Resistant Fit"`가 3D에서 2D-only 가드에 걸림(Procrustes는 안
  걸림)로 라우팅 확인.
- 다이얼로그: 2D는 세 방식 enabled, 3D는 Resistant Fit disabled.

## 결과

- 관련 스위트 427 passed(+smoke/statistics/workflow 83 passed). `ruff`/`format`
  클린, Sphinx 경고 없음.
- Procrustes/Bookstein/Resistant Fit(2D) 세 정합이 모두 실제로 동작한다.
- 문서(`user_guide.rst`, `USER_GUIDE.md`) 갱신.

## 남은 것

- **3D resistant fit**(generalized resistant fit) — 3D 회전의 repeated-median
  추정을 구현·검증해야 함. 되면 `analysis_dialog.py`의 3D 비활성 가드만 풀면 된다.
- Bookstein/Resistant Fit의 결측 랜드마크 지원(현재 거부).
