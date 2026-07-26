# ZIP import 롤백 시 고아 미디어/디렉터리 정리 (R04 #4 잔여)

## 날짜
2026-07-26

## 배경

[[20260723_R04_audit_fileio_security_errorhandling]] #4의 잔여 항목: JSON+ZIP 패키지
import는 `gDatabase.atomic()`로 DB를 롤백하지만, 롤백 시 이미 스토리지로 복사된
미디어 파일 정리는 `copied_files` 리스트 기반 per-file cleanup에 의존한다 — "별도
점검 여지"로 남아 있었다.

점검 결과 갭이 있었다. `import_dataset_from_zip`의 롤백 핸들러는 추적된 파일만
지우고 **`_import_media`가 만든 디렉터리(`<storage>/<ds.id>/`)는 남긴다**(빈 디렉터리
고아). 또한 `shutil.copy2`가 중간에 실패해 부분 기록된 파일은 `copied_files`에
추가되기 전이라 추적되지 않아 정리되지 않는다.

## 수정 (`MdUtils.import_dataset_from_zip`)

import는 항상 **새 데이터셋**을 만들므로(`_dataset_from_manifest`가 새 `MdDataset`을
생성, 고유 이름), 복사된 모든 미디어는 `<storage>/<새 ds.id>/` 아래에만 있다. 롤백
시 그 **데이터셋 스토리지 디렉터리 전체를 `shutil.rmtree`**로 제거하도록 변경:

- `ds = None`을 atomic try 앞에 두고, 예외 핸들러에서 `ds`가 생성됐으면
  `<storage>/<ds.id>/`를 통째로 삭제. 이로써 복사 파일 + 생성된 디렉터리 + 추적 안 된
  부분 파일까지 한 번에 정리된다.
- 기존 per-file `copied_files` 정리는 "혹시 그 트리 밖에 있는 추적 파일"을 위한
  백스톱으로 유지.
- 삭제 실패는 `logger.warning`으로만(정리 실패가 원래 예외를 덮지 않도록). 원래
  예외는 그대로 재발생.

`ModanController._remove_dataset_directory`(devlog 228, 삭제 경로)와 동일한
`rmtree(<storage>/<id>/)` 패턴이라 일관적이다.

## 테스트

`test_failed_import_leaves_no_orphaned_files`: 이미지가 붙은 오브젝트 + 일반
오브젝트 2개를 `include_files=True`로 패키징하고, `_object_from_manifest`를 2번째
호출에서 raise하도록 몽키패치(= 첫 오브젝트 이미지가 복사된 뒤 실패). 스토리지는
`_get_storage_dir` 패치로 tmp에 격리. import가 raise한 뒤:

- 스토리지 디렉터리 목록이 import 전과 동일(고아 데이터셋 디렉터리 없음).
- 새 데이터셋이 DB에 남지 않음.

수정 전에는 빈 `<storage>/<새 id>/`가 남아 이 테스트가 실패한다(회귀 가드).

## 결과

- 관련 스위트 156 passed. `ruff`/`format` 클린.
- 실패한 ZIP import가 디스크에 아무것도 남기지 않는다(파일·디렉터리·부분 파일 모두).
