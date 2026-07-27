# ruff SIM / PERF / A 도입 — 그리고 내가 만든 회귀

## 날짜
2026-07-27

## 배경

R05 도입의 다음 세 그룹. 합쳐서 161건으로 PIE/RET(122건)보다 크고, 자동수정 비율이
낮아 판단이 훨씬 많이 필요했다.

| 그룹 | 위반 | 결과 |
|---|---|---|
| SIM | 97 | 자동수정 + 수동 변환, SIM102/SIM108 무시 |
| PERF | 21 | PERF102 자동수정, PERF401 15건 변환 / 4건 noqa |
| A | 43 | 전부 개명 (conf.py의 `copyright` 1건만 noqa) |

## SIM

기계적인 것(`in dict.keys()` 29, 수동 카운터→`enumerate` 7, 중첩 `with` 4,
needless bool 3 등)은 자동수정.

**`try/except/pass` → `contextlib.suppress` (8건, 수동)**. ruff가 자동수정을
거부한 이유는 블록 안의 설명 주석이 사라지기 때문이다. 주석을 `with` 위로 올려
직접 변환했다. 이 프로젝트는 S110을 "의도적 방어 억제"라는 근거로 무시하고 있는데,
`contextlib.suppress` 는 **그 의도를 산문이 아니라 코드로 표현**하므로 방침과
어긋나지 않는다.

**SIM102 / SIM108 무시.** ruff가 두 규칙 모두 남은 사이트에서 자동수정을 거부하는데,
그 이유가 곧 판단 근거다:

- SIM102 7곳은 층층이 쌓인 가드로, **각 층이 무엇을 걸러내는지 주석으로 설명**한다
  (`table_view` 의 드래그 모드 검사, 3D 뷰어의 GLUT 가용성). 합치면 긴 조건 하나가
  되고 주석은 갈 곳이 없다.
- SIM108 3곳은 분기 안에 주석이 있어 삼항 연산자로는 담을 자리가 없다.

### 부수 소득 — 아무것도 검증하지 않던 테스트

SIM222가 짚은 `assert viewer.mouse_curr_x != 10 or True` 는 `assert True` 와 같다.
즉 **`test_no_dialog_is_a_noop` 이라는 이름의 테스트가 실제로는 아무것도 확인하지
않고 있었다.** 구현을 보니 `object_dialog is None` 이면 `mouseMoveEvent` 가 좌표를
기록하기 전에 반환하므로(`object_viewer_2d.py:903`), 이름이 주장하는 대로 "상태가
변하지 않는다"를 검증하도록 고쳤다.

## PERF

PERF102 2건 자동수정. PERF401 19건은 자동수정이 아예 제공되지 않아 손으로 변환했다
— 앱 코드 9건, 테스트 2건, 도구 4건.

`tools/search_index.py` 의 4건은 **중첩 루프 + 조건 안에서 여러 줄 dict를
append** 하는 형태라 컴프리헨션이 오히려 읽기 나쁘다. `noqa: PERF401` 로 남겼다.
(처음에 6곳에 noqa를 넣었다가 `--extend-select RUF100` 으로 불필요한 2건을 찾아
제거했다. `--select RUF100` 은 설정을 덮어써서 PERF가 빠진 채 검사되므로 전부
"unused"로 나온다 — `--extend-select` 를 써야 한다.)

## A (빌트인 섀도잉)

- **`int` 인자 14건**: `def cbxShow_stateChanged(self, int):` 같은 Qt 슬롯 시그니처.
  Qt가 위치 인자로 호출하므로 `_state` 로 개명해도 안전.
- **`object` 인자 17건**: `obj` 로 개명. 사전에 `object=` 키워드 호출이 없음을 확인.
- **지역 변수 12건**: `sum`→`total`, `property`→`variablename`, `id`→`object_id`,
  `object`→`obj`. `docs/manual/conf.py` 의 `copyright` 만 noqa — Sphinx가 요구하는
  이름이라 우리가 바꿀 수 있는 게 아니다.

`MdStatistics` 의 `sum`→`total` 은 개명 범위를 좁게 잡아 `cumul / sum` 두 곳이
남았었다. 그대로 뒀다면 **빌트인 `sum` 함수와 나누기를 시도해 TypeError** 가 났을
것이다. 잡아서 함께 고쳤다.

## 내가 만든 회귀 — `self.object` 가 사라졌다

`object` 인자 개명을 함수 단위 정규식(`\bobject\b → obj`)으로 처리했는데, 이게
인자뿐 아니라 **`self.object` 속성까지** 바꿨다:

```diff
     def set_object(self, obj):
-        self.object = object
-        self.dataset = object.dataset
+        self.obj = obj
+        self.dataset = obj.dataset
```

`self.object` 는 뷰어 전반이 읽는 속성이라 12곳이 깨졌고, 2D `paintEvent` 가
세그폴트했다:

```
TypeError: ObjectViewer2D.draw_object() missing 1 required positional argument: 'obj'
```

**사전 검사가 왜 놓쳤나**: 개명 전에 호출부를 `object=` 키워드로 전수 검색해
"키워드 호출 없음 → 안전"이라고 판단했다. 그러나 **피해는 호출부가 아니라 속성
쪽에 났다.** 인자명을 바꾸는 위험만 보고, 같은 이름의 *다른 것*이 함께 바뀔 위험은
보지 못했다.

속성만 원래대로 되돌리고 인자 개명은 유지했다. 전체 스위트가 잡아냈다 —
`git stash` 로 변경 전 상태에서 같은 테스트를 돌려 회귀임을 확정한 뒤 수정했다.

## 검증

- `ruff check .` / `ruff format .` 클린.
- 전체 스위트 **1882 passed, 10 skipped** (변경 전과 동일).
- CI 3개 플랫폼 통과.

## 현황

```
E F I N UP B C4 LOG RUF012 S DTZ C901(래칫 19) PIE RET SIM PERF A   ← 적용
PTH G                                                              ← 남음
```

근거와 함께 무시 중인 서브룰: S110/S112/S311, RET504, SIM102, SIM108.
