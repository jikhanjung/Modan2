# X1Y1 `nlandmarks=0` 잠복 버그 수정 + X1Y1/NTS 파서 테스트 커버리지

## 날짜
2026-07-26

## 배경

`components/formats/`의 파서 커버리지를 실측하니 `x1y1.py` 17%, `nts.py` 16%로
형제 파서(`tps` 85%, `morphologika` 87%)에 크게 뒤졌다. X1Y1/NTS는 import 시
거의 검증되지 않은 경로를 타고 있었다. `tests/test_format_handlers.py`에는 두
포맷 테스트가 `@pytest.mark.skip`으로 꺼진 채 방치돼 있었다.

- NTS: 2개 테스트가 작성돼 있었으나 클래스 레벨 skip.
- X1Y1: 빈 스텁 + "차원 감지 로직이 반직관적이라 조사 필요"라는 skip 사유.

되살려 채우는 과정에서 **X1Y1의 잠복 버그**를 발견했다 —
[[20260721_R03_improvement_review]] 이후 NTS에서 고쳤던 것과 완전히 같은 형태.

## 1. X1Y1 `nlandmarks=0` 버그

`x1y1.py:read()`는 랜드마크 개수를 `int(len(xyz_header_list) / self.dimension)`로
**계산만 하고 결과를 버렸다**(대입 없음). 그래서 `landmark_count`는 초기값 0에
머물고 `self.nlandmarks = landmark_count`도 항상 0이었다. `nts.py`에서 이미
고쳤던 것과 동일한 버그(계산해 놓고 안 쓰는)다.

- **영향**: 죽은 값이 아니다. `ModanController.import_dataset`가
  `MdUtils.build_curve_config(import_data.nlandmarks, ...)`에 이 값을 넘긴다
  (`ModanController.py:678`). X1Y1 import 시 커브 config가 잘못된 랜드마크 수(0)로
  만들어질 수 있었다 — NTS 수정이 필요했던 이유와 같다.
- **수정**: 계산 결과를 `landmark_count`에 대입. 한 줄.

## 2. "차원 감지가 이상하다"는 skip 사유는 오해

skip 주석은 헤더 `['', 'X1', 'Y1', 'X2', 'Y2']`에서 `xyz_header_list[2]`가 `'Y1'`
이라 3D로 잘못 잡힌다고 적어 놨지만, 실제로는 `header[1:]`이라
`xyz_header_list = ['X1','Y1','X2','Y2']`, `[2] = 'X2'` → `'x'`로 시작 → 2D로 정상.
3D면 `['X1','Y1','Z1',...]`에서 `[2]='Z1'` → 2D 아님 → 3D. **세 번째 좌표열**을
보는 영리하고 올바른 로직이다. 인덱스 오산에서 나온 오해였다.

주의: `read()`는 `lines[0].strip().split("\t")`로 헤더를 파싱한다. `strip()`이
선행 탭(빈 이름열)을 먹어버리므로 실제 X1Y1 헤더의 첫 셀은 비어 있으면 안 된다
(이름열 라벨이 있어야 함). 테스트도 라벨(`name`)을 넣어 작성.

## 3. 테스트 추가

`tests/test_format_handlers.py`:
- **NTS**(클래스 skip 해제 + 확장): 행이름 레이아웃 `L`(별도 줄)/`b`(행 시작)/
  `e`(행 끝), 이름 미제공 시 `dataset_N` 자동생성, 3D, 2D invertY, 따옴표 주석
  수집, `0 object / 0 variable` 헤더 단락 처리.
- **X1Y1**(스텁 → 실테스트): 2D/3D 파싱, `nlandmarks` 회귀, 2D invertY,
  주석(`#`)·따옴표 줄 스킵, 빈 파일 `ValueError`, 좌표열 3개 미만 헤더 `ValueError`.

## 결과

- 커버리지: `x1y1.py` 17% → **89%**, `nts.py` 16% → **88%**
  (`components/formats` 전체 57% → 86%).
- `test_format_handlers.py`: 10 passed + 2 skipped → **26 passed, 0 skipped**.
- 남은 미커버는 대부분 모듈 상단 GLUT import 폴백과 미사용 `isNumber` 헬퍼.
- import/controller/semilandmark/sentinel 관련 스위트 회귀 없음.
