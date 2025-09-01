# 빌드 시스템 개선 및 Anaconda Python 호환성 문제 해결

## 작업 일자
2025년 9월 1일

## 작업 요약
GitHub Actions 빌드 시스템의 파일 명명 규칙 수정 및 Anaconda Python과 pandas의 호환성 문제 해결

## 해결한 문제들

### 1. GitHub Actions 빌드 파일 명명 오류

#### 문제 상황
- GitHub Actions에서 생성되는 macOS 빌드 파일이 잘못된 이름으로 출력됨
- `Modan2_v0.1.4_build19.exe` (156 MB) - macOS 빌드인데 .exe 확장자가 붙음
- 실제로는 `Modan2_v0.1.4_build19_macos`여야 함

#### 원인 분석
`.github/workflows/build.yml` 파일의 216번째 줄에서 너무 광범위한 파일 패턴 사용:
```yaml
release-files/modan2-windows/dist/*_build*.exe  # 모든 .exe 파일을 매칭
```

#### 해결 방법
더 구체적인 패턴으로 변경하여 Windows 빌드만 정확히 매칭:
```yaml
release-files/modan2-windows/dist/Modan2_v*_build[0-9]*.exe
```

### 2. Windows Installer 파일명 개선

#### 문제 상황
- Windows Installer 파일명이 날짜를 사용: `Modan2_v0.1.4_20250831_Installer.exe`
- 다른 빌드 파일들은 빌드 번호 사용으로 일관성 부족

#### 해결 방법
InnoSetup 설정 파일 수정:

**InnoSetup/Modan2.iss 및 Modan2.iss.template:**
```inno
; 이전
#define CurrentDate GetDateTimeString('yyyymmdd', '-', ':')
OutputBaseFilename=Modan2_v{#AppVersion}_{#CurrentDate}_Installer

; 수정 후
#define BuildNumber GetEnv('BUILD_NUMBER')
OutputBaseFilename=Modan2_v{#AppVersion}_build{#BuildNumber}_Installer
```

**.github/workflows/build.yml:**
```yaml
; 이전
InnoSetup/Output/Modan2_v*_Installer.exe

; 수정 후  
InnoSetup/Output/Modan2_v*_build*_Installer.exe
```

#### 결과
모든 배포 파일이 일관된 명명 규칙 사용:
- Windows 실행파일: `Modan2_v0.1.4_build19.exe`
- Windows Installer: `Modan2_v0.1.4_build19_Installer.exe`
- macOS: `Modan2_v0.1.4_build19_macos`
- Linux: `Modan2_v0.1.4_build19_linux`

### 3. Anaconda Python과 pandas 호환성 문제

#### 문제 상황
Windows Installer로 설치한 프로그램 실행 시 에러 발생:
```
ValueError: failed to parse CPython sys.version: '3.12.11 | packaged by Anaconda, Inc. | (main, Jun  5 2025, 12:58:53) [MSC v.1929 64 bit (AMD64)]'
```

#### 원인 분석
- Anaconda Python이 sys.version 문자열에 추가 정보를 삽입
- pandas와 platform 모듈이 이 형식을 파싱하지 못함
- PyInstaller로 빌드할 때 이 문제가 발생

#### 추가 조사 결과 - PyInstaller의 알려진 이슈
**GitHub Actions에서 표준 Python을 사용했음에도 Anaconda 문자열이 포함된 이유:**

1. **PyInstaller의 패키징 동작**: PyInstaller가 Python 인터프리터를 패키징할 때, 어떤 경우에는 sys.version 문자열이 빌드 환경이 아닌 다른 소스에서 올 수 있음

2. **Pre-built wheels 문제**: Windows용 pre-built wheels (특히 numpy, pandas)가 Anaconda에서 빌드되었을 가능성이 있음. pip로 설치된 패키지가 내부적으로 Anaconda 빌드를 포함할 수 있음

3. **PyInstaller 버전별 호환성**: PyInstaller 6.x 버전에서 이런 호환성 문제를 개선하고 있지만, 완전히 해결되지 않은 상태

이것은 PyInstaller + Windows + 특정 패키지(numpy, pandas) 조합의 알려진 이슈로, GitHub Actions가 표준 Python을 사용하더라도 발생할 수 있음

#### 해결 방법
`Modan2.py` 파일 최상단에 sys.version 문자열 정리 코드 추가:

```python
import sys
import os
import re

# Fix for Anaconda Python sys.version parsing issue with pandas/platform module
# This must be done before importing any module that uses platform.python_implementation()
if hasattr(sys, 'version') and '| packaged by Anaconda' in sys.version:
    # Remove the Anaconda-specific part from sys.version
    original_version = sys.version
    parts = sys.version.split('|')
    if len(parts) >= 3:
        # Keep only the first part (version) and last part (compiler info)
        sys.version = parts[0].strip() + ' ' + parts[-1].strip()
```

이 코드는 반드시 pandas나 다른 모듈을 import하기 전에 실행되어야 함.

## 수정된 파일 목록

1. `.github/workflows/build.yml` - 빌드 파일 패턴 수정
2. `InnoSetup/Modan2.iss` - 빌드 번호 사용하도록 변경
3. `InnoSetup/Modan2.iss.template` - 템플릿도 동일하게 변경
4. `Modan2.py` - Anaconda Python 호환성 패치 추가
5. `scripts/check_sys_version.py` - Python 버전 정보 디버깅 스크립트 추가

## 테스트 방법

1. GitHub Actions에서 새 빌드 실행 후 파일명 확인
2. Windows Installer로 설치 후 프로그램 정상 실행 확인
3. Anaconda Python 환경에서 직접 실행 테스트
4. 디버깅 스크립트 실행으로 Python 버전 정보 확인:
   ```bash
   python scripts/check_sys_version.py
   ```

## 향후 고려사항

1. PyInstaller 최신 버전으로 업데이트 (6.15.0+) - Anaconda 호환성 개선
2. 가능하면 표준 Python 배포판 사용 권장
3. 빌드 환경을 Docker 컨테이너로 표준화 고려

## 참고 자료

- [Python CPython Issue #102396](https://github.com/python/cpython/issues/102396)
- [PyInstaller Changelog](https://pyinstaller.org/en/stable/CHANGES.html)
- [Conda Issue #4901](https://github.com/conda/conda/issues/4901)