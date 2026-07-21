# 다이얼로그 블로킹으로 꺼져 있던 테스트 되살리기 (R03 항목 6)

## 날짜
2026-07-21

## 배경

스킵된 테스트 74개를 분류해 보니 정당한 환경 스킵은 **1개**(Windows 전용 경로
정규화)뿐이었고, 가장 큰 덩어리 37개가 다음 사유로 통째 꺼져 있었다:

> "Menu/Toolbar/Tree action tests cause dialog exec_() blocking - needs dialog
> mocking refactor"

즉 메인 윈도우의 메뉴·툴바·트리 상호작용이 사실상 미검증 상태였다.

## 원인

`QDialog.exec_()`는 자체 이벤트 루프를 돌며 누군가 다이얼로그를 닫아야
반환하는데, 헤드리스 테스트에서는 닫는 주체가 없어 **영원히 멈춘다**. 실제로
스킵을 걷어내니 `on_action_new_dataset_triggered` → `self.dlg.exec_()`에서
정확히 멈추는 것을 확인했다 (pytest-timeout의 signal 방식으로는 Qt 루프를 못
끊어서 `--timeout-method=thread`로 특정).

## 수정

### 1. 전역 차단 (`tests/conftest.py`)

`suppress_modal_dialogs` autouse 픽스처 추가: `QDialog.exec_` / `exec` /
`open`을 패치해 `Rejected`를 즉시 반환한다. 이미 있던 `QMessageBox` 패치의
자연스러운 확장이며, 스킵 사유가 요구하던 "dialog mocking refactor"를 테스트
하나하나가 아니라 **한 곳에서** 해결한다.

`Rejected`를 고른 이유: 코드가 "사용자가 취소함" 분기를 타서 아무 것도 커밋하지
않는다. 수락 경로를 원하는 테스트는 지금처럼 다이얼로그 클래스를 직접 목킹하면
된다.

### 2. 낡은 기대값 정리

행이 사라지자 13개가 실패했는데, 전부 앱 동작과 어긋난 기대값이었다:

| 문제 | 처리 |
|---|---|
| `controller.db_file_path`로 "DB 미개방" 경고 기대 (2개) | 그런 API·상태가 애초에 없음 → 삭제 |
| `on_action_edit_object_triggered` 호출 | 존재하지 않는 메서드 → 삭제 |
| `controller.current_dataset`에 값 설정 | 핸들러는 `self.selected_dataset`를 봄 → 수정 |
| 선택 없을 때 경고 기대 (2개) | 액션이 비활성화되므로 조용한 return이 맞음 → "아무 일도 안 함"을 검증하도록 변경 |
| `QMessageBox.about` 목킹 (2개) | About이 리치 텍스트 박스 생성 방식으로 바뀜(devlog: About 링크) → `build_about_message` 검증 |
| 객체 삭제가 `controller.current_object` 기준일 것으로 가정 | 실제로는 테이블 선택 기준 + `warning`으로 확인 → 수정 |
| 분석 액션이 객체 수를 검증할 것으로 가정 | 검증은 다이얼로그가 함 → 다이얼로그가 열리는지로 변경 |
| Row selection이 무조건 동작할 것으로 가정 | 액션이 checked일 때만 동작 → 수정 |
| Explore data가 `exec_`될 것으로 가정 | 비모달 `show()`이고 분석(dataset 아님) 기준 → 수정 |

### 3. 앱 잠재 결함 하나

`ModanMainWindow.selected_analysis`가 `__init__`에서 초기화되지 않아, 트리에서
분석을 고르기 전에 읽으면 `AttributeError`가 났다
(`on_action_explore_data_triggered`가 그렇게 읽는다). 지금은 그 액션이 컨텍스트
메뉴에서 주석 처리되어 UI로는 도달할 수 없지만, `selected_dataset` /
`selected_object`와 같이 `None`으로 초기화했다.

## 결과

- 스킵 **74개 → 37개**, 통과 1482 → **1516개**.
- 되살린 58개(메뉴 24 · 툴바 22 · 트리 16)가 모두 통과.

## 2차: 나머지 스킵 정리

남은 37개 중 29개("CI timeout" 사유)를 조사한 결과, 타임아웃이 아니라
**존재한 적 없는 API를 대상으로 쓰인 가공의 테스트**였다. 스킵 처리되어 있어
실패할 기회조차 없었다:

- `test_ui_dialogs.py` (19개): `dialog.edit_dataset_name`(실제는
  `edtDatasetName`), `dialog.slider_landmark_size`,
  `main_window.on_action_open_image`, 인자 2개짜리 `ObjectDialog(parent, obj)`
  (실제 생성자는 parent만) 등.
- `test_workflows.py` (10개): 오래전 삭제된 `ModanDialogs` 모듈 import,
  `MdTreeView.addTopLevelItem`(QTreeView인데 QTreeWidget API), 존재하지 않는
  `on_action_export` / `on_action_analysis` / `on_action_import_3d`.

삭제해도 커버리지 손실이 없다 — 각 대상마다 실제로 도는 스위트가 이미 있다:
다이얼로그는 `tests/dialogs/` (dataset 21 · preferences 38 · analysis 34 +
import/export/object-mode/calibration), 워크플로는
`test_integration_workflows` / `test_analysis_workflow` / `test_object_workflows`
/ `test_multi_analysis_workflow` / `test_error_recovery_workflow` /
`test_dataset_lifecycle` 합계 61개(통과 확인).

그래서 `test_workflows.py`는 파일째 삭제하고, `test_ui_dialogs.py`는 실제
메서드에 대응하는 것만 남겼다 — About 박스, 그리고 컨트롤러 오류/분석 실패가
사용자에게 표시되는지 검증하는 `TestControllerMessages`.

## 결과 (최종)

스킵 **74개 → 8개**, 통과 **1482 → 1518개**. 남은 8개는 모두 정당하다:
성능 픽스처 3, 수동 UI 조작 2, 변수 삭제/재정렬 조사 필요 2, Windows 전용 1.

## 곁가지 발견 (미수정)

`ModanController`는 `warning_occurred`(2곳)와 `info_message`(7곳)를 emit하지만
**메인 윈도우가 두 시그널을 연결하지 않는다** — 해당 메시지는 조용히 버려진다.
그냥 연결하면 `on_dataset_created`가 이미 직접 띄우는 메시지와 중복되므로,
사용자 메시지를 어느 계층이 책임질지 정하는 설계 판단이 먼저 필요해 남겨 둔다.
