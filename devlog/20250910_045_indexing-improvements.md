# Devlog: 코드 인덱싱/검색 도구 개선

- 날짜: 2025-09-10
- 관련 파일: `tools/build_index.py`, `tools/search_index.py`, `AGENTS.md`

## 요약
코드베이스 탐색 정확도와 범위를 높이기 위해 인덱싱/검색 툴을 개선했습니다. 테스트와 도구 스크립트까지 인덱스에 포함하고, Dialog 위젯 추출 정확도, wait cursor 탐지, 검색 타입 필터 동작을 보강했습니다.

## 변경 사항
- 재귀 인덱싱 도입
  - 기존: 리포지토리 최상위의 `*.py`만 스캔
  - 변경: `rglob('**/*.py')`로 재귀 스캔, 다음 폴더 제외: `.index/`, `dist/`, `build/`, `__pycache__/`
  - 효과: `tests/`, `tools/`, 서브패키지(`OBJFileLoader/`) 등 포함 → 통계/검색 신뢰도 개선
- Dialog 위젯/레이아웃 추출 정밀화
  - 기존: 파일 전체에서 정규식으로 긁어 다이얼로그별 요소가 혼재할 수 있었음
  - 변경: 클래스 블록(라인 범위) 내에서만 `self.<name> = Q*`/`Q*Layout(` 패턴 매칭
  - 효과: 각 Dialog 카드의 위젯/레이아웃 목록 정확도 향상
- 검색 타입 맵핑 수정
  - `--type` 인자(`class/function/dialog`)를 내부 키(`classes/functions/dialogs`)로 매핑
  - 예: `python tools/search_index.py --symbol ModanMainWindow --type class`
- Wait cursor 사용 탐지 고도화
  - 기존: 하드코딩된 예시 반환
  - 변경: 소스에서 `QApplication.setOverrideCursor`/`restoreOverrideCursor` 라인 스캔 → AST로 둘러싼 함수/메서드 이름 추정해 `{file, method, line}` 보고
  - 성능: 텍스트 프리필터로 AST 파싱 범위를 최소화
- 인덱스 디렉터리 보장
  - `.index/symbols`, `.index/graphs` 생성 후 파일 저장

## 재생성 결과(현재 리포지토리)
- 명령: `python tools/build_index.py`
- 통계:
  - files: 85
  - classes: 194
  - functions: 1,533
  - dialogs: 11
  - db_models: 5
  - qt_signals: 28
  - qt_connections: 284
  - total_lines: 35,090

## 사용 방법(요약)
- 인덱스 빌드: `python tools/build_index.py`
- 검색 도움말: `python tools/search_index.py --help`
- 타입 지정 심볼 검색: `python tools/search_index.py --symbol ModanMainWindow --type class`
- 프로젝트 통계: `python tools/search_index.py --stats`
- 파일 정보: `python tools/search_index.py --file ModanDialogs.py`
- Qt 연결 검색: `python tools/search_index.py --qt clicked`
- Dialog 위젯: `python tools/search_index.py --dialog NewAnalysisDialog`
- Wait cursor 사용 지점: `python tools/search_index.py --wait-cursor`

## 한계와 다음 단계
- Qt 신호/슬롯: 현재 정규식 기반으로 동적 연결(람다/partial) 일부 누락 가능 → AST 기반/기호해석 보강 검토
- Wait cursor: 메서드 경계 추정은 AST line span에 의존 → 중첩/데코레이터 케이스 정밀화 여지
- 보고서 자동화: `.index/index_summary.json`을 사용해 `INDEX_REPORT.md` 수치를 자동 삽입하는 생성 스크립트 도입 검토

## 문서화
- `AGENTS.md`에 “Code Index & Search Tools” 섹션 추가: 포함/제외 범위, 타입 맵핑, wait cursor 스캔 동작을 명시

