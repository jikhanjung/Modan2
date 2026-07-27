# 발행 매뉴얼을 `docs/manual/` 로 분리 — 확장자 규약을 디렉토리로 드러내기

## 날짜
2026-07-27

## 배경

devlog 262에서 확인한 문제: `docs/` 에 Sphinx 소스(`.rst` 8개)와 저장소 전용
Markdown 노트(12개)가 한 디렉토리에 섞여 있었다. `conf.py` 에 `myst_parser` 가
없어 Sphinx는 `.rst` 만 읽으므로, `.md` 12개는 **전부 사이트에 나오지 않았다**.

경계가 보이지 않으니 실제로 비용이 발생했다. `USER_GUIDE.md` 는 `user_guide.rst`
와 겹치는 사용자 매뉴얼인데, 발행되지 않는 쪽이라 조용히 낡았다 — devlog 262에서
`.rst` 만 고친 결과 `.md` 에는 아직 `python3 main.py`, `Modan2-Setup`,
`portable`, 그리고 3D "Pan: right-drag" 오류가 남아 있다.

선택지는 두 가지였다: `myst-parser` 를 붙여 `.md` 도 발행하거나(두 종류를 더
섞는다), 확장자로 확실히 나누거나. 후자를 택하되, **규약을 문서에만 적어 두지 말고
디렉토리로 드러내기로** 했다.

## 변경

`git mv` 로 Sphinx 프로젝트 전체를 `docs/manual/` 로 이동(이력 보존):

```
docs/
├── *.md              ← 저장소 전용 노트 (그대로)
└── manual/           ← Sphinx 프로젝트, .rst 전용, 발행됨
    ├── conf.py, index.rst, installation.rst, user_guide.rst,
    │   faq.rst, troubleshooting.rst, advanced_features.rst,
    │   developer_guide.rst, changelog.rst
    ├── _templates/, locale/ko/LC_MESSAGES/*.po
    └── Makefile, make.bat, requirements.txt, build_all.py, .gitignore, .nojekyll
```

이동으로 깨지는 경로를 함께 고쳤다:

- `conf.py`: `sys.path.insert(0, abspath(".."))` → `"../.."`
  (`version.py` 를 import 해 버전을 단일 출처화하므로, 한 단계 깊어진 만큼 조정).
- `.github/workflows/docs.yml`: `cd docs` → `cd docs/manual`, requirements 경로,
  artifact 경로(`docs/manual/_build/html`), 그리고 **path 트리거를
  `docs/manual/**` 로 축소**. 이제 Markdown 노트를 고쳐도 사이트가 재배포되지
  않는다 — 노트는 사이트의 일부가 아니므로 이게 맞다.
- `pyproject.toml`: ruff exclude `docs/_build` → `docs/manual/_build`.

문서화:

- `docs/README.md` 를 새로 작성. 확장자별 분리를 표로 명시하고, `docs/manual/` 에
  Markdown을 넣으면 아무것도 빌드되지 않고 `docs/` 에 `.rst` 를 넣으면 잡히지
  않는다는 점을 적었다. 저장소 전용 노트 11개의 용도도 표로 정리.
- 기존 `docs/README.md`(Sphinx 프로젝트 안내)는 `docs/manual/README.md` 로 이동해
  갱신. "GitHub Pages 배포 예정(to be set up)"이라는 낡은 문장을 실제 동작 설명으로
  교체하고, 구조 트리에 빠져 있던 faq/troubleshooting/advanced_features 를 추가.
- `CLAUDE.md` 프로젝트 구조에 `docs/` 와 `docs/manual/` 을 추가하고 규약을 명시.

링크 정리:

- 루트 `README.md`: 사용자용 링크를 `docs/QUICK_START.md` / `docs/USER_GUIDE.md`
  등 저장소 파일 대신 **발행 사이트**로 변경(`README.ko.md` 는 이미 그렇게 되어
  있었다). 저장소 전용 노트는 `docs/README.md` 한 곳으로 안내.
- `INSTALL.md`: 같은 방식으로 정리. 겸사겸사 `github.com/yourusername/Modan2` 라는
  플레이스홀더 URL도 실제 저장소로 고쳤다.

## 검증

새 위치에서 두 언어 빌드: **en / ko 모두 build succeeded, 2 warnings** (이동 전과
동일한 무해 경고). `index.html` 의 버전이 `0.2.0-alpha.2` 로 렌더링되어
`conf.py` 의 `version.py` import 가 새 경로에서도 동작함을 확인. 한국어
`user_guide.html` 한글 포함 줄 726.

## 남은 일

이번 이동은 **구조** 를 고친 것이지 내용 유실 문제를 해결한 것은 아니다.
`USER_GUIDE.md`(`user_guide.rst` 대비 고유 제목 57개), `developer_guide.md`(고유
110개), `QUICK_START.md`(대응 `.rst` 없음)는 여전히 발행되지 않는 쪽에 있다.
확인해 보니 이들은 단순 중복본이 아니라 **더 두꺼운 쪽** 이어서 — 예를 들어
"Managing Variables" 는 어느 `.rst` 에도 없다 — 그냥 지우면 내용이 사라진다.
고유 섹션을 `.rst` 로 병합한 뒤 삭제하는 작업을 `TODOs.md` 에 남겼다.
