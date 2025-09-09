# Modan2 v0.1.4 Release Note

## 주요 개선사항

### 🚀 자동화 시스템 구축
- GitHub Actions 기반 CI/CD 파이프라인 구축
- Windows, Linux, macOS 크로스 플랫폼 자동 빌드
- pytest 기반 자동화 테스트 (229개 테스트)

### 🎨 UI/UX 개선
- 오버레이 드래그 및 코너 스냅 기능 추가
- 스플래시 스크린 개선
- 3D 랜드마크 인덱스 표시 복원
- 한국어 번역 대폭 개선

### 🔧 기술적 개선
- 코드 모듈화 (Controller, Helpers, Constants, Widgets 분리)
- NumPy 2.0+ 및 Python 3.12 지원
- 에러 핸들링 및 로깅 시스템 강화
- JSON 기반 설정 관리로 전환

### 🐛 버그 수정
- PCA 분석 일관성 문제 해결
- Reset Pose 기능 복구
- Linux/WSL Qt 호환성 문제 해결
- Windows Defender 오탐 문제 완화

### 📚 문서화
- 한국어 README 추가
- 개발 가이드 문서 작성 (CLAUDE.md, GEMINI.md)
- 상세한 개발 로그 추가

## 다운로드

[릴리즈 페이지](https://github.com/jikhanjung/Modan2/releases)에서 플랫폼에 맞는 버전을 다운로드하세요:

- **Windows**: `Modan2-Windows-Installer-v0.1.4-build*.zip`
- **macOS**: `Modan2-macOS-Installer-v0.1.4-build*.dmg`
- **Linux**: `Modan2-Linux-v0.1.4-build*.AppImage`

자세한 설치 방법은 [README](https://github.com/jikhanjung/Modan2/blob/main/README.ko.md#설치)를 참조하세요.

## 시스템 요구사항
- Python 3.11 이상
- NumPy 2.0+
- PyQt5

## 알려진 이슈
- WSL 환경에서 썸네일 동기화 지연
- 대용량 데이터셋 처리 시 메모리 사용량 증가

## 다음 버전 계획
- PyQt6 마이그레이션 검토
- 성능 최적화
- 추가 파일 형식 지원