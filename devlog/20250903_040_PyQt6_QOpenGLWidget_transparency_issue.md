# PyQt6 QOpenGLWidget 투명 배경 문제 분석

## 문제 현상
PyQt6 마이그레이션 후 Data Exploration Dialog의 shape grid에서 9개의 3D viewer widget이 투명하게 표시되어야 하는데, 검은색 배경으로 표시되어 뒤의 차트가 가려지는 문제가 발생함.

## 관련 소스코드 위치

### 1. Shape Grid 생성 위치
**파일**: `/mnt/d/projects/Modan2/ModanDialogs.py`
**위치**: 라인 3337-3343
```python
if self.analysis.dataset.dimension == 3:
    self.shape_grid[scatter_key_name]['view'] = ObjectViewer3D(parent=None,transparent=True)
else:
    self.shape_grid[scatter_key_name]['view'] = ObjectViewer2D(parent=None,transparent=True)
```
- `parent=None`으로 독립 윈도우로 생성
- `transparent=True` 파라미터로 투명 모드 활성화

### 2. ObjectViewer3D 투명 모드 초기화
**파일**: `/mnt/d/projects/Modan2/ModanComponents.py`
**위치**: 라인 1128-1164
```python
if transparent:
    # Surface format 설정
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(0)
    self.setFormat(fmt)
    
    # Window flags 설정 (parent가 없을 때만)
    if parent is None:
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
    
    # 투명 속성 설정
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
```

### 3. OpenGL 렌더링 시 투명 처리
**파일**: `/mnt/d/projects/Modan2/ModanComponents.py`
**위치**: 라인 1968-1988 (paintGL 메서드)
```python
if self.transparent:
    gl.glClearColor(0.0, 0.0, 0.0, 0.0)  # 알파값 0으로 클리어
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
```

### 4. Shape Grid 위치 설정
**파일**: `/mnt/d/projects/Modan2/ModanDialogs.py`
**위치**: 라인 3645
```python
view.setGeometry(x_pos, y_pos, width, height)  # 차트 위에 오버레이로 배치
```

## 문제 원인 분석

### 1. QOpenGLWidget의 구조적 제한
- **QOpenGLWidget은 내부적으로 FBO(Framebuffer Object)를 사용**: 일반 위젯과 다른 렌더링 파이프라인
- **컴포지션 방식의 차이**: QOpenGLWidget은 off-screen 렌더링 후 결과를 메인 윈도우에 합성
- **PyQt6에서의 변경사항**: PyQt5에서 PyQt6로 전환하면서 OpenGL 위젯의 컴포지션 처리가 변경됨

### 2. 투명도가 작동하지 않는 구체적 원인

#### a) Framebuffer 알파 채널 처리 문제
- QOpenGLWidget의 기본 framebuffer가 알파 채널을 제대로 지원하지 않을 가능성
- `defaultFramebufferObject()`가 반환하는 FBO의 포맷이 투명도를 지원하지 않을 수 있음

#### b) 윈도우 매니저와의 상호작용
- `parent=None`으로 생성된 top-level 윈도우의 경우 OS 윈도우 매니저의 컴포지션 지원 필요
- Linux/Windows/macOS 각각의 윈도우 시스템이 OpenGL 위젯 투명도를 다르게 처리

#### c) Qt의 렌더링 파이프라인
- Qt가 OpenGL 컨텐츠를 raster 엔진과 합성하는 과정에서 알파 정보 손실
- QOpenGLWidget의 `paintGL()` 결과가 최종 화면에 그려질 때 알파값이 무시됨

### 3. PyQt5 vs PyQt6 차이점
- **PyQt5**: QGLWidget (deprecated) 또는 QOpenGLWidget 사용
- **PyQt6**: QOpenGLWidget만 지원, 내부 구현이 변경됨
- PyQt6에서 QOpenGLWidget의 투명도 처리가 더 제한적일 가능성

## 시도한 해결 방법들

1. **Surface Format 설정**
   - Alpha buffer size 설정
   - Multisampling 비활성화
   - Swap behavior 설정

2. **Widget 속성 설정**
   - `WA_TranslucentBackground`
   - `WA_NoSystemBackground`
   - `WA_OpaquePaintEvent = False`
   - `setAutoFillBackground(False)`

3. **OpenGL 상태 설정**
   - Blending 활성화
   - Clear color를 (0,0,0,0)으로 설정
   - Color mask 설정

4. **Window flags 조정**
   - `FramelessWindowHint`
   - Parent 설정 변경 시도

## 추정되는 근본 원인

**PyQt6의 QOpenGLWidget이 독립 윈도우(parent=None)로 생성될 때 투명 배경을 제대로 지원하지 않는 것으로 판단됨.**

주요 이유:
1. QOpenGLWidget의 내부 FBO가 메인 윈도우 시스템과 합성될 때 알파 채널이 무시됨
2. Qt6의 새로운 렌더링 백엔드(RHI - Rendering Hardware Interface)가 OpenGL 위젯의 투명도를 다르게 처리
3. Platform-specific 컴포지터 지원 부족

## 가능한 해결 방안

### 1. 대체 구현 방법
- QOpenGLWindow 사용 (더 low-level 제어 가능)
- QPainter 기반 2D 렌더링으로 전환
- WebGL 기반 렌더링 (QWebEngineView)

### 2. Workaround
- Shape grid를 투명 대신 반투명 배경색 사용
- Shape grid를 차트 옆에 배치 (오버레이 대신)
- 클릭 시에만 shape viewer 표시

### 3. 플랫폼별 해결책
- Windows: ANGLE 백엔드 사용 시도
- Linux: 컴포지터 설정 확인 (Wayland vs X11)
- macOS: Metal 백엔드 관련 설정 확인

## 결론

현재 PyQt6의 QOpenGLWidget은 독립 윈도우로 생성 시 완전한 투명 배경을 지원하지 않는 것으로 보임. 이는 Qt6의 구조적 제한사항일 가능성이 높으며, Qt 업데이트를 기다리거나 대체 구현 방법을 고려해야 함.

## 참고 사항

- 이 문제는 PyQt6 특정 문제로, PyQt5에서는 정상 작동했을 가능성
- Qt 6.5+ 버전에서 개선되었을 수 있으므로 Qt/PyQt6 버전 업데이트 검토 필요
- 플랫폼별로 다른 동작을 보일 수 있으므로 타겟 플랫폼에서의 테스트 필요

---
*작성일: 2025-01-03*
*작성자: Claude*