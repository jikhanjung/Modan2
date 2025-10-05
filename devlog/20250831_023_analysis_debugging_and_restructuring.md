# Modan2 분석 시스템 디버깅 및 재구성 문서

## 작업 일자
2025-08-31

## 개요
Modan2의 통계 분석 시스템(PCA, CVA, MANOVA)에서 발생한 여러 문제들을 해결하고 전체 구조를 재구성한 작업 내용을 정리합니다.

## 주요 문제점 및 해결 과정

### 1. UI 프리징 문제
**문제**: 분석 실행 후 메인 윈도우가 응답하지 않음
- 증상: 마치 숨겨진 모달 다이얼로그가 있는 것처럼 UI가 완전히 멈춤
- 원인: `ModanMainWindow`에 `set_splash` 메서드가 없어서 발생한 AttributeError

**해결**:
```python
# Modan2.py에 누락된 메서드 추가
def set_splash(self, splash):
    self.splash_screen = splash
```

### 2. 분석 결과 JSON 데이터 누락
**문제**: 분석 결과가 데이터베이스에 저장되지만 JSON 형태로 저장되지 않아 UI에서 표시 불가

**해결**: ModanController.py에서 분석 결과를 JSON으로 직렬화하여 저장
```python
# 분석 결과 JSON 저장 로직 추가
analysis.object_info_json = json.dumps(object_info_list)
analysis.pca_analysis_result_json = json.dumps(result['scores'])
analysis.cva_analysis_result_json = json.dumps(cva_result.get('canonical_variables'))
analysis.manova_analysis_result_json = json.dumps(manova_result)
```

### 3. PCA + CVA + MANOVA 통합 실행
**문제**: 각 분석이 개별적으로만 실행되고 통합 실행이 안 됨

**해결**: PCA 분석 시 CVA와 MANOVA도 함께 실행하도록 구조 변경
```python
if analysis_type.upper() == "PCA":
    pca_result = self._run_pca(landmarks_data, params)

    # CVA도 함께 실행
    if cva_group_by is not None:
        cva_result = self._run_cva(landmarks_data, cva_params)

    # MANOVA도 함께 실행
    if manova_group_by is not None:
        manova_result = self._run_manova(landmarks_data, manova_params)
```

### 4. CVA 결과 표시 문제
**문제**: CVA 분석은 성공하지만 결과가 UI에 표시되지 않음
- 원인: CVA 결과를 'scores' 키로 찾았지만 실제로는 'canonical_variables' 키에 저장됨

**해결**:
```python
# ModanController.py
if 'canonical_variables' in cva_result:
    analysis.cva_analysis_result_json = json.dumps(cva_result['canonical_variables'])
```

### 5. MANOVA 테이블 형식 문제
**문제**: MANOVA 결과가 단일 통계량만 표시되고 4개의 다변량 검정 통계량이 모두 표시되지 않음

**해결**:
1. MdStatistics.py에서 4개 통계량 모두 계산
   - Wilks' Lambda
   - Pillai's Trace
   - Hotelling-Lawley Trace
   - Roy's Greatest Root

2. 각 통계량에 대한 F-통계량과 p-값 계산
3. 표준 통계 형식으로 테이블 구성

```python
# MdStatistics.py
return {
    'test_statistics': [
        {
            'name': "Wilks' Lambda",
            'value': wilks_lambda,
            'f_statistic': wilks_f,
            'p_value': wilks_p,
            'df_num': df_num,
            'df_den': df_den
        },
        # ... 다른 통계량들
    ]
}
```

### 6. 3D 데이터 차원 문제
**문제**: 3D 데이터(72 landmarks × 3 = 216차원)가 2D(144차원)로 처리됨

**원인 분석**:
- PCA 분석에서 `landmark[:2]`로 X, Y 좌표만 사용
- 216차원 데이터가 144차원으로 축소되어 처리됨
- Data Exploration에서 shape dimension mismatch 발생

**해결**:
```python
# MdStatistics.py - do_pca_analysis()
# 수정 전
for landmark in landmarks:
    flat_coords.extend(landmark[:2])  # X, Y만 사용

# 수정 후
for landmark in landmarks:
    flat_coords.extend(landmark)  # 모든 차원(X, Y, Z) 사용
```

### 7. Rotation Matrix 문제
**문제**: PCA eigenvectors를 rotation matrix로 잘못 사용
- eigenvectors는 (n_components × n_features) 형태
- 전체 공간에서의 회전을 위해서는 정방행렬 필요

**해결**: 전체 rotation matrix 생성
```python
# MdStatistics.py
rotation_matrix = pca.components_.T  # (n_features × n_components)
full_rotation_matrix = np.eye(n_features)
full_rotation_matrix[:, :rotation_matrix.shape[1]] = rotation_matrix
# 결과: (216 × 216) 정방행렬
```

### 8. 분석 객체 속성 누락
**문제**: 새로 생성된 분석 객체에 dataset의 속성들이 복사되지 않음
- propertyname_str (변수명 목록)
- dimension (2D/3D)
- wireframe, baseline, polygons

**해결**: ModanController.py에서 분석 생성 시 dataset 속성 복사
```python
analysis = MdModel.MdAnalysis.create(
    dataset=self.current_dataset,
    analysis_name=analysis_name,
    propertyname_str=self.current_dataset.propertyname_str,
    dimension=self.current_dataset.dimension,
    wireframe=self.current_dataset.wireframe,
    baseline=self.current_dataset.baseline,
    polygons=self.current_dataset.polygons
)
```

## 추가 개선사항

### 1. 로깅 시스템 개선
- JSON 데이터 출력을 INFO에서 DEBUG 레벨로 변경
- 분석 과정의 차원 변화를 추적하는 로그 추가

### 2. 에러 처리 강화
- Data Exploration에서 shape dimension mismatch 시 안전장치 추가
- propertyname_str이 None일 때 fallback 메커니즘 구현

### 3. 코드 구조 개선
- 분석 메서드들을 개별 헬퍼 함수로 분리 (_run_pca, _run_cva, _run_manova)
- 일관된 결과 형식 유지

## 테스트 결과
- ✅ PCA 분석: 3D 데이터 올바르게 처리 (216차원)
- ✅ CVA 분석: 결과 정상 표시
- ✅ MANOVA: 4개 다변량 검정 통계량 모두 표시
- ✅ Data Exploration: 3D viewer 정상 작동
- ✅ 그룹별 색상 구분 정상 작동

## 남은 이슈
1. Data Exploration의 unrotate_shape 기능
   - PCA/CVA 공간에서 원본 3D 공간으로의 변환 필요
   - 현재는 average shape만 표시

2. PCA components 저장
   - 차원 축소된 공간에서 원본 공간으로의 역변환을 위해 필요
   - 추후 구현 예정

## 파일 변경 목록
1. **Modan2.py**: set_splash 메서드 추가
2. **ModanController.py**:
   - 통합 분석 실행 로직 구현
   - JSON 데이터 생성 및 저장
   - 분석 객체 속성 복사
3. **ModanComponents.py**:
   - MANOVA 테이블 형식 개선
   - stat_dict 형식 처리 추가
4. **MdStatistics.py**:
   - 3D 데이터 처리 수정
   - 4개 MANOVA 통계량 계산
   - rotation matrix 생성 로직 개선
5. **ModanDialogs.py**:
   - Data Exploration shape dimension 처리
   - propertyname_str None 처리

## 결론
Modan2의 분석 시스템이 이제 2D/3D 데이터를 올바르게 처리하고, PCA+CVA+MANOVA 통합 분석을 수행하며, 결과를 적절한 형식으로 표시할 수 있게 되었습니다. 특히 3D 형태 분석에서 발생했던 차원 불일치 문제가 해결되어 전체적인 안정성이 크게 향상되었습니다.
