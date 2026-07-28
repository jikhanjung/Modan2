# 설치 위치·설치 정체성 정리와 설정 파일 이전

## 날짜
2026-07-28

## 배경

0.2.0-beta.1 릴리스 직후, 설치 관리자 설정을 확인하는 데서 시작해 "사용자의
파일이 어디에 놓이는가"를 전반적으로 정리하게 됐다. 확인해 보니 앱이 쓰는
위치가 **네 군데로 갈라져 있었다.**

| 무엇 | 어디 | 정의 |
|---|---|---|
| 프로그램 본체 | `%APPDATA%\PaleoBytes\Modan2` (Roaming) | `Modan2.iss.template` |
| DB·미디어·로그·백업 | `~/PaleoBytes/Modan2/` | `MdUtils.py:100-103` |
| 설정 | `~/.modan2/config.json` | `MdAppSetup.py:45`, `Modan2.py:218` |
| 임시 파일 | Windows Roaming AppData / 그 외 `~/.modan2` | `MdHelpers.get_app_data_dir` |

넷 중 셋이 서로 다른 규칙이고, 그중 둘이 Roaming을 쓴다.

## 1. 설치 위치: Roaming → Local

`DefaultDirName={userappdata}\PaleoBytes\Modan2` 는 **Roaming** 이다. onedir
페이로드가 ~130MB인데, 도메인 가입 머신에서는 로밍 프로필과 함께 동기화되므로
로그인마다 따라다닌다. 설치형 앱 본체가 있을 자리가 아니다.

`{localappdata}` 로 변경했다.

## 2. `PrivilegesRequired=lowest`

지정돼 있지 않았고 Inno의 기본값은 `admin` 이다. 설치 대상이 사용자별
디렉터리인데도 UAC 승격을 요구하고 있었다. 더 나쁜 것은 **승격이 다른 계정으로
이뤄지면 `{localappdata}` 가 그 관리자 계정의 폴더로 풀린다**는 점이다. 정작
사용자에게는 앱이 보이지 않는다. (`{userappdata}` 시절에도 있던 결함이다.)

`lowest` 로 명시해 완전한 사용자별 설치로 만들었다. `{localappdata}`,
`{userprograms}`, `{%userprofile}` 이 모두 실제 실행 사용자 기준으로 해석된다.

### 이것이 업그레이드 경로를 바꾼다

Inno 6은 언인스톨 정보를 install mode에 따라 결정되는 `HKA` 에 쓴다.

| install mode | HKA | 언인스톨 키 |
|---|---|---|
| 이전 릴리스 (`admin` 기본값) | HKLM | `HKLM\...\Uninstall\Modan2_is1` |
| 지금 (`lowest`) | HKCU | `HKCU\...\Uninstall\Modan2_is1` |

`UsePreviousAppDir` 은 HKA만 본다. 새 설치 관리자는 HKCU를 뒤지는데 기존
사용자의 기록은 HKLM에 있으니 찾지 못한다. **기존 Roaming 설치가 남은 채
LocalAppData에 두 번째 설치가 생긴다.**

작업 중간에 이 점을 정정했다 — `{localappdata}` 변경만 했을 때는 "기존 설치는
제자리 업그레이드"가 맞았지만, `lowest` 를 추가하면서 성립하지 않게 됐다.

## 3. `AppId` 도입

`AppId` 를 지정하지 않으면 **`AppName` 값이 그대로 쓰인다**(여기서는 `Modan2`).
여기에 `_is1` 을 붙인 것이 레지스트리 서브키가 되고, 이 키 하나로 업그레이드
감지·언인스톨러 등록·`{app}` 해석이 모두 결정된다.

표시용 문자열을 내부 식별자로 겸용하는 것이 문제다. `AppName` 을 언젠가 바꾸면
그 순간 모든 기존 설치와의 연결이 끊긴다. 전역 레지스트리에서 `Modan2` 라는
평범한 문자열이 남에게 선점될 여지도 있다.

GUID `46308C1B-18AE-4B0D-B029-41CF44660599` 를 `uuid4` 로 생성해 넣었다.
Inno에서 `{` 는 상수 치환의 시작 문자이므로 여는 중괄호를 두 번 쓴다:

```ini
AppId={{46308C1B-18AE-4B0D-B029-41CF44660599}
```

`build.py` 의 치환은 `{{VERSION}}` / `{{DIST_PATH}}` 정확 문자열 두 개와
`#define AppVersion "..."` 정규식뿐이라(`build.py:159-164`) 충돌하지 않는다.
치환 드라이런으로 `AppId` 줄이 원형 그대로 남는 것을 확인했다.

`AppPublisher=PaleoBytes` (제어판 게시자 칸이 비어 있었다) 와
`UninstallDisplayIcon={app}\Modan2.exe` 도 함께 넣었다.

**언인스톨러 자체는 원래부터 정상이었다.** Inno는 지시 없이도
`{app}\unins000.exe` 를 만들고 등록한다. 빠져 있던 것은 정체성과 표시 정보뿐이다.

## 4. QSettings 삭제

`MdHelpers` 에 `load_settings()` / `save_window_state()` / `restore_window_state()`
가 `QSettings("Modan2Team", "Modan2")` 를 쓰고 있었다. 그런데 `main.py:202` 가
앱에 설정한 조직명은 `"Modan2 Team"`(공백 있음)이다 — 애초에 경로가 갈린다.

이력을 보니 **2025-08-29~30의 `2581a72` / `ca84a36` 리팩토링**에서 설정 저장이
QSettings → JSON으로 바뀌었고, 이 세 함수만 남았다. 앱 코드에 호출처가 하나도
없고 테스트만 붙잡고 있었다. 함수 3개와 `QSettings` import, 대응 테스트 4개를
삭제했다.

## 5. 설정 파일 이전

```
~/.modan2/config.json  →  ~/PaleoBytes/Modan2/preferences.json
```

DB·미디어·로그·백업이 이미 있는 곳에 설정도 둔다. **폴더 하나만 복사하면 전부
옮겨진다.**

경로 정의를 `MdUtils.DEFAULT_CONFIG_PATH` 한 곳으로 모으고, 쓰이지 않던 중복
정의 `MdConstants.CONFIG_DIR` 은 제거했다(왜 지웠는지 주석으로 남겼다 — 두 번째
정의가 load/save 경로가 갈라지게 둔 원인이다).

### 마이그레이션은 선택이 아니다

`migrate_legacy_config()` 가 첫 실행 때 구 파일을 새 위치로 복사한다. 이게
없으면 사용자 눈에는 창 위치·언어·오버레이 설정이 **전부 초기화된 것으로
보인다.** 옮겨진 것이 아니라 잃은 것처럼 보인다.

구 파일은 일부러 남긴다 — 비용이 없고, 구버전을 같은 프로필로 계속 쓸 수 있다.
`--config` 로 명시한 경로에는 적용하지 않는다(사용자가 지정한 것을 액면 그대로
받는다).

### 함께 고친 버그: `--config` 왕복 불일치

`SettingsWrapper.save()` 가 `Path.home() / ".modan2" / "config.json"` 을
하드코딩하고 있었다. `main.py` 는 `ModanMainWindow(setup.get_config())` 로 **dict만**
넘기고 경로는 넘기지 않았으므로, `--config` 를 주면 **한 파일에서 읽고 다른
파일에 저장**했다.

메인 윈도우가 `config_path` 를 들고 다니게 하고 (`main.py` 에서 주입),
`SettingsWrapper._config_path()` 가 그것을 따르도록 했다. 부모가 없는
래퍼(테스트, 독립 사용)는 기본 경로로 떨어진다. 회귀 테스트를 붙였다.

## 6. 임시 디렉터리의 Roaming 제거

`MdHelpers.get_app_data_dir()` 이 네 번째 위치였다 — Windows에서
`QStandardPaths.AppDataLocation`(Roaming), 그 외에서 `~/.modan2`. 스크래치
데이터를 프로필 동기화 공유에 넣는 셈이고, 플랫폼별로 규칙도 달랐다.

`mu.DEFAULT_DB_DIRECTORY` 를 반환하도록 바꿔 나머지와 통일했다. `MdUtils` 는
`MdHelpers` 를 import하지 않으므로 순환 참조는 없다.

기존 `~/.modan2/temp` 는 고아가 되지만 임시 파일이므로 이관하지 않는다.

## 결과

네 위치가 둘로 줄었다.

| 무엇 | 어디 |
|---|---|
| 프로그램 본체 | `%LOCALAPPDATA%\PaleoBytes\Modan2` |
| **사용자 데이터 전부** (DB·미디어·로그·백업·설정·임시) | `~/PaleoBytes/Modan2/` |

## 검증

- 전체 스위트 **1882 passed, 10 skipped** (Xvfb 헤드리스, CI와 동일).
  QSettings 테스트 4개 삭제, 마이그레이션 3개 + `--config` 왕복 1개 추가.
- `ruff check` / `ruff format --check` 통과. `MdAppSetup.py` 와 `MdHelpers.py` 를
  `N813` 예외에 추가했다(`import MdUtils as mu` 관례는 파일별 등록 방식이다).
- **실제 마이그레이션 동작 확인** — 개발 머신의 `~/.modan2/config.json`(999바이트)이
  `~/PaleoBytes/Modan2/preferences.json` 으로 복사됐고 `diff` 결과 동일, 원본 유지.
  가짜 홈으로 첫 실행/재실행/신규 설치 세 경우도 확인했다.
- `main.py --self-test` exit 0 (CI 스모크 테스트가 타는 경로).
- 문서 3개 페이지 갱신 + 한국어 9건 번역. sphinx를 설치해 EN/KO 양쪽 빌드
  성공을 확인했다(경고 2건은 기존 것).

**검증하지 못한 것: Inno 컴파일은 Windows 전용이라 로컬에서 돌릴 수 없다.**
`{{` 이스케이프와 `lowest` 동작은 다음 Windows 빌드에서 처음 확인된다. 마법사가
생성하는 표준 형태라 위험은 낮다고 보지만, 확인 전까지는 미검증이다.

## 남은 것

**다음 릴리스 노트에 "구버전을 먼저 제거하세요" 안내가 필요하다.** `lowest` 전환과
`AppId` 도입으로 기존 설치와의 연결이 끊기므로, 안내가 없으면 사용자에게 설치가
둘 남는다. 두 변경이 같은 단절을 공유하므로 손실이 겹치지는 않는다 — 0.2 베타
단계에서 한 번에 흡수시킬 유일한 타이밍이었다.
