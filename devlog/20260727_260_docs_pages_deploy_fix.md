# 문서 배포 워크플로 복구 — GitHub Pages가 411커밋 뒤에 멈춰 있던 문제

## 날짜
2026-07-27

## 배경

"매뉴얼에 semi-landmark / missing landmark 내용이 들어갔는지, GitHub Pages 포함해서
확인" 요청에서 출발. 소스 문서는 멀쩡했지만 **게시된 사이트에는 하나도 반영되어 있지
않았다.**

확인 결과:

- 로컬 `docs/user_guide.rst`(983줄)에는 `.. _semi-landmark-curves:` 섹션(Curve 모드,
  snap-to-curve, smooth, 커브 편집/테이블)과 결측 랜드마크 섹션 2곳
  (`Missing Landmarks`, `.. _analysis-missing-landmarks:` EM 대치 루프)이 모두 존재.
  커밋 `be09357`(2026-07-25)에서 작성됨.
- 반면 게시본 `en/user_guide.html`의 semi-landmark/curve 언급은 **0건**. missing은
  21건 있었지만 내용이 **틀렸다** — 존재하지 않는 *"Right-click → Mark as Missing"*
  UI를 설명하고, 대치 방식도 옛 서술이었다.
- 마지막 성공 배포는 `0b5255c`, 현재 main보다 **411 커밋** 뒤.

## 원인 — 버그 2개가 겹쳐 있었다

`.github/workflows/docs.yml`이 2026-07-24부터 **매 실행 실패**(최근 10회 전부).
두 원인이 같은 날 들어왔고, 첫 번째가 두 번째를 가리고 있었다.

### 1) sphinx pin vs Python 버전 불일치

Dependabot #22가 `docs/requirements.txt`의 sphinx를 `>=9.1.0`으로 올렸는데,
sphinx 9.1.0은 **Python >=3.12**를 요구한다. 그런데 `docs.yml`만 `python-version: '3.11'`
에 남아 있었다 (`80c5006`에서 CI 전반은 3.11을 버렸지만 docs.yml은 따라가지 않음).

```
ERROR: Could not find a version that satisfies the requirement sphinx>=9.1.0
ERROR: No matching distribution found for sphinx>=9.1.0
```

pip 설치 단계에서 죽었기 때문에 sphinx-build는 아예 실행되지 않았다.

### 2) `docs/requirements.txt`에 `semver` 누락 (가려져 있던 버그)

`b52bab0`에서 `docs/conf.py`가 버전을 단일 출처화하며 `from version import __version__`
를 추가했는데, `version.py`는 `import semver`를 한다. `semver`는 루트
`requirements.txt`에만 있고 `docs/requirements.txt`에는 없다. docs 빌드는 루트
requirements를 설치하지 않으므로:

```
sphinx.errors.ConfigError: There is a programmable error in your configuration file:
  File "/mnt/d/projects/Modan2/version.py", line 6, in <module>
    import semver
ModuleNotFoundError: No module named 'semver'
```

1)만 고쳤으면 그대로 2)에서 다시 깨졌을 것이다. 로컬 재현으로 미리 잡았다.

## 변경

- `.github/workflows/docs.yml`: `python-version: '3.11'` → `'3.12'`
  (나머지 6개 워크플로와 일치).
- `docs/requirements.txt`: `semver>=3.0.0` 추가 (루트 requirements와 동일한 하한),
  왜 필요한지 주석 명시.

## 검증

Python 3.12 + `docs/requirements.txt`로 깨끗한 venv를 만들어 워크플로와 동일한 두
빌드를 로컬 실행:

- `sphinx-build -b html -D language=en .` → **build succeeded, 2 warnings**
- `sphinx-build -b html -D language=ko .` → **build succeeded, 2 warnings**

(경고 2건은 `developer_guide.rst:180`의 ASCII 다이어그램을 python으로 하이라이트하려다
난 `misc.highlighting_failure` — 무해.)

산출물 내용 확인 (`user_guide.html`, 게시본 대비):

| 항목 | 게시본(구) | 새 빌드 |
|---|---|---|
| semi-landmark / curve | 0 | 52 |
| "Snap to curve" | 0 | 2 |
| "Mark as Missing" (없는 UI) | 있음 | **0** |
| "Add Missing" (실제 UI) | 0 | 1 |

`index.html`의 버전도 `0.2.0-alpha.2`로 정상 렌더링 (conf.py의 version.py 단일 출처가
동작한다는 확인).

Pages 설정도 함께 확인: `build_type: "workflow"` — 즉 Actions 워크플로가 실제 배포
경로이고, `gh-pages` 브랜치는 옛 브랜치 배포의 잔재다. 워크플로를 고치면 실제로 반영된다.
docs.yml이 쓰는 액션 4종(checkout@v7, setup-python@v7, upload-pages-artifact@v5,
deploy-pages@v5)은 모두 현재 최신 태그로 유효함을 확인했다.

## 남은 일

- **한국어 번역이 오래됨.** `docs/locale/ko/LC_MESSAGES/user_guide.po`는 2025-10-04이
  마지막이라 semi-landmark/curve msgid가 **0건**이다. 이번 배포로 한국어 페이지에도
  섹션은 뜨지만 신규 내용 52줄은 전부 영어 fallback이다. `sphinx-intl update` + 번역 필요.
- **toctree의 다른 페이지 미갱신.** `advanced_features.rst`(curve 0건), `faq.rst`(1건),
  `troubleshooting.rst`(0건)은 `be09357` 대상이 아니었다. 사용자가 실제로 찾아볼 FAQ/
  트러블슈팅에 semi-landmark 항목이 없다.
- docs 빌드가 이렇게 오래(약 이틀, 커밋 6개) 조용히 깨져 있었다는 점 자체가 문제다.
  docs.yml은 필수 상태 체크가 아니라 실패해도 눈에 띄지 않았다.
