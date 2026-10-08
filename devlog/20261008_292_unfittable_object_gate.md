# 기록된 landmark가 너무 적은 개체: 분석 전에 거부

## 날짜
2026-10-08

## 발견 경위

논문(Chapter 2) 4차 외부 검토가 "관측 landmark가 부족해 일부 결측값을 채우지 못한 specimen이
후속 단계에서 어떻게 처리되는지"를 물었다. v0.2.0에서 직접 만들어 보았다.

## 무엇이 문제였나

결측 landmark는 평균 형태를 그 개체의 기록된 landmark에 similarity transform으로 맞춰서
채운다(`impute_missing_landmarks`). 이 맞춤에는 차원 수만큼의 공유 landmark가 필요하다(2D 2개,
3D 3개). 그보다 적으면 로그에 경고만 남기고 결측을 비운 채 넘어간다.

2D 자료에서 한 개체에 landmark를 1개만 남기자:

- 분석 전 검사(`find_unimputable_landmarks`)는 "모든 개체에서 빠진 landmark"만 보므로 통과.
- 중첩은 `True`를 반환하고, 그 개체의 landmark 4개가 `None`으로 남음.
- PCA에서 `float() argument must be a string or a real number, not 'NoneType'`로 분석 전체가 실패.

잘못된 결과를 내지는 않지만, 사용자가 원인을 알 수 없는 오류로 멈춘다. `find_unimputable_landmarks`가
막으려던 바로 그 실패가 개체 단위로 남아 있던 것.

## 수정

- `MdModel.find_unfittable_objects(objects, dimension)`: 결측이 있고 기록된 landmark가 `dimension`
  개 미만인 개체와 그 수를 돌려준다.
  - 기록된 landmark는 평균 형태에도 반드시 있다(평균은 모든 개체에서 계산). 그래서 "공유"는 곧
    "이 개체에 기록됨"이다. 좌표가 모두 있어야 기록된 것으로 친다 — 맞춤과 같은 기준.
  - semi-landmark 곡선은 분석 시점에 펼쳐지므로 `MdDatasetOps.object_list`를 넘긴다. 추적된
    곡선은 기록된 점을 더하고, 추적되지 않은 곡선은 결측을 더한다.
- `ModanController.unfittable_objects_message()`: 개체 이름과 기록된 수, 필요한 수, 해결책.
- 분석 전 검사 세 곳(`_prepare_landmarks`, `_validate_dataset_for_analysis_type`,
  `_validate_dataset_for_general_analysis`)에 `find_unimputable_landmarks` 다음으로 추가.
  `_prepare_landmarks`에서는 어차피 만드는 `ds_ops`를 그대로 쓴다.
- 매뉴얼: 사용자 안내서의 거부 조건 목록과 문제 해결 항목, 한국어 `.po`도 같이. 한국어 빌드로
  번역이 적용되는 것을 확인.

## 테스트

`tests/test_unimputable_landmarks.py`에 13개 추가 — 2D에서 1개 기록은 거부·2개는 통과, 3D는
3개 필요, 일부 좌표만 있는 landmark는 기록으로 치지 않음, 완전한 개체는 대상 아님, 추적된 곡선의
점은 기록으로 셈, 추적 안 된 곡선은 결측을 더함, 메시지 단수·복수·해결책, 분석 경로에서
`NoneType` 대신 개체 이름이 든 `ValueError`, 검증 경로에서 거부, 2개 기록된 개체는 여전히 진행.

전체 스위트: 2140 passed, 10 skipped. `ruff check .` 통과.

## 논문과의 관계

논문은 v0.2.0을 기술하므로 이 수정은 반영되지 않는다. 원고의 "a specimen with fewer is left with
its gaps unfilled"는 v0.2.0의 결측 추정 단계 동작으로서 맞는 서술이다.
