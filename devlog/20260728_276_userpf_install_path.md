# 설치 경로를 `{userpf}` 로 — 그리고 데이터 위치에 대한 질문

## 날짜
2026-07-28

## 배경

devlog 272에서 설치 경로를 `{userappdata}`(Roaming) → `{localappdata}` 로 옮겼다.
로밍 프로필 동기화를 없앤 것은 맞았지만, 경로가 한 칸 부족했다.

Windows에서 사용자별 설치의 관례는 `%LOCALAPPDATA%\Programs\...` 다. Inno에 이걸
위한 상수가 따로 있다:

| 상수 | 확장 |
|---|---|
| `{userpf}` | `%LOCALAPPDATA%\Programs` (사용자용 Program Files) |
| `{commonpf}` | `%ProgramFiles%` |
| `{autopf}` | install mode에 따라 위 둘 중 하나 |

`{localappdata}` 바로 밑에 두면 프로그램이 `Temp`, `Packages`, `Microsoft` 같은
**데이터 폴더들 사이에 놓인다.** Inno 마법사도 non-admin 설치를 고르면 `{userpf}`
를 생성한다.

```ini
DefaultDirName={userpf}\PaleoBytes\Modan2
```

즉 `C:\Users\<사용자>\AppData\Local\Programs\PaleoBytes\Modan2`.

## 왜 지금 바꿔도 안전한가

devlog 272에서 `AppId` 를 GUID로 고정해 뒀기 때문이다. 제품 정체성이 경로와
무관하므로, 기존 설치는 `UsePreviousAppDir` 로 원래 위치에 그대로 업그레이드되고
**신규 설치만 새 경로로 간다.** beta.2 때와 같은 단절이 다시 생기지 않는다.

`AppId` 를 안 박아 뒀다면 이 변경도 또 한 번의 단절이었을 것이다.

## 검토했지만 채택하지 않은 것

`{autopf}` + `PrivilegesRequiredOverridesAllowed=dialog` 로 **설치 시 "모든 사용자
/ 나만" 을 묻는** 방식도 있다. 관리자 권한이 있으면 Program Files, 없으면
사용자별로 간다.

per-user의 알려진 약점이 이걸로 완화된다 — 관리된 환경에서 AppLocker/SRP 기본
정책이 사용자 쓰기 가능한 경로의 실행을 차단하는 경우가 있고, 대학 실험실 PC는
이 앱의 실제 사용처다.

**미룬 이유**: install mode가 다시 두 갈래가 되면 devlog 272에서 정리한 HKLM/HKCU
문제가 재등장하고 검증 대상이 늘어난다. 설치 관리자 쪽 미검증 항목이 이미 쌓여
있는데(devlog 273의 `[Code]`, `lowest` 동작) 여기에 더 얹는 것은 순서가 아니다.
**실제로 AppLocker 차단 사례가 확인되면** 그때 가는 것이 맞다.

## 데이터 위치에 대한 질문 (기록만)

같은 대화에서 "데이터 파일 위치는 관례에 맞느냐" 는 질문이 나왔다. 답은
**맞지 않는다** 이다.

`~/PaleoBytes/Modan2/` 는 세 플랫폼 어디의 관례도 아니다. Windows는
`%LOCALAPPDATA%\<Vendor>\<App>` 또는 `Documents\`, macOS는
`~/Library/Application Support/`, Linux는 XDG `~/.local/share/` 를 쓴다. 프로필
루트는 알려진 폴더가 놓이는 자리이지 앱 데이터 자리가 아니다. 이번 세션이 만든
구조가 아니라 `MdUtils.py:100` 에 오래전부터 있던 것이고, devlog 272는 거기에
`preferences.json` 을 합류시켰을 뿐이다.

변호할 여지는 있다. 데이터셋은 사용자의 **유일한 사본** 이고 백업·이동 대상인데,
`%LOCALAPPDATA%` 는 숨은 경로라 찾기 어렵다. "폴더 하나만 복사하면 전부 옮겨진다"
는 성질은 실제 값어치가 있다.

**구체적 위험 하나**: OneDrive의 Known Folder Move는 Documents·Desktop·Pictures를
백업하지만 프로필 루트의 임의 폴더는 백업하지 않는다. OneDrive 사용자는 자기
파일이 클라우드에 있다고 여기는데 Modan2 데이터베이스만 빠진다. 유일한 사본이라는
점과 겹치면 나쁜 조합이다.

**이번에 바꾸지 않았다.** 설치 경로 변경은 신규 설치만 영향받지만, 데이터 이동은
기존 사용자의 DB·미디어를 실제로 옮겨야 하고 실패하면 데이터 손실이다. 설정 파일
마이그레이션(999바이트 복사)과는 규모가 다르다. TODOs에 판단 항목으로 남겼다.

## 릴리스 처리

`{userpf}` 는 beta.2에 들어가야 하는데 beta.2는 이미 게시된 상태였다. 새 버전을
올리는 대신 **태그와 릴리스를 지우고 다시 만들기로 했다** — 게시 한 시간 안이고
prerelease이므로 내려받은 사람이 있을 가능성이 낮다.

빌드 번호는 커밋 수에서 나오므로 재생성 시 달라진다(844 → 그 이후). 같은 버전
문자열의 자산이 빌드 번호로 구분되는 셈이라, 혹시 이전 것을 받은 사람이 있어도
어느 쪽인지 알 수 있다.
