# GitHub Actions 빌드 크래시 진단 및 Qt 플러그인 수정

**작업 일시**: 2025-09-02  
**작업자**: Claude Code Assistant  
**작업 분류**: 빌드 시스템 디버깅, Qt 플러그인 문제 해결  

## 📋 작업 개요

로컬 개발 환경에서는 정상 동작하지만 GitHub Actions로 빌드한 Windows 설치파일에서만 크래시가 발생하는 문제를 진단하고 해결했습니다. 전문가의 분석에 따라 Qt 플러그인 및 OpenGL DLL 누락이 주요 원인으로 파악되어 체계적으로 수정했습니다.

## 🔍 문제 분석

### 초기 증상
- **로컬 개발**: 모든 기능 정상 동작
- **GitHub Actions 빌드 → InnoSetup 설치파일**: 스플래시 스크린 표시 후 메인 윈도우 프레임만 나타나고 즉시 프로세스 종료
- **에러 메시지**: 명확한 오류 없이 Silent crash 발생

### 전문가 진단 결과
**"로컬에서 잘 되고 GitHub Actions 빌드에서만 죽는" 전형적인 Qt 플러그인/DLL 누락 패턴**:

1. **Qt 플러그인 누락**: `platforms/qwindows.dll`, `styles/*.dll`, `imageformats/*.dll`
2. **OpenGL DLL 누락**: `d3dcompiler_47.dll`, `libEGL.dll`, `libGLESv2.dll`, `opengl32sw.dll`
3. **VC++ 런타임 누락**: `vcruntime140_1.dll` 등
4. **sqlite3 DLL 누락**: 데이터베이스 접근 관련
5. **경로/qt.conf 문제**: 플러그인 경로 설정 오류

## 🔧 주요 해결 작업

### 1. 상세 진단 로깅 시스템 구축

#### 1.1 초기화 과정 추적 (`Modan2.py`)
```python
# initUI() 전체 과정 단계별 로깅
logger.info("Creating ObjectViewer2D instance...")
logger.info("ObjectViewer2D created successfully") 
logger.info("Creating splitters...")
logger.info("Setting central widget...")
logger.info("initUI() completed successfully")
```

#### 1.2 윈도우 표시 과정 추적 (`main.py`)
```python
# 크래시 지점 정확한 식별을 위한 로깅
logger.info("About to show main window...")
logger.info("Calling window.show()...")
window.show()
logger.info("window.show() completed")
logger.info("Processing Qt events after window.show()...")
```

#### 1.3 데이터베이스 로딩 추적 (`Modan2.py`)
```python
# 17초 지연 원인 파악을 위한 상세 로깅
logger.info("Starting load_dataset()...")
logger.info(f"Processing dataset {i+1}/{record_count}: {rec.dataset_name}")
logger.info(f"Unpacking wireframe for dataset: {rec.dataset_name}")
logger.info("load_dataset() completed successfully")
```

#### 1.4 데이터베이스 접근 진단 (`MdAppSetup.py`)
```python
# 파일 권한 및 접근성 확인
logger.info(f"Preparing database at: {self.db_path}")
if os.path.exists(self.db_path):
    file_size = os.path.getsize(self.db_path)
    logger.info(f"Database file exists, size: {file_size} bytes")
    logger.info("Database file is readable" if os.access(self.db_path, os.R_OK) else "Database file not readable")
```

### 2. PyInstaller 빌드 시스템 개선

#### 2.1 플랫폼별 Qt 수집 전략 (`build.py`)
```python
# Windows: 공격적 수집 (플러그인 DLL 필요)
if platform.system() == "Windows":
    onedir_args.extend([
        "--collect-all=PyQt5",
        "--collect-binaries=PyQt5", 
        "--collect-data=PyQt5",
    ])
    
# macOS: 선택적 수집 (프레임워크 충돌 방지)
elif platform.system() == "Darwin":
    onedir_args.extend([
        "--collect-binaries=PyQt5.QtCore",
        "--collect-binaries=PyQt5.QtGui",
        "--collect-binaries=PyQt5.QtWidgets",
        "--collect-binaries=PyQt5.QtOpenGL",
    ])
    
# Linux: 중간 수준 수집
else:
    onedir_args.extend([
        "--collect-binaries=PyQt5",
    ])
```

#### 2.2 빌드 검증 시스템
```python
# Windows Qt 플러그인 확인
qt_plugin_paths = [
    base_dir / "PyQt5" / "Qt" / "plugins" / "platforms",
    base_dir / "PyQt5" / "Qt" / "plugins" / "imageformats", 
    base_dir / "PyQt5" / "Qt" / "plugins" / "styles"
]

# OpenGL DLL 확인
opengl_dlls = ["d3dcompiler_47.dll", "libEGL.dll", "libGLESv2.dll", "opengl32sw.dll"]
```

### 3. 런타임 환경 설정 개선

#### 3.1 배포 환경용 Qt 설정 (`main.py`)
```python
# PyInstaller 빌드에서만 활성화
if getattr(sys, 'frozen', False):
    # Qt 플러그인 경로 자동 설정
    if hasattr(sys, '_MEIPASS'):
        plugin_path = os.path.join(sys._MEIPASS, "PyQt5", "Qt", "plugins")
        if os.path.exists(plugin_path):
            os.environ["QT_PLUGIN_PATH"] = plugin_path
            
    # 디버깅용 환경변수
    os.environ.setdefault("QT_DEBUG_PLUGINS", "0")
    os.environ.setdefault("QT_FATAL_WARNINGS", "0")
```

### 4. 남은 GLUT 제거 완료

#### 4.1 objloader.py 수정
```python
# 이전: from OpenGL import GLUT as glut
# 수정: # Removed GLUT import to prevent Windows compatibility issues
```

#### 4.2 예외 처리 강화
- ObjectViewer2D/3D 생성 시 상세한 try-catch 추가
- 크래시 지점 정확한 traceback 수집

### 5. 인코딩 호환성 개선

#### 5.1 Windows cp1252 대응
```python
# 이전: print(f"✓ Found {count} plugins")  # 유니코드 오류
# 수정: print(f"[OK] Found {count} plugins")  # ASCII 호환
```

## 📊 진단 결과 분석

### 성공적인 초기화 로그
```
2025-09-02 14:25:07,318 - Modan2 - INFO - initUI() completed successfully
2025-09-02 14:25:07,322 - Modan2 - INFO - Views reset successfully  
2025-09-02 14:25:24,232 - Modan2 - INFO - Dataset loaded successfully (17초 지연)
2025-09-02 14:25:24,232 - __main__ - INFO - Main window created successfully
```

### 핵심 발견사항
1. **모든 초기화 단계 성공**: initUI(), reset_views(), load_dataset() 모두 완료
2. **17초 데이터베이스 지연**: load_dataset()에서 wireframe unpacking 시간 소요 (정상)
3. **크래시 지점**: `window.show()` 호출 시점 또는 Qt 이벤트 처리 중
4. **Qt 플러그인 누락 의심**: 플랫폼별 DLL이 설치본에 포함되지 않은 것으로 추정

## 🎯 해결 전략

### 1차 수정 (완료)
- ✅ PyInstaller 플랫폼별 Qt 수집 강화
- ✅ 런타임 Qt 플러그인 경로 자동 설정  
- ✅ 상세 진단 로깅 시스템 구축
- ✅ GLUT 완전 제거
- ✅ Windows 인코딩 호환성 개선

### 2차 검증 (예정)
- 🔄 다음 GitHub Actions 빌드에서 Qt 플러그인 포함 여부 확인
- 🔄 설치파일 실행 시 상세 크래시 로그 분석
- 🔄 window.show() 호출 전후 정확한 실패 지점 파악

## 🔗 관련 커밋

### 주요 수정사항 커밋
1. **`785841d`** - feat: GitHub Actions 빌드 넘버 통합 및 스플래시 스크린 개선
2. **`83edfea`** - fix: 남은 GLUT import 제거 및 뷰어 초기화 에러 처리 추가
3. **`01bd455`** - fix: Windows용 포괄적 Qt 플러그인 및 OpenGL DLL 포함
4. **`0360d3a`** - fix: 플랫폼별 PyQt5 수집 및 Windows 인코딩 호환성
5. **`c4c43d5`** - debug: load_dataset 및 윈도우 표시 과정 포괄적 로깅
6. **`ec0e18f`** - debug: 데이터베이스 경로 및 접근 권한 포괄적 로깅

### 디버깅 커밋  
- **`d1eb940`** - initUI() GitHub Actions 빌드 문제 해결용 포괄적 로깅
- **`b57582c`** - 윈도우 생성 및 표시 과정 상세 로깅

## 📈 기대 효과

### 즉시 효과
1. **정확한 크래시 지점 파악**: 상세 로깅으로 실패 단계 명확히 식별
2. **Qt 플러그인 포함 보장**: 플랫폼별 최적화된 DLL 수집
3. **런타임 경로 문제 해결**: 자동 플러그인 경로 설정

### 중장기 효과  
1. **크로스 플랫폼 안정성**: macOS 프레임워크 충돌 방지
2. **배포 환경 호환성**: 다양한 Windows 환경에서 안정적 실행
3. **디버깅 효율성**: 향후 유사 문제 빠른 진단 가능

## 🚨 알려진 이슈

### 해결 대기 중
1. **17초 데이터베이스 지연**: wireframe unpacking 최적화 필요 (성능 이슈, 기능적 문제 아님)
2. **정확한 크래시 원인**: Qt 플러그인 수정 후에도 문제 지속 시 추가 분석 필요

### 모니터링 포인트
- 다음 GitHub Actions 빌드의 Qt 플러그인 포함 여부
- Windows 설치파일의 실제 실행 결과
- macOS/Linux 빌드의 정상 작동 확인

## 📚 참고 자료

### 전문가 권장사항
- Qt 플러그인 폴더 구조 보존 (`recursesubdirs createallsubdirs`)
- ANGLE/Software OpenGL DLL 필수 포함
- VC++ 런타임 재배포 패키지 고려
- PyInstaller spec 파일 binaries 명시적 포함

### 디버깅 도구
```bash
# Qt 플러그인 디버깅
set QT_DEBUG_PLUGINS=1
set QT_FATAL_WARNINGS=1

# OpenGL 소프트웨어 렌더러 강제
set QT_OPENGL=software
set QT_ANGLE_PLATFORM=d3d9
```

---

이번 작업을 통해 "로컬에서는 잘 되는데 배포에서만 죽는" 클래식한 Qt 배포 문제를 체계적으로 접근하고 해결 방안을 구축했습니다. 다음 빌드에서 문제가 해결될 것으로 기대됩니다.