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

## 후속: 드래그 위치 저장이 범례를 날려버린 문제 (0.1.9 신고)

사용자 신고: `Var. explained`를 누르니 오류가 뜨고(아래) **그 뒤로 범례가
보이지 않게 됐다**. 드래그 자체는 잘 됐다고 함.

```
_set_transform(): incompatible function arguments ...
Invoked with: <matplotlib.ft2font.FT2Font object ...>, array([[65536, 0], [0, 65536]]),
[170963420737, 61716190414]
```

### 원인

`set_draggable(True, update="bbox")`로 드래그를 끝내면 matplotlib이 이렇게 한다:

```python
def _update_bbox_to_anchor(self, loc_in_canvas):
    loc_in_bbox = self.legend.axes.transAxes.transform(loc_in_canvas)  # 이미 캔버스 좌표
    self.legend.set_bbox_to_anchor(loc_in_bbox)                        # 2-tuple -> 점
```

캔버스 좌표에 `transAxes`를 한 번 더 적용하므로 앵커가 **거대한 값의 크기 0인
점**이 된다(측정값: `(248080, 110932, 0, 0)`). 내 코드가 그걸 읽어 저장했고,
다음 렌더링에서 그대로 다시 적용하니 범례가 화면 밖 천문학적 좌표로 날아갔다.
텍스트를 그 위치에 그리려다 FT2Font 변환이 터진 것이 신고된 오류이고, 범례가
사라진 것도 같은 이유다. 세 증상(드래그는 정상 → 다음 갱신에서 오류 → 범례
소실)이 모두 여기서 설명된다.

### 수정

- **`update="loc"`으로 변경.** 이 경로는 정규화된 axes 분수 위치를 남기고
  (측정값: `(0.847, 0.669)`), 퇴화된 앵커도 스스로 리셋한다. 저장은 2-tuple,
  복원은 범례 생성 시 `loc=` 로 넘긴다 (`legend_placement_kwargs`).
- **실제 드래그가 끝났을 때만 저장.** 이전에는 캔버스 `button_release_event`에
  물려 있어 평범한 클릭에도 위치를 덮어썼다. 이제 `finalize_offset`을 감싼다.
- **읽을 때·쓸 때 모두 검증** (`_is_sane_placement`: 2개 값, 유한, ±3 이내).
  0.1.9가 저장한 4개짜리 값은 형식부터 어긋나 자동으로 폐기되므로, 이미 범례가
  사라진 사용자도 다음 실행에서 기본 위치로 복구된다.

### 테스트

`tests/dialogs/test_legend_arrangement.py` 28개로 확대. 핵심은 matplotlib의
드래그 종료 동작(`_update_loc`)을 직접 호출해 **저장 가능한 값이 나오는지**
확인하는 것과, 0.1.9가 남긴 값이 폐기되고 범례가 다시 그려지는지 확인하는 것.
