# 데이터셋 export/import의 조용한 데이터 손실 — 커브 · missing · polygons

## 날짜
2026-07-24

## 배경

복잡도 리팩토링([[20260724_242_complexity_refactoring_and_characterization]]) 중
`MdUtils.import_dataset_from_zip`(23→<15)을 정리한 직후, "export/import가
missing·curve 데이터를 제대로 처리하는가?"라는 물음을 실제 라운드트립으로
검증했다. 조용한 데이터 손실을 찾는 이 점검에서 **세 개의 버그**가 드러났다 —
zip 경로 2건(커브·missing)과 파일 import 경로 1건(polygons).

## 실증

커브 스킴 + missing 랜드마크 + 객체 트레이스를 넣고
`create_zip_package` → `import_dataset_from_zip`:

| 항목 | export 전 | import 후(수정 前) |
|---|---|---|
| 랜드마크(missing 포함) | `[[1,2],[None,None],[5,6]]` | 값은 동일하나 `landmark_str`이 `None\tNone` |
| `curve_config`(데이터셋 스킴) | `[{id:c1, n:4, start:3, …}]` | **`[]`** ❌ |
| `curve_raw`(객체 트레이스) | `{c1:[3점]}` | **`{}`** ❌ |
| `curve_anchors` | `{c1:[2점]}` | **`{}`** ❌ |

## 버그 1 — 세미랜드마크 커브 전체 소실 (export 쪽 문제)

> **관점 주의:** 1.1은 **커브 기능이 들어오기 전** 포맷이므로 커브 데이터가
> 없는 게 당연하다. 따라서 "import가 1.1을 못 읽는다"는 문제가 아니다 — **1.1
> 패키지는 커브 없이 그대로 읽히는 게 올바른 동작**이다. 진짜 버그는 **export가
> 커브 기능 추가 후에도 매니페스트를 확장하지 않아, 현재(1.2급) 데이터를 낡은
> 1.1 스키마로 내보내며 스스로 버린 것**이다.

패키지 매니페스트(`format_version: "1.1"`)에 **커브 필드가 없었다.** dataset에는
`name/description/dimension/variables/wireframe/polygons/baseline`만, object에는
`landmarks/variables/files`만 있었다. 세미랜드마크 커브(devlog 237~240)가
추가됐는데도 export 직렬화가 그에 맞춰 확장되지 않아, 커브를 가진 데이터셋을 zip
으로 내보냈다 다시 들이면 **커브가 통째로 사라지고** 고정 랜드마크만 남았다.
경고조차 없는 조용한 손실이라 더 위험했다.

**수정:** export 스키마를 **1.1 → 1.2**로 올리고 커브 필드를 추가.
- dataset → `curve_config`
- object → `curve_raw` / `curve_anchors`

serialize가 이를 쓰고, importer가 `set_curve_config` / `set_curve_raw` /
`set_curve_anchors`로 복원한다. **1.1 하위호환은 원래 정상 동작**이며 그대로
유지된다 — 커브 키가 없는 1.1 패키지는 `.get(...) or {}`로 읽혀 커브 없이
import된다(기존 1.1-입력 테스트가 이를 커버). 즉 이번 변경은 "1.1을 고친 것"이
아니라 **export가 1.2 데이터를 온전히 담게 한 것**이다.

## 버그 2 — missing 랜드마크가 앱 관례와 다르게 기록됨

importer가 `mo.landmark_str = "\\n".join("\\t".join(str(x) for x in lm) …)`로
문자열을 만들어, JSON `null`이 **`"None"`**이 됐다. 앱의 정식 인코딩은
`pack_landmark()`가 쓰는 **`"Missing"`**이다. 라운드트립이 되던 건 순전히
`unpack_landmark()`가 **모든 비숫자 토큰을 None으로** 처리하는 덕의 **우연한
정합**이었고, 파서가 엄격해지거나 "Missing"을 특별 취급하면 깨질 상태였다.

**수정:** importer가 `landmark_list`를 만들어 **모델의 `pack_landmark()`를 호출**.
이제 missing이 앱 어디서나처럼 `"Missing"`으로 저장된다.

## 버그 3 — 파일 import이 polygons를 버림 (Morphologika [polygons])

zip 두 건을 고친 뒤 **다른 포맷의 파일 import 경로도 같은 관점으로** 점검했다.
각 리더가 파싱하는 `self.*`와 `ModanController.import_dataset`가 실제 소비하는
필드를 대조하니, import가 **wireframe(`edge_list`)은 데이터셋에 넣지만
`polygon_list`는 전혀 쓰지 않았다.**

실증: `[wireframe]`+`[polygons]`가 있는 Morphologika 파일을 import하면 리더는
`polygon_list=[[1,2,3]]`로 정확히 파싱하는데, 데이터셋 polygons는 **`[]`**로
비었다(wireframe·variables는 정상). MdDataset 모델도 zip export도 polygons를
담는데 **파일 import 경로만 누락**이었다 — 커브 손실과 같은 부류의 조용한 손실.

리더별 대조 결과 메타데이터를 담는 건 Morphologika뿐이고(변수·wireframe·polygons·
이미지·ppmm), 그중 **polygons만** 빠져 있었다. TPS(comment/image/curve)·NTS·X1Y1은
각 포맷이 담는 것만 있고 모두 소비된다.

**수정:** `import_dataset`가 wireframe 옆에서 `polygon_list`도 `pack_polygons()`로
저장한다.

## 회귀 테스트

- `test_zip_roundtrip_preserves_missing_landmarks_and_curves` — 커브 스킴·raw·
  anchors 보존과 missing 랜드마크(그 `"Missing"` 인코딩)를 단언. 기존 1.1-입력
  import 테스트는 그대로 통과하여 하위호환을 검증한다.
- `TestImportPreservesGeometry.test_morphologika_polygons_and_wireframe_survive_import`
  — Morphologika 파일 import 후 polygons·wireframe·variables가 DB에 도달함을 단언.

**전체 체인 검증:** Morphologika 파일 → `import_dataset` → zip export → zip import
에서 wireframe·polygons·variables·landmarks가 끝까지 보존됨을 확인.

## 교훈

- **직렬화·import 경로는 기능이 늘 때 함께 커야 한다.** 세미랜드마크 커브(devlog
  237~240)가 추가됐지만 export 매니페스트는 그에 맞춰 확장되지 않았고, polygons는
  리더·모델·zip은 지원하는데 파일 import 경로만 빠져 있었다. 이런 **소비-측 누락**은
  UI 테스트로는 안 잡히고 **라운드트립 테스트**로만 드러난다.
- "우연히 동작하는" 인코딩(`"None"` ↔ 관대한 파서)은 잠복 폭탄이다. 앱의 단일
  인코딩 경로(`pack_landmark`)를 재사용하는 게 정도(正道).
- **점검 방법:** "리더가 채우는 `self.*`" vs "import/serialize가 실제 읽는 필드"를
  대조하면 소비되지 않는(=버려지는) 데이터를 체계적으로 찾을 수 있다.
