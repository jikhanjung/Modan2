# 논문 벤치마크를 figshare 공개 자료로 전환, MANOVA 시간 측정 수정

## 날짜
2026-10-08

## 발견 경위

논문(Chapter 2) 5차 외부 검토의 체크리스트 "데이터 checksum과 결과 재현 확인"을 실제로 해 보려고
Rovinsky et al. (2021)의 figshare 공개본(CC BY 4.0, https://doi.org/10.6084/m9.figshare.14330759.v1)을
받아, 지금까지 벤치마크가 읽던 `Morphometrics dataset/`의 두 파일과 비교했다.

| 파일 | 공개본과의 관계 |
|---|---|
| `Thylacine2020_NeuroGM.txt` (222 × 72) | 좌표는 `Thylacine2021_NeuroGM.txt`와 222개 모두 정확히 같다. 그러나 표본 이름이 약칭(`AcJu1217`)이고, 순서가 다르며(공개본은 *Canis adustus* → *Lupulella adustus* 등 학명이 바뀌어 정렬이 다름), 붙어 있는 식성·먹이 크기 범주가 공개본(`REA_2021_dataforR.xlsx`)과 다르다 — 범주 체계 자체가 다르고(HypCar 102 … vs Carniv 90, DurCar 16 …), 먹이 크기는 6범주(XXS–XLG)인데 공개본은 2범주(SML/LRG, 포식자 체중의 45% 기준)이며 일치는 210개 중 82개. 출판 전 판으로 보인다. |
| `Rovinsky_etal Morphologika.txt` (14 × 381) | 표본 번호는 공개본 `Thylacine2021_SkullGM.txt`의 thylacine 16개 중 14개와 대응하지만, 같은 표본끼리의 Procrustes 거리가 0.050으로 서로 다른 thylacine 사이(0.045–0.047)만큼 크다. 공개 좌표가 아니다. |

논문은 이 자료를 Rovinsky et al. (2021b)의 것으로, 범주를 그 논문의 범주로 기술하고, Data Availability에서
공개본의 checksum과 받는 스크립트를 약속했다. 그 약속을 지킬 수 없는 상태였다.

## 공개본으로 전환

- `scripts/rovinsky2021_data.py`: figshare에서 `Thylacine2021_NeuroGM.txt`, `Thylacine2021_SkullGM.txt`,
  `REA_2021_dataforR.xlsx`를 받아 figshare가 공개한 MD5와 대조하고(이미 있으면 대조만),
  `benchmarks/data/rovinsky2021/`(`.gitignore`의 `data/`로 제외)에 두 파일을 만든다.
  - `neurocranium_222.txt`: NeuroGM에 `Classifier_Total` 시트의 분류를 변수로 붙임 —
    Clade, Family, Genus, Species, DietFine(FeedCatgFine, 10범주), DietCoarse, PreyCatg. thylacine 16개는 NA.
  - `skull_thylacines_16.txt`: SkullGM(381점)의 thylacine 16개.
  - 좌표·이름·순서는 그대로. xlsx는 표준 라이브러리로 읽는다(분석 환경에 Excel 리더가 없음).
    XML 파싱은 checksum 대조 뒤에만 하므로 S314에 이유를 달아 둠.
- `benchmark_paper_tables.py`: 데이터셋 `cranial222`, `cranial206`(DietFine = NA 제외), `dense16`.
  파일이 없으면 받는 스크립트를 먼저 돌리라고 안내.
- `paper_worked_examples.py`: `bench.DATASETS["cranial206"]`과 `apply_exclusion`을 그대로 쓰고,
  grouping은 DietFine(식성)과 PreyCatg(먹이 크기). 두 범주면 판별축이 하나라 출력이 축 수에 맞게.
- `paper_r_comparison.py`: 판별축이 하나일 때 R(jsonlite)이 값을 배열이 아닌 스칼라로 쓰는 것을 받도록.
- `paper_refinement_sensitivity.py`: `dense14` → `dense16`.
- `paper_accuracy_dense14.json` 삭제, `paper_accuracy_dense16.json` 추가.

`Morphometrics dataset/`의 두 파일은 테스트(`test_analysis_workflow.py`, `test_import.py`)가 쓰고 있어
그대로 두었다. 출처 표기를 붙일지 지울지는 따로 정한다.

## MANOVA 시간 측정 수정

런타임 표의 MANOVA는 `do_manova_analysis_on_pca(pca_result["scores"], groups)` — PC 점수 **전체**
(216개, 표본 206개보다 많음)로 시간을 쟀다. 앱(`ModanController._run_manova`)은
`effective_component_count`로 14개까지 줄인 점수로 계산한다. 그래서 측정한 것은 앱의 계산이 아니었고,
변수가 표본보다 많아 검정 자체가 퇴화했다(새 범주에서 statsmodels가 `invalid value encountered in power`를
경고하면서 드러남). `manova_scores()`로 앱과 같이 줄인 점수를 쓰게 고쳤다. `--manova-paths`도 같은 점수.

이전 논문 수치의 MANOVA 0.36 s는 이 잘못된 경로의 값이다. 바른 값은 0.025 s.

## 결과 (v0.2.0 worktree)

- 런타임(206개, 10그룹, 9회 중앙값, 단독 실행): GPA 0.41 s, Bookstein 0.18 s, PCA 0.05 s, CVA 1.73 s,
  MANOVA 0.025 s, 전체 2.21 s. 결측 5/10/20%: 1.84/1.93/1.99 s (4.5×/4.7×/4.9×).
- 정확도 222개: 평균 1.69/1.69/1.69/1.70% (기준선 1.63%). 좌표는 같지만 표본 순서가 달라 무작위 패턴이
  다른 표본에 떨어지므로 이전 값(1.71/1.70/1.69/1.70%)과 약간 다르다.
- 정확도 dense16: 평균 0.15/0.15/0.15/0.16% (기준선 0.14%).
- Worked example: PCA 52.5%/12.1%, 95%까지 14개(좌표가 같으므로 이전과 같음).
  식성 10범주 CV1/CV2 51.3/19.1%, LOOCV 57.3%(최다 범주 43.7%), balanced 48.9%(10%),
  Wilks λ 0.025, F(126, 1412) = 6.99. 먹이 크기 2범주는 판별축 하나, LOOCV 85.9%(76.2%),
  balanced 78.8%(50%), Wilks λ 0.575, F(14, 191) = 10.07.
  (식성 LOOCV 118/206과 balanced 48.9%가 이전과 같은 것은 우연 — 범주별 재현율은 전혀 다르다.)
- R 비교: GPA 4.9×10⁻⁸, PCA 그대로, CVA 축 비율 ≤ 7.9×10⁻⁷ %p, 두 grouping 모두 LOOCV 분류 차이 0,
  MANOVA 값과 F 상대 차이 ≤ 1.1×10⁻⁷. Hotelling–Lawley F는 식성에서만 근사식 차이(8.7754 vs 8.7674),
  먹이 크기(두 범주)에서는 일치.
- 민감도: 상한 10·20회에서 Table 2 값 변화 없음, 추정값 최대 이동 0.0066% of CS, 평균 오차 변화
  ≤ 3.9×10⁻⁶ %p, 상한 20회에서 80회 중 79회 수렴.
