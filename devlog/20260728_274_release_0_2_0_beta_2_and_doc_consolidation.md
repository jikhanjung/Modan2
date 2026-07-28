# 0.2.0-beta.2 릴리스와 문서 통폐합

## 날짜
2026-07-28

## 1. 릴리스

devlog 272–273의 변경(설치 위치·정체성·설정 이전)을 담아 beta.2를 냈다.

절차는 devlog 271과 같다. **태그 없이 버전 범프만 먼저 푸시**해 CI 5개 워크플로가
green인 것을 확인한 뒤 태그를 만들었다. 태그를 밀면 릴리스가 즉시 나가므로 이
순서가 중요하다.

CHANGELOG 절은 문서가 아니라 **릴리스 본문 그 자체**이므로, 태그 전에
`release.yml` 과 동일한 awk로 추출을 검증했다 — 41줄, beta.1 헤더로 넘어가지
않고 정확히 끊겼다.

### 결과

| 항목 | 값 |
|---|---|
| 태그 | `v0.2.0-beta.2` |
| prerelease | true (태그의 `-beta` 로 자동 판정) |
| draft | false |
| 빌드 번호 | 844 (3개 플랫폼 일관) |
| 워크플로 | 18분 37초, 전체 성공 |

자산 4종: Windows Installer ZIP(134MB), macOS DMG(140MB), Linux
AppImage(209MB), `SHA256SUMS.txt`.

### 이 릴리스가 실제로 검증해 준 것

**Windows 설치 관리자가 빌드됐다는 것은 Inno가 devlog 272–273의 `[Code]` 와
`AppId` 를 컴파일했다는 뜻이다.** Inno는 Windows 전용이라 로컬에서 확인할 수
없었던 부분인데, 이 빌드로 **문법과 `{{` 이스케이프는 검증됐다.**

여전히 미검증인 것은 **런타임 동작** 이다: 구버전 감지가 실제로 뜨는지,
`lowest` 모드에서 설치 경로가 맞는지, 그리고 무엇보다 **구버전이 없는 깨끗한
머신에서 프롬프트가 뜨지 않는지.** 마지막 항목이 회귀 위험이 가장 크다.

## 2. 문서 통폐합

릴리스 후 "업데이트가 필요한 문서가 있는지" 훑다가, 이번 변경과 무관한 부채가
드러났다.

### `INSTALL.md` (516줄) — 삭제

**0.1.5-alpha.1 시절에 멈춰 있었다**(문서 스스로 그렇게 적고 있었다). 실제
릴리스 자산과 대조한 결과 거의 모든 사실이 틀렸다:

| 주장 | 실제 |
|---|---|
| `Modan2-Setup.exe` | `Modan2-Windows-Installer-v{ver}-build{N}.zip` |
| `Modan2.dmg` | `Modan2-macOS-Installer-v{ver}-build{N}.dmg` |
| `Modan2_linux` | `Modan2-Linux-v{ver}-build{N}.AppImage` |
| 설치 폴더 `C:\Program Files\Modan2` | 한 번도 그랬던 적 없음 |
| "Create desktop shortcut" 옵션 | `.iss` 에 그런 task 없음 |
| Portable Executable | 발행되지 않음 (devlog 261이 확인) |
| macOS `~/Library/Preferences/com.paleobytes.modan2*` | 앱이 쓴 적 없는 경로 |
| `python3 Modan2.py` | 진입점은 `main.py` |

`yourusername` 플레이스홀더 URL도 9곳 남아 있었다. **devlog 263은 이것을 고쳤다고
기록했는데 실제로는 반영되지 않았다** — 링크 정리가 `README.md` 에만 적용된 것으로
보인다. 기록과 실제가 어긋난 사례이므로 남겨 둔다.

구조적으로도 `docs/manual/installation.rst`(검증·번역·발행됨)와 중복이고,
`README.md` 는 이미 사용자를 발행 사이트로 보내고 있었다. devlog 264가
`USER_GUIDE.md` / `QUICK_START.md` 에 한 것과 같은 처리를 했다.

**발행본에 없어서 건져 옮긴 것** (사실 확인 후):

- Windows: DLL 누락 → Visual C++ 재배포 패키지 (→ `installation.rst`)
- macOS: "손상되어 열 수 없습니다" → `xattr -rd com.apple.quarantine` (→ 같은 곳)
- Linux: xcb 플러그인 로드 실패 → XCB 라이브러리 목록 (→ 같은 곳)
- 배포판별 시스템 의존성 (→ `developer_guide.rst`, 소스 설치는 개발자용이므로)

버린 것: 존재하지 않는 자산·경로·옵션, 그리고 "Tested Platforms" 표 — 발행본의
"Windows만 충분히 테스트됨" 경고와 정면으로 어긋났고, 그쪽이 정직한 쪽이다.

### 발행 매뉴얼에서 발견한 오류

INSTALL.md를 병합하면서 `installation.rst` 자체의 오류도 두 건 나왔다:

1. **"Start Menu 또는 데스크톱 바로가기에서 실행"** — `.iss` 의 `[Icons]` 에는
   시작 메뉴 항목 하나뿐이다. 데스크톱 바로가기는 없다.
2. **"Windows: 새 설치 관리자를 실행하면 구버전을 대체한다"** — beta.2부터 성립하지
   않는다. 업그레이드 절차와 제거 절을 새로 썼다.

### 릴리스 문서 3종 → 1곳

`docs/RELEASE_PROCESS.md`(1044줄)는 11번째 줄에 "`RELEASE_NOTES.md` 는 더 이상
없으니 아래 단계를 전부 무시하라"는 배너를 달고 **그 아래 1000줄이 존재하지 않는
파일에 대한 지침** 이었다. 게다가 배너 자체도 이제 틀렸다 — "prerelease 접미사
없이 patch만 올린다"고 적혀 있는데 방금 beta.1 → beta.2를 냈다.

`RELEASE_GUIDE.md`(75줄)는 채택된 적 없는 "Option A/B/C" 나열이었고,
`VERSION_MANAGEMENT.md`(143줄)는 `manage_version.py` 사용법이었다.

셋 다 삭제하고, **발행 `developer_guide.rst` 의 "Creating Releases" 절을 실제
워크플로에 맞춰 다시 썼다.** 그 절도 원래는 "GitHub에서 릴리스 초안을 만들고
빌드한 실행 파일을 첨부하라"고 되어 있었는데, `release.yml` 이 태그를 받아 전부
자동으로 한다.

### 루트 잔재 삭제

`PCA_ANALYSIS_FIX_GUIDE_backup.md`, `RELEASE_NOTE_0.1.4{,_ko}.md`,
`RELEASE_NOTE_0.1.5_alpha{,_ko}.md` — devlog 269가 CHANGELOG.md를 릴리스 이력
단일 출처로 만든 뒤 남은 것들이다.

`docs/README.md` 의 색인도 고쳤다. `developer_guide.md` 가 devlog 265에서
삭제됐는데 표에 남아 있었고, 그 파일에 대한 "Caveat" 절까지 통째로 살아 있었다.

## 검증

- EN/KO 매뉴얼 빌드 성공(경고 2건은 기존 것). 렌더된 HTML에서 새 제거 절을 양쪽
  언어로 확인했다.
- **한국어 34건 번역** — `installation` 21, `developer_guide` 13. 두 카탈로그 모두
  미번역·fuzzy 0.
- 삭제한 파일에 대한 잔여 참조 확인. `CHANGELOG.md` 와 devlog의 언급은 과거 기록
  이므로 그대로 둔다.

### 작업 중 낸 실수

RST 제목 밑줄 길이를 일괄 교정하는 스크립트를 돌렸는데, code-block 안의 docstring
예시 3곳(`"""` 닫는 줄)을 제목 밑줄로 오인해 따옴표 나열로 바꿔 놨다. 들여쓰기와
code-block 문맥을 보지 않은 정규식이 원인이다. 즉시 원복했고 빌드로 확인했다.

## 남은 것

**`changelog.po` 가 미번역 111 / fuzzy 18 이다.** 이번 작업 때문이 아니라
**devlog 269가 `changelog.rst` 를 CHANGELOG.md 전문 include로 바꾸면서** 생긴
격차다. 그전에는 손으로 유지하던 축약 미러였기 때문에 devlog 262의 "8개 카탈로그
모두 0" 상태가 성립했지만, 지금은 릴리스 이력 전체가 번역 대상이 됐다.

과거 릴리스 노트를 한국어로 옮기는 값어치가 얼마인지는 판단이 필요하다. 선택지는
셋이다: 전부 번역, 최근 몇 개 릴리스만 번역, 또는 `changelog` 를 번역 대상에서
제외.
