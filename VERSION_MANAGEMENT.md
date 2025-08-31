# Modan2 버전 관리 가이드

## 개요

Modan2는 중앙 집중식 버전 관리 시스템을 사용합니다. 모든 버전 정보는 `version.py` 파일에서 관리되며, 빌드 및 배포 과정에서 자동으로 적용됩니다.

## 🎯 핵심 원칙

- **Single Source of Truth**: `version.py` 파일이 유일한 버전 정보 소스
- **Semantic Versioning**: [SemVer 2.0.0](https://semver.org/) 규칙 준수
- **자동화**: 버전 업데이트와 관련 작업 자동화

## 📁 관련 파일

| 파일 | 설명 |
|------|------|
| `version.py` | 버전 정보 저장 (Single Source of Truth) |
| `bump_version.py` | 버전 업데이트 자동화 스크립트 |
| `version_utils.py` | 버전 관리 유틸리티 함수 |

## 🔧 버전 업데이트 방법

### 1. 자동 업데이트 (권장)

```bash
# 패치 버전 증가 (버그 수정)
# 예: 0.1.4 → 0.1.5
python bump_version.py patch

# 마이너 버전 증가 (새 기능 추가, 하위 호환)
# 예: 0.1.4 → 0.2.0
python bump_version.py minor

# 메이저 버전 증가 (호환성 깨지는 변경)
# 예: 0.1.4 → 1.0.0
python bump_version.py major
```

스크립트 실행 시 대화형으로 진행됩니다:
1. 현재 버전 표시
2. 새 버전 확인
3. CHANGELOG.md 업데이트 (선택)
4. Git commit 생성 (선택)
5. Git tag 생성 (선택)

### 2. 수동 업데이트

긴급한 경우에만 `version.py`를 직접 편집:

```python
# version.py
__version__ = "0.1.5"  # 직접 수정
```

⚠️ **주의**: 수동 업데이트 시 Git 태그와 CHANGELOG를 직접 관리해야 합니다.

## 📦 빌드 시 버전 적용

빌드 스크립트가 자동으로 `version.py`에서 버전을 읽어 적용합니다:

```bash
# 빌드 실행
python build.py

# 생성되는 파일 예시:
# - Modan2_v0.1.4_build123_linux
# - Modan2_v0.1.4_20240831_Installer.exe
```

## 🏷️ Git 태그 관리

### 자동 태그 생성

`bump_version.py` 사용 시 자동으로 Git 태그 생성 옵션 제공:

```bash
python bump_version.py patch
# ... 
# Create git tag? (y/N): y
# ✅ Git tag created: v0.1.5
# Push tag to remote? (y/N): y
# ✅ Tag pushed to remote
```

### 수동 태그 생성

```bash
# 태그 생성
git tag -a v0.1.5 -m "Release version 0.1.5"

# 원격 저장소에 푸시
git push origin v0.1.5
```

## 📋 CHANGELOG 관리

### 자동 업데이트

`bump_version.py` 실행 시 CHANGELOG.md 자동 업데이트:

```bash
python bump_version.py minor
# Update CHANGELOG.md? (y/N): y
# ✅ CHANGELOG.md updated
```

### 수동 편집

CHANGELOG.md 형식:

```markdown
## [0.2.0] - 2024-08-31

### Added
- 새로운 기능 설명

### Changed
- 변경된 기능 설명

### Fixed
- 수정된 버그 설명
```

## 🔍 버전 확인 방법

### 코드에서 확인

```python
# Python 코드에서
from version import __version__
print(f"Current version: {__version__}")

# 또는
import MdUtils
print(f"Version: {MdUtils.PROGRAM_VERSION}")
```

### 명령줄에서 확인

```bash
# 현재 버전 확인
python -c "from version import __version__; print(__version__)"

# Git 태그 목록 확인
git tag -l "v*"
```

## 🚀 릴리즈 워크플로우

### 1. 기능 개발 완료

```bash
# 기능 브랜치에서 작업 완료
git checkout main
git merge feature/new-feature
```

### 2. 버전 업데이트

```bash
# 버전 타입에 따라 선택
python bump_version.py minor  # 새 기능인 경우
```

### 3. CHANGELOG 편집

자동 생성된 CHANGELOG 항목을 구체적으로 편집:

```markdown
## [0.2.0] - 2024-08-31

### Added
- 3D 모델 뷰어 회전 기능 추가
- 데이터셋 내보내기 CSV 형식 지원

### Fixed
- 대용량 파일 로딩 시 메모리 누수 수정
```

### 4. 최종 커밋

```bash
git add CHANGELOG.md
git commit --amend  # 버전 커밋에 CHANGELOG 변경 포함
```

### 5. 빌드 및 배포

```bash
# 빌드 실행
python build.py

# 테스트
python Modan2.py

# 배포 아티팩트는 dist/ 폴더에 생성됨
```

## ⚠️ 주의사항

1. **버전 형식**: 항상 `MAJOR.MINOR.PATCH` 형식 유지
2. **하위 호환성**: 메이저 버전 변경 시 사용자에게 충분한 안내
3. **태그 일관성**: Git 태그는 항상 `v` 접두사 사용 (예: `v0.1.5`)
4. **CHANGELOG**: 사용자 관점에서 이해하기 쉽게 작성
5. **테스트**: 버전 업데이트 후 반드시 애플리케이션 실행 테스트

## 🔧 문제 해결

### 버전 불일치 발생 시

```bash
# version.py 확인
cat version.py

# 다른 파일들이 올바르게 import하는지 확인
python -c "import MdUtils; print(MdUtils.PROGRAM_VERSION)"

# 필요시 강제 재빌드
rm -rf build/ dist/
python build.py
```

### Git 태그 오류 시

```bash
# 로컬 태그 삭제
git tag -d v0.1.5

# 원격 태그 삭제 (주의!)
git push origin --delete v0.1.5

# 새 태그 생성
git tag -a v0.1.5 -m "Release version 0.1.5"
git push origin v0.1.5
```

## 📚 참고 자료

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Git 태그 문서](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

---

*Last updated: 2024-08-31*