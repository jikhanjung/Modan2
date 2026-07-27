# 한국어 문서 번역 갱신 + 설치 안내를 실제 릴리스에 맞게 재작성

## 날짜
2026-07-27

## 배경

devlog 260에서 docs 배포를 복구하자, 예고한 대로 한국어 페이지의 신규 섹션이 전부
영어 fallback으로 뜨는 것이 확인되었다. `docs/locale/ko/LC_MESSAGES/user_guide.po`는
2025-10-04 이후 손대지 않아 semi-landmark/curve msgid가 **0건**이었다.

이어서 설치 안내가 실제 릴리스와 전혀 맞지 않는다는 지적이 있었다: 포터블 버전은
현재 배포하지 않고, 릴리스 자산은 버전이 박힌 ZIP/DMG/AppImage이며, macOS/Linux는
제대로 테스트되지 않았다.

## 1) 한국어 카탈로그 갱신

`sphinx-build -b gettext` → `sphinx-intl update -l ko`. 기존 5개 `.po` 갱신,
번역이 없던 3개(`advanced_features`, `faq`, `troubleshooting`) 신규 생성.

번역 대상 233건을 처리했다:

| 파일 | 미번역/fuzzy |
|---|---|
| `user_guide.po` | 157 |
| `changelog.po` | 59 |
| `developer_guide.po` | 11 |
| `index.po` | 5 (이후 +7) |
| `installation.po` | 1 (이후 +31) |

용어는 추측하지 않고 **앱의 실제 한국어 UI**(`translations/Modan2_ko.ts`)에서 뽑아
맞췄다: Superimposition → 중첩정렬, Resistant Fit → 강건적합, Bookstein → 북스틴,
Add/Insert Missing → 결측 추가/결측 삽입, Show Estimated → 추정값 보기,
Show Original → 원본 보기. 앱이 아직 번역하지 않은 Curve 모드 UI 문자열
(Curve/Snap to curve/Smooth curve/Semi-LM)은 한국어 UI에도 영어로 보이므로,
매뉴얼에서도 영어 레이블을 유지하고 괄호로 우리말 설명을 덧붙였다.
semi-landmark 자체는 **준랜드마크** 로 옮겼다.

### RST 마크업 함정 (경고 2 → 63건)

첫 빌드에서 경고가 63건으로 폭증했다. docutils는 인라인 마크업의 **끝 문자열 뒤에**
공백 또는 ``- . , : ; ! ? \ / ' " ) ] } >`` 만 허용하는데, 한국어 표기 관행상
`**Save**(저장)` 처럼 괄호를 붙여 쓰면 `(` 는 그 목록에 없어 마크업이 깨진다.
(`(` 는 *시작* 문자열 **앞**에만 허용된다.)

RST의 이스케이프 공백 `\ ` 으로 고쳤다 — 파서는 만족시키면서 출력에는 공백이 없다.
29개 항목 수정.

이 수정 스크립트 자체에서 버그가 하나 나왔다: 1차 실행 때 emphasis 규칙이 인라인
리터럴 **내부**의 `*Eurekia*` 를 잡아 ``` ``*Eurekia*\ `` ``` 로 망가뜨렸다. 백틱 앞에
삽입된 `\ ` 만 되돌려 복구했고, 이후 정규식에 리터럴(` ``…`` `)을 먼저 매칭하도록
추가했다.

남은 1건은 `\`Importing a Dataset Package (JSON+ZIP)\`_` 참조 — 원문 RST가 줄바꿈으로
쪼개져 있어 Sphinx의 일관성 검사가 불일치로 보았다. msgstr에도 같은 위치에 줄바꿈을
넣어 해소(RST가 참조명 공백을 정규화하므로 링크는 원래도 동작).

**결과: 한국어 빌드 경고 2건** — 영어 빌드와 동일하며 둘 다 무해
(`_static` 없음, ASCII 다이어그램 하이라이팅 실패).

## 2) 설치 안내 재작성

실제 릴리스 자산을 `gh release view` 와 `reusable_build.yml` / InnoSetup 템플릿에서
확인했다:

- Windows: `Modan2-Windows-Installer-v<version>-build<build>.zip`
  (내부에 `Modan2_v<version>_build<build>_Installer.exe`)
- macOS: `Modan2-macOS-Installer-v<version>-build<build>.dmg`
- Linux: `Modan2-Linux-v<version>-build<build>.AppImage`
- `SHA256SUMS.txt` 동봉

기존 문서가 틀렸던 것들:

- **포터블 버전** (`Modan2-portable-windows.zip`) — 배포하지 않는다. 삭제하고,
  Windows 패키지는 설치 프로그램뿐임을 명시.
- **`Modan2-Setup.exe`**, **`Modan2.dmg`** — 실제 이름과 다름. 버전/빌드가 들어간
  실제 형식으로 교체.
- **Linux에 AppImage 안내가 아예 없었다.** Linux 절이 전부 소스 빌드였다.
  AppImage 실행법 + FUSE 누락 시 대처로 교체.
- macOS/Linux가 제대로 테스트되지 않았다는 **경고**를 추가.

**소스 실행 안내 제거** (`installation.rst`, `user_guide.rst`, `index.rst`, `faq.rst`):
"From Source" 절, `pip install -r requirements.txt`, `python3 Modan2.py`
(애초에 유효한 엔트리포인트도 아니다 — `main.py` 다), WSL X11 절, 그리고 소스 전용
문제 해결 항목(fix_qt_import / Missing Python Dependencies / migrate.py)을 걷어냈다.
OpenGL 항목은 바이너리 사용자에게도 해당하므로 pip 명령 없이 다시 썼다.
업데이트 절도 플랫폼별 재설치 안내로 교체했다.

문서를 고친 뒤 `sphinx-intl update` 를 다시 돌려 새로 생긴 40건을 번역했다.

## 검증

- en/ko 두 빌드 모두 **build succeeded, 2 warnings** (동일한 무해 경고).
- 산출물 grep: `Modan2-Setup.exe` / `portable-windows` / `python3 Modan2.py` /
  `From Source` 가 사용자용 페이지에서 사라지고, `Modan2-Windows-Installer-v` /
  `AppImage` / `SHA256SUMS` 가 나타남을 확인.
- 한국어 `user_guide.html`: 준랜드마크 13, 결측 랜드마크 19, 중첩정렬 4, 강건적합 2.

## 남은 일

- `advanced_features.rst` / `faq.rst` / `troubleshooting.rst` 세 페이지는 여전히
  미갱신 + 미번역이다. semi-landmark 언급이 0/1/0건이고, `.po` 카탈로그가 새로
  생성되어 **100% 미번역**(약 1200건)이며, 아직 `python Modan2.py` 실행을 안내한다.
  사용자가 실제로 찾아보는 FAQ/트러블슈팅이라 문서 작업 중 가장 값어치가 크다.
- `developer_guide.rst` 도 `python Modan2.py`(3곳)와 `Output/Modan2-Setup.exe` 를
  쓴다. 개발자 문서이므로 소스 실행 안내 자체는 맞지만, 이름은 `main.py` 와 실제
  설치 파일명으로 바로잡아야 한다.
