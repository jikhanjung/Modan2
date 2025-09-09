# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2024-12-09

### Added
- **CI/CD 및 빌드 시스템**
  - GitHub Actions 워크플로우 구축 (자동 빌드, 테스트, 릴리즈)
  - 크로스 플랫폼 빌드 지원 (Windows, Linux, macOS)
  - PyInstaller 기반 자동화 빌드 스크립트 (`build.py`)
  - 빌드 번호 시스템 및 버전 관리 중앙화 (`version.py`)

- **테스트 인프라**
  - pytest 기반 자동화 테스트 시스템 (229개 테스트, 13개 모듈)
  - 테스트 카테고리: 단위, 통합, 성능, GUI, 워크플로우
  - CI 통합으로 PR시 자동 테스트 실행
  - 테스트 커버리지 분석 도구 설정

- **UI/UX 기능**
  - 오버레이 드래그 및 코너 스냅 기능
  - 오버레이 타이틀 표시
  - 스플래시 스크린 (빌드 정보 및 저작권 표시)
  - 3D 랜드마크 인덱스 표시 복원 (GLUT 사용)
  - 툴바 버튼 상태 관리 개선
  - TreeView 사용성 개선
  - 읽기 전용 열 컨텍스트 메뉴

- **문서화**
  - 한국어 README (`README.ko.md`)
  - 개발 가이드 문서 (CLAUDE.md, GEMINI.md)
  - 릴리즈 가이드 및 버전 관리 문서
  - Windows Defender 공지 문서
  - 상세한 개발 로그 (devlog 디렉토리)

- **국제화 (i18n)**
  - 한국어 번역 대폭 개선
  - 언어 설정 즉시 적용 기능
  - 번역 파일 업데이트 (Modan2_ko.ts)

### Changed
- **코드 구조 개선**
  - 새로운 모듈 분리: `ModanController.py`, `MdHelpers.py`, `MdConstants.py`, `ModanWidgets.py`
  - 설정 관리를 QSettings에서 JSON으로 마이그레이션
  - 로깅 시스템 전환 (print문을 logging 모듈로)
  - 에러 핸들링 강화 (체계적인 try-catch 구조)
  - 저작권 정보 동적 연도 업데이트

- **의존성 업데이트**
  - NumPy 2.0+ 지원 (OpenGL 호환성 문제 해결)
  - Python 3.12 지원
  - 요구사항 파일 정리 및 크로스 플랫폼 지원

- **데이터 분석 개선**
  - PCA/CVA 분석 시스템 재구조화
  - 회귀 분석과 산점도 분리
  - Data Exploration Dialog 재구성
  - 속성(property)에서 변수(variable)로 용어 통일

### Fixed
- **주요 버그 수정**
  - PCA 분석 일관성 및 차원 문제 해결
  - Reset Pose 기능 완전 복구
  - Windows Defender 오탐 문제 완화
  - OpenGL/GLUT와 matplotlib 호환성 문제 해결
  - Linux/WSL Qt 플랫폼 플러그인 오류 수정
  - CI/CD 테스트 XIO fatal 오류 해결
  - 썸네일 동기화 문제 (WSL 특정)
  - landmark_count 의존성 제거 및 동적 계산
  - 2D 객체 뷰 마이너 버그 수정
  - 데이터셋 저장 모니터링 코드 개선
  - shape retrieval 문제 해결 (currentData vs currentIndex)
  - 와이어프레임 랜드마크 인덱스 불일치 수정

- **빌드 및 배포**
  - InnoSetup 출력 디렉토리 수정
  - Linux AppImage 생성 프로세스 개선
  - macOS 빌드 아티팩트 패턴 수정
  - Anaconda Python 호환성 개선

### Removed
- 하드코딩된 Modan2.spec 파일 (동적 생성으로 전환)
- 레거시 테스트 스크립트 (pytest로 마이그레이션)

## [0.1.3] - 2024-06-21

### Added
- 초기 안정 버전 릴리즈
- 기본 형태 분석 기능
- 2D/3D 랜드마크 지원
- TPS, NTS, OBJ, PLY, STL 파일 형식 지원
- 기본 통계 분석 기능 (PCA, CVA, MANOVA)