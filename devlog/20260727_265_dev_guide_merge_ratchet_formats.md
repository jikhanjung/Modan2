# 개발자 가이드 병합, 복잡도 래칫, 파일 형식 레퍼런스

## 날짜
2026-07-27

## 1. `developer_guide.md` 병합 (마지막 미발행 중복본)

### 앞선 수치 정정

devlog 263/264에서 "고유 제목 110개"라고 적었는데 **틀렸다**. `grep "^#"` 이
bash 코드 펜스 안의 주석(`# Clone repository` 등)까지 제목으로 셌기 때문이다.
코드 펜스를 제외하면 실제 제목은 **53개**(`.rst` 는 46개)다.

### 양쪽 다 틀렸던 것들

`.rst` 쪽:

- Python **3.11** (실제 3.12)
- `python Modan2.py` 로 실행하라고 안내 (엔트리포인트가 아님, `main.py` 다)
- 개발 의존성에 `ruff`, `pytest-qt` 를 **"(future)"** 로 표기 — 둘 다 CI에서
  강제 중이다

`.md` 쪽:

- **"새 분석 방법 추가"** 레시피가 `run_analysis(dataset, analysis_method, **params)`
  와 `cbxAnalysisMethod` 콤보를 전제로 쓰여 있다. 실제 시그니처는
  `superimposition_method` / `cva_group_by` / `manova_group_by` 이고, 대화상자에
  있는 건 `comboSuperimposition` 이다. 한 번의 실행이 PCA·CVA·MANOVA를 함께
  계산하므로 **분석 종류별 분기 자체가 없다**.
- **"새 파일 형식 추가"** 레시피가 리더를 `MdUtils.py` 의 함수로 안내한다. 실제로는
  `components/formats/` 의 클래스다.
- 로깅 레시피가 `from MdLogger import setup_logger` — **`MdLogger` 는 존재하지 않는다.**
  실제는 표준 `logging.getLogger(__name__)` + `main.py:setup_logging()`.

### 검증 후 발행한 것

`BaseDialog(parent, title=...)` 와 `create_button_box()` 는 실제와 맞아 대화상자
레시피는 유지하고, 이 프로젝트가 값을 치르고 배운 관례(`@guard_slot`,
`exec_()` 뒤 `deleteLater()`)를 덧붙였다. 그 외 프로젝트 구조, 코드 품질 도구
(ruff/mypy/pre-commit), 나머지 두 레시피 재작성, DB·Qt 디버깅, 유용한 명령어
부록(`scripts/` 의 벤치마크·프로파일러는 실재함을 확인). 한국어 34건.

## 2. 복잡도 래칫 (C901)

### "전에 작업하지 않았나?" — 했지만 잠그지 않았다

devlog 242의 리팩터링 캠페인은 실제로 있었고 최악값을 56 → 21로 내렸다. 그러나
R05에서 C901을 **비게이팅**으로 도입한 뒤 `[tool.ruff.lint.mccabe]` 를 끝내
설정하지 않았다. 즉 결과를 고정하는 장치가 없었다.

그리고 **CHANGELOG의 "모든 애플리케이션 함수가 15 미만"은 사실이 아니었다.**
이번 세션 시작 시점(`dade191`)에 측정하니 15 초과가 이미 12개였다. 이번 세션의
변경 때문이 아니라 처음부터 그랬다. CHANGELOG.md와 changelog.rst 문구를 실제
결과(56 → 21)로 정정했다.

### 20으로 걸고 21짜리를 리팩터링

래칫은 "목표"가 아니라 "천장"이다. 오늘 통과하면서 악화만 막는 값으로 건다.
20에 걸기 위해 유일하게 그 위에 있던 함수를 쪼갰다:

`tools/build_index.py::extract_qt_elements` (21) →
`_extract_qt_by_regex` (파스 실패 시 폴백) / `_extract_signal_definitions` /
`_extract_signal_connections`, 재귀 `expr_to_str` 은 모듈 레벨로 승격.

**동작 보존 검증**: 이 함수는 테스트 커버리지가 없으므로, 구·신 코드로 각각
인덱스를 생성해 `.index/graphs/qt_signals.json` 을 비교했다 — **바이트 단위로 동일**.

결과 분포: `> 18: 3`, `> 15: 11`, `> 10: 52`. 다음 칸(19)은
`tools/search_index.py::find_wait_cursor_methods` (20) 하나가 막고 있다.

### 테스트 환경 주의

로컬에서 전체 스위트가 코어 덤프한다 — 이 WSL 환경에 **Xvfb가 없어서**
(`pytest-xvfb could not find Xvfb`) GUI 테스트가 죽는 것이며, 기존 문제다.
비GUI 모듈은 정상: `test_mdmodel` 294 passed, `test_mdstatistics` 51 passed.
어떤 테스트도 `build_index` 를 import하지 않으므로 이번 리팩터링과 무관하다.
GUI 스위트는 CI(Xvfb 사용)가 커버한다.

## 3. docs 배포 트리거의 구멍 (내가 만든 것)

devlog 263에서 `docs.yml` 의 path 트리거를 `docs/manual/**` 로 좁혔는데,
`conf.py` 는 버전을 `version.py` 에서 단일 출처화한다. 즉 **버전 범프 시 docs
워크플로가 아예 실행되지 않아** 사이트에 옛 버전이 남는다 — 릴리스마다 발생할
문제였다. 트리거에 `version.py` 를 추가했다.

브랜치 보호(필수 상태 체크)는 손대지 않았다. `main` 에는 보호가 **아예 없고**,
켜면 PR 워크플로가 강제되어 현재의 commit-to-main 방식이 막힌다. 워크플로 자체를
바꾸는 결정이라 사용자 판단 영역이다.

## 4. 파일 형식 레퍼런스 (devlog 264에서 보류했던 것)

devlog 264에서 `.md` 의 형식 부록을 "NTS 예시가 파서와 안 맞는다"는 이유로 병합
하지 않았다. 이번에 파서를 읽어 실제 스펙을 확인하고 새로 썼다.

- **TPS**: `LM=<n>` + 좌표, 키는 `ID`/`IMAGE`/`COMMENT`/`SCALE`
  (`tps.py:121-129`), 주석은 `#`/`"`/`'`. 곡선은 `CURVES=<k>` + k×(`POINTS=<m>` +
  좌표) — 읽기/쓰기 모두 지원.
- **NTS**: NTSYS 행렬 헤더. 정규식(`nts.py:126`)이 파싱하는 필드는 순서대로
  행렬 종류, 행 이름 플래그가 붙은 객체 수, 열 이름 플래그가 붙은 변수 수,
  결측값 표시, `DIM=<d>`. 행 이름 플래그 `L`/`B`/`E` 는 이름 위치를 뜻하고,
  랜드마크 개수는 변수 수 ÷ DIM. **`.md` 의 예시(이름 줄 → 개수 → 좌표)는 이
  헤더가 아예 없어 틀렸다.**
- **Morphologika**: `[names]` 와 `[rawpoints]` 필수(`morphologika.py:134`),
  선택 섹션은 `[labels]`, `[labelvalues]`, `[wireframe]`, `[polygons]`,
  `[images]`, `[pixelspermm]`.

한국어 15건 추가.

## 결과

- `docs/*.md` 의 미발행 중복본이 모두 사라졌다. 남은 `.md` 9개는 순수 저장소 전용
  노트(빌드/릴리스/품질 가이드 등)다.
- 한국어 카탈로그 **전부 미번역 0건** 유지.
- en/ko 두 빌드 모두 build succeeded, 2 warnings.
- `ruff check .` 통과 (C901 래칫 20 포함).
