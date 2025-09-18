# Missing Landmark 대응 Procrustes 정렬 구현

## 날짜
2025-09-17

## 작업자
Claude

## 배경
- 기존 Procrustes 정렬 파이프라인은 모든 표본이 동일한 랜드마크 개수를 가져야 했고, 하나라도 결측이 있으면 해당 인덱스를 전체에서 제거했음.
- 사용자 요청으로 Object Dialog에 "Add Missing" 기능이 추가되면서 `None`/결측 값을 실제로 저장할 수 있게 되었으나, 분석 단계에서 재사용하지 못하는 문제가 남아 있었음.
- 결측 좌표를 가진 표본도 분석에 참여시키기 위해, 기존 Procrustes 루틴을 최대한 보존하면서 결측 보간과 반복 정렬을 도입할 필요가 발생함.

## 구현 개요
1. **랜드마크 결측 표현 통일 (`MdModel.py`)**
   - `MISSING_LANDMARK_TOKEN`/`is_missing_coordinate`/`is_valid_landmark`/`iter_valid_landmarks` 헬퍼 추가.
   - `pack_landmark`는 결측 좌표를 토큰으로 직렬화하고, 평균·크기·이동·회전 관련 로직은 결측 좌표를 자동으로 건너뛸 수 있도록 수정.
   - `MdDatasetOps`는 더 이상 결측 인덱스를 제거하지 않으며, 기존 Procrustes 반복 루프에 로깅을 추가해 수렴 과정을 추적할 수 있음.

2. **결측 보간 + GPA 반복 (`MdStatistics.py`)**
   - `do_procrustes_analysis()` 시그니처 확장: `missing_method='REG'`, `missing_tol`, `missing_max_iter` 파라미터 추가.
   - 결측이 존재하면 `_procrustes_with_missing()` 경로 선택.
     - 초기화: `None` → `NaN` 변환, 랜드마크/마스크 배열 구성 후 간단한 평균 값으로 임시 채움.
     - 반복 루프: (a) 관측 랜드마크만으로 부분 Procrustes 정렬, (b) 최소제곱(릿지) 회귀로 결측 좌표 예측, (c) 평균 형상 업데이트 후 수렴 검사.
     - 메타데이터(`missing_meta`)에 반복 횟수·수렴 여부·사용한 방법 기록.
   - 기존 결측이 없는 경로는 SciPy `procrustes` 호출 방식 그대로 유지.

3. **컨트롤러/로그/결과 확장 (`ModanController.py`)**
   - 분석 실행 시간을 측정하도록 로깅 보강 (`Analysis execution started/completed`).
   - `_run_procrustes()`에서 새 파라미터를 통과시키고, 결측 보간 메타 정보를 로그로 남기며 결과 JSON에 함께 반환.

4. **UI/사용 흐름 조정**
   - Object Dialog에서 추가한 `Add Missing` 버튼이 저장한 `None` 좌표가 분석 단계까지 유지되고, 보간 루프에서 처리되도록 경로 연결.
   - 기존 Procrustes 루틴을 가능한 한 유지했기 때문에, 결측이 없는 데이터는 과거와 동일한 경로를 따른다.

## 동작 방식 요약
1. 사용자가 Object Dialog에서 결측 랜드마크를 추가하면 `None`으로 저장됨.
2. 분석 실행 시 `MdStatistics.do_procrustes_analysis()`가 결측 존재 여부를 검사.
3. 결측이 있으면 `missing_method='REG'` 기준으로 반복 보간 + Procrustes 정렬 수행.
4. 정렬된 좌표, 평균 형상, centroid size, 결측 보간 메타 정보를 컨트롤러가 받아 로그로 남기고 결과에 포함.

## 한계 및 TODO
- 현재 보간 방법은 회귀(REG)만 구현. TPS 등 다른 방식은 `_update_missing_landmarks()`에서 후속 구현 필요.
- 회귀 모델 학습 대상 표본 수가 부족한 경우 평균 형상 좌표로 폴백하도록 구성되어 있어, 극단적으로 결측이 많으면 추정 정확도가 낮을 수 있음.
- 세미랜드마크 슬라이딩/미러링 등 추가 정밀도 향상 작업은 추후 과제로 남겨둠.
- 컨트롤러 파라미터는 내부 기본값만 사용 중. UI에서 선택할 수 있도록 확장할지 검토 필요.

## 테스트
- 자동 테스트: `pytest --no-xvfb -k procrustes` 실행 시도했으나, 현재 환경에서 Xvfb 접근이 차단되어 수동 확인 필요.
- 향후 GUI 가능 환경에서 Procrustes 및 후속 PCA/CVA/MANOVA 워크플로우를 재검증 권장.

## 관련 파일 요약
- `MdModel.py`: 결측 인식 헬퍼 및 기하학 연산 보강.
- `MdStatistics.py`: 결측-aware Procrustes 루틴과 보조 함수 집합 추가.
- `ModanController.py`: 로그/결과 확장 및 새 파라미터 전달.
- (기존 변경 사항) `ModanDialogs.py`, `ModanComponents.py` 등은 결측 입력 UI/렌더링을 이미 지원.

## 후속 작업 제안
1. TPS 기반 보간 로직 구현 및 하이브리드 전략(예: 관측 수 부족 시 TPS→REG) 실험.
2. 회귀 피처 차원 축소(PCA/PLS) 도입으로 과적합 가능성 감소 검토.
3. 결측 처리 결과를 분석 리포트/JSON에 명시하여 재현성 확보.
4. 실제 사용자 워크플로우를 대상으로 성능·정확도 검증 및 튜닝.
