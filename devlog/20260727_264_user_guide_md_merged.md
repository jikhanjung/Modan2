# `USER_GUIDE.md` / `QUICK_START.md` 를 발행 매뉴얼로 병합

## 날짜
2026-07-27

## 배경

devlog 263에서 `docs/manual/` 로 구조를 분리했지만, 내용 문제는 남아 있었다:
`USER_GUIDE.md`(1184줄)와 `QUICK_START.md` 는 사용자용인데 발행되지 않는 쪽에
있었고, `user_guide.rst` 와 겹치면서도 동일하지 않았다(고유 제목 57개). 단순
중복본이 아니라 **더 두꺼운 쪽** 이라 그냥 지우면 내용이 사라진다.

## 접근 — 옮겨 붙이지 않고 코드로 재판정

`.md` 가 낡았다는 걸 이미 알고 있었으므로(`python3 main.py`, `Modan2-Setup`,
`portable`, 3D "Pan: right-drag"), 고유 섹션을 그대로 옮기지 않고 **양쪽 서술을
코드와 대조** 했다. 그 결과 **양쪽 다 틀린** 항목이 나왔다.

### 변수 (Variables)

- `.rst` 주장: 툴바의 "Add Variable" → **변수 타입(Categorical/Continuous) 선택**
  → 범주형이면 가능한 값 목록 추가. 객체 값은 **객체 테이블의 변수 열을 클릭해
  입력**.
- `.md` 주장: 데이터셋 대화상자에서 추가, 객체 값은 "Properties 필드에
  콤마 구분으로 입력".
- **실제**: 변수에는 타입이 없다. `Modan2.py:1089` 의 `QInputDialog` 는 **이름만**
  받고 `add_variablename()` 을 호출한다. 데이터셋 대화상자에는
  `btnAddVariable`/`btnDeleteVariable` 과 리스트가 있다. 객체 값은 객체
  대화상자에서 **변수마다 별도 `QLineEdit`**(`edtPropertyList`)로 입력하며,
  콤마 결합(`",".join(...)` → `property_str`)은 저장 형식일 뿐 UI가 아니다.
- 어느 쪽도 맞지 않아 새로 썼다.

### 캘리브레이션 (`.rst` 에 아예 없던 기능)

`user_guide.rst` 는 Calibration 모드 버튼을 한 번 언급할 뿐 설명이 없었다.
`.md` 설명을 코드로 검증:

- 저장 위치: `MdObject.pixels_per_mm` — **객체별**(`.md` 주장 맞음). 중심 크기를
  실제 단위로 환산하는 데 쓰인다(`MdModel.py:858`).
- 단위: `nm/um/mm/cm/m` (`calibration_dialog.py:53-57`). `.md` 는 "mm, cm, m 등"
  으로 뭉뚱그렸다.
- 조작: 클릭 두 번이 아니라 **드래그**(press → release, 러버밴드 선;
  `object_viewer_2d.py:1028`, `1104`).
- **`.md` 의 "Batch: Apply to all objects in dataset" 는 존재하지 않는다.**
  일괄 적용 코드가 없다.

검증한 내용으로 새 절을 작성했다.

### 그 밖에 병합한 것

- **데이터셋 편집/정리**: 이름 변경, 트리 드래그로 상위 변경(`Modan2.py:1445`
  `source_dataset.parent = target_dataset`), 객체를 다른 데이터셋으로 드래그
  (`dropEvent` 의 `event.source() == self.tableView` 분기), 그리고 삭제가 파일까지
  지운다는 경고(devlog 228에서 구현).
- **용어집(Glossary)**: `.rst` 어디에도 없었다. Type I/II/III 랜드마크, 중심 크기,
  형상 공간 등. 준랜드마크·결측 랜드마크 항목은 해당 절로 `:ref:` 연결.

### 병합하지 않은 것 — 파일 형식 부록

`.md` 의 TPS/NTS/Morphologika 형식 예시는 **NTS 예시가 실제 파서와 맞지 않는다**.
`components/formats/nts.py` 는 객체 수·변수 수·차원을 담은 **헤더 라인**을 정규식
으로 파싱하는데, `.md` 예시는 `"specimen_001"` 다음에 개수, 좌표가 오는 형태다.
세 형식의 스펙을 제대로 검증하는 건 그 자체로 별도 작업이므로, **틀린 스펙을
발행하느니 싣지 않기로** 했다.

## `QUICK_START.md` → `quick_start.rst`

10분 안내는 종합 안내서와 역할이 달라 별도 페이지로 변환하고 toctree의
`installation` 다음에 넣었다. 낡은 부분을 교정: `Modan2-Setup.exe`/`Modan2.dmg`
→ :doc:`installation` 참조, Linux 소스 설치 절 삭제, `fix_qt_import.py` 삭제,
플레이스홀더 연락처(`[your email]`, `[forum link]`) 삭제, 문서 링크를
`docs/*.md` 경로 대신 `:doc:` 참조로 교체.

## 결과

- `docs/USER_GUIDE.md`, `docs/QUICK_START.md` 삭제.
- `user_guide.rst`: 변수 절 재작성 + 데이터셋 편집·캘리브레이션·용어집 신설.
- `quick_start.rst` 신설, `index.rst` toctree 등재.
- 한국어 번역 110건 추가(user_guide 45, quick_start 65) → **9개 카탈로그 전부
  미번역 0건 유지**.
- en/ko 두 빌드 모두 **build succeeded, 2 warnings** (동일한 무해 경고).

## 남은 일

`developer_guide.md`(1082줄) vs `developer_guide.rst`(876줄) — 같은 상황이 그대로
남아 있다. `.md` 쪽이 더 두껍고(고유 제목 110개, 대부분 개발 환경 설정과 기여
절차), 위와 같은 방식으로 각 항목을 저장소와 대조하며 옮겨야 한다. 사용자용
페이지보다는 우선순위가 낮다.
