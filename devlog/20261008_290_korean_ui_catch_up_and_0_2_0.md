# 한국어 UI 밀린 번역 정리와 0.2.0 정식 릴리스

## 날짜
2026-10-08

## 번역

devlog 288이 남겨 둔 숙제("`Modan2_ko.ts`에 이전 작업분 문자열 40여 개 미추출")를
`main`에서 처리했다. 실제로는 40여 개보다 많았다 — 추출 전부터 `type="unfinished"`
가 41개 있었고(이전에 추출만 하고 채우지 않은 것), 재추출로 40개가 더 늘어 **81개**.

| 출처 | 내용 |
|---|---|
| devlog 282–283 | 라이브러리 백업/복원, 데이터 폴더 이동·위험 위치 경고 |
| devlog 237 이후 곡선 작업 | 곡선 표, 추적 버튼, 가장자리 맞춤(live-wire), 곡선 다듬기, 점/곡선 삭제 |
| 데이터셋·랜드마크 이름 대화상자 | 탭 이름(일반·고정 랜드마크·곡선·변수), 열 머리글 |

절차는 devlog 229 그대로:

1. `pylupdate5` — 소스 목록은 `tr()`가 실제로 있는 15개 파일을 grep으로 다시
   잡았다(`Modan2.py`, `dialogs/` 11개, `components/` 3개). **`.ts`가 있는 자리에 그대로 실행할 것** — 다른
   디렉터리의 사본에 돌리면 `location`이 `../../../../home/...` 절대 경로로 바뀐다.
2. 빈 항목 76개 번역, 번역문이 있는데 `unfinished`인 5개(랜드마크·설명·저장·취소 등)
   플래그 제거. 자리표시자 `{}` 개수는 스크립트로 원문과 대조.
3. 기존 완료 번역 361개를 재추출 전후로 (context, source) 단위 비교 — 바뀐 것 없음.
   obsolete로 넘어간 2개는 정당하다(Resistant Fit 철회 devlog 281, 환경설정 확인
   문구가 두 부분으로 쪼개짐).
4. `pyside6-lrelease` → 380 finished, 0 unfinished. PyQt5 `QTranslator`로 표본
   확인, em-dash(`—`)가 든 복원 확인 문구도 `tr()`로 정상 조회됨(229의 비ASCII
   주의는 `QCoreApplication.translate` 쪽 이야기).

용어: 객체=개체, semi-landmark=준랜드마크(매뉴얼과 동일), live-wire=라이브와이어,
specimen이 UI에 나올 때는 개체("곡선 삭제 (모든 개체)"). 문체는 기존 번역의
"~하십시오"를 따랐다.

`main.py`의 "data location unavailable" 대화상자는 의도적으로 번역하지 않는다
(QTranslator 설치 전에 뜬다 — 해당 docstring). 이 문자열이 `Modan2.py`에 있던
시절의 번역은 obsolete로 남는다.

### 매뉴얼

한국어 매뉴얼이 영어로 인용하던 UI 이름 7곳(**Semi-LM**, **Show Expected**,
**Delete Point / Delete Curve**, **Delete Curve (all specimens)**,
**"Landmark Names"**, 곡선 체크박스)을 이제 한국어로 보이는 이름으로 바꿨다.
`.po`의 해당 `msgstr`만 직접 수정(288과 같은 이유로 `sphinx-intl update` 미사용).

## 0.2.0

beta.5(2026-08-13) 이후 `main`의 사용자 영향 변경은 About 창 새 버전 확인(289),
Bookstein이 한국어 UI에서 Procrustes로 돌던 버그, 곡선 이름 유실 버그, 이번 번역.
EFA(288)는 `feature/efa-outline-analysis`에 남겨 0.3.0으로 간다.

CHANGELOG `[0.2.0]` 절은 beta.5 이후 변경에 더해, 0.1.x에서 바로 올라오는 사용자를
위한 요약(설치 위치·데이터 폴더·CVA 수치 변화 등)을 담았다. 릴리스 본문은 이 절만
게시되므로 베타별 상세는 CHANGELOG 링크로 넘긴다.

0.1.12 사용자는 About 창 확인 기능이 없는 버전이라 0.2.0을 앱 안에서 안내받지
못한다. 0.2.0-beta.5 사용자는 같은 0.2.0 줄이라 안내받는다(devlog 289 규칙).

## 환경

`~/venv/Modan2`(Python 3.12, `requirements-linux.lock` + ruff 0.15.22)를 새로 만들었다.
`lrelease`는 이 venv에 없다 — PySide6를 프로젝트 venv에 넣으면 Qt 바인딩이 둘이 되므로
별도 환경의 `pyside6-lrelease`를 썼다.
