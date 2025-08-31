# [20250831_021] 버전 관리 중앙 집중화 - 향상된 제안사항

## 개요

이 문서는 [20250831_020] 버전 관리 중앙 집중화 계획에 대한 추가 개선사항과 구현 상세를 제안합니다.

## 1. 버전 정보 독립 파일 분리

### 1.1 구조 개선안

현재 `MdUtils.py`에 버전이 포함되어 있는 구조를 개선하여, 독립적인 버전 파일을 생성합니다.

```python
# version.py (프로젝트 루트에 새로 생성)
"""
Modan2 Version Information
Single Source of Truth for version management
"""
__version__ = "0.1.4"
__version_info__ = tuple(map(int, __version__.split('.')))
```

```python
# MdUtils.py 수정
from version import __version__ as PROGRAM_VERSION

# 또는 하위 호환성을 위해
try:
    from version import __version__
    PROGRAM_VERSION = __version__
except ImportError:
    PROGRAM_VERSION = "0.1.4"  # fallback
```

### 1.2 장점

- **명확한 책임 분리**: 버전 정보만을 위한 전용 파일
- **Import 편의성**: 다른 모듈에서 `from version import __version__` 로 쉽게 접근
- **도구 호환성**: 많은 Python 도구들이 `__version__` 변수를 표준으로 인식

## 2. 버전 검증 및 관리 유틸리티

### 2.1 버전 검증 함수

```python
# version_utils.py (새 파일)
import re
from typing import Tuple, Optional

def validate_version(version: str) -> bool:
    """
    Semantic Versioning 2.0.0 형식 검증
    https://semver.org/
    
    Examples:
        - 0.1.4 (valid)
        - 1.0.0-alpha (valid)
        - 2.1.0-beta.1 (valid)
        - 1.2 (invalid - patch version missing)
    """
    pattern = r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)' \
              r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)' \
              r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?$'
    
    if not re.match(pattern, version):
        raise ValueError(f"Invalid semantic version format: {version}")
    return True

def parse_version(version: str) -> Tuple[int, int, int, Optional[str]]:
    """
    버전 문자열을 구성 요소로 분해
    
    Returns:
        (major, minor, patch, prerelease)
    """
    validate_version(version)
    
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$', version)
    if match:
        major, minor, patch, prerelease = match.groups()
        return int(major), int(minor), int(patch), prerelease
    
    raise ValueError(f"Unable to parse version: {version}")

def compare_versions(v1: str, v2: str) -> int:
    """
    두 버전 비교
    Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    p1 = parse_version(v1)[:3]  # major, minor, patch only
    p2 = parse_version(v2)[:3]
    
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0
```

## 3. 자동 버전 업데이트 스크립트

### 3.1 버전 범프 유틸리티

```python
# bump_version.py (프로젝트 루트에 새 파일)
#!/usr/bin/env python
"""
버전 자동 업데이트 스크립트
사용법: python bump_version.py [major|minor|patch]
"""

import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path

def get_current_version():
    """현재 버전 읽기"""
    version_file = Path("version.py")
    content = version_file.read_text()
    match = re.search(r'__version__ = "(.*?)"', content)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string")

def update_version_file(new_version: str):
    """version.py 파일 업데이트"""
    version_file = Path("version.py")
    content = version_file.read_text()
    
    # 버전 문자열 교체
    new_content = re.sub(
        r'__version__ = ".*?"',
        f'__version__ = "{new_version}"',
        content
    )
    
    # 백업 생성
    backup_file = version_file.with_suffix('.py.bak')
    version_file.rename(backup_file)
    
    try:
        # 새 파일 작성
        version_file.write_text(new_content)
        print(f"✅ Version updated to {new_version}")
        
        # 백업 삭제
        backup_file.unlink()
    except Exception as e:
        # 롤백
        backup_file.rename(version_file)
        raise e

def bump_version(bump_type: str = 'patch'):
    """
    버전 증가
    
    Args:
        bump_type: 'major', 'minor', 'patch' 중 하나
    """
    current = get_current_version()
    parts = current.split('.')
    
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == 'major':
        new_version = f"{major + 1}.0.0"
    elif bump_type == 'minor':
        new_version = f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        new_version = f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    print(f"Bumping version: {current} → {new_version}")
    return new_version

def create_git_tag(version: str, message: Optional[str] = None):
    """Git 태그 생성"""
    tag_name = f"v{version}"
    
    if message is None:
        message = f"Release version {version}"
    
    try:
        # 태그 생성
        subprocess.run(['git', 'tag', '-a', tag_name, '-m', message], check=True)
        print(f"✅ Git tag created: {tag_name}")
        
        # 태그 푸시 여부 확인
        response = input("Push tag to remote? (y/N): ")
        if response.lower() == 'y':
            subprocess.run(['git', 'push', 'origin', tag_name], check=True)
            print(f"✅ Tag pushed to remote")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create git tag: {e}")

def update_changelog(version: str):
    """CHANGELOG.md 자동 업데이트 (선택적)"""
    changelog_file = Path("CHANGELOG.md")
    
    if not changelog_file.exists():
        # CHANGELOG.md가 없으면 생성
        content = f"""# Changelog

## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial release

"""
        changelog_file.write_text(content)
        print("✅ CHANGELOG.md created")
    else:
        # 기존 파일에 새 버전 섹션 추가
        content = changelog_file.read_text()
        
        # 새 버전 섹션 생성
        new_section = f"""
## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- 

### Changed
- 

### Fixed
- 

"""
        # "# Changelog" 다음에 삽입
        new_content = content.replace("# Changelog\n", f"# Changelog\n{new_section}")
        changelog_file.write_text(new_content)
        print("✅ CHANGELOG.md updated")

def main():
    """메인 실행 함수"""
    bump_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    
    if bump_type not in ['major', 'minor', 'patch']:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    try:
        # 1. 버전 범프
        new_version = bump_version(bump_type)
        
        # 2. 파일 업데이트
        update_version_file(new_version)
        
        # 3. CHANGELOG 업데이트 (선택적)
        response = input("Update CHANGELOG.md? (y/N): ")
        if response.lower() == 'y':
            update_changelog(new_version)
        
        # 4. Git 커밋
        response = input("Create git commit? (y/N): ")
        if response.lower() == 'y':
            subprocess.run(['git', 'add', 'version.py'], check=True)
            if Path("CHANGELOG.md").exists():
                subprocess.run(['git', 'add', 'CHANGELOG.md'], check=True)
            
            commit_message = f"chore: bump version to {new_version}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print(f"✅ Git commit created")
            
            # 5. Git 태그 생성
            response = input("Create git tag? (y/N): ")
            if response.lower() == 'y':
                create_git_tag(new_version)
        
        print(f"\n🎉 Version {new_version} is ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 4. 빌드 시스템 통합 개선

### 4.1 향상된 build.py

```python
# build.py 개선 사항
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Optional

# 버전 가져오기를 import로 변경
try:
    from version import __version__
except ImportError:
    # fallback: 정규식으로 추출
    def get_version():
        with open("version.py", "r") as f:
            content = f.read()
            match = re.search(r'__version__ = "(.*?)"', content)
            if match:
                return match.group(1)
        raise RuntimeError("Unable to find version string")
    __version__ = get_version()

class BuildManager:
    """빌드 프로세스 관리 클래스"""
    
    def __init__(self, version: str):
        self.version = version
        self.build_dir = Path("dist")
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def prepare_innosetup(self):
        """InnoSetup 스크립트 준비"""
        template_path = Path("InnoSetup/Modan2.iss.template")
        output_path = self.temp_dir / "Modan2.iss"
        
        # 템플릿 읽기
        template_content = template_path.read_text()
        
        # 버전 교체
        content = template_content.replace("{{VERSION}}", self.version)
        
        # 임시 파일 생성
        output_path.write_text(content)
        
        return output_path
    
    def build_pyinstaller(self, platform: str):
        """PyInstaller 빌드 실행"""
        output_name = f"Modan2_v{self.version}_{platform}"
        
        cmd = [
            "pyinstaller",
            "--name", output_name,
            "--onefile",
            "--windowed",
            "--icon", "icons/main.ico" if platform == "win" else "icons/main.png",
            "--add-data", f"ExampleDataset{os.pathsep}ExampleDataset",
            "--add-data", f"icons{os.pathsep}icons",
            "Modan2.py"
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"PyInstaller build failed: {result.stderr}")
        
        return self.build_dir / output_name
    
    def cleanup(self):
        """임시 파일 정리"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
```

## 5. CI/CD 통합

### 5.1 GitHub Actions 워크플로우

```yaml
# .github/workflows/version-check.yml
name: Version Consistency Check

on:
  pull_request:
    paths:
      - 'version.py'
      - 'MdUtils.py'
      - 'InnoSetup/**'
      - 'build.py'

jobs:
  check-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Check version consistency
        run: |
          python -c "
          import re
          from pathlib import Path
          
          # Read version from version.py
          version_content = Path('version.py').read_text()
          version_match = re.search(r'__version__ = \"(.*?)\"', version_content)
          if not version_match:
              raise RuntimeError('Version not found in version.py')
          
          version = version_match.group(1)
          print(f'Version found: {version}')
          
          # Validate semantic versioning
          import re
          pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
          if not re.match(pattern, version):
              raise ValueError(f'Invalid version format: {version}')
          
          print('✅ Version format is valid')
          "
```

## 6. 구현 로드맵

### Phase 1: 기본 구조 구축 (1일)
1. `version.py` 파일 생성
2. `MdUtils.py` 수정하여 version.py import
3. 기본 테스트

### Phase 2: 빌드 시스템 개선 (2일)
1. `build.py` 개선
2. InnoSetup 템플릿 시스템 구현
3. PyInstaller 명령어 동적 생성

### Phase 3: 자동화 도구 추가 (1일)
1. `bump_version.py` 스크립트 작성
2. `version_utils.py` 유틸리티 함수 구현
3. 문서화

### Phase 4: CI/CD 통합 (1일)
1. GitHub Actions 워크플로우 설정
2. 자동 버전 검증
3. 릴리즈 자동화

## 7. 마이그레이션 체크리스트

- [ ] `version.py` 파일 생성
- [ ] `MdUtils.py`에서 version.py import
- [ ] `build.py` 개선
- [ ] InnoSetup 템플릿 파일 생성
- [ ] `setup.py` 업데이트
- [ ] `bump_version.py` 스크립트 작성
- [ ] 테스트 실행
- [ ] 문서 업데이트
- [ ] CI/CD 파이프라인 설정

## 8. 예상 효과

1. **개발 효율성 향상**: 버전 업데이트가 단일 명령으로 가능
2. **일관성 보장**: 모든 컴포넌트가 동일한 버전 사용
3. **자동화**: Git 태그, CHANGELOG, 빌드 파일명 등 자동 관리
4. **추적성**: 버전 히스토리와 변경사항 명확한 관리
5. **CI/CD 친화적**: 자동 빌드 및 배포 파이프라인 구축 용이

## 9. 참고 자료

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 440 -- Version Identification](https://www.python.org/dev/peps/pep-0440/)