# QOpenGLWidget 투명 배경 문제 해결 방안

- **Date:** 2025-09-03
- **Author:** Gemini
- **Status:** Proposed Solution

## 1. 문제 요약

- **참조 문서:** `devlog/20250903_039_PyQt6_QOpenGLWidget_transparency_issue.md`

PyQt6으로 마이그레이션 후, `parent=None`으로 생성된 `ObjectViewer3D`(`QOpenGLWidget`) 위젯의 투명 배경이 동작하지 않는 문제가 발생했습니다. 이는 Qt6에서 최상위 레벨(top-level) OpenGL 위젯의 투명도 처리에 구조적 제한이 있기 때문입니다.

## 2. 해결책 제안: "유리창(Glass Pane)" 오버레이

가장 안정적인 해결책은 OS의 윈도우 합성 기능에 의존하는 최상위 레벨 윈도우 생성을 피하는 것입니다. 대신, 모든 위젯을 단일 윈도우 내에서 처리하도록 구조를 변경합니다.

### 접근 방식

1.  차트 위젯 위에 전체를 덮는 **단일 투명 컨테이너 위젯(`QWidget`)**을 생성합니다.
2.  9개의 `ObjectViewer3D` 위젯들을 이 투명 컨테이너의 **자식 위젯**으로 생성합니다. (`parent=None` 대신)
3.  이를 통해 복잡한 OS별 윈도우 합성 문제 대신, 안정적인 Qt 내부의 위젯 합성 메커니즘을 활용합니다.

## 3. 구체적인 구현 단계

### 단계 1: `ModanDialogs.py` - 투명 컨테이너 생성

`DataExplorationDialog`의 `__init__` 메서드에서, 차트 위젯 위에 `shape_grid_container`라는 이름의 투명 `QWidget`를 추가합니다.

```python
# In DataExplorationDialog.__init__
# self.scatter_plot_widget (차트 위젯)이 생성된 후

# 1. 투명 컨테이너 위젯 생성 (차트 위젯을 부모로)
self.shape_grid_container = QWidget(self.scatter_plot_widget)

# 2. 컨테이너의 배경을 투명하게 설정
self.shape_grid_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

# 3. 컨테이너의 크기와 위치를 부모(차트)와 동일하게 설정
self.shape_grid_container.setGeometry(self.scatter_plot_widget.rect())

# 4. 컨테이너를 보이게 처리
self.shape_grid_container.show()
```
*Note: 다이얼로그의 크기가 조절될 때 컨테이너의 크기도 함께 조절되도록 `resizeEvent`에서 `setGeometry`를 다시 호출해주는 로직을 추가하면 더 좋습니다.*

### 단계 2: `ModanDialogs.py` - `ObjectViewer3D` 부모 변경

`ObjectViewer3D` 인스턴스를 생성하는 부분을 찾아 `parent` 인자를 수정합니다.

```python
# 라인 3338 근처
if self.analysis.dataset.dimension == 3:
    # 기존: parent=None
    # self.shape_grid[scatter_key_name]['view'] = ObjectViewer3D(parent=None, transparent=True)
    
    # 변경: parent=self.shape_grid_container
    self.shape_grid[scatter_key_name]['view'] = ObjectViewer3D(parent=self.shape_grid_container, transparent=True)
else:
    # ... (ObjectViewer2D도 동일하게 수정)
```

### 단계 3: `ModanComponents.py` - 변경 필요 없음

`ObjectViewer3D`의 `__init__` 코드는 수정할 필요가 없습니다. 문제가 되었던 `setWindowFlags` 호출은 `if parent is None:` 블록 안에 있으므로, 부모가 지정된 이제는 자동으로 실행되지 않습니다. 나머지 투명도 관련 설정은 그대로 유효합니다.

## 4. 기대 결과

이 변경으로 `ObjectViewer3D` 위젯들은 OS의 최상위 윈도우가 아닌, `DataExplorationDialog` 내의 자식 위젯으로 올바르게 합성됩니다. 결과적으로 모든 플랫폼에서 일관되게 투명한 배경을 가질 것으로 기대됩니다.
