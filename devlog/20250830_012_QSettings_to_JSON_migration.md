# QSettings에서 JSON 기반 설정 시스템으로 완전 마이그레이션 계획

## 작성일: 2025-08-30
## 작성자: Claude

## 1. 개요

현재 Modan2는 QSettings와 JSON 기반 설정 시스템이 혼재되어 있는 과도기적 상태입니다.
이를 완전한 JSON 기반 시스템으로 통합하여 일관성을 확보하고 유지보수성을 향상시킵니다.

## 2. 현재 상태 분석

### 2.1 QSettings 사용 현황
- **CalibrationDialog**: `setValue()`, `value()` 직접 사용
- **다른 Dialog들**: 읽기는 `value()`, 쓰기는 시도했으나 실패 (SettingsWrapper가 읽기 전용)
- **ModanComponents**: `value()` 메서드로 설정 읽기

### 2.2 문제점
1. SettingsWrapper가 읽기 전용 (set 메서드 없음)
2. CalibrationDialog의 설정이 실제로 저장되지 않음
3. 설정 저장 방식의 일관성 부재
4. 이중 시스템으로 인한 혼란

## 3. 마이그레이션 전략

### 3.1 단계별 접근
1. **Phase 1**: SettingsWrapper에 쓰기 기능 추가
2. **Phase 2**: 모든 Dialog의 설정 저장/읽기 통합
3. **Phase 3**: ModanComponents 마이그레이션
4. **Phase 4**: 테스트 및 검증

### 3.2 키 매핑 규칙
```
QSettings 키 → JSON 경로
"WindowGeometry/MainWindow" → config["ui"]["window_geometry"]["main_window"]
"IsMaximized/MainWindow" → config["ui"]["is_maximized"]["main_window"]
"Calibration/Unit" → config["calibration"]["unit"]
"DataPointColor/0" → config["ui"]["data_point_colors"][0]
```

## 4. 구현 계획

### 4.1 SettingsWrapper 확장
```python
class SettingsWrapper:
    def __init__(self, config, config_path):
        self.config = config
        self.config_path = config_path

    def value(self, key, default_value):
        # 기존 읽기 기능

    def setValue(self, key, value):
        # 새로운 쓰기 기능

    def sync(self):
        # 설정 파일에 저장
```

### 4.2 설정 키 통합 목록

#### Window Geometry 관련
- WindowGeometry/RememberGeometry → ui.remember_geometry
- WindowGeometry/MainWindow → ui.window_geometry.main_window
- WindowGeometry/ObjectDialog → ui.window_geometry.object_dialog
- WindowGeometry/DatasetDialog → ui.window_geometry.dataset_dialog
- WindowGeometry/DataExplorationWindow → ui.window_geometry.data_exploration_window
- WindowGeometry/DatasetAnalysisWindow → ui.window_geometry.dataset_analysis_window
- WindowGeometry/ExportDialog → ui.window_geometry.export_dialog
- WindowGeometry/ImportDialog → ui.window_geometry.import_dialog

#### Maximized 상태
- IsMaximized/MainWindow → ui.is_maximized.main_window
- IsMaximized/DataExplorationWindow → ui.is_maximized.data_exploration_window

#### Calibration
- Calibration/Unit → calibration.unit

#### UI 설정
- ToolbarIconSize → ui.toolbar_icon_size
- PlotSize → ui.plot_size
- BackgroundColor → ui.background_color

#### Landmark/Wireframe 설정 (2D/3D)
- LandmarkSize/2D → ui.landmark_size_2d
- LandmarkColor/2D → ui.landmark_color_2d
- WireframeThickness/2D → ui.wireframe_thickness_2d
- WireframeColor/2D → ui.wireframe_color_2d
- IndexSize/2D → ui.index_size_2d
- IndexColor/2D → ui.index_color_2d
- (3D 버전도 동일한 패턴)

#### Data Point 설정
- DataPointColor/[0-9] → ui.data_point_colors[]
- DataPointMarker/[0-9] → ui.data_point_markers[]

#### 기타
- Language → language
- LastCalibrationUnit → calibration.last_unit

### 4.3 마이그레이션 코드 예시

```python
# 기존 코드
self.m_app.settings.setValue("Calibration/Unit", self.last_calibration_unit)

# 새 코드
self.m_app.settings.setValue("Calibration/Unit", self.last_calibration_unit)
# SettingsWrapper가 자동으로 config["calibration"]["unit"]에 저장
```

## 5. 영향 범위

### 5.1 수정 필요 파일
1. **Modan2.py**: SettingsWrapper 클래스 확장
2. **ModanDialogs.py**: 모든 Dialog의 read_settings/write_settings 메서드
3. **ModanComponents.py**: 설정 읽기 부분
4. **MdAppSetup.py**: 설정 저장 로직 추가

### 5.2 테스트 필요 항목
- [ ] 윈도우 위치/크기 저장 및 복원
- [ ] Calibration 단위 저장
- [ ] 색상 및 크기 설정 저장
- [ ] 언어 설정 저장
- [ ] 설정 파일 마이그레이션 (기존 사용자)

## 6. 롤백 계획

만약 문제 발생 시:
1. SettingsWrapper의 setValue를 no-op으로 만들기
2. 기존 QSettings 코드 복원
3. 설정 파일 백업본 복원

## 7. 예상 결과

### 7.1 장점
- 일관된 설정 관리 시스템
- 설정 파일 직접 편집 가능
- 버전 관리 용이
- 디버깅 간편
- 향후 웹 버전 확장 용이

### 7.2 주의사항
- 기존 사용자의 설정 마이그레이션 필요
- 초기 버전에서는 두 시스템 병행 운영 고려

## 8. 구현 순서

1. SettingsWrapper에 setValue, sync 메서드 추가
2. CalibrationDialog 마이그레이션 (가장 간단)
3. 각 Dialog의 write_settings 메서드 정리
4. ModanComponents 설정 읽기 확인
5. 전체 테스트
6. 설정 마이그레이션 도구 작성 (선택사항)

## 9. 완료 기준

- [ ] 모든 QSettings.setValue() 호출이 제거됨
- [ ] 모든 설정이 config.json에 저장됨
- [ ] 설정 변경 후 재시작 시 올바르게 복원됨
- [ ] 기존 기능 모두 정상 동작

## 10. 참고사항

이 마이그레이션은 코드베이스의 현대화와 유지보수성 향상을 위한 중요한 단계입니다.
완료 후에는 설정 관리가 훨씬 단순하고 직관적이 될 것입니다.
