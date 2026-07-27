# 변경 이력을 CHANGELOG.md 하나로 통일 (myst include)

## 날짜
2026-07-27

## 배경

CTHarvester에서 같은 문제를 다루며 나온 지적을 Modan2에도 적용했다: **버전이
올라가면 매뉴얼의 변경 이력도 따라가야 하는데, 손으로 관리하는 사본이 두 개면
반드시 어긋난다.**

Modan2도 `CHANGELOG.md` 와 `docs/manual/changelog.rst` 를 각각 손으로 써 왔고,
**이미 양방향으로 어긋나 있었다**:

| | 한쪽에만 있는 버전 |
|---|---|
| `CHANGELOG.md` 에만 | `0.1.5`, `0.1.5-beta.1`, `0.1.5-beta.2` |
| `changelog.rst` 에만 | `0.1.0`, `0.1.1`, `0.1.2` |

공통은 10개뿐이었다. 즉 발행된 매뉴얼은 0.1.5 계열 세 릴리스를 통째로 빠뜨린 채
보여 주고 있었고, 반대로 초기 세 버전은 `CHANGELOG.md` 에 없었다.

이 프로젝트는 이미 "단일 진실 공급원"을 원칙으로 삼고 있다(`version.py` →
앱/`conf.py`/설치 파일명, `tests/test_version_consistency.py` 가 강제). 변경 이력만
예외였다.

## 선택지와 판단

- **A. 두 파일을 유지하되 자동 동기화** — Markdown → reStructuredText 변환이
  들어가고, 그 변환이 틀리면 조용히 깨진다.
- **B. `CHANGELOG.md` 하나로 통일** — `myst_parser` 로 매뉴얼이 저장소 루트의
  정본을 포함한다. 손으로 쓰는 이력이 하나가 되어 어긋날 수 없다.
- **C. 지금 빠진 항목만 손으로 추가** — 구조가 그대로라 다음 릴리스에 또 빠진다.

**B**를 택했다. `CHANGELOG.md` 는 저장소 루트에 있어야 하는 파일이다 — 기여자가
거기서 편집하고, `release.yml` 이 GitHub 릴리스 본문을 거기서 추출한다. 매뉴얼이
사본을 두는 대신 그것을 포함하는 것이 맞다.

## 작업

1. **사라질 내용을 먼저 이관.** `changelog.rst` 에만 있던 `0.1.0`/`0.1.1`/`0.1.2`
   를 `CHANGELOG.md` 로 옮겼다. 이 단계를 건너뛰었으면 전환과 동시에 세 버전이
   발행 문서에서 사라졌을 것이다.
   - 다만 rst 끝의 **"Upcoming Features" 로드맵은 이관하지 않았다.** 비대칭 분석,
     다크 모드, GPU 가속 프로크루스테스 등 존재하지 않는 기능 목록으로, 이번
     세션 내내 걷어낸 "검증되지 않은 주장"과 같은 부류다. 같은 문단이 이미
     GitHub Issues를 가리키고 있어 그 링크가 역할을 대신한다.
2. `myst-parser` 를 `docs/manual/requirements.txt` 에 추가하고 `conf.py` 확장에
   등록. 둘 다 "이 include 하나만을 위한 것"이라는 주석을 달았다.
3. `changelog.rst` 를 `../../CHANGELOG.md` 를 include하는 형태로 교체. 페이지 제목은
   Markdown의 `# Changelog` 가 맡으므로 rst 쪽에 별도 제목을 두지 않았다.
4. **한국어 재번역** (아래).
5. `docs/README.md` 와 `docs/manual/README.md` 의 규칙 문구 수정.

### 부작용 하나 — myst가 `.md` 를 전부 페이지로 만든다

`myst_parser` 를 켜자 `docs/manual/README.md` 가 "toctree에 없는 문서" 경고를
냈다. Sphinx가 이 디렉토리의 `.md` 를 문서로 인식하기 시작한 것이다.
`conf.py` 의 `exclude_patterns` 에 `README.md` 를 넣어 해결했다 — 이것이 ".rst만
발행" 규칙을 유지하는 방법이기도 하다.

## 한국어 번역 — Modan2 특유의 비용

CTHarvester에 없었을 비용이 여기 있었다. `changelog.po` 에 번역 230건이 있었는데,
msgid가 rst 본문에서 Markdown 본문으로 바뀌면서 대부분 무효화됐다(재동기화 후
미번역 313건).

그런데 세어 보니 **313건 중 129건은 원문 자체가 한국어** 였다 — `CHANGELOG.md` 의
구버전 항목들이 한국어로 작성되어 있다. 이런 항목은 msgstr이 비어 있어도 Sphinx가
원문으로 fallback하므로 **한국어로 정확히 표시된다.** 번역이 실제로 필요한 것은
영어 원문 184건(19,170자)이었고, 이를 모두 번역했다.

결과: 영어 원문 기준 **미번역 0건**, 한국어 원문 129건은 의도적으로 비워 둠.

## 검증

- en/ko 두 빌드 **build succeeded, 2 warnings** (기존과 동일한 무해 경고).
- 발행된 변경 이력 페이지에 **16개 버전 전부** 렌더링 — 이관한 0.1.0~0.1.2와
  매뉴얼에 없던 0.1.5 계열이 한곳에 모였다.
- 페이지 제목의 버전(`Modan2 0.2.0-beta.1 documentation`)은 여전히 `conf.py` 가
  `version.py` 에서 가져온다.

## 결과

이제 릴리스 노트를 쓰는 곳은 `CHANGELOG.md` 한 곳이다. 버전을 올리고 그 절을
작성하면 GitHub 릴리스 본문과 발행 매뉴얼이 **같은 원본에서** 나온다. 다음 릴리스에
매뉴얼 쪽을 빠뜨릴 방법이 없어졌다.
