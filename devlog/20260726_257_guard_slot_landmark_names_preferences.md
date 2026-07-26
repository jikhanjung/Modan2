# @guard_slot 커버리지 확대 — landmark 이름 저장 / 환경설정 저장

## 날짜
2026-07-26

## 배경

[[20260723_R04_audit_fileio_security_errorhandling]] 후속: 사용자 조작 슬롯에
`@guard_slot`을 넓혀 실패가 창을 조용히 죽이지 않고 컨텍스트 있는 에러로 뜨게 한다.
R04 후속에서 object_dialog·data_exploration은 처리됐고 "나머지 다이얼로그 미완".

## 점검 결과

import/export/analysis 다이얼로그의 무거운 슬롯은 이미 보호돼 있었다:
- import: `open_file`/`import_file` `@guard_slot`.
- export: `export_dataset` `@guard_slot`, `update_estimated_size`는 자체 try.
- analysis: `btnOK_clicked`는 자체 try/except로 UI 상태까지 복구(guard_slot보다 적합).
- 나머지 미보호 슬롯(라디오 토글, 리스트 항목 이동 등)은 순수 인메모리 위젯 조작이라
  데이터/IO 실패가 없어 가드 불필요.

반면 **영속 상태를 쓰는데 무방비인 슬롯 2곳**을 발견:
- `landmark_name_dialog.accept_names` — `dataset.save()`(DB 쓰기)인데 guard/try 없음.
- `preferences_dialog.Okay` — `write_settings()`(설정 저장) 후 close, 무방비.

## 변경

- `accept_names`에 `@guard_slot("Failed to save landmark names")`.
- `Okay`에 `@guard_slot("Failed to save preferences")`.
- 두 파일에 `from MdHelpers import guard_slot` 추가.

가드가 예외를 잡으면 `self.accept()`/`self.close()`에 도달하지 않아, 저장 실패 시
다이얼로그가 닫히지 않고 에러가 노출된다(데이터 유실 방지에도 유리).

## 테스트

`test_accept_names_surfaces_save_error`: `dataset.save`가 던지도록 몽키패치 →
`accept_names()`가 예외를 전파하지 않고 `QMessageBox.critical`을 띄우는지 확인.

## 결과

- 대상 스위트 47 passed. `ruff`/`format` 클린.
- import/export/analysis의 위험 슬롯은 이미 보호돼 있었고, 실제 갭이던 두 저장 슬롯을
  가드로 덮었다.
