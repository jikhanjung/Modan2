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

## 후속: 매뉴얼의 UI 이름 인용 통일 (같은 날)

위 "매뉴얼" 절의 7곳 수정은 **한 줄짜리 `msgstr`만 grep한 결과**였다. 여러 줄로
감싼 `msgstr`까지 파싱하니(`msgid`/`msgstr` 연속 줄을 이어 붙여 디코드) 더 있었다
— 그리고 문제가 이번 번역분에 국한되지 않았다. 한국어 매뉴얼은 오래전에 번역된
UI(설정, 인덱스, 불러오기 …)까지 영어로 인용하는 게 사실상의 관례였고, 7곳만
한국어로 바꾼 것은 오히려 한 문단 안에 "**Index** / **이름**" 같은 혼용을 만든다.
0.2.0 릴리스 노트의 "매뉴얼이 화면에 보이는 이름을 쓴다"는 문장도 그 시점엔 반만
사실이었다.

사용자 결정: **한국어 + 영어 병기**. 형식은 매뉴얼에 이미 있던
`**분석**\ (Analyze, ``Ctrl+G``)`를 따라 `**한국어**\ (English)`.

- 대상: `.ts`에서 번역문이 원문과 다른 라벨이 `msgstr`의 `**…**`/`*…*` 안에 영어로
  남은 곳. 4개 파일 59개 항목.
- 같은 영어라도 화면(context)마다 다르다 — 항목별로 rst 원문과 코드를 보고 실제 위젯을
  확인했다. 회귀선의 **All**은 DataExploration에서 `tr()` 대상이 아니라 영어 유지
  (`전체선택`은 분석 대화상자의 다른 버튼). 메인 창 표의 **Curve**/**LM Count** 열은
  `header_labels`가 하드코딩이라 영어 유지. **Landmark**/**Calibration** 모드 버튼은
  글자 없는 아이콘이라 영어 유지.
- 영어 매뉴얼이 화면과 다른 곳은 한국어 쪽을 **화면 기준**으로 썼다: quick_start의
  새 데이터셋 "**Name** … **OK**"는 실제로 **데이터셋 이름** / **저장** 버튼,
  가져오기 대화상자의 "**Import**"는 **가져오기 실행**(Execute Import). 영어 원문은
  그대로다 — 고치면 msgid가 바뀌어 번역을 다시 맞춰야 하므로 별도 작업.
- 조사는 한국어 단어 기준으로 다시 붙였다("Curve 나" → "곡선\ (Curve)이나").
  정규식 일괄 치환을 하지 않은 이유다. 치환은 디코드한 `msgstr`에서 정확히 1회
  일치해야만 적용되게 해서 엉뚱한 곳이 바뀌지 않게 했다.
- 검증: 한국어 Sphinx 빌드 경고 수 전후 동일(기존 2개), 렌더된 HTML에 닫히지 않은
  `**` 없음, 재스캔 시 남은 영어 라벨은 위의 의도된 3종뿐.

## 후속 2: 영어 매뉴얼을 실제 UI에 맞춤 (같은 날)

위 절에서 별도 작업으로 미룬 "영어 원문이 화면과 다른 곳"을 처리했다. 7개 문서를
코드와 한 줄씩 대조하니 버튼 이름 몇 개 수준이 아니었다:

- **메뉴 경로**: File 메뉴에는 Exit뿐이다. Import/Export/Analyze/백업은 전부 **Data**
  메뉴. "File → Import"가 여러 문서에 있었다. "Settings → Visualization",
  "View → Reset Camera", "Right-click → Properties", ``Ctrl+O``(데이터베이스 열기)도 없다.
- **없는 기능**: Import Objects / Add Images 대화상자, 스크리 플롯, PC 점수 표, CSV 내보내기,
  분류 테이블, 효과 크기(부분 η²), Fit to View, Estimate Missing, 변수 매핑, 조명 설정.
  실제 경로로 바꿨다 — 이미지는 객체 표로 드롭하거나 New Object → Load Image, 결과 표는
  Analysis Details(→ Save Results, ``.xlsx``), 플롯은 Export Chart(PNG/JPG/PDF/SVG).
- **동작 차이**:
  - 가져오기는 항상 **새 데이터셋**을 만든다(선택한 데이터셋에 추가하지 않음).
    랜드마크 파일 드롭은 트리에만 연결돼 있다.
  - 객체를 트리로 끌면 **복사**되고, Shift를 누르면 이동이다.
  - 데이터셋 더블클릭은 데이터셋 대화상자를 연다. 분석 결과는 한 번 클릭으로 보인다.
  - 3D 뷰어는 가운데 드래그가 이동, 오른쪽 드래그가 확대다.
  - 회귀선의 All/By group 콤보는 숨겨져 있다.
  - Baseline 체크박스는 늘 숨겨져 있다.
  - 분석 최소 객체 수는 5개다.
- **변수 0개면 분석 전체가 거부된다**(`_validate_dataset_for_general_analysis`). 경고문은
  "Only PCA analysis will be available"이라고 하지만 `return False`라 PCA도 안 돈다.
  Quick Start의 "변수 추가 (선택)"는 사실이 아니어서 "현재는 하나 이상 필요"로 썼다
  — 코드가 의도대로 고쳐지면 되돌릴 문장이다.

`.po`는 `sphinx-intl update` 없이 직접 고쳤다: 새 `.pot`와 기존 `.po`의 msgid 순서를
정렬해 바뀐 문단을 찾고, msgid·msgstr을 함께 교체/삽입/삭제(주석은 보존). 한 문서 안의
같은 원문은 번역을 하나만 가진다는 점에 주의 — Quick Start의 "Click **OK**"는 새
데이터셋(실제는 Save)과 분석(실제 OK) 두 곳이 같은 항목이라, 앞의 후속 절에서 "저장"으로
바꾼 번역이 분석 단계까지 "저장"으로 만들고 있었다. 영어를 "Click **Save**"로 고치면서
항목이 갈라져 해결됐다.

이전부터 남아 있던 번역 공백도 메웠다: FAQ·개발자 가이드의 라이선스 문단(GPL-3.0 빌드
설명, 11개 미번역)과 Resistant Fit 철회 전의 fuzzy 4개. 이제 전 카탈로그 미번역 0 /
fuzzy 0 / 남은 옛 항목 0. 한국어·영어 빌드 경고는 기존 2개 그대로.

코드 쪽에서 본 것(매뉴얼은 손대지 않음):
- 내보내기의 **X1Y1** 라디오는 `export_dataset`에 분기가 없어 아무 파일도 쓰지 않는다.
- 내보내기의 Object List / Export List 선택을 무시하고 항상 전체 객체를 쓴다.
- Analysis Details는 저장된 분석이 아니라 데이터셋에서 Procrustes PCA를 다시 계산한다.
- 내보내기 대화상자에 비활성 "Resistant fit" 라디오가 남아 있다.
