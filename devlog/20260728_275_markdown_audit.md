# 저장소 Markdown 전수 점검

## 날짜
2026-07-28

## 배경

devlog 274에서 설치·릴리스 문서를 정리한 뒤, 남은 `.md` 전체를 코드·워크플로와
대조했다. 이번에는 특정 주제가 아니라 **전수 점검** 이다.

방법은 "알려진 stale 마커"를 grep한 것이다: 삭제된 모듈 이름(`ModanDialogs.py`),
틀린 진입점(`python Modan2.py`), 옛 설정 경로(`~/.modan2`), 존재하지 않는 자산명
(`Modan2-Setup`), 플레이스홀더(`yourusername`), 그리고 버전·Python 버전 주장.

## 삭제 (3)

### `AGENTS.md`, `GEMINI.md`

`CLAUDE.md` 와 같은 역할(에이전트용 저장소 안내)의 세 번째·두 번째 사본이었고,
둘 다 낡아 있었다. `AGENTS.md` 는 구조 설명이 **뒤집혀** 있었다 —
"`Modan2.py` (GUI entry) and `main.py` (build entry)". 실제는 반대다. 둘 다
`ModanDialogs.py`(0.1.5에서 삭제)를 핵심 모듈로 나열하고 `python Modan2.py` 로
실행하라고 했다.

같은 내용을 세 벌 유지하면 두 벌은 반드시 낡는다. `CLAUDE.md` 만 남긴다.

### `devlog/README.md`

devlog 색인인데 **147에서 멈춰 있었다.** 실제 devlog는 269개(최대 274)이므로
약 127개가 빠져 있었고, 제목도 "Recent Sessions (October 2025)" 그대로였다.

손으로 채우면 다음에 또 끊긴다. 파일명이 `날짜_번호_제목.md` 로 자기설명적이라
디렉터리 목록 자체가 색인 역할을 하므로 삭제했다.

## 수정

### `README.md` / `README.ko.md` — Python 버전

배지와 본문 모두 "Python 3.11+", "CI runs the test suite on 3.11 and 3.12".
**실제로는 3.12 전용** 이다 — `test.yml` 의 매트릭스가 `['3.12']` 이고 모든
워크플로가 3.12다. devlog 248이 3.11을 버렸고 CHANGELOG 0.2.0-beta.1에도 적혀
있는데 첫 화면만 남아 있었다.

### `HANDOFF.md`

"Current state (2026-07-20): v0.1.6, 1404 passed / 75 skipped, coverage 59%" →
0.2.0-beta.2, 1882/10, 67%로 갱신. 여기 적힌 **"각 릴리스는 patch만 올린다"는
관례도 더는 맞지 않는다** — 0.2는 pre-release 시리즈다.

`RELEASE_NOTES.md` 삭제가 "deferred, do it next session" 으로 남아 있었는데 그
파일은 devlog 269에서 이미 사라졌다. 열린 작업은 `TODOs.md` 가 관리한다는 것도
명시했다.

### `docs/BUILD_GUIDE.md`

`build.py` 를 읽어 실제 산출물과 대조했다.

- 헤더의 `Version: 0.1.5-alpha.1` → 버전을 박지 않고 `<version>` 플레이스홀더로.
  `build.py` 가 `version.py` 를 읽으므로 문서가 버전을 알 필요가 없다.
- **설치 관리자 경로가 틀렸다**: `Output/Modan2-Setup-{VERSION}.exe` 는 존재한 적
  없는 이름이다. 실제는 `InnoSetup/Output/Modan2_v{VERSION}_build{BUILD}_Installer.exe`
  (템플릿의 `OutputBaseFilename`).
- onefile/onedir 산출물 이름과 `buildlocal` 접미사는 **맞았다** —
  `BUILD_NUMBER` 의 기본값이 `"local"` 이라 `build{BUILD_NUMBER}` 가
  `buildlocal` 이 된다. 틀린 것만 고쳤다.

### `docs/architecture.md`

이번 세션 작업과 정면으로 어긋나는 절이 있었다.

- **"Application Settings (QSettings)"** — 조직명 `"YourOrganization"` 까지 적혀
  있었다. QSettings는 devlog 272에서 제거했고, 애초에 그 조직명을 쓴 적도 없다.
  JSON 설정 파일과 `SettingsWrapper` 의 실제 동작으로 다시 썼다.
- **환경 변수 절에 `MODAN_DB_PATH`** — 앱에 그런 변수는 없다(grep으로 확인).
  devlog 262가 발행 매뉴얼에서 같은 허구를 걷어냈는데 여기 남아 있었다.
  "앱은 자기 환경 변수를 읽지 않는다"로 고치고 실제 수단인 CLI 플래그를 적었다.
- **통계** (98 파일 / ~28,000줄) 와 **커버리지 표** (962 tests, MdModel 70%) 를
  실측값으로 교체: 앱 코드 68 파일 / ~30,800줄, 테스트 86 파일 / 1892개,
  MdModel 92%, 전체 67%.

### `docs/performance.md` — 고치지 않고 시점을 명시

2025-10-06에 0.1.5-alpha.1에서 측정한 벤치마크다. **재측정 없이 숫자를 갱신하면
거짓이 된다.** 헤더를 "측정 시점" 으로 바꾸고, 수치가 현재 빌드를 설명하지
않는다는 것과 "Known Performance Issues" 의 상태도 재확인하지 않았다는 것을
명시했다. 재측정 명령(`scripts/benchmark_analysis.py` 등, 실재 확인)도 적었다.

### `docs/TEST_RELEASE_PLAN.md`, `docs/SCREENSHOT_GUIDE.md`

각각 "Ready to Execute"(2025-10에 이미 실행됨), "TODO - Requires GUI
environment"(여전히 미완). 상태를 사실대로 적었다.

### grep이 마지막에 잡아낸 셋

주제별로 훑을 때는 안 보이다가 마커 전수 검색에서 나왔다.

- **`.github/PULL_REQUEST_TEMPLATE.md`** — 체크리스트에 "launches successfully
  with `python Modan2.py`". **모든 PR에 표시되는 템플릿** 이다.
- `WINDOWS_DEFENDER_NOTICE.md` — 같은 오류.
- `config/README.md` — 커버리지 표에 `ModanDialogs.py: 21%`. 실측값으로 교체.

## 결과

최종 grep에서 남은 stale 마커는 **전부 devlog와 CHANGELOG/TODOs의 역사 기록**
이다(과거에 그랬다는 서술이므로 유지가 맞다).

루트 `.md` 는 9개에서 6개로 줄었다: `README.md`, `README.ko.md`, `CHANGELOG.md`,
`CLAUDE.md`, `HANDOFF.md`, `TODOs.md`, `WINDOWS_DEFENDER_NOTICE.md`.

## 관찰

이번 점검에서 고친 것의 대부분은 **한 번 옳게 쓰인 뒤 코드가 움직인 문서** 가
아니라, **처음부터 검증되지 않은 문서** 였다. `Modan2-Setup-{VERSION}.exe`,
`MODAN_DB_PATH`, `"YourOrganization"`, `AGENTS.md` 의 뒤집힌 진입점 설명 —
이것들은 낡은 것이 아니라 애초에 사실이 아니었다. devlog 262가 발행 매뉴얼에서
같은 결론에 도달했다.

문서를 쓸 때 코드를 열어보는 것과, 문서를 나중에 갱신하는 것은 다른 문제다.
후자는 이런 점검으로 잡히지만 전자는 잡히지 않는다.
