# CVA/MANOVA 변수 선택 및 계산 오류 수정

## 날짜
2025-09-09

## 작업자
Claude

## 문제 상황

### 1. 변수 선택 버그
**증상**:
- 분석 대화상자에서 CVA/MANOVA를 위해 'prey' 변수를 선택했지만, 실제 분석은 'diet' 변수로 수행됨
- 사용자가 선택한 변수가 무시되고 다른 변수가 사용되는 문제

**원인**:
- `NewAnalysisDialog`는 선택된 변수의 인덱스를 `currentData()`로 반환
- `ModanController.run_analysis()`에서 이 인덱스를 변수명으로 변환하지 않고 그대로 저장
- 데이터베이스에 인덱스가 저장되어 UI에서 잘못된 변수가 표시됨

### 2. MANOVA P값 이상
**증상**:
- CVA는 그룹이 명확히 구분되는데, MANOVA의 모든 P값이 1.000으로 표시
- Wilks' Lambda, Pillai's Trace 등 모든 통계량의 P값이 동일하게 1.000

**원인 분석**:
1. 초기에는 원시 랜드마크 데이터를 MANOVA에 사용 (잘못된 접근)
2. PCA 점수를 사용하도록 수정했으나, eigenvalue 계산 오류로 0개의 컴포넌트 선택
3. MANOVA 결과가 생성되지 않아 UI에 표시되지 않음

## 해결 방법

### 1. 변수 선택 버그 수정

**ModanController.py**에서 인덱스를 변수명으로 변환:

```python
# Convert group_by indices to variable names for storage
variablename_list = self.current_dataset.get_variablename_list()
cva_group_by_name = None
manova_group_by_name = None

if cva_group_by is not None and isinstance(cva_group_by, int):
    if 0 <= cva_group_by < len(variablename_list):
        cva_group_by_name = variablename_list[cva_group_by]
        self.logger.info(f"CVA group_by: index {cva_group_by} -> variable '{cva_group_by_name}'")

# 데이터베이스에 변수명 저장
analysis = MdModel.MdAnalysis.create(
    ...
    cva_group_by=cva_group_by_name,
    manova_group_by=manova_group_by_name,
    ...
)
```

### 2. MANOVA 계산 수정

#### 접근 방법 변경 과정:

**시도 1**: 원시 랜드마크 데이터 사용
- 문제: 통계적으로 부적절한 접근

**시도 2**: Procrustes 정렬된 랜드마크 직접 사용
- 문제: 변수가 너무 많아(1143개) 계산 불가능
- 해결 시도: 처음 20개 변수만 사용 → 임시방편

**최종 해결**: PCA 점수 사용 with eigenvalue 기반 선택
```python
def _run_manova(self, landmarks_data, params):
    pca_result = params.get('pca_result', None)

    if pca_result and 'scores' in pca_result:
        # eigenvalue 기반으로 95% 분산을 설명하는 컴포넌트 선택
        eigenvalues = pca_result['explained_variance']
        total_variance = sum(eigenvalues)
        cumulative_variance = 0

        for i, eigenvalue in enumerate(eigenvalues):
            cumulative_variance += eigenvalue
            if cumulative_variance / total_variance >= 0.95:
                effective_components = i + 1
                break

        # 최대 20개로 제한 (계산 안정성)
        if effective_components > 20:
            effective_components = 20

        # PCA 점수 추출 및 MANOVA 수행
        pca_scores = pca_result['scores']
        manova_data = [score[:effective_components] for score in pca_scores]
        manova_result = MdStatistics.do_manova_analysis_on_pca(manova_data, groups)
```

### 3. MANOVA 결과 표시 수정

**ModanComponents.py**에서 JSON 포맷 호환성 처리:

```python
if self.analysis.manova_analysis_result_json:
    manova_result_raw = json.loads(self.analysis.manova_analysis_result_json)

    # stat_dict 포맷 확인 및 래핑
    if isinstance(manova_result_raw, dict):
        if 'stat_dict' in manova_result_raw:
            manova_result = manova_result_raw
        elif 'column_names' in manova_result_raw:
            # stat_dict 자체인 경우 래핑
            manova_result = {'stat_dict': manova_result_raw}
```

## 구현 세부사항

### 추가된 함수들:

1. **MdStatistics.py**:
   - `do_manova_analysis_on_pca()`: PCA 점수 기반 MANOVA
   - `do_manova_analysis_on_procrustes()`: Procrustes 데이터 기반 MANOVA (폴백)

2. **로깅 강화**:
   - 각 단계별 상세 로그 추가
   - 변수 선택, PCA 컴포넌트 수, MANOVA 결과 등 추적

## 테스트 결과

### 수정 전:
- CVA/MANOVA 변수 선택 불일치
- MANOVA P값 모두 1.000
- MANOVA 결과 테이블 비어있음

### 수정 후:
- 선택한 변수가 올바르게 적용됨
- MANOVA가 적절한 P값 계산
- Wilks' Lambda, Pillai's Trace 등 통계량 정상 표시

## 향후 개선사항

1. **PCA 컴포넌트 선택 기준 개선**:
   - 현재 95% 고정 → 사용자 설정 가능하도록
   - Scree plot 기반 자동 선택 옵션

2. **MANOVA 변수 수 제한**:
   - 현재 20개 고정 → 샘플 수 대비 동적 조정

3. **UI 개선**:
   - 선택된 변수명 실시간 표시
   - MANOVA에 사용된 PC 수 표시

## 참고사항

- 원본 Modan2는 PCA 점수를 MANOVA에 사용 (올바른 접근)
- statsmodels의 MANOVA는 변수 수가 샘플 수보다 많으면 실패
- CVA는 원시 데이터에서도 작동하지만, MANOVA는 차원 축소 필요

## 관련 파일
- `/mnt/d/projects/Modan2/ModanController.py`
- `/mnt/d/projects/Modan2/MdStatistics.py`
- `/mnt/d/projects/Modan2/ModanComponents.py`
- `/mnt/d/projects/Modan2/ModanDialogs.py`
