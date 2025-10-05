# DataExploration 썸네일 동기화 문제 분석 (Linux/WSL)

## 문제 현상

**발생 환경**: WSL (Windows Subsystem for Linux) - WSL2 with WSLg
**정상 작동 환경**: Native Linux
**발생 일자**: 2025-09-05
**보고자**: 사용자
**확인 일자**: 2025-09-05 - Native Linux에서는 정상 작동 확인

### 증상 설명

Data Exploration 윈도우에서 3D 뷰를 회전할 때 썸네일 동기화에 문제가 발생:

1. **마우스 드래그 중 (회전 진행 중)**
   - 메인 3D 뷰는 정상적으로 회전
   - 썸네일들이 완전히 사라짐 (렌더링되지 않음)

2. **마우스 버튼 릴리즈 후**
   - 썸네일이 다시 나타나며 회전이 반영됨
   - 단, 마우스 커서가 matplotlib 그래프 영역 위에 있을 때만 즉시 업데이트
   - 그래프 영역 밖에서 릴리즈하면 마우스가 그래프 위로 이동할 때까지 업데이트 지연

## 기술적 분석

### 관련 코드 구조

```python
# ModanComponents.py - ObjectViewer3D
def mouseMoveEvent(self, event):
    if event.buttons() == Qt.LeftButton and self.view_mode == ROTATE_MODE:
        self.temp_rotate_x = self.curr_x - self.down_x
        self.temp_rotate_y = self.curr_y - self.down_y
        if self.parent != None and callable(getattr(self.parent, 'sync_temp_rotation', None)):
            self.parent.sync_temp_rotation(self, self.temp_rotate_x, self.temp_rotate_y)

# ModanDialogs.py - DataExplorationDialog
def sync_temp_rotation(self, shape_view, temp_rotate_x, temp_rotate_y):
    for sv in self.shape_view_list:
        if sv != shape_view:
            sv.temp_rotate_x = temp_rotate_x
            sv.temp_rotate_y = temp_rotate_y
            sv.update()  # Qt update 호출
```

### 문제의 원인

1. **Qt와 matplotlib 캔버스 간의 렌더링 우선순위 충돌**
   - mouseMoveEvent 처리 중에 OpenGL 위젯(썸네일)의 렌더링이 차단됨
   - matplotlib 캔버스의 이벤트 처리가 OpenGL 렌더링보다 우선순위가 높음

2. **X11 서버와의 동기화 문제 (Linux/WSL 특유)**
   - Windows에서는 정상 작동하는 것으로 보아 플랫폼별 렌더링 파이프라인 차이
   - X11 서버가 OpenGL 컨텍스트와 2D 그래픽스 컨텍스트를 다르게 처리

3. **matplotlib 캔버스의 `draw()` 호출이 트리거 역할**
   ```python
   # on_canvas_move에서 canvas.draw() 호출
   def on_canvas_move(self, evt):
       # ...
       self.fig2.canvas.draw()  # 이 호출이 썸네일을 다시 그리게 함
   ```

## 시도한 해결 방법들

### 1. update() → repaint() 변경 (실패)
```python
sv.repaint()  # 즉시 다시 그리기 강제
```
- 결과: 효과 없음
- 이유: repaint()도 이벤트 루프가 차단된 상태에서는 실행되지 않음

### 2. matplotlib canvas.draw_idle() 추가 (실패)
```python
if hasattr(self, 'fig2') and self.fig2:
    self.fig2.canvas.draw_idle()
```
- 결과: 오히려 성능 저하
- 이유: 매 mouseMoveEvent마다 캔버스 다시 그리기는 과도한 부하

### 3. QApplication.processEvents() 추가 (미시도)
```python
QApplication.processEvents()  # 이벤트 큐 강제 처리
```
- 예상 문제: mouseMoveEvent 중 호출 시 무한 재귀 위험

## 근본적인 문제

### Linux/WSL의 렌더링 아키텍처
1. **X11 서버 레이어**
   - OpenGL 컨텍스트와 2D 렌더링이 별도 버퍼에서 처리
   - 동기화 시점이 Windows와 다름

2. **Qt의 이벤트 처리**
   - mouseMoveEvent가 연속적으로 발생 시 다른 이벤트 처리 차단
   - OpenGL 위젯의 paintGL() 호출이 지연됨

3. **matplotlib와 OpenGL의 상호작용**
   - matplotlib FigureCanvas와 QGLWidget이 같은 윈도우에 있을 때 렌더링 충돌
   - 서로 다른 렌더링 백엔드 사용 (matplotlib: Agg/Cairo, OpenGL: GPU)

## 가능한 해결 방향

### 1. 스레드 분리 (권장)
```python
# 별도 스레드에서 썸네일 업데이트
from PyQt5.QtCore import QTimer
def sync_temp_rotation(self, ...):
    # Timer로 지연 실행
    QTimer.singleShot(0, lambda: self.update_thumbnails())
```

### 2. 렌더링 최적화
- mouseMoveEvent 중에는 썸네일 업데이트 스킵
- mouseReleaseEvent에서만 최종 동기화
- 또는 일정 간격(예: 50ms)으로만 업데이트

### 3. 플랫폼별 분기
```python
if sys.platform.startswith('linux'):
    # Linux 전용 처리
    pass
else:
    # Windows/macOS 처리
    pass
```

### 4. OpenGL 컨텍스트 공유
- 메인 3D 뷰와 썸네일이 같은 OpenGL 컨텍스트 사용
- QOpenGLWidget으로 마이그레이션 고려 (Qt5.4+)

## 결론 (업데이트: 2025-09-05)

**중요 발견**: 이 문제는 WSL 환경에서만 발생하며, 네이티브 Linux에서는 정상 작동합니다.

### WSL vs Native Linux
- **WSL**: 썸네일 동기화 실패 (WSLg의 중간 레이어로 인한 렌더링 지연)
- **Native Linux**: 정상 작동 (직접적인 X11/Wayland 및 GPU 드라이버 접근)

이는 WSLg의 Windows-Linux 그래픽 브릿지 구조로 인한 문제로, WSL의 근본적인 한계입니다.

### 권장사항
1. **개발/테스트**: 그래픽 집약적 기능은 네이티브 Linux 또는 Windows에서 수행
2. **WSL 사용자 가이드**: WSL에서 썸네일 동기화 제한 사항 문서화
3. **장기적 해결**: WSL 전용 최적화 또는 기능 비활성화 옵션 제공 고려

## 참고 자료

- [Qt OpenGL Rendering](https://doc.qt.io/qt-5/qtopengl-index.html)
- [X11 Composite Extension](https://www.x.org/releases/X11R7.5/doc/compositeproto/compositeproto.txt)
- [matplotlib backends](https://matplotlib.org/stable/users/explain/backends.html)
