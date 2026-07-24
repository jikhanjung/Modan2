# Dependabot lock 자동 갱신 워크플로 + 열린 PR 11건 정리

## 날짜
2026-07-24

## 배경

[[20260724_246_per_platform_lockfiles_pyqt5_windows_fix]]에서 per-platform
lockfile을 도입한 뒤, dependabot이 `requirements.txt` 등을 bump하면 커밋된 lock이
stale해져 `lock-check` 게이트가 실패하는 마찰이 드러났다(예: PR #24 numpy).
dependabot은 pip 요구사항만 바꾸고 uv lock은 못 만들기 때문이다.

이 세션에서: ① dependabot PR의 lock을 자동 재생성하는 워크플로 추가,
② 의도적 major 핀을 dependabot ignore, ③ 열린 11개 PR 전수 triage.

## 열린 PR triage (모두 dependabot, 2026-07-23 생성 = 옛 main 기준)

핵심 통찰: **이 PR들은 전부 universal-lock 버그가 있던 옛 main에서 생성**돼,
대부분의 "Test (windows) 실패"는 이미 246에서 고친 그 버그다 → **rebase하면 해소**.

| PR | 대상 | 파일 | 실패 | 처리 |
|---|---|---|---|---|
| #17 | pandas `>=3.0.5,<4.0` | requirements.txt | lock-check + win | **CLOSE** (아래) |
| #24 | numpy `>=2.5.1,<3.0` | requirements.txt(+win) | lock-check + win | rebase → lock 자동갱신 |
| #18 | pytest `>=9.1.1` | dev | win only | rebase → green |
| #19 | pytest-cov `>=7.1.0` | dev | win only | rebase → green |
| #20 | pytest-timeout `>=2.4.0` | dev | win only | rebase → green |
| #23 | coverage `>=7.15.2` | dev | win only | rebase → green |
| #16 | actions/setup-python 6→7 | workflow | win only | rebase → green |
| #21 | sphinx-rtd-theme | docs/requirements.txt | — (green) | merge 가능 |
| #22 | sphinx `>=9.1.0` | docs/requirements.txt | — (green) | merge 가능(주의: major×2) |
| #25 | sphinx-autobuild | docs/requirements.txt | — (green) | merge 가능 |
| #26 | sphinx-intl | docs/requirements.txt | — (green) | merge 가능 |

- **dev-tool PR(#18/19/20/23)**: lock에 이미 목표 버전이 들어 있어(uv가 최신으로
  해상) rebase 후 lock-check도 통과, 별도 갱신 불필요.
- **docs PR(#21/22/25/26)**: `docs/requirements.txt`만 바꿔 lock/앱과 무관 → 이미
  green. #22 sphinx는 7→9 major 2단계라 docs 빌드만 확인하면 됨.
- **#16 actions**: 워크플로 파일 변경, lock 무관. rebase로 win 재실행.

### #17 pandas는 CLOSE
`requirements.txt`에 "pandas 3.0이 pytz 메타데이터를 떨궈 frozen Windows 빌드를
깨서 의도적으로 `<3.0` 고정"이라는 주석이 달려 있다. #17(`>=3.0.5`)은 이 문서화된
제약을 정면으로 위반 → 병합하면 알려진 빌드 실패 재발. 사유를 코멘트로 남기고 close.
재제안 방지를 위해 dependabot.yml에 pandas/numpy **major** ignore 추가.

## 자동 갱신 워크플로 (`dependabot-lock-refresh.yml`)

- 트리거: `pull_request_target`(base 컨텍스트라 쓰기 토큰+시크릿 접근 가능;
  dependabot의 `pull_request`는 read-only라 push 불가) + `requirements*.txt` /
  `config/requirements-dev.txt` paths + `if: actor == dependabot[bot]`.
- 동작: PR 브랜치 checkout → `pip install uv` → `make lock` → lock이 바뀌었으면
  dependabot 명의로 commit + push.
- 보안: dependabot 액터는 외부 PR이 위조 불가. `make lock`은 `uv pip compile`만
  실행(패키지 코드 미실행)이라 head checkout이 안전.
- **토큰 주의(중요)**: 기본 `GITHUB_TOKEN`으로 push하면 성공하지만 **CI가 새 커밋에
  재실행되지 않는다**(GitHub 루프 방지) → 체크가 stale로 남음. 완전 자동화하려면
  `contents: write` fine-grained PAT를 **`LOCK_REFRESH_TOKEN`** Actions 시크릿으로
  등록해야 한다. 없으면 GITHUB_TOKEN으로 fallback(lock은 갱신되나 체크 수동 재실행
  필요).

### 필요한 후속 설정 (사용자)
1. GitHub → Settings → Developer settings → fine-grained PAT 생성
   (repo: Modan2, permission: Contents = Read/write).
2. repo → Settings → Secrets and variables → Actions → `LOCK_REFRESH_TOKEN`으로 추가.

## 검증
- `dependabot-lock-refresh.yml`, `dependabot.yml` YAML 유효.

## 실행한 PR 조치
- #17 close (+코멘트).
- #16/#18/#19/#20/#23/#24 `@dependabot rebase`(옛 main 버그 해소 + #24는 lock 자동갱신
  트리거).
- docs PR(#21/22/25/26)은 green이므로 병합 판단만 남음(사용자 몫).
