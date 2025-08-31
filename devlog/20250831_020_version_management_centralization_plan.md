# [20250831_020] 버전 관리 중앙 집중화 계획

## 1. 문제점

현재 Modan2 프로젝트의 버전 정보는 여러 파일에 하드코딩되어 분산 관리되고 있습니다.

- `MdUtils.py`: `PROGRAM_VERSION = "0.1.4"` (애플리케이션 로직에서 사용)
- `InnoSetup/Modan2.iss`: `#define AppVersion "0.1.4"` (Windows 설치 프로그램)
- `Modan2.py` 주석: `pyinstaller` 명령어에 버전 포함 (`Modan2_v0.1.4_...`)
- `setup.py`: `version="0.0.1"` (오래된 정보)

이러한 구조는 버전 업데이트 시 여러 파일을 수동으로 수정해야 하므로, 실수를 유발하고 유지보수성을 저하시킵니다.

## 2. 목표

**"Single Source of Truth" 원칙**에 따라 버전 정보를 한 곳에서 관리하여, 버전 업데이트 작업을 단일 파일 수정으로 완료할 수 있도록 시스템을 개선합니다.

- **기준 정보**: `MdUtils.py` 파일의 `PROGRAM_VERSION` 변수를 유일한 버전 정보 소스로 지정합니다.
- **자동화**: 다른 파일들은 빌드 또는 실행 시점에 기준 정보를 동적으로 읽어오도록 자동화합니다.

## 3. 상세 실행 계획

### 1단계: 기준 정보 확인

- `MdUtils.py`의 `PROGRAM_VERSION` 변수를 버전 관리의 유일한 기준으로 확정합니다. (현재 구조 유지)

### 2단계: 빌드 스크립트 개선 (`build.py`)

`build.py` 파일을 수정하여, `MdUtils.py`에서 버전을 읽어와 다른 파일에 적용하는 자동화 로직을 추가합니다.

1.  **버전 추출 함수 추가**: `MdUtils.py` 파일을 읽어 정규식을 사용해 `PROGRAM_VERSION` 값을 추출하는 함수를 `build.py`에 구현합니다.

    ```python
    # build.py에 추가될 함수 예시
    import re
    import os

    def get_version():
        with open("MdUtils.py", "r") as f:
            content = f.read()
            match = re.search(r'''PROGRAM_VERSION = "(.*?)"''', content)
            if match:
                return match.group(1)
        raise RuntimeError("Unable to find version string.")
    ```

2.  **InnoSetup 스크립트(.iss) 내용 동적 생성**:
    - 원본 `InnoSetup/Modan2.iss` 파일을 템플릿으로 사용합니다.
    - 빌드 시점에 `get_version()`으로 버전을 가져옵니다.
    - `#define AppVersion "0.1.4"` 라인을 `#define AppVersion "{version}"` 형태로 교체한 임시 `.iss` 파일을 생성합니다.
    - InnoSetup 컴파일러는 이 임시 파일을 사용하도록 합니다.

3.  **PyInstaller 명령어 생성 함수 추가**:
    - `get_version()`으로 버전을 가져옵니다.
    - OS에 맞는 `pyinstaller` 명령어 문자열을 동적으로 생성하는 함수를 `build.py`에 추가합니다. 파일명에 버전이 포함되도록 합니다.
    - 예: `f"pyinstaller --name Modan2_v{version} ..."`
    - 이 함수를 실행하여 PyInstaller 빌드를 수행합니다.

### 3단계: `setup.py` 수정

- `setup.py` 파일이 `cx_Freeze` 빌드에 계속 사용될 경우를 대비하여, 이 파일도 `MdUtils.py`의 버전을 읽어오도록 수정합니다.

    ```python
    # setup.py 수정 예시
    import re

    def get_version():
        # ... (위와 동일한 함수) ...

    setup(
        name="Modan2",
        version=get_version(),
        ...
    )
    ```

## 4. 기대 효과

- `MdUtils.py`의 `PROGRAM_VERSION` 변수만 수정하면, 애플리케이션, Windows 설치 프로그램, 빌드 결과물(exe)의 버전이 모두 일관되게 변경됩니다.
- 버전 업데이트 과정이 단순화되고, 사람의 실수로 인한 버전 불일치 문제가 원천적으로 차단됩니다.
- 프로젝트의 유지보수성이 향상됩니다.
