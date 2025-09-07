# Modan2 버전 관리 가이드 (v2)

## 개요

Modan2는 중앙 집중식 버전 관리 시스템을 사용합니다. 모든 버전 정보는 `version.py` 파일에서 관리되며, `manage_version.py` 스크립트를 통해 자동화된 방식으로 업데이트됩니다.

## 🎯 핵심 원칙

- **Single Source of Truth**: `version.py` 파일이 유일한 버전 정보 소스입니다.
- **Semantic Versioning**: [SemVer 2.0.0](https://semver.org/) 규칙을 엄격히 준수합니다.
- **자동화**: `manage_version.py` 스크립트를 통해 버전 업데이트와 관련 작업(CHANGELOG, Git commit/tag)을 자동화합니다.

## 📁 관련 파일

| 파일 | 설명 |
|--------------------|------------------------------------------------|
| `version.py` | 버전 정보를 저장합니다. (Single Source of Truth) |
| `manage_version.py` | 버전 업데이트 및 관련 작업을 자동화하는 스크립트입니다. |
| `CHANGELOG.md` | 각 버전별 변경 사항을 기록하는 문서입니다. |

## 🔧 버전 관리 명령어

`manage_version.py` 스크립트는 다음과 같은 명령어를 제공합니다.

### 1. 정식 버전 업데이트

안정된 정식 버전의 번호를 올립니다.

- **`major`**: `1.2.3` -> `2.0.0` (하위 호환성이 없는 변경)
- **`minor`**: `1.2.3` -> `1.3.0` (하위 호환성을 유지하는 기능 추가)
- **`patch`**: `1.2.3` -> `1.2.4` (하위 호환성을 유지하는 버그 수정)

```bash
# 마이너 버전 올리기
python manage_version.py minor
```

### 2. Pre-release 시작

다음 버전의 pre-release(사전 출시)를 시작합니다. 토큰(alpha, beta, rc)을 지정하지 않으면 `alpha`가 기본값입니다.

- **`premajor`, `preminor`, `prepatch`**

```bash
# 현재 0.1.4 버전에서 다음 마이너 버전(0.2.0)의 alpha 테스트 시작
# 결과: 0.2.0-alpha.1
python manage_version.py preminor

# 현재 0.2.0-alpha.1 버전에서 다음 메이저 버전(1.0.0)의 beta 테스트 시작
# 결과: 1.0.0-beta.1
python manage_version.py premajor beta
```

### 3. Pre-release 번호 증가

현재 pre-release 버전의 번호를 1 올립니다.

- **`prerelease`**

```bash
# 현재 0.2.0-alpha.1 버전에서
# 결과: 0.2.0-alpha.2
python manage_version.py prerelease
```

### 4. Pre-release 단계 전환

`alpha` -> `beta` -> `rc` 와 같이 pre-release 단계를 전환합니다. 번호는 1로 초기화됩니다.

- **`stage <alpha|beta|rc>`**

```bash
# 현재 0.2.0-alpha.2 버전에서 beta 단계로 전환
# 결과: 0.2.0-beta.1
python manage_version.py stage beta
```

### 5. 정식 버전으로 출시

Pre-release 버전을 안정된 정식 버전으로 변경합니다.

- **`release`**

```bash
# 현재 0.2.0-rc.3 버전에서 정식 버전으로 출시
# 결과: 0.2.0
python manage_version.py release
```

## 🚀 일반적인 릴리스 워크플로우 예시

`v0.1.0` 버전 출시 이후, `v0.2.0` 버전을 출시하는 전체 과정 예시입니다.

1.  **v0.2.0 개발 시작 (alpha)**
    - `v0.1.0` 에서 `v0.2.0`의 `alpha` 버전을 시작합니다.
    ```bash
    python manage_version.py preminor alpha
    # 새 버전: 0.2.0-alpha.1
    ```

2.  **alpha 버전 개발 및 업데이트**
    - 기능 개발 및 버그 수정을 진행하며 `prerelease`로 버전을 올립니다.
    ```bash
    # 기능 추가 후
    python manage_version.py prerelease
    # 새 버전: 0.2.0-alpha.2
    ```

3.  **beta 단계로 전환**
    - 주요 기능 개발이 완료되면 `beta` 단계로 전환하여 안정성 테스트를 시작합니다.
    ```bash
    python manage_version.py stage beta
    # 새 버전: 0.2.0-beta.1
    ```

4.  **beta 버전 테스트 및 업데이트**
    - 버그를 수정하며 `prerelease`로 버전을 올립니다.
    ```bash
    python manage_version.py prerelease
    # 새 버전: 0.2.0-beta.2
    ```

5.  **RC(Release Candidate) 단계로 전환**
    - 정식 출시 직전, 최종 후보 버전을 만듭니다.
    ```bash
    python manage_version.py stage rc
    # 새 버전: 0.2.0-rc.1
    ```

6.  **정식 버전 출시**
    - RC 버전에서 더 이상 심각한 버그가 발견되지 않으면 정식 버전으로 출시합니다.
    ```bash
    python manage_version.py release
    # 새 버전: 0.2.0
    ```

각 단계에서 `manage_version.py` 스크립트는 `CHANGELOG.md` 업데이트, Git 커밋 및 태그 생성을 대화형으로 안내합니다.

## ⚙️ 설치 및 요구사항

새로운 버전 관리 스크립트는 `semver` 라이브러리를 사용합니다. 프로젝트 실행 전, 반드시 의존성을 설치해야 합니다.

```bash
pip install -r requirements.txt
```

---
*Last updated: 2025-09-07*
