# Devlog: AST 기반 Qt 분석과 자동 리포트 생성기 추가

- 날짜: 2025-09-10
- 관련 파일: `tools/build_index.py`, `tools/generate_report.py`, `tools/search_index.py`

## 요약
인덱스 품질과 보고서 생성 생산성을 높이기 위해
1) Qt 신호/슬롯 수집을 AST 기반으로 보강했고,
2) 인덱스 JSON을 바탕으로 `.index/INDEX_REPORT.md`를 자동 생성하는 스크립트를 추가했습니다.

## 변경 사항 상세
- AST 기반 Qt 분석 (`tools/build_index.py`)
  - `obj.signal.connect(slot)` 호출을 AST로 파싱하여 객체/시그널/슬롯을 정규화해 저장합니다.
  - 슬롯 인자가 `lambda`, `functools.partial`, `self.on_x` 등의 패턴을 문자열로 안전하게 요약합니다.
  - `pyqtSignal`/`Signal` 정의를 Assign(Call) 노드로 추출하여 시그니처 요약을 함께 기록합니다.
  - QAction 연결(예: `actionSomething.triggered.connect(...)`)은 `actions` 섹션에 별도 기록합니다.
- 자동 리포트 생성기 (`tools/generate_report.py`)
  - `.index/index_summary.json`, `symbols.json`, `qt_signals.json`, `db_models.json`을 읽어
    `.index/INDEX_REPORT.md`를 재생성합니다.
  - 통계 테이블, Dialog/Model 목록, 대형 파일 Top N, 메서드 수 기준 복잡 클래스 Top N, 사용법/툴 섹션을 자동 채웁니다.

## 사용 방법
- 인덱스 빌드(필수):
  - `python tools/build_index.py`
- 리포트 생성:
  - `python tools/generate_report.py`
- 유용한 검색 예시:
  - 타입 지정 심볼 검색: `python tools/search_index.py --symbol ModanMainWindow --type class`
  - 프로젝트 통계: `python tools/search_index.py --stats`
  - 파일 정보: `python tools/search_index.py --file ModanDialogs.py`
  - Qt 연결 검색: `python tools/search_index.py --qt clicked`
  - Wait cursor 사용 지점: `python tools/search_index.py --wait-cursor`

## 기대 효과
- Qt 연결/액션 집계 정확도 향상(람다/partial 포함)으로 UI 이벤트 흐름 파악이 쉬워집니다.
- 리포트 자동화로 수치/목록이 항상 최신 인덱스와 일치합니다(수동 갱신 오류 방지).

## 한계 및 후속 과제
- 매우 동적인 신호 연결(런타임 바인딩/리플렉션)은 여전히 누락될 수 있습니다 → 힌트 주석/메타데이터로 보강 검토.
- 슬롯 해석 고도화(람다 본문 요약, partial 인자 리스트 상세화) 여지.
- 리포트 섹션 확장: 성능 지표(인덱싱 시간/파일 수 변화), TODO/FIXME 추적, 커밋/릴리스 메타 통합.

## 참고
- 인덱싱/검색 도구 전반 사용법 및 주의사항은 `AGENTS.md`의 “Code Index & Search Tools” 섹션에 정리되어 있습니다.
