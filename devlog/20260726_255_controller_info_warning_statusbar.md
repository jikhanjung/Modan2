# 컨트롤러 info/warning 메시지를 status bar로 연결 (버려지던 메시지 복구)

## 날짜
2026-07-26

## 배경

`ModanController`는 `error_occurred`/`warning_occurred`/`info_message` 세 메시지
시그널을 정의하지만, `Modan2.py`는 `error_occurred`만 연결하고 나머지 둘은 연결하지
않았다. 그래서:

- `info_message.emit` **7곳**(데이터셋 생성/수정/삭제, "Imported N objects", 오브젝트
  삭제, 분석 완료, 분석 삭제)과 `warning_occurred.emit` **3곳**("Another operation
  is in progress", "Another analysis is already running", CVA/MANOVA 부분 실패)이
  **전부 조용히 버려졌다**. 특히 경고는 UI에 대체 표시가 없어서, 이미 분석 중일 때
  Analyze를 또 눌러도 사용자에겐 아무 반응이 없었다.
- 게다가 일부 사건은 **중복 설계**였다: 컨트롤러가 이름까지 담은 구체 문구
  (`info_message`)를 쏘는데 이를 버리고, 연결된 lifecycle 슬롯이 하드코딩된 일반
  문구를 **모달 팝업**으로 띄웠다(`on_dataset_created`, `on_analysis_completed`).

## 결정

옵션 A(컨트롤러가 메시지 소유) + **status bar**(비모달). 즉 info/warning 텍스트의
단일 소스를 컨트롤러로 삼고, UI 슬롯의 하드코딩 모달 팝업은 제거한다. 에러는 심각도가
달라 기존대로 모달 유지(`on_controller_error`).

## 변경 (`Modan2.py`)

- `warning_occurred`/`info_message`를 새 슬롯 `on_controller_warning`/
  `on_controller_info`에 연결. 두 슬롯 모두 `self.statusBar.showMessage(msg, 5000)`
  로 5초 노출(비모달).
- 중복이던 하드코딩 모달 제거: `on_dataset_created`의
  `show_info("Dataset created successfully")`, `on_analysis_completed`의
  `show_info("Analysis completed successfully")`. 두 슬롯은 `load_dataset()`(뷰
  갱신)만 남긴다. 결과적으로 사건당 **구체 문구 하나가 status bar에** 뜬다.
- 미사용이 된 `show_info` import 제거(`show_error`/`show_warning`은 유지).

## 테스트 (`tests/test_ui_dialogs.py::TestControllerMessages`)

- `on_controller_info`/`on_controller_warning`가 status bar에 문구를 띄우는지.
- **엔드투엔드**: `controller.info_message.emit(...)` / `warning_occurred.emit(...)`
  가 status bar에 도달하는지(연결 자체가 이번에 고친 회귀).

(로컬은 헤드리스라 `QT_QPA_PLATFORM=offscreen`으로 실행; CI는 xvfb.)

## 결과

- 대상 스위트 54 passed(ui_dialogs/menu_actions/smoke). `ruff`/`format` 클린.
- 버려지던 info 7종·warning 3종이 이제 사용자에게 노출되고, 데이터셋 생성/분석 완료의
  성가신 성공 모달이 비모달 status bar로 바뀌었다.

## 참고

- error는 여전히 모달(`show_error`). info/warning만 status bar로 이동.
- Modan2가 아직 연결하지 않는 lifecycle 시그널(`dataset_deleted`/`object_deleted`)은
  삭제 사건의 사용자 피드백을 이제 `info_message`(224/535)가 status bar로 대신 제공하므로
  기능상 갭은 없다.
