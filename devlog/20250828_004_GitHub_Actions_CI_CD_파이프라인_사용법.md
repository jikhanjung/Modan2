# GitHub Actions CI/CD 파이프라인 사용법

## 작성일: 2025-08-28

## 1. 개요

Modan2 프로젝트에 자동화된 CI/CD 파이프라인을 구축했습니다. 이를 통해 코드 품질 관리, 자동 테스트, 크로스 플랫폼 빌드, 릴리즈 자동화가 가능합니다.

## 2. 파이프라인 구성

### 2.1 생성된 파일 목록
```
.github/
├── workflows/
│   ├── test.yml        # 테스트 자동화
│   ├── build.yml       # 빌드 자동화
│   └── release.yml     # 릴리즈 자동화
├── PULL_REQUEST_TEMPLATE.md  # PR 템플릿
└── dependabot.yml      # 의존성 업데이트 자동화
```

### 2.2 각 파이프라인의 역할

#### 🧪 **test.yml - 테스트 자동화**
- **트리거**: `main`, `develop` 브랜치로 push 또는 PR 생성 시
- **실행 환경**: Ubuntu Latest
- **Python 버전**: 3.11, 3.12 (매트릭스 빌드)
- **주요 작업**:
  - 시스템 의존성 설치 (Qt, OpenGL 등)
  - Python 패키지 설치
  - pytest 실행 + 커버리지 측정
  - Codecov에 결과 업로드
  - Xvfb를 통한 headless GUI 테스트

#### 🏗️ **build.yml - 빌드 자동화**  
- **트리거**: 태그 푸시 (`v*.*.*`) 또는 수동 실행
- **실행 환경**: Windows, macOS, Ubuntu
- **주요 작업**:
  - 각 플랫폼에서 PyInstaller로 실행파일 생성
  - 빌드 아티팩트를 GitHub Actions에 저장

#### 🚀 **release.yml - 릴리즈 자동화**
- **트리거**: GitHub Release 생성 시
- **주요 작업**:
  - 모든 플랫폼 빌드 실행
  - 압축 파일 생성 (Windows: .zip, macOS/Linux: .tar.gz)
  - Release에 자동 업로드

#### 📝 **dependabot.yml - 의존성 관리**
- **트리거**: 매주 자동 실행
- **기능**: Python 패키지 업데이트 PR 자동 생성

## 3. 초기 설정 방법

### 3.1 GitHub 저장소에 파이프라인 등록
```bash
# 파이프라인 파일들을 저장소에 추가
git add .github/
git commit -m "Add GitHub Actions CI/CD pipeline

- 테스트 자동화 (test.yml)
- 크로스 플랫폼 빌드 자동화 (build.yml)  
- 릴리즈 자동화 (release.yml)
- PR 템플릿 및 Dependabot 설정

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### 3.2 첫 실행 확인
1. GitHub 저장소 → **Actions** 탭 방문
2. "Tests" 워크플로우 실행 상태 확인
3. 초록색 ✅ 체크 시 정상 작동

## 4. 일상 개발 워크플로우

### 4.1 기능 개발 프로세스

#### Step 1: 브랜치 생성 및 개발
```bash
git checkout -b feature/새기능명
# 코드 개발...
python Modan2.py  # 로컬 테스트
pytest            # 단위 테스트
```

#### Step 2: Pull Request 생성
```bash
git add .
git commit -m "feat: 새 기능 추가

상세 설명...

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin feature/새기능명
```

GitHub에서 PR 생성 시:
- PR 템플릿이 자동으로 로드됨
- 체크리스트를 따라 작성
- 테스트가 자동으로 실행됨

#### Step 3: 코드 리뷰 및 머지
- CI 테스트 통과 확인 (✅ 초록색 체크)
- 코드 리뷰 완료 후 머지
- `main` 브랜치에서 다시 테스트 자동 실행

### 4.2 테스트 실패 시 대응

#### 로컬에서 디버깅
```bash
# 실패한 테스트 재현
pytest tests/test_실패한파일.py -v

# 커버리지 확인
pytest --cov=. --cov-report=html

# HTML 리포트 확인
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### CI 로그 확인
1. GitHub Actions → 실패한 워크플로우 클릭
2. 실패한 단계의 로그 펼쳐서 에러 메시지 확인
3. 로컬에서 동일한 환경으로 재현 테스트

## 5. 릴리즈 관리

### 5.1 버전 태그 기반 릴리즈

#### 패치 릴리즈 (버그 수정)
```bash
git tag v0.1.4
git push origin v0.1.4
```

#### 마이너 릴리즈 (새 기능)  
```bash
git tag v0.2.0
git push origin v0.2.0
```

#### 메이저 릴리즈 (호환성 변경)
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 5.2 GitHub Release를 통한 릴리즈

1. GitHub 저장소 → **Releases** → **Create a new release**
2. **Tag version**: `v0.1.4` (새 태그 생성)
3. **Release title**: `Modan2 v0.1.4 - 버그 수정 및 개선`
4. **Release notes**: 변경사항 작성
5. **Publish release** 클릭

→ 자동으로 모든 플랫폼 빌드 실행 및 업로드

### 5.3 빌드 결과물 확인

릴리즈 완료 후 다음 파일들이 자동 생성됩니다:
- `Modan2-Windows.zip` - Windows 실행 파일
- `Modan2-macOS.tar.gz` - macOS 애플리케이션
- `Modan2-Linux.tar.gz` - Linux 실행 파일

## 6. 고급 설정

### 6.1 Codecov 연동 (선택사항)

더 상세한 커버리지 리포트를 위해:

1. https://codecov.io 에서 GitHub 계정으로 로그인
2. Modan2 저장소 추가
3. 제공되는 토큰 복사
4. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
5. **New repository secret**: 
   - Name: `CODECOV_TOKEN`
   - Secret: 복사한 토큰 값

### 6.2 브랜치 보호 규칙 설정

main 브랜치의 안정성을 위해:

1. GitHub 저장소 → **Settings** → **Branches**
2. **Add rule** → Branch name pattern: `main`
3. 다음 옵션 활성화:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
   - Status checks: `test (3.11)`, `test (3.12)` 선택
4. **Create** 클릭

### 6.3 알림 설정

#### Slack 연동 (팀 작업 시)
```yaml
# .github/workflows/test.yml 에 추가
- name: Notify Slack on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    channel: '#dev-alerts'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

#### 이메일 알림
GitHub 계정 설정에서 Watching 상태를 "All Activity"로 설정

## 7. 문제 해결

### 7.1 자주 발생하는 문제들

#### Qt 관련 오류
```bash
# 로컬에서 Qt 환경 확인
python -c "from PyQt5.QtWidgets import QApplication; print('Qt OK')"

# Linux에서 headless 환경 테스트
export QT_QPA_PLATFORM=offscreen
python Modan2.py
```

#### 의존성 충돌
```bash
# 의존성 트리 확인
pip show 패키지명
pip list --outdated

# 가상환경 재생성
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 빌드 실패
- PyInstaller 호환성 확인
- 각 플랫폼별 시스템 의존성 누락 체크
- build.py 스크립트 로컬 테스트

### 7.2 디버깅 팁

#### 로컬에서 CI 환경 재현
```bash
# Docker를 사용한 Ubuntu 환경 재현
docker run -it ubuntu:latest
apt-get update && apt-get install -y python3 python3-pip git

# 의존성 설치 후 테스트
```

#### Actions 로그 다운로드
1. GitHub Actions → 실패한 워크플로우
2. 우측 상단 **⚙️** → **Download logs**
3. 로컬에서 상세 분석

## 8. 모니터링 및 유지보수

### 8.1 정기 점검 사항

#### 월간 체크리스트
- [ ] Dependabot PR 검토 및 머지
- [ ] CI 실행 시간 모니터링 (15분 초과 시 최적화 필요)
- [ ] 커버리지 추세 확인 (감소 시 테스트 추가)
- [ ] Actions 사용량 확인 (GitHub 무료 할당량 2000분/월)

#### 연간 체크리스트  
- [ ] Python 버전 매트릭스 업데이트
- [ ] GitHub Actions 버전 업데이트 (v3 → v4 등)
- [ ] 보안 취약점 점검
- [ ] 빌드 도구 업데이트 (PyInstaller 등)

### 8.2 성능 최적화

#### 캐시 활용도 확인
```yaml
# 캐시 히트율 모니터링
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

#### 매트릭스 빌드 최적화
- 자주 실패하는 Python 버전 식별
- 필수 버전만 유지하여 실행 시간 단축

## 9. 추가 리소스

### 9.1 공식 문서
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [PyInstaller 문서](https://pyinstaller.readthedocs.io/)
- [pytest 문서](https://docs.pytest.org/)

### 9.2 유용한 GitHub Actions
- `actions/checkout@v4` - 코드 체크아웃
- `actions/setup-python@v4` - Python 환경 설정
- `actions/cache@v3` - 의존성 캐시
- `codecov/codecov-action@v3` - 커버리지 업로드

### 9.3 모범 사례
- 커밋 메시지에 명확한 변경 사항 기록
- PR은 작은 단위로 분할
- 테스트 커버리지 70% 이상 유지
- 릴리즈 노트에 사용자 관점의 변경사항 기록

---

## 결론

이 CI/CD 파이프라인을 통해 Modan2 프로젝트의 품질과 배포 과정이 크게 개선됩니다. 자동화된 테스트로 버그를 조기에 발견하고, 크로스 플랫폼 빌드로 사용자에게 안정적인 소프트웨어를 제공할 수 있습니다.

문제 발생 시 이 문서를 참고하여 해결하고, 새로운 팀원은 이 가이드를 따라 개발 환경을 구축할 수 있습니다.