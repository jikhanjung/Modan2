# 타원 푸리에 윤곽선 분석(EFA) — 계획과 1차 구현 (2D)

## 날짜
2026-10-02

## 결정 변경: devlog 237의 "EFA는 범위 밖"을 철회

devlog 237(세미랜드마크 계획)은 EFA를 "랜드마크가 아닌 푸리에 계수를 다루는
별개 패러다임이라 평행 서브시스템이 되므로 별도 도구(예: Silhouetto)나 내보내기로
처리"한다고 범위 밖에 두었다. 두 전제가 모두 성립하지 않았다.

1. **Silhouetto에는 EFA가 없다.** `~/projects/Silhouetto`는 wxPython 기반의 오래된
   윤곽 디지타이저로, 푸리에 분석 코드가 한 줄도 없다. 넘길 곳이 없었다.
2. **평행 서브시스템이 필요 없다.** 아래 "핵심 설계"대로, 정규화된 계수를 등거리
   사상(isometry)으로 점 집합에 옮기면 PCA·CVA·MANOVA와 Data Exploration이
   무변경으로 계수 공간의 결과를 낸다. 갈라지는 곳은 "형태 변수를 만드는 단계"
   (Procrustes 대신 EFA) 하나뿐이다.

입력 쪽은 237이 예상한 그대로다. `MdObject.curve_raw_json`(원시 추적점)이 EFA의
입력이고, 곡선 추적 UI·live-wire·병합-시점(merge-at-analysis) 모델을 그대로 쓴다.

## 사용자 결정 (2026-10-02)

- **시작점은 랜드마크 성격의 점으로 잡는다.** 매뉴얼에 명시. 따라서 EFA의
  시작점(위상) 정규화를 하지 *않는다* — 시작점은 형태의 일부다.
- **방향은 항상 시계방향.** 사용자가 어느 방향으로 추적해도 분석 전에 시계방향으로
  맞춘다(첫 점 기준으로 뒤집어 시작점 유지).
- **조화항 수 H 기본값은 harmonic power 99%.**
- **2D 먼저.** 3D 윤곽(구면 조화 등)은 다른 방법이라 별개 작업.

## 핵심 설계

### 데이터
| 데이터 | 위치 | 비고 |
|---|---|---|
| 닫힌 곡선 여부 | `MdDataset.curve_config_json` 각 곡선의 `"closed": true` | 새 키. 열린 곡선은 키가 없음(기존 설정이 바이트 그대로 유지) |
| 원시 윤곽선 | `MdObject.curve_raw_json` | 기존 그대로 |
| EFA 설정·계수 | `MdAnalysis.efa_json` (마이그레이션 010) | 곡선 id/이름, H, H 자동 여부, 임계값, 표본점 수 M, 객체별 `{id, size, coefficients}` |

`closed` 플래그는 원래 `resample_polyline(closed=)`과 `build_landmarks_with_curves`
에만 있었고 **설정·UI·`MdDatasetOps`에는 저장되지도 쓰이지도 않았다.** 이번에
곡선 설정에 넣고, 객체 대화상자(Closed 체크 열)·데이터셋 대화상자(Curves 탭
Closed 열)에서 편집하며, `MdDatasetOps`와 2D 뷰어가 닫힌 곡선을 고리로 재표본화
한다. 뷰어는 끝점→시작점 선분을 그리고 시작점을 작은 사각형으로 표시한다.

설정을 재구성하는 세 곳(곡선 N 변경, 새 곡선 추가, 곡선 삭제)이 각자 dict를
손으로 다시 만들면서 필드를 골라 담고 있었다. `closed`를 잃지 않도록
`mu.curve_scheme_entries(config)` 하나로 모았다. 그 과정에서 **기존 버그**를
발견: 새 곡선을 추적해 추가하면(`finish_curve`) 정수 개수만 넘겨 재구성하므로
기존 곡선의 이름·설명이 모두 지워졌다. 이 수정은 EFA와 무관하게 0.2.x에도
필요해 **main에 따로 커밋**했다(`aaae78c`). 이 브랜치는 그 위에서 같은 자리를
`curve_scheme_entries`로 바꾼다.

### 수학 — `MdOutline.py` (순수 numpy)
- `efa_coefficients`: Kuhl & Giardina(1982) 폐형식. 매개변수는 호 길이 비례,
  `t = 0`이 첫 추적점. 중복점·닫는 점은 `clean_outline`이 제거(0 길이 선분 방지).
- `make_clockwise`: 신발끈 공식 부호로 판정. 이미지 좌표(y 아래 방향)에서 화면상
  시계방향 = 양의 면적. 반시계면 `p0, pk, …, p1`로 뒤집어 시작점 유지.
- `normalize_coefficients`: 크기·회전만 정규화, **위상 이동 없음**. 첫 조화항
  타원의 장반경으로 나누고 장축을 +x에 맞춘다. 장축의 두 끝 중 매개변수상
  시작점에 가까운 쪽(θ* ∈ (−π/2, π/2])을 택한다 — Momocs
  `efourier_norm(start = TRUE)`와 같은 규칙. 첫 조화항이 정규화 후에도 상수가
  되지 않으므로(시작점 보존) 4H 계수를 모두 쓴다.
- `choose_harmonics`: 표본별로 누적 power가 임계값에 닿는 최소 H를 구해 **최대값**
  을 데이터셋 H로 쓴다(모든 표본에서 99% 이상 보존). power는 데이터셋 전체가
  지원하는 상한(가장 성긴 윤곽선 점 수의 절반, 최대 50)까지에 대한 비율.

### 핵심 트릭 — 계수를 등거리 점으로
정규화 계수를 `t_k = 2πk/M` (k = 0..M−1)에서 재구성하고 `√(2/M)`을 곱한다
(`coefficients_to_points`). M > 2H이면 그 표본점들에서 cos/sin 기저가 직교하고
노름²이 M/2이므로, 이 사상은 계수 공간의 **정확한 등거리 사상**이다. 결과:

- PCA 고유값·점수가 계수 PCA와 동일(테스트로 고정). CVA·MANOVA(PCA 점수 기반)도
  선형 불변이라 동일.
- 이 점들을 `superimposed_landmark_json`에 넣으면 PC 축을 따른 재구성·형태 격자·
  평균 형태가 Data Exploration에서 **윤곽선 그대로** 그려진다. 역변환 UI를 따로
  만들 필요가 없다.
- 점 0은 (조화항 절단 오차 범위에서) 상동 시작점이다.

M = max(64, 4H). 분석 `wireframe`은 M점 닫힌 고리(`outline_loop_wireframe`),
baseline·polygons는 없음.

### 분석 경로
- `NewAnalysisDialog`: 2D이고 닫힌 곡선이 있을 때만 "Elliptic Fourier (outline)"
  항목이 나타난다. 선택 시 Outline(닫힌 곡선 콤보)과 Harmonics(0 = "Auto (99%
  power)") 표시. 방식 콤보에 번역되지 않는 키를 item data로 달았다. **기존 버그**:
  이전에는 `currentText()`(번역 문자열)를 넘겼고, 한국어 UI에서 Bookstein을 고르면
  "북스틴"이 넘어가 컨트롤러가 인식하지 못하고 조용히 Procrustes로 실행한 뒤
  분석을 "북스틴"이라는 이름으로 저장했다. 이 수정도 **main에 따로 커밋**했다
  (`fae676f`); 이 브랜치는 그 위에 EFA 항목을 더한다.
- `ModanController._prepare_landmarks`: 방식이 EFA면
  `MdModel.outline_dataset_ops()`로 우회(GPA 없음). 모든 객체에 윤곽선이 있어야
  하며 없으면 이름을 나열해 실패.
- 검증(`validate_dataset_for_analysis(..., outline_curve=)`): EFA는 랜드마크가 아니라
  해당 곡선을 추적한 객체 수(≥5)를 센다. 고정 랜드마크가 전혀 없는 데이터셋도
  분석 가능해야 하기 때문.
- `object_info_json`의 `csize`: EFA 분석에서는 **첫 조화항 장반경**(EFA가 나눠
  없애는 크기, 축척 보정)을 넣는다. 매뉴얼에 명시.
- 분석에 `curve_config` 스냅샷도 저장.

### Data Exploration
- 형태를 그릴 데이터셋: 랜드마크 분석은 실제 데이터셋, EFA 분석은 저장되지 않는
  대리 데이터셋(id −1, 2D, 고리 wireframe만). 실제 데이터셋의 wireframe·
  landmark 이름·곡선 설정은 윤곽 점을 가리키지 않으므로.
- PC 축 콤보의 개수를 데이터셋 객체의 랜드마크 수가 아니라 분석된 형태에서 센다.
  **기존 버그**도 같이 해결: 곡선 데이터셋은 세미랜드마크가 `landmark_list`에
  없으므로(병합-시점 모델) PC 목록이 고정 랜드마크 수만큼에서 끊겼다.

## 범위 밖 / 후속

- **계수 내보내기** (CSV, SHAPE의 NEF 형식). 계수는 `efa_json`에 저장되어 있어
  내보내기만 붙이면 된다. 다음 단계 1순위.
- **표본당 여러 윤곽선**: 계수 벡터를 이어 붙이면 되지만 정규화 기준(어느 윤곽의
  첫 조화항?)을 정해야 한다.
- **랜드마크와 계수의 결합 분석**: 표준이 아니어서 제외.
- **회전 정규화 대안**: 첫 조화항 타원이 원에 가깝거나 시작점이 단축 끝 근처면
  회전이 뒤집힐 수 있다(EFA의 알려진 약점). 매뉴얼에 "형태의 긴 축 끝 근처에서
  시작"을 권고했다. 필요해지면 "시작점 방향으로 회전" 옵션을 추가.
- **live-wire로 추적한 닫힌 곡선의 마지막 구간**은 끝점→시작점 직선. 시작점
  근처에서 끝내라고 매뉴얼에 적었다. 고리 전체를 스냅하려면 추적 UI 변경 필요.
- **3D**.

## 테스트

`tests/test_efa.py`(30개):
- Kuhl–Giardina 폐형식이 호 길이 매개 다각형의 푸리에 적분(독립 수치 적분)과 일치
- 위치·크기·회전·추적 방향 불변, 시작점은 보존(굴린 시작점은 다른 계수)
- 첫 조화항 장축이 +x, 퇴화 첫 조화항 거부
- power 99% 선택(순수 타원 = 1, 경계값, 데이터셋 최대값, Nyquist 상한)
- 계수↔점 등거리, **점 PCA = 계수 PCA**
- `closed` 플래그 왕복, `MdDatasetOps`가 닫힌 곡선을 고리로 재표본화
- `outline_dataset_ops`: 열린 곡선·미추적 객체(이름)·3D 거부, 축척 보정 크기
- 컨트롤러 end-to-end: `efa_json`, 고리 wireframe, `csize` = 윤곽 크기, 기존 분석
  무영향, 추적 객체 수 검증

`tests/dialogs/test_analysis_dialog.py`(4개 추가): EFA 항목이 닫힌 곡선이 있을
때만 나타남, 닫힌 곡선만 Outline에 나열, Auto면 `harmonics=None`, 수동 값 전달.

전체: 2106 passed, 10 skipped. 이 환경에는 `libxcb-icccm4` 등이 없어 xcb 플랫폼
대신 `QT_QPA_PLATFORM=offscreen`으로 실행했다(CLAUDE.md의 시스템 패키지 미설치
상태).

## UI 번역

`Modan2_ko.ts`는 이미 이전 작업분(라이브러리 백업·이동 등, devlog 282–283) 문자열
40여 개가 추출되지 않은 상태였다. `pylupdate5` 결과를 그대로 쓰면 무관한 변경이
섞이므로 되돌리고, 이번 기능의 문자열 7개(Closed ×2, Outline, Harmonics, Auto (99%
power), Elliptic Fourier (outline), 계산 중 메시지)만 해당 context에 직접 넣었다.
PySide6 `lrelease`로 `.qm`을 만들고 PyQt5 `QTranslator`로 로드해 확인. 밀린 40여
개는 그대로 남아 있다 — 별도 작업.

## 매뉴얼

- `user_guide.rst`: 곡선 표에 Closed 열, "닫힌 곡선(윤곽선)" 단락, 분석 방식 목록,
  새 절 **Outline Analysis (Elliptic Fourier)** — 시작점을 랜드마크 성격의 점으로
  잡을 것, 시계방향 자동 처리, H 자동(99%), 정규화 내용, 회전 불안정 주의.
- `advanced_features.rst`: 중첩정렬 방식 설명과 선택 표에 EFA 추가.
- 한국어 `.po`: 바뀐/새 항목만 직접 삽입(`sphinx-intl update`는 모든 위치 주석을
  이 머신의 경로로 다시 써서 diff가 커지므로). 두 카탈로그 모두 미번역 0. 손댄 기존
  항목 2개는 번역이 낡아 있었다(중첩정렬 방식을 Resistant Fit 포함 세 가지로
  설명) — 새 원문에 맞춰 함께 갱신.
