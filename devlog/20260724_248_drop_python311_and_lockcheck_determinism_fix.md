# Python 3.11 지원 제거 + lock-check 결정성 버그 수정

## 날짜
2026-07-24

## 배경

dependabot PR #24(numpy `>=2.5.1`)를 처리하려다 두 가지가 드러났다:
1. **numpy 2.5.1은 Python 3.12+ 필요** — 3.11 floor로 lock을 만들면 해상 불가.
   테스트 매트릭스에 3.11이 있어서 numpy를 못 올린다. 사용자가 "3.11 제거해도
   될 것 같다" 판단 → 제거.
2. lock-check가 **결정적이지 않게 실패** — 아래 근본 원인.

[[20260724_246_per_platform_lockfiles_pyqt5_windows_fix]],
[[20260724_247_dependabot_lock_autorefresh_and_pr_triage]]의 후속.

## 1. Python 3.11 제거

앱은 원래 3.12 타깃(`pyproject.toml target-version = py312`)이고, 매트릭스에만
3.11이 남아 있었다. numpy 2.5.1+/scipy 등 최신 휠이 3.12+를 요구하는 흐름이라 유지
비용이 커진다.

- `test.yml`: 매트릭스 `python-version: ['3.11','3.12']` → `['3.12']`.
- `Makefile`: `PY_FLOOR 3.11 → 3.12`.
- lock 3개 재생성: **버전 변경 없음**, 3.11 전용 backport인 `tomli`(3.12는
  `tomllib` 표준 제공)만 제거됨. numpy는 2.4.6 유지(무언가가 <2.5로 캡하는 게
  아니라, preserve 동작 때문 — #24가 floor를 올리면 그때 2.5.1로 감).

## 2. lock-check 결정성 버그 (중요)

### 증상
`make lock` 직후 `make lock-check`가 실패. numpy가 2.4.6 ↔ 2.5.1로 오락가락.

### 근본 원인
**uv pip compile은 기존 출력 파일의 핀을 "preference"로 재사용**한다(pip-tools와
동일). 그래서:
- `make lock` → `-o requirements-<p>.lock`(기존 2.4.6 존재) → **2.4.6 보존**.
- `make lock-check` → `-o <빈 temp>` → 제약 없는 패키지를 **최신(2.5.1)으로** 해상.
→ 둘이 항상 어긋남. 게다가 이 방식이면 **upstream이 뭔가 릴리스할 때마다**
lock-check가 실패(요구사항 변경이 없어도)하는 취약 구조였다.

### 수정
`lock-check`가 비교 전에 **committed lock을 temp에 먼저 `cp`** 하도록 변경 →
uv가 기존 핀을 preference로 재사용(=`make lock`과 동일 동작) → 요구사항이 실제로
바뀐 패키지만 갱신. 결과: **요구사항 변경 시에만 실패**, 그 외엔 안정적.
`make lock-check` 3회 연속 통과 확인.

이 수정은 main의 lock-check 게이트도 upstream 릴리스에 덜 취약하게 만든다.

## 검증
- `make lock-check` × 3 → 안정적으로 "up to date".
- lock diff: `tomli`만 제거, 버전 변경 0.
- `ruff check .` clean, `test.yml`/워크플로 YAML 유효.

## 후속 (열린 PR)
- #24 numpy: 이 커밋(3.12 floor)이 main에 들어가면 rebase 시 numpy 2.5.1로 해상
  가능 → refresh-locks가 lock 갱신(단, CI 재실행은 `LOCK_REFRESH_TOKEN` PAT 필요,
  devlog 247).
- #18/19/20/23(pip dev-tool): rebase 후 refresh-locks가 push하나 PAT 없으면 CI
  미재실행 → 검증 위해 PAT 등록 또는 빈 커밋 재트리거 필요.
- 이번 세션 병합 완료: #16(setup-python v7), #21/#25(sphinx docs). Close: #17(pandas).
  rebase 대기: #22/#26(docs 충돌).
