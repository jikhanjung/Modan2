# Procrustes 회전의 반사 보정 수정

## 날짜
2026-10-08

## 발견 경위

논문(Chapter 2)의 분석을 R 독립 구현과 비교하는 스크립트(`scripts/paper_r_comparison.py`)를
만들면서, 비교가 다루지 못하는 분기가 있는지 보려고 `MdDatasetOps.rotation_matrix()`가
반사를 보정한 횟수를 세게 했다. 코드를 읽다가 그 보정 자체가 틀린 것을 찾았다.

## 무엇이 틀렸나

`rotation_matrix(ref, target)`는 `ref.T @ target`을 SVD해 `v, s, w`를 얻고 `v @ w`를
회전으로 쓴다. 이것이 반사(행렬식 −1)이면 반사 없이 가장 잘 맞는 회전은
`v @ diag(1, …, −1) @ w`다(Kabsch). 즉 `v`의 마지막 **열**을 뒤집는다. 그 열은 가장 작은
특이값, 곧 두 형태가 가장 덜 맞는 방향이어서 포기해도 손해가 가장 적다.

코드는 `v[-1, :] = -v[-1, :]`, 즉 마지막 **행**을 뒤집었다. 이는 `diag(1, …, −1) @ v @ w`와
같다. 결과는 회전(행렬식 +1)이지만, "반사를 허용한 최적 맞춤을 한 뒤 좌표계의 마지막
축(3D z, 2D y)을 뒤집은 것"이다. 어느 축을 포기할지를 자료가 아니라 좌표계가 정한다.

- 거울상에 가까운 3D 배치 한 예: 잔차가 반사 허용 0.781, 올바른 회전 1.738, 이전 코드 2.500.
- 무작위 시험 2000번 모두 이전 코드가 Kabsch보다 잔차가 컸다(중앙값 1.49배).

## 언제 일어나나

최적 직교변환이 반사일 때만. 좌우가 뒤집혀 들어온 표본, 그리고 landmark가 거의 한
직선(2D)이나 평면(3D) 위에 있어 가장 작은 특이값이 0에 가까운 경우 — 잡음만으로 반사
쪽이 최적이 된다. 후자에서 올바른 보정은 비용이 거의 없지만, 이전 코드는 결과의 마지막
축을 통째로 뒤집었다.

논문 자료에는 한 번도 없었다: cranial 206·222개, dense 14개의 완전한 자료와 Table 2의
결측 실행 80회, 합계 회전 약 14만 번 중 반사 0번. 결측 추정의 회전
(`impute_missing_landmarks`, 처음부터 Kabsch)과 Bookstein 등록은 이 함수를 쓰지 않는다.

## 수정

`MdModel.py` `rotation_matrix()`: `v[:, -1] = -v[:, -1]`, 이유를 주석으로.

## 테스트

- `tests/test_mdmodel.py` `TestMdDatasetOpsRotationMatrix`에 두 개 추가 — 반사가 최적인
  잡음 섞인 거울상 쌍(시드 고정, 반사 조건을 테스트 안에서 확인)에서
  - 3D: SciPy `Rotation.align_vectors`(독립 Kabsch 구현)와 행렬이 일치
  - 2D: 닫힌 형태의 최적 각도와 일치

  두 테스트 모두 이전 코드에서는 실패하는 것을 확인했다.
- **골든 테스트 갱신:** `tests/dialogs/test_data_exploration_scatter.py`의 자료는 거의
  일직선 위의 3점 형태 6개라 이 경우를 자주 밟는다(이전 코드에서 회전 60번 중 23번).
  수정 후 GPA가 3회 반복(회전 18번)으로 수렴하고 평균까지의 거리 제곱합도 0.054878 →
  0.05487723으로 줄었다. PCA는 PC1·PC2 부호가 뒤집히고 점수가 최대 6×10⁻⁵ 움직였다.
  테스트 docstring의 안내대로 골든 값을 다시 만들고 이유를 주석으로 남겼다.
- 전체 스위트(Xvfb): 2106 passed, 10 skipped.

## 가려져 있던 테스트 13개

`tests/test_mdmodel.py`에 같은 이름의 클래스가 여섯 쌍 있었다. 뒤에 정의된 클래스가 앞의 것을
덮어써서 앞 클래스의 테스트 13개가 수집조차 되지 않았다. `pyproject.toml`이 `test_*.py`에
F811(재정의)을 무시하게 해 두어 ruff도 잡지 않았다. 반사 보정 테스트를 넣을 자리를 찾다가 발견.

같은 이름의 메서드도 세 쌍 있었지만 내용이 모두 달라(AST로 비교), 지우지 않고 앞 클래스의
이름만 내용에 맞게 바꿨다.

| 행 | 이전 이름 | 새 이름 | 살아난 테스트 |
|---|---|---|---|
| 367 | `TestMdAnalysis` | `TestMdAnalysisBasics` | 2 |
| 1694 | `TestMdObjectCopyOperations` | `TestMdObjectChangeDataset` | 2 |
| 1747 | `TestMdDatasetAddOperations` | `TestMdDatasetAddBasics` | 4 |
| 1864 | `TestMdObjectRefresh` | `TestMdObjectRefreshOperation` | 1 |
| 2043 | `TestMdDatasetOpsRotationMatrix` | `TestMdDatasetOpsReferenceAndRotation` | 2 |
| 2186 | `TestMdObjectOpsEdgeCases` | `TestMdObjectOpsMissingLandmarks` | 2 |

13개 모두 지금 코드에서 통과한다. `test_mdmodel.py` 309 passed.

## 다른 두 파일, 그리고 재발 방지

이어서 같은 문제가 있던 두 파일도 정리했다(별도 커밋).

| 파일 | 가려져 있던 클래스 | 처리 |
|---|---|---|
| `tests/test_mdhelpers.py` | `TestFileBackup` (548행) | **삭제.** 두 테스트 모두 수집되던 쪽(705행)의 약한 사본이다. 성공 테스트는 `if result:` 안에서만 검사해 실패해도 통과했고, 실패 테스트는 고정 절대 경로를 썼다. |
| | `TestColorFunctions` (404행) | `TestColorConversion`으로 이름 변경. 그 안의 `test_parse_color_invalid`는 수집되던 쪽의 엄격한 버전(`is None`)이 포괄하므로 삭제. 살아난 테스트 3개(hex·이름 파싱, `color_to_hex`). |
| `tests/test_mdutils.py` | `TestUtilityFunctions` (170행) | `TestValueAndDroppedFileHelpers`로 이름 변경. 살아난 테스트 5개. 그중 `test_is_numeric`에는 R01 수정(`is_numeric(None)`이 예외 대신 False)의 회귀 검사가 들어 있었는데, 지금까지 한 번도 실행되지 않았다. 지금 코드에서 통과한다. |

`pyproject.toml`의 `"test_*.py"` 무시 목록에서 F811을 뺐다. 다시 켜자 `tests/test_semilandmark.py`의
중복 import(`QTableWidget`, 448행과 630행) 하나가 잡혀 뒤쪽에서 지웠다. `ruff check .` 통과.

전체 스위트: 2127 passed, 10 skipped — 2106에 살아난 테스트 21개(13 + 3 + 5)가 더해진 수.
