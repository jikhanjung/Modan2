# R06 — CTHarvester CI 권고안 검토 (2026-07-24 세션)

**Date:** 2026-07-24
**Type:** review (R) — 자매 프로젝트 CTHarvester가 역제안한 CI 개선안을 Modan2
현재 상태에 비추어 평가하고 채택 여부를 결정
**Related:** [[20260723_R05_code_quality_checks_review]],
[[20260723_R04_audit_fileio_security_errorhandling]],
[[20260724_244_ci_lockfiles_codeql_version_test]] (← 채택분 실제 구현),
`../CTHarvester/docs/CI_RECOMMENDATIONS_FOR_MODAN2.md`

발단: CTHarvester가 Modan2의 `CODE_QUALITY_GUIDE.md`를 도입한 뒤, 역방향으로
"CTHarvester CI에는 있는데 Modan2에는 아직 없는 것"을 정리해준 문서
(`CI_RECOMMENDATIONS_FOR_MODAN2.md`)를 검토한다. 이 문서는 **평가·결정**만 담고,
채택한 항목의 실제 작업은 devlog 244에 있다.

> **상태 표기:** ☐ 미착수 · ◐ 진행 · ☑ 완료.

---

## 1. 권고안 5건 평가

문서는 정확하고 노이즈가 적었으나, Modan2의 실제 상태와 맞춰 보니 2건은 그대로
적용 불가라 조정이 필요했다.

| # | 권고 | 가치 | 결정 | 근거 |
|---|---|---|---|---|
| 1 | Lockfile + `--require-hashes` + `lock-check` | 높음 | ☑ 채택 | 재현 가능 빌드. 단 레시피 수정 필요(아래) |
| 2 | CodeQL SAST (`codeql.yml`) | 중상 | ☑ 채택 | pip-audit이 못 보는 자체 코드 data-flow 분석 |
| 3 | ruff `S`(bandit) 룰셋 | 중 | ◐ 보류 | 가치 있으나 첫 스캔 triage 예산 필요 → R05 큐 |
| 4 | 버전 단일 소스 일치 테스트 | 중 | ☑ 채택 | 실제 드리프트 발견(§2) |
| — | 패키징 산출물 스모크 테스트(공통) | 높음 | ☐ 보류 | ~2h·OS별, 후속 |

**채택 3건(#1·#2·#4)의 구현 → [[20260724_244_ci_lockfiles_codeql_version_test]].**

---

## 2. 검토 중 확인한 Modan2 특이사항 (결정에 영향)

### 2-1. 권고 #1은 문서 레시피대로는 실패
문서는 `uv pip compile pyproject.toml ...`을 제시하지만, **Modan2의
`pyproject.toml`에는 `[project]` 섹션이 없다**(ruff/mypy 툴 설정만). 의존성은
`requirements*.txt`에 있으므로, lockfile은 requirements 파일을 입력으로 컴파일해야
한다. 또 소스가 4갈래(`requirements.txt`, `config/requirements-ci.txt`,
`config/requirements-dev.txt`, `requirements_win.txt`)라 **어느 파일을 진실 소스로
삼을지 결정이 선행**되어야 함 → 사용자 판단으로 `requirements.txt` +
`config/requirements-dev.txt`로 확정(구현은 244).

### 2-2. 권고 #4가 예언한 드리프트가 실재
검토 중 `docs/conf.py`의 `release = "0.1.5"`가 `version.py`의 `0.2.0-alpha.2`와
이미 어긋나 있음을 발견. 문서가 경고한 "한 파일만 bump하고 나머지 잊는" 실패가
가설이 아니라 현재 상태였다 → #4를 즉시 채택할 근거가 됨(수정·가드 구현은 244).

### 2-3. #4의 검사 범위는 CTHarvester보다 작다
Modan2엔 `[project]` 테이블도 Rust 크레이트도 없어, CTHarvester판의
`[project] dynamic`·`Cargo.toml`·`config.constants` 검사는 해당 없음.
버전 보유 파일은 `version.py`(진실), `setup.py`(이미 파생), InnoSetup
템플릿(`{{VERSION}}`, 이미 파생), `docs/conf.py`(하드코딩 → 수정 대상)뿐.

---

## 3. "채택 안 함" 항목 (문서 §Not recommended 동의)
CTHarvester가 과잉으로 판단해 걷어내는 것들 — Modan2도 추가하지 않음에 동의:
- `dependency-review` 액션 — PR에서만 발화, solo commit-to-main엔 저가치, CVE
  커버리지가 pip-audit과 중복.
- 전용 성능 추적 워크플로 — 성능 SLA 있는 제품용. 마커 뒤 온디맨드 벤치로 충분.
- README 배지 자동 커밋 봇 — 히스토리 churn. 라이브 데이터 배지로 대체.

---

## 4. 후속 (R 관점의 남은 리뷰거리)
- ☐ 권고 #3 ruff `S`: 첫 스캔 findings 규모를 재본 뒤(예: `ruff check --select S`
  dry-run) R05 단계적 도입에 편입.
- ☐ 패키징 스모크 테스트(공통): 채택은 했으나 범위·비용(~2h) 때문에 보류. 릴리스
  게이트로서의 가치는 높음.
- ☐ `config/requirements-ci.txt` 존치/제거 판단(현재 CI 미사용).
