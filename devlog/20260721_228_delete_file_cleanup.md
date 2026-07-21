# 데이터셋/객체 삭제 시 파일 정리 (R03 항목 1 잔여분)

## 날짜
2026-07-21

## 문제

devlog 226에서 이미지 *교체* 시 고아 파일을 정리했지만, R03에 "관련 별건"으로
남겨둔 **삭제 경로**는 그대로였다. 확인해 보니 범위가 더 넓었다.

삭제 경로가 셋인데 파일을 정리하는 건 하나뿐이었다:

| 경로 | 정리 여부 |
|---|---|
| `ModanController.delete_object_with_files` (객체 다이얼로그) | 이미지만 (3D 모델 누락) |
| `ModanController.delete_object` | 없음 |
| `ModanController.delete_dataset` | 없음 |

게다가 **앱의 실제 삭제 동작은 컨트롤러를 거치지도 않았다**:

- `dialogs/dataset_dialog.py` `Delete()` → `self.dataset.delete_instance()`
- `Modan2.py` 객체 삭제 → `object.delete_instance()`

결과적으로 데이터셋을 지우면 `<storage>/<dataset_id>/` 디렉터리 전체(모든
객체의 이미지 + `originals/` 보관본 + 3D 모델)가 디스크에 영구히 남았다.
devlog 222의 원본 보관 기능 때문에 남는 용량은 대략 두 배가 됐다.

## 수정

### `ModanController`
- `object_file_paths(obj, storage_directory)` — 객체가 소유한 모든 파일 경로
  (이미지 작업본, 보관 원본, 3D 모델). 경로가 행에서 파생되므로 삭제 *전에*
  수집해야 한다는 점을 문서화.
- `_remove_files(paths)` — best-effort 삭제, 실패는 warning 로그만. **DB 커밋
  이후에** 호출한다: 반대 순서면 DB가 롤백됐을 때 파일만 사라진다. 이 순서면
  최악의 경우 무해한 고아가 남을 뿐이다.
- `_remove_dataset_directory(dataset_id, storage_directory)` — 한 데이터셋의
  파일은 전부 `<storage>/<dataset_id>/` 하나에 모이므로 트리째 제거.
- `delete_dataset` / `delete_object`에 `storage_directory=None` 인자 추가
  (기본값은 `mu.DEFAULT_STORAGE_DIRECTORY`), 커밋 후 정리 호출.
- `delete_object_with_files`도 공용 헬퍼를 쓰도록 변경 — 덤으로 3D 모델을
  남기던 구멍이 막혔다.

### UI 연결
정리 로직이 실제로 돌게 하려면 UI가 컨트롤러를 타야 한다 (devlog 189–191의
"다이얼로그의 DB/파일 I/O를 컨트롤러로" 방향과 동일):

- `DatasetDialog`: `ObjectDialog`와 같은 패턴으로 컨트롤러 확보
  (`parent.controller` + isinstance 가드 + 독립 폴백), `Delete()`가
  `controller.delete_dataset(id, storage_directory)` 호출.
- `Modan2.py` 객체 삭제 루프: `controller.delete_object(id, storage_directory)`.

## 테스트

`tests/test_delete_file_cleanup.py` (신규 9개): 데이터셋 삭제 시 디렉터리 제거,
다른 데이터셋 파일 보존, 파일 없는 데이터셋도 성공, 객체 삭제 시 이미지+보관
원본 제거, 3D 모델 제거, 형제 객체 파일 보존, 다이얼로그 경로의 3D 모델 정리,
파일이 이미 없어도 행은 삭제, 그리고 `DatasetDialog.Delete()`가 실제로
컨트롤러를 타는지(직접 `delete_instance()`로 돌아가는 회귀 방지).

## 남은 것

기존 데이터베이스에 이미 쌓인 고아 파일은 소급 정리되지 않는다. 필요하면
`<storage>/` 하위에서 DB에 없는 dataset_id 디렉터리를 찾아 지우는 정리
스크립트를 별도로 만들 것.
