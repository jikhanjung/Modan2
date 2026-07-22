# 세미랜드마크(Semi-landmark) 지원 구현 계획

## 날짜
2026-07-22 (개정: 배치 중심으로 재정렬, JSON 3분할 데이터 모델 확정,
미끄러짐은 구현 범위에서 제외하고 기록만 유지)

## 배경

세미랜드마크(semi-landmark)는 곡선/곡면 위에 놓이는 점으로, **위치 자체는 의미가
없고 곡선 상의 "어딘가"라는 것만 의미가 있다** (고정 해부학적 랜드마크와 대비).
이를 다루는 방식은 크게 두 단계/두 학파로 나뉜다. 둘은 배타적이지 않고 순차적인
파이프라인이다:

```
곡선 정의 → 곡선 위 점 배치(등간격/등각도) → [선택: Procrustes 중 접선 미끄러짐] → 통계
              (A. 배치 방식 — 핵심)                  (B. 미끄러짐 방식 — 옵션)
```

### A. 배치(placement) 방식 — 이 계획의 핵심
곡선을 그린 뒤 그 위에 세미랜드마크를 **등간격(호 길이 기준)** 또는 **등각도**로
N개 찍는다. 이렇게 놓은 점을 그냥 일반 랜드마크처럼 Procrustes에 넣는다.
**Procrustes 과정에서 점을 움직이지 않는다.** 단순하고 널리 쓰이며, 아웃라인
분석의 표준.

### B. 미끄러짐(sliding) 방식 — 선택적 후속
배치 이후, Procrustes 반복 중 각 세미랜드마크를 **곡선 접선 방향으로만** 이동시켜
(곡선을 벗어나지 않음) 기준 형상(mean shape)과의 굽힘 에너지 또는 Procrustes
거리를 최소화한다 (Bookstein 1997; Gunz et al. 2005; `geomorph` curves,
`Morpho` slider3d, tps 시리즈에 구현).

미끄러짐의 근거: 등간격 배치는 사실 **임의적**이다. 두 곡선 모양이 다르면
"3번 점"이 호 길이의 같은 분율에 있어도 기하학적으로 대응하는 위치가 아닐 수
있고, 이 임의성이 가짜 변이를 데이터에 넣는다. 미끄러짐은 이를 완화해 기하학적
상동성을 맞춘다. **그러나 필수가 아니다** — 등간격 고정 점만으로 충분한 경우가
많다. 미끄러짐은 배치를 대체하는 게 아니라 그 위에 얹는 옵션이다.

핵심 통찰: **세미랜드마크는 (배치 이후) 그냥 좌표다.** PCA/CVA/MANOVA 등 하류
통계(`MdStatistics.py`)는 어느 방식이든 수정이 필요 없다. 특별 취급이 있다면
오직 (B) 미끄러짐 단계뿐이며, 그것도 옵션이다.

## 현재 코드 구조 (조사 결과)

### 랜드마크 저장
- `MdObject.landmark_str` (CharField) 에 직렬화. `pack_landmark()`/
  `unpack_landmark()` (MdModel.py:576-633) 로 `landmark_list: list[list[float|None]]`
  변환.
- **점 단위 메타데이터(랜드마크 "타입")는 현재 전혀 없다.** 유일한 점 구분은
  결측(None) 여부뿐.

### 데이터셋 부가 구조 저장 패턴 (모방 대상)
`MdDataset` 는 부가 구조를 모두 문자열 컬럼으로 저장한다:
- `wireframe` — `pack_wireframe()`/`unpack_wireframe()` (MdModel.py:288-334).
  엣지 = `"1-2,2-3,3-1"` 형식(1-based 인덱스). → `edge_list`.
- `baseline`, `polygons` — 동일 패턴.
- 곡선/세미랜드마크 스펙도 **동일하게 새 문자열 컬럼**으로 저장하는 것이 자연스럽다.

### 대화형 편집 UI (곡선 그리기의 모방 대상)
- 대화형 엣지 편집이 뷰어에 있음: `components/viewers/object_viewer_2d.py`
  (MODE 상수, `add_edge()` :1144-1158, `pack_wireframe()`+`save()`). 3D는
  `object_viewer_3d.py`. **곡선(점 순서) 그리기 UI는 이 엣지 편집 흐름을
  거의 그대로 모방하면 된다.**
- `dialogs/dataset_dialog.py` — 구조를 텍스트로도 편집(`edtWireframe` 등).

### 정렬 파이프라인 (미끄러짐 삽입 지점 — 옵션 B용)
`MdDatasetOps` (MdModel.py:1665). GPA 반복 루프:
- `procrustes_superimposition()` (MdModel.py:2036-2085): 중심 이동 + 단위 스케일
  → 반복 루프(`get_average_shape` → `is_same_shape` 수렴 → `set_reference_shape`
  → 각 객체 `rotate_gls_to_reference_shape(j)`).
- `_align_to_mean_shape()` (MdModel.py:1986-2015): 결측/임퓨테이션 경로가 쓰는
  공유 GPA 코어. 동일 구조.
- 미끄러짐을 넣는다면 회전 정렬 직후(:2080, :2008)에 삽입. 스펙이 없거나 옵션이
  꺼져 있으면 no-op.

### 마이그레이션 / 통계 / 포맷
- `peewee_migrate`, 최신 템플릿 `migrations/006_20260721.py`.
- `MdStatistics.py` PCA/CVA/MANOVA는 모든 좌표 동등 취급 → **수정 불필요.**
- `components/formats/tps.py` 는 `CURVES=`/`SLIDERS=` 를 현재 무시(:121-137).
  향후 임포트 확장 지점.

## 데이터 모델 설계 (JSON 3분할 — 확정)

기존 delimited 문자열(`wireframe`/`baseline`/`polygons`)은 **평탄한 정수 인덱스
목록**에만 적합하다. 곡선 데이터는 (표본당 여러 곡선) × (곡선당 가변 개수의 원시
점) × (점당 좌표) 로 **중첩·가변·다중** 구조라 str로는 부족하다. 이 코드베이스는
이미 복잡/중첩 데이터를 JSON-in-CharField 로 저장한다(`MdAnalysis.object_info_json`,
`raw_landmark_json`, `chart_settings_json` — MdModel.py:2437-2459; 접근자 패턴은
`get_chart_settings`/`set_chart_settings` :2466-2483). 따라서 **JSON 채택.**

데이터를 세 조각으로 분리한다:

| 데이터 | 위치 | 형식 | 성격 |
|---|---|---|---|
| 곡선 설정(곡선 개수, 각 곡선 목표 세미랜드마크 수 N, 리샘플 방식, landmark_list 내 시작 인덱스) | `MdDataset.curve_config_json` | JSON | 모든 표본 공유 구조 |
| 원시 곡선 추적(표본별 폴리라인 점들, 곡선별) | `MdObject.curve_raw_json` | JSON, **선택적** | 표본마다 다름 |
| 리샘플된 세미랜드마크(등간격/등각도 N개) | 기존 `landmark_str`/`landmark_list` | 기존 그대로 | **그냥 일반 랜드마크** |

- **리샘플된 최종 점은 기존 `landmark_list`에 일반 랜드마크로 들어간다.** 따라서
  뷰어·GPA·통계가 전부 무변경. 설정 JSON이 "몇 번~몇 번 인덱스가 어느 곡선의
  세미랜드마크인지"만 기록한다.
- **N은 데이터셋 설정**(모든 표본 동일해야 GPA 가능), **원시 추적점 개수는 표본
  자유**(같은 N으로 리샘플).
- 재현성을 위해 `MdAnalysis` 에도 곡선 설정 스냅샷.
- 접근자: `get_curve_config()`/`set_curve_config()`, `get_curve_raw()`/
  `set_curve_raw()` (chart_settings 패턴 재사용 — 손상/부재 시 안전 기본값).

예시 레이아웃(모든 표본 동일):
```
landmark_list = [고정1, 고정2, 곡선A×10, 고정3, 곡선B×8]
MdDataset.curve_config_json = [
  {"id":"A","n":10,"method":"equidistant","start":2},
  {"id":"B","n":8, "method":"equidistant","start":13}
]
MdObject.curve_raw_json = {"A": [[x,y],...raw...], "B": [[x,y],...]}   # 표본마다 다름
```

### 원시 추적점 보관 정책 — 보관하되 선택적
원시점을 버리면 **재리샘플(N/방식 변경)과 곡선 편집이 영구 불가**해진다(one-way
door). 원시점이 실제 관측이고 리샘플 결과는 파생물이므로 provenance 상으로도
보관이 옳다(tpsDig outline, geomorph traced curve 도 원본 유지). 용량은
CharField(TEXT, 길이 무제한)로 충분하며 정말 커지면 `MdCurve` 별도 테이블로 이관.

단, `curve_raw_json` 은 **선택적**이라 없어도 우아하게 저하한다:
- 앱에서 곡선을 그린 데이터셋 → 원시점 보관 → 재리샘플/편집 가능
- TPS 등에서 이미 리샘플된 세미랜드마크만 임포트 → `curve_raw_json` 부재 →
  분석은 정상, 재리샘플만 불가

### 별도 테이블(`MdCurve`) 대안
원시점이 매우 커지거나 독립 쿼리가 필요하면 `MdImage` 처럼 FK 연결 별도 테이블이
더 깔끔(지연 로딩, 행 비대화 방지). 현재는 데이터 규모·코드 관례상 JSON 컬럼을
우선하고, 성능 문제가 실측되면 이관.

## 구현 단계 (권장 순서)

### 1단계 — 데이터 모델 + 리샘플링 유틸 (핵심, Procrustes 무변경)
- 데이터 모델: `MdDataset.curve_config_json`, `MdObject.curve_raw_json`,
  `MdAnalysis.curve_config_json` 스냅샷 + get/set 접근자(chart_settings 패턴) +
  마이그레이션 `007_20260722.py` (006 템플릿; 테이블 `mddataset`/`mdobject`/
  `mdanalysis`, 컬럼은 `CharField(null=True)`).
- 기하 유틸: 순서 있는 점 목록(폴리라인)을 받아 **등간격(호 길이)** 또는
  **등각도**로 N개 점을 리샘플하는 함수(`MdUtils`/`MdHelpers`). 2D 우선, 3D 후속.
- 리샘플 결과를 `landmark_list` 의 지정 인덱스 범위에 주입하고 설정 JSON에
  기록하는 헬퍼.
- 테스트: config/raw JSON 왕복(손상·부재 시 안전 기본값), 등간격 리샘플이 실제로
  균등한지, 알려진 곡선(반원 등)에서 등각도 배치 검증, 원시점 부재 시 분석 정상.

### 2단계 — 곡선 그리기 UI + 렌더링 통합
- 뷰어 UI: `object_viewer_2d.py` 에 곡선 그리기 MODE 추가(엣지 편집 흐름 모방) —
  점들을 순서대로 클릭해 원시 곡선 정의(`curve_raw_json` 저장), N 지정 시
  리샘플하여 세미랜드마크를 `landmark_list` 에 생성.
- 세미랜드마크를 뷰어에서 구분 표시(색/모양), 원시 곡선 오버레이 그리기.
- 데이터셋 대화상자에 곡선 설정 노출(선택). 3D 곡선은 후속.

### 3단계 (선택, 후속) — 임포트/익스포트
- `tps.py:read()` 에 `CURVES=` 브랜치 추가하여 곡선 설정으로 변환. 익스포트 대칭.
  (임포트된 데이터는 원시점이 없을 수 있음 → `curve_raw_json` 부재 허용.)

## 구현 범위에서 제외 (기록 보존) — 정렬 중 미끄러짐

**이번 구현에서는 미끄러짐(sliding)을 넣지 않는다.** 등간격/등각도로 배치한
세미랜드마크를 일반 랜드마크로 취급하는 것으로 충분하며, 미끄러짐은 배치를
대체하지 않는 선택적 정제 단계이기 때문이다. 향후 도입할 경우를 위해 접근만
기록해 둔다:

- `MdDatasetOps.__init__` 에서 곡선 설정 로드.
- `slide_semilandmarks(reference_shape)`: 각 세미랜드마크에서 곡선 이웃으로 접선
  계산, `dot(reference - current, tangent)` 만큼 접선 따라 이동. 접선 투영 방식
  (Procrustes 거리 최소화; `geomorph` ProcD)이 가장 단순. 굽힘 에너지(TPS)는 그
  다음.
- GPA 루프 회전 직후(MdModel.py:2080, `_align_to_mean_shape` :2008) 삽입,
  **기본 꺼짐**. 도입 시 필수 검증: 스펙 없거나 꺼진 데이터셋은 결과가 완전히
  동일(no-op).

## 위험 요소

- **인덱스 정합성**: 리샘플된 세미랜드마크가 모든 표본에서 같은 개수·같은
  landmark_list 인덱스 범위를 차지해야 GPA/통계가 성립. 설정 JSON의 N·start가
  단일 진실 원천이 되도록.
- **인덱스 베이스 혼동**: wireframe/baseline 문자열은 1-based 저장이지만 일부
  경로는 0-based로 변환(`object_viewer_2d.py:1155` add_edge 는 `+1` 저장).
  곡선 설정 인덱스도 저장·연산 베이스를 일관되게 정하고 문서화.
- **원시점 부재**: 임포트/레거시 데이터는 `curve_raw_json` 이 없을 수 있으므로
  모든 곡선 편집·재리샘플 경로가 부재를 우아하게 처리해야 한다.
- **3D 곡선**: 리샘플/접선 계산이 2D보다 복잡. 2D 먼저.
- **미끄러짐 회귀(향후 도입 시)**: 삽입 지점이 모든 GPA 경로에 걸리므로, 옵션이
  꺼졌거나 스펙이 없으면 완전한 no-op 임을 테스트로 못박아야 한다.

## 요약

핵심은 **곡선 정의 + 등간격/등각도 배치**이며 Procrustes를 전혀 건드리지 않는다
(1~2단계). 데이터는 JSON 3분할 — 설정(dataset), 원시 추적점(object, 선택적),
리샘플 결과(landmark_list의 일반 랜드마크) — 로 저장해 다중 곡선을 자연스럽게
수용하고 뷰어·GPA·통계를 무변경으로 유지한다. 원시 추적점은 재리샘플·편집을 위해
보관하되 부재를 허용한다. 정렬 중 미끄러짐은 이번 구현에서 제외하고 접근만
기록으로 남긴다. 하류 통계는 어느 경우든 수정 불필요.
