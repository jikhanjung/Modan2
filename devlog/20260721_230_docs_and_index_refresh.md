# CLAUDE.md / 코드 인덱스 최신화 (R03 항목 5)

## 날짜
2026-07-21

## 배경

`CLAUDE.md`는 세션 시작 시 자동으로 읽히는 문서라, 틀린 내용이 있으면 이후
작업을 계속 오도한다. 실제로 상당 부분이 리팩토링 이전 상태로 남아 있었다.

## 고친 것

| 항목 | 이전 | 실제 |
|---|---|---|
| 버전 | 0.1.4 | 0.1.8 (`version.py` 참조로 변경) |
| 프로젝트 구조 | `ModanDialogs.py` 등 단일 파일 | `dialogs/` · `components/{viewers,widgets,formats}` 패키지 |
| 테스트 수 | 500+ / 503 passed (2025-10-05) | 1538 collected / 1463 passed / 75 skipped |
| pytest 설정 | `config/pytest.ini` | 루트 `pytest.ini` (config 쪽은 낡은 사본) |
| Key Files 표 | `ModanDialogs.py` (6,511줄) 등 | 현재 파일과 실제 줄 수 |
| Performance Hotspots | 존재하지 않는 `ModanDialogs.py` 줄 번호 | 현재 wait-cursor 위치 6곳 |
| Quick Stats | 27파일 / 24,145줄 / 다이얼로그 11 | 146파일 / 58,855줄 / 다이얼로그 83 |
| cv2 사용처 | `ModanDialogs.py`, `ModanComponents.py` | `dialogs/data_exploration_dialog.py`(동영상 내보내기), `MdHelpers.py`(가용성 확인) |
| InnoSetup | `InnoSetup/Modan2.iss` | `InnoSetup/Modan2.iss.template`에서 생성 |
| 없어진 디렉터리 | `test_script/` 언급 | 존재하지 않아 제거 |

문서에 백틱으로 적힌 경로가 실제로 존재하는지 스크립트로 대조해 확인했다.

## 인덱스 도구 버그

`.index/`를 재생성하려다 **다이얼로그가 0개로 잡히는 것**을 발견했다.
`tools/build_index.py`의 조건이 `"Dialog" in filepath.name`이라 대소문자를
가리는데, 옛 `ModanDialogs.py`는 걸렸지만 현재의 `dialogs/object_dialog.py`
같은 snake_case 파일은 걸리지 않았다. 즉 CLAUDE.md가 안내하는
`search_index.py --dialog` 검색이 조용히 아무것도 반환하지 않는 상태였다.

파일명 소문자 비교 + `dialogs/` 패키지 조건으로 수정: 다이얼로그 0개 → 83개.

## 참고

- 인덱스는 `tests/`까지 포함해 집계한다(146파일/58,855줄). 애플리케이션
  코드만은 약 32,800줄이라 CLAUDE.md에 함께 적어 혼동을 줄였다.
- 재생성 절차는 기존과 동일: `python tools/build_index.py` →
  `python tools/generate_report.py`.
