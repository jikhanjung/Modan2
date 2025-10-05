# 2025-09-05 Compatibility and Feature Improvements

## Overview
오늘은 OpenGL/GLUT 호환성 문제 해결, CI/CD 테스트 안정성 개선, 스플래시 스크린 개선, 그리고 랜드마크 인덱스 표시 기능 복원 작업을 진행했습니다.

## 1. OpenGL/GLUT 호환성 문제 해결

### 문제점
- Windows/Linux 환경에서 `glutSolidSphere()` 호출 시 Access Violation 발생
- matplotlib에서 artist 제거 시 NotImplementedError 발생

### 해결 방법

#### GLUT 초기화 개선 (ModanComponents.py)
```python
# 모듈 레벨에서 한 번만 초기화
if GLUT_AVAILABLE and glut:
    try:
        glut.glutInit(sys.argv)
        GLUT_INITIALIZED = True
    except Exception as e:
        print(f"Warning: Failed to initialize GLUT ({e}), using fallback rendering")
        GLUT_AVAILABLE = False
        GLUT_INITIALIZED = False
```

#### matplotlib artist 안전한 제거 (ModanDialogs.py)
```python
def safe_remove_artist(artist, ax=None):
    """Safely remove matplotlib artist from plot"""
    if artist is None:
        return
    try:
        artist.remove()
    except NotImplementedError:
        # For scatter plots and other collections
        if ax is not None:
            if hasattr(ax, 'collections') and artist in ax.collections:
                ax.collections.remove(artist)
```

### 개선 효과
- GLUT 함수 호출 시 크래시 방지
- matplotlib 그래프 업데이트 시 에러 없이 동작

## 2. CI/CD 테스트 안정성 개선

### 문제점
- GitHub Actions에서 pytest 실행 시 XIO Fatal error 발생
- X11 서버 접근 불가로 인한 테스트 실패

### 해결 방법 (.github/workflows/test.yml)
```yaml
- name: Run tests with virtual display
  run: |
    # Use xvfb-run to handle virtual display automatically
    xvfb-run -a -s "-screen 0 1024x768x24" \
      timeout 1500 pytest tests/
```

### 개선 효과
- CI/CD에서 GUI 테스트 정상 실행
- False positive 테스트 실패 제거

## 3. 스플래시 스크린 개선

### 구현 내용

#### 즉시 표시 (main.py)
```python
# Show splash screen FIRST, before any heavy imports
splash = None
if not args.no_splash:
    from MdSplashScreen import create_splash_screen
    splash = create_splash_screen(background_path)
    splash.setProgress("Starting Modan2...")
    splash.show()
    QApplication.processEvents()  # Force immediate display
```

#### 빌드 정보 표시 (MdSplashScreen.py, MdUtils.py)
- 동적 저작권 연도 표시 (2023-현재)
- 빌드 번호 통합 표시
- build_info.json 생성 및 포함

### 개선 효과
- 애플리케이션 시작 시 즉시 스플래시 스크린 표시
- 빌드 정보 추적 개선

## 4. 동적 랜드마크 카운트 계산

### 문제점
- dataset.landmark_count 속성 의존으로 인한 AttributeError

### 해결 방법 (ModanController.py, MdUtils.py)
```python
# 첫 번째 객체에서 랜드마크 수 동적 계산
first_obj = dataset.object_list.first() if dataset.object_list.count() > 0 else None
landmark_count = first_obj.count_landmarks() if first_obj else 0
```

### 개선 효과
- 데이터베이스 스키마 변경 없이 작동
- 더 유연한 데이터셋 처리

## 5. 3D 랜드마크 인덱스 표시 복원

### 구현 내용 (ModanComponents.py)
```python
if self.show_index:
    gl.glDisable(gl.GL_LIGHTING)
    index_color = mu.as_gl_color(self.index_color)
    gl.glColor3f( *index_color )
    gl.glRasterPos3f(lm[0] + 0.05, lm[1] + 0.05, lm[2])
    font_size_list = [ glut.GLUT_BITMAP_HELVETICA_10,
                      glut.GLUT_BITMAP_HELVETICA_12,
                      glut.GLUT_BITMAP_HELVETICA_18]
    if GLUT_AVAILABLE and GLUT_INITIALIZED and glut:
        try:
            for letter in list(str(i+1)):
                glut.glutBitmapCharacter(font_size_list[int(self.index_size)], ord(letter))
        except (OSError, AttributeError) as e:
            # Fallback if GLUT text rendering fails
            pass
    gl.glEnable(gl.GL_LIGHTING)
```

### 설정
- 기본값: `show_index = False`
- ObjectDialog에서만: `show_index = True`

### 개선 효과
- 3D 뷰에서 랜드마크 번호 시각적 확인 가능
- 안전한 GLUT 사용으로 크래시 방지

## 6. WSL 썸네일 동기화 문제 문서화

### 발견된 문제
- WSL 환경에서만 3D 뷰 회전 시 썸네일이 실시간 업데이트 안 됨
- Native Linux에서는 정상 작동

### 원인 분석
- WSLg의 그래픽 파이프라인 특성
- X11 프로토콜 변환 과정에서의 이벤트 처리 지연

### 결론
- 애플리케이션 레벨에서 해결 불가
- 문서화하여 known issue로 관리

## 커밋 히스토리

1. `65f4b46`: OpenGL/GLUT 및 matplotlib 호환성 문제 해결
2. `28f06ed`, `a111788`: CI/CD XIO 에러 해결
3. `2bb20b9`, `e2da0d1`: xvfb-run으로 테스트 안정화
4. `2140e60`: 스플래시 스크린 즉시 표시
5. `859f58f`: landmark_count 동적 계산
6. `5ed4c1d`, `90b5101`: WSL 썸네일 동기화 문제 문서화
7. `edad423`: 스플래시 스크린 빌드 정보 표시
8. `c543d9d`: 3D 랜드마크 인덱스 표시 복원

## 향후 과제

1. **WSL 썸네일 동기화**: WSLg 업데이트 모니터링
2. **랜드마크 인덱스 표시**: QPainter 오버레이 방식 고려 (GLUT 의존성 제거)
3. **테스트 커버리지**: 핵심 모듈 테스트 확대

## 결론

오늘의 작업으로 애플리케이션의 안정성과 사용성이 크게 개선되었습니다. 특히 GLUT 관련 크래시 문제 해결과 CI/CD 안정화는 향후 개발 효율성을 높일 것으로 기대됩니다.
