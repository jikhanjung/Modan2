# update_image 고아 파일 정리 (R03 항목 1)

## 날짜
2026-07-21

## 문제

`MdObject.update_image`는 기존 `MdImage`의 DB 행만 지우고 새 행을 만든다.
파일 경로가 `<storage>/<ds.id>/<obj.id>.<확장자>`이므로 새 이미지의 확장자가
같으면 덮어쓰지만, **다르면 이전 작업본 파일이 디스크에 고아로 남았다**.
첨부 시점 다운스케일(devlog 222) 도입 후에는 `originals/` 보관본까지 고아가
될 수 있어 수정 (R03 리뷰 항목 1).

## 수정 (`MdModel.py`)

`update_image`에서 기존 행을 지우기 전에 이전 이미지의 `get_file_path()`와
`get_original_file_path()`를 삭제. 삭제 실패(OSError)는 warning 로그만 남기고
교체는 계속 진행 — 파일 정리 실패가 이미지 교체를 막으면 안 된다.

3D 모델은 교체 경로가 없어(`save_object`가 `not has_threed_model()`일 때만
`add_threed_model` 호출) 해당 없음.

데이터셋 삭제 시 `<storage>/<ds.id>/` 디렉터리 전체가 고아가 되는 관련 별건은
R03에 남아 있음 (미해결).

## 테스트

`tests/test_image_attach_downscale.py`에 추가:
- 확장자가 다른 이미지로 교체 시 이전 작업본+보관 원본이 삭제되고 새 파일만
  남는지.
- 같은 확장자 교체는 덮어쓰기로 정상 동작하고 DB 행이 1개 유지되는지.

참고: `update_image`는 이미지가 이미 있는 객체 전제(`get_image()`가
`image[0]` 접근; 컨트롤러도 `has_image()`일 때만 호출). 첫 첨부는
`add_image`가 맞다.
