# 복잡도 핫스팟 리팩토링 캠페인 + 렌더링 특성화 테스트

## 날짜
2026-07-24

## 배경

[[20260723_R05_code_quality_checks_review]]에서 도입한 **복잡도 리포트(C901,
비게이팅)**가 짚은 핫스팟들을 실제로 정리했다. R05의 관측대로 이 프로젝트의
반복 테마는 **"쌍둥이/죽은/도달 불가 경로에 숨은 잠복 버그"**인데, 복잡한 함수를
쪼개는 과정에서 그런 것들이 계속 드러났다 — 리팩토링 자체보다 **부수적으로 발견한
버그·죽은 코드**가 더 큰 소득이었다.

원칙: **테스트 안전망이 있는 것부터**, 렌더링/이벤트처럼 커버리지가 얇은 곳은
**특성화 테스트를 먼저 붙이고** 손댄다.

---

## 1. 리팩토링 6건 (모두 동작 변경 없음)

| # | 대상 | 복잡도 | 커밋 |
|---|------|--------|------|
| 1 | `components/formats/tps.py::read` | **36 → 25** | `_store_object` 추출 |
| 2 | `components/formats/morphologika.py::read` | **30 → <15** | `_parse_sections`, `_apply_optional_sections` |
| 3 | `ModanController::_persist_analysis_results` | **26 → <10** | 헬퍼 4개 |
| 4 | `dialogs/data_exploration_dialog::show_analysis_result` | **42 → <15** | 헬퍼 7개 |
| 5 | `components/widgets/analysis_info::show_analysis_result` | **51 → <15** | 헬퍼 7개 |
| 6 | `dialogs/dataset_analysis_dialog::show_analysis_result` | **26 → <15** | 헬퍼 5개 |

### 1-1. TPS 리더 (36 → 25)
객체 확정(finalize) 로직이 **두 곳에 중복**돼 있었다 — 루프에서 새 `LM=` 헤더를
만날 때와 파일 끝. 키 선택 + 5개 컬렉션 저장이 손으로 동기화되던 twin-code(=
`draw_dataset` 중복과 같은 냄새). `_store_object()`로 추출하고 출력 컬렉션을
`self.*`로 통일. 빈 파일 검사를 마지막 flush **앞으로** 옮겨 기존 폐기 동작을
정확히 보존했다.

### 1-2. Morphologika 리더 (30 → <15)
`read()`가 ① 섹션 버킷팅 ② 좌표 구성 ③ **거의 동일한 optional 섹션 6개**(labels,
labelvalues, wireframe, polygons, images, pixelspermm)를 한 몸에 하고 있었다.
①→`_parse_sections()`, ③→`_apply_optional_sections()`로 분리.
- 죽은 코드: 즉시 덮어써지는 `self.nobjects = len(...)`.

### 1-3. `_persist_analysis_results` (26 → <10)
group_by 이름 해석의 **CVA/MANOVA 블록이 복붙 중복** → `_resolve_group_by_name()`.
직렬화는 `_serialize_object_data` / `_serialize_pca_result` /
`_serialize_cva_result` / `_serialize_manova_result`로 분리. 함수 지역
`import json`을 모듈 레벨로 올렸다. (PCA일 때만 CVA/MANOVA를 직렬화하는 가드는
그대로 보존.)

### 1-4. Data Exploration `show_analysis_result` (42 → <15)
244줄 차트 렌더러를 7개 헬퍼로 분해. **죽은 코드 발견:**
- 메서드 본문 전체를 감싼 **`if True:`**
- 절대 False가 안 되는 `show_axis_label = True`
- **중복 `ax2.clear()`**
- 결과를 버리는 `self.comboAxis3.currentText()`

골든 특성화 테스트가 지키고 있어 안전하게 진행할 수 있었다.

### 1-5. Analysis Info `show_analysis_result` (51 → <15) — 최대 규모
384줄. JSON 로딩 / MANOVA 테이블(레거시 레이아웃 3종) / PCA·CVA 산점도 구성·렌더를
한 함수에서 처리하고, **6개 병렬 리스트를 인덱스로** 훑는 패턴이었다
(`scatter_data_list[idx]`, `ax_list[idx]` …). 타입별 명시 파라미터 호출로 전환.

**죽은 코드·잠복 버그 (이번 건이 최다):**
- **`self.pca_scatter_data` / `cva_scatter_data` / `pca_scatter_result` /
  `cva_scatter_result`** — 루프가 `scatter_data_list[idx] = {}`로 **리스트 슬롯을
  재바인딩**해서 self 속성은 **항상 빈 dict**로 남았다. 게다가 레포 어디서도 읽지
  않는 **write-only 상태**였다.
- **`if True:` 래퍼 3개** 추가 발견
- `marker_list`/`color_list`로 즉시 덮어써지는 symbol/color 후보 리터럴
- `continue`로 스킵되는 키를 검사하는 **도달 불가 `degrees_of_freedom` 분기**
- 결과를 버리는 `stat_dict.get("column_names", ...)`, 미사용 `failure_reasons`

### 1-6. Dataset Analysis `show_analysis_result` (26 → <15)
`_scatter_point_size` / `_build_scatter_groups` / `_draw_scatter_2d` /
`_draw_scatter_3d` + 공용 `_finish_canvas`(레이아웃·draw·pick/press/release 핸들러
재연결 — 2D/3D 분기가 중복하던 부분)로 분해.

**실제 버그 수정:** `plot_size`가 `{small, medium, large}` 밖의 값이면
`scatter_size`가 **미바인딩 → NameError**였다. medium 기본값으로 폴백.
**죽은 코드:** 덮어써지는 candidate 리터럴, 미사용 `key_list`,
`get_centroid_size(True)` 중복 호출(첫 결과 폐기).

> 참고: 리팩토링 중 새로 만든 `SCATTER_SIZES` 클래스 속성을 **R05에서 켠 RUF012가
> 즉시 잡았다**(mutable class default). `ClassVar` 주석으로 해결 — 룰이 의도대로
> 작동함을 확인한 사례.

---

## 2. CI 도구 버전 핀 사건 (코드 변경 없이 CI가 깨짐)

리팩토링 도중 CI lint가 빨간불. 원인은 우리 코드가 아니었다:

- lint job이 **`pip install ruff`(버전 핀 없음)** → 매 실행 최신 ruff를 받음
- 최근 ruff가 **Markdown 안의 파이썬 코드 블록까지 포맷**하기 시작
- 로컬(0.15.19/0.15.22) **162 파일 통과** vs CI(최신) **437 파일 검사 →
  `103 files would be reformatted`**
- 재포맷 대상은 `docs/performance.md`, `developer_guide.md` 등 **문서 예제 코드**

**수정:** ruff를 `.pre-commit-config.yaml`의 핀과 동일한 **0.15.22로 고정**, mypy도
**2.3.0으로 고정**(같은 위험 방지). CI·pre-commit·로컬 3자가 동일하게 동작한다.
교훈은 [[docs/CODE_QUALITY_GUIDE.md]] §6에 **"의존성뿐 아니라 도구 버전도 핀하라"**로
기록했다.

---

## 3. 렌더링 핫스팟 특성화 테스트 (리팩토링 前 안전망)

남은 최상위 핫스팋 3개는 **커버리지가 거의 없었다**:
`ObjectViewer2D.paintEvent`(56), `ObjectViewer2D.mousePressEvent`(33, 2개 분기만
테스트됨), `ObjectViewer3D.draw_object`(39, 전무).

커버리지 없이 렌더링 코드를 쪼개면 회귀를 못 잡으므로, **먼저 특성화 테스트를
작성**했다 — `tests/test_viewer_rendering_characterization.py` (40개).

- **렌더링:** "모든 표시 플래그 / 각 edit 모드 / 객체 없음 / ds_ops(데이터셋) 경로 /
  3D GL 경로에서 렌더되고 유효한 pixmap을 낸다"로 단언. **픽셀 골든은 쓰지 않았다**
  — OS 매트릭스(폰트·안티앨리어싱)에서 flaky해지기 때문.
- **인터랙션:** `mousePressEvent`는 분기별 상태 전이를 정밀 단언 — 우클릭→PAN,
  `READY_MOVE_LANDMARK`→`MOVE_LANDMARK`, wireframe이 hover 정점을 start로 래치,
  calibration이 이미지 좌표 기록, 이미지 없는 edit-landmark는 no-op.
- 3D 뷰어는 헤드리스(offscreen)에서 `makeCurrent()`·`grab()`이 동작함을 확인 후 GL
  컨텍스트 안에서 `draw_object`를 호출.

**이빨 검증:** 세 함수에 각각 예외를 주입하니 **35 / 4 / 5개 테스트가 실패** — 실제로
해당 코드를 잡고 있음을 확인. 이 파일만으로 `object_viewer_2d.py` **30%**,
`object_viewer_3d.py` **28%** 커버.

---

## 남은 것

- **렌더링 3인방 리팩토링**: 이제 안전망이 생겼으므로 `paintEvent`(56),
  `draw_object`(39), `mousePressEvent`(33)를 분해할 수 있다.
- 그 외 15 초과 잔여: `prepare_shape_view`(22), `import_dataset_from_zip`(23),
  `nts.read`(22), `on_canvas_move`(19), `on_btnSaveResults_clicked`(16),
  `run_analysis`(16), `pick_shape`(16), `tps.read`(25, 이미 36에서 개선).
- 복잡도 리포트는 비게이팅 유지(가이드 §13: GUI 코드엔 정당하게 긴 핸들러가 있다).
