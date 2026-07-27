# 낡은 세 안내서 교정 + 한국어 번역 완성

## 날짜
2026-07-27

## 배경

devlog 261에서 남겨 둔 항목: `advanced_features.rst` / `troubleshooting.rst` /
`faq.rst` 세 페이지가 미갱신 + 미번역 상태였다. "세 파일도 한국어로 번역해야
한다"는 요청에 대해 **낡은 내용을 그대로 번역하면 오류가 한국어로도 굳고, 나중에
원문을 고치면 fuzzy로 풀려 재번역이 필요하다** 고 지적했고, 영문을 먼저 고치기로
했다.

## 1) 영문 교정 — 주장한 기능이 실제로 있는지 코드로 확인

문서를 읽고 고친 게 아니라, 각 주장을 코드에서 확인했다. 존재하지 않는 기능이
많았다.

| 문서의 주장 | 실제 |
|---|---|
| 설정 `%APPDATA%\Modan2\settings.json` | `~/.modan2/config.json` (`Modan2.py:219`) |
| DB `~/.local/share/Modan2/modan.db` | `~/PaleoBytes/Modan2/Modan2.db` (`MdModel.py:194`, `MdUtils.py:100`) |
| `MODAN2_LOG_LEVEL` / `MODAN2_DB_PATH` | **없음.** 환경 변수로 설정하지 않음 |
| `--verbose`, `--no-3d` | **없음.** 실제는 `--debug/--db/--config/--lang/--no-splash/--version/--self-test` |
| `Ctrl+O/Q/R`, `Ctrl+1~9`·`Ctrl+Tab`(탭 전환), `F5` | **없음.** 메인 창에 탭 자체가 없음 |
| 3D 뷰어 `F3/W/S/P/R/L` | **없음.** `object_viewer_3d.py` 에 `keyPressEvent` 자체가 없음 |
| 3D: 오른쪽 드래그 = 이동, 더블클릭 = 시점 초기화 | 오른쪽 = **확대/축소**, 가운데 = 이동, 더블클릭 동작 없음 |
| Full / Partial Procrustes 선택 | **없음.** Procrustes / Bookstein / Resistant Fit |
| Bookstein = "처음 두 랜드마크" | 데이터셋 **베이스라인**, 3D는 3점 |
| 결측 추정: TPS 보간 / 평균 대체 / 수동 | 형상 정합 기반 **EM 루프** (devlog 227) |
| 비대칭(asymmetry) 분석 | **없음** |
| "Data Exploration → Regression", "Results → Shape Variation" | `Show regression` / `Shape grid` **체크박스** |
| "New Child Dataset" + 랜드마크 복사·중첩정렬 선택 | `Add child dataset`, 빈 데이터셋 생성뿐 |

3D 조작은 `user_guide.rst` 에도 "Pan: right-drag" 로 **잘못 적혀 있었고**, 이건
devlog 261에서 이미 한국어로 번역까지 해 둔 상태였다. 두 곳 모두 바로잡았다.

그 밖에: 사용자용 페이지에서 소스 실행 안내를 제거하고, 준랜드마크 내용을 추가했다
(FAQ 항목 신설, advanced_features 의 대규모 작업 절, troubleshooting 의 2D 전용
제한 사항). troubleshooting 에는 파일 위치 표를 새로 넣었다.

`main.py` 의 `--db` 도움말도 `~/.modan2/modan2.db` 라는, 애플리케이션이 한 번도
쓴 적 없는 경로를 안내하고 있어 함께 고쳤다(`MdAppSetup.py` 주석이 바로 그 버그를
설명하고 있다).

## 2) 한국어 번역 완성

영문을 확정한 뒤 `sphinx-intl update` 로 재동기화하고 번역했다.

| 파일 | 번역 항목 |
|---|---|
| `faq.po` | 492 |
| `troubleshooting.po` | 374 |
| `advanced_features.po` | 276 |
| `user_guide.po` | 5 (3D 조작 수정분) |

devlog 261의 233건과 합쳐 **총 1380건**. 8개 카탈로그 전부 미번역/fuzzy **0건**.

용어는 devlog 261과 동일하게 앱의 실제 한국어 UI를 따랐다(중첩정렬, 강건적합,
결측 추가/삽입, 추정값 보기, 준랜드마크).

## 검증

- en / ko 두 빌드 모두 **build succeeded, 2 warnings** (동일한 무해 경고).
- 산출물 grep: 사용자용 페이지에서 `python Modan2.py`, `MODAN2_LOG_LEVEL`,
  `settings.json`, `modan.db`, `Full Procrustes`, `--verbose`, `Modan2-Setup.exe`
  가 모두 0. `PaleoBytes/Modan2`, `config.json`, `Semi-landmark`, `Resistant Fit`,
  `Snap to curve` 는 정상 등장.
- 한국어 페이지 한글 포함 줄: faq 833, troubleshooting 714, advanced_features 587.

## 별건 — CTHarvester addendum 검토 (문서 관련)

`../CTHarvester/docs/CI_RECOMMENDATIONS_FOR_MODAN2.md` 의 2026-07-27 addendum
1번(“`docs/` 의 Markdown이 발행되지 않음”)을 Modan2 트리에서 확인했다. **지적이
정확하며, Modan2에서는 한 가지가 더 나쁘다.**

- `docs/conf.py` 에 `myst_parser` 가 없어 Sphinx가 `.rst` 만 읽는다. `docs/*.md`
  는 12개이고 **전부 사이트에 나오지 않는다**(GitHub에서만 읽힘).
- 그중 **`USER_GUIDE.md`(34KB)는 `user_guide.rst` 의 중복본**이고,
  `developer_guide.md`(1082줄)는 `developer_guide.rst`(876줄)의 중복본이다.
- 발행되지 않는 사본은 이미 **드리프트했다**: `USER_GUIDE.md` 에는 아직
  `python3 main.py`(2곳), `Modan2-Setup`(1곳), `portable`(2곳), 그리고 방금
  고친 3D "Pan: right-drag" 오류(2곳)가 남아 있다.
- `QUICK_START.md` 는 사용자용인데 `.rst` 대응본이 없어, 발행 대상에서 통째로 빠져 있다.

즉 매뉴얼이 두 벌 존재하고 한 벌만 발행되며, 발행되지 않는 쪽이 조용히 낡고 있다.
처리 방향은 사용자 결정이 필요해 보류(아래 TODO).
