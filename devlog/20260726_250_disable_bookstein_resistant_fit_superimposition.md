# 분석 다이얼로그의 Bookstein / Resistant Fit 정합 옵션 비활성화

## 날짜
2026-07-26

## 배경

분석 다이얼로그(`dialogs/analysis_dialog.py`)의 정합(superimposition) 방식 콤보는
**Procrustes / Bookstein / Resistant Fit** 세 가지를 모두 활성 상태로 노출한다.
그러나 실행 경로를 추적해 보면 컨트롤러가 메서드 문자열을 **저장만 하고**
(`ModanController.py:1054`) 실제로는 **항상 `procrustes_superimposition()`만
호출**한다(`:1130`). 문자열로 분기하는 코드는 존재하지 않는다(grep으로 확인).

즉 사용자가 Bookstein이나 Resistant Fit을 골라도 **조용히 Procrustes가 돌아간다**.
`MdModel`에 `bookstein_registration` / `resistant_fit_superimposition`가 있긴 하나
분석 경로에서 호출되지 않는다. export 다이얼로그는 이미 두 옵션을
`setEnabled(False)`로 꺼 두어 두 다이얼로그가 불일치했다.

사용자 결정: **두 옵션을 비활성화**(연결이 아니라).

## 변경

- `analysis_dialog.py`: 콤보 생성 직후 항목 1(Bookstein)·2(Resistant Fit)를
  `model().item(i).setEnabled(False)`로 그레이아웃. 항목은 보이되 선택 불가 —
  export 다이얼로그와 동일한 방식. 향후 각 방식의 dispatch가 구현되면 그 자리에서
  다시 켜라는 주석을 남김.
- 테스트: `tests/dialogs/test_analysis_dialog.py`에 Procrustes만 enabled,
  나머지 둘은 disabled임을 검증하는 테스트 추가. 기존 테스트는
  `setCurrentIndex(1)`을 프로그램적으로 호출하는데, disable은 팝업 상호작용만
  막으므로 그대로 통과.

## 문서 동기화

바로 전 세션([[20260726_249_x1y1_nlandmarks_fix_and_parser_tests]] 직전의 매뉴얼
갱신)에서 세 방식이 모두 동작하는 것처럼 문서화했는데, 이제 사실과 어긋난다.
`docs/user_guide.rst`·`docs/USER_GUIDE.md`를 "Procrustes만 분석에 사용되며,
Bookstein/Resistant Fit은 표시되나 현재 비활성"으로 수정.

## 결과

- `tests/dialogs/test_analysis_dialog.py` 35 passed(신규 1 포함).
- `ruff check` / `ruff format --check` 클린, Sphinx 빌드 경고 없음.
- 사용자가 마주하던 "옵션을 골라도 무시됨" 문제 제거. 근본 연결(각 방식의
  실제 dispatch)은 별도 작업으로 남김.
