# QGLWidget에서 QOpenGLWidget으로 마이그레이션 완료

## 개요
2025년 9월 2일, Modan2 프로젝트의 3D 뷰어 컴포넌트를 레거시 QGLWidget에서 현대적인 QOpenGLWidget으로 성공적으로 마이그레이션했습니다. 이 작업은 Windows 배포 빌드에서 발생하던 OpenGL 크래시 문제를 해결하고, 전반적인 렌더링 안정성을 크게 향상시켰습니다.

## 배경 및 문제점

### 기존 QGLWidget의 문제
1. **레거시 API**: Qt5에서 deprecated 경고, Qt6에서는 완전히 제거됨
2. **Windows 호환성 문제**: GitHub Actions 빌드에서 glBindFramebuffer NullFunctionError 발생
3. **GPU 드라이버 의존성**: 다양한 하드웨어에서 불안정한 동작
4. **GLUT 의존성**: Windows에서 freeglut.dll 배포 문제

### 마이그레이션 필요성
- GitHub Actions CI/CD 파이프라인에서 지속적인 빌드 실패
- Windows 사용자들의 크래시 리포트 증가
- Qt6로의 향후 업그레이드 대비 필요

## 구현 내용

### 1. 핵심 클래스 변경
```python
# Before
from PyQt5.QtOpenGL import QGLWidget
class ObjectViewer3D(QGLWidget):
    def updateGL(self):
        # 레거시 업데이트 메서드
        
# After  
from PyQt5.QtWidgets import QOpenGLWidget
class ObjectViewer3D(QOpenGLWidget):
    def update(self):
        # 현대적인 업데이트 메서드
```

### 2. OpenGL 컨텍스트 설정 강화
- **OpenGL 2.1 Compatibility Profile** 설정 (GLU/immediate mode 지원)
- **버퍼 구성**: 24-bit depth buffer, 8-bit stencil buffer
- **안티앨리어싱**: 4x MSAA 적용
- **더블 버퍼링**: 플리커 방지

### 3. 플랫폼별 최적화
```python
# Windows: ANGLE 우선, Software 폴백
if platform.system() == 'Windows':
    QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL, False)
    os.environ['QT_OPENGL'] = 'angle'
    
# Linux/macOS: Desktop OpenGL 사용
else:
    QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL, True)
```

### 4. 프레임버퍼 처리 개선
- QOpenGLWidget의 내부 FBO 활용
- `defaultFramebufferObject()` 메서드 사용
- 직접적인 `glBindFramebuffer` 호출 제거

### 5. 렌더링 파이프라인 현대화
- `paintGL()` 메서드에서 적절한 viewport 설정
- Clear 작업 최적화
- QPainter 오버레이 통합 (랜드마크 인덱스 표시)

## 주요 변경 사항

### 커밋 히스토리
1. **dd8ca2c**: 초기 마이그레이션 - QGLWidget → QOpenGLWidget
2. **58df9ec**: OpenGL 컨텍스트 관리 개선
3. **9712e62**: 배포 빌드용 Desktop OpenGL 설정
4. **292cae4**: 포괄적인 OpenGL 안정성 개선
5. **cb52a4a**: QPainter 오버레이로 랜드마크 인덱스 표시 추가

### 변경된 파일
- `ModanComponents.py`: ObjectViewer3D 클래스 전면 리팩토링
- `main.py`: QSurfaceFormat 설정 및 플랫폼별 최적화
- `build.py`: PyInstaller 빌드 설정 업데이트
- `requirements.txt`: PyOpenGL numpy 2.x 호환성 해결

## 성과 및 개선 효과

### 안정성 향상
- ✅ GitHub Actions Windows 빌드 성공
- ✅ glBindFramebuffer NullFunctionError 해결
- ✅ 다양한 GPU 드라이버에서 안정적 동작

### 성능 개선
- 프레임 드롭 현상 감소
- 스무스한 3D 회전 및 줌
- 메모리 사용량 최적화

### 호환성 확대
- Windows 7/8/10/11 지원
- Intel 내장 그래픽 지원
- 가상 머신 환경 지원 (Software 렌더링)

## 테스트 및 검증

### 추가된 테스트
- `test_opengl_smoke.py`: OpenGL 기본 기능 테스트
- `test_desktop_compatibility.py`: Desktop OpenGL 호환성 테스트
- `test_compatibility_profile.py`: Compatibility Profile 검증

### 테스트 결과
- 모든 플랫폼에서 CI/CD 파이프라인 통과
- Windows/macOS/Linux 로컬 테스트 성공
- 사용자 피드백 긍정적

## 향후 계획

### 단기 계획
1. OpenGL ES 지원 검토 (모바일 플랫폼 대비)
2. Vulkan 백엔드 실험적 지원
3. 렌더링 성능 프로파일링 도구 추가

### 장기 계획
1. Qt6 마이그레이션 준비
2. WebGL 기반 웹 뷰어 개발
3. GPU 가속 형태학적 분석 구현

## 기술적 세부사항

### API 변경 사항
| QGLWidget | QOpenGLWidget | 설명 |
|-----------|---------------|------|
| updateGL() | update() | 화면 갱신 메서드 |
| initializeGL() | initializeGL() | 변경 없음 |
| paintGL() | paintGL() | 변경 없음 |
| resizeGL() | resizeGL() | 변경 없음 |
| N/A | defaultFramebufferObject() | FBO 접근 메서드 |

### 의존성 변경
- 제거: `PyQt5.QtOpenGL.QGLWidget`
- 추가: `PyQt5.QtWidgets.QOpenGLWidget`
- 업데이트: PyOpenGL (numpy 2.x 호환 버전)

## 결론
QOpenGLWidget으로의 마이그레이션은 Modan2 프로젝트의 3D 렌더링 안정성과 호환성을 크게 향상시켰습니다. 이 변경으로 인해 더 많은 사용자가 다양한 환경에서 안정적으로 소프트웨어를 사용할 수 있게 되었으며, 향후 Qt6 및 현대적인 그래픽 API로의 전환을 위한 기반을 마련했습니다.

## 참고 자료
- [Qt Documentation: QOpenGLWidget](https://doc.qt.io/qt-5/qopenglwidget.html)
- [Qt Blog: Migrate from QGLWidget](https://www.qt.io/blog/2014/09/10/qt-weekly-19-qopenglwidget)
- [PyQt5 OpenGL Examples](https://github.com/pyqt/examples/tree/master/opengl)

---
*작성일: 2025년 9월 3일*
*작성자: Modan2 개발팀*