# ruff `S`(bandit) 도입 + 패키징 스모크 테스트 + requirements-ci 정리

## 날짜
2026-07-24

## 배경

[[20260724_244_ci_lockfiles_codeql_version_test]]에서 채택했으나 미착수로 남겼던
CI 후속 3건을 마무리했다. 셋 다 [[20260724_R06_ci_recommendations_review_and_quickwins]]
리뷰에서 나온 항목이다.

1. ruff `S`(flake8-bandit) 룰셋 활성화 (권고 #3)
2. 패키징 산출물 스모크 테스트 (공통 gap)
3. `config/requirements-ci.txt` 제거 (244의 부수 정리 항목)

---

## 1. ruff `S`(bandit) 활성화 — 전수 triage 후 도입

### 규모
`ruff check . --select S` → 3818건. 그러나 **3751건이 S101(assert)** 로 거의 전부
tests. tests/** carve-out 후 앱코드 실제 대상은 **34건**이었다.

| 룰 | 건수 | 처리 |
|---|---|---|
| S110 try-except-pass | 11 | 전역 ignore (의도적 방어 패턴) |
| S607 partial-path process | 6 | dev/build 도구 per-file-ignore |
| S603 subprocess untrusted | 6 | dev/build 도구 per-file-ignore |
| S311 non-crypto random | 6 | 전역 ignore (뷰어 색상 픽킹, 암호용 아님) |
| S324 insecure md5 | 2 | **코드 수정** |
| S112 try-except-continue | 2 | 전역 ignore (의도적) |
| S602 shell=True | 1 | dev 도구 per-file-ignore |

### 개별 판단
- **S324 (md5 2건, `MdModel.py`)**: `get_md5hash_info` — 이미지 파일 **내용 해싱**
  (중복 검출/변경 감지)용이지 보안용이 아님. `hashlib.md5(usedforsecurity=False)`로
  수정(의미상 정확, Python 3.9+). 진짜 고칠 값어치가 있던 유일한 건.
- **S110/S112 (13건 전수 확인)**: 전부 의도적 best-effort suppression —
  에러 핸들러 정리(cursor 복원/msgbox), 옵션 기능 폴백(QApplication/pytz shim),
  startup 보호(excepthook은 절대 재-raise 금지), matplotlib artist 제거,
  per-item 루프 skip. 실제 버그를 숨기는 곳 0. 방어적 GUI 코드에 대해 高노이즈
  룰이라 **전역 ignore** + 사유 주석.
- **S311 (6건, `object_viewer_3d.py`)**: `initialize_colors`가 GL 픽킹용 고유 색을
  뽑는 데 `random` 사용. 암호와 무관. 앱 전체에 암호용 난수가 없어 **전역 ignore**.
- **S603/S607/S602 (subprocess)**: 전부 dev/build 도구(`build.py`,
  `manage_version.py`, `docs/build_all.py`, `tools/*`)가 신뢰된 git/python/sphinx를
  실행. 배포되는 파일-인제스트 앱 코드가 아니므로 **해당 파일만 per-file-ignore**.
  앱 코드엔 S603/S607을 active로 유지(향후 shell-out 시 잡음).
- **S101 (앱코드 1건, `ModanController.py:368`)**: `assert self.current_dataset
  is not None` — mypy 타입 내로잉 겸 불변식(공개 호출자가 이미 검증). 입력 검증이
  아니므로 `# noqa: S101` + 사유.

### tests
`"tests/**" = ["S"]` — 신뢰된 테스트 코드엔 bandit 미적용(assert, `/tmp` fixture,
테스트용 SQL/subprocess/md5). 서브디렉터리(`tests/dialogs/`)까지 `**`로 커버.

### 결과
`ruff check .` clean, `ruff format --check` clean. 이제 `S` 그룹의 값어치 있는
부분(eval/exec/pickle/unsafe-yaml/hardcoded-SQL 등)이 앱 전체에 상시 active —
신규 코드 가드. 현재 위반 0.

---

## 2. 패키징 산출물 스모크 테스트 — frozen 빌드 headless 부팅

### 문제
CI가 OS별 인스톨러를 빌드하지만 실행파일이 *존재하는지*만 확인했다. "소스에선
되는데 frozen에선 깨지는"(PyInstaller `--add-data` 누락, 언번들 네이티브 lib)
클래스는 소스 테스트로 도달 불가.

### 구현
- **`main.py`에 `--self-test` 플래그 신설**: 전체 startup 경로(무거운 import +
  마이그레이션 + 메인윈도 생성)를 실행한 뒤, 이벤트 루프에서 `QTimer.singleShot(2s)`로
  top-level 정리 후 `app.quit()` → exit 0. frozen 앱은 self-contained(번들된
  Python/libs 사용, 빌드 venv 아님)라 같은 job에서 실행해도 번들 무결성을 검증.
  - 로컬 검증: `QT_QPA_PLATFORM=offscreen python main.py --self-test` → exit 0 확인.
- **`reusable_build.yml` 3개 빌드 job에 스모크 스텝 추가** (onedir 산출물
  `dist/Modan2/Modan2[.exe]` 대상, 인스톨러에 들어가는 바로 그 빌드):
  - **Windows**: `Start-Process -Wait -PassThru`로 windowed(`--noconsole`) 앱을
    실제로 기다린 뒤 `ExitCode` 확인.
  - **macOS**: 직접 실행(coreutils `timeout` 없음 → 인앱 워치독에 의존).
  - **Linux**: Xvfb 필요 — 뷰어가 construction 시 `glutInit()`을 호출하는데
    display 없으면 offscreen Qt로도 SEGFAULT(test.yml과 동일 이유). `timeout 120`
    안전망.
- **`tests/test_main_cli.py` 신설**: `--self-test`/`--no-splash`/`--lang` 파싱
  가드(플래그가 사라지면 유닛 테스트에서 먼저 실패).

### 주의 (첫 릴리스 시 관찰 필요)
CI에서 로컬 검증이 불가능한 부분(frozen exe의 실제 기동)이라, 다음 릴리스 빌드에서
세 스텝이 초록인지 확인할 것. 인앱 2초 워치독이 종료를 보장하지만, 예기치 못한
모달이 뜨면 워치독이 top-level을 닫고 quit.

---

## 3. `config/requirements-ci.txt` 제거

244에서 CI 설치를 `requirements-dev.lock`으로 전환하면서 미사용이 됐다(dev.lock이
상위집합). 세 번째 중복 의존성 목록을 남길 이유가 없어 제거:
- `git rm config/requirements-ci.txt`.
- `config/README.md` 갱신: requirements-ci 섹션 → lockfile 설명으로 교체, CI/CD
  설치 스텝·트러블슈팅 참조 수정, 은퇴 노트 추가.
- `CLAUDE.md`의 config/ 설명 갱신.

---

## 검증
- `ruff check .` / `ruff format --check .` → clean (S 활성 상태).
- `pytest tests/test_main_cli.py tests/test_version_consistency.py` → 7 passed.
- `pytest tests/test_smoke_import.py tests/test_controller.py` → 124 passed.
- `pytest tests/test_mdmodel.py -k "md5 or hash or image"` → 22 passed (md5 수정).
- `QT_QPA_PLATFORM=offscreen python main.py --self-test` → exit 0.
- `reusable_build.yml` YAML 파싱 유효.

## 남은 후속
- 다음 릴리스에서 3개 스모크 스텝 초록 확인(첫 실전 검증).
- (선택) 스모크를 별도 클린-러너 job으로 승격 — 산출물 다운로드 후 시스템 lib까지
  격리 검증. 현재는 빌드 job 내 실행(frozen exe self-contained라 실효적).
