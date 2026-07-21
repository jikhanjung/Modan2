# 첨부 시점 이미지 다운스케일 + 원본 보관 + "Show Original"

## 날짜
2026-07-21

## 배경

거대 이미지(예: 24MP 사진)를 객체에 붙이면 뷰어가 느려진다. 이전에 렌더링
시점 다운스케일로 접근했다가(devlog 209, revert는 devlog 220) 좌표계 이원화의
복잡성 때문에 걷어냈다. 이번에는 **첨부(저장) 시점**에 처리한다:

- 긴 변이 `IMAGE_MAX_DIM`(2560px)을 넘는 이미지는 **축소본을 작업 파일로 저장**
  (JPEG는 quality 90). 랜드마크는 처음부터 축소본 픽셀 좌표로 찍히므로
  좌표계는 하나뿐이고 변환이 필요 없다.
- **원본은 무손실로 별도 보관**: `<storage>/<dataset_id>/originals/<object_id>.<ext>`.
- 작은 이미지는 이전과 동일하게 원본 그대로 저장 (보관본 없음).

## 구현

### MdModel (`MdImage`)
- `add_file(file_name, base_path=...)`: `_try_downscale`가 성공하면 축소본을
  작업 경로에 쓰고 원본을 `originals/`에 복사. 다운스케일이 불필요하거나
  실패하면 기존처럼 원본 그대로 복사 — **첨부는 다운스케일 실패로 절대
  실패하지 않는다**.
- `_try_downscale`: PIL `thumbnail`(LANCZOS), JPEG는 quality 90 + EXIF 보존.
- DB 필드(md5hash/size)는 **원본 파일 기준**으로 기록 (출처 증빙).
- `get_original_file_path()` / `has_archived_original()` 추가.
- `copy_image()`: 데이터셋/객체 복사 시 보관 원본도 함께 복사.

### ModanController
- `_import_object_image`: 인라인 복사 로직을 `add_file(file_name, base_path=…)`
  호출로 통합 — 임포트 경로도 동일한 다운스케일+보관 루틴을 탄다.
- `delete_object_with_files`: 작업본과 함께 보관 원본도 삭제.

### "Show Original" (ObjectDialog 체크박스)
축소본으로 랜드마크를 찍을 때 디테일이 부족할 수 있어, 보관 원본이 있는
객체에서만 `Show Original` 체크박스가 나타난다. 체크하면
`ObjectViewer2D.set_fullres_source(원본 경로)`로 **렌더 소스만** 원본으로
바꾼다:

- 좌표 공간은 계속 작업본(`orig_pixmap`) 치수가 정의 — `image_canvas_ratio`,
  랜드마크 수학 전부 불변. 파일 교체/좌표 변환 없음.
- `curr_pixmap`을 리샘플할 소스만 고해상 원본이 되어 줌인 시 선명해진다.
- 객체 전환/새 이미지 로드 시 자동으로 작업본 렌더로 복귀.

메모리: 체크 중에만 원본 픽스맵(24MP ≈ 96MB)을 추가로 든다. 성능 문제가
보이면 추후 조정하기로 함.

## 테스트
- `tests/test_image_attach_downscale.py`: 축소본 치수/원본 보관/해시 증빙,
  소형 파일 무변경, 파싱 불가 파일 fallback, copy_image의 보관본 전파,
  삭제 시 보관본 정리.
- `tests/test_viewer_fullres_source.py`: 렌더 소스 교체가 좌표 공간을 바꾸지
  않는지, 해제/새 이미지 로드/로드 실패 시 작업본 복귀.

## 참고
- 기존 데이터(이 기능 이전에 첨부된 대형 이미지)는 소급 적용되지 않는다 —
  이미 원본이 작업본이므로 그대로 동작.
- `Show Original` 체크박스 문구의 한국어 번역(ts/qm 갱신)은 다음 lupdate
  주기에 반영할 것.
