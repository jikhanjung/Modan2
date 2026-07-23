# R05 — 코드 품질 검사 현황 리뷰 + 추가 도입 계획 (2026-07-23 세션)

**Date:** 2026-07-23
**Type:** review (R) — 지금까지 수행된 품질 검사 종류 정리 + 추가 도입 검사 계획
**Related:** [[20260625_R01_code_review_legacy_and_db_patterns]],
[[20260717_194_R02_persist_analysis_type_case]],
[[20260721_R03_improvement_review]],
[[20260723_R04_audit_fileio_security_errorhandling]],
[[20260723_241_post_audit_runtime_fixes]],
`20260717_198_error_handling_audit`, `20251008_142_cicd_audit`,
`20251008_147_production_readiness_audit`, `20251006_111_performance_profiling_results`

발단: "과거 품질 검사 이력을 정리하고, 추가로 생각할 수 있는 검사가 뭔지" 문의.
이력 조사(devlog 병렬 서베이) + 상시 도구 구성(`pyproject.toml`,
`.pre-commit-config.yaml`, `.github/workflows/`) 확인 결과를 남긴다.

> **상태 표기:** ☐ 미착수 · ◐ 진행 · ☑ 완료. 하단 [작업 진행](#작업-진행)에서 갱신.

---

## 1. 지금까지 수행된 품질 검사 (분류별)

R-시리즈(R01~R04)가 정식 리뷰 축이고, 번호 devlog가 후속 수정을 담는다.

| 분류 | 무엇을 / 언제 | 상태 |
|---|---|---|
| 린트/포맷 | Ruff(`E,F,I,N,UP,B,C4`), pre-commit, 레포 전체 클린(`174`) | 상시 자동. **CI는 `\|\| true` 비차단** |
| 타입 체크 | mypy 훅 **주석 처리(비활성)**, 타입힌트는 신규 모듈만 | ❌ 자동화 없음 |
| 테스트 커버리지 | 34%→목표 80/70% 계획(`058`), 부스트(`075`) | 상시 측정, **게이트 없음** |
| 죽은 코드 제거 | 중복/도달불가(`152`), 죽은 모듈6+스펙8(`173`), 죽은 export(`075`) | 주기적 **수동** |
| 에러 처리 감사 | 미가드 슬롯/파서 전수(`198`), 대소문자 잠복(R02), CVA/save_object(R04) | 반복 감사, guard_slot |
| 리소스/누수 | Qt 위젯 수명주기 누수 800MB 진단·수정(`224`) | conftest 상시 반영 |
| 보안/파일 I/O | R04 3축 병렬 감사(인코딩/취약점/리소스) | 1회 종합, 전부 수정 |
| 성능 | line/memory profiler + benchmark, Procrustes 지배(`111`) | 1회 베이스라인 |
| CI/CD | 전용 감사 A등급(`142`) | 상시 자동, 1회 감사 |
| DB 무결성/마이그레이션 | R01(silent field drop·공유 mutable·numpy view), 경로 회귀(`236`), orphan(`226/228`) | 개별 수정, **상시 검사 없음** |

**반복 테마:** 쌍둥이/죽은/하위호환 경로의 잠복 버그(UI엔 안 보이나 경로 재배선 시
터짐). 대부분 감사는 1회성 스윕, **자동 게이트는 Ruff(비차단)·테스트(비게이팅)뿐.**

## 2. 관측된 구조적 갭

최근 사용자가 겪은 크래시 — `datetime.UTC`(3.10), `PyQt5.sip`, `PIL._imaging`,
한글 폰트 — 는 **전부 Windows/플랫폼 특정**인데 다음 이유로 자동으로 안 걸러졌다:

1. **CI 테스트가 ubuntu 전용** (`test.yml`). 빌드는 멀티플랫폼이나 테스트는 아님.
2. **품질 게이트가 비차단**: CI ruff `|| true`, 테스트 실패 `|| echo`로 삼켜짐.
3. **타입 체크 부재**: mypy 비활성.
4. Ruff 룰셋이 중간 수준 — 실제 데인 문제를 잡는 룰군 다수 미활성
   (`DTZ` datetime, `RUF012` mutable 클래스속성, `S` 보안, `TRY` 예외).

## 3. 추가 도입 검사 (우선순위 · 이 레포의 통증과 연결)

### 🔴 높은 가치 · 낮은 비용
1. **CI에 Windows(+macOS) 테스트 매트릭스** — 위 플랫폼 버그를 직접 포착. ☐
2. **Ruff·테스트 gating 전환** (`|| true`/`|| echo` 제거). ☐
3. **Ruff 룰셋 확대** — `DTZ`(←UTC 사가), `RUF012`(←R01 C2 공유 mutable),
   `S`(←R04 경로탈출), `TRY`/`LOG`/`G`, `SIM`/`PTH`/`RET`/`PIE`/`PERF`/`A`,
   `C901`(초장문 메서드). 위반 건수부터 리포트 후 단계 도입. ☐
4. **pytest `filterwarnings=error`** (matplotlib glyph-missing·Deprecation·numpy)
   — 한글 폰트 두부·미래 deprecation 자동 포착. ☐
5. **Import/스모크 테스트를 OS 매트릭스에서** — import 시점 크래시(`datetime.UTC`)를
   명확한 CI 실패로. ☐

### 🟡 중간 가치
6. **의존성 보안 + 환경 재현성** — Dependabot/`pip-audit`, 락파일(pip-tools/uv) +
   클린 재구성 문서(sip/PIL 손상 구조적 완화). ☐
7. **커버리지 게이트** — 전체 하한 + PR 하락 차단. ☐
8. **죽은 코드 탐지 자동화** (`vulture`) — 수동 스윕 상시화. ☐

### 🟢 탐색적
9. **속성 기반/퍼즈 테스트** (`hypothesis`) — 파서·수치 코드. ☐
10. **렌더링/i18n 회귀 테스트** — CJK 폰트 CI에서 glyph 경고 0 단언. ☐

## 4. 진행 방침

"차례대로" — 위 우선순위대로 진행하되, **변경 규모가 큰 항목(룰셋 확대,
warnings-as-error)은 먼저 위반/실패 건수를 측정**하고 자동수정 가능한 것부터
단계 도입한다. CI를 gating으로 바꾸기 전에 로컬이 깨끗한지 확인한다.

---

## 작업 진행

### 산출물
- **`docs/CODE_QUALITY_GUIDE.md`** — 멀티플랫폼 데스크탑 SW 코드 품질 종합
  가이드라인(재사용 가능). 이 R05의 관측을 일반화한 레퍼런스.

### 항목 3(Ruff 룰셋 확대) — 측정 결과 및 단계 계획

전체 레포 위반 건수(현 exclude 기준) 측정:

| 그룹 | 건수 | 자동수정 | 판단 |
|---|---|---|---|
| `LOG` | **0** | — | ✅ **즉시 도입**(무비용, 신규 코드 가드) |
| `ISC` | 0 | — | 포매터 충돌(ISC001) 소지 → 보류 |
| `DTZ` | 28 | 일부 | 🎯 고가치(UTC 사가). DTZ005(13)/006(5)/001(4)/007(4)/011(2) 개별 검토 후 도입 |
| `RUF012` | 8 | ✗ | 🎯 고가치(R01 C2 공유 mutable). ClassVar/`__init__` 이동으로 수정 후 도입 |
| `PIE` | 69 | 66 | 자동수정 대부분. 단독 PR로 |
| `RET` | 62 | 41 | 자동수정 다수(RET504/503 수동 24). 단독 PR로 |
| `SIM` | 135 | 16 | 대부분 수동. 별도 |
| `PERF` | 22 | 0 | 수동. 별도 |
| `A` | 37 | 0 | 빌트인 섀도잉, 수동. 별도 |
| `TRY` | 184 | — | 노이즈(TRY003 등) 큼. 선별 도입 |
| `G` | 280 | — | 로깅 f-string. 대규모, 별도 |
| `PTH` | 320 | — | os.path→pathlib 대규모 churn. 전용 패스 |
| `S` | 3742 | — | 대부분 S101(test assert) 등 노이즈. **특정 룰만**(S602 shell,
  S324 weak hash, S506 yaml) 선별 |
| `C901` | 62 | — | 복잡도, 정보성. 임계값 정해 리포트 |

**이번 세션 적용:** `LOG`만 `pyproject.toml` select에 추가(위반 0, 무위험).
자동수정 그룹(PIE/RET)을 전체 fix 시도했으나 **34개 파일(테스트 포함) cosmetic
churn**이 발생해 되돌림 — 가이드의 "bulk-churn 금지, 단계 도입" 원칙에 따라
각 그룹을 **단독 PR로** 처리하는 게 맞다.

**다음 단계(권장 순서):** DTZ(28) → RUF012(8) → PIE/RET 자동수정 → 나머지.
각 그룹은 자체 커밋으로, 도입 시 위반을 0으로 만든 뒤 select에 추가.

### 나머지 항목(1,2,4,5,6~10)
CI 매트릭스·gating·warnings-as-error·스모크 테스트 등은 워크플로/설정 변경이라
로컬 검증이 제한적(특히 Windows CI). 사용자와 진행 순서를 조율해 단계적으로.
[[docs/CODE_QUALITY_GUIDE.md]] Appendix A의 채택 체크리스트를 로드맵으로 사용.
