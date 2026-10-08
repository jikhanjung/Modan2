# CVA 분류 정확도를 CVA 탭에 표시

## 날짜
2026-10-08

## 배경

`MdStatistics.do_cva_analysis`는 P04(devlog의 CVA 차원 계획) 이후 정확도를 계산한다:
교차검증 정확도(기본은 leave-one-out, 계산량이 크면 층화 k겹), 재대입 정확도, 우연
수준(가장 큰 그룹 비율), 차원 축소 여부와 사용한 변수 수, 해결기 경고. 그런데
`_run_cva`가 돌려준 이 값들은 어디에도 저장되지 않았고, 화면에도 나오지 않았다.
0.2.0 릴리스 노트의 "the old figure is still shown, as resubstitution accuracy"는
사실이 아니었다(devlog 293에서 발견).

## 결정

메인 창 분석 패널의 **CVA 탭, CV 점수 플롯 아래 한 줄**에 표시한다. 다른 후보는 맞지
않았다:
- Data Exploration: 플롯 도구이고, 메인 창에서 PCA 탭일 때만 열린다.
- Analysis Details: 저장된 분석이 아니라 현재 랜드마크로 다시 계산하는 창이다.

> Classification accuracy: 58.3% (leave-one-out cross-validation) · chance 50.0% · resubstitution 100.0%

순서가 요점이다. 교차검증 값을 앞에 두고, 그 옆에 우연 수준을 붙여야 그 수치를 읽을
수 있다. 재대입 값은 0.1.x가 보고하던 낙관적인 수치라 비교용으로 남긴다. 축소한 경우
"12 of 40 variables used"를 붙이고, 해결기 경고는 툴팁으로 둔다.

## 구현

- `MdAnalysis.cva_accuracy_json`(마이그레이션 `010_20261008`)과 `get_cva_accuracy()`
  (손상된 값이면 `{}`). 저장 키는 `MdModel.CVA_ACCURACY_KEYS`.
- `_serialize_cva_result`가 CVA 결과에 정확도가 있으면 함께 저장한다.
- `AnalysisInfoWidget.cva_accuracy_text()`가 상태별 문장을 만든다:
  - CVA 없음
  - 이 기능 전에 저장된 분석: "다시 실행하세요"
  - 교차검증 불가: 표본이 너무 적어 하나도 떼어 둘 수 없을 때(`accuracy_method == "unavailable"`)
  - 정상
  - 레거시 분석(JSON 없음)으로 바꿀 때 이전 줄이 남지 않게 `set_analysis`에서 지운다.
- 한국어: "분류 정확도: …% (leave-one-out 교차검증) · 우연 수준 …% · 재대입 …%".
  "{} of {} variables used"는 어순 때문에 "변수 {1}개 중 {0}개 사용".

## 같이 고친 매뉴얼

메인 창은 PCA 탭이 아니면 **Data Exploration**과 **Analysis Details** 버튼을 비활성화한다
(`AnalysisInfoWidget.on_tab_changed`). 그런데 devlog 290 후속 2와 293에서 쓴 매뉴얼은
"PCA나 CVA 탭을 골라 데이터 탐색"이라고 안내했다. 코드를 읽을 때 `btnDataExploration_clicked`만
보고 탭 전환 쪽 제약을 놓친 결과다. 두 버튼은 PCA 탭에서만 쓸 수 있다고 고쳤고, CVA
점수는 CVA 탭에서 본다고 바로잡았다.

그 결과 devlog 293의 "CVA/MANOVA 탭에서 데이터 탐색" 수정은 지금 UI에서는 닿지 않는
경로를 고친 것이다. 다만 버튼 제약이 풀리는 순간 다시 드러날 버그였으므로 되돌리지 않는다.

## 검증

- `tests/test_cva_accuracy_display.py` 14개: 저장, CVA 없음, 손상 값, 표시 문장 상태별,
  레거시 분석으로 바꿀 때 줄 지움, 툴팁.
- `tests/test_migrations.py`에 컬럼 존재 검사 추가.
- `.ts` 9개 번역, `.qm` 392 finished. 매뉴얼 ko 미번역 0 / fuzzy 0, 빌드 경고는 기존 2개.

## EFA 브랜치

`feature/efa-outline-analysis`에도 `migrations/010_20261002.py`가 있다. 다음 rebase 때
EFA 쪽을 `011_…`로 옮겨, `main`에서 이미 010을 적용한 DB에도 순서대로 들어가게 한다.
