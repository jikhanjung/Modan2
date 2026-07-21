# 범례 순서 지정 및 위치 이동 (Data Exploration)

## 날짜
2026-07-21

## 배경

사용자 요청 두 가지:

1. 범례 위치를 조절하고 싶다 → Legend 체크박스 옆에 드래그 가능 여부 체크박스.
2. 범례 항목 순서를 원하는 대로 정하고 싶다.

### 왜 순서가 임의로 보였나

`build_scatter_legend`는 `scatter_result`의 키 순서대로 범례를 만드는데, 그
키 순서는 `_populate_scatter_groups`가 **표본을 순회하다 처음 만난 그룹을 그때
생성**하면서 정해진다. 즉 데이터셋에 표본이 우연히 들어간 순서이고, 읽는
사람 입장에선 아무 의미가 없다.

## 구현

### 저장 위치

`MdAnalysis.chart_settings_json` (nullable CharField) 신설 +
`migrations/006_20260721.py`. 마이그레이션은 앱 시작 시
`MdModel.prepare_database()`의 `router.run()`이 자동 적용한다.

기존 `*_json` 필드들은 각각 특정 페이로드(객체 정보, 랜드마크, PCA 결과…)라
거기에 끼워 넣지 않고 전용 필드를 뒀다. 접근은
`get_chart_settings()` / `set_chart_settings()`로 하며, 깨진 JSON은 경고만
남기고 `{}`를 돌려준다 — 표시 설정 때문에 분석이 안 열리면 안 된다.

구조:

```json
{
  "legend_order":     {"Sex": ["F", "M"]},
  "legend_placement": {"Sex": [x0, y0, w, h]}
}
```

**그룹 기준 변수별로** 저장한다. Sex에서 Locality로 바꾸면 그룹 집합 자체가
달라지므로 순서를 공유하면 안 된다.

### 순서

`scatter_utils.order_legend_keys(keys, order)` 추가 —
`build_scatter_legend(..., order=...)`가 사용한다. 저장된 순서는 낡을 수 있으므로:

- `order`에 있는데 지금 없는 그룹(이름 변경/삭제)은 무시하고,
- `order`에 없는 그룹(새로 생김)은 기존 상대 순서를 유지한 채 뒤에 붙인다.

덕분에 그룹 구성이 바뀌어도 조용히 degrade한다. `build_scatter_legend`는
`DatasetAnalysisDialog`와 공유하므로 그쪽도 나중에 같은 방식으로 쓸 수 있다.

UI는 `dialogs/legend_order_dialog.py`의 작은 모달: `QListWidget`
(InternalMove)로 드래그 재정렬 + A→Z / Z→A 정렬 버튼. 이미 빽빽한 메인
다이얼로그에 목록을 상시 노출하지 않으려고 버튼("Order...")으로 열게 했다.

### 위치

`legend.set_draggable(True, update="bbox")` 자체는 한 줄이지만, **차트가 옵션
변경마다 `ax2.clear()`로 통째로 다시 그려지므로 옮긴 위치가 매번 초기화된다.**
그래서 matplotlib에 드래그 완료 시그널이 없는 점을 감안해 캔버스의
`button_release_event`에서 위치를 읽어 저장하고, 재생성 때
`apply_legend_placement`가 `set_bbox_to_anchor`로 복원한다.

`Movable` 체크박스와 `Order...` 버튼은 Legend가 켜져 있을 때만 활성화된다.

## 테스트

`tests/dialogs/test_legend_arrangement.py` (18개):

- `order_legend_keys` 규칙: 저장값 없음/적용/새 그룹 뒤에 붙음/낡은 항목
  무시/중복 항목.
- 설정 저장: 기본 `{}`, DB 왕복, 깨진 JSON에도 예외 없음.
- 다이얼로그: 기준 변수별 저장, 저장된 순서가 범례에 반영, 다른 기준 변수의
  순서는 적용 안 됨, 재생성 후에도 순서 유지.
- 위치: 왕복 저장, 형식이 잘못된 값 무시, 체크박스 연동, 드래그 활성 상태에서
  재생성이 깨지지 않음.
- 순서 다이얼로그: 목록 순서 반환, 정렬 버튼.

## 남은 것

- `DatasetAnalysisDialog`는 아직 `order`를 넘기지 않는다(같은 헬퍼라 연결만
  하면 된다).
- 새 문구 5개(`Movable`, `Order...`, `Legend Order` 등)는 다음 번역 주기에
  반영 필요 — 절차는 devlog 229.
