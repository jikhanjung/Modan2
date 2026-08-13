# CVA 계획 — 판별 전에 차원을 줄이고, 정직한 정확도를 보고한다

## 날짜
2026-08-13

## 배경 — 어떻게 발견했나

dissertation Chapter 2(Modan2 논문)의 worked example에 실제 통계 수치를 넣으려고
Rovinsky et al. (2021) 두개골 데이터셋(222 표본 × 72 랜드마크, 3D)으로 CVA를
돌렸다. 결과:

```
FeedCat1 (식이 범주, 11군):  accuracy = 100.0
PreyRatio (먹이 크기, 7군):  accuracy = 100.0
```

두 그룹 변수 모두 분류 정확도가 정확히 100%다. 그룹 수가 11개이고 가장 작은 군은
표본이 2개(`InsHer`)뿐인데도 그렇다. **이 값은 논문에 넣지 않았다** — 심사자가
곧바로 과적합을 지적할 값이기 때문이다. 대신 CVA 고유값 비율만 인용했다.

## 원인

`MdStatistics.do_cva_analysis` 가 Procrustes 정렬 좌표를 **평탄화한 그대로**
LDA에 넣는다.

```python
data_matrix = np.array(flattened_data)      # 222 x 216
lda = LinearDiscriminantAnalysis()
cv_scores = lda.fit_transform(data_matrix, group_array)
predictions = lda.predict(data_matrix)      # 훈련에 쓴 바로 그 데이터
accuracy = accuracy_score(group_array, predictions) * 100
```

변수가 216개(랜드마크 72 × 3차원), 표본이 222개다. 판별분석에서 군내 산포행렬의
자유도는 대략 `n − g` = 222 − 11 = 211 인데 변수가 216개이므로 **군내 산포행렬이
특이하거나 특이에 가깝다.** 이 조건에서 선형판별은 어떤 그룹 분할이든 완벽하게
분리한다. 그룹이 실제로 다른지와 무관하다.

여기에 두 번째 문제가 겹친다. 정확도를 **훈련에 사용한 바로 그 데이터로**
측정한다(재대입, resubstitution). 과적합된 모형의 재대입 정확도는 정의상 100%에
가깝고, 아무 정보도 담고 있지 않다.

사용자에게는 "완벽하게 분류된다"로 읽힌다. 즉 이 숫자는 비어 있는 정도가 아니라
**적극적으로 오해를 부른다.**

## 그리고 일관성 문제이기도 하다

같은 분석 실행 안에서 MANOVA는 이미 차원을 줄인다. `ModanController._run_manova`:

```python
# 누적 분산 95% 지점까지의 성분 수, 단 20개 상한
for i, eigenvalue in enumerate(eigenvalues):
    cumulative_variance += eigenvalue
    if cumulative_variance / total_variance >= 0.95:
        effective_components = i + 1
        break
...
manova_data = [score[:effective_components] for score in pca_scores]
```

이 데이터셋에서 13개 성분이 선택된다. 즉 **하나의 PCA 분석 실행에서 MANOVA는
13차원을, CVA는 216차원을 본다.** 두 검정이 같은 데이터를 보고 있다고 믿을 근거가
없고, 결과를 나란히 해석할 수도 없다.

`MdStatistics.py` 는 이미 MANOVA 쪽에 축소 개념을 갖고 있다 —
`MANOVA_MAX_VARIABLES = 20` 과, 결과에 `n_variables_total` /
`n_variables_used` / `truncated` 를 실어 보내는 관례. CVA에는 그에 해당하는 것이
없다.

---

## 계획

### 1단계 — 축소를 `do_cva_analysis` 안에서 한다

MANOVA처럼 컨트롤러에서 줄이지 **않는다.** `do_cva_analysis` 는 테스트
(`test_mdstatistics.py`, `test_multi_analysis_workflow.py`)와 컨트롤러 양쪽에서
직접 불린다. 컨트롤러에만 고치면 함수를 직접 부르는 경로는 그대로 망가진 채
남는다. 축소는 함수 안에 두고, 시그니처는 그대로 유지한다.

### 2단계 — 축소 규칙

공용 헬퍼를 `MdStatistics` 에 두어 MANOVA와 CVA가 같은 규칙을 쓰게 한다.

```
k = min( 누적분산 95% 에 필요한 성분 수,
         MAX_VARIABLES (20),
         n_samples − n_groups − 1 )
k = max(k, 1)
```

세 번째 항이 이번 문제의 핵심이다. `n − g − 1` 은 군내 산포행렬을 비특이로 만드는
데 필요한 여유이고, 이것을 넘지 않는 한 판별은 자동으로 완벽해지지 않는다.
95% 기준만으로는 부족하다 — 표본이 적고 랜드마크가 많은 데이터셋(예: 동봉된
14 × 381)에서는 95%에 도달하는 성분 수가 이미 표본 수를 넘길 수 있다.

**변수 수가 이미 충분히 적으면 축소하지 않는다.** `n_features <= n_samples −
n_groups` 이면 원좌표를 그대로 쓴다. 잘 조건화된 소규모 데이터셋의 현행 동작을
바꾸지 않기 위해서다.

이 데이터셋에서는 `min(13, 20, 210) = 13` 이 되어 **MANOVA와 정확히 같은 13차원**을
본다. 목표했던 일관성이 여기서 확보된다.

### 3단계 — 정확도를 교차검증으로 보고한다

재대입 대신 층화 K겹 교차검증을 쓴다. 겹 수는 가장 작은 군의 크기에 맞춘다:

```
n_splits = min(5, 가장 작은 군의 표본 수)
가장 작은 군이 2 미만이면 교차검증 불가
```

Rovinsky 데이터셋의 `InsHer` 가 2개이므로 2겹이 된다.

반환 키는 이렇게 한다. 기존 `accuracy` 의 의미를 조용히 바꾸는 대신 둘 다 싣고,
어느 쪽인지 명시한다:

| 키 | 내용 |
|---|---|
| `accuracy` | 교차검증 정확도 (교차검증 불가 시 `None`) |
| `accuracy_method` | `"cross-validated (k folds)"` 또는 `"unavailable"` |
| `resubstitution_accuracy` | 기존 값. 참고용으로 남긴다 |
| `n_variables_total` / `n_variables_used` / `reduced` | MANOVA의 보고 관례를 그대로 따른다 |

**교차검증 정확도는 100%보다 한참 낮게 나올 것이고, 그것이 요점이다.** 값이
떨어졌다고 회귀로 읽지 않도록 릴리스 노트에 적어야 한다.

### 4단계 — UI

현재 `accuracy` 를 화면에 표시하는 코드는 없다(`dialogs/`, `components/` 에
소비처 없음). 컨트롤러 `_run_cva` 가 결과 딕셔너리에 실어 보낼 뿐이다. 따라서
UI 변경은 이번 범위에 없지만, 나중에 표시하게 된다면 **`accuracy_method` 를 값
옆에 함께 보여야 한다.** 방법을 밝히지 않은 분류 정확도는 그 자체로 오해의 소지가
있다.

---

## 기존 테스트에 미치는 영향

`tests/test_mdstatistics.py::TestCVAAnalysis` 세 건은 모두 축소 경로를 타게 된다:

| 테스트 | n / 군 / 변수 | `n−g−1` | 축소 후 | 단언 통과 여부 |
|---|---|---|---|---|
| `basic` | 6 / 2 / 6 | 3 | ≤3 | `len(canonical_variables) == 6` (표본 수) — 통과 |
| `three_groups` | 6 / 3 / 4 | 2 | ≤2 | `n_components == 3` (3으로 패딩) — 통과 |
| `padding` | 4 / 2 / 4 | 1 | 1 | `n_components == 3` (패딩) — 통과 |

세 건 모두 표본 수와 패딩된 성분 수만 단언하므로 그대로 통과할 것으로 보이지만,
**실행해서 확인해야 한다.** `test_controller.py:339` 는 `do_cva_analysis` 를
mock 하므로 무관하다.

축소 규칙 자체를 직접 겨냥한 테스트를 새로 추가한다:

1. 변수 수 > 표본 수인 데이터에서 재대입 정확도가 100%인데 교차검증 정확도는
   그보다 낮다 — 이 문제의 회귀 테스트.
2. 같은 데이터에서 CVA가 쓴 변수 수와 MANOVA가 쓴 변수 수가 일치한다.
3. 변수 수가 이미 적으면 축소가 일어나지 않는다(`reduced == False`).
4. 가장 작은 군이 1개일 때 `accuracy is None`, `accuracy_method == "unavailable"`,
   예외는 발생하지 않는다.

## 위험

1. **저장된 분석 결과와의 불연속.** 새 CVA는 이전 버전과 다른 canonical variable
   값을 낸다. 기존 DB의 결과는 그대로 남으므로 같은 데이터셋을 다시 분석하면
   숫자가 달라진다. 릴리스 노트에 명시해야 하고, 논문에 인용한 CVA 고유값 비율
   (CV1 74.0%, CV2 16.2%)도 **수정 후 다시 뽑아 갱신해야 한다.**
2. **축소가 군 간 차이를 실제로 버릴 수 있다.** 95% 분산 기준은 분산이 큰 축을
   남기지 군을 잘 가르는 축을 남기지 않는다. 이론적으로는 판별 신호가 하위 성분에
   있을 수 있다. 다만 MANOVA가 이미 같은 기준을 쓰고 있으므로 새로 도입되는
   위험이 아니라 **이미 존재하는 선택을 CVA로 확장하는 것**이다. 두 검정이
   불일치하는 현 상태보다 낫다.
3. **작은 군에서 교차검증이 불안정하다.** 2겹 교차검증의 정확도는 분산이 크다.
   그래도 100%라는 무의미한 값보다는 낫고, `accuracy_method` 가 겹 수를 밝히므로
   사용자가 신뢰도를 판단할 수 있다.

## 후속으로 미뤄둘 것

MANOVA의 성분 선택 로직이 `ModanController._run_manova` 안에 있다. 공용 헬퍼를
`MdStatistics` 에 만들고 나면 MANOVA도 그것을 쓰도록 옮기는 것이 맞지만, 컨트롤러
경로를 건드리는 변경이라 이번 계획에서 분리한다. 1차에서는 헬퍼를 만들고 CVA만
연결한다.

## 참고

- 발견 경위와 측정값: `devlog/20260813_287_paper_benchmarks_and_cva_overfit.md`
- 논문 쪽 기록: paper_vault `Dissertation/devlog/20260813_chapter2_restructure.md`
- 재현: `python scripts/benchmark_paper_tables.py` 와 같은 방식으로 동봉
  `Morphometrics dataset/Thylacine2020_NeuroGM.txt` 를 읽어 `FeedCat1` 로 CVA
