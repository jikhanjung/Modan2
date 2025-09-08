
# Modan2 - 기하학적 형태분석 소프트웨어

[![Build](https://github.com/jikhanjung/Modan2/actions/workflows/build.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/build.yml)
[![Tests](https://github.com/jikhanjung/Modan2/actions/workflows/test.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/test.yml)
[![Release Status](https://github.com/jikhanjung/Modan2/actions/workflows/release.yml/badge.svg)](https://github.com/jikhanjung/Modan2/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

*Read this in other languages: [English](README.md), [한국어](README.ko.md)*

Modan2는 연구자들이 기하학적 형태분석을 통해 형태의 변이를 탐색하고 이해할 수 있도록 돕는 사용자 친화적인 데스크톱 애플리케이션입니다. 데이터 수집(2D/3D)부터 통계 분석 및 시각화에 이르는 전체 워크플로우를 간소화합니다.

## 핵심 기능

- **계층적 데이터 관리:** 명확한 구조로 데이터를 중첩된 데이터셋으로 구성합니다.
- **2D 및 3D 시각화:** 랜드마크 플로팅을 포함한 2D 이미지 및 3D 모델용 통합 뷰어를 제공합니다.
- **통계 분석:** 주성분 분석(PCA), 정준 판별 분석(CVA), 다변량 분산 분석(MANOVA)을 수행합니다.
- **데이터 가져오기/내보내기:** 다양한 파일 형식을 지원하며 드래그 앤 드롭으로 쉽게 데이터를 처리할 수 있습니다.
- **영구 저장소:** 모든 데이터와 분석 결과는 Peewee ORM으로 관리되는 로컬 데이터베이스에 저장됩니다.

## 기술 스택

- **언어:** Python 3
- **GUI 프레임워크:** PyQt5
- **핵심 라이브러리:**
    - **데이터베이스 ORM:** Peewee
    - **수치/과학:** NumPy, SciPy, Pandas, Statsmodels
    - **3D 그래픽스 & 이미지 처리:** PyOpenGL, Trimesh, Pillow, OpenCV

## 소스 코드로 설치 및 실행하기

소스 코드에서 직접 Modan2를 실행하려면 다음 지침을 따르세요.

### 사전 요구사항

- Python 3.10 이상
- Git

### 1. 리포지토리 복제

```bash
git clone <repository-url>
cd Modan2
```

### 2. 의존성 설치

pip를 사용하여 필요한 Python 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

**Linux 사용자:** Qt 및 기타 라이브러리에 대한 시스템 수준 의존성도 설치해야 합니다.

```bash
sudo apt-get update && sudo apt-get install -y \
  libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-xfixes0 libxcb-shape0 libxcb-cursor0 \
  qt5-qmake qtbase5-dev libqt5gui5 libqt5core5a libqt5widgets5
```

### 3. 애플리케이션 실행

의존성이 설치되면 애플리케이션을 시작할 수 있습니다:

```bash
python main.py
```

## 소스 코드로 빌드하기

이 프로젝트는 `PyInstaller`를 사용하여 독립 실행 파일을 만듭니다. 헬퍼 스크립트인 `build.py`가 이 과정을 자동화합니다.

운영 체제에 맞는 배포용 패키지를 만들려면 다음을 실행하세요:

```bash
python build.py
```

빌드 결과물은 `dist/` 디렉토리에 생성됩니다.

## 테스트 실행하기

이 프로젝트는 `pytest`를 사용하여 테스트합니다. 테스트 스위트를 실행하려면 먼저 개발용 의존성을 설치하세요:

```bash
pip install -r config/requirements-dev.txt
```

그런 다음, 프로젝트 루트에서 pytest를 실행합니다:

```bash
pytest
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.
