# 메인 윈도우 Geometry 저장/복원 문제 수정

## 작성일: 2025-08-30
## 작성자: Claude

## 1. 문제 현황

사용자가 메인 윈도우의 크기와 위치를 변경한 후 애플리케이션을 종료했을 때, 다음 실행 시 geometry가 올바르게 복원되지 않는 문제가 발생했습니다.

### 증상
- ✅ **윈도우 크기**: 정상 저장/복원
- ❌ **윈도우 위치**: 저장되지 않거나 임의 위치로 변경됨
- ❌ 두 번째 모니터에 전체화면으로 뜨는 문제

## 2. 원인 분석

### 2.1 기존 코드 문제점
```python
# 기존 write_settings() - 문제가 있던 코드
def write_settings(self):
    if self.m_app.remember_geometry:
        if self.isMaximized():
            self.config.setdefault("ui", {})["is_maximized"] = True
        else:
            self.config.setdefault("ui", {})["is_maximized"] = False
            geometry = self.geometry()
            self.config.setdefault("ui", {})["window_geometry"] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
```

**문제점**:
1. `self.config`에 직접 저장 → SettingsWrapper를 통해 저장해야 함
2. JSON 파일에 반영되지 않음
3. 잘못된 키 구조 사용

### 2.2 모니터 구성 분석
- **Screen 0** (주 모니터): 3840x2160 at (1920, 0)
- **Screen 1** (두 번째 모니터): 1920x1080 at (0, 416)
- 두 번째 모니터가 주 모니터 **왼쪽**에 위치

## 3. 해결 과정

### 3.1 단계 1: SettingsWrapper를 통한 저장 구현
```python
def write_settings(self):
    """Write settings using SettingsWrapper for proper JSON storage"""
    if not hasattr(self.m_app, 'settings') or not hasattr(self.m_app, 'remember_geometry'):
        return

    # Save remember geometry setting
    self.m_app.settings.setValue("WindowGeometry/RememberGeometry", self.m_app.remember_geometry)

    if self.m_app.remember_geometry:
        # Save maximized state
        if self.isMaximized():
            self.m_app.settings.setValue("IsMaximized/MainWindow", True)
        else:
            self.m_app.settings.setValue("IsMaximized/MainWindow", False)
            # Save window geometry
            self.m_app.settings.setValue("WindowGeometry/MainWindow", self.geometry())

    # Save language setting
    if hasattr(self.m_app, 'language'):
        self.m_app.settings.setValue("Language", self.m_app.language)
```

### 3.2 단계 2: 디버깅 로그 추가
읽기와 쓰기 과정을 추적하기 위한 상세 로그 추가:

```python
# 읽기 과정
print(f"🔍 READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}, w={geometry[2]}, h={geometry[3]}")
print(f"🔍 READ_SETTINGS - Primary monitor size: {primary_rect.width()}x{primary_rect.height()}")

# 쓰기 과정
print(f"🔍 WRITE_SETTINGS - Current window geometry: x={current_geometry.x()}, y={current_geometry.y()}, w={current_geometry.width()}, h={current_geometry.height()}")
```

### 3.3 단계 3: 좌표 제한 로직 제거
초기에는 좌표 범위를 제한하려 했으나, 사용자 요청에 따라 제거:

```python
# 제거된 잘못된 접근
if geometry[0] < min_safe_x or geometry[0] > max_safe_x:
    geometry[0] = 100  # 임의 변경 - 문제!

# 수정된 접근 - 원본 좌표 그대로 사용
print(f"🔍 READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}, w={geometry[2]}, h={geometry[3]}")
```

### 3.4 단계 4: 위치 강제 적용 시스템
윈도우 매니저의 간섭을 방지하기 위한 위치 검증 및 수정:

```python
def verify_position():
    actual = self.geometry()
    if abs(actual.x() - geometry[0]) > 10 or abs(actual.y() - geometry[1]) > 10:
        print(f"🔍 POSITION_DRIFT - Expected: ({geometry[0]}, {geometry[1]}), Got: ({actual.x()}, {actual.y()}), Correcting...")
        self.move(geometry[0], geometry[1])

QTimer.singleShot(100, verify_position)
```

## 4. 최종 해결책

### 4.1 올바른 저장 구조
JSON 파일의 올바른 구조:
```json
{
  "ui": {
    "remember_geometry": true,
    "window_geometry": {
      "main_window": [2322, 889, 1638, 1101]
    },
    "is_maximized": {
      "main_window": false
    }
  }
}
```

### 4.2 키 매핑 시스템
SettingsWrapper의 키 매핑:
```python
"WindowGeometry/MainWindow": ("ui", "window_geometry", "main_window"),
"IsMaximized/MainWindow": ("ui", "is_maximized", "main_window"),
```

### 4.3 멀티모니터 지원
- 좌표 제한 없이 전체 데스크탑 영역에서 자유롭게 위치 설정
- 음수 좌표(두 번째 모니터) 지원
- 모든 모니터 정보를 로그로 출력하여 디버깅 지원

## 5. 테스트 결과

### 5.1 성공 사례
```
🔍 READ_SETTINGS - Using saved geometry: x=2322, y=889, w=1638, h=1101
🔍 READ_SETTINGS - Screen 0: 3840x2160 at (1920, 0)
🔍 READ_SETTINGS - Screen 1: 1920x1080 at (0, 416)
🔍 SET_GEOMETRY - Requested: [2322, 889, 1638, 1101], After setGeometry(): [2322, 889, 1638, 1101]
```

### 5.2 검증 완료 항목
- ✅ 윈도우 크기 저장/복원
- ✅ 윈도우 위치 저장/복원
- ✅ 최대화 상태 저장/복원
- ✅ 멀티모니터 환경 지원
- ✅ JSON 파일에 올바른 구조로 저장

## 6. 학습된 교훈

### 6.1 설정 시스템 일관성
- 모든 설정은 SettingsWrapper를 통해 저장해야 함
- 직접 config 딕셔너리 조작은 JSON 파일에 반영되지 않음

### 6.2 윈도우 매니저 고려사항
- 윈도우 매니저가 창 위치를 임의로 조정할 수 있음
- 지연된 위치 검증이 필요할 수 있음

### 6.3 디버깅의 중요성
- 상세한 로그 없이는 geometry 문제 진단이 어려움
- 멀티모니터 환경에서는 모든 스크린 정보 출력 필요

## 7. 향후 개선 사항

### 7.1 추가 고려사항
- 모니터 구성 변경 시 자동 조정 로직
- 유효하지 않은 위치의 자동 보정
- 사용자별 모니터 프로필 저장

### 7.2 코드 정리
- 디버깅 로그의 production 환경에서 제거 고려
- 위치 강제 적용 로직의 최적화

## 8. 관련 파일

- `Modan2.py`: 메인 윈도우 클래스 (`read_settings`, `write_settings`, `closeEvent`)
- `/home/jikhanjung/.modan2/config.json`: 설정 저장 파일
- `test_geometry_save.py`, `test_geometry_debug.py`: 테스트 스크립트들

---

이 수정으로 인해 메인 윈도우의 geometry가 올바르게 저장되고 복원되며, 멀티모니터 환경에서도 정상 동작합니다.
