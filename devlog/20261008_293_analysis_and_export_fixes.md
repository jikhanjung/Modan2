# 변수 없는 분석, 내보내기, Analysis Details 버그 수정

## 날짜
2026-10-08

## 배경

devlog 290 후속 2에서 매뉴얼을 코드에 맞추다가 찾은 코드 쪽 문제들. 매뉴얼에는
"현재는 변수가 하나 이상 필요" 같은 임시 문장으로 적어 두었던 것을 이번에 코드에서
고치고 문장을 되돌렸다.

## 변수가 없는 데이터셋

`_validate_dataset_for_general_analysis`가 변수가 없으면 `return False` 했다. 경고문은
"Only PCA analysis will be available"이었다. 2025-09의 271bc26이 "grouping variables가
없으면 분석 대화상자를 막는다"로 넣은 차단이다. `run_analysis`는 원래
`cva_group_by=None`이면 CVA/MANOVA를 건너뛰게 돼 있어서, 차단만 풀면 PCA만 돈다.
분석 대화상자는 두 콤보에 *None (no variables)*(data `None`)를 넣고 비활성화한다.

차단 뒤에는 두 화면 버그가 있었다. 둘 다 `guard_slot` 안에서 나서 오류 상자와 로그
한 줄로만 드러났다:

- **CVA 탭 → Data Exploration**: CV 점수가 없으면 `json.loads(None)`. 변수가 있어도
  CVA가 실패한 분석이면 같은 일이 생긴다. 이제는 안내 메시지를 띄우고 열지 않는다.
- **MANOVA 탭 → Data Exploration**: `set_analysis`가 PCA/CVA만 처리해서
  `analysis_result_list`가 없었다. 변수 유무와 상관없이 늘 실패했다. MANOVA는 PCA
  점수로 검정하므로, PCA 점수를 MANOVA 변수로 그룹 지어 보여 준다.

`tests/dialogs/test_analysis_dialog.py`의 `sample_dataset_with_variables` fixture는
`variablename_list=`(모델 필드가 아님)로 변수를 넘겨서, 실제로는 변수가 없는 데이터셋이었다.
그래서 두 테스트가 "콤보 0개"와 "변수 없는데 콤보 활성"을 검사하고 있었다.
`propertyname_str` / `property_str`로 고치고 `expected_count > 0`을 추가했다.

## 내보내기

- **X1Y1**: 라디오는 있는데 `export_dataset`에 분기가 없었다. `format_x1y1`을 추가했다.
  탭 구분, 머리글 `name X1 Y1 …`이다. 리더는 세 번째 좌표 열 머리글이 `X`로 시작하는지로
  2D/3D를 가른다.
- **객체 선택**: Export List를 무시하고 `ds_ops.object_list` 전체를 썼다.
  - 이제 항목에 객체 id를 넣는다(이름은 중복될 수 있음).
  - 중첩정렬 **전에** 걸러, 내보낸 객체끼리 정렬되게 했다.
  - JSON+ZIP은 `create_zip_package(dataset_id)`라 데이터셋 전체여서 목록을 비활성화한다.
  - 목록이 비면 경고만 띄우고 쓰지 않는다.
- **결측 랜드마크**: TPS·Morphologika가 `str(None)`, 즉 `None`을 썼다. Modan2 TPS
  리더의 `float("None")`이 실패해서 자기 내보내기를 다시 못 읽었다. 이제 `-999`
  (`mu.MISSING_SENTINEL`)로 쓰고, 가져오기가 결측으로 되돌릴지 묻는다.
- 철회된 Resistant fit 라디오를 내보내기에서 제거했다(기존 테스트 2곳 갱신).

## Analysis Details

`DatasetAnalysisDialog`는 저장된 분석을 보여 주는 창이 아니라, 데이터셋을 받아 직접
계산하는 별도 도구다. 그래서 늘 Procrustes였다. 저장된 결과를 그대로 보여 주려면 창을
다시 설계해야 해서 범위를 좁혔다:

- 분석의 `superimposition_method`를 넘긴다.
- 데이터셋에 베이스라인이 있으면 Bookstein 라디오를 켜고 그 방식으로 계산한다.
- 계산이 실패하거나 객체가 모자라 일찍 끝날 때 대기 커서를 되돌리지 않던 것도 고쳤다.

"현재 랜드마크로 다시 계산"이라는 성격은 그대로다. 매뉴얼에도 그렇게 적었다.

## 남은 것

- **CVA 정확도가 어디에도 표시되지 않는다.** 0.2.0 릴리스 노트는 "the old figure is
  still shown, as resubstitution accuracy"라고 적었다. 그런데 `_run_cva`가 돌려주는
  `resubstitution_accuracy` / `cross_validated_accuracy`는 저장되지도, 화면에 나오지도
  않는다.

## 검증

- 새 테스트: `test_pca_only_analysis.py` 13개, `test_export_selection.py` 11개.
  수정 전 코드에서는 각각 5개 실패 / 수집 실패였다.
- 전체 테스트 통과, ruff 깨끗함.
- `.ts`: 새 문자열 4개 번역, Resistant fit은 obsolete 처리. `.qm` 383 finished.
- 매뉴얼 ko 카탈로그 미번역 0 / fuzzy 0, Sphinx 경고는 기존 2개.
