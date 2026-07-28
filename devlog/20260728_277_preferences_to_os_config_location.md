# 설정 파일을 OS 설정 위치로 — PaleoBytes 공통 규약 적용

## 날짜
2026-07-28

## 배경

P03 3단계다. devlog 272는 `preferences.json` 을 데이터 디렉터리에 넣었는데
("사용자가 소유한 모든 것을 한 디렉터리에"), P03에서 **부트스트랩 순환** 때문에
그 결정을 되돌려야 한다는 것이 드러났다 — 데이터 위치를 설정 가능하게 만들면,
설정 파일이 데이터 디렉터리 안에 있을 수 없다. 위치를 알려고 설정을 읽어야 하고
설정을 읽으려고 위치를 알아야 하기 때문이다.

## 방향 전환 — `QStandardPaths` 로 한 번 만들었다가 되돌렸다

처음에는 P03 초안대로 Qt의 `QStandardPaths.AppConfigLocation` 으로 구현했다.
그 과정에서 **초기화 순서 함정** 을 발견해 지연 평가 함수로 우회했다.

그 뒤 PaperMeister 쪽에서 같은 작업을 하며 정리한 규약
(`../PaperMeister/devlog/20260728_R02_Config_File_Location_Convention.md`, 제품군
공통 문서)에 맞추기로 하고 **`platformdirs` 로 다시 만들었다.**

### Qt를 쓰지 않는 이유 셋

1. **초기화 순서 (Modan2 고유).** `MdUtils` 는 `main.py` 가 `QApplication` 을
   만들기 전에 import된다 — 로깅이 먼저 구성되고, 그 안에서 `MdUtils` 를 끌어온다.
   Qt의 앱별 위치는 조직명·앱명에서 파생되는데 그 시점에는 설정돼 있지 않다.
   실측:

   | 시점 | `AppConfigLocation` |
   |---|---|
   | `QApplication` 없음 | `~/.config` |
   | 생성했지만 이름 설정 전 | `~/.config` |
   | 이름 설정 후 | `~/.config/PaleoBytes/Modan2` |

   즉 모듈 상수로 즉시 평가하면 **다른 모든 애플리케이션과 공유하는 설정 루트** 가
   조용히 박힌다. `platformdirs` 는 순수 파이썬이라 이 순서 의존이 없다.

2. **macOS 관례.** Qt는 `~/Library/Preferences` 로 보내지만 Apple은 그곳을
   defaults(plist) 시스템의 자리로 둔다. 앱이 직접 관리하는 JSON은
   `~/Library/Application Support` 가 맞고 `platformdirs` 가 그쪽을 준다.
   **두 도구를 섞으면 제품군의 macOS 경로가 여기서 갈린다.**

3. **경로 모듈에 GUI 툴킷을 끌어들이지 않는다.** Modan2는 GUI 전용이라 이 이유
   자체는 약하지만, 제품군에서 한쪽으로 통일하는 편이 위 2를 피한다.

## 결과 경로

```
Windows   %LOCALAPPDATA%\PaleoBytes\Modan2\preferences.json
macOS     ~/Library/Application Support/PaleoBytes/Modan2/preferences.json
Linux     $XDG_CONFIG_HOME (또는 ~/.config)/PaleoBytes/Modan2/preferences.json
```

Linux는 실행해 확인했고, Windows/macOS는 `platformdirs` 소스에서 확인했다
(`windows.user_config_dir` → `user_data_dir` → `CSIDL_LOCAL_APPDATA`,
`macos` → `_base_user_app_support_dir`).

**벤더 세그먼트는 직접 붙였다.** `platformdirs` 는 `appauthor` 를 Windows에서만
반영한다 — macOS·Linux 관례에 벤더 계층이 없어 의도적으로 무시한다. 하지만 이
앱이 소유한 다른 모든 경로(설치 디렉터리, 시작 메뉴, 데이터 디렉터리)가
`PaleoBytes` 아래로 묶여 있으므로, 설정만 세 플랫폼 중 둘에서 갈라지는 쪽이 더
나쁘다. 벤더 계층이 금지된 것이 아니라 필수가 아닐 뿐이다.

## 이전(migration)

**자동이다.** 데이터 디렉터리 이전을 자동화하면 안 되는 것과 정확히 반대편에
있다 — 1KB 미만이고 실패해도 창 위치가 초기화될 뿐이다.

이전 위치를 최신 순으로 훑는다:

1. `~/PaleoBytes/Modan2/preferences.json` (0.2.0-beta.2, devlog 272)
2. `~/.modan2/config.json` (그 이전)

R02가 정한 세 가지를 그대로 지켰다:

- **첫 읽기에 건다** — `MdAppSetup._load_settings()` 의 `open()` 직전. Modan2는
  설정을 읽는 곳이 이 한 곳뿐이고 `scripts/`·`tools/`·`migrate.py` 중 설정을 읽는
  것이 없어, R02가 경고한 "진입점 누락으로 설정 없이 도는 실행" 은 해당되지 않는다.
- **이미 있으면 덮지 않는다** — 오래된 레거시가 현재 설정을 되돌리면 조용한 회귀다.
- **원본을 지우지 않는다** — 비용이 0이고 옛 빌드로 되돌려도 설정을 찾는다.

## 잡아낸 것 — 빌드가 깨질 뻔했다 ★

`platformdirs` 는 전이 의존성으로 **개발 환경에 이미 설치돼 있었다.** 그래서
로컬에서는 전부 통과한다.

그런데 CI와 빌드는 `pip install --require-hashes -r requirements-<os>.lock` 으로
설치하고, **세 lockfile 어디에도 `platformdirs` 가 없었다.** 선언만 하고 lock을
갱신하지 않았다면 frozen 빌드가 `import platformdirs` 에서 죽는다 —
**로컬 테스트로는 절대 드러나지 않는 종류의 실패다.**

R02 체크리스트의 첫 항목("`platformdirs` 의존성 추가 (lock 갱신)")이 정확히 이걸
잡았다. 규약 문서에 체크리스트를 둔 값어치가 여기서 나왔다.

`uv pip compile` 로 세 lock을 재생성했다. diff는 `platformdirs==4.11.0` 한 줄과
해시뿐이고 다른 패키지의 버전 드리프트는 없다. `--require-hashes` 드라이런으로
해석 가능한 것도 확인했다.

PyInstaller 번들링은 별도 조치가 필요 없다 — `platformdirs/__init__.py` 가
`if sys.platform == "win32": from platformdirs.windows import ...` 식의 **정적**
import 세 개를 쓰므로 분석기가 전부 따라간다. 혹시 누락돼도 CI의 frozen 스모크
테스트(`main.py --self-test`)가 3개 플랫폼에서 즉시 잡는다.

## 로그는 옮기지 않았다

두 가지 이유다. **부트스트랩** — 로깅은 설정을 읽기 전에 세팅되므로(`main.py:98`)
로그 위치를 설정에 따르게 하려면 초기 로그를 버리거나 이중 초기화를 해야 한다.
그리고 **조사 편의** — 장애를 볼 때 로그가 데이터와 한 폴더에 있으면 그곳만 보면
된다.

## 조직명에 대한 정정

devlog 276 직후 `main.py` 의 `setOrganizationName` 을 `"Modan2 Team"` 에서
`COMPANY_NAME`(=`PaleoBytes`)으로, 앱명도 `PROGRAM_NAME` 으로 통일했다
(`d36a319`). 당시에는 `QStandardPaths` 가 이 이름들로 경로를 만들기 때문에
**P03의 선행 조건** 이라고 적었다.

`platformdirs` 로 바꾸면서 **그 선행 조건은 사라졌다** — 경로가 Qt 이름에
의존하지 않는다. 수정 자체는 그대로 둔다. 조직명이 `"Modan2 Team"`,
`"Modan2Team"`(devlog 272에서 삭제한 죽은 QSettings 헬퍼), `PaleoBytes` 세
가지로 갈려 있던 것은 그 자체로 고칠 값어치가 있었다.

## 검증

- 전체 스위트 **1886 passed, 10 skipped**.
- 신규 테스트: 데이터 디렉터리 밖에 있는가 / 벤더 세그먼트가 있는가 /
  `platformdirs` 루트 아래인가 / 최신 레거시에서 복사 / 오래된 레거시로 폴백 /
  이미 있으면 덮지 않음 / 신규 설치는 무동작.
- **네 시나리오 end-to-end** (beta.2 사용자, beta.1 이하, 둘 다 존재, 신규 설치)를
  가짜 홈으로 확인.
- **실제 앱 부팅에서 이관 확인** — 로그에
  `Migrated preferences from ~/PaleoBytes/Modan2/preferences.json to
  ~/.config/PaleoBytes/Modan2/preferences.json`, `diff` 결과 동일, 원본 유지.
- EN/KO 매뉴얼 빌드 성공. 한국어 12건 번역, 3개 카탈로그 미번역·fuzzy 0.

## 문서

매뉴얼 3곳(`faq`, `troubleshooting`, `advanced_features`)의 설정 경로를 플랫폼별
표로 바꿨다. `CLAUDE.md` 의 "사용자 파일 위치" 표에서 설정을 빼고 왜 밖에 있는지
적었다.

CHANGELOG는 **`[Unreleased]` 에 새 항목을 넣었고 `[0.2.0-beta.2]` 절은 건드리지
않았다.** 그 절은 이미 게시된 GitHub 릴리스의 본문이므로, 사후에 고치면 배포된
내용과 저장소가 어긋난다.

## 남은 것

P03의 1·2·4단계 — 저장 위치 설정 가능화, 이전 기능, 기본값을 Documents로.
4단계 전에 OneDrive 실측이 필요하다는 판단은 그대로다(P03 위험 5).
