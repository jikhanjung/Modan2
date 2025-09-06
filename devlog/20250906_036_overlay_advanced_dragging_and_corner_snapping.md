# 오버레이 고급 드래그 및 코너 스냅 기능 구현

**작업일**: 2025-09-06  
**작업자**: Claude  
**관련 파일**: `ModanComponents.py`

## 작업 요약

오버레이 위젯의 드래그 및 리사이즈 기능을 개선하여 사용성을 향상시켰습니다. 특히 리사이즈 우선순위, 스마트 코너 스냅, 그리고 실패 시 복원 기능을 구현했습니다.

## 주요 변경 사항

### 1. 리사이즈 우선순위 개선

#### 1.1 마우스 이벤트 처리 순서 변경
- **기존**: 헤더 영역 클릭 시 드래그 모드로 전환 후 리사이즈 체크
- **변경**: 리사이즈 가능 영역 우선 체크, 그 다음 헤더 드래그 체크
- 리사이즈 영역과 헤더 영역이 겹치는 경우 리사이즈가 우선됨

#### 1.2 커서 표시 우선순위 변경
```python
# 커서 우선순위: 리사이즈 > 헤더 드래그 > 기본 화살표
if direction != self.RESIZE_NONE:
    self.update_cursor(direction)
elif self.is_header_area(event.pos()):
    self.setCursor(Qt.OpenHandCursor)
else:
    self.setCursor(Qt.ArrowCursor)
```

### 2. 헤더 영역 드래그 제한

#### 2.1 드래그 가능 영역 제한
- **드래그 가능**: 상단 30px 헤더 영역 (타이틀바)
- **손 모양 커서**: 헤더 영역에서만 표시
- **드래그 불가**: 리사이즈 영역 및 닫기 버튼 영역

#### 2.2 닫기 버튼 영역 제외 (부분 구현)
- 우상단 20x20px 영역을 닫기 버튼 영역으로 정의
- 해당 영역에서는 드래그 불가능하도록 설정
- **미해결**: 커서 변경이 완전히 작동하지 않음

### 3. 스마트 코너 스냅 시스템

#### 3.1 사분면 기반 스냅 로직
- **기존**: 고정된 50px 스냅 거리로 가장 가까운 코너에 스냅
- **변경**: 부모 패널의 중심을 기준으로 한 사분면 기반 스냅
- 오버레이 중심이 부모 중심선(가로/세로 절반)을 넘으면 해당 사분면 코너로 스냅

#### 3.2 스냅 로직 구현
```python
def snap_to_corner(self):
    parent_center = parent_rect.center()
    current_center = current_rect.center()
    
    # 사분면 판단
    is_right = current_center.x() > parent_center.x()
    is_bottom = current_center.y() > parent_center.y()
    
    # 코너 결정
    if is_right and is_bottom:
        target_corner = 'bottom_right'
    elif is_right and not is_bottom:
        target_corner = 'top_right'
    # ... 나머지 사분면들
```

### 4. 스냅 실패 시 복원 기능

#### 4.1 원래 위치 복원
- 드래그 시작 위치를 `drag_start_geometry`로 저장
- 스냅이 실패하면 원래 위치로 자동 복원
- 현재는 항상 스냅되도록 구현되어 실제로는 복원되지 않음

#### 4.2 복원 로직
```python
def mouseReleaseEvent(self, event):
    if self.dragging:
        original_position = self.drag_start_geometry.topLeft()
        if not self.snap_to_corner():
            self.move(original_position)  # 스냅 실패 시 복원
```

### 5. 다방향 리사이즈 지원

#### 5.1 모든 코너에서 리사이즈 가능
- **기존**: 좌상단 코너에서만 리사이즈
- **변경**: 현재 위치한 코너의 대각선 코너를 잡고 리사이즈

#### 5.2 리사이즈 방향별 처리
```python
def handle_resize(self, global_pos):
    if self.resize_direction == self.RESIZE_TOP_LEFT:
        # 좌상단 코너 리사이즈
    elif self.resize_direction == self.RESIZE_TOP_RIGHT:
        # 우상단 코너 리사이즈
    elif self.resize_direction == self.RESIZE_BOTTOM_LEFT:
        # 좌하단 코너 리사이즈
    elif self.resize_direction == self.RESIZE_BOTTOM_RIGHT:
        # 우하단 코너 리사이즈
```

## 구현 세부사항

### 리사이즈 우선순위 시스템
`mousePressEvent`에서 이벤트 처리 순서를 변경하여 리사이즈가 드래그보다 우선되도록 구현:

```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        # 1순위: 리사이즈 체크
        self.resize_direction = self.get_resize_direction(event.pos())
        if self.resize_direction != self.RESIZE_NONE:
            self.resizing = True
            # 리사이즈 관련 변수 설정
        elif self.is_header_area(event.pos()):
            # 2순위: 헤더 드래그 체크
            self.dragging = True
            # 드래그 관련 변수 설정
```

### 사분면 기반 코너 스냅
부모 위젯의 중심점을 기준으로 현재 오버레이의 중심점 위치를 판단하여 목표 코너를 결정:

```python
# 중심점 비교로 사분면 판단
is_right = current_center.x() > parent_center.x()
is_bottom = current_center.y() > parent_center.y()

# 사분면에 따른 코너 매핑
quadrant_corner_map = {
    (True, True): 'bottom_right',    # 우하단
    (True, False): 'top_right',      # 우상단
    (False, True): 'bottom_left',    # 좌하단
    (False, False): 'top_left'       # 좌상단
}
```

## 사용자 경험 개선

### 직관적인 상호작용
1. **리사이즈 우선**: 모서리 근처에서는 항상 리사이즈가 우선되어 의도하지 않은 드래그 방지
2. **명확한 영역 구분**: 타이틀바에서만 드래그 가능하여 사용자 혼란 최소화
3. **스마트 스냅**: 드래그 방향에 따라 자연스럽게 코너에 붙음

### 시각적 피드백
1. **커서 변경**: 각 영역별로 적절한 커서 표시
   - 리사이즈 영역: 대각선 화살표 (`Qt.SizeFDiagCursor`, `Qt.SizeBDiagCursor`)
   - 드래그 영역: 열린 손 모양 (`Qt.OpenHandCursor`)
   - 일반 영역: 화살표 (`Qt.ArrowCursor`)

## 알려진 문제

### 1. 닫기 버튼 커서 이슈
- **문제**: 닫기 버튼 영역에서 커서가 화살표로 변경되지 않음
- **시도한 해결책**: 
  - `is_close_button_area()` 메서드로 영역 분리
  - `mouseMoveEvent`에서 우선순위 조정
- **현재 상태**: 드래그는 차단되지만 커서 변경은 미작동

### 2. 스냅 복원 기능
- **현재 상태**: 항상 스냅되도록 구현되어 복원 기능이 실제로는 사용되지 않음
- **향후 개선**: 스냅 실패 조건 추가 시 복원 기능 활성화 예상

## 테스트 확인 사항

1. **리사이즈 우선순위**: 모서리에서 리사이즈가 드래그보다 우선되는지 확인 ✅
2. **헤더 드래그**: 타이틀바 영역에서만 드래그 가능한지 확인 ✅
3. **코너 스냅**: 중심선을 넘어가면 해당 코너로 스냅되는지 확인 ✅
4. **다방향 리사이즈**: 모든 코너 위치에서 리사이즈 가능한지 확인 ✅
5. **커서 변경**: 각 영역별로 적절한 커서 표시되는지 확인 (부분적 성공)

## 향후 개선 사항

1. **닫기 버튼 커서 수정**: QPushButton의 커서 설정 override 필요
2. **스냅 임계값 조정**: 필요시 스냅 실패 조건 추가
3. **애니메이션 효과**: 스냅 시 부드러운 이동 효과 추가 고려
4. **키보드 단축키**: Esc 키로 드래그 취소 기능 추가 고려

## 코드 품질

- **모듈화**: 각 기능별 메서드 분리 (드래그, 리사이즈, 스냅, 커서 관리)
- **가독성**: 명확한 메서드명과 주석
- **확장성**: 새로운 스냅 모드나 리사이즈 방향 추가 용이
- **유지보수성**: 설정값들을 클래스 상수로 관리

## 성능 영향

- **마우스 추적**: `setMouseTracking(True)` 사용으로 미세한 성능 오버헤드
- **실시간 계산**: 드래그/리사이즈 시 실시간 기하학적 계산
- **전반적 영향**: 사용자 경험 향상 대비 허용 가능한 수준