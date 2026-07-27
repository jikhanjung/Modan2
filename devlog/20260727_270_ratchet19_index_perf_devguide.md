# 래칫 19, 인덱스 경로 기록, 개발자 가이드 교정 — 그리고 내가 만든 회귀 하나

## 날짜
2026-07-27

## 배경

devlog 265를 그 뒤에 이어진 작업들보다 먼저 써 버려서, 아래 네 가지가 어느
devlog에도 들어가지 않았다. 뒤늦게 기록한다.

## 1. 내가 만든 회귀 — 버전 일관성 테스트 (`6941a2d`)

`docs/manual/` 이동(devlog 263)이 `tests/test_version_consistency.py::
test_docs_conf_derives_version` 을 깨뜨렸다. 이 테스트는 경로를
`PROJECT_ROOT / "docs" / "conf.py"` 로 **조립** 하는데, 이동 전 내가 돌린 grep은
리터럴 `"docs/conf.py"` 를 찾았기 때문에 걸리지 않았다.

CI가 3개 플랫폼 모두에서 잡아냈다. 로컬은 아래 xvfb 문제 때문에 그 테스트에
도달하기도 전에 죽고 있어서 보이지 않았다.

**교훈**: 파일을 옮길 때 리터럴 경로 grep만으로는 부족하다. 조립된 경로
(`Path(...) / "x" / "y"`)는 잡히지 않는다.

## 2. 복잡도 래칫 19 (`ca5c1d4`)

265에서 20에 걸었는데, 사용자 지적으로 방향이 바뀌었다: **`tools/` 는 앱 코드가
아니다.** 확인해 보니 `tools/` 는 앱이 import하지도, PyInstaller 빌드에 포함되지도
않는 순수 개발용 코드 탐색 도구였다.

그리고 측정해 보니 **래칫이 20/21에 묶여 있던 것은 앱이 아니라 그 도구들 때문**
이었다. 앱 코드의 실제 천장은 처음부터 19였다(`rotate_gls_to_reference_shape`,
`on_canvas_move`).

| 구분 | 15 초과 | 최대 |
|---|---|---|
| 앱 코드 | 7 | **19** |
| tests/scripts | 3 | 16 |
| tools/ | 0 (2건 리팩터링됨) | — |

`tools/search_index.py::find_wait_cursor_methods` (20)를 쪼개 19로 내렸다:
경로 해석 헬퍼 + 모듈 레벨 `function_spans` / `enclosing_function`. 반복되던
`__import__("ast")` 도 정상 import로 정리.

**동작 보존 검증**: 이 함수는 테스트 커버리지가 없어서, 이전 중첩 함수를 스크립트로
복사해 두고 소스 177개에 대해 두 구현을 비교했다 — **span 불일치 0, wait-cursor
히트 41건 중 불일치 0**.

돌아보면 `tools/` 를 per-file-ignore로 빼는 게 더 곧은 길이었다. 다만 쪼갠 결과
래칫이 앱의 실제 수치를 그대로 반영하게 됐다.

## 3. 인덱스에 경로 기록 (`49603bf`) — 10분+ → 0.96초

래칫 검증 중 `python tools/search_index.py --wait-cursor` 가 **10분이 지나도 끝나지
않는다**는 것을 발견했다. CLAUDE.md가 안내하는 명령이 사실상 못 쓰는 상태였다.

원인: `build_index.py` 가 `file_stats` 를 **basename으로만** 저장한다
(`self.file_stats[str(filepath.name)]`). 그래서 146개 중 **127개가 직접 경로 조회에
실패** 하고 `rglob("**/<name>")` 폴백을 탄다 — `.git`, `build`, `dist`, `AppDir` 를
포함한 전체 트리를 127번 걷는다. 게다가 `/mnt/d` (WSL의 Windows 드라이브 마운트)라
파일시스템 접근이 특히 느리다.

**수정 방향**: basename 키는 도구의 공개 인터페이스다(`--file "object_dialog.py"`
처럼 문서화되어 있다). 그래서 키는 두고 **인덱스에 프로젝트 상대경로를 함께
기록** 해 탐색 자체를 없앴다. 옛 인덱스는 기존 폴백으로 계속 동작한다.

덤으로, 인덱스가 2026-07-21 이후 재생성되지 않아 CLAUDE.md의 통계와 핫스팟이
낡아 있던 것도 드러났다(파일 146→169, 클래스 547→613, 핫스팟 줄 번호 전부 이동,
존재하지 않는 `animate_shape` 항목 잔존). 함께 갱신하고 재생성 명령을 옆에 적었다.

## 4. 개발자 가이드 릴리스·구조 절 교정 (`234a52c`)

TODOs에 남아 있던 "`developer_guide.rst` 에 `python Modan2.py` 가 남았다" 항목을
처리하다가, 문제가 그보다 크다는 것을 발견했다.

**릴리스 절이 버전을 잘못된 곳에 올리라고 안내하고 있었다**:

```rst
1. **Update version** in ``MdUtils.py``:
      PROGRAM_VERSION = "0.1.5"
```

`MdUtils.PROGRAM_VERSION` 은 `version.py` 에서 import하는 값이다. 그대로 따르면
아무 효과가 없거나 `tests/test_version_consistency.py` 가 깨진다. 실제 도구는
`manage_version.py` 다.

설치 프로그램 안내도 틀렸다: `iscc InnoSetup/Modan2.iss` 라고 하는데 저장소에는
`Modan2.iss.template` 이 있고, `build.py` 가 버전·빌드 번호를 채워
`InnoSetup/Output/Modan2_v<version>_build<build>_Installer.exe` 를 만든다.

프로젝트 트리에는 **존재하지 않는 `MdLogger.py`** 와 **삭제된 `ModanDialogs.py`**
가 있었고, 아키텍처 다이어그램도 둘을 그대로 그리고 있었다. 실제 저장소 기준으로
다시 쓰고, 며칠 전 내가 Development Setup에 중복으로 넣었던 트리를 Project
Overview의 것으로 합쳤다.

## 5. 로컬 GUI 테스트가 한 번도 돌지 않고 있었다 (`f170dc6`, `2df5b6d`)

전체 스위트가 코어 덤프해서 xvfb를 설치했는데도 같은 자리에서 죽었다.
`QT_DEBUG_PLUGINS=1` 로 원인을 확인:

```
Cannot load library .../libqxcb.so: (libxcb-icccm.so.4: cannot open shared object file)
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

**CLAUDE.md에 적혀 있던 xcb 라이브러리 7개가 애초에 설치되어 있지 않았다**
(`libxcb-xinerama0`, `libxcb-icccm4`, `libxcb-image0`, `libxcb-keysyms1`,
`libxcb-render-util0`, `libxcb-cursor0`, 그리고 목록에 없던
`libxkbcommon-x11-0`). 설치 후에야 `QApplication` 이 초기화됐고, 이 환경에서
**전체 스위트가 처음으로 완주** 했다 (1882 passed, 10 skipped).

실패 모드가 오해를 부른다는 점이 핵심이다: 공유 라이브러리가 없으면 예외가 아니라
**인터프리터가 중간에 abort** 해서 코드 문제처럼 보인다. `libxkbcommon-x11-0` 은
GitHub 러너에 이미 있어 `test.yml` 에도 없었고, 그래서 CI는 눈치채지 못했다.

### 그리고 함정 하나 더

릴리스 검증 중 pytest가 **멈추기** 시작했다(실패가 아니라 hang). 원인은
`-p no:xvfb` 를 빠뜨린 것 — xvfb를 설치하기 *전에는* 플러그인이
"could not find Xvfb"라며 넘어갔지만, 설치 후에는 자체 Xvfb를 띄우려다 돌아오지
않는다.

```
pytest ... -p no:xvfb   → 4 passed in 1.74s
pytest ...              → 무한 대기
```

CLAUDE.md와 개발자 가이드에 "이 옵션이 왜 필요한지"는 있었지만 **빼먹으면 어떤
증상이 나는지** 가 없어 진단이 오래 걸렸다. 두 문서 모두에 그 증상과
`QT_DEBUG_PLUGINS=1` 진단법을 적었다.
