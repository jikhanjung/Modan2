# Ruff DTZ(flake8-datetimez) 도입 — tz-naive datetime 가드

## 날짜
2026-07-26

## 배경

[[20260723_R05_code_quality_checks_review]]의 단계 확대 계획에서 LOG/RUF012/S 다음
순서가 DTZ였다("28건, 개별 검토 — 로컬시간 의도 여부"). DTZ는 tz 정보 없는
`datetime.now()`/`fromtimestamp()`/`strptime()`/`date.today()` 등 naive datetime을
잡아 신규 코드가 타임존 버그를 만들지 않게 가드한다.

## 개별 검토 결과

28개 사이트를 모두 확인한 결과 **전부 로컬 wall-clock 의도**였다 — 크로스-타임존
저장/비교 용도는 하나도 없다:

- export/log/migration **파일명 타임스탬프**(`strftime("%Y%m%d…")`)
- 빌드 메타데이터(`build_year = datetime.now().year`)
- 파일 mtime/ctime **표시**(`fromtimestamp(...)`), ZIP 매니페스트의 `last_modified`
  (쓰기 전용 정보 — import에서 파싱하지 않음을 확인)
- 이미지 EXIF 날짜 파싱(ctime 문자열 → strftime 재포맷)

## 접근 — 동작 보존

로컬 wall-clock 유지가 목표이므로 `datetime.now()` → `datetime.now().astimezone()`,
`fromtimestamp(ts)` → `.astimezone()`. `strftime`/`.year` 출력은 **완전히 동일**
(astimezone은 aware-local이라 벽시계 숫자 불변). `isoformat()` 사이트는 오프셋
접미사가 붙지만, 해당 값들은 표시/정보용이라 무해함(매니페스트 last_modified는
파싱되지 않음을 grep으로 확인).

- 앱 코드 13곳 수정: `MdUtils`(build year·mtime isoformat), `MdModel`(EXIF strptime·
  migration date), `MdHelpers`(format_timestamp·file-info fromtimestamp), `main`
  (로그 파일명), `export_dialog`/`dataset_analysis_dialog`(export 파일명).
- `MdHelpers.parse_datetime`는 포맷 무관 범용 파서라 naive가 설계 의도 → 인라인
  `# noqa: DTZ007`(앱 내 호출자 없음, 테스트만 사용).

## 스코프

- `select`에 `DTZ` 추가.
- **tests/** 와 **dev/build 스크립트**(build.py, migrate.py, manage_version.py,
  tools/*, docs/build_all.py)는 per-file-ignore로 DTZ 제외 — S(bandit)를 tests에서
  제외한 것과 동일한 원칙. 테스트 픽스처의 고정 datetime과 빌드 스크립트의 로컬
  타임스탬프는 tz-aware로 만들 이득이 없고 churn만 늘어난다.

## 결과

- `ruff check .` 전체 통과(DTZ 포함). 관련 스위트 517 passed, 1 skipped.
- 앱 코드의 모든 datetime 사용이 명시적 로컬(aware)로 바뀌었고, 이후 신규 코드의
  naive datetime은 린트가 잡는다.
