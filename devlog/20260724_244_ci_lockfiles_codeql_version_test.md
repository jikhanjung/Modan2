# CI 강화: 의존성 lockfile + CodeQL SAST + 버전 일치 테스트

## 날짜
2026-07-24

## 배경

[[20260724_R06_ci_recommendations_review_and_quickwins]]에서 검토한 CTHarvester의
역제안 문서(`../CTHarvester/docs/CI_RECOMMENDATIONS_FOR_MODAN2.md`) 권고 5건 중,
채택 결정한 3건(#1 lockfile · #2 CodeQL · #4 버전 일치 테스트)을 실제로 구현했다.
(#3 ruff `S`는 triage 예산 필요 → R05 단계적 도입 큐, 패키징 스모크 테스트는 보류.)

R06가 "무엇을 왜 채택할지" 리뷰라면, 이 문서는 "실제로 무엇을 바꿨는지" 작업 기록이다.

---

## 1. 버전 단일 소스 일치 테스트 (권고 #4)

### 발견한 실제 드리프트
`docs/conf.py`의 `release = "0.1.5"`가 `version.py`의 `0.2.0-alpha.2`와 이미
어긋나 있었다. Sphinx 문서가 3개 마이너 이전 버전을 표기 중이었던 것. 문서가
경고한 "한 파일만 bump하고 나머지 잊는" 드리프트가 실재했다.

### 수정
- `docs/conf.py`: `release` 하드코딩 제거 → `version.py`에서 import.
  ```python
  from version import __version__, __version_info__
  release = __version__
  version = f"{__version_info__[0]}.{__version_info__[1]}"  # 짧은 X.Y
  ```
- `tests/test_version_consistency.py` 신설 — 4 테스트(전부 통과):
  - `test_version_is_valid_semver` — `version.py`가 semver로 파싱되고
    `__version_info__`와 일치.
  - `test_docs_conf_derives_version` — `release` 리터럴 하드코딩 금지 + import 확인.
  - `test_setup_derives_version` — `setup.py`가 `get_version()`으로 파생.
  - `test_innosetup_template_uses_placeholder` — 인스톨러 템플릿이 `{{VERSION}}`
    플레이스홀더 사용.

Modan2 형태에 맞춰 CTHarvester판의 `[project] dynamic`·`Cargo.toml`·
`config.constants` 검사는 제외(해당 파일/구조 없음). `setup.py`와 InnoSetup
템플릿은 원래부터 올바르게 파생 중이라 가드만 추가.

---

## 2. CodeQL SAST (권고 #2)

`.github/workflows/codeql.yml` 신설. 기존 `security.yml`(pip-audit = 의존성 CVE)이
못 보는 **Modan2 자체 코드의 data-flow 분석**(injection, path traversal, tainted-file
handling)을 담당. 파일 인제스트 데스크톱 앱에 실효.

- 트리거: push/PR to main + 주간(월 06:00 UTC, `security.yml`과 동일) + 수동.
- Modan2 액션 핀에 정렬: `checkout@v7`, `setup-python@v6`, `codeql-action@v3`.
- 쿼리: `security-extended,security-and-quality`.
- `paths-ignore`: `tests/`, `docs/`, `devlog/`, `build/`, `dist/`, `OBJFileLoader/`.
- Python 추출은 의존성 설치 불필요 → 무거운 PyQt5/OpenGL 설치 생략해 빠르게 유지.

---

## 3. 의존성 lockfile + hash 검증 설치 + drift 게이트 (권고 #1)

가장 값어치 높은 항목. **진실 소스는 `requirements.txt`(런타임) +
`config/requirements-dev.txt`(개발/테스트)로 결정**(사용자 지시).

### 3-1. 레시피 수정
문서는 `uv pip compile pyproject.toml`을 제시하나, Modan2의 `pyproject.toml`에는
`[project]` 섹션이 없다(ruff/mypy 툴 설정만). → requirements 파일을 입력으로 컴파일.

### 3-2. 생성물 (`uv` 0.11.32)
| 파일 | 내용 | 명령 |
|---|---|---|
| `requirements.lock` | 런타임 36 pkg | `uv pip compile requirements.txt` |
| `requirements-dev.lock` | 런타임+개발 52 pkg | `uv pip compile requirements.txt config/requirements-dev.txt` |

공통 플래그: `--universal --generate-hashes --python-version 3.11`.

> **3.11 floor가 핵심.** 테스트 매트릭스가 Python 3.11·3.12 양쪽이라, floor를
> 3.12로 두면 3.11 레그에서 `--require-hashes` 설치가 깨질 수 있음. 3.11 floor는
> 3.11·3.12 모두에 유효한 해상도를 낳는다. (처음 3.12로 만들었다가 이 이유로 재생성.)

### 3-3. 설치 경로 전환 (전부)
- **`test.yml`**: `pip install -r config/requirements-ci.txt` →
  `pip install --require-hashes -r requirements-dev.lock`.
  캐시 키도 `hashFiles('requirements-dev.lock')`로.
- **`reusable_build.yml`** (Win/mac/Linux 빌드 3곳): `pip install -r requirements.txt`
  → `pip install --require-hashes -r requirements.lock`.
  → **배포 인스톨러가 CI가 검증한 것과 동일 wheel로 빌드됨을 보장**(문서의 핵심 payoff).
- **`security.yml`** pip-audit: `-r requirements.txt` → `-r requirements.lock`
  (실제 배포되는 고정 버전을 감사).

### 3-4. drift 게이트
- `Makefile` 신설(자매 CTHarvester와 동일 패턴): `lock`(재생성) / `lock-check`
  (temp로 재생성 후 헤더 제외 diff).
  - process substitution 때문에 `SHELL := bash` 필요(기본 dash 불가).
- `security.yml`에 `lock-check` 잡 추가(uv 설치 후 `make lock-check`)
  → requirements 수정하고 재-lock 잊으면 빌드 실패.

### 3-5. 부수 효과
`config/requirements-ci.txt`는 이제 CI에서 미사용(dev.lock이 상위집합). 로컬 편의/
문서 참조 가능성 때문에 일단 존치 — 후속 정리 후보.

---

## 4. 검증 (전부 green)
- `pytest tests/test_version_consistency.py` → 4 passed.
- `python -c "import docs.conf"` → `release=0.2.0-alpha.2`, `version=0.2`.
- `ruff check tests/test_version_consistency.py docs/conf.py` → clean.
- `pip install --require-hashes --dry-run -r requirements-dev.lock` → 해시 검증 통과.
- `pip-audit -r requirements.lock --dry-run` → 32 pkg, 취약점 0.
- `make lock-check` → "Lockfiles are up to date."
- 전체 워크플로 8개 YAML 파싱 유효.

---

## 5. 유지보수 노트
- **requirements 수정 시 반드시 `make lock` 후 lock 커밋** — 안 하면 CI
  `lock-check` 실패.
- 신규 파일: `requirements.lock`, `requirements-dev.lock`, `Makefile`,
  `.github/workflows/codeql.yml`, `tests/test_version_consistency.py`.

## 남은 작업 (R06에서 이월)
- ☐ 권고 #3 ruff `S`(bandit) — R05 단계적 도입 큐. 첫 스캔 triage 예산 필요.
- ☐ 패키징 산출물 스모크 테스트(공통, ~2h) — 빌드 후 클린 러너 오프스크린 기동.
- ☐ `config/requirements-ci.txt` 제거 여부 판단.
