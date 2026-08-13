# 논문용 벤치마크 스크립트, 그리고 CVA가 정확도 100%를 보고하는 문제

## 날짜
2026-08-13

## 관련 커밋
`e61b437`

---

## 한 일

### 1. `scripts/benchmark_paper_tables.py` 추가

기존 `benchmark_analysis.py`는 무작위 데이터로 분석 원시연산을 잰다. 회귀 추적에는
맞지만 논문에 인용할 수치는 나오지 않는다. 새 스크립트는 저장소에 동봉된 Morphologika
데이터셋을 읽고 **앱이 실제로 실행하는 경로**를 잰다.

```bash
python scripts/benchmark_paper_tables.py --runs 9 --markdown          # 런타임 표
python scripts/benchmark_paper_tables.py --accuracy --patterns 10     # 결측 추정 정확도
python scripts/benchmark_paper_tables.py --dataset dense14 --accuracy
python scripts/benchmark_paper_tables.py --manova-paths               # MANOVA 경로별 비용
python scripts/benchmark_paper_tables.py --repo <다른 checkout>       # 버전 간 비교
```

`--markdown`은 원고에 그대로 붙일 표를 출력하고, JSON은 CPU·RAM·버전·git describe와
함께 `benchmarks/`에 저장된다. 수치는 그 정보 없이는 의미가 없다.

`--repo`는 다른 checkout(예: 이전 태그의 worktree)의 코드로 돌리되 데이터셋은 이
저장소에서 읽는다. 런타임 차이가 **코드 때문인지 기계 때문인지** 분리하려는 것이다.

### 2. MANOVA 진입점이 셋인데 비용이 10배 다르다

논문의 0.37 s가 재현되지 않아 파고든 결과:

| 함수 | 시간 (222×72, 3D) |
|---|---|
| `do_manova_analysis_on_pca` — **`ModanController._run_manova`가 쓰는 것** | **0.366 s** |
| `do_manova_analysis` (generic) | 0.172 s |
| `do_manova_analysis_on_procrustes` | 0.033 s |

발표값이 맞았고 내가 처음 잰 함수가 틀렸던 것이다. 틀린 것을 재면 워크플로 비용을
한 자릿수 적게 보고하게 되므로, 스크립트는 PCA 점수 경로를 재고 docstring에 이유를
적어뒀다.

### 3. beta.2 대 beta.3 — 차이 없음

같은 기계(i7-6700)에서 beta.2 worktree로 돌린 결과:

| 연산 | beta.2 | beta.3 |
|---|---|---|
| Procrustes | 0.481 s | 0.429 s |
| Bookstein | 0.210 s | 0.180 s |
| PCA | 0.059 s | 0.041 s |
| CVA | 0.083 s | 0.062 s |
| MANOVA | 0.410 s | 0.364 s |

전반적으로 약 10% 빠르지만 알고리즘 변화가 아니라 측정 노이즈 수준이다. 논문 발표값
(i5-1240P 노트북)과의 차이는 전부 하드웨어 때문.

### 4. 결측 추정 정확도 검증 모드

`--accuracy`는 무작위로 제거한 랜드마크를 복원한 뒤, 그 표본이 **완전 데이터로 분석했을
때 차지하는 위치**와 비교한다. 두 배치를 그 표본의 *제거된 적 없는* 랜드마크만으로
공통 좌표계에 놓으므로, 잔차가 전역 정렬 차이가 아니라 추정 자체를 반영한다.
mean-shape 추정자가 피할 수 없는 하한(shape-variation floor)도 함께 보고한다.

논문의 값이 그대로 재현됐다 — floor(1.63%/1.42%, 0.14%/0.13%)와 imputed 개수가
정확히 일치.

---

## 발견한 문제 — 미해결

### CVA가 분류 정확도 100%를 보고한다

Rovinsky 두개골 데이터셋(222 표본 × 72 랜드마크, 3D)에서 식이 범주(11군)와 먹이
크기(7군) 둘 다 `accuracy: 100.0`이 나온다.

원인은 `do_cva_analysis`가 **216개 변수(72 × 3)를 그대로 222개 표본에 LDA로 적합**
시키는 것이다. 변수 수가 표본 수와 거의 같으니 재대입(resubstitution) 정확도 100%는
필연이고, 이 값은 아무 정보도 담고 있지 않다. 사용자에게는 "완벽하게 분류된다"로
읽히므로 적극적으로 오해를 부른다.

**일관성 문제이기도 하다.** MANOVA는 이미 PCA 점수를 95% 분산 기준으로 축소해서
(이 데이터셋에서 13개 성분) 돌린다 — `ModanController._run_manova`. CVA만 원좌표
216개를 쓴다. 같은 분석 실행 안에서 두 검정이 서로 다른 차원의 데이터를 본다.

생각해볼 수정 방향:

1. CVA도 PCA 점수 위에서 돌린다 (MANOVA와 같은 성분 선택 규칙). 가장 일관적이다.
2. 재대입 대신 **교차검증 정확도**를 보고한다. 최소한 값이 정직해진다.
3. 둘 다 하고, 변수 수 대비 표본 수가 부족하면 UI에서 경고한다.

논문(dissertation Chapter 2)에는 이 값을 **넣지 않았다.** 심사자가 곧바로 과적합을
지적할 값이다. 대신 CVA 고유값 비율(CV1 74.0%, CV2 16.2%)만 인용했다.

---

## 참고

- 논문 쪽 기록: paper_vault `Dissertation/devlog/20260813_chapter2_restructure.md`
- 동봉 데이터셋의 이름과 내용이 어긋나 있다. `Thylacine2020_NeuroGM.txt`가 222×72
  (FeedCat1/PreyRatio 변수), `Rovinsky_etal Morphologika.txt`가 14×381
  (변수 Sex, 표본명 전부 `ThCy…`). 논문에서 데이터셋을 인용할 때 혼동하기 쉽다.
